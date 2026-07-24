from __future__ import annotations

import pytest
import torch

from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process import direction_balanced_full_actor_g30 as g30_source
from ha_ctse_process.anchored_residual_g19 import maximum_state_difference
from ha_ctse_process.direction_balanced_full_actor_g30 import (
    DirectionBalancedFullActorPolicy,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    ReturnToGoDirectionBalancedFullActorPolicy,
    compute_return_to_go_credit,
    optimize_return_to_go_direction_balanced_update,
)
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from scripts import screen_return_to_go_direction_balanced_full_actor_g31 as screen


def _model() -> ReturnToGoDirectionBalancedFullActorPolicy:
    model = ReturnToGoDirectionBalancedFullActorPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=16,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


def _state(parameters: tuple[torch.nn.Parameter, ...]) -> dict[str, torch.Tensor]:
    return {
        str(index): parameter.detach().clone()
        for index, parameter in enumerate(parameters)
    }


def _credit(
    rewards: torch.Tensor, terminals: torch.Tensor, *, gamma: float
):
    zeros = torch.zeros_like(rewards)
    return compute_return_to_go_credit(
        rewards=rewards,
        slow_values=zeros,
        immediate_baselines=zeros,
        successor_baselines=zeros,
        terminals=terminals,
        gamma=gamma,
    )


def test_return_to_go_excludes_current_reward_and_is_detached() -> None:
    rewards = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
    credit = _credit(
        rewards,
        torch.tensor([[False], [False], [True]]),
        gamma=0.5,
    )

    torch.testing.assert_close(
        credit.successor_targets,
        torch.tensor([[1.75], [1.5], [0.0]]),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        credit.slow_return_targets,
        torch.tensor([[2.75], [3.5], [3.0]]),
        rtol=0,
        atol=0,
    )
    assert credit.successor_targets.requires_grad is False
    assert credit.immediate_residual.requires_grad is False
    assert credit.slow_return_targets.requires_grad is False


def test_mid_trajectory_terminal_resets_future_tail_exactly() -> None:
    rewards = torch.tensor([[1.0], [2.0], [10.0], [20.0]])
    credit = _credit(
        rewards,
        torch.tensor([[False], [True], [False], [True]]),
        gamma=0.5,
    )

    torch.testing.assert_close(
        credit.successor_targets,
        torch.tensor([[1.0], [0.0], [10.0], [0.0]]),
        rtol=0,
        atol=0,
    )
    assert torch.count_nonzero(
        credit.successor_targets[torch.tensor([False, True, False, True])]
    ) == 0


def test_g31_model_has_no_new_actor_input_or_checkpoint_shape() -> None:
    g31 = _model()
    g30 = DirectionBalancedFullActorPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=16,
    )

    assert g31.policy.observation_dim == battery_source.OBSERVATION_DIM
    assert g31.state_dict().keys() == g30.state_dict().keys()
    assert screen._configuration()["future_actor_input"] == (
        "none_training_target_only"
    )
    assert screen._configuration()["checkpoint_identity"] == (
        "fresh_no_g30_resume"
    )


def test_return_to_go_update_reuses_replay_and_preserves_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch.manual_seed(3119000)
    model = _model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=3139000,
        device=torch.device("cpu"),
    )
    actor_before = _state(model.full_actor_parameters())
    residual_before = _state(model.residual_parameters())
    core_critic_before = _state(tuple(model.policy.critic.parameters()))
    critic_before = _state(model.critic_parameters())
    model.begin_direction_balanced_phase()
    replay_calls = [0]
    original_replay = g30_source.replay_trajectory

    def counted_replay(*args, **kwargs):
        replay_calls[0] += 1
        return original_replay(*args, **kwargs)

    monkeypatch.setattr(g30_source, "replay_trajectory", counted_replay)
    metrics = optimize_return_to_go_direction_balanced_update(
        model,
        torch.optim.Adam(model.full_actor_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )

    assert replay_calls[0] == 2
    assert metrics["finite_update"] == 1.0
    assert metrics["terminal_return_to_go_error"] == 0.0
    assert metrics["maximum_return_to_go_target_absolute_value"] > 0.0
    assert metrics["minimum_direction_immediate_dot"] >= -1e-7
    assert metrics["minimum_actor_optimizer_step_increment"] == 1.0
    assert maximum_state_difference(
        actor_before, _state(model.full_actor_parameters())
    ) > 0.0
    assert maximum_state_difference(
        critic_before, _state(model.critic_parameters())
    ) > 0.0
    assert maximum_state_difference(
        residual_before, _state(model.residual_parameters())
    ) == 0.0
    assert maximum_state_difference(
        core_critic_before, _state(tuple(model.policy.critic.parameters()))
    ) == 0.0


def test_credit_validation_fails_closed() -> None:
    rewards = torch.ones((2, 1))
    zeros = torch.zeros_like(rewards)
    with pytest.raises(ValueError, match="terminal mask must be bool"):
        compute_return_to_go_credit(
            rewards=rewards,
            slow_values=zeros,
            immediate_baselines=zeros,
            successor_baselines=zeros,
            terminals=zeros,
            gamma=0.99,
        )
    invalid = rewards.clone()
    invalid[0, 0] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        _credit(
            invalid,
            torch.tensor([[False], [True]]),
            gamma=0.99,
        )


def test_g31_result_precedence_and_screen_counts_are_frozen() -> None:
    passing = {
        "operational_valid": True,
        "g17_final_iid_utility": 0.93,
        "g17_final_heldout_utility": 0.92,
        "g17_gain": 0.20,
        "g17_minimum_episode": 0.85,
        "g17_effort_correlation": 0.95,
        "g17_mix_correlation": 0.96,
        "g17_effort_mae": 0.03,
        "g17_mix_mae": 0.02,
        "g18_final_utility": 0.97,
        "g18_gain_over_anchor": 0.15,
        "g18_spike_utility": 0.94,
        "g18_rotating_effort_share": 0.82,
    }
    assert screen.select_result_branch(passing) == screen.PROMISING_BRANCH
    assert screen.select_result_branch(
        passing | {"g17_effort_correlation": 0.89}
    ) == screen.NO_G17_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_spike_utility": 0.89}
    ) == screen.NO_G18_ACCESS_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_rotating_effort_share": 0.74}
    ) == screen.NO_G18_MECHANISM_BRANCH
    assert screen.select_result_branch(
        passing | {"operational_valid": False}
    ) == screen.INVALID_BRANCH

    configuration = screen._configuration()
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_return_to_go_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_return_to_go_updates"] == 300
    assert configuration["successor_actor_target"].startswith("detached_")
