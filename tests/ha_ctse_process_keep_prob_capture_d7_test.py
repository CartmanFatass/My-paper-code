"""D7 keep-prob capture: `docs/research/designs/D7_KEEP_PROB_CAPTURE_SPEC.md`.

These tests calibrate the diagnostic capture of ``sigmoid(keep_logit)``, the
per-agent, per-check renewal-decision probability. Each test targets one of
the spec's acceptance criteria (detach, byte-identical `token_logp`, branch
semantics -- including the `not active` row the spec's first revision missed)
or the buffer-version plumbing the spec calls out as the one that "defeats a
naive bump".
"""

import hashlib
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.config import Config
from ha_ctse_process.r30_fixed_clock import (
    HIGH_BUFFER_VERSION,
    EditSequenceSample,
    FixedClockAREditPolicy,
    HighCheckBuffer,
    HighCheckRow,
    KEEP_TOKEN,
    SET_TOKEN,
)
from ha_ctse_process.standalone_agent import StandaloneProcessAgent


torch.set_num_threads(1)


def _build_policy(seed, **kwargs):
    torch.manual_seed(seed)
    defaults = dict(
        obs_dim=4,
        n_agents=3,
        n_skills=4,
        hidden_dim=16,
        compact_dim=3,
        team_code_dim=3,
    )
    defaults.update(kwargs)
    return FixedClockAREditPolicy(**defaults)


def _context(n_agents=3):
    joint_obs = torch.randn(n_agents, 4)
    compact = torch.randn(1, 3)
    team_vector = torch.randn(1, 3)
    agent_order = torch.arange(n_agents, dtype=torch.long)
    return joint_obs, compact, team_vector, agent_order


def test_edit_sequence_sample_construction_requires_keep_prob():
    """Frozen dataclass: omitting keep_prob is a construction error, not a
    silent None -- this is the property the spec relies on at r30_fixed_clock.py:315."""
    kwargs = dict(
        token_kind=torch.zeros(2, dtype=torch.long),
        set_skill=torch.zeros(2, dtype=torch.long),
        token_logp=torch.zeros(2),
        token_valid=torch.ones(2, dtype=torch.bool),
        skill_entropy=torch.zeros(2),
        final_skills=torch.zeros(2, dtype=torch.long),
        final_ages=torch.zeros(2, dtype=torch.long),
        final_active=torch.zeros(2, dtype=torch.bool),
    )
    with pytest.raises(TypeError):
        EditSequenceSample(**kwargs)
    # With keep_prob supplied, construction succeeds.
    EditSequenceSample(keep_prob=torch.full((2,), float("nan")), **kwargs)


def test_high_check_row_construction_requires_keep_prob():
    kwargs = dict(
        env_id=0,
        episode_id=0,
        sequence_index=0,
        state=np.zeros(1, dtype=np.float32),
        joint_obs=np.zeros(1, dtype=np.float32),
        prev_skills=np.zeros(1, dtype=np.int64),
        prev_active=np.zeros(1, dtype=np.bool_),
        prev_ages=np.zeros(1, dtype=np.int64),
        steps_to_check=0,
        decision_mask=True,
        agent_order=np.zeros(1, dtype=np.int64),
        token_kind=np.zeros(1, dtype=np.int64),
        set_skill=np.zeros(1, dtype=np.int64),
        token_valid=np.ones(1, dtype=np.bool_),
        old_token_logp=np.zeros(1, dtype=np.float32),
        old_value=0.0,
    )
    with pytest.raises(TypeError):
        HighCheckRow(**kwargs)
    HighCheckRow(keep_prob=np.full(1, np.nan, dtype=np.float32), **kwargs)


