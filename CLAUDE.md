# CLAUDE.md

This file is the operating brief for Claude agents working in this repository through `herdr`. It distills the repository `AGENTS.md`, `README.md`, `STRATEGY.md`, `CONTEXT.md`, and current Phase 1B handoff state. Read this before making changes.

## Repository mission

MAMA-SYNTH targets virtual contrast enhancement for breast MRI: given one pre-contrast T1-weighted 2D breast MRI slice, produce the matching synthetic peak-enhancement post-contrast `.mha` slice.

The project is currently in Phase 1B work: compare PyTorch/CUDA-capable 2D U-Net residual-regressor candidates and generate challenge-style synthetic `.mha` outputs while preserving the Phase 1A/Grand Challenge contracts.

## Hard rules

- Use `uv run ...` for Python, pytest, preprocessing, training, and evaluation commands. Do not use bare `python`, `pip`, or `pytest` unless `uv` is unavailable and you state that fallback.
- Keep changes surgical. Do not refactor adjacent code, reformat broad files, or clean up unrelated artifacts.
- Preserve existing user work and uncommitted changes. Do not revert anything you did not author unless explicitly asked.
- Do not commit or upload protected MRI slices, generated challenge outputs, checkpoints, model weights, Docker archives, or experiment directories.
- `experiments/`, generated predictions, checkpoints, and local dataset artifacts are local/ignored outputs. They may be used for evidence but must not be treated as source changes.
- Grand Challenge inference must remain pre-contrast-only. Training/evaluation may use masks locally, but submission inference must not require ground-truth masks.
- Synthetic outputs are final post-contrast slices, not residual images. The model may predict `post - pre` internally, then output `pre + residual` as z-score `float32` `.mha`.
- Preserve native input size and `.mha` metadata where the code path promises it.
- Use fixed local evaluator settings for comparable hold-out evaluation unless explicitly doing a separate sensitivity analysis: `MAMA_MODELS_DIR=src/evaluation/models`, `MAMA_ENSEMBLE=True`, `MAMA_SEG_FOLD=0`.
- Do not promote a submission candidate from debug/exploratory evidence alone. Record no-promotion decisions when metrics are mixed, train/hold-out sets are too small, or Dice remains weak.
- GPU 0 only — mandatory: always run GPU workloads on GPU 0 and never on any other GPU, even though the host has two cards. Set `CUDA_VISIBLE_DEVICES=0` on every GPU command — training, inference, and the official evaluator (its segmentation stage uses the GPU) — and explicitly override any tool/script default that points elsewhere (e.g. pass `--gpu 0`, since `eval_finetuned.py` defaults to GPU 1). Never use GPU 1, and never run on two GPUs at once. UPDATE 2026-05-30: heavy GPU load now hard-crashes this server **even with a single GPU 0 job** — a pix2pixHD fine-tune on GPU 0 alone (GPU 1 idle, verified) caused a logless instant shutdown at 10:58:52 with ~62s auto power-on, the same signature as the 03:17:47 crash (no kernel panic/thermal/OOM/MCE before the cut, no UPS present → load-correlated hard power cut / PSU or circuit overcurrent trip, NOT a concurrency-only issue). **Treat sustained GPU training as currently UNSAFE: do not launch GPU training/large eval without the user's go-ahead on the power/hardware fix.** Possible mitigations to discuss first: cap the A4500 power limit (`sudo nvidia-smi -i 0 -pl 100`, min 100W vs 200W default), smaller batch, add a UPS, or move heavy training off-box. Before any GPU job, run `nvidia-smi`, confirm GPU 0 free and no other GPU job active, and never fall back to GPU 1. UPDATE 2026-05-30 (decisive): at user direction we tried **GPU 1 (RTX 3080 Ti)** as a last resort — a 64-case nnU-Net eval crashed the server **again** at 11:25:58 (~56s auto power-on, same logless signature, no panic/thermal/MCE). **Both GPUs now reproduce the crash → this is a system-wide power fault (PSU/circuit), NOT GPU-specific. No heavy GPU work is safe on this box; move training/eval to another machine** (passwordless sudo is unavailable here, so power-capping must be done by the user). CPU-only work (preprocessing, inference, the official evaluator with `CUDA_VISIBLE_DEVICES=""`) is the only safe on-box compute.

