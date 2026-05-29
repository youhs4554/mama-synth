# Pretrained Generative Models for MAMA-SYNTH 2026 — Deep Research Report

> Goal: maximally leverage existing **pretrained** generative models (fine-tune / transfer / ensemble) to
> synthesize peak-enhancement post-contrast breast DCE-MRI 2D slices from a single pre-contrast T1 slice,
> scoring well across all 4 equal-weight metric groups (fidelity MSE/LPIPS, tumor-ROI SSIM/FRD,
> classification AUROC, segmentation Dice/HD95) on the official nnU-Net evaluator.
>
> Author: deep-research pass, 2026-05-30. Local training GPU = RTX A4500 20GB.
> Eligibility cutoff: public + documented + accessible before **2026-05-07 23:59 CET**; no NIH CADR / private data.
>
> Honesty note: web access is the source of truth here. Where a fact could not be confirmed across ≥2 sources
> it is flagged **[uncertain]**. No weights were downloaded; no code was modified.

---

## (a) Executive summary

The single most important finding is a **scarcity of directly usable pretrained breast-MRI pre→post weights**:
across the entire surveyed landscape, **only one** public checkpoint actually exists for this exact task —
**medigan `00023` (pix2pixHD, Duke), Zenodo `10.5281/zenodo.10215478`, CC-BY-4.0** — and we already have it and
already know it transfers poorly to NACT (MSE 0.856, negative SSIM-tumor, AUROC-contrast 0.25 on our n=4 NACT
hold-out). Every other strong, design-aligned candidate (CC-Net latent diffusion, TeNCA, the Ibarra DDPM
comparison) ships **code + public training data but NO released weights**, so "leverage pretrained" for those
really means "reproduce/train using their public, eligible recipe + public data," not "download and fine-tune."

Therefore the highest-ROI strategy is **not** to keep fine-tuning the weak Duke pix2pixHD checkpoint, and **not**
to chase an unavailable diffusion checkpoint, but to **transfer architecture + recipe (not weights)** from the
challenge organizers' own MAMA-MIA work, training on our already-preprocessed full eligible dataset
(DUKE+ISPY1+ISPY2 = 1153 staged) with the proven design (subtraction target + tumor-ROI-weighted loss +
feature-matching/adversarial), then optionally warm-starting from `00023` and from generic Stable Diffusion
autoencoder weights where they genuinely help.

### Ranked shortlist of pretrained-model leverage strategies (ROI × feasibility on A4500 20GB)

