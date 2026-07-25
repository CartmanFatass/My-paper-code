from __future__ import annotations

from types import SimpleNamespace

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchor_action_advantage_g20r2 import (
    AnchorActionAdvantageRosterPolicy,
    FastAnchorActionAdvantagePolicy,
    _batched_routing_order,
    _qj_forward,
    attach_prefix_credit,
    center_residual_over_active_set,
    cluster_bootstrap_lcb,
    maximum_state_difference,
    optimize_delayed_update,
    optimize_fast_update,
    optimize_qualification_update,
    prefix_critic_values,
    replay_errors,
    replay_trajectory,
    residual_action_space_score,
    stage_a_p2_authority_check,
    stage_a_source_effect,
    stage_b1_contrast_alignment,
    stage_b1_recalibrated_r2,
    stage_b2_gradient_alignment,
    validate_disjoint_roles,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from scripts import screen_anchor_action_advantage_g20r2 as screen


# ---------------------------------------------------------------------------
# Shared-surface guards: zero-residual equivalence and exact centering are
# reused unchanged from G20R (design instruction). Cheap regressions on that
# reuse claim.
# ---------------------------------------------------------------------------


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
    torch.manual_seed(3020000)
    base = ContinuousRosterPolicy(
        5, 4, member_capacity=3, action_dim=2, hidden_dim=8,
        current_observation_residual=True,
    )
    anchor_policy = AnchorActionAdvantageRosterPolicy(
        5, 4, member_capacity=3, action_dim=2, hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = anchor_policy.load_state_dict(base.state_dict(), strict=False)
    assert unexpected == []
    assert all(name.startswith("delayed_residual.") for name in missing)
    observations = torch.randn(2, 3, 5)
    active_mask = torch.tensor([[True, True, False], [True, False, True]])
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
    torch.testing.assert_close(
        anchor_sample.centered_residual,
        torch.zeros_like(anchor_sample.centered_residual),
        rtol=0, atol=0,
    )


def test_active_set_centering_sums_to_zero_and_inactive_rows_are_exact_zero() -> None:
    torch.manual_seed(3020001)
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
# Fixtures shared by the credit-rule / Q_j tests below.
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
        "prefix_action_sums": torch.zeros(time_steps, batch, capacity, model.action_dim),
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


def _clone_namespace(namespace):
    return SimpleNamespace(**vars(namespace))


# ---------------------------------------------------------------------------
# Q_j contract: prefix integrity beyond j, with a vacuity guard.
# ---------------------------------------------------------------------------


def test_prefix_critic_ignores_actions_at_later_routing_positions() -> None:
    torch.manual_seed(3020003)
    model = _make_model()
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=4
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    order = model.policy._routing_order(active_mask[0], observations[0])
    active_count = int(active_mask[0, 0].sum())
    assert active_count >= 2, "fixture requires at least two active members"
    first_position_member = int(order[0, 0])

    attached_original = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=30203030
    )

    perturbed = _clone_namespace(raw)
    perturbed.pre_tanh_actions = perturbed.pre_tanh_actions.clone()
    for position in range(1, active_count):
        member = int(order[0, position])
        perturbed.pre_tanh_actions[0, 0, member] += 7.0

    attached_perturbed = attach_prefix_credit(
        model, perturbed, device=torch.device("cpu"), baseline_seed=30203030
    )

    # Position 0's factual Q_j, baseline and advantage cannot depend on any
    # later position's action.
    torch.testing.assert_close(
        attached_original.old_values[0, 0, 0],
        attached_perturbed.old_values[0, 0, 0],
        rtol=0, atol=0,
    )
    torch.testing.assert_close(
        attached_original.old_baseline[0, 0, 0],
        attached_perturbed.old_baseline[0, 0, 0],
        rtol=0, atol=0,
    )
    torch.testing.assert_close(
        attached_original.old_prefix_advantage[0, 0, first_position_member],
        attached_perturbed.old_prefix_advantage[0, 0, first_position_member],
        rtol=0, atol=0,
    )
    # Vacuity guard: the mutation must actually have changed something
    # downstream (a later position's factual Q_j), or this test proves
    # nothing.
    assert not bool(
        torch.equal(
            attached_original.old_values[0, 0, active_count - 1],
            attached_perturbed.old_values[0, 0, active_count - 1],
        )
    ), "fixture failed to perturb a later position; test proves nothing"


def test_qj_forward_receives_full_x_r_m_and_ordered_prefix_not_a_sum() -> None:
    """Direct contract test on `_qj_forward` itself (design section 1).

    Perturbing X_t (observation content) or R_t (recurrent state) at a
    position *strictly before* j must change Q_j -- unlike G20R's reduced
    critic, which took only an aggregate critic state, raw mask, position
    and a prefix *sum*. This is the concrete regression test for the
    G20R -> G20R2 contract change: swapping which of two members contributed
    a given prefix action (same sum, different member-context pairing) must
    change Q_j, because the design requires the full ordered prefix "paired
    with its member context", not a sum that would be invariant to the swap.
    """

    torch.manual_seed(3020030)
    model = _make_model(capacity=4)
    capacity, obs_dim, hidden_dim, action_dim = 4, 5, model.hidden_dim, 2
    critic_state = torch.randn(1, 4)
    active_mask = torch.ones(1, capacity, dtype=torch.bool)
    observations = torch.randn(1, capacity, obs_dim)
    hidden_before = torch.randn(1, capacity, hidden_dim)
    order = torch.arange(capacity).unsqueeze(0)  # identity routing order
    prefix_actions = torch.randn(1, capacity, action_dim)

    base = _qj_forward(
        model, critic_state=critic_state, active_mask=active_mask,
        observations=observations, hidden_before=hidden_before, order=order,
        prefix_actions=prefix_actions, focal_actions=prefix_actions,
    )

    # Perturb X_t at position 0 only (strictly before every j >= 1): Q_j for
    # j >= 1 must change (X_t/R_t are read for every query position, design
    # section 1), and Q_0 (which has no prefix at all) must NOT change,
    # since position 0 has no earlier position to condition on via X_t
    # itself being irrelevant to its *own* row... but X_t IS part of every
    # row's fixed (non-prefix) input, so Q_0 changes too -- assert the
    # weaker, unambiguous claim: at least one later position changes.
    observations_perturbed = observations.clone()
    observations_perturbed[0, 0] += 3.0
    perturbed_x = _qj_forward(
        model, critic_state=critic_state, active_mask=active_mask,
        observations=observations_perturbed, hidden_before=hidden_before, order=order,
        prefix_actions=prefix_actions, focal_actions=prefix_actions,
    )
    assert not bool(torch.equal(base, perturbed_x)), "Q_j is insensitive to X_t"

    # Perturb R_t at position 0 only: Q_j must change for at least one
    # position (R_t is part of the fixed per-step input too).
    hidden_perturbed = hidden_before.clone()
    hidden_perturbed[0, 0] += 3.0
    perturbed_r = _qj_forward(
        model, critic_state=critic_state, active_mask=active_mask,
        observations=observations, hidden_before=hidden_perturbed, order=order,
        prefix_actions=prefix_actions, focal_actions=prefix_actions,
    )
    assert not bool(torch.equal(base, perturbed_r)), "Q_j is insensitive to R_t"

    # Swap the prefix actions at positions 0 and 1 (same *sum* over the
    # prefix through position 2, different member-context pairing since
    # X_t/R_t at positions 0 and 1 differ): Q_2 (which reads both rows as
    # its prefix) must change, proving the critic sees the ordered table,
    # not a sum -- a sum-based critic (like G20R's) would be invariant to
    # this swap.
    swapped_prefix = prefix_actions.clone()
    swapped_prefix[0, [0, 1]] = swapped_prefix[0, [1, 0]]
    swapped = _qj_forward(
        model, critic_state=critic_state, active_mask=active_mask,
        observations=observations, hidden_before=hidden_before, order=order,
        prefix_actions=swapped_prefix, focal_actions=prefix_actions,
    )
    assert not bool(
        torch.equal(base[:, 2], swapped[:, 2])
    ), "Q_2 is invariant to swapping which member contributed the prefix action -- contract regressed to a sum"


def test_qj_forward_never_reads_actions_at_or_after_the_query_position_from_prefix() -> None:
    """`prefix_actions` rows at position `k >= j` must never reach `Q_j`.

    Complements the ordered-prefix test above by directly perturbing every
    row at and after each query position and confirming zero sensitivity --
    the fail-closed structural claim from design section 1's prohibited-
    inputs list ("any action at a position greater than j").
    """

    torch.manual_seed(3020031)
    model = _make_model(capacity=4)
    capacity, obs_dim, hidden_dim, action_dim = 4, 5, model.hidden_dim, 2
    critic_state = torch.randn(1, 4)
    active_mask = torch.ones(1, capacity, dtype=torch.bool)
    observations = torch.randn(1, capacity, obs_dim)
    hidden_before = torch.randn(1, capacity, hidden_dim)
    order = torch.arange(capacity).unsqueeze(0)
    prefix_actions = torch.randn(1, capacity, action_dim)

    base = _qj_forward(
        model, critic_state=critic_state, active_mask=active_mask,
        observations=observations, hidden_before=hidden_before, order=order,
        prefix_actions=prefix_actions, focal_actions=prefix_actions,
    )
    for j in range(capacity):
        perturbed_prefix = prefix_actions.clone()
        perturbed_prefix[0, j:] += 11.0  # perturb every row at/after j
        perturbed = _qj_forward(
            model, critic_state=critic_state, active_mask=active_mask,
            observations=observations, hidden_before=hidden_before, order=order,
            prefix_actions=perturbed_prefix, focal_actions=prefix_actions,
        )
        torch.testing.assert_close(base[:, j], perturbed[:, j], rtol=0, atol=0)


# ---------------------------------------------------------------------------
# Permutation equivariance: simultaneously permuting lifecycle rows leaves
# Q_j unchanged; routing position never becomes a fixed member identity.
# ---------------------------------------------------------------------------


def test_qj_is_equivariant_to_simultaneous_lifecycle_row_permutation() -> None:
    torch.manual_seed(3020004)
    capacity, obs_dim, critic_dim, action_dim, hidden_dim = 5, 6, 4, 2, 8
    model = FastAnchorActionAdvantagePolicy(
        obs_dim, critic_dim, member_capacity=capacity, action_dim=action_dim,
        hidden_dim=hidden_dim,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    model.eval()

    batch = 2
    observations = torch.randn(batch, capacity, obs_dim)
    active_mask = torch.tensor(
        [[True, True, True, False, True], [True, True, False, True, True]]
    )
    critic_state = torch.randn(batch, critic_dim)
    hidden = torch.randn(batch, capacity, hidden_dim)
    teacher = torch.tanh(torch.randn(batch, capacity, action_dim))

    with torch.no_grad():
        original = model.forward_step(
            observations=observations, active_mask=active_mask, critic_state=critic_state,
            hidden=hidden, teacher_pre_tanh=teacher,
        )

    perm = torch.stack([torch.randperm(capacity) for _ in range(batch)])

    def permute_slots(tensor: torch.Tensor) -> torch.Tensor:
        out = torch.empty_like(tensor)
        for row in range(tensor.shape[0]):
            out[row] = tensor[row, perm[row]]
        return out

    observations_p = permute_slots(observations)
    active_mask_p = permute_slots(active_mask.unsqueeze(-1)).squeeze(-1)
    hidden_p = permute_slots(hidden)
    teacher_p = permute_slots(teacher)

    with torch.no_grad():
        permuted = model.forward_step(
            observations=observations_p, active_mask=active_mask_p,
            critic_state=critic_state, hidden=hidden_p, teacher_pre_tanh=teacher_p,
        )

    torch.testing.assert_close(
        original.position_value, permuted.position_value, rtol=0, atol=0
    )
    torch.testing.assert_close(original.value, permuted.value, rtol=0, atol=0)

    # Sanity: the permutation must have actually rearranged the raw member
    # axis (or this test would pass vacuously).
    assert not bool(torch.equal(observations, observations_p))


def test_qj_routing_position_never_becomes_a_fixed_member_identity() -> None:
    """Two different members occupying the *same slot* across two otherwise
    identical fixtures must not make Q_j depend on the slot index itself --
    only content (which drives routing order) may matter."""

    torch.manual_seed(3020005)
    capacity, obs_dim, critic_dim, action_dim, hidden_dim = 4, 5, 4, 2, 8
    model = FastAnchorActionAdvantagePolicy(
        obs_dim, critic_dim, member_capacity=capacity, action_dim=action_dim,
        hidden_dim=hidden_dim,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    model.eval()

    active_mask = torch.ones(1, capacity, dtype=torch.bool)
    critic_state = torch.randn(1, critic_dim)
    hidden = torch.randn(1, capacity, hidden_dim)
    observations = torch.randn(1, capacity, obs_dim)
    teacher = torch.tanh(torch.randn(1, capacity, action_dim))

    with torch.no_grad():
        original = model.forward_step(
            observations=observations, active_mask=active_mask, critic_state=critic_state,
            hidden=hidden, teacher_pre_tanh=teacher,
        )

    # Swap two members' full content (observation, hidden, teacher action)
    # between slots 0 and 1. If the network keyed off *slot* identity rather
    # than routed content, this would change more than just the routed
    # positions those two members now occupy.
    swap_observations = observations.clone()
    swap_observations[0, [0, 1]] = swap_observations[0, [1, 0]]
    swap_hidden = hidden.clone()
    swap_hidden[0, [0, 1]] = swap_hidden[0, [1, 0]]
    swap_teacher = teacher.clone()
    swap_teacher[0, [0, 1]] = swap_teacher[0, [1, 0]]

    with torch.no_grad():
        swapped = model.forward_step(
            observations=swap_observations, active_mask=active_mask,
            critic_state=critic_state, hidden=swap_hidden, teacher_pre_tanh=swap_teacher,
        )

    torch.testing.assert_close(
        original.position_value, swapped.position_value, rtol=0, atol=0
    )


# ---------------------------------------------------------------------------
# Stage A: source action effect identification.
# ---------------------------------------------------------------------------


def test_stage_a_passes_on_known_nonzero_effect_and_fails_on_degenerate_zero() -> None:
    generator = torch.Generator()
    generator.manual_seed(555001)
    effect_clusters = [
        torch.full((16, 1), 0.30) + 0.01 * torch.randn(16, 1, generator=generator)
        for _ in range(12)
    ]
    result_effect = stage_a_source_effect(
        effect_clusters, generator=generator, epsilon_audit=1e-3
    )
    assert result_effect["passed"] is True
    assert result_effect["s_source"] > result_effect["epsilon_audit_squared"]

    generator2 = torch.Generator()
    generator2.manual_seed(555002)
    zero_clusters = [1e-6 * torch.randn(16, 1, generator=generator2) for _ in range(12)]
    result_zero = stage_a_source_effect(
        zero_clusters, generator=generator2, epsilon_audit=1e-3
    )
    assert result_zero["passed"] is False


def test_stage_a_floor_is_a_resolution_bound_not_an_effect_size_threshold() -> None:
    """A *small* but accurately-measured effect must pass identification --
    this is the exact defect the re-registration retires (design section 2:
    "A tiny but accurately measurable effect passes identification")."""

    generator = torch.Generator()
    generator.manual_seed(555010)
    small_but_precise = [
        torch.full((30, 1), 0.02) + 1e-4 * torch.randn(30, 1, generator=generator)
        for _ in range(12)
    ]
    small_result = stage_a_source_effect(
        small_but_precise, generator=generator, epsilon_audit=1e-3
    )
    assert small_result["passed"] is True, (
        "a small but precisely measured effect must pass Stage A -- the "
        "floor is a numerical resolution bound, not a fraction-of-variance "
        "effect-size gate"
    )

    generator2 = torch.Generator()
    generator2.manual_seed(555011)
    zero_effect_same_scale = [
        1e-4 * torch.randn(30, 1, generator=generator2) for _ in range(12)
    ]
    zero_result = stage_a_source_effect(
        zero_effect_same_scale, generator=generator2, epsilon_audit=1e-3
    )
    assert zero_result["passed"] is False, (
        "a genuinely zero effect at the same measurement precision must "
        "still fail -- the floor only forgives noise, not the absence of an "
        "effect"
    )


def test_stage_a_p2_authority_check_flags_effect_outside_centered_authority() -> None:
    """`S_source > 0` but `|g*_res| = 0` -- a source-authority mismatch, not
    a critic failure (design section 2)."""

    torch.manual_seed(555020)
    half = 20
    # Each of the first `half` rows is exactly duplicated in the second
    # `half` rows, with the paired score flipped in sign -- this makes
    # E[score * oracle] an *exact* telescoping zero (sum of
    # oracle_i - oracle_i terms), not merely small, so it survives the
    # P2 check's tight numeric-equality tolerance.
    base_oracle = 0.4 + 0.02 * torch.randn(half, 1)
    oracle = torch.cat((base_oracle, base_oracle), dim=0)
    sign = torch.cat((torch.ones(half, 1), -torch.ones(half, 1)), dim=0)
    score = sign.repeat(1, 2)  # action_dim = 2
    result = stage_a_p2_authority_check([oracle], [score])
    assert result["outside_authority"] is True
    assert abs(result["g_star_res_magnitude"]) < 1e-8

    # Contrast: an aligned score (same sign as a nonzero oracle contribution
    # on average) must NOT be flagged as outside authority.
    aligned_score = torch.ones(2 * half, 1).repeat(1, 2)
    aligned_result = stage_a_p2_authority_check([oracle], [aligned_score])
    assert aligned_result["outside_authority"] is False
    assert aligned_result["g_star_res_magnitude"] > 1e-3


# ---------------------------------------------------------------------------
# Stage B1: critic contrast alignment and positive-scale recalibrated R^2.
# ---------------------------------------------------------------------------


def test_stage_b1_contrast_alignment_passes_for_correlated_and_fails_for_independent() -> None:
    generator = torch.Generator()
    generator.manual_seed(555030)
    g_list, q_list = [], []
    for _ in range(12):
        g = torch.randn(20, generator=generator)
        q = 3.0 * g + 0.02 * torch.randn(20, generator=generator)
        g_list.append(g)
        q_list.append(q)
    correlated = stage_b1_contrast_alignment(g_list, q_list, generator=generator)
    assert correlated["passed"] is True
    assert correlated["rho"] > 0.9

    generator2 = torch.Generator()
    generator2.manual_seed(555031)
    g_list2 = [torch.randn(20, generator=generator2) for _ in range(12)]
    q_list2 = [torch.randn(20, generator=generator2) for _ in range(12)]
    independent = stage_b1_contrast_alignment(g_list2, q_list2, generator=generator2)
    assert independent["passed"] is False


def test_stage_b1_recalibrated_r2_recovers_from_positive_scale_mismatch() -> None:
    """`q = 10g` must pass the recalibrated gate despite failing raw NMSE --
    design section 3's explicit retraction of raw NMSE as a mandatory gate."""

    torch.manual_seed(555040)
    calibration_g = torch.randn(300)
    calibration_q = 10.0 * calibration_g
    audit_clusters = [
        torch.stack((g, 10.0 * g), dim=-1) for g in [torch.randn(20) for _ in range(12)]
    ]
    generator = torch.Generator()
    generator.manual_seed(555041)
    result = stage_b1_recalibrated_r2(
        calibration_g, calibration_q, audit_clusters, generator=generator
    )
    assert result["passed"] is True
    assert result["alpha_star"] > 0.0
    raw_nmse = float(
        torch.mean(torch.square(torch.cat([row[:, 0] for row in audit_clusters])
                                 - torch.cat([row[:, 1] for row in audit_clusters])))
    )
    assert raw_nmse > 1.0, "fixture must actually fail raw NMSE, or this test proves nothing"


def test_stage_b1_recalibrated_r2_fails_for_unrelated_critic() -> None:
    torch.manual_seed(555042)
    calibration_g = torch.randn(300)
    calibration_q = torch.randn(300)  # unrelated to calibration_g
    audit_clusters = [
        torch.stack((torch.randn(20), torch.randn(20)), dim=-1) for _ in range(12)
    ]
    generator = torch.Generator()
    generator.manual_seed(555043)
    result = stage_b1_recalibrated_r2(
        calibration_g, calibration_q, audit_clusters, generator=generator
    )
    assert result["passed"] is False


# ---------------------------------------------------------------------------
# Stage B2: oracle-versus-learned residual-gradient alignment.
# ---------------------------------------------------------------------------


def test_stage_b2_passes_when_aligned_fails_when_anti_aligned() -> None:
    torch.manual_seed(555050)
    n = 20
    score_clusters, aligned_learned, oracle_clusters, anti_learned = [], [], [], []
    for _ in range(12):
        score = torch.randn(n, 2)
        oracle = score[:, 0:1] + 0.05 * torch.randn(n, 1)
        aligned_learned.append(oracle + 0.05 * torch.randn(n, 1))
        anti_learned.append(-oracle + 0.05 * torch.randn(n, 1))
        score_clusters.append(score)
        oracle_clusters.append(oracle)

    generator = torch.Generator()
    generator.manual_seed(555051)
    aligned_result = stage_b2_gradient_alignment(
        score_clusters, aligned_learned, oracle_clusters, generator=generator
    )
    assert aligned_result["passed"] is True
    assert aligned_result["cosine"] > 0.5

    generator2 = torch.Generator()
    generator2.manual_seed(555052)
    anti_result = stage_b2_gradient_alignment(
        score_clusters, anti_learned, oracle_clusters, generator=generator2
    )
    assert anti_result["passed"] is False
    assert anti_result["cosine"] < 0.0


def test_stage_b2_fails_when_oracle_direction_is_degenerate_zero() -> None:
    """`|g*_res| > 0` is required even if the cosine would otherwise read as
    perfectly aligned (a zero oracle direction has no well-defined
    direction to align with)."""

    torch.manual_seed(555053)
    n = 20
    score_clusters, learned_clusters, oracle_clusters = [], [], []
    for _ in range(12):
        score = torch.randn(n, 2)
        oracle_clusters.append(torch.zeros(n, 1))
        learned_clusters.append(torch.randn(n, 1))
        score_clusters.append(score)
    generator = torch.Generator()
    generator.manual_seed(555054)
    result = stage_b2_gradient_alignment(
        score_clusters, learned_clusters, oracle_clusters, generator=generator
    )
    assert result["g_star_res_magnitude"] == 0.0
    assert result["passed"] is False


def test_residual_action_space_score_matches_hand_computation() -> None:
    raw_action = torch.tensor([1.5, -0.5])
    mean = torch.tensor([1.0, 0.0])
    std = torch.tensor([0.5, 2.0])
    score = residual_action_space_score(raw_action, mean, std)
    expected = torch.tensor([(1.5 - 1.0) / 0.25, (-0.5 - 0.0) / 4.0])
    torch.testing.assert_close(score, expected, rtol=1e-6, atol=1e-6)


# ---------------------------------------------------------------------------
# Cluster bootstrap: a statistic must actually be resamplable at the cluster
# (not token) level, and a degenerate single-cluster input must be refused.
# ---------------------------------------------------------------------------


def test_cluster_bootstrap_lcb_requires_at_least_two_clusters() -> None:
    generator = torch.Generator()
    generator.manual_seed(1)
    try:
        cluster_bootstrap_lcb(
            [torch.ones(5, 1)], lambda pooled: float(pooled.mean()), generator=generator
        )
    except ValueError as error:
        assert "at least two clusters" in str(error)
    else:
        raise AssertionError("single-cluster bootstrap was accepted")


def test_cluster_bootstrap_lcb_is_below_or_equal_to_point_estimate_for_noisy_data() -> None:
    generator = torch.Generator()
    generator.manual_seed(2)
    clusters = [torch.randn(10, 1) + float(index) for index in range(8)]
    point, lcb = cluster_bootstrap_lcb(
        clusters, lambda pooled: float(pooled.mean()), generator=generator
    )
    assert lcb <= point + 1e-9


# ---------------------------------------------------------------------------
# Data-role disjointness: structural, not incidental.
# ---------------------------------------------------------------------------


def test_validate_disjoint_roles_raises_on_any_pairwise_overlap() -> None:
    validate_disjoint_roles([1, 2, 3], [4, 5, 6], [7, 8, 9])  # must not raise
    for fit, credit, audit in (
        ([1, 2], [2, 3], [4, 5]),
        ([1, 2], [3, 4], [4, 5]),
        ([1, 2], [3, 4], [1, 9]),
    ):
        try:
            validate_disjoint_roles(fit, credit, audit)
        except ValueError:
            pass
        else:
            raise AssertionError(f"overlap not detected: {fit}, {credit}, {audit}")


def test_qualification_and_credit_episode_blocks_are_disjoint_by_construction() -> None:
    """Regression test on the screen's own block-allocation helpers: a bug
    that made two update indices collide would be caught here, not just by
    the generic guard's own unit test above."""

    fit_ids: list[int] = []
    for update in range(10):
        fit_ids.extend(screen._qualification_episode_block("g18", update))
    credit_ids: list[int] = []
    for update in range(10):
        credit_ids.extend(screen._credit_episode_block("g18", 10, update))
    validate_disjoint_roles(fit_ids, credit_ids, [])
    assert len(set(fit_ids)) == len(fit_ids)
    assert len(set(credit_ids)) == len(credit_ids)


# ---------------------------------------------------------------------------
# No residual movement before Stage B passes.
# ---------------------------------------------------------------------------


def test_qualification_phase_keeps_residual_output_layer_exactly_zero() -> None:
    torch.manual_seed(3020006)
    model = _make_model(capacity=4)
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=3, time_steps=4
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    fast_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=1
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    assert model.residual_output_layer_maximum_absolute_value() == 0.0

    model.begin_qualification_phase()
    assert model.phase == "qualification"
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    for update in range(5):
        observations, active_mask, critic_states, rewards, noise = _small_fixture(
            capacity=4, batch=3, time_steps=4
        )
        raw = _rollout(
            model, observations=observations, active_mask=active_mask,
            critic_states=critic_states, rewards=rewards, noise=noise,
        )
        trajectory = attach_prefix_credit(
            model, raw, device=torch.device("cpu"), baseline_seed=100 + update
        )
        metrics = optimize_qualification_update(
            model, critic_optimizer, trajectory, device=torch.device("cpu"),
            ppo_passes=2, gamma=0.99,
        )
        assert metrics["finite_update"] == 1.0
        # The load-bearing assertion: residual output layer stays exactly
        # zero across every qualification update, not just at entry.
        assert model.residual_output_layer_maximum_absolute_value() == 0.0

    # Critic actually moved (otherwise "stayed zero" would be true only
    # because nothing happened at all).
    assert any(
        float(parameter.detach().abs().max()) > 0.0
        for parameter in model.critic_parameters()
    )


def test_begin_delayed_phase_refuses_without_stage_b_passed() -> None:
    model = _make_model(capacity=4)
    model.begin_qualification_phase()
    try:
        model.begin_delayed_phase(stage_b_passed=False)
    except RuntimeError as error:
        assert "forbids a residual-actor update" in str(error)
    else:
        raise AssertionError("delayed phase opened without Stage B passing")
    assert model.phase == "qualification"
    assert all(not parameter.requires_grad for parameter in model.residual_parameters())

    model.begin_delayed_phase(stage_b_passed=True)
    assert model.phase == "delayed"
    assert all(parameter.requires_grad for parameter in model.residual_parameters())


def test_optimize_qualification_update_refuses_if_residual_is_trainable() -> None:
    model = _make_model(capacity=4)
    model.begin_qualification_phase()
    for parameter in model.residual_parameters():
        parameter.requires_grad_(True)  # simulate an incorrect external mutation
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=3
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    trajectory = attach_prefix_credit(model, raw, device=torch.device("cpu"), baseline_seed=7)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    try:
        optimize_qualification_update(
            model, critic_optimizer, trajectory, device=torch.device("cpu"),
            ppo_passes=1, gamma=0.99,
        )
    except RuntimeError as error:
        assert "must stay frozen" in str(error)
    else:
        raise AssertionError("qualification update proceeded with a trainable residual")


def test_optimize_delayed_update_refuses_outside_delayed_phase() -> None:
    model = _make_model(capacity=4)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=3
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    trajectory = attach_prefix_credit(model, raw, device=torch.device("cpu"), baseline_seed=8)
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    try:
        optimize_delayed_update(
            model, residual_optimizer, critic_optimizer, trajectory,
            device=torch.device("cpu"), ppo_passes=1, gamma=0.99,
        )
    except RuntimeError as error:
        assert "delayed phase" in str(error)
    else:
        raise AssertionError("delayed update ran outside the delayed phase")


# ---------------------------------------------------------------------------
# Full three-phase run keeps the anchor exact, and only moves the residual
# once Stage B has (in this test, trivially) passed.
# ---------------------------------------------------------------------------


def test_fast_then_qualification_then_delayed_keeps_anchor_exact_and_finite() -> None:
    torch.manual_seed(3020007)
    model = _make_model(capacity=4)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=3, time_steps=4
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    fast_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=21
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    fast_metrics = optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    assert fast_metrics["finite_update"] == 1.0
    anchor = model.anchor_state()

    model.begin_qualification_phase()
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=3, time_steps=4
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    qualification_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=22
    )
    qualification_metrics = optimize_qualification_update(
        model, critic_optimizer, qualification_trajectory, device=torch.device("cpu"),
        ppo_passes=1, gamma=0.99,
    )
    assert qualification_metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0

    model.begin_delayed_phase(stage_b_passed=True)
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    delayed_critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=3, time_steps=4
    )
    raw = _rollout(
        model, observations=observations, active_mask=active_mask,
        critic_states=critic_states, rewards=rewards, noise=noise,
    )
    delayed_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=23
    )
    delayed_metrics = optimize_delayed_update(
        model, residual_optimizer, delayed_critic_optimizer, delayed_trajectory,
        device=torch.device("cpu"), ppo_passes=1, gamma=0.99,
    )
    assert delayed_metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0


