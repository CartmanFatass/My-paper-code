from __future__ import annotations

import torch
from torch import nn

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchor_action_advantage_g20r import (
    AnchorActionAdvantageRosterPolicy,
    FastAnchorActionAdvantagePolicy,
    _batched_routing_order,
    _member_policy_loss,
    attach_prefix_credit,
    center_residual_over_active_set,
    maximum_state_difference,
    optimize_delayed_update,
    optimize_fast_update,
    prefix_critic_values,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.centered_residual_g20 import (
    FastCenteredCounterfactualResidualPolicy as RetiredFastPolicy,
    center_residual_over_active_set as retired_center_residual,
    compute_counterfactual_advantage as retired_compute_counterfactual_advantage,
    optimize_delayed_update as retired_optimize_delayed_update,
    optimize_fast_update as retired_optimize_fast_update,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from scripts import screen_anchor_action_advantage_g20r as screen
from scripts import screen_centered_counterfactual_residual_g20 as retired_screen


def _battery_model(hidden_dim: int = 16) -> FastAnchorActionAdvantagePolicy:
    model = FastAnchorActionAdvantagePolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=hidden_dim,
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


# ---------------------------------------------------------------------------
# Exact zero-residual equivalence to the base policy.
# ---------------------------------------------------------------------------


def test_zero_residual_exactly_matches_base_policy_in_all_modes() -> None:
    torch.manual_seed(2820000)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    anchor_policy = AnchorActionAdvantageRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = anchor_policy.load_state_dict(
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
    anchor_sample = anchor_policy.forward_step(**arguments, sampling_noise=noise)
    _assert_step_equal(base_sample, anchor_sample)
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        anchor_policy.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
        anchor_policy.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
    )
    torch.testing.assert_close(
        anchor_sample.centered_residual,
        torch.zeros_like(anchor_sample.centered_residual),
        rtol=0,
        atol=0,
    )


# ---------------------------------------------------------------------------
# Exact active-set centering.
# ---------------------------------------------------------------------------


def test_active_set_centering_sums_to_zero_and_inactive_rows_are_exact_zero() -> None:
    torch.manual_seed(2820001)
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


# ---------------------------------------------------------------------------
# Helpers shared by the credit-rule tests below.
# ---------------------------------------------------------------------------


def _rollout(
    model: FastAnchorActionAdvantagePolicy,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_states: torch.Tensor,
    rewards: torch.Tensor,
    noise: torch.Tensor,
):
    from types import SimpleNamespace

    time_steps, batch, capacity, _ = observations.shape
    hidden = torch.zeros(batch, capacity, model.hidden_dim)
    rows: dict[str, torch.Tensor] = {
        "observations": observations,
        "active_mask": active_mask,
        "critic_states": critic_states,
        "actions": torch.zeros(time_steps, batch, capacity, model.action_dim),
        "pre_tanh_actions": torch.zeros(time_steps, batch, capacity, model.action_dim),
        "old_log_probs": torch.zeros(time_steps, batch, capacity),
        "rewards": rewards,
        "hidden_before": torch.zeros(time_steps, batch, capacity, model.hidden_dim),
        "hidden_after": torch.zeros(time_steps, batch, capacity, model.hidden_dim),
        "prefix_action_sums": torch.zeros(
            time_steps, batch, capacity, model.action_dim
        ),
    }
    model.eval()
    with torch.no_grad():
        for time in range(time_steps):
            rows["hidden_before"][time] = hidden
            output = model.forward_step(
                observations=observations[time],
                active_mask=active_mask[time],
                critic_state=critic_states[time],
                hidden=hidden,
                sampling_noise=noise[time],
            )
            rows["actions"][time] = output.actions
            rows["pre_tanh_actions"][time] = output.pre_tanh_actions
            rows["old_log_probs"][time] = output.token_log_probs
            rows["hidden_after"][time] = output.next_hidden
            rows["prefix_action_sums"][time] = output.prefix_action_sums
            hidden = output.next_hidden
    return SimpleNamespace(**rows, outcomes=(), ledgers=())


def _small_fixture(capacity: int = 4, batch: int = 3, time_steps: int = 5):
    observations = torch.randn(time_steps, batch, capacity, 5)
    active_mask = torch.ones(time_steps, batch, capacity, dtype=torch.bool)
    active_mask[:, :, -1] = False
    critic_states = torch.randn(time_steps, batch, 4)
    rewards = torch.randn(time_steps, batch)
    noise = torch.randn(time_steps, batch, capacity, 2)
    return observations, active_mask, critic_states, rewards, noise


def _make_model(capacity: int = 4, hidden_dim: int = 8) -> FastAnchorActionAdvantagePolicy:
    model = FastAnchorActionAdvantagePolicy(
        5, 4, member_capacity=capacity, action_dim=2, hidden_dim=hidden_dim
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


# ---------------------------------------------------------------------------
# Baseline independence.
# ---------------------------------------------------------------------------


def test_baseline_independent_of_the_factual_action_at_its_own_position() -> None:
    torch.manual_seed(2820002)
    model = _make_model()
    observations, active_mask, critic_states, rewards, noise = _small_fixture()
    raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )

    # Identify, for (time=0, batch=0), the *last* valid routing position and
    # the member occupying it.  Perturbing that member's action cannot ripple
    # into any later position's prefix (there is none), isolating exactly the
    # claim under test: b_j must not depend on a_{j,t}.
    order = model.policy._routing_order(active_mask[0], observations[0])
    active_count = int(active_mask[0, 0].sum())
    last_position = active_count - 1
    member = int(order[0, last_position])

    attached_original = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=13579
    )

    perturbed = _clone_namespace(raw)
    perturbed.pre_tanh_actions = perturbed.pre_tanh_actions.clone()
    perturbed.pre_tanh_actions[0, 0, member] += 5.0

    attached_perturbed = attach_prefix_credit(
        model, perturbed, device=torch.device("cpu"), baseline_seed=13579
    )

    torch.testing.assert_close(
        attached_original.old_baseline[0, 0, last_position],
        attached_perturbed.old_baseline[0, 0, last_position],
        rtol=0,
        atol=0,
    )
    assert not bool(
        torch.equal(
            attached_original.old_values[0, 0, last_position],
            attached_perturbed.old_values[0, 0, last_position],
        )
    ), "fixture failed to perturb the factual Q_j value; test proves nothing"


def _clone_namespace(namespace):
    from types import SimpleNamespace

    return SimpleNamespace(**vars(namespace))


# ---------------------------------------------------------------------------
# Prefix integrity: Q_j must never see an action at a position > j.
# ---------------------------------------------------------------------------


def test_prefix_critic_ignores_actions_at_later_routing_positions() -> None:
    torch.manual_seed(2820003)
    model = _make_model()
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=4
    )
    raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )
    order = model.policy._routing_order(active_mask[0], observations[0])
    active_count = int(active_mask[0, 0].sum())
    assert active_count >= 2, "fixture requires at least two active members"
    first_position_member = int(order[0, 0])

    attached_original = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=24680
    )

    perturbed = _clone_namespace(raw)
    perturbed.pre_tanh_actions = perturbed.pre_tanh_actions.clone()
    for position in range(1, active_count):
        member = int(order[0, position])
        perturbed.pre_tanh_actions[0, 0, member] += 7.0

    attached_perturbed = attach_prefix_credit(
        model, perturbed, device=torch.device("cpu"), baseline_seed=24680
    )

    # Position 0's factual Q_j, anchor baseline and advantage cannot depend on
    # any later position's action -- assert all three survive the mutation.
    torch.testing.assert_close(
        attached_original.old_values[0, 0, 0],
        attached_perturbed.old_values[0, 0, 0],
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        attached_original.old_baseline[0, 0, 0],
        attached_perturbed.old_baseline[0, 0, 0],
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        attached_original.old_prefix_advantage[0, 0, first_position_member],
        attached_perturbed.old_prefix_advantage[0, 0, first_position_member],
        rtol=0,
        atol=0,
    )
    # Sanity: the mutation must have actually changed *something* downstream
    # (a later position's factual value), or this test would pass vacuously.
    assert not bool(
        torch.equal(
            attached_original.old_values[0, 0, active_count - 1],
            attached_perturbed.old_values[0, 0, active_count - 1],
        )
    ), "fixture failed to perturb a later position; test proves nothing"


