# Building Kit maintenance and safe integration

These commands are for maintainers. Builders use [BUILDERS.md](BUILDERS.md).
All worlds must be closed. Keep immutable originals, use a separate work directory,
and never point tools at a live server or the only copy of a save.

## Inspect and reserve

1. Confirm the building identity, reference packet and approved scope in the claim.
2. Open and save a separate clean base once in the pinned client, then close the game. Generate kits from this initialized snapshot so Forge-created config/global data and default world settings are present before the baseline is recorded. Keep the original generated save. Choose a base campus snapshot in the repository's 1024 m coordinate frame.
   The small 256 m calibration/core worlds and the separate Hunt specimen have
   different origins: **do not use them as a base or substitute their region files**.
3. Reserve the entire square, chunk-aligned footprint extent, all Y=0..255. Inspect
   the actual base for neighbors, tunnels, paths and overhangs. The generated
   intersecting-reference list covers only 41 named records, not every structure.
4. Compare the reservation with every active claim. Shared chunks cannot be
   independently imported; combine the work or finish one and regenerate the next kit.
5. Record the claim URL, base commit/save SHA-256, maintainer, reservation, allowed
   removals, source links, and chosen spawn in the issue. Labels are optional aids;
   the issue confirmation is authoritative. No reservation is automatically granted.

## Generate a kit

Install the [developer dependencies](DEVELOPMENT.md), then from the repository root:

```bash
python -m cmucraft.building_kit create hunt-library \
  --base campus_artifacts/world --spawn-y 130 --output build/hunt-kit
```

This produces `build/hunt-kit/` and `build/hunt-kit.zip`: copied starter save,
reference JSON, footprint PNG, exact mod-download manifest, source/license notices,
English instructions and `kit.json`. The example uses the **legacy** campus and an
explicit, unverified spawn height, not the detailed Hunt specimen. Spawn safety and
world-border behavior require client inspection. Coordinates are unchanged, so
translation is exactly `(0,0,0)`; `X=easting-west`, `Z=north-northing`,
`Y=elevation_m-208` for the committed legacy campus. No rotation or rescaling occurs.

The tool copies the base instead of regenerating it through `world.write_world`.
That generator is not an existing-world editor and would discard unknown mod state.
The kit retains rough buildings and terrain; it does not infer a cleared or measured
construction surface. No photo is downloaded without reuse permission. Maintainers
must inspect the source URLs and add usable permitted views before assigning facade work.

Before distributing a kit, inspect its files for private information (custom bases
may contain it), validate the base provenance/height datum, launch it in the pinned
client, verify spawn and bounds, and mark the observed results in the issue. Keep the
original manifest privately with the base snapshot; **never trust a returned manifest
as authorization**. Upload the ZIP to the claim or a repository release and link it.
The committed sample ZIP is an experimental example, not an approved assignment.

## Intake and dry run

Use a disposable local instance for submissions; do not install supplied JARs or
run scripts. The archive utility rejects traversal, absolute paths, symlinks,
duplicate/case-colliding paths, encrypted entries and archives over 2 GiB/20,000 entries.
This is not an antivirus or a command-block scanner. Inspect datapacks, commands,
entities and unexpected files before loading; ask for a minimal kit-based save if unsure.

```bash
python -m cmucraft.building_kit unpack incoming.zip --output build/quarantine
python -m cmucraft.building_kit plan \
  --base campus_artifacts/world --submission build/quarantine/starter-world \
  --kit build/hunt-kit/kit.json --plan build/review-plan.json
```

Adjust the submission path to the actual folder containing `level.dat`.
Review every `changes` entry, the reservation and the original claim. Entries cover
terrain and POI including unchanged entries. SHA-256 hashes cover compression type
and payload, not timestamps or padding. A target change since kit generation fails
closed, even if Minecraft only recompressed a chunk. Regenerate a kit and coordinate
rework; do not bypass the baseline to force a merge. The planner rejects missing
terrain chunks, wrong versions/coordinates, changed world generation settings and
changed global saved data/config/dimensions, except a strictly recognized Xaero map identity and the elapsed Tick in a pristine empty raid manager. World-generation NBT key order alone is not a conflict. Global-state rejections are expected
for some real saves: investigate the specific mod/runtime data and leave integration
blocked until a dedicated supported transfer is implemented. Do not delete data to
make a test pass.

Edits outside the reservation are not imported. Review the whole submitted save for
such edits and ask the builder to remove or separately claim them. Player inventory,
spawn, world rules and other `level.dat` state stay from the target. New dependencies
in `level.dat` or global mod registries are not transferred: confirm exact mod hashes
with `scripts/verify_mods.py` and inspect the save in the pinned environment.

## Stage and validate

After reviewing the saved dry-run plan:

```bash
python -m cmucraft.building_kit stage \
  --base campus_artifacts/world --submission build/quarantine/starter-world \
  --kit build/hunt-kit/kit.json --plan build/review-plan.json \
  --output build/campus-candidate
```

The plan must still match both inputs. The tool copies the target into a fresh
folder, replaces only reserved records in `region` and `poi`, preserves opaque
payloads (including C&B NBT), handles `.mcc` sidecars, verifies written payload hashes,
and leaves inputs unchanged. Region sectors are repacked; neighboring chunk payloads
remain unchanged. Raw transfers include entities, scheduled ticks, terrain and all
vertical levels. They cannot merge two buildings inside the same chunk. They also do
not promise support for arbitrary mods with cross-chunk/global state.

No automatic promotion command exists. Before acceptance:

- Check the building's position, footprint, elevation, orientation, materials,
  photos and source rights. Check every adjacent boundary, path and basement.
- Compare original submission and candidate in the same pinned client. Verify
  chiseled geometry/materials, collision, lighting and save/quit/reload twice.
- Inspect entity duplication and cross-boundary behavior; do not accept problematic
  entities by relying on byte equality. Run the compatibility matrix for new features.
- Record versions, hashes, screenshots, test steps, tester and failures in the issue
  and PR. Run `python -m pytest -q` for tool changes. Request a review before publishing.
- Back up the entire current campus, including global data and sidecars. Only after
  acceptance replace the distributed world with the reviewed candidate as one unit.
  Roll back by restoring the entire backup, never individual stale region files.
- Credit the builder and record the accepted base/candidate hashes in release notes.

For a plain-block schematic, use the separate disposable-client workflow in
[BUILDER-COMPATIBILITY.md](BUILDER-COMPATIBILITY.md). The Python importer intentionally
does not parse/paste schematics or rewrite mod NBT at new coordinates.
