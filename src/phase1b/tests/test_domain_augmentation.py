from __future__ import annotations

import numpy as np

from phase1b.augmentation import DomainAugmentationConfig, apply_domain_robustness_augmentation


def test_domain_augmentation_is_reproducible_under_seed() -> None:
    pre = np.arange(9, dtype=np.float32).reshape(3, 3)
    post = pre + 2.0
    mask = np.array([[0, 1, 0], [0, 1, 0], [0, 0, 0]], dtype=np.uint8)
    config = DomainAugmentationConfig(enabled=True, seed=11, intensity_scale_range=(0.8, 1.2), intensity_shift_range=(-0.5, 0.5))

    first = apply_domain_robustness_augmentation(pre, post, mask, config)
    second = apply_domain_robustness_augmentation(pre, post, mask, config)

    np.testing.assert_allclose(first.pre_contrast, second.pre_contrast)
    np.testing.assert_allclose(first.ground_truth_post, second.ground_truth_post)
    np.testing.assert_array_equal(first.tumor_mask, second.tumor_mask)
    assert first.parameters == second.parameters


def test_domain_augmentation_preserves_paired_alignment_and_mask() -> None:
    pre = np.ones((3, 3), dtype=np.float32)
    post = pre + 4.0
    mask = np.eye(3, dtype=np.uint8)
    config = DomainAugmentationConfig(enabled=True, seed=3, intensity_scale_range=(0.5, 0.5), intensity_shift_range=(2.0, 2.0))

    augmented = apply_domain_robustness_augmentation(pre, post, mask, config)

    np.testing.assert_allclose(augmented.ground_truth_post - augmented.pre_contrast, np.full((3, 3), 2.0, dtype=np.float32))
    np.testing.assert_array_equal(augmented.tumor_mask, mask)
    assert augmented.pre_contrast.shape == pre.shape
    assert augmented.ground_truth_post.shape == post.shape


def test_disabled_domain_augmentation_is_noop() -> None:
    pre = np.arange(4, dtype=np.float32).reshape(2, 2)
    post = pre + 1.0
    mask = np.array([[0, 1], [1, 0]], dtype=np.uint8)

    augmented = apply_domain_robustness_augmentation(
        pre,
        post,
        mask,
        DomainAugmentationConfig(enabled=False, seed=99),
    )

    np.testing.assert_array_equal(augmented.pre_contrast, pre)
    np.testing.assert_array_equal(augmented.ground_truth_post, post)
    np.testing.assert_array_equal(augmented.tumor_mask, mask)
    assert augmented.parameters == {"enabled": False}
