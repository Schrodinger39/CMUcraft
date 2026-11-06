"""Regression tests for structure parts.
Fixtures are test inputs, not substitute campus survey data. Assertions state
the invariant being checked; passing them does not certify visual fidelity."""

from pathlib import Path
from shapely.ops import unary_union
from cmucraft.osm import parse
from cmucraft.structure_parts import campus_parts


def test_split_gates_hillman_preserves_connector_without_ground_extrusion():
    source = Path(__file__).parents[1] / "data/raw/campus.osm"
    old, _ = parse(source)
    parent = next(f for f in old if f["id"] == "relation/21724638")
    buildings, connectors = campus_parts(source)
    bodies = [
        b["geometry"]
        for b in buildings
        if b["id"] in ("relation/21724637", "way/1569847706")
    ]
    assert len(bodies) == 2 and len(connectors) == 1
    whole = unary_union(bodies + [c["geometry"] for c in connectors])
    assert whole.symmetric_difference(parent["geometry"]).area < 1e-14
    assert all(
        c["deck_elevation_m"] is None and not c["ground_extrusion_allowed"]
        for c in connectors
    )
