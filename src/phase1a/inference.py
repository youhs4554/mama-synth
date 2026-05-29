"""Mask-free residual inference helpers for Phase 1A."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class ResidualPredictor(Protocol):
    def predict(self, pre_contrast: np.ndarray) -> np.ndarray:
        """Predict an enhancement residual from a pre-contrast slice."""


def synthesize_post_from_pre_contrast(
    pre_contrast: np.ndarray,
    *,
    predictor: ResidualPredictor,
    pad_to_multiple: int | None = None,
    evaluation_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Predict residual from pre-contrast only and return synthetic post image."""
    pre = pre_contrast.astype(np.float32, copy=False)
    if evaluation_mask is not None and evaluation_mask.shape != pre.shape:
        raise ValueError("evaluation mask shape must match pre-contrast input shape")
    padded_pre, original_shape = _pad_to_multiple(pre, pad_to_multiple)
    padded_residual = predictor.predict(padded_pre)
    residual = padded_residual[: original_shape[0], : original_shape[1]]
    return (pre + residual).astype(np.float32, copy=False)


def _pad_to_multiple(
    image: np.ndarray, pad_to_multiple: int | None
) -> tuple[np.ndarray, tuple[int, int]]:
    if pad_to_multiple is None:
        return image, image.shape
    rows, cols = image.shape
    padded_rows = _round_up(rows, pad_to_multiple)
    padded_cols = _round_up(cols, pad_to_multiple)
    if (padded_rows, padded_cols) == image.shape:
        return image, image.shape
    padded = np.zeros((padded_rows, padded_cols), dtype=image.dtype)
    padded[:rows, :cols] = image
    return padded, image.shape


def _round_up(value: int, multiple: int) -> int:
    return ((value + multiple - 1) // multiple) * multiple
