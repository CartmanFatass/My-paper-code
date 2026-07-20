from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest
import torch

import scripts.run_noncalendar_commitment_benchmark_g0 as benchmark_runner
from ha_ctse_process.dynamic_roster_direct import (
    replay_direct_trajectory,
    replay_errors,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    CALENDAR_MASK_INDICES,
    EVAL_ORDER_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_NUM_ENVS,
    FORMAL_OPTIMIZER_STEPS_PER_ARM,
    FORMAL_TRAIN_EPISODES,
    FORMAL_TRANSITIONS_PER_ARM,
    FORMAL_UPDATES,
    HELD_OUT_EVAL_TASK_SEED,
    NoncalendarTrackingEnv,
    PARAMETER_COUNT,
    SolverStep,
    anonymous_relabeling_audit,
    bootstrap_cluster_indices,
    brute_force_trace_outcomes,
    collect_causal_trajectory,
    heterogeneity_support,
    initialize_causal_arms,
    make_noncalendar_ledger,
    paired_ledgers_equal_except_targets,
    registered_contract,
    select_result_branch,
    solve_trace_outcomes,
    trajectory_metric_arrays,
)


def _reactive_actions(environment: NoncalendarTrackingEnv) -> dict[int, int]:
    actions: dict[int, int] = {}
    for key in environment.active_keys:
        state = environment.members[key]
        actions[key] = 2 if state.target > state.x else (0 if state.target < state.x else 1)
    return actions


def _passing_terminal_inputs() -> tuple[dict[str, float], dict[str, float]]:
    means = {
        "h_tracking": 0.90,
        "h_completion": 1.00,
        "h_utility": 0.90,
        "c_held_det_tracking": 0.50,
        "c_held_det_completion": 0.40,
        "c_held_det_utility": 0.20,
        "s_tracking": 0.60,
        "s_completion": 0.50,
        "s_utility": 0.30,
        "d_iid_det_tracking": 0.90,
        "d_iid_det_completion": 0.95,
        "d_iid_det_utility": 0.86,
        "d_held_det_tracking": 0.85,
        "d_held_det_completion": 0.90,
        "d_held_det_utility": 0.80,
        "d_held_stoch_tracking": 0.75,
        "d_held_stoch_completion": 0.82,
        "d_held_stoch_utility": 0.72,
    }
    lcbs = {
        "h_minus_s_tracking": 0.20,
        "h_minus_s_completion": 0.30,
        "h_minus_s_utility": 0.30,
        "d_gain_utility": 0.30,
        "d_minus_c_tracking": 0.30,
        "d_minus_c_completion": 0.35,
        "d_minus_c_utility": 0.30,
    }
    return means, lcbs


