"""Submission-style packaging helpers for Phase 1A checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from phase1a.image_io import read_image_artifact, write_image_artifact
from phase1a.inference import synthesize_post_from_pre_contrast
from phase1a.run import ConstantResidualPredictor


@dataclass(frozen=True)
class SubmissionSmokeTestResult:
    passed: bool
    max_abs_value: float


@dataclass(frozen=True)
class SubmissionPackage:
    output_path: Path
    smoke_test: SubmissionSmokeTestResult
    submission_ready: bool


def run_phase1a_submission_inference(
    *,
    pre_contrast_path: str | Path,
    checkpoint_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Run submission-style inference with pre-contrast input only."""
    pre_artifact = read_image_artifact(pre_contrast_path)
    with np.load(checkpoint_path) as checkpoint:
        residual = checkpoint["residual"].astype(np.float32)

    synthetic_post = synthesize_post_from_pre_contrast(
        pre_artifact.array,
        predictor=ConstantResidualPredictor(residual),
    )
    return write_image_artifact(
        output_path,
        synthetic_post,
        reference=pre_artifact,
        case_id=pre_artifact.case_id,
    )


def run_phase1a_submission_smoke_test(
    *,
    pre_contrast_path: str | Path,
    output_path: str | Path,
) -> SubmissionSmokeTestResult:
    pre_artifact = read_image_artifact(pre_contrast_path)
    output_artifact = read_image_artifact(output_path)
    pre_shape = pre_artifact.array.shape
    expected_metadata = pre_artifact.metadata
    synthetic_post = output_artifact.array
    metadata = output_artifact.metadata
    max_abs_value = float(np.max(np.abs(synthetic_post)))
    metadata_matches = _metadata_equal(metadata, expected_metadata)
    passed = bool(
        synthetic_post.shape == pre_shape
        and synthetic_post.dtype == np.float32
        and np.isfinite(synthetic_post).all()
        and max_abs_value <= 50
        and metadata_matches
    )
    return SubmissionSmokeTestResult(passed=passed, max_abs_value=max_abs_value)


def package_phase1a_checkpoint(
    *,
    pre_contrast_path: str | Path,
    checkpoint_path: str | Path,
    output_path: str | Path,
) -> SubmissionPackage:
    written_path = run_phase1a_submission_inference(
        pre_contrast_path=pre_contrast_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )
    smoke_test = run_phase1a_submission_smoke_test(
        pre_contrast_path=pre_contrast_path,
        output_path=written_path,
    )
    if not smoke_test.passed:
        raise ValueError("checkpoint is not submission-ready because smoke test failed")
    return SubmissionPackage(
        output_path=written_path,
        smoke_test=smoke_test,
        submission_ready=True,
    )


def _metadata_equal(left: object, right: object) -> bool:
    return left == right
