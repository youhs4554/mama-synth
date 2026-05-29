from __future__ import annotations

import json

from phase1b.runner import run_phase1b_ablation


class FakeEvaluator:
    def __init__(self) -> None:
        self.calls = []

    def evaluate(self, candidate: str, metric_groups: tuple[str, ...], fixed_settings: dict[str, object]) -> dict[str, dict[str, object]]:
        self.calls.append((candidate, metric_groups, fixed_settings))
        return {
            group: {"candidate": 0.9, "baseline": 1.0, "higher_is_better": False}
            for group in metric_groups
        }


def _config(stage: str = "early") -> dict[str, object]:
    return {
        "run": {"name": "phase1b-smoke"},
        "data": {"split_manifest": "splits/debug.json"},
        "evaluation": {"mode": "fixed_downstream_evaluators", "classifier_ensemble": True, "segmentation_fold": 0},
        "ablation": {"model_family": "unet_residual_regressor", "selection_stage": stage},
        "run_metadata": {
            "config": "configs/phase1b/unet.yaml",
            "split": "splits/debug.json",
            "model_variant": "unet_residual_regressor",
            "loss_weights": {"tumor": 3.0},
            "augmentation_settings": {"enabled": False},
            "checkpoint_hash": "sha256:abc",
            "metric_summary": {},
        },
    }


def test_ablation_runner_returns_stable_early_metric_audit_summary(tmp_path) -> None:
    evaluator = FakeEvaluator()

    summary = run_phase1b_ablation(config=_config("early"), evaluator=evaluator, output_path=tmp_path / "summary.json")

    assert evaluator.calls == [
        (
            "unet_residual_regressor",
            ("image_fidelity", "tumor_roi_realism"),
            {"classifier_ensemble": True, "segmentation_fold": 0},
        )
    ]
    assert summary["schema_version"] == "phase1b-ablation-summary-v1"
    assert summary["stage"] == "early"
    assert summary["metric_groups"] == ["image_fidelity", "tumor_roi_realism"]
    assert summary["audit"] == {
        "config": "configs/phase1b/unet.yaml",
        "split": "splits/debug.json",
        "model_variant": "unet_residual_regressor",
        "loss_weights": {"tumor": 3.0},
        "augmentation_settings": {"enabled": False},
        "checkpoint_hash": "sha256:abc",
    }
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8")) == summary


def test_ablation_runner_reports_group_level_regressions(tmp_path) -> None:
    class RegressingEvaluator(FakeEvaluator):
        def evaluate(self, candidate: str, metric_groups: tuple[str, ...], fixed_settings: dict[str, object]) -> dict[str, dict[str, object]]:
            return {"image_fidelity": {"candidate": 1.2, "baseline": 1.0, "higher_is_better": False}}

    summary = run_phase1b_ablation(config=_config("early"), evaluator=RegressingEvaluator(), output_path=tmp_path / "summary.json")

    assert summary["group_regressions"] == ["image_fidelity"]


def test_ablation_runner_shortlist_summary_is_phase1a_promotion_compatible(tmp_path) -> None:
    summary = run_phase1b_ablation(config=_config("shortlist"), evaluator=FakeEvaluator(), output_path=tmp_path / "summary.json")

    assert summary["promotion_summary"]["metric_groups"].keys() == {
        "image_fidelity",
        "tumor_roi_realism",
        "classification_utility",
        "segmentation_utility",
    }
    assert summary["promotion_summary"]["config"] == {"path": "configs/phase1b/unet.yaml"}
    assert summary["promotion_summary"]["inference_settings"] == {"inputs": ["pre_contrast"], "output": "synthetic_post"}
    assert summary["promotion_summary"]["model_hash"] == "sha256:abc"
