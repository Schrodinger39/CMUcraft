"""Build a standalone, unapproved Hunt development world.
The source footprint stays in campus metres until the explicit local translation.
The roof fit is measured; facade and entrance dimensions include hypotheses.
Do not use this specimen as evidence that the full campus is complete."""

from pathlib import Path
import json, math, argparse
import numpy as np
from shapely.geometry import shape
from shapely import contains_xy
from cmucraft.world import write_world
from cmucraft.chisel import encode
import nbtlib as n

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("build/hunt-prototype"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
out = args.output
out.mkdir(parents=True, exist_ok=True)
record = json.loads((root / "data/reference/buildings/hunt-library.json").read_text())
g = shape(record["footprint_xz"])
# Preserve source rotation and metre dimensions. Standalone world has an explicit translation.
ox, oz = 384, 704
vertical_offset = 262
main_base = 294.5 - vertical_offset
main_eave = 312.0 - vertical_offset
palette = [
    "minecraft:air",
    "minecraft:stone",
    "minecraft:smooth_stone",
    "minecraft:iron_block",
    "minecraft:black_stained_glass",
]
bit_palette = [
    "minecraft:air",
    "minecraft:iron_block",
    "minecraft:black_stained_glass",
    "minecraft:light_gray_concrete",
    "minecraft:brown_terracotta",
    "minecraft:black_concrete",
]
volume = np.zeros((80, 128, 128), dtype=np.uint8)
volume[:32] = 1
volume[32] = 2
entities = []
microcache = {}
coords = np.array(g.exterior.coords[:-1])
segments = list(zip(coords, np.roll(coords, -1, axis=0)))
fit = json.loads((root / "data/reference/survey/hunt-roof-fit-2024.json").read_text())
origin = np.array(fit["basis_origin_xz"])
u = np.array(fit["basis_u"])
v = np.array(fit["basis_v"])
# Per-block local surface sampling retains the actual rotated perimeter at 6.25cm resolution.
a, b, c, d = g.bounds
for bz in range(math.floor(b), math.ceil(d)):
    for bx in range(math.floor(a), math.ceil(c)):
        xs = bx + (np.arange(16) + 0.5) / 16
        zs = bz + (np.arange(16) + 0.5) / 16
        xx, zz = np.meshgrid(xs, zs)
        inside = contains_xy(g, xx, zz)
        U = (xx - origin[0]) * u[0] + (zz - origin[1]) * u[1]
        V = (xx - origin[0]) * v[0] + (zz - origin[1]) * v[1]
        distance = np.full((16, 16), 1e9)
        along = np.zeros((16, 16))
        for start, end in segments:
            dx, dz = end - start
            length = np.hypot(dx, dz)
            u = ((xx - start[0]) * dx + (zz - start[1]) * dz) / length
            clipped = np.clip(u, 0, length)
            dist = np.hypot(
                xx - start[0] - clipped * dx / length,
                zz - start[1] - clipped * dz / length,
            )
            better = dist < distance
            along[better] = u[better]
            distance[better] = dist[better]
        wall = inside & (distance < 0.9)
        if not wall.any():
            continue
        glass = inside & (distance >= 0.70) & (distance < 0.825)
        fin = (
            np.minimum(np.mod(along, 1.524), 1.524 - np.mod(along, 1.524)) < 0.08
        ) & inside
        for by in range(math.floor(main_base), math.ceil(main_eave)):
            bits = np.zeros((16, 16, 16), dtype=np.uint8)
            for iy in range(16):
                yy = by + (iy + 0.5) / 16
                if not main_base <= yy < main_eave:
                    continue
                relative = yy - main_base
                bits[iy, glass] = 2
                # Photo-derived floor bands: double silver transoms and a low sill per bay.
                for band in [297.5, 301.5, 305.5, 309.5]:
                    if (
                        abs(yy + vertical_offset - band) < 0.14
                        or abs(yy + vertical_offset - (band + 0.55)) < 0.065
                        or abs(yy + vertical_offset - (band - 0.75)) < 0.065
                    ):
                        bits[iy, inside & (distance >= 0.61) & (distance < 0.825)] = 1
                # Taper upper fin projection, matching the characteristic profile qualitatively.
                outer_depth = max(0, (relative / (main_eave - main_base) - 0.72)) * 0.9
                bits[iy, fin & (distance >= outer_depth) & (distance < 0.825)] = 1
                if relative < 0.15 or main_eave - yy < 0.25:
                    bits[iy, wall] = 1
            # Ground-level doorway is defined in building axes, not an axis-aligned hole.
            for iy in range(16):
                yy = by + (iy + 0.5) / 16
                if yy < main_base + 2.6:
                    entry = (U >= 17.8) & (U <= 24.2) & (V >= 0) & (V < 1.2)
                    bits[iy, entry] = 0
                    glazing = (
                        entry & (V > 0.70) & (V < 0.825) & ~((U > 20.3) & (U < 21.7))
                    )
                    bits[iy, glazing] = 2
                    frames = glazing & (np.abs((U - 17.8) % 1.1) < 0.08)
                    bits[iy, frames] = 4
            if not bits.any():
                continue
            # Entry location from the OSM-based legacy entrance, width is still a modeling hypothesis.
            # Keep an opening under the canopy; do not invent furnished interiors.
            # The doorway dimensions remain a photo-derived modeling hypothesis.
            pos = (bx - ox, by, bz - oz)
            state, entity = encode(bits, bit_palette, pos)
            if state not in palette:
                palette.append(state)
            volume[by, bz - oz, bx - ox] = palette.index(state)
            entities.append(entity)
# Regularized 2024 survey fit. Flat lower deck and raised four-plane hip,
# rather than noisy isolated roof voxels. Roof metadata preserves held-out errors.
fit = json.loads((root / "data/reference/survey/hunt-roof-fit-2024.json").read_text())
origin = np.array(fit["basis_origin_xz"])
u = np.array(fit["basis_u"])
v = np.array(fit["basis_v"])
lo, hi = fit["hip_u_min_max_m"]
near, far = fit["hip_v_min_max_m"]
valid = np.zeros((128, 128), dtype=bool)
mask = valid.copy()
# Store detail blocks first so roof and facade pieces can merge at shared cells.
from cmucraft.chisel import decode_geometry

micro = {}
for ent in entities:
    ids, pal = decode_geometry(ent)
    lookup = np.array([bit_palette.index(name) for name in pal], dtype=np.uint8)
    micro[tuple(int(ent[k]) for k in ("x", "y", "z"))] = lookup[ids]
entities = []
for bz in range(math.floor(b), math.ceil(d)):
    for bx in range(math.floor(a), math.ceil(c)):
        xx, zz = np.meshgrid(
            bx + (np.arange(16) + 0.5) / 16, bz + (np.arange(16) + 0.5) / 16
        )
        inside = contains_xy(g, xx, zz)
        if not inside.any():
            continue
        U = (xx - origin[0]) * u[0] + (zz - origin[1]) * u[1]
        V = (xx - origin[0]) * v[0] + (zz - origin[1]) * v[1]
        edge = np.minimum.reduce([U - lo, hi - U, V - near, far - V])
        upper = edge >= 0
        roofheight = (
            fit["hip_eave_elevation_m"] + fit["hip_slope"] * edge - vertical_offset
        )
        for by in range(47, 55):
            yy = by + (np.arange(16) + 0.5) / 16
            # Thin lower deck, upper roof and vertical penthouse envelope remain hollow.
            deck = (yy[:, None, None] >= 47.75) & (yy[:, None, None] < 48) & inside
            top = (
                (yy[:, None, None] <= roofheight)
                & (yy[:, None, None] > roofheight - 0.1875)
                & inside
                & upper
            )
            edgewall = inside & upper & (edge < 0.1875)
            wall = (
                (yy[:, None, None] >= 48) & (yy[:, None, None] <= roofheight) & edgewall
            )
            bits = micro.get(
                (bx - ox, by, bz - oz), np.zeros((16, 16, 16), dtype=np.uint8)
            )
            bits[deck | top | wall] = 3
            if bits.any():
                micro[bx - ox, by, bz - oz] = bits
        valid[bz - oz, bx - ox] = True
        mask[bz - oz, bx - ox] = True
# Dark bronze canopy with an angled brown fascia, aligned to the real facade.
# Photo-derived dimensions are recorded as hypotheses pending entrance survey.
for bz in range(724, 746):
    for bx in range(421, 441):
        xx, zz = np.meshgrid(
            bx + (np.arange(16) + 0.5) / 16, bz + (np.arange(16) + 0.5) / 16
        )
        U = (xx - origin[0]) * u[0] + (zz - origin[1]) * u[1]
        V = (xx - origin[0]) * v[0] + (zz - origin[1]) * v[1]
        for by in range(35, 37):
            bits = micro.get(
                (bx - ox, by, bz - oz), np.zeros((16, 16, 16), dtype=np.uint8)
            )
            for iy in range(16):
                h = by + (iy + 0.5) / 16 - main_base
                if 3.75 < h < 3.95:
                    bits[(iy,)][(U > 16.5) & (U < 25.5) & (V > -3.4) & (V < 0.9)] = 5
                if 2.8 < h <= 3.75:
                    t = (h - 2.8) / 0.95
                    left = 17.5 - t
                    right = 24.5 + t
                    front = -2.5 - 0.8 * t
                    fascia = (
                        (U >= left)
                        & (U <= right)
                        & (V >= front)
                        & (V < 0.8)
                        & (
                            (V < front + 0.1875)
                            | (U < left + 0.1875)
                            | (U > right - 0.1875)
                        )
                    )
                    bits[iy, fascia] = 4
            if bits.any():
                micro[bx - ox, by, bz - oz] = bits
for pos, bits in micro.items():
    state, entity = encode(bits, bit_palette, pos)
    if state not in palette:
        palette.append(state)
    x, y, z = pos
    volume[y, z, x] = palette.index(state)
    entities.append(entity)
write_world(volume, palette, out / "world", [49, 34, 18], extra_entities=entities)
f = n.load(out / "world/level.dat")
f["Data"]["LevelName"] = n.String("CMUcraft - Hunt Exterior Prototype (Unverified)")
f.save()
np.savez_compressed(out / "geometry.npz", blocks=volume, palette=np.array(palette))
(out / "manifest.json").write_text(
    json.dumps(
        {
            "name": "Hunt exterior prototype",
            "status": "NOT APPROVED; not a replacement campus",
            "source_osm_id": record["osm_id"],
            "standalone_translation_xz_m": [ox, oz],
            "vertical_offset_m": vertical_offset,
            "world_scale_blocks_per_m": 1,
            "detail_resolution_m": 0.0625,
            "chiseled_blocks": len(entities),
            "base_elevation_hypothesis_m": 294.5,
            "eave_elevation_hypothesis_m": 312.0,
            "roof_source": "2024 USGS/PASDA surface candidates; regularized hip fit with held-out residuals",
            "roof_fit": fit,
            "roof_covered_cells": int(valid.sum()),
            "roof_footprint_cells": int(mask.sum()),
            "unverified": [
                "all-side facade matching",
                "entrance and canopy dimensions",
                "fin pitch and taper",
                "window/transom elevations",
                "canopy/door geometry from photographs",
                "roof material/shape interpretation",
                "mod runtime and save/reload",
            ],
            "references": [
                "https://library.cmu.edu/visit/hunt",
                "https://library.cmu.edu/about/news/2024-11/hunt-library",
            ],
        },
        indent=2,
    )
    + "\n"
)
print(
    "Built",
    len(entities),
    "sub-block facade blocks; roof coverage",
    valid.sum(),
    "/",
    mask.sum(),
    flush=True,
)
