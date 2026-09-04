from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process import anchored_residual_g19 as anchored_source
from ha_ctse_process.anchored_residual_g19 import (
    FastAnchoredResidualPolicy,
    attach_credit_baselines,
    maximum_state_difference,
    optimize_delayed_residual_update,
    optimize_fast_anchor_update,
    project_delayed_gradients,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from tools.analysis import screen_fast_policy_anchored_residual_g19 as screen


def _battery_model() -> FastAnchoredResidualPolicy:
    model = FastAnchoredResidualPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=16,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


def _assert_step_equal(left: object, right: object) -> None:
    for name in (
        "actions",
        "pre_tanh_actions",
        "token_log_probs",
        "token_entropies",
        "value",
        "next_hidden",
        "prefix_action_sums",
        "likelihood_mask",
    ):
        torch.testing.assert_close(
            getattr(left, name), getattr(right, name), rtol=0, atol=0
        )


def test_zero_residual_exactly_matches_base_policy_in_all_modes() -> None:
    torch.manual_seed(1919000)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    anchored = FastAnchoredResidualPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = anchored.policy.load_state_dict(
        base.state_dict(), strict=False
    )
    assert unexpected == []
    assert all(name.startswith("delayed_residual.") for name in missing)
    observations = torch.randn(2, 3, 5)
    active_mask = torch.tensor(
        [[True, True, False], [True, False, True]]
    )
    critic_state = torch.randn(2, 4)
    hidden = torch.randn(2, 3, 8)
    noise = torch.randn(2, 3, 2)
    arguments = {
        "observations": observations,
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
    }

    base_sample = base.forward_step(**arguments, sampling_noise=noise)
    anchored_sample = anchored.policy.forward_step(
        **arguments, sampling_noise=noise
    )
    _assert_step_equal(base_sample, anchored_sample)
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        anchored.policy.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
        anchored.policy.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
    )


def test_conflicting_delayed_gradient_is_projected_to_fast_tangent() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    conflict = project_delayed_gradients(
        (torch.tensor([-2.0, 3.0]),),
        (torch.tensor([1.0, 0.0]),),
        (parameter,),
    )
    assert conflict.conflict is True
    torch.testing.assert_close(
        conflict.gradients[0], torch.tensor([0.0, 3.0]), rtol=0, atol=0
    )
    assert conflict.pre_dot == -2.0
    assert conflict.post_dot == 0.0

    aligned = project_delayed_gradients(
        (torch.tensor([2.0, 3.0]),),
        (torch.tensor([1.0, 0.0]),),
        (parameter,),
    )
    assert aligned.conflict is False
    torch.testing.assert_close(
        aligned.gradients[0], torch.tensor([2.0, 3.0]), rtol=0, atol=0
    )


def test_fast_then_delayed_update_keeps_anchor_exact_and_moves_residual(
    monkeypatch,
) -> None:
    torch.manual_seed(1919001)
    model = _battery_model()
    fast_trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=1939001,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters()
        + tuple(model.credit_baselines.parameters()),
        lr=1e-3,
    )
    replay_calls = [0]
    original_replay = anchored_source.replay_trajectory

    def counted_replay(*args, **kwargs):
        replay_calls[0] += 1
        return original_replay(*args, **kwargs)

    monkeypatch.setattr(anchored_source, "replay_trajectory", counted_replay)
    fast_metrics = optimize_fast_anchor_update(
        model,
        fast_optimizer,
        fast_trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
    )
    assert fast_metrics["finite_update"] == 1.0
    assert replay_calls[0] == 1
    assert model.residual_output_layer_maximum_absolute_value() == 0.0

    anchor = model.anchor_state()
    model.begin_delayed_phase()
    assert model.phase == "delayed"
    assert all(not parameter.requires_grad for parameter in model.fast_actor_parameters())
    delayed_trajectory = collect_battery_trajectory(
        model,
        episode_ids=(2, 3),
        action_seed=1939002,
        device=torch.device("cpu"),
    )
    residual_optimizer = torch.optim.SGD(model.residual_parameters(), lr=1e-3)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-3)
    replay_calls[0] = 0
    delayed_metrics = optimize_delayed_residual_update(
        model,
        residual_optimizer,
        critic_optimizer,
        delayed_trajectory,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )

    assert delayed_metrics["finite_update"] == 1.0
    assert replay_calls[0] == 4
    assert delayed_metrics["projection_post_dot"] >= -1e-7
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0
    assert all(
        not parameter.requires_grad
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    )


def test_battery_replay_and_inactive_rows_remain_exact() -> None:
    torch.manual_seed(1919002)
    model = _battery_model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(4, 5, 6),
        action_seed=1939003,
        device=torch.device("cpu"),
    )
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))

    assert all(value == 0.0 for value in replay_errors(replay, trajectory).values())
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    assert torch.count_nonzero(inactive_actions) == 0


def test_g17_collection_uses_the_same_exact_generic_replay() -> None:
    torch.manual_seed(1919003)
    model = FastAnchoredResidualPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=1929003,
        action_seed=1939004,
        device=torch.device("cpu"),
    )
    trajectory = attach_credit_baselines(
        model, raw, device=torch.device("cpu")
    )
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))

    assert all(value == 0.0 for value in replay_errors(replay, trajectory).values())
    assert all(
        outcome.roster_sizes == ledger.expected_roster_sizes
        for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters()
        + tuple(model.credit_baselines.parameters()),
        lr=1e-3,
    )
    assert optimize_fast_anchor_update(
        model,
        fast_optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(2, 3),
        ledger_seed=1929003,
        action_seed=1939004,
        device=torch.device("cpu"),
    )
    delayed = attach_credit_baselines(
        model, raw, device=torch.device("cpu")
    )
    metrics = optimize_delayed_residual_update(
        model,
        torch.optim.SGD(model.residual_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        delayed,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert metrics["minimum_projection_post_dot"] >= -1e-7
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0


def test_delayed_phase_rejects_nonzero_residual_output_and_reentry() -> None:
    model = _battery_model()
    final = model.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.1)
    try:
        model.begin_delayed_phase()
    except RuntimeError as error:
        assert "exact zero" in str(error)
    else:
        raise AssertionError("nonzero residual output was accepted")

    with torch.no_grad():
        final.bias.zero_()
    model.begin_delayed_phase()
    try:
        model.begin_delayed_phase()
    except RuntimeError as error:
        assert "exactly once" in str(error)
    else:
        raise AssertionError("delayed phase reentry was accepted")


def test_g19_result_precedence_is_first_match() -> None:
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
        passing
        | {
            "g17_effort_correlation": 0.89,
            "g18_final_utility": 0.1,
        }
    ) == screen.NO_G17_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_gain_over_anchor": 0.09}
    ) == screen.NO_G18_ACCESS_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_rotating_effort_share": 0.74}
    ) == screen.NO_G18_MECHANISM_BRANCH
    assert screen.select_result_branch(
        passing | {"operational_valid": False}
    ) == screen.INVALID_BRANCH


def test_screen_configuration_matches_frozen_design() -> None:
    configuration = screen._configuration()
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_delayed_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_delayed_updates"] == 300
    assert configuration["delayed_residual_initialization"] == "exact_zero_output"
    assert configuration["delayed_gradient_rule"] == "immediate_tangent_projection"
