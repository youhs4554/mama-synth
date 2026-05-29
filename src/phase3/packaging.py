"""Phase 3 final packaging validation."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import SimpleITK as sitk

EXPECTED_OUTPUT_SLUG = "synthetic-contrast-dce-mri-slice-breast"


def validate_final_packaging(
    *,
    output_path: Path,
    output_slug: str,
    weight_strategy: Mapping[str, object],
    runtime_checks: Mapping[str, object],
) -> dict[str, object]:
    """Validate final package evidence for Grand Challenge runtime constraints."""
    if output_slug != EXPECTED_OUTPUT_SLUG:
        raise ValueError("final packaging output slug does not match Grand Challenge contract")
    packaged = bool(weight_strategy.get("packaged_weights"))
    uploaded = bool(weight_strategy.get("model_upload_path"))
    if packaged == uploaded:
        raise ValueError("final packaging requires exactly one model-weight loading strategy")
    if runtime_checks.get("network") != "none":
        raise ValueError("final packaging runtime network must be none")
    if runtime_checks.get("non_root") is not True:
        raise ValueError("final packaging requires non-root runtime")
    if runtime_checks.get("writable_output") is not True:
        raise ValueError("final packaging requires writable output")

    image = sitk.ReadImage(str(output_path))
    array = sitk.GetArrayFromImage(image)
    if array.ndim == 3 and array.shape[0] == 1:
        array = array[0]
    return {
        "schema_version": "phase3-final-packaging-v1",
        "output": {
            "slug": output_slug,
            "readable_mha": output_path.suffix.lower() == ".mha",
            "dtype": str(array.dtype),
            "finite": bool(np.isfinite(array).all()),
        },
        "weight_strategy": dict(weight_strategy),
        "runtime_checks": dict(runtime_checks),
    }
