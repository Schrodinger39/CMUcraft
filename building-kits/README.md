# Example Building Kit

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
