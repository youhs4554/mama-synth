"""Phase 0 metric contract helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class FixedEvaluatorPaths:
    """Local fixed downstream evaluator model paths."""

    classifier: Path
    segmenter: Path


def build_phase0_metric_contract(
    *,
    split_id: str,
    manifest_path: Path,
    identity_metrics: Mapping[str, object],
    fixed_evaluator_paths: FixedEvaluatorPaths,
) -> dict[str, object]:
    """Build a stable Phase 0 metric contract without promoting identity output."""
    return {
        "schema_version": "phase0-metric-contract-v1",
        "split_id": split_id,
        "manifest": str(manifest_path),
        "identity": {
            "role": "lower_bound_benchmark",
            "is_primary_performance_baseline": False,
            "metrics": dict(identity_metrics),
        },
        "primary_performance_baseline": None,
        "fixed_evaluator_paths": {
            "classifier": _path_status(fixed_evaluator_paths.classifier),
            "segmenter": _path_status(fixed_evaluator_paths.segmenter),
        },
    }


def write_phase0_metric_contract(
    contract: Mapping[str, object],
    *,
    json_path: Path,
    csv_path: Path,
) -> None:
    """Write stable JSON and CSV metric summaries for later promotion gates."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_identity_csv(contract, csv_path)


def _path_status(path: Path) -> dict[str, object]:
    return {"path": str(path), "exists": path.exists()}


def _write_identity_csv(contract: Mapping[str, object], csv_path: Path) -> None:
    identity = contract["identity"]
    assert isinstance(identity, dict)
    metrics = identity["metrics"]
    assert isinstance(metrics, dict)
    fieldnames = [
        "split_id",
        "method",
        "role",
        "is_primary_performance_baseline",
        *sorted(str(key) for key in metrics),
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "split_id": contract["split_id"],
                "method": "identity",
                "role": identity["role"],
                "is_primary_performance_baseline": identity["is_primary_performance_baseline"],
                **metrics,
            }
        )
