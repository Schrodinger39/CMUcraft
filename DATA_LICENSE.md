# Data attribution and license

© OpenStreetMap contributors. Source: https://www.openstreetmap.org/

The raw OSM snapshot and derived footprint database files (`.geojson`, coordinate JSON, grid arrays and CSV exports) are made available under the Open Database License 1.0 (ODbL):

- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/

The PNG preview and Minecraft schematic are produced from that database and carry the same attribution. Anyone redistributing these outputs must retain appropriate attribution and comply with applicable ODbL obligations. The corresponding source and derived database are included in this repository.

The repository's MIT license applies only to original program code and original project documentation; it does not override source-data rights. OSM names, tags, object history, and contributor metadata are upstream data and are retained verbatim.

## Terrain and building references

Terrain: USGS National Map 3DEP public-domain US government geospatial data. The exact service request, grid spacing, timestamp and checksum are saved in `data/raw/terrain.source.json`. The 4 m service output is resampled to 1 m for block placement.

Building material families and level counts are factual references from CMU 2022 Institutional Master Plan, Appendix E, pages 158–163. The original PDF is linked, not redistributed. All model heights derived from level counts and all procedural architectural details are estimates.
