from __future__ import annotations

from pathlib import Path

import pytest

from phase1b.packaging import Phase1BPackagingEvidence, package_promoted_phase1b_checkpoint


def test_phase1b_packaging_rejects_candidate_without_promotion_evidence(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.npz"
    checkpoint.write_text("fake")

    with pytest.raises(ValueError, match="promotion evidence"):
        package_promoted_phase1b_checkpoint(
            checkpoint_path=checkpoint,
            evidence=Phase1BPackagingEvidence(
                promotion_decision=None,
                smoke_test_passed=True,
                audit_fields={"config": "cfg", "split": "split", "model_hash": "sha256:abc"},
                output_dir=tmp_path / "package",
            ),
        )


def test_phase1b_packaging_requires_passing_smoke_test(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.npz"
    checkpoint.write_text("fake")

    with pytest.raises(ValueError, match="smoke test"):
        package_promoted_phase1b_checkpoint(
            checkpoint_path=checkpoint,
            evidence=Phase1BPackagingEvidence(
                promotion_decision={"accepted": True},
                smoke_test_passed=False,
                audit_fields={"config": "cfg", "split": "split", "model_hash": "sha256:abc"},
                output_dir=tmp_path / "package",
            ),
        )


def test_phase1b_packaging_writes_local_manifest_for_promoted_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.npz"
    checkpoint.write_text("fake")

    manifest = package_promoted_phase1b_checkpoint(
        checkpoint_path=checkpoint,
        evidence=Phase1BPackagingEvidence(
            promotion_decision={"accepted": True, "reasons": []},
            smoke_test_passed=True,
            audit_fields={
                "config": "configs/phase1b/unet.yaml",
                "split": "splits/debug.json",
                "model_hash": "sha256:abc",
                "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
            },
            output_dir=tmp_path / "experiments" / "phase1b" / "package",
        ),
    )

    assert manifest["schema_version"] == "phase1b-packaging-manifest-v1"
    assert manifest["checkpoint_path"] == str(checkpoint)
    assert manifest["submission_contract"] == {"inputs": ["pre_contrast"], "output": "synthetic_post"}
    assert manifest["protected_artifacts_included"] is False
    assert (tmp_path / "experiments" / "phase1b" / "package" / "packaging_manifest.json").exists()


def test_phase1b_packaging_requires_audit_fields(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.npz"
    checkpoint.write_text("fake")

    with pytest.raises(ValueError, match="model_hash"):
        package_promoted_phase1b_checkpoint(
            checkpoint_path=checkpoint,
            evidence=Phase1BPackagingEvidence(
                promotion_decision={"accepted": True},
                smoke_test_passed=True,
                audit_fields={"config": "cfg", "split": "split"},
                output_dir=tmp_path / "package",
            ),
        )
