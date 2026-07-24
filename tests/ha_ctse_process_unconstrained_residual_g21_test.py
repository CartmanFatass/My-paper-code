"""Focused acceptance for the G21 unconstrained anchored residual."""

from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    optimize_fast_anchor_update,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from ha_ctse_process.unconstrained_residual_g21 import (
    UnconstrainedAnchoredResidualPolicy,
    optimize_unconstrained_delayed_update,
)
from scripts import screen_unconstrained_anchored_residual_g21 as screen


def _model(
    observation_dim: int, critic_state_dim: int, capacity: int, action_dim: int
) -> UnconstrainedAnchoredResidualPolicy:
    model = UnconstrainedAnchoredResidualPolicy(
        observation_dim,
        critic_state_dim,
        member_capacity=capacity,
        action_dim=action_dim,
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


def _generic_pair() -> tuple[
    ContinuousRosterPolicy, UnconstrainedAnchoredResidualPolicy, dict[str, torch.Tensor]
]:
    torch.manual_seed(2120000)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    residual = UnconstrainedAnchoredResidualPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = residual.policy.load_state_dict(
        base.state_dict(), strict=False
    )
    assert unexpected == []
    assert all(name.startswith("delayed_residual.") for name in missing)
    arguments = {
        "observations": torch.randn(2, 3, 5),
        "active_mask": torch.tensor(
            [[True, True, False], [True, False, True]]
        ),
        "critic_state": torch.randn(2, 4),
        "hidden": torch.randn(2, 3, 8),
    }
    return base, residual, arguments


def test_zero_residual_exactly_matches_base_policy_in_all_modes() -> None:
    base, residual, arguments = _generic_pair()
    noise = torch.randn(2, 3, 2)
    base_sample = base.forward_step(**arguments, sampling_noise=noise)
    residual_sample = residual.policy.forward_step(
        **arguments, sampling_noise=noise
    )
    _assert_step_equal(base_sample, residual_sample)
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        residual.policy.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
        residual.policy.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
    )


def test_residual_retains_active_common_mode_and_inactive_zero() -> None:
    base, residual, arguments = _generic_pair()
    final = residual.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.25)
    base_step = base.forward_step(**arguments, deterministic=True)
    residual_step = residual.policy.forward_step(
        **arguments, deterministic=True
    )
    active = arguments["active_mask"].unsqueeze(-1).expand_as(
        residual_step.pre_tanh_actions
    )
    delta = residual_step.pre_tanh_actions - base_step.pre_tanh_actions
    first_owner = base._routing_order(
        arguments["active_mask"], arguments["observations"]
    )[:, 0]
    batch = torch.arange(first_owner.shape[0])
    torch.testing.assert_close(
        delta[batch, first_owner],
        torch.full_like(delta[batch, first_owner], 0.25),
        rtol=0,
        atol=1e-7,
    )
    assert torch.count_nonzero(residual_step.pre_tanh_actions[~active]) == 0
    assert bool(torch.all(delta.sum(dim=1) > 0))


def test_battery_successor_update_keeps_anchor_and_exercises_residual() -> None:
    torch.manual_seed(2120001)
    model = _model(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        battery_source.CAPACITY,
        battery_source.ACTION_DIM,
    )
    fast = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2130001,
        device=torch.device("cpu"),
    )
    assert optimize_fast_anchor_update(
        model,
        torch.optim.Adam(
            model.fast_actor_parameters()
            + tuple(model.credit_baselines.parameters()),
            lr=1e-3,
        ),
        fast,
        device=torch.device("cpu"),
        ppo_passes=1,
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    delayed = collect_battery_trajectory(
        model,
        episode_ids=(2, 3),
        action_seed=2130002,
        device=torch.device("cpu"),
    )
    metrics = optimize_unconstrained_delayed_update(
        model,
        torch.optim.SGD(model.residual_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        delayed,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0
    assert all(
        value == 0.0
        for name, value in metrics.items()
        if name.endswith("_error") or name.endswith("_max_abs")
    )
    assert not any("projection" in name or "centering" in name for name in metrics)


def test_g17_successor_update_replays_and_preserves_anchor() -> None:
    torch.manual_seed(2120002)
    model = _model(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        g17_source.CAPACITY,
        g17_source.ACTION_DIM,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2129002,
        action_seed=2139002,
        device=torch.device("cpu"),
    )
    fast = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    assert all(
        value == 0.0
        for value in replay_errors(
            replay_trajectory(model, fast, device=torch.device("cpu")), fast
        ).values()
    )
    assert optimize_fast_anchor_update(
        model,
        torch.optim.Adam(
            model.fast_actor_parameters()
            + tuple(model.credit_baselines.parameters()),
            lr=1e-3,
        ),
        fast,
        device=torch.device("cpu"),
        ppo_passes=1,
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(2, 3),
        ledger_seed=2129002,
        action_seed=2139002,
        device=torch.device("cpu"),
    )
    delayed = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    metrics = optimize_unconstrained_delayed_update(
        model,
        torch.optim.SGD(model.residual_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        delayed,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0


def test_g21_result_precedence_and_configuration_are_frozen() -> None:
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
        passing | {"g17_mix_correlation": 0.89, "g18_final_utility": 0.1}
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
    configuration = screen._configuration()
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_delayed_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_delayed_updates"] == 300
    assert configuration["delayed_residual_optimizer"] == "sgd"
    assert configuration["delayed_residual_geometry"] == "unconstrained_pre_squash_mean"
    assert configuration["delayed_gradient_rule"] == "successor_only_unprojected"
