# CMUcraft

Help rebuild Carnegie Mellon University's Pittsburgh campus in Minecraft Java.

The goal is a campus you can recognize while walking through it: buildings in the right places, believable proportions, and the materials, windows, roofs and entrances that make each building different. We use real geographic data as a starting point, then check the architecture against measurements and photographs.

**This is an independent student project, not an official CMU map. It is under active reconstruction.** The full-campus model is still rough; Hunt Library is the first detailed development specimen. Contributions from Minecraft builders, CMU students, photographers, GIS users and programmers are welcome. You do not need to write Python to help.

[Try the preview](https://github.com/Schrodinger39/CMUcraft/releases/tag/v0.3.0-preview) · [How to contribute](CONTRIBUTING.md) · [Open tasks](ROADMAP.md) · [Report a problem](https://github.com/Schrodinger39/CMUcraft/issues/new/choose) · [Development journal](DEVLOG.md)

![Hunt Library development geometry](audit/hunt-exterior-prototype.png)

*Hunt's current geometry, rendered outside Minecraft. The roof uses 2024 measurements; facade dimensions, materials in-game and save/reload behavior are still being checked. This is not a screenshot of a finished campus.*

## What is here today?

| Part | Current state |
| --- | --- |
| Full-campus context | A 1024 × 1024 m legacy approximation with buildings, paths and terrain. Useful for comparison; architecture needs revision. |
| Hunt Library | Separate detailed specimen with silver fins, recessed glazing, window frames, an entrance canopy and a measured roof model. Not yet accepted as a finished replica. |
| Geographic pipeline | Real OSM footprints → metric coordinates → 1 m cells → inspectable exports and Java world files. |
| Survey evidence | Reproducible 2024 point-cloud processing and 41 building reference packets. Reference packets are not completed models. |
| Modpack | Pinned Forge build with Chisels & Bits, WorldEdit, FerriteCore and Xaero maps. |
| Validation | Automated geometry, units, storage and repair tests. Client walkthroughs and multiplayer testing remain open. |

The earlier v0.2 world was not recognizable enough during a campus walkthrough. It remains available as a legacy reference, not as the target quality. Better screenshots alone will not solve that: the project needs building-by-building checks.

## Try the current preview

1. Download **CMUcraft-Preview.mrpack** from [v0.3.0-preview](https://github.com/Schrodinger39/CMUcraft/releases/tag/v0.3.0-preview).
2. Import it into HMCL as a separate instance. Use **Minecraft Java 1.16.5 + Forge 36.2.42** and the pinned mods.
3. Choose **Hunt Detail Preview** to inspect the detailed specimen, or **Campus Preview (Legacy Geometry)** for the earlier full-campus layout. Scale Calibration is also included.

Xaero's World Map uses **M** by default and fills as you explore. Hunt requires Chisels & Bits; opening it without the mod can lose its details. Keep copies of saves before changing versions. Bedrock is not supported.

The known experimental-world-settings defect has been corrected and checked with Minecraft 1.16.5's own parser. **That check does not establish Forge client compatibility.** Rendering, collisions, saving/reloading and multiplayer still need direct testing. There is no hosted multiplayer server.

See the [modpack guide](modpack/README.md) for versions, credits and verification limits. The separate worlds ZIP is for people who already have the matching environment.

## Pick a small contribution

| If you enjoy… | A useful first contribution |
| --- | --- |
| Walking around campus | Compare one building's entrance, window pattern or roof with the model. Include a dated reference. |
| Minecraft building | Improve one facade in a copied save, preserving the building's coordinates and scale. |
| Photography | Share your own exterior photos with building name, side, date and permission to reuse them. |
| Maps and measurements | Investigate one flagged footprint or height discrepancy without moving a whole building on a guess. |
| Testing games | Load the pinned preview, inspect Hunt, save/reload, and report what persists or breaks. |
| Python | Improve a documented pipeline step or reproduce a bug with a small test. |
| Explaining things | Try the setup instructions on a fresh machine and fix unclear steps. |

Start with [CONTRIBUTING.md](CONTRIBUTING.md), then choose a task in [ROADMAP.md](ROADMAP.md). Open a focused issue to say what you want to work on so two people do not unknowingly rebuild the same facade. Small, reviewable changes are easier to merge than an entire replacement world.

The repository is currently private. These collaboration instructions are ready for invited contributors; people without access cannot see its issues or downloads. Public visibility has not been enabled.

## Work on the code

Python 3.10+; no GIS desktop application is required. Run these commands from the repository root:

```bash
git clone https://github.com/Schrodinger39/CMUcraft.git
cd CMUcraft
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
cmucraft build --output build/core-check
```

The last command builds the small 256 m footprint model from the committed source snapshot. It does **not** generate a detailed campus. This route needs no data download after dependencies are installed. For optional lidar tools, install `.[dev,survey]` and follow [SURVEY.md](docs/SURVEY.md).

To reproduce the Hunt specimen:

```bash
python scripts/build_hunt_prototype.py --output build/hunt-prototype
python scripts/render_hunt_prototype.py build/hunt-prototype
```

The builder uses the committed roof-fit parameters. To refit from the survey, follow the separate survey instructions. Building a specimen does not mark it approved. To reproduce the old campus for diagnostics only, use `python -m cmucraft.campus --output build/legacy-campus --legacy-approximation`.

## How the project fits together

| Location | What to read or change |
| --- | --- |
| `src/cmucraft/` | Projection, OSM parsing, rasterization, survey processing and Minecraft export. |
| `scripts/` | Downloads, development models, packaging, rendering and audits. |
| `tests/` | Reproducible checks, including synthetic fixtures explicitly separate from real campus data. |
| `data/raw/` | Source snapshots and provenance. Do not hand-edit or silently replace these. |
| `data/reference/` | Building identities, measured evidence and unresolved review items. |
| `audit/` | Comparison images and reports; a passing storage check is not visual approval. |
| `artifacts/` | Original 256 m footprint outputs. |
| `campus_artifacts/` | Legacy full-campus outputs. |
| `modpack/` | Pinned mod downloads, portable workbench and upstream credits. |

Start with the [code and file guide](docs/CODE_GUIDE.md). The [reconstruction requirements](docs/RECONSTRUCTION.md) define acceptance; the [development journal](DEVLOG.md) explains setbacks and decisions. The journal is in Chinese; contributor-facing documentation and code comments are in English.

## Accuracy rules

- Keep one campus origin: UTM 17N (`EPSG:32617`), Minecraft X east and Z south. One world block represents one metre; smaller details use sub-block geometry.
- Preserve real source IDs and record units, dates and uncertainty. OSM agreement alone does not prove a footprint matches reality.
- Survey roof heights do not establish window spacing, entrance height or facade appearance. Unclassified lidar points can include vegetation.
- Do not change a building's scale or position just to improve a screenshot. Use comparison evidence and report unresolved differences.
- Interiors may stay unfinished. Exterior identity and safe, coherent exploration come first.

## Credits and licensing

Contributor: **[Chris Yu / Schrodinger39](https://github.com/Schrodinger39)**. New contributors can add their chosen name and contribution to [CONTRIBUTORS.md](CONTRIBUTORS.md) with their PR.

Original code and documentation use the [MIT license](LICENSE). OSM source data and derived databases have separate ODbL obligations, © OpenStreetMap contributors. Government survey data and third-party reference material retain their own provenance; the code license does not relicense them. Read [DATA_LICENSE.md](DATA_LICENSE.md). Third-party mods retain their authorship and licenses; the pack references upstream downloads and does not bundle Minecraft binaries.
