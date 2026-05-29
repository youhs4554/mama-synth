"""Image artifact I/O for Phase 1A local data and submission paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ImageArtifact:
    array: np.ndarray
    metadata: dict[str, Any]
    case_id: str | None = None
    sitk_image: object | None = None


def read_image_artifact(path: str | Path) -> ImageArtifact:
    """Read a Phase 1A image artifact from NPZ tests or challenge-style MHA."""
    image_path = Path(path)
    if image_path.suffix.lower() == ".npz":
        return _read_npz_artifact(image_path)
    if image_path.suffix.lower() == ".mha":
        return _read_mha_artifact(image_path)
    raise ValueError(f"unsupported image artifact extension: {image_path}")


def write_image_artifact(
    path: str | Path,
    array: np.ndarray,
    *,
    reference: ImageArtifact | None = None,
    case_id: str | None = None,
) -> Path:
    """Write a Phase 1A image artifact, preserving reference metadata when present."""
    image_path = Path(path)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    if image_path.suffix.lower() == ".npz":
        metadata = reference.metadata if reference is not None else {}
        np.savez(image_path, case_id=case_id, array=array.astype(np.float32), metadata=metadata)
        return image_path
    if image_path.suffix.lower() == ".mha":
        sitk = _require_simpleitk()
        output_image = sitk.GetImageFromArray(array.astype(np.float32))
        if reference is not None and reference.sitk_image is not None:
            output_image.CopyInformation(reference.sitk_image)
            for key, value in reference.metadata.get("keys", {}).items():
                output_image.SetMetaData(str(key), str(value))
        if case_id is not None:
            output_image.SetMetaData("case_id", case_id)
        sitk.WriteImage(output_image, str(image_path), useCompression=True)
        return image_path
    raise ValueError(f"unsupported image artifact extension: {image_path}")


def _read_npz_artifact(path: Path) -> ImageArtifact:
    with np.load(path, allow_pickle=True) as artifact:
        case_id = str(artifact["case_id"]) if "case_id" in artifact else None
        metadata = artifact["metadata"].item() if "metadata" in artifact else {}
        return ImageArtifact(
            array=artifact["array"].astype(np.float32),
            metadata=metadata,
            case_id=case_id,
        )


def _read_mha_artifact(path: Path) -> ImageArtifact:
    sitk = _require_simpleitk()
    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image).astype(np.float32)
    if array.ndim == 3 and array.shape[0] == 1:
        array = array[0]
    metadata = {
        "spacing": tuple(image.GetSpacing()),
        "origin": tuple(image.GetOrigin()),
        "direction": tuple(image.GetDirection()),
        "keys": {key: image.GetMetaData(key) for key in image.GetMetaDataKeys()},
    }
    case_id = image.GetMetaData("case_id") if image.HasMetaDataKey("case_id") else None
    return ImageArtifact(array=array, metadata=metadata, case_id=case_id, sitk_image=image)


def _require_simpleitk() -> object:
    try:
        import SimpleITK as sitk
    except ImportError as exc:
        raise RuntimeError(
            "SimpleITK is required for challenge-style .mha Phase 1A I/O"
        ) from exc
    return sitk
