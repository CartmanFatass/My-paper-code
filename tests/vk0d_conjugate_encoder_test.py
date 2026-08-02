"""V-K0D A-VD-1 / A-VD-6: the anonymous-OTHER (conjugate) roster encoder.

`docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`, amendments A-VD-1
(anonymous-OTHER encoding, no populated SELF block, unchanged tensor layout),
A-VD-2 (conjugacy, NOT same-state serialization invariance) and A-VD-6 (the
flag creates no parameter or initialization-order change).

These are calibration tests for the PRIMARY arm's carrier, not coverage of
plumbing. Each one is here because failing it would make the V-K0D comparison
report a wrong number:

* if the flag moved or resized a module, the three arms would not start from
  identical parameters and any competence difference would be confounded
  (A-VD-6) -- `test_conjugate_flag_creates_no_parameter_or_init_order_change`;
* if the relative slot still depended on the other agent's physical index, the
  absolute agent-label shortcut the treatment is supposed to delete would still
  be readable -- `test_conjugate_context_is_independent_of_physical_identity`;
* if the encoder leaked any physical-ID information, the frozen conjugacy gate
  of VD-5 would be certifying a property the carrier does not have --
  `test_conjugate_encoder_satisfies_permutation_conjugacy_over_the_ar_tree`,
  paired with the deliberate negative
  `test_absolute_encoder_fails_the_same_conjugacy_witness`, which runs the
  identical witness against the unchanged absolute-ID encoder and requires it
  to be rejected. A conjugacy witness that cannot go red is not a witness.
* if the flag-off path drifted at all, the REFERENCE arm would stop
  reproducing the frozen V-K0B digests (A-VD-7) --
  `test_flag_off_encoding_matches_the_frozen_absolute_layout`.

The expected roster vectors below are written as literal indices and literal
arithmetic taken from the frozen layout description, never recomputed by
calling the production code or by re-deriving its offsets symbolically.
"""

import math

import torch

from ha_ctse_process.r30_fixed_clock import (
    KEEP_TOKEN,
    SET_TOKEN,
    FixedClockAREditPolicy,
    advance_working_state,
)

N_AGENTS = 2
N_SKILLS = 3
OBS_DIM = 4
COMPACT_DIM = 3
TEAM_DIM = 3
OMEGA_DIM = 2
RELEVANCE_DIM = 2
HIDDEN = 16
AGE_REFERENCE_STEPS = 500

# Frozen layout for (n_agents=2, n_skills=3), stated as literals rather than as
# the production expression `n_skills * (1 + 2 * n_agents)`:
#   index  0.. 2  permutation-invariant skill-count block
#   index  3.. 5  identity block, slot 0
#   index  6.. 8  identity block, slot 1
#   index  9..11  age block, slot 0
#   index 12..14  age block, slot 1
AR_PREFIX_DIM = 15
# obs 4 + skill one-hot 3 + age 1 + compact 3 + team 3 + omega 2 + relevance 2
# + roster prefix 15
INPUT_DIM = 33


def _policy(conjugate, seed=1234):
    torch.manual_seed(seed)
    return FixedClockAREditPolicy(
        obs_dim=OBS_DIM,
        n_agents=N_AGENTS,
        n_skills=N_SKILLS,
        hidden_dim=HIDDEN,
        compact_dim=COMPACT_DIM,
        team_code_dim=TEAM_DIM,
        omega_dim=OMEGA_DIM,
        agent_relevance_dim=RELEVANCE_DIM,
        age_reference_steps=AGE_REFERENCE_STEPS,
        conjugate_context=conjugate,
    )


def _discriminating_policy(conjugate, seed=1234):
    """`keep_head` ships zero-initialized, which would make `keep_mass` an
    input-independent constant and leave half of every mass comparison below
    trivially satisfied. Perturb it (the technique
    `tests/vk0c_token_mass_test.py` already uses) so both the KEEP and the SET
    component of every comparison actually discriminate contexts."""
    policy = _policy(conjugate, seed=seed)
    torch.manual_seed(77)
    torch.nn.init.normal_(policy.keep_head.weight, std=1.0)
    return policy


def _roster(policy, skills, ages, active, focal):
    return policy.encode_working_roster(
        torch.tensor(skills, dtype=torch.long),
        torch.tensor(ages, dtype=torch.long),
        torch.tensor(active, dtype=torch.bool),
        focal,
    )


# ---------------------------------------------------------------- A-VD-6 ----


def test_conjugate_flag_creates_no_parameter_or_init_order_change():
    """A-VD-6 witness. Same seed, flag on vs off: identical state_dict keys,
    shapes, dtypes and exact bytes, and identical torch RNG position after
    construction (an added module that consumed RNG but exposed no parameter
    would still shift every arm's initialization and is caught here)."""
    torch.manual_seed(9)
    off = _policy(False)
    off_rng = torch.get_rng_state()
    torch.manual_seed(9)
    on = _policy(True)
    on_rng = torch.get_rng_state()

    off_state = off.state_dict()
    on_state = on.state_dict()
    assert list(off_state.keys()) == list(on_state.keys())
    for key in off_state:
        a, b = off_state[key], on_state[key]
        assert a.shape == b.shape, key
        assert a.dtype == b.dtype, key
        assert a.detach().numpy().tobytes() == b.detach().numpy().tobytes(), key
    assert torch.equal(off_rng, on_rng)


