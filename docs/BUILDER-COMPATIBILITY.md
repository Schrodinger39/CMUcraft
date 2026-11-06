# Builder compatibility evidence

## Pinned environment and inspected implementation

The authoritative download list is `modpack/modrinth.index.json`: Minecraft Java
1.16.5, Forge 36.2.42, C&B 1.0.63 and WorldEdit 7.2.5, plus the other mods listed in
[the Workbench guide](../modpack/README.md). Do not infer compatibility from a modern
version of either project. The official [C&B file 3593643](https://www.curseforge.com/minecraft/mc-mods/chisels-bits/files/3593643)
identifies 1.0.63 as Forge and includes Minecraft 1.16.5 in its supported versions.
That metadata is not a test of this pack. The [official Forge 1.16.5 index](https://files.minecraftforge.net/net/minecraftforge/forge/index_1.16.5.html)
also lists 36.2.42. All six pinned JARs were freshly downloaded and passed the
repository's size, SHA-1/SHA-512 and ZIP-integrity checks; their declared metadata
was inspected. This did not execute Minecraft or any mod.

WorldEdit tag `7.2.5`, commit `57d5ac961d310f653f7fa5faafeb61ab3b3b687d`, was inspected:

- [SpongeSchematicWriter](https://github.com/EngineHub/WorldEdit/blob/57d5ac961d310f653f7fa5faafeb61ab3b3b687d/worldedit-core/src/main/java/com/sk89q/worldedit/extent/clipboard/io/SpongeSchematicWriter.java)
  serializes block-entity NBT into the Sponge schematic; it converts position fields.
- [ForgeWorld](https://github.com/EngineHub/WorldEdit/blob/57d5ac961d310f653f7fa5faafeb61ab3b3b687d/worldedit-forge/src/main/java/com/sk89q/worldedit/forge/ForgeWorld.java)
  obtains block-entity data through Forge, including `TileEntityUtils.copyNbtData`.
- This provides a generic NBT path, **not proof** that C&B's voxel data, cached
  statistics, collision or lifecycle behavior survives copy/paste. No C&B-specific
  integration test was found in the inspected path, and no client round trip was run.

The hash-matched C&B JAR was also inspected with `javap -p -c` (no game launch).
`ChiseledBlockEntity` reads `chiselBlockData`, `compressedStorage` and `statistics`;
its disk writer calls `ChunkSectionUtils.serializeNBTCompressed`. That utility
writes `isCompressed` and `compressedData`, and its reader also accepts the direct
`palette`/`blockStates` representation. Its decompression-failure path resets data.
These findings support preserving the original bytes and checking reload, rather
than reconstructing details from block names. The repository's geometry decoder is
for its direct-format generated fixtures, not a complete decoder of client saves.
To reproduce the static inspection after obtaining the pinned JAR:

```bash
javap -p -c -classpath /path/to/chiselsandbits-1.0.63.jar \
  mod.chiselsandbits.block.entities.ChiseledBlockEntity
javap -p -c -classpath /path/to/chiselsandbits-1.0.63.jar \
  mod.chiselsandbits.utils.ChunkSectionUtils
```

In this repository, `chisel.py` encodes experimental `chiselBlockData` storage and
statistics. `world.py` writes Anvil DataVersion 2586 and external `.mcc` streams for
oversized chunks. `schematic.py` exports only two-layer ordinary-block footprints
with an empty `BlockEntities` list: it cannot export a detailed building.

The new raw-chunk staging path retains source compressed payloads at the **same
chunk coordinates**, avoiding schematic conversion and mod-NBT translation. Tests
prove synthetic C&B payload preservation and neighboring chunk protection. They do
not prove that C&B accepts the original payload or that all mod state is chunk-local.
Full-save submissions retain the evidence needed if another transfer path is required.

## Required client matrix — all currently unverified

| Check | Test input and required evidence | Status |
| --- | --- | --- |
| Clean installation | Fresh launcher import; exact Mods menu and hashes | Not run |
| Starter world | Correct spawn, border, context and F3 coordinates | Not run |
| C&B persistence | Client-created asymmetric multicolor/transparent detail, save/quit/reload twice | Not run |
| Generated C&B | Existing Hunt specimen rendering, materials, collision and reload | Not run |
| Raw-chunk integration | Original save vs staged campus, same coordinates, boundary checks and reload | Not run |
| WorldEdit plain blocks | Selection/copy anchor, export/import to fresh world, reload | Not run |
| WorldEdit C&B | Same asymmetric detail, material/voxel comparison, collisions and reload | Not run; not an approved delivery path |
| Multiplayer | Matching server/client versions, two-client visibility and server restart | Not run |

A real test should contain stone, glass, an asymmetric 1/16-block shape, two materials
inside one chiseled block, and details across chunk boundaries. Record source/paste
coordinates, screenshots from multiple sides and before/after NBT if possible.
Include a large detail sample that actually produces `.mcc` before claiming runtime
external-stream coverage. A synthetic large-byte test is only storage coverage.

For the optional schematic experiment, in a disposable source copy use `//pos1 x,y,z`
and `//pos2 x,y,z` for the inclusive selection corners. Stand at a recorded integer
anchor with `/tp @s x y z`, then `//copy` and `//schem save test-building`. Copy the
resulting `.schem` from the instance's WorldEdit schematics directory into a fresh
matching instance. Use `//schem load test-building`, teleport to the recorded target
anchor, and `//paste` without rotation/mirroring. Use a clear area; air in the selection
also replaces destination blocks. Do not use `//paste -o` when testing translation.
Save, quit, restart and compare. See the [WorldEdit 7.2 clipboard guide](https://worldedit.enginehub.org/en/7.2.20/usage/clipboard/)
for command concepts; that later patch's documentation is not certification of 7.2.5.

Any missing voxels, invisible blocks, changed materials, bad collisions, errors or
reload loss is a failure. Keep both original and imported saves, mark the test failed,
and do not promote the schematic. Even if one sample passes, require a round trip of
the actual building. Do not enable arbitrary rotations based on a translation test.

See [the executed validation record](BUILDER-VALIDATION.md) for commands and results.
