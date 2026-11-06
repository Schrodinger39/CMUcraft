# Code and file guide

Read this alongside the source comments. The program has several separate jobs: collecting evidence, generating geometry, writing Minecraft files, and checking results. A result from one job does not automatically validate the others.

## A useful reading order

1. [`geo.py`](../src/cmucraft/geo.py): the shared coordinates and cell rule.
2. [`osm.py`](../src/cmucraft/osm.py): actual source geometry, complete rings and holes.
3. [`build.py`](../src/cmucraft/build.py): small survey export and distance checks.
4. [`world.py`](../src/cmucraft/world.py): whole-block arrays to Java save files.
5. [`chisel.py`](../src/cmucraft/chisel.py): finer geometry inside a whole block.
6. [`lidar.py`](../src/cmucraft/lidar.py): independent surface measurements.
7. The building prototype and audit scripts relevant to your task.

## Coordinates and arrays

| Value | Meaning | Common mistake |
| --- | --- | --- |
| `(lon, lat)` | WGS84 longitude, latitude in degrees | Reversing the order because a website displays latitude first |
| `(easting, northing)` | UTM 17N coordinates in metres | Using degree differences as metre distances |
| `(x, z)` | Local metres: `x = easting - west`; `z = north - northing` | Forgetting that Minecraft Z increases south |
| `origin` | Northwest UTM corner of the chosen extent | Mixing the 256 m survey origin with the 1024 m campus origin |
| `grid[z, x]` | A horizontal cell or building ID | Swapping row and column |
| `volume[y, z, x]` | A whole-world block ID | Reading an array index as Minecraft's usual written `(x, y, z)` order |
| `bits[y, z, x]` | A 16 × 16 × 16 material grid inside one block | Moving the whole building to adjust a sub-block detail |
| Elevation | Source height, converted explicitly to metres | Assuming a horizontal projection also converts height units |
| Minecraft Y | Metre elevation minus the model's vertical offset | Comparing raw Y across specimens with different offsets |
| `NaN` | No observed lidar value in that cell | Replacing it with zero and creating a false ground or roof |

A block occupies a volume; a footprint cell is selected by testing its center `(x+0.5, z+0.5)`. Features narrower than one metre can disappear from this coarse raster. Chisels & Bits geometry addresses fine detail separately. No individual building is stretched to fit a grid.

## Library modules

| Module | Inputs, output and important boundary |
| --- | --- |
| [`__init__.py`](../src/cmucraft/__init__.py) | Package marker; does not perform a build. |
| [`cli.py`](../src/cmucraft/cli.py) | Parses `download`/`build`, constructs a region and prints the result or an explicit error. |
| [`geo.py`](../src/cmucraft/geo.py) | Projects geometry, defines the local extent and rasterizes strict interior cell centers. |
| [`osm.py`](../src/cmucraft/osm.py) | Fetches XML with provenance; assembles ways and nested multipolygons. Invalid/incomplete geometry becomes a warning, not an invented repair. |
| [`build.py`](../src/cmucraft/build.py) | Requires matching source hashes; exports the core grid, vectors, CSV, PNG and schematic. Stable first-feature ownership resolves raster overlap but is disclosed. |
| [`schematic.py`](../src/cmucraft/schematic.py) | Writes a two-layer Sponge v2 file. The one-block footprint height is a placeholder. |
| [`campus.py`](../src/cmucraft/campus.py) | Builds the old full-campus approximation. The explicit legacy flag prevents accidental use as a realistic replacement. |
| [`world.py`](../src/cmucraft/world.py) | Writes sections, chunks, region headers and `level.dat`. It supports external oversized chunks, not arbitrary existing-world editing. |
| [`chisel.py`](../src/cmucraft/chisel.py) | Encodes the pinned mod's material palette and block-entity statistics. Unsupported materials are rejected. |
| [`lidar.py`](../src/cmucraft/lidar.py) | Streams survey files, checks CRS/units, writes observed-cell summaries and unapproved building-height evidence. |
| [`scale.py`](../src/cmucraft/scale.py) | Applies a consistent geometry scale and checks the corresponding avatar multiplier. |
| [`structure_parts.py`](../src/cmucraft/structure_parts.py) | Keeps the mapped Gates/Hillman connector separate, with unknown deck elevation. |
| [`layout_audit.py`](../src/cmucraft/layout_audit.py) | Checks generated cells against their own source polygons. It cannot establish source accuracy. |
| [`position_audit.py`](../src/cmucraft/position_audit.py) | Compares county and OSM outlines, including differently merged complexes. Thresholds create review candidates, not automatic approvals. |
| [`review.py`](../src/cmucraft/review.py) | Requires evidence, identity resolution, supported height and facade comparisons. It cannot judge visual truth by itself. |

