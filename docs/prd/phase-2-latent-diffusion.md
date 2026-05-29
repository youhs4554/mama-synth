# PRD: Phase 2 — Latent Diffusion Synthesis

## Reference Documents

- `CONTEXT.md` defines canonical project terminology used by this PRD.
- `STRATEGY.md` defines Phase 2 as a time-permitting high-performance path using latent diffusion rather than pixel-space full-resolution DDPM.
- Phase 1A and Phase 1B PRDs define the reusable contracts for split manifests, experiment configs, hold-out evaluation, promotion gates, and submission smoke tests.

## Problem Statement

GAN and regression-style models may plateau on tumor ROI realism, FRD, and downstream utility even after Phase 1A and Phase 1B improvements. Literature around CC-Net and related conditional latent diffusion suggests that latent diffusion can improve realism and radiomic distribution metrics, but it is more complex to train, easier to hallucinate, slower at inference, and riskier under a single-GPU timeline.

The project needs a tightly scoped Phase 2 plan that explores latent diffusion only when justified by Phase 1 evidence, fits within the RTX A4500 20GB local constraint, preserves the Grand Challenge pre-contrast-only input contract, and produces synthetic post outputs that remain competitive across all four metric groups.

## Solution

Implement Phase 2 as a go/no-go gated latent diffusion track. The preferred design is a CC-Net-inspired conditional latent diffusion model: a frozen autoencoder compresses the image space, a conditional denoising model receives pre-contrast information through a ControlNet-style path, and the model learns a subtraction target or synthetic post reconstruction strategy that ultimately outputs native-size z-score float32 synthetic post images.

Phase 2 must not begin as a speculative rewrite. It starts only after Phase 1A/1B evidence shows either a plateau or a specific metric gap that latent diffusion is expected to address. The first milestone is a minimal latent reconstruction and inference contract; only then should tumor-aware losses, few-step sampling, or metric-balancing strategies be added.

## User Stories

1. As a challenge participant, I want a go/no-go gate before latent diffusion work begins, so that scarce time is not spent on a high-risk track prematurely.
2. As a challenge participant, I want latent diffusion considered only if Phase 1 models plateau or leave a clear FRD/AUROC/tumor-realism gap, so that Phase 2 has a measurable purpose.
3. As a model developer, I want the autoencoder frozen by default, so that training fits within local 20GB GPU constraints.
4. As a model developer, I want latent-space training instead of pixel-space full-resolution DDPM, so that memory usage is realistic for the available hardware.
5. As a model developer, I want the pre-contrast slice to be the only inference input, so that the Grand Challenge input contract remains valid.
6. As a model developer, I want the conditional path to inject pre-contrast structure, so that generated enhancement preserves anatomy rather than hallucinating unrelated tissue.
7. As a model developer, I want subtraction target learning evaluated for latent diffusion, so that the strongest Phase 1 lesson is not discarded.
8. As a model developer, I want native-size synthetic post output after latent decoding, padding, and crop-back, so that evaluation masks and metadata still align.
9. As a model developer, I want gradient clipping, AMP, batch-size limits, and checkpointing configurable, so that training failures are visible and recoverable.
10. As a researcher, I want latent scale and autoencoder preprocessing recorded explicitly, so that reconstructions are reproducible and not silently mis-scaled.
11. As a researcher, I want few-step or regression-style sampling compared against full diffusion sampling, so that MSE/LPIPS degradation can be controlled.
12. As a researcher, I want hallucination risk measured through all four metric groups, so that better FRD does not hide worse fidelity or segmentation utility.
13. As a researcher, I want latent reconstruction quality checked before denoising model training, so that autoencoder artifacts are not blamed on the diffusion model.
14. As an evaluator, I want Phase 2 candidates compared against the same primary performance baseline and Phase 1 shortlist, so that improvement claims are meaningful.
15. As an evaluator, I want early Phase 2 screening to include MSE, LPIPS, SSIM-tumor, and FRD, so that diffusion realism is balanced against fidelity.
16. As an evaluator, I want shortlist Phase 2 checkpoints evaluated with fixed downstream classifier and segmenter settings, so that classification and segmentation utility remain comparable.
17. As an operator, I want long-running diffusion training to run in the background with durable logs and watchdog monitoring, so that failures such as NaNs, OOM, or stalled loss are caught early.
18. As an operator, I want inference-time memory and runtime measured on a submission-like path, so that a model that trains locally does not fail on Grand Challenge T4/A10G hardware.
19. As an operator, I want external pretrained weights documented as publicly accessible before the challenge cutoff, so that submission policy compliance is auditable.
20. As an operator, I want the final container to avoid network dependencies, so that Grand Challenge runtime succeeds without external downloads.
21. As a future issue author, I want autoencoder reconstruction, conditional latent training, sampling, evaluation, and packaging separated into independent issues, so that Phase 2 can stop safely if any gate fails.
22. As a future issue author, I want failed diffusion experiments recorded with model hash, config, and metrics, so that the team does not repeatedly retry unstable settings.
23. As a challenge participant, I want Phase 2 to produce a submission candidate only if it improves local proxy rank mean without unacceptable group regressions, so that official submissions remain disciplined.

