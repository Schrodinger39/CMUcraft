# CMUcraft Architecture Workbench

This is a construction and calibration environment, **not a completed realistic campus**.
Contributor: Chris Yu. Third-party mods retain their own authorship and licenses.

## Pinned runtime

Minecraft Java 1.16.5 + Forge 36.2.42. Do not substitute Fabric mods or copy mods from unrelated instances.

| Mod | Version | Purpose | Upstream |
| --- | --- | --- | --- |
| WorldEdit | 7.2.5 | Building editing and schematics | [EngineHub](https://enginehub.org/worldedit) |
| Chisels & Bits | 1.0.63 | Sub-block architectural details | [Official file](https://www.curseforge.com/minecraft/mc-mods/chisels-bits/files/3593643) |
| Xaero's Minimap | 26.6.0 | Corner map and waypoints | [Xaero96](https://modrinth.com/mod/xaeros-minimap) |
| Xaero's World Map | 1.47.0 | Explored-world map (default M key) | [Xaero96](https://modrinth.com/mod/xaeros-world-map) |
| XaeroLib | 1.7.3 | Required shared library | [Xaero96](https://modrinth.com/mod/xaerolib) |
| FerriteCore | 2.1.1 Forge | Memory optimization | [Project](https://modrinth.com/mod/ferrite-core) |

No shader, texture pack, or automatic facade reconstruction is included. Installing a detailing mod does not add details to existing buildings. Chiseled blocks require the matching mod on clients and servers; WorldEdit and FerriteCore are pinned in this workbench for reproducibility.

## Installation

Import `CMUcraft-Workbench.mrpack` as a **new instance** in a launcher that supports `.mrpack`; HMCL is not required. For the Hunt and campus previews, choose `CMUcraft-Preview.mrpack` instead. See [launcher options](../docs/LAUNCHERS.md) for format support, the manual route and unverified configurations. The package pins mod URLs and hashes; it does not redistribute Minecraft or Forge game binaries. Keep the launcher-created runtime. Do not overlay an existing instance.

The delivery computer has a separate local profile named `CMUcraft-Architecture-1.16.5`. Choose that exact name. The original `1.16.5` profile does not load these installed mods. Its saves have not been overwritten.

The included `CMUcraft - Scale Calibration` world contains nominal rooms at three scales. Only the 1 block/metre case matches the default player scale; the larger rooms do not change player size. It is not a campus model.

## Verification status

JAR integrity and pinned versions were checked. WorldEdit and FerriteCore hashes were compared with published Modrinth metadata. The Chisels & Bits download was taken from the official CurseForge file; its recorded hashes pin that download, rather than claiming an independently published signature.

**Modded runtime, saving/reloading chiseled blocks, and multiplayer remain unverified.** A reported main-menu launch may have used the original profile. Do not interpret static checks as a crash-free guarantee.

Before distributing a finished world: launch the exact pack, confirm all six mods in the Mods menu, load a copied world, place a chiseled test block, save/quit/reload, and verify persistence. Check client/server matching versions before multiplayer. Keep backups; never downgrade an upgraded save.

```bash
python scripts/build_modpack.py
python scripts/verify_mods.py /path/to/instance
```

The portable package can be shared through repository releases. A hosted multiplayer server has not been configured.

## Current preview

`CMUcraft-Preview.mrpack` additionally includes the Hunt detail specimen and a legacy campus comparison save. Both have corrected vanilla dimension settings. The ordinary Workbench package contains only the calibration save. Xaero maps reveal terrain as it is explored; an empty world map on first load is expected.
