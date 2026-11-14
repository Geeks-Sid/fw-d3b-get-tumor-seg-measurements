from unittest.mock import MagicMock

import numpy as np
import pytest

import run as gear


@pytest.fixture(autouse=True)
def no_core_client(monkeypatch):
    monkeypatch.setattr("fw_gear_functions.parser.CoreClient", MagicMock())


def make_context(path, segmentation_type, info=None):
    inputs = {
        "input-file": {"hierarchy": {"id": "acq"}, "location": {"path": path}, "object": {"type": "nifti"}},
        "api-key": {"key": "host:key"},
    }
    context = MagicMock()
    context.get_input.side_effect = inputs.__getitem__
    context.config = {"segmentation_type": segmentation_type}
    session = MagicMock()
    session.reload.return_value = session
    session.info = {} if info is None else info
    context.client.get.return_value = session
    return context, session


def written_info(session):
    (info,), _ = session.update_info.call_args
    return info


@pytest.mark.parametrize(
    "name, segmentation_type, expected",
    [
        ("case_manual.nii.gz", 0, "manual"),
        ("CASE_PRED.nii.gz", 0, "model_predicted"),
        ("case_manual_pred.nii.gz", 0, "manual"),
        ("case.nii.gz", 1, "manual"),
        ("case_manual.nii.gz", 2, "model_predicted"),
    ],
)
def test_segmentation_type(write_seg, name, segmentation_type, expected):
    data = np.zeros((10, 10, 3))
    data[2:8, 2:8, 1] = 1
    context, session = make_context(write_seg(data, name=name), segmentation_type)

    assert gear.main(context) == 0
    assert list(written_info(session)["measurements"]["tumor_segm"]) == [expected]


def test_unknown_segmentation_type_fails_before_processing(tmp_path):
    context, session = make_context(str(tmp_path / "does_not_exist.nii.gz"), 0)
    with pytest.raises(ValueError, match="segmentation type"):
        gear.main(context)
    session.update_info.assert_not_called()


def test_existing_measurements_are_kept_and_same_type_replaced(write_seg):
    data = np.zeros((10, 10, 3))
    data[2:8, 2:8, 1] = 1
    info = {
        "keep": 1,
        "measurements": {
            "other": {"a": 1},
            "tumor_segm": {"manual": {"3d": {"old": 1}}, "model_predicted": {"3d": {"stale": 1}}},
        },
    }
    context, session = make_context(write_seg(data, name="x_pred.nii.gz"), 0, info)

    gear.main(context)

    written = written_info(session)
    assert written["keep"] == 1
    assert written["measurements"]["other"] == {"a": 1}
    assert written["measurements"]["tumor_segm"]["manual"] == {"3d": {"old": 1}}
    replaced = written["measurements"]["tumor_segm"]["model_predicted"]
    assert set(replaced) == {"3d", "2d"}
    assert "stale" not in replaced["3d"]
