from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase3.final_bundle import build_final_submission_evidence_bundle, write_final_submission_evidence_bundle


def _audit_bundle() -> dict[str, object]:
    return {
        "config": "configs/phase1b/unet.yaml",
        "split": "splits/debug.json",
        "metrics": {"image_fidelity": {"candidate": 0.9, "baseline": 1.0}},
        "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
        "model_hash": "sha256:abc",
        "container_version": "phase1b-v1",
    }


def test_final_evidence_bundle_records_selected_candidate_decision_and_audit_fields(tmp_path: Path) -> None:
    bundle = build_final_submission_evidence_bundle(
        decision_record={
            "selected_candidate": "phase1b-unet",
            "why_selected": "best local proxy rank mean while preserving all four metric groups within non-inferiority margin",
            "alternatives_considered": ["identity", "constant_residual"],
        },
        audit_bundle=_audit_bundle(),
        resource_provenance={"code": "local git workspace", "external_data": [], "pretrained_weights": ["phase1b-v1 local checkpoint"]},
        smoke_test_logs=["phase1b container smoke passed"],
        official_submission_records=[],
    )

    assert bundle["schema_version"] == "phase3-final-evidence-bundle-v1"
    assert bundle["decision_record"]["selected_candidate"] == "phase1b-unet"
    assert bundle["audit_bundle"] == _audit_bundle()
    assert bundle["top3_readiness"]["clean_code_provenance"] is True
    assert bundle["top3_readiness"]["clean_external_data_provenance"] is True
    assert bundle["top3_readiness"]["clean_pretrained_weight_provenance"] is True

    output_path = tmp_path / "final_bundle.json"
    write_final_submission_evidence_bundle(bundle, output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == bundle


def test_final_evidence_bundle_rejects_null_selected_candidate() -> None:
    with pytest.raises(ValueError, match="selected_candidate"):
        build_final_submission_evidence_bundle(
            decision_record={"selected_candidate": None, "reason": "no promoted candidates available"},
            audit_bundle=_audit_bundle(),
            resource_provenance={"code": "local git workspace", "external_data": [], "pretrained_weights": []},
            smoke_test_logs=["smoke passed"],
            official_submission_records=[],
        )


def test_final_evidence_bundle_rejects_missing_audit_fields() -> None:
    audit = _audit_bundle()
    audit["model_hash"] = None

    with pytest.raises(ValueError, match="model_hash"):
        build_final_submission_evidence_bundle(
            decision_record={"selected_candidate": "phase1b-unet", "why_selected": "best", "alternatives_considered": []},
            audit_bundle=audit,
            resource_provenance={"code": "local git workspace", "external_data": [], "pretrained_weights": []},
            smoke_test_logs=["smoke passed"],
            official_submission_records=[],
        )


def test_final_evidence_bundle_marks_missing_provenance_not_ready() -> None:
    bundle = build_final_submission_evidence_bundle(
        decision_record={"selected_candidate": "candidate-a", "why_selected": "best", "alternatives_considered": []},
        audit_bundle=_audit_bundle(),
        resource_provenance={"code": "", "external_data": ["unknown"], "pretrained_weights": [""]},
        smoke_test_logs=[],
        official_submission_records=[{"phase": "Debug", "status": "passed"}],
    )

    assert bundle["top3_readiness"] == {
        "clean_code_provenance": False,
        "clean_external_data_provenance": False,
        "clean_pretrained_weight_provenance": False,
        "training_inference_commands_recorded": False,
    }
