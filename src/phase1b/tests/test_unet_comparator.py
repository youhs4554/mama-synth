from __future__ import annotations

import inspect

import numpy as np

from phase1a.inference import synthesize_post_from_pre_contrast
from phase1b.models import UNetResidualRegressor, train_unet_residual_regressor


def test_unet_residual_regressor_has_convolutional_encoder_decoder_architecture() -> None:
    model = UNetResidualRegressor(in_channels=1, base_channels=4)

    assert model.architecture_summary() == {
        "conv2d_layers": 6,
        "downsampling": "max_pool_2x2",
        "upsampling": "nearest_2x",
        "skip_connections": ["encoder_to_decoder_concat"],
        "trainable_head": "1x1_residual_head",
    }
    assert model.encoder_conv1.weight.shape == (4, 1, 3, 3)
    assert model.bottleneck_conv1.weight.shape == (8, 4, 3, 3)
    assert model.decoder_conv1.weight.shape == (4, 12, 3, 3)


def test_unet_residual_regressor_returns_native_size_residual_batch() -> None:
    model = UNetResidualRegressor(in_channels=1, base_channels=4)
    pre_contrast = np.ones((2, 1, 5, 7), dtype=np.float32)

    residual = model.forward(pre_contrast)

    assert residual.shape == pre_contrast.shape
    assert residual.dtype == np.float32


def test_unet_predict_public_interface_accepts_pre_contrast_only() -> None:
    model = UNetResidualRegressor(in_channels=1, base_channels=4)

    assert list(inspect.signature(model.predict).parameters) == ["pre_contrast"]

    residual = model.predict(np.ones((5, 7), dtype=np.float32))

    assert residual.shape == (5, 7)
    assert residual.dtype == np.float32


def test_unet_comparator_outputs_synthetic_post_without_mask() -> None:
    model = UNetResidualRegressor(in_channels=1, base_channels=4)
    pre_contrast = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)

    synthetic_post = synthesize_post_from_pre_contrast(pre_contrast, predictor=model)

    assert synthetic_post.shape == pre_contrast.shape
    np.testing.assert_allclose(synthetic_post, pre_contrast, atol=1e-6)


def test_train_unet_residual_regressor_learns_input_dependent_residuals() -> None:
    pre_cases = [
        np.zeros((8, 8), dtype=np.float32),
        np.ones((8, 8), dtype=np.float32),
    ]
    post_cases = [pre_cases[0] + 0.25, pre_cases[1] + 1.25]

    model = train_unet_residual_regressor(
        pre_cases,
        post_cases,
        in_channels=1,
        base_channels=4,
        seed=7,
    )

    dark_residual = model.predict(np.zeros((8, 8), dtype=np.float32))
    bright_residual = model.predict(np.ones((8, 8), dtype=np.float32))

    assert float(bright_residual.mean()) > float(dark_residual.mean()) + 0.5
    np.testing.assert_allclose(dark_residual.mean(), 0.25, atol=0.05)
    np.testing.assert_allclose(bright_residual.mean(), 1.25, atol=0.05)


def test_train_unet_residual_regressor_supports_variable_native_shapes() -> None:
    # Full-dataset training mixes cases with different native slice shapes.
    pre_cases = [
        np.zeros((8, 8), dtype=np.float32),
        np.ones((6, 10), dtype=np.float32),
        np.full((12, 5), 0.5, dtype=np.float32),
    ]
    post_cases = [pre_cases[0] + 0.25, pre_cases[1] + 1.25, pre_cases[2] + 0.75]

    model = train_unet_residual_regressor(
        pre_cases,
        post_cases,
        in_channels=1,
        base_channels=4,
        seed=7,
    )

    dark_residual = model.predict(np.zeros((8, 8), dtype=np.float32))
    bright_residual = model.predict(np.ones((8, 8), dtype=np.float32))

    assert float(bright_residual.mean()) > float(dark_residual.mean()) + 0.5
    np.testing.assert_allclose(dark_residual.mean(), 0.25, atol=0.1)
    np.testing.assert_allclose(bright_residual.mean(), 1.25, atol=0.1)


def test_trained_unet_regressor_predicts_native_size_after_training() -> None:
    model = train_unet_residual_regressor(
        [np.zeros((8, 8), dtype=np.float32), np.ones((8, 8), dtype=np.float32)],
        [np.ones((8, 8), dtype=np.float32), np.full((8, 8), 3.0, dtype=np.float32)],
        in_channels=1,
        base_channels=4,
        seed=11,
    )

    residual = model.predict(np.ones((9, 11), dtype=np.float32))

    assert residual.shape == (9, 11)
    assert np.isfinite(residual).all()
