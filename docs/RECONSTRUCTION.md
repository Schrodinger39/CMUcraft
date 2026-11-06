# Reconstruction acceptance requirements

The legacy v0.2 world failed the user's recognizability review. It must not be described as the realistic replacement.

## Per-building acceptance

Every delivered building needs a stable source ID, a verified identity, an independently checked footprint and orientation, supported height, and matching player/world scale. Preserve a single campus coordinate origin; do not move a building to make a local screenshot look right.

Exterior review requires reference/model comparisons for **materials and colors, window arrangement, roof silhouette, entrances, distinctive features, and terrain/bridge connections**. Generic boxes or repeated window patterns are not acceptable substitutes. Interiors may remain empty. Store reference URLs, dates, model views, reviewer notes and remaining uncertainty in the building record.

The source packets in `data/reference/buildings` are starting evidence, not approved architecture. Their context PNGs show geographic footprints only. The inventory is from 2022, with some buildings planned for future completion. Raw level strings such as `4+5` must not silently become four floors or a measured height.

## Position audit

`python -m cmucraft.layout_audit` compares the old exported building ID grid with the original OSM footprint raster. It can catch translation or source-cell loss, but cannot prove the OSM geometry or names are correct. The independent county comparison is a separate check; a merged historical county complex must not cause individual buildings to be moved toward its centroid.

Official reference map: [CMU visitor map, updated August 12, 2024](https://www.cmu.edu/sites/default/files/cmu-visit-site-files/2025-08/campus-map.pdf). Its approximate grid is useful for campus identity/context, not survey measurements.

## Current blocking findings

- Gates and Hillman were modeled as one combined shell; preserve independent building geometry and audit the connector separately.
- Phipps has overlapping source relations; v0.2 silently assigned overlap to the first record. It requires explicit resolution rather than source-order ownership.
- Hunt's metal/glass facade was replaced by generic walls. Its roof height is not established by the inventory level string.
- Smith Hall is an identity conflict: the 2022 inventory's Smith/EDSH in West Quad must not automatically supply properties for the southern OSM Smith Hall.
- Building foundations were flattened, hillside floor counts were estimated, and bridge elevations were guessed. These remain modeling defects to resolve.

## Release gate

```bash
python -m cmucraft.review
```

Exit code 2 means incomplete evidence or review, not a software crash. The gate currently fails intentionally. It cannot assess visual fidelity automatically; a human comparison and in-game walkthrough are still needed. No replacement campus ZIP should be labeled complete while these checks remain unresolved.

## Scale

Keep world, building, and avatar scales consistent. A blanket enlargement of buildings with the normal avatar would worsen proportions. The calibration world is a test instrument, not approval of any enlarged scale. Sub-block facade details can be modeled with the pinned Chisels & Bits version without moving the campus footprints.
