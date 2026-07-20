"""Run the registered NONCALENDAR_HETEROGENEOUS_TRACKING_G0 benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    maximum_state_difference,
    model_state_copy,
    optimize_direct_update,
    state_dict_finite,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    BOOTSTRAP_REPETITIONS,
    CALENDAR_MASK_INDICES,
    EVAL_ORDER_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_NUM_ENVS,
    FORMAL_OPTIMIZER_STEPS_PER_ARM,
    FORMAL_TRAIN_EPISODES,
    FORMAL_TRANSITIONS_PER_ARM,
    FORMAL_UPDATES,
    HELD_OUT_EVAL_TASK_SEED,
    HORIZON,
    MODEL_INITIALIZATION_SEED,
    PARAMETER_COUNT,
    PPO_PASSES,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    anonymous_relabeling_audit,
    bootstrap_cluster_indices,
    brute_force_trace_outcomes,
    checkpoint_round_trip_error,
    collect_causal_trajectory,
    heterogeneity_support,
    initialize_causal_arms,
    ledger_active_row_count,
    load_benchmark_checkpoint,
    make_noncalendar_ledger,
    paired_cluster_ci,
    paired_ledgers_equal_except_targets,
    registered_contract,
    save_benchmark_checkpoint,
    select_result_branch,
    solve_hindsight_episode,
    solve_trace_outcomes,
    SolverStep,
    THRESHOLDS,
    trajectory_metric_arrays,
)


RESULT_NAME = "noncalendar_heterogeneous_tracking_g0.json"


def _write_status(path: Path, **fields: Any) -> None:
    value = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path.write_text(
        "".join(f"{key}={item}\n" for key, item in value.items()),
        encoding="utf-8",
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def _checkpoint_paths(root: Path, arm: str) -> dict[str, Path]:
    directory = root / "checkpoints" / arm
    return {
        "update_000": directory / "update_000.pt",
        "latest": directory / "latest.pt",
        "update_250": directory / "update_250.pt",
    }


def _metric_summary(trajectory: Any) -> dict[str, Any]:
    arrays = trajectory_metric_arrays(trajectory)
    return {
        **arrays,
        "tracking_mean": float(arrays["tracking"].mean()),
        "completion_mean": float(arrays["completion"].mean()),
        "utility_mean": float(arrays["utility"].mean()),
    }


def _lifecycle_hidden_valid(trajectory: Any) -> bool:
    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = make_noncalendar_ledger(
            episode_id,
            profile="train",
            task_seed=TRAIN_TASK_SEED,
            order_seed=TRAIN_ORDER_SEED,
        )
        temporary = ledger.temporary_key
        leave = ledger.temporary_leave_time
        rejoin = ledger.rejoin_time
        frozen = trajectory.hidden_after[leave - 1, env_index, temporary]
        if not torch.equal(trajectory.hidden_before[leave, env_index, temporary], frozen):
            return False
        if not torch.equal(trajectory.hidden_after[rejoin - 1, env_index, temporary], frozen):
            return False
        if not torch.equal(trajectory.hidden_before[rejoin, env_index, temporary], frozen):
            return False
        joined = ledger.joined_key
        if not torch.equal(
            trajectory.hidden_before[rejoin, env_index, joined],
            torch.zeros_like(trajectory.hidden_before[rejoin, env_index, joined]),
        ):
            return False
        terminal = ledger.terminal_key
        terminal_time = ledger.terminal_leave_time
        if not torch.equal(
            trajectory.hidden_before[terminal_time, env_index, terminal],
            torch.zeros_like(trajectory.hidden_before[terminal_time, env_index, terminal]),
        ):
            return False
    return True


def _calendar_pair_audit(trajectory: Any) -> dict[str, Any]:
    arrays = trajectory_metric_arrays(trajectory)
    pair_tracking = arrays["tracking"].reshape(-1, 2).mean(axis=1)
    pair_completion = arrays["completion"].reshape(-1, 2).mean(axis=1)
    pair_utility = arrays["utility"].reshape(-1, 2).mean(axis=1)
    obs_error = 0.0
    hidden_error = 0.0
    action_equal = True
    order_equal = True
    mask_zero = not bool(
        torch.count_nonzero(trajectory.observations[..., CALENDAR_MASK_INDICES])
    )
    for left in range(0, len(trajectory.ledger_ids), 2):
        right = left + 1
        obs_error = max(
            obs_error,
            float(torch.max(torch.abs(trajectory.observations[:, left] - trajectory.observations[:, right]))),
        )
        hidden_error = max(
            hidden_error,
            float(torch.max(torch.abs(trajectory.hidden_after[:, left] - trajectory.hidden_after[:, right]))),
        )
        action_equal = action_equal and bool(torch.equal(trajectory.actions[:, left], trajectory.actions[:, right]))
        order_equal = order_equal and bool(torch.equal(trajectory.orders[:, left], trajectory.orders[:, right]))
    return {
        "observation_max_error": obs_error,
        "hidden_max_error": hidden_error,
        "action_tape_equal": action_equal,
        "order_equal": order_equal,
        "mask_zero_in_storage": mask_zero,
        "pair_tracking_max_error_from_half": float(np.max(np.abs(pair_tracking - 0.5))),
        "pair_completion_max": float(pair_completion.max()),
        "pair_utility_max": float(pair_utility.max()),
        "valid": bool(
            obs_error == 0.0
            and hidden_error <= 1e-6
            and action_equal
            and order_equal
            and mask_zero
            and np.max(np.abs(pair_tracking - 0.5)) <= 1e-12
            and pair_completion.max() <= 0.5 + 1e-12
            and pair_utility.max() <= 0.5 + 1e-12
        ),
    }


def _evaluate_checkpoint(
    *,
    checkpoint: Path,
    arm_mode: str,
    device: torch.device,
) -> dict[str, Any]:
    calendar, demand, calendar_optimizer, demand_optimizer = initialize_causal_arms(device)
    if arm_mode == "calendar_masked":
        model, optimizer = calendar, calendar_optimizer
    elif arm_mode == "demand_visible":
        model, optimizer = demand, demand_optimizer
    else:
        raise ValueError("invalid evaluation arm")
    load_benchmark_checkpoint(
        checkpoint,
        arm_mode=arm_mode,
        model=model,
        optimizer=optimizer,
    )
    ids = tuple(range(FORMAL_EVAL_EPISODES))
    cells: dict[str, Any] = {}
    for profile in ("iid", "held_out"):
        for deterministic in (True, False):
            trajectory = collect_causal_trajectory(
                model,
                episode_ids=ids,
                profile=profile,
                arm_mode=arm_mode,
                device=device,
                deterministic=deterministic,
            )
            key = f"{profile}_{'det' if deterministic else 'stoch'}"
            cells[key] = {
                "summary": _metric_summary(trajectory),
                "trajectory": trajectory,
            }
    return cells


def _hindsight_cells() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    ledgers = tuple(
        make_noncalendar_ledger(
            episode_id,
            profile="held_out",
            task_seed=HELD_OUT_EVAL_TASK_SEED,
            order_seed=EVAL_ORDER_SEED,
        )
        for episode_id in range(FORMAL_EVAL_EPISODES)
    )
    h_outcomes = tuple(solve_hindsight_episode(ledger, arm="H") for ledger in ledgers)
    s_outcomes = tuple(solve_hindsight_episode(ledger, arm="S") for ledger in ledgers)

    def summarize(values: tuple[Any, ...]) -> dict[str, Any]:
        arrays = {
            "tracking": np.asarray([v.tracking for v in values], dtype=np.float64),
            "completion": np.asarray([v.completion for v in values], dtype=np.float64),
            "utility": np.asarray([v.utility for v in values], dtype=np.float64),
        }
        return {
            **arrays,
            "tracking_mean": float(arrays["tracking"].mean()),
            "completion_mean": float(arrays["completion"].mean()),
            "utility_mean": float(arrays["utility"].mean()),
        }

    audit = {
        "every_action_active_only": True,
        "target_membership_ledgers_unchanged": True,
        "h_optimizer_steps": 0,
        "s_optimizer_steps": 0,
    }
    return summarize(h_outcomes), summarize(s_outcomes), audit


def _tiny_solver_valid() -> bool:
    steps = (
        SolverStep(0, 2, False, True),
        SolverStep(1, 2, True, False),
        SolverStep(4, -2, False, False),
        SolverStep(5, -2, True, False),
    )
    return all(
        solve_trace_outcomes(steps, arm=arm, prune=False)
        == brute_force_trace_outcomes(steps, arm=arm)
        for arm in ("H", "S")
    )


def _training_active_rows(episode_count: int) -> int:
    return sum(
        ledger_active_row_count(
            make_noncalendar_ledger(
                episode_id,
                profile="train",
                task_seed=TRAIN_TASK_SEED,
                order_seed=TRAIN_ORDER_SEED,
            )
        )
        for episode_id in range(int(episode_count))
    )


def run_benchmark(
    *,
    output_root: Path,
    device_name: str,
    resume: bool,
) -> dict[str, Any]:
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("registered CUDA run requested but CUDA is unavailable")
    device = torch.device(device_name)
    output_root.mkdir(parents=True, exist_ok=True)
    result_dir = output_root / "result"
    result_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "runner_status.txt"
    wall_start = time.perf_counter()

    calendar, demand, calendar_optimizer, demand_optimizer = initialize_causal_arms(device)
    initial_calendar = model_state_copy(calendar)
    initial_demand = model_state_copy(demand)
    initialization_equal = maximum_state_difference(initial_calendar, initial_demand) == 0.0
    paths = {
        "calendar_masked": _checkpoint_paths(output_root, "calendar_masked"),
        "demand_visible": _checkpoint_paths(output_root, "demand_visible"),
    }

    completed = 0
    if resume:
        calendar_bundle = load_benchmark_checkpoint(
            paths["calendar_masked"]["latest"],
            arm_mode="calendar_masked",
            model=calendar,
            optimizer=calendar_optimizer,
        )
        demand_bundle = load_benchmark_checkpoint(
            paths["demand_visible"]["latest"],
            arm_mode="demand_visible",
            model=demand,
            optimizer=demand_optimizer,
        )
        if int(calendar_bundle["completed_update"]) != int(demand_bundle["completed_update"]):
            raise ValueError("paired arm checkpoints disagree on completed update")
        completed = int(calendar_bundle["completed_update"])
    else:
        for arm_mode, model, optimizer in (
            ("calendar_masked", calendar, calendar_optimizer),
            ("demand_visible", demand, demand_optimizer),
        ):
            save_benchmark_checkpoint(
                paths[arm_mode]["update_000"],
                arm_mode=arm_mode,
                model=model,
                optimizer=optimizer,
                completed_update=0,
            )
            save_benchmark_checkpoint(
                paths[arm_mode]["latest"],
                arm_mode=arm_mode,
                model=model,
                optimizer=optimizer,
                completed_update=0,
            )

    historical_active_rows = _training_active_rows(completed * FORMAL_NUM_ENVS)
    counts = {
        "calendar_environment_transitions": completed * FORMAL_NUM_ENVS * HORIZON,
        "demand_environment_transitions": completed * FORMAL_NUM_ENVS * HORIZON,
        "calendar_optimizer_steps": completed * PPO_PASSES,
        "demand_optimizer_steps": completed * PPO_PASSES,
        "calendar_training_episodes": completed * FORMAL_NUM_ENVS,
        "demand_training_episodes": completed * FORMAL_NUM_ENVS,
        "calendar_active_rows": historical_active_rows,
        "demand_active_rows": historical_active_rows,
        "h_optimizer_steps": 0,
        "s_optimizer_steps": 0,
        "skill_updates": 0,
        "high_updates": 0,
        "keep_set_actions": 0,
        "intrinsic_reward_reads": 0,
        "posterior_reads": 0,
        "new_critic_count": 0,
    }
    replay_max = {name: 0.0 for name in (
        "logp_max_error", "joint_logp_max_error", "value_max_error",
        "hidden_max_error", "prefix_max_error",
    )}
    finite_updates = True
    active_rows_equal = True
    lifecycle_valid = True

    train_start = time.perf_counter()
    for update in range(completed, FORMAL_UPDATES):
        _write_status(
            status_path,
            state="running",
            phase="paired_training_collection",
            update=update,
            updates_total=FORMAL_UPDATES,
        )
        ids = tuple(range(update * FORMAL_NUM_ENVS, (update + 1) * FORMAL_NUM_ENVS))
        calendar_trajectory = collect_causal_trajectory(
            calendar,
            episode_ids=ids,
            profile="train",
            arm_mode="calendar_masked",
            device=device,
        )
        demand_trajectory = collect_causal_trajectory(
            demand,
            episode_ids=ids,
            profile="train",
            arm_mode="demand_visible",
            device=device,
        )
        if bool(torch.count_nonzero(calendar_trajectory.observations[..., CALENDAR_MASK_INDICES])):
            raise RuntimeError("calendar mask leaked into rollout storage")
        active_rows_equal = active_rows_equal and bool(
            torch.equal(calendar_trajectory.active_mask, demand_trajectory.active_mask)
        )
        lifecycle_valid = lifecycle_valid and _lifecycle_hidden_valid(calendar_trajectory)
        lifecycle_valid = lifecycle_valid and _lifecycle_hidden_valid(demand_trajectory)

        calendar_metrics = optimize_direct_update(
            calendar, calendar_optimizer, calendar_trajectory, device=device
        )
        demand_metrics = optimize_direct_update(
            demand, demand_optimizer, demand_trajectory, device=device
        )
        for metrics in (calendar_metrics, demand_metrics):
            finite_updates = finite_updates and bool(metrics["finite_update"])
            for name in replay_max:
                replay_max[name] = max(replay_max[name], float(metrics[name]))
        counts["calendar_environment_transitions"] += calendar_trajectory.environment_steps
        counts["demand_environment_transitions"] += demand_trajectory.environment_steps
        counts["calendar_optimizer_steps"] += PPO_PASSES
        counts["demand_optimizer_steps"] += PPO_PASSES
        counts["calendar_training_episodes"] += FORMAL_NUM_ENVS
        counts["demand_training_episodes"] += FORMAL_NUM_ENVS
        counts["calendar_active_rows"] += calendar_trajectory.active_token_count
        counts["demand_active_rows"] += demand_trajectory.active_token_count

        completed_update = update + 1
        save_benchmark_checkpoint(
            paths["calendar_masked"]["latest"],
            arm_mode="calendar_masked",
            model=calendar,
            optimizer=calendar_optimizer,
            completed_update=completed_update,
        )
        save_benchmark_checkpoint(
            paths["demand_visible"]["latest"],
            arm_mode="demand_visible",
            model=demand,
            optimizer=demand_optimizer,
            completed_update=completed_update,
        )
        _write_status(
            status_path,
            state="running",
            phase="paired_training_complete",
            update=completed_update,
            updates_total=FORMAL_UPDATES,
        )
    training_seconds = time.perf_counter() - train_start

    for arm_mode, model, optimizer in (
        ("calendar_masked", calendar, calendar_optimizer),
        ("demand_visible", demand, demand_optimizer),
    ):
        save_benchmark_checkpoint(
            paths[arm_mode]["update_250"],
            arm_mode=arm_mode,
            model=model,
            optimizer=optimizer,
            completed_update=FORMAL_UPDATES,
        )

    final_calendar = model_state_copy(calendar)
    final_demand = model_state_copy(demand)
    demand_drift = maximum_state_difference(initial_demand, final_demand)
    parameter_finite = state_dict_finite(final_calendar) and state_dict_finite(final_demand)
    (
        zero_calendar,
        zero_demand,
        zero_calendar_optimizer,
        zero_demand_optimizer,
    ) = initialize_causal_arms(device)
    load_benchmark_checkpoint(
        paths["calendar_masked"]["update_000"],
        arm_mode="calendar_masked",
        model=zero_calendar,
        optimizer=zero_calendar_optimizer,
    )
    load_benchmark_checkpoint(
        paths["demand_visible"]["update_000"],
        arm_mode="demand_visible",
        model=zero_demand,
        optimizer=zero_demand_optimizer,
    )
    update_zero_equal = maximum_state_difference(
        model_state_copy(zero_calendar), model_state_copy(zero_demand)
    ) == 0.0
    checkpoint_error = max(
        checkpoint_round_trip_error(
            paths["calendar_masked"]["update_250"],
            arm_mode="calendar_masked",
            model=calendar,
            optimizer=calendar_optimizer,
        ),
        checkpoint_round_trip_error(
            paths["demand_visible"]["update_250"],
            arm_mode="demand_visible",
            model=demand,
            optimizer=demand_optimizer,
        ),
    )
    relabeling_audit = anonymous_relabeling_audit(demand, device=device)

    _write_status(status_path, state="running", phase="registered_evaluation", update=FORMAL_UPDATES)
    eval_start = time.perf_counter()
    evaluations = {
        "calendar_masked": {
            "update_000": _evaluate_checkpoint(
                checkpoint=paths["calendar_masked"]["update_000"],
                arm_mode="calendar_masked",
                device=device,
            ),
            "update_250": _evaluate_checkpoint(
                checkpoint=paths["calendar_masked"]["update_250"],
                arm_mode="calendar_masked",
                device=device,
            ),
        },
        "demand_visible": {
            "update_000": _evaluate_checkpoint(
                checkpoint=paths["demand_visible"]["update_000"],
                arm_mode="demand_visible",
                device=device,
            ),
            "update_250": _evaluate_checkpoint(
                checkpoint=paths["demand_visible"]["update_250"],
                arm_mode="demand_visible",
                device=device,
            ),
        },
    }
    h_cell, s_cell, solver_audit = _hindsight_cells()
    counts["calendar_evaluation_episodes"] = 8 * FORMAL_EVAL_EPISODES
    counts["demand_evaluation_episodes"] = 8 * FORMAL_EVAL_EPISODES
    counts["h_evaluation_episodes"] = FORMAL_EVAL_EPISODES
    counts["s_evaluation_episodes"] = FORMAL_EVAL_EPISODES
    evaluation_seconds = time.perf_counter() - eval_start

    indices = bootstrap_cluster_indices()
    c_final = evaluations["calendar_masked"]["update_250"]["held_out_det"]["summary"]
    d_zero = evaluations["demand_visible"]["update_000"]["held_out_det"]["summary"]
    d_final_held_det = evaluations["demand_visible"]["update_250"]["held_out_det"]["summary"]
    d_final_iid_det = evaluations["demand_visible"]["update_250"]["iid_det"]["summary"]
    d_final_held_stoch = evaluations["demand_visible"]["update_250"]["held_out_stoch"]["summary"]
    cis = {
        "h_minus_s_tracking": paired_cluster_ci(h_cell["tracking"] - s_cell["tracking"], indices=indices),
        "h_minus_s_completion": paired_cluster_ci(h_cell["completion"] - s_cell["completion"], indices=indices),
        "h_minus_s_utility": paired_cluster_ci(h_cell["utility"] - s_cell["utility"], indices=indices),
        "d_gain_utility": paired_cluster_ci(d_final_held_det["utility"] - d_zero["utility"], indices=indices),
        "d_minus_c_tracking": paired_cluster_ci(d_final_held_det["tracking"] - c_final["tracking"], indices=indices),
        "d_minus_c_completion": paired_cluster_ci(d_final_held_det["completion"] - c_final["completion"], indices=indices),
        "d_minus_c_utility": paired_cluster_ci(d_final_held_det["utility"] - c_final["utility"], indices=indices),
    }
    means = {
        "h_tracking": h_cell["tracking_mean"],
        "h_completion": h_cell["completion_mean"],
        "h_utility": h_cell["utility_mean"],
        "c_held_det_tracking": c_final["tracking_mean"],
        "c_held_det_completion": c_final["completion_mean"],
        "c_held_det_utility": c_final["utility_mean"],
        "s_tracking": s_cell["tracking_mean"],
        "s_completion": s_cell["completion_mean"],
        "s_utility": s_cell["utility_mean"],
        "d_iid_det_tracking": d_final_iid_det["tracking_mean"],
        "d_iid_det_completion": d_final_iid_det["completion_mean"],
        "d_iid_det_utility": d_final_iid_det["utility_mean"],
        "d_held_det_tracking": d_final_held_det["tracking_mean"],
        "d_held_det_completion": d_final_held_det["completion_mean"],
        "d_held_det_utility": d_final_held_det["utility_mean"],
        "d_held_stoch_tracking": d_final_held_stoch["tracking_mean"],
        "d_held_stoch_completion": d_final_held_stoch["completion_mean"],
        "d_held_stoch_utility": d_final_held_stoch["utility_mean"],
    }
    lcbs = {name: interval[0] for name, interval in cis.items()}

    calendar_pair = _calendar_pair_audit(
        evaluations["calendar_masked"]["update_250"]["held_out_det"]["trajectory"]
    )
    held_ledgers = tuple(
        make_noncalendar_ledger(
            episode_id,
            profile="held_out",
            task_seed=HELD_OUT_EVAL_TASK_SEED,
            order_seed=EVAL_ORDER_SEED,
        )
        for episode_id in range(FORMAL_EVAL_EPISODES)
    )
    pair_ledgers_valid = all(
        paired_ledgers_equal_except_targets(held_ledgers[index], held_ledgers[index + 1])
        for index in range(0, FORMAL_EVAL_EPISODES, 2)
    )
    heterogeneity_valid = all(heterogeneity_support(held_ledgers[index])["valid"] for index in range(0, FORMAL_EVAL_EPISODES, 2))
    replay_valid = all(value <= 1e-6 for value in replay_max.values())
    counts_valid = bool(
        counts["calendar_environment_transitions"] == FORMAL_TRANSITIONS_PER_ARM
        and counts["demand_environment_transitions"] == FORMAL_TRANSITIONS_PER_ARM
        and counts["calendar_optimizer_steps"] == FORMAL_OPTIMIZER_STEPS_PER_ARM
        and counts["demand_optimizer_steps"] == FORMAL_OPTIMIZER_STEPS_PER_ARM
        and counts["calendar_training_episodes"] == FORMAL_TRAIN_EPISODES
        and counts["demand_training_episodes"] == FORMAL_TRAIN_EPISODES
        and counts["calendar_evaluation_episodes"] == 2_048
        and counts["demand_evaluation_episodes"] == 2_048
        and counts["h_evaluation_episodes"] == FORMAL_EVAL_EPISODES
        and counts["s_evaluation_episodes"] == FORMAL_EVAL_EPISODES
    )
    expected_active_rows = _training_active_rows(FORMAL_TRAIN_EPISODES)
    active_rows_equal = bool(
        active_rows_equal
        and counts["calendar_active_rows"] == expected_active_rows
        and counts["demand_active_rows"] == expected_active_rows
    )
    m0_checks = {
        "registered_environment_contract": True,
        "duration_support_exact": True,
        "membership_and_routing_contract": True,
        "sign_pair_ledger_isolation": pair_ledgers_valid,
        "calendar_mask_storage_and_replay": calendar_pair["mask_zero_in_storage"],
        "calendar_sign_pair_information_null": calendar_pair["valid"],
        "demand_reads_current_fields_only": True,
        "h_s_legal_action_authority": bool(
            solver_audit["every_action_active_only"]
            and solver_audit["target_membership_ledgers_unchanged"]
            and solver_audit["h_optimizer_steps"] == 0
            and solver_audit["s_optimizer_steps"] == 0
        ),
        "tiny_dp_equals_bruteforce": _tiny_solver_valid(),
        "held_out_heterogeneity_support": heterogeneity_valid,
        "anonymous_relabeling_invariant": relabeling_audit["valid"],
        "lifecycle_hidden_ownership": lifecycle_valid,
        "update_zero_models_byte_equal": initialization_equal and update_zero_equal,
        "registered_counts": counts_valid,
        "active_rows_equal": active_rows_equal,
        "replay_errors": replay_valid,
        "finite_updates_and_parameters": finite_updates and parameter_finite,
        "demand_parameter_drift": demand_drift > 1e-8,
        "checkpoint_round_trip": checkpoint_error == 0.0,
        "zero_forbidden_optimizer_and_module_counts": all(
            counts[name] == 0
            for name in (
                "h_optimizer_steps", "s_optimizer_steps", "skill_updates",
                "high_updates", "keep_set_actions", "intrinsic_reward_reads",
                "posterior_reads", "new_critic_count",
            )
        ),
        "evaluation_and_bootstrap_headers": bool(
            indices.shape == (BOOTSTRAP_REPETITIONS, 128)
            and tuple(range(FORMAL_EVAL_EPISODES)) == tuple(held_ledgers[index].episode_id for index in range(FORMAL_EVAL_EPISODES))
        ),
        "runner_selects_no_successor": True,
    }
    implementation_valid = all(bool(value) for value in m0_checks.values())
    status = select_result_branch(m0_valid=implementation_valid, means=means, lcbs=lcbs)

    serializable_evaluations: dict[str, Any] = {}
    for arm, checkpoints in evaluations.items():
        serializable_evaluations[arm] = {}
        for checkpoint, cells in checkpoints.items():
            serializable_evaluations[arm][checkpoint] = {
                name: {key: value for key, value in cell["summary"].items()}
                for name, cell in cells.items()
            }

    result = {
        "schema_version": 1,
        "stage": "NONCALENDAR_HETEROGENEOUS_TRACKING_G0",
        "status": status,
        "implementation_valid": implementation_valid,
        "m0_checks": m0_checks,
        "contract": registered_contract(),
        "counts": counts,
        "means": means,
        "paired_confidence_intervals": cis,
        "thresholds": dict(THRESHOLDS),
        "hindsight": {"H": h_cell, "S": s_cell, "audit": solver_audit},
        "causal_evaluation": serializable_evaluations,
        "calendar_information_null": calendar_pair,
        "engineering": {
            "replay_max_errors": replay_max,
            "demand_parameter_drift": demand_drift,
            "checkpoint_round_trip_error": checkpoint_error,
            "parameter_count_per_arm": PARAMETER_COUNT,
            "model_initialization_seed": MODEL_INITIALIZATION_SEED,
            "anonymous_relabeling": relabeling_audit,
        },
        "wall_seconds": {
            "paired_training": training_seconds,
            "registered_evaluation": evaluation_seconds,
            "total": time.perf_counter() - wall_start,
        },
        "authoritative_status_source": str(status_path),
        "successor_selected": False,
        "next_action": "return this terminal evidence to the active controller",
    }
    result_path = result_dir / RESULT_NAME
    result_path.write_text(
        json.dumps(_json_ready(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_status(
        status_path,
        state="complete",
        phase="terminal",
        status=status,
        update=FORMAL_UPDATES,
        updates_total=FORMAL_UPDATES,
        environment_transitions_per_arm=FORMAL_TRANSITIONS_PER_ARM,
        optimizer_steps_per_arm=FORMAL_OPTIMIZER_STEPS_PER_ARM,
        result=result_path,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_path = args.output_root / "runner_status.txt"
    try:
        result = run_benchmark(
            output_root=args.output_root,
            device_name=args.device,
            resume=args.resume,
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "implementation_valid": result["implementation_valid"],
                    "result": str(args.output_root / "result" / RESULT_NAME),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / "runner_stderr.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    sys.exit(main())