# ---------------------------------------------------------------------------
# Non-inertness: the direct regression against the retired G20 rule.
# ---------------------------------------------------------------------------


class _SyntheticActionSensitiveQ(nn.Module):
    """A fixed, deliberately action-sensitive Q_j.

    Mirrors the pre-freeze probe methodology (design section 7): sums the
    trailing ``action_dim`` feature columns, which are exactly the prefix-
    through-j block that ``_prefix_critic_forward`` appends last.  Carries
    one inert, unused parameter solely so ``model.critic_parameters()``
    remains non-empty when this stand-in replaces the real ``prefix_critic``
    -- ``torch.optim.Adam`` rejects an empty parameter list -- without that
    parameter influencing the fixed, deliberately-chosen output.
    """

    def __init__(self, action_dim: int) -> None:
        super().__init__()
        self.action_dim = action_dim
        self.unused = nn.Parameter(torch.zeros(1))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        # `+ self.unused.sum() * 0.0` keeps `unused` connected to the output
        # so a critic-loss `.backward()` has a valid graph and defines a
        # (zero) gradient for it, without perturbing the deliberately fixed,
        # action-sensitive value by even a rounding error.
        return (
            features[..., -self.action_dim :].sum(dim=-1, keepdim=True)
            + self.unused.sum() * 0.0
        )


