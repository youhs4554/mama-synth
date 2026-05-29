from __future__ import annotations

import json
from pathlib import Path

from phase2.gate import decide_phase2_go_no_go, write_phase2_gate_decision


def test_phase2_gate_records_no_go_when_metric_gap_is_missing(tmp_path: Path) -> None:
    decision = decide_phase2_go_no_go(
        phase1_evidence={"plateau": False, "metric_gap": None},
        available_days=7,
        gpu_memory_gb=20,
        approved_scope="conditional_latent_diffusion",
    )

    assert decision == {
        "schema_version": "phase2-go-no-go-v1",
        "decision": "no-go",
        "reasons": ["Phase 1 evidence does not show a plateau or concrete metric gap"],
        "metric_gap": None,
        "available_days": 7,
        "gpu_memory_gb": 20,
        "approved_scope": "conditional_latent_diffusion",
        "deferred": True,
    }

    output_path = tmp_path / "phase2_gate.json"
    write_phase2_gate_decision(decision, output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == decision


def test_phase2_gate_records_go_when_gap_time_and_resources_are_present() -> None:
    decision = decide_phase2_go_no_go(
        phase1_evidence={"plateau": True, "metric_gap": "FRD remains worse than baseline"},
        available_days=21,
        gpu_memory_gb=20,
        approved_scope="frozen_autoencoder_reconstruction_gate_only",
    )

    assert decision["decision"] == "go"
    assert decision["reasons"] == []
    assert decision["metric_gap"] == "FRD remains worse than baseline"
    assert decision["deferred"] is False


def test_phase2_gate_records_no_go_when_time_or_resources_are_insufficient() -> None:
    decision = decide_phase2_go_no_go(
        phase1_evidence={"plateau": True, "metric_gap": "tumor realism gap"},
        available_days=2,
        gpu_memory_gb=8,
        approved_scope="conditional_latent_diffusion",
    )

    assert decision["decision"] == "no-go"
    assert "Phase 2 has less than 7 available days" in decision["reasons"]
    assert "local GPU memory is below the 20GB planning assumption" in decision["reasons"]
