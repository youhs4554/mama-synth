"""Split manifest contract for Phase 1A hold-out evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SplitIntent = Literal["debug_holdout", "model_selection_holdout"]
Membership = Literal["train", "holdout"]


@dataclass(frozen=True)
class SplitCase:
    """One local case entry in a Phase 1A split manifest."""

    case_id: str
    membership: Membership
    source_id: str
    center_id: str | None
    pre_contrast_path: Path
    ground_truth_post_path: Path
    tumor_mask_path: Path


@dataclass(frozen=True)
class SplitManifest:
    """Validated Phase 1A split manifest."""

    split_intent: SplitIntent
    cases: tuple[SplitCase, ...]

    @property
    def train_case_ids(self) -> list[str]:
        return [case.case_id for case in self.cases if case.membership == "train"]

    @property
    def holdout_case_ids(self) -> list[str]:
        return [case.case_id for case in self.cases if case.membership == "holdout"]

    @property
    def submission_input_requirements(self) -> tuple[str, ...]:
        return ("pre_contrast",)

    @property
    def is_debug_holdout(self) -> bool:
        return self.split_intent == "debug_holdout"

    @property
    def is_model_selection_holdout(self) -> bool:
        return self.split_intent == "model_selection_holdout"


def load_split_manifest(path: str | Path) -> SplitManifest:
    """Load and validate a Phase 1A split manifest JSON file."""
    manifest_path = Path(path)
    raw = json.loads(manifest_path.read_text())

    if raw.get("schema_version") != "phase1a.split_manifest.v1":
        raise ValueError("split manifest schema_version must be phase1a.split_manifest.v1")

    split_intent = raw.get("split_intent")
    if split_intent not in {"debug_holdout", "model_selection_holdout"}:
        raise ValueError("split_intent must be debug_holdout or model_selection_holdout")

    cases = tuple(_parse_case(item, manifest_path.parent) for item in raw.get("cases", []))
    _reject_duplicate_case_ids(cases)
    if not any(case.membership == "train" for case in cases):
        raise ValueError("split manifest must include at least one train case")
    if not any(case.membership == "holdout" for case in cases):
        raise ValueError("split manifest must include at least one holdout case")

    return SplitManifest(split_intent=split_intent, cases=cases)


def _reject_duplicate_case_ids(cases: tuple[SplitCase, ...]) -> None:
    seen: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            raise ValueError(f"case {case.case_id}: duplicate case_id in split manifest")
        seen.add(case.case_id)


def _parse_case(raw_case: object, base_dir: Path) -> SplitCase:
    if not isinstance(raw_case, dict):
        raise ValueError("each split manifest case must be an object")

    case_id = raw_case.get("case_id")
    membership = raw_case.get("membership")
    source_id = raw_case.get("source_id")
    center_id = raw_case.get("center_id")
    paths = raw_case.get("paths")

    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case_id is required for each split manifest case")
    if membership not in {"train", "holdout"}:
        raise ValueError(f"case {case_id}: membership must be train or holdout")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError(f"case {case_id}: source_id is required")
    if center_id is not None and not isinstance(center_id, str):
        raise ValueError(f"case {case_id}: center_id must be a string or null")
    if not isinstance(paths, dict):
        raise ValueError(f"case {case_id}: paths are required")

    return SplitCase(
        case_id=case_id,
        membership=membership,
        source_id=source_id,
        center_id=center_id,
        pre_contrast_path=_required_existing_path(paths, "pre_contrast", case_id, base_dir),
        ground_truth_post_path=_required_existing_path(
            paths, "ground_truth_post", case_id, base_dir
        ),
        tumor_mask_path=_required_existing_path(paths, "tumor_mask", case_id, base_dir),
    )


def _required_existing_path(
    paths: dict[object, object], key: str, case_id: str, base_dir: Path
) -> Path:
    value = paths.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"case {case_id}: paths.{key} is required")
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.exists():
        raise ValueError(f"case {case_id}: paths.{key} does not resolve locally: {path}")
    return path
