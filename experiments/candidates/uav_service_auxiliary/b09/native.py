"""Prospectively fixed B09 N-then-A feedback training and primary F panel."""

from __future__ import annotations

import copy
import gc
import resource
import time
from dataclasses import dataclass
from pathlib import Path

import torch

from ..b01.native import make_config, sha256_file
from ..b08.native import (
    ARMS, B08Spec, ENDPOINT_FIELDS, TRAINING_FEEDBACK,
    assert_common_initialization, endpoint_comparison, evaluate_feedback_panel,
    fixed_config_record as b08_config_record, initialization_identity,
    new_initialized_agent as b08_new_initialized_agent,
)
from .persistence import append_progress, compact_opportunity, write_raw_json, write_summary


OBJECT_ID = "UAV-SERVICE-FEEDBACK-TRAINING-B09"
TRAINING_SEED = 925031
PRIMARY_SEEDS = tuple(range(952001, 952033))


@dataclass(frozen=True)
class B09Spec(B08Spec):
    seed: int = TRAINING_SEED
    eval_seeds: tuple[int, ...] = ()
    final_seeds: tuple[int, ...] = PRIMARY_SEEDS


def production_spec(seed: int) -> B09Spec:
    if int(seed) != TRAINING_SEED:
        raise ValueError("unplanned B09 training seed")
    return B09Spec()


def make_b09_config(spec: B09Spec):
    if spec != B09Spec():
        raise ValueError("B09 accepts only the prospectively fixed production specification")
    config = make_config(spec)
    config.ordinary_completed_segments = True
    expected = {
        "seed": TRAINING_SEED, "num_envs": 2, "rollout_length": 3000,
        "episode_length": 3000, "max_steps": 3000, "total_timesteps": 180000,
        "n_agents": 8, "k": 10,
    }
    mismatches = {key: (value, getattr(config, key, None)) for key, value in expected.items()
                  if getattr(config, key, None) != value}
    if mismatches:
        raise ValueError(f"B09 fixed native configuration mismatch: {mismatches}")
    if config.lambda_return != 2.0 or config.lambda_e != 1.0:
        raise ValueError("B09 native reward coefficients changed")
    if config.use_obsnorm or config.use_statenorm:
        raise ValueError("B09 expected disabled observation/state normalizers")
    return config


def fixed_config_record(spec: B09Spec, config):
    record = b08_config_record(spec, config)
    record["object_id"] = OBJECT_ID
    record["primary_seeds"] = list(PRIMARY_SEEDS)
    record.pop("development_seeds")
    record.pop("final_seeds")
    return record


def new_initialized_agent(config, *, device, log_dir, seed=TRAINING_SEED):
    return b08_new_initialized_agent(config, device=device, log_dir=log_dir, seed=seed)