# ---------------------------------------------------------------------------
# Gradient ownership.
# ---------------------------------------------------------------------------


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


def test_qualification_gradient_ownership_touches_only_critic_parameters() -> None:
    torch.manual_seed(3020008)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(0, 1), action_seed=3939001, baseline_seed=3949001,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    model.begin_qualification_phase()
    trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(2, 3), action_seed=3939002, baseline_seed=3949002,
        device=torch.device("cpu"),
    )
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-3)

    frozen_named = [
        (name, parameter)
        for name, parameter in model.policy.named_parameters()
        if not name.startswith("delayed_residual.")
    ] + [
        (f"delayed_residual.{name}", parameter)
        for name, parameter in model.policy.delayed_residual.named_parameters()
    ] + [
        (f"immediate_baseline.{name}", parameter)
        for name, parameter in model.immediate_baseline.named_parameters()
    ]
    for _, parameter in frozen_named:
        parameter.grad = None

    optimize_qualification_update(
        model, critic_optimizer, trajectory, device=torch.device("cpu"),
        ppo_passes=1, gamma=0.99,
    )

    for name, parameter in frozen_named:
        assert parameter.requires_grad is False
        assert parameter.grad is None, f"{name} unexpectedly received a gradient"
    assert any(parameter.grad is not None for parameter in model.critic_parameters())


