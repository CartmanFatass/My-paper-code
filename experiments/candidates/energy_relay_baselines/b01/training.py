"""Fresh independent-seed SET fits; B02 owns collection, learner, and config semantics."""

from __future__ import annotations

import json
import resource
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from experiments.candidates.energy_relay_benchmark.b02.configuration import actor_input_width
from experiments.candidates.energy_relay_benchmark.b02.training import (
    PPO_NOT_EXPOSED, PPO_UPDATE_KEYS, collect_and_train, new_agent,
)
from experiments.candidates.uav_service_auxiliary.b01.native import (
    active_config, initialization_fingerprint, optimizer_steps, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b06.feedback import PRODUCTION_LAYOUT
from experiments.candidates.uav_service_auxiliary.b09.persistence import append_progress, write_summary
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS

from .configuration import (
    CHECKPOINT_RULE, DIRECTION, OBJECT_ID, PROGRAMME, RECIPE_NOTES, B02Spec,
    checkpoint_rollouts, config_dict, make_b02_config, spec_record,
)


def save_checkpoint(agent, config, spec: B02Spec, out: Path, index: int, *,
                    rollout: int, transitions: int, started: float,
                    launch_sha: str) -> dict[str, Any]:
    """B02-compatible record with this direction's identity; no RNG draw."""
    root = Path(out) / "checkpoints" / f"c{index:02d}"
    if root.exists():
        raise FileExistsError(f"checkpoint already exists: {root}")
    root.mkdir(parents=True)
    agent_pt = root / "agent.pt"
    agent.save_model(agent_pt)
    record = {
        "object_id": OBJECT_ID, "direction": DIRECTION, "programme": PROGRAMME,
        "launch_sha": launch_sha, "checkpoint": f"c{index:02d}",
        "rollout": int(rollout), "transitions": int(transitions),
        "optimizer_steps": optimizer_steps(agent), "wall_seconds": time.perf_counter() - started,
        "agent_pt": "agent.pt", "agent_pt_sha256": sha256_file(agent_pt),
        "agent_pt_bytes": agent_pt.stat().st_size,
        "policy_fingerprint": initialization_fingerprint(agent),
        "training_seed": int(spec.seed), "config": config_dict(config),
    }
    write_summary(root / "record.json", record)
    return record


def run_training(*, out: Path, launch_sha: str, spec: B02Spec,
                 device_name: str = "cuda", threads: int = 4, argv=None) -> dict[str, Any]:
    """One fresh fit, with c00 and all six B02-scheduled post-update checkpoints."""
    out = Path(out)
    if any((out / name).exists() for name in ("config.json", "summary.json", "progress.jsonl",
                                              "checkpoints")):
        raise FileExistsError(f"training scientific output already exists: {out}")
    config = make_b02_config(spec)
    device = torch.device(device_name)
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(int(threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("SET training requires Torch FP32 default dtype")
    schedule = checkpoint_rollouts(spec)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    run_config = {
        "object_id": OBJECT_ID, "direction": DIRECTION, "programme": PROGRAMME,
        "launch_sha": launch_sha, "argv": list(sys.argv if argv is None else argv),
        "device": str(device), "torch_threads": int(threads), "seed": int(spec.seed),
        "spec": spec_record(spec), "config": config_dict(config),
        "active": json.loads(json.dumps(active_config(config)), parse_constant=str),
        "recipe_notes": RECIPE_NOTES, "checkpoint_rule": CHECKPOINT_RULE,
        "training_feedback": {"layout": asdict(PRODUCTION_LAYOUT),
                              "params": asdict(PRODUCTION_PARAMS)},
        "actor_input_width": actor_input_width(config),
        "ppo_update_keys": list(PPO_UPDATE_KEYS), "ppo_not_exposed": list(PPO_NOT_EXPOSED),
    }
    write_summary(out / "config.json", run_config)
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "direction": DIRECTION, "programme": PROGRAMME,
        "status": "INCOMPLETE", "failure": None, "launch_sha": launch_sha,
        "seed": int(spec.seed), "device": str(device), "torch_threads": int(threads),
        "counts": {"transitions": 0, "rollouts": 0, "native_episodes": 0,
                   "checkpoints": 0},
        "checkpoint_rollouts": list(schedule), "rollouts": [], "checkpoints": {},
        "artifacts": {"config.json": sha256_file(out / "config.json")},
    }
    write_summary(out / "summary.json", summary)

    def checkpoint(agent, index, rollout, transitions):
        record = save_checkpoint(agent, config, spec, out, index, rollout=rollout,
                                 transitions=transitions, started=started, launch_sha=launch_sha)
        label = record["checkpoint"]
        summary["checkpoints"][label] = {
            key: record[key] for key in ("rollout", "transitions", "optimizer_steps",
                                         "wall_seconds", "agent_pt_sha256", "policy_fingerprint")}
        summary["counts"]["checkpoints"] += 1
        append_progress(out, {"event": "checkpoint", "checkpoint": label,
                              **summary["checkpoints"][label]}, dict(summary["counts"]))

    training_error = None
    try:
        agent, identity = new_agent(config, device=device, log_dir=out / "logs", seed=spec.seed)
        summary["initialization"] = identity
        summary["initial_fingerprint"] = identity["policy_fingerprint"]
        width = int(agent.skill_discoverer.central_input_dim) + int(config.obs_dim)
        if width != actor_input_width(config):
            raise RuntimeError(f"SET actor input width {width} != {actor_input_width(config)}")
        summary["actor_input_width"] = width
        checkpoint(agent, 0, 0, 0)
        write_summary(out / "summary.json", summary)

        def after_rollout(rollout, record):
            summary["rollouts"].append(record)
            summary["counts"].update(
                transitions=record["transitions"], rollouts=rollout,
                native_episodes=summary["counts"]["native_episodes"]
                + len(record["episodes_completed"]))
            append_progress(out, {"event": "rollout", **record}, dict(summary["counts"]))
            if rollout in schedule:
                checkpoint(agent, schedule.index(rollout) + 1, rollout,
                           record["transitions"])
            write_summary(out / "summary.json", summary)
            print(f"B01 seed={spec.seed} rollout {rollout}/{spec.rollouts} "
                  f"transitions={record['transitions']}", flush=True)

        result = collect_and_train(agent, config, spec, feedback=True,
                                   after_rollout=after_rollout)
        if summary["counts"]["checkpoints"] != len(schedule) + 1:
            raise RuntimeError("checkpoint count differs from schedule")
        steps = optimizer_steps(agent)
        if steps["low_actor"] <= 0 or steps["low_critic"] <= 0:
            raise RuntimeError("low-level SET learner did not update")
        final_fingerprint = initialization_fingerprint(agent)
        summary.update(status="COMPLETE", optimizer_steps=steps,
                       final_fingerprint=final_fingerprint,
                       fingerprint_changed=(final_fingerprint != summary["initial_fingerprint"]),
                       collector_wall=result["wall"])
        return summary
    except Exception as exc:
        training_error = exc
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        try:
            from .diagnostics import failure_context
            context_path = out / "failure-context.json"
            write_summary(context_path, failure_context(exc, summary["counts"]))
            summary["artifacts"]["failure-context.json"] = sha256_file(context_path)
        except Exception:
            # Diagnostic capture is best effort; the original training failure owns the exit.
            pass
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        wall = time.perf_counter() - started
        transitions = summary["counts"]["transitions"]
        summary.update(
            wall_seconds=wall, cpu_user_seconds=usage.ru_utime - cpu_start.ru_utime,
            cpu_system_seconds=usage.ru_stime - cpu_start.ru_stime,
            peak_rss_kib=int(usage.ru_maxrss), rss_scope="runner process high-water mark",
            seconds_per_transition=(wall / transitions if transitions else None))
        try:
            write_summary(out / "summary.json", summary)
            append_progress(out, {"event": "training_exit", "status": summary["status"]},
                            dict(summary["counts"]))
        except Exception:
            if training_error is None:
                raise
