from __future__ import annotations

import inspect

import numpy as np
import pytest

from phase1a.inference import synthesize_post_from_pre_contrast


class OnesResidualPredictor:
    def predict(self, pre_contrast: np.ndarray) -> np.ndarray:
        return np.ones_like(pre_contrast, dtype=np.float32)


class RecordingResidualPredictor:
    def __init__(self) -> None:
        self.input_shape: tuple[int, int] | None = None

    def predict(self, pre_contrast: np.ndarray) -> np.ndarray:
        self.input_shape = pre_contrast.shape
        return np.ones_like(pre_contrast, dtype=np.float32)


def test_mask_free_residual_inference_accepts_pre_contrast_only() -> None:
    pre_contrast = np.array([[1, 2], [3, 4]], dtype=np.float32)

    synthetic_post = synthesize_post_from_pre_contrast(
        pre_contrast,
        predictor=OnesResidualPredictor(),
    )

    np.testing.assert_array_equal(
        synthetic_post,
        np.array([[2, 3], [4, 5]], dtype=np.float32),
    )


def test_inference_public_api_has_no_tumor_mask_parameter() -> None:
    signature = inspect.signature(synthesize_post_from_pre_contrast)

    assert "tumor_mask" not in signature.parameters


def test_residual_inference_pads_internally_and_crops_back_to_native_size() -> None:
    pre_contrast = np.ones((5, 7), dtype=np.float32)
    predictor = RecordingResidualPredictor()

    synthetic_post = synthesize_post_from_pre_contrast(
        pre_contrast,
        predictor=predictor,
        pad_to_multiple=4,
    )

    assert predictor.input_shape == (8, 8)
    assert synthetic_post.shape == (5, 7)


def test_residual_inference_output_shape_matches_input_and_evaluation_mask() -> None:
    pre_contrast = np.ones((5, 7), dtype=np.float32)
    evaluation_mask = np.ones((5, 7), dtype=np.float32)

    synthetic_post = synthesize_post_from_pre_contrast(
        pre_contrast,
        predictor=OnesResidualPredictor(),
        evaluation_mask=evaluation_mask,
    )

    assert synthetic_post.shape == pre_contrast.shape == evaluation_mask.shape


def test_residual_inference_rejects_evaluation_mask_shape_mismatch() -> None:
    pre_contrast = np.ones((5, 7), dtype=np.float32)
    evaluation_mask = np.ones((5, 6), dtype=np.float32)

    with pytest.raises(ValueError, match="evaluation mask"):
        synthesize_post_from_pre_contrast(
            pre_contrast,
            predictor=OnesResidualPredictor(),
            evaluation_mask=evaluation_mask,
        )
