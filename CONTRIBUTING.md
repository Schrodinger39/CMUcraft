# Contributing to CMUcraft

Thanks for helping. The most useful contribution is one that makes a particular building, measurement or instruction easier to trust. A good reference photo or a clear bug report can help as much as code.

## Start here

1. Read the current limitations in [README.md](README.md).
2. Pick one task from [ROADMAP.md](ROADMAP.md), or open an issue describing a specific problem.
3. Comment on the issue before starting a substantial model change. Include the building or file you want to work on and the evidence you will use. A maintainer can help narrow the scope.
4. Work on a branch or fork, then submit a pull request. A private repository requires an invitation before this workflow is available.

No Discord, public build server or external coordination channel has been set up. Use repository issues and pull requests for project work. Do not post account tokens, launcher account files or unfiltered logs.

## You do not need to code

For a building observation, include its name or OSM ID, the side you are looking at, and a screenshot or coordinate. Describe one concrete mismatch: a missing wing, the wrong entrance level, a roof shape, a color, or a window pattern. “This facade has six bays; the model has four” is more actionable than “make it realistic.” Mark estimates as estimates.

For photographs, use your own images or links to permitted sources. Record the date, viewpoint, credit and reuse permission. Avoid identifiable bystanders and private interior information. Linking a photograph is not permission to redistribute it.

For playtesting, record the pack version, operating system and exact world name. Check appearance, collisions and a save/quit/reload cycle separately. Share only relevant error lines after removing tokens, usernames you do not want public, and private server addresses. The bug-report template has a checklist.

## Contributing a Minecraft build

- Use the pinned Java/Forge environment and a copy of the save. Keep the original as a rollback point.
- Pick one facade, roof or building section. Do not merge work from the legacy campus into the detailed specimen without explaining the coordinate conversion.
- Keep the shared origin, orientation and metre scale. Document a standalone specimen's translation and vertical offset so it can be placed back in the campus.
- Include before/after views from the same angle, reference links, material choices and any dimensions that remain guesses.
- Preserve mod block entities. Do not assume a schematic tool retains Chisels & Bits geometry; test export/import before relying on it. A small zipped save is acceptable when the tool cannot preserve the details.
- Keep `.mcc` files beside `.mca` files when sharing a save. Large detail chunks may depend on them.
- Coordinate large binary uploads in an issue first. Keep account data, game binaries, caches and unrelated saves out of Git.

## Contributing code

Use Python 3.10+ and install `python -m pip install -e '.[dev]'`. See [CODE_GUIDE.md](docs/CODE_GUIDE.md) for module responsibilities, array layouts and the data flow.

Write readable English comments. Explain units, coordinate axes, assumptions, validation boundaries and reasons for unusual operations. Split dense statements so another contributor can follow them. A comment should explain the operation or decision, not simply repeat the variable name. Machine-readable formats that do not support comments are documented in the file guide instead.

For a change that affects behavior, run the relevant tests and add a regression test where it catches a real failure. Run the complete suite before submitting changes to shared geometry or world storage:

```bash
python -m pytest -q
cmucraft build --output build/pr-check
```

Use a fresh output directory for world builders; they refuse to overwrite existing worlds. Document required network access or optional survey dependencies. Synthetic test shapes are welcome in tests; they must never be substituted for real campus data in a download or build result.

The Actions workflow under `docs/ci/` is a template, not evidence that hosted CI ran. Include the checks you actually ran and any you could not run.

## What a useful PR includes

Explain the problem, the change, and how it was checked. For architecture, include comparable model/reference views. For source data, include provenance and why the snapshot changed. Keep unrelated refactoring and binary exports out of a small fix.

Passing tests does not approve a building's appearance. Keep its review record incomplete until the relevant evidence and runtime checks exist. Do not remove a failing acceptance gate merely to make a report green.

Contributions to original code and documentation use the repository's MIT license. Data, photographs and third-party assets need their own compatible permissions and attribution. You can add your name or GitHub handle to `CONTRIBUTORS.md`; do not attribute work to someone without their agreement.
