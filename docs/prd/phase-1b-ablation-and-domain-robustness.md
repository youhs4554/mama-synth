# PRD: Phase 1B — Ablation and Domain Robustness

## Reference Documents

- `CONTEXT.md` defines canonical project terminology used by this PRD.
- `STRATEGY.md` defines Phase 1B as the next comparison and robustness phase after Phase 1A is reproducible.
- The Phase 1A PRD defines the required contracts for split manifests, Phase 1A experiment configs, residual targets, mask-free inference, staged hold-out evaluation, and submission candidate promotion.

## Problem Statement

Phase 1A establishes a mask-free tumor-aware residual synthesis pipeline, but a minimal residual/ROI-weighted setup is unlikely to be the final competitive model. The project needs a disciplined way to test targeted improvements without losing the reproducibility, pre-contrast-only inference, native-size synthetic post output, and fixed hold-out evaluation contracts already established.

The main risk is uncontrolled ablation sprawl: adding a U-Net comparator, perceptual losses, feature matching, tumor discriminators, auxiliary segmentation, or domain robustness augmentation all at once would make results hard to interpret and could overfit the local hold-out split or official Validation phase feedback.

## Solution

Build Phase 1B as a controlled ablation and robustness framework on top of the Phase 1A contracts. Each ablation changes one primary factor at a time, runs on the same split and evaluation configuration, records the same audit metadata, and is promoted only through the existing staged hold-out evaluation and submission smoke-test gates.

The first comparison path is a 2D U-Net residual regressor against the Phase 1A pix2pixHD-style model. In the current repository state, this U-Net residual-regressor path is the active low-risk implementation path because the shared Phase 1A contracts are reproducible while the reference GAN remains blocked without staged external weights. After the U-Net path is stable on a fuller eligible local dataset, Phase 1B can test domain robustness augmentation, tumor ROI loss-weight changes, perceptual/LPIPS-style losses, stronger pix2pixHD feature matching, tumor ROI discriminator ideas, and auxiliary segmentation objectives as separate, reversible experiments.

### Current implementation alignment note

As of the latest Phase 1B evidence, completed local experiments are exploratory and no candidate is promoted for packaging. The center/source-proxy held-out runs use NACT hold-out `n=4`; base16 U-Net improves several proxy groups over lower-capacity variants, but the evidence remains too small and segmentation utility remains weak. Therefore the next implementation step is to create an explicit full-dataset or larger eligible-dataset split/config for the U-Net residual-regressor baseline before starting heavier GAN/perceptual/discriminator work. If that split leaves no independent local hold-out, its evidence must be recorded as training/smoke evidence rather than promotion-grade model-selection evidence.

## User Stories

1. As a model developer, I want a 2D U-Net residual-regressor comparison, so that the project has a simple deterministic baseline against the pix2pixHD-style Phase 1A backbone.
2. As a model developer, I want each ablation to reuse the Phase 1A split manifest, so that model comparisons are not confounded by different train/hold-out membership.
3. As a model developer, I want each ablation to reuse the Phase 1A experiment config contract, so that run metadata remains comparable.
4. As a model developer, I want pre-contrast-only inference preserved across all Phase 1B variants, so that improvements remain compatible with the Grand Challenge input contract.
5. As a model developer, I want all Phase 1B variants to output synthetic post images, so that evaluation and submission artifacts are consistent.
6. As a model developer, I want residual target learning preserved unless an ablation explicitly changes it, so that subtraction target benefits can be isolated.
7. As a model developer, I want domain robustness augmentation tested independently, so that external-institution generalization is improved without hiding its effect behind architecture changes.
8. As a model developer, I want scanner/protocol-inspired intensity augmentation configurable, so that models are less brittle to 3T Siemens and 1.5T GE hidden test distributions.
9. As a model developer, I want native-size padding and crop-back preserved, so that mixed-size hold-out cases can be evaluated without permanent resize artifacts.
10. As a researcher, I want feature matching and perceptual losses tested separately, so that image fidelity and tumor ROI realism tradeoffs are visible.
11. As a researcher, I want tumor ROI discriminator experiments isolated, so that any gain in SSIM-tumor or FRD can be attributed to the tumor-local objective.
12. As a researcher, I want auxiliary segmentation branch experiments isolated, so that segmentation utility improvements are not confused with generic image-fidelity changes.
13. As a researcher, I want curriculum learning considered only after simpler tumor-aware objectives are measured, so that implementation complexity is justified by evidence.
14. As an evaluator, I want early ablation filtering to use image fidelity and tumor ROI realism, so that expensive downstream classification and segmentation evaluation is reserved for shortlists.
15. As an evaluator, I want shortlist candidates evaluated with all four metric groups, so that local model selection remains aligned with the challenge ranking philosophy.
16. As an evaluator, I want fixed evaluation classifier and segmenter settings unchanged across ablations, so that improvements are not caused by evaluator drift.
17. As an evaluator, I want group-level regressions reported, so that a model that improves FRD but harms MSE or segmentation utility is not promoted blindly.
18. As an operator, I want only promoted Phase 1B checkpoints packaged behind submission smoke tests, so that container work follows evidence rather than every experiment.
19. As an operator, I want experiment tracking to record config, split, model variant, loss weights, augmentation settings, checkpoint hash, and metric summary, so that Validation phase results are reproducible.
20. As an operator, I want long-running training and evaluation jobs to write durable logs under ignored experiment outputs, so that the active coding session is not blocked.
21. As a challenge participant, I want Validation phase submissions conserved for candidates that beat the primary performance baseline locally, so that the five official submissions are not wasted.
22. As a future issue author, I want Phase 1B split into independent tracer-bullet issues, so that one ablation can be implemented and tested without pulling in the full ablation matrix.
23. As a future issue author, I want failed ablations recorded with enough evidence to stop repeating them, so that experiment time is used efficiently.
24. As a future issue author, I want Phase 1B to leave Phase 2 go/no-go evidence, so that latent diffusion work starts only if the simpler family has plateaued.

