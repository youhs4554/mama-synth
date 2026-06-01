"""Smoke tests for Phase 2 latent diffusion (CPU, tiny data).

Run with torch/diffusers in the project venv:
    PYTHONPATH=src uv run --with pytest python -m pytest src/phase2/tests/test_latent_diffusion.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("diffusers")
import SimpleITK as sitk  # noqa: E402

from phase2 import latent_diffusion as ld  # noqa: E402


def test_zscore_unit_roundtrip_exact_within_bounds():
    z = np.linspace(ld.Z_LO, ld.Z_HI, 50).astype(np.float32)
    back = ld.unit_to_zscore(ld.zscore_to_unit(z))
    assert np.allclose(z, back, atol=1e-4)


def test_zscore_unit_clips_outside_bounds():
    u = ld.zscore_to_unit(np.array([ld.Z_LO - 5, ld.Z_HI + 5], dtype=np.float32))
    assert np.allclose(u, [-1.0, 1.0], atol=1e-5)


def test_unet_concat_condition_shapes():
    unet = ld.build_unet()
    x = torch.randn(2, ld.LATENT_CH * 2, ld.LATENT_SIZE, ld.LATENT_SIZE)
    t = torch.randint(0, 1000, (2,))
    out = unet(x, t).sample
    assert out.shape == (2, ld.LATENT_CH, ld.LATENT_SIZE, ld.LATENT_SIZE)


def _write_mha(path: Path, arr: np.ndarray, spacing=(0.8, 0.8)):
    img = sitk.GetImageFromArray(arr.astype(np.float32))
    img.SetSpacing(spacing)
    img.SetOrigin((1.0, 2.0))
    sitk.WriteImage(img, str(path))


def _tiny_manifest(tmp: Path, n_train=2, n_hold=2, hw=(96, 80)):
    mha = tmp / "mha"
    (mha / "input").mkdir(parents=True)
    (mha / "gt").mkdir(parents=True)
    rng = np.random.default_rng(0)
    cases = []
    for split, count in [("train", n_train), ("holdout", n_hold)]:
        for i in range(count):
            cid = f"{split}_{i}"
            pre = (rng.random(hw) * 6 - 0.5).astype(np.float32)
            post = pre + rng.random(hw).astype(np.float32)  # post = pre + enhancement
            _write_mha(mha / "input" / f"{cid}.mha", pre)
            _write_mha(mha / "gt" / f"{cid}.mha", post)
            cases.append({"case_id": cid, "membership": split,
                          "paths": {"pre_contrast": f"mha/input/{cid}.mha",
                                    "ground_truth_post": f"mha/gt/{cid}.mha"}})
    mpath = tmp / "manifest.json"
    mpath.write_text(json.dumps({"cases": cases}))
    return mpath


def test_encode_train_eval_contract(tmp_path):
    """End-to-end on tiny data: encode -> train -> eval emits native-size float32 .mha
    with input metadata preserved and pre-contrast-only inference."""
    if not Path(ld.VAE_DIR).exists():
        pytest.skip(f"VAE not staged at {ld.VAE_DIR}")
    manifest = _tiny_manifest(tmp_path)
    out = tmp_path / "ldm"

    ld.main(["encode", "--manifest", str(manifest), "--out", str(out)])
    assert (out / "latents.pt").exists() and (out / "norm_stats.json").exists()

    ld.main(["train", "--out", str(out), "--epochs", "2", "--batch", "2",
             "--ckpt_every", "0", "--log_every", "1"])
    ckpt = out / "checkpoints" / "unet_last.pt"
    assert ckpt.exists()

    ld.main(["eval", "--out", str(out), "--manifest", str(manifest),
             "--ckpt", str(ckpt), "--tag", "smoke", "--steps", "3"])
    preds = sorted((out / "eval_smoke" / "predictions").glob("*.mha"))
    assert len(preds) == 2
    # contract: native size, float32, finite, metadata preserved from input
    ref = sitk.ReadImage(str(tmp_path / "mha" / "input" / "train_0.mha"))  # any input for spacing check
    pred = sitk.ReadImage(str(preds[0]))
    arr = sitk.GetArrayFromImage(pred)
    assert arr.dtype == np.float32 and np.isfinite(arr).all()
    in_img = sitk.ReadImage(str(tmp_path / "mha" / "input" / f"{preds[0].stem}.mha"))
    assert arr.shape == sitk.GetArrayFromImage(in_img).shape
    assert pred.GetSpacing() == in_img.GetSpacing()
    assert pred.GetOrigin() == in_img.GetOrigin()
