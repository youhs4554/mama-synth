# PRD: Phase 3 — Final Selection and Submission

## Reference Documents

- `CONTEXT.md` defines canonical project terminology used by this PRD.
- `STRATEGY.md` defines Phase 3 as optional ensemble/selection work and emphasizes choosing a single robust submission model based on balanced metric groups.
- Phase 0, Phase 1A, Phase 1B, and Phase 2 PRDs define the upstream infrastructure, model candidates, evaluation contracts, and promotion gates.

## Problem Statement

By the time Phase 3 begins, the project may have multiple candidates with different strengths: a Phase 1A or Phase 1B regression/GAN-style candidate may have strong image fidelity, while a Phase 2 latent diffusion candidate may have stronger tumor ROI realism or downstream proxy metrics. The official MAMA-SYNTH ranking averages four metric-group ranks, so choosing the model with the best single metric can lose overall.

The project needs a final selection and submission phase that compares all eligible candidates on the same evidence base, avoids overfitting limited Validation phase feedback, packages the chosen model safely, and preserves enough audit material for Test phase submission and possible top-3 code review.

## Solution

Build Phase 3 as the final candidate-selection, optional blending/ensemble analysis, and Grand Challenge submission-readiness phase. It consumes only candidates that have already passed local promotion gates and submission smoke tests. It compares them using the frozen local ranking table, group-level regressions, Validation phase feedback when available, runtime/memory risk, policy compliance, and reproducibility completeness.

The default outcome is one selected submission candidate, not a complex ensemble. Optional blending or ensemble selection is allowed only when it is simple, deterministic, submission-compatible, and demonstrably improves balanced hold-out performance without increasing operational risk.

## User Stories

1. As a challenge participant, I want all promoted candidates compared on the same hold-out evaluation basis, so that the final model is chosen from fair evidence.
2. As a challenge participant, I want model selection based on four metric groups rather than one metric, so that the final choice matches the challenge ranking philosophy.
3. As a challenge participant, I want local proxy rank mean computed over a frozen candidate table, so that candidate ordering is reproducible.
4. As a challenge participant, I want group-level regressions visible, so that a visually impressive model does not hide unacceptable MSE, classification, or segmentation damage.
5. As a researcher, I want Phase 1 and Phase 2 candidates summarized by strengths and weaknesses, so that the final decision can be defended in a paper or postmortem.
6. As a researcher, I want Validation phase feedback incorporated carefully, so that limited official results help calibrate but do not cause uncontrolled overfitting.
7. As a researcher, I want any ensemble or blending rule treated as a candidate with its own audit bundle, so that it is not a hidden post-processing trick.
8. As a researcher, I want deterministic blending rules preferred over complex ensembles, so that final submission behavior is reproducible.
9. As an evaluator, I want fixed evaluation classifier and segmenter settings preserved for final comparison, so that downstream utility evidence stays comparable.
10. As an evaluator, I want final candidates checked for no major metric group regression versus the primary performance baseline, so that balanced performance remains required.
11. As an evaluator, I want final selection to distinguish lower-bound benchmark, primary performance baseline, and submission candidate, so that decision language remains precise.
12. As an operator, I want the selected model packaged into a Grand Challenge-compatible container, so that it can run with only the official pre-contrast input image.
13. As an operator, I want the container to preserve dtype, shape, metadata, slug, and output path, so that official evaluation can read the synthetic post image.
14. As an operator, I want model weights handled through one documented strategy, so that packaging is reproducible and not dependent on local paths.
15. As an operator, I want runtime and memory measured on a submission-like path, so that the selected candidate is safe for T4/A10G-style Grand Challenge hardware.
16. As an operator, I want Try-out Algorithm and Debug phase checks completed before any Validation or Test phase submission, so that official submissions are not wasted on I/O errors.
17. As an operator, I want every official submission tagged with container version, model hash, config, split, and metric summary, so that leaderboard results can be traced back to code.
18. As an operator, I want the Test phase candidate frozen before final submission, so that last-minute changes do not invalidate reproducibility.
19. As a compliance reviewer, I want public dataset and pretrained weight provenance documented, so that top-3 code review can be answered quickly.
20. As a compliance reviewer, I want protected MRI data, masks, generated outputs, and checkpoints kept out of commits and external trackers, so that data policy is respected.
21. As a future issue author, I want selection, packaging, smoke testing, and official submission steps separated, so that a failure in one step does not corrupt the final decision record.
22. As a future issue author, I want a final handoff artifact, so that another agent can reproduce the selected submission if the active session is lost.
23. As a paper author, I want aggregate metric tables and sanitized plots available, so that challenge results can support a Deep-Breath Workshop paper without exposing protected images.
24. As a challenge participant, I want a clear stop rule after final submission, so that post-deadline changes are not confused with the submitted artifact.

## Implementation Decisions

- Phase 3 consumes only candidates that already passed prior local promotion and submission smoke-test gates.
- The default final decision is to choose a single submission candidate.
- Optional ensemble or blending is allowed only as a simple, deterministic, auditable candidate that preserves pre-contrast-only inference and synthetic post output.
- Candidate comparison uses a frozen local ranking table containing the lower-bound benchmark, primary performance baseline, and all promoted candidates evaluated on the same split.
- Four metric groups are considered together: image fidelity, tumor ROI realism, downstream classification utility, and downstream segmentation utility.
- Validation phase leaderboard feedback may inform final choice but must be recorded as official-phase evidence, not substituted for local hold-out evaluation.
- The Test phase candidate must have a complete audit bundle: config, split, metrics, inference settings, model hash, container version, resource provenance, and smoke-test logs.
- Final packaging uses one documented model-weight loading strategy and avoids runtime network dependencies.
- The selected container must satisfy Grand Challenge I/O, non-root runtime, writable output, metadata preservation, and hardware memory constraints.
- Final artifacts should include a concise decision record explaining why the selected candidate beat alternatives under the four-group ranking philosophy.
- Top-3 readiness requires clean provenance for code, external data, pretrained weights, and training/inference commands.

## Testing Decisions

- Tests should verify selection behavior from stable metric-summary inputs, not private sorting implementation details.
- Selection tests should cover local proxy rank mean, group-level non-inferiority checks, tie handling, and rejection of candidates missing audit artifacts.
- Ensemble/blending tests should verify deterministic output, native-size preservation, pre-contrast-only inference, and synthetic post output if blending is implemented.
- Packaging tests should verify output slug, `.mha` readability, float32 dtype, finite values, metadata preservation, and configured model-weight path behavior.
- Reproducibility tests should verify that final audit bundles include config, split, metrics, inference settings, model hash, container version, and resource provenance.
- Operational checks should include Docker build/run/save, Try-out Algorithm, Debug phase execution, and official submission record capture.
- Protected data must not be embedded in tests, issue bodies, or PRD artifacts.

## Out of Scope

- Training new model families from scratch.
- Broad hyperparameter exploration after final candidate freeze.
- Changing fixed downstream evaluation models for the primary selection score.
- Test-time ground-truth mask conditioning.
- Submitting candidates that lack local audit bundles.
- Treating Validation phase feedback as unlimited tuning data.
- Publishing protected MRI images, masks, generated outputs, or checkpoints.

## Further Notes

- Phase 3 should begin only after there is at least one promoted submission candidate.
- If no candidate beats the primary performance baseline under local gates, the safest final choice may be the primary performance baseline rather than a newer but unbalanced model.
- The final response after Phase 3 work should state the selected candidate, evidence basis, official submission status, and the exact remaining action if submission is not yet complete.
