import logging

import numpy as np
import pytest

from fw_gear_functions.main import run

NO_2D = {
    "major_axis": None,
    "minor_axis": None,
    "largest_slice_index": None,
    "cross_sectional_area": None,
}


def test_run_measures_volumes_in_mm3_and_2d_on_largest_slice(write_seg):
    data = np.zeros((20, 20, 5))
    data[4:14, 4:12, 2] = 1  # 80 voxels
    data[0:2, 0:2, 3] = 2
    three_d, two_d = run(write_seg(data, zooms=(1.5, 1.5, 3)))  # 6.75 mm³ per voxel

    assert three_d["enhancing"] == pytest.approx(80 * 6.75)
    assert three_d["nonenhancing"] == pytest.approx(4 * 6.75)
    assert three_d["whole_tumor"] == pytest.approx(84 * 6.75)
    assert two_d["largest_slice_index"] == 2
    assert two_d["major_axis"] >= two_d["minor_axis"] > 0
    assert two_d["cross_sectional_area"] > 0


def test_run_empty_mask_gives_zero_volumes_and_no_2d(write_seg, caplog):
    with caplog.at_level(logging.WARNING):
        three_d, two_d = run(write_seg(np.zeros((10, 10, 3))))
    assert set(three_d.values()) == {0}
    assert two_d == NO_2D
    assert "Could not calculate 2D measurements" in caplog.text


def test_run_tumor_too_small_for_ellipse_gives_no_2d(write_seg):
    data = np.zeros((10, 10, 3))
    data[4:6, 4:6, 1] = 1  # 4 boundary voxels, ellipse fit needs 5
    three_d, two_d = run(write_seg(data))
    assert three_d["whole_tumor"] == 4
    assert two_d == NO_2D
