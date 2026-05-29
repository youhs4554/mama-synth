# MAMA-SYNTH Context

This glossary defines the shared project language for MAMA-SYNTH development, evaluation, and submission planning. It keeps challenge-specific terms precise so model work, validation, and documentation use the same vocabulary. For strategy, roadmap, and implementation gates, see `STRATEGY.md`.

## Language

**Baseline**:
A reproducible model, split, and metric result used as the performance comparison point for experiments.
_Avoid_: using baseline to mean smoke-test container, reference submission, or first submit-ready model.

**Smoke-test submission**:
A submission artifact whose purpose is to verify the Grand Challenge input/output and container path, not to establish model performance.
_Avoid_: baseline.

**Reference GAN submission**:
The provided pix2pixHD/medigan-style submission used as an implementation reference and possible starting point.
_Avoid_: baseline, unless it has been run on the chosen split and recorded as the project baseline.

**Submission candidate**:
A model artifact and container configuration that is eligible for a Validation phase or Test phase submission after local verification. For Phase 1A, promotion requires no major group regression, at least two metric groups improving or staying useful, improved 4-group rank mean versus the primary performance baseline, and a passing submission smoke test.
_Avoid_: baseline.

**Validation phase**:
The official Grand Challenge phase used for limited leaderboard submissions before the Test phase.
_Avoid_: local validation, validation run, container validation.

**Hold-out evaluation**:
A local performance evaluation on a project-owned split, used to compare models and choose checkpoints before official submissions. Model selection should use a center-held-out split, while small random patient splits may be used only for fast debugging.
_Avoid_: validation, Validation phase.

**Center-held-out split**:
A hold-out evaluation split where one or more acquisition centers are excluded from training to better approximate external-institution generalization.
_Avoid_: random validation split, unless the goal is explicitly fast debugging.

**Debug hold-out split**:
A small random patient split used for quick pipeline checks and regression tests, not for final checkpoint selection.
_Avoid_: validation split, baseline split.

**Split manifest**:
A single JSON file under `splits/` that records train/hold-out membership, file paths, split strategy, seed, and nullable grouping metadata such as `center_id`. It is local training/evaluation metadata only and must not change submission filenames, MHA contents, or inference inputs.
_Avoid_: encoding split metadata into filenames or requiring it at submission time.

**Tumor-aware synthesis**:
Synthesis training that uses tumor location information to shape losses or auxiliary objectives while preserving a mask-free inference path unless explicitly stated otherwise.
_Avoid_: using tumor-aware to imply ground-truth mask input at submission time.

**Mask-free tumor-aware residual synthesis**:
The Phase 1A contribution concept: a synthesis approach that learns enhancement residuals with tumor-aware training signals while requiring only the pre-contrast slice at inference time. Phase 1A uses a 2D U-Net residual regressor as the first backbone; pix2pixHD/GAN strengthening is a later ablation.
_Avoid_: claiming test-time ground-truth mask conditioning or presenting the first Phase 1A backbone as a novel architecture.

**Loss-only tumor-aware synthesis**:
A tumor-aware synthesis approach that uses ground-truth masks only during training losses or auxiliary heads, with pre-contrast-only inference. Phase 1A starts with tumor-mask-only ROI weighting while the config keeps `roi_dilation_px` and `roi_context_weight` available for later context ablations.
_Avoid_: mask-conditioned inference.

**Predicted-mask conditioning**:
A synthesis approach that first predicts a coarse tumor mask at inference time and then uses that predicted mask as an input condition for synthesis.
_Avoid_: treating it as the default tumor-aware approach.

**Subtraction target**:
An internal training target where the model predicts the enhancement residual `post − pre`; submitted and evaluated outputs remain synthetic post-contrast slices.
_Avoid_: treating residual images as official submission outputs.

**Synthetic post**:
The final predicted peak-enhancement post-contrast slice in the required z-score float32 image space; this is the image consumed by downstream classification and segmentation evaluators. Phase 1A preserves native input size by padding internally to a U-Net-compatible multiple and cropping back before output.
_Avoid_: delta output, residual output, subtraction image, permanent resize output.

**Fixed evaluation classifier**:
A pretrained, frozen classifier under `src/evaluation/models/classification/` used during hold-out evaluation to measure downstream classification utility from synthetic post images. The default hold-out configuration uses the classifier ensemble from `src/evaluation/models`.
_Avoid_: retraining the classifier per synthesis model, or including the classifier in the synthesis submission container.

**Fixed evaluation segmenter**:
A pretrained, frozen nnU-Net under `src/evaluation/models/segmentation/` used during hold-out evaluation to measure downstream segmentation utility from synthetic post images. The default hold-out configuration uses fold 0.
_Avoid_: training a separate local segmenter for the primary model-selection score.

**Evaluation model config**:
The fixed downstream-evaluator setup used for hold-out evaluation: `MAMA_MODELS_DIR=src/evaluation/models`, `MAMA_ENSEMBLE=True`, and `MAMA_SEG_FOLD=0` unless a separate sensitivity analysis explicitly says otherwise.
_Avoid_: changing evaluator weights or folds between synthesis model comparisons.

**Phase 1A experiment config**:
A single YAML config that records run, data, model, loss, training, evaluation, and submission-contract settings for mask-free tumor-aware residual synthesis.
_Avoid_: separating inference/evaluation contract from the training config in ways that make a run non-reproducible.

**Submission smoke test**:
A local or Grand Challenge try-out/debug execution that verifies container behavior and input/output compatibility without claiming model performance.
_Avoid_: validation, baseline.

## Example dialogue

Dev: “Did our baseline improve?”
Domain expert: “If you mean the performance comparison point, compare against the recorded baseline metrics on the agreed split. If you mean the identity container, call it the smoke-test submission.”

Dev: “Should we use a validation submission?”
Domain expert: “Use Validation phase only for the official Grand Challenge phase. For local metrics, say hold-out evaluation. For container I/O checks, say submission smoke test.”

## Flagged ambiguities

- “Baseline” is overloaded in challenge materials and local planning. In this project it means only the reproducible performance comparison point; infrastructure and reference artifacts use more specific terms.
- “Validation” is reserved for the official Grand Challenge Validation phase. Local model comparison is hold-out evaluation; container and I/O verification is submission smoke test.
