# Developer setup

Use this document to install the Python tools and reproduce generated outputs. You do not need these tools to play the preview or contribute a campus observation. See [CONTRIBUTING.md](../CONTRIBUTING.md) to choose a contribution.

## Install and run

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

The last command builds the small 256 m footprint model from the committed source snapshot. It does **not** generate a detailed campus. This route needs no data download after dependencies are installed. For optional lidar tools, install `.[dev,survey]` and follow [SURVEY.md](SURVEY.md).

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

Start with the [code and file guide](CODE_GUIDE.md). The [reconstruction requirements](RECONSTRUCTION.md) define acceptance; the [development journal](../DEVLOG.md) explains setbacks and decisions. The journal, contributor-facing documentation and code comments are in English.

## Building Kit tools

See [BUILDER-MAINTENANCE.md](BUILDER-MAINTENANCE.md) for `python -m cmucraft.building_kit` create, unpack, plan and stage commands. Builders do not run these tools. Tests use synthetic saves plus the existing pipeline suite; runtime checks are tracked separately.

Maintainers with GitHub label permissions can run `python scripts/setup_builder_labels.py` after authenticating `gh`. It creates missing labels from `.github/builder-labels.json` and does not overwrite existing labels. Forms work even when labels are unavailable.
