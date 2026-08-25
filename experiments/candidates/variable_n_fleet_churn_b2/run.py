"""Production train/evaluate/analyze launcher for VNFC-B2."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Mapping

import torch

from .analyze import analyze
from .config import BASE_SEEDS, EVENT_CELLS, LEARNED_ARMS, PRODUCTION_CONFIG
from .experiment import (
    evaluate_models, evaluate_validation, peak_process_rss_bytes,
    save_checkpoint, train_arm,
)
from .models import RecurrentSetActorCritic


ASSIGNMENT_ID = "VNFC-B2-TYPED-CAPSULE-RETENTION-v1"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _resources(started: float) -> dict[str, float | int]:
    result = {
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak_process_rss_bytes(),
    }
    if int(result["peak_rss_bytes"]) > PRODUCTION_CONFIG.peak_rss_bytes:
        raise RuntimeError("VNFC-B2 peak-RSS envelope exceeded")
    if float(result["wall_seconds"]) > PRODUCTION_CONFIG.wall_cap_seconds:
        raise RuntimeError("VNFC-B2 wall-time envelope exceeded")
    return result


def exercise(output_root: Path, result_path: Path) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("VNFC-B2 output root must be fresh")
    if result_path.exists():
        raise FileExistsError("VNFC-B2 retained result must be absent")
    output_root.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    started = time.perf_counter()
    cpu_started = time.process_time()
    probes = [RecurrentSetActorCritic() for _ in LEARNED_ARMS]
    parameter_counts = dict(zip(LEARNED_ARMS, (model.parameter_count for model in probes)))
    if len(set(parameter_counts.values())) != 1:
        raise RuntimeError(f"arm parameter mismatch: {parameter_counts}")
    del probes
    manifest = {
        "artifact_kind": "VNFC_B2_PRODUCTION_MANIFEST",
        "assignment_id": ASSIGNMENT_ID,
        "base_seeds": list(BASE_SEEDS), "learned_arms": list(LEARNED_ARMS),
        "event_cells": list(EVENT_CELLS),
        "training_sizes": list(PRODUCTION_CONFIG.training_sizes),
        "held_out_size": PRODUCTION_CONFIG.held_out_size,
        "seen_schedules": ["S1", "S2"], "held_out_schedule": "S*",
        "training": {
            "updates": PRODUCTION_CONFIG.updates,
            "episodes_per_update": PRODUCTION_CONFIG.episodes_per_update,
            "ticks_per_episode": PRODUCTION_CONFIG.episode_ticks,
            "ppo_epochs": PRODUCTION_CONFIG.ppo_epochs,
            "minibatch_agent_event_rows": PRODUCTION_CONFIG.minibatch_agent_rows,
            "final_checkpoint_only": True,
        },
        "network": {
            "row_encoder": "27->64->64 SiLU",
            "actor": "masked DeepSets mean+sum -> 64 GRU -> 5 actions",
            "critic": "masked DeepSets mean+sum -> 64 GRU -> scalar",
            "trainable_parameter_counts": parameter_counts,
        },
        "evaluation": {
            "base_worlds_per_seed": 1280,
            "row_order_replicas": PRODUCTION_CONFIG.row_order_replicas,
            "joint_holdout_worlds_per_event_cell": PRODUCTION_CONFIG.joint_holdout_worlds_per_cell,
        },
        "ordinary_float_comparison": {
            "rtol": PRODUCTION_CONFIG.ordinary_rtol,
            "atol": PRODUCTION_CONFIG.ordinary_atol,
        },
        "engineering_resource_envelope": {
            "wall_seconds": PRODUCTION_CONFIG.wall_cap_seconds,
            "peak_rss_bytes": PRODUCTION_CONFIG.peak_rss_bytes,
        },
    }
    _write_json(output_root / "manifest.json", manifest)

    seed_rows: list[dict[str, object]] = []
    activity_path = output_root / "activity_start.json"
    for base_seed in BASE_SEEDS:
        models = {}
        curves = {}
        validations = {}
        train_walls = {}
        for arm in LEARNED_ARMS:
            arm_started = time.perf_counter()
            model, optimizer, curve = train_arm(arm, base_seed)
            train_walls[arm] = time.perf_counter() - arm_started
            curves[arm] = curve
            models[arm] = model
            save_checkpoint(
                output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.pt",
                model, optimizer, arm, base_seed, curve,
            )
            validations[arm] = evaluate_validation(model, arm, base_seed)
            _resources(started)
        raw_path = output_root / "evaluation_rows" / f"seed_{base_seed}.jsonl.gz"
        evaluation = evaluate_models(models, base_seed, raw_path)
        seed_row = {
            "base_seed": base_seed, "arms": evaluation["arms"],
            "inference_latency": evaluation["inference_latency"],
            "learning_curves": curves, "validation": validations,
            "training_wall_seconds": train_walls,
            "base_worlds": evaluation["base_worlds"],
            "replicated_episodes_per_arm": evaluation["replicated_episodes_per_arm"],
            "raw_rows": str(raw_path),
        }
        seed_rows.append(seed_row)
        seed_path = output_root / "seed_summaries" / f"seed_{base_seed}.json"
        _write_json(seed_path, seed_row)
        if not activity_path.exists():
            _write_json(activity_path, {
                "criterion": (
                    "all three learned arms for one paired seed have final checkpoints and emit "
                    "every event cell in all four evaluation panels, fresh-oracle counterfactuals, "
                    "stale-state instrumentation, and all four row-order replicas"
                ),
                "reached": True, "base_seed": base_seed,
                "seed_summary": str(seed_path), "raw_rows": str(raw_path),
                "checkpoint_paths": {
                    arm: str(output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.pt")
                    for arm in LEARNED_ARMS
                },
            })
        _resources(started)

    analysis = analyze(seed_rows)
    anomalies = []
    for seed in seed_rows:
        for arm, summary in seed["arms"].items():
            observed = summary["permutation"]
            if any(int(observed[key]) for key in (
                "assignment_disagreements", "probability_tolerance_violations",
                "reward_tolerance_violations",
            )):
                anomalies.append({
                    "base_seed": seed["base_seed"], "arm": arm,
                    "kind": "row_permutation_deviation", "observed": observed,
                })
    if any(int(value) != 0 for value in analysis["typed_hard_stale_errors"].values()):
        anomalies.append({
            "kind": "typed_hard_stale_state_error",
            "observed": analysis["typed_hard_stale_errors"],
        })
    resources = _resources(started)
    total_agent_rows = sum(
        int(row["agent_event_rows"])
        for seed in seed_rows for arm in LEARNED_ARMS
        for row in seed["learning_curves"][arm]
    )
    result = {
        "artifact_kind": "VNFC_B2_RETAINED_RESULT",
        "assignment_id": ASSIGNMENT_ID,
        "scientific_activity_criterion_reached": activity_path.exists(),
        "manifest": manifest,
        "actual_counts": {
            "base_seeds": len(BASE_SEEDS),
            "learned_checkpoints": len(BASE_SEEDS) * len(LEARNED_ARMS),
            "training_episodes_per_arm_seed": (
                PRODUCTION_CONFIG.updates * PRODUCTION_CONFIG.episodes_per_update
            ),
            "total_training_agent_event_rows": total_agent_rows,
            "optimizer_steps_by_seed_arm": {
                str(seed["base_seed"]): {
                    arm: int(seed["learning_curves"][arm][-1]["optimizer_steps_completed"])
                    for arm in LEARNED_ARMS
                } for seed in seed_rows
            },
        },
        "resources": {
            **resources, "process_cpu_seconds": time.process_time() - cpu_started,
        },
        "per_seed": seed_rows, "analysis": analysis,
        "material_anomalies": anomalies,
        "claim_ceiling": (
            "Constructed two-role relay-coverage game, one shared policy across the "
            "registered roster sizes and schedules, and the named finite-budget comparators only."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    exercise_parser = subparsers.add_parser("exercise")
    exercise_parser.add_argument("--output-root", required=True, type=Path)
    exercise_parser.add_argument("--result", required=True, type=Path)
    recover_parser = subparsers.add_parser("recover")
    recover_parser.add_argument("--output-root", required=True, type=Path)
    recover_parser.add_argument("--result", required=True, type=Path)
    recover_parser.add_argument("--terminal-json", required=True, type=Path)
    validate_parser = subparsers.add_parser("validate-recovery")
    validate_parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    if args.action == "validate-recovery":
        from .recovery import validate_recovery_source
        print(json.dumps(validate_recovery_source(args.output_root), sort_keys=True))
        return 0
    if args.action == "recover":
        from .recovery import RecoveryRefused, recover
        try:
            result = recover(
                args.output_root.resolve(), args.result.resolve(), args.terminal_json.resolve(),
            )
        except RecoveryRefused as exc:
            print(json.dumps({"recovery_refused": str(exc)}, sort_keys=True), file=os.sys.stderr)
            return 2
        print(json.dumps({
            "result": str(args.result.resolve()),
            "closure_revision": result["closure_revision"],
            "finished_at": result["recovery_resources"]["finished_at"],
        }, sort_keys=True))
        return 0
    result = exercise(args.output_root.resolve(), args.result.resolve())
    print(json.dumps({
        "result": str(args.result.resolve()),
        "activity_reached": result["scientific_activity_criterion_reached"],
        "wall_seconds": result["resources"]["wall_seconds"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
