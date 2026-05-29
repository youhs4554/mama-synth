from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import SimpleITK as sitk

from phase0.debug_artifacts import inspect_phase0_debug_artifacts, write_phase0_debug_artifact_audit


def _write_mha(path: Path, array: np.ndarray, *, case_id: str, source_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = sitk.GetImageFromArray(array.astype(np.float32))
    image.SetSpacing((0.7, 0.8))
    image.SetOrigin((10.0, 20.0))
    image.SetDirection((0.0, 1.0, 1.0, 0.0))
    image.SetMetaData("case_id", case_id)
    image.SetMetaData("source_id", source_id)
    sitk.WriteImage(image, str(path))


def _case(root: Path, case_id: str, membership: str, source_id: str, center_id: str | None) -> dict[str, object]:
    case_root = root / case_id
    _write_mha(case_root / "pre.mha", np.array([[1, 2], [3, 4]]), case_id=case_id, source_id=source_id)
    _write_mha(case_root / "post.mha", np.array([[2, 3], [4, 5]]), case_id=case_id, source_id=source_id)
    _write_mha(case_root / "mask.mha", np.array([[0, 1], [0, 0]]), case_id=case_id, source_id=source_id)
    return {
        "case_id": case_id,
        "membership": membership,
        "source_id": source_id,
        "center_id": center_id,
        "paths": {
            "pre_contrast": str(case_root / "pre.mha"),
            "ground_truth_post": str(case_root / "post.mha"),
            "tumor_mask": str(case_root / "mask.mha"),
        },
    }


def test_debug_artifact_audit_verifies_mha_paths_metadata_and_local_mask_usage(tmp_path: Path) -> None:
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    _case(tmp_path / "artifacts", "case-train", "train", "source-a", "center-a"),
                    _case(tmp_path / "artifacts", "case-holdout", "holdout", "source-b", None),
                ],
            }
        ),
        encoding="utf-8",
    )

    audit = inspect_phase0_debug_artifacts(manifest_path)

    assert audit["schema_version"] == "phase0-debug-artifacts-audit-v1"
    assert audit["split_intent"] == "debug_holdout"
    assert audit["case_counts"] == {"train": 1, "holdout": 1}
    assert audit["artifact_roles"] == ["ground_truth_post", "pre_contrast", "tumor_mask"]
    assert audit["submission_input_requirements"] == ["pre_contrast"]
    assert audit["local_only_artifacts"] == ["ground_truth_post", "tumor_mask"]
    assert audit["center_ids"] == ["center-a"]
    assert audit["source_ids"] == ["source-a", "source-b"]
    assert audit["all_artifacts_are_mha"] is True
    assert audit["all_cases_have_matching_shape_and_metadata"] is True
    assert audit["cases"] == [
        {"case_id": "case-train", "membership": "train", "shape": [2, 2]},
        {"case_id": "case-holdout", "membership": "holdout", "shape": [2, 2]},
    ]

    output_path = tmp_path / "debug_artifacts_audit.json"
    write_phase0_debug_artifact_audit(audit, output_path)
    written = output_path.read_text(encoding="utf-8")
    assert json.loads(written) == audit
    assert "case-train/pre.mha" not in written
