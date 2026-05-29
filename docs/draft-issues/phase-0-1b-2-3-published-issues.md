# Published implementation issues: Phase 0, Phase 1B, Phase 2, Phase 3

These issues were approved from the `docs/prd/` breakdown and published in dependency order.

| Slice | Issue | Type | Blocked by |
|---|---|---|---|
| P0-1 | [Audit local test, dataset, hardware, and preprocessing assumptions](https://github.com/youhs4554/mama-synth/issues/15) | AFK | None |
| P0-2 | [Generate challenge-like debug MHA artifacts and split manifest](https://github.com/youhs4554/mama-synth/issues/16) | AFK | #15 |
| P0-3 | [Record identity lower-bound and stable metric output contract](https://github.com/youhs4554/mama-synth/issues/17) | AFK | #16 |
| P0-4 | [Reproduce reference GAN baseline or mark it unreproducible](https://github.com/youhs4554/mama-synth/issues/18) | HITL | #16, #17 |
| P0-5 | [Smoke-test identity submission container and output validation](https://github.com/youhs4554/mama-synth/issues/19) | AFK | #16 |
| P0-6 | [Publish Phase 0 audit bundle and weight-staging decision](https://github.com/youhs4554/mama-synth/issues/20) | AFK | #17, #18, #19 |
| P1B-1 | [Add Phase 1B ablation config and registry on Phase 1A contracts](https://github.com/youhs4554/mama-synth/issues/21) | AFK | #1, #2, #9, #10 |
| P1B-2 | [Implement 2D U-Net residual-regressor comparator](https://github.com/youhs4554/mama-synth/issues/22) | AFK | #21 |
| P1B-3 | [Add seeded domain robustness augmentation ablation](https://github.com/youhs4554/mama-synth/issues/23) | AFK | #21 |
| P1B-4 | [Add isolated loss/model ablation groups](https://github.com/youhs4554/mama-synth/issues/24) | AFK | #21, #22 |
| P1B-5 | [Add ablation runner and audit metric summary interface](https://github.com/youhs4554/mama-synth/issues/25) | AFK | #22, #23, #24 |
| P1B-6 | [Package only promoted Phase 1B checkpoint behind smoke tests](https://github.com/youhs4554/mama-synth/issues/26) | AFK | #25 |
| P2-1 | [Make Phase 2 go/no-go decision from Phase 1 evidence](https://github.com/youhs4554/mama-synth/issues/27) | HITL | #25 |
| P2-2 | [Build frozen autoencoder reconstruction gate](https://github.com/youhs4554/mama-synth/issues/28) | AFK | #27 |
| P2-3 | [Build conditional latent inference contract](https://github.com/youhs4554/mama-synth/issues/29) | AFK | #28 |
| P2-4 | [Add safe diffusion training job controls](https://github.com/youhs4554/mama-synth/issues/30) | AFK | #29 |
| P2-5 | [Compare target and sampling variants through staged metrics](https://github.com/youhs4554/mama-synth/issues/31) | AFK | #30 |
| P2-6 | [Package viable Phase 2 candidate without network dependencies](https://github.com/youhs4554/mama-synth/issues/32) | AFK | #31 |
| P3-1 | [Validate final candidate audit bundles](https://github.com/youhs4554/mama-synth/issues/33) | AFK | #26, #32 |
| P3-2 | [Select final candidate from frozen local ranking table](https://github.com/youhs4554/mama-synth/issues/34) | HITL | #33 |
| P3-3 | [Optional deterministic ensemble or blending candidate](https://github.com/youhs4554/mama-synth/issues/35) | HITL | #33 |
| P3-4 | [Harden final packaging and model-weight strategy](https://github.com/youhs4554/mama-synth/issues/36) | AFK | #34 |
| P3-5 | [Produce final decision record and submission evidence bundle](https://github.com/youhs4554/mama-synth/issues/37) | HITL | #34, #36 |
