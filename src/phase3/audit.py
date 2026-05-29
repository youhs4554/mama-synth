"""Phase 3 final candidate audit-bundle validation."""

from __future__ import annotations

from typing import Mapping

REQUIRED_FINAL_AUDIT_FIELDS = (
    "candidate_name",
    "config",
    "split",
    "metrics",
    "inference_settings",
    "model_hash",
    "container_version",
    "resource_provenance",
    "smoke_test_logs",
)


def validate_final_candidate_audit_bundle(bundle: Mapping[str, object]) -> dict[str, object]:
    """Validate that a candidate can enter final Phase 3 selection."""
    missing = [field for field in REQUIRED_FINAL_AUDIT_FIELDS if field not in bundle]
    if missing:
        raise ValueError(f"final candidate audit bundle missing: {', '.join(missing)}")
    if bundle.get("protected_data_embedded") is True:
        raise ValueError("final candidate audit bundle must not embed protected data")
    inference_settings = bundle.get("inference_settings")
    if inference_settings != {"inputs": ["pre_contrast"], "output": "synthetic_post"}:
        raise ValueError("final candidate must preserve pre-contrast-only synthetic post contract")
    return {
        "candidate_name": bundle["candidate_name"],
        "complete": True,
        "missing_fields": [],
    }
