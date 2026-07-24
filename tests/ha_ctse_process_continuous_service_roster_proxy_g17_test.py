from __future__ import annotations

import json

import numpy as np
import pytest
import torch

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ACTION_DIM,
    CAPACITY,
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
from scripts import screen_continuous_roster_td0_g18 as td0_screen


def test_continuous_policy_masks_inactive_rows_and_bounds_actions() -> None:
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
    hidden = torch.randn(2, 6, 8)
    output = model.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=torch.randn(2, 5),
        hidden=hidden,
        deterministic=True,
    )
    assert output.actions.shape == (2, 6, 2)
    assert bool((output.actions.abs() <= 1.0).all())
    assert torch.count_nonzero(output.actions[~active]) == 0
    assert torch.count_nonzero(output.token_log_probs[~active]) == 0
    torch.testing.assert_close(output.next_hidden[~active], hidden[~active], rtol=0, atol=0)


def test_current_observation_residual_is_the_only_parameter_delta() -> None:
    torch.manual_seed(19)
    base = ContinuousRosterPolicy(7, 5, member_capacity=6, action_dim=2, hidden_dim=8)
    torch.manual_seed(19)
    residual = ContinuousRosterPolicy(
        7,
        5,
        member_capacity=6,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    assert residual.parameter_count == base.parameter_count + 16
    assert residual.current_observation_residual is not None
    assert base.current_observation_residual is None


def test_source_schedule_and_constructive_access_are_exact() -> None:
    ledger = make_ledger(2, master_seed=170_001)
    same = make_ledger(2, master_seed=170_001)
    np.testing.assert_array_equal(ledger.capacities, same.capacities)
    np.testing.assert_array_equal(ledger.load, same.load)
    np.testing.assert_array_equal(ledger.target_mix, same.target_mix)
    environment = ContinuousServiceRosterEnv(ledger)
    roster_sizes = []
    utilities = []
    for _ in range(HORIZON):
        view = environment.observe()
        roster_sizes.append(int(view.active_mask.sum()))
        reward, terminal, info = environment.step(constructive_actions(view))
        utilities.append(reward)
        assert info["service_utility"] == reward
    outcome = environment.outcome()
    assert terminal
    assert tuple(roster_sizes) == ledger.expected_roster_sizes
    np.testing.assert_allclose(utilities, np.ones(HORIZON), rtol=0, atol=2e-7)
    assert outcome.minimum_step_utility >= 1.0 - 2e-7


def test_replay_lifecycle_and_one_step_credit_are_exact() -> None:
    torch.manual_seed(170_017)
    model = runner.make_model()
    trajectory = collect_trajectory(
        model,
        episode_ids=(0, 1, 2),
        ledger_seed=170_101,
        action_seed=170_201,
        device=torch.device("cpu"),
    )
    errors = replay_errors(
        replay_trajectory(model, trajectory, device=torch.device("cpu")), trajectory
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
    rewards = torch.tensor([[0.2, 0.7], [0.4, 0.5]])
    values = torch.tensor([[0.1, 0.3], [0.2, 0.1]])
    advantages, returns = compute_gae(rewards, values, gamma=0.0)
    torch.testing.assert_close(advantages, rewards - values, rtol=0, atol=0)
    torch.testing.assert_close(returns, rewards, rtol=0, atol=0)
    optimizer = torch.optim.Adam(model.parameters(), lr=runner.LEARNING_RATE)
    metrics = optimize_update(
        model,
        optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.0,
    )
    assert metrics["finite_update"] == 1.0


def test_td_zero_uses_next_value_without_later_error_carry() -> None:
    rewards = torch.tensor([[0.2], [0.4], [0.7]])
    values = torch.tensor([[0.1], [0.3], [0.5]])
    advantages, returns = compute_gae(
        rewards, values, gamma=0.9, gae_lambda=0.0
    )
    expected_advantages = torch.tensor(
        [[0.2 + 0.9 * 0.3 - 0.1], [0.4 + 0.9 * 0.5 - 0.3], [0.7 - 0.5]]
    )
    torch.testing.assert_close(advantages, expected_advantages, rtol=0, atol=1e-7)
    torch.testing.assert_close(
        returns, expected_advantages + values, rtol=0, atol=1e-7
    )


def test_first_match_branch_precedence() -> None:
    passing = {
        "operational_valid": True,
        "formal": True,
        "iid_lcb": 0.94,
        "heldout_lcb": 0.93,
        "minimum_effort_correlation": 0.97,
        "minimum_mix_correlation": 0.96,
        "maximum_effort_mae": 0.02,
        "maximum_mix_mae": 0.02,
        "gain_lcb": 0.20,
        "minimum_heldout_replicate": 0.91,
    }
    assert runner.select_result_branch(passing) == runner.USABLE_BRANCH
    assert runner.select_result_branch(passing | {"iid_lcb": 0.89}) == runner.NO_IID_BRANCH
    assert runner.select_result_branch(
        passing | {"heldout_lcb": 0.89, "gain_lcb": -1.0}
    ) == runner.NO_HELDOUT_BRANCH
    assert runner.select_result_branch(
        passing | {"minimum_effort_correlation": 0.89, "gain_lcb": -1.0}
    ) == runner.NO_CONDITIONAL_BRANCH
    assert runner.select_result_branch(passing | {"gain_lcb": 0.10}) == runner.NO_GAIN_BRANCH
    assert runner.select_result_branch(
        passing | {"minimum_heldout_replicate": 0.84}
    ) == runner.UNSTABLE_BRANCH
    assert runner.select_result_branch(passing | {"operational_valid": False}) == runner.INVALID_BRANCH


def test_g18_td_zero_screen_requires_conditional_access() -> None:
    passing = {
        "operational_valid": True,
        "iid_mean": 0.94,
        "heldout_mean": 0.93,
        "gain_mean": 0.2,
        "minimum_episode": 0.86,
        "minimum_effort_correlation": 0.96,
        "minimum_mix_correlation": 0.97,
        "maximum_effort_mae": 0.02,
        "maximum_mix_mae": 0.02,
    }
    assert td0_screen.select_candidate(passing) == td0_screen.COMPATIBLE_BRANCH
    assert td0_screen.select_candidate(
        passing | {"minimum_mix_correlation": 0.89}
    ) == td0_screen.NOT_COMPATIBLE_BRANCH
    assert td0_screen.select_candidate(
        passing | {"operational_valid": False}
    ) == td0_screen.INVALID_BRANCH


def test_nonformal_exercise_closes_and_formal_analysis_rejects_it(tmp_path) -> None:
    run_root = tmp_path / "g17_exercise"
    result = runner.exercise(run_root=run_root)
    assert result["formal"] is False
    assert result["operational_valid"] is True
    assert result["branch"] == runner.NONFORMAL_BRANCH
    for name in ("train_manifest.json", "evaluation_manifest.json", "analysis_result.json"):
        assert (run_root / name).is_file()
    with pytest.raises(ValueError, match="formal analysis requires formal artifacts"):
        runner.analyze(run_root=run_root, require_formal=True)

    evaluation = json.loads((run_root / "evaluation_manifest.json").read_text())
    evaluation["source_commit"] = "tampered"
    (run_root / "evaluation_manifest.json").write_text(json.dumps(evaluation))
    invalid = runner.analyze(run_root=run_root)
    assert invalid["operational_valid"] is False
    assert invalid["branch"] == runner.INVALID_BRANCH


def test_nonformal_td_zero_configuration_round_trips(tmp_path) -> None:
    run_root = tmp_path / "td0_round_trip"
    training = runner.train(
        run_root=run_root,
        source_commit="TEST_SOURCE",
        formal=False,
        authorization_token=None,
        replicates=1,
        updates=1,
        num_envs=2,
        eval_episodes=3,
        ppo_passes=1,
        credit_gamma=td0_screen.CREDIT_GAMMA,
        gae_lambda=td0_screen.GAE_LAMBDA,
        seed_offset=td0_screen.SEED_OFFSET,
    )
    assert training["configuration"]["gae_lambda"] == 0.0
    assert training["replicate_results"][0]["seeds"]["model"] == 1_918_000
    runner.evaluate(run_root=run_root)
    analysis = runner.analyze(run_root=run_root)
    assert analysis["operational_valid"] is True
    assert analysis["branch"] == runner.NONFORMAL_BRANCH
