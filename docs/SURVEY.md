# Measured campus reconstruction evidence

The previous world is not the replacement. These tools collect independent height evidence; they do not automatically certify architectural appearance.

## 2024 source

[Official PASDA tile index](https://services.pasda.psu.edu/arcgis/rest/services/pasda/USGS_PA_17County_D2024/MapServer/23) supplies the nine recorded state-plane LAZ tiles. The project is USGS PA 17 County 2024. The retained USGS metadata gives acquisition April 14–May 8, 2024. Later construction is not established by this survey.

The LAS headers declare NAD83(2011) / Pennsylvania South **US survey feet**, including NAVD88 elevations in **US survey feet** with Geoid18. Horizontal coordinates transform to UTM 17N. Vertical coordinates multiply by exactly 1200/3937 to produce metres. Horizontal projection does not perform the vertical conversion. A missing vertical CRS requires explicit verified units; conflicting units stop extraction.

```bash
python -m pip install -e '.[dev,survey]'
python scripts/download_survey.py /path/to/survey
python -m cmucraft.lidar /path/to/survey/*.laz \
  --source-crs EPSG:6565 --output /path/to/measured-campus \
  --acquired-start 2024-04-14 --acquired-end 2024-05-08 \
  --include-unclassified
```

Use the Laszip decoder: the tiles use Point14 compression version 4, which the tested lazrs backend cannot decode. The downloader checks the entire point stream and records hashes; it never substitutes sample geometry.

The data does not provide a building-only class. Class 1 is explicitly enabled as a **surface candidate**, not relabeled as class 6. Trees and other objects can remain. Class 2 supplies ground; noise and withheld returns are excluded. Missing raster cells stay NaN. Roof interpretation must combine the points, dated aerial imagery, footprints, and facade photographs.

## Position and roof checks

A single metre-based campus origin is retained. Orthophoto roof outlines can differ from ground footprints because of roof overhangs, image parallax, source date or mapping errors. Never translate a building to match an aerial roof without checking ground/wall evidence. The 2021–2023 PASDA imagery service can provide a contextual image, but its actual tile acquisition date must be recorded before treating it as contemporaneous.

The earlier 2019 project spans two acquisitions: WesternPA 1 ends March 9, 2020; WesternPA 2 ends March 22, 2020. Combined coverage must use the latter end date and cannot establish newer buildings.

## Sub-block facade work

`python scripts/build_facade_lab.py` creates an experimental detail specimen using the pinned Chisels & Bits schema. Its NBT geometry is tested independently; this is **not** a completed Minecraft load/save compatibility test. Do not include it in a final campus release until the pinned client successfully loads, saves and reloads the specimen.
