# Builder workflow validation record

Recorded 2026-11-05 (America/New_York). This is offline implementation evidence,
not a completed client or end-to-end Builder acceptance test.

## Initial offline checks

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


## Follow-up: local client small-sample test

On 2026-11-05, Chris tested the existing `CMUcraft-Architecture-1.16.5`
instance on macOS. All six installed mod files matched the pinned manifest.
The user reported successful world entry, ordinary-block save/re-entry, and
C&B detail save/re-entry; supplied screenshots showed the world and carved blocks.
This was an existing instance, not a fresh launcher installation test.

A closed-save backup contained three `chiselsandbits:chiseled` block entities at
(469,88,725), (469,88,726), and (470,88,725). A separate clean legacy campus copy
was opened and saved by the user to establish a runtime-initialized comparison.
Both backups were retained. Their world-generation settings were semantically
equal; first-save additions in the generated base made the old, uninitialized
manifest unsuitable. A new test kit was issued against the initialized baseline,
not by disabling the stale-target guard on the old kit.

The real client exposed three overly strict checks, now corrected:

- World-generation NBT compares structurally, not by serialized key order.
- Zero-byte region files created before the first POI write represent no records;
  nonempty truncated files still fail.
- A strictly recognized per-world Xaero map ID is excluded from building-global
  comparison. Only a pristine 1.16.5 raid manager with no raids, NextAvailableID=1
  and exactly the expected fields may differ in its elapsed Tick value. Unknown,
  active or history-bearing data still compares by exact hash. Target data stays
  in the candidate; these source files are not copied over it.

The planner and staging tool then completed against the initialized baseline.
All reserved terrain/POI payloads matched the submission, all other existing chunk
payloads matched the baseline, and target global data was retained. The three
C&B entities remained in the candidate. A separately named test copy was installed
with a nearby spawn. Chris reported that the sample looked correct after integration
and remained correct after another save/re-entry.

**Result: one local, small C&B full-save/raw-chunk integration round trip passed
based on file verification and user-reported client observations.** The post-import
visual check was performed by the user, not by automated UI inspection. Current
regression suite: **64 passed**. No full-desktop screenshots, player data or private
world backups are published in this repository.

Still unverified: fresh install, a complete contributed building, collision details,
multimaterial/transparent geometry, client-created oversized external chunks,
WorldEdit schematic export/import, multiplayer and independent volunteer onboarding.
The original example ZIP remains an uninitialized experimental example; issue new
Builder kits from a separately initialized, reviewed base. Do not describe this
small-sample result as general C&B compatibility certification.

## First Builds distribution preparation

The first round now exposes Hunt #3 and CUC #4 as small public proposal tasks;
screenshots are requested in #5. No claim is needed for an independent trial or
reference contribution. Main-save ownership and actual integration remain coordinated.

A combined `.mrpack` and two world ZIPs were built from the clean, runtime-initialized
comparison world, not the player's modified test world. Player NBT, player files,
progress, old level files, session locks, map identity, icon and config backups were
removed from the publication copy. The retained world-owned config/data was inspected.
Archives contain no game binaries, mod JARs, account folders or desktop screenshots.
Pinned mod metadata is unchanged. Both trial reservations are disjoint from each
other; their overlaps with neighboring buildings remain documented restrictions.
Starter chunk payloads match the reviewed base. Archive integrity, included worlds,
privacy exclusions, manifest consistency and local documentation links were checked.
Regression suite: **65 passed**.

The new downloadable pack has not been freshly imported in a launcher. The CUC trial
world has not been entered in a client. These are explicit trial downloads, not an
approved full-building handoff. The earlier Hunt example remains historical. Source
code, public kit manifests and download checksums allow tracking this fixed round;
maintainers retain the exact sanitized base and issued kit archives for future review.
