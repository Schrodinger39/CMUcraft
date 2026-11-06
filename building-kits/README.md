# Building Kits

**Start with the [First Builds release](https://github.com/Schrodinger39/CMUcraft/releases/tag/builders-round1):**

- `CMUcraft-First-Builds.mrpack`: combined Hunt + CUC trial environment; recommended
  for new Builders with a compatible launcher. Contains download metadata, not mod JARs.
- `hunt-library.zip` / `cohon-university-center.zip`: worlds and briefs for people
  who already have the exact pinned environment.
- `SHA256.json`: download checksums.

No claim is needed for a private trial or design proposal. Use [Hunt #3](https://github.com/Schrodinger39/CMUcraft/issues/3)
or [CUC #4](https://github.com/Schrodinger39/CMUcraft/issues/4) for discussion and setup help.
The combined pack and CUC trial world still need client import/entry testing.

Maintainers can reproduce the archives from a closed, reviewed, runtime-initialized
base using `python scripts/build_first_contributor_pack.py --base /path/to/base --output build/first-builds-new`.
The packager removes player data, backup saves and personal progress; maintainers
must still inspect custom source worlds for unexpected files before publishing.

## Historical example


`hunt-library-example.zip` is an experimental, generated starter kit based on the
committed legacy campus. It is **not** the detailed Hunt model, a finished building,
an active claim or a client-validated release. No Python/Git is needed to unzip it.
Download the ZIP using GitHub's file download button; do not download the HTML page.

The expanded `hunt-library-example/` directory contains the readable manifest,
reference and instructions for review. Its save is in the ZIP to avoid duplicating
binary world data. The ZIP includes the full base context and required license notices.

Maintainers must confirm the reservation and spawn, inspect references, and complete
the client checks before giving a kit to a new builder. Builders should use the kit
linked from their confirmed claim, not assume this sample grants permission to edit.

Reproduce with:

```bash
python -m cmucraft.building_kit create hunt-library \
  --base campus_artifacts/world --spawn-y 130 --output build/hunt-library-example
```

See [Builder instructions](../docs/BUILDERS.md),
[maintainer commands](../docs/BUILDER-MAINTENANCE.md), and
[compatibility limits](../docs/BUILDER-COMPATIBILITY.md).
