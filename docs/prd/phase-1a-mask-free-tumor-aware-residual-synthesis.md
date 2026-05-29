# PRD: Phase 1A — Mask-Free Tumor-Aware Residual Synthesis

## Problem Statement

MAMA-SYNTH requires generating a synthetic peak-enhancement post-contrast breast DCE-MRI slice from a single pre-contrast slice. The challenge rewards balanced performance across image fidelity, tumor ROI realism, downstream classification utility, and downstream segmentation utility. A model that optimizes only pixel similarity can blur tumor enhancement, while mask-conditioned approaches from recent literature can be difficult to use under the Grand Challenge inference contract because the test-time input does not include a tumor mask.

We need a first development phase that is practically implementable on a single RTX A4500 20GB GPU and designed to test a task-specific contribution hypothesis. Any contribution claim requires hold-out and/or Validation phase evidence. The phase must establish a reproducible training/evaluation pipeline, preserve mask-free submission inference, and produce a submission candidate only when local hold-out evidence supports it.

## Solution

Build Phase 1A as **mask-free tumor-aware residual synthesis**: a pix2pixHD-style ROI/SUB model that predicts or reconstructs the enhancement residual from the pre-contrast slice, uses ground-truth tumor masks only in training losses, and outputs a synthetic post image for evaluation and submission. A 2D U-Net residual regressor remains a later comparison path after the pix2pixHD-first pipeline is reproducible. The model must preserve native spatial size by padding internally when required and cropping back before output.

The phase will standardize three supporting contracts before model comparison:

1. A split manifest that records train/hold-out membership and nullable center metadata without changing filenames, image metadata, or submission inputs.
2. A single experiment config that captures the run, data, model, loss, training, evaluation, and submission contracts.
3. A staged submission candidate gate based on hold-out evaluation, fixed downstream evaluation models, and submission smoke tests.

This PRD stops at the planning/specification level. It does not start implementation.

## User Stories

1. As a challenge participant, I want a mask-free synthesis model, so that the Grand Challenge container can run with only the pre-contrast slice at inference time.
2. As a challenge participant, I want tumor masks used only during training loss computation, so that tumor-aware learning does not violate the hidden test input contract.
3. As a challenge participant, I want the model to predict a residual rather than direct post-contrast pixels, so that static anatomy is preserved and enhancement learning is focused.
4. As a challenge participant, I want the final output to always be a synthetic post image, so that local evaluation and official submission consume the correct artifact.
5. As a researcher, I want the Phase 1A hypothesis framed as a task-specific adaptation rather than a novel architecture, so that any later contribution claim is accurate and evidence-backed.
6. As a researcher, I want the Phase 1A narrative to address test-time mask unavailability, so that the method responds to a real limitation of mask-conditioned approaches.
7. As a researcher, I want the recorded reference GAN result on the selected hold-out split treated as the primary performance baseline once its weights and inference path are reproducible, so that improvements are measured against a meaningful comparison point.
8. As a researcher, I want identity output treated only as a lower-bound benchmark, so that infrastructure checks are not confused with performance baselines.
9. As a model developer, I want a single split manifest, so that training and hold-out evaluation are reproducible.
10. As a model developer, I want nullable center metadata in the split manifest, so that center-held-out evaluation can be supported when center labels are available.
11. As a model developer, I want split metadata kept out of submission filenames and image metadata, so that local training choices cannot break the submission contract.
12. As a model developer, I want a debug hold-out split separate from the center-held-out split, so that quick checks do not contaminate model selection evidence.
13. As a model developer, I want a single experiment config per run, so that training, evaluation, and submission behavior can be reproduced.
14. As a model developer, I want the config to explicitly declare pre-contrast-only inference, so that accidental mask-conditioned inference is caught early.
15. As a model developer, I want native-size inference with internal padding and crop-back, so that output shapes match the input and evaluation masks.
16. As a model developer, I want tumor-mask-only ROI weighting as the Phase 1A default, so that the first experiment remains simple and interpretable.
17. As a model developer, I want ROI context parameters present but disabled by default, so that later ablations can test dilated tumor context without changing the config contract.
18. As an evaluator, I want fixed downstream evaluation models used consistently, so that synthesis model comparisons are fair.
19. As an evaluator, I want classifier ensemble and segmentation fold settings fixed by config, so that ③④ metrics are not changed between runs.
20. As an evaluator, I want staged model selection, so that cheap metrics filter early experiments and expensive downstream evaluation is reserved for shortlists.
21. As an evaluator, I want submission candidate promotion to define major group regression as more than 5% relative worsening versus the primary performance baseline, so that a model does not overfit one metric group.
22. As an evaluator, I want at least two metric groups to improve or remain within the 5% non-inferiority margin, so that Phase 1A candidates are balanced.
23. As an evaluator, I want the local proxy rank mean to improve over the primary performance baseline in a frozen local ranking table, so that the candidate aligns with the challenge ranking philosophy without pretending to reproduce unpublished official ranking code.
24. As an operator, I want submission smoke tests required before Validation phase submission, so that Docker/I/O failures do not waste limited official submissions.
25. As an operator, I want every promoted checkpoint bundled with metrics, config, inference settings, and model hash, so that results remain auditable.
26. As a future issue author, I want architecture details such as pix2pixHD discriminator settings, feature-matching weights, and optimizer choices left to implementation issues, so that the PRD stays focused on stable contracts.
27. As a future issue author, I want predicted-mask conditioning, diffusion, and 2D U-Net comparison work deferred until the pix2pixHD-first pipeline is reproducible, so that the first implementation remains small and testable.

## Implementation Decisions

