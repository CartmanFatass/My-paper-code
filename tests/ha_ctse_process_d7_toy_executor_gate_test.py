"""D7.2B toy-lane gates: `docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md`.

The D7.2B positive control needs two things at once -- the supplied primitive
executor its ruling permits, so the competence prerequisite is met before any
renewal behaviour is read, and the learned-keep carrier it is measuring. Three
separate gates used to make that combination unreachable, all of them keyed to
`r39_native_categorical_edit` or to CUDA rather than to the thing they protect:

1. the executor gate refused fixed primitives unless native-categorical edit was
   on -- the branch where KEEP is not a decision at all;
2. the R30 contract's toy check-interval allowance sat inside the same
   native-categorical branch, so a learned-keep toy fell through to the generic
   `skill_interval=10` rule and silently broke D7's `Delta`;
3. the R30 contract hard-required CUDA, and this project's only environment is
   CPU-only.

These tests pin the unbundling: the permitted combination constructs and runs the
contract, and every restriction that protects something real still fails closed.
"""

from types import SimpleNamespace

import pytest

from ha_ctse_process import train as process_train
from ha_ctse_process.r30_fixed_clock import HIGH_BUFFER_VERSION
from ha_ctse_process.standalone_agent import (
    FixedSkillPrimitivePolicy,
    StandaloneProcessAgent,
)

TOY = "two_timescale_role_free_actions"


