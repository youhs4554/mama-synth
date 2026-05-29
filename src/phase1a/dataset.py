"""Dataset helpers for Phase 1A residual synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from phase1a.image_io import read_image_artifact
from phase1a.splits import Membership, SplitCase, SplitManifest


@dataclass(frozen=True)
class ResidualTrainingSample:
    case_id: str
    pre_contrast: np.ndarray
    ground_truth_post: np.ndarray
    tumor_mask: np.ndarray
    residual_target: np.ndarray
    pre_contrast_path: Path


@dataclass(frozen=True)
class ResidualInferenceSample:
    case_id: str
    pre_contrast: np.ndarray


class ResidualSynthesisDataset:
    """Model-ready residual synthesis samples backed by a split manifest."""

    def __init__(self, cases: tuple[SplitCase, ...]) -> None:
        self._cases = cases

    @classmethod
    def from_manifest(
        cls, manifest: SplitManifest, membership: Membership
    ) -> "ResidualSynthesisDataset":
        cases = tuple(case for case in manifest.cases if case.membership == membership)
        return cls(cases)

    def __len__(self) -> int:
        return len(self._cases)

    def __getitem__(self, index: int) -> ResidualTrainingSample:
        case = self._cases[index]
        pre = _load_case_array(case.pre_contrast_path, case.case_id)
        post = _load_case_array(case.ground_truth_post_path, case.case_id)
        mask = _load_case_array(case.tumor_mask_path, case.case_id)
        return ResidualTrainingSample(
            case_id=case.case_id,
            pre_contrast=pre,
            ground_truth_post=post,
            tumor_mask=mask,
            residual_target=post - pre,
            pre_contrast_path=case.pre_contrast_path,
        )


def load_inference_sample(
    case_id: str, pre_contrast_path: str | Path
) -> ResidualInferenceSample:
    return ResidualInferenceSample(
        case_id=case_id,
        pre_contrast=_load_case_array(Path(pre_contrast_path), case_id),
    )


def _load_case_array(path: Path, expected_case_id: str) -> np.ndarray:
    artifact = read_image_artifact(path)
    if artifact.case_id is not None and artifact.case_id != expected_case_id:
        raise ValueError(
            f"artifact {path} belongs to case {artifact.case_id}, expected {expected_case_id}"
        )
    return artifact.array.astype(np.float32)
