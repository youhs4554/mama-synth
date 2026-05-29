from __future__ import annotations

import pytest

from phase1a.baselines import validate_baseline_evidence


def test_identity_evidence_is_lower_bound_not_primary_performance_baseline() -> None:
    evidence = validate_baseline_evidence(
        {
            "selected_holdout_split": "splits/debug.json",
            "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 1.0}},
            "primary_performance_baseline": None,
            "reference_gan": {"reproducible": False},
            "promotion": {"deferred": True, "reason": "reference_gan_not_reproducible"},
            "local_ranking_table": [],
        }
    )

    assert evidence.identity_role == "lower_bound_benchmark"
    assert evidence.primary_performance_baseline is None


def test_local_ranking_table_accepts_identity_reference_gan_and_candidates_on_same_split() -> None:
    evidence = validate_baseline_evidence(
        {
            "selected_holdout_split": "splits/model-selection.json",
            "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 4.0}},
            "primary_performance_baseline": "reference_gan",
            "reference_gan": {
                "reproducible": True,
                "selected_holdout_split": "splits/model-selection.json",
                "inference_path": "src/submission/submission-gan/inference.py",
                "model_artifact_identity": "sha256:abc123",
                "metric_summary": {"mse": 2.0, "proxy_rank_mean": 2.0},
            },
            "promotion": {"deferred": False},
            "local_ranking_table": [
                {"name": "identity", "split": "splits/model-selection.json", "proxy_rank_mean": 3.0},
                {"name": "reference_gan", "split": "splits/model-selection.json", "proxy_rank_mean": 2.0},
                {"name": "phase1a-candidate", "split": "splits/model-selection.json", "proxy_rank_mean": 1.0},
            ],
        }
    )

    assert evidence.ranking_names == ("identity", "reference_gan", "phase1a-candidate")


def test_reproducible_reference_gan_requires_split_inference_artifact_and_metrics() -> None:
    with pytest.raises(ValueError, match="reference GAN"):
        validate_baseline_evidence(
            {
                "selected_holdout_split": "splits/model-selection.json",
                "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 1.0}},
                "primary_performance_baseline": "reference_gan",
                "reference_gan": {
                    "reproducible": True,
                    "selected_holdout_split": "splits/model-selection.json",
                    "inference_path": "src/submission/submission-gan/inference.py",
                },
                "promotion": {"deferred": False},
                "local_ranking_table": [],
            }
        )


def test_reproducible_reference_gan_becomes_primary_performance_baseline() -> None:
    with pytest.raises(ValueError, match="primary performance baseline"):
        validate_baseline_evidence(
            {
                "selected_holdout_split": "splits/model-selection.json",
                "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 1.0}},
                "primary_performance_baseline": None,
                "reference_gan": {
                    "reproducible": True,
                    "selected_holdout_split": "splits/model-selection.json",
                    "inference_path": "src/submission/submission-gan/inference.py",
                    "model_artifact_identity": "sha256:abc123",
                    "metric_summary": {"mse": 2.0, "proxy_rank_mean": 2.0},
                },
                "promotion": {"deferred": False},
                "local_ranking_table": [],
            }
        )


def test_unreproducible_reference_gan_requires_promotion_deferred() -> None:
    with pytest.raises(ValueError, match="deferred"):
        validate_baseline_evidence(
            {
                "selected_holdout_split": "splits/model-selection.json",
                "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 1.0}},
                "primary_performance_baseline": None,
                "reference_gan": {"reproducible": False},
                "promotion": {"deferred": False},
                "local_ranking_table": [],
            }
        )


def test_alternative_primary_baseline_requires_human_approval() -> None:
    with pytest.raises(ValueError, match="human approval"):
        validate_baseline_evidence(
            {
                "selected_holdout_split": "splits/model-selection.json",
                "identity": {"role": "lower_bound_benchmark", "metrics": {"mse": 1.0}},
                "primary_performance_baseline": "alternative_baseline",
                "alternative_baseline": {"metric_summary": {"mse": 2.0}},
                "reference_gan": {"reproducible": False},
                "promotion": {"deferred": True},
                "local_ranking_table": [],
            }
        )
