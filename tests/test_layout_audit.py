"""Regression tests for layout audit.
Fixtures are test inputs, not substitute campus survey data. Assertions state
the invariant being checked; passing them does not certify visual fidelity."""

from pathlib import Path
import json
import numpy as np
from cmucraft.layout_audit import compare

ROOT = Path(__file__).parents[1]


def test_detects_translated_export():
    bs = json.loads((ROOT / "campus_artifacts/buildings.json").read_text())
    grid = np.load(ROOT / "campus_artifacts/building_grid.npy")
    original = compare(ROOT / "data/raw/campus.osm", bs, grid)
    moved = compare(ROOT / "data/raw/campus.osm", bs, np.roll(grid, 8, axis=1))
    assert original["buildings_outside_source"] == 0
    assert moved["buildings_outside_source"] > 100
    assert original["buildings_with_source_loss"] == 1
