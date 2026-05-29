from __future__ import annotations

import numpy as np
import pytest

from phase3.ensemble import build_optional_blend_candidate


def test_optional_blend_rejected_without_explicit_approval() -> None:
    with pytest.raises(ValueError, match="explicit approval"):
        build_optional_blend_candidate(
            predictions=[np.ones((2, 2), dtype=np.float32), np.zeros((2, 2), dtype=np.float32)],
            weights=[0.5, 0.5],
            approved=False,
        )


def test_optional_blend_is_deterministic_native_size_synthetic_post_when_approved() -> None:
    first = np.ones((2, 3), dtype=np.float32)
    second = np.full((2, 3), 3.0, dtype=np.float32)

    candidate = build_optional_blend_candidate(
        predictions=[first, second],
        weights=[0.25, 0.75],
        approved=True,
    )

    np.testing.assert_allclose(candidate.synthetic_post, np.full((2, 3), 2.5, dtype=np.float32))
    assert candidate.synthetic_post.dtype == np.float32
    assert candidate.inference_settings == {"inputs": ["pre_contrast"], "output": "synthetic_post"}


def test_optional_blend_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same native shape"):
        build_optional_blend_candidate(
            predictions=[np.ones((2, 2), dtype=np.float32), np.ones((3, 2), dtype=np.float32)],
            weights=[0.5, 0.5],
            approved=True,
        )
