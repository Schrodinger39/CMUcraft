# CMUcraft

**Rebuilding CMU in Minecraft, just for fun.**

![Hunt area in the current Minecraft campus](docs/images/hunt-area-rough-in-game.png)

*Hunt area — rough, in-game. Screenshot by Chris Yu.*
[More campus screenshots](docs/GALLERY.md)

CMUcraft is an independent student project to recreate Carnegie Mellon's Pittsburgh
campus in Minecraft. We want to build a place we know, explore it with friends, and
make something fun together. The campus is still rough, and we'd love your help.

## Start with Hunt or CUC

Our first round focuses on **Hunt Library** and **Cohon University Center**.
Try a small exterior detail, share a reference, or tell us what the model misses.
You do not need Python, Git, or a commitment to build a whole building.

| Try this | What to share | Join here |
| --- | --- | --- |
| Hunt window-and-fin section | A small build or reference image, plus a sentence about your idea | [Hunt #3](https://github.com/Schrodinger39/CMUcraft/issues/3) |
| CUC entrance or facade | A photo/link and two or three observations; no Minecraft needed | [CUC #4](https://github.com/Schrodinger39/CMUcraft/issues/4) |

**[Download First Builds — Hunt + CUC](https://github.com/Schrodinger39/CMUcraft/releases/tag/builders-round1)**
· **[Short Builder guide](docs/BUILDERS.md)**

Import the `.mrpack` as a new instance in a compatible launcher. It includes both
trial worlds and the mod download list. You can try a design and post it in the
building's issue without waiting for a claim. If you want to take on a whole building,
let us know there so we can coordinate. We currently build in separate saves, not a shared server.

**Questions?** Ask Chris (@Schrodinger39) in [Hunt #3](https://github.com/Schrodinger39/CMUcraft/issues/3)
or [CUC #4](https://github.com/Schrodinger39/CMUcraft/issues/4). I check these issues
at least twice a week and usually reply within 3–4 days.

The downloads are early previews. A small C&B build has passed a local save-and-transfer
test; new installs and larger builds still need testing. [Testing notes](docs/BUILDER-VALIDATION.md).

## Just want to explore?

The [v0.3.0 preview](https://github.com/Schrodinger39/CMUcraft/releases/tag/v0.3.0-preview)
includes two separate worlds: **Campus Preview (Legacy Geometry)** for the campus
layout and **Hunt Detail Preview** for the more detailed Hunt experiment. The First
Builds download above uses the rough campus as its starting point.

You need Minecraft **Java 1.16.5 + Forge 36.2.42** and the included mod versions.
Use a separate instance and keep copies of your saves. Keep Chisels & Bits installed
so its details are preserved. Bedrock is not supported. HMCL is not required;
see [launcher help](docs/LAUNCHERS.md) for setup options.

## How it works

The first campus was generated from map footprints and terrain data, with one block
representing one metre. That gives us a starting layout; photos, measurements and
hand-built details help turn it into a place people recognize.

The repository includes the Python tools, 41 building reference packets and a separate
Hunt detail prototype. WorldEdit helps with editing, Chisels & Bits adds smaller
details, and Xaero's maps help you find your way around.

<details>
<summary>Hunt detail prototype — external render</summary>

![Hunt Library development geometry](audit/hunt-exterior-prototype.png)

A separate design experiment for Hunt's fins, glazing and roof. This is an external
render, not the building shown in the trial-world screenshot above.

</details>

## Read more

- [Contributing](CONTRIBUTING.md) and [future plans](ROADMAP.md)
- [Builder guide](docs/BUILDERS.md) and [building briefs](docs/buildings/hunt-library.md)
- [Developer setup](docs/DEVELOPMENT.md) and [code guide](docs/CODE_GUIDE.md)
- [Mod versions](modpack/README.md) and [compatibility notes](docs/BUILDER-COMPATIBILITY.md)
- [Kit maintenance](docs/BUILDER-MAINTENANCE.md), [survey methods](docs/SURVEY.md) and [building review](docs/RECONSTRUCTION.md)
- [Development journal](DEVLOG.md)

## Credits

Started by **[Chris Yu / Schrodinger39](https://github.com/Schrodinger39)**.
Contributors are credited in [CONTRIBUTORS.md](CONTRIBUTORS.md).

Code and documentation use the [MIT license](LICENSE). Map data is © OpenStreetMap
contributors under ODbL; other sources and mods retain their own licenses.
See [DATA_LICENSE.md](DATA_LICENSE.md) for details. This is not an official CMU project.
