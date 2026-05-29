"""Phase 0 debug artifact audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from phase1a.image_io import ImageArtifact, read_image_artifact
from phase1a.splits import SplitCase, load_split_manifest

ARTIFACT_ROLES = ("ground_truth_post", "pre_contrast", "tumor_mask")
LOCAL_ONLY_ARTIFACTS = ("ground_truth_post", "tumor_mask")


def inspect_phase0_debug_artifacts(manifest_path: str | Path) -> dict[str, object]:
    """Inspect challenge-like debug MHA artifacts without embedding image data."""
    manifest = load_split_manifest(manifest_path)
    case_summaries: list[dict[str, object]] = []
    all_artifacts_are_mha = True
    all_cases_have_matching_shape_and_metadata = True

    for case in manifest.cases:
        artifacts = _read_case_artifacts(case)
        if any(path.suffix.lower() != ".mha" for path in _case_paths(case).values()):
            all_artifacts_are_mha = False
        if not _case_artifacts_match(artifacts):
            all_cases_have_matching_shape_and_metadata = False
        case_summaries.append(
            {
                "case_id": case.case_id,
                "membership": case.membership,
                "shape": list(artifacts["pre_contrast"].array.shape),
            }
        )

    return {
        "schema_version": "phase0-debug-artifacts-audit-v1",
        "split_intent": manifest.split_intent,
        "case_counts": {
            "train": len(manifest.train_case_ids),
            "holdout": len(manifest.holdout_case_ids),
        },
        "artifact_roles": sorted(ARTIFACT_ROLES),
        "submission_input_requirements": list(manifest.submission_input_requirements),
        "local_only_artifacts": list(LOCAL_ONLY_ARTIFACTS),
        "center_ids": sorted({case.center_id for case in manifest.cases if case.center_id is not None}),
        "source_ids": sorted({case.source_id for case in manifest.cases}),
        "all_artifacts_are_mha": all_artifacts_are_mha,
        "all_cases_have_matching_shape_and_metadata": all_cases_have_matching_shape_and_metadata,
        "cases": case_summaries,
    }


def write_phase0_debug_artifact_audit(audit: Mapping[str, object], output_path: str | Path) -> None:
    """Write a durable JSON audit artifact for Phase 0 debug artifacts."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_case_artifacts(case: SplitCase) -> dict[str, ImageArtifact]:
    return {role: read_image_artifact(path) for role, path in _case_paths(case).items()}


def _case_paths(case: SplitCase) -> dict[str, Path]:
    return {
        "pre_contrast": case.pre_contrast_path,
        "ground_truth_post": case.ground_truth_post_path,
        "tumor_mask": case.tumor_mask_path,
    }


def _case_artifacts_match(artifacts: Mapping[str, ImageArtifact]) -> bool:
    reference = artifacts["pre_contrast"]
    reference_shape = reference.array.shape
    reference_metadata = _spatial_metadata(reference)
    for artifact in artifacts.values():
        if artifact.array.shape != reference_shape:
            return False
        if _spatial_metadata(artifact) != reference_metadata:
            return False
    return True


def _spatial_metadata(artifact: ImageArtifact) -> dict[str, object]:
    return {
        "spacing": artifact.metadata.get("spacing"),
        "origin": artifact.metadata.get("origin"),
        "direction": artifact.metadata.get("direction"),
    }
