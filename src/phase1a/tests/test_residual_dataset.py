from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from phase1a.dataset import ResidualSynthesisDataset, load_inference_sample
from phase1a.splits import load_split_manifest


def _write_fake_artifact(path: Path, case_id: str, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, case_id=case_id, array=values.astype(np.float32))


def _write_case(
    root: Path, case_id: str, pre: np.ndarray, post: np.ndarray, mask: np.ndarray
) -> dict[str, str]:
    case_dir = root / case_id
    paths = {
        "pre_contrast": case_dir / "pre.npz",
        "ground_truth_post": case_dir / "post.npz",
        "tumor_mask": case_dir / "mask.npz",
    }
    _write_fake_artifact(paths["pre_contrast"], case_id, pre)
    _write_fake_artifact(paths["ground_truth_post"], case_id, post)
    _write_fake_artifact(paths["tumor_mask"], case_id, mask)
    return {name: str(path) for name, path in paths.items()}


def _write_manifest(tmp_path: Path) -> Path:
    pre = np.array([[1, 2], [3, 4]], dtype=np.float32)
    post = np.array([[2, 4], [6, 8]], dtype=np.float32)
    mask = np.array([[0, 1], [1, 0]], dtype=np.float32)
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
                        "paths": _write_case(tmp_path, "case-train-001", pre, post, mask),
                    },
                    {
                        "case_id": "case-holdout-001",
                        "membership": "holdout",
                        "source_id": "source-b",
                        "center_id": None,
                        "paths": _write_case(tmp_path, "case-holdout-001", pre, post, mask),
                    },
                ],
            }
        )
    )
    return manifest_path


def test_residual_synthesis_dataset_loads_train_cases_from_split_manifest(
    tmp_path: Path,
) -> None:
    manifest = load_split_manifest(_write_manifest(tmp_path))

    dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="train")

    assert len(dataset) == 1
    assert dataset[0].case_id == "case-train-001"


def test_training_sample_includes_arrays_and_residual_target(tmp_path: Path) -> None:
    manifest = load_split_manifest(_write_manifest(tmp_path))
    dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="train")

    sample = dataset[0]

    np.testing.assert_array_equal(
        sample.pre_contrast,
        np.array([[1, 2], [3, 4]], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        sample.ground_truth_post,
        np.array([[2, 4], [6, 8]], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        sample.tumor_mask,
        np.array([[0, 1], [1, 0]], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        sample.residual_target,
        np.array([[1, 2], [3, 4]], dtype=np.float32),
    )


def test_inference_sample_uses_pre_contrast_only(tmp_path: Path) -> None:
    pre_path = tmp_path / "case-001" / "pre.npz"
    _write_fake_artifact(
        pre_path,
        "case-001",
        np.array([[1, 2], [3, 4]], dtype=np.float32),
    )

    sample = load_inference_sample(case_id="case-001", pre_contrast_path=pre_path)

    assert sample.case_id == "case-001"
    np.testing.assert_array_equal(
        sample.pre_contrast,
        np.array([[1, 2], [3, 4]], dtype=np.float32),
    )


def test_training_sample_rejects_mismatched_case_identity(tmp_path: Path) -> None:
    pre = np.array([[1, 2], [3, 4]], dtype=np.float32)
    post = np.array([[2, 4], [6, 8]], dtype=np.float32)
    mask = np.array([[0, 1], [1, 0]], dtype=np.float32)
    paths = _write_case(tmp_path, "case-train-001", pre, post, mask)
    _write_fake_artifact(Path(paths["tumor_mask"]), "other-case", mask)
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
                        "paths": _write_case(tmp_path, "case-holdout-001", pre, post, mask),
                    },
                ],
            }
        )
    )
    dataset = ResidualSynthesisDataset.from_manifest(
        load_split_manifest(manifest_path),
        membership="train",
    )

    with pytest.raises(ValueError, match="other-case"):
        dataset[0]
