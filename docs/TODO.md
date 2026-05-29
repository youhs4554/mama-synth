# TODO

- [x] Read `STRATEGY.md` and start grill-with-docs session.
- [x] Capture agreed glossary terms in `CONTEXT.md`.
- [x] Update `STRATEGY.md` to match agreed Phase 1A terminology and evaluation-model decisions.
- [x] Continue Phase 1A grilling on split manifest format.
- [x] Continue Phase 1A grilling on minimal model/training config schema.
- [x] Continue Phase 1A grilling on submission candidate promotion criteria.
- [x] Write Phase 1A PRD draft.
- [x] Request Codex review of `STRATEGY.md`, `CONTEXT.md`, and Phase 1A PRD.
- [x] Request Claude review of `STRATEGY.md`, `CONTEXT.md`, and Phase 1A PRD.
- [x] Collect review feedback.
- [x] Ask point-by-point whether to apply each suggestion.
- [x] Read Phase 1A PRD for issue breakdown.
- [x] Check glossary/strategy/repository context for domain vocabulary.
- [x] Get user approval on Phase 1A tracer-bullet issue breakdown.
- [x] Save approved issue drafts because no issue tracker CLI is available.
- [x] Install/configure `gh` CLI and enable GitHub Issues for the repository.
- [x] Publish approved issues to the issue tracker when tooling is available.

## Active goal: Phase 1A TDD implementation

- [x] Issue #1: Create split manifest contract and validator.
  - [x] RED: manifest validates deterministic train/hold-out fake cases.
  - [x] GREEN: minimal split manifest public interface passes tracer test.
  - [x] Add nullable center metadata and required-field/path validation tests.
  - [x] Add local-only split metadata/submission input contract test.
  - [x] Add debug vs model-selection split distinction test.
  - [x] Run targeted Issue #1 tests: `PYTHONPATH=src pytest src/phase1a/tests/test_split_manifest.py -q`.
- [x] Issue #2: Create single Phase 1A experiment config contract.
  - [x] RED: minimal valid config declares required sections.
  - [x] GREEN: minimal config validator passes tracer test.
  - [x] Add pre-contrast-only inference and synthetic post output validation tests.
  - [x] Add residual target validation test.
  - [x] Add fixed evaluator/sensitivity-analysis validation tests.
  - [x] Add ROI weighting defaults test.
  - [x] Run targeted Issue #2 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #3: Load manifest cases into a residual-synthesis dataset.
  - [x] RED: dataset loads deterministic fake train cases from valid split manifest.
  - [x] GREEN: minimal residual synthesis dataset passes tracer test.
  - [x] Add sample fields and residual `post - pre` test.
  - [x] Add pre-contrast-only inference sample test.
  - [x] Add matching case identity validation test.
  - [x] Run targeted Issue #3 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #4: Prove mask-free native-size synthetic post inference.
  - [x] RED: inference public API accepts pre-contrast only.
  - [x] GREEN: minimal residual inference contract passes tracer test.
  - [x] Add synthetic post = pre + predicted residual test.
  - [x] Add native-size padding/crop-back test.
  - [x] Add evaluation mask shape match test.
  - [x] Run targeted Issue #4 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #5: Add Phase 1A residual and tumor ROI weighted losses.
  - [x] RED: residual L1 returns expected deterministic value.
  - [x] GREEN: minimal residual L1 passes tracer test.
  - [x] Add tumor ROI weighted residual L1 deterministic mask test.
  - [x] Add mask-only-training-path / no inference conditioning test.
  - [x] Add empty-mask/no-tumor behavior test.
  - [x] Run targeted Issue #5 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #6: Run a minimal train/evaluate loop.
  - [x] RED: smoke-scale run trains/evaluates on deterministic fake data.
  - [x] GREEN: minimal train/evaluate runner passes tracer test.
  - [x] Add run record config/split/seed/checkpoint/inference settings test.
  - [x] Add synthetic post prediction-not-residual test.
  - [x] Add pre-contrast-only after training and ablations-out-of-scope tests.
  - [x] Run targeted Issue #6 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #7: Record identity lower-bound and reference GAN baseline evidence.
  - [x] RED: identity evidence is lower-bound, not primary performance baseline.
  - [x] GREEN: minimal baseline evidence validator passes tracer test.
  - [x] Add reproducible reference GAN required-fields test.
  - [x] Add same-split local ranking table test.
  - [x] Add promotion-deferred and human-approved alternative baseline tests.
  - [x] Run targeted Issue #7 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #8: Add staged hold-out evaluation runner.
  - [x] RED: early stage runs cheap metric groups only.
  - [x] GREEN: minimal staged evaluation runner passes tracer test.
  - [x] Add shortlist/full metric groups and fixed evaluator settings tests.
  - [x] Add changed fixed evaluator rejection test.
  - [x] Add stable metric-summary output test.
  - [x] Run targeted Issue #8 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #9: Implement promotion gate and audit bundle.
  - [x] RED: toy metric summary candidate accepted deterministically.
  - [x] GREEN: minimal promotion gate passes tracer test.
  - [x] Add >5% metric group worsening rejection test.
  - [x] Add two-group non-inferiority and local proxy rank mean tests.
  - [x] Add audit bundle metrics/config/inference/model hash test.
  - [x] Run targeted Issue #9 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Issue #10: Package checkpoint behind submission smoke tests.
  - [x] RED: submission-style inference consumes pre-contrast only.
  - [x] GREEN: minimal submission inference passes tracer test.
  - [x] Add readable native-size float32/finite output test.
  - [x] Add soft z-score and metadata preservation tests.
  - [x] Add submission-ready requires passing smoke test.
  - [x] Run targeted Issue #10 tests: `PYTHONPATH=src pytest src/phase1a/tests -q`.

