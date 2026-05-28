# Repository Guidelines

## Project Structure & Module Organization

This repository supports the MAMA-SYNTH breast MRI synthesis challenge. Core Python code lives in `src/`. Preprocessing utilities for slice extraction, normalization, and dataset statistics are in `src/preprocessing/`. Grand Challenge evaluation code is in `src/evaluation/`, with metric-specific evaluators under `src/evaluation/evaluators/` and tests under `src/evaluation/tests/`. Submission templates live in `src/submission/`: `identity-baseline/` is the pass-through smoke test, and `submission-gan/` is the Pix2PixHD baseline. Challenge documentation and static assets are in `docs/` and `docs/images/`.

## Challenge Strategy Reference

Before changing model design, preprocessing assumptions, or evaluation strategy, read `STRATEGY.md`. It summarizes the MAMA-SYNTH task, metric tradeoffs, baseline constraints, and recommended development roadmap.

## Domain Context & Grill-With-Docs Workflow

When a change involves fuzzy domain language, model-selection terminology, evaluation strategy, dataset boundaries, or submission policy, use a grill-with-docs workflow before implementation. This follows the AI Hero guidance for codebases: align the language used by the codebase, developers, and domain experts before building.

First look for `CONTEXT-MAP.md`; if it exists, use it to find the right bounded context. Otherwise look for a root `CONTEXT.md`. If neither exists, create `CONTEXT.md` lazily only after the first project-specific term or relationship is resolved with the user. This repository is currently treated as one context unless a context map is introduced.

During that workflow, ask one concrete, grillable question at a time, give a recommended answer, and check the code or existing docs when the answer can be discovered locally. Challenge ambiguous terms against `CONTEXT.md`; if the user says "baseline", "validation", "mask", "synthetic post", or similar overloaded terms, clarify the precise project meaning before naming files, variables, or experiments. Keep the scope small; split broad plans into smaller grilling sessions instead of exhausting the context window.

`CONTEXT.md` is a glossary, not a spec. Keep it free of implementation details, training recipes, TODOs, metric results, and architecture decisions. Store only stable shared language: canonical terms, short definitions, avoided aliases, relationships/cardinality, flagged ambiguities, and a small example dialogue when useful. For hard-to-reverse non-obvious tradeoffs, prefer a focused ADR under `docs/adr/` instead of expanding `CONTEXT.md`.

If grilling exposes a high-fidelity question that cannot be answered in words, pause the grilling thread, use a throwaway prototype or spike to answer that question, record the answer durably, and then return to the original planning thread. Do not clear the conversation context before creating the PRD; the resolved design decisions are valuable handoff material.

## PRD-to-TDD Delivery Workflow

For substantial features or experiment infrastructure, use this sequence: `grill-with-docs` → `to-prd` → `to-issues` → `tdd`. Do not skip directly to implementation when terms, acceptance criteria, or issue boundaries are still fuzzy.

1. `grill-with-docs`: resolve project language first. Update `CONTEXT.md` inline for agreed glossary terms and create ADRs only for hard-to-reverse, non-obvious tradeoffs.
2. `to-prd`: synthesize the agreed context into a PRD using canonical terms. Include problem statement, user stories, implementation decisions, testing decisions, out-of-scope items, and notes. If no issue tracker is configured, keep the PRD as a draft artifact instead of claiming it was published.
3. `to-issues`: break the PRD into independently grabbable tracer-bullet issues. Prefer thin vertical slices that are demoable or verifiable end-to-end; mark each as HITL or AFK, list dependencies, and get user approval before publishing or saving issue drafts.
4. `tdd`: implement one approved issue at a time. Use red-green-refactor with one behavior test at a time through public interfaces; do not write all tests first or couple tests to implementation details.

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