## Design-grounded development (living-design workflow)

All development must be grounded in the design and strategy documents. Treat `STRATEGY.md` (strategy/roadmap/model design), `CONTEXT.md` (canonical terms), the relevant `docs/prd/` PRD, and `docs/adr/` ADRs as authoritative.

- Before implementing, confirm the approach matches these documents. Do not introduce a model architecture/framework, preprocessing assumption, evaluation strategy, or submission-contract change that contradicts them.
- If implementation reveals that a design or strategy change is genuinely needed (e.g., a new model family/framework, a different preprocessing/evaluation/submission policy), first get user approval for the change, then **update the authoritative document(s) in the same change** — record what changed, why, and the decision date — before or alongside the code. Code and design docs must not drift apart.
- Example of staying grounded: the synthesis generator follows `STRATEGY.md` §4.2 (pix2pixHD-first, then U-Net residual comparator, then latent diffusion). `nnU-Net v2` is the fixed evaluation segmenter only, never the generator (`CONTEXT.md`). Picking a generator framework outside the documented roadmap requires approval + a STRATEGY/PRD update first.
- When blocked between documented alternatives (e.g., reference-GAN inference vs training from scratch), stop and ask rather than silently choosing.

## Canonical project language

Use `CONTEXT.md` terms exactly:

- **Hold-out evaluation**, not local validation.
- **Validation phase** only means the official Grand Challenge phase.
- **Synthetic post** means the final z-score `float32` peak-enhancement prediction.
- **Tumor ROI** is available for local training/evaluation, not submission input.
- **Subtraction target** is the internal residual target `post - pre`.
- **Baseline** means reproducible performance comparison point, not smoke test or reference artifact.
- **Submission smoke test** verifies I/O/container behavior; it is not a model-performance baseline.

## Important files and surfaces

- `AGENTS.md`: repository rules. Follow it.
- `README.md`: operational entry point and command examples.
- `STRATEGY.md`: challenge strategy, metric tradeoffs, phase roadmap, preprocessing/evaluation assumptions.
- `CONTEXT.md`: canonical glossary.
- `docs/TODO.md`: long-running task progress and latest experiment handoffs.
- `docs/phase1b_ablation_readiness_analysis.md`: Phase 1B candidate/readiness notes.
- `src/phase1a/`: Phase 1A contracts for split manifests, configs, residual datasets, inference, losses, promotion gates, and submission packaging.
- `src/phase1b/`: Phase 1B U-Net comparator, augmentation, ablation runner, and CLI driver.
- `configs/phase1b/`: Phase 1B experiment configs.
- `splits/`: local split manifests.
- `src/evaluation/evaluate.py` and `src/evaluation/evaluators/`: official local evaluator surfaces.
- `src/submission/identity-baseline/`: GC I/O smoke-test template.
- `src/submission/submission-gan/`: reference GAN submission template; needs external `30_net_G.pth` via `MODEL_WEIGHTS_DIR`.

## Known Phase 1B state

Recent completed Phase 1B work recorded in `docs/TODO.md`:

- Center/source-held-out split: `splits/phase1b_center_heldout_nact_v1.json` with DUKE train and NACT hold-out evidence.
- Larger-train split: `splits/phase1b_train6_center_heldout_nact_v1.json` with DUKE train n=6 and fixed NACT hold-out n=4.
- Existing candidate configs include:
  - `configs/phase1b/unet_residual_smoke_center_heldout_nact_v1.yaml`
  - `configs/phase1b/unet_residual_scanner_protocol_intensity_seed29_center_heldout_nact_v1.yaml`
  - `configs/phase1b/unet_residual_base16_center_heldout_nact_v1.yaml`
  - `configs/phase1b/unet_residual_base16_train6_center_heldout_nact_v1.yaml`
