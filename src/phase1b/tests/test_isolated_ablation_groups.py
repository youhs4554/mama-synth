from __future__ import annotations

import numpy as np
import pytest

from phase1b.ablation_groups import (
    compute_configured_loss_terms,
    validate_isolated_ablation_plan,
)


def test_ablation_plan_allows_single_factor_changes() -> None:
    plan = validate_isolated_ablation_plan(
        {
            "name": "tumor-roi-weighted-loss",
            "changed_factors": ["loss_terms"],
            "loss_terms": ["residual_l1", "tumor_roi_weighted_residual_l1"],
            "model_family": "unet_residual_regressor",
            "uses_predicted_mask_conditioning": False,
        }
    )

    assert plan["changed_factors"] == ["loss_terms"]
    assert plan["combined_experiment"] is False


def test_ablation_plan_rejects_combined_experiment_without_single_factor_evidence() -> None:
    with pytest.raises(ValueError, match="single-factor evidence"):
        validate_isolated_ablation_plan(
            {
                "name": "unet-plus-augmentation",
                "changed_factors": ["model_family", "augmentation_policy"],
                "loss_terms": ["residual_l1"],
                "model_family": "unet_residual_regressor",
                "uses_predicted_mask_conditioning": False,
            }
        )


def test_ablation_plan_rejects_predicted_mask_conditioning() -> None:
    with pytest.raises(ValueError, match="Predicted-mask conditioning remains outside Phase 1B"):
        validate_isolated_ablation_plan(
            {
                "name": "predicted-mask",
                "changed_factors": ["model_family"],
                "loss_terms": ["residual_l1"],
                "model_family": "predicted_mask_conditioning",
                "uses_predicted_mask_conditioning": True,
            }
        )


def test_configured_loss_terms_compute_on_toy_arrays() -> None:
    predicted = np.array([[1, 3], [2, 4]], dtype=np.float32)
    target = np.array([[1, 1], [1, 1]], dtype=np.float32)
    mask = np.array([[0, 1], [0, 0]], dtype=np.uint8)

    losses = compute_configured_loss_terms(
        ["residual_l1", "tumor_roi_weighted_residual_l1"],
        predicted_residual=predicted,
        target_residual=target,
        tumor_mask=mask,
        tumor_weight=3.0,
    )

    assert losses == {
        "residual_l1": 1.5,
        "tumor_roi_weighted_residual_l1": 10.0 / 6.0,
    }
