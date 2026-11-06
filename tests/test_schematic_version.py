"""Regression tests for schematic version.
Fixtures are test inputs, not substitute campus survey data. Assertions state
the invariant being checked; passing them does not certify visual fidelity."""

import nbtlib
import numpy as np
from cmucraft.schematic import export


def test_schematic_targets_installed_minecraft(tmp_path):
    path = tmp_path / "survey.schem"
    export(np.zeros((8, 8), dtype=np.int16), path)
    assert int(nbtlib.load(path)["DataVersion"]) == 2586
