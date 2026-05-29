# Phase 1B Ablation Readiness Analysis

Date: 2026-05-29
Updated: 2026-05-30

## Verdict

The repository is ready for **local exploratory Phase 1B ablation runs**, but not ready to promote a submission candidate. The current evidence is useful for choosing the next ablation direction, but it is still small-split evidence: debug hold-out `n=2`, center/source-proxy held-out `n=4`, and larger-train `n=6` against the same `n=4` NACT hold-out. The latest completed capacity check shows base8 is dominated by base16 on 7 of 8 fixed-evaluator metrics, while train6 base16 remains mixed and non-promotable. The next work should prioritize an explicit full-dataset or fuller eligible-dataset split/config for the U-Net baseline before any submission packaging or heavier model family work.

## Reviewed sources

- Project docs: `README.md`, `STRATEGY.md`, `CONTEXT.md`, `docs/gc_mamasynth_metrics.md`, `docs/prd/phase-1b-ablation-and-domain-robustness.md`.
- Preprocessing code: `src/preprocessing/preprocess.py`, `src/preprocessing/compute_dataset_stats.py`.
- Evaluation code: `src/evaluation/evaluate.py`, `src/evaluation/evaluators/`.
- Phase 1A contracts: `src/phase1a/config.py`, `src/phase1a/dataset.py`, `src/phase1a/run.py`, `src/phase1a/evaluation_runner.py`, `src/phase1a/promotion.py`, `src/phase1a/submission.py`.
- Phase 1B code: `src/phase1b/config.py`, `src/phase1b/ablation_groups.py`, `src/phase1b/models.py`, `src/phase1b/augmentation.py`, `src/phase1b/runner.py`, `src/phase1b/run.py`, `src/phase1b/packaging.py`.
- Experiment/config assets: `configs/phase1a/`, `configs/phase1b/`, `splits/`, and ignored local artifacts under `experiments/phase1b/`.

## Current pipeline structure

### Data and preprocessing

- Raw local data is available through the ignored `datasets` symlink/path, including `images/`, `segmentations/`, `patient_info_files/`, `train_test_splits.csv`, and nnU-Net pretrained weight archives.
- `src/preprocessing/compute_dataset_stats.py` computes global pre-contrast normalization statistics; `src/preprocessing/training_pre_stats.json` is the checked-in default.
- `src/preprocessing/preprocess.py` converts 3D DCE-MRI volumes plus segmentations into 2D `.mha` artifacts:
  - `mha/input` for pre-contrast input.
  - `mha/ground_truth` for peak-enhancement post-contrast ground truth.
  - `mha/mask` for tumor masks used only for training and hold-out evaluation.
- Strategy constraint: submission outputs remain 2D `float32` `.mha` in z-score space with spacing/origin/direction metadata preserved.

### Phase 1A baseline contracts

- Phase 1A established the shared contracts that Phase 1B must preserve:
  - split manifest under `splits/` with train/hold-out membership and metadata;
  - pre-contrast-only inference;
  - residual target learning internally (`post - pre`);
  - output as synthetic post, not residual;
  - tumor mask allowed for training loss/evaluation, not for submission inference;
  - fixed downstream evaluator settings for comparable hold-out evaluation;
  - promotion based on metric-group evidence and submission smoke-test readiness.
- `configs/phase1a/debug_holdout_real_v1.yaml` is a small DUKE-only debug split config, not promotion-grade model-selection evidence.

### Phase 1B implementation surface

- `src/phase1b/config.py` validates Phase 1B configs on top of Phase 1A-compatible sections and fixed evaluator compatibility.
- `src/phase1b/ablation_groups.py` enforces isolated ablation planning: single-factor experiments should precede combined experiments.
- `src/phase1b/models.py` implements a small NumPy 2D U-Net residual regressor comparator with configurable `base_channels`.
- `src/phase1b/augmentation.py` implements seeded paired domain/intensity augmentation while preserving pre/post/mask alignment.
- `src/phase1b/run.py` is the runnable train/inference driver. Canonical command pattern:

```bash
PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/<config>.yaml
```

- `src/phase1b/runner.py` and `src/phase1b/packaging.py` provide stable ablation summaries and packaging gates, but packaging is only appropriate after promotion evidence exists.

