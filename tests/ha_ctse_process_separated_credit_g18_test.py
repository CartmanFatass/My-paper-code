from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.separated_credit_g18 import (
    SeparatedCreditPolicy,
    attach_credit_baselines,
    collect_battery_trajectory,
    compute_separated_credit,
    evaluate_battery_policy,
    optimize_separated_update,
    replay_separated_trajectory,
    separated_replay_errors,
    separated_critic_loss,
)
from scripts import screen_fast_slow_separated_credit_g18 as screen


def _battery_model() -> SeparatedCreditPolicy:
    model = SeparatedCreditPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=16,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


def test_centered_successor_channel_reduces_to_immediate_credit() -> None:
    rewards = torch.tensor([[0.2], [0.7], [0.4]])
    slow_values = torch.tensor([[0.1], [0.5], [0.3]])
    bootstrap = torch.tensor([0.8])
    terminals = torch.tensor([[False], [False], [True]])
    immediate = torch.tensor([[0.1], [0.4], [0.2]])
    successor = torch.tensor([[0.45], [0.27], [0.0]])
    active = torch.tensor(
        [[[True, False]], [[True, True]], [[False, True]]]
    )

    credit = compute_separated_credit(
        rewards=rewards,
        slow_values=slow_values,
        bootstrap_slow_values=bootstrap,
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=terminals,
        active_mask=active,
        gamma=0.9,
    )

    torch.testing.assert_close(
        credit.successor_residual, torch.zeros_like(rewards), rtol=0, atol=0
    )
    torch.testing.assert_close(
        credit.actor_advantage, rewards - immediate, rtol=0, atol=0
    )
    assert torch.count_nonzero(credit.token_actor_advantage[~active]) == 0


def test_equal_current_reward_gets_delayed_credit_from_next_value_only() -> None:
    rewards = torch.tensor([[0.5, 0.5], [0.0, 0.0]])
    slow_values = torch.tensor([[0.0, 0.0], [0.9, 0.2]])
    zeros = torch.zeros_like(rewards)
    credit = compute_separated_credit(
        rewards=rewards,
        slow_values=slow_values,
        bootstrap_slow_values=torch.zeros(2),
        immediate_baselines=torch.full_like(rewards, 0.5),
        successor_baselines=zeros,
        terminals=torch.tensor([[False, False], [True, True]]),
        active_mask=torch.ones((2, 2, 1), dtype=torch.bool),
        gamma=0.9,
    )

    assert credit.immediate_residual[0, 0] == credit.immediate_residual[0, 1] == 0
    torch.testing.assert_close(
        credit.actor_advantage[0], torch.tensor([0.81, 0.18]), rtol=0, atol=1e-7
    )


def test_terminal_rows_ignore_bootstrap_and_returns_are_exact() -> None:
    rewards = torch.tensor([[1.0], [2.0], [3.0]])
    terminals = torch.tensor([[False], [True], [False]])
    credit = compute_separated_credit(
        rewards=rewards,
        slow_values=torch.tensor([[0.2], [0.4], [0.6]]),
        bootstrap_slow_values=torch.tensor([4.0]),
        immediate_baselines=torch.zeros_like(rewards),
        successor_baselines=torch.zeros_like(rewards),
        terminals=terminals,
        active_mask=torch.ones((3, 1, 2), dtype=torch.bool),
        gamma=0.5,
    )

    torch.testing.assert_close(
        credit.successor_targets,
        torch.tensor([[0.2], [0.0], [2.0]]),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        credit.slow_return_targets,
        torch.tensor([[2.0], [2.0], [5.0]]),
        rtol=0,
        atol=0,
    )


def test_critic_loss_updates_baselines_but_not_actor_credit_targets() -> None:
    rewards = torch.tensor([[0.2], [0.4]])
    slow = torch.tensor([[0.1], [0.3]], requires_grad=True)
    immediate = torch.tensor([[0.0], [0.1]], requires_grad=True)
    successor = torch.tensor([[0.0], [0.0]], requires_grad=True)
    credit = compute_separated_credit(
        rewards=rewards,
        slow_values=slow,
        bootstrap_slow_values=torch.zeros(1),
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=torch.tensor([[False], [True]]),
        active_mask=torch.ones((2, 1, 2), dtype=torch.bool),
        gamma=0.9,
    )
    assert credit.actor_advantage.requires_grad is False

    loss = separated_critic_loss(
        slow_values=slow,
        immediate_baselines=immediate,
        successor_baselines=successor,
        credit=credit,
    )
    loss.backward()

    assert torch.isfinite(loss)
    assert slow.grad is not None and torch.isfinite(slow.grad).all()
    assert immediate.grad is not None and torch.isfinite(immediate.grad).all()
    assert successor.grad is not None and torch.isfinite(successor.grad).all()


