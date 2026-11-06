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

## Maintainer example

`hunt-library-example/` contains a readable manifest, footprint and instructions
for the original generator example. New builders should use the First Builds
release above. The old generated ZIP has been removed to keep one clear download
entry point; maintainers can recreate it when testing the generator.

This example uses the rough legacy campus and has not been client-validated.
Review its reservation and surrounding structures before using it for a new kit.

Reproduce with:

```bash
python -m cmucraft.building_kit create hunt-library \
  --base campus_artifacts/world --spawn-y 130 --output build/hunt-library-example
```

See [Builder instructions](../docs/BUILDERS.md),
[maintainer commands](../docs/BUILDER-MAINTENANCE.md), and
[compatibility limits](../docs/BUILDER-COMPATIBILITY.md).
