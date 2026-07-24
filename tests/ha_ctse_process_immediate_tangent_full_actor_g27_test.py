from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.immediate_tangent_full_actor_g27 import (
    ImmediateTangentProtectedFullActorPolicy,
    compose_tangent_protected_gradients,
    optimize_tangent_protected_update,
    project_successor_to_immediate_tangent,
)
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from scripts import screen_immediate_tangent_full_actor_g27 as screen


def _battery_model() -> ImmediateTangentProtectedFullActorPolicy:
    model = ImmediateTangentProtectedFullActorPolicy(
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


def test_full_actor_inventory_is_exact_and_disjoint() -> None:
    model = _battery_model()
    names = set(model.full_actor_parameter_names())
    expected = {
        name
        for name, _ in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
        and not name.startswith("critic.")
    }
    assert names == expected
    assert "log_std" in names
    for prefix in (
        "member_encoder.",
        "context_encoder.",
        "actor_rnn.",
        "action_mean.",
        "current_observation_residual.",
    ):
        assert any(name.startswith(prefix) for name in names)

    model.begin_tangent_phase()
    actor = {id(row) for row in model.full_actor_parameters()}
    critic = {id(row) for row in model.critic_parameters()}
    residual = {id(row) for row in model.residual_parameters()}
    core_critic = {id(row) for row in model.policy.critic.parameters()}
    assert actor.isdisjoint(critic | residual | core_critic)
    assert all(row.requires_grad for row in model.full_actor_parameters())
    assert all(row.requires_grad for row in model.critic_parameters())
    assert all(not row.requires_grad for row in model.residual_parameters())
    assert all(not row.requires_grad for row in model.policy.critic.parameters())


def test_tangent_composition_preserves_aligned_and_projects_conflict() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    conflict = compose_tangent_protected_gradients(
        (torch.tensor([1.0, 0.0]),),
        (torch.tensor([-2.0, 3.0]),),
        (parameter,),
    )
    assert conflict.conflict is True
    torch.testing.assert_close(
        conflict.successor_gradients[0],
        torch.tensor([0.0, 3.0]),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        conflict.gradients[0],
        torch.tensor([0.5, 1.5]),
        rtol=0,
        atol=0,
    )
    assert conflict.pre_dot == -2.0
    assert conflict.post_dot == 0.0
    assert conflict.identity_error == 0.0

    aligned = compose_tangent_protected_gradients(
        (torch.tensor([1.0, 0.0]),),
        (torch.tensor([2.0, 3.0]),),
        (parameter,),
    )
    assert aligned.conflict is False
    torch.testing.assert_close(
        aligned.successor_gradients[0],
        torch.tensor([2.0, 3.0]),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        aligned.gradients[0],
        torch.tensor([1.5, 1.5]),
        rtol=0,
        atol=0,
    )


def test_float32_projection_closes_the_registered_half_space() -> None:
    torch.manual_seed(0)
    immediate = torch.randn(100)
    successor = -0.3 * immediate + torch.randn(100)
    parameter = torch.nn.Parameter(torch.zeros(100))
    from ha_ctse_process.anchored_residual_g19 import project_delayed_gradients

    assert project_delayed_gradients(
        (successor,), (immediate,), (parameter,)
    ).post_dot < -1e-7
    projection = project_successor_to_immediate_tangent(
        (successor,), (immediate,), (parameter,)
    )
    assert projection.conflict is True
    assert projection.post_dot >= 0.0
    assert projection.lattice_correction > 0.0


def test_tangent_update_moves_actor_but_not_residual_or_core_critic() -> None:
    torch.manual_seed(2719000)
    model = _battery_model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2739000,
        device=torch.device("cpu"),
    )
    actor_before = _state(model.full_actor_parameters())
    residual_before = _state(model.residual_parameters())
    core_critic_before = _state(tuple(model.policy.critic.parameters()))
    critic_before = _state(model.critic_parameters())
    model.begin_tangent_phase()

    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    critic_only = (
        replay.values.sum()
        + replay.immediate_baselines.sum()
        + replay.successor_baselines.sum()
    )
    critic_to_actor = torch.autograd.grad(
        critic_only,
        model.full_actor_parameters(),
        allow_unused=True,
    )
    assert all(row is None for row in critic_to_actor)

    metrics = optimize_tangent_protected_update(
        model,
        torch.optim.Adam(model.full_actor_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )

    assert metrics["finite_update"] == 1.0
    assert metrics["minimum_projection_post_dot"] >= -1e-7
    assert metrics["maximum_applied_gradient_identity_error"] <= 1e-7
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
    assert model.residual_output_layer_maximum_absolute_value() == 0.0
    assert all(
        value == 0.0
        for name, value in metrics.items()
        if name.endswith("_error") and name != "maximum_applied_gradient_identity_error"
    )


def test_g17_collection_retains_exact_generic_replay() -> None:
    torch.manual_seed(2719001)
    model = ImmediateTangentProtectedFullActorPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2729001,
        action_seed=2739001,
        device=torch.device("cpu"),
    )
    trajectory = attach_credit_baselines(
        model, raw, device=torch.device("cpu")
    )
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    assert all(
        value == 0.0 for value in replay_errors(replay, trajectory).values()
    )
    assert all(
        outcome.roster_sizes == ledger.expected_roster_sizes
        for outcome, ledger in zip(trajectory.outcomes, trajectory.ledgers)
    )


def test_tangent_phase_rejects_nonzero_residual_and_reentry() -> None:
    model = _battery_model()
    final = model.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.1)
    try:
        model.begin_tangent_phase()
    except RuntimeError as error:
        assert "exact zero" in str(error)
    else:
        raise AssertionError("nonzero residual output was accepted")
    with torch.no_grad():
        final.bias.zero_()
    model.begin_tangent_phase()
    try:
        model.begin_tangent_phase()
    except RuntimeError as error:
        assert "exactly once" in str(error)
    else:
        raise AssertionError("tangent phase reentry was accepted")


def test_g27_result_precedence_and_configuration_are_frozen() -> None:
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
        passing | {"g17_effort_correlation": 0.89, "g18_final_utility": 0.1}
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
    assert configuration["g17_tangent_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_tangent_updates"] == 300
    assert configuration["residual"] == "exact_zero_frozen"
    assert (
        configuration["actor_gradient_rule"]
        == "half_immediate_plus_projected_successor"
    )