def test_non_inertness_at_zero_residual_contrasts_with_retired_rule() -> None:
    torch.manual_seed(2820004)
    model = _make_model(capacity=4)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=4, time_steps=3
    )
    raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    fast_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=1
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    assert model.residual_output_layer_maximum_absolute_value() == 0.0
    model.begin_delayed_phase()

    # Swap in the deliberately action-sensitive synthetic Q_j, exactly as the
    # pre-freeze probe did, so the entry-state numbers are reproducible.
    model.prefix_critic = _SyntheticActionSensitiveQ(model.action_dim)

    entry_raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )
    trajectory = attach_prefix_credit(
        model, entry_raw, device=torch.device("cpu"), baseline_seed=2
    )

    advantage = trajectory.old_prefix_advantage
    assert float(advantage.abs().max()) > 0.0

    # Member-distinct: at least one fully-active row has two members whose
    # advantages differ.
    found_distinct = False
    for time in range(advantage.shape[0]):
        for batch in range(advantage.shape[1]):
            active_members = active_mask[time, batch].nonzero(as_tuple=True)[0]
            values = advantage[time, batch, active_members]
            if active_members.numel() >= 2 and not bool(
                torch.allclose(values[0], values[1])
            ):
                found_distinct = True
    assert found_distinct

    # Contrast: the retired G20 leave-one-out rule is exactly zero on this
    # same zero-residual fixture, for any Q_slow, since it compares
    # Q_slow(s, R) against Q_slow(s, R-with-row-zeroed) and R is identically
    # zero at entry -- both arguments are the same tensor.
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    torch.testing.assert_close(
        replay.centered_residual, torch.zeros_like(replay.centered_residual)
    )
    retired_centered = retired_center_residual(
        torch.zeros_like(replay.centered_residual), replay.active_mask
    )

    def _synthetic_leave_one_out_q(cs, mask, table):
        return table.sum(dim=(-2, -1)) + cs.sum(dim=-1)

    retired_advantage = retired_compute_counterfactual_advantage(
        _synthetic_leave_one_out_q,
        critic_state=trajectory.critic_states,
        active_mask=trajectory.active_mask,
        residual_table=retired_centered,
    )
    assert float(retired_advantage.abs().max()) == 0.0

    # Residual gradient at entry: run the actual PPO surrogate against the
    # synthetic-Q advantage and confirm the residual head receives a nonzero
    # gradient even though its weights are currently exactly zero.
    replay_with_grad = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    loss = _member_policy_loss(replay_with_grad, trajectory, advantage)
    for parameter in model.residual_parameters():
        parameter.grad = None
    loss.backward()
    gradient_maxima = [
        float(parameter.grad.detach().abs().max())
        for parameter in model.residual_parameters()
        if parameter.grad is not None
    ]
    assert gradient_maxima and max(gradient_maxima) > 0.0


def _retired_battery_model(hidden_dim: int = 16) -> RetiredFastPolicy:
    model = RetiredFastPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=hidden_dim,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


