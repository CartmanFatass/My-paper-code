from __future__ import annotations

import torch
import numpy as np
import json

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ACTION_DIM,
    CAPACITY,
    CURRICULUM_SINGLETON_PROFILES,
    HORIZON,
    ContinuousServiceRosterEnv,
    collect_trajectory,
    compute_gae,
    constructive_actions,
    make_ledger,
    optimize_update,
    replay_errors,
    replay_trajectory,
)
from scripts import run_continuous_service_roster_proxy_g17 as runner


def test_continuous_roster_policy_is_capacity_generic_and_masks_inactive_rows() -> None:
    torch.manual_seed(17)
    model = ContinuousRosterPolicy(
        observation_dim=7,
        critic_state_dim=5,
        member_capacity=6,
        action_dim=2,
        hidden_dim=8,
    )
    observations = torch.randn(2, 6, 7)
    active = torch.tensor(
        [[True, True, False, True, False, True], [True, False, True, True, True, False]]
    )
    critic_state = torch.randn(2, 5)
    hidden = torch.randn(2, 6, 8)
    output = model.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=critic_state,
        hidden=hidden,
        deterministic=True,
    )

    assert output.actions.shape == (2, 6, 2)
    assert output.prefix_action_sums.shape == (2, 6, 2)
    assert torch.isfinite(output.actions).all()
    assert bool((output.actions.abs() <= 1.0).all())
    assert torch.count_nonzero(output.actions[~active]) == 0
    assert torch.count_nonzero(output.token_log_probs[~active]) == 0
    torch.testing.assert_close(output.next_hidden[~active], hidden[~active], rtol=0, atol=0)


def test_optional_current_observation_residual_is_a_real_bounded_delta() -> None:
    torch.manual_seed(19)
    base = ContinuousRosterPolicy(
        observation_dim=7,
        critic_state_dim=5,
        member_capacity=6,
        action_dim=2,
        hidden_dim=8,
    )
    torch.manual_seed(19)
    residual = ContinuousRosterPolicy(
        observation_dim=7,
        critic_state_dim=5,
        member_capacity=6,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    assert residual.parameter_count == base.parameter_count + 16
    assert residual.current_observation_residual is not None
    assert base.current_observation_residual is None


def test_new_source_has_exact_dynamic_roster_and_constructive_access() -> None:
    ledger = make_ledger(2, master_seed=170_001)
    same = make_ledger(2, master_seed=170_001)
    np.testing.assert_array_equal(ledger.capacities, same.capacities)
    np.testing.assert_array_equal(ledger.load, same.load)
    np.testing.assert_array_equal(ledger.target_mix, same.target_mix)

    env = ContinuousServiceRosterEnv(ledger)
    roster_sizes = []
    utilities = []
    for _ in range(HORIZON):
        view = env.observe()
        roster_sizes.append(int(view.active_mask.sum()))
        actions = constructive_actions(view)
        assert actions.shape == (CAPACITY, ACTION_DIM)
        reward, terminal, info = env.step(actions)
        utilities.append(reward)
        assert info["service_utility"] == reward
    outcome = env.outcome()

    assert terminal
    assert tuple(roster_sizes) == ledger.expected_roster_sizes
    np.testing.assert_allclose(utilities, np.ones(HORIZON), rtol=0, atol=2e-7)
    assert outcome.utility == np.mean(utilities)
    assert outcome.minimum_step_utility >= 1.0 - 2e-7

    singleton = make_ledger(
        0,
        master_seed=170_002,
        profiles=CURRICULUM_SINGLETON_PROFILES,
    )
    assert singleton.expected_roster_sizes == (1,) * HORIZON


def test_collection_replay_lifecycle_and_one_update_are_exact_and_finite() -> None:
    torch.manual_seed(170_017)
    model = ContinuousRosterPolicy(
        observation_dim=10,
        critic_state_dim=6,
        member_capacity=CAPACITY,
        action_dim=ACTION_DIM,
        hidden_dim=16,
    )
    trajectory = collect_trajectory(
        model,
        episode_ids=(0, 1, 2),
        ledger_seed=170_101,
        action_seed=170_201,
        device=torch.device("cpu"),
    )
    errors = replay_errors(
        replay_trajectory(model, trajectory, device=torch.device("cpu")),
        trajectory,
    )
    assert max(errors.values()) == 0.0

    for env_index in range(3):
        absent = ~trajectory.active_mask[:, env_index]
        for key in range(CAPACITY):
            for time in range(HORIZON - 1):
                if bool(absent[time, key] and absent[time + 1, key]):
                    torch.testing.assert_close(
                        trajectory.hidden_after[time, env_index, key],
                        trajectory.hidden_after[time + 1, env_index, key],
                        rtol=0,
                        atol=0,
                    )

    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    metrics = optimize_update(
        model,
        optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
    )
    assert metrics["finite_update"] == 1.0
    assert metrics["optimizer_steps"] == 1.0


def test_one_step_credit_matches_the_registered_mean_step_utility() -> None:
    rewards = torch.tensor([[0.2, 0.7], [0.4, 0.5]], dtype=torch.float32)
    values = torch.tensor([[0.1, 0.3], [0.2, 0.1]], dtype=torch.float32)
    advantages, returns = compute_gae(rewards, values, gamma=0.0)
    torch.testing.assert_close(advantages, rewards - values, rtol=0, atol=0)
    torch.testing.assert_close(returns, rewards, rtol=0, atol=0)


def test_nonformal_screen_closes_one_small_artifact(tmp_path) -> None:
    result = runner.screen(
        run_root=tmp_path / "g17_screen",
        updates=1,
        num_envs=2,
        eval_episodes=3,
        ppo_passes=1,
    )
    stored = json.loads((tmp_path / "g17_screen" / "screen_result.json").read_text())
    assert stored == result
    assert result["formal"] is False
    assert result["status"] in {
        "NONFORMAL_G17_PROMISING",
        "NONFORMAL_G17_NOT_PROMISING",
    }
    assert result["source_control"]["minimum_utility"] >= 1.0 - 2e-7
    assert result["runtime"]["backend"] == "cpu"
    assert result["runtime"]["torch_threads"] == 1

    curriculum = runner.screen(
        run_root=tmp_path / "g17_curriculum_screen",
        updates=3,
        num_envs=2,
        eval_episodes=2,
        ppo_passes=1,
        learning_rate=1e-3,
        initial_log_std=-1.0,
        current_observation_residual=True,
        active_count_curriculum=True,
    )
    assert curriculum["active_count_curriculum"] is True
    assert sum(curriculum["training_stages"].values()) == 3


def test_representation_probe_reduces_constructive_mapping_error(tmp_path) -> None:
    result = runner.representation_probe(
        run_root=tmp_path / "g17_representation",
        steps=8,
        batch_size=32,
        learning_rate=1e-3,
    )
    assert result["formal"] is False
    assert result["final_loss"] < result["initial_loss"]
    assert result["status"] == "NONFORMAL_G17_REPRESENTATION_PROBE_COMPLETE"