- Existing comparison artifacts include:
  - `experiments/phase1b/center_heldout_v1/promotion_grade_comparison_v1.{json,md}`
  - `experiments/phase1b/train6_center_heldout_v1/base16_train6_promotion_reevaluation_v1.{json,md}`
- Latest recorded result: train6 base16 improved MSE, SSIM-tumor, Dice, and HD95 versus train4 base16, but worsened LPIPS, FRD, AUROC-contrast, and AUROC-tumor-ROI. Decision: `no_promotion_exploratory_only`.

## Common commands

Run focused Phase 1B validation:

```bash
PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_split_manifest.py -q
```

Run broad validation:

```bash
PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q
```

Run a Phase 1B train/inference config:

```bash
PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/<config>.yaml
```

Run local official evaluator after setting paths for predictions, pre-contrast, ground truth, masks, models, and output. Keep fixed evaluator settings unless this is explicitly a sensitivity analysis:

```bash
MAMA_PREDICTIONS_DIR=<prediction_dir> \
MAMA_PRECONTRAST_DIR=<input_dir> \
MAMA_GT_DIR=<ground_truth_dir> \
MAMA_MASKS_DIR=<mask_dir> \
MAMA_MODELS_DIR=src/evaluation/models \
MAMA_OUTPUT_DIR=<metrics_output_dir> \
MAMA_ENSEMBLE=True \
MAMA_SEG_FOLD=0 \
PYTHONPATH=src/evaluation uv run python src/evaluation/evaluate.py
```

## Long-running work policy

For training, full evaluator sweeps, preprocessing, or external-agent reviews:

1. Run in the background with durable logs under `experiments/.../logs/`.
2. Record the PID, log path, command, and monitor command.
3. Use a lightweight monitor/watchdog or periodic tailing.
4. Report first useful metrics, best-checkpoint changes, metric regressions, NaNs, OOM, stalls, completion, or failure.
5. Do not block the active session if other useful work can continue.

## Atopix sweep instruction

The current pi goal says to stop the Atopix sweep before delegating Phase 1B work. If asked to do this through `herdr` or shell commands:

- First identify the running job/session/process unambiguously.
- Stop only the Atopix sweep owned by this workflow.
- If multiple candidates exist or ownership is unclear, stop and ask the user rather than killing a process speculatively.
- Record evidence: command used, process/session id, status before and after.

## Delegation expectation for Claude via herdr

When a `herdr` task is delegated to Claude, the task should include:

- Read `CLAUDE.md`, `AGENTS.md`, `README.md`, `STRATEGY.md`, `CONTEXT.md`, and current `docs/TODO.md` relevant sections.
- Confirm Atopix sweep is stopped or out of scope before Phase 1B execution.
- Continue Phase 1B PyTorch/CUDA U-Net training + synthetic `.mha` generation work without violating pre-contrast-only inference.
- Prefer the existing Phase 1B CLI/config surfaces before adding new APIs.
- Run the most focused validation that covers changed behavior; run broad validation for risky/shared changes.
- Write durable experiment artifacts/logs under ignored `experiments/` paths.
- Return a concise status with changed files/artifacts, commands run, metrics, promotion/no-promotion decision, blockers, and next step.

## If blocked

Stop and ask instead of inventing a workaround when:

- `herdr` cannot find the target Claude session.
- Atopix sweep cannot be identified safely.
- dataset, model weight, CUDA, or evaluator paths are missing.
- a command would upload protected data or weights.
- a requested phase change would alter model design, preprocessing assumptions, evaluation strategy, or submission policy without user approval.

## Session-clear handoff note

This file exists so the next cleared session and the delegated Claude agent can recover the repository rules and current Phase 1B context. After a session clear, resume by checking:

1. `git status --short`
2. `docs/TODO.md` latest active task
3. `CLAUDE.md`
4. `herdr` CLI session list/status
5. Atopix sweep status
6. Phase 1B config/run/evaluator artifacts relevant to the next delegated task
