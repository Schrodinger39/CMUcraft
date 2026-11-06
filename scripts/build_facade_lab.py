"""Export a small fin-and-glass specimen for mod compatibility testing.
Dimensions are experimental. The PNG shows geometry with preview swatches,
not Minecraft lighting or a certified match to Hunt."""

from pathlib import Path
import argparse, json
import numpy as np
import nbtlib as n
from cmucraft.chisel import encode
from cmucraft.world import write_world
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, default=Path("build/facade-lab"))
a = p.parse_args()
# Six metres wide, four metres tall; sixteen detail voxels per metre.
# Historic five-foot fin spacing is an evidence-backed starting point, not a
# measured current spacing. Projection/taper are explicitly modeling hypotheses.
width, height = 96, 64
micro = np.zeros((height, 16, width), dtype=np.uint8)
micro[:, 14:, :] = 2
for x in range(width):
    u = (x + 0.5) / 16
    if min(u % 1.524, 1.524 - u % 1.524) < 0.075:
        for y in range(height):
            front = round(2 + max(0, y / 16 - 2.5) * 4)
            micro[y, front:14, x] = 1
# Thin transoms; no full-block-wide silver mullions.
micro[0:2, 13:, :] = 1
micro[-2:, 13:, :] = 1
palette = ["minecraft:air", "minecraft:iron_block", "minecraft:glass"]
world_palette = ["minecraft:air", "minecraft:stone", "minecraft:smooth_stone"]
volume = np.zeros((64, 32, 32), dtype=np.uint8)
volume[:31] = 1
volume[31] = 2
entities = []
for by in range(4):
    for bx in range(6):
        block, entity = encode(
            micro[by * 16 : (by + 1) * 16, :, bx * 16 : (bx + 1) * 16],
            palette,
            (12 + bx, 32 + by, 18),
        )
        if block not in world_palette:
            world_palette.append(block)
        volume[32 + by, 18, 12 + bx] = world_palette.index(block)
        entities.append(entity)
write_world(
    volume, world_palette, a.output / "world", [15, 33, 12], extra_entities=entities
)
f = n.load(a.output / "world/level.dat")
f["Data"]["LevelName"] = n.String("CMUcraft - Facade Lab (Unverified)")
f.save()
np.savez_compressed(a.output / "facade_geometry.npz", voxels=micro)
# Orthographic oblique pixel render from the actual microvoxel geometry.
im = Image.new("RGB", (1050, 760), "#e5e9eb")
d = ImageDraw.Draw(im)
colors = {1: (214, 218, 221), 2: (83, 121, 133)}
for z in range(15, -1, -1):
    for y in range(height):
        for x in range(width):
            material = int(micro[y, z, x])
            if not material:
                continue
            px = 65 + x * 9 + z * 3
            py = 655 - y * 8 - z * 2
            c = colors[material]
            shade = 0.8 + 0.2 * (16 - z) / 16
            d.rectangle((px, py - 8, px + 9, py), fill=tuple(int(v * shade) for v in c))
d.rectangle((0, 0, 1050, 95), fill="#f7f5ee")
d.text(
    (25, 18),
    "Facade detail experiment / 1:16 block resolution",
    font=ImageFont.load_default(size=26),
    fill="#233d36",
)
d.text(
    (25, 58),
    "Geometry render, not a game screenshot or an approved Hunt facade",
    font=ImageFont.load_default(size=17),
    fill="#52625e",
)
d.text(
    (25, 720),
    "6 m panel | silver fins and glazing | runtime validation pending",
    font=ImageFont.load_default(size=18),
    fill="#233d36",
)
im.save(a.output / "facade_geometry.png")
report = {
    "name": "Hunt-inspired facade detail experiment",
    "status": "not approved; runtime and visual validation pending",
    "world_scale": "1 block per metre",
    "detail_resolution_m": 1 / 16,
    "panel_dimensions_m": [6, 4, 1],
    "fin_pitch_m": 1.524,
    "fin_pitch_source": "Historical 1961 description; current facade measurement still required",
    "hypotheses": [
        "fin thickness",
        "fin taper/projection",
        "sample panel height",
        "Minecraft material appearance",
    ],
    "references": [
        "https://iiif.library.cmu.edu/file/Charette_Vol41_No10_Oct1961/Charette_Vol41_No10_Oct1961.pdf",
        "https://library.cmu.edu/about/news/2024-11/hunt-library",
    ],
    "mod": "Chisels & Bits 1.0.63 for Forge 1.16.5",
    "block_entities": len(entities),
    "runtime_test_passed": False,
}
(a.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(a.output)
