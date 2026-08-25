from __future__ import annotations

import pytest
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process import direction_balanced_full_actor_g30 as g30_source
from ha_ctse_process.anchored_residual_g19 import (
    GRADIENT_CLIP,
    attach_credit_baselines,
    maximum_state_difference,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.direction_balanced_full_actor_g30 import (
    DirectionBalancedFullActorPolicy,
    apply_direction_balanced_adam_step,
    compose_direction_balanced_gradients,
    optimize_direction_balanced_update,
)
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from scripts import screen_direction_balanced_full_actor_g30 as screen


def _battery_model() -> DirectionBalancedFullActorPolicy:
    model = DirectionBalancedFullActorPolicy(
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

    model.begin_direction_balanced_phase()
    actor = {id(row) for row in model.full_actor_parameters()}
    critic = {id(row) for row in model.critic_parameters()}
    residual = {id(row) for row in model.residual_parameters()}
    core_critic = {id(row) for row in model.policy.critic.parameters()}
    assert actor.isdisjoint(critic | residual | core_critic)
    assert all(row.requires_grad for row in model.full_actor_parameters())
    assert all(row.requires_grad for row in model.critic_parameters())
    assert all(not row.requires_grad for row in model.residual_parameters())
    assert all(not row.requires_grad for row in model.policy.critic.parameters())


@pytest.mark.parametrize(
    ("immediate", "successor", "expected", "zero_flags"),
    (
        ([2.0, 0.0], [4.0, 0.0], [1.0, 0.0], (False, False)),
        ([1.0, 0.0], [-0.6, 0.8], [0.2, 0.4], (False, False)),
        ([2.0, 0.0], [-7.0, 0.0], [0.0, 0.0], (False, False)),
        ([0.0, 0.0], [0.0, 0.0], [0.0, 0.0], (True, True)),
        ([0.0, 0.0], [0.0, 5.0], [0.0, 0.5], (True, False)),
        ([0.0, 3.0], [0.0, 0.0], [0.0, 0.5], (False, True)),
    ),
)
def test_direction_composition_matches_closed_form_and_zero_branches(
    immediate: list[float],
    successor: list[float],
    expected: list[float],
    zero_flags: tuple[bool, bool],
) -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    composition = compose_direction_balanced_gradients(
        (torch.tensor(immediate),),
        (torch.tensor(successor),),
        (parameter,),
    )

    torch.testing.assert_close(
        composition.gradients[0], torch.tensor(expected), rtol=0, atol=1e-7
    )
    assert composition.immediate_dot >= -1e-7
    assert composition.identity_error <= 1e-7
    assert (
        composition.immediate_zero,
        composition.successor_zero,
    ) == zero_flags


def test_high_dimensional_near_opposite_direction_is_finite_and_admissible() -> None:
    generator = torch.Generator().manual_seed(3019000)
    immediate = torch.randn(4096, generator=generator)
    successor = -immediate + 1e-4 * torch.randn(4096, generator=generator)
    parameter = torch.nn.Parameter(torch.zeros_like(immediate))

    composition = compose_direction_balanced_gradients(
        (immediate,), (successor,), (parameter,)
    )

    assert bool(torch.isfinite(composition.gradients[0]).all())
    assert composition.immediate_dot >= -1e-7
    assert composition.identity_error <= 1e-7


def test_ordinary_adam_receives_exact_composition_and_advances_once() -> None:
    balanced_parameter = torch.nn.Parameter(torch.zeros(3))
    ordinary_parameter = torch.nn.Parameter(torch.zeros(3))
    balanced_optimizer = torch.optim.Adam((balanced_parameter,), lr=1e-2)
    ordinary_optimizer = torch.optim.Adam((ordinary_parameter,), lr=1e-2)
    immediate = (torch.tensor([3.0, 0.0, 4.0]),)
    successor = (torch.tensor([-2.0, 1.0, 0.0]),)
    expected = compose_direction_balanced_gradients(
        immediate, successor, (ordinary_parameter,)
    )

    step = apply_direction_balanced_adam_step(
        balanced_optimizer,
        (balanced_parameter,),
        immediate,
        successor,
    )
    ordinary_optimizer.zero_grad(set_to_none=True)
    ordinary_parameter.grad = expected.gradients[0].clone()
    torch.nn.utils.clip_grad_norm_((ordinary_parameter,), GRADIENT_CLIP)
    ordinary_optimizer.step()

    assert step.optimizer_step_increment == 1.0
    assert step.composition.immediate_dot >= -1e-7
    torch.testing.assert_close(
        balanced_parameter, ordinary_parameter, rtol=0, atol=0
    )
    balanced_state = _adam_state(balanced_optimizer, balanced_parameter)
    ordinary_state = _adam_state(ordinary_optimizer, ordinary_parameter)
    assert balanced_state.keys() == ordinary_state.keys()
    for name in balanced_state:
        left = balanced_state[name]
        right = ordinary_state[name]
        if isinstance(left, torch.Tensor):
            assert isinstance(right, torch.Tensor)
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        else:
            assert left == right


def test_direction_balanced_update_moves_only_owned_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch.manual_seed(3019001)
    model = _battery_model()
    trajectory = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=3039001,
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
    metrics = optimize_direction_balanced_update(
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
    assert metrics["minimum_direction_immediate_dot"] >= -1e-7
    assert metrics["maximum_direction_composition_identity_error"] <= 1e-7
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
    torch.manual_seed(3019002)
    model = DirectionBalancedFullActorPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=3029002,
        action_seed=3039002,
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


def test_direction_balanced_phase_rejects_nonzero_residual_and_reentry() -> None:
    model = _battery_model()
    final = model.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.1)
    with pytest.raises(RuntimeError, match="exact zero"):
        model.begin_direction_balanced_phase()
    with torch.no_grad():
        final.bias.zero_()
    model.begin_direction_balanced_phase()
    with pytest.raises(RuntimeError, match="exactly once"):
        model.begin_direction_balanced_phase()


def test_g30_result_precedence_and_configuration_are_frozen() -> None:
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
    assert configuration["g17_direction_balanced_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_direction_balanced_updates"] == 300
    assert configuration["residual"] == "exact_zero_frozen"
    assert (
        configuration["actor_gradient_rule"]
        == "equal_global_unit_gradient_directions"
    )
    assert configuration["actor_global_rescale"] == "none_existing_gradient_clip_only"
    assert configuration["actor_optimizer_state_rule"] == "ordinary_adam_on_applied_direction"
    assert configuration["checkpoint_identity"] == "fresh_no_g28_g29_resume"


def test_g30_metrics_adapt_shared_projection_name_without_persisting_it(
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
        "minimum_direction_immediate_dot": 0.25,
        "maximum_direction_composition_identity_error": 0.0,
        "minimum_actor_optimizer_step_increment": 1.0,
    }

    metrics = screen._metrics([row])

    assert captured[0][0]["minimum_projection_post_dot"] == 0.25
    assert "minimum_projection_post_dot" not in metrics
    assert metrics["operational_valid"] is True
