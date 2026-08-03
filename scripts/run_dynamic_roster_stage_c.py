"""Run and analyze the frozen paired F0/F1 Stage-C contract."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch


FORMAL_NUM_ENVS = 16
FORMAL_UPDATES = 250
FORMAL_STEPS_PER_ARM = 320_000
FORMAL_OPTIMIZER_STEPS = 1_000
FORMAL_EVAL_EPISODES = 256
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 107_057
PROCESS_CLEANUP_TIMEOUT_SECONDS = 5.0


def _git_source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    source_commit = completed.stdout.strip().lower()
    if len(source_commit) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit
    ):
        raise RuntimeError("Stage C source commit is not a full Git SHA")
    return source_commit


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_status(path: Path, **fields: Any) -> None:
    value = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _atomic_text(path, "".join(f"{key}={item}\n" for key, item in value.items()))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_text(
        path,
        json.dumps(dict(payload), ensure_ascii=False, indent=2, allow_nan=False),
    )


def _cleanup_direct_arm_processes(processes: Mapping[str, subprocess.Popen[Any]]) -> None:
    """Reap only direct Stage-C arm processes after an interrupted run."""

    for process in processes.values():
        if process.poll() is None:
            process.terminate()
    for process in processes.values():
        try:
            process.wait(timeout=PROCESS_CLEANUP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _read_arm_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "state": "starting",
            "phase": "starting",
            "update": 0,
            "steps": 0,
            "high_optimizer_steps": 0,
            "low_optimizer_steps": 0,
        }
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "state": "starting",
            "phase": "status_pending",
            "update": 0,
            "steps": 0,
            "high_optimizer_steps": 0,
            "low_optimizer_steps": 0,
        }
    return dict(value)


def _phase_fraction(status: Mapping[str, Any]) -> float:
    phase = str(status.get("phase", "starting"))
    if str(status.get("state")) == "complete":
        return 1.0
    if phase == "zero_evaluation":
        return 0.03
    if phase == "training":
        return 0.05 + 0.78 * min(
            max(float(status.get("steps", 0)) / FORMAL_STEPS_PER_ARM, 0.0), 1.0
        )
    if phase == "final_evaluation":
        return 0.86
    if phase == "forced_audit_and_stochastic_evaluation":
        return 0.91
    if str(status.get("state")) == "failed":
        return 0.0
    return 0.01


def _paired_ci(values: Sequence[float], *, seed: int) -> list[float]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if array.size <= 0 or not np.isfinite(array).all():
        raise ValueError("paired bootstrap requires finite non-empty values")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed)])))
    draws = np.empty(BOOTSTRAP_REPETITIONS, dtype=np.float64)
    for index in range(BOOTSTRAP_REPETITIONS):
        selected = rng.integers(0, array.size, array.size)
        draws[index] = float(np.mean(array[selected]))
    return [
        float(np.quantile(draws, 0.025)),
        float(np.mean(array)),
        float(np.quantile(draws, 0.975)),
    ]


def _tensor_mapping_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if set(left) != set(right):
        return False
    for key in left:
        lhs = left[key]
        rhs = right[key]
        if isinstance(lhs, torch.Tensor) or isinstance(rhs, torch.Tensor):
            if not torch.equal(torch.as_tensor(lhs).cpu(), torch.as_tensor(rhs).cpu()):
                return False
        elif isinstance(lhs, Mapping) and isinstance(rhs, Mapping):
            if not _tensor_mapping_equal(lhs, rhs):
                return False
        elif lhs != rhs:
            return False
    return True


def _initialization_equal(f0_checkpoint: Path, f1_checkpoint: Path) -> bool:
    f0 = torch.load(f0_checkpoint, map_location="cpu", weights_only=False)
    f1 = torch.load(f1_checkpoint, map_location="cpu", weights_only=False)
    left = f0["event_architecture"]
    right = f1["event_architecture"]
    model_fields = (
        "commitment_model_state",
        "event_critic_state",
        "low_actor_state",
        "low_critic_state",
    )
    return all(_tensor_mapping_equal(left[name], right[name]) for name in model_fields)


def _task_access(arm: Mapping[str, Any]) -> bool:
    final = arm["final"]["deterministic"]
    improvement = arm["paired_final_minus_zero_deterministic_utility_ci95"]
    return bool(
        float(final["utility_mean"]) >= 0.60
        and float(final["persistent_mean"]) >= 0.55
        and float(final["short_mean"]) >= 0.55
        and float(improvement[0]) > 0.10
    )


def _timing_read(f1: Mapping[str, Any]) -> dict[str, Any]:
    reactive = int(f1["forced_audit"]["reactive_like_skill"])
    persistent = int(f1["forced_audit"]["persistent_like_skill"])
    rows = list(f1.get("timing_rows", []))
    wave_rows: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        wave_index = row.get("wave_index")
        if wave_index is None:
            continue
        key = (int(row["episode_id"]), int(wave_index))
        wave_rows.setdefault(key, []).append(row)
    feasible_completion: dict[int, list[float]] = {}
    infeasible_completion: dict[int, list[float]] = {}
    uncompleted_total = 0
    timing_infeasible_uncompleted = 0
    opportunity_window_counts: list[int] = []
    for key, values in wave_rows.items():
        ordered = sorted(values, key=lambda row: int(row["physical_time"]))
        arrival = ordered[0]
        arrival_time = int(arrival["wave_arrival_time"])
        required = int(arrival["wave_required"])
        arrival_keys = [str(value) for value in arrival["active_keys"]]
        arrival_skills = [int(value) for value in arrival["active_skills"]]
        opportunities_by_deadline = {
            str(owner)
            for row in ordered
            if arrival_time <= int(row["physical_time"]) <= arrival_time + 2
            for owner in row["opportunity_keys_at_time"]
        }
        opportunity_window_counts.append(len(opportunities_by_deadline))
        available = sum(
            int(skill == reactive or owner in opportunities_by_deadline)
            for owner, skill in zip(arrival_keys, arrival_skills)
        )
        feasible = available >= required
        completed = int(ordered[-1]["wave_completed_after_action"])
        fraction = float(completed) / float(max(required, 1))
        target = feasible_completion if feasible else infeasible_completion
        target.setdefault(key[0], []).append(fraction)
        unfinished = max(required - completed, 0)
        uncompleted_total += unfinished
        if not feasible:
            timing_infeasible_uncompleted += unfinished
    episode_ids = sorted(
        set(feasible_completion).intersection(infeasible_completion)
    )
    differences = [
        float(np.mean(feasible_completion[episode_id]))
        - float(np.mean(infeasible_completion[episode_id]))
        for episode_id in episode_ids
    ]
    completion_ci = (
        _paired_ci(differences, seed=BOOTSTRAP_SEED + 3)
        if differences
        else [-1e30, 0.0, 1e30]
    )
    infeasible_fraction = float(timing_infeasible_uncompleted) / float(
        max(uncompleted_total, 1)
    )
    supported = bool(infeasible_fraction >= 0.25 and completion_ci[0] > 0.0)
    restore_delays: list[int] = []
    by_episode: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_episode.setdefault(int(row["episode_id"]), []).append(row)
    for episode_rows in by_episode.values():
        ordered = sorted(episode_rows, key=lambda row: int(row["physical_time"]))
        loss_time: int | None = None
        previous_owner = False
        for row in ordered:
            owner_exists = bool(row["persistent_owner_exists"])
            if previous_owner and not owner_exists:
                loss_time = int(row["physical_time"])
            if loss_time is not None and persistent in {
                int(skill) for skill in row["active_skills"]
            }:
                restore_delays.append(int(row["physical_time"]) - loss_time)
                loss_time = None
            previous_owner = owner_exists
    return {
        "waves": len(wave_rows),
        "opportunity_evidence_source": "natural_frontier_t_w_through_t_w_plus_2",
        "opportunity_window_member_counts": opportunity_window_counts,
        "uncompleted_work": uncompleted_total,
        "timing_infeasible_uncompleted_work": timing_infeasible_uncompleted,
        "timing_infeasible_uncompleted_fraction": infeasible_fraction,
        "feasible_minus_infeasible_completion_ci95": completion_ci,
        "persistent_commitment_restore_delays": restore_delays,
        "persistent_commitment_restore_delay_mean": (
            float(np.mean(restore_delays)) if restore_delays else None
        ),
        "conditional_h3_supported": supported,
    }


def _classify_outcome(
    *,
    implementation_valid: bool,
    h1_supported: bool,
    f0_task: bool,
    f1_task: bool,
    f0_skills: bool,
    f1_skills: bool,
    timing_prerequisites: bool,
    conditional_h3_supported: bool,
) -> tuple[str, str]:
    """Apply the registered Stage C outcome priority without interpretation."""

    if not implementation_valid:
        return (
            "INVALID_IMPLEMENTATION",
            "repair only the concrete Stage C M0 defect",
        )
    if h1_supported:
        return (
            "SUPPORT_H1_ON_TESTBED",
            "stop for a separate integration decision",
        )
    if f0_task:
        return (
            "SUPPORT_H0_STOP_AT_F0",
            "retire H1 and stop at F0",
        )
    if not f0_task and not f1_task and not f0_skills and not f1_skills:
        return (
            "SUPPORT_H2_SKILL_LIMIT",
            "record the skill bottleneck and stop without adding a module",
        )
    if timing_prerequisites and conditional_h3_supported:
        return (
            "CONDITIONAL_H3_TIMING_LIMIT",
            "record conditional timing evidence; do not enable learned timing",
        )
    return (
        "VALID_MIXED_UNCATEGORIZED",
        "stop without forced attribution or a successor toy",
    )


def _timing_prerequisites(
    *,
    f1_skills: bool,
    eligible_natural_rows: int,
    natural_prefix_tv: bool,
    directional_composition: bool,
    f1_minus_f0_utility: bool,
) -> bool:
    return bool(
        f1_skills
        and int(eligible_natural_rows) >= 1_024
        and natural_prefix_tv
        and directional_composition
        and not f1_minus_f0_utility
    )


def analyze_pair(
    *,
    output_root: Path,
    f0: Mapping[str, Any],
    f1: Mapping[str, Any],
    source_commit: str,
    run_id: str,
) -> dict[str, Any]:
    f0_zero = output_root / "f0" / "checkpoints" / "update_000_eval.pt"
    f1_zero = output_root / "f1" / "checkpoints" / "update_000_eval.pt"
    f0_det = f0["final"]["deterministic"]
    f1_det = f1["final"]["deterministic"]
    utility_difference = np.asarray(f1_det["utility"], dtype=np.float64) - np.asarray(
        f0_det["utility"], dtype=np.float64
    )
    utility_difference_ci = _paired_ci(utility_difference, seed=BOOTSTRAP_SEED)
    contract_f0 = dict(f0["contract"])
    contract_f1 = dict(f1["contract"])
    selector_pair = (
        contract_f0.pop("selector", None),
        contract_f1.pop("selector", None),
    )
    m0 = {
        "both_arms_implementation_valid": bool(f0["implementation_valid"])
        and bool(f1["implementation_valid"]),
        "paired_initialization_byte_equal": _initialization_equal(f0_zero, f1_zero),
        "selector_only_contract_difference": contract_f0 == contract_f1
        and selector_pair == ("initial_summary", "working_summary"),
        "paired_zero_ledgers_exact": f0["zero"]["deterministic"]["episode_ids"]
        == f1["zero"]["deterministic"]["episode_ids"]
        == list(range(FORMAL_EVAL_EPISODES)),
        "paired_final_ledgers_exact": f0_det["episode_ids"]
        == f1_det["episode_ids"]
        == list(range(FORMAL_EVAL_EPISODES)),
        "f0_common_support_tv": float(
            f0["prefix"]["f0_common_support_tv_max"]
        )
        <= 1e-6,
    }
    implementation_valid = all(bool(value) for value in m0.values())
    f0_task = _task_access(f0)
    f1_task = _task_access(f1)
    f0_skills = bool(
        f0["forced_audit"]["executable_naturally_used_skills"]
    )
    f1_skills = bool(
        f1["forced_audit"]["executable_naturally_used_skills"]
    )
    tv_ci = f1["prefix"]["working_initial_tv_ci95"]
    direction_ci = f1["prefix"]["directional_composition_shift_ci95"]
    h1_components = {
        "eligible_natural_rows": int(f1["prefix"]["eligible_natural_rows"])
        >= 1_024,
        "natural_prefix_tv": float(tv_ci[0]) > 0.02,
        "f0_reduction": bool(m0["f0_common_support_tv"]),
        "directional_composition": float(direction_ci[0]) > 0.02,
        "f1_minus_f0_utility": float(utility_difference_ci[0]) > 0.03,
        "f1_utility": float(f1_det["utility_mean"]) >= 0.60,
        "f1_persistent": float(f1_det["persistent_mean"]) >= 0.55,
        "f1_short": float(f1_det["short_mean"]) >= 0.55,
        "f1_executable_skills": f1_skills,
    }
    h1_supported = all(bool(value) for value in h1_components.values())
    timing_prerequisites = _timing_prerequisites(
        f1_skills=f1_skills,
        eligible_natural_rows=int(f1["prefix"]["eligible_natural_rows"]),
        natural_prefix_tv=bool(h1_components["natural_prefix_tv"]),
        directional_composition=bool(h1_components["directional_composition"]),
        f1_minus_f0_utility=bool(h1_components["f1_minus_f0_utility"]),
    )
    timing = _timing_read(f1) if timing_prerequisites else {
        "read_permitted": False,
        "conditional_h3_supported": False,
    }
    status, next_action = _classify_outcome(
        implementation_valid=implementation_valid,
        h1_supported=h1_supported,
        f0_task=f0_task,
        f1_task=f1_task,
        f0_skills=f0_skills,
        f1_skills=f1_skills,
        timing_prerequisites=timing_prerequisites,
        conditional_h3_supported=bool(timing["conditional_h3_supported"]),
    )
    f0_prefix_summary = {
        key: value for key, value in f0["prefix"].items() if key != "rows"
    }
    f1_prefix_summary = {
        key: value for key, value in f1["prefix"].items() if key != "rows"
    }
    f0_forced_summary = {
        key: value for key, value in f0["forced_audit"].items() if key != "effects"
    }
    f1_forced_summary = {
        key: value for key, value in f1["forced_audit"].items() if key != "effects"
    }
    return {
        "schema_version": 1,
        "stage": "stage_c_paired_f0_f1",
        "contract": {
            "stage": "stage_c_paired_f0_f1",
            "contract_version": 1,
            "source_commit": source_commit,
            "run_id": run_id,
            "sole_treatment_selector": {
                "f0": selector_pair[0],
                "f1": selector_pair[1],
            },
            "frozen_environment_and_training_config": {
                "scenario": "generic_short_dynamic_roster",
                "membership_schedule": [4, 2, 6, 4],
                "reward": "terminal_external_utility_only",
                **contract_f0,
            },
            "seed_and_ledger_map": {
                "paired_model_initialization": 57_057,
                "training_task_ledger": 67_057,
                "event_opportunity_and_order": 77_057,
                "policy_action_sampling": 87_057,
                "evaluation_ledger": 97_057,
                "bootstrap": BOOTSTRAP_SEED,
                "training_episode_ids": [0, 3_999],
                "evaluation_episode_ids": [0, FORMAL_EVAL_EPISODES - 1],
            },
        },
        "status": status,
        "implementation_valid": implementation_valid,
        "environment_steps": 2 * FORMAL_STEPS_PER_ARM,
        "optimizer_steps": 4 * FORMAL_OPTIMIZER_STEPS,
        "m0": m0,
        "hypotheses": {
            "f0_task_sufficiency": f0_task,
            "f1_task_access": f1_task,
            "f0_executable_skills": f0_skills,
            "f1_executable_skills": f1_skills,
            "h1_components": h1_components,
            "h1_supported": h1_supported,
            "timing_prerequisites": timing_prerequisites,
            "timing": timing,
        },
        "paired_f1_minus_f0_final_deterministic_utility_ci95": utility_difference_ci,
        "arm_summary": {
            "f0": {
                "utility": f0_det["utility_mean"],
                "persistent": f0_det["persistent_mean"],
                "short": f0_det["short_mean"],
                "prefix": f0_prefix_summary,
                "forced_audit": f0_forced_summary,
                "result_path": str(output_root / "f0" / "result" / "stage_c_arm.json"),
            },
            "f1": {
                "utility": f1_det["utility_mean"],
                "persistent": f1_det["persistent_mean"],
                "short": f1_det["short_mean"],
                "prefix": f1_prefix_summary,
                "forced_audit": f1_forced_summary,
                "result_path": str(output_root / "f1" / "result" / "stage_c_arm.json"),
            },
        },
        "thresholds": {
            "f0_utility_min": 0.60,
            "f0_persistent_min": 0.55,
            "f0_short_min": 0.55,
            "f0_improvement_lcb_exclusive": 0.10,
            "eligible_prefix_rows_min": 1_024,
            "prefix_tv_lcb_exclusive": 0.02,
            "direction_lcb_exclusive": 0.02,
            "f1_minus_f0_utility_lcb_exclusive": 0.03,
            "f0_tv_max": 1e-6,
        },
        "authoritative_status_source": str(output_root / "runner_status.txt"),
        "next_action": next_action,
    }


def _arm_command(
    *,
    python: str,
    mode: str,
    output_root: Path,
    resume: Path | None,
) -> list[str]:
    command = [
        python,
        "-B",
        "-m",
        "ha_ctse_process.train",
        "--mode",
        "train",
        "--config",
        "ha_ctse_process.config",
        "--scenario",
        "generic_short_dynamic_roster",
        "--high_controller",
        "variable_roster_event",
        "--event_architecture_mode",
        mode,
        "--num_envs",
        "16",
        "--collector_backend",
        "subproc",
        "--collector_start_method",
        "spawn",
        "--device",
        "cuda",
        "--rollout_length",
        "80",
        "--total_timesteps",
        "320000",
        "--save_interval",
        "10",
        "--eval_interval",
        "0",
        "--plot_interval",
        "0",
        "--log_dir",
        str(output_root),
    ]
    if resume is not None:
        command.extend(("--resume_from", str(resume)))
    return command


def _preflight_validate(commands: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    """Validate the frozen package without constructing an environment or trainer."""

    from ha_ctse_process.config import Config
    from ha_ctse_process.standalone_contracts import (
        enforce_variable_roster_event_contract,
    )
    from ha_ctse_process.variable_roster_event import (
        CHECKPOINT_SCHEMA_VERSION,
        EVENT_ARCHITECTURE_SCHEMA_VERSION,
        EVENT_CONTROLLER,
        OPPORTUNITY_SCHEDULE_NAME,
        validate_event_runtime_configuration,
    )

    expected_flags = {
        "--scenario": "generic_short_dynamic_roster",
        "--high_controller": EVENT_CONTROLLER,
        "--num_envs": str(FORMAL_NUM_ENVS),
        "--collector_backend": "subproc",
        "--collector_start_method": "spawn",
        "--device": "cuda",
        "--rollout_length": "80",
        "--total_timesteps": str(FORMAL_STEPS_PER_ARM),
        "--save_interval": "10",
        "--eval_interval": "0",
        "--plot_interval": "0",
    }
    headers = {}
    for mode in ("f0", "f1"):
        command = list(commands[mode])
        for flag, expected in expected_flags.items():
            if flag not in command or command[command.index(flag) + 1] != expected:
                raise ValueError(f"Stage C preflight command mismatch: {mode} {flag}")
        if command[command.index("--event_architecture_mode") + 1] != mode:
            raise ValueError(f"Stage C preflight selector mismatch: {mode}")
        config = Config()
        config.high_controller = EVENT_CONTROLLER
        config.event_architecture_mode = mode
        config.event_architecture_schema_version = EVENT_ARCHITECTURE_SCHEMA_VERSION
        config.event_opportunity_schedule = OPPORTUNITY_SCHEDULE_NAME
        validation_args = SimpleNamespace()
        enforce_variable_roster_event_contract(config, validation_args, None)
        headers[mode] = validate_event_runtime_configuration(config)
    package_paths = [
        PROJECT_ROOT / "ha_ctse_process" / "variable_roster_event.py",
        PROJECT_ROOT / "ha_ctse_process" / "train.py",
        PROJECT_ROOT / "scripts" / "run_dynamic_roster_stage_c.py",
    ]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Stage C preflight package is incomplete: {missing}")
    if (
        CHECKPOINT_SCHEMA_VERSION != 3
        or EVENT_ARCHITECTURE_SCHEMA_VERSION != 1
        or FORMAL_UPDATES * 4 != FORMAL_OPTIMIZER_STEPS
        or FORMAL_NUM_ENVS * 80 * FORMAL_UPDATES != FORMAL_STEPS_PER_ARM
    ):
        raise ValueError("Stage C preflight frozen header or budget mismatch")
    return {
        "config_headers": headers,
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "package_files": [str(path) for path in package_paths],
        "commands_validated": 2,
    }


def run_pair(args: argparse.Namespace) -> dict[str, Any]:
    output_root = args.output_root.resolve()
    result_path = output_root / "result" / "stage_c_f0_f1.json"
    error_path = output_root / "runner_stderr.log"
    status_path = output_root / "runner_status.txt"
    arm_roots = {mode: output_root / mode for mode in ("f0", "f1")}
    commands = {
        "f0": _arm_command(
            python=args.python,
            mode="f0",
            output_root=arm_roots["f0"],
            resume=args.resume_f0,
        ),
        "f1": _arm_command(
            python=args.python,
            mode="f1",
            output_root=arm_roots["f1"],
            resume=args.resume_f1,
        ),
    }
    preflight = _preflight_validate(commands)
    if args.dry_validate:
        return {
            "status": "DRY_VALID",
            "environment_steps": 0,
            "optimizer_steps": 0,
            "commands": commands,
            "preflight": preflight,
            "contract": {
                "num_envs_per_arm": FORMAL_NUM_ENVS,
                "steps_per_arm": FORMAL_STEPS_PER_ARM,
                "updates": FORMAL_UPDATES,
                "optimizer_steps_per_path": FORMAL_OPTIMIZER_STEPS,
                "concurrent_arms": True,
            },
        }
    output_root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    run_id = output_root.name
    source_commit = ""
    handles = {}
    processes = {}
    last_statuses = {
        mode: {"phase": "starting", "update": 0, "steps": 0}
        for mode in ("f0", "f1")
    }
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        source_commit = _git_source_commit()
        for mode in ("f0", "f1"):
            arm_roots[mode].mkdir(parents=True, exist_ok=True)
            stdout = (arm_roots[mode] / "worker_stdout.log").open(
                "a", encoding="utf-8"
            )
            stderr = (arm_roots[mode] / "worker_stderr.log").open(
                "a", encoding="utf-8"
            )
            handles[mode] = (stdout, stderr)
            processes[mode] = subprocess.Popen(
                commands[mode],
                cwd=PROJECT_ROOT,
                stdout=stdout,
                stderr=stderr,
                env=environment,
            )
        while True:
            statuses = {
                mode: _read_arm_status(arm_roots[mode] / "arm_status.json")
                for mode in ("f0", "f1")
            }
            last_statuses = statuses
            fractions = [_phase_fraction(statuses[mode]) for mode in ("f0", "f1")]
            progress = float(np.mean(fractions))
            elapsed = time.perf_counter() - started
            eta = (
                int(max(elapsed * (1.0 - progress) / progress, 0.0))
                if progress > 0.01
                else -1
            )
            phases = {str(statuses[mode].get("phase")) for mode in ("f0", "f1")}
            root_phase = phases.pop() if len(phases) == 1 else "paired_mixed_phase"
            _write_status(
                status_path,
                state="running",
                phase=root_phase,
                run_id=run_id,
                source_commit=source_commit,
                f0_pid=processes["f0"].pid,
                f1_pid=processes["f1"].pid,
                f0_phase=statuses["f0"].get("phase", "starting"),
                f0_update=statuses["f0"].get("update", 0),
                f0_updates_total=FORMAL_UPDATES,
                f0_steps=statuses["f0"].get("steps", 0),
                f0_steps_total=FORMAL_STEPS_PER_ARM,
                f0_high_optimizer_steps=statuses["f0"].get(
                    "high_optimizer_steps", 0
                ),
                f0_low_optimizer_steps=statuses["f0"].get(
                    "low_optimizer_steps", 0
                ),
                f0_optimizer_steps_total=FORMAL_OPTIMIZER_STEPS,
                f1_phase=statuses["f1"].get("phase", "starting"),
                f1_update=statuses["f1"].get("update", 0),
                f1_updates_total=FORMAL_UPDATES,
                f1_steps=statuses["f1"].get("steps", 0),
                f1_steps_total=FORMAL_STEPS_PER_ARM,
                f1_high_optimizer_steps=statuses["f1"].get(
                    "high_optimizer_steps", 0
                ),
                f1_low_optimizer_steps=statuses["f1"].get(
                    "low_optimizer_steps", 0
                ),
                f1_optimizer_steps_total=FORMAL_OPTIMIZER_STEPS,
                progress_fraction=f"{progress:.6f}",
                eta_seconds=eta,
                result_path=result_path,
                error_path=error_path,
            )
            return_codes = {mode: process.poll() for mode, process in processes.items()}
            if any(code not in (None, 0) for code in return_codes.values()):
                raise RuntimeError(f"Stage C arm failure: {return_codes}")
            if all(code == 0 for code in return_codes.values()):
                break
            time.sleep(max(float(args.poll_seconds), 1.0))
        _write_status(
            status_path,
            state="running",
            phase="analysis",
            run_id=run_id,
            source_commit=source_commit,
            f0_phase="terminal",
            f0_update=250,
            f0_updates_total=250,
            f0_steps=320_000,
            f0_steps_total=320_000,
            f0_high_optimizer_steps=1_000,
            f0_low_optimizer_steps=1_000,
            f0_optimizer_steps_total=1_000,
            f1_phase="terminal",
            f1_update=250,
            f1_updates_total=250,
            f1_steps=320_000,
            f1_steps_total=320_000,
            f1_high_optimizer_steps=1_000,
            f1_low_optimizer_steps=1_000,
            f1_optimizer_steps_total=1_000,
            eta_seconds=0,
            result_path=result_path,
            error_path=error_path,
        )
        f0 = json.loads(
            (arm_roots["f0"] / "result" / "stage_c_arm.json").read_text(
                encoding="utf-8"
            )
        )
        f1 = json.loads(
            (arm_roots["f1"] / "result" / "stage_c_arm.json").read_text(
                encoding="utf-8"
            )
        )
        result = analyze_pair(
            output_root=output_root,
            f0=f0,
            f1=f1,
            source_commit=source_commit,
            run_id=run_id,
        )
        result["wall_seconds"] = time.perf_counter() - started
        result_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(result_path, result)
        _write_status(
            status_path,
            state="complete",
            phase="terminal",
            run_id=run_id,
            source_commit=source_commit,
            status=result["status"],
            f0_phase="terminal",
            f0_update=250,
            f0_steps=320_000,
            f0_high_optimizer_steps=1_000,
            f0_low_optimizer_steps=1_000,
            f1_phase="terminal",
            f1_update=250,
            f1_steps=320_000,
            f1_high_optimizer_steps=1_000,
            f1_low_optimizer_steps=1_000,
            result_path=result_path,
            error_path=error_path,
        )
        return result
    except Exception as exc:
        _atomic_text(error_path, traceback.format_exc())
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            run_id=run_id,
            source_commit=source_commit,
            error=f"{type(exc).__name__}: {exc}",
            f0_phase=last_statuses["f0"].get("phase", "starting"),
            f0_update=last_statuses["f0"].get("update", 0),
            f0_steps=last_statuses["f0"].get("steps", 0),
            f0_high_optimizer_steps=last_statuses["f0"].get(
                "high_optimizer_steps", 0
            ),
            f0_low_optimizer_steps=last_statuses["f0"].get(
                "low_optimizer_steps", 0
            ),
            f1_phase=last_statuses["f1"].get("phase", "starting"),
            f1_update=last_statuses["f1"].get("update", 0),
            f1_steps=last_statuses["f1"].get("steps", 0),
            f1_high_optimizer_steps=last_statuses["f1"].get(
                "high_optimizer_steps", 0
            ),
            f1_low_optimizer_steps=last_statuses["f1"].get(
                "low_optimizer_steps", 0
            ),
            result_path=result_path,
            error_path=error_path,
        )
        raise
    finally:
        try:
            _cleanup_direct_arm_processes(processes)
        finally:
            for stdout, stderr in handles.values():
                stdout.close()
                stderr.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    parser.add_argument("--resume-f0", type=Path)
    parser.add_argument("--resume-f1", type=Path)
    parser.add_argument("--dry-validate", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_pair(args)
    print(
        json.dumps(
            {
                "status": result["status"],
                "environment_steps": result.get("environment_steps"),
                "optimizer_steps": result.get("optimizer_steps"),
                "result": str(args.output_root / "result" / "stage_c_f0_f1.json"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
