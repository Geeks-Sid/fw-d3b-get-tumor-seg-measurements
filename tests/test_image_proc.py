import math

import cv2
import numpy as np
import pytest

from fw_gear_functions.image_proc import (
    calculate_3d_volumes,
    calculate_cross_section_area_ellipse,
    find_largest_tumor_slice,
    find_major_minor_axes,
)

LABELS = {0: "background", 1: "enhancing", 2: "nonenhancing", 3: "cyst", 4: "edema"}


def disc(shape, center, radius):
    m = np.zeros(shape, np.uint8)
    cv2.circle(m, center, radius, 1, -1)
    return m


def test_3d_volumes_per_label_and_whole_tumor():
    mask = np.zeros((4, 4, 4))
    mask[0, 0, 0] = mask[1, 0, 0] = 1
    mask[2, 0, 0] = 3
    mask[3, 0, 0] = 5  # unmapped label still counts as tumor
    assert calculate_3d_volumes(mask, 2.0, LABELS) == {
        "whole_tumor": 8.0,
        "enhancing": 4.0,
        "nonenhancing": 0.0,
        "cyst": 2.0,
        "edema": 0.0,
    }


def test_3d_volumes_round_float_labels():
    mask = np.zeros((2, 2, 2))
    mask[0, 0, 0] = 0.9999999
    assert calculate_3d_volumes(mask, 1.0, LABELS)["enhancing"] == 1.0


def test_cross_section_area_is_ellipse_area_of_full_diameters():
    assert calculate_cross_section_area_ellipse(20, 10) == pytest.approx(math.pi * 10 * 5)


def test_fitted_circle_area_matches_pixel_area():
    mask = disc((100, 100), (50, 50), 20)
    _, axes, _ = find_major_minor_axes(mask)
    assert calculate_cross_section_area_ellipse(*axes) == pytest.approx(mask.sum(), rel=0.1)


def test_largest_slice_ignores_float_noise_in_labels():
    v = np.zeros((20, 20, 5))
    v[5:15, 5:15, 2] = 1.0000001  # 100 voxels
    v[0:2, 0:2, 1] = 2  # 4 voxels
    idx, sl = find_largest_tumor_slice(v)
    assert idx == 2
    assert sl.sum() == 100


def test_largest_slice_counts_labels_above_4_like_whole_tumor():
    v = np.zeros((20, 20, 3))
    v[0:6, 0:6, 0] = 5
    v[0:2, 0:2, 1] = 1
    idx, _ = find_largest_tumor_slice(v)
    assert idx == 0


def test_major_minor_axes_for_rectangle():
    m = np.zeros((20, 20), bool)
    m[3:15, 4:12] = True  # a rectangle outline is only 4 points with CHAIN_APPROX_SIMPLE
    _, axes, _ = find_major_minor_axes(m)
    assert max(axes) > min(axes) > 0


def test_major_minor_axes_uses_largest_region_only():
    m = disc((100, 100), (30, 30), 15) | disc((100, 100), (80, 80), 5)
    (cx, cy), axes, _ = find_major_minor_axes(m)
    assert (cx, cy) == pytest.approx((30, 30), abs=1)
    assert max(axes) == pytest.approx(30, abs=2)