## Scripts

Run Python scripts from the repository root unless their help says otherwise. Development models create new output directories; do not overwrite a save you have played.

| Script | Purpose |
| --- | --- |
| [`download_osm.py`](../scripts/download_osm.py) | Small-survey OSM download wrapper. |
| [`download_terrain.py`](../scripts/download_terrain.py) | Fixed-extent USGS terrain request and provenance. |
| [`download_county.py`](../scripts/download_county.py) | Independent county footprint query. |
| [`download_survey.py`](../scripts/download_survey.py) | Verified PASDA downloads, full-point-stream checks and receipts. Requires survey extras. |
| [`build_review_plans.py`](../scripts/build_review_plans.py) | Source-outline context images for reference packets. |
| [`build_scale_lab.py`](../scripts/build_scale_lab.py) | Rooms demonstrating the effect of changing geometry scale. |
| [`build_facade_lab.py`](../scripts/build_facade_lab.py) | Small fin/glass specimen for mod testing. |
| [`fit_hunt_roof.py`](../scripts/fit_hunt_roof.py) | Deterministic coordinate-descent fit with held-out cells. Input is the shared campus surface grid. |
| [`build_hunt_prototype.py`](../scripts/build_hunt_prototype.py) | Current standalone Hunt model using the committed fit and documented facade hypotheses. |
| [`render_hunt_prototype.py`](../scripts/render_hunt_prototype.py) | Reads exported geometry and draws a fixed-view specimen PNG. Not a general game renderer. |
| [`audit_world.py`](../scripts/audit_world.py) | Checks region allocation, palettes, coordinates, external streams and expected chunk count. |
| [`repair_world_settings.py`](../scripts/repair_world_settings.py) | Backs up and repairs the specific old secondary-dimension defect in 1.16.5 saves. Do not use on a running world. |
| [`verify_mods.py`](../scripts/verify_mods.py) | Checks file bytes against the modpack manifest; does not launch Forge. |
| [`build_modpack.py`](../scripts/build_modpack.py) | Creates a portable manifest/overrides archive, optionally with preview saves. |
| [`CheckWorldSettings.java`](../scripts/CheckWorldSettings.java) | Uses the official 1.16.5 server JAR's obfuscated classes to parse world settings without starting a server. Version-specific; requires a separately obtained JAR. |

## Why the Minecraft writer looks unusual

Java 1.16.5 stores block IDs in signed 64-bit NBT values, but packing is easiest with unsigned arithmetic. `packed` views the same bits as signed only at the NBT boundary. During read-back, arrays are first converted to native-endian `int64`; viewing a big-endian NBT buffer directly as native `uint64` corrupts the decoded IDs.

Each 16-cubed section has its own palette. `np.unique(..., return_inverse=True)` returns both the used global IDs and each cell's local palette index. The local index uses at least four bits. In this Minecraft version, entries do not straddle a 64-bit word, so each word holds `64 // bits` entries and the rest is padding.

An `.mca` header addresses 4 KiB sectors. The low byte of a location entry is the number of sectors; the remaining bytes are the start offset. A chunk needing more than 255 sectors is stored in `c.<chunkX>.<chunkZ>.mcc`, with a small `.mca` stub. Deleting these sidecars loses detail chunks.

`DataVersion = 2586` targets Java 1.16.5. `level.dat` uses standard Nether and End generator IDs and biome sources. The previous fixed-biome configuration used invalid settings names and triggered the experimental warning. The repair changes those known settings, not campus geometry.

Initial heightmaps in this writer use a simplified non-air surface, and lighting is left for the game. Tests of packed IDs and file structure do not replace collision, lighting or modded save/reload checks.

## Files that cannot contain inline comments

Do not insert comments into JSON, source OSM, NBT, ZIP, image or NumPy files. That can invalidate parsers or source hashes. Use this guide and the producing script instead.

