"""Baseline evidence contracts for Phase 1A promotion decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class BaselineEvidence:
    identity_role: str
    primary_performance_baseline: str | None
    ranking_names: tuple[str, ...]


def validate_baseline_evidence(raw: Mapping[str, object]) -> BaselineEvidence:
    """Validate local baseline evidence for Phase 1A comparisons."""
    identity = raw.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("identity evidence is required")
    identity_role = identity.get("role")
    if identity_role != "lower_bound_benchmark":
        raise ValueError("identity output must be recorded only as a lower-bound benchmark")

    reference_gan = raw.get("reference_gan")
    if not isinstance(reference_gan, dict):
        raise ValueError("reference GAN evidence is required")
    if reference_gan.get("reproducible") is True:
        for field in (
            "selected_holdout_split",
            "inference_path",
            "model_artifact_identity",
            "metric_summary",
        ):
            if not reference_gan.get(field):
                raise ValueError(f"reference GAN evidence requires {field}")

    promotion = raw.get("promotion")
    if not isinstance(promotion, dict):
        raise ValueError("promotion evidence is required")
    if reference_gan.get("reproducible") is not True and promotion.get("deferred") is not True:
        raise ValueError("promotion must be deferred when reference GAN is not reproducible")

    primary = raw.get("primary_performance_baseline")
    if primary == "identity":
        raise ValueError("identity cannot be the primary performance baseline")
    if primary is not None and not isinstance(primary, str):
        raise ValueError("primary_performance_baseline must be a string or null")
    if reference_gan.get("reproducible") is True and primary != "reference_gan":
        raise ValueError(
            "reproducible reference GAN must be the primary performance baseline"
        )
    if primary not in {None, "reference_gan"}:
        alternative = raw.get(primary)
        if not isinstance(alternative, dict) or alternative.get("human_approval") is not True:
            raise ValueError("alternative primary performance baseline requires human approval")

    selected_split = raw.get("selected_holdout_split")
    ranking_table = raw.get("local_ranking_table", [])
    if not isinstance(ranking_table, list):
        raise ValueError("local_ranking_table must be a list")
    ranking_names: list[str] = []
    for entry in ranking_table:
        if not isinstance(entry, dict):
            raise ValueError("local_ranking_table entries must be objects")
        if entry.get("split") != selected_split:
            raise ValueError("local ranking table entries must use the selected hold-out split")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("local ranking table entries require name")
        ranking_names.append(name)

    return BaselineEvidence(
        identity_role=identity_role,
        primary_performance_baseline=primary,
        ranking_names=tuple(ranking_names),
    )