## Completion audit fixes

- [x] Replace submission-only NPZ assumption with challenge-style `.mha` I/O support via SimpleITK when available.
- [x] Add `.mha` submission smoke test preserving spacing, origin, direction, and metadata keys.
- [x] Make the minimal train/evaluate loop use residual L1 and tumor ROI weighted residual L1 and record loss history.
- [x] Write `.mha` predictions for `.mha` manifest cases while preserving reference metadata.
- [x] Strengthen staged evaluator comparison to reject candidate-specific fixed evaluator setting changes.
- [x] Re-run Phase 1A tests after audit fixes: `PYTHONPATH=src pytest src/phase1a/tests -q`.
- [x] Align GC predictions.json loading with declared `relative_path` while retaining configured slug fallback.
- [x] Run broader repo validation: `PYTHONPATH=src:src/evaluation pytest src/phase1a/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Enforce promotion-gate audit bundle requirements: metrics, config, inference settings, and model hash must be present before acceptance.
- [x] Enforce reproducible reference GAN as the primary performance baseline.
- [x] Re-run broader validation after promotion/baseline audit fixes: `PYTHONPATH=src:src/evaluation pytest src/phase1a/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Enforce all four promotion metric groups before candidate acceptance: image fidelity, tumor ROI realism, classification utility, and segmentation utility.
- [x] Re-run broader validation after four-metric promotion gate fix: `PYTHONPATH=src:src/evaluation pytest src/phase1a/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.

## Active task: Phase 1A real-data baseline readiness

- [x] Check repository state and Phase 1A runnable surface.
- [x] Check for local dataset, split manifest, experiment outputs, and fixed evaluator model directories.
- [x] Add or identify the smallest command for running Phase 1A on a real split.
- [x] Run Phase 1A on real train/hold-out data.
- [x] Produce baseline metric table for Phase 1A before Phase 1B ablations.
  - [x] Compute identity lower-bound fidelity metrics on the debug hold-out split.
  - [x] Compute current constant-residual Phase 1A fidelity metrics on the same split.
  - [x] Save a comparable CSV/JSON metric table under ignored experiment outputs.

## Active task: Phase 1A real datasets split/config

- [x] Commit Phase 1A CLI changes.
- [x] Create a small real-data debug split from `datasets/train_test_splits.csv`.
- [x] Generate local 2D MHA artifacts under ignored `datasets/` paths for the split.
- [x] Write Phase 1A split manifest and YAML config.
- [x] Validate the generated manifest/config with the Phase 1A CLI.

## Active task: Claude design-doc sync after data munging

- [x] Delegate design-doc drift review/update to the running Claude agent via `herdr`.
- [x] Review Claude's changes and verify repository docs still match the real-data debug workflow.
- [x] Run focused validation after documentation/config updates.
- [x] Commit the resulting changes.

## Active task: Write PRDs for all STRATEGY phases

- [x] Confirm existing Phase 1A PRD and closed implementation issues.
- [x] Write missing Phase 0, Phase 1B, Phase 2, and Phase 3 PRDs.
- [x] Publish missing phase PRDs to the issue tracker with `ready-for-agent`.
- [x] Run lightweight validation and summarize created artifacts.

## Active goal: PRD-to-issues and TDD implementation

- [x] Read `/skill:to-issues` and `/skill:tdd` workflow requirements.
- [x] Review `docs/prd/` phase PRDs and current GitHub issue state.
- [x] Confirm Phase 1A tracer-bullet issues are already published and closed.
- [x] Get user approval on the Phase 0/1B/2/3 issue breakdown before publishing implementation issues.
- [x] Publish approved implementation issues in dependency order (`#15`-`#37`).
- [x] Issue #15 / P0-1: Audit local test, dataset, hardware, and preprocessing assumptions.
  - [x] RED: audit artifact records test command/result, dataset layout, preprocessing stats, and GPU assumptions.
  - [x] GREEN: minimal Phase 0 audit public interface passes tracer test.
  - [x] Add missing-path and protected-data-safe dataset summary tests.
  - [x] Run targeted Issue #15 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_infrastructure_audit.py -q`.
  - [x] Run Phase 0 validation audit check: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
  - [x] Write local ignored audit artifact: `experiments/phase0/infrastructure_audit.json`.