| Rank | Strategy | What is actually "pretrained / leveraged" | Why ranked here |
|---|---|---|---|
| **1** | **Train our own pix2pixHD on full MAMA-MIA-eligible set, warm-started from `00023` generator weights**, with SUB target + ROI-weighted L1 + feature-matching + adversarial (organizers' `pre_post_synthesis` / `SimulatingDCE` codebase). | `00023` weights as initialization + organizers' open code (Apache-2.0 / CC-BY-4.0). | Only path that reuses a real breast-MRI checkpoint, fits 512² on 20GB easily, fixes the Duke→multi-source domain gap by *training on the target distribution*, and is the design the challenge was built around. Strong on MSE/LPIPS + ROI. Lowest risk. |
| **2** | **Reproduce CC-Net (ContrastControlNet) latent diffusion**: frozen Stable Diffusion 2.1 autoencoder (HF weights, leveraged) + trainable ControlNet conditioned on pre-contrast, on public Duke/MAMA-MIA. | SD2.1 VAE weights (frozen, downloadable) + organizers' Apache-2.0 ccnet code. CC-Net's *own* weights are NOT released. | Best expected FRD / realism (group 2/3) and the only diffusion path that fits 20GB (latent space, batch ≤8). Higher effort + hallucination risk; needs training from scratch on top of the frozen VAE. |
| **3** | **Reproduce the Ibarra 2025 DDPM comparison best config (SUB-ROI, full-breast)** using their MIT-licensed `conditional-diffusion-breast-MRI` repo on MAMA-MIA. | Open MIT code + public MAMA-MIA. No weights released. | Most metric-evidence-backed recipe (organizer-adjacent, 22 variants benchmarked, SUB consistently best across 5 metrics). Custom 2D DDPM, 20GB-friendly. Effort = full training run. |
| **4** | **Reproduce / train TeNCA** (13k-param temporal NCA) as a cheap fidelity-group specialist for ensembling. | Apache-2.0 code, public MAMA-MIA+Duke. No weights released. | Trivial to fit (13k params), best LPIPS/SSIM/PSNR in its paper, but weak FRD. Use as group-1 specialist in a metric-group ensemble, not as a standalone submission. |
| **5** | **MONAI Generative / MAISI VAE as a generic latent-space backbone** if SD2.1 VAE underperforms on MRI. | Apache-2.0, downloadable MAISI/MONAI VAE weights (CT+MRI). | Plausible drop-in autoencoder for strategy 2; MAISI is CT-centric and 3D, so MRI-2D fit is **[uncertain]**. Backup only. |
| **6** | **medigan `00023` direct fine-tune (continue current path)** | The `00023` weights themselves. | Already shown weak on NACT; fine-tuning may help but is dominated by strategy 1 (which subsumes it as initialization). Keep only as the reproducible *baseline*, not the bet. |

**Bottom line:** the leverage is mostly in *open recipes + open data + a frozen SD/MAISI autoencoder + the `00023`
checkpoint as a warm start* — not in any single downloadable breast-MRI generator. Build a pix2pixHD-first
submission (strategy 1) now; develop CC-Net-style latent diffusion (strategy 2) as the realism/FRD challenger;
keep TeNCA as a cheap ensemble specialist.

---

## (b) Comparison table

Effort key: **Low** = use/fine-tune existing weights; **Med** = reproduce on public data, single training run; **High** = multi-stage training (e.g. ControlNet) or substantial adaptation.

| Model / resource | Weights available? | License (code / weights) | Eligible (public + accessible pre-2026-05-07)? | Strengths by metric group | Effort | Notes |
|---|---|---|---|---|---|---|
| **medigan `00023_PIX2PIXHD_BREAST_DCEMRI`** (`pre_post_synthesis`) | **Yes** — Zenodo `10.5281/zenodo.10215478` (`00023.zip`, ~691 MB; `30_net_G.pth`) | Code Apache-2.0 / weights **CC-BY-4.0** | **Yes** (pub. 2023-11-28; medigan-installable) | ① fidelity decent on Duke; weak cross-domain. ② ROI moderate. Weak ③④ on NACT in our runs. | Low (already have) | The ONLY downloadable breast pre→post checkpoint. Duke-only ⇒ domain shift to NACT/ISPY. Best used as **init**, not final. |
| **`SimulatingDCE`** (Osuala 2024, arXiv:2409.18872) | Shares same `00023` family weights (multi-sequence variant) **[uncertain whether the 3-phase generator weights are separately downloadable]** | Code **Apache-2.0** | **Yes** (2024) | Multi-phase DCE (512×512×3); peak-phase selectable. ① ② similar to 00023. | Low–Med | Same pix2pixHD lineage; outputs phases 1–3. Useful if we want explicit peak-phase channel. Trained on Duke (922 cases) only. |
| **CC-Net / `ccnet`** (Osuala MICCAI 2024, arXiv:2403.13890) | **No released weights** (code only) | Code **Apache-2.0** | **Yes** (code+Duke public) | ② **FRD/realism strong** (FRD 20.0 vs TeNCA 48.7 in TeNCA paper). ③ likely strong. ① weaker, hallucination risk. | High | SD2.1 VAE frozen + ControlNet(pre-contrast)+time/text conditioning. Latent ⇒ fits 20GB (batch≤8, latent scale s≈0.1, grad clip). Must train. |
| **TeNCA** (`LangDaniel/TeNCA`, arXiv:2506.18720, MICCAI 2025) | **No released weights** (code only) | Code **Apache-2.0** | **Yes** (trained on **public** MAMA-MIA + Duke; CC-BY data) | ① **best** in its class: LPIPS 0.12, SSIM 0.89, MS-SSIM 0.93, PSNR 32.3 (beats CC-Net). ② weak FRD (48.7). | Med | Only **13k params**; trivially fits 20GB. Temporal NCA on 168² patches, 1mm spacing. Group-1 ensemble specialist. |
| **Ibarra DDPM comparison** (`sebastibar/conditional-diffusion-breast-MRI`, arXiv:2508.13776) | **No released weights** (code only) | Code **MIT** | **Yes** (MAMA-MIA public; 92,838 paired 2D slices) | Benchmarks 22 variants; **SUB target consistently best across 5 metrics**; SUB-ROI + mask-cond improves ② tumor fidelity; full-breast > single-breast. | High | Custom 2D DDPM (U-Net + bottleneck self-attn). Most directly MAMA-MIA-validated recipe. Batch 16–32. Train from scratch. |
| **SynDiff** (`icon-lab/SynDiff`, arXiv:2207.08208, TMI 2023) | **Yes**, but for **IXI / BraTS** (T1↔PD, T1↔T2) — NOT breast | Code present (org repo) **[license uncertain]** | Code yes; weights not breast-relevant | Multi-contrast MRI translation; adversarial diffusion fast sampling. | High | Architecture transferable; **no breast pre→post weights**. Would need full retraining. Lower priority. |
| **medigan `00021_CYCLEGAN_BRAIN_MRI_T1_T2`** | Yes — Zenodo `10.5281/zenodo.7074555` | MIT-family (medigan) | Yes | Brain T1↔T2 only. | n/a | Only other MRI→MRI translation in zoo; **not breast, not pre→post**. Not applicable. |
| **MONAI Generative / MAISI** (`Project-MONAI/model-zoo`) | **Yes** — MAISI VAE+diffusion bundle (CT-centric; VAE works for CT+MRI) | **Apache-2.0** | **Yes** | Generic 3D LDM; VAE reusable as latent backbone. | Med–High | MAISI is CT-focused, 3D, unconditional-ish; not a pre→post translator. Use **only** the VAE as a backbone candidate for strategy 2. MRI-2D fit **[uncertain]**. |
| **BrLP** (`LemuelPuglisi/BrLP`, arXiv:2502.08560) | Code; weights brain-only | Code present **[license uncertain]** | Brain MRI only | Longitudinal 3D brain progression LDM. | n/a | **Not breast, not contrast.** Not applicable. |
| **Stable Diffusion 2.1 VAE** (HF `stabilityai/stable-diffusion-2-1`) | **Yes** (HF) | **CreativeML OpenRAIL / OpenRAIL++** | **Yes** | Frozen autoencoder enabler for CC-Net-style latent diffusion. | Low (download) | Not a generator for us; the **frozen latent backbone** CC-Net depends on. Check OpenRAIL terms for challenge use. |

---

## (c) Concrete next-step recommendation for MAMA-SYNTH

### Primary bet — Strategy 1: pix2pixHD-first, warm-started from `00023`, trained on the full eligible set

This is exactly the model-path re-alignment already recorded in `STRATEGY.md` §4.2 (2026-05-30) and is the
lowest-risk way to actually *use* a pretrained breast-MRI checkpoint.

1. **Code base:** organizers' open `pre_post_synthesis` (Apache-2.0) / `SimulatingDCE` pix2pixHD. We already have
   the `submission-gan` template wired to `00023` and the z-score↔PNG bridging, so the inference/packaging
   contract is solved.
2. **Initialization (the "leverage"):** load `00023` `30_net_G.pth` as the generator warm-start. It encodes a
   real pre→post breast-MRI prior; fine-tuning from it should converge faster and better than random init,
   *even though* its zero-shot NACT performance is weak.
3. **Train on target distribution:** our already-preprocessed full eligible local set (DUKE 200 + ISPY1 104 +
   ISPY2 849 = 1153 2D slices) — this directly closes the Duke→multi-source gap that broke zero-shot `00023`.
4. **Objective (proven design):** internal **subtraction target** Δ = post − pre; **ROI-weighted L1** using GT
   masks in loss only; **feature-matching loss** (pix2pixHD) to fight blur; **adversarial loss**. Output
   `post_hat = pre + Δ_hat` as z-score float32 `.mha`, pre-contrast-only inference. (Matches `CONTEXT.md` and
   the Ibarra finding that SUB + tumor-aware loss is consistently best.)
5. **Domain robustness:** strong intensity/scanner augmentation (already implemented in `phase1b/augmentation.py`)
   to generalize toward 3T Siemens (Radboud) / 1.5T GE (Fleming) test distributions.
6. **Expected metric impact:** ① MSE/LPIPS — strong (pix2pixHD + SUB is fidelity-friendly); ② SSIM-tumor/FRD —
   improved by ROI-weighted loss and on-distribution training; ③④ AUROC/Dice — improved vs the weak NACT
   `00023` baseline because the generator now sees ISPY/NACT-like contrast. Promote only on a **larger,
   reliable hold-out** than n=4.

### Challenger — Strategy 2: CC-Net-style latent diffusion for the realism/FRD group

Run in parallel/after, only if Phase-1 metrics plateau on groups ②③:

- Freeze a downloadable autoencoder (**SD2.1 VAE** first; **MAISI VAE** as fallback) — this frozen backbone is
  the genuine "pretrained leverage" and the reason it fits 20GB.
- Train a ControlNet conditioned on the pre-contrast slice (CC-Net recipe: latent scale s≈0.1, gradient-value
  clipping, DDPM 1000 steps, AdamW, batch ≤8) on public Duke+MAMA-MIA. Use SUB target.
- Use few-step / regression-style sampling (perception–distortion balance) so MSE does not collapse.
- Expected impact: best FRD + classification realism; watch hallucination harming MSE/LPIPS.

### Ensemble option — Strategy 4: TeNCA as a fidelity specialist

If groups split cleanly (TeNCA strong on ①, diffusion strong on ②③), TeNCA is 13k params and trains in minutes;
keep it as a candidate for a **single deterministic blended submission** (Phase 3), inference speed is unscored.

### What NOT to do

- Do not keep betting on zero-shot or light fine-tune of `00023` alone (dominated by strategy 1).
- Do not pursue SynDiff/BrLP/MAISI as *generators* — none ship breast pre→post weights; they offer only
  architecture/backbone reuse at high effort.
- Do not assume CC-Net or TeNCA weights are downloadable — **they are not**; budget for training.

---

## (d) Eligibility verdict

All recommended resources clear the **public + documented + accessible before 2026-05-07 23:59 CET** filter and
avoid NIH CADR / private data:

| Resource | Public before cutoff? | Data provenance | Verdict |
|---|---|---|---|
| medigan `00023` weights (Zenodo 10215478) | Yes (2023-11-28) | Duke-Breast-Cancer-MRI (TCIA, open-access) | **Eligible** |
| `pre_post_synthesis` / `SimulatingDCE` code | Yes (2024) | Duke (TCIA) | **Eligible** |
| `ccnet` code | Yes (MICCAI 2024) | Duke (TCIA) | **Eligible** |
| TeNCA code | Yes (arXiv Jun 2025) | MAMA-MIA + Duke (both public, CC-BY) | **Eligible** |
| `conditional-diffusion-breast-MRI` (Ibarra) | Yes (arXiv Aug 2025) | MAMA-MIA (public) | **Eligible** |
| SD2.1 VAE (HF) | Yes (2022) | LAION (general images) | **Eligible** — verify OpenRAIL terms allow challenge use **[verify]** |
| MAISI / MONAI model-zoo | Yes (2024) | Public CT/MRI collections | **Eligible** (Apache-2.0) |

**Flags / caveats:**
- **MAMA-MIA dataset license is CC-BY-NC** (non-commercial), per the Nature Scientific Data record — fine for
  this academic challenge (it is the challenge's own training set), but note the non-commercial term. Source:
  Synapse `syn60868042`, arXiv:2406.13844.
- **TeNCA reports training on MAMA-MIA + Duke** with a 300-case MAMA-MIA test split; ensure any reproduction
  respects the challenge's hidden validation/test cases (no leakage). Both source datasets are public.
- **`00023` was trained on Duke only** — its weak NACT/ISPY zero-shot behavior is a *domain-shift* artifact, not
  an eligibility problem.
- **No NIH CADR data** is used by any recommended resource.

---

## (e) Full citations

**medigan zoo & breast pre→post (pix2pixHD, `00023`)**
- medigan repo + global.json: https://github.com/RichardObi/medigan ; config https://github.com/RichardObi/medigan/blob/main/config/global.json
- medigan paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC9940031/ (PubMed 36814939)
- `00023` paper "Pre- to Post-Contrast Breast MRI Synthesis for Enhanced Tumour Segmentation" (SPIE MI 2024): arXiv:2311.10879 — https://arxiv.org/abs/2311.10879
- `00023` code: https://github.com/RichardObi/pre_post_synthesis
- `00023` weights (Zenodo concept DOI `10.5281/zenodo.10215478`, CC-BY-4.0, `00023.zip` ~691 MB; version records 10210944/10210945): https://zenodo.org/records/10210944
- `SimulatingDCE` (multi-sequence DCE GAN): arXiv:2409.18872 — https://arxiv.org/abs/2409.18872 ; code https://github.com/RichardObi/SimulatingDCE (Apache-2.0)

**CC-Net latent diffusion**
- "Towards Learning Contrast Kinetics with Multi-Condition Latent Diffusion Models" (MICCAI 2024): arXiv:2403.13890 — https://arxiv.org/abs/2403.13890 ; Springer https://link.springer.com/chapter/10.1007/978-3-031-72086-4_67
- code (Apache-2.0, **no released weights**): https://github.com/RichardObi/ccnet

**TeNCA**
- "Temporal Neural Cellular Automata … contrast enhancement in breast MRI" (MICCAI 2025): arXiv:2506.18720 — https://arxiv.org/abs/2506.18720
- code (Apache-2.0, **no released weights**): https://github.com/LangDaniel/TeNCA ; project page https://langdaniel.github.io/TeNCA/

**Conditional diffusion comparison (MAMA-MIA, organizer-adjacent)**
- "Comparing Conditional Diffusion Models for Synthesizing CE Breast MRI from Pre-Contrast" (Deep-Breath @ MICCAI 2025): arXiv:2508.13776 — https://arxiv.org/abs/2508.13776
- code (MIT, **no released weights**): https://github.com/sebastibar/conditional-diffusion-breast-MRI

**Domain adaptation (organizer)**
- "Fat-Suppressed Breast MRI Synthesis for Domain Adaptation in Tumour Segmentation" (MICCAI 2024): https://link.springer.com/chapter/10.1007/978-3-031-77789-9_20 ; repo https://github.com/RichardObi/pre_post_synthesis

**Other generative codebases / backbones**
- SynDiff (TMI 2023): arXiv:2207.08208 — https://arxiv.org/abs/2207.08208 ; code https://github.com/icon-lab/SynDiff (pretrained weights for IXI/BraTS only)
- MAISI (3D LDM): arXiv:2409.11169 — https://arxiv.org/abs/2409.11169 ; MONAI model-zoo https://github.com/Project-MONAI/model-zoo/tree/dev/models/maisi_ct_generative ; MONAI GenerativeModels https://github.com/Project-MONAI/GenerativeModels
- BrLP (brain LDM): arXiv:2502.08560 — https://arxiv.org/abs/2502.08560 ; code https://github.com/LemuelPuglisi/BrLP
- Stable Diffusion 2.1 (frozen VAE backbone): https://huggingface.co/stabilityai/stable-diffusion-2-1

**Datasets / metrics**
- MAMA-MIA dataset (training set; CC-BY-NC; Synapse syn60868042): arXiv:2406.13844 — https://arxiv.org/abs/2406.13844 ; Nature Sci Data https://www.nature.com/articles/s41597-025-04707-4 ; repo https://github.com/LidiaGarrucho/MAMA-MIA
- FRD score (organizer metric): arXiv:2412.01496 ; PyPI https://pypi.org/project/frd-score ; repo https://github.com/RichardObi/frd-score

---

## Verification & uncertainty log

- **Confirmed across ≥2 sources:** `00023` = pix2pixHD breast DCE-MRI, Duke, 512², Zenodo 10215478, CC-BY-4.0
  (Zenodo record + medigan README + repo). TeNCA params (13k), datasets (MAMA-MIA+Duke public), and
  LPIPS/SSIM/FRD numbers (arXiv HTML). CC-Net = SD-based latent diffusion + ControlNet, Apache-2.0, no weights
  (repo + paper). Ibarra repo MIT, no weights, SUB best (repo + paper abstract). MAMA-MIA = DUKE/ISPY1/ISPY2/NACT,
  1506 cases, CC-BY-NC (Nature + arXiv).
- **[uncertain] / could not confirm:**
  - Whether `SimulatingDCE`'s multi-sequence 512×512×3 generator weights are downloadable separately from `00023`.
  - Exact SD autoencoder version and latent scale inside `ccnet` (README sparse; paper says SD2.1, s≈0.1 per
    project notes — not re-verified line-by-line this pass).
  - SynDiff and BrLP exact code licenses (repos exist; license text not individually opened).
  - Whether MAISI's VAE performs acceptably on 2D breast MRI (it is CT-centric, 3D) — needs an empirical spike.
  - SD2.1 OpenRAIL terms vs challenge commercial/redistribution constraints — **verify before submission**.
- **Single newest models** (any 2026 medigan additions beyond `00023`) could not be confirmed; the zoo as
  surveyed tops out at `00023` for breast and `00021` for any MRI→MRI translation.
