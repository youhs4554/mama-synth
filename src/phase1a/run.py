"""Minimal Phase 1A train/evaluate loop."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from phase1a.config import validate_phase1a_config
from phase1a.dataset import ResidualSynthesisDataset
from phase1a.image_io import read_image_artifact, write_image_artifact
from phase1a.inference import synthesize_post_from_pre_contrast
from phase1a.losses import residual_l1, tumor_roi_weighted_residual_l1
from phase1a.splits import load_split_manifest


@dataclass(frozen=True)
class Phase1ARunResult:
    checkpoint_path: Path
    prediction_paths: dict[str, Path]
    summary_path: Path
    loss_history: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class ConstantResidualPredictor:
    residual: np.ndarray

    def predict(self, pre_contrast: np.ndarray) -> np.ndarray:
        return np.broadcast_to(self.residual, pre_contrast.shape).astype(np.float32)


def load_phase1a_config_file(path: str | Path) -> Mapping[str, object]:
    """Load a Phase 1A experiment config from JSON or YAML."""
    config_path = Path(path)
    if config_path.suffix in {".yaml", ".yml"}:
        import yaml

        loaded = yaml.safe_load(config_path.read_text())
    elif config_path.suffix == ".json":
        loaded = json.loads(config_path.read_text())
    else:
        raise ValueError("Phase 1A config file must be .json, .yaml, or .yml")
    if not isinstance(loaded, Mapping):
        raise ValueError("Phase 1A config file must contain an object")
    return loaded


def run_phase1a_train_evaluate(raw_config: Mapping[str, object]) -> Phase1ARunResult:
    """Run a smoke-scale residual train/evaluate cycle on local manifest data."""
    config = validate_phase1a_config(raw_config)
    run_section = config.raw["run"]
    data_section = config.raw["data"]
    train_section = config.raw["train"]
    assert isinstance(run_section, dict)
    assert isinstance(data_section, dict)
    assert isinstance(train_section, dict)

    output_dir = Path(str(run_section.get("output_dir", "phase1a-run")))
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.npz"
    predictions_dir = output_dir / "predictions"
    predictions_dir.mkdir(exist_ok=True)

    split_manifest_path = Path(str(data_section["split_manifest"]))
    manifest = load_split_manifest(split_manifest_path)

    train_dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="train")
    trained_residual, loss_history = _train_tumor_aware_constant_residual_model(
        train_dataset,
        max_epochs=int(train_section.get("max_epochs", 1)),
    )
    np.savez(
        checkpoint_path,
        residual=trained_residual,
        loss_history=np.array(loss_history, dtype=object),
    )

    predictor = ConstantResidualPredictor(trained_residual)
    holdout_dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="holdout")
    prediction_paths: dict[str, Path] = {}
    for index in range(len(holdout_dataset)):
        sample = holdout_dataset[index]
        synthetic_post = synthesize_post_from_pre_contrast(
            sample.pre_contrast,
            predictor=predictor,
            evaluation_mask=sample.tumor_mask,
        )
        prediction_extension = sample.pre_contrast_path.suffix if sample.pre_contrast_path.suffix == ".mha" else ".npz"
        prediction_path = predictions_dir / f"{sample.case_id}{prediction_extension}"
        write_image_artifact(
            prediction_path,
            synthetic_post,
            reference=read_image_artifact(sample.pre_contrast_path),
            case_id=sample.case_id,
        )
        prediction_paths[sample.case_id] = prediction_path

    summary_path = output_dir / "run_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "config": config.raw,
                "split_manifest": str(split_manifest_path),
                "seed": run_section.get("seed"),
                "checkpoint": str(checkpoint_path),
                "inference_settings": {
                    "inputs": ["pre_contrast"],
                    "output": "synthetic_post",
                },
                "loss_history": list(loss_history),
            },
            indent=2,
        )
    )

    return Phase1ARunResult(
        checkpoint_path=checkpoint_path,
        prediction_paths=prediction_paths,
        summary_path=summary_path,
        loss_history=loss_history,
    )


def _train_tumor_aware_constant_residual_model(
    dataset: ResidualSynthesisDataset,
    *,
    max_epochs: int,
    tumor_weight: float = 3.0,
) -> tuple[np.ndarray, tuple[dict[str, float], ...]]:
    samples = [dataset[index] for index in range(len(dataset))]
    residual_targets = np.stack([sample.residual_target for sample in samples])
    tumor_masks = np.stack([sample.tumor_mask for sample in samples]).astype(bool)
    weights = np.ones_like(residual_targets, dtype=np.float32)
    weights = weights + tumor_masks * (tumor_weight - 1.0)
    trained_residual = (np.sum(residual_targets * weights, axis=0) / np.sum(weights, axis=0)).astype(
        np.float32
    )

    loss_history: list[dict[str, float]] = []
    for epoch in range(max_epochs):
        residual_losses = []
        tumor_weighted_losses = []
        for sample in samples:
            prediction = np.broadcast_to(trained_residual, sample.residual_target.shape)
            residual_losses.append(residual_l1(prediction, sample.residual_target))
            tumor_weighted_losses.append(
                tumor_roi_weighted_residual_l1(
                    prediction,
                    sample.residual_target,
                    tumor_mask=sample.tumor_mask,
                    tumor_weight=tumor_weight,
                )
            )
        loss_history.append(
            {
                "epoch": float(epoch),
                "residual_l1": float(np.mean(residual_losses)),
                "tumor_roi_weighted_residual_l1": float(np.mean(tumor_weighted_losses)),
            }
        )
    return trained_residual, tuple(loss_history)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Phase 1A train/evaluate from a JSON or YAML config path."""
    parser = argparse.ArgumentParser(description="Run Phase 1A train/evaluate")
    parser.add_argument("config", help="Path to a Phase 1A JSON/YAML experiment config")
    args = parser.parse_args(argv)

    result = run_phase1a_train_evaluate(load_phase1a_config_file(args.config))
    print(
        json.dumps(
            {
                "checkpoint_path": str(result.checkpoint_path),
                "summary_path": str(result.summary_path),
                "prediction_paths": {
                    case_id: str(path) for case_id, path in result.prediction_paths.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