def test_conjugate_flag_preserves_shape_and_parameter_count():
    off = _policy(False)
    on = _policy(True)

    assert off.ar_prefix_dim == AR_PREFIX_DIM
    assert on.ar_prefix_dim == AR_PREFIX_DIM
    assert _roster(on, (0, 2), (5, 7), (True, True), 0).shape == (1, AR_PREFIX_DIM)

    assert off.input[1].in_features == INPUT_DIM
    assert on.input[1].in_features == INPUT_DIM
    assert tuple(off.input[0].normalized_shape) == (INPUT_DIM,)
    assert tuple(on.input[0].normalized_shape) == (INPUT_DIM,)

    off_params = sum(p.numel() for p in off.parameters())
    on_params = sum(p.numel() for p in on.parameters())
    assert off_params == on_params


def test_conjugate_context_rejects_more_than_one_other_agent():
    """The relative encoding names exactly one OTHER slot. With three agents
    two of them would collide in slot 0, silently losing a roster fact; the
    constructor must fail closed instead."""
    torch.manual_seed(3)
    try:
        FixedClockAREditPolicy(
            obs_dim=OBS_DIM,
            n_agents=3,
            n_skills=N_SKILLS,
            hidden_dim=HIDDEN,
            compact_dim=COMPACT_DIM,
            team_code_dim=TEAM_DIM,
            conjugate_context=True,
        )
    except ValueError as exc:
        assert "n_agents=2" in str(exc)
    else:
        raise AssertionError("expected ValueError for conjugate_context with n_agents=3")


# ---------------------------------------------------- A-VD-1 slot layout ----


def test_flag_off_encoding_matches_the_frozen_absolute_layout():
    """Flag-off byte compatibility. The expected vector is the frozen absolute
    layout written as literals: the other agent is physical id 1 with skill 2
    and age 7, so its identity entry is index 3 + 1*3 + 2 = 8 and its age entry
    index 9 + 1*3 + 2 = 14."""
    policy = _policy(False)
    out = _roster(policy, (0, 2), (5, 7), (True, True), 0)

    expected = torch.zeros(1, AR_PREFIX_DIM)
    expected[0, 2] = 0.5
    expected[0, 8] = 0.5
    expected[0, 14] = 0.5 * (math.log1p(7.0) / math.log1p(500.0))

    assert torch.equal(out, expected), f"{out} != {expected}"


def test_conjugate_encoding_writes_the_other_agent_into_relative_slot_zero():
    """A-VD-1 layout: the same roster, encoded relatively. The other agent's
    skill lands at index 3 + 0*3 + 2 = 5 and its age at index 9 + 0*3 + 2 = 11,
    the invariant count block is unchanged, and every self slot (identity
    indices 6..8, age indices 12..14) is exactly zero."""
    policy = _policy(True)
    out = _roster(policy, (0, 2), (5, 7), (True, True), 0)

    expected = torch.zeros(1, AR_PREFIX_DIM)
    expected[0, 2] = 0.5
    expected[0, 5] = 0.5
    expected[0, 11] = 0.5 * (math.log1p(7.0) / math.log1p(500.0))

    assert torch.equal(out, expected), f"{out} != {expected}"
    assert torch.equal(out[0, 6:9], torch.zeros(3))
    assert torch.equal(out[0, 12:15], torch.zeros(3))


def test_conjugate_context_is_independent_of_physical_identity():
    """The treatment itself: with the flag on, two rosters whose OTHER agent
    carries the same (skill, age) must encode identically even though the other
    agent sits at a different physical index and the focal agent's own skill,
    age and physical index all differ.

    The final assertion is the fixture check: the identical pair of rosters
    encodes *differently* under the unchanged absolute encoder, so the equality
    above is enforced by the conjugate code rather than by inputs that already
    had the property."""
    conjugate = _policy(True)
    # Case A: focal is physical agent 0; the OTHER is agent 1 with skill 2,
    # age 7. Focal's own state is skill 0, age 5.
    case_a = _roster(conjugate, (0, 2), (5, 7), (True, True), 0)
    # Case B: focal is physical agent 1; the OTHER is agent 0 with the same
    # skill 2, age 7. Focal's own state is a different skill 1 and age 4.
    case_b = _roster(conjugate, (2, 1), (7, 4), (True, True), 1)

    assert torch.equal(case_a, case_b), f"{case_a} != {case_b}"
    # Self slots stay empty from both sides.
    assert torch.equal(case_a[0, 6:9], torch.zeros(3))
    assert torch.equal(case_b[0, 6:9], torch.zeros(3))
    assert torch.equal(case_a[0, 12:15], torch.zeros(3))
    assert torch.equal(case_b[0, 12:15], torch.zeros(3))

    absolute = _policy(False)
    abs_a = _roster(absolute, (0, 2), (5, 7), (True, True), 0)
    abs_b = _roster(absolute, (2, 1), (7, 4), (True, True), 1)
    assert not torch.equal(abs_a, abs_b), "fixture check: absolute encoder must differ"


