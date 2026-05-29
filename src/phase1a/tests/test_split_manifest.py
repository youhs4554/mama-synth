from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase1a.splits import load_split_manifest


def _touch_case_files(root: Path, case_id: str) -> dict[str, str]:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    paths = {
        "pre_contrast": case_dir / "pre.mha",
        "ground_truth_post": case_dir / "post.mha",
        "tumor_mask": case_dir / "mask.mha",
    }
    for path in paths.values():
        path.write_text("fake image artifact")
    return {name: str(path) for name, path in paths.items()}


def _touch_relative_case_files(manifest_dir: Path, case_id: str) -> dict[str, str]:
    absolute_paths = _touch_case_files(manifest_dir / "artifacts", case_id)
    return {
        name: str(Path(path).relative_to(manifest_dir))
        for name, path in absolute_paths.items()
    }


def test_split_manifest_validates_deterministic_train_and_holdout_cases(tmp_path: Path) -> None:
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": "center-a",
                        "paths": _touch_case_files(tmp_path, "case-train-001"),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    manifest = load_split_manifest(manifest_path)

    assert manifest.split_intent == "debug_holdout"
    assert manifest.train_case_ids == ["case-train-001"]
    assert manifest.holdout_case_ids == ["case-holdout-001"]


def test_split_manifest_rejects_case_in_both_train_and_holdout(tmp_path: Path) -> None:
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-001-train"),
                    },
                    {
                        "case_id": "case-001",
                        "membership": "holdout",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-001-holdout"),
                    },
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="case-001"):
        load_split_manifest(manifest_path)


def test_split_manifest_resolves_relative_artifact_paths_from_manifest_file(
    tmp_path: Path,
) -> None:
    manifest_dir = tmp_path / "splits"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": _touch_relative_case_files(manifest_dir, "case-train-001"),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_relative_case_files(manifest_dir, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    manifest = load_split_manifest(manifest_path)

    assert manifest.cases[0].pre_contrast_path == manifest_dir / "artifacts" / "case-train-001" / "pre.mha"


def test_split_manifest_keeps_local_metadata_out_of_submission_inputs(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "model_selection_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": "center-a",
                        "paths": _touch_case_files(tmp_path, "case-train-001"),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": "center-b",
                        "paths": _touch_case_files(tmp_path, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    manifest = load_split_manifest(manifest_path)

    assert manifest.submission_input_requirements == ("pre_contrast",)


def test_split_manifest_distinguishes_debug_from_model_selection_holdout(
    tmp_path: Path,
) -> None:
    debug_path = tmp_path / "debug_split.json"
    model_selection_path = tmp_path / "model_selection_split.json"
    base_cases = [
        {
            "case_id": "case-train-001",
            "membership": "train",
            "source_id": "source-a",
            "center_id": None,
            "paths": _touch_case_files(tmp_path, "case-train-001"),
        },
        {
            "case_id": "case-holdout-001",
            "membership": "holdout",
            "source_id": "source-b",
            "center_id": None,
            "paths": _touch_case_files(tmp_path, "case-holdout-001"),
        },
    ]
    debug_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": base_cases,
            }
        )
    )
    model_selection_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "model_selection_holdout",
                "cases": base_cases,
            }
        )
    )

    debug_manifest = load_split_manifest(debug_path)
    model_selection_manifest = load_split_manifest(model_selection_path)

    assert debug_manifest.is_debug_holdout is True
    assert debug_manifest.is_model_selection_holdout is False
    assert model_selection_manifest.is_debug_holdout is False
    assert model_selection_manifest.is_model_selection_holdout is True


def test_split_manifest_rejects_missing_required_case_field(tmp_path: Path) -> None:
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-train-001"),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="source_id"):
        load_split_manifest(manifest_path)


def test_split_manifest_rejects_missing_required_artifact_path(tmp_path: Path) -> None:
    paths = _touch_case_files(tmp_path, "case-train-001")
    paths.pop("tumor_mask")
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": paths,
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="tumor_mask"):
        load_split_manifest(manifest_path)


def test_split_manifest_rejects_unresolved_local_artifact_path(tmp_path: Path) -> None:
    paths = _touch_case_files(tmp_path, "case-train-001")
    Path(paths["pre_contrast"]).unlink()
    manifest_path = tmp_path / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1a.split_manifest.v1",
                "split_intent": "debug_holdout",
                "cases": [
                    {
                        "case_id": "case-train-001",
                        "membership": "train",
                        "source_id": "source-a",
                        "center_id": None,
                        "paths": paths,
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _touch_case_files(tmp_path, "case-holdout-001"),
                    },
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="pre_contrast"):
        load_split_manifest(manifest_path)