def _toy_config(**overrides):
    cfg = SimpleNamespace(
        n_z=4,
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
        scenario=TOY,
        high_controller="r30_fixed_clock_ar_edit",
        skill_interval=5,
        r30_high_buffer_version=HIGH_BUFFER_VERSION,
        r39_native_categorical_edit=False,
        r39_toy_fixed_skill_primitives=True,
        r39_toy_fixed_skill_action_schema="axis4_xy_v1",
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def _build(cfg, *, action_dim=2, action_space_type="continuous"):
    return StandaloneProcessAgent(
        obs_dim=4,
        action_dim=action_dim,
        n_agents=2,
        config=cfg,
        device="cpu",
        action_space_type=action_space_type,
        num_envs=1,
    )


def _contract_args(**overrides):
    args = SimpleNamespace(
        scenario=TOY,
        r28_g1_arm="off",
        r29_action_info_mode="off",
        skill_interval=5,
        device="cpu",
        enable_team_intent=False,
        enable_low_actor_team_code=False,
        edit_penalty_alpha=None,
        switch_penalty_beta=None,
        enable_duration_entropy_floor=False,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def _contract_config(**overrides):
    cfg = SimpleNamespace(
        high_controller="r30_fixed_clock_ar_edit",
        r30_high_buffer_version=HIGH_BUFFER_VERSION,
        r39_native_categorical_edit=False,
        constant_skill_no_high=False,
        r39_toy_k0=5,
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def test_supplied_executor_and_learned_keep_carrier_coexist():
    """The D7.2B combination itself. Before the unbundling this raised, and the
    positive control had to choose between its access floor and the carrier it
    measures."""
    agent = _build(_toy_config())

    # The supplied executor is in place: a constant table, no trainable
    # parameters, and no low-level optimizer to move them.
    assert isinstance(agent.low, FixedSkillPrimitivePolicy)
    assert agent.low.action_table.shape == (4, 2)
    assert not list(agent.low.parameters())
    assert agent.low_opt is None
    assert agent.low_actor_opt is None
    assert agent.low_critic_opt is None

    # And the carrier is live: learned-keep means the high controller owns a
    # keep_head, which is exactly what native-categorical edit removes.
    assert agent.r30_enabled
    assert not agent.r39_native_categorical_edit
    assert agent.high.keep_head is not None


def test_native_categorical_executor_lane_is_unchanged():
    """Unbundling must widen the gate, not move it: the lane that was already
    permitted still constructs, and still has no keep_head."""
    agent = _build(_toy_config(r39_native_categorical_edit=True))
    assert isinstance(agent.low, FixedSkillPrimitivePolicy)
    assert agent.high.keep_head is None


@pytest.mark.parametrize(
    "overrides,build_kwargs",
    [
        # The action table is tabulated for four skills over 2D continuous
        # actions on this one toy. Each of those is still pinned.
        ({"n_z": 3}, {}),
        ({"scenario": "alice_bob_asymmetric_cycles"}, {}),
        ({}, {"action_dim": 3}),
        ({"r39_toy_fixed_skill_action_schema": "axis4_xy_v2"}, {}),
    ],
)
def test_executor_gate_still_pinned_to_the_table_domain(overrides, build_kwargs):
    with pytest.raises(ValueError):
        _build(_toy_config(**overrides), **build_kwargs)


def test_direct_state_context_is_permitted_under_learned_keep():
    """The information contract D7.2B cannot do without. The toy's observations
    are identically zero and the initial target signs are redrawn per episode, so
    a high actor without the centralized state cannot tell which target is which:
    both match rates cap near 0.5 and the 0.75 competence floor is unreachable
    architecturally. Keyed to the edit mode, that made the positive control
    unmeasurable rather than negative."""
    agent = _build(_toy_config(r39_toy_direct_state_context=True))
    assert agent.r39_toy_direct_state_context
    assert agent.high.keep_head is not None
    # The compact vector is replaced by the state, so it must be wide enough to
    # carry it and must not be trained through.
    assert agent.state_dim <= 16
    assert not any(p.requires_grad for p in agent.compact.parameters())


def test_direct_state_context_actually_reaches_the_skill_logits():
    """The information contract must be *live*, not merely declared -- the class of
    defect that made the G20 credit rule inert. `_high_context_batch` sets
    `compact = pad(state)` under direct state, so the high actor's skill logits
    must move when the target signs flip.

    Note what cannot be used as the probe: `keep_head.weight` is zero-initialized,
    so `keep_logit` is a constant bias and both agents deterministically KEEP at
    entry. Comparing realized *tokens* therefore shows no difference even when the
    state is wired through correctly. The skill logits are the observable.
    """
    import torch

    import numpy as np

    agent = _build(_toy_config(r39_toy_direct_state_context=True))
    obs = np.zeros((2, 4), dtype=np.float32)

    def skill_logits(slow_sign, fast_sign):
        state = np.array(
            [slow_sign, 0.0, 0.0, fast_sign, 0.0, 0.0], dtype=np.float32
        )
        joint_obs = agent._joint_obs_array(obs)
        state_arr = agent._state_array(state, joint_obs)
        # The deployed context builder, so the input widths are the real ones.
        (
            _state_t,
            joint_t,
            compact,
            _team_code,
            team_vector,
            *_rest,
            weights,
            agent_relevance,
        ) = agent._r30_context_tensors(state_arr, joint_obs)
        _h, _keep, logits, _e = agent.high._token_context(
            joint_t.squeeze(0),
            compact,
            team_vector,
            torch.tensor([0, 2], dtype=torch.long),
            torch.tensor([3, 3], dtype=torch.long),
            torch.tensor([True, True]),
            0,
            weights if agent.high_condition_on_omega else None,
            agent_relevance if agent.use_agent_prototype_relevance else None,
        )
        return logits.detach()

    positive = skill_logits(1.0, 1.0)
    negative = skill_logits(-1.0, -1.0)
    assert not torch.allclose(positive, negative), (
        "target signs do not move the high actor's skill logits; the direct-state "
        "context is not live and condition A would be unreachable"
    )
    # The incumbent stays masked out regardless of the state.
    assert float(positive[0, 0]) <= torch.finfo(positive.dtype).min


@pytest.mark.parametrize(
    "overrides",
    [
        {"r39_toy_fixed_skill_primitives": False},
        {"scenario": "alice_bob_asymmetric_cycles"},
    ],
)
def test_direct_state_context_still_pinned_to_the_fixed_primitive_toy(overrides):
    with pytest.raises(ValueError):
        _build(_toy_config(r39_toy_direct_state_context=True, **overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"r30_high_ppo_epochs": 3},
        {"r30_high_actor_advantage_mode": "block_return"},
    ],
)
def test_credit_machinery_stays_pinned_to_the_native_lane(overrides):
    """Widening the information contract must not hand the learned-keep lane a
    multi-epoch or block-return high actor as a side effect. Those were validated
    on the native-categorical direct-state lane and nothing here revalidates
    them."""
    with pytest.raises(ValueError, match="native-categorical"):
        _build(_toy_config(r39_toy_direct_state_context=True, **overrides))


def test_contract_keys_the_toy_check_interval_to_the_scenario():
    """`Delta` is one check interval and the toy's fast period is k0=5 against a
    30-step slow period -- six checks per slow period. Keyed to the edit mode,
    the learned-keep toy was forced to skill_interval=10 instead."""
    config = _contract_config()
    process_train.enforce_r30_contract(config, _contract_args())

    with pytest.raises(ValueError, match="skill_interval=r39_toy_k0"):
        process_train.enforce_r30_contract(
            _contract_config(), _contract_args(skill_interval=10)
        )


def test_contract_still_requires_interval_ten_off_the_toy(monkeypatch):
    monkeypatch.setattr(process_train.torch.cuda, "is_available", lambda: True)
    scenario = "alice_bob_asymmetric_cycles"
    with pytest.raises(ValueError, match="skill_interval=10"):
        process_train.enforce_r30_contract(
            _contract_config(),
            _contract_args(scenario=scenario, skill_interval=5, device="cuda"),
        )
    # The interval the generic rule does accept still passes.
    process_train.enforce_r30_contract(
        _contract_config(),
        _contract_args(scenario=scenario, skill_interval=10, device="cuda"),
    )


def test_native_categorical_is_still_restricted_to_the_toy():
    with pytest.raises(ValueError, match="restricted to its toy gate"):
        process_train.enforce_r30_contract(
            _contract_config(r39_native_categorical_edit=True),
            _contract_args(scenario="alice_bob_asymmetric_cycles"),
        )


def test_d7_2b_config_yields_the_intended_lane():
    """The config is the run's identity, so assert the four properties D7.2B's
    validity rests on rather than trusting the file to keep saying so:
    learned-keep carrier live, supplied executor in place, the check interval
    equal to the source's own fast period, and external reward only."""
    from config_d7_2b_toy_learned_keep import Config

    cfg = Config()
    assert cfg.scenario == TOY
    assert cfg.high_controller == "r30_fixed_clock_ar_edit"
    assert cfg.r39_native_categorical_edit is False
    # Full refresh is the other branch where KEEP is not a decision.
    assert cfg.r30_force_refresh_every_check is False
    assert cfg.r39_toy_fixed_skill_primitives is True
    assert cfg.r39_toy_fixed_skill_action_schema == "axis4_xy_v1"
    # The declared information contract: centralized state at decision time.
    assert cfg.r39_toy_direct_state_context is True
    assert cfg.opt_compact_dim >= cfg.state_dim
    assert cfg.skill_interval == cfg.r39_toy_k0 == 5
    assert cfg.r39_toy_slow_period_blocks == 6
    assert cfg.n_z == 4
    assert cfg.process_reward_injection == "none"
    assert cfg.use_process_reward_for_discoverer is False

    agent = StandaloneProcessAgent(
        obs_dim=4,
        action_dim=2,
        n_agents=2,
        config=cfg,
        device="cpu",
        action_space_type="continuous",
        num_envs=2,
    )
    assert agent.r30_enabled
    assert isinstance(agent.low, FixedSkillPrimitivePolicy)
    assert agent.high.keep_head is not None
    assert agent.skill_interval == 5
    # The executor is frozen, so nothing can train it into the answer.
    assert not list(agent.low.parameters())
    assert agent.low_opt is None


def test_cpu_is_permitted_on_the_toy_lane_only(monkeypatch):
    """The toy is a self-contained diagnostic whose pass conditions are read
    inside the run that produces them, so CPU is its own lane rather than a
    backend fallback. Everywhere else the CUDA pin still fails closed -- and it
    fails closed on the toy too if CUDA is asked for and absent."""
    monkeypatch.setattr(process_train.torch.cuda, "is_available", lambda: False)

    process_train.enforce_r30_contract(_contract_config(), _contract_args())

    with pytest.raises(ValueError, match="explicit CUDA"):
        process_train.enforce_r30_contract(
            _contract_config(),
            _contract_args(scenario="alice_bob_asymmetric_cycles", skill_interval=10),
        )
    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        process_train.enforce_r30_contract(
            _contract_config(), _contract_args(device="cuda")
        )
