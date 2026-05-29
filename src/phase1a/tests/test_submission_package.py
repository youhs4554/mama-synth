from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import SimpleITK as sitk

import pytest

from phase1a.submission import (
    package_phase1a_checkpoint,
    run_phase1a_submission_inference,
    run_phase1a_submission_smoke_test,
)


def _write_pre_contrast(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        case_id="case-001",
        array=np.array([[1, 2], [3, 4]], dtype=np.float32),
        metadata={"spacing": [1.0, 1.0], "origin": [0.0, 0.0]},
    )


def _write_pre_contrast_mha(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = sitk.GetImageFromArray(np.array([[1, 2], [3, 4]], dtype=np.float32))
    image.SetSpacing((0.7, 0.8))
    image.SetOrigin((10.0, 20.0))
    image.SetDirection((0.0, 1.0, 1.0, 0.0))
    image.SetMetaData("case_id", "case-001")
    image.SetMetaData("source_id", "source-a")
    sitk.WriteImage(image, str(path))


def _write_checkpoint(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, residual=np.ones((2, 2), dtype=np.float32))


def test_submission_inference_consumes_pre_contrast_input_only(tmp_path: Path) -> None:
    pre_path = tmp_path / "input" / "pre.npz"
    checkpoint_path = tmp_path / "checkpoint.npz"
    output_path = tmp_path / "output" / "synthetic_post.npz"
    _write_pre_contrast(pre_path)
    _write_checkpoint(checkpoint_path)

    run_phase1a_submission_inference(
        pre_contrast_path=pre_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )

    assert "tumor_mask" not in inspect.signature(run_phase1a_submission_inference).parameters
    assert output_path.exists()


def test_submission_inference_writes_challenge_style_mha_and_preserves_sitk_metadata(
    tmp_path: Path,
) -> None:
    pre_path = tmp_path / "input" / "images" / "pre-contrast-dce-mri-slice-breast" / "case.mha"
    checkpoint_path = tmp_path / "checkpoint.npz"
    output_path = tmp_path / "output" / "images" / "synthetic-contrast-dce-mri-slice-breast" / "output.mha"
    _write_pre_contrast_mha(pre_path)
    _write_checkpoint(checkpoint_path)

    run_phase1a_submission_inference(
        pre_contrast_path=pre_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )

    output_image = sitk.ReadImage(str(output_path))
    synthetic_post = sitk.GetArrayFromImage(output_image)
    np.testing.assert_array_equal(
        synthetic_post,
        np.array([[2, 3], [4, 5]], dtype=np.float32),
    )
    assert synthetic_post.dtype == np.float32
    assert output_image.GetSpacing() == (0.7, 0.8)
    assert output_image.GetOrigin() == (10.0, 20.0)
    assert output_image.GetDirection() == (0.0, 1.0, 1.0, 0.0)
    assert output_image.GetMetaData("case_id") == "case-001"
    assert output_image.GetMetaData("source_id") == "source-a"


def test_submission_output_is_readable_native_size_float32_and_finite(tmp_path: Path) -> None:
    pre_path = tmp_path / "input" / "pre.npz"
    checkpoint_path = tmp_path / "checkpoint.npz"
    output_path = tmp_path / "output" / "synthetic_post.npz"
    _write_pre_contrast(pre_path)
    _write_checkpoint(checkpoint_path)

    run_phase1a_submission_inference(
        pre_contrast_path=pre_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )

    with np.load(output_path, allow_pickle=True) as output:
        synthetic_post = output["array"]
    assert synthetic_post.shape == (2, 2)
    assert synthetic_post.dtype == np.float32
    assert np.isfinite(synthetic_post).all()


def test_submission_smoke_test_checks_soft_z_score_and_preserves_metadata(tmp_path: Path) -> None:
    pre_path = tmp_path / "input" / "pre.npz"
    checkpoint_path = tmp_path / "checkpoint.npz"
    output_path = tmp_path / "output" / "synthetic_post.npz"
    _write_pre_contrast(pre_path)
    _write_checkpoint(checkpoint_path)
    run_phase1a_submission_inference(
        pre_contrast_path=pre_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )

    result = run_phase1a_submission_smoke_test(
        pre_contrast_path=pre_path,
        output_path=output_path,
    )

    assert result.passed is True
    assert result.max_abs_value <= 50
    with np.load(output_path, allow_pickle=True) as output:
        metadata = output["metadata"].item()
    assert metadata == {"spacing": [1.0, 1.0], "origin": [0.0, 0.0]}


def test_checkpoint_is_submission_ready_only_after_passing_smoke_test(tmp_path: Path) -> None:
    pre_path = tmp_path / "input" / "pre.npz"
    checkpoint_path = tmp_path / "checkpoint.npz"
    output_path = tmp_path / "output" / "synthetic_post.npz"
    _write_pre_contrast(pre_path)
    np.savez(checkpoint_path, residual=np.full((2, 2), 100.0, dtype=np.float32))

    with pytest.raises(ValueError, match="smoke test"):
        package_phase1a_checkpoint(
            pre_contrast_path=pre_path,
            checkpoint_path=checkpoint_path,
            output_path=output_path,
        )
