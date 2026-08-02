"""V-K0C `token_mass` pure API and `advance_working_state` helper.

`docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md`, VC-D1 as
amended by A-VC-1 (unconditional token-mass semantics) and A-VC-2 (shared
factorization, not only shared roster advance). `token_mass` is the sole
probability authority in the chain `token_mass -> act_sequence sampling ->
V-K0C enumeration`: these tests calibrate that the mass split is correct at
both branches, that the API is genuinely pure, that `act_sequence`'s
sampling path literally consumes the same masses rather than a second,
independently re-derived softmax/sigmoid, and that the extracted
`advance_working_state` helper reproduces the mutation it replaced.
"""

import torch
import torch.nn.functional as F
from torch.distributions import Categorical

from ha_ctse_process.r30_fixed_clock import (
    INVALID_SKILL,
    KEEP_TOKEN,
    SET_TOKEN,
    FixedClockAREditPolicy,
    advance_working_state,
)

N_AGENTS = 3
N_SKILLS = 4


def _policy(seed=17, **kwargs):
    torch.manual_seed(seed)
    defaults = dict(
        obs_dim=4,
        n_agents=N_AGENTS,
        n_skills=N_SKILLS,
        hidden_dim=16,
        compact_dim=3,
        team_code_dim=3,
    )
    defaults.update(kwargs)
    policy = FixedClockAREditPolicy(**defaults)
    if policy.keep_head is not None:
        # Zero-initialized keep_head (r30_fixed_clock.py:84) makes every
        # position's keep_logit an identical input-independent constant --
        # perturb it so mass computations are not degenerate.
        torch.nn.init.normal_(policy.keep_head.weight, std=1.0)
    return policy


def _context(active=True, skills=(0, 1, 2)):
    torch.manual_seed(101)
    return dict(
        joint_obs=torch.randn(N_AGENTS, 4),
        compact=torch.randn(1, 3),
        team_vector=torch.randn(1, 3),
        prev_skills=torch.tensor(skills, dtype=torch.long),
        prev_ages=torch.tensor([7, 7, 7], dtype=torch.long),
        prev_active=torch.full((N_AGENTS,), bool(active), dtype=torch.bool),
        agent_order=torch.arange(N_AGENTS, dtype=torch.long),
    )


def _token_mass(policy, ctx, agent_id=0):
    return policy.token_mass(
        ctx["joint_obs"],
        ctx["compact"],
        ctx["team_vector"],
        ctx["prev_skills"],
        ctx["prev_ages"],
        ctx["prev_active"],
        agent_id,
        None,
        None,
    )


def test_active_branch_masses_sum_to_one_and_incumbent_set_mass_is_zero():
    policy = _policy()
    ctx = _context(active=True, skills=(2, 1, 0))
    mass = _token_mass(policy, ctx, agent_id=0)

    total = (mass["keep_mass"] + mass["set_mass"].sum()).item()
    eps = torch.finfo(mass["keep_mass"].dtype).eps
    assert abs(total - 1.0) <= eps, f"{total} not within one ulp of 1.0"

    incumbent_skill = int(ctx["prev_skills"][0].item())
    assert mass["set_mass"][0, incumbent_skill].item() == 0.0


def test_no_incumbent_branch_keep_mass_zero_and_set_mass_is_unmasked_softmax():
    policy = _policy()
    ctx = _context(active=False)
    mass = _token_mass(policy, ctx, agent_id=0)

    assert mass["keep_mass"].item() == 0.0

    total = mass["set_mass"].sum().item()
    eps = torch.finfo(mass["set_mass"].dtype).eps
    assert abs(total - 1.0) <= eps, f"{total} not within one ulp of 1.0"

    # Unmasked: a masked distribution would pin one entry to exactly zero
    # (the same underflow VC-D1 relies on for the incumbent). With no
    # incumbent, and generic (non-degenerate) logits, no entry should land
    # on exactly zero -- this is the property a wrongly-still-masked
    # implementation would violate.
    assert not bool((mass["set_mass"] == 0.0).any())
    torch.testing.assert_close(
        mass["set_mass"],
        F.softmax(mass["raw_skill_logits"], dim=-1),
        rtol=0,
        atol=0,
    )


def test_token_mass_is_pure_repeat_calls_match_and_do_not_advance_rng():
    policy = _policy()
    ctx = _context(active=True)

    rng_before = torch.get_rng_state()
    first = _token_mass(policy, ctx, agent_id=0)
    rng_after_first = torch.get_rng_state()
    second = _token_mass(policy, ctx, agent_id=0)
    rng_after_second = torch.get_rng_state()

    for key in first:
        assert torch.equal(first[key], second[key]), key
    assert torch.equal(rng_before, rng_after_first)
    assert torch.equal(rng_after_first, rng_after_second)


