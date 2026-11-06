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

## Hunt development model (not a release)

```bash
python scripts/fit_hunt_roof.py \
  --surface /path/to/measured-campus/roof_elevation.npy \
  --output /path/to/hunt-fit.json
python scripts/build_hunt_prototype.py --output build/hunt-prototype
python scripts/render_hunt_prototype.py build/hunt-prototype
python scripts/audit_world.py build/hunt-prototype/world --expected-chunks 64
```

The builder uses the committed 2024 roof fit. The separate 128 m world is a translated development specimen, not a relocated building in the campus. Its X/Z translation and elevation offset are recorded in its manifest. Silver fins, recessed glazing, paired transoms, a bronze-colored canopy, and the four-plane raised roof replace the old generic box. Facade and entrance dimensions remain photo-derived hypotheses. Materials in the offline render are swatches, not evidence of their in-game appearance.

The roof fit holds out one fifth of observed cells: median absolute residual 0.065 m and 95th percentile 0.224 m. Those are fitting residuals, not absolute survey accuracy or a certificate for the exterior. The lower roof and raised hip are modeled separately, avoiding the jagged isolated roof blocks from the earlier experiment.

Dense detail can exceed the 255-sector internal chunk limit. The exporter then writes the standard external `.mcc` stream, retaining a one-sector `.mca` stub; both files must travel with the save. Storage handling follows the [PaperMC region-format specification](https://github.com/PaperMC/SectorTool/blob/master/SPECIFICATION.MD). Read-back and boundary tests pass. A Forge client load/save/reload test is still outstanding.

Photographic references: [CMU Hunt Library](https://library.cmu.edu/visit/hunt), [CMU library exterior article](https://library.cmu.edu/about/news/2024-11/hunt-library), and [Dllu's 2015 front photograph, CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Carnegie_Mellon_University_Hunt_Library_front.jpg). Photographs are not bundled. Nighttime blue lighting is not treated as blue wall paint.
