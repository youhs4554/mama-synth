from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase1b.config import (
    PHASE1B_REQUIRED_RUN_METADATA_FIELDS,
    validate_phase1b_config,
    validate_phase1b_fixed_evaluator_compatibility,
)


def _touch_case_files(root: Path, case_id: str) -> dict[str, str]:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    paths = {
        "pre_contrast": case_dir / "pre.mha",
        "ground_truth_post": case_dir / "post.mha",
        "tumor_mask": case_dir / "mask.mha",
    }
    for path in paths.values():
        path.write_text("fake image")
    return {name: str(path) for name, path in paths.items()}


def _split_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "split.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "train-001"),
                    },
                    {
                        "case_id": "holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "holdout-001"),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _valid_config(tmp_path: Path) -> dict[str, object]:
    return {
        "run": {"name": "phase1b-unet-smoke", "seed": 7, "output_dir": str(tmp_path / "out")},
        "data": {"split_manifest": str(_split_manifest(tmp_path))},
        "model": {"inference_inputs": ["pre_contrast"], "target": "residual"},
        "loss": {"roi_weighting": {"mode": "tumor_mask_only", "context": {"enabled": False}}},
        "train": {"max_epochs": 1, "batch_size": 1},
        "evaluation": {"mode": "fixed_downstream_evaluators", "classifier_ensemble": True, "segmentation_fold": 0},
        "submission": {"output": "synthetic_post"},
        "ablation": {
            "model_family": "unet_residual_regressor",
            "loss_terms": ["residual_l1", "tumor_roi_weighted_residual_l1"],
            "augmentation_policy": "disabled",
            "selection_stage": "early",
        },
        "run_metadata": {
            "config": "configs/phase1b/unet.yaml",
            "split": "splits/debug.json",
            "model_variant": "unet_residual_regressor",
            "loss_weights": {"tumor": 3.0},
            "augmentation_settings": {"enabled": False},
            "checkpoint_hash": "sha256:abc123",
            "metric_summary": {"image_fidelity": {"mse": 1.0}},
        },
    }


def test_phase1b_config_reuses_phase1a_contract_and_records_ablation_dimensions(tmp_path: Path) -> None:
    config = validate_phase1b_config(_valid_config(tmp_path))

    assert config.phase1a.section_names == ("run", "data", "model", "loss", "train", "evaluation", "submission")
    assert config.ablation_dimensions == {
        "model_family": "unet_residual_regressor",
        "loss_terms": ["residual_l1", "tumor_roi_weighted_residual_l1"],
        "augmentation_policy": "disabled",
        "selection_stage": "early",
    }
    assert config.required_run_metadata_fields == PHASE1B_REQUIRED_RUN_METADATA_FIELDS


def test_phase1b_config_preserves_precontrast_residual_synthetic_post_contracts(tmp_path: Path) -> None:
    raw = _valid_config(tmp_path)
    raw["model"] = {"inference_inputs": ["pre_contrast", "tumor_mask"], "target": "residual"}

    with pytest.raises(ValueError, match="pre_contrast-only"):
        validate_phase1b_config(raw)


def test_phase1b_registry_rejects_unknown_or_incompatible_ablation(tmp_path: Path) -> None:
    raw = _valid_config(tmp_path)
    raw["ablation"] = {"model_family": "predicted_mask_conditioning", "loss_terms": [], "augmentation_policy": "disabled", "selection_stage": "early"}

    with pytest.raises(ValueError, match="unknown Phase 1B model_family"):
        validate_phase1b_config(raw)


def test_phase1b_rejects_fixed_evaluator_drift_between_candidates(tmp_path: Path) -> None:
    base = _valid_config(tmp_path / "base")
    candidate = _valid_config(tmp_path / "candidate")
    candidate["evaluation"] = {"mode": "fixed_downstream_evaluators", "classifier_ensemble": True, "segmentation_fold": 1}

    with pytest.raises(ValueError, match="fixed evaluator settings changed"):
        validate_phase1b_fixed_evaluator_compatibility(base, candidate)


def test_phase1b_requires_audit_run_metadata_fields(tmp_path: Path) -> None:
    raw = _valid_config(tmp_path)
    del raw["run_metadata"]["checkpoint_hash"]  # type: ignore[index]

    with pytest.raises(ValueError, match="checkpoint_hash"):
        validate_phase1b_config(raw)
