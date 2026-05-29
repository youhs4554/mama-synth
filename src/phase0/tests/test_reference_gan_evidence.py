from __future__ import annotations

import json
from pathlib import Path

from phase0.reference_gan import (
    build_reference_gan_evidence,
    write_reference_gan_evidence,
)
from phase1a.baselines import validate_baseline_evidence


def test_reference_gan_evidence_accepts_explicit_unreproducible_blocker(tmp_path: Path) -> None:
    evidence = build_reference_gan_evidence(
        selected_holdout_split="splits/phase1a_debug_holdout_real_v1.json",
        reproducible=False,
        blocker="missing MODEL_WEIGHTS_DIR/30_net_G.pth",
        attempted_command="MODEL_WEIGHTS_DIR=/missing ./do_build.sh",
    )

    assert evidence["reference_gan"] == {
        "reproducible": False,
        "blocker": "missing MODEL_WEIGHTS_DIR/30_net_G.pth",
        "attempted_command": "MODEL_WEIGHTS_DIR=/missing ./do_build.sh",
    }
    assert evidence["promotion"] == {
        "deferred": True,
        "reason": "reference_gan_not_reproducible",
    }
    assert evidence["primary_performance_baseline"] is None
    validated = validate_baseline_evidence(evidence)
    assert validated.primary_performance_baseline is None

    output_path = tmp_path / "reference_gan_evidence.json"
    write_reference_gan_evidence(evidence, output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == evidence


def test_reference_gan_evidence_records_reproducible_run_fields() -> None:
    evidence = build_reference_gan_evidence(
        selected_holdout_split="splits/model_selection.json",
        reproducible=True,
        inference_path="src/submission/submission-gan/inference.py",
        model_artifact_identity="sha256:abc123",
        metric_summary={"proxy_rank_mean": 2.0, "mse": 1.5},
    )

    assert evidence["reference_gan"] == {
        "reproducible": True,
        "selected_holdout_split": "splits/model_selection.json",
        "inference_path": "src/submission/submission-gan/inference.py",
        "model_artifact_identity": "sha256:abc123",
        "metric_summary": {"proxy_rank_mean": 2.0, "mse": 1.5},
    }
    assert evidence["primary_performance_baseline"] == "reference_gan"
    assert evidence["promotion"] == {"deferred": False}
    validated = validate_baseline_evidence(evidence)
    assert validated.primary_performance_baseline == "reference_gan"