- [x] Issue #16 / P0-2: Generate challenge-like debug MHA artifacts and split manifest.
  - [x] RED: debug artifact manifest verifies pre/post/mask MHA paths and metadata expectations.
  - [x] GREEN: minimal Phase 0 debug artifact public interface passes tracer test.
  - [x] Add center/source metadata and local-only mask usage tests.
  - [x] Run targeted Issue #16 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_debug_artifacts.py -q`.
  - [x] Write local ignored audit artifact: `experiments/phase0/debug_artifacts_audit.json`.
- [x] Issue #17 / P0-3: Record identity lower-bound and stable metric output contract.
  - [x] RED: metric contract records identity as lower-bound only and fixed evaluator checks.
  - [x] GREEN: minimal Phase 0 metric contract public interface passes tracer test.
  - [x] Add stable JSON/CSV summary tests.
  - [x] Run targeted Issue #17 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_metric_contract.py -q`.
  - [x] Run Phase 0 validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests/test_baseline_evidence.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
  - [x] Write local ignored metric contract artifacts: `experiments/phase0/metric_contract.json` and `experiments/phase0/metric_contract.csv`.
- [x] Issue #18 / P0-4: Reproduce reference GAN baseline or mark it unreproducible.
  - [x] RED: reference GAN baseline evidence requires reproducible run fields or explicit unreproducible blocker.
  - [x] GREEN: minimal Phase 0 reference GAN evidence public interface passes tracer test.
  - [x] Add command/path/model artifact evidence tests.
  - [x] Run targeted Issue #18 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_reference_gan_evidence.py -q`.
  - [x] Attempt reference GAN build: `cd src/submission/submission-gan && ./do_build.sh` -> failed because `30_net_G.pth` is missing and `MODEL_WEIGHTS_DIR` is unset.
  - [x] Write local ignored unreproducible evidence artifact: `experiments/phase0/reference_gan_evidence.json`.
