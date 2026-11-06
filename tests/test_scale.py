"""Regression tests for scale.
Fixtures are test inputs, not substitute campus survey data. Assertions state
the invariant being checked; passing them does not certify visual fidelity."""

import pytest


def test_world_player_scale_must_match():
    from cmucraft.scale import Scale

    assert Scale(2).position(10, 20, 260, 240) == (20, 40, 40)
    with pytest.raises(ValueError):
        Scale(2).validate_player(1)
    Scale(1).validate_player(1)
