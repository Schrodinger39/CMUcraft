"""Regression tests for lidar.
Fixtures are test inputs, not substitute campus survey data. Assertions state
the invariant being checked; passing them does not certify visual fidelity."""

import numpy as np
import pytest
from cmucraft.lidar import cell_quantile


def test_median_rejects_isolated_high_return_and_keeps_missing_cells():
    roof, count = cell_quantile(
        [0.2, 0.3, 0.4, 1.2], [0.2, 0.3, 0.4, 1.2], [10, 11, 99, 20], 4
    )
    assert roof[0, 0] == 11 and count[0, 0] == 3
    assert roof[1, 1] == 20 and np.isnan(roof[3, 3])


def test_points_do_not_wrap_across_extent_or_swap_axes():
    roof, count = cell_quantile([-0.1, 4, 2.2], [1, 1, 1.1], [999, 999, 12], 4)
    assert roof[1, 2] == 12 and count.sum() == 1
    assert np.isnan(roof[2, 1])


def test_empty_cloud_is_missing_not_zero_ground():
    roof, count = cell_quantile([], [], [], 4)
    assert np.isnan(roof).all() and count.sum() == 0


def test_invalid_quantile_rejected():
    with pytest.raises(ValueError):
        cell_quantile([0], [0], [0], 4, 2)


def test_vertical_feet_are_converted_independently_of_xy():
    from cmucraft.lidar import vertical_factor
    from pyproj import CRS

    crs = CRS.from_user_input("EPSG:6565+6360")
    assert vertical_factor(crs) == pytest.approx(1200 / 3937)
    assert 1000 * vertical_factor(crs) == pytest.approx(304.8006096012192)
    with pytest.raises(ValueError):
        vertical_factor(crs, "metres")
    with pytest.raises(ValueError):
        vertical_factor(CRS.from_epsg(32617))
    assert vertical_factor(CRS.from_epsg(32617), "metres") == 1
