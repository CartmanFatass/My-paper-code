"""D7 interventional hook: forced tokens in `FixedClockAREditPolicy.act_sequence`.

Pass condition B of `D7_R30_RENEWAL_DIAGNOSTIC.md` needs a paired KEEP-versus-SET
contrast at one focal token, and D0's continuation semantics require that later
agents in the same check **react** to the changed prefix. These tests pin the four
properties that make that a valid intervention rather than a different policy:

1. the default path is untouched -- guarded bitwise by
   `test_act_sequence_golden_token_logp_and_rng_consumption` in the keep-prob
   suite, and re-checked here against an explicit empty forcing map;
2. forcing consumes the same base draws, so paired branches under common random
   numbers stay aligned downstream;
3. later agents are regenerated under the modified prefix;
4. an inadmissible intervention raises instead of reporting a fabricated branch.
"""

import numpy as np
import pytest
import torch

from ha_ctse_process.r30_fixed_clock import (
    INVALID_SKILL,
    KEEP_TOKEN,
    SET_TOKEN,
    FixedClockAREditPolicy,
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
    return FixedClockAREditPolicy(**defaults)


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


def _run(policy, ctx, seed=555, **kwargs):
    torch.manual_seed(seed)
    sample = policy.act_sequence(**ctx, **kwargs)
    return sample, torch.get_rng_state()


def test_empty_forcing_map_is_the_unhooked_sampler():
    policy = _policy()
    ctx = _context()
    base, base_rng = _run(policy, ctx)
    none_sample, none_rng = _run(policy, ctx, forced_tokens=None)
    empty_sample, empty_rng = _run(policy, ctx, forced_tokens={})

    for other, rng in ((none_sample, none_rng), (empty_sample, empty_rng)):
        torch.testing.assert_close(other.token_logp, base.token_logp, rtol=0, atol=0)
        torch.testing.assert_close(other.keep_prob, base.keep_prob, rtol=0, atol=0)
        assert torch.equal(other.token_kind, base.token_kind)
        assert torch.equal(other.set_skill, base.set_skill)
        assert torch.equal(other.final_skills, base.final_skills)
        assert torch.equal(rng, base_rng)


def test_forcing_consumes_the_same_base_draws():
    """The property paired replay rests on. The learned-keep branch draws both the
    keep uniform and the skill categorical unconditionally before either is used,
    so replacing the *outcome* cannot shift any later random choice. If it could,
    the KEEP and SET branches would diverge downstream for a reason that has
    nothing to do with the intervention."""
    policy = _policy()
    ctx = _context()
    _, base_rng = _run(policy, ctx)

    incumbent = int(ctx["prev_skills"][0].item())
    other_skill = (incumbent + 1) % N_SKILLS
    _, keep_rng = _run(policy, ctx, forced_tokens={0: (KEEP_TOKEN, INVALID_SKILL)})
    _, set_rng = _run(policy, ctx, forced_tokens={0: (SET_TOKEN, other_skill)})

    assert torch.equal(keep_rng, base_rng)
    assert torch.equal(set_rng, base_rng)


def test_forced_keep_and_forced_set_take_effect():
    policy = _policy()
    ctx = _context()
    incumbent = int(ctx["prev_skills"][0].item())
    target = (incumbent + 2) % N_SKILLS

    kept, _ = _run(policy, ctx, forced_tokens={0: (KEEP_TOKEN, INVALID_SKILL)})
    assert int(kept.token_kind[0]) == KEEP_TOKEN
    assert int(kept.set_skill[0]) == INVALID_SKILL
    # A KEEP does not touch the commitment: same skill, age keeps running.
    assert int(kept.final_skills[0]) == incumbent
    assert int(kept.final_ages[0]) == int(ctx["prev_ages"][0])

    switched, _ = _run(policy, ctx, forced_tokens={0: (SET_TOKEN, target)})
    assert int(switched.token_kind[0]) == SET_TOKEN
    assert int(switched.set_skill[0]) == target
    assert int(switched.final_skills[0]) == target
    # A genuine SET resets the realized-lifetime clock; D0 section 1 measures
    # lifetime as skill_age at exactly this moment.
    assert int(switched.final_ages[0]) == 0
    assert bool(switched.final_active[0])


def test_forced_token_logp_follows_the_policy_factorization():
    """A forced token reports the log-probability the policy assigns to the
    branch actually taken, so `log_keep` and `log_switch + skill_logp` stay
    consistent -- not the one the sampler happened to draw."""
    policy = _policy()
    ctx = _context()
    incumbent = int(ctx["prev_skills"][0].item())
    target = (incumbent + 1) % N_SKILLS

    kept, _ = _run(policy, ctx, forced_tokens={0: (KEEP_TOKEN, INVALID_SKILL)})
    switched, _ = _run(policy, ctx, forced_tokens={0: (SET_TOKEN, target)})

    # Recover the focal token's own distributions from the same pre-decision state.
    _hidden, keep_logit, skill_logits, _entropy_logits = policy._token_context(
        ctx["joint_obs"],
        ctx["compact"],
        ctx["team_vector"],
        ctx["prev_skills"].clone(),
        ctx["prev_ages"].clone(),
        ctx["prev_active"].clone(),
        0,
        None,
        None,
    )
    log_keep = torch.nn.functional.logsigmoid(keep_logit).squeeze(0)
    log_switch = torch.nn.functional.logsigmoid(-keep_logit).squeeze(0)
    skill_logp = torch.nn.functional.log_softmax(skill_logits, dim=-1)[0, target]

    torch.testing.assert_close(kept.token_logp[0], log_keep)
    torch.testing.assert_close(switched.token_logp[0], log_switch + skill_logp)
    # Both are real log-probabilities, which the masked-incumbent branch is not.
    assert float(kept.token_logp[0]) < 0.0
    assert float(switched.token_logp[0]) < 0.0


def test_later_agents_react_to_the_forced_prefix():
    """D0's continuation semantics. Holding later factual tokens fixed would
    estimate a direct effect the deployed autoregressive policy never exhibits,
    so agent 1's own token must depend on what agent 0 was forced to do."""
    policy = _policy()
    ctx = _context()
    incumbent = int(ctx["prev_skills"][0].item())
    first = (incumbent + 1) % N_SKILLS
    second = (incumbent + 2) % N_SKILLS

    a, _ = _run(policy, ctx, forced_tokens={0: (SET_TOKEN, first)})
    b, _ = _run(policy, ctx, forced_tokens={0: (SET_TOKEN, second)})

    # Only agent 0 is forced; agents 1 and 2 are sampled. Their log-probabilities
    # are computed from a roster encoding that includes agent 0's new skill and
    # reset age, so they must move when that prefix moves.
    assert not torch.equal(a.token_logp[1:], b.token_logp[1:])


@pytest.mark.parametrize(
    "forced,active,expected",
    [
        # Nothing to keep: the sampler itself forces SET with no incumbent.
        ({0: (KEEP_TOKEN, INVALID_SKILL)}, False, "no incumbent"),
        # Same-label renewal is structurally excluded, not merely unlikely.
        ({0: (SET_TOKEN, 0)}, True, "structurally excluded"),
        ({0: (7, INVALID_SKILL)}, True, "not KEEP or SET"),
        ({0: (SET_TOKEN, 99)}, True, "out of range"),
    ],
)
def test_inadmissible_forcing_raises(forced, active, expected):
    policy = _policy()
    ctx = _context(active=active)
    with pytest.raises(ValueError, match=expected):
        _run(policy, ctx, forced_tokens=forced)


def test_forcing_is_rejected_on_branches_without_a_renewal_decision():
    """Under native-categorical edit and full refresh, KEEP is not a decision, so
    a forced renewal contrast there would be a fabricated quantity."""
    ctx = _context()
    for kwargs in (
        dict(native_categorical_edit=True),
        dict(force_refresh_every_check=True),
    ):
        policy = _policy(**kwargs)
        with pytest.raises(ValueError, match="learned-keep branch"):
            _run(policy, ctx, forced_tokens={0: (KEEP_TOKEN, INVALID_SKILL)})


def test_keep_prob_records_the_policy_not_the_intervention():
    """`keep_prob` is the diagnostic the whole primitive rests on. It must keep
    reporting sigmoid(keep_logit) -- what the policy would have done -- so a
    forced branch cannot contaminate the natural-alignment reading of condition C.
    """
    policy = _policy()
    ctx = _context()
    base, _ = _run(policy, ctx)
    kept, _ = _run(policy, ctx, forced_tokens={0: (KEEP_TOKEN, INVALID_SKILL)})
    incumbent = int(ctx["prev_skills"][0].item())
    switched, _ = _run(
        policy, ctx, forced_tokens={0: (SET_TOKEN, (incumbent + 1) % N_SKILLS)}
    )

    torch.testing.assert_close(kept.keep_prob[0], base.keep_prob[0], rtol=0, atol=0)
    torch.testing.assert_close(switched.keep_prob[0], base.keep_prob[0], rtol=0, atol=0)
    assert np.isfinite(float(base.keep_prob[0]))
