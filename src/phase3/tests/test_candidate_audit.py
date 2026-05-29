from __future__ import annotations

import pytest

from phase3.audit import validate_final_candidate_audit_bundle


def _valid_bundle() -> dict[str, object]:
    return {
        "candidate_name": "phase1b-unet",
        "config": "configs/phase1b/unet.yaml",
        "split": "splits/debug.json",
        "metrics": {"image_fidelity": {"candidate": 0.9, "baseline": 1.0, "higher_is_better": False}},
        "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
        "model_hash": "sha256:abc",
        "container_version": "phase1b-v1",
        "resource_provenance": {"weights": "local checkpoint", "external_data": []},
        "smoke_test_logs": ["container smoke passed"],
        "protected_data_embedded": False,
    }


def test_final_candidate_audit_bundle_accepts_complete_candidate() -> None:
    audit = validate_final_candidate_audit_bundle(_valid_bundle())

    assert audit["candidate_name"] == "phase1b-unet"
    assert audit["complete"] is True
    assert audit["missing_fields"] == []


def test_final_candidate_audit_bundle_rejects_missing_required_artifact() -> None:
    bundle = _valid_bundle()
    del bundle["model_hash"]

    with pytest.raises(ValueError, match="model_hash"):
        validate_final_candidate_audit_bundle(bundle)


def test_final_candidate_audit_bundle_rejects_protected_data_embedding() -> None:
    bundle = _valid_bundle()
    bundle["protected_data_embedded"] = True

    with pytest.raises(ValueError, match="protected data"):
        validate_final_candidate_audit_bundle(bundle)


def test_final_candidate_audit_bundle_rejects_wrong_submission_contract() -> None:
    bundle = _valid_bundle()
    bundle["inference_settings"] = {"inputs": ["pre_contrast", "tumor_mask"], "output": "latent"}

    with pytest.raises(ValueError, match="pre-contrast-only synthetic post"):
        validate_final_candidate_audit_bundle(bundle)
