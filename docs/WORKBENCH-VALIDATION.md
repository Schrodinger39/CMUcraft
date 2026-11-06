# Workbench validation

This revision is a review/construction workbench, not a replacement campus release.

- 39 Python tests passed locally, including deliberately moving the old exported layout by eight blocks and detecting the shift.
- 342 legacy building ID masks compared to their source: 341 exact raster matches; one overlapping Phipps record loses source cells. None extends beyond its source raster. This is not independent proof of location or an audit of final roof voxels.
- Independent county comparison: 115 agreement candidates, 222 requiring review, seven unmatched. Different source age and segmentation are unresolved.
- 41 named-building packets preserve the source geometry and origin. Their exported context sheets were generated; the Hunt sheet was visually inspected. They do not show finished facades.
- Strict realistic-release review: **0 of 41 approved**. The result is intentionally failing until external evidence and model comparisons are completed.
- Installed mod bytes match all three pinned package entries. The independent profile has not produced a verified startup log. Runtime stability and chiseled-block persistence are not certified.
- The portable `.mrpack` archive was reopened and checked. A clean launcher import and multiplayer run have not been tested.

Reproduce from the repository root:

```bash
python -m pytest -q
python -m cmucraft.layout_audit
python scripts/download_county.py
python -m cmucraft.position_audit --county build/county-buildings.geojson
python scripts/build_review_plans.py
python -m cmucraft.review  # exit 2 while incomplete
python scripts/build_modpack.py
```

The old campus and played saves are preserved. No unverified replacement world is installed as a finished reconstruction.