def run_native(*, out: Path, launch_sha: str, device_name="cuda", threads=4,
               spec: B09Spec | None = None):
    """Execute one fixed pair; keep partial artifacts and never reuse an output root."""
    from .training import train_arm

    spec = spec or B09Spec()
    if threads != 4 or device_name != "cuda":
        raise ValueError("B09 production requires CUDA FP32 and four torch threads")
    config = make_b09_config(spec)
    device = torch.device(device_name)
    if not torch.cuda.is_available():
        raise RuntimeError("B09 CUDA was requested but is unavailable")
    torch.set_num_threads(threads)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl", "N", "A")):
        raise FileExistsError(f"B09 scientific output already exists: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    summary = {
        "object_id": OBJECT_ID, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "seed": spec.seed, "arm_order": list(ARMS),
        "device": str(device), "torch_threads": threads,
        "counts": {key: 0 for key in ("fits_started", "fits_completed", "training_transitions",
                                     "evaluation_transitions", "evaluation_episodes_attempted",
                                     "evaluation_episodes_completed")},
        "arms": {}, "evaluations": {}, "artifacts": {},
    }
    write_summary(out / "config.json", fixed_config_record(spec, config))
    summary["artifacts"]["config.json"] = sha256_file(out / "config.json")

    def progress(event):
        summary["counts"]["training_transitions"] = sum(
            row["counts"]["transitions"] for row in summary["arms"].values())
        append_progress(out, event, dict(summary["counts"]))
        if event["event"] in {"episode_complete", "phase_complete", "training_exit",
                              "fit_start", "fit_complete", "evaluation_world",
                              "panel_complete", "batch_exit"}:
            write_summary(out / "summary.json", summary)

    def panel(agent, label):
        def advance(kind, count):
            field = {"attempt": "evaluation_episodes_attempted",
                     "transition": "evaluation_transitions",
                     "world": "evaluation_episodes_completed"}[kind]
            summary["counts"][field] += 1 if kind == "world" else count
            if kind != "transition" or summary["counts"][field] % 100 == 0:
                progress({"event": "evaluation_" + kind, "panel": label,
                          "count": summary["counts"][field]})
        path = out / "evaluation" / (label + ".npz")
        result, arrays = evaluate_feedback_panel(
            agent, config, PRIMARY_SEEDS, device, trace_path=path,
            log_dir=out / "evaluation_logs" / label, policy_seed=spec.seed, progress=advance)
        del arrays
        raw_path = out / "raw" / f"evaluation_{label}.json.gz"
        write_raw_json(raw_path, result)
        summary["artifacts"][str(raw_path.relative_to(out))] = sha256_file(raw_path)
        for world in result["worlds"]:
            world["recovery_opportunity"] = compact_opportunity(world["recovery_opportunity"])
        result["raw_detail"] = str(raw_path.relative_to(out))
        summary["evaluations"][label] = result
        summary["artifacts"][str(path.relative_to(out))] = result["trace_sha256"]
        progress({"event": "panel_complete", "panel": label})

    def checkpoint(agent, label):
        path = out / label / "agent.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        agent.save_model(path)
        summary["artifacts"][str(path.relative_to(out))] = sha256_file(path)

    try:
        common_identity = None
        for arm in ARMS:
            arm_config = copy.deepcopy(config)
            agent, identity = new_initialized_agent(
                arm_config, device=device, log_dir=out / arm / "logs", seed=spec.seed)
            if common_identity is None:
                common_identity = identity
                summary["common_initialization"] = identity
                checkpoint(agent, "common_initial")
                panel(agent, "initial_primary")
            else:
                assert_common_initialization(common_identity, identity)
            arm_summary = {"status": "INCOMPLETE", "counts": {"transitions": 0},
                           "initialization": identity, "common_initialization_equal": True}
            summary["arms"][arm] = arm_summary
            summary["counts"]["fits_started"] += 1
            progress({"event": "fit_start", "arm": arm})
            train_arm(agent, arm_config, spec, arm=arm, out=out / arm,
                      summary=arm_summary, progress=progress)
            summary["counts"]["fits_completed"] += 1
            checkpoint(agent, arm + "/endpoint")
            progress({"event": "fit_complete", "arm": arm})
            panel(agent, arm + "_primary")
            del agent
            gc.collect()
            torch.cuda.empty_cache()
        summary["comparisons"] = {"primary": endpoint_comparison(
            summary["evaluations"]["initial_primary"],
            summary["evaluations"]["N_primary"],
            summary["evaluations"]["A_primary"])}
        counts = summary["counts"]
        expected_episodes = 3 * len(PRIMARY_SEEDS)
        if (counts["training_transitions"] != 2 * spec.transitions
                or counts["evaluation_episodes_completed"] != expected_episodes
                or counts["evaluation_episodes_attempted"] != expected_episodes
                or counts["evaluation_transitions"] > expected_episodes * spec.episode_length):
            raise RuntimeError("B09 actual batch exposure mismatch")
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update(wall_seconds=time.perf_counter() - started,
                       cpu_user_seconds=usage.ru_utime - cpu_start.ru_utime,
                       cpu_system_seconds=usage.ru_stime - cpu_start.ru_stime,
                       peak_rss_kib=int(usage.ru_maxrss), rss_scope="runner process high-water mark")
        progress({"event": "batch_exit", "status": summary["status"]})
