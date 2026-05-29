from __future__ import annotations

from phase1a.promotion import evaluate_promotion_candidate


def _accepted_candidate_summary() -> dict[str, object]:
    return {
        "candidate": "phase1a-candidate",
        "primary_performance_baseline": "reference_gan",
        "metric_groups": {
            "image_fidelity": {"candidate": 0.90, "baseline": 1.00, "higher_is_better": False},
            "tumor_roi_realism": {"candidate": 0.96, "baseline": 1.00, "higher_is_better": False},
            "classification_utility": {"candidate": 0.81, "baseline": 0.80, "higher_is_better": True},
            "segmentation_utility": {"candidate": 0.77, "baseline": 0.75, "higher_is_better": True},
        },
        "local_proxy_rank_mean": {"candidate": 1.5, "baseline": 2.0},
        "config": {"run": {"name": "phase-1a"}},
        "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
        "model_hash": "sha256:abc123",
    }


def test_promotion_gate_accepts_deterministic_toy_metric_summary() -> None:
    decision = evaluate_promotion_candidate(_accepted_candidate_summary())

    assert decision.accepted is True
    assert decision.reasons == ()


def test_promotion_gate_rejects_metric_group_worsening_by_more_than_five_percent() -> None:
    summary = _accepted_candidate_summary()
    summary["metric_groups"]["image_fidelity"] = {
        "candidate": 1.06,
        "baseline": 1.00,
        "higher_is_better": False,
    }

    decision = evaluate_promotion_candidate(summary)

    assert decision.accepted is False
    assert "image_fidelity worsened by more than 5%" in decision.reasons


def test_promotion_gate_requires_all_four_challenge_metric_groups() -> None:
    summary = _accepted_candidate_summary()
    summary["metric_groups"] = {
        "image_fidelity": {"candidate": 0.90, "baseline": 1.00, "higher_is_better": False},
        "tumor_roi_realism": {"candidate": 0.96, "baseline": 1.00, "higher_is_better": False},
    }

    decision = evaluate_promotion_candidate(summary)

    assert decision.accepted is False
    assert "classification_utility metric group is required for promotion" in decision.reasons
    assert "segmentation_utility metric group is required for promotion" in decision.reasons


def test_promotion_gate_requires_at_least_two_non_inferior_metric_groups() -> None:
    summary = _accepted_candidate_summary()
    summary["metric_groups"] = {
        "image_fidelity": {"candidate": 1.06, "baseline": 1.00, "higher_is_better": False},
        "tumor_roi_realism": {"candidate": 1.06, "baseline": 1.00, "higher_is_better": False},
        "classification_utility": {"candidate": 0.75, "baseline": 0.80, "higher_is_better": True},
        "segmentation_utility": {"candidate": 0.70, "baseline": 0.75, "higher_is_better": True},
    }

    decision = evaluate_promotion_candidate(summary)

    assert decision.accepted is False
    assert "at least two metric groups must improve or remain within 5%" in decision.reasons


def test_promotion_gate_requires_local_proxy_rank_mean_improvement() -> None:
    summary = _accepted_candidate_summary()
    summary["local_proxy_rank_mean"] = {"candidate": 2.0, "baseline": 2.0}

    decision = evaluate_promotion_candidate(summary)

    assert decision.accepted is False
    assert "local proxy rank mean must improve" in decision.reasons


def test_promotion_gate_audit_bundle_includes_required_evidence() -> None:
    summary = _accepted_candidate_summary()

    decision = evaluate_promotion_candidate(summary)

    assert decision.audit_bundle == {
        "metrics": summary["metric_groups"],
        "config": summary["config"],
        "inference_settings": summary["inference_settings"],
        "model_hash": "sha256:abc123",
    }


def test_promotion_gate_rejects_candidate_missing_auditable_bundle_evidence() -> None:
    summary = _accepted_candidate_summary()
    summary.pop("config")
    summary.pop("inference_settings")
    summary.pop("model_hash")

    decision = evaluate_promotion_candidate(summary)

    assert decision.accepted is False
    assert "config is required for audit bundle" in decision.reasons
    assert "inference_settings are required for audit bundle" in decision.reasons
    assert "model_hash is required for audit bundle" in decision.reasons
