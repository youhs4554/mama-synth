"""Phase 0 audit bundle helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

REQUIRED_PHASE0_EVIDENCE = (
    "infrastructure",
    "debug_artifacts",
    "metric_contract",
    "reference_gan",
    "identity_submission_smoke",
)


def build_phase0_audit_bundle(
    *,
    evidence_paths: Mapping[str, Path],
    weight_staging_decision: Mapping[str, object],
) -> dict[str, object]:
    """Build a bundle that later phases can depend on for infrastructure evidence."""
    missing = [name for name in REQUIRED_PHASE0_EVIDENCE if name not in evidence_paths or not evidence_paths[name].exists()]
    if missing:
        raise ValueError(f"missing Phase 0 evidence: {', '.join(missing)}")
    return {
        "schema_version": "phase0-audit-bundle-v1",
        "evidence": {
            name: _evidence_status(evidence_paths[name]) for name in REQUIRED_PHASE0_EVIDENCE
        },
        "weight_staging_decision": dict(weight_staging_decision),
    }


def write_phase0_audit_bundle(bundle: Mapping[str, object], output_path: str | Path) -> None:
    """Write a durable Phase 0 audit bundle."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _evidence_status(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version") if isinstance(payload, dict) else None
    return {"path": str(path), "exists": path.exists(), "schema_version": schema_version}
