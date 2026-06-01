"""Fine-tune the pretrained medigan 00023 pix2pixHD generator on our local full dataset.

Warm-starts netG from the public 00023 `30_net_G.pth` (the only downloadable breast
pre->post checkpoint; see docs/research/pretrained_synthesis_models_deep_research.md,
strategy #1) and trains on our preprocessed pre->post pairs to close the Duke->multi-source
domain gap that broke zero-shot 00023. Reuses the 00023 pix2pixHD networks
(define_G / define_D / GANLoss). Objective = LSGAN + feature-matching + L1 (VGG skipped to
avoid a runtime download). Direct post synthesis in the model's native [-1,1] 3ch 512x512
space (mirrors submission-gan/inference.py bridging) so the warm start stays valid and the
existing inference/packaging path is reused unchanged.

Output stays GC-contract-compatible at inference: the saved generator is the same
GlobalGenerator state as `30_net_G.pth`, so submission-gan/inference.py loads it and emits
native-size float32 z-score synthetic-post .mha with metadata preserved (pre-contrast-only).

Run (example):
    CUDA_VISIBLE_DEVICES=0 CUDA_DEVICE_ORDER=PCI_BUS_ID PYTHONPATH=src \
      uv run python -m phase1b.finetune_pix2pixhd \
        --manifest splits/phase1b_full_dataset_v1.json \
        --warm_start src/submission/submission-gan/models/00023/30_net_G.pth \
        --out experiments/phase1b/finetune_pix2pixhd_v1 --epochs 40 --batch 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import SimpleITK as sitk
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

# Reuse the 00023 pix2pixHD network definitions (GlobalGenerator / MultiscaleDiscriminator / GANLoss).
_GAN_SRC = Path("src/submission/submission-gan/models/00023/src").resolve()
for _p in (_GAN_SRC, _GAN_SRC / "prepost_model"):
    if str(_p) not in sys.path:
        sys.path.append(str(_p))
from prepost_model import networks  # noqa: E402

MODEL_SIZE = 512


# --------------------------------------------------------------------------- data

def _zscore_to_unit(arr: np.ndarray, mean: float, std: float) -> np.ndarray:
    """z-score 2D -> [-1,1] via inverse-zscore + per-image min-max (mirrors inference)."""
    raw = arr.astype(np.float64) * std + mean
    lo, hi = float(raw.min()), float(raw.max())
    if hi - lo < 1e-6:
        unit = np.zeros_like(raw, dtype=np.float32)
    else:
        unit = ((raw - lo) / (hi - lo)).astype(np.float32)  # [0,1]
    return unit * 2.0 - 1.0  # [-1,1]


def _to_model_tensor(arr2d: np.ndarray) -> torch.Tensor:
    """[-1,1] HxW -> 3xMODEL_SIZE x MODEL_SIZE float32 (bilinear resize, channel-replicated)."""
    t = torch.from_numpy(arr2d)[None, None]
    t = F.interpolate(t, size=(MODEL_SIZE, MODEL_SIZE), mode="bilinear", align_corners=False)
    return t[0].repeat(3, 1, 1)


class PrePostPairs(Dataset):
    def __init__(self, manifest_path: str, mean: float, std: float, membership: str = "train") -> None:
        raw = json.loads(Path(manifest_path).read_text())
        base = Path(manifest_path).parent
        self.cases = []
        for c in raw["cases"]:
            if c["membership"] != membership:
                continue
            pre = (base / c["paths"]["pre_contrast"]).resolve()
            post = (base / c["paths"]["ground_truth_post"]).resolve()
            self.cases.append((c["case_id"], pre, post))
        self.mean, self.std = mean, std

    def __len__(self) -> int:
        return len(self.cases)

    def __getitem__(self, i: int):
        _, pre_p, post_p = self.cases[i]
        pre = sitk.GetArrayFromImage(sitk.ReadImage(str(pre_p))).astype(np.float32)
        post = sitk.GetArrayFromImage(sitk.ReadImage(str(post_p))).astype(np.float32)
        if pre.ndim == 3:
            pre = pre[0]
        if post.ndim == 3:
            post = post[0]
        pre_u = _zscore_to_unit(pre, self.mean, self.std)
        post_u = _zscore_to_unit(post, self.mean, self.std)
        return _to_model_tensor(pre_u), _to_model_tensor(post_u)


# --------------------------------------------------------------------------- model

def build_generator(warm_start: str | None, device: torch.device) -> torch.nn.Module:
    netG = networks.define_G(3, 3, 64, "global", n_downsample_global=4, n_blocks_global=9, norm="instance", gpu_ids=[])
    if warm_start:
        sd = torch.load(warm_start, map_location="cpu", weights_only=True)
        missing, unexpected = netG.load_state_dict(sd, strict=False)
        print(f"[warm-start] loaded {warm_start}: missing={len(missing)} unexpected={len(unexpected)}")
    return netG.to(device)


def build_discriminator(device: torch.device) -> torch.nn.Module:
    netD = networks.define_D(6, 64, 3, norm="instance", use_sigmoid=False, num_D=2, getIntermFeat=True, gpu_ids=[])
    return netD.to(device)


def feature_matching_loss(pred_fake, pred_real, num_D: int = 2, n_layers_D: int = 3, lambda_feat: float = 10.0):
    crit = torch.nn.L1Loss()
    fw = 4.0 / (n_layers_D + 1)
    dw = 1.0 / num_D
    loss = 0.0
    for i in range(num_D):
        for j in range(len(pred_fake[i]) - 1):
            loss = loss + dw * fw * crit(pred_fake[i][j], pred_real[i][j].detach()) * lambda_feat
    return loss


# --------------------------------------------------------------------------- train

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--warm_start", default="src/submission/submission-gan/models/00023/30_net_G.pth")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stats", default="src/preprocessing/training_pre_stats.json")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lambda_l1", type=float, default=10.0)
    ap.add_argument("--lambda_feat", type=float, default=10.0)
    ap.add_argument("--val_frac", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--ckpt_every", type=int, default=5, help="snapshot 30_net_G_e{epoch}.pth every N epochs for metric-based selection (val_l1 is a poor proxy)")
    args = ap.parse_args(argv)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(args.out)
    (out / "checkpoints").mkdir(parents=True, exist_ok=True)
    stats = json.loads(Path(args.stats).read_text())
    mean, std = float(stats["mean"]), float(stats["std"])

    full = PrePostPairs(args.manifest, mean, std, membership="train")
    n_val = max(1, int(len(full) * args.val_frac))
    perm = np.random.default_rng(args.seed).permutation(len(full))
    val_idx = set(perm[:n_val].tolist())
    train_ds = torch.utils.data.Subset(full, [i for i in range(len(full)) if i not in val_idx])
    val_ds = torch.utils.data.Subset(full, sorted(val_idx))
    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=4, drop_last=True, pin_memory=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=2)
    print(f"[data] train={len(train_ds)} val={len(val_ds)} device={device}")

    netG = build_generator(args.warm_start, device)
    netD = build_discriminator(device)
    criterionGAN = networks.GANLoss(use_lsgan=True, tensor=torch.cuda.FloatTensor if device.type == "cuda" else torch.FloatTensor)
    optG = torch.optim.Adam(netG.parameters(), lr=args.lr, betas=(0.5, 0.999))
    optD = torch.optim.Adam(netD.parameters(), lr=args.lr, betas=(0.5, 0.999))
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    def D_pred(inp, img):
        return netD(torch.cat([inp, img], dim=1))

    history = []
    best_val = float("inf")
    t0 = time.time()
    for epoch in range(args.epochs):
        netG.train(); netD.train()
        agg = {"G_GAN": 0.0, "G_feat": 0.0, "G_L1": 0.0, "D": 0.0}
        nb = 0
        for pre, post in train_dl:
            pre, post = pre.to(device), post.to(device)
            with torch.autocast("cuda", enabled=use_amp):
                fake = netG(pre)
                # D
                pred_fake_d = D_pred(pre, fake.detach())
                pred_real_d = D_pred(pre, post)
                loss_D = 0.5 * (criterionGAN(pred_fake_d, False) + criterionGAN(pred_real_d, True))
            optD.zero_grad(set_to_none=True)
            scaler.scale(loss_D).backward(); scaler.step(optD)
            with torch.autocast("cuda", enabled=use_amp):
                pred_fake = D_pred(pre, fake)
                pred_real = D_pred(pre, post)
                loss_G_GAN = criterionGAN(pred_fake, True)
                loss_G_feat = feature_matching_loss(pred_fake, pred_real, lambda_feat=args.lambda_feat)
                loss_G_L1 = F.l1_loss(fake, post) * args.lambda_l1
                loss_G = loss_G_GAN + loss_G_feat + loss_G_L1
            optG.zero_grad(set_to_none=True)
            scaler.scale(loss_G).backward(); scaler.step(optG); scaler.update()
            agg["G_GAN"] += float(loss_G_GAN.detach()); agg["G_feat"] += float(loss_G_feat.detach())
            agg["G_L1"] += float(loss_G_L1.detach()); agg["D"] += float(loss_D.detach()); nb += 1

        # validation L1 in [-1,1] space (cheap, no nnU-Net)
        netG.eval()
        with torch.no_grad():
            vl, vn = 0.0, 0
            for pre, post in val_dl:
                pre, post = pre.to(device), post.to(device)
                vl += float(F.l1_loss(netG(pre), post)); vn += 1
        val_l1 = vl / max(1, vn)
        rec = {"epoch": epoch, "val_l1": val_l1, **{k: agg[k] / max(1, nb) for k in agg}, "sec": round(time.time() - t0, 1)}
        history.append(rec)
        print(f"[epoch {epoch}] val_l1={val_l1:.4f} G_GAN={rec['G_GAN']:.3f} G_feat={rec['G_feat']:.3f} G_L1={rec['G_L1']:.3f} D={rec['D']:.3f} t={rec['sec']}s", flush=True)
        torch.save(netG.state_dict(), out / "checkpoints" / "30_net_G_last.pth")
        if args.ckpt_every and (epoch % args.ckpt_every == 0 or epoch == args.epochs - 1):
            torch.save(netG.state_dict(), out / "checkpoints" / f"30_net_G_e{epoch}.pth")
        if val_l1 < best_val:
            best_val = val_l1
            torch.save(netG.state_dict(), out / "checkpoints" / "30_net_G.pth")
            rec["is_best"] = True
        (out / "history.json").write_text(json.dumps({"args": vars(args), "best_val_l1": best_val, "history": history}, indent=2))

    print(f"[done] best_val_l1={best_val:.4f} best ckpt: {out/'checkpoints'/'30_net_G.pth'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
