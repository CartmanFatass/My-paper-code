"""VK-D5 / A-VK-D5: the reversed-roster `agent_order` hook.

`docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` VK-D5 (as amended by
A-VK-D5 in `docs/external-review/rounds/20260801_vk0_design_conformance/
21_PRO_OPEN_RAW.md`) threads an optional `agent_order` keyword from the public
`maybe_assign_skills` surface down to `_r30_maybe_assign_skills` and the R30
sampler. Three properties make this a valid, minimal addition rather than a
new source of drift:

1. `agent_order=None` (the only value any training path ever passes) stays
   byte-identical to today's hardcoded ascending order;
2. an explicit order actually changes which agent's token is sampled at which
   sequence position -- checked against an independent recomputation of
   `sigmoid(keep_logit)`, the same technique
   `tests/ha_ctse_process_keep_prob_capture_d7_test.py` uses to pin capture
   correctness, not by re-deriving the expected value the way the production
   code does;
3. a malformed order (wrong length, a duplicate, an out-of-range index) is
   rejected before any sampling happens, per A-VK-D5's guard
   (`sorted(agent_order) == list(range(n_agents))`).

The agent fixture below follows the same seeded-construction, seeded-call
pattern `tests/ha_ctse_process_d7_forced_token_test.py` uses for
`FixedClockAREditPolicy` directly (`torch.manual_seed` before construction,
`torch.manual_seed` before each sampling call, compare outputs) -- applied one
level up, at the `StandaloneProcessAgent.maybe_assign_skills` surface this
task actually threads the parameter through, using the same
`StandaloneProcessAgent` R30 construction as
`tests/ha_ctse_process_keep_prob_capture_d7_test.py`
(`test_maybe_assign_skills_wires_keep_prob_end_to_end_on_r30_toy`), with
`n_agents=2` to match the V-K0 config.
"""

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.standalone_agent import StandaloneProcessAgent


def _r30_process_config(**overrides):
    cfg = SimpleNamespace(
        n_z=3,
        state_dim=8,
        skill_lifetime_candidates=(1, 2),
        hidden_size=16,
        gamma=0.99,
        clip_epsilon=0.2,
        low_clip_epsilon=0.1,
        process_reward_coef=1.0,
        process_reward_warmup_steps=0,
        process_shortcut_margin=0.1,
        process_shortcut_margin_coef=0.5,
        normalize_process_outcomes=False,
        lr_discoverer_actor=1e-3,
        lr_coordinator=1e-3,
        lr_process_encoder=1e-3,
        process_encoder_embedding_dim=8,
        opt_compact_dim=8,
        opt_num_prototypes=2,
        opt_use_sparsemax=True,
        team_code_dim=8,
        num_team_codes=2,
        team_bridge_type="stochastic",
        high_entropy_coef=0.01,
        low_entropy_coef=0.01,
        edit_penalty_alpha=0.0,
        switch_penalty_beta=0.0,
        opt_cd_coef=0.0,
        opt_cmi_coef=0.0,
        scenario="two_timescale_role_free_actions",
        high_controller="r30_fixed_clock_ar_edit",
        skill_interval=3,
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def _build_agent(num_envs=1, seed=909, **overrides):
    cfg = _r30_process_config(**overrides)
    torch.manual_seed(seed)
    agent = StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=cfg,
        device="cpu",
        action_space_type="discrete",
        num_envs=num_envs,
    )
    assert agent.r30_enabled
    return agent


def test_default_none_is_byte_identical_to_explicit_ascending_order():
    """Property 1: `None` and an explicit `[0, 1]` must be indistinguishable,
    including in RNG consumption -- an explicit ascending order must not take
    a different code path (e.g. a different tensor construction, or extra
    random draws inside the guard) than the implicit default."""
    agent = _build_agent(num_envs=2)
    obs = np.zeros((2, 4), dtype=np.float32)

    torch.manual_seed(11)
    agent.maybe_assign_skills(
        obs, state=None, env_id=0, deterministic=False, agent_order=None
    )
    rng_default = torch.get_rng_state()

    torch.manual_seed(11)
    agent.maybe_assign_skills(
        obs, state=None, env_id=1, deterministic=False, agent_order=[0, 1]
    )
    rng_explicit = torch.get_rng_state()

    row_default = agent.high_check_buffer.pending[0]
    row_explicit = agent.high_check_buffer.pending[1]
    assert row_default is not None and row_explicit is not None

    np.testing.assert_array_equal(row_default.agent_order, row_explicit.agent_order)
    np.testing.assert_array_equal(row_default.token_kind, row_explicit.token_kind)
    np.testing.assert_array_equal(row_default.set_skill, row_explicit.set_skill)
    np.testing.assert_array_equal(row_default.token_valid, row_explicit.token_valid)
    np.testing.assert_array_equal(row_default.old_token_logp, row_explicit.old_token_logp)
    np.testing.assert_array_equal(row_default.keep_prob, row_explicit.keep_prob)
    np.testing.assert_array_equal(agent.active_skills[0], agent.active_skills[1])
    np.testing.assert_array_equal(agent.skill_age[0], agent.skill_age[1])
    np.testing.assert_array_equal(agent.has_active_skill[0], agent.has_active_skill[1])
    assert torch.equal(rng_default, rng_explicit)


