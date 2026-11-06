"""Compare OSM with an independent county footprint snapshot.
Merged complexes and historical changes can explain disagreements. Candidate
thresholds flag review work; the script never moves or approves a building."""

import argparse, csv, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape
from shapely.ops import unary_union
from .campus import REGION
from .osm import parse
from .build import write_json


def compare(source, county_file, output):
    """Compare overlapping county parts with each OSM polygon and export review candidates."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    features, warnings = parse(source)
    if warnings:
        raise ValueError(str(warnings))
    raw = json.loads(Path(county_file).read_text())
    if raw.get("exceededTransferLimit"):
        raise ValueError("Truncated county query; paginate before audit")
    county = [
        (f["properties"]["OBJECTID"], REGION.local_geometry(shape(f["geometry"])))
        for f in raw["features"]
    ]
    county = [(i, g) for i, g in county if g.is_valid and g.intersects(REGION.extent)]
    report = []
    polygons = []
    for f in features:
        geometry = REGION.local_geometry(f["geometry"])
        if (
            not geometry.intersects(REGION.extent)
            or geometry.intersection(REGION.extent).area < 1
        ):
            continue
        # Require meaningful overlap before grouping differently segmented county parts.
        candidates = [
            (i, g)
            for i, g in county
            if g.intersection(geometry).area > min(geometry.area, g.area) * 0.15
        ]
        if candidates:
            reference = unary_union([g for i, g in candidates])
            # A union handles footprint databases splitting a campus complex differently.
            overlap = geometry.intersection(reference).area
            iou = overlap / geometry.union(reference).area
            centre = geometry.centroid.distance(reference.centroid)
            hausdorff = geometry.hausdorff_distance(reference)
            # These numeric cutoffs only prioritize review; no location is auto-approved.
            status = (
                "agreement_candidate"
                if iou >= 0.80 and centre <= 3 and hausdorff <= 8
                else "needs_review"
            )
        else:
            iou = 0
            centre = None
            hausdorff = None
            status = "no_independent_match"
        record = {
            "osm_id": f["id"],
            "name": f["tags"].get("name", ""),
            "county_ids": ";".join(str(i) for i, g in candidates),
            "overlap_iou": round(iou, 4),
            "centroid_difference_m": round(centre, 3) if centre is not None else None,
            "boundary_hausdorff_m": (
                round(hausdorff, 3) if hausdorff is not None else None
            ),
            "status": status,
            "name_verified": False,
            "facade_verified": False,
            "height_verified": False,
        }
        report.append(record)
        polygons.append((geometry, record))
    with (output / "building_positions.csv").open("w", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=list(report[0]))
        writer.writeheader()
        writer.writerows(report)
    write_json(output / "building_positions.json", report)
    summary = {
        "buildings_checked": len(report),
        "county_features": len(county),
        "agreement_candidates": sum(
            r["status"] == "agreement_candidate" for r in report
        ),
        "needs_review": sum(r["status"] == "needs_review" for r in report),
        "no_independent_match": sum(
            r["status"] == "no_independent_match" for r in report
        ),
        "county_source": "https://gisdata.alleghenycounty.us/arcgis/rest/services/EGIS/Buildings/MapServer/0",
        "county_snapshot_sha256": hashlib.sha256(
            Path(county_file).read_bytes()
        ).hexdigest(),
        "county_metadata_date": "not established; possible historical footprints",
        "method": "Compare independent footprint datasets in UTM metres; union overlapping county parts. No automatic repositioning.",
        "limits": [
            "Agreement is not surveyed accuracy",
            "A disagreement can reflect age, roof overhangs, extensions, or different segmentation",
            "Building names, current state, facade and height are not validated by this comparison",
        ],
    }
    write_json(output / "position_summary.json", summary)
    image = Image.new("RGB", (1200, 1200), "#f5f4ec")
    d = ImageDraw.Draw(image)

    def draw_geometry(g, color, width):
        """Draw polygon boundaries and holes with the same local-coordinate screen offset."""
        geoms = list(g.geoms) if hasattr(g, "geoms") else [g]
        for p in geoms:
            if p.geom_type != "Polygon":
                continue
            for ring in [p.exterior, *p.interiors]:
                d.line(
                    [(60 + x, 95 + z) for x, z in ring.coords], fill=color, width=width
                )

    for _, g in county:
        draw_geometry(g, "#adb7bd", 1)
    for g, r in polygons:
        draw_geometry(
            g, "#178367" if r["status"] == "agreement_candidate" else "#d85e38", 2
        )
    font = ImageFont.load_default(size=18)
    d.rectangle((0, 0, 1200, 88), fill="#f5f4ec")
    d.text(
        (35, 20),
        "CMUcraft / independent footprint audit",
        font=ImageFont.load_default(size=27),
        fill="#263d34",
    )
    d.text(
        (35, 56),
        "Gray: county | Green: agreement candidate | Orange: review / unmatched | North up",
        font=font,
        fill="#263d34",
    )
    d.rectangle((0, 1130, 1200, 1200), fill="#f5f4ec")
    d.text(
        (35, 1145),
        f"{summary['agreement_candidates']} candidates / {summary['needs_review']} review / {summary['no_independent_match']} unmatched",
        font=font,
        fill="#263d34",
    )
    d.text(
        (35, 1172),
        "© OpenStreetMap contributors / Allegheny County GIS. Agreement does not verify current building identity.",
        font=ImageFont.load_default(size=14),
        fill="#52635d",
    )
    image.save(output / "position_overlay.png")
    return summary


def main():
    """Run the independent footprint comparison using explicitly supplied county data."""
    p = argparse.ArgumentParser()
    p.add_argument("--osm", default="data/raw/campus.osm")
    p.add_argument("--county", required=True)
    p.add_argument("--output", default="audit")
    a = p.parse_args()
    print(json.dumps(compare(a.osm, a.county, a.output), indent=2))


if __name__ == "__main__":
    main()