### Evaluation pipeline

- `src/evaluation/evaluate.py` supports local evaluation through environment variables:
  - `MAMA_PREDICTIONS_DIR`
  - `MAMA_PRECONTRAST_DIR`
  - `MAMA_GT_DIR`
  - `MAMA_MASKS_DIR`
  - `MAMA_MODELS_DIR`
  - `MAMA_OUTPUT_DIR`
  - `MAMA_ENSEMBLE=True`
  - `MAMA_SEG_FOLD=0`
- Challenge-aligned metric groups:
  1. image fidelity: MSE ↓, LPIPS ↓;
  2. tumor ROI realism: SSIM-tumor ↑, FRD ↓;
  3. downstream classification: AUROC contrast ↑, AUROC tumor ROI ↑;
  4. downstream segmentation: Dice ↑, HD95 ↓.
- Fixed evaluation models are present under `src/evaluation/models/`, including classifier `.pkl` files and nnU-Net fold 0 files. These are Git LFS-managed exceptions; generated checkpoints/predictions remain ignored artifacts.

### Submission templates

- `src/submission/identity-baseline/` is a pass-through smoke-test submission, not a performance baseline.
- `src/submission/submission-gan/` is the reference GAN submission template. It requires staged external model weights through `MODEL_WEIGHTS_DIR` before build/test; previous evidence indicates missing `30_net_G.pth` blocks reproducible reference GAN use unless weights are supplied.

## Available experiment assets

### Split manifests

- `splits/phase1a_debug_holdout_real_v1.json`
  - intent: debug hold-out;
  - 6 DUKE cases: 4 train, 2 hold-out;
  - useful for smoke/regression checks only.
- `splits/phase1b_center_heldout_nact_v1.json`
  - intent: model-selection hold-out, but still exploratory;
  - DUKE train `n=4`, NACT held-out `n=4`;
  - source/center-proxy held-out split with explicit note that evidence remains exploratory because training count is intentionally small.
- `splits/phase1b_train6_center_heldout_nact_v1.json`
  - intent: larger-train re-evaluation path for the current strongest U-Net family;
  - DUKE train `n=6`, same fixed NACT held-out `n=4`;
  - remains exploratory because the independent hold-out is still small and previous mixed-shape train cases exposed the current comparator's native-shape constraint.

### Phase 1B configs

- Disabled U-Net residual comparator:
  - `configs/phase1b/unet_residual_smoke_v1.yaml`
  - `configs/phase1b/unet_residual_smoke_center_heldout_nact_v1.yaml`
