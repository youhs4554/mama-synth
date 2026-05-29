"""Phase 3 final candidate selection."""

from __future__ import annotations

from typing import Mapping, Sequence

NON_INFERIORITY_MARGIN = 0.05
REQUIRED_METRIC_GROUPS = (
    "image_fidelity",
    "tumor_roi_realism",
    "classification_utility",
    "segmentation_utility",
)


def select_final_candidate(
    *,
    candidates: Sequence[Mapping[str, object]],
    validation_feedback: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Select a final candidate from a frozen local ranking table."""
    if not candidates:
        return {
            "schema_version": "phase3-final-selection-v1",
            "selected_candidate": None,
            "reason": "no promoted candidates available",
            "validation_feedback": list(validation_feedback),
        }
    eligible = [_validate_candidate(candidate) for candidate in candidates]
    eligible.sort(key=lambda candidate: float(candidate["local_proxy_rank_mean"]))
    if len(eligible) > 1 and float(eligible[0]["local_proxy_rank_mean"]) == float(eligible[1]["local_proxy_rank_mean"]):
        raise ValueError("final selection tie requires a human tie-break decision")
    selected = eligible[0]
    return {
        "schema_version": "phase3-final-selection-v1",
        "selected_candidate": selected["name"],
        "local_proxy_rank_mean": selected["local_proxy_rank_mean"],
        "validation_feedback": list(validation_feedback),
        "validation_feedback_role": "official-phase evidence, not a substitute for local hold-out evaluation",
    }


def _validate_candidate(candidate: Mapping[str, object]) -> Mapping[str, object]:
    if candidate.get("audit_complete") is not True:
        raise ValueError("final selection candidate requires complete audit bundle")
    metric_group_worsening = candidate.get("metric_group_worsening")
    if not isinstance(metric_group_worsening, dict):
        raise ValueError("final selection candidate requires metric_group_worsening")
    for group in REQUIRED_METRIC_GROUPS:
        if group not in metric_group_worsening:
            raise ValueError(f"final selection candidate missing {group} non-inferiority evidence")
        if float(metric_group_worsening[group]) > NON_INFERIORITY_MARGIN:
            raise ValueError(f"{group} violates 5% non-inferiority margin")
    if "local_proxy_rank_mean" not in candidate:
        raise ValueError("final selection candidate requires local_proxy_rank_mean")
    if "name" not in candidate:
        raise ValueError("final selection candidate requires name")
    return candidate
