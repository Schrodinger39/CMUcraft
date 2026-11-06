"""Compare exported building-ID cells against the same OSM input.
This catches export displacement or missing cells, not source survey error."""

import argparse, json
from pathlib import Path
import numpy as np
from .osm import parse
from .campus import REGION
from .geo import rasterize


def compare(source, buildings, grid, region=REGION):
    """Count source cells missing from each exported building and cells outside its source mask."""
    features, warnings = parse(source)
    if warnings:
        raise ValueError(str(warnings))
    lookup = {f["id"]: f for f in features}
    if grid.shape != (region.size, region.size):
        raise ValueError("Grid and region differ")
    if int(grid.max()) > len(buildings):
        raise ValueError("Unknown building grid identifier")
    rows = []
    for i, b in enumerate(buildings, 1):
        geom = region.local_geometry(lookup[b["osm_id"]]["geometry"]).intersection(
            region.extent
        )
        expected = rasterize(geom, region.size)
        actual = grid == i
        missing = int((expected & ~actual).sum())
        outside = int((actual & ~expected).sum())
        rows.append(
            {
                "osm_id": b["osm_id"],
                "name": b["name"],
                "source_cells": int(expected.sum()),
                "export_cells": int(actual.sum()),
                "missing_source_cells": missing,
                "outside_source_cells": outside,
                "exact_raster_match": missing == 0 and outside == 0,
                "real_world_location_verified": False,
            }
        )
    return {
        "method": "Legacy exported ID grid versus the same OSM snapshot; centre-in-cell rasterization",
        "limits": "Checks export placement only, not source accuracy, building identity, elevations or actual final roof blocks.",
        "buildings": rows,
        "exact_matches": sum(r["exact_raster_match"] for r in rows),
        "buildings_with_source_loss": sum(r["missing_source_cells"] > 0 for r in rows),
        "buildings_outside_source": sum(r["outside_source_cells"] > 0 for r in rows),
    }


def main():
    """Read the legacy grid and building list, then save a placement-only audit."""
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="data/raw/campus.osm")
    p.add_argument("--artifacts", type=Path, default=Path("campus_artifacts"))
    p.add_argument(
        "--output", type=Path, default=Path("audit/legacy_export_positions.json")
    )
    a = p.parse_args()
    report = compare(
        a.source,
        json.loads((a.artifacts / "buildings.json").read_text()),
        np.load(a.artifacts / "building_grid.npy"),
    )
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print({k: v for k, v in report.items() if k != "buildings"})


if __name__ == "__main__":
    main()
