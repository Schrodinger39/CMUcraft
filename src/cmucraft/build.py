"""Build the small 2D survey and two-layer schematic.
Input hashes and coverage are checked before export. Distances check projection
and quantization, not the real-world accuracy of the source building survey."""

import csv
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyproj import Geod
from shapely.geometry import mapping
from .geo import rasterize
from .osm import parse
from .schematic import export


def write_json(path, data):
    """Write readable UTF-8 JSON, preserving non-ASCII source names."""
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def preview(grid, buildings, path, source_kind):
    """Draw numbered footprint cells with a scale bar and source attribution; no terrain is implied."""
    size = grid.shape[0]
    scale = max(1, min(3, 1024 // size))
    palette = [
        (187, 111, 82),
        (93, 143, 161),
        (170, 142, 77),
        (123, 137, 102),
        (138, 120, 160),
    ]
    rgb = np.full((size, size, 3), (230, 236, 223), dtype=np.uint8)
    for b in buildings:
        rgb[grid == b["index"]] = palette[(b["index"] - 1) % len(palette)]
    map_img = Image.fromarray(rgb).resize(
        (size * scale, size * scale), Image.Resampling.NEAREST
    )
    side = 420
    img = Image.new(
        "RGB",
        (size * scale + side + 64, max(size * scale + 165, 200 + len(buildings) * 39)),
        (246, 245, 240),
    )
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=16)
    small = ImageFont.load_default(size=13)
    title = ImageFont.load_default(size=27)
    d.text((24, 18), "CMUcraft / Week 01", font=title, fill="#22372f")
    d.text(
        (24, 55),
        f"{size} x {size} m | 1 block = 1 m | EPSG:32617 | {source_kind}",
        font=font,
        fill="#394d44",
    )
    img.paste(map_img, (24, 92))
    for tick in range(0, size + 1, 32):
        p = 24 + tick * scale
        q = 92 + tick * scale
        d.line((p, 92, p, 92 + size * scale), fill="#c8d3c1", width=1)
        d.line((24, q, 24 + size * scale, q), fill="#c8d3c1", width=1)
    for b in buildings:
        x, z = b["label_xz"]
        px, py = 24 + x * scale, 92 + z * scale
        label = str(b["index"])
        bounds = d.textbbox((0, 0), label, font=font)
        w = bounds[2] + 8
        d.rectangle((px - 3, py - 2, px + w, py + 20), fill="#fffdf4")
        d.text((px, py), label, font=font, fill="#182a22")
    left = size * scale + 50
    d.text((left, 94), "NORTH up / -Z    EAST right / +X", font=font, fill="#22372f")
    d.text((left, 124), "Numbered OSM building footprints", font=font, fill="#22372f")
    for i, b in enumerate(buildings):
        y = 159 + i * 39
        name = b["name"] or b["osm_id"]
        d.text((left, y), f"{b['index']:02d}  {name}", font=small, fill="#22372f")
        d.text(
            (left, y + 16),
            f"{b['cells']} cells" + (" / clipped at edge" if b["clipped"] else ""),
            font=small,
            fill="#68766a",
        )
    bottom = 100 + size * scale
    d.line((24, bottom, 24 + 32 * scale, bottom), fill="#22372f", width=4)
    d.text((24, bottom + 8), "32 m", font=small, fill="#22372f")
    d.text(
        (170, bottom + 8),
        "Background is schematic; no terrain or roads surveyed.",
        font=small,
        fill="#536457",
    )
    d.text(
        (24, bottom + 30),
        "© OpenStreetMap contributors | ODbL 1.0 | Heights are not modelled",
        font=small,
        fill="#536457",
    )
    img.save(path)


def build(source, output, region):
    """Validate source provenance, rasterize buildings, and export survey evidence.

    Returns a report of overlap, clipping and independent geodesic distance checks.
    Overlapping cells use stable first-feature ownership, disclosed in each record."""
    source, output = Path(source), Path(output)
    provenance_path = source.with_suffix(".source.json")
    if not provenance_path.exists():
        raise ValueError(
            "Missing .source.json provenance; explicitly label real_osm or synthetic_fixture"
        )
    # A plausible-looking geometry file is not enough; its recorded source must match.
    provenance = json.loads(provenance_path.read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if provenance.get("sha256") != digest:
        raise ValueError("Source SHA256 does not match provenance")
    if provenance.get("source_kind") not in ("real_osm", "synthetic_fixture"):
        raise ValueError("Unrecognized source_kind")
    bbox = provenance.get("bbox_wgs84")
    if bbox:
        corners = [
            region.lonlat(x, z) for x in (0, region.size) for z in (0, region.size)
        ]
        if any(
            not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3])
            for lon, lat in corners
        ):
            raise ValueError(
                "Region exceeds downloaded bbox; download data for the new region first"
            )
    features, warnings = parse(source)
    output.mkdir(parents=True, exist_ok=True)
    grid = np.zeros((region.size, region.size), dtype=np.uint16)
    buildings = []
    geo_features = []
    locals_ = []
    all_masks = []
    for f in features:
        full = region.local_geometry(f["geometry"])
        clipped = full.intersection(region.extent)
        if clipped.is_empty or clipped.area < 1e-8:
            continue
        mask = rasterize(clipped, region.size)
        idx = len(buildings) + 1
        overlap = int(np.count_nonzero(mask & (grid > 0)))
        # OSM may map overlapping parent complexes/child buildings. Keep all vectors;
        # assign cells to first feature by stable OSM ID ordering and disclose overlaps.
        assigned = mask & (grid == 0)
        grid[assigned] = idx
        point = clipped.representative_point()
        # Use the full footprint centroid, not the clipped part at the extent edge.
        centroid = full.centroid
        b = {
            "index": idx,
            "osm_id": f["id"],
            "name": f["tags"].get("name", ""),
            "clipped": not region.extent.covers(full),
            "full_area_m2": full.area,
            "visible_area_m2": clipped.area,
            "cells": int(assigned.sum()),
            "raw_mask_cells": int(mask.sum()),
            "overlap_cells": overlap,
            "label_xz": [point.x, point.y],
            "full_centroid_xz": [centroid.x, centroid.y],
            "full_centroid_lonlat": region.lonlat(centroid.x, centroid.y),
            "tags": f["tags"],
        }
        buildings.append(b)
        all_masks.append(mask)
        geo_features.append(
            {
                "type": "Feature",
                "id": f["id"],
                "properties": b,
                "geometry": mapping(region.geographic_geometry(clipped)),
            }
        )
        locals_.append({"osm_id": f["id"], "geometry_xz_metres": mapping(clipped)})
    if not buildings:
        raise ValueError("No buildings in region; check source coverage and centre")
    distances = []
    geod = Geod(ellps="WGS84")
    for a, b in itertools.combinations(buildings, 2):
        p, q = a["full_centroid_xz"], b["full_centroid_xz"]
        projected = float(np.linalg.norm(np.subtract(p, q)))
        # Ellipsoidal distance is an independent reference for projected scale error.
        _, _, geodesic = geod.inv(
            *a["full_centroid_lonlat"], *b["full_centroid_lonlat"]
        )
        if geodesic < 1e-8:
            continue
        # Integer cell centres containing each original full-footprint centroid.
        raster_distance = float(np.linalg.norm(np.floor(p) - np.floor(q)))
        distances.append(
            {
                "from": a["osm_id"],
                "to": b["osm_id"],
                "from_name": a["name"],
                "to_name": b["name"],
                "geodesic_m": geodesic,
                "minecraft_float_m": projected,
                "centroid_cell_distance_m": raster_distance,
                "projection_error_m": abs(projected - geodesic),
                "quantization_error_m": abs(raster_distance - projected),
                "relative_projection_error": abs(projected - geodesic) / geodesic,
            }
        )
    np.save(output / "grid.npy", grid, allow_pickle=False)
    with (output / "cells.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x", "z", "building_index"])
        for z, x in zip(*np.nonzero(grid)):
            writer.writerow([int(x), int(z), int(grid[z, x])])
    with (output / "distances.csv").open("w", newline="") as handle:
        if distances:
            writer = csv.DictWriter(handle, fieldnames=list(distances[0]))
            writer.writeheader()
            writer.writerows(distances)
    write_json(
        output / "buildings.geojson",
        {"type": "FeatureCollection", "features": geo_features},
    )
    # Deliberately JSON, not mislabeled RFC7946 GeoJSON with metre coordinates.
    write_json(
        output / "local_geometry.json",
        {"axes": "Minecraft X east / Z south, metres", "buildings": locals_},
    )
    write_json(output / "buildings.json", buildings)
    preview(grid, buildings, output / "campus.png", provenance["source_kind"])
    export(grid, output / "cmu_core.schem")
    report = {
        "source": provenance,
        "region": {
            "center_lon": region.lon,
            "center_lat": region.lat,
            "size_m": region.size,
            "crs": "EPSG:32617",
            "origin_utm_west_north": region.origin,
            "xz_formula": "X=E-west; Z=north-N",
            "cell_rule": "strict interior at (x+0.5,z+0.5)",
        },
        "building_count": len(buildings),
        "occupied_cells": int(np.count_nonzero(grid)),
        "clipped_count": sum(b["clipped"] for b in buildings),
        "overlap_cells_sum": sum(b["overlap_cells"] for b in buildings),
        "parse_warnings": warnings,
        "distance_pair_count": len(distances),
        "max_projection_error_m": max(
            (d["projection_error_m"] for d in distances), default=0
        ),
        "max_relative_projection_error": max(
            (d["relative_projection_error"] for d in distances), default=0
        ),
        "max_centroid_quantization_error_m": max(
            (d["quantization_error_m"] for d in distances), default=0
        ),
        "limitations": [
            "OSM positional accuracy is not independently surveyed",
            "Distances validate projection scale, not accuracy of source survey",
            "Grid north differs slightly from true north (UTM convergence)",
            "Flat ground and one-block footprint height are placeholders",
            "No real terrain, roads, facades, interiors or in-game verification",
        ],
    }
    write_json(output / "report.json", report)
    return report
