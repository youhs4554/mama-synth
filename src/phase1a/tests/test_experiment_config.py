from __future__ import annotations

from pathlib import Path

import pytest

from phase1a.config import validate_phase1a_config


def _minimal_config(split_manifest_path: Path) -> dict[str, object]:
    return {
        "run": {"name": "phase-1a-smoke", "seed": 7},
        "data": {"split_manifest": str(split_manifest_path)},
        "model": {
            "inference_inputs": ["pre_contrast"],
            "target": "residual",
        },
        "loss": {},
        "train": {"max_epochs": 1, "batch_size": 1},
        "evaluation": {
            "mode": "fixed_downstream_evaluators",
            "classifier_ensemble": True,
            "segmentation_fold": 0,
        },
        "submission": {"output": "synthetic_post"},
    }


def test_minimal_phase1a_config_declares_required_sections(tmp_path: Path) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")

    config = validate_phase1a_config(_minimal_config(split_manifest_path))

    assert config.section_names == (
        "run",
        "data",
        "model",
        "loss",
        "train",
        "evaluation",
        "submission",
    )


def test_phase1a_config_rejects_mask_conditioned_inference(tmp_path: Path) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["model"] = {
        "inference_inputs": ["pre_contrast", "tumor_mask"],
        "target": "residual",
    }

    with pytest.raises(ValueError, match="pre_contrast-only"):
        validate_phase1a_config(raw_config)


def test_phase1a_config_rejects_non_synthetic_post_submission_output(
    tmp_path: Path,
) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["submission"] = {"output": "predicted_residual"}

    with pytest.raises(ValueError, match="synthetic_post"):
        validate_phase1a_config(raw_config)


def test_phase1a_config_requires_residual_target_learning(tmp_path: Path) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["model"] = {
        "inference_inputs": ["pre_contrast"],
        "target": "post_contrast",
    }

    with pytest.raises(ValueError, match="residual"):
        validate_phase1a_config(raw_config)


def test_phase1a_config_rejects_changed_fixed_downstream_evaluator_setup(
    tmp_path: Path,
) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["evaluation"] = {
        "mode": "fixed_downstream_evaluators",
        "classifier_ensemble": True,
        "segmentation_fold": 1,
    }

    with pytest.raises(ValueError, match="fixed downstream evaluator"):
        validate_phase1a_config(raw_config)


def test_phase1a_config_rejects_implicit_evaluator_changes(tmp_path: Path) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["evaluation"] = {
        "mode": "custom_evaluator_settings",
        "classifier_ensemble": False,
        "segmentation_fold": 2,
    }

    with pytest.raises(ValueError, match="sensitivity_analysis"):
        validate_phase1a_config(raw_config)


def test_phase1a_config_allows_explicit_sensitivity_analysis_mode(
    tmp_path: Path,
) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["evaluation"] = {
        "mode": "sensitivity_analysis",
        "classifier_ensemble": False,
        "segmentation_fold": 2,
    }

    config = validate_phase1a_config(raw_config)

    assert config.raw["evaluation"] == raw_config["evaluation"]


def test_phase1a_config_defaults_to_tumor_mask_only_roi_weighting(
    tmp_path: Path,
) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")

    config = validate_phase1a_config(_minimal_config(split_manifest_path))

    assert config.raw["loss"]["roi_weighting"] == {
        "mode": "tumor_mask_only",
        "context": {"enabled": False},
    }


def test_phase1a_config_rejects_enabled_roi_context_by_default(
    tmp_path: Path,
) -> None:
    split_manifest_path = tmp_path / "split_manifest.json"
    split_manifest_path.write_text("{}")
    raw_config = _minimal_config(split_manifest_path)
    raw_config["loss"] = {
        "roi_weighting": {
            "mode": "tumor_mask_only",
            "context": {"enabled": True, "dilation_pixels": 3},
        }
    }

    with pytest.raises(ValueError, match="ROI context"):
        validate_phase1a_config(raw_config)
