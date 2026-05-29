from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import SimpleITK as sitk

from phase0.submission_smoke import (
    SubmissionCommandResult,
    build_identity_submission_smoke_evidence,
    write_identity_submission_smoke_evidence,
)


def _write_mha(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = sitk.GetImageFromArray(array.astype(np.float32))
    image.SetSpacing((0.7, 0.8))
    image.SetOrigin((10.0, 20.0))
    image.SetDirection((0.0, 1.0, 1.0, 0.0))
    image.SetMetaData("case_id", "case-001")
    sitk.WriteImage(image, str(path))


def test_identity_submission_smoke_evidence_validates_output_contract(tmp_path: Path) -> None:
    input_path = tmp_path / "input" / "case.mha"
    output_path = tmp_path / "output" / "output.mha"
    _write_mha(input_path, np.array([[1, 2], [3, 4]], dtype=np.float32))
    _write_mha(output_path, np.array([[1, 2], [3, 4]], dtype=np.float32))

    evidence = build_identity_submission_smoke_evidence(
        build=SubmissionCommandResult(command="./do_build.sh", exit_code=0, summary="built"),
        run=SubmissionCommandResult(command="./do_test_run.sh", exit_code=0, summary="ran"),
        save=SubmissionCommandResult(command="./do_save.sh", exit_code=0, summary="saved"),
        input_path=input_path,
        output_path=output_path,
        docker_runtime={"network": "none", "memory": "4g", "read_only_input": True, "writable_output": True},
    )

    assert evidence["schema_version"] == "phase0-identity-submission-smoke-v1"
    assert evidence["commands"] == {
        "build": {"command": "./do_build.sh", "exit_code": 0, "summary": "built"},
        "run": {"command": "./do_test_run.sh", "exit_code": 0, "summary": "ran"},
        "save": {"command": "./do_save.sh", "exit_code": 0, "summary": "saved"},
    }
    assert evidence["output_contract"] == {
        "exists": True,
        "readable": True,
        "shape": [2, 2],
        "dtype": "float32",
        "finite": True,
        "matches_input_shape": True,
        "metadata_preserved": True,
    }
    assert evidence["docker_runtime"] == {
        "network": "none",
        "memory": "4g",
        "read_only_input": True,
        "writable_output": True,
    }

    output_json = tmp_path / "smoke.json"
    write_identity_submission_smoke_evidence(evidence, output_json)
    assert json.loads(output_json.read_text(encoding="utf-8")) == evidence


def test_identity_submission_smoke_evidence_records_failed_command_without_output(tmp_path: Path) -> None:
    missing_output = tmp_path / "missing.mha"
    input_path = tmp_path / "input" / "case.mha"
    _write_mha(input_path, np.ones((2, 2), dtype=np.float32))

    evidence = build_identity_submission_smoke_evidence(
        build=SubmissionCommandResult(command="./do_build.sh", exit_code=1, summary="docker unavailable"),
        run=SubmissionCommandResult(command="./do_test_run.sh", exit_code=1, summary="not run"),
        save=SubmissionCommandResult(command="./do_save.sh", exit_code=1, summary="not run"),
        input_path=input_path,
        output_path=missing_output,
        docker_runtime={"network": "none", "memory": "4g", "read_only_input": True, "writable_output": True},
    )

    assert evidence["output_contract"] == {
        "exists": False,
        "readable": False,
        "shape": None,
        "dtype": None,
        "finite": False,
        "matches_input_shape": False,
        "metadata_preserved": False,
    }