def test_real_optimizer_step_moves_residual_off_zero_under_synthetic_q_only() -> None:
    """Pins the exact endpoint the G20R repair exists to reach.

    `test_non_inertness_at_zero_residual_contrasts_with_retired_rule` proves
    the score-function *gradient* on the residual head is nonzero at entry
    under an action-sensitive synthetic Q_j.  Nonzero gradient implies the
    optimizer will move the parameter -- but "implies" is exactly what failed
    to hold for G20 in spirit: there the gradient itself was the structural
    zero, so any optimizer was a no-op.  This test does not repeat the
    gradient claim; it runs one real `optimize_delayed_update` with a real
    Adam optimizer over `residual_parameters()` and checks the parameter
    itself, then contrasts it against G20's retired rule taking an identical
    kind of step on an equivalent zero-residual entry state.

    Deliberately NOT exercised here: the untrained, real `prefix_critic`.  An
    untrained Q_j may be close to action-independent at initialization, so
    the residual legitimately might not move yet -- that is precisely what
    result branch 2 (NON_IDENTIFIED_ACTION_CRITIC) exists to report, and
    asserting movement under the real critic would encode a false invariant.
    The synthetic Q_j guarantees action sensitivity by construction, so this
    test isolates "does a live gradient actually move the parameter" from
    "did training make Q_j identify the action" -- the latter is not this
    test's claim.
    """

    torch.manual_seed(2820011)
    model = _make_model(capacity=4)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=4, time_steps=3
    )
    raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    fast_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=11
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    assert model.residual_output_layer_maximum_absolute_value() == 0.0
    model.begin_delayed_phase()
    model.prefix_critic = _SyntheticActionSensitiveQ(model.action_dim)

    entry_raw = _rollout(
        model,
        observations=observations,
        active_mask=active_mask,
        critic_states=critic_states,
        rewards=rewards,
        noise=noise,
    )
    trajectory = attach_prefix_credit(
        model, entry_raw, device=torch.device("cpu"), baseline_seed=12
    )
    assert float(trajectory.old_prefix_advantage.abs().max()) > 0.0

    anchor_before = model.anchor_state()
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    metrics = optimize_delayed_update(
        model,
        residual_optimizer,
        critic_optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0
    assert maximum_state_difference(anchor_before, model.anchor_state()) == 0.0

    # Direct contrast: G20's retired leave-one-out rule, run through its own
    # real fast-then-delayed update with a real Adam optimizer starting from
    # an equivalent zero-residual entry state, stays pinned at exactly 0.0.
    # No synthetic Q_slow swap is needed on this side: at the mandated
    # zero-residual entry the centered residual table is identically zero,
    # so Q_slow(s, R) - Q_slow(s, R-with-row-zeroed) compares the same
    # all-zero tensor to itself for *any* Q_slow -- the retired rule's
    # gradient is the structural zero this repair replaces.
    retired_model = _retired_battery_model()
    retired_fast_trajectory = retired_screen.collect_battery_trajectory(
        retired_model,
        episode_ids=(0, 1),
        action_seed=2039101,
        device=torch.device("cpu"),
    )
    retired_fast_optimizer = torch.optim.Adam(
        retired_model.fast_actor_parameters()
        + tuple(retired_model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    retired_optimize_fast_update(
        retired_model,
        retired_fast_optimizer,
        retired_fast_trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
    )
    assert retired_model.residual_output_layer_maximum_absolute_value() == 0.0
    retired_model.begin_delayed_phase()
    retired_delayed_trajectory = retired_screen.collect_battery_trajectory(
        retired_model,
        episode_ids=(2, 3),
        action_seed=2039102,
        device=torch.device("cpu"),
    )
    retired_residual_optimizer = torch.optim.Adam(
        retired_model.residual_parameters(), lr=1e-2
    )
    retired_critic_optimizer = torch.optim.Adam(
        retired_model.critic_parameters(), lr=1e-2
    )
    retired_metrics = retired_optimize_delayed_update(
        retired_model,
        retired_residual_optimizer,
        retired_critic_optimizer,
        retired_delayed_trajectory,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )
    assert retired_metrics["finite_update"] == 1.0
    assert retired_model.residual_output_layer_maximum_absolute_value() == 0.0


# ---------------------------------------------------------------------------
# Gradient ownership.
# ---------------------------------------------------------------------------


def test_delayed_gradient_ownership_excludes_fast_surfaces_and_residual_from_critic() -> None:
    torch.manual_seed(2820005)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2939001,
        baseline_seed=2949001,
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
        action_seed=2939002,
        baseline_seed=2949002,
        device=torch.device("cpu"),
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-3)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-3)

    frozen_named = [
        (name, parameter)
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    ] + [
        ("immediate_baseline", parameter)
        for parameter in model.immediate_baseline.parameters()
    ]
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

    # Directly verify the Q_j regression alone has no gradient on the
    # residual head: build the same critic loss in isolation and check.
    for parameter in model.residual_parameters():
        parameter.grad = None
    q_now = prefix_critic_values(model, trajectory, device=torch.device("cpu"))
    loss = torch.square(q_now - trajectory.old_values).mean()
    loss.backward()
    for parameter in model.residual_parameters():
        assert parameter.grad is None
    for parameter in model.critic_parameters():
        assert parameter.grad is not None


# ---------------------------------------------------------------------------
# Exact replay and inactive-row zero likelihood on both sources.
# ---------------------------------------------------------------------------


def test_battery_replay_and_inactive_rows_remain_exact_with_nonzero_residual() -> None:
    torch.manual_seed(2820006)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(4, 5),
        action_seed=2939005,
        baseline_seed=2949005,
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
    move_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(6, 7),
        action_seed=2939006,
        baseline_seed=2949006,
        device=torch.device("cpu"),
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
    with torch.no_grad():
        final = model.policy.delayed_residual[-1]
        assert isinstance(final, torch.nn.Linear)
        final.bias.add_(0.05)
        final.weight.add_(0.01)
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(8, 9, 10),
        action_seed=2939007,
        baseline_seed=2949007,
        device=torch.device("cpu"),
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
    torch.manual_seed(2820007)
    model = FastAnchorActionAdvantagePolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2829006,
        action_seed=2839008,
        device=torch.device("cpu"),
    )
    trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=2869008
    )
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
        ledger_seed=2829006,
        action_seed=2839008,
        device=torch.device("cpu"),
    )
    delayed = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=2869009
    )
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
    with torch.no_grad():
        final = model.policy.delayed_residual[-1]
        assert isinstance(final, torch.nn.Linear)
        final.bias.add_(0.05)
        final.weight.add_(0.01)
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(4, 5),
        ledger_seed=2829006,
        action_seed=2839008,
        device=torch.device("cpu"),
    )
    replay_trajectory_object = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=2869010
    )
    replay = replay_trajectory(model, replay_trajectory_object, device=torch.device("cpu"))
    errors = replay_errors(replay, replay_trajectory_object)
    assert all(value == 0.0 for value in errors.values())
    inactive_actions = torch.where(
        replay_trajectory_object.active_mask.unsqueeze(-1),
        torch.zeros_like(replay_trajectory_object.actions),
        replay_trajectory_object.actions,
    )
    assert torch.count_nonzero(inactive_actions) == 0


