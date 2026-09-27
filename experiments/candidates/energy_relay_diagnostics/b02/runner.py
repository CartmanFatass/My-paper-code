#!/usr/bin/env python3
"""Admission-guarded c03 continuation and fixed B02 endpoint panel."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SEED = 925031
START_ROLLOUT = 100
END_ROLLOUT = 150
START_TRANSITIONS = 600_000
END_TRANSITIONS = 900_000
RESUME_SEED = 925131
SOURCE_LAUNCH_SHA = "759927b5e8caa0ba5bd8ba505ab5388985f6a2fa"
SOURCE_CHECKPOINT = Path(
    "/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c03"
)
SOURCE_AGENT_SHA256 = "80b2bdadddb76a4c03fe9fea8ae9fb1317a136363d28dec0d8fae350745dcce4"
EXPECTED_END_OPTIMIZER_STEPS = 337_500
ARM_CHOICES = ("ordinary", "masked")


def _validate_value_norm_increment(start_count, end_count, expected_increment):
    observed_increment = float(end_count) - float(start_count)
    if abs(observed_increment - float(expected_increment)) > 1e-5:
        raise RuntimeError(
            f"discoverer ValueNorm count increased by {observed_increment}, "
            f"expected {expected_increment} new action rows"
        )
    return observed_increment


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    train = commands.add_parser("train")
    train.add_argument("--arm", choices=ARM_CHOICES, required=True)
    train.add_argument("--seed", type=int, choices=(SEED,), required=True)
    train.add_argument("--launch-sha", required=True)
    train.add_argument("--out", type=Path, required=True)
    train.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    train.add_argument("--threads", type=int, default=4)

    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--ordinary-checkpoint", type=Path, required=True)
    evaluate.add_argument("--masked-checkpoint", type=Path, required=True)
    evaluate.add_argument("--launch-sha", required=True)
    evaluate.add_argument("--out", type=Path, required=True)
    evaluate.add_argument("--workers", type=int, default=8)
    evaluate.add_argument("--threads", type=int, default=2)
    evaluate.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    return parser.parse_args(argv)


def _set_numeric_threads(threads: int) -> None:
    value = str(int(threads))
    for name in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[name] = value


def main(argv=None):
    args = parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_diagnostics")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    if args.command == "train":
        if args.threads != 4:
            raise ValueError("B02 continuation fixes four numerical threads")
        _set_numeric_threads(args.threads)
        return train_continuation(
            arm=args.arm, seed=args.seed, launch_sha=args.launch_sha, out=args.out,
            device_name=args.device, threads=args.threads,
        )

    if (args.workers, args.threads, args.device) != (8, 2, "cpu"):
        raise ValueError("B02 endpoint evaluation fixes eight workers, two threads, and CPU")
    _set_numeric_threads(args.threads)
    return evaluate_pair(
        ordinary_checkpoint=args.ordinary_checkpoint,
        masked_checkpoint=args.masked_checkpoint,
        launch_sha=args.launch_sha,
        out=args.out,
        workers=args.workers,
        threads=args.threads,
        device_name=args.device,
    )


def train_continuation(*, arm, seed, launch_sha, out, device_name="cuda", threads=4):
    """Continue one arm from the pinned published c03 full learner state."""
    import numpy as np
    import torch

    from experiments.candidates.energy_relay_benchmark.b02 import configuration as source_cfg
    from experiments.candidates.energy_relay_benchmark.b02 import training as source_training
    from experiments.candidates.energy_relay_diagnostics.b02.training import (
        collect_with_policy_surrogate_mask,
        parameter_displacement,
        snapshot_low_level_parameters,
    )
    from experiments.candidates.uav_service_auxiliary.b01.native import (
        active_config,
        initialization_fingerprint,
        optimizer_steps,
        sha256_file,
    )
    from experiments.candidates.uav_service_auxiliary.b09.persistence import (
        append_progress,
        write_summary,
    )

    if arm not in ARM_CHOICES or int(seed) != SEED:
        raise ValueError("arm or training seed differs from the prospectively fixed comparison")
    if int(threads) != 4:
        raise ValueError("B02 continuation fixes four numerical threads")
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl",
                                              "checkpoints")):
        raise FileExistsError(f"B02 surrogate output already exists: {out}")

    source_spec = source_cfg.production_spec(int(seed))
    run_spec = replace(source_spec, rollouts=END_ROLLOUT)
    config = source_cfg.make_b02_config(source_spec)
    source_record = source_training.read_resume_checkpoint(
        SOURCE_CHECKPOINT,
        source_spec,
        config,
        resume_source_sha=SOURCE_LAUNCH_SHA,
    )
    source_agent_pt = SOURCE_CHECKPOINT / "agent.pt"
    actual_source_sha = sha256_file(source_agent_pt)
    if actual_source_sha != SOURCE_AGENT_SHA256:
        raise ValueError(
            f"c03 agent.pt SHA256 {actual_source_sha} differs from pinned {SOURCE_AGENT_SHA256}"
        )
    if (source_record.get("checkpoint"), source_record.get("rollout"),
            source_record.get("transitions")) != ("c03", START_ROLLOUT, START_TRANSITIONS):
        raise ValueError("c03 record does not identify the pinned 600,000-transition boundary")
    source_steps = source_record.get("optimizer_steps", {})
    if (source_steps.get("low_actor"), source_steps.get("low_critic")) != (225_000, 225_000):
        raise ValueError("c03 low-level optimizer steps differ from the declared continuation")
    if int(source_record.get("training_seed", -1)) != int(seed):
        raise ValueError("c03 training seed differs from the continuation seed")

    device = torch.device(device_name)
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA continuation was requested but CUDA is unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(int(threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B02 continuation requires Torch FP32 default dtype")

    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    run_config = {
        "object_id": source_cfg.OBJECT_ID,
        "programme": "B02-direct-surrogate-mask-c03-continuation",
        "launch_sha": launch_sha,
        "arm": arm,
        "seed": int(seed),
        "device": str(device),
        "torch_threads": int(threads),
        "source_checkpoint_dir": str(SOURCE_CHECKPOINT),
        "source_checkpoint": source_record,
        "source_agent_pt_sha256": actual_source_sha,
        "source_launch_sha": SOURCE_LAUNCH_SHA,
        "resume_seed": RESUME_SEED,
        "resume_seed_rule": "B02 c03 recovery: training seed + c03 rollout",
        "continuation_start": {"rollout": START_ROLLOUT, "transitions": START_TRANSITIONS},
        "continuation_end": {"rollout": END_ROLLOUT, "transitions": END_TRANSITIONS},
        "source_spec": source_cfg.spec_record(source_spec),
        "continuation_spec": source_cfg.spec_record(run_spec),
        "active_config": json.loads(
            json.dumps(active_config(config), parse_constant=str)
        ),
        "config": source_cfg.config_dict(config),
        "mask": {
            "direct_policy_surrogate_only": arm == "masked",
            "source": "production shield decision.modes returned before env.step",
            "denominator": "all valid PPO action rows before shield mask",
            "critic_entropy_gae_recurrence_and_valuenorm": "unchanged",
        },
    }
    write_summary(out / "config.json", run_config)
    summary = {
        "object_id": source_cfg.OBJECT_ID,
        "programme": run_config["programme"],
        "status": "INCOMPLETE",
        "failure": None,
        "launch_sha": launch_sha,
        "arm": arm,
        "seed": int(seed),
        "device": str(device),
        "counts": {
            "transitions": START_TRANSITIONS,
            "rollouts": START_ROLLOUT,
            "new_transitions": 0,
            "new_rollouts": 0,
            "native_episodes": 0,
        },
        "source": {
            "checkpoint": "c03",
            "rollout": START_ROLLOUT,
            "transitions": START_TRANSITIONS,
            "agent_pt_sha256": actual_source_sha,
            "policy_fingerprint": source_record["policy_fingerprint"],
            "optimizer_steps": source_steps,
        },
        "initialization": None,
        "rollouts": [],
        "checkpoints": {},
        "artifacts": {"config.json": sha256_file(out / "config.json")},
    }
    write_summary(out / "summary.json", summary)
    append_progress(out, {"event": "continuation_start", "arm": arm},
                    dict(summary["counts"]))

    try:
        agent, identity = source_training.resumed_agent(
            config,
            source_record,
            source_agent_pt,
            device=device,
            log_dir=out / "logs",
            seed=RESUME_SEED,
        )
        initial_steps = optimizer_steps(agent)
        if initial_steps != source_steps:
            raise RuntimeError("loaded learner optimizer counts differ from c03 record")
        if initialization_fingerprint(agent) != source_record["policy_fingerprint"]:
            raise RuntimeError("loaded learner fingerprint differs from c03 record")
        initial_value_norm_count = float(
            np.asarray(agent.value_norm_discoverer.count).item()
        )
        summary["initialization"] = identity
        summary["resume_seed"] = RESUME_SEED
        summary["optimizer_steps_before"] = initial_steps
        summary["discoverer_value_norm_count_before"] = initial_value_norm_count
        reference = snapshot_low_level_parameters(agent)
        write_summary(out / "summary.json", summary)

        def after_rollout(rollout: int, record: dict):
            record["optimizer_steps"] = optimizer_steps(agent)
            record["parameter_displacement_from_c03"] = None
            if rollout % 10 == 0 or rollout == END_ROLLOUT:
                record["parameter_displacement_from_c03"] = parameter_displacement(
                    agent, reference
                )
            summary["rollouts"].append(record)
            new_rollouts = int(rollout) - START_ROLLOUT
            summary["counts"].update(
                transitions=int(record["transitions"]),
                rollouts=int(rollout),
                new_transitions=int(record["transitions"]) - START_TRANSITIONS,
                new_rollouts=new_rollouts,
                native_episodes=(summary["counts"]["native_episodes"]
                                 + len(record["episodes_completed"])),
            )
            append_progress(out, {"event": "rollout", **record}, dict(summary["counts"]))
            write_summary(out / "summary.json", summary)
            print(f"B02 surrogate {arm} rollout {rollout}/{END_ROLLOUT} "
                  f"transitions={record['transitions']}", flush=True)

        collector = collect_with_policy_surrogate_mask(
            agent,
            config,
            run_spec,
            mask_direct_policy_surrogate=(arm == "masked"),
            after_rollout=after_rollout,
            start_rollout=START_ROLLOUT,
            start_transitions=START_TRANSITIONS,
            env_seed=RESUME_SEED,
        )
        final_steps = optimizer_steps(agent)
        for optimizer_name in ("low_actor", "low_critic"):
            if final_steps[optimizer_name] != EXPECTED_END_OPTIMIZER_STEPS:
                raise RuntimeError(
                    f"{optimizer_name} ended at {final_steps[optimizer_name]}, "
                    f"expected {EXPECTED_END_OPTIMIZER_STEPS}"
                )
        for optimizer_name in ("high", "team_discriminator", "individual_discriminator"):
            if final_steps.get(optimizer_name, 0) != initial_steps.get(optimizer_name, 0):
                raise RuntimeError(f"unexpected non-SET learner update: {optimizer_name}")
        value_norm_count = float(np.asarray(agent.value_norm_discoverer.count).item())
        expected_value_norm_increment = int(
            (END_TRANSITIONS - START_TRANSITIONS) * config.n_agents
        )
        observed_value_norm_increment = _validate_value_norm_increment(
            initial_value_norm_count,
            value_norm_count,
            expected_value_norm_increment,
        )
        if collector["counts"]["transitions"] != END_TRANSITIONS:
            raise RuntimeError("continuation exposure differs from 300,000 new transitions")
        if len(collector["rollouts"]) != END_ROLLOUT - START_ROLLOUT:
            raise RuntimeError("continuation rollout count differs from fifty")
        if summary["counts"]["new_transitions"] != END_TRANSITIONS - START_TRANSITIONS:
            raise RuntimeError("recorded continuation transition count differs from contract")

        endpoint = out / "checkpoints" / "endpoint"
        endpoint.mkdir(parents=True)
        agent_pt = endpoint / "agent.pt"
        agent.save_model(agent_pt)
        endpoint_record = {
            "object_id": source_cfg.OBJECT_ID,
            "programme": source_cfg.PROGRAMME,
            "launch_sha": launch_sha,
            "checkpoint": "endpoint",
            "rollout": END_ROLLOUT,
            "transitions": END_TRANSITIONS,
            "optimizer_steps": final_steps,
            "agent_pt": "agent.pt",
            "agent_pt_sha256": sha256_file(agent_pt),
            "agent_pt_bytes": agent_pt.stat().st_size,
            "policy_fingerprint": initialization_fingerprint(agent),
            "training_seed": int(seed),
            "config": source_cfg.config_dict(config),
            "arm": arm,
            "source_checkpoint": "c03",
            "source_agent_pt_sha256": actual_source_sha,
            "resume_seed": RESUME_SEED,
            "new_transitions": END_TRANSITIONS - START_TRANSITIONS,
            "discoverer_value_norm_count": value_norm_count,
            "discoverer_value_norm_count_before": initial_value_norm_count,
            "discoverer_value_norm_count_increment": observed_value_norm_increment,
            "parameter_displacement_from_c03": parameter_displacement(agent, reference),
        }
        write_summary(endpoint / "record.json", endpoint_record)
        summary["checkpoints"]["endpoint"] = {
            key: endpoint_record[key] for key in (
                "rollout", "transitions", "optimizer_steps", "agent_pt_sha256",
                "policy_fingerprint", "parameter_displacement_from_c03",
            )
        }
        summary.update(
            status="COMPLETE",
            optimizer_steps=final_steps,
            discoverer_value_norm_count=value_norm_count,
            discoverer_value_norm_count_increment=observed_value_norm_increment,
            collector_wall=collector["wall"],
            continuation_source="same published c03 state loaded independently per arm",
            endpoint_checkpoint=str(endpoint),
        )
        summary["artifacts"]["checkpoints/endpoint/agent.pt"] = endpoint_record["agent_pt_sha256"]
        summary["artifacts"]["checkpoints/endpoint/record.json"] = sha256_file(
            endpoint / "record.json"
        )
        summary["wall_seconds"] = time.perf_counter() - started
        write_summary(out / "summary.json", summary)
        append_progress(out, {"event": "training_exit", "status": "COMPLETE"},
                        dict(summary["counts"]))
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        summary["wall_seconds"] = time.perf_counter() - started
        write_summary(out / "summary.json", summary)
        append_progress(out, {"event": "training_exit", "status": "INCOMPLETE"},
                        dict(summary["counts"]))
        raise


def evaluate_pair(*, ordinary_checkpoint, masked_checkpoint, launch_sha, out,
                  workers=8, threads=2, device_name="cpu"):
    """Read the two endpoints once on the fixed development panel and pair their summaries."""
    from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import (
        DEVELOPMENT_WORLDS,
        STOCHASTIC_DRAW,
        evaluate_checkpoint,
        read_record,
    )
    from experiments.candidates.energy_relay_benchmark.b02.configuration import (
        OBJECT_ID,
        PROGRAMME,
    )
    from experiments.candidates.uav_service_auxiliary.b01.native import sha256_file
    from experiments.candidates.uav_service_auxiliary.b09.persistence import write_summary

    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json",
                                              "paired_evaluation.json")):
        raise FileExistsError(f"B02 paired evaluation output already exists: {out}")
    checkpoints = {
        "ordinary": Path(ordinary_checkpoint),
        "masked": Path(masked_checkpoint),
    }
    records = {arm: read_record(path) for arm, path in checkpoints.items()}
    for arm, record in records.items():
        if (record.get("checkpoint"), record.get("rollout"), record.get("transitions")) != (
            "endpoint", END_ROLLOUT, END_TRANSITIONS
        ):
            raise ValueError(f"{arm} checkpoint is not the declared B02 endpoint")
        if record.get("arm") != arm or record.get("source_agent_pt_sha256") != SOURCE_AGENT_SHA256:
            raise ValueError(f"{arm} checkpoint provenance differs from the fixed c03 continuation")
    out.mkdir(parents=True, exist_ok=True)
    config = {
        "object_id": OBJECT_ID,
        "programme": "B02-direct-surrogate-mask-endpoint-panel",
        "launch_sha": launch_sha,
        "source_programme": PROGRAMME,
        "checkpoints": {
            arm: {
                "path": str(checkpoints[arm]),
                "record": records[arm],
                "agent_pt_sha256": sha256_file(checkpoints[arm] / "agent.pt"),
            }
            for arm in checkpoints
        },
        "worlds": list(DEVELOPMENT_WORLDS),
        "modes": ["deterministic", "stochastic"],
        "stochastic_draw": STOCHASTIC_DRAW,
        "final": False,
        "horizon": 3000,
        "workers": int(workers),
        "threads": int(threads),
        "device": device_name,
    }
    write_summary(out / "config.json", config)
    paired = {
        "object_id": OBJECT_ID,
        "programme": config["programme"],
        "status": "INCOMPLETE",
        "failure": None,
        "launch_sha": launch_sha,
        "counts": {"episodes_completed": 0, "steps": 0, "panels_completed": 0},
        "cells": {},
        "config_sha256": sha256_file(out / "config.json"),
    }
    write_summary(out / "summary.json", paired)
    started = time.perf_counter()
    try:
        for arm, checkpoint in checkpoints.items():
            arm_out = out / arm
            result = evaluate_checkpoint(
                checkpoint_dir=checkpoint,
                out=arm_out,
                worlds=DEVELOPMENT_WORLDS,
                modes=("deterministic", "stochastic"),
                final=False,
                launch_sha=launch_sha,
                workers=int(workers),
                threads=int(threads),
                device_name=device_name,
                horizon=3000,
                argv=sys.argv,
            )
            if result.get("status") != "COMPLETE":
                raise RuntimeError(f"{arm} endpoint panel did not complete")
            if result["counts"]["episodes_completed"] != 64 or result["counts"]["panels_completed"] != 2:
                raise RuntimeError(f"{arm} endpoint panel episode/panel count differs from contract")
            paired["counts"]["episodes_completed"] += int(
                result["counts"]["episodes_completed"]
            )
            paired["counts"]["steps"] += int(result["counts"]["steps"])
            paired["counts"]["panels_completed"] += int(
                result["counts"]["panels_completed"]
            )
            paired["cells"][arm] = {
                "checkpoint": str(checkpoint),
                "checkpoint_record_sha256": sha256_file(checkpoint / "record.json"),
                "counts": result["counts"],
                "panels": result["panels"],
                "summary": str(arm_out / "checkpoint-eval" / "endpoint_deterministic-stochastic"
                               / "summary.json"),
                "status": result["status"],
            }
            write_summary(out / "summary.json", paired)
        if (paired["counts"]["episodes_completed"], paired["counts"]["panels_completed"]) != (
            128, 4
        ):
            raise RuntimeError("paired endpoint evaluation does not contain 128 episodes/four cells")
        paired.update(status="COMPLETE", wall_seconds=time.perf_counter() - started)
        write_summary(out / "paired_evaluation.json", paired)
        write_summary(out / "summary.json", paired)
        return paired
    except Exception as exc:
        paired["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        paired["wall_seconds"] = time.perf_counter() - started
        write_summary(out / "summary.json", paired)
        raise


if __name__ == "__main__":
    main()