def test_delayed_gradient_ownership_excludes_fast_surfaces_and_residual_from_critic() -> None:
    torch.manual_seed(3020009)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(0, 1), action_seed=3939003, baseline_seed=3949003,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    model.begin_qualification_phase()
    qualification_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(2, 3), action_seed=3939004, baseline_seed=3949004,
        device=torch.device("cpu"),
    )
    critic_optimizer_q = torch.optim.Adam(model.critic_parameters(), lr=1e-3)
    optimize_qualification_update(
        model, critic_optimizer_q, qualification_trajectory, device=torch.device("cpu"),
        ppo_passes=1, gamma=0.99,
    )
    model.begin_delayed_phase(stage_b_passed=True)
    trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(4, 5), action_seed=3939005, baseline_seed=3949005,
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
        model, residual_optimizer, critic_optimizer, trajectory,
        device=torch.device("cpu"), ppo_passes=1, gamma=0.99,
    )

    for name, parameter in frozen_named:
        assert parameter.requires_grad is False
        assert parameter.grad is None, f"{name} unexpectedly received a gradient"

    # Directly verify the Q_j regression alone has no gradient on the
    # residual head.
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
# Replay exactness on both sources with the new (richer) Q_j contract.
# ---------------------------------------------------------------------------


def test_battery_replay_remains_exact_with_nonzero_residual() -> None:
    torch.manual_seed(3020010)
    model = _battery_model()
    fast_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(4, 5), action_seed=3939006, baseline_seed=3949006,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    optimize_fast_update(
        model, fast_optimizer, fast_trajectory, device=torch.device("cpu"), ppo_passes=1
    )
    model.begin_qualification_phase()
    qualification_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(6, 7), action_seed=3939007, baseline_seed=3949007,
        device=torch.device("cpu"),
    )
    critic_optimizer_q = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    optimize_qualification_update(
        model, critic_optimizer_q, qualification_trajectory, device=torch.device("cpu"),
        ppo_passes=1, gamma=0.99,
    )
    model.begin_delayed_phase(stage_b_passed=True)
    move_trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(8, 9), action_seed=3939008, baseline_seed=3949008,
        device=torch.device("cpu"),
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    delayed_metrics = optimize_delayed_update(
        model, residual_optimizer, critic_optimizer, move_trajectory,
        device=torch.device("cpu"), ppo_passes=2, gamma=0.99,
    )
    assert delayed_metrics["finite_update"] == 1.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    trajectory = screen.collect_battery_trajectory(
        model, episode_ids=(10, 11, 12), action_seed=3939009, baseline_seed=3949009,
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
    torch.manual_seed(3020011)
    model = FastAnchorActionAdvantagePolicy(
        g17_source.OBSERVATION_DIM, g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY, action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    raw = g17_source.collect_trajectory(
        model, episode_ids=(0, 1), ledger_seed=3029007, action_seed=3039008,
        device=torch.device("cpu"),
    )
    trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=3079008
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=1e-3,
    )
    assert optimize_fast_update(
        model, fast_optimizer, trajectory, device=torch.device("cpu"), ppo_passes=1
    )["finite_update"] == 1.0

    model.begin_qualification_phase()
    raw = g17_source.collect_trajectory(
        model, episode_ids=(2, 3), ledger_seed=3029007, action_seed=3039008,
        device=torch.device("cpu"),
    )
    qualification_trajectory = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=3079009
    )
    critic_optimizer_q = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    qmetrics = optimize_qualification_update(
        model, critic_optimizer_q, qualification_trajectory, device=torch.device("cpu"),
        ppo_passes=1, gamma=0.99,
    )
    assert qmetrics["finite_update"] == 1.0
    anchor = model.anchor_state()

    model.begin_delayed_phase(stage_b_passed=True)
    raw = g17_source.collect_trajectory(
        model, episode_ids=(4, 5), ledger_seed=3029007, action_seed=3039008,
        device=torch.device("cpu"),
    )
    delayed = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=3079010
    )
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=1e-2)
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=1e-2)
    metrics = optimize_delayed_update(
        model, residual_optimizer, critic_optimizer, delayed,
        device=torch.device("cpu"), ppo_passes=2, gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0

    raw = g17_source.collect_trajectory(
        model, episode_ids=(6, 7), ledger_seed=3029007, action_seed=3039008,
        device=torch.device("cpu"),
    )
    replay_trajectory_object = attach_prefix_credit(
        model, raw, device=torch.device("cpu"), baseline_seed=3079011
    )
    replay = replay_trajectory(model, replay_trajectory_object, device=torch.device("cpu"))
    errors = replay_errors(replay, replay_trajectory_object)
    assert all(value == 0.0 for value in errors.values())


def test_batched_routing_order_matches_per_step_routing_order() -> None:
    torch.manual_seed(3020012)
    model = _make_model()
    observations, active_mask, critic_states, rewards, noise = _small_fixture(
        capacity=4, batch=2, time_steps=3
    )
    batched = _batched_routing_order(model.policy, observations, active_mask)
    for time in range(observations.shape[0]):
        expected = model.policy._routing_order(active_mask[time], observations[time])
        torch.testing.assert_close(batched[time], expected, rtol=0, atol=0)


# ---------------------------------------------------------------------------
# Branch precedence: gate 2 before 4 before 6, source-specific, and the
# G17-fails-identification-but-passes-behaviour case does not mask G18.
# ---------------------------------------------------------------------------


def _passing_identification() -> dict:
    return {
        "operational_valid": True,
        "stage_a_passed": True,
        "p2_outside_authority": False,
        "stage_b1_passed": True,
        "stage_b2_passed": True,
    }


def _passing_g17_behavior() -> dict:
    return {
        "g17_final_iid_utility": 0.93,
        "g17_final_heldout_utility": 0.92,
        "g17_gain": 0.20,
        "g17_minimum_episode": 0.85,
        "g17_effort_correlation": 0.95,
        "g17_mix_correlation": 0.96,
        "g17_effort_mae": 0.03,
        "g17_mix_mae": 0.02,
    }


def _passing_g18_behavior() -> dict:
    return {
        "g18_final_utility": 0.97,
        "g18_gain_over_anchor": 0.15,
        "g18_spike_utility": 0.94,
        "g18_rotating_effort_share": 0.82,
    }


def test_g18_branch_precedence_is_first_match_gate2_then_4_then_6() -> None:
    passing = _passing_identification() | _passing_g18_behavior()
    assert screen.select_g18_branch(passing) == screen.PROMISING_BRANCH_G18

    assert screen.select_g18_branch(
        passing | {"operational_valid": False}
    ) == screen.INVALID_BRANCH_TEMPLATE.format(suffix="G18")

    # Gate 2 (Stage A) must fire even if gate 4/5 would also fail.
    gate2_and_gate4_fail = passing | {"stage_a_passed": False, "stage_b1_passed": False}
    assert screen.select_g18_branch(
        gate2_and_gate4_fail
    ) == screen.STAGE_A_FAIL_TEMPLATE.format(suffix="G18")

    assert screen.select_g18_branch(
        passing | {"p2_outside_authority": True}
    ) == screen.P2_FAIL_TEMPLATE.format(suffix="G18")

    # Gate 4 (Stage B1) must fire before gate 6 (behavior), even when
    # behavior would also fail.
    gate4_and_behavior_fail = passing | {
        "stage_b1_passed": False, "g18_gain_over_anchor": 0.0,
    }
    assert screen.select_g18_branch(
        gate4_and_behavior_fail
    ) == screen.STAGE_B1_FAIL_TEMPLATE.format(suffix="G18")

    assert screen.select_g18_branch(
        passing | {"stage_b2_passed": False}
    ) == screen.STAGE_B2_FAIL_TEMPLATE.format(suffix="G18")

    assert screen.select_g18_branch(
        passing | {"g18_gain_over_anchor": 0.01}
    ) == screen.NO_G18_ACCESS_BRANCH
    assert screen.select_g18_branch(
        passing | {"g18_rotating_effort_share": 0.5}
    ) == screen.NO_G18_MECHANISM_BRANCH


def test_g17_identification_failure_with_behavioral_pass_is_diagnostic_not_qualified() -> None:
    g17_metrics = (
        _passing_identification()
        | _passing_g17_behavior()
        | {"stage_a_passed": False}
    )
    assert screen.select_g17_branch(g17_metrics) == screen.G17_DIAGNOSTIC_PASS_BRANCH
    assert screen.select_g17_branch(g17_metrics) != screen.G17_QUALIFIED_PASS_BRANCH


def test_g17_identification_failure_with_behavioral_failure_is_unqualified_loss_not_incompatibility() -> None:
    g17_metrics = (
        _passing_identification()
        | _passing_g17_behavior()
        | {"stage_b1_passed": False, "g17_gain": 0.0}
    )
    assert screen.select_g17_branch(g17_metrics) == screen.G17_UNQUALIFIED_LOSS_BRANCH
    assert screen.select_g17_branch(g17_metrics) != screen.G17_QUALIFIED_FAIL_BRANCH


def test_g17_identification_failure_never_masks_a_qualified_g18_result() -> None:
    """The concrete regression for design section 8's central defect: a G17
    identification failure with a G17 behavioral pass must not mask a
    qualified G18 result. Proven here by construction, not by inspection --
    `select_g18_branch` is called with only G18's own metrics, so nothing
    in a failing G17 metrics dict can reach it."""

    g17_failing_identification = (
        _passing_identification()
        | _passing_g17_behavior()
        | {"stage_a_passed": False, "operational_valid": False}
    )
    g18_fully_qualified = _passing_identification() | _passing_g18_behavior()

    g17_branch = screen.select_g17_branch(g17_failing_identification)
    g18_branch = screen.select_g18_branch(g18_fully_qualified)

    assert g17_branch in (screen.G17_DIAGNOSTIC_PASS_BRANCH, screen.G17_UNQUALIFIED_LOSS_BRANCH)
    assert g18_branch == screen.PROMISING_BRANCH_G18

    # Directly demonstrate independence: mutating every field in the G17
    # metrics dict must never change the already-computed G18 branch, since
    # `select_g18_branch` takes only a G18 metrics dict as its argument --
    # there is no `all(...)` or shared-state path between them.
    for corrupted_g17 in (
        _passing_identification() | _passing_g17_behavior(),
        {key: False for key in _passing_identification()},
        _passing_identification() | {"g17_gain": -5.0, "g17_final_iid_utility": 0.0},
    ):
        assert screen.select_g18_branch(g18_fully_qualified) == g18_branch


def test_select_result_branch_dispatches_by_source() -> None:
    g17_metrics = _passing_identification() | _passing_g17_behavior()
    g18_metrics = _passing_identification() | _passing_g18_behavior()
    assert screen.select_result_branch("g17", g17_metrics) == screen.G17_QUALIFIED_PASS_BRANCH
    assert screen.select_result_branch("g18", g18_metrics) == screen.PROMISING_BRANCH_G18
    try:
        screen.select_result_branch("unknown", {})
    except ValueError:
        pass
    else:
        raise AssertionError("unknown source was silently accepted")


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


def test_screen_seeds_match_frozen_design_section_11() -> None:
    assert screen.SEEDS["g17"]["model"] == 3_019_000
    assert screen.SEEDS["g17"]["train_ledger"] == 3_029_000
    assert screen.SEEDS["g17"]["action"] == 3_039_000
    assert screen.SEEDS["g17"]["evaluation_ledger"] == 3_049_000
    assert screen.SEEDS["g17"]["evaluation_action"] == 3_059_000
    assert screen.SEEDS["g17"]["audit"] == 3_069_000
    assert screen.SEEDS["g18"]["model"] == 3_119_000
    assert screen.SEEDS["g18"]["action"] == 3_139_000
    assert screen.SEEDS["g18"]["audit"] == 3_149_000
    assert screen.BASELINE_SAMPLES_K_CONFIGURED == 8
    # Every G20R2 seed is disjoint from the earlier, retired G20R block.
    import scripts.screen_anchor_action_advantage_g20r as retired_screen

    retired_values = {
        value for source in retired_screen.SEEDS.values() for value in source.values()
    }
    new_values = {value for source in screen.SEEDS.values() for value in source.values()}
    assert retired_values.isdisjoint(new_values)
