# Week 1 validation record

Validated on November 5, 2026 (America/New_York).

## Completed locally

- Python 3.13.15 on macOS arm64; editable package installation and the installed `cmucraft build` command succeeded.
- 16 pytest tests passed without warnings.
- Coverage: axes, round trips, independent 100 m geodesic baselines at 12 bearings, rectangle area, holes, clipping, boundary-centre policy, disconnected polygons, invalid regions, real OSM parsing and checksum, missing members, source extent enforcement, GeoJSON/CSV consistency, and schematic ordering and decoding.
- Snapshot: 11 intersecting building/complex features, 8 clipped, 20,228 occupied cells, 0 parsing warnings, 0 overlapping assigned cells.
- 55 full-building centroid pairs: maximum projected-vs-geodesic difference 0.111611 m; maximum relative difference 0.0301592%; maximum additional cell-centre quantization difference 0.845949 m.
- PNG opened and visually reviewed: labels, scale, attribution, holes, and clipping are visible.
- One local in-process build took about 0.091 seconds after imports; process peak resident memory was about 68.72 MiB. This is a single observation, not a cross-device benchmark. Installation and Minecraft memory are excluded.
- Schematic decompressed and decoded with nbtlib in tests: 256 × 2 × 256, zero offset, valid palette, `x + z*width + y*width*length` ordering, exact agreement with the grid.
- Downloader actually rerun against the OSM API to a separate temporary snapshot. HTTPS certificate verification remains enabled using certifi. Committed source data was preserved.

## Not verified / not included

- No Minecraft/WorldEdit runtime import was performed. File validation cannot prove every game/mod combination will load it.
- No field survey, orthophoto comparison, lidar, or building-plan validation. Source accuracy remains OSM accuracy.
- No real heights, topography, roads, facades, rooms, or world save. The grass slab is a visualization aid.
- GitHub Actions has not run. The current OAuth credential lacks workflow scope; the configuration is included as the inactive template `docs/ci/tests.yml`.

## Reproduce

From the repository root after installation:

```bash
python -m pytest -q
cmucraft build
```

See `artifacts/report.json` and `artifacts/distances.csv` for numerical results. Source integrity is checked before each build. Do not run `download` first when reproducing the committed snapshot: that intentionally refreshes the source.
