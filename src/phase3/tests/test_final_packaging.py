from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import SimpleITK as sitk

from phase3.packaging import validate_final_packaging


def _write_mha(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = sitk.GetImageFromArray(np.ones((2, 2), dtype=np.float32))
    sitk.WriteImage(image, str(path))


def test_final_packaging_accepts_single_packaged_weight_strategy_and_mha_output(tmp_path: Path) -> None:
    output_path = tmp_path / "output" / "images" / "synthetic-contrast-dce-mri-slice-breast" / "output.mha"
    _write_mha(output_path)

    result = validate_final_packaging(
        output_path=output_path,
        output_slug="synthetic-contrast-dce-mri-slice-breast",
        weight_strategy={"packaged_weights": "models/checkpoint.npz", "model_upload_path": None},
        runtime_checks={"non_root": True, "writable_output": True, "memory_gb": 16, "network": "none"},
    )

    assert result["schema_version"] == "phase3-final-packaging-v1"
    assert result["output"] == {"slug": "synthetic-contrast-dce-mri-slice-breast", "readable_mha": True, "dtype": "float32", "finite": True}
    assert result["weight_strategy"] == {"packaged_weights": "models/checkpoint.npz", "model_upload_path": None}


def test_final_packaging_rejects_mixed_weight_strategies(tmp_path: Path) -> None:
    output_path = tmp_path / "output.mha"
    _write_mha(output_path)

    with pytest.raises(ValueError, match="exactly one model-weight loading strategy"):
        validate_final_packaging(
            output_path=output_path,
            output_slug="synthetic-contrast-dce-mri-slice-breast",
            weight_strategy={"packaged_weights": "models/checkpoint.npz", "model_upload_path": "/opt/ml/model"},
            runtime_checks={"non_root": True, "writable_output": True, "memory_gb": 16, "network": "none"},
        )


def test_final_packaging_rejects_wrong_output_slug_or_runtime_network(tmp_path: Path) -> None:
    output_path = tmp_path / "output.mha"
    _write_mha(output_path)

    with pytest.raises(ValueError, match="output slug"):
        validate_final_packaging(
            output_path=output_path,
            output_slug="wrong-slug",
            weight_strategy={"packaged_weights": "models/checkpoint.npz", "model_upload_path": None},
            runtime_checks={"non_root": True, "writable_output": True, "memory_gb": 16, "network": "none"},
        )

    with pytest.raises(ValueError, match="runtime network"):
        validate_final_packaging(
            output_path=output_path,
            output_slug="synthetic-contrast-dce-mri-slice-breast",
            weight_strategy={"packaged_weights": "models/checkpoint.npz", "model_upload_path": None},
            runtime_checks={"non_root": True, "writable_output": True, "memory_gb": 16, "network": "enabled"},
        )
