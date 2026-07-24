from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.centered_residual_g20 import (
    CenteredCounterfactualRosterPolicy,
    FastCenteredCounterfactualResidualPolicy,
    attach_slow_credit,
    center_residual_over_active_set,
    compute_counterfactual_advantage,
    maximum_state_difference,
    optimize_delayed_update,
    optimize_fast_update,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from scripts import screen_centered_counterfactual_residual_g20 as screen


def _battery_model() -> FastCenteredCounterfactualResidualPolicy:
    model = FastCenteredCounterfactualResidualPolicy(
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
    torch.manual_seed(2019000)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    centered = CenteredCounterfactualRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = centered.load_state_dict(base.state_dict(), strict=False)
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
    centered_sample = centered.forward_step(**arguments, sampling_noise=noise)
    _assert_step_equal(base_sample, centered_sample)
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        centered.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
        centered.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
    )
    # The zero-initialized residual head must also center to exactly zero.
    torch.testing.assert_close(
        centered_sample.centered_residual,
        torch.zeros_like(centered_sample.centered_residual),
        rtol=0,
        atol=0,
    )


def test_active_set_centering_sums_to_zero_and_inactive_rows_are_exact_zero() -> None:
    torch.manual_seed(2019001)
    raw = torch.randn(4, 5, 3)
    active_mask = torch.tensor(
        [
            [True, True, True, False, False],
            [True, False, True, True, False],
            [True, True, True, True, True],
            [True, False, False, False, False],
        ]
    )
    centered = center_residual_over_active_set(raw, active_mask)

    row_sums = torch.where(
        active_mask.unsqueeze(-1), centered, torch.zeros_like(centered)
    ).sum(dim=-2)
    assert float(row_sums.abs().max()) < 1e-6

    inactive = torch.where(
        active_mask.unsqueeze(-1), torch.zeros_like(centered), centered
    )
    assert float(inactive.abs().max()) == 0.0


def test_member_resolved_counterfactual_advantage_matches_direct_evaluation() -> None:
    torch.manual_seed(2019002)
    critic_state = torch.randn(2, 3)
    active_mask = torch.tensor([[True, True, False], [True, True, True]])
    residual_table = torch.randn(2, 3, 2)

    weights = torch.tensor([1.0, 2.0, -3.0])

    def synthetic_q_slow(
        cs: torch.Tensor, mask: torch.Tensor, table: torch.Tensor
    ) -> torch.Tensor:
        # A deterministic, asymmetric function of the residual table so the
        # leave-one-out contrast differs across members.
        weighted = (table.sum(dim=-1) * weights).sum(dim=-1)
        return cs.sum(dim=-1) + weighted

    advantage = compute_counterfactual_advantage(
        synthetic_q_slow,
        critic_state=critic_state,
        active_mask=active_mask,
        residual_table=residual_table,
    )
    assert advantage.shape == active_mask.shape

    baseline = synthetic_q_slow(critic_state, active_mask, residual_table)
    for member in range(active_mask.shape[-1]):
        modified = residual_table.clone()
        modified[..., member, :] = 0.0
        direct = baseline - synthetic_q_slow(critic_state, active_mask, modified)
        torch.testing.assert_close(
            advantage[..., member],
            torch.where(
                active_mask[..., member], direct, torch.zeros_like(direct)
            ),
            rtol=0,
            atol=0,
        )
    # Inactive row is exactly zero.
    assert advantage[0, 2] == 0.0
    # The synthetic Q_slow was built to differ per member for the fully
    # active row; confirm the advantage is not degenerate.
    row = advantage[1]
    assert not bool(torch.allclose(row[0], row[1]))
    assert not bool(torch.allclose(row[1], row[2]))


def test_fast_then_delayed_update_keeps_anchor_exact_and_completes_finitely() -> None:
    torch.manual_seed(2019003)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2039001,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    fast_metrics = optimize_fast_update(
        model,
        fast_optimizer,
        fast_trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
    )
    assert fast_metrics["finite_update"] == 1.0
    assert model.residual_output_layer_maximum_absolute_value() == 0.0

    anchor = model.anchor_state()
    model.begin_delayed_phase()
    assert model.phase == "delayed"
    assert all(
        not parameter.requires_grad for parameter in model.fast_actor_parameters()
    )
    assert all(
        not parameter.requires_grad
        for parameter in model.immediate_baseline.parameters()
    )
    assert all(
        not parameter.requires_grad
        for parameter in model.policy.critic.parameters()
    )
    delayed_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(2, 3),
        action_seed=2039002,
        device=torch.device("cpu"),
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-3)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-3)
    delayed_metrics = optimize_delayed_update(
        model,
        residual_optimizer,
        critic_optimizer,
        delayed_trajectory,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )

    assert delayed_metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    # At delayed-phase entry R_t is identically zero (mandatory per the
    # spec), so the leave-one-out contrast Q_slow(s,R) - Q_slow(s, R with
    # row i zeroed) is Q_slow evaluated twice on the *same* input and is
    # therefore exactly zero for every member on this first collection.
    # The residual head's only gradient path is this (exactly zero)
    # advantage weighting log pi, so it receives exactly zero gradient and
    # Adam leaves it unmoved.  This is a structural property of the
    # leave-one-out credit at cold start, not a bug in the update rule;
    # pin it explicitly so a future change is visible either way.
    assert model.residual_output_layer_maximum_absolute_value() == 0.0
    assert all(
        not parameter.requires_grad
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    )