## Implementation Decisions

- Phase 1B depends on Phase 1A contracts; it must not weaken pre-contrast-only inference, residual-target training, synthetic post output, native-size preservation, or staged promotion gates.
- A 2D U-Net residual regressor is the first comparison path because it is simpler than the pix2pixHD-style backbone and provides a strong regression-style reference.
- The ablation framework should make model family, loss terms, augmentation policy, and selection stage explicit run dimensions.
- Ablations change one primary factor at a time unless a combined experiment is explicitly marked as such after single-factor evidence exists.
- Domain robustness augmentation is treated as a first-class ablation group, not an incidental training detail.
- Perceptual loss, feature matching changes, tumor ROI discriminator, auxiliary segmentation branch, curriculum learning, and ROI context weighting are separate ablation groups.
- Predicted-mask conditioning remains outside Phase 1B unless explicitly promoted into a separate later PRD; Phase 1B defaults remain loss-only tumor-aware synthesis.
- All Phase 1B variants must record the same audit fields required by Phase 1A promotion: metrics, config, inference settings, and model hash.
- Validation phase feedback can inform prioritization, but local hold-out evaluation remains the gate for declaring a submission candidate.
- Experiment outputs, checkpoints, predictions, and protected image artifacts remain ignored local artifacts.
- The ablation runner should expose a deep module interface that accepts a config and returns a stable metric/audit summary, hiding training-loop details from promotion logic.

## Testing Decisions

- Tests should verify external ablation behavior: config validation, one-factor changes, run record completeness, pre-contrast-only inference, synthetic post output, and staged evaluator routing.
- U-Net comparator tests should verify residual target shape, native-size output, and inference without masks on deterministic fake images.
- Augmentation tests should verify reproducibility under a seed, that paired pre/post/mask alignment is preserved, and that disabled augmentation is a no-op.
- Loss-composition tests should verify selected loss terms from config on toy arrays without coupling to private training-loop implementation.
- Ablation registry tests should reject unknown variants, incompatible combinations, and accidental changes to fixed evaluator settings.
- Promotion tests should reuse Phase 1A promotion-gate behavior with toy metric summaries for Phase 1B candidates.
- Heavy GPU training, full FRD/classifier/segmenter evaluation, and Dockerized submission checks remain operational checks, not unit tests.

## Out of Scope

- Latent diffusion, CC-Net, ControlNet, or SD autoencoder work.
- TeNCA or temporal kinetic modeling.
- Test-time ground-truth mask conditioning.
- Full official Test phase submission.
- Broad hyperparameter sweeps without a defined ablation question.
- Retraining fixed downstream evaluation classifiers or segmenters.
- Changing the challenge I/O contract or z-score image space.

## Further Notes

- Phase 1B should produce a ranked set of candidate families and concrete go/no-go evidence for Phase 2.
- If Phase 1B yields a submission candidate, it must pass the same promotion and submission smoke-test standards as Phase 1A.