- Scanner/protocol intensity augmentation variants:
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_v1.yaml`
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_seed29_v1.yaml`
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_narrow_v1.yaml`
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_wide_v1.yaml`
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_seed29_center_heldout_nact_v1.yaml`
- Capacity variants:
  - `configs/phase1b/unet_residual_base8_center_heldout_nact_v1.yaml`
  - `configs/phase1b/unet_residual_base16_center_heldout_nact_v1.yaml`
  - `configs/phase1b/unet_residual_base16_train6_center_heldout_nact_v1.yaml`

### Existing local evidence

- Debug augmentation comparison: `experiments/phase1b/augmentation_comparison_v1.json`.
  - Scanner/protocol intensity slightly improved image MSE but worsened tumor ROI MSE on `n=2` debug evidence.
- Debug scanner sensitivity: `experiments/phase1b/scanner_protocol_sensitivity_v1.json`.
  - ROI MSE degradation/improvement was seed/range-sensitive; seed29 mild was the only debug variant that mildly improved ROI MSE versus disabled.
- Debug official shortlist: `experiments/phase1b/official_shortlist_comparison_v1.json`.
  - Seed29 mild improved FRD, LPIPS, and SSIM-tumor slightly, worsened MSE slightly, and tied AUROC/segmentation on `n=2`.
- Center-held-out comparison: `experiments/phase1b/center_heldout_v1/center_heldout_comparison_v1.json`.
  - On `n=4` NACT held-out evidence, scanner seed29 mild improved LPIPS and AUROC-contrast, tied AUROC-tumor/segmentation, but worsened MSE, SSIM-tumor, and FRD.
  - Promotion decision: exploratory only.
- Base16 center-held-out comparison: `experiments/phase1b/center_heldout_v1/base16_comparison_v1.json`.
  - Base16 improved LPIPS, FRD, AUROC-contrast, Dice, and HD95 versus disabled, but worsened MSE and substantially worsened SSIM-tumor.
  - Promotion decision: exploratory only, no submission promotion.
- Train6 base16 promotion re-evaluation: `experiments/phase1b/train6_center_heldout_v1/base16_train6_promotion_reevaluation_v1.json`.
  - Train6 base16 improved MSE, SSIM-tumor, Dice, and HD95 versus train4 base16, but worsened LPIPS, FRD, AUROC-contrast, and AUROC-tumor-ROI.
  - Promotion decision: `no_promotion_exploratory_only`.
- Base8 versus base16 capacity comparison: `experiments/phase1b/center_heldout_v1/base8_vs_base16_capacity_comparison_v1.json`.
  - Base16 won 7 of 8 fixed-evaluator metrics; base8 won only AUROC-tumor-ROI, which is a single-case swing at `n=4`.
  - Decision: base8 is dominated on the current center-held-out evidence and should not be the next capacity direction unless full-dataset evidence changes the tradeoff.

## External requirements and known blockers

- `uv` is the expected command runner.
- `requirements.txt` includes `SimpleITK`, `scikit-learn`, `scipy`, `scikit-image`, AIM-Harvard `pyradiomics`, `frd-score`, `torchmetrics`, `torch<2.10`, `nnunetv2`, `numpy`, `pandas`, `xgboost<2.0`, and `tqdm`.
- Full evaluation needs fixed evaluator models under `src/evaluation/models/`; they are present in this checkout.
- Reference GAN build/test remains blocked without staged GAN weights (`MODEL_WEIGHTS_DIR` containing the expected `30_net_G.pth`).
- Promotion-grade conclusions are blocked by small local split size and weak segmentation evidence, not by missing evaluation infrastructure.
- Full-dataset or fuller eligible-dataset training is currently blocked on explicit split semantics and, for mixed native-size cases, a deliberate shape-handling path such as bucketing, pad/crop-back, or PyTorch/CUDA data loading. The output contract remains native-size synthetic post `.mha` with metadata preserved.
- Generated experiment outputs, predictions, and checkpoints live under ignored `experiments/` and must not be committed or uploaded.

## Ablation candidate matrix

| Priority | Candidate | Purpose | Expected effect | Needed change | Cost | Validation | Main risk |
|---|---|---|---|---|---|---|---|
| P0 | Full-dataset or fuller eligible-dataset U-Net baseline split/config | Move from tiny exploratory evidence to the largest safe local training surface | Reduces false conclusions from `n=2`/`n=4`/`n=6` evidence and tests whether base16 gains persist | New explicit split manifest/config; may require minimal shape-handling support before training all eligible cases | Medium/high due preprocessing + training/eval | Smoke/inference checks if no independent hold-out remains; otherwise full four metric groups with fixed evaluator settings | Split leakage risk, mixed native shapes, and non-promotion-grade evidence if no independent hold-out remains |
| P1 | Capacity sweep constrained to U-Net residual regressor (`base_channels` 4/8/16) | Test whether base16 gains are capacity-driven and whether SSIM-tumor loss can be controlled | Potential LPIPS/FRD/Dice gains with better regularization choice | Add base8 config; reuse existing base4/base16 pattern | Low/medium | Same split, same losses, full evaluator for shortlist | Higher capacity worsens MSE/SSIM or overfits tiny train set |
| P1 | Tumor ROI loss weight sweep | Directly target SSIM-tumor/FRD regression seen in base16 | Improve tumor-local structure without changing architecture | Configurable tumor loss weight if not already exposed in runner; otherwise minimal config support | Low | Early image+ROI metrics first; full evaluator if ROI improves without large MSE hit | Over-weighting ROI can create artifacts and hurt classification/segmentation |
| P1 | Scanner/protocol intensity augmentation seed/range replication on larger split | Decide whether seed29 mild was noise or robust | Improved domain robustness and AUROC-contrast without ROI penalty | Reuse existing augmentation configs with larger split variants | Medium | Compare disabled vs seed29 mild vs narrow on same split | Augmentation can hurt SSIM-tumor/FRD as already observed |
| P2 | LPIPS/perceptual loss as isolated loss term | Address perception-distortion balance beyond MSE | Improve LPIPS and visual realism | Add loss term and config validation; keep inference unchanged | Medium | Early MSE/LPIPS/SSIM/FRD; full evaluator only if not degraded | Perceptual loss may hallucinate or hurt MSE/segmentation |
| P2 | Feature matching / pix2pixHD-style strengthened comparator | Test STRATEGY-recommended GAN-family enhancement | Sharper enhancement and better ROI realism | Larger code change or reuse `submission-gan`/Phase 1A backbone cleanly | High | Same split, fixed evaluator, smoke inference contract | Complexity, weight staging, and hard-to-interpret combined changes |
| P2 | ROI context/dilation ablation | Test whether tumor-adjacent context improves realism | Improve SSIM-tumor/FRD and segmentation boundary cues | Expose/use existing ROI context config path in loss/data | Medium | ROI metrics and segmentation utility | Context leakage or overfitting if masks influence inference path indirectly |
| P3 | Auxiliary segmentation objective | Bias synthetic post toward segmentable lesions | Improve Dice/HD95 and tumor utility | Add auxiliary head/loss while keeping pre-contrast-only inference | High | Full evaluator required; ensure synthetic post output unchanged | May optimize evaluator behavior rather than image realism |
| P3 | Tumor ROI discriminator | Local adversarial pressure on tumor patches | Improve FRD/SSIM-tumor | New discriminator/training loop; isolated after simpler loss tests | High | ROI metrics and classification utility | Instability and hallucination risk |
| P4 | Predicted-mask conditioning | Explore mask-conditioned inference without GT masks | Potential tumor-local gains if loss-only approach plateaus | New predicted mask model and synthesis input contract | Very high | Separate PRD/goal before implementation | Changes inference contract and may be too risky for current phase |

## Recommended next-step order

1. Do **not** package or promote a submission candidate yet.
2. Create a full-dataset or fuller eligible-dataset split/config for the U-Net residual-regressor baseline. If all eligible cases are used for training and no independent hold-out remains, label the result as training/smoke evidence rather than promotion-grade evidence.
3. Resolve mixed native-size handling explicitly before claiming full-dataset support: shape buckets, pad/crop-back, or PyTorch/CUDA data loading are acceptable only if synthetic post outputs remain native-size `float32` `.mha` with metadata preserved.
4. Run the baseline U-Net path first, with base16 as the current preferred capacity point. Base8 is deprioritized because it was dominated by base16 on the current center-held-out evidence.
5. If GPU/time remains after the baseline is stable, run one isolated low-cost ablation at a time: tumor ROI loss-weight sweep first, then scanner/protocol intensity augmentation replication.
6. Only after the baseline and low-cost ablations are characterized should heavier LPIPS/perceptual, feature-matching/pix2pixHD-style, auxiliary segmentation, or tumor ROI discriminator work start.
7. Predicted-mask conditioning or any inference-contract-changing approach requires separate user approval and likely a separate PRD/goal.
8. Only after a candidate improves or is non-inferior across the four metric groups should packaging or official Validation phase submission be considered.

## Suggested commands for the next goal

Existing command pattern for train/inference:

```bash
PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_smoke_center_heldout_nact_v1.yaml
PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_scanner_protocol_intensity_seed29_center_heldout_nact_v1.yaml
PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_base16_center_heldout_nact_v1.yaml
```

Existing focused validation pattern:

```bash
PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_split_manifest.py -q
```

For full official local evaluator runs, keep these settings fixed across candidates:

```bash
MAMA_MODELS_DIR=src/evaluation/models
MAMA_ENSEMBLE=True
MAMA_SEG_FOLD=0
```

## Boundary decision

This analysis intentionally does not start new long-running training, full-dataset preprocessing, container builds, official submissions, or protected artifact uploads. The current next implementation goal is the P0 full-dataset/fuller eligible-dataset U-Net baseline transition; it should define the split, candidate config, metrics or smoke-only evidence rules, and promotion boundary before execution. Any subsequent ablation should be announced in order before it starts.