| File family | How to interpret it |
| --- | --- |
| `data/raw/*.osm` | Original XML nodes, ways and relations. Coordinates are degrees; IDs belong to OSM. Preserve original bytes. |
| `data/raw/*.source.json` | URL/request, retrieval time, source kind and checksum. Read with the corresponding raw file. |
| `data/raw/terrain.tif` | GeoTIFF elevation cells, tie point and pixel spacing; see `campus.terrain`. |
| `data/reference/buildings/*.json` | `osm_id` identifies the source; `footprint_wgs84` is degrees; `footprint_xz` is local metres; `verification` flags remain false until supported. `surveyed_height_m: null` means unknown. |
| `data/reference/building_profiles.json` | Historical inventory fields and legacy material/height assumptions, not a current survey certificate. |
| `data/reference/survey/*` | Official metadata/index, file hashes, elevation-unit factors, height percentiles and Hunt roof-fit parameters. `approved: false` is intentional. |
| `artifacts/grid.npy`, `campus_artifacts/building_grid.npy` | Integer `[z,x]` building IDs. Zero is unassigned; positive IDs correspond to their generated building lists. |
| `artifacts/*.geojson` | Geographic vectors in longitude/latitude. `local_geometry.json` separately holds metre geometry. |
| `artifacts/cells.csv` | Occupied X/Z cells and building ID; omitted cells are empty. |
| `artifacts/distances.csv` | Geodesic, projected and quantized centroid distances with separate errors. |
| `campus_artifacts/ground.npy` | Legacy Minecraft surface Y, not raw geodetic elevation. Add the manifest offset to compare with metre elevations. |
| `campus_artifacts/buildings.json` | Legacy modeled base, height, materials and entrance assumptions per feature. |
| `campus_artifacts/routes.json` | Source paths, widths and bridge flags; untagged widths are estimates. |
| `campus_artifacts/destinations.json` | Legacy teleport locations; do not reuse them in a translated specimen without conversion. |
| `audit/*.json`, `audit/*.csv` | Results of a specific check. Read the method and limits; approval flags are not interchangeable. |
| `*.png` | Either plan evidence or a geometry render. Captions distinguish these from actual game screenshots. |
| `world/level.dat` | Compressed NBT world metadata, spawn, rules and generators. Never edit as text. |
| `world/region/*.mca`, `*.mcc` | Chunk containers and optional external chunk payloads; keep both. |
| `*.schem` | Compressed Sponge schematic, generated by `schematic.py`. |
| `modpack/modrinth.index.json` | Pinned game/loader versions, mod paths, upstream URLs, hashes and environment requirements. |
| `*.mrpack` | ZIP-based pack with the index plus overrides. It references mod downloads rather than bundling Minecraft. |

## Tests and project metadata

Tests under `tests/` describe their expected behavior in their names and assertions. `test_pipeline.py` covers source provenance and core geometry; `test_world.py` covers binary storage; the remaining files focus on units, scale, detail geometry, repair, building records and review gates. Small synthetic shapes are fixtures. Tests using committed campus inputs are integration checks, not substitutes for a new download.

`pyproject.toml` defines the Python package, command entry points, optional survey dependencies and pytest discovery. `requirements.txt` installs the package with development extras; the lock file records a tested environment. `requirements-survey.txt` adds pinned survey decoders. The Python package version and a development-preview release tag may differ.

`.gitignore` excludes caches, builds and repair backups. `.github/ISSUE_TEMPLATE/` provides structured entry points for contributors; `.github/pull_request_template.md` asks for evidence and validation. `docs/ci/tests.yml` is an inactive workflow template. README, CONTRIBUTING, ROADMAP, licensing files and the development journal explain their own roles in their opening sections.

When adding a new file type, document its producer, units, field meanings and limitations here. Do not modify upstream data just to make it easier to annotate.

## Builder exchange tools

`building_kit.py` clones a closed base world into a kit, records reserved chunk hashes, checks submitted saves against that baseline, and stages opaque region/POI records into a new target copy. It preserves same-coordinate compressed payloads and external `.mcc` streams. It is deliberately not a schematic converter, mod-NBT translator, live-world editor or automatic acceptance system. See [maintenance](BUILDER-MAINTENANCE.md) for scope and review gates.