def test_reversed_order_flips_which_agent_is_sampled_at_position_zero():
    """Property 2. Position 0 of the autoregressive sequence must belong to
    whichever agent the supplied order names first, not always agent 0. This
    is checked against an independent recomputation of
    `sigmoid(keep_logit)` for each agent's own (unmodified, pre-sampling)
    context -- an independent source of truth, not the value the production
    code itself produced. A wrong implementation that ignores `agent_order`
    (always samples ascending) would leave `row_reversed.agent_order ==
    [0, 1]` and `row_reversed.keep_prob[0]` equal to agent 0's recomputed
    value instead of agent 1's, and this test would catch either failure.
    """
    agent = _build_agent(num_envs=2, seed=321)
    # keep_head is zero-initialized (r30_fixed_clock.py), so every position
    # would carry the identical constant sigmoid(bias) regardless of agent
    # identity or order. Perturb it so the two agents' keep logits are
    # genuinely distinguishable, exactly as the keep-prob capture suite does.
    torch.nn.init.normal_(agent.high.keep_head.weight, std=1.0)
    obs = np.zeros((2, 4), dtype=np.float32)

    # Give both envs an identical, real (non-empty) incumbent roster so the
    # check exercises the learned-keep branch rather than the "no incumbent"
    # forced-SET branch, and force the clock so the check is due.
    for env_id in (0, 1):
        agent.has_active_skill[env_id, :] = True
        agent.active_skills[env_id, :] = np.array([1, 2], dtype=np.int64)
        agent.skill_age[env_id, :] = np.array([4, 9], dtype=np.int64)
        agent.steps_to_check[env_id] = 0

    torch.manual_seed(42)
    agent.maybe_assign_skills(
        obs, state=None, env_id=0, deterministic=False, agent_order=[0, 1]
    )
    torch.manual_seed(42)
    agent.maybe_assign_skills(
        obs, state=None, env_id=1, deterministic=False, agent_order=[1, 0]
    )

    row_ascending = agent.high_check_buffer.pending[0]
    row_reversed = agent.high_check_buffer.pending[1]
    assert row_ascending is not None and row_reversed is not None

    np.testing.assert_array_equal(row_ascending.agent_order, np.array([0, 1]))
    np.testing.assert_array_equal(row_reversed.agent_order, np.array([1, 0]))

    # Independently recompute keep_logit for each agent's own identity at the
    # (unmodified) pre-sampling roster, via the untouched per-token helper.
    joint_obs = agent._joint_obs_array(obs)
    state_arr = agent._state_array(None, joint_obs)
    context = agent._r30_context_tensors(state_arr, joint_obs)
    (
        _state_t,
        joint_t,
        compact,
        _team_code,
        team_vector,
        *_rest,
        weights,
        agent_relevance,
    ) = context
    omega = weights if agent.high_condition_on_omega else None
    relevance = agent_relevance if agent.use_agent_prototype_relevance else None

    prev_skills = torch.tensor([1, 2], dtype=torch.long)
    prev_ages = torch.tensor([4, 9], dtype=torch.long)
    prev_active = torch.tensor([True, True])

    def expected_keep_prob(agent_id):
        _hidden, keep_logit, _skill_logits, _entropy = agent.high._token_context(
            joint_t.squeeze(0),
            compact,
            team_vector,
            prev_skills.clone(),
            prev_ages.clone(),
            prev_active.clone(),
            agent_id,
            omega,
            relevance,
        )
        return torch.sigmoid(keep_logit).detach().squeeze(0)

    expected_agent0 = expected_keep_prob(0)
    expected_agent1 = expected_keep_prob(1)
    # Sanity: the perturbed head really does distinguish the two agents at
    # this roster, so the cross-check below is not vacuously satisfied.
    assert not torch.isclose(expected_agent0, expected_agent1)

    torch.testing.assert_close(
        torch.tensor(float(row_ascending.keep_prob[0])), expected_agent0, rtol=0, atol=0
    )
    torch.testing.assert_close(
        torch.tensor(float(row_reversed.keep_prob[0])), expected_agent1, rtol=0, atol=0
    )
    assert not np.isclose(row_ascending.keep_prob[0], row_reversed.keep_prob[0])


@pytest.mark.parametrize(
    "bad_order",
    [
        [0, 0],  # duplicate, not a permutation
        [1],  # wrong length
        [0, 2],  # index out of range for n_agents=2
    ],
)
def test_invalid_agent_order_raises_before_sampling(bad_order):
    """A-VK-D5's guard: `sorted(agent_order) == list(range(n_agents))`. Each
    of these is a distinct way to fail that check (duplicate, short, out of
    range); all must raise ValueError naming the defect, before any
    sampling happens."""
    agent = _build_agent(num_envs=1, seed=17)
    obs = np.zeros((2, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="permutation"):
        agent.maybe_assign_skills(
            obs, state=None, env_id=0, deterministic=False, agent_order=bad_order
        )
    # No decision was recorded: the guard fired before act_sequence/start_decision.
    assert agent.high_check_buffer.pending[0] is None
