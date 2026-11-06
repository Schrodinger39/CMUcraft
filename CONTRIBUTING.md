# Contributing

CMUcraft is an unfinished reconstruction of CMU's Pittsburgh campus. Contributions to the world, generation tools, reference data and installation experience are welcome. The project is currently focused on exterior accuracy and making the existing work usable by other people.

## Minecraft Builders — no code required

Start with [BUILDERS.md](docs/BUILDERS.md). The first round focuses on
[Hunt #3](https://github.com/Schrodinger39/CMUcraft/issues/3) and
[CUC #4](https://github.com/Schrodinger39/CMUcraft/issues/4). Download a fixed trial
pack, try one exterior idea, or share a reference in the existing task. No separate
claim or submission form is needed for a first proposal. Python and Git are not required.
For a building lead or actual integration, coordinate scope in the same task before
replacing architecture; each building has one accepted main save.

Chisels & Bits submissions must include a full save, including `.mcc` sidecars.
WorldEdit schematic compatibility is **not verified**. Plain-block schematics need
selection/copy/paste coordinates and a documented round trip. The maintainer stages
reviewed changes into a new campus copy; no contribution directly overwrites it.
See [maintenance](docs/BUILDER-MAINTENANCE.md) and [compatibility](docs/BUILDER-COMPATIBILITY.md).

## Coordination

Use issues to discuss substantial changes before starting, especially when they affect building placement, shared coordinates, mod dependencies or the world format. Check existing issues and pull requests for overlapping work. Small fixes and documentation corrections can go straight to a pull request.

There is no shared build server at the moment. World changes are developed in separate copies and reviewed before integration. The current direction is described in [Future Plans](ROADMAP.md); it is not a list of assigned tasks or a release schedule.

## Code changes

Set up the project using [DEVELOPMENT.md](docs/DEVELOPMENT.md). Keep a pull request focused on one change and explain the reason for it. Include the checks you ran and any behavior that remains unverified. Changes to coordinates, rasterization or save generation should include a regression test where appropriate.

```bash
python -m pytest -q
```

Use English for code comments and contributor-facing documentation. Explain assumptions, units and non-obvious operations. The [code guide](docs/CODE_GUIDE.md) covers the existing modules and file formats. The workflow in `docs/ci/` is a template; it should not be presented as a successful CI run.

## World and architecture changes

Use the pinned game and mod versions and work from a copy of the save. Preserve the campus coordinate system and scale. Kit worlds keep the campus coordinates, with zero translation. Independently created worlds need an explicitly reviewed placement and transfer route; the raw-chunk tool will not translate modded NBT.

Include comparison images and reference sources with a model change. Identify which dimensions are measured and which are estimated. Architectural review should cover the result in context, rather than only a favorable render. Interiors are not a current requirement.

Discuss delivery of large saves in the issue or PR before adding them to Git. Keep `.mcc` files with their `.mca` region files. Schematic exports are acceptable only if the export/import process preserves the modded geometry; that round trip still needs verification for the current detailing workflow.

## Data and references

Keep source IDs, acquisition dates, coordinate systems, units and attribution with data changes. Do not hand-edit a raw snapshot without updating its provenance. Conflicting datasets should be documented rather than resolved by silently moving geometry.

Photographs and drawings need a source and reuse permission if included in the repository. Links can be used for references that cannot be redistributed. Do not commit game binaries, launcher account files, private server information or unfiltered logs.

## Review and credit

A pull request should explain what changed, why, and how it was checked. For visual changes, provide comparable before/after views. Passing code tests does not establish architectural accuracy or client compatibility; leave unresolved review items explicit.

Contributions to original code and documentation fall under the project's MIT license. Source data and third-party assets retain their own licensing requirements. Contributors may add their preferred name or handle and contribution to [CONTRIBUTORS.md](CONTRIBUTORS.md).
