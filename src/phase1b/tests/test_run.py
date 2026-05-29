from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from phase1b.run import main, run_phase1b_train_evaluate


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


def _write_split_manifest(tmp_path: Path) -> Path:
    mask = np.indices((8, 8)).sum(axis=0).astype(np.float32) % 2
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
                            pre=np.zeros((8, 8), dtype=np.float32),
                            post=np.full((8, 8), 0.25, dtype=np.float32),
                            mask=mask,
                        ),
                    },
                    {
                        "case_id": "case-train-002",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _write_case(
                            tmp_path,
                            "case-train-002",
                            pre=np.ones((8, 8), dtype=np.float32),
                            post=np.full((8, 8), 2.25, dtype=np.float32),
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
                            pre=np.ones((8, 8), dtype=np.float32),
                            post=np.full((8, 8), 2.0, dtype=np.float32),
                            mask=mask,
                        ),
                    },
                ],
            }
        )
    )
    return manifest_path


def _minimal_config(tmp_path: Path) -> dict[str, object]:
    output_dir = tmp_path / "run"
    split_manifest = _write_split_manifest(tmp_path)
    return {
        "run": {"name": "phase1b-unet-smoke", "seed": 7, "output_dir": str(output_dir)},
        "data": {"split_manifest": str(split_manifest)},
        "model": {"inference_inputs": ["pre_contrast"], "target": "residual", "base_channels": 4},
        "loss": {"roi_weighting": {"mode": "tumor_mask_only", "context": {"enabled": False}}},
        "train": {"max_epochs": 1, "batch_size": 1},
        "evaluation": {
            "mode": "fixed_downstream_evaluators",
            "classifier_ensemble": True,
            "segmentation_fold": 0,
        },
        "submission": {"output": "synthetic_post"},
        "ablation": {
            "model_family": "unet_residual_regressor",
            "loss_terms": ["residual_l1", "tumor_roi_weighted_residual_l1"],
            "augmentation_policy": "disabled",
            "selection_stage": "early",
        },
        "run_metadata": {
            "config": "configs/phase1b/unet_residual_smoke_v1.yaml",
            "split": str(split_manifest),
            "model_variant": "unet_residual_regressor",
            "loss_weights": {"tumor": 3.0},
            "augmentation_settings": {"enabled": False},
            "checkpoint_hash": "pending-smoke-run",
            "metric_summary": {},
        },
    }


def test_phase1b_train_evaluate_driver_writes_real_debug_artifacts(tmp_path: Path) -> None:
    result = run_phase1b_train_evaluate(_minimal_config(tmp_path))

    assert result.checkpoint_path == tmp_path / "run" / "checkpoint.npz"
    assert result.checkpoint_path.exists()
    assert result.prediction_paths == {"case-holdout-001": tmp_path / "run" / "predictions" / "case-holdout-001.npz"}
    assert result.run_summary_path.exists()
    assert result.ablation_summary_path.exists()

    summary = json.loads(result.run_summary_path.read_text(encoding="utf-8"))
    assert summary["command"] == "PYTHONPATH=src uv run python -m phase1b.run <config>"
    assert summary["inference_settings"] == {"inputs": ["pre_contrast"], "output": "synthetic_post"}
    assert summary["checkpoint_hash"].startswith("sha256:")
    assert summary["augmentation"] == {"enabled": False}
    assert summary["metrics"]["image_fidelity"]["higher_is_better"] is False
    assert summary["metrics"]["tumor_roi_realism"]["higher_is_better"] is False

    ablation_summary = json.loads(result.ablation_summary_path.read_text(encoding="utf-8"))
    assert ablation_summary["candidate"] == "unet_residual_regressor"
    assert ablation_summary["metric_groups"] == ["image_fidelity", "tumor_roi_realism"]
    assert ablation_summary["audit"]["checkpoint_hash"] == summary["checkpoint_hash"]


def test_phase1b_driver_applies_scanner_protocol_intensity_augmentation(tmp_path: Path) -> None:
    config = _minimal_config(tmp_path)
    config["run"] = {"name": "phase1b-unet-aug", "seed": 7, "output_dir": str(tmp_path / "aug-run")}
    config["augmentation"] = {
        "enabled": True,
        "seed": 13,
        "intensity_scale_range": [0.5, 0.5],
        "intensity_shift_range": [2.0, 2.0],
    }
    config["ablation"]["augmentation_policy"] = "scanner_protocol_intensity"  # type: ignore[index]
    config["run_metadata"]["augmentation_settings"] = config["augmentation"]  # type: ignore[index]

    result = run_phase1b_train_evaluate(config)

    summary = json.loads(result.run_summary_path.read_text(encoding="utf-8"))
    assert summary["augmentation"]["enabled"] is True
    assert summary["augmentation"]["policy"] == "scanner_protocol_intensity"
    assert summary["augmentation"]["train_cases"] == {
        "case-train-001": {"enabled": True, "scale": 0.5, "seed": 13, "shift": 2.0},
        "case-train-002": {"enabled": True, "scale": 0.5, "seed": 14, "shift": 2.0},
    }
    assert summary["config"]["run_metadata"]["augmentation_settings"]["enabled"] is True


@pytest.mark.parametrize("suffix", [".yaml", ".json"])
def test_phase1b_run_cli_loads_config_and_prints_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], suffix: str
) -> None:
    config = _minimal_config(tmp_path)
    config_path = tmp_path / f"phase1b{suffix}"
    if suffix == ".yaml":
        import yaml

        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    else:
        config_path.write_text(json.dumps(config), encoding="utf-8")

    assert main([str(config_path)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["checkpoint_path"] == str(tmp_path / "run" / "checkpoint.npz")
    assert output["run_summary_path"] == str(tmp_path / "run" / "run_summary.json")
    assert output["ablation_summary_path"] == str(tmp_path / "run" / "metrics" / "ablation_summary.json")
    assert output["canonical_command"] == f"PYTHONPATH=src uv run python -m phase1b.run {config_path}"