def test_battery_collection_replays_exactly_and_keeps_inactive_rows_zero() -> None:
    torch.manual_seed(1818000)
    model = _battery_model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1, 2),
        action_seed=1838000,
        device=torch.device("cpu"),
    )

    replay = replay_separated_trajectory(
        model, trajectory, device=torch.device("cpu")
    )
    assert all(value == 0.0 for value in separated_replay_errors(replay, trajectory).values())
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    assert torch.count_nonzero(inactive_actions) == 0
    assert {ledger.slot_order for ledger in trajectory.ledgers} == set(
        battery_source.GATE_SLOT_ORDERS
    )
    assert all(
        outcome.roster_sizes == (4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 4, 4)
        for outcome in trajectory.outcomes
    )


def test_one_separated_update_is_finite_and_moves_parameters() -> None:
    torch.manual_seed(1818001)
    model = _battery_model()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(3, 4),
        action_seed=1838001,
        device=torch.device("cpu"),
    )
    before = {
        name: value.detach().clone() for name, value in model.state_dict().items()
    }

    metrics = optimize_separated_update(
        model,
        optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )

    assert metrics["finite_update"] == 1.0
    assert metrics["optimizer_steps"] == 2.0
    assert max(
        float(torch.max(torch.abs(before[name] - value)).item())
        for name, value in model.state_dict().items()
    ) > 0.0


def test_battery_evaluation_covers_each_slot_order_without_inactive_actions() -> None:
    torch.manual_seed(1818002)
    rows = evaluate_battery_policy(
        _battery_model(), device=torch.device("cpu")
    )

    assert [tuple(row["slot_order"]) for row in rows] == list(
        battery_source.GATE_SLOT_ORDERS
    )
    assert all(row["inactive_action_zero"] is True for row in rows)
    assert all(0.0 <= row["utility"] <= 1.0 for row in rows)
    assert all(len(row["roster_sizes"]) == battery_source.HORIZON for row in rows)


def test_closed_g17_source_uses_the_same_exact_replay_and_update_path() -> None:
    torch.manual_seed(1818003)
    model = SeparatedCreditPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=1828003,
        action_seed=1838003,
        device=torch.device("cpu"),
    )
    trajectory = attach_credit_baselines(
        model, raw, device=torch.device("cpu")
    )
    replay = replay_separated_trajectory(
        model, trajectory, device=torch.device("cpu")
    )

    assert all(value == 0.0 for value in separated_replay_errors(replay, trajectory).values())
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    metrics = optimize_separated_update(
        model,
        optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=screen.GAMMA,
    )
    assert metrics["finite_update"] == 1.0


def test_dual_source_result_precedence_is_first_match() -> None:
    passing = {
        "operational_valid": True,
        "g17_iid_mean": 0.95,
        "g17_heldout_mean": 0.94,
        "g17_gain_mean": 0.20,
        "g17_minimum_episode": 0.90,
        "g17_effort_correlation": 0.96,
        "g17_mix_correlation": 0.97,
        "g17_effort_mae": 0.02,
        "g17_mix_mae": 0.02,
        "g18_utility_mean": 0.98,
        "g18_minimum_slot_utility": 0.97,
        "g18_gain_mean": 0.18,
        "g18_minimum_spike_utility": 0.95,
        "g18_minimum_rotating_effort_share": 0.82,
    }
    assert screen.select_result_branch(passing) == screen.PROMISING_BRANCH
    assert screen.select_result_branch(
        passing | {"g17_mix_correlation": 0.89, "g18_utility_mean": 0.1}
    ) == screen.NO_G17_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_minimum_slot_utility": 0.94}
    ) == screen.NO_G18_ACCESS_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_minimum_rotating_effort_share": 0.74}
    ) == screen.NO_G18_MECHANISM_BRANCH
    assert screen.select_result_branch(
        passing | {"operational_valid": False}
    ) == screen.INVALID_BRANCH


def test_one_update_training_helper_closes_checkpoint_and_contract(tmp_path) -> None:
    run_root = tmp_path / "g18_one_update"
    run_root.mkdir()
    (run_root / "checkpoints").mkdir()

    row = screen._train_source(
        run_root=run_root,
        source="g18",
        source_commit="TEST_SOURCE",
        updates=1,
    )

    assert row["finite_updates"] is True
    assert row["lifecycle_contract_valid"] is True
    assert max(row["maximum_replay_errors"].values()) == 0.0
    assert row["parameter_drift"] > 0.0
    restored = screen._load_checkpoint(
        run_root / row["final_checkpoint"],
        source="g18",
        source_commit="TEST_SOURCE",
        completed_updates=1,
    )
    assert restored.parameter_count == row["parameter_count"]
