"""Phase 1B ablation runner and audit summary interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

CHEAP_METRIC_GROUPS = ("image_fidelity", "tumor_roi_realism")
FULL_METRIC_GROUPS = (
    "image_fidelity",
    "tumor_roi_realism",
    "classification_utility",
    "segmentation_utility",
)


class Phase1BEvaluator(Protocol):
    def evaluate(
        self,
        candidate: str,
        metric_groups: tuple[str, ...],
        fixed_settings: dict[str, object],
    ) -> dict[str, dict[str, object]]:
        """Return per-metric-group candidate/baseline summaries."""


def run_phase1b_ablation(
    *,
    config: dict[str, object],
    evaluator: Phase1BEvaluator,
    output_path: str | Path,
) -> dict[str, object]:
    """Run a Phase 1B ablation evaluator and write a stable audit summary."""
    ablation = _section(config, "ablation")
    run_metadata = _section(config, "run_metadata")
    stage = str(ablation.get("selection_stage"))
    metric_groups = _metric_groups_for_stage(stage)
    fixed_settings = _fixed_evaluator_settings(config)
    candidate = str(ablation.get("model_family"))
    metrics = evaluator.evaluate(candidate, metric_groups, fixed_settings)
    summary: dict[str, object] = {
        "schema_version": "phase1b-ablation-summary-v1",
        "stage": stage,
        "metric_groups": list(metric_groups),
        "fixed_evaluator_settings": fixed_settings,
        "candidate": candidate,
        "metrics": metrics,
        "group_regressions": _group_regressions(metrics),
        "audit": {
            "config": run_metadata.get("config"),
            "split": run_metadata.get("split"),
            "model_variant": run_metadata.get("model_variant"),
            "loss_weights": run_metadata.get("loss_weights"),
            "augmentation_settings": run_metadata.get("augmentation_settings"),
            "checkpoint_hash": run_metadata.get("checkpoint_hash"),
        },
    }
    if metric_groups == FULL_METRIC_GROUPS:
        summary["promotion_summary"] = {
            "metric_groups": metrics,
            "config": {"path": run_metadata.get("config")},
            "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
            "model_hash": run_metadata.get("checkpoint_hash"),
        }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _section(config: dict[str, object], name: str) -> dict[str, object]:
    section = config.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"{name} section is required")
    return section


def _metric_groups_for_stage(stage: str) -> tuple[str, ...]:
    if stage == "early":
        return CHEAP_METRIC_GROUPS
    if stage == "shortlist":
        return FULL_METRIC_GROUPS
    raise ValueError("Phase 1B stage must be early or shortlist")


def _fixed_evaluator_settings(config: dict[str, object]) -> dict[str, object]:
    evaluation = _section(config, "evaluation")
    settings = {
        "classifier_ensemble": bool(evaluation.get("classifier_ensemble")),
        "segmentation_fold": int(evaluation.get("segmentation_fold", -1)),
    }
    if evaluation.get("mode") != "fixed_downstream_evaluators" or settings != {
        "classifier_ensemble": True,
        "segmentation_fold": 0,
    }:
        raise ValueError("Phase 1B runner requires fixed evaluator settings")
    return settings


def _group_regressions(metrics: dict[str, dict[str, object]]) -> list[str]:
    regressions: list[str] = []
    for group_name, group in metrics.items():
        if _relative_worsening(group) > 0.05:
            regressions.append(group_name)
    return regressions


def _relative_worsening(group: dict[str, object]) -> float:
    candidate = float(group["candidate"])
    baseline = float(group["baseline"])
    higher_is_better = bool(group["higher_is_better"])
    if higher_is_better:
        return (baseline - candidate) / abs(baseline)
    return (candidate - baseline) / abs(baseline)