def test_keep_prob_matches_sigmoid_keep_logit_on_learned_incumbent_branch():
    """Learned keep, neither flag, agent has an incumbent -> a real probability,
    shaped like token_kind, and equal to sigmoid(keep_logit) for the same
    forward pass (checked via the untouched replay path, evaluate_sequence).

    ``keep_head`` is zero-initialized (``r30_fixed_clock.py:84``), so at
    initialization ``keep_logit`` is input-independent and every position
    carries the identical constant ``sigmoid(bias)``. An ``allclose`` check
    against that constant passes even if the capture is positional, or reads
    the wrong agent's logit, or is simply ``torch.full_like(keep_logit, 0.6)``.
    Perturb the head off that degeneracy first so the three positions carry
    genuinely different logits, then require bit-exact equality against an
    independently recomputed ``sigmoid(keep_logit)``.
    """
    policy = _build_policy(101)
    torch.nn.init.normal_(policy.keep_head.weight, std=1.0)
    joint_obs, compact, team_vector, agent_order = _context(n_agents=3)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([5, 10, 1])
    prev_active = torch.tensor([True, True, True])
    torch.manual_seed(555)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=True,
    )
    assert sample.keep_prob.shape == sample.token_kind.shape
    assert torch.isfinite(sample.keep_prob).all()
    # The head is no longer degenerate, so a real capture must differ across
    # positions. A constant, positional, or wrong-agent capture would still
    # produce a single repeated value here.
    distinct = {round(value, 9) for value in sample.keep_prob.tolist()}
    assert len(distinct) == sample.keep_prob.numel()

    # Recompute keep_logit independently for each token via the untouched
    # per-token context helper, using the same (deterministic) working state
    # act_sequence would have produced, and compare sigmoid(keep_logit) to the
    # captured value bit-exactly (not allclose, which the degenerate-init
    # constant would already satisfy).
    working_skills = prev_skills.long().clone()
    working_ages = prev_ages.long().clone()
    working_active = prev_active.bool().clone()
    for position, agent_id in enumerate(agent_order.tolist()):
        _hidden, keep_logit, _skill_logits, _entropy_logits = policy._token_context(
            joint_obs,
            compact,
            team_vector,
            working_skills,
            working_ages,
            working_active,
            agent_id,
            None,
            None,
        )
        expected = torch.sigmoid(keep_logit).detach().squeeze(0)
        assert torch.equal(sample.keep_prob[position], expected)
        kind = int(sample.token_kind[position].item())
        if kind != KEEP_TOKEN:
            working_skills[agent_id] = int(sample.set_skill[position].item())
            working_ages[agent_id] = 0
            working_active[agent_id] = True


def test_keep_prob_has_no_grad_fn_while_token_logp_stays_differentiable():
    """Proves criterion 1: keep_prob must never carry a gradient path, even
    though keep_logit is live in the graph at the point of capture (proven by
    token_logp, from the same forward pass, remaining differentiable)."""
    policy = _build_policy(202, n_agents=1)
    joint_obs, compact, team_vector, agent_order = _context(n_agents=1)
    prev_skills = torch.tensor([0])
    prev_ages = torch.tensor([3])
    prev_active = torch.tensor([True])
    torch.manual_seed(9)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )
    assert sample.keep_prob.requires_grad is False
    assert sample.keep_prob.grad_fn is None
    # The graph was genuinely live at capture: token_logp from the identical
    # forward pass still carries a gradient back to the policy parameters.
    assert sample.token_logp.requires_grad is True
    loss = sample.token_logp.sum()
    loss.backward()
    assert policy.keep_head.weight.grad is not None


def test_keep_prob_nan_for_native_categorical_edit_run():
    """`native_categorical_edit` -> NaN for every token; count equals token
    count, the exact check the spec's verification section asks for."""
    policy = _build_policy(303, native_categorical_edit=True)
    assert policy.keep_head is None
    joint_obs, compact, team_vector, agent_order = _context(n_agents=3)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([1, 2, 3])
    prev_active = torch.tensor([True, True, True])
    torch.manual_seed(11)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )
    assert int(torch.isnan(sample.keep_prob).sum()) == sample.keep_prob.numel()


