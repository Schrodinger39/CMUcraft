# Playing with your own launcher

CMUcraft does not require HMCL. It requires a matching Minecraft Java/mod environment. You need your own access to Minecraft Java; the downloads do not include the game or an account. Bedrock, console and phone editions cannot load this Java modpack.

## Choose a route

| Your situation | Route | What has actually been checked? |
| --- | --- | --- |
| You use HMCL | Import `CMUcraft-Preview.mrpack` into a separate instance. | The local profile and file hashes were checked. Client load/save validation is still pending. |
| You use Prism Launcher | Use Add Instance → Import and select the downloaded `.mrpack`. | [Prism officially supports this format](https://prismlauncher.org/wiki/help-pages/Zip-import/); CMUcraft has not been playtested there. |
| Your launcher documents `.mrpack` import | Import the preview into a new instance and retain its pinned versions. | Format support alone does not certify this pack. Report the launcher/version when testing. |
| Your launcher does not import `.mrpack` | Prepare a separate Java 1.16.5 / Forge 36.2.42 game directory and install the pinned mods and worlds manually. | This is a manual setup route, not a verified one-click installer. |
| You just want to help with campus references | Look at the repository images and open a focused issue. | No launcher, Minecraft installation or Python is needed. Repository access is still required. |

Do not rename a worlds ZIP to `.mrpack` and expect it to become a modpack. The [Modrinth format](https://support.modrinth.com/en/articles/8802351-modrinth-modpack-format-mrpack) contains an index with dependencies and download hashes, plus override files. It is not a bundled copy of every required mod.

## Manual setup

This route assumes you already know how your launcher installs Forge and selects a separate game directory. If you do not, ask for setup help in an issue rather than changing your main Minecraft installation.

1. Create a separate **Minecraft Java 1.16.5 / Forge 36.2.42** instance or game directory. Use your launcher's supported Java configuration for that combination; there is no verified cross-platform Java prescription for this pack yet.
2. Install the six exact mod versions in the [mod list](../modpack/README.md) into that instance's `mods` folder. Use their official download sources. The exact file URLs and hashes are in [`modrinth.index.json`](../modpack/modrinth.index.json). Do not substitute a Fabric build or simply select each mod's newest version.
3. Download `CMUcraft-Preview-Worlds.zip` from the [preview release](https://github.com/Schrodinger39/CMUcraft/releases/tag/v0.3.0-preview). Extract the two world folders into that instance's `saves` folder. Each world folder should directly contain `level.dat` and `region/`, without another nested world folder.
4. Keep every `.mcc` file inside `region/`. The Hunt model uses these external chunks for dense detail.
5. Launch the selected instance and confirm the six mods appear before opening Hunt. Choose **Hunt Detail Preview** or **Campus Preview (Legacy Geometry)** in Singleplayer.

Hunt depends on Chisels & Bits. Do not open and save it without that mod. Use a copy when testing, and do not downgrade a save that another game version has upgraded.

## If you get stuck

- **The world is missing:** check the selected instance's game directory and the nesting of the save folder. Different launcher profiles may have different `saves` folders.
- **A mod download fails:** record which file and download source failed. A format-compatible launcher may still encounter a blocked or unavailable upstream download.
- **The campus looks rough:** make sure you know which world you selected. The campus-wide world uses legacy geometry; only the separate Hunt specimen has the current detail work.
- **The map starts blank:** Xaero's World Map fills as chunks are explored. This is not a prefilled campus atlas.
- **The game crashes or details disappear:** stop using that test copy and report the launcher, OS, Minecraft/Forge versions, exact world and relevant sanitized error lines. The pack has not yet passed a complete client save/reload test.

There is no public multiplayer server or shared live building session yet. Installing the pack does not connect you to other contributors.
