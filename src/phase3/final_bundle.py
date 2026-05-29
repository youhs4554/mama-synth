"""Phase 3 final decision and submission evidence bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

REQUIRED_FINAL_AUDIT_FIELDS = (
    "config",
    "split",
    "metrics",
    "inference_settings",
    "model_hash",
    "container_version",
)


def build_final_submission_evidence_bundle(
    *,
    decision_record: Mapping[str, object],
    audit_bundle: Mapping[str, object],
    resource_provenance: Mapping[str, object],
    smoke_test_logs: Sequence[str],
    official_submission_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build the final evidence bundle for a selected submission candidate."""
    _validate_decision_record(decision_record)
    _validate_audit_bundle(audit_bundle)
    return {
        "schema_version": "phase3-final-evidence-bundle-v1",
        "decision_record": dict(decision_record),
        "audit_bundle": dict(audit_bundle),
        "resource_provenance": dict(resource_provenance),
        "smoke_test_logs": list(smoke_test_logs),
        "official_submission_records": [dict(record) for record in official_submission_records],
        "top3_readiness": _top3_readiness(resource_provenance, smoke_test_logs),
    }


def write_final_submission_evidence_bundle(bundle: Mapping[str, object], output_path: str | Path) -> None:
    """Write a durable final evidence bundle."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_decision_record(decision_record: Mapping[str, object]) -> None:
    if not decision_record.get("selected_candidate"):
        raise ValueError("final evidence bundle requires selected_candidate")
    if not decision_record.get("why_selected"):
        raise ValueError("final evidence bundle requires why_selected decision rationale")
    if "alternatives_considered" not in decision_record:
        raise ValueError("final evidence bundle requires alternatives_considered")


def _validate_audit_bundle(audit_bundle: Mapping[str, object]) -> None:
    for field in REQUIRED_FINAL_AUDIT_FIELDS:
        if not audit_bundle.get(field):
            raise ValueError(f"final evidence bundle audit_bundle requires {field}")


def _top3_readiness(resource_provenance: Mapping[str, object], smoke_test_logs: Sequence[str]) -> dict[str, bool]:
    external_data = resource_provenance.get("external_data", [])
    pretrained_weights = resource_provenance.get("pretrained_weights", [])
    return {
        "clean_code_provenance": bool(resource_provenance.get("code")),
        "clean_external_data_provenance": _all_entries_documented(external_data),
        "clean_pretrained_weight_provenance": _all_entries_documented(pretrained_weights),
        "training_inference_commands_recorded": bool(smoke_test_logs),
    }


def _all_entries_documented(entries: object) -> bool:
    if not isinstance(entries, list):
        return False
    return all(bool(entry) and entry != "unknown" for entry in entries)
