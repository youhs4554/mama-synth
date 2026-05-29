from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase0.bundle import build_phase0_audit_bundle, write_phase0_audit_bundle


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_phase0_audit_bundle_links_evidence_and_weight_staging_decision(tmp_path: Path) -> None:
    evidence_paths = {
        "infrastructure": _write_json(tmp_path / "infrastructure.json", {"schema_version": "phase0-infrastructure-audit-v1"}),
        "debug_artifacts": _write_json(tmp_path / "debug.json", {"schema_version": "phase0-debug-artifacts-audit-v1"}),
        "metric_contract": _write_json(tmp_path / "metrics.json", {"schema_version": "phase0-metric-contract-v1"}),
        "reference_gan": _write_json(tmp_path / "gan.json", {"reference_gan": {"reproducible": False}}),
        "identity_submission_smoke": _write_json(tmp_path / "smoke.json", {"schema_version": "phase0-identity-submission-smoke-v1"}),
    }

    bundle = build_phase0_audit_bundle(
        evidence_paths=evidence_paths,
        weight_staging_decision={
            "strategy": "package_weights_in_container_for_identity_none_required",
            "future_model_rule": "choose exactly one of packaged weights or Grand Challenge model upload path per submission candidate",
        },
    )

    assert bundle["schema_version"] == "phase0-audit-bundle-v1"
    assert bundle["evidence"] == {
        "infrastructure": {"path": str(evidence_paths["infrastructure"]), "exists": True, "schema_version": "phase0-infrastructure-audit-v1"},
        "debug_artifacts": {"path": str(evidence_paths["debug_artifacts"]), "exists": True, "schema_version": "phase0-debug-artifacts-audit-v1"},
        "metric_contract": {"path": str(evidence_paths["metric_contract"]), "exists": True, "schema_version": "phase0-metric-contract-v1"},
        "reference_gan": {"path": str(evidence_paths["reference_gan"]), "exists": True, "schema_version": None},
        "identity_submission_smoke": {"path": str(evidence_paths["identity_submission_smoke"]), "exists": True, "schema_version": "phase0-identity-submission-smoke-v1"},
    }
    assert bundle["weight_staging_decision"]["future_model_rule"].startswith("choose exactly one")

    output_path = tmp_path / "bundle.json"
    write_phase0_audit_bundle(bundle, output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == bundle


def test_phase0_audit_bundle_rejects_missing_required_evidence(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing Phase 0 evidence"):
        build_phase0_audit_bundle(
            evidence_paths={
                "infrastructure": tmp_path / "missing.json",
            },
            weight_staging_decision={"strategy": "none"},
        )
