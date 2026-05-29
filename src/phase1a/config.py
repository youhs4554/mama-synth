"""Experiment config contract for Phase 1A runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

REQUIRED_SECTIONS = (
    "run",
    "data",
    "model",
    "loss",
    "train",
    "evaluation",
    "submission",
)


@dataclass(frozen=True)
class Phase1AConfig:
    """Validated Phase 1A experiment config."""

    raw: dict[str, object]

    @property
    def section_names(self) -> tuple[str, ...]:
        return REQUIRED_SECTIONS


def validate_phase1a_config(raw_config: Mapping[str, object]) -> Phase1AConfig:
    """Validate the single Phase 1A experiment config contract."""
    config = dict(raw_config)
    for section in REQUIRED_SECTIONS:
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Phase 1A config requires {section} section")

    loss = config["loss"]
    assert isinstance(loss, dict)
    roi_weighting = loss.setdefault(
        "roi_weighting",
        {"mode": "tumor_mask_only", "context": {"enabled": False}},
    )
    if not isinstance(roi_weighting, dict):
        raise ValueError("loss.roi_weighting must be an object")
    if roi_weighting.get("mode") != "tumor_mask_only":
        raise ValueError("Phase 1A ROI weighting mode must be tumor_mask_only")
    context = roi_weighting.setdefault("context", {"enabled": False})
    if not isinstance(context, dict):
        raise ValueError("loss.roi_weighting.context must be an object")
    if context.get("enabled") is not False:
        raise ValueError("Phase 1A ROI context must be disabled by default")

    data = config["data"]
    assert isinstance(data, dict)
    split_manifest = data.get("split_manifest")
    if not isinstance(split_manifest, str) or not split_manifest:
        raise ValueError("data.split_manifest is required")
    if not Path(split_manifest).exists():
        raise ValueError(f"data.split_manifest does not resolve locally: {split_manifest}")

    model = config["model"]
    assert isinstance(model, dict)
    if model.get("inference_inputs") != ["pre_contrast"]:
        raise ValueError("Phase 1A inference must be pre_contrast-only")
    if model.get("target") != "residual":
        raise ValueError("Phase 1A model.target must be residual")
    if "ablations" in model:
        raise ValueError("Architecture-specific ablations are out of scope for this issue")

    evaluation = config["evaluation"]
    assert isinstance(evaluation, dict)
    evaluation_mode = evaluation.get("mode")
    if evaluation_mode == "fixed_downstream_evaluators":
        if evaluation.get("classifier_ensemble") is not True or evaluation.get("segmentation_fold") != 0:
            raise ValueError(
                "Phase 1A fixed downstream evaluator setup requires "
                "classifier_ensemble=true and segmentation_fold=0"
            )
    elif evaluation_mode != "sensitivity_analysis":
        raise ValueError(
            "Phase 1A evaluation.mode must be fixed_downstream_evaluators "
            "or sensitivity_analysis"
        )

    submission = config["submission"]
    assert isinstance(submission, dict)
    if submission.get("output") != "synthetic_post":
        raise ValueError("Phase 1A submission output must be synthetic_post")

    return Phase1AConfig(raw=config)
