import nibabel as nib
import numpy as np
import pytest


@pytest.fixture
def write_seg(tmp_path):
    """Write `data` as a NIfTI file with the given voxel size and return its path."""

    def _write(data, zooms=(1, 1, 1), name="seg.nii.gz"):
        path = str(tmp_path / name)
        nib.save(nib.Nifti1Image(np.asarray(data, dtype=np.int16), np.diag([*zooms, 1])), path)
        return path

    return _write
