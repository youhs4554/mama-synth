"""Phase 1A residual synthesis losses."""

from __future__ import annotations

import numpy as np


def residual_l1(predicted_residual: np.ndarray, target_residual: np.ndarray) -> float:
    """Mean absolute residual error."""
    return float(np.mean(np.abs(predicted_residual - target_residual)))


def tumor_roi_weighted_residual_l1(
    predicted_residual: np.ndarray,
    target_residual: np.ndarray,
    *,
    tumor_mask: np.ndarray,
    tumor_weight: float,
) -> float:
    """Mean residual L1 with tumor-mask voxels upweighted for training."""
    absolute_error = np.abs(predicted_residual - target_residual)
    weights = np.ones_like(absolute_error, dtype=np.float32)
    weights = weights + (tumor_mask.astype(bool) * (tumor_weight - 1.0))
    return float(np.sum(absolute_error * weights) / np.sum(weights))
