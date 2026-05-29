from __future__ import annotations

import pytest

from phase3.selection import select_final_candidate


def _candidate(name: str, rank: float, groups: dict[str, float] | None = None) -> dict[str, object]:
    return {
        "name": name,
        "local_proxy_rank_mean": rank,
        "metric_group_worsening": groups or {
            "image_fidelity": 0.0,
            "tumor_roi_realism": 0.0,
            "classification_utility": 0.0,
            "segmentation_utility": 0.0,
        },
        "audit_complete": True,
    }


def test_final_selection_returns_no_candidate_when_ranking_table_is_empty() -> None:
    decision = select_final_candidate(candidates=[], validation_feedback=[])

    assert decision == {
        "schema_version": "phase3-final-selection-v1",
        "selected_candidate": None,
        "reason": "no promoted candidates available",
        "validation_feedback": [],
    }


def test_final_selection_chooses_best_noninferior_proxy_rank() -> None:
    decision = select_final_candidate(
        candidates=[_candidate("candidate-b", 2.0), _candidate("candidate-a", 1.0)],
        validation_feedback=[{"phase": "Validation", "note": "candidate-a submitted"}],
    )

    assert decision["selected_candidate"] == "candidate-a"
    assert decision["local_proxy_rank_mean"] == 1.0
    assert decision["validation_feedback"] == [{"phase": "Validation", "note": "candidate-a submitted"}]
    assert decision["validation_feedback_role"] == "official-phase evidence, not a substitute for local hold-out evaluation"


def test_final_selection_rejects_group_regression_over_margin() -> None:
    with pytest.raises(ValueError, match="non-inferiority"):
        select_final_candidate(
            candidates=[
                _candidate("bad", 1.0, {"image_fidelity": 0.06, "tumor_roi_realism": 0.0, "classification_utility": 0.0, "segmentation_utility": 0.0})
            ],
            validation_feedback=[],
        )


def test_final_selection_requires_tie_break_decision() -> None:
    with pytest.raises(ValueError, match="tie"):
        select_final_candidate(candidates=[_candidate("a", 1.0), _candidate("b", 1.0)], validation_feedback=[])
