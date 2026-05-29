"""Phase 2 latent diffusion go/no-go gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

MIN_PHASE2_DAYS = 7
MIN_GPU_MEMORY_GB = 20


def decide_phase2_go_no_go(
    *,
    phase1_evidence: Mapping[str, object],
    available_days: int,
    gpu_memory_gb: int | float,
    approved_scope: str,
) -> dict[str, object]:
    """Decide whether Phase 2 should start from Phase 1 evidence and resources."""
    reasons: list[str] = []
    metric_gap = phase1_evidence.get("metric_gap")
    plateau = phase1_evidence.get("plateau") is True
    if not plateau and not metric_gap:
        reasons.append("Phase 1 evidence does not show a plateau or concrete metric gap")
    if available_days < MIN_PHASE2_DAYS:
        reasons.append("Phase 2 has less than 7 available days")
    if float(gpu_memory_gb) < MIN_GPU_MEMORY_GB:
        reasons.append("local GPU memory is below the 20GB planning assumption")
    decision = "no-go" if reasons else "go"
    return {
        "schema_version": "phase2-go-no-go-v1",
        "decision": decision,
        "reasons": reasons,
        "metric_gap": metric_gap,
        "available_days": available_days,
        "gpu_memory_gb": gpu_memory_gb,
        "approved_scope": approved_scope,
        "deferred": decision == "no-go",
    }


def write_phase2_gate_decision(decision: Mapping[str, object], output_path: str | Path) -> None:
    """Write a durable Phase 2 gate decision."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
