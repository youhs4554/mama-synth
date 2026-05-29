"""Phase 1B ablation config and registry contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from phase1a.config import Phase1AConfig, validate_phase1a_config

SUPPORTED_MODEL_FAMILIES = ("phase1a_constant_residual", "unet_residual_regressor")
SUPPORTED_LOSS_TERMS = (
    "residual_l1",
    "tumor_roi_weighted_residual_l1",
    "perceptual_loss",
    "feature_matching",
    "tumor_roi_discriminator",
    "auxiliary_segmentation_branch",
    "roi_context_weighting",
)
SUPPORTED_AUGMENTATION_POLICIES = ("disabled", "scanner_protocol_intensity")
SUPPORTED_SELECTION_STAGES = ("early", "shortlist")
PHASE1B_REQUIRED_RUN_METADATA_FIELDS = (
    "config",
    "split",
    "model_variant",
    "loss_weights",
    "augmentation_settings",
    "checkpoint_hash",
    "metric_summary",
)


@dataclass(frozen=True)
class Phase1BConfig:
    """Validated Phase 1B config layered on Phase 1A contracts."""

    phase1a: Phase1AConfig
    ablation_dimensions: dict[str, object]
    required_run_metadata_fields: tuple[str, ...] = PHASE1B_REQUIRED_RUN_METADATA_FIELDS


def validate_phase1b_config(raw_config: Mapping[str, object]) -> Phase1BConfig:
    """Validate a Phase 1B ablation config without weakening Phase 1A contracts."""
    config = dict(raw_config)
    phase1a = validate_phase1a_config(config)
    ablation_dimensions = _validate_ablation(config.get("ablation"))
    _validate_run_metadata(config.get("run_metadata"))
    return Phase1BConfig(phase1a=phase1a, ablation_dimensions=ablation_dimensions)


def validate_phase1b_fixed_evaluator_compatibility(
    base_config: Mapping[str, object],
    candidate_config: Mapping[str, object],
) -> None:
    """Reject candidate comparisons that alter fixed evaluator settings."""
    base_settings = _fixed_evaluator_settings(base_config)
    candidate_settings = _fixed_evaluator_settings(candidate_config)
    if candidate_settings != base_settings:
        raise ValueError("fixed evaluator settings changed between Phase 1B candidates")


def _validate_ablation(raw_ablation: object) -> dict[str, object]:
    if not isinstance(raw_ablation, dict):
        raise ValueError("Phase 1B ablation section is required")
    model_family = raw_ablation.get("model_family")
    if model_family not in SUPPORTED_MODEL_FAMILIES:
        raise ValueError(f"unknown Phase 1B model_family: {model_family}")
    loss_terms = raw_ablation.get("loss_terms")
    if not isinstance(loss_terms, list):
        raise ValueError("Phase 1B ablation.loss_terms must be a list")
    for term in loss_terms:
        if term not in SUPPORTED_LOSS_TERMS:
            raise ValueError(f"unknown Phase 1B loss term: {term}")
    augmentation_policy = raw_ablation.get("augmentation_policy")
    if augmentation_policy not in SUPPORTED_AUGMENTATION_POLICIES:
        raise ValueError(f"unknown Phase 1B augmentation_policy: {augmentation_policy}")
    selection_stage = raw_ablation.get("selection_stage")
    if selection_stage not in SUPPORTED_SELECTION_STAGES:
        raise ValueError("Phase 1B selection_stage must be early or shortlist")
    return {
        "model_family": model_family,
        "loss_terms": list(loss_terms),
        "augmentation_policy": augmentation_policy,
        "selection_stage": selection_stage,
    }


def _validate_run_metadata(raw_metadata: object) -> None:
    if not isinstance(raw_metadata, dict):
        raise ValueError("Phase 1B run_metadata section is required")
    for field in PHASE1B_REQUIRED_RUN_METADATA_FIELDS:
        if field not in raw_metadata:
            raise ValueError(f"Phase 1B run_metadata requires {field}")


def _fixed_evaluator_settings(config: Mapping[str, object]) -> dict[str, object]:
    evaluation = config.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ValueError("evaluation config is required")
    if evaluation.get("mode") != "fixed_downstream_evaluators":
        raise ValueError("Phase 1B comparisons require fixed_downstream_evaluators mode")
    return {
        "classifier_ensemble": bool(evaluation.get("classifier_ensemble")),
        "segmentation_fold": int(evaluation.get("segmentation_fold", -1)),
    }
