# Build one CMU building

You can contribute without Python, Git or a pull request. You need Minecraft Java,
the pinned Workbench, and a Building Kit supplied by a maintainer. There is no
shared server. The current kits are **experimental**: one local small-sample load/save/integration test has passed, but each issued kit
still needs maintainer review; collisions and full-building transfer are not certified.

## 1. Claim a building

Open [Building claim](https://github.com/Schrodinger39/CMUcraft/issues/new?template=building-claim.yml).
Give the building name, preferred credit name, whether you plan to use Chisels &
Bits, and the part you want to build. Search existing issues first. A request is
not an assignment: wait for the maintainer's confirmation and kit link.
If you do not have a GitHub account, a collaborator can open and maintain the
issue for you; agree a file-transfer channel with that person. No Discord,
email address or hosted upload service is assumed to exist.

The maintainer reserves a square group of 16 × 16 block chunks, at **all heights**.
Nearby buildings may share that group. Those claims must be combined or scheduled
one after another. A kit is tied to a specific base-world snapshot; do not reuse
an old kit for a new assignment.

## 2. Download and open your kit

1. Get the ZIP linked in your confirmed claim. The maintainer prepares it; you do
   not run the generator. See the [example kit](../building-kits/README.md).
2. Set up a separate instance using [the launcher guide](LAUNCHERS.md) and
   [the Workbench versions](../modpack/README.md): Java 1.16.5, Forge 36.2.42,
   Chisels & Bits 1.0.63, WorldEdit 7.2.5, and the other pinned mods. Do not update
   individual mods or open this save in vanilla, Fabric, Bedrock or newer Minecraft.
3. Close Minecraft. Unzip the kit. Open your launcher's instance folder, then its
   Minecraft folder and `saves`. Copy `starter-world` there; give the copied folder
   a unique name. `level.dat` must be directly inside that folder, not two levels down.
4. Read `START-HERE.md`, `reference.json` and `footprint.png`. Launch the instance
   and select **CMUcraft Kit - [building]**. Verify the Mods menu matches the pack.
5. If the world fails to open, stop and report the error with versions. Keep the
   original ZIP. Never try to repair it by removing Chisels & Bits.

A kit includes real existing terrain/context, not an empty flat building plot.
Existing architecture is rough and must be replaced only as agreed in the claim.
The world border marks your reserved square; the green footprint in the plan is
source geometry, not a claim that the facade or height has been verified.

## 3. Build in place

- One full block is one metre. North is decreasing Z; east is increasing X.
  Use F3 to see coordinates. Keep the exact position and orientation in the kit.
- Work only inside the coordinates in `START-HERE.md`, including roofs, basements,
  overhangs and temporary blocks. Ask for a larger reservation before extending it.
- Use the linked references. Record estimated dimensions; do not turn an unknown
  height or ambiguous floor count into a measured fact. Exterior and roof come first.
- Preserve neighboring buildings, terrain, paths and underground features unless
  the claim explicitly authorizes replacing them. All reserved chunks are imported,
  not just the new walls. Remove scaffolding and temporary work before delivery.
- Do not add mods, datapacks, command blocks or executable files. Avoid free-moving
  entities, villagers, portals and mod features that store data outside their chunks.
  Ask the maintainer if these are essential; the automatic path may reject them.
- Save, quit and reopen regularly. For chiseled details, compare close-ups, materials,
  transparency and collision behavior after reopening. Record failures honestly.

## 4. Submit a complete save

1. Save and quit, then close Minecraft completely so no files are changing.
2. ZIP the **entire world folder**, including `level.dat`, `region`, every `.mcc`,
   `data`, `poi`, `serverconfig` and other world-owned files if present. Do not send
   the whole launcher instance: it contains mods, account information and logs.
3. Open [Building submission](https://github.com/Schrodinger39/CMUcraft/issues/new?template=building-submission.yml).
   Link the claim and attach the ZIP, or use an agreed downloadable file link if
   GitHub refuses its size. Do not split a region file or omit sidecars to shrink it.
4. Include the original `kit.json`; front, back, both sides, roof and context views;
   close-ups before/after reload; exact game/mod versions; known issues; reference
   URLs and rights; your credit name and permission to redistribute your original build.
   Say which tests you did **not** run. Never include account files or private logs.

Screenshots do not replace the save. Keep your original until integration is accepted.
The maintainer may ask for changes or a new kit if the campus has changed.

## Optional schematic delivery

For ordinary blocks, a WorldEdit `.schem` may accompany or replace a save after a
successful export → fresh-world import → save/quit/reload test. Record both selection
corners, the exact position used for `//copy`, the intended campus paste position,
versions, dimensions and screenshots. Do not rotate or mirror during transfer.
Modern `.schem` and legacy `.schematic` are different formats; do not rename an extension.

For **Chisels & Bits**, always submit the full original world, even if you attach a
schematic. We have not certified WorldEdit 7.2.5 + C&B 1.0.63 round trips. A schematic
that has the right block names may still lose voxel data or runtime state. See
[compatibility evidence and the test protocol](BUILDER-COMPATIBILITY.md).

## What happens next?

The maintainer checks the claim, sources, dimensions and neighborhood; reviews a
chunk-change plan; stages into a new campus copy; and tests that copy in the pinned
client. Passing automated checks does not accept a building. Accepted work receives
credit in `CONTRIBUTORS.md` and release notes. If integration fails, the original
submission stays intact and the claim stays open.