def test_keep_prob_nan_for_force_refresh_every_check_run():
    policy = _build_policy(404, force_refresh_every_check=True)
    assert policy.keep_head is not None
    joint_obs, compact, team_vector, agent_order = _context(n_agents=3)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([1, 2, 3])
    prev_active = torch.tensor([True, True, True])
    torch.manual_seed(12)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )
    assert int(torch.isnan(sample.keep_prob).sum()) == sample.keep_prob.numel()
    assert torch.all(sample.token_kind != KEEP_TOKEN)


def test_keep_prob_nan_exactly_for_no_incumbent_tokens_finite_elsewhere():
    """The row the first spec revision missed: on an ordinary learned-keep
    run, `keep_prob` is NaN exactly for the tokens whose agent had no
    incumbent at that check (`not active`, r30_fixed_clock.py:263-267), and
    finite everywhere else. A wrong implementation that keys only on the two
    constructor flags (the original table) would leave this finite instead --
    this is exactly the case that must fail if that regression recurs."""
    policy = _build_policy(505)
    assert not policy.native_categorical_edit
    assert not policy.force_refresh_every_check
    joint_obs, compact, team_vector, agent_order = _context(n_agents=3)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([0, 4, 9])
    prev_active = torch.tensor([False, True, True])
    torch.manual_seed(13)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )
    expected_nan = ~prev_active
    assert torch.equal(torch.isnan(sample.keep_prob), expected_nan)
    assert torch.isfinite(sample.keep_prob[prev_active]).all()
    # And the no-incumbent token is unconditionally SET, per the spec row.
    assert int(sample.token_kind[0].item()) != KEEP_TOKEN


def test_keep_prob_nan_when_keep_head_forced_none_defensively(monkeypatch):
    """`keep_head is None` is listed as its own branch-semantics row, distinct
    from `native_categorical_edit`, even though the current constructor only
    ever produces a None head under that flag. Force the head to None directly
    (independent of the flag) to prove the guard is load-bearing rather than
    dead code riding on the flag coincidence."""
    policy = _build_policy(606, n_agents=1)
    assert not policy.native_categorical_edit
    monkeypatch.setattr(policy, "keep_head", None)
    joint_obs, compact, team_vector, agent_order = _context(n_agents=1)
    prev_skills = torch.tensor([0])
    prev_ages = torch.tensor([2])
    prev_active = torch.tensor([True])
    torch.manual_seed(14)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )
    assert bool(torch.isnan(sample.keep_prob).all())


def test_token_logp_matches_untouched_replay_path_evaluate_sequence():
    """Criterion 2: token_logp must be byte-identical -- checked against
    evaluate_sequence, a separate, untouched code path that independently
    recomputes logp from the realized (token_kind, set_skill) under the same
    (unchanged) weights. If keep_prob capture had leaked into the logp
    factorization, these would diverge."""
    policy = _build_policy(707)
    joint_obs, compact, team_vector, agent_order = _context(n_agents=3)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([1, 1, 1])
    prev_active = torch.tensor([True, True, True])
    torch.manual_seed(15)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=True,
    )
    replay_logp, _replay_entropy = policy.evaluate_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        sample.token_kind,
        sample.set_skill,
    )
    assert torch.equal(sample.token_logp.detach(), replay_logp.detach())


def test_high_check_buffer_stores_keep_prob_and_continuation_defaults_to_nan():
    """Wiring check for HighCheckRow (required change 3): a decision row keeps
    the supplied per-position array; a continuation row (no per-token decision
    at all) defaults to NaN rather than zeros, consistent with 'not a real
    renewal decision' -> NaN."""
    buffer = HighCheckBuffer(num_envs=2, n_agents=3, gamma=0.99)
    keep_prob = np.array([0.7, float("nan"), 0.2], dtype=np.float32)
    row = buffer.start_decision(
        env_id=0,
        episode_id=0,
        state=np.zeros(1, dtype=np.float32),
        joint_obs=np.zeros(1, dtype=np.float32),
        prev_skills=np.zeros(3, dtype=np.int64),
        prev_active=np.ones(3, dtype=np.bool_),
        prev_ages=np.zeros(3, dtype=np.int64),
        steps_to_check=0,
        old_value=0.0,
        keep_prob=keep_prob,
    )
    np.testing.assert_array_equal(row.keep_prob[np.isfinite(keep_prob)], keep_prob[np.isfinite(keep_prob)])
    assert np.isnan(row.keep_prob[1])

    continuation = buffer.start_continuation(
        env_id=1,
        episode_id=0,
        state=np.zeros(1, dtype=np.float32),
        joint_obs=np.zeros(1, dtype=np.float32),
        prev_skills=np.zeros(3, dtype=np.int64),
        prev_active=np.ones(3, dtype=np.bool_),
        prev_ages=np.zeros(3, dtype=np.int64),
        steps_to_check=5,
        old_value=0.0,
    )
    assert np.isnan(continuation.keep_prob).all()


