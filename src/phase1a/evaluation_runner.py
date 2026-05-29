"""Staged hold-out evaluation runner for Phase 1A candidates."""

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


class HoldoutEvaluator(Protocol):
    def evaluate(
        self,
        candidate: str,
        metric_groups: tuple[str, ...],
        fixed_settings: dict[str, object],
    ) -> dict[str, float]:
        """Return metric summary values for the requested groups."""


def run_staged_holdout_evaluation(
    *,
    candidates: list[str],
    stage: str,
    config: dict[str, object],
    evaluator: HoldoutEvaluator,
    output_path: str | Path,
    candidate_configs: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    """Run staged hold-out metrics and write promotion-gate-ready summary JSON."""
    metric_groups = _metric_groups_for_stage(stage)
    fixed_settings = _fixed_evaluator_settings(config)
    summary: dict[str, object] = {
        "stage": stage,
        "metric_groups": list(metric_groups),
        "fixed_evaluator_settings": fixed_settings,
        "candidates": [],
    }
    candidate_summaries = summary["candidates"]
    assert isinstance(candidate_summaries, list)
    for candidate in candidates:
        candidate_config = candidate_configs.get(candidate) if candidate_configs else None
        if candidate_config is not None:
            candidate_fixed_settings = _declared_evaluator_settings(candidate_config)
            if candidate_fixed_settings != fixed_settings:
                raise ValueError("fixed evaluator settings changed between candidates")
        metrics = evaluator.evaluate(candidate, metric_groups, fixed_settings)
        candidate_summaries.append({"name": candidate, "metrics": metrics})

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def _metric_groups_for_stage(stage: str) -> tuple[str, ...]:
    if stage == "early":
        return CHEAP_METRIC_GROUPS
    if stage == "shortlist":
        return FULL_METRIC_GROUPS
    raise ValueError("stage must be early or shortlist")


def _fixed_evaluator_settings(config: dict[str, object]) -> dict[str, object]:
    settings = _declared_evaluator_settings(config)
    if settings != {"classifier_ensemble": True, "segmentation_fold": 0}:
        raise ValueError("fixed evaluator settings must not change between candidates")
    return settings


def _declared_evaluator_settings(config: dict[str, object]) -> dict[str, object]:
    evaluation = config.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ValueError("evaluation config is required")
    if evaluation.get("mode") != "fixed_downstream_evaluators":
        raise ValueError("staged evaluation requires fixed_downstream_evaluators mode")
    return {
        "classifier_ensemble": bool(evaluation.get("classifier_ensemble")),
        "segmentation_fold": int(evaluation.get("segmentation_fold", -1)),
    }
