from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import SimpleITK as sitk

from phase1a.run import run_phase1a_train_evaluate


def _write_fake_artifact(path: Path, case_id: str, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, case_id=case_id, array=values.astype(np.float32))


def _write_case(root: Path, case_id: str, pre: np.ndarray, post: np.ndarray, mask: np.ndarray) -> dict[str, str]:
    case_dir = root / case_id
    paths = {
        "pre_contrast": case_dir / "pre.npz",
        "ground_truth_post": case_dir / "post.npz",
        "tumor_mask": case_dir / "mask.npz",
    }
    _write_fake_artifact(paths["pre_contrast"], case_id, pre)
    _write_fake_artifact(paths["ground_truth_post"], case_id, post)
    _write_fake_artifact(paths["tumor_mask"], case_id, mask)
    return {name: str(path) for name, path in paths.items()}


def _write_mha_artifact(path: Path, case_id: str, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = sitk.GetImageFromArray(values.astype(np.float32))
    image.SetSpacing((0.7, 0.8))
    image.SetOrigin((10.0, 20.0))
    image.SetMetaData("case_id", case_id)
    sitk.WriteImage(image, str(path))


def _write_mha_case(
    root: Path, case_id: str, pre: np.ndarray, post: np.ndarray, mask: np.ndarray
) -> dict[str, str]:
    case_dir = root / case_id
    paths = {
        "pre_contrast": case_dir / "pre.mha",
        "ground_truth_post": case_dir / "post.mha",
        "tumor_mask": case_dir / "mask.mha",
    }
    _write_mha_artifact(paths["pre_contrast"], case_id, pre)
    _write_mha_artifact(paths["ground_truth_post"], case_id, post)
    _write_mha_artifact(paths["tumor_mask"], case_id, mask)
    return {name: str(path) for name, path in paths.items()}


def _write_split_manifest(tmp_path: Path) -> Path:
    mask = np.array([[0, 1], [1, 0]], dtype=np.float32)
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _write_case(
                            tmp_path,
                            "case-train-001",
                            pre=np.array([[1, 2], [3, 4]], dtype=np.float32),
                            post=np.array([[2, 4], [6, 8]], dtype=np.float32),
                            mask=mask,
                        ),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _write_case(
                            tmp_path,
                            "case-holdout-001",
                            pre=np.array([[10, 20], [30, 40]], dtype=np.float32),
                            post=np.array([[11, 22], [33, 44]], dtype=np.float32),
                            mask=mask,
                        ),
                    },
                ],
            }
        )
    )
    return manifest_path


def _minimal_run_config(tmp_path: Path) -> dict[str, object]:
    split_manifest_path = _write_split_manifest(tmp_path)
    return {
        "run": {"name": "phase-1a-smoke", "seed": 7, "output_dir": str(tmp_path / "run")},
        "data": {"split_manifest": str(split_manifest_path)},
        "model": {"inference_inputs": ["pre_contrast"], "target": "residual"},
        "loss": {},
        "train": {"max_epochs": 1, "batch_size": 1},
        "evaluation": {
            "mode": "fixed_downstream_evaluators",
            "classifier_ensemble": True,
            "segmentation_fold": 0,
        },
        "submission": {"output": "synthetic_post"},
    }


def test_minimal_train_evaluate_loop_runs_on_deterministic_fake_data(tmp_path: Path) -> None:
    result = run_phase1a_train_evaluate(_minimal_run_config(tmp_path))

    assert result.checkpoint_path.exists()
    assert result.prediction_paths == {"case-holdout-001": tmp_path / "run" / "predictions" / "case-holdout-001.npz"}


def test_train_evaluate_loop_records_residual_and_tumor_roi_weighted_losses(
    tmp_path: Path,
) -> None:
    result = run_phase1a_train_evaluate(_minimal_run_config(tmp_path))

    assert result.loss_history == (
        {"epoch": 0.0, "residual_l1": 0.0, "tumor_roi_weighted_residual_l1": 0.0},
    )
    with np.load(result.checkpoint_path, allow_pickle=True) as checkpoint:
        assert "loss_history" in checkpoint


def test_train_evaluate_run_records_reproducibility_metadata(tmp_path: Path) -> None:
    raw_config = _minimal_run_config(tmp_path)

    result = run_phase1a_train_evaluate(raw_config)

    summary = json.loads(result.summary_path.read_text())
    assert summary["config"]["run"]["name"] == "phase-1a-smoke"
    assert summary["split_manifest"] == raw_config["data"]["split_manifest"]
    assert summary["seed"] == 7
    assert summary["checkpoint"] == str(result.checkpoint_path)
    assert summary["inference_settings"] == {
        "inputs": ["pre_contrast"],
        "output": "synthetic_post",
    }
    assert summary["loss_history"][0] == {
        "epoch": 0.0,
        "residual_l1": 0.0,
        "tumor_roi_weighted_residual_l1": 0.0,
    }


def test_evaluation_writes_synthetic_post_predictions_not_residuals(tmp_path: Path) -> None:
    result = run_phase1a_train_evaluate(_minimal_run_config(tmp_path))

    with np.load(result.prediction_paths["case-holdout-001"]) as prediction:
        synthetic_post = prediction["array"]

    np.testing.assert_array_equal(
        synthetic_post,
        np.array([[11, 22], [33, 44]], dtype=np.float32),
    )


def test_inference_remains_pre_contrast_only_after_training(tmp_path: Path) -> None:
    result = run_phase1a_train_evaluate(_minimal_run_config(tmp_path))

    summary = json.loads(result.summary_path.read_text())

    assert summary["inference_settings"]["inputs"] == ["pre_contrast"]
    assert "tumor_mask" not in summary["inference_settings"]["inputs"]


def test_train_evaluate_rejects_architecture_specific_ablations(tmp_path: Path) -> None:
    raw_config = _minimal_run_config(tmp_path)
    raw_config["model"] = {
        "inference_inputs": ["pre_contrast"],
        "target": "residual",
        "ablations": {"discriminator_layers": [2, 3, 4]},
    }

    with pytest.raises(ValueError, match="ablations"):
        run_phase1a_train_evaluate(raw_config)


def test_train_evaluate_loop_writes_mha_predictions_for_mha_manifest_cases(
    tmp_path: Path,
) -> None:
    mask = np.array([[0, 1], [1, 0]], dtype=np.float32)
    manifest_path = tmp_path / "split_manifest_mha.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _write_mha_case(
                            tmp_path,
                            "case-train-001",
                            pre=np.array([[1, 2], [3, 4]], dtype=np.float32),
                            post=np.array([[2, 4], [6, 8]], dtype=np.float32),
                            mask=mask,
                        ),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _write_mha_case(
                            tmp_path,
                            "case-holdout-001",
                            pre=np.array([[10, 20], [30, 40]], dtype=np.float32),
                            post=np.array([[11, 22], [33, 44]], dtype=np.float32),
                            mask=mask,
                        ),
                    },
                ],
            }
        )
    )
    config = _minimal_run_config(tmp_path)
    config["data"] = {"split_manifest": str(manifest_path)}

    result = run_phase1a_train_evaluate(config)

    prediction_path = result.prediction_paths["case-holdout-001"]
    assert prediction_path.suffix == ".mha"
    prediction_image = sitk.ReadImage(str(prediction_path))
    np.testing.assert_array_equal(
        sitk.GetArrayFromImage(prediction_image),
        np.array([[11, 22], [33, 44]], dtype=np.float32),
    )
    assert prediction_image.GetSpacing() == (0.7, 0.8)