def test_high_buffer_version_constant_and_config_default_are_bumped():
    assert HIGH_BUFFER_VERSION == 2
    buffer = HighCheckBuffer(num_envs=1, n_agents=1, gamma=0.99)
    assert buffer.version == 2
    assert Config.r30_high_buffer_version == 2


def test_enforce_r30_contract_hard_assign_writes_new_buffer_version(monkeypatch):
    """The site the spec calls out as the one that 'defeats a naive bump':
    train.py's enforce_r30_contract hard-assigns config.r30_high_buffer_version
    regardless of what the config already said. Confirm it now hard-assigns
    the bumped value, not the stale one."""
    monkeypatch.setattr(process_train.torch.cuda, "is_available", lambda: True)
    config = SimpleNamespace(
        high_controller="r30_fixed_clock_ar_edit",
        r30_high_buffer_version=1,
        r39_native_categorical_edit=False,
        constant_skill_no_high=False,
    )
    args = SimpleNamespace(
        r28_g1_arm="off",
        r29_action_info_mode="off",
        skill_interval=10,
        device="cuda",
        enable_team_intent=False,
        enable_low_actor_team_code=False,
        edit_penalty_alpha=None,
        switch_penalty_beta=None,
        enable_duration_entropy_floor=False,
    )
    process_train.enforce_r30_contract(config, args)
    assert config.r30_high_buffer_version == 2


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


def test_r30_agent_construction_rejects_stale_buffer_version_pin():
    """Implementation-adjacent closure: `HighCheckBuffer.version` reads the
    module constant while the manifest/checkpoint read
    `agent.r30_high_buffer_version` off config -- nothing previously asserted
    they agree, so a stale config/checkpoint pin would silently diverge from
    what the buffer actually writes. Construction must now refuse to build an
    agent whose config disagrees with the frozen constant."""
    cfg = _r30_process_config(r30_high_buffer_version=1)
    with pytest.raises(ValueError):
        StandaloneProcessAgent(
            obs_dim=4,
            action_dim=3,
            n_agents=2,
            config=cfg,
            device="cpu",
            action_space_type="discrete",
            num_envs=1,
        )
    # The registered value (2, matching HIGH_BUFFER_VERSION) still constructs.
    ok_cfg = _r30_process_config(r30_high_buffer_version=HIGH_BUFFER_VERSION)
    StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=ok_cfg,
        device="cpu",
        action_space_type="discrete",
        num_envs=1,
    )