- [x] Issue #19 / P0-5: Smoke-test identity submission container and output validation.
  - [x] RED: identity smoke evidence validates command result and output contract.
  - [x] GREEN: minimal Phase 0 submission smoke public interface passes tracer test.
  - [x] Add Docker-assumption and failure evidence tests.
  - [x] Fix local identity `do_test_run.sh` writable-output cleanup for non-root container runs.
  - [x] Run targeted Issue #19 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_submission_smoke.py -q`.
  - [x] Run container validation: `cd src/submission/identity-baseline && ./do_test_run.sh`.
  - [x] Run export validation: `cd src/submission/identity-baseline && ./do_save.sh`.
  - [x] Run submission validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/submission/identity-baseline/test_algorithm.py -q`.
  - [x] Write local ignored smoke artifact: `experiments/phase0/identity_submission_smoke.json`.
- [x] Issue #20 / P0-6: Publish Phase 0 audit bundle and weight-staging decision.
  - [x] RED: audit bundle links Phase 0 evidence and documents weight-staging strategy.
  - [x] GREEN: minimal Phase 0 audit bundle public interface passes tracer test.
  - [x] Add missing-evidence rejection tests.
  - [x] Run targeted Issue #20 tests: `PYTHONPATH=src uv run pytest src/phase0/tests/test_audit_bundle.py -q`.
  - [x] Run Phase 0 validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
  - [x] Write local ignored audit bundle: `experiments/phase0/audit_bundle.json`.
- [x] Issue #21 / P1B-1: Add Phase 1B ablation config and registry on Phase 1A contracts.
  - [x] RED: Phase 1B config reuses Phase 1A contracts and rejects incompatible ablations.
  - [x] GREEN: minimal Phase 1B config/registry public interface passes tracer test.
  - [x] Add fixed evaluator drift and run metadata tests.
  - [x] Add smoke config: `configs/phase1b/unet_residual_smoke_v1.yaml`.
  - [x] Run targeted Issue #21 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_ablation_config.py -q`.
  - [x] Run Phase 1B config validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_experiment_config.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #22 / P1B-2: Implement 2D U-Net residual-regressor comparator.
  - [x] RED: U-Net comparator predicts residual and preserves synthetic post/native-size inference contract.
  - [x] GREEN: minimal 2D U-Net residual-regressor public interface passes tracer test.
  - [x] Add pre-contrast-only and no-mask inference tests.
  - [x] Strengthen after audit: replace constant/template predictor with a convolutional encoder/downsample/bottleneck/upsample decoder, skip concatenation, and trainable 1x1 residual head.
  - [x] Add input-dependent learned residual test that fails the old constant predictor.
  - [x] Add native-size inference after training test.
  - [x] Run targeted Issue #22 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_unet_comparator.py -q` -> 6 passed.
  - [x] Run Phase 1B comparator validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_residual_inference.py src/evaluation/tests src/preprocessing/test_preprocess.py -q` -> 107 passed, 3 skipped.
- [x] Issue #23 / P1B-3: Add seeded domain robustness augmentation ablation.
  - [x] RED: augmentation is reproducible and preserves paired pre/post/mask alignment.
  - [x] GREEN: minimal Phase 1B augmentation public interface passes tracer test.
  - [x] Add disabled no-op test.
  - [x] Run targeted Issue #23 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_domain_augmentation.py -q`.
  - [x] Run Phase 1B augmentation validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_residual_dataset.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #24 / P1B-4: Add isolated loss/model ablation groups.
  - [x] RED: ablation plan rejects combined experiments without single-factor evidence.
  - [x] GREEN: minimal isolated ablation planning public interface passes tracer test.
  - [x] Add selected loss-term toy-array tests and predicted-mask exclusion test.
  - [x] Run targeted Issue #24 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_isolated_ablation_groups.py -q`.
  - [x] Run Phase 1B ablation-group validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_losses.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #25 / P1B-5: Add ablation runner and audit metric summary interface.
  - [x] RED: ablation runner returns stable staged metric/audit summary.
  - [x] GREEN: minimal Phase 1B ablation runner public interface passes tracer test.
  - [x] Add fixed evaluator, regression reporting, and Phase 1A promotion compatibility tests.
  - [x] Run targeted Issue #25 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_ablation_runner.py -q`.
  - [x] Run Phase 1B runner validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_promotion_gate.py src/phase1a/tests/test_evaluation_runner.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #26 / P1B-6: Package only promoted Phase 1B checkpoint behind smoke tests.
  - [x] RED: Phase 1B packaging rejects candidates without promotion evidence.
  - [x] GREEN: minimal Phase 1B packaging gate public interface passes tracer test.
  - [x] Add smoke-test and protected-artifact locality tests.
  - [x] Run targeted Issue #26 tests: `PYTHONPATH=src uv run pytest src/phase1b/tests/test_packaging_gate.py -q`.
  - [x] Run Phase 1B packaging validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests/test_submission_package.py src/phase1a/tests/test_promotion_gate.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #27 / P2-1: Make Phase 2 go/no-go decision from Phase 1 evidence.
  - [x] RED: Phase 2 gate records go/no-go based on Phase 1 metric gap, time, and resources.
  - [x] GREEN: minimal Phase 2 gate public interface passes tracer test.
  - [x] Add no-go clean stop and failed/deferred audit tests.
  - [x] Run targeted Issue #27 tests: `PYTHONPATH=src uv run pytest src/phase2/tests/test_go_no_go_gate.py -q`.
  - [x] Write local ignored no-go gate artifact: `experiments/phase2/go_no_go_decision.json`.
  - [x] Run Phase 2 gate validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase2/tests src/phase1b/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issues #28-#32 / P2-2..P2-6: Deferred by Phase 2 no-go gate.
  - [x] Close downstream latent-diffusion implementation issues as not planned because `experiments/phase2/go_no_go_decision.json` records `decision=no-go`.
  - [x] Do not start speculative autoencoder, denoising, sampling, or Phase 2 packaging work without a future go decision.
