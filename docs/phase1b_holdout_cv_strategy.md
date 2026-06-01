# Phase 1B hold-out / CV strategy — leave-one-source-out (LOSO)

Date: 2026-05-30

## Motivation

All Phase 1B evidence so far used the **n=4 NACT** center-held-out split — explicitly *exploratory, not promotion-grade*. Promotion (STRATEGY §4.6 / CONTEXT promotion gate) requires a credible hold-out where the four metric groups are jointly satisfied vs the primary baseline. We now have the full local training set preprocessed, so we can build a **larger, more reliable source/center-proxy hold-out** via leave-one-source-out.

Source ≈ center in MAMA-MIA, so LOSO approximates external-institution generalization. It is **still a proxy**, not the true hidden Test A/B (Radboud/Fleming), which are external and absent locally.

## Data (preprocessed, `experiments/phase1b/full_dataset_v1/preprocessed/mha`)

DUKE 200 · ISPY1 104 · ISPY2 849 · NACT 64 = **1217** cases (pre/post/mask, z-score float32 .mha, native size). All from `train_split` plus NACT `test_split` members; the official validation/test sets are external (no leakage).

## LOSO folds (manifests under `splits/`, model-agnostic, data-ready)

| Fold | Hold-out (eval) | n hold-out | Train | n train | Use |
|---|---|---|---|---|---|
| `phase1b_loso_nact_v1.json` | NACT | 64 | DUKE+ISPY1+ISPY2 | 1153 | **Primary promotion-grade** (large train, replaces n=4 NACT) |
| `phase1b_loso_duke_v1.json` | DUKE | 200 | ISPY1+ISPY2+NACT | 1017 | **Primary promotion-grade** (largest hold-out, balanced) |
| `phase1b_loso_ispy1_v1.json` | ISPY1 | 104 | DUKE+ISPY2+NACT | 1113 | Secondary |
| `phase1b_loso_ispy2_v1.json` | ISPY2 | 849 | DUKE+ISPY1+NACT | 368 | Stress/generalization probe only — imbalanced (train≪hold-out), slow eval |

## Promotion semantics

- Fixed evaluator unchanged: `MAMA_MODELS_DIR=src/evaluation/models`, `MAMA_ENSEMBLE=True`, `MAMA_SEG_FOLD=0`.
- Primary performance baseline on each fold = reference GAN (medigan 00023) + identity lower bound, plus prior candidates, in a per-fold local ranking table.
- A candidate is promotion-eligible only if, on the primary fold(s) (NACT-out and/or DUKE-out), it shows no >5% metric-group regression, ≥2 groups improved/non-inferior, improved local proxy rank-mean vs baseline, and passes the submission smoke test (STRATEGY §4.6).
- Aggregate across NACT-out + DUKE-out (and ISPY1-out) by mean rank for a robustness view; ISPY2-out is reported as a generalization stress probe, not a gate.

## Cost & sequencing note

Running all 4 folds × (train + nnU-Net segmentation eval) is expensive (ISPY2-out evaluates 849 cases). Therefore:
- The manifests are built now (data-ready), but the **LOSO training/eval runs are deferred until the model choice is fixed** by the pretrained-model deep research (`docs/research/pretrained_synthesis_models_deep_research.md`). We will not spend fold-runs on the fixed-random-feature NumPy comparator (shown to have a representational ceiling).
- First fold to run on the chosen model: **NACT-out** (directly comparable to prior n=4 NACT evidence at larger n), then **DUKE-out**.

## Status

- [x] All sources preprocessed (1217 cases).
- [x] 4 LOSO manifests generated + validated (load OK).
- [ ] Run chosen model (post-research; e.g. fine-tuned pretrained 00023) on NACT-out then DUKE-out with fixed evaluator; record promotion/no-promotion per fold.
