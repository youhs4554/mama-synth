"""Optional Phase 3 deterministic ensemble/blending helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BlendCandidate:
    """Approved deterministic blend output."""

    synthetic_post: np.ndarray
    inference_settings: dict[str, object]


def build_optional_blend_candidate(
    *,
    predictions: Sequence[np.ndarray],
    weights: Sequence[float],
    approved: bool,
) -> BlendCandidate:
    """Build a deterministic synthetic-post blend only after explicit approval."""
    if not approved:
        raise ValueError("optional ensemble/blending requires explicit approval")
    if not predictions:
        raise ValueError("optional blend requires at least one prediction")
    if len(predictions) != len(weights):
        raise ValueError("optional blend requires one weight per prediction")
    arrays = [np.asarray(prediction, dtype=np.float32) for prediction in predictions]
    native_shape = arrays[0].shape
    if any(array.shape != native_shape for array in arrays):
        raise ValueError("all blended predictions must have the same native shape")
    weight_array = np.asarray(weights, dtype=np.float32)
    if float(weight_array.sum()) == 0.0:
        raise ValueError("optional blend weights must not sum to zero")
    normalized = weight_array / weight_array.sum()
    synthetic_post = np.zeros(native_shape, dtype=np.float32)
    for weight, array in zip(normalized, arrays, strict=True):
        synthetic_post = synthetic_post + float(weight) * array
    return BlendCandidate(
        synthetic_post=synthetic_post.astype(np.float32),
        inference_settings={"inputs": ["pre_contrast"], "output": "synthetic_post"},
    )
