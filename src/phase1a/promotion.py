"""Phase 1A submission candidate promotion gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

REQUIRED_PROMOTION_METRIC_GROUPS = (
    "image_fidelity",
    "tumor_roi_realism",
    "classification_utility",
    "segmentation_utility",
)


@dataclass(frozen=True)
class PromotionDecision:
    accepted: bool
    reasons: tuple[str, ...]
    audit_bundle: dict[str, object]


def evaluate_promotion_candidate(summary: Mapping[str, object]) -> PromotionDecision:
    """Accept or reject a Phase 1A candidate from metric summary evidence."""
    reasons: list[str] = []
    metric_groups = summary.get("metric_groups")
    if not isinstance(metric_groups, dict):
        reasons.append("metric_groups are required")
    else:
        for required_group in REQUIRED_PROMOTION_METRIC_GROUPS:
            if required_group not in metric_groups:
                reasons.append(f"{required_group} metric group is required for promotion")
        non_inferior_count = 0
        for group_name, raw_group in metric_groups.items():
            if not isinstance(raw_group, dict):
                reasons.append(f"{group_name} metric group is invalid")
                continue
            worsening = _relative_worsening(raw_group)
            if worsening > 0.05:
                reasons.append(f"{group_name} worsened by more than 5%")
            else:
                non_inferior_count += 1
        if non_inferior_count < 2:
            reasons.append("at least two metric groups must improve or remain within 5%")

    rank_mean = summary.get("local_proxy_rank_mean")
    if not isinstance(rank_mean, dict) or float(rank_mean["candidate"]) >= float(rank_mean["baseline"]):
        reasons.append("local proxy rank mean must improve")

    config = summary.get("config")
    inference_settings = summary.get("inference_settings")
    model_hash = summary.get("model_hash")
    if not isinstance(config, dict) or not config:
        reasons.append("config is required for audit bundle")
    if not isinstance(inference_settings, dict) or not inference_settings:
        reasons.append("inference_settings are required for audit bundle")
    if not isinstance(model_hash, str) or not model_hash:
        reasons.append("model_hash is required for audit bundle")

    audit_bundle = {
        "metrics": summary.get("metric_groups"),
        "config": config,
        "inference_settings": inference_settings,
        "model_hash": model_hash,
    }
    return PromotionDecision(
        accepted=not reasons,
        reasons=tuple(reasons),
        audit_bundle=audit_bundle,
    )


def _relative_worsening(group: Mapping[str, object]) -> float:
    candidate = float(group["candidate"])
    baseline = float(group["baseline"])
    higher_is_better = bool(group["higher_is_better"])
    if higher_is_better:
        return (baseline - candidate) / abs(baseline)
    return (candidate - baseline) / abs(baseline)
