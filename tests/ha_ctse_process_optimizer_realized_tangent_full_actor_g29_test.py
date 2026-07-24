from __future__ import annotations

import pytest
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process import optimizer_realized_tangent_full_actor_g29 as g29_source
from ha_ctse_process.anchored_residual_g19 import (
    GRADIENT_CLIP,
    attach_credit_baselines,
    maximum_state_difference,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.optimizer_realized_tangent_full_actor_g29 import (
    OptimizerRealizedTangentFullActorPolicy,
    apply_optimizer_realized_tangent_step,
    optimize_optimizer_realized_tangent_update,
    project_realized_parameters,
)
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from scripts import screen_optimizer_realized_tangent_full_actor_g29 as screen


def _battery_model() -> OptimizerRealizedTangentFullActorPolicy:
    model = OptimizerRealizedTangentFullActorPolicy(
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


def _adam_state(
    optimizer: torch.optim.Adam, parameter: torch.nn.Parameter
) -> dict[str, torch.Tensor | float]:
    return {
        name: (
            value.detach().clone()
            if isinstance(value, torch.Tensor)
            else float(value)
        )
        for name, value in optimizer.state[parameter].items()
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

    model.begin_realized_tangent_phase()
    actor = {id(row) for row in model.full_actor_parameters()}
    critic = {id(row) for row in model.critic_parameters()}
    residual = {id(row) for row in model.residual_parameters()}
    core_critic = {id(row) for row in model.policy.critic.parameters()}
    assert actor.isdisjoint(critic | residual | core_critic)
    assert all(row.requires_grad for row in model.full_actor_parameters())
    assert all(row.requires_grad for row in model.critic_parameters())
    assert all(not row.requires_grad for row in model.residual_parameters())
    assert all(not row.requires_grad for row in model.policy.critic.parameters())


def test_realized_projection_closes_at_first_float_lattice_point() -> None:
    torch.manual_seed(0)
    before = torch.randn(1000)
    immediate = torch.randn(1000)
    displacement = -2.0 * immediate + torch.randn(1000)
    proposed_after = before - displacement
    parameter = torch.nn.Parameter(before.clone())

    projection = project_realized_parameters(
        (before,), (proposed_after,), (immediate,), (parameter,)
    )

    assert projection.conflict is True
    assert projection.pre_dot < 0.0
    assert projection.post_dot >= 0.0
    assert projection.lattice_correction > 0.0
    coordinate = int(immediate.abs().argmax())
    predecessor = projection.parameters[0].clone()
    predecessor[coordinate] = torch.nextafter(
        predecessor[coordinate],
        torch.full_like(
            predecessor[coordinate],
            (
                float("inf")
                if float(immediate[coordinate]) > 0.0
                else -float("inf")
            ),
        ),
    )
    predecessor_dot = (
        (before - predecessor).to(torch.float64)
        * immediate.to(torch.float64)
    ).sum()
    assert float(predecessor_dot) < 0.0

    invalid = immediate.clone()
    invalid[0] = float("nan")
    with pytest.raises(ValueError, match="invalid actor gradients"):
        project_realized_parameters(
            (before,), (proposed_after,), (invalid,), (parameter,)
        )


def test_nonconflicting_step_is_bitwise_ordinary_adam() -> None:
    realized_parameter = torch.nn.Parameter(torch.zeros(2))
    ordinary_parameter = torch.nn.Parameter(torch.zeros(2))
    realized_optimizer = torch.optim.Adam((realized_parameter,), lr=1e-2)
    ordinary_optimizer = torch.optim.Adam((ordinary_parameter,), lr=1e-2)
    immediate = (torch.tensor([1.0, 1.0]),)
    successor = (torch.tensor([1.0, 1.0]),)

    step = apply_optimizer_realized_tangent_step(
        realized_optimizer,
        (realized_parameter,),
        immediate,
        successor,
    )
    ordinary_optimizer.zero_grad(set_to_none=True)
    ordinary_parameter.grad = torch.tensor([1.0, 1.0])
    torch.nn.utils.clip_grad_norm_((ordinary_parameter,), GRADIENT_CLIP)
    ordinary_optimizer.step()

    assert step.conflict is False
    assert step.pre_dot > 0.0
    assert step.post_dot == step.pre_dot
    assert step.parameter_identity_error == 0.0
    torch.testing.assert_close(
        realized_parameter, ordinary_parameter, rtol=0, atol=0
    )
    realized_state = _adam_state(realized_optimizer, realized_parameter)
    ordinary_state = _adam_state(ordinary_optimizer, ordinary_parameter)
    assert realized_state.keys() == ordinary_state.keys()
    for name in realized_state:
        left = realized_state[name]
        right = ordinary_state[name]
        if isinstance(left, torch.Tensor):
            assert isinstance(right, torch.Tensor)
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        else:
            assert left == right


def test_momentum_counterexample_projects_actual_step_once() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    optimizer = torch.optim.Adam((parameter,), lr=0.1)
    for _ in range(5):
        optimizer.zero_grad(set_to_none=True)
        parameter.grad = torch.tensor([-10.0, 0.0])
        optimizer.step()
    before = parameter.detach().clone()
    step_before = float(optimizer.state[parameter]["step"])
    immediate = (torch.tensor([1.0, 0.0]),)
    successor = (torch.tensor([1.0, 0.0]),)
    raw_combined_dot = float((immediate[0] * immediate[0]).sum())

    step = apply_optimizer_realized_tangent_step(
        optimizer, (parameter,), immediate, successor
    )

    assert raw_combined_dot > 0.0
    assert step.pre_dot < 0.0
    assert step.conflict is True
    assert step.post_dot >= 0.0
    assert float(optimizer.state[parameter]["step"]) == step_before + 1.0
    actual_dot = float(
        ((before - parameter).to(torch.float64) * immediate[0]).sum()
    )
    assert actual_dot >= 0.0
    assert step.optimizer_step_increment == 1.0


def test_realized_tangent_update_moves_only_owned_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch.manual_seed(2919000)
    model = _battery_model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2939000,
        device=torch.device("cpu"),
    )
    actor_before = _state(model.full_actor_parameters())
    residual_before = _state(model.residual_parameters())
    core_critic_before = _state(tuple(model.policy.critic.parameters()))
    critic_before = _state(model.critic_parameters())
    model.begin_realized_tangent_phase()

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
    replay_calls = [0]
    original_replay = g29_source.replay_trajectory

    def counted_replay(*args, **kwargs):
        replay_calls[0] += 1
        return original_replay(*args, **kwargs)

    monkeypatch.setattr(g29_source, "replay_trajectory", counted_replay)
    metrics = optimize_optimizer_realized_tangent_update(
        model,
        torch.optim.Adam(model.full_actor_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )

    assert metrics["finite_update"] == 1.0
    assert replay_calls[0] == 2
    assert metrics["minimum_realized_displacement_post_dot"] >= -1e-7
    assert metrics["maximum_applied_parameter_identity_error"] <= 1e-7
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
    assert model.residual_output_layer_maximum_absolute_value() == 0.0
    assert all(
        value == 0.0
        for name, value in metrics.items()
        if name.endswith("_error")
    )


def test_g17_collection_retains_exact_generic_replay() -> None:
    torch.manual_seed(2919001)
    model = OptimizerRealizedTangentFullActorPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2929001,
        action_seed=2939001,
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


def test_realized_tangent_phase_rejects_nonzero_residual_and_reentry() -> None:
    model = _battery_model()
    final = model.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.1)
    with pytest.raises(RuntimeError, match="exact zero"):
        model.begin_realized_tangent_phase()
    with torch.no_grad():
        final.bias.zero_()
    model.begin_realized_tangent_phase()
    with pytest.raises(RuntimeError, match="exactly once"):
        model.begin_realized_tangent_phase()


def test_g29_result_precedence_and_configuration_are_frozen() -> None:
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
    assert configuration["g17_realized_tangent_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_realized_tangent_updates"] == 300
    assert configuration["residual"] == "exact_zero_frozen"
    assert (
        configuration["actor_gradient_rule"]
        == "equal_combined_then_realized_adam_displacement_tangent"
    )
    assert (
        configuration["actor_optimizer_state_rule"]
        == "unprojected_combined_gradient_state_projected_parameters"
    )


def test_g29_metrics_adapt_shared_projection_name_without_persisting_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[dict[str, object]]] = []

    def shared_metrics(rows):
        captured.append(rows)
        return {
            "maximum_anchor_difference": 1.0,
            "minimum_projection_post_dot": 0.25,
        }

    monkeypatch.setattr(screen.g19_screen, "_metrics", shared_metrics)
    row = {
        "maximum_replay_errors": {"logp_max_error": 0.0},
        "actor_maximum_difference": 1.0,
        "finite_updates": True,
        "lifecycle_contract_valid": True,
        "optimizer_ownership_valid": True,
        "residual_output_layer_maximum_absolute_value": 0.0,
        "minimum_realized_displacement_post_dot": 0.25,
        "maximum_applied_parameter_identity_error": 0.0,
        "minimum_actor_optimizer_step_increment": 1.0,
    }

    metrics = screen._metrics([row])

    assert captured[0][0]["minimum_projection_post_dot"] == 0.25
    assert "minimum_projection_post_dot" not in metrics
    assert metrics["operational_valid"] is True
