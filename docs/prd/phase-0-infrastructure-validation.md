# PRD: Phase 0 — Infrastructure Validation

## Reference Documents

- `CONTEXT.md` defines canonical project terminology used by this PRD.
- `STRATEGY.md` defines the MAMA-SYNTH roadmap, Grand Challenge submission contract, evaluation groups, and operational gates.
- The existing Phase 1A PRD defines the downstream contracts that Phase 0 must make possible: split manifests, hold-out evaluation, baseline evidence, and submission smoke tests.

## Problem Statement

MAMA-SYNTH success depends on a working end-to-end path from local data preprocessing through local hold-out evaluation and Grand Challenge-compatible container execution. Before investing GPU time in model improvements, the project needs proof that the repository, dataset mount, preprocessing statistics, submission templates, Docker runtime assumptions, and evaluation harness are all aligned with the official input/output contract.

Without this phase, later model work can produce misleading metrics, waste limited Validation phase submissions, or fail for operational reasons such as wrong z-score scale, missing metadata, wrong image slug, unavailable weights, broken Docker permissions, or fixed evaluation model misconfiguration.

## Solution

Establish Phase 0 as the infrastructure gate for every later phase. It verifies that the repository can run tests, locate the local MAMA-MIA dataset through the `datasets` symlink, preprocess raw 3D volumes into native-size 2D `.mha` artifacts, run smoke-test submission containers, stage or load model weights, execute local hold-out evaluation, and record identity lower-bound and reference GAN evidence separately.

Phase 0 does not optimize model quality. It proves the local and Grand Challenge execution surfaces are safe enough for Phase 1A, Phase 1B, Phase 2, and Phase 3 work.

## User Stories

1. As a challenge participant, I want the repository test suite to pass locally, so that later model changes start from a known-good codebase.
2. As a challenge participant, I want the local dataset mount verified, so that preprocessing commands do not silently point at the wrong data root.
3. As a challenge participant, I want raw MAMA-MIA layout discovery documented, so that future agents know whether preprocessed `.mha` artifacts already exist or must be generated.
4. As a preprocessing developer, I want the official training pre-contrast z-score statistics used consistently, so that generated inputs and ground truth match evaluator assumptions.
5. As a preprocessing developer, I want generated `.mha` images to preserve native size and metadata, so that evaluation and submission smoke tests operate on challenge-like artifacts.
6. As a preprocessing developer, I want tumor masks generated alongside input and ground-truth images, so that tumor ROI metrics and loss-only tumor-aware synthesis can run locally.
7. As a model developer, I want a small debug hold-out split available, so that train/evaluate loops can be checked without waiting for full experiments.
8. As a model developer, I want center/source metadata inspected before model-selection splits are chosen, so that hold-out evaluation approximates external-institution generalization as much as local data allows.
9. As an evaluator, I want identity output recorded as a lower-bound benchmark, so that evaluator wiring can be tested without pretending it is a performance baseline.
10. As an evaluator, I want the reference GAN submission run or explicitly marked unreproducible, so that the primary performance baseline is not ambiguous.
11. As an evaluator, I want local metrics written in a stable format, so that Phase 1A and later candidates can be compared on the same split.
12. As an evaluator, I want fixed evaluation classifier and segmenter paths checked before expensive evaluation, so that missing model weights are discovered early.
13. As an operator, I want the smoke-test submission container to build, run, test, and save, so that the Grand Challenge input/output path is proven before model submissions.
14. As an operator, I want submission outputs checked for float32 dtype, finite values, synthetic post shape, and metadata preservation, so that trivial container mistakes do not consume Validation phase submissions.
15. As an operator, I want Docker runtime assumptions verified locally, so that non-root execution, read-only input, writable output, and no-network behavior are not surprises.
16. As an operator, I want GPU availability and memory assumptions recorded, so that later experiments can distinguish model failures from environment failures.
17. As an operator, I want model weight staging strategy documented, so that a container either packages weights or loads them from the Grand Challenge model upload path, not both.
18. As a future issue author, I want Phase 0 outputs to be audit artifacts, so that later implementation issues can depend on verified infrastructure instead of rediscovering it.
19. As a future issue author, I want Validation phase submissions protected by local smoke tests, so that limited official submissions are used only after reproducibility gates pass.
20. As a researcher, I want Phase 0 to avoid performance claims, so that infrastructure validation is not confused with a synthesis contribution.

## Implementation Decisions

- Phase 0 is an operational readiness phase, not a model-development phase.
- The smoke-test submission is used to verify Grand Challenge I/O and container execution only.
- Identity output is a lower-bound benchmark and must not be called the primary performance baseline.
- The reference GAN submission becomes the primary performance baseline only after its weights, preprocessing bridge, inference path, split, and metrics are recorded reproducibly.
- The preprocessing contract uses native-size 2D slices, z-score float32 image space, official pre-contrast statistics, and metadata preservation.
- Preprocessed artifacts are generated under ignored local data or experiment locations; protected MRI data, masks, predictions, and checkpoints are not committed.
- Dataset discovery must be symlink-aware because the local `datasets` path may point outside the repository.
- Local split metadata is training/evaluation metadata only and must not alter image filenames, image metadata, or submission inputs.
- Fixed downstream evaluation models are treated as local evaluator dependencies, not submission-container dependencies.
- The submission container must produce synthetic post `.mha` output with the expected slug, dtype, shape, finite values, and copied image information.
- Weight handling chooses one primary loading strategy per submission template: packaged resources or Grand Challenge model upload.
- Grand Challenge Try-out and Debug phase executions are submission smoke tests, not Validation phase performance evidence.
- Phase 0 artifacts should include command records, environment notes, metric summaries, and any known blocker around reference GAN reproducibility.

## Testing Decisions

- Tests should verify observable contracts: filesystem discovery, image I/O, metadata preservation, evaluator configuration, and container output behavior.
- Preprocessing tests should use deterministic small fixtures and verify z-score conversion, peak/slice selection behavior where practical, dtype, and mask alignment.
- Submission smoke tests should verify the same external behavior expected by the Grand Challenge runner: one input image produces one output image in the required location.
- Evaluation harness tests should distinguish identity lower-bound evidence from reference GAN baseline evidence.
- Fixed evaluator tests should check configuration stability without running heavyweight classifier or segmenter inference in unit tests.
- Operational checks should cover Docker build/run/save and Grand Challenge Try-out/Debug logs; these are not unit tests.
- Protected MRI data must not be copied into test fixtures; synthetic fake arrays or locally ignored artifacts are used instead.

## Out of Scope

- Training a new synthesis model.
- Tuning loss weights or architecture choices.
- Submitting to the official Validation phase for performance.
- Implementing Phase 1A, Phase 1B, Phase 2, or Phase 3 model improvements.
- Claiming any model contribution.
- Uploading protected MRI data or experiment outputs to external services.

## Further Notes

- Phase 0 is complete only when later phases can rely on a reproducible local data path, smoke-test submission path, and hold-out evaluation harness.
- Any unresolved infrastructure blocker should stop downstream model work until the smallest safe unblock action is identified.
