from __future__ import annotations

import csv
import json
from pathlib import Path

from phase0.metrics import (
    FixedEvaluatorPaths,
    build_phase0_metric_contract,
    write_phase0_metric_contract,
)


def test_metric_contract_records_identity_lower_bound_and_fixed_evaluator_checks(tmp_path: Path) -> None:
    classifier_path = tmp_path / "models" / "classifier.pt"
    segmenter_path = tmp_path / "models" / "segmenter.pt"
    classifier_path.parent.mkdir(parents=True)
    classifier_path.write_text("fake classifier")
    segmenter_path.write_text("fake segmenter")

    contract = build_phase0_metric_contract(
        split_id="debug_holdout_real_v1",
        manifest_path=Path("splits/debug.json"),
        identity_metrics={"mean_mse": 3.4, "mean_ssim": 0.64},
        fixed_evaluator_paths=FixedEvaluatorPaths(
            classifier=classifier_path,
            segmenter=segmenter_path,
        ),
    )

    assert contract["schema_version"] == "phase0-metric-contract-v1"
    assert contract["split_id"] == "debug_holdout_real_v1"
    assert contract["identity"] == {
        "role": "lower_bound_benchmark",
        "is_primary_performance_baseline": False,
        "metrics": {"mean_mse": 3.4, "mean_ssim": 0.64},
    }
    assert contract["primary_performance_baseline"] is None
    assert contract["fixed_evaluator_paths"] == {
        "classifier": {"path": str(classifier_path), "exists": True},
        "segmenter": {"path": str(segmenter_path), "exists": True},
    }


def test_metric_contract_writes_stable_json_and_csv_summary(tmp_path: Path) -> None:
    contract = build_phase0_metric_contract(
        split_id="debug_holdout_real_v1",
        manifest_path=Path("splits/debug.json"),
        identity_metrics={"mean_mse": 3.4, "mean_ssim": 0.64},
        fixed_evaluator_paths=FixedEvaluatorPaths(
            classifier=tmp_path / "missing_classifier.pt",
            segmenter=tmp_path / "missing_segmenter.pt",
        ),
    )

    json_path = tmp_path / "metric_contract.json"
    csv_path = tmp_path / "metric_contract.csv"
    write_phase0_metric_contract(contract, json_path=json_path, csv_path=csv_path)

    assert json.loads(json_path.read_text(encoding="utf-8")) == contract
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows == [
        {
            "split_id": "debug_holdout_real_v1",
            "method": "identity",
            "role": "lower_bound_benchmark",
            "is_primary_performance_baseline": "False",
            "mean_mse": "3.4",
            "mean_ssim": "0.64",
        }
    ]
