"""Phase 1B submission packaging gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

REQUIRED_PACKAGING_AUDIT_FIELDS = ("config", "split", "model_hash")


@dataclass(frozen=True)
class Phase1BPackagingEvidence:
    """Evidence required before packaging a Phase 1B checkpoint."""

    promotion_decision: Mapping[str, object] | None
    smoke_test_passed: bool
    audit_fields: Mapping[str, object]
    output_dir: Path


def package_promoted_phase1b_checkpoint(
    *,
    checkpoint_path: Path,
    evidence: Phase1BPackagingEvidence,
) -> dict[str, object]:
    """Write a packaging manifest only for promoted, smoke-tested checkpoints."""
    if evidence.promotion_decision is None or evidence.promotion_decision.get("accepted") is not True:
        raise ValueError("Phase 1B packaging requires accepted promotion evidence")
    if evidence.smoke_test_passed is not True:
        raise ValueError("Phase 1B packaging requires a passing smoke test")
    if not checkpoint_path.exists():
        raise ValueError(f"checkpoint does not exist: {checkpoint_path}")
    for field in REQUIRED_PACKAGING_AUDIT_FIELDS:
        if field not in evidence.audit_fields:
            raise ValueError(f"Phase 1B packaging audit_fields requires {field}")

    inference_settings = evidence.audit_fields.get(
        "inference_settings",
        {"inputs": ["pre_contrast"], "output": "synthetic_post"},
    )
    manifest = {
        "schema_version": "phase1b-packaging-manifest-v1",
        "checkpoint_path": str(checkpoint_path),
        "promotion_decision": dict(evidence.promotion_decision),
        "audit_fields": dict(evidence.audit_fields),
        "submission_contract": inference_settings,
        "protected_artifacts_included": False,
    }
    evidence.output_dir.mkdir(parents=True, exist_ok=True)
    (evidence.output_dir / "packaging_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