- Phase 1A will implement **mask-free tumor-aware residual synthesis**.
- The first backbone will be a pix2pixHD-style ROI/SUB model.
- The model input contract is pre-contrast only.
- The training target is the residual between peak-enhancement post-contrast and pre-contrast.
- The evaluation and submission output is always synthetic post, reconstructed from pre-contrast plus predicted residual.
- Ground-truth tumor masks are allowed only for training losses and local evaluation; they are not model inputs at inference time.
- Native image size must be preserved. The model may pad internally to a model-compatible multiple, but must crop back to the original size before producing synthetic post.
- The Phase 1A loss starts with residual L1 and tumor ROI weighted residual L1.
- Tumor ROI weighting defaults to tumor mask only.
- ROI context parameters are included in the config but disabled by default for Phase 1A.
- The split manifest is a single JSON artifact.
- The split manifest includes case membership, source grouping, nullable center grouping, and paths to pre-contrast, ground-truth post, and mask images.
- Center metadata is local training/evaluation metadata only. It must not alter case filenames, image metadata, Docker inputs, or inference behavior.
- Final model selection uses a center-held-out split when center metadata is available.
- If center metadata is unavailable, model selection falls back to a patient-grouped, source-stratified hold-out using `source_id` as the grouping signal.
- A small random debug hold-out split may exist for fast pipeline checks but cannot justify submission candidate promotion.
- Each run uses a single YAML experiment config.
- The experiment config includes run, data, model, loss, train, evaluation, and submission sections.
- The experiment config explicitly records residual target learning, pre-contrast-only inference, synthetic post output, fixed evaluator configuration, and submission smoke-test expectations.
- Fixed downstream evaluation models are used for hold-out classification and segmentation utility.
- The default fixed evaluator setup uses classifier ensemble enabled and segmentation fold 0.
- Fold sensitivity or alternative downstream evaluators are separate analyses, not part of the primary Phase 1A selection score.
- Model selection is staged: early ablations use image fidelity and tumor ROI realism metrics; shortlist candidates use all four metric groups.
- A Phase 1A submission candidate must satisfy: no metric group worsens by more than 5% relative to the primary performance baseline, at least two metric groups improve or remain within that 5% non-inferiority margin, improved local proxy rank mean over the primary performance baseline, and passing submission smoke tests.
- The local proxy rank mean is computed within a frozen local ranking table containing the identity lower-bound benchmark, the recorded reference GAN baseline, and all Phase 1A candidates evaluated on the same split.
- The primary performance baseline is the recorded reference GAN result on the selected hold-out split once its weights and inference path are reproducible.
- If the reference GAN cannot yet be reproduced, identity output is used only to validate the evaluation harness; submission-candidate promotion is deferred until the reference GAN baseline or an explicitly approved alternative baseline is recorded.
- The identity output is a lower-bound benchmark and submission smoke-test artifact, not the primary performance baseline.
- Phase 1A should test a task-specific, evaluation-aligned contribution hypothesis; any contribution claim requires hold-out and/or Validation phase evidence and must not claim a novel architecture.

## Testing Decisions

- Tests should verify external behavior and contracts, not private implementation details.
- Split manifest tests should verify schema validity, path resolvability, split membership consistency, nullable center metadata handling, and that local metadata does not require submission-time inputs.
- Experiment config tests should verify required sections, fixed evaluator settings, synthetic post output contract, residual target declaration, and pre-contrast-only inference declaration.
- Dataset/loading tests should verify that cases are loaded from the manifest with matching pre-contrast, ground-truth post, and mask stems.
- Model contract tests should verify that inference accepts pre-contrast only and does not require masks.
- Shape tests should verify native-size preservation across padding and crop-back behavior.
- Loss tests should verify residual L1 and tumor ROI weighted residual L1 on deterministic toy arrays.
- Output tests should verify that predicted residuals are converted to synthetic post before evaluation artifacts are written.
- Evaluation runner tests should verify staged metric execution and fixed evaluator configuration without changing evaluator weights between compared models.
- Unit tests should mock fixed evaluator outputs; full `src/evaluation/models` execution is an operational check.
- FRD contract tests should verify v1 configuration, tumor-mask path usage for both ground truth and prediction, and the minimum two-case aggregate requirement.
- Promotion-gate tests should verify candidate acceptance/rejection from toy metric-summary JSON.
- Submission smoke tests should verify output creation, readability, 2D shape, float32 dtype, finite values with no NaN/Inf, `max(abs(value)) <= 50` as a soft z-score sanity bound, and metadata preservation.
- Integration tests should prefer small deterministic fake cases over protected MRI data.
- Heavy training, full downstream evaluation, Docker GPU execution, and Validation phase submission are operational checks, not unit tests.

## Out of Scope

- Predicted-mask conditioning.
- Test-time ground-truth mask conditioning.
- Diffusion or latent diffusion models.
- TeNCA or temporal modeling.
- LPIPS/perceptual training loss beyond the pix2pixHD-first minimum.
- Auxiliary segmentation branch training.
- Curriculum learning.
- Domain robustness augmentation beyond what is needed for a minimal Phase 1A run.
- 2D U-Net residual-regressor comparison before the pix2pixHD-first pipeline is reproducible.
- Optimizer and scheduler ablation beyond a reasonable first default.
- Validation phase submission execution.
- Issue implementation or TDD execution.

## Further Notes

- Canonical terms are defined in the project glossary. Strategy, roadmap, and gates are maintained in the strategy document.
- The PRD should be converted into independently grabbable tracer-bullet issues before implementation starts.
- Implementation must be split at least into split/config contracts, dataset loader, residual model contract, loss, evaluation adapter, promotion gate, and submission smoke test issues.
- Implementation should proceed issue by issue using TDD, with user approval before publishing or executing the issue plan.
- No development should continue from this PRD step unless explicitly requested.
