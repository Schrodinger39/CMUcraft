"""Extract measured surface evidence from LAZ files.
Class 2 is ground; class 1 is used only with explicit opt-in and can include
vegetation. Source horizontal CRS and vertical units are separate checks.
Missing observations remain NaN; metre conversion is not a vertical-datum shift."""

import argparse, hashlib, json
from pathlib import Path
import numpy as np
from pyproj import CRS, Transformer
from shapely import contains_xy
from shapely.geometry import shape
from .campus import REGION


def sha256_file(path):
    """Hash a file in bounded chunks, without loading the whole survey into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cell_quantile(x, z, height, size, quantile=0.5):
    """Aggregate only observed cells; missing cells remain NaN, never invented heights."""
    if not 0 <= quantile <= 1:
        raise ValueError("Invalid quantile")
    x, z, height = map(np.asarray, (x, z, height))
    if not (x.shape == z.shape == height.shape):
        raise ValueError("Point shapes differ")
    valid = (
        np.isfinite(x)
        & np.isfinite(z)
        & np.isfinite(height)
        & (x >= 0)
        & (z >= 0)
        & (x < size)
        & (z < size)
    )
    # Collapse each [z,x] cell into a sortable one-dimensional cell ID.
    indices = np.floor(z[valid]).astype(np.int64) * size + np.floor(x[valid]).astype(
        np.int64
    )
    height = height[valid]
    result = np.full(size * size, np.nan, dtype=np.float32)
    counts = np.zeros(size * size, dtype=np.uint32)
    if len(indices):
        # Last key wins: group by cell, then sort heights within each group.
        order = np.lexsort((height, indices))
        indices = indices[order]
        height = height[order]
        # Locate the sorted slice and observation count belonging to each occupied cell.
        ids, starts, n = np.unique(indices, return_index=True, return_counts=True)
        # Interpolate the quantile between the two neighboring ranks in each slice.
        q = (n - 1) * quantile
        lo = np.floor(q).astype(int)
        hi = np.ceil(q).astype(int)
        result[ids] = height[starts + lo] * (1 - (q - lo)) + height[starts + hi] * (
            q - lo
        )
        counts[ids] = n
    return result.reshape(size, size), counts.reshape(size, size)


def vertical_factor(header_crs, explicit_unit=None):
    """Never infer vertical units from horizontal coordinates or height magnitude."""
    units = {"metres": 1.0, "us-survey-feet": 1200 / 3937}
    # Only an explicit vertical axis supplies vertical units; XY units are insufficient.
    axis = (
        None
        if header_crs is None
        else next((a for a in header_crs.axis_info if a.direction == "up"), None)
    )
    if explicit_unit is not None and explicit_unit not in units:
        raise ValueError("Unsupported elevation unit")
    if axis is not None:
        factor = axis.unit_conversion_factor
        if explicit_unit is not None and not np.isclose(
            factor, units[explicit_unit], rtol=1e-9
        ):
            raise ValueError("Explicit elevation unit disagrees with LAS vertical CRS")
        return factor
    if explicit_unit is None:
        raise ValueError("Missing vertical CRS: supply verified elevation units")
    return units[explicit_unit]


def extract(
    files,
    output,
    source_crs,
    acquisition_interval,
    region=REGION,
    include_unclassified=False,
    elevation_unit=None,
):
    """Stream classified survey points, project X/Z and convert elevation units.

    Outputs retained points, observed-cell median rasters, counts and source hashes.
    Class-1 surfaces require opt-in; missing ground or roof classes fail explicitly."""
    import laspy

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    transformer = Transformer.from_crs(source_crs, "EPSG:32617", always_xy=True)
    west, north = region.origin
    parts = []
    sources = []
    hist = {}
    for path in map(Path, files):
        with laspy.open(path, laz_backend=laspy.LazBackend.Laszip) as reader:
            # Cross-check the file header with the caller-specified horizontal metadata.
            header_crs = reader.header.parse_crs()
            z_factor = vertical_factor(header_crs, elevation_unit)
            if header_crs is not None and not CRS.from_user_input(
                header_crs
            ).to_2d().equals(CRS.from_user_input(source_crs).to_2d()):
                raise ValueError("LAS header disagrees with explicit metadata CRS")
            total = 0
            kept = 0
            for pts in reader.chunk_iterator(500_000):
                total += len(pts)
                cls = np.asarray(pts.classification)
                unique, n = np.unique(cls, return_counts=True)
                for c, count in zip(unique, n):
                    hist[str(c)] = hist.get(str(c), 0) + int(count)
                # Discard withheld/noise classes; class 1 is a deliberate, flagged fallback.
                select = np.isin(
                    cls, [1, 2, 6] if include_unclassified else [2, 6]
                ) & ~np.asarray(pts.withheld, dtype=bool)
                if not select.any():
                    continue
                e, n = transformer.transform(
                    np.asarray(pts.x)[select], np.asarray(pts.y)[select]
                )
                x = e - west
                z = north - n
                # This converts units only; it does not transform the vertical datum.
                h = np.asarray(pts.z)[select] * z_factor
                c = cls[select]
                inside = (
                    (x >= 0)
                    & (z >= 0)
                    & (x < region.size)
                    & (z < region.size)
                    & np.isfinite(h)
                )
                if inside.any():
                    parts.append(
                        (
                            x[inside].astype("float32"),
                            z[inside].astype("float32"),
                            h[inside].astype("float32"),
                            c[inside].astype("uint8"),
                        )
                    )
                    kept += int(inside.sum())
            if total != reader.header.point_count:
                raise ValueError("Incomplete LAS stream")
            sources.append(
                {
                    "file": path.name,
                    "sha256": sha256_file(path),
                    "points": total,
                    "retained": kept,
                    "elevation_to_metres": z_factor,
                }
            )
        print(path.name, kept, "ground/building points retained", flush=True)
    if not parts:
        raise ValueError("No classified ground/building points in requested extent")
    x, z, h, c = [np.concatenate([p[i] for p in parts]) for i in range(4)]
    np.savez_compressed(
        output / "classified_points.npz", x=x, z=z, elevation=h, classification=c
    )
    for name, classification in [("ground", 2), ("roof", 6)]:
        # Class-1 candidates may contain trees; their raster name does not certify roofs.
        selected = (
            np.isin(c, [1, 6])
            if name == "roof" and include_unclassified
            else c == classification
        )
        if not selected.any():
            raise ValueError(
                "Missing class " + name + "; do not silently use vegetation"
            )
        raster, counts = cell_quantile(
            x[selected], z[selected], h[selected], region.size
        )
        np.save(output / (name + "_elevation.npy"), raster)
        np.save(output / (name + "_count.npy"), counts)
    meta = {
        "sources": sources,
        "source_crs": CRS.from_user_input(source_crs).to_string(),
        "output_crs": "EPSG:32617",
        "transformation": transformer.description,
        "horizontal_operation_accuracy_m": transformer.accuracy,
        "utm_origin": region.origin,
        "size_m": region.size,
        "vertical_datum": "NAVD88; output elevations in metres; input conversion recorded per tile",
        "acquisition_interval": acquisition_interval,
        "point_class_histogram": hist,
        "include_unclassified_surface_candidates": include_unclassified,
        "method": "Class 2 ground; class 6 building or explicitly enabled class 1 surface candidates; discard withheld; median in observed 1m cells",
        "limits": [
            "Missing cells remain NaN",
            "Historical observations cannot certify later building changes",
            "Unclassified surface candidates can include vegetation and must be checked within footprints",
            "Roof returns do not establish facade details or entrances",
            "Horizontal datum transformation accuracy is not survey accuracy",
        ],
    }
    (output / "source.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def building_report(
    points, records, output, acquisition_interval, include_unclassified=False
):
    """Compare inset building surface returns with surrounding classified ground.

    Percentiles expose different hillside levels; they do not certify one building
    height. Every generated row remains unapproved pending architectural review."""
    data = np.load(points)
    x, z, h, c = [data[k] for k in ("x", "z", "elevation", "classification")]
    rows = []
    for file in sorted(Path(records).glob("*.json")):
        record = json.loads(file.read_text())
        g = shape(record["footprint_xz"])
        a, b, cc, d = g.buffer(6).bounds
        select = (x >= a) & (x <= cc) & (z >= b) & (z <= d)
        xx, zz, hh, cl = x[select], z[select], h[select], c[select]
        # Inset avoids roof-edge mixing; surrounding ground exposes hillsides rather than flattening them.
        # Inset the outline to reduce mixed wall/roof returns near building edges.
        roof = hh[
            contains_xy(g.buffer(-1), xx, zz)
            & np.isin(cl, [1, 6] if include_unclassified else [6])
        ]
        # A surrounding ring captures differing ground elevations on a slope.
        ground = hh[contains_xy(g.buffer(6).difference(g), xx, zz) & (cl == 2)]
        row = {
            "name": record["name"],
            "osm_id": record["osm_id"],
            "roof_returns": len(roof),
            "ground_returns": len(ground),
            "method": "Inset surface candidates vs surrounding classified ground; no total-height certification",
            "acquisition_interval": acquisition_interval,
            "unclassified_surface_candidates": include_unclassified,
            "approved": False,
        }
        if len(roof) >= 30 and len(ground) >= 30:
            rp = np.percentile(roof, [5, 50, 95])
            gp = np.percentile(ground, [5, 50, 95])
            row.update(
                roof_elevation_p05_p50_p95_m=rp.tolist(),
                ground_elevation_p05_p50_p95_m=gp.tolist(),
                roof_p95_above_low_high_ground_m=[
                    float(rp[2] - gp[0]),
                    float(rp[2] - gp[2]),
                ],
                status="measured_evidence_requires_current_building_review",
            )
        else:
            row["status"] = "insufficient_classified_points"
        rows.append(row)
    Path(output).write_text(json.dumps(rows, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--source-crs", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--acquired-start", required=True)
    p.add_argument("--acquired-end", required=True)
    p.add_argument("--include-unclassified", action="store_true")
    p.add_argument("--elevation-unit", choices=["metres", "us-survey-feet"])
    a = p.parse_args()
    extract(
        a.files,
        a.output,
        a.source_crs,
        [a.acquired_start, a.acquired_end],
        include_unclassified=a.include_unclassified,
        elevation_unit=a.elevation_unit,
    )