def test_delayed_gradient_ownership_excludes_fast_surfaces_and_residual_from_critic() -> None:
    torch.manual_seed(2019004)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2039003,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    model.begin_delayed_phase()
    trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(2, 3),
        action_seed=2039004,
        device=torch.device("cpu"),
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-3)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-3)

    # Frozen fast surfaces must carry no *new* gradient from the delayed
    # update.  The fast phase's own optimizer step legitimately populated
    # .grad on these (then-trainable) parameters and neither the residual
    # nor the critic optimizer's zero_grad() clears parameters outside its
    # own group, so clear the stale fast-phase grad here to make the check
    # below a true test of the delayed update's gradient ownership rather
    # than a leftover artifact of the earlier fast-phase backward pass.
    frozen_named = [
        (name, parameter)
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    ] + [("immediate_baseline", parameter) for parameter in model.immediate_baseline.parameters()]
    for _, parameter in frozen_named:
        parameter.grad = None

    optimize_delayed_update(
        model,
        residual_optimizer,
        critic_optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )

    for name, parameter in frozen_named:
        assert parameter.requires_grad is False
        assert parameter.grad is None, f"{name} unexpectedly received a gradient"

    # Directly verify the Q_slow regression alone has no gradient on the
    # residual head: build the same critic loss in isolation and check.
    for parameter in model.residual_parameters():
        parameter.grad = None
    with torch.no_grad():
        replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    values = model.slow_action_value(
        trajectory.critic_states, replay.active_mask, replay.centered_residual
    )
    slow_value_loss = torch.square(values - trajectory.old_values).mean()
    slow_value_loss.backward()
    for parameter in model.residual_parameters():
        assert parameter.grad is None
    for parameter in model.critic_parameters():
        assert parameter.grad is not None


def test_battery_replay_and_inactive_rows_remain_exact_with_nonzero_residual() -> None:
    torch.manual_seed(2019005)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(4, 5), action_seed=2039005, device=torch.device("cpu")
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    model.begin_delayed_phase()
    move_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(6, 7), action_seed=2039006, device=torch.device("cpu")
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    delayed_metrics = optimize_delayed_update(
        model,
        residual_optimizer,
        critic_optimizer,
        move_trajectory,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )
    assert delayed_metrics["finite_update"] == 1.0
    # The leave-one-out credit is exactly zero while R_t is identically
    # zero (see the cold-start finding above), so training alone cannot
    # produce a nonzero residual here.  Set one directly so this test can
    # target what it actually claims: replay/inactive-row exactness "with
    # a nonzero residual active," independent of how that state is reached.
    with torch.no_grad():
        final = model.policy.delayed_residual[-1]
        assert isinstance(final, torch.nn.Linear)
        final.bias.add_(0.05)
        final.weight.add_(0.01)
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(8, 9, 10), action_seed=2039007, device=torch.device("cpu")
    )
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    errors = replay_errors(replay, trajectory)
    assert all(value == 0.0 for value in errors.values())
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    assert torch.count_nonzero(inactive_actions) == 0


def test_g17_collection_replay_remains_exact_with_nonzero_residual() -> None:
    torch.manual_seed(2019006)
    model = FastCenteredCounterfactualResidualPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2029006,
        action_seed=2039008,
        device=torch.device("cpu"),
    )
    trajectory = attach_slow_credit(model, raw, device=torch.device("cpu"))
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    assert optimize_fast_update(
        model, fast_optimizer, trajectory, device=torch.device("cpu"), ppo_passes=1
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(2, 3),
        ledger_seed=2029006,
        action_seed=2039008,
        device=torch.device("cpu"),
    )
    delayed = attach_slow_credit(model, raw, device=torch.device("cpu"))
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    metrics = optimize_delayed_update(
        model,
        residual_optimizer,
        critic_optimizer,
        delayed,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    # As in the battery case, the leave-one-out credit is exactly zero
    # while R_t is identically zero, so training alone cannot move the
    # residual away from its mandatory zero entry state.  Inject a direct
    # perturbation so the replay-exactness check below actually exercises
    # "a nonzero residual active," as the acceptance item requires.
    with torch.no_grad():
        final = model.policy.delayed_residual[-1]
        assert isinstance(final, torch.nn.Linear)
        final.bias.add_(0.05)
        final.weight.add_(0.01)
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(4, 5),
        ledger_seed=2029006,
        action_seed=2039008,
        device=torch.device("cpu"),
    )
    replay_trajectory_object = attach_slow_credit(model, raw, device=torch.device("cpu"))
    replay = replay_trajectory(model, replay_trajectory_object, device=torch.device("cpu"))
    errors = replay_errors(replay, replay_trajectory_object)
    assert all(value == 0.0 for value in errors.values())
    inactive_actions = torch.where(
        replay_trajectory_object.active_mask.unsqueeze(-1),
        torch.zeros_like(replay_trajectory_object.actions),
        replay_trajectory_object.actions,
    )
    assert torch.count_nonzero(inactive_actions) == 0


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


def test_g20_result_precedence_is_first_match() -> None:
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
    assert configuration["fast_optimizer"] == "adam"
    assert configuration["delayed_residual_optimizer"] == "adam"
    assert configuration["critic_optimizer"] == "adam"
    assert configuration["delayed_residual_initialization"] == "exact_zero_output"
