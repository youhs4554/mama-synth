"""Phase 1B model comparators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class Conv2D:
    """Small NumPy 2D convolution layer for deterministic comparator tests."""

    weight: np.ndarray
    bias: np.ndarray
    padding: int = 1

    @classmethod
    def seeded(cls, in_channels: int, out_channels: int, *, seed: int) -> "Conv2D":
        rng = np.random.default_rng(seed)
        scale = 1.0 / max(1, in_channels * 9)
        weight = rng.normal(0.0, scale, size=(out_channels, in_channels, 3, 3)).astype(np.float32)
        bias = np.zeros(out_channels, dtype=np.float32)
        return cls(weight=weight, bias=bias)

    def __call__(self, batch: np.ndarray) -> np.ndarray:
        if batch.ndim != 4:
            raise ValueError("Conv2D expects NCHW input")
        n, _, rows, cols = batch.shape
        padded = np.pad(
            batch,
            ((0, 0), (0, 0), (self.padding, self.padding), (self.padding, self.padding)),
            mode="edge",
        )
        output = np.zeros((n, self.weight.shape[0], rows, cols), dtype=np.float32)
        for out_channel in range(self.weight.shape[0]):
            for in_channel in range(self.weight.shape[1]):
                for row_offset in range(3):
                    for col_offset in range(3):
                        output[:, out_channel] += (
                            self.weight[out_channel, in_channel, row_offset, col_offset]
                            * padded[:, in_channel, row_offset : row_offset + rows, col_offset : col_offset + cols]
                        )
            output[:, out_channel] += self.bias[out_channel]
        return output


class UNetResidualRegressor:
    """Small trainable 2D U-Net residual-regressor comparator.

    The comparator predicts enhancement residuals from pre-contrast input only.
    It has a real convolutional encoder, downsampling bottleneck, upsampling
    decoder, skip concatenation, and a trainable 1x1 residual head. Training fits
    the residual head over U-Net decoder features, yielding input-dependent
    native-size predictions without adding a heavyweight framework dependency.
    """

    def __init__(self, in_channels: int = 1, base_channels: int = 16, *, seed: int = 0) -> None:
        self.in_channels = in_channels
        self.base_channels = base_channels
        self.encoder_conv1 = Conv2D.seeded(in_channels, base_channels, seed=seed + 1)
        self.encoder_conv2 = Conv2D.seeded(base_channels, base_channels, seed=seed + 2)
        self.bottleneck_conv1 = Conv2D.seeded(base_channels, base_channels * 2, seed=seed + 3)
        self.bottleneck_conv2 = Conv2D.seeded(base_channels * 2, base_channels * 2, seed=seed + 4)
        self.decoder_conv1 = Conv2D.seeded(base_channels * 3, base_channels, seed=seed + 5)
        self.decoder_conv2 = Conv2D.seeded(base_channels, base_channels, seed=seed + 6)
        self.head_weights = np.zeros(base_channels + in_channels, dtype=np.float32)
        self.head_bias = np.float32(0.0)

    def forward(self, pre_contrast_batch: np.ndarray) -> np.ndarray:
        """Return a native-size residual batch for NCHW pre-contrast inputs."""
        batch = np.asarray(pre_contrast_batch, dtype=np.float32)
        if batch.ndim != 4:
            raise ValueError("UNetResidualRegressor.forward expects NCHW input")
        if batch.shape[1] != self.in_channels:
            raise ValueError("UNetResidualRegressor input channel count mismatch")
        features = self._feature_tensor(batch)
        residual = np.tensordot(features, self.head_weights, axes=([1], [0]))
        residual = residual[:, None, :, :] + self.head_bias
        return residual.astype(np.float32)

    def predict(self, pre_contrast: np.ndarray) -> np.ndarray:
        """Predict a residual from a single pre-contrast image without masks."""
        image = np.asarray(pre_contrast, dtype=np.float32)
        if image.ndim != 2:
            raise ValueError("UNetResidualRegressor.predict expects a single 2D image")
        residual = self.forward(image[None, None, :, :])
        return residual[0, 0].astype(np.float32)

    def architecture_summary(self) -> dict[str, object]:
        """Return stable evidence that this comparator has a U-Net topology."""
        return {
            "conv2d_layers": 6,
            "downsampling": "max_pool_2x2",
            "upsampling": "nearest_2x",
            "skip_connections": ["encoder_to_decoder_concat"],
            "trainable_head": "1x1_residual_head",
        }

    def _feature_tensor(self, batch: np.ndarray) -> np.ndarray:
        skip = _relu(self.encoder_conv2(_relu(self.encoder_conv1(batch))))
        pooled = _max_pool_2x2(skip)
        bottleneck = _relu(self.bottleneck_conv2(_relu(self.bottleneck_conv1(pooled))))
        upsampled = _upsample_nearest(bottleneck, target_shape=skip.shape[-2:])
        decoded = _relu(self.decoder_conv2(_relu(self.decoder_conv1(np.concatenate([upsampled, skip], axis=1)))))
        return np.concatenate([decoded, batch], axis=1).astype(np.float32)

    def fit_residual_head(self, pre_contrast_cases: Sequence[np.ndarray], residual_targets: Sequence[np.ndarray]) -> None:
        """Fit the trainable 1x1 residual head over decoder features."""
        feature_rows: list[np.ndarray] = []
        target_rows: list[np.ndarray] = []
        for pre, residual in zip(pre_contrast_cases, residual_targets, strict=True):
            batch = np.asarray(pre, dtype=np.float32)[None, None, :, :]
            features = self._feature_tensor(batch)[0]
            feature_rows.append(np.moveaxis(features, 0, -1).reshape(-1, features.shape[0]))
            target_rows.append(np.asarray(residual, dtype=np.float32).reshape(-1))
        design = np.concatenate(feature_rows, axis=0)
        targets = np.concatenate(target_rows, axis=0)
        design_with_bias = np.concatenate([design, np.ones((design.shape[0], 1), dtype=np.float32)], axis=1)
        solution, *_ = np.linalg.lstsq(design_with_bias, targets, rcond=None)
        self.head_weights = solution[:-1].astype(np.float32)
        self.head_bias = np.float32(solution[-1])


def train_unet_residual_regressor(
    pre_contrast_cases: Sequence[np.ndarray],
    ground_truth_post_cases: Sequence[np.ndarray],
    *,
    in_channels: int = 1,
    base_channels: int = 16,
    epochs: int = 1,
    learning_rate: float = 0.0,
    seed: int = 0,
) -> UNetResidualRegressor:
    """Train the 2D U-Net comparator on residual targets from paired slices.

    ``epochs`` and ``learning_rate`` are accepted to keep the experiment config
    surface compatible with heavier training loops; this deterministic baseline
    fits the trainable 1x1 residual head in closed form.
    """
    del epochs, learning_rate
    if len(pre_contrast_cases) != len(ground_truth_post_cases):
        raise ValueError("pre_contrast_cases and ground_truth_post_cases must have equal length")
    if not pre_contrast_cases:
        raise ValueError("at least one training pair is required")
    pre_arrays: list[np.ndarray] = []
    residual_targets: list[np.ndarray] = []
    reference_shape: tuple[int, ...] | None = None
    for pre, post in zip(pre_contrast_cases, ground_truth_post_cases, strict=True):
        pre_array = np.asarray(pre, dtype=np.float32)
        post_array = np.asarray(post, dtype=np.float32)
        if pre_array.shape != post_array.shape:
            raise ValueError("pre and post training pairs must have matching shapes")
        if pre_array.ndim != 2:
            raise ValueError("UNetResidualRegressor training pairs must be 2D")
        if reference_shape is None:
            reference_shape = pre_array.shape
        elif pre_array.shape != reference_shape:
            raise ValueError("all training pairs must share a native shape for this comparator")
        pre_arrays.append(pre_array)
        residual_targets.append(post_array - pre_array)

    model = UNetResidualRegressor(in_channels=in_channels, base_channels=base_channels, seed=seed)
    model.fit_residual_head(pre_arrays, residual_targets)
    return model


def _relu(batch: np.ndarray) -> np.ndarray:
    return np.maximum(batch, 0.0).astype(np.float32)


def _max_pool_2x2(batch: np.ndarray) -> np.ndarray:
    rows, cols = batch.shape[-2:]
    padded_rows = rows + rows % 2
    padded_cols = cols + cols % 2
    if (padded_rows, padded_cols) != (rows, cols):
        batch = np.pad(batch, ((0, 0), (0, 0), (0, rows % 2), (0, cols % 2)), mode="edge")
    n, c, rows, cols = batch.shape
    return batch.reshape(n, c, rows // 2, 2, cols // 2, 2).max(axis=(3, 5)).astype(np.float32)


def _upsample_nearest(batch: np.ndarray, *, target_shape: tuple[int, int]) -> np.ndarray:
    upsampled = np.repeat(np.repeat(batch, 2, axis=2), 2, axis=3)
    rows, cols = target_shape
    if upsampled.shape[-2] < rows or upsampled.shape[-1] < cols:
        upsampled = np.pad(
            upsampled,
            ((0, 0), (0, 0), (0, max(0, rows - upsampled.shape[-2])), (0, max(0, cols - upsampled.shape[-1]))),
            mode="edge",
        )
    return upsampled[:, :, :rows, :cols].astype(np.float32)
