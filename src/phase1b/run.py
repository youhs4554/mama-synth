"""Minimal Phase 1B real-debug train/evaluate driver."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from phase1a.dataset import ResidualSynthesisDataset, ResidualTrainingSample
from phase1a.image_io import read_image_artifact, write_image_artifact
from phase1a.inference import synthesize_post_from_pre_contrast
from phase1a.losses import residual_l1, tumor_roi_weighted_residual_l1
from phase1a.splits import load_split_manifest
from phase1b.augmentation import DomainAugmentationConfig, apply_domain_robustness_augmentation
from phase1b.config import validate_phase1b_config
from phase1b.models import train_unet_residual_regressor
from phase1b.runner import run_phase1b_ablation


@dataclass(frozen=True)
class Phase1BRunResult:
    checkpoint_path: Path
    prediction_paths: dict[str, Path]
    run_summary_path: Path
    ablation_summary_path: Path


@dataclass(frozen=True)
class _StaticMetricsEvaluator:
    metrics: dict[str, dict[str, object]]

    def evaluate(
        self,
        candidate: str,
        metric_groups: tuple[str, ...],
        fixed_settings: dict[str, object],
    ) -> dict[str, dict[str, object]]:
        del candidate, fixed_settings
        return {group: self.metrics[group] for group in metric_groups}


def load_phase1b_config_file(path: str | Path) -> Mapping[str, object]:
    """Load a Phase 1B experiment config from JSON or YAML."""
    config_path = Path(path)
    if config_path.suffix in {".yaml", ".yml"}:
        import yaml

        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    elif config_path.suffix == ".json":
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Phase 1B config file must be .json, .yaml, or .yml")
    if not isinstance(loaded, Mapping):
        raise ValueError("Phase 1B config file must contain an object")
    return loaded


def run_phase1b_train_evaluate(raw_config: Mapping[str, object]) -> Phase1BRunResult:
    """Run the smoke-scale Phase 1B U-Net residual ablation on a local split."""
    validated = validate_phase1b_config(raw_config)
    config = validated.phase1a.raw
    run_section = _section(config, "run")
    data_section = _section(config, "data")
    model_section = _section(config, "model")
    train_section = _section(config, "train")
    ablation_section = _section(config, "ablation")

    if ablation_section.get("model_family") != "unet_residual_regressor":
        raise ValueError("Phase 1B first real-debug driver only runs unet_residual_regressor")
    augmentation_policy = str(ablation_section.get("augmentation_policy"))
    if augmentation_policy not in {"disabled", "scanner_protocol_intensity"}:
        raise ValueError("Phase 1B driver only supports disabled or scanner_protocol_intensity augmentation")

    output_dir = Path(str(run_section.get("output_dir", "experiments/phase1b/unet_residual_smoke_v1")))
    predictions_dir = output_dir / "predictions"
    metrics_dir = output_dir / "metrics"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = Path(str(data_section["split_manifest"]))
    manifest = load_split_manifest(manifest_path)
    train_dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="train")
    holdout_dataset = ResidualSynthesisDataset.from_manifest(manifest, membership="holdout")
    raw_train_samples = [train_dataset[index] for index in range(len(train_dataset))]
    if not raw_train_samples:
        raise ValueError("Phase 1B driver requires at least one train case")

    seed = int(run_section.get("seed", 0))
    train_samples, augmentation_summary = _prepare_training_samples(
        raw_train_samples,
        policy=augmentation_policy,
        raw_config=config.get("augmentation"),
        default_seed=seed,
    )
    base_channels = int(model_section.get("base_channels", 4))
    max_epochs = int(train_section.get("max_epochs", 1))
    model = train_unet_residual_regressor(
        [sample.pre_contrast for sample in train_samples],
        [sample.ground_truth_post for sample in train_samples],
        base_channels=base_channels,
        epochs=max_epochs,
        seed=seed,
    )

    loss_history = _loss_history(train_samples, model, max_epochs=max_epochs)
    checkpoint_path = output_dir / "checkpoint.npz"
    np.savez(
        checkpoint_path,
        model_family="unet_residual_regressor",
        seed=np.array(seed),
        base_channels=np.array(base_channels),
        head_weights=model.head_weights,
        head_bias=np.array(model.head_bias, dtype=np.float32),
        loss_history=np.array(loss_history, dtype=object),
    )
    checkpoint_hash = _sha256_file(checkpoint_path)

    prediction_paths: dict[str, Path] = {}
    metric_rows: list[dict[str, object]] = []
    for index in range(len(holdout_dataset)):
        sample = holdout_dataset[index]
        synthetic_post = synthesize_post_from_pre_contrast(
            sample.pre_contrast,
            predictor=model,
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
        metric_rows.append(_case_metric_row(sample, synthetic_post))

    metrics_by_case_path = metrics_dir / "holdout_fidelity_by_case.csv"
    _write_metric_rows(metrics_by_case_path, metric_rows)
    metrics = _metric_groups(metric_rows)

    run_metadata = dict(_section(config, "run_metadata"))
    run_metadata["checkpoint_hash"] = checkpoint_hash
    run_metadata["metric_summary"] = metrics
    config_for_summary = dict(config)
    config_for_summary["run_metadata"] = run_metadata
    ablation_summary_path = metrics_dir / "ablation_summary.json"
    run_phase1b_ablation(
        config=config_for_summary,
        evaluator=_StaticMetricsEvaluator(metrics),
        output_path=ablation_summary_path,
    )

    run_summary_path = output_dir / "run_summary.json"
    run_summary_path.write_text(
        json.dumps(
            {
                "schema_version": "phase1b-real-debug-run-v1",
                "command": "PYTHONPATH=src uv run python -m phase1b.run <config>",
                "config": config,
                "split_manifest": str(manifest_path),
                "seed": seed,
                "checkpoint": str(checkpoint_path),
                "checkpoint_hash": checkpoint_hash,
                "predictions": {case_id: str(path) for case_id, path in prediction_paths.items()},
                "metrics_by_case": str(metrics_by_case_path),
                "ablation_summary": str(ablation_summary_path),
                "metrics": metrics,
                "augmentation": augmentation_summary,
                "inference_settings": {"inputs": ["pre_contrast"], "output": "synthetic_post"},
                "loss_history": loss_history,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return Phase1BRunResult(
        checkpoint_path=checkpoint_path,
        prediction_paths=prediction_paths,
        run_summary_path=run_summary_path,
        ablation_summary_path=ablation_summary_path,
    )


def _section(config: Mapping[str, object], name: str) -> dict[str, object]:
    section = config.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"{name} section is required")
    return section


def _prepare_training_samples(
    samples: Sequence[ResidualTrainingSample],
    *,
    policy: str,
    raw_config: object,
    default_seed: int,
) -> tuple[list[ResidualTrainingSample], dict[str, object]]:
    if policy == "disabled":
        return list(samples), {"enabled": False}
    if policy != "scanner_protocol_intensity":
        raise ValueError("unsupported Phase 1B augmentation policy")
    if not isinstance(raw_config, Mapping):
        raise ValueError("scanner_protocol_intensity augmentation requires an augmentation config section")
    if raw_config.get("enabled") is not True:
        raise ValueError("scanner_protocol_intensity augmentation requires augmentation.enabled=true")

    base_seed = int(raw_config.get("seed", default_seed))
    scale_range = _float_pair(raw_config.get("intensity_scale_range", (0.9, 1.1)), "intensity_scale_range")
    shift_range = _float_pair(raw_config.get("intensity_shift_range", (-0.1, 0.1)), "intensity_shift_range")
    augmented_samples: list[ResidualTrainingSample] = []
    parameters_by_case: dict[str, object] = {}
    for index, sample in enumerate(samples):
        augmented = apply_domain_robustness_augmentation(
            sample.pre_contrast,
            sample.ground_truth_post,
            sample.tumor_mask,
            DomainAugmentationConfig(
                enabled=True,
                seed=base_seed + index,
                intensity_scale_range=scale_range,
                intensity_shift_range=shift_range,
            ),
        )
        augmented_samples.append(
            ResidualTrainingSample(
                case_id=sample.case_id,
                pre_contrast=augmented.pre_contrast,
                ground_truth_post=augmented.ground_truth_post,
                tumor_mask=augmented.tumor_mask,
                residual_target=augmented.ground_truth_post - augmented.pre_contrast,
                pre_contrast_path=sample.pre_contrast_path,
            )
        )
        parameters_by_case[sample.case_id] = augmented.parameters
    return augmented_samples, {
        "enabled": True,
        "policy": "scanner_protocol_intensity",
        "seed": base_seed,
        "intensity_scale_range": list(scale_range),
        "intensity_shift_range": list(shift_range),
        "train_cases": parameters_by_case,
    }


def _float_pair(raw_value: object, name: str) -> tuple[float, float]:
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, (str, bytes)) or len(raw_value) != 2:
        raise ValueError(f"augmentation.{name} must contain two numeric values")
    return (float(raw_value[0]), float(raw_value[1]))


def _loss_history(
    samples: Sequence[ResidualTrainingSample],
    model: object,
    *,
    max_epochs: int,
    tumor_weight: float = 3.0,
) -> list[dict[str, float]]:
    losses: list[dict[str, float]] = []
    for epoch in range(max_epochs):
        residual_losses = []
        tumor_weighted_losses = []
        for sample in samples:
            predicted_residual = model.predict(sample.pre_contrast)
            residual_losses.append(residual_l1(predicted_residual, sample.residual_target))
            tumor_weighted_losses.append(
                tumor_roi_weighted_residual_l1(
                    predicted_residual,
                    sample.residual_target,
                    tumor_mask=sample.tumor_mask,
                    tumor_weight=tumor_weight,
                )
            )
        losses.append(
            {
                "epoch": float(epoch),
                "residual_l1": float(np.mean(residual_losses)),
                "tumor_roi_weighted_residual_l1": float(np.mean(tumor_weighted_losses)),
            }
        )
    return losses


def _case_metric_row(sample: ResidualTrainingSample, synthetic_post: np.ndarray) -> dict[str, object]:
    mask = sample.tumor_mask.astype(bool)
    if not mask.any():
        mask = np.ones_like(sample.tumor_mask, dtype=bool)
    candidate_error = synthetic_post - sample.ground_truth_post
    identity_error = sample.pre_contrast - sample.ground_truth_post
    return {
        "case_id": sample.case_id,
        "candidate_mse": float(np.mean(candidate_error**2)),
        "identity_mse": float(np.mean(identity_error**2)),
        "candidate_mae": float(np.mean(np.abs(candidate_error))),
        "identity_mae": float(np.mean(np.abs(identity_error))),
        "candidate_tumor_roi_mse": float(np.mean(candidate_error[mask] ** 2)),
        "identity_tumor_roi_mse": float(np.mean(identity_error[mask] ** 2)),
    }


def _write_metric_rows(path: Path, rows: Sequence[dict[str, object]]) -> None:
    fieldnames = [
        "case_id",
        "candidate_mse",
        "identity_mse",
        "candidate_mae",
        "identity_mae",
        "candidate_tumor_roi_mse",
        "identity_tumor_roi_mse",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _metric_groups(rows: Sequence[dict[str, object]]) -> dict[str, dict[str, object]]:
    if not rows:
        raise ValueError("Phase 1B driver requires at least one holdout case")
    return {
        "image_fidelity": {
            "candidate": _mean(rows, "candidate_mse"),
            "baseline": _mean(rows, "identity_mse"),
            "higher_is_better": False,
        },
        "tumor_roi_realism": {
            "candidate": _mean(rows, "candidate_tumor_roi_mse"),
            "baseline": _mean(rows, "identity_tumor_roi_mse"),
            "higher_is_better": False,
        },
    }


def _mean(rows: Sequence[dict[str, object]], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows]))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run Phase 1B train/evaluate from a JSON or YAML config path."""
    parser = argparse.ArgumentParser(description="Run Phase 1B real-debug train/evaluate")
    parser.add_argument("config", help="Path to a Phase 1B JSON/YAML experiment config")
    args = parser.parse_args(argv)

    result = run_phase1b_train_evaluate(load_phase1b_config_file(args.config))
    print(
        json.dumps(
            {
                "canonical_command": f"PYTHONPATH=src uv run python -m phase1b.run {args.config}",
                "checkpoint_path": str(result.checkpoint_path),
                "run_summary_path": str(result.run_summary_path),
                "ablation_summary_path": str(result.ablation_summary_path),
                "prediction_paths": {case_id: str(path) for case_id, path in result.prediction_paths.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
