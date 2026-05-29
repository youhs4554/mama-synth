# Draft issues: Phase 1A — Mask-Free Tumor-Aware Residual Synthesis

Parent PRD: `docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

These are approved draft issues. They are not yet published to an issue tracker because the GitHub CLI is not available in this environment.

---

## DRAFT-001: Create split manifest contract and validator

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Create the split manifest contract for Phase 1A hold-out evaluation. The manifest should record train/hold-out membership, debug versus model-selection split intent, case grouping metadata, nullable center metadata, and all local paths needed for training and evaluation while keeping split metadata out of submission filenames, image metadata, and inference behavior.

## Acceptance criteria

- [ ] A split manifest can be validated from deterministic fake cases with train and hold-out membership.
- [ ] Manifest validation accepts nullable center metadata and rejects inconsistent or missing required case fields.
- [ ] Manifest validation verifies that referenced pre-contrast, ground-truth post, and tumor mask artifacts resolve locally.
- [ ] Tests prove that split metadata is local-only and does not create submission-time input requirements.
- [ ] Tests distinguish debug hold-out splits from model-selection hold-out splits.

## Blocked by

None - can start immediately

---

## DRAFT-002: Create single Phase 1A experiment config contract

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Create the single Phase 1A experiment config contract. The config should make the run reproducible by declaring data, model, residual target learning, loss defaults, training settings, fixed evaluation model settings, synthetic post output, and submission smoke-test expectations in one place.

## Acceptance criteria

- [ ] A minimal valid config declares run, data, model, loss, train, evaluation, and submission sections.
- [ ] Config validation requires pre-contrast-only inference and synthetic post output.
- [ ] Config validation requires residual target learning for Phase 1A.
- [ ] Config validation fixes the downstream evaluator setup unless a separate sensitivity-analysis mode is explicitly declared.
- [ ] Config validation includes tumor-mask-only ROI weighting by default and ROI context parameters disabled by default.

## Blocked by

- DRAFT-001

---

## DRAFT-003: Load manifest cases into a residual-synthesis dataset

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Create the dataset path from split manifest cases to model-ready samples for residual synthesis. Training samples should expose pre-contrast images, ground-truth post images, tumor masks for loss computation, and residual targets; inference samples should prove that masks are not required as model inputs.

## Acceptance criteria

- [ ] Dataset loading succeeds for deterministic fake cases described by a valid split manifest.
- [ ] Loaded training samples include pre-contrast, ground-truth post, tumor mask, and derived residual target.
- [ ] Derived residual targets equal `post - pre` on deterministic toy data.
- [ ] Inference sample construction accepts pre-contrast only and does not require tumor masks.
- [ ] Tests verify matching case identity across pre-contrast, post, and mask artifacts.

## Blocked by

- DRAFT-001
- DRAFT-002

---

## DRAFT-004: Prove mask-free native-size synthetic post inference

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Add the minimal residual model contract and inference path for Phase 1A. The path should accept only a pre-contrast slice, predict an enhancement residual, reconstruct a synthetic post image, and preserve native spatial size by padding internally when needed and cropping back before output.

## Acceptance criteria

- [ ] Inference public API accepts pre-contrast input without mask input.
- [ ] Tests fail if a tumor mask is required for inference.
- [ ] Predicted residuals are converted to synthetic post images before evaluation or submission artifacts are written.
- [ ] Native-size output is preserved for shapes that require internal padding.
- [ ] Output shape matches the input shape and evaluation mask shape on deterministic fake cases.

## Blocked by

- DRAFT-002
- DRAFT-003

---

## DRAFT-005: Add Phase 1A residual and tumor ROI weighted losses

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Implement the Phase 1A loss behavior: residual L1 plus tumor ROI weighted residual L1. Tumor ROI weighting should use the tumor mask only during training loss computation, with ROI context parameters available in config but disabled by default.

## Acceptance criteria

- [ ] Residual L1 returns the expected value on deterministic toy arrays.
- [ ] Tumor ROI weighted residual L1 returns the expected value on deterministic toy masks.
- [ ] Tumor masks are consumed only by the training loss path, not by inference.
- [ ] ROI context parameters are present but disabled by default.
- [ ] Tests cover empty-mask or no-tumor toy behavior without introducing inference mask conditioning.

## Blocked by

- DRAFT-003
- DRAFT-004

---

## DRAFT-006: Run a minimal train/evaluate loop for mask-free tumor-aware residual synthesis

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Wire the Phase 1A config, split manifest, dataset, residual model, losses, checkpointing, and synthetic post prediction output into a minimal reproducible train/evaluate loop. This slice should establish a living end-to-end path rather than optimize architecture details.

## Acceptance criteria

- [ ] A smoke-scale run trains on deterministic fake or tiny local data without requiring protected MRI data in tests.
- [ ] The run records config, split manifest reference, seed, checkpoint reference, and inference settings.
- [ ] The evaluation side writes synthetic post predictions, not residual images.
- [ ] Tests or smoke checks prove inference remains pre-contrast-only after training.
- [ ] Architecture-specific ablations remain out of scope for this issue.

## Blocked by

- DRAFT-004
- DRAFT-005

---

## DRAFT-007: Record identity lower-bound and reference GAN baseline evidence

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Record the comparison evidence needed before promoting any Phase 1A submission candidate. Identity output should be recorded only as a lower-bound benchmark and submission smoke-test artifact. The reference GAN should become the primary performance baseline only after its weights, inference path, selected hold-out split, and metrics are reproducible; otherwise promotion remains deferred until a human-approved alternative baseline exists.

## Acceptance criteria

- [ ] Identity output is recorded as a lower-bound benchmark, not as the primary performance baseline.
- [ ] Reference GAN evidence includes the selected hold-out split, inference path, model artifact identity, and metric summary when reproducible.
- [ ] The local ranking table can include identity, reference GAN, and later Phase 1A candidates evaluated on the same split.
- [ ] If the reference GAN cannot be reproduced, submission-candidate promotion is explicitly blocked or deferred.
- [ ] Any alternative primary performance baseline requires human approval before use.

## Blocked by

- DRAFT-001
- DRAFT-002

---

## DRAFT-008: Add staged hold-out evaluation runner with fixed downstream evaluators

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Create the staged hold-out evaluation runner for Phase 1A candidates. Early ablations should run cheaper image fidelity and tumor ROI realism metrics, while shortlisted candidates run all four metric groups using the fixed downstream evaluator configuration.

## Acceptance criteria

- [ ] The runner can execute cheap metric groups for early candidates and full metric groups for shortlist candidates.
- [ ] Fixed classifier ensemble and segmentation fold settings come from the approved config contract.
- [ ] Tests mock fixed downstream evaluator outputs rather than requiring full evaluator model execution.
- [ ] The runner rejects comparisons that change fixed evaluator settings between candidates.
- [ ] Metric summaries can be written in a stable format for promotion-gate input.

## Blocked by

- DRAFT-002
- DRAFT-006
- DRAFT-007

---

## DRAFT-009: Implement submission candidate promotion gate and audit bundle

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Implement the Phase 1A submission candidate promotion gate. The gate should compare candidate metric summaries against the primary performance baseline, enforce the 5% non-inferiority rules, require local proxy rank mean improvement, and require an auditable bundle of metrics, config, inference settings, and model hash.

## Acceptance criteria

- [ ] Toy metric summaries can be accepted or rejected deterministically by the promotion gate.
- [ ] Any metric group worsening by more than 5% relative to the primary performance baseline rejects the candidate.
- [ ] At least two metric groups must improve or remain within the 5% non-inferiority margin.
- [ ] Local proxy rank mean must improve over the primary performance baseline in the frozen local ranking table.
- [ ] The output audit bundle includes metrics, config, inference settings, and model hash.

## Blocked by

- DRAFT-007
- DRAFT-008

---

## DRAFT-010: Package Phase 1A checkpoint behind submission smoke tests

## Parent

`docs/prd/phase-1a-mask-free-tumor-aware-residual-synthesis.md`

## What to build

Package a promoted Phase 1A checkpoint behind submission-style inference and smoke tests. The package should consume only the pre-contrast slice at inference time and write a native-size synthetic post image that satisfies the Grand Challenge-style output contract.

## Acceptance criteria

- [ ] Submission-style inference consumes pre-contrast input only.
- [ ] Output is a readable native-size synthetic post image with float32 dtype.
- [ ] Output values are finite with no NaN or Inf.
- [ ] A soft z-score sanity check verifies `max(abs(value)) <= 50` on smoke-test output.
- [ ] Output metadata needed by the challenge interface is preserved.
- [ ] Smoke tests must pass before a checkpoint is considered submission-ready.

## Blocked by

- DRAFT-006
- DRAFT-009
