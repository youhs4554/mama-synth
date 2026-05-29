from __future__ import annotations

import json

from phase0.audit import TestCommandResult, collect_phase0_infrastructure_audit, write_phase0_audit


def test_audit_records_local_test_dataset_stats_and_gpu_assumptions(tmp_path):
    dataset_root = tmp_path / "dataset"
    (dataset_root / "train" / "images").mkdir(parents=True)
    (dataset_root / "train" / "masks").mkdir(parents=True)
    (dataset_root / "train" / "images" / "protected_case_001.mha").write_text("not real image")
    (dataset_root / "train" / "masks" / "protected_case_001.mha").write_text("not real mask")

    stats_path = tmp_path / "training_pre_stats.json"
    stats_path.write_text(json.dumps({"mean": 1.25, "std": 2.5}), encoding="utf-8")

    audit = collect_phase0_infrastructure_audit(
        test_result=TestCommandResult(
            command="PYTHONPATH=src:src/evaluation uv run pytest src/evaluation/tests -q",
            exit_code=0,
            summary="2 passed",
        ),
        dataset_root=dataset_root,
        preprocessing_stats_path=stats_path,
        gpu_info={"available": False, "memory_gb": None, "device_name": None},
    )

    assert audit["schema_version"] == "phase0-infrastructure-audit-v1"
    assert audit["test_baseline"] == {
        "command": "PYTHONPATH=src:src/evaluation uv run pytest src/evaluation/tests -q",
        "exit_code": 0,
        "summary": "2 passed",
    }
    assert audit["dataset"] == {
        "root": str(dataset_root),
        "root_exists": True,
        "top_level_entries": ["train"],
        "file_counts_by_extension": {".mha": 2},
    }
    assert audit["preprocessing_stats"] == {
        "path": str(stats_path),
        "exists": True,
        "keys": ["mean", "std"],
        "mean": 1.25,
        "std": 2.5,
    }
    assert audit["hardware"] == {"available": False, "memory_gb": None, "device_name": None}

    output_path = tmp_path / "phase0_audit.json"
    write_phase0_audit(audit, output_path)
    written = output_path.read_text(encoding="utf-8")
    assert json.loads(written) == audit
    assert "protected_case_001" not in written


def test_audit_records_missing_paths_without_failing(tmp_path):
    audit = collect_phase0_infrastructure_audit(
        test_result=TestCommandResult(command="uv run pytest missing -q", exit_code=4, summary="not run"),
        dataset_root=tmp_path / "missing_dataset",
        preprocessing_stats_path=tmp_path / "missing_stats.json",
        gpu_info={"available": False, "memory_gb": None, "device_name": None},
    )

    assert audit["dataset"] == {
        "root": str(tmp_path / "missing_dataset"),
        "root_exists": False,
        "top_level_entries": [],
        "file_counts_by_extension": {},
    }
    assert audit["preprocessing_stats"] == {
        "path": str(tmp_path / "missing_stats.json"),
        "exists": False,
        "keys": [],
    }
