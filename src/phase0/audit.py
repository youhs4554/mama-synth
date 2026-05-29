"""Phase 0 infrastructure audit artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class TestCommandResult:
    """Recorded result for a local validation command."""

    __test__ = False

    command: str
    exit_code: int
    summary: str


def collect_phase0_infrastructure_audit(
    *,
    test_result: TestCommandResult,
    dataset_root: Path,
    preprocessing_stats_path: Path,
    gpu_info: Mapping[str, object],
) -> dict[str, object]:
    """Collect protected-data-safe Phase 0 infrastructure evidence."""
    return {
        "schema_version": "phase0-infrastructure-audit-v1",
        "test_baseline": {
            "command": test_result.command,
            "exit_code": test_result.exit_code,
            "summary": test_result.summary,
        },
        "dataset": _summarize_dataset_root(Path(dataset_root)),
        "preprocessing_stats": _summarize_preprocessing_stats(Path(preprocessing_stats_path)),
        "hardware": dict(gpu_info),
    }


def write_phase0_audit(audit: Mapping[str, object], output_path: Path) -> None:
    """Write a durable JSON audit artifact."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _summarize_dataset_root(dataset_root: Path) -> dict[str, object]:
    root_exists = dataset_root.exists()
    top_level_entries: list[str] = []
    file_counts_by_extension: dict[str, int] = {}
    if root_exists:
        top_level_entries = sorted(path.name for path in dataset_root.iterdir())
        for path in dataset_root.rglob("*"):
            if path.is_file():
                file_counts_by_extension[path.suffix] = file_counts_by_extension.get(path.suffix, 0) + 1
    return {
        "root": str(dataset_root),
        "root_exists": root_exists,
        "top_level_entries": top_level_entries,
        "file_counts_by_extension": dict(sorted(file_counts_by_extension.items())),
    }


def _summarize_preprocessing_stats(stats_path: Path) -> dict[str, object]:
    summary: dict[str, object] = {"path": str(stats_path), "exists": stats_path.exists()}
    if not stats_path.exists():
        summary["keys"] = []
        return summary
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    if not isinstance(stats, dict):
        raise ValueError("preprocessing stats must be a JSON object")
    summary["keys"] = sorted(str(key) for key in stats)
    for key in ("mean", "std"):
        if key in stats:
            summary[key] = stats[key]
    return summary