def test_maybe_assign_skills_wires_keep_prob_end_to_end_on_r30_toy():
    """End-to-end wiring check for the drain point the unit tests above never
    exercise: `standalone_agent.py:4073` (`keep_prob=sample.keep_prob...`).
    Constructing the actual R30 agent on the `two_timescale_role_free_actions`
    toy under the registered CPU/1-thread contract and driving
    `maybe_assign_skills` through two checks proves the field is actually
    populated from the policy's own capture rather than left at its
    all-NaN default or silently pointed at another tensor.

    Deleting the `keep_prob=...` kwarg at the call site leaves every row's
    `keep_prob` at the constructor default (all-NaN); the `prev_active`-mask
    assertion on the second row is exactly what that leaves failing.
    Substituting `token_logp` for `keep_prob` at that call site leaves every
    row's `keep_prob` elementwise identical to `old_token_logp`; the final
    assertion is exactly what that leaves failing. `enforce_r30_contract`
    hard-requires CUDA, so the agent is constructed directly rather than
    through that path -- the registered backend for this suite is CPU.
    """
    cfg = _r30_process_config()
    torch.manual_seed(909)
    agent = StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=cfg,
        device="cpu",
        action_space_type="discrete",
        num_envs=1,
    )
    assert agent.r30_enabled

    obs = np.zeros((2, 4), dtype=np.float32)

    # First check: episode start. has_active_skill starts all-False, so this
    # check is due unconditionally, every agent has no incumbent to keep, and
    # the spec's table requires NaN there (r30_fixed_clock.py:263-267) with
    # every token forced SET.
    torch.manual_seed(11)
    agent.maybe_assign_skills(obs, state=None, env_id=0, deterministic=False)
    assert agent.high_check_buffer.pending[0] is not None
    assert agent.high_check_buffer.rows == []

    # Force the clock so the next check is due even though every agent now
    # has an incumbent (the ordinary case the D7 branch table calls the
    # "learned keep" regime).
    agent.steps_to_check[0] = 0
    torch.manual_seed(12)
    agent.maybe_assign_skills(obs, state=None, env_id=0, deterministic=False)

    # (a) the first (now-closed) row: all-NaN keep_prob, all-SET tokens.
    assert len(agent.high_check_buffer.rows) == 1
    first_row = agent.high_check_buffer.rows[0]
    assert np.isnan(first_row.keep_prob).all()
    assert np.all(first_row.token_kind == SET_TOKEN)

    # (b) the second (still-pending) row: finite keep_prob exactly where
    # prev_active is True.
    second_row = agent.high_check_buffer.pending[0]
    assert second_row is not None
    assert bool(np.all(second_row.prev_active))
    np.testing.assert_array_equal(
        np.isfinite(second_row.keep_prob), second_row.prev_active
    )

    # (c) keep_prob is not the wrong tensor: it must not equal old_token_logp,
    # the quantity the spec explicitly says is not a substitute.
    assert not np.array_equal(second_row.keep_prob, second_row.old_token_logp)


def test_act_sequence_golden_token_logp_and_rng_consumption():
    """Golden-value regression: pins `token_logp` and post-call RNG state
    bitwise, at a fixed seed, against values measured from the current
    implementation. This is the artifact that discharges the D7 spec's
    verification (`token_logp` equality, RNG-consumption equality) going
    forward -- once this change commits, the pre-change code used for the
    original before/after comparison is no longer available to diff against.
    """
    torch.manual_seed(2026)
    policy = FixedClockAREditPolicy(
        obs_dim=4,
        n_agents=3,
        n_skills=4,
        hidden_dim=16,
        compact_dim=3,
        team_code_dim=3,
    )
    generator = torch.Generator().manual_seed(4242)
    joint_obs = torch.randn(3, 4, generator=generator)
    compact = torch.randn(1, 3, generator=generator)
    team_vector = torch.randn(1, 3, generator=generator)
    agent_order = torch.arange(3, dtype=torch.long)
    prev_skills = torch.tensor([0, 1, 2])
    prev_ages = torch.tensor([5, 10, 1])
    prev_active = torch.tensor([True, True, True])

    torch.manual_seed(77)
    sample = policy.act_sequence(
        joint_obs,
        compact,
        team_vector,
        prev_skills,
        prev_ages,
        prev_active,
        agent_order,
        deterministic=False,
    )

    expected_token_logp = np.array(
        [-0.5108256340026855, -0.5108256340026855, -1.7274526357650757],
        dtype=np.float32,
    )
    actual_token_logp = sample.token_logp.detach().numpy().astype(np.float32)
    assert np.array_equal(actual_token_logp, expected_token_logp)

    rng_digest = hashlib.sha256(
        torch.get_rng_state().numpy().tobytes()
    ).hexdigest()
    assert (
        rng_digest
        == "81bfe5328655c1edb5313893abb3ac37189580610b50a3c4bf866c75ae222e7b"
    )
