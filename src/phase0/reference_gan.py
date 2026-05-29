"""Phase 0 reference GAN baseline evidence helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def build_reference_gan_evidence(
    *,
    selected_holdout_split: str,
    reproducible: bool,
    blocker: str | None = None,
    attempted_command: str | None = None,
    inference_path: str | None = None,
    model_artifact_identity: str | None = None,
    metric_summary: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build baseline evidence for the reference GAN path."""
    evidence: dict[str, object] = {
        "selected_holdout_split": selected_holdout_split,
        "identity": {"role": "lower_bound_benchmark", "metrics": {}},
        "local_ranking_table": [],
    }
    if reproducible:
        if not inference_path or not model_artifact_identity or not metric_summary:
            raise ValueError("reproducible reference GAN requires inference path, model artifact, and metrics")
        evidence.update(
            {
                "primary_performance_baseline": "reference_gan",
                "reference_gan": {
                    "reproducible": True,
                    "selected_holdout_split": selected_holdout_split,
                    "inference_path": inference_path,
                    "model_artifact_identity": model_artifact_identity,
                    "metric_summary": dict(metric_summary),
                },
                "promotion": {"deferred": False},
            }
        )
    else:
        if not blocker or not attempted_command:
            raise ValueError("unreproducible reference GAN requires blocker and attempted command")
        evidence.update(
            {
                "primary_performance_baseline": None,
                "reference_gan": {
                    "reproducible": False,
                    "blocker": blocker,
                    "attempted_command": attempted_command,
                },
                "promotion": {
                    "deferred": True,
                    "reason": "reference_gan_not_reproducible",
                },
            }
        )
    return evidence


def write_reference_gan_evidence(evidence: Mapping[str, object], output_path: str | Path) -> None:
    """Write durable reference GAN baseline evidence."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
