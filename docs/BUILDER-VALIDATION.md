# Builder workflow validation record

Recorded 2026-11-05 (America/New_York). This is offline implementation evidence,
not a completed client or end-to-end Builder acceptance test.

## Executed

- `python -m pytest -q`: **61 passed** (51 existing cases and 10 new cases).
  New cases cover kit metadata/bounds, same-coordinate payload identity, synthetic
  C&B block-entity preservation, adjacent-chunk preservation, external streams
  including valid large NBT, negative region addressing, stale target/plan rejection,
  missing chunks, global-state/worldgen/version rejection, POI removal, unsafe ZIP
  paths/size limits, symlinks and existing/nested output protection.
- `python -m cmucraft.cli build --output build/core-regression`: completed from the
  committed OSM snapshot, 11 building records and 20,228 occupied cells.
- `python -m cmucraft.layout_audit`: 341 exact matches, one source-loss overlap,
  zero buildings outside the source. This is the existing legacy result, not proof
  of geographic source accuracy or a new architectural review.
- Generated `hunt-library-example` from `campus_artifacts/world`, opened its ZIP for
  integrity checking, inspected the footprint PNG, ran the planner and staged a
  no-edit copy. The synthetic tests separately exercise an actual changed C&B chunk.
- Reopened the committed `.mrpack`; its embedded mod manifest equals the standalone
  manifest. Freshly downloaded all six pinned JARs and checked sizes, recorded hashes
  and ZIP integrity with `scripts/verify_mods.py`: all passed, runtime flag false.
- Inspected pinned WorldEdit source and C&B bytecode; see
  [compatibility evidence](BUILDER-COMPATIBILITY.md). No game code was executed.
- Checked Markdown/templates for remaining Chinese characters after translating
  the historical journal into English; none remained. `git diff --check` passed.
- Created the six Builder workflow labels in GitHub. Forms and a repeatable setup
  script are included; claims still require explicit maintainer coordination.

## Sample limitations and remaining acceptance gates

The example reserves X 400..479, Z 720..799, all Y 0..255, with spawn (440,130,760).
Its reserved chunks intersect the Baker Hall and College of Fine Arts reference
outlines as well as Hunt. It is therefore a **coordination example**, not a safe
independent assignment until a maintainer reviews the actual surrounding structures.
No neighboring chunk is independently claimable while this reservation is active.

The sample copies rough legacy architecture and terrain. It does not contain a
cleared plot, newly verified dimensions, permitted facade photos, or a completed
Hunt model. The linked references are starting evidence for a maintainer and builder.

No Minecraft client/launcher test, live C&B save/reload, collision check, schematic
round trip, multiplayer run or real volunteer onboarding was performed. No building
was accepted, no production world was replaced, and the PR is not an approval of a
playable release. Global-data changes intentionally block automatic staging; that
may require additional mod-specific work after the first actual client submission.
Use the [client test matrix](BUILDER-COMPATIBILITY.md) before distributing an approved kit.
