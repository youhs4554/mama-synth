"""Phase 2: conditional latent diffusion (CC-Net style) for pre->post breast MRI synthesis.

Design (STRATEGY.md S2.1 CC-Net / S4.2 Phase 2):
- Frozen SD VAE (sd-vae-ft-mse, f8 downsample, 4-channel latent; substitutes for the
  gated SD2.1 VAE, same KL architecture, MIT-licensed, public pre-cutoff).
- Conditional UNet2DModel denoises the post-contrast latent conditioned on the
  pre-contrast latent via channel concatenation (Palette-style latent conditioning;
  a lighter stand-in for CC-Net's ControlNet that fits 20GB).
- FIXED invertible z-score<->[-1,1] normalization (Z_LO..Z_HI clip) instead of the
  per-image min-max uint8 bridge used by the pix2pixHD path -- the per-image bridge is
  not invertible and compresses tumor enhancement (cause of negative SSIM-tumor).
- Latents are per-channel standardized with stats stored at encode time.

GC contract preserved at inference: pre-contrast-only input, native-size float32
z-score synthetic-post .mha with metadata copied from the input.

Subcommands:
    encode   manifest train pre/post -> cached latents + norm stats
    train    cached latents -> conditional UNet (epsilon prediction, DDPM)
    eval     manifest holdout -> DDIM-sampled synthetic-post .mha (no evaluator call)

Run (after GPU 0 frees; CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0):
    PYTHONPATH=src uv run python -m phase2.latent_diffusion encode \
        --manifest splits/phase1b_full_dataset_v1.json --out experiments/phase2/ldm_v1
    PYTHONPATH=src uv run python -m phase2.latent_diffusion train \
        --out experiments/phase2/ldm_v1 --epochs 200 --batch 32
    PYTHONPATH=src uv run python -m phase2.latent_diffusion eval \
        --out experiments/phase2/ldm_v1 --manifest splits/phase1b_loso_nact_v1.json \
        --ckpt experiments/phase2/ldm_v1/checkpoints/unet_last.pt --steps 50
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import SimpleITK as sitk
import torch
import torch.nn.functional as F

VAE_DIR = "experiments/phase2/sd_vae_ft_mse"
MODEL_SIZE = 512
LATENT_SIZE = 64
LATENT_CH = 4
# Fixed invertible z-score clip bounds (see data percentiles: pre p99.9~9.5, post p99.9~19).
Z_LO = -0.5
Z_HI = 12.0


# --------------------------------------------------------------------------- normalization

def zscore_to_unit(arr: np.ndarray, lo: float = Z_LO, hi: float = Z_HI) -> np.ndarray:
    """Fixed, invertible z-score -> [-1,1] (clip to [lo,hi] then linear map)."""
    u = (np.clip(arr.astype(np.float32), lo, hi) - lo) / (hi - lo)
    return u * 2.0 - 1.0


def unit_to_zscore(unit: np.ndarray, lo: float = Z_LO, hi: float = Z_HI) -> np.ndarray:
    """Inverse of zscore_to_unit (exact except for values clipped at encode time)."""
    u = (unit.astype(np.float32) + 1.0) / 2.0
    return u * (hi - lo) + lo


def _load_2d(path: Path) -> np.ndarray:
    a = sitk.GetArrayFromImage(sitk.ReadImage(str(path))).astype(np.float32)
    return a[0] if a.ndim == 3 else a


def _to_model_tensor(arr2d_unit: np.ndarray) -> torch.Tensor:
    """[-1,1] HxW -> 1x3xMODEL_SIZE x MODEL_SIZE (bilinear resize, channel-replicated)."""
    t = torch.from_numpy(arr2d_unit.astype(np.float32))[None, None]
    t = F.interpolate(t, size=(MODEL_SIZE, MODEL_SIZE), mode="bilinear", align_corners=False)
    return t.repeat(1, 3, 1, 1)


# --------------------------------------------------------------------------- VAE

def load_vae(device: torch.device):
    from diffusers import AutoencoderKL

    vae = AutoencoderKL.from_pretrained(VAE_DIR).to(device).eval()
    for p in vae.parameters():
        p.requires_grad_(False)
    return vae


@torch.no_grad()
def encode_image(vae, unit_arr2d: np.ndarray, device: torch.device) -> torch.Tensor:
    x = _to_model_tensor(unit_arr2d).to(device)
    return vae.encode(x).latent_dist.mean  # (1,4,64,64), pre-scaling


@torch.no_grad()
def decode_latent(vae, latent: torch.Tensor) -> torch.Tensor:
    rec = vae.decode(latent).sample  # (1,3,512,512) in ~[-1,1]
    return rec.clamp(-1, 1).mean(dim=1, keepdim=True)  # grayscale (1,1,512,512)


# --------------------------------------------------------------------------- manifest

def _manifest_cases(manifest_path: str, membership: str):
    raw = json.loads(Path(manifest_path).read_text())
    base = Path(manifest_path).parent
    out = []
    for c in raw["cases"]:
        if c["membership"] != membership:
            continue
        out.append((
            c["case_id"],
            (base / c["paths"]["pre_contrast"]).resolve(),
            (base / c["paths"]["ground_truth_post"]).resolve(),
        ))
    return out


# --------------------------------------------------------------------------- encode

def cmd_encode(args) -> int:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vae = load_vae(device)
    cases = _manifest_cases(args.manifest, "train")
    print(f"[encode] {len(cases)} train cases on {device}")
    z_pre, z_post = [], []
    t0 = time.time()
    for i, (cid, pre_p, post_p) in enumerate(cases):
        lp = encode_image(vae, zscore_to_unit(_load_2d(pre_p)), device)
        lq = encode_image(vae, zscore_to_unit(_load_2d(post_p)), device)
        z_pre.append(lp.squeeze(0).to("cpu", torch.float16))
        z_post.append(lq.squeeze(0).to("cpu", torch.float16))
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(cases)} ({time.time() - t0:.0f}s)", flush=True)
    zp = torch.stack(z_pre)  # (N,4,64,64) fp16
    zq = torch.stack(z_post)
    # per-channel standardization stats over the JOINT pre+post latent distribution
    both = torch.cat([zp.float(), zq.float()], dim=0)
    mean = both.mean(dim=(0, 2, 3))
    std = both.std(dim=(0, 2, 3)).clamp_min(1e-6)
    torch.save({"z_pre": zp, "z_post": zq}, out / "latents.pt")
    (out / "norm_stats.json").write_text(json.dumps({
        "z_lo": Z_LO, "z_hi": Z_HI, "model_size": MODEL_SIZE,
        "latent_mean": mean.tolist(), "latent_std": std.tolist(),
        "n": len(cases), "vae_dir": VAE_DIR,
    }, indent=2))
    print(f"[encode] saved {out/'latents.pt'} shape={tuple(zp.shape)} "
          f"lat_mean={[round(v,3) for v in mean.tolist()]} lat_std={[round(v,3) for v in std.tolist()]}")
    return 0


# --------------------------------------------------------------------------- model

def build_unet():
    from diffusers import UNet2DModel

    return UNet2DModel(
        sample_size=LATENT_SIZE,
        in_channels=LATENT_CH * 2,   # noisy post latent + pre latent (concat condition)
        out_channels=LATENT_CH,      # epsilon on post latent
        layers_per_block=2,
        block_out_channels=(128, 256, 384, 512),
        down_block_types=("DownBlock2D", "AttnDownBlock2D", "AttnDownBlock2D", "AttnDownBlock2D"),
        up_block_types=("AttnUpBlock2D", "AttnUpBlock2D", "AttnUpBlock2D", "UpBlock2D"),
    )


def _load_norm(out: Path):
    s = json.loads((out / "norm_stats.json").read_text())
    mean = torch.tensor(s["latent_mean"]).view(1, -1, 1, 1)
    std = torch.tensor(s["latent_std"]).view(1, -1, 1, 1)
    return s, mean, std


# --------------------------------------------------------------------------- train

def cmd_train(args) -> int:
    from diffusers import DDPMScheduler

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(args.out)
    (out / "checkpoints").mkdir(parents=True, exist_ok=True)
    torch.manual_seed(args.seed)
    s, mean, std = _load_norm(out)
    mean, std = mean.to(device), std.to(device)
    data = torch.load(out / "latents.pt")
    zp, zq = data["z_pre"].float(), data["z_post"].float()
    n = zp.shape[0]
    print(f"[train] {n} latents on {device}, batch={args.batch} epochs={args.epochs}")

    unet = build_unet().to(device)
    sched = DDPMScheduler(num_train_timesteps=1000, beta_schedule="linear", prediction_type="epsilon")
    opt = torch.optim.AdamW(unet.parameters(), lr=args.lr, betas=(0.9, 0.999), weight_decay=1e-4)
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    def norm(z):
        return (z.to(device) - mean) / std

    history, t0 = [], time.time()
    for epoch in range(args.epochs):
        unet.train()
        perm = torch.randperm(n)
        agg, nb = 0.0, 0
        for i in range(0, n, args.batch):
            idx = perm[i:i + args.batch]
            pre = norm(zp[idx]); post = norm(zq[idx])
            noise = torch.randn_like(post)
            ts = torch.randint(0, sched.config.num_train_timesteps, (post.shape[0],), device=device)
            noisy = sched.add_noise(post, noise, ts)
            with torch.autocast("cuda", enabled=use_amp):
                pred = unet(torch.cat([noisy, pre], dim=1), ts).sample
                loss = F.mse_loss(pred, noise)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
            scaler.step(opt); scaler.update()
            agg += float(loss.detach()); nb += 1
        rec = {"epoch": epoch, "loss": agg / max(1, nb), "sec": round(time.time() - t0, 1)}
        history.append(rec)
        if epoch % max(1, args.log_every) == 0 or epoch == args.epochs - 1:
            print(f"[epoch {epoch}] loss={rec['loss']:.4f} t={rec['sec']}s", flush=True)
        torch.save(unet.state_dict(), out / "checkpoints" / "unet_last.pt")
        if args.ckpt_every and (epoch % args.ckpt_every == 0 or epoch == args.epochs - 1):
            torch.save(unet.state_dict(), out / "checkpoints" / f"unet_e{epoch}.pt")
        (out / "train_history.json").write_text(json.dumps({"args": vars(args), "history": history}, indent=2))
    print(f"[train] done in {time.time() - t0:.0f}s -> {out/'checkpoints'/'unet_last.pt'}")
    return 0


# --------------------------------------------------------------------------- eval (sample -> .mha)

@torch.no_grad()
def sample_post(unet, sched, vae, mean, std, pre_unit2d: np.ndarray, device, steps: int) -> torch.Tensor:
    """DDIM-sample a post latent conditioned on pre, decode to grayscale [-1,1] 512x512."""
    pre_lat = (encode_image(vae, pre_unit2d, device) - mean) / std
    x = torch.randn(1, LATENT_CH, LATENT_SIZE, LATENT_SIZE, device=device)
    sched.set_timesteps(steps, device=device)
    for t in sched.timesteps:
        eps = unet(torch.cat([x, pre_lat], dim=1), t.expand(1)).sample
        x = sched.step(eps, t, x).prev_sample
    post_lat = x * std + mean
    return decode_latent(vae, post_lat)  # (1,1,512,512) in [-1,1]


def cmd_eval(args) -> int:
    from diffusers import DDIMScheduler

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(args.out)
    pred_dir = out / f"eval_{args.tag}" / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    s, mean, std = _load_norm(out)
    mean, std = mean.to(device), std.to(device)
    vae = load_vae(device)
    unet = build_unet().to(device).eval()
    unet.load_state_dict(torch.load(args.ckpt, map_location=device))
    sched = DDIMScheduler(num_train_timesteps=1000, beta_schedule="linear", prediction_type="epsilon")

    holdout = _manifest_cases(args.manifest, "holdout")
    print(f"[eval] {len(holdout)} holdout cases, steps={args.steps}, ckpt={args.ckpt}")
    for cid, pre_p, _post_p in holdout:
        ref = sitk.ReadImage(str(pre_p))
        native = _load_2d(pre_p)
        rec = sample_post(unet, sched, vae, mean, std, zscore_to_unit(native), device, args.steps)
        rec = F.interpolate(rec, size=native.shape, mode="bilinear", align_corners=False)[0, 0].cpu().numpy()
        z = unit_to_zscore(rec).astype(np.float32)
        img = sitk.GetImageFromArray(z)
        img.CopyInformation(ref)
        sitk.WriteImage(img, str(pred_dir / f"{cid}.mha"))
    print(f"[eval] wrote {len(list(pred_dir.glob('*.mha')))}/{len(holdout)} -> {pred_dir}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("encode")
    pe.add_argument("--manifest", required=True)
    pe.add_argument("--out", required=True)

    pt = sub.add_parser("train")
    pt.add_argument("--out", required=True)
    pt.add_argument("--epochs", type=int, default=200)
    pt.add_argument("--batch", type=int, default=32)
    pt.add_argument("--lr", type=float, default=1e-4)
    pt.add_argument("--seed", type=int, default=7)
    pt.add_argument("--ckpt_every", type=int, default=25)
    pt.add_argument("--log_every", type=int, default=10)

    pv = sub.add_parser("eval")
    pv.add_argument("--out", required=True)
    pv.add_argument("--manifest", required=True)
    pv.add_argument("--ckpt", required=True)
    pv.add_argument("--tag", default="nact_loso")
    pv.add_argument("--steps", type=int, default=50)

    args = ap.parse_args(argv)
    return {"encode": cmd_encode, "train": cmd_train, "eval": cmd_eval}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