# ---------------------------------------------------------------------------
# One finite update per phase; delayed phase begins exactly once at exact zero.
# ---------------------------------------------------------------------------


def test_fast_then_delayed_update_keeps_anchor_exact_and_completes_finitely() -> None:
    torch.manual_seed(2820008)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2939009,
        baseline_seed=2949009,
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
        action_seed=2939010,
        baseline_seed=2949010,
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
    assert all(
        not parameter.requires_grad
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    )


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


# ---------------------------------------------------------------------------
# First-match branch precedence, including branch 2 before branch 4.
# ---------------------------------------------------------------------------


def _passing_metrics() -> dict:
    return {
        "operational_valid": True,
        "q_identification_ok": True,
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


def test_g20r_result_precedence_is_first_match() -> None:
    passing = _passing_metrics()
    assert screen.select_result_branch(passing) == screen.PROMISING_BRANCH
    assert screen.select_result_branch(
        passing | {"q_identification_ok": False}
    ) == screen.NON_IDENTIFIED_BRANCH
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


def test_non_identified_branch_precedes_no_delayed_access_branch_when_both_hold() -> None:
    """Section 9: branch 2 (non-identified critic) must fire before branch 4
    (no delayed access) when both conditions independently hold -- a critic
    that never learned action sensitivity must never be reported as a
    behavioural absence-of-delayed-access finding."""

    passing = _passing_metrics()
    both_fail = passing | {
        "q_identification_ok": False,
        "g18_gain_over_anchor": 0.01,  # also fails the G18-access floor
    }
    assert bool(both_fail["q_identification_ok"]) is False
    assert not (
        float(both_fail["g18_gain_over_anchor"]) >= screen.G18_GAIN_FLOOR
    )
    assert screen.select_result_branch(both_fail) == screen.NON_IDENTIFIED_BRANCH
    assert screen.select_result_branch(both_fail) != screen.NO_G18_ACCESS_BRANCH


def test_screen_configuration_matches_frozen_design() -> None:
    configuration = screen._configuration()
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_delayed_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_delayed_updates"] == 300
    assert configuration["baseline_samples_k"] == 8
    assert configuration["fast_optimizer"] == "adam"
    assert configuration["delayed_residual_optimizer"] == "adam"
    assert configuration["critic_optimizer"] == "adam"
    assert configuration["delayed_residual_initialization"] == "exact_zero_output"


def test_batched_routing_order_matches_per_step_routing_order() -> None:
    torch.manual_seed(2820009)
    model = _make_model()
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=3
    )
    batched = _batched_routing_order(model.policy, observations, active_mask)
    for time in range(observations.shape[0]):
        expected = model.policy._routing_order(active_mask[time], observations[time])
        torch.testing.assert_close(batched[time], expected, rtol=0, atol=0)
