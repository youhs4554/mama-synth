from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase1a.evaluation_runner import run_staged_holdout_evaluation


class MockEvaluator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...], dict[str, object]]] = []

    def evaluate(
        self,
        candidate: str,
        metric_groups: tuple[str, ...],
        fixed_settings: dict[str, object],
    ) -> dict[str, float]:
        self.calls.append((candidate, metric_groups, fixed_settings))
        return {group: float(index + 1) for index, group in enumerate(metric_groups)}


def _config() -> dict[str, object]:
    return {
        "evaluation": {
            "mode": "fixed_downstream_evaluators",
            "classifier_ensemble": True,
            "segmentation_fold": 0,
        }
    }


def test_early_stage_runs_cheap_metric_groups_only(tmp_path: Path) -> None:
    evaluator = MockEvaluator()

    summary = run_staged_holdout_evaluation(
        candidates=["candidate-a"],
        stage="early",
        config=_config(),
        evaluator=evaluator,
        output_path=tmp_path / "metrics.json",
    )

    assert evaluator.calls[0][1] == ("image_fidelity", "tumor_roi_realism")
    assert summary["candidates"][0]["name"] == "candidate-a"


def test_shortlist_stage_runs_all_metric_groups_with_fixed_settings(tmp_path: Path) -> None:
    evaluator = MockEvaluator()

    run_staged_holdout_evaluation(
        candidates=["candidate-a"],
        stage="shortlist",
        config=_config(),
        evaluator=evaluator,
        output_path=tmp_path / "metrics.json",
    )

    assert evaluator.calls[0][1] == (
        "image_fidelity",
        "tumor_roi_realism",
        "classification_utility",
        "segmentation_utility",
    )
    assert evaluator.calls[0][2] == {"classifier_ensemble": True, "segmentation_fold": 0}


def test_runner_rejects_changed_fixed_evaluator_settings_between_candidates(
    tmp_path: Path,
) -> None:
    changed_config = _config()
    changed_config["evaluation"] = {
        "mode": "fixed_downstream_evaluators",
        "classifier_ensemble": True,
        "segmentation_fold": 1,
    }

    with pytest.raises(ValueError, match="fixed evaluator settings changed"):
        run_staged_holdout_evaluation(
            candidates=["candidate-a", "candidate-b"],
            stage="shortlist",
            config=_config(),
            evaluator=MockEvaluator(),
            output_path=tmp_path / "metrics.json",
            candidate_configs={"candidate-b": changed_config},
        )


def test_metric_summary_is_written_in_stable_promotion_gate_format(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "metrics.json"

    summary = run_staged_holdout_evaluation(
        candidates=["candidate-a"],
        stage="early",
        config=_config(),
        evaluator=MockEvaluator(),
        output_path=output_path,
    )

    written = json.loads(output_path.read_text())
    assert written == summary
    assert set(written) == {
        "stage",
        "metric_groups",
        "fixed_evaluator_settings",
        "candidates",
    }
