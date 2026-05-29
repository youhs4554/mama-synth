from __future__ import annotations

import inspect

import numpy as np

from phase1a.inference import synthesize_post_from_pre_contrast
from phase1a.losses import residual_l1, tumor_roi_weighted_residual_l1


def test_residual_l1_returns_expected_value_on_toy_arrays() -> None:
    predicted_residual = np.array([[1.0, 3.0], [5.0, 7.0]], dtype=np.float32)
    target_residual = np.array([[0.0, 1.0], [3.0, 10.0]], dtype=np.float32)

    loss = residual_l1(predicted_residual, target_residual)

    assert loss == 2.0


def test_tumor_roi_weighted_residual_l1_returns_expected_value_on_toy_mask() -> None:
    predicted_residual = np.array([[1.0, 5.0], [5.0, 7.0]], dtype=np.float32)
    target_residual = np.array([[0.0, 1.0], [3.0, 10.0]], dtype=np.float32)
    tumor_mask = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)

    loss = tumor_roi_weighted_residual_l1(
        predicted_residual,
        target_residual,
        tumor_mask=tumor_mask,
        tumor_weight=3.0,
    )

    assert loss == 2.75


def test_tumor_masks_are_used_by_training_loss_not_inference_api() -> None:
    loss_signature = inspect.signature(tumor_roi_weighted_residual_l1)
    inference_signature = inspect.signature(synthesize_post_from_pre_contrast)

    assert "tumor_mask" in loss_signature.parameters
    assert "tumor_mask" not in inference_signature.parameters


def test_empty_tumor_mask_falls_back_to_residual_l1_without_inference_conditioning() -> None:
    predicted_residual = np.array([[1.0, 5.0], [5.0, 7.0]], dtype=np.float32)
    target_residual = np.array([[0.0, 1.0], [3.0, 10.0]], dtype=np.float32)
    empty_tumor_mask = np.zeros((2, 2), dtype=np.float32)

    weighted_loss = tumor_roi_weighted_residual_l1(
        predicted_residual,
        target_residual,
        tumor_mask=empty_tumor_mask,
        tumor_weight=3.0,
    )

    assert weighted_loss == residual_l1(predicted_residual, target_residual)
    assert "tumor_mask" not in inspect.signature(synthesize_post_from_pre_contrast).parameters