def test_sampling_path_consumes_token_mass_bit_exactly():
    """`act_sequence`'s learned-KEEP branch must use the SAME keep_mass and
    conditional skill distribution `token_mass` reports for the first
    agent's initial (unmodified) working state -- not a second,
    independently re-derived sigmoid/softmax.

    The learned-KEEP branch draws `torch.rand_like(keep_logit)` as its very
    first random op (before `skill_dist.sample()`), and `_token_context` is
    a pure function of its inputs, so re-seeding and replaying that same
    draw sequence against `token_mass`'s own returned tensors reproduces
    exactly what `act_sequence` must have compared against -- if
    `act_sequence` used a different mass (stale logits, a reintroduced
    independent sigmoid, wrong agent), the realized branch would disagree
    with this reconstruction with high probability.
    """
    policy = _policy()
    ctx = _context(active=True)
    first_agent = int(ctx["agent_order"][0].item())
    mass = _token_mass(policy, ctx, agent_id=first_agent)

    seed = 4242
    torch.manual_seed(seed)
    sample = policy.act_sequence(
        ctx["joint_obs"],
        ctx["compact"],
        ctx["team_vector"],
        ctx["prev_skills"],
        ctx["prev_ages"],
        ctx["prev_active"],
        ctx["agent_order"],
        deterministic=False,
    )

    torch.manual_seed(seed)
    expected_uniform = torch.rand_like(mass["raw_keep_logit"])
    expected_choose_keep = bool((expected_uniform < mass["keep_mass"]).item())
    expected_skill = Categorical(logits=mass["raw_skill_logits"]).sample()

    if expected_choose_keep:
        assert int(sample.token_kind[0].item()) == KEEP_TOKEN
        assert int(sample.set_skill[0].item()) == INVALID_SKILL
    else:
        assert int(sample.token_kind[0].item()) == SET_TOKEN
        assert int(sample.set_skill[0].item()) == int(expected_skill.item())


def test_advance_working_state_keep_is_a_no_op():
    working_skills = torch.tensor([2, 1, 0])
    working_ages = torch.tensor([9, 4, 1])
    working_active = torch.tensor([True, True, False])

    advance_working_state(
        working_skills, working_ages, working_active, 0, KEEP_TOKEN, 99
    )

    assert torch.equal(working_skills, torch.tensor([2, 1, 0]))
    assert torch.equal(working_ages, torch.tensor([9, 4, 1]))
    assert torch.equal(working_active, torch.tensor([True, True, False]))


def test_advance_working_state_set_writes_skill_resets_age_marks_active():
    working_skills = torch.tensor([2, 1, 0])
    working_ages = torch.tensor([9, 4, 1])
    working_active = torch.tensor([True, True, False])

    advance_working_state(
        working_skills, working_ages, working_active, 2, SET_TOKEN, 3
    )

    assert torch.equal(working_skills, torch.tensor([2, 1, 3]))
    assert torch.equal(working_ages, torch.tensor([9, 4, 0]))
    assert torch.equal(working_active, torch.tensor([True, True, True]))


def test_token_mass_fails_closed_on_native_categorical_edit():
    policy = _policy(native_categorical_edit=True)
    ctx = _context(active=True)
    try:
        _token_mass(policy, ctx, agent_id=0)
    except RuntimeError as exc:
        assert "VK0C_UNSUPPORTED_POLICY_MODE" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_token_mass_fails_closed_on_forced_full_refresh():
    policy = _policy(force_refresh_every_check=True)
    ctx = _context(active=True)
    try:
        _token_mass(policy, ctx, agent_id=0)
    except RuntimeError as exc:
        assert "VK0C_UNSUPPORTED_POLICY_MODE" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_token_mass_fails_closed_regardless_of_active_status():
    """A-VC-1's fail-closed rule is a policy-instance-level gate, not
    conditioned on the queried agent's active status -- force_refresh with
    no incumbent still fails closed rather than silently taking the
    no-incumbent branch semantics."""
    policy = _policy(force_refresh_every_check=True)
    ctx = _context(active=False)
    try:
        _token_mass(policy, ctx, agent_id=0)
    except RuntimeError as exc:
        assert "VK0C_UNSUPPORTED_POLICY_MODE" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
