"""Phase 1B isolated ablation group helpers."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from phase1a.losses import residual_l1, tumor_roi_weighted_residual_l1

SUPPORTED_COMPUTABLE_LOSSES = ("residual_l1", "tumor_roi_weighted_residual_l1")


def validate_isolated_ablation_plan(raw_plan: Mapping[str, object]) -> dict[str, object]:
    """Validate that a Phase 1B ablation changes one primary factor at a time."""
    if raw_plan.get("uses_predicted_mask_conditioning") is True:
        raise ValueError("Predicted-mask conditioning remains outside Phase 1B")
    changed_factors = raw_plan.get("changed_factors")
    if not isinstance(changed_factors, list) or not changed_factors:
        raise ValueError("ablation plan requires changed_factors")
    single_factor_evidence = raw_plan.get("single_factor_evidence")
    combined = len(changed_factors) > 1
    if combined and not single_factor_evidence:
        raise ValueError("combined Phase 1B experiments require prior single-factor evidence")
    loss_terms = raw_plan.get("loss_terms")
    if not isinstance(loss_terms, list):
        raise ValueError("ablation plan requires loss_terms")
    return {
        "name": raw_plan.get("name"),
        "changed_factors": list(changed_factors),
        "combined_experiment": combined,
        "loss_terms": list(loss_terms),
        "model_family": raw_plan.get("model_family"),
    }


def compute_configured_loss_terms(
    loss_terms: Sequence[str],
    *,
    predicted_residual: np.ndarray,
    target_residual: np.ndarray,
    tumor_mask: np.ndarray,
    tumor_weight: float,
) -> dict[str, float]:
    """Compute configured Phase 1B loss terms on deterministic arrays."""
    losses: dict[str, float] = {}
    for term in loss_terms:
        if term == "residual_l1":
            losses[term] = residual_l1(predicted_residual, target_residual)
        elif term == "tumor_roi_weighted_residual_l1":
            losses[term] = tumor_roi_weighted_residual_l1(
                predicted_residual,
                target_residual,
                tumor_mask=tumor_mask,
                tumor_weight=tumor_weight,
            )
        else:
            raise ValueError(f"loss term is not computable in this contract test: {term}")
    return losses
