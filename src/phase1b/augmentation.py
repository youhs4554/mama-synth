"""Phase 1B domain robustness augmentation contracts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DomainAugmentationConfig:
    """Seeded scanner/protocol-inspired intensity augmentation config."""

    enabled: bool
    seed: int
    intensity_scale_range: tuple[float, float] = (0.9, 1.1)
    intensity_shift_range: tuple[float, float] = (-0.1, 0.1)


@dataclass(frozen=True)
class AugmentedTriplet:
    """Paired pre/post/mask augmentation output."""

    pre_contrast: np.ndarray
    ground_truth_post: np.ndarray
    tumor_mask: np.ndarray
    parameters: dict[str, object]


def apply_domain_robustness_augmentation(
    pre_contrast: np.ndarray,
    ground_truth_post: np.ndarray,
    tumor_mask: np.ndarray,
    config: DomainAugmentationConfig,
) -> AugmentedTriplet:
    """Apply a seeded paired intensity transform while preserving mask alignment."""
    pre = np.asarray(pre_contrast, dtype=np.float32)
    post = np.asarray(ground_truth_post, dtype=np.float32)
    mask = np.asarray(tumor_mask).copy()
    if pre.shape != post.shape or pre.shape != mask.shape:
        raise ValueError("pre, post, and mask must have matching shapes for paired augmentation")
    if not config.enabled:
        return AugmentedTriplet(
            pre_contrast=pre.copy(),
            ground_truth_post=post.copy(),
            tumor_mask=mask,
            parameters={"enabled": False},
        )

    rng = np.random.default_rng(config.seed)
    scale = float(rng.uniform(*config.intensity_scale_range))
    shift = float(rng.uniform(*config.intensity_shift_range))
    return AugmentedTriplet(
        pre_contrast=(pre * scale + shift).astype(np.float32),
        ground_truth_post=(post * scale + shift).astype(np.float32),
        tumor_mask=mask,
        parameters={"enabled": True, "seed": config.seed, "scale": scale, "shift": shift},
    )
