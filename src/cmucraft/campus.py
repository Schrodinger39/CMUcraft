"""Legacy campus generator, retained for diagnostics only.
Arrays use [y, z, x]. Heights, facade patterns, foundations and bridge decks
include estimates; this module must not be used as an approved reconstruction."""

import argparse
import hashlib
import json
import math
import shutil
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Polygon
from .geo import Region, rasterize
from .osm import parse
from .build import write_json
from .world import write_world

REGION = Region(-79.9428, 40.4433, 1024)
STATES = [
    "air",
    "bedrock",
    "stone",
    "dirt",
    "grass_block[snowy=false]",
    "gray_concrete",
    "smooth_stone",
    "sandstone",
    "smooth_sandstone",
    "bricks",
    "quartz_block",
    "white_concrete",
    "light_gray_concrete",
    "stone_bricks",
    "dark_prismarine",
    "black_stained_glass",
    "glass",
    "oak_planks",
    "oak_log[axis=y]",
    "oak_leaves[distance=1,persistent=true]",
    "water[level=0]",
    "green_concrete",
    "red_concrete",
    "white_wool",
    "oak_fence[east=true,north=true,south=true,waterlogged=false,west=true]",
    "glowstone",
    "ladder[facing=north,waterlogged=false]",
    "oak_sign[rotation=0,waterlogged=false]",
    "yellow_concrete",
]
PALETTE = ["minecraft:" + x for x in STATES]
ID = {v: i for i, v in enumerate(STATES)}
COLORS = [
    (0, 0, 0),
    (60, 60, 60),
    (119, 119, 115),
    (127, 92, 64),
    (108, 143, 72),
    (83, 86, 87),
    (160, 159, 151),
    (203, 184, 136),
    (207, 194, 155),
    (157, 86, 66),
    (221, 217, 201),
    (217, 218, 213),
    (155, 158, 151),
    (133, 133, 126),
    (55, 102, 95),
    (58, 76, 85),
    (117, 170, 183),
    (161, 125, 78),
    (96, 72, 41),
    (57, 109, 54),
    (53, 127, 167),
    (62, 122, 66),
    (151, 66, 52),
    (236, 233, 215),
    (168, 71, 59),
    (237, 202, 112),
    (132, 98, 64),
    (164, 133, 87),
    (230, 196, 65),
]


def erode(mask):
    """Keep mask cells with four occupied neighbors; the removed ring becomes a one-cell wall."""
    padded = np.pad(mask, 1)
    return (
        mask
        & padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )


def verified(path):
    """Load the source sidecar and reject bytes that do not match its recorded hash."""
    meta = json.loads(path.with_suffix(".source.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError(f"Checksum mismatch: {path.name}")
    return meta


def terrain(path, region):
    """Check DEM registration and return block heights, metre elevations, offset and metadata.

    The constant offset puts the lowest terrain near Y=40. Bilinear interpolation
    resamples the source raster; it does not establish one-metre source accuracy."""
    meta = verified(path)
    im = Image.open(path)
    tie = im.tag_v2[33922]
    spacing = im.tag_v2[33550]
    west, north = region.origin
    if not np.allclose((tie[3], tie[4]), (west, north), atol=1e-5, rtol=0):
        raise ValueError("DEM origin does not match campus origin")
    if not np.allclose(
        (im.width * spacing[0], im.height * spacing[1]), (region.size, region.size)
    ):
        raise ValueError("DEM extent mismatch")
    elevation = np.array(
        im.resize((region.size, region.size), Image.Resampling.BILINEAR)
    )
    if (
        not np.isfinite(elevation).all()
        or elevation.min() < 100
        or elevation.max() > 500
    ):
        raise ValueError("Invalid elevation or no-data values")
    offset = math.floor(float(elevation.min())) - 40
    return np.rint(elevation - offset).astype(np.int16), elevation, offset, meta


def osm_details(path, region):
    """Extract roads, mapped trees and entrance points in local campus metres."""
    root = ET.parse(path).getroot()
    tags = lambda e: {t.attrib["k"]: t.attrib["v"] for t in e.findall("tag")}
    nodes = {e.attrib["id"]: e for e in root.findall("node")}
    xy = {
        i: region.xz(float(e.attrib["lon"]), float(e.attrib["lat"]))
        for i, e in nodes.items()
    }
    ways = []
    trees = []
    entrances = []
    for i, e in nodes.items():
        x, z = xy[i]
        t = tags(e)
        if not (0 <= x < region.size and 0 <= z < region.size):
            continue
        if t.get("natural") == "tree":
            trees.append((round(x), round(z)))
        if t.get("entrance") and t["entrance"] != "no":
            entrances.append((x, z))
    for e in root.findall("way"):
        t = tags(e)
        if not any(
            k in t
            for k in ("highway", "landuse", "leisure", "natural", "water", "barrier")
        ):
            continue
        try:
            coords = [xy[p.attrib["ref"]] for p in e.findall("nd")]
        except KeyError:
            continue
        if len(coords) < 2:
            continue
        ways.append((e.attrib["id"], coords, t))
    return ways, trees, entrances


def build_campus(root, output, allow_approximate=False):
    """Generate the explicitly opted-in legacy approximation in a new output directory.

    Road widths, floor heights, facade rhythms, foundations and bridge decks
    include estimates. Returns a manifest that records these limitations."""
    if not allow_approximate:
        raise ValueError(
            "Legacy procedural architecture is not an approved reconstruction; explicitly enable --legacy-approximation for diagnostics"
        )
    root, output = Path(root), Path(output)
    region = REGION
    size = region.size
    if (output / "world" / "level.dat").exists():
        raise ValueError("Choose an empty output directory; world already exists")
    output.mkdir(parents=True, exist_ok=True)
    ground, elevation, offset, dem_meta = terrain(root / "data/raw/terrain.tif", region)
    osm_meta = verified(root / "data/raw/campus.osm")
    features, warnings = parse(root / "data/raw/campus.osm")
    if warnings:
        raise ValueError("OSM parse warnings: " + str(warnings))
    ways, trees, entrances = osm_details(root / "data/raw/campus.osm", region)
    profiles = json.loads((root / "data/reference/building_profiles.json").read_text())
    surface = np.full((size, size), ID["grass_block[snowy=false]"], dtype=np.uint8)
    road = np.zeros((size, size), dtype=bool)
    linear = []
    landmarks = []
    # Fallback widths are legacy estimates; an explicit OSM width overrides them.
    widths = {
        "primary": 10,
        "secondary": 9,
        "tertiary": 8,
        "residential": 6,
        "service": 4,
        "footway": 2,
        "path": 2,
        "pedestrian": 5,
        "steps": 2,
        "cycleway": 2,
        "living_street": 5,
        "unclassified": 6,
    }
    for wid, coords, t in ways:
        if coords[0] == coords[-1] and len(coords) >= 4:
            poly = Polygon(coords)
            if poly.is_valid:
                material = None
                if t.get("natural") == "water" or "water" in t:
                    material = "water[level=0]"
                elif t.get("leisure") in ("pitch", "track"):
                    material = (
                        "green_concrete" if t["leisure"] == "pitch" else "red_concrete"
                    )
                if material:
                    mask = rasterize(poly, size)
                    surface[mask] = ID[material]
                    if material == "green_concrete":
                        border = mask & ~erode(mask)
                        surface[border] = ID["white_wool"]
        if t.get("highway") in widths:
            width = widths[t["highway"]]
            try:
                width = float(t.get("width", width))
            except ValueError:
                pass
            width = min(20, max(1, width))
            line = LineString(coords)
            mask = rasterize(line.buffer(width / 2), size)
            if not mask.any():
                continue
            elevated = t.get("bridge") == "yes"
            if not elevated:
                surface[mask] = ID[
                    (
                        "smooth_stone"
                        if t["highway"]
                        in ("footway", "path", "steps", "pedestrian", "cycleway")
                        else "gray_concrete"
                    )
                ]
                road |= mask
            linear.append(
                {
                    "osm_id": "way/" + wid,
                    "name": t.get("name", ""),
                    "width_m": width,
                    "width_source": "osm" if "width" in t else "class estimate",
                    "bridge": elevated,
                    "coords": coords,
                }
            )
        if t.get("name") == "The Fence":
            landmarks.append(("The Fence", coords))
    # 192 vertical blocks is sufficient for this DEM and the explicitly estimated roofs.
    volume = np.zeros((192, size, size), dtype=np.uint8)
    zz, xx = np.indices((size, size))
    for y in range(int(ground.max()) + 1):
        volume[y] = np.where(
            y < ground - 3, ID["stone"], np.where(y < ground, ID["dirt"], 0)
        )
    volume[0] = ID["bedrock"]
    volume[ground, zz, xx] = surface
    buildings = []
    occupancy = np.zeros((size, size), dtype=np.uint16)
    signs = []
    destinations = []
    for feature in features:
        geom = region.local_geometry(feature["geometry"]).intersection(region.extent)
        mask = rasterize(geom, size)
        if not mask.any():
            continue
        mask &= occupancy == 0
        if not mask.any():
            continue
        z, x = np.nonzero(mask)
        z0, z1 = int(z.min()), int(z.max() + 1)
        x0, x1 = int(x.min()), int(x.max() + 1)
        local = mask[z0:z1, x0:x1]
        inside = erode(local)
        wall = local & ~inside
        idx = len(buildings) + 1
        occupancy[mask] = idx
        t = feature["tags"]
        name = t.get("name", "")
        profile = profiles["profiles"].get(name)
        material = (
            "bricks"
            if t.get("building") in ("house", "apartments", "dormitory", "residential")
            else "sandstone"
        )
        roof = t.get("roof:shape", "flat")
        raw_levels = t.get("building:levels")
        basis = "generic estimate"
        floors = 3 if material == "bricks" else 4
        if raw_levels:
            try:
                floors = max(1, min(12, int(float(raw_levels))))
                basis = "OSM levels; storey height estimated"
            except ValueError:
                pass
        if profile:
            raw_levels, floors, material, roof = profile
            basis = "CMU 2022 inventory; model height estimated"
        # Legacy heuristic only: storey count is not a measured roof elevation.
        height = round(floors * 3.5)
        if t.get("height"):
            try:
                height = round(float(t["height"].replace(" m", "")))
                basis = "OSM height"
            except ValueError:
                pass
        height = max(4, min(60, height))
        # This flattens the foundation and is a known limitation on hillside buildings.
        base = int(np.percentile(ground[mask], 55))
        top = base + height
        if top + 8 >= 192:
            raise ValueError("Model exceeds vertical range")
        sub = volume[:, z0:z1, x0:x1]
        # Foundations and hollow interiors; no claim of real floor plans.
        for y in range(int(ground[mask].min()), base + 1):
            sub[y, local] = ID["stone_bricks"]
        for y in range(base + 1, top):
            sub[y, local] = 0
        sub[base, local] = ID["oak_planks"]
        wz, wx = np.nonzero(wall)
        for y in range(base + 1, top):
            sub[y, wall] = ID[material]
            if (y - base) % 4 in (2, 3):
                windows = (wx + x0 + wz + z0) % 5 < 3
                sub[y, wz[windows], wx[windows]] = ID["black_stained_glass"]
            if (y - base) % 4 == 0:
                sub[y, inside] = ID["oak_planks"]
                sub[y, wall] = ID[
                    "smooth_sandstone" if material == "sandstone" else "smooth_stone"
                ]
        for light_y in range(base + 4, top, 4):
            for light_z in range(3, local.shape[0], 8):
                for light_x in range(3, local.shape[1], 8):
                    if inside[light_z, light_x]:
                        sub[light_y, light_z, light_x] = ID["glowstone"]
        sub[top, local] = ID["smooth_stone"]
        if roof in ("pitched", "gabled", "hipped"):
            roofmask = local.copy()
            for dy in range(1, 6):
                roofmask = erode(roofmask)
                if not roofmask.any():
                    break
                sub[top + dy, roofmask] = ID["dark_prismarine"]
        # Actual OSM entrance when available; otherwise an explicitly inferred facade opening.
        edge_x = wx + x0
        edge_z = wz + z0
        nearby = [
            p
            for p in entrances
            if geom.distance(__import__("shapely").geometry.Point(*p)) < 2
        ]
        if nearby:
            target = nearby[0]
            j = int(np.argmin((edge_x - target[0]) ** 2 + (edge_z - target[1]) ** 2))
            entry_source = "OSM entrance"
        else:
            # Pick a boundary location near the centre and with low elevation discrepancy.
            cx, cz = geom.centroid.coords[0]
            j = int(
                np.argmin(
                    (ground[edge_z, edge_x] - base) ** 2 * 20
                    + ((edge_x - cx) ** 2 + (edge_z - cz) ** 2) * 0.01
                )
            )
            entry_source = "inferred opening"
        ex, ez = int(edge_x[j]), int(edge_z[j])
        volume[
            base + 1 : base + 4, max(0, ez - 1) : ez + 2, max(0, ex - 1) : ex + 2
        ] = 0
        volume[base, max(0, ez - 1) : ez + 2, max(0, ex - 1) : ex + 2] = ID[
            "smooth_stone"
        ]
        # Indoor ladder beside a solid support column makes placeholder floors explorable.
        candidates = np.argwhere(inside)
        if len(candidates):
            iz, ix = map(int, candidates[len(candidates) // 2])
            gx, gz = x0 + ix, z0 + iz
            if iz + 1 < local.shape[0] and local[iz + 1, ix]:
                volume[base + 1 : top + 1, gz + 1, gx] = ID[material]
                volume[base + 1 : top + 1, gz, gx] = ID[
                    "ladder[facing=north,waterlogged=false]"
                ]
                volume[base + 1 : top + 1, gz, max(0, gx - 1)] = 0
        record = {
            "osm_id": feature["id"],
            "name": name,
            "model_base_y": base,
            "model_height_m": height,
            "height_basis": basis,
            "inventory_levels_raw": raw_levels,
            "material": material,
            "roof": roof,
            "entrance_source": entry_source,
            "entrance_xyz": [ex, base + 1, ez],
            "clipped": not region.extent.covers(
                region.local_geometry(feature["geometry"])
            ),
            "footprint_cells": int(mask.sum()),
            "interior": "procedural open floors and ladder, not real floor plan",
        }
        buildings.append(record)
        if name:
            destinations.append(
                {
                    "name": name,
                    "x": ex,
                    "y": top + 8,
                    "z": ez,
                    "command": f"/tp @s {ex} {top+8} {ez}",
                }
            )
            sx, sz = ex, min(size - 1, ez + 2)
            sy = base + 1
            volume[sy, sz, sx] = ID["oak_sign[rotation=0,waterlogged=false]"]
            lines = textwrap.wrap(name, 20)[:3] + ["Approx. model"]
            signs.append((sx, sy, sz, lines))
    # Elevated OSM walkways; endpoint height is sampled from the DEM.
    bridge_count = 0
    for way in linear:
        if not way["bridge"]:
            continue
        coords = way["coords"]
        mask = rasterize(LineString(coords).buffer(way["width_m"] / 2), size)
        endpoints = [
            (min(size - 1, max(0, round(x))), min(size - 1, max(0, round(z))))
            for x, z in (coords[0], coords[-1])
        ]
        # Legacy deck estimate; it is not a surveyed bridge connection height.
        deck = max(int(ground[z, x]) for x, z in endpoints) + 4
        z, x = np.nonzero(mask)
        if len(x) == 0:
            continue
        volume[deck, z, x] = ID["smooth_stone"]
        volume[deck + 1 : deck + 4, z, x] = 0
        border = mask & ~erode(mask)
        bz, bx = np.nonzero(border)
        volume[deck + 1, bz, bx] = ID["glass"]
        bridge_count += 1
    # Only OSM-mapped individual trees are placed, with explicitly generic crowns.
    tree_count = 0
    for x, z in trees:
        if (
            not (3 <= x < size - 3 and 3 <= z < size - 3)
            or occupancy[z, x]
            or road[z, x]
        ):
            continue
        y = int(ground[z, x])
        volume[y + 1 : y + 6, z, x] = ID["oak_log[axis=y]"]
        for dy, radius in [(4, 2), (5, 3), (6, 2), (7, 1)]:
            for dz in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if (
                        dx * dx + dz * dz <= radius * radius
                        and volume[y + dy, z + dz, x + dx] == 0
                    ):
                        volume[y + dy, z + dz, x + dx] = ID[
                            "oak_leaves[distance=1,persistent=true]"
                        ]
        tree_count += 1
    for name, coords in landmarks:
        mask = rasterize(LineString(coords).buffer(0.6), size)
        z, x = np.nonzero(mask)
        volume[ground[z, x] + 1, z, x] = ID["red_concrete"]
    # Spawn on The Cut; move to nearby unoccupied grass if necessary.
    sx, sz = map(round, region.xz(-79.94325, 40.44250))
    for dz in range(-12, 13):
        if (
            occupancy[sz + dz, sx] == 0
            and volume[int(ground[sz + dz, sx]) + 1, sz + dz, sx] == 0
        ):
            sz += dz
            break
    spawn = [sx, int(ground[sz, sx]) + 2, sz]
    signs.append(
        (
            sx + 3,
            spawn[1] - 1,
            sz,
            ["CMUcraft", "Chris Yu", "OSM + USGS", "Approx. facades"],
        )
    )
    volume[spawn[1] - 1, sz, sx + 3] = ID["oak_sign[rotation=0,waterlogged=false]"]
    print(
        f"Writing world: {len(buildings)} buildings, {len(linear)} routes, {tree_count} trees",
        flush=True,
    )
    chunks = write_world(volume, PALETTE, output / "world", spawn, signs)
    np.save(output / "ground.npy", ground)
    np.save(output / "building_grid.npy", occupancy)
    write_json(output / "buildings.json", buildings)
    write_json(output / "destinations.json", destinations)
    write_json(output / "routes.json", linear)
    # CPU render of actual exported block surfaces, not an AI-generated mockup.
    render(volume, ground, output, buildings)
    summary = {
        "region": {
            "lon": region.lon,
            "lat": region.lat,
            "size_m": size,
            "utm_origin": region.origin,
        },
        "source_osm": osm_meta,
        "source_dem": dem_meta,
        "vertical_offset_m": offset,
        "elevation_range_m": [float(elevation.min()), float(elevation.max())],
        "buildings": len(buildings),
        "routes": len(linear),
        "bridges": bridge_count,
        "trees": tree_count,
        "chunks": chunks,
        "spawn": spawn,
        "game_version": "Java 1.16.5",
        "contributor": "Chris Yu",
        "limitations": [
            "4m service-resampled DEM interpolated to 1m; building foundations flattened",
            "Campus inventory is historical (2022), not current architectural drawings",
            "Heights derived from storeys are estimates; facades, roofs, floors and ladders are procedural",
            "Bridge deck elevations, road widths without OSM tags, and inferred entrances are approximate",
            "1024m square covers central campus and nearby residences, not every off-campus CMU property",
        ],
    }
    write_json(output / "manifest.json", summary)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in ("buildings", "routes", "bridges", "trees", "chunks", "spawn")
            },
            indent=2,
        )
    )
    return summary


def render(volume, ground, output, buildings):
    """Draw overview and isometric views from exported block IDs, not photographs."""
    size = ground.shape[0]
    height = volume.shape[0]
    tops = height - 1 - np.argmax(volume[::-1] != 0, axis=0)
    z, x = np.indices((size, size))
    ids = volume[tops, z, x]
    colors = np.array(COLORS, dtype=np.uint8)[ids]
    dz, dx = np.gradient(tops.astype(float))
    shade = np.clip(0.90 + 0.07 * dx - 0.09 * dz, 0.55, 1.15)
    rgb = np.clip(colors * shade[:, :, None], 0, 255).astype(np.uint8)
    overview = Image.new("RGB", (size, size + 95), "#f6f4ec")
    overview.paste(Image.fromarray(rgb), (0, 70))
    d = ImageDraw.Draw(overview)
    font = ImageFont.load_default(size=20)
    d.text((20, 12), "CMUcraft | 1024 x 1024 metres | N up", font=font, fill="#20382e")
    d.text(
        (20, 40),
        "Real OSM layout + USGS terrain | Approximate building heights and facades",
        font=ImageFont.load_default(size=15),
        fill="#465e50",
    )
    d.text(
        (20, size + 73),
        "© OpenStreetMap contributors / ODbL | USGS 3DEP | Contributor: Chris Yu",
        font=ImageFont.load_default(size=13),
        fill="#465e50",
    )
    overview.save(output / "campus_overview.png")
    # Isometric cropped campus core, rendered from voxel column heights.
    a, b, c, d0 = 180, 260, 800, 900
    image = Image.new("RGB", (1500, 1150), "#dce8ed")
    draw = ImageDraw.Draw(image)
    scale = 1.08
    for z0 in range(b, d0):
        for x0 in range(a, c):
            h = int(tops[z0, x0])
            color = tuple(map(int, colors[z0, x0]))
            px = 750 + (x0 - a - (z0 - b)) * scale
            py = 350 + (x0 - a + z0 - b) * scale * 0.47 - (h - 40) * 2.5
            # Visible column sides to neighboring surface; draw only exposed walls.
            for nx, nz, poly, shade_factor in [
                (x0 + 1, z0, [(px, py), (px + scale, py + scale * 0.47)], 0.72),
                (x0, z0 + 1, [(px, py), (px - scale, py + scale * 0.47)], 0.85),
            ]:
                lower = int(tops[nz, nx])
                if lower < h:
                    for yy in range(lower + 1, h + 1):
                        drop = (h - yy) * 2.5
                        block_color = COLORS[int(volume[yy, z0, x0])]
                        if volume[yy, z0, x0] == 0:
                            continue
                        draw.polygon(
                            [
                                (poly[0][0], poly[0][1] + drop),
                                (poly[1][0], poly[1][1] + drop),
                                (poly[1][0], poly[1][1] + drop + 2.5),
                                (poly[0][0], poly[0][1] + drop + 2.5),
                            ],
                            fill=tuple(int(v * shade_factor) for v in block_color),
                        )
            draw.polygon(
                [
                    (px, py - scale * 0.47),
                    (px + scale, py),
                    (px, py + scale * 0.47),
                    (px - scale, py),
                ],
                fill=color,
            )
    draw.rectangle((0, 0, 1500, 85), fill="#f6f4ec")
    draw.text(
        (28, 17),
        "CMUcraft / Pittsburgh campus",
        font=ImageFont.load_default(size=29),
        fill="#21382e",
    )
    draw.text(
        (28, 55),
        "Rendered from exported blocks. Real layout and terrain; architecture is approximate.",
        font=ImageFont.load_default(size=18),
        fill="#4d6255",
    )
    draw.rectangle((0, 1110, 1500, 1150), fill="#f6f4ec")
    draw.text(
        (28, 1120),
        "© OpenStreetMap contributors | USGS 3DEP | Contributor: Chris Yu",
        font=ImageFont.load_default(size=16),
        fill="#4d6255",
    )
    image.save(output / "campus_isometric.png")


def main():
    """Require the explicit legacy flag before dispatching the campus generator."""
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--output", type=Path, default=Path("campus_artifacts"))
    p.add_argument(
        "--legacy-approximation",
        action="store_true",
        help="Explicitly generate the rejected approximate model for diagnostics only",
    )
    args = p.parse_args()
    build_campus(args.root, args.output, args.legacy_approximation)


if __name__ == "__main__":
    main()