# ----------------------------------------------- A-VD-2 conjugacy witness ----


def _state():
    """One asymmetric decision context. Every physical-agent-indexed component
    differs between the two agents, so nothing below can be satisfied by an
    accidentally symmetric fixture."""
    torch.manual_seed(505)
    return {
        "joint_obs": torch.tensor(
            [
                [0.9, -0.3, 0.4, 1.7],
                [-1.1, 0.6, -0.8, 0.2],
            ]
        ),
        "compact": torch.randn(1, COMPACT_DIM),
        "team_vector": torch.randn(1, TEAM_DIM),
        "omega": torch.randn(1, OMEGA_DIM),
        "relevance": torch.tensor([[[0.2, -0.7], [1.3, 0.5]]]),
        "skills": torch.tensor([0, 2], dtype=torch.long),
        "ages": torch.tensor([5, 11], dtype=torch.long),
        "active": torch.tensor([True, True]),
    }


def _swap(x):
    """swap(x) over every physical-agent-indexed component: the two agents'
    observation rows, relevance rows, skills, ages and active flags. The
    anonymous global context (compact, team vector, omega) is untouched."""
    return {
        "joint_obs": x["joint_obs"].flip(0).clone(),
        "compact": x["compact"].clone(),
        "team_vector": x["team_vector"].clone(),
        "omega": x["omega"].clone(),
        "relevance": x["relevance"].flip(1).clone(),
        "skills": x["skills"].flip(0).clone(),
        "ages": x["ages"].flip(0).clone(),
        "active": x["active"].flip(0).clone(),
    }


def _mass(policy, ctx, skills, ages, active, agent_id):
    return policy.token_mass(
        ctx["joint_obs"],
        ctx["compact"],
        ctx["team_vector"],
        skills,
        ages,
        active,
        agent_id,
        ctx["omega"],
        ctx["relevance"],
    )


def _conjugacy_mismatches(policy):
    """Walk the whole two-token autoregressive tree and return the labels of
    every place where P01(.|x) and P10(.|swap(x)) disagree bit-exactly.

    Order [0,1] at x has physical agent 0 moving first; order [1,0] at swap(x)
    has physical agent 1 moving first, and agent 1's row of swap(x) is agent
    0's row of x. Conjugacy (A-VD-2) says the first mover's token mass must
    agree exactly, and then -- after each realizable first token is applied to
    the respective first mover -- the second mover's token mass must agree
    exactly too. Same-state invariance is NOT asserted anywhere here.
    """
    x = _state()
    y = _swap(x)
    mismatches = []

    def compare(label, left, right):
        for key in ("keep_mass", "set_mass"):
            if not torch.equal(left[key], right[key]):
                mismatches.append(f"{label}:{key}")

    compare(
        "first_mover",
        _mass(policy, x, x["skills"], x["ages"], x["active"], 0),
        _mass(policy, y, y["skills"], y["ages"], y["active"], 1),
    )

    first_tokens = [(KEEP_TOKEN, -1)] + [(SET_TOKEN, s) for s in range(N_SKILLS)]
    for kind, skill in first_tokens:
        xs, xa, xac = x["skills"].clone(), x["ages"].clone(), x["active"].clone()
        ys, ya, yac = y["skills"].clone(), y["ages"].clone(), y["active"].clone()
        advance_working_state(xs, xa, xac, 0, kind, skill)
        advance_working_state(ys, ya, yac, 1, kind, skill)
        compare(
            f"second_mover|kind={kind},skill={skill}",
            _mass(policy, x, xs, xa, xac, 1),
            _mass(policy, y, ys, ya, yac, 0),
        )
    return mismatches


def test_conjugate_encoder_satisfies_permutation_conjugacy_over_the_ar_tree():
    assert _conjugacy_mismatches(_discriminating_policy(True)) == []


def test_absolute_encoder_fails_the_same_conjugacy_witness():
    """Deliberate negative (A-VD-5's paired-negative rule, at unit level). The
    unchanged absolute-ID encoder writes the other agent at its physical slot,
    so the focal policy can read who it is -- the identical witness must
    reject it, and must already reject it at the first mover."""
    mismatches = _conjugacy_mismatches(_discriminating_policy(False))
    assert mismatches, "absolute-ID encoder must not satisfy the conjugacy witness"
    assert any(label.startswith("first_mover") for label in mismatches), mismatches
