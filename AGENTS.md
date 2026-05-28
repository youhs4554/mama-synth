# Repository Guidelines

## Project Structure & Module Organization

This repository supports the MAMA-SYNTH breast MRI synthesis challenge. Core Python code lives in `src/`. Preprocessing utilities for slice extraction, normalization, and dataset statistics are in `src/preprocessing/`. Grand Challenge evaluation code is in `src/evaluation/`, with metric-specific evaluators under `src/evaluation/evaluators/` and tests under `src/evaluation/tests/`. Submission templates live in `src/submission/`: `identity-baseline/` is the pass-through smoke test, and `submission-gan/` is the Pix2PixHD baseline. Challenge documentation and static assets are in `docs/` and `docs/images/`.

## Challenge Strategy Reference

Before changing model design, preprocessing assumptions, or evaluation strategy, read `strategy.md`. It summarizes the MAMA-SYNTH task, metric tradeoffs, baseline constraints, and recommended development roadmap.

## Build, Test, and Development Commands

Install runtime dependencies from the repository root:

```bash
pip install -r requirements.txt
```

Run the Python test suite:

```bash
PYTHONPATH=src/evaluation pytest src/evaluation/tests src/preprocessing/test_preprocess.py -v
```

Run local evaluation after setting the required `MAMA_*` paths:

```bash
python src/evaluation/evaluate.py
```

Build and smoke-test the identity submission container:

```bash
cd src/submission/identity-baseline
./do_build.sh
./do_test_run.sh
./do_save.sh
```

For `submission-gan`, set `MODEL_WEIGHTS_DIR=/path/to/00023` before building.

## Coding Style & Naming Conventions

Use Python 3.10+ and match the existing style: 4-space indentation, clear `snake_case` names for functions and variables, and `PascalCase` for classes such as evaluator or test classes. Prefer `pathlib.Path` for filesystem work. Add type hints for public helpers where practical. No formatter configuration is checked in, so keep formatting consistent with nearby files and avoid broad reformatting.

## Testing Guidelines

Tests use `pytest`. Name test files `test_*.py`, group related checks in `Test*` classes, and use fixtures for temporary images, masks, or model artifacts. Prefer deterministic mock data, especially seeded NumPy arrays. Add regression tests for evaluator behavior, preprocessing edge cases, and Grand Challenge input/output contracts. Container changes should also be validated with the relevant `do_test_run.sh` script.

## Experiment Monitoring & Tracking

Use a local-first experiment tracker for model training and ablation runs. The default recommendation is MLflow with a local file backend under `experiments/mlruns`, optionally paired with TensorBoard event files under `experiments/tensorboard` for dense scalar/image inspection. These directories are generated artifacts and must stay out of commits, along with checkpoints, predictions, and exported containers.

Each training run should log enough context to reproduce the result: git commit, command line, config file path and resolved hyperparameters, dataset split identifier, preprocessing statistics, model architecture variant, random seed, checkpoint path, Docker/submission template version if relevant, and hardware/runtime metadata. Log validation metrics using the challenge grouping vocabulary: image fidelity (`mse`, `lpips`), tumor ROI realism (`ssim_tumor`, `frd`), classification proxies (`auroc_contrast`, `auroc_tumor_roi`), segmentation proxies (`dice`, `hd95`), and the proxy rank-average used for checkpoint selection.

Do not upload protected MRI slices, masks, generated challenge outputs, or model weights to cloud experiment trackers. If an external service such as Weights & Biases is used, run it in offline/private mode and log only scalar metrics, plots derived from aggregate metrics, sanitized configuration, and small non-identifying debug images when explicitly approved. Grand Challenge inference containers must not depend on a monitoring service because runtime network access is unavailable.

## Commit & Pull Request Guidelines

Recent history uses short imperative or descriptive commit messages, such as `Add submission documentation` and `Further updates during testing and debugging...`. Keep each commit scoped to one concern. Pull requests should describe the affected pipeline area, list validation commands run, note any required external data or model weights, and include metric excerpts or screenshots when outputs or documentation change.

## Security & Configuration Tips

Do not commit protected MRI data, generated challenge outputs, Docker archives, or downloaded model weights. Configure local runs through environment variables such as `MAMA_PREDICTIONS_DIR`, `MAMA_GT_DIR`, `MAMA_MASKS_DIR`, `MAMA_MODELS_DIR`, and `MAMA_OUTPUT_DIR`.
