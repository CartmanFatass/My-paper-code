from __future__ import annotations

import torch
import numpy as np
import json

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ACTION_DIM,
    CAPACITY,
    HORIZON,
    ContinuousServiceRosterEnv,
    collect_trajectory,
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
