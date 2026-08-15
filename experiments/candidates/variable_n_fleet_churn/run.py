"""Single production train/evaluate/analyze launcher for VNFC-B1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import time
from typing import Mapping

import torch

from .analyze import analyze
from .experiment import (
    BASE_SEEDS, EPISODES_PER_UPDATE, LEARNED_ARMS, PPO_EPOCHS, TRAIN_UPDATES,
    clone_model, evaluate_models, evaluate_validation, peak_process_rss_bytes,
    save_checkpoint, train_arm,
)
from .models import SetActorCritic


ASSIGNMENT_ID = "VNFC-B1-CHURNED-CAPABILITY-MATCHING-v1"
WALL_CAP_SECONDS = 3 * 60 * 60
RSS_CAP_BYTES = 4 * 1024**3


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _check_resources(started: float) -> dict[str, float | int]:
    resources = {
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak_process_rss_bytes(),
    }
    if float(resources["wall_seconds"]) > WALL_CAP_SECONDS:
        raise RuntimeError("VNFC-B1 wall-time envelope exceeded")
    if int(resources["peak_rss_bytes"]) > RSS_CAP_BYTES:
        raise RuntimeError("VNFC-B1 peak-RSS envelope exceeded")
    return resources


def exercise(output_root: Path, result_path: Path) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("VNFC-B1 production output root must be fresh")
    if result_path.exists():
        raise FileExistsError("VNFC-B1 retained result path already exists")
    output_root.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    started = time.perf_counter()
    process_started = time.process_time()

    probe_models = [SetActorCritic(arm) for arm in LEARNED_ARMS]
    parameter_counts = {arm: model.parameter_count for arm, model in zip(LEARNED_ARMS, probe_models)}
    if len(set(parameter_counts.values())) != 1:
        raise RuntimeError(f"learned-arm parameter mismatch: {parameter_counts}")
    del probe_models
    manifest = {
        "artifact_kind": "VNFC_B1_PRODUCTION_MANIFEST",
        "assignment_id": ASSIGNMENT_ID,
        "base_seeds": list(BASE_SEEDS),
        "learned_arms": list(LEARNED_ARMS),
        "training_sizes": [3, 5, 7],
        "held_out_sizes": [4, 6],
        "capacity_regimes": ["CAPACITY_NORMALIZED", "TRUE_EXPANSION"],
        "network": {
            "agent_encoder": "9->64->64 SiLU",
            "task_encoder": "4->32->32 SiLU",
            "bid_head": "333->64->64->1 SiLU",
            "critic": "237->64->64->1 SiLU",
            "common_context_width": 237,
            "trainable_parameter_counts": parameter_counts,
        },
        "training": {
            "updates": TRAIN_UPDATES,
            "episodes_per_update": EPISODES_PER_UPDATE,
            "segments_per_episode": 3,
            "ppo_epochs": PPO_EPOCHS,
            "minibatch_event_rows": 192,
            "final_checkpoint_only": True,
        },
        "conclusion": {
            "static_pairs_per_regime": 48,
            "static_base_episodes_per_seed": 192,
            "churn_worlds_per_regime_sequence": 24,
            "churn_base_episodes_per_seed": 288,
            "row_order_replicas": 4,
        },
        "ordinary_float_comparison": {"rtol": 1e-5, "atol": 1e-6},
        "caps": {"wall_seconds": WALL_CAP_SECONDS, "peak_rss_bytes": RSS_CAP_BYTES},
    }
    _write_json(output_root / "manifest.json", manifest)

    seed_rows: list[dict[str, object]] = []
    activity_path = output_root / "activity_start.json"
    total_training_cpu_seconds = 0.0
    for base_seed in BASE_SEEDS:
        models: dict[str, SetActorCritic] = {}
        curves: dict[str, object] = {}
        validations: dict[str, object] = {}
        snapshots: dict[str, list[dict[str, torch.Tensor]]] = {}
        arm_train_wall: dict[str, float] = {}
        arm_train_cpu: dict[str, float] = {}
        for arm in LEARNED_ARMS:
            arm_wall_started = time.perf_counter()
            arm_cpu_started = time.process_time()
            model, optimizer, arm_curve, arm_snapshots = train_arm(arm, base_seed)
            arm_train_wall[arm] = time.perf_counter() - arm_wall_started
            arm_train_cpu[arm] = time.process_time() - arm_cpu_started
            total_training_cpu_seconds += arm_train_cpu[arm]
            save_checkpoint(
                output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.pt",
                model, optimizer, arm, base_seed,
            )
            models[arm] = model
            curves[arm] = arm_curve
            snapshots[arm] = arm_snapshots
            validations[arm] = evaluate_validation(model, arm, base_seed)
            _check_resources(started)

        raw_rows_path = output_root / "evaluation_rows" / f"seed_{base_seed}.jsonl.gz"
        final_evaluation = evaluate_models(models, base_seed, raw_rows_path)

        cutoff = min(arm_train_wall.values())
        equal_time_updates: dict[str, int] = {}
        equal_time_models: dict[str, SetActorCritic] = {}
        for arm in LEARNED_ARMS:
            eligible = [
                int(row["update"])
                for row in curves[arm]  # type: ignore[union-attr]
                if float(row["cumulative_wall_seconds"]) <= cutoff
            ]
            selected_update = max(eligible) if eligible else 1
            equal_time_updates[arm] = selected_update
            equal_time_models[arm] = clone_model(
                arm, base_seed, snapshots[arm][selected_update - 1]
            )
        equal_time_full = evaluate_models(
            equal_time_models, base_seed, raw_rows_path=None, include_oracle=False,
        )
        equal_time_summary = {
            "wall_cutoff_seconds": cutoff,
            "selected_update_by_arm": equal_time_updates,
            "arms": {
                arm: {
                    metric: equal_time_full["arms"][arm][metric]  # type: ignore[index]
                    for metric in ("P", "H", "Ogap", "X", "capacity_normalized_N6_minus_N4")
                }
                for arm in LEARNED_ARMS
            },
        }
        seed_row = {
            "base_seed": base_seed,
            "arms": final_evaluation["arms"],
            "inference_latency": final_evaluation["inference_latency"],
            "training_wall_seconds": arm_train_wall,
            "training_cpu_seconds": arm_train_cpu,
            "learning_curves": curves,
            "validation": validations,
            "equal_time": equal_time_summary,
            "raw_rows": str(raw_rows_path),
        }
        seed_rows.append(seed_row)
        _write_json(output_root / "seed_summaries" / f"seed_{base_seed}.json", seed_row)

        if not activity_path.exists():
            _write_json(activity_path, {
                "criterion": (
                    "all four learned arms for one base seed have frozen update-32 checkpoints "
                    "and a complete paired conclusion block with both regimes, static N=4/N=6, "
                    "all churn sequences, four row-order replicas, and greedy-oracle rows"
                ),
                "reached": True,
                "base_seed": base_seed,
                "checkpoint_paths": {
                    arm: str(output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.pt")
                    for arm in LEARNED_ARMS
                },
                "seed_summary": str(output_root / "seed_summaries" / f"seed_{base_seed}.json"),
                "raw_rows": str(raw_rows_path),
            })
        _check_resources(started)

    analysis = analyze(seed_rows)
    permutation_anomalies: list[dict[str, object]] = []
    for seed_row in seed_rows:
        for arm, summary in seed_row["arms"].items():  # type: ignore[union-attr]
            permutation = summary["permutation"]
            if (
                int(permutation["assignment_disagreements"]) != 0
                or int(permutation["probability_tolerance_violations"]) != 0
                or int(permutation["reward_tolerance_violations"]) != 0
            ):
                permutation_anomalies.append({
                    "base_seed": seed_row["base_seed"], "arm": arm,
                    "observed": permutation,
                })
    resources = _check_resources(started)
    result: dict[str, object] = {
        "artifact_kind": "VNFC_B1_RETAINED_RESULT",
        "assignment_id": ASSIGNMENT_ID,
        "scientific_activity_criterion_reached": activity_path.exists(),
        "manifest": manifest,
        "actual_counts": {
            "base_seeds": len(BASE_SEEDS),
            "learned_checkpoints": len(BASE_SEEDS) * len(LEARNED_ARMS),
            "training_episodes_per_arm_seed": 4096,
            "training_segment_rows_per_arm_seed": 12288,
            "total_training_segment_rows": 393216,
            "optimizer_steps_per_arm_seed": 256,
            "total_optimizer_steps": 8192,
            "validation_episodes_per_arm_seed": 192,
            "final_base_episodes_per_arm_seed": 480,
            "final_replicated_episodes_per_arm_seed": 1920,
        },
        "resources": {
            **resources,
            "process_cpu_seconds": time.process_time() - process_started,
            "training_cpu_seconds": total_training_cpu_seconds,
        },
        "per_seed": seed_rows,
        "analysis": analysis,
        "material_anomalies": permutation_anomalies,
        "claim_ceiling": (
            "Constructed three-task, three-segment N=3..7 capability-allocation host; "
            "shared finite-budget PPO policies and the prespecified held-out static/churn panels only."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    registered = subparsers.add_parser("exercise")
    registered.add_argument("--output-root", required=True, type=Path)
    registered.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    result = exercise(args.output_root.resolve(), args.result.resolve())
    print(json.dumps({
        "result": str(args.result.resolve()),
        "activity_reached": result["scientific_activity_criterion_reached"],
        "wall_seconds": result["resources"]["wall_seconds"],  # type: ignore[index]
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