def test_noncalendar_g0_focused_contract() -> None:
    left = make_noncalendar_ledger(
        0,
        profile="held_out",
        task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=EVAL_ORDER_SEED,
    )
    right = make_noncalendar_ledger(
        1,
        profile="held_out",
        task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=EVAL_ORDER_SEED,
    )
    assert paired_ledgers_equal_except_targets(left, right)
    assert heterogeneity_support(left)["valid"]

    demand_env = NoncalendarTrackingEnv(left, arm_mode="demand_visible")
    calendar_env = NoncalendarTrackingEnv(left, arm_mode="calendar_masked")
    demand_view = demand_env.observe()
    calendar_view = calendar_env.observe()
    assert demand_view.observations.shape[1] == 15
    assert np.allclose(demand_view.observations[:, 5], 0.5)
    assert np.all((0.0 <= demand_view.observations[:, 5]) & (demand_view.observations[:, 5] <= 1.0))
    assert np.array_equal(calendar_view.observations[:, CALENDAR_MASK_INDICES], np.zeros((left.initial_count, len(CALENDAR_MASK_INDICES)), dtype=np.float32))
    retained = tuple(index for index in range(15) if index not in CALENDAR_MASK_INDICES)
    assert np.array_equal(calendar_view.observations[:, retained], demand_view.observations[:, retained])

    calendar, _demand, _calendar_optimizer, _demand_optimizer = initialize_causal_arms(torch.device("cpu"))
    assert calendar.parameter_count == PARAMETER_COUNT
    trajectory = collect_causal_trajectory(
        calendar,
        episode_ids=(0, 1),
        profile="held_out",
        arm_mode="calendar_masked",
        device=torch.device("cpu"),
    )
    assert torch.equal(trajectory.observations[:, 0], trajectory.observations[:, 1])
    assert torch.equal(trajectory.orders[:, 0], trajectory.orders[:, 1])
    assert torch.equal(trajectory.actions[:, 0], trajectory.actions[:, 1])
    assert torch.max(torch.abs(trajectory.hidden_after[:, 0] - trajectory.hidden_after[:, 1])) <= 1e-6
    training_trajectory = collect_causal_trajectory(
        calendar,
        episode_ids=(0, 1),
        profile="train",
        arm_mode="calendar_masked",
        device=torch.device("cpu"),
    )
    replay = replay_direct_trajectory(
        calendar, training_trajectory, device=torch.device("cpu")
    )
    assert max(replay_errors(replay, training_trajectory).values()) <= 1e-6
    metrics = trajectory_metric_arrays(trajectory)
    assert abs(float(metrics["tracking"].mean()) - 0.5) <= 1e-12
    assert float(metrics["completion"].mean()) <= 0.5 + 1e-12
    assert float(metrics["utility"].mean()) <= 0.5 + 1e-12

    temporary = left.temporary_key
    leave = left.temporary_leave_time
    rejoin = left.rejoin_time
    frozen = trajectory.hidden_after[leave - 1, 0, temporary]
    assert torch.equal(trajectory.hidden_before[leave, 0, temporary], frozen)
    assert torch.equal(trajectory.hidden_after[rejoin - 1, 0, temporary], frozen)
    assert torch.equal(trajectory.hidden_before[rejoin, 0, temporary], frozen)
    assert torch.equal(
        trajectory.hidden_before[rejoin, 0, left.joined_key],
        torch.zeros_like(trajectory.hidden_before[rejoin, 0, left.joined_key]),
    )
    assert torch.equal(
        trajectory.hidden_before[left.terminal_leave_time, 0, left.terminal_key],
        torch.zeros_like(trajectory.hidden_before[left.terminal_leave_time, 0, left.terminal_key]),
    )

    lifecycle_env = NoncalendarTrackingEnv(left, arm_mode="demand_visible")
    for _ in range(25):
        lifecycle_env.observe()
        lifecycle_env.step(_reactive_actions(lifecycle_env))
    snapshot = lifecycle_env.snapshot_state()
    restored = NoncalendarTrackingEnv.from_snapshot_state(deepcopy(snapshot))
    while lifecycle_env.time < 80:
        lifecycle_env.observe()
        restored.observe()
        lifecycle_env.step(_reactive_actions(lifecycle_env))
        restored.step(_reactive_actions(restored))
    lifecycle_outcome = lifecycle_env.outcome()
    assert lifecycle_outcome == restored.outcome()
    assert lifecycle_outcome.utility == pytest.approx(
        np.sqrt(lifecycle_outcome.tracking * lifecycle_outcome.completion),
        abs=1e-12,
    )
    assert left.terminal_key not in lifecycle_env.members
    assert anonymous_relabeling_audit(calendar, device=torch.device("cpu"))["valid"]

    tiny = (
        SolverStep(0, 2, False, True),
        SolverStep(1, 2, True, False),
        SolverStep(4, -2, False, False),
        SolverStep(5, -2, True, False),
    )
    for arm in ("H", "S"):
        assert solve_trace_outcomes(tiny, arm=arm, prune=False) == brute_force_trace_outcomes(tiny, arm=arm)
    assert benchmark_runner._tiny_solver_valid() is True

    means, lcbs = _passing_terminal_inputs()
    assert select_result_branch(m0_valid=True, means=means, lcbs=lcbs) == "PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS"
    assert select_result_branch(m0_valid=False, means=means, lcbs=lcbs) == "INVALID_BENCHMARK_IDENTIFIABILITY_G0"
    corrupted = dict(means)
    corrupted.pop("h_tracking")
    with pytest.raises(ValueError, match="key set mismatch"):
        select_result_branch(m0_valid=True, means=corrupted, lcbs=lcbs)
    extra = dict(lcbs, unregistered_margin=1.0)
    with pytest.raises(ValueError, match="key set mismatch"):
        select_result_branch(m0_valid=True, means=means, lcbs=extra)

    contract = registered_contract()
    assert contract["num_envs"] == FORMAL_NUM_ENVS == 16
    assert contract["outer_updates"] == FORMAL_UPDATES == 250
    assert contract["transitions_per_arm"] == FORMAL_TRANSITIONS_PER_ARM == 320_000
    assert contract["optimizer_steps_per_arm"] == FORMAL_OPTIMIZER_STEPS_PER_ARM == 1_000
    assert contract["training_episodes_per_arm"] == FORMAL_TRAIN_EPISODES == 4_000
    assert contract["eval_episodes_per_cell"] == FORMAL_EVAL_EPISODES == 256
    assert bootstrap_cluster_indices().shape == (10_000, 128)
