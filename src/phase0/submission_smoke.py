"""Phase 0 identity submission smoke-test evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import SimpleITK as sitk


@dataclass(frozen=True)
class SubmissionCommandResult:
    """Recorded submission command result."""

    __test__ = False

    command: str
    exit_code: int
    summary: str


def build_identity_submission_smoke_evidence(
    *,
    build: SubmissionCommandResult,
    run: SubmissionCommandResult,
    save: SubmissionCommandResult,
    input_path: Path,
    output_path: Path,
    docker_runtime: Mapping[str, object],
) -> dict[str, object]:
    """Build evidence for identity submission smoke-test commands and output."""
    return {
        "schema_version": "phase0-identity-submission-smoke-v1",
        "commands": {
            "build": _command_result(build),
            "run": _command_result(run),
            "save": _command_result(save),
        },
        "output_contract": _inspect_output_contract(input_path, output_path),
        "docker_runtime": dict(docker_runtime),
    }


def write_identity_submission_smoke_evidence(evidence: Mapping[str, object], output_path: str | Path) -> None:
    """Write durable identity submission smoke-test evidence."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _command_result(result: SubmissionCommandResult) -> dict[str, object]:
    return {"command": result.command, "exit_code": result.exit_code, "summary": result.summary}


def _inspect_output_contract(input_path: Path, output_path: Path) -> dict[str, object]:
    if not output_path.exists():
        return {
            "exists": False,
            "readable": False,
            "shape": None,
            "dtype": None,
            "finite": False,
            "matches_input_shape": False,
            "metadata_preserved": False,
        }
    input_image = sitk.ReadImage(str(input_path))
    output_image = sitk.ReadImage(str(output_path))
    output_array = sitk.GetArrayFromImage(output_image)
    if output_array.ndim == 3 and output_array.shape[0] == 1:
        output_array = output_array[0]
    return {
        "exists": True,
        "readable": True,
        "shape": list(output_array.shape),
        "dtype": str(output_array.dtype),
        "finite": bool(np.isfinite(output_array).all()),
        "matches_input_shape": input_image.GetSize() == output_image.GetSize(),
        "metadata_preserved": _metadata_preserved(input_image, output_image),
    }


def _metadata_preserved(input_image: object, output_image: object) -> bool:
    if input_image.GetSpacing() != output_image.GetSpacing():
        return False
    if input_image.GetOrigin() != output_image.GetOrigin():
        return False
    if input_image.GetDirection() != output_image.GetDirection():
        return False
    for key in input_image.GetMetaDataKeys():
        if not output_image.HasMetaDataKey(key):
            return False
        if input_image.GetMetaData(key) != output_image.GetMetaData(key):
            return False
    return True