## Implementation Decisions

- Phase 2 is gated by Phase 1 evidence and should not start unless there is time and a clearly defined metric gap.
- Pixel-space full-resolution DDPM is avoided because it is too risky for the local GPU and timeline.
- The default Phase 2 family is conditional latent diffusion with a frozen autoencoder and pre-contrast conditioning.
- Pretrained resources must be public, policy-compliant, documented, and available before the challenge resource cutoff.
- The model input contract remains pre-contrast only at inference time.
- Tumor masks may be used for training losses or local evaluation, but not as submission inputs.
- The final artifact remains synthetic post in z-score float32 image space, not a latent, residual, or subtraction image.
- Native-size preservation remains required through any internal latent resize, padding, or crop-back path.
- Autoencoder reconstruction quality is a mandatory first gate before denoising model training.
- Latent scale, normalization bridge, conditioning path, sampling steps, random seed, and checkpoint hash are required run metadata.
- Few-step or regression-style sampling is part of the metric-balancing plan because pure diffusion sampling may improve realism while harming fidelity.
- Phase 2 promotion uses the same four-group staged evaluation philosophy as Phase 1.
- Grand Challenge packaging must include all weights or use the configured model-upload path and must not depend on runtime network access.
- Training jobs must produce durable logs, checkpoint records, and monitorable failure signals.

## Testing Decisions

- Tests should verify contracts around latent reconstruction, conditional inputs, synthetic post output, native-size preservation, and run metadata completeness.
- Autoencoder wrapper tests should verify deterministic encode/decode shape behavior and stable reconstruction output on toy arrays or fixtures.
- Conditioning tests should verify that inference requires pre-contrast input and does not require tumor masks.
- Sampling tests should verify deterministic behavior under a fixed seed for small toy models or mocked denoisers.
- Config tests should reject missing latent scale, missing pretrained-resource provenance, unsupported sampling settings, or policy-incompatible external resources.
- Evaluation tests should reuse existing staged metric and promotion-gate behavior with mocked metric summaries.
- Operational checks should include GPU memory profiling, NaN/OOM monitoring, long-running job logs, and submission-style inference timing.
- Full diffusion training and full downstream evaluation are operational experiments, not unit tests.

## Out of Scope

- Pixel-space full-resolution DDPM.
- Unpaired translation methods that ignore paired MAMA-MIA supervision.
- Test-time ground-truth mask conditioning.
- Building a new autoencoder from scratch unless frozen public weights are unusable and the user explicitly approves the cost.
- Broad diffusion architecture research beyond the CC-Net-inspired path.
- Replacing Phase 1 evaluation and promotion contracts.
- Official Test phase submission without Phase 3 selection and packaging review.

## Further Notes

- Phase 2 should be abandoned quickly if latent reconstruction is poor, training is unstable, inference cannot fit target Grand Challenge hardware, or local proxy rank mean does not beat Phase 1 candidates.
- A successful Phase 2 result should still be treated as a submission candidate, not the final Test phase model, until Phase 3 selection completes.