- [x] Issue #33 / P3-1: Validate final candidate audit bundles.
  - [x] RED: final candidate audit validation rejects missing required artifacts.
  - [x] GREEN: minimal Phase 3 candidate audit validation public interface passes tracer test.
  - [x] Add protected-data exclusion tests.
  - [x] Run targeted Issue #33 tests: `PYTHONPATH=src uv run pytest src/phase3/tests/test_candidate_audit.py -q`.
  - [x] Run Phase 3 audit validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase3/tests src/phase1b/tests/test_packaging_gate.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #34 / P3-2: Select final candidate from frozen local ranking table.
  - [x] RED: final selection handles rank mean, non-inferiority, ties, and no-candidate state.
  - [x] GREEN: minimal Phase 3 final selection public interface passes tracer test.
  - [x] Add validation-feedback separation tests.
  - [x] Run targeted Issue #34 tests: `PYTHONPATH=src uv run pytest src/phase3/tests/test_final_selection.py -q`.
  - [x] Write local ignored no-candidate final-selection artifact: `experiments/phase3/final_selection_decision.json`.
  - [x] Run Phase 3 selection validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase3/tests src/phase1b/tests/test_ablation_runner.py src/phase1a/tests/test_promotion_gate.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #35 / P3-3: Optional deterministic ensemble or blending candidate.
  - [x] RED: ensemble/blending is rejected unless explicitly approved.
  - [x] GREEN: minimal Phase 3 optional ensemble gate public interface passes tracer test.
  - [x] Add deterministic output contract tests for approved blending.
  - [x] Run targeted Issue #35 tests: `PYTHONPATH=src uv run pytest src/phase3/tests/test_optional_ensemble.py -q`.
  - [x] Run Phase 3 optional ensemble validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase3/tests src/phase1a/tests/test_residual_inference.py src/evaluation/tests src/preprocessing/test_preprocess.py -q`.
- [x] Issue #36 / P3-4: Harden final packaging and model-weight strategy.
  - [x] RED: final packaging requires one weight-loading strategy and Grand Challenge runtime checks.
  - [x] GREEN: minimal Phase 3 final packaging public interface passes tracer test.
  - [x] Add output slug/MHA/model-weight path tests.
  - [x] Run targeted Issue #36 tests: `PYTHONPATH=src uv run pytest src/phase3/tests/test_final_packaging.py -q`.
  - [x] Run Phase 3 packaging validation slice: `PYTHONPATH=src:src/evaluation uv run pytest src/phase3/tests src/phase1a/tests/test_submission_package.py src/submission/identity-baseline/test_algorithm.py -q`.
- [x] Issue #37 / P3-5: Produce final decision record and submission evidence bundle, or terminal documented blocked state if no promoted final candidate exists.
  - [x] RED: final evidence bundle records selected candidate decision, audit fields, provenance, and optional official submission records.
  - [x] GREEN: minimal Phase 3 final evidence bundle public interface passes tracer test for a real selected candidate.
  - [x] Add top-3 provenance readiness tests.
  - [x] Strengthen after audit: reject null `selected_candidate` and null required audit fields instead of accepting a no-candidate bundle.
  - [x] Run targeted Issue #37 tests: `PYTHONPATH=src uv run pytest src/phase3/tests/test_final_evidence_bundle.py -q`.
  - [x] Remove invalid null final bundle and write blocked note: `experiments/phase3/final_evidence_bundle_blocked.json`.
  - [x] Terminal blocked state accepted by tweaked goal: no promoted final candidate exists, so a semantically valid final bundle with selected candidate, config, split, metrics, inference settings, model hash, and container version cannot be produced yet.
- [x] Implement approved issues one at a time with `/skill:tdd` red-green-refactor cycles.
- [x] Run relevant validation for each completed/blocked issue and record results.
- [x] Write final handoff: `docs/draft-issues/phase-0-1b-2-3-final-handoff.md`.
- [x] Complete final broad validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q` -> 197 passed, 3 skipped.
- [x] Complete final completion audit in `docs/draft-issues/phase-0-1b-2-3-final-handoff.md`.

## Active task: Current experiment readiness audit

- [x] Compare current repository artifacts against `STRATEGY.md` phase roadmap.
- [x] Inspect Phase 0/1A/1B/2/3 implementation surfaces and experiment evidence.
- [x] Verify current broad validation still passes.
- [x] Summarize current stage, blockers, and next experiment step.

## Active task: Phase 1B first real-debug experiment driver

- [x] Inspect existing Phase 1B config, runner, model comparator, and Phase 1A CLI pattern.
- [x] Add a minimal tested Phase 1B CLI/driver for `configs/phase1b/unet_residual_smoke_v1.yaml`.
- [x] Run the fixed real debug split command and confirm output artifacts.
- [x] Record the canonical command and validation result.
  - Command: `PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_smoke_v1.yaml`.
  - Output: `experiments/phase1b/unet_residual_smoke_v1/run_summary.json`, `metrics/ablation_summary.json`, `metrics/holdout_fidelity_by_case.csv`, `checkpoint.npz`, and hold-out `.mha` predictions.
  - Validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase1b/tests src/phase1a/tests src/evaluation/tests src/preprocessing/test_preprocess.py -q` -> 165 passed, 3 skipped.
  - Broad validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q` -> 200 passed, 3 skipped.

## Active task: Phase 1B scanner-protocol augmentation comparison

- [x] Inspect current Phase 1B augmentation API and run driver constraints.
- [x] Add scanner-protocol-intensity config and driver support.
- [x] Run disabled-vs-augmentation comparison with the same command pattern.
- [x] Record metrics and validation result.
  - Disabled command: `PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_smoke_v1.yaml`.
  - Augmentation command: `PYTHONPATH=src uv run python -m phase1b.run configs/phase1b/unet_residual_scanner_protocol_intensity_v1.yaml`.
  - Comparison artifact: `experiments/phase1b/augmentation_comparison_v1.json`.
  - Debug result: scanner augmentation image-fidelity MSE 2.9627 vs disabled 2.9824; tumor ROI MSE 37.6535 vs disabled 37.0752.
  - Validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q` -> 201 passed, 3 skipped.

## Active task: Phase 1B scanner-protocol seed/range sensitivity

- [x] Add 2-3 separate scanner-protocol-intensity YAML variants.
- [x] Run each variant with the fixed Phase 1B driver command pattern.
- [x] Compare image MSE and tumor ROI MSE against disabled and original scanner augmentation.
- [x] Record whether ROI MSE degradation appears seed/range-sensitive on the debug split.
  - Sensitivity artifact: `experiments/phase1b/scanner_protocol_sensitivity_v1.json`.
  - Result: ROI MSE degradation is seed/range-sensitive on n=2 debug split; seed29 mild improves ROI MSE vs disabled, while seed17 mild/narrow/wide worsen ROI MSE, with the wide range worst.
  - Validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q` -> 201 passed, 3 skipped.

## Active task: Phase 1B official evaluator shortlist comparison

- [x] Run the full local evaluator for disabled U-Net and scanner seed29 mild candidates on the same debug split.
- [x] Fix old XGBoost classifier pickle compatibility so AUROC metrics are reported instead of silently skipped.
- [x] Record the official shortlist comparison artifact.
  - Disabled metrics: `experiments/phase1b/unet_residual_smoke_v1/official_metrics/metrics.json`.
  - Scanner seed29 mild metrics: `experiments/phase1b/unet_residual_scanner_protocol_intensity_seed29_v1/official_metrics/metrics.json`.
  - Comparison artifact: `experiments/phase1b/official_shortlist_comparison_v1.json`.
  - Result: seed29 mild slightly improves FRD, LPIPS, and SSIM-tumor; slightly worsens MSE; AUROC and segmentation aggregates tie on the n=2 debug split.
  - Promotion decision: no submission candidate promotion from this evidence alone because the split is only n=2 debug smoke evidence and Dice remains 0.0 for both candidates.
  - Focused validation: `PYTHONPATH=src:src/evaluation uv run pytest src/evaluation/tests src/phase1b/tests -q` -> 79 passed, 3 skipped.
  - Broad validation: `PYTHONPATH=src:src/evaluation uv run pytest src/phase0/tests src/phase1a/tests src/phase1b/tests src/phase2/tests src/phase3/tests src/evaluation/tests src/preprocessing/test_preprocess.py src/submission/identity-baseline/test_algorithm.py -q` -> 202 passed, 3 skipped.

## Active task: Post-goal summary rule and commit

- [x] Summarize the completed goal result in Korean for the user.
- [x] Add an `AGENTS.md` rule requiring Korean goal completion summaries.
- [x] Commit the major tracked changes from the completed goal.
