"""V-K0D training-order plumbing: the counter-based order schedule (A-VD-4),
the canonical path's inertia (A-VD-7 clause 4), the PPO reuse of the stored
order, the durable order exposure, and the launcher's arm refusals (A-VD-3).

Contract: `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`,
amendments A-VD-3, A-VD-4, A-VD-6, A-VD-7.

The rollout driver below calls the same production functions
`ha_ctse_process/train.py`'s rollout loop calls, in the same order:
`vk0d_pre_call_check_index` before the call, `maybe_assign_skills` with the
`agent_order` the policy resolves to, `vk0d_record_committed_order` after it,
and `record_environment_step` for the primitive step. It does not run a real
environment -- the toy's observations are zero-signal by construction (see
`config_d7_2b_toy_learned_keep.py`) and nothing the order schedule touches
depends on observation or reward content -- so a tiny synthetic step is a real
exercise of the counted code paths rather than a mock of them. `num_envs=4`
(never width 1 or 2, `docs/project/AGENT_CONTEXT.md`) keeps the identity space
genuinely multi-environment while staying proof-sized.

What each guard would catch is stated where it is not obvious. The two the
whole task rests on:

* `test_canonical_policy_never_reaches_the_order_stream` goes red the moment
  the canonical path evaluates the assignment function or constructs a Philox
  generator -- which is the unit-level form of the run-level digest witness.
* `test_committed_orders_regenerate_from_the_row_identities` goes red if the
  identity the runtime *draws* with ever differs from the identity the
  committed row *records*, which is exactly what would make the offline audit
  mechanism unable to reproduce the schedule.
"""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from config_d7_2b_toy_learned_keep import Config as ReferenceConfig
from config_d7_2b_toy_randorder_keep import Config as ControlConfig
from config_d7_2b_toy_conjugate_keep import Config as PrimaryConfig
from ha_ctse_process import train as process_train
from ha_ctse_process.r30_fixed_clock import KEEP_TOKEN, SET_TOKEN
from ha_ctse_process.standalone_agent import (
    VK0D_ORDER_CANONICAL,
    VK0D_ORDER_REVERSED,
    VK0D_ORDER_STREAM_NONE,
    VK0D_ORDER_STREAM_VERSION,
    StandaloneProcessAgent,
    Vk0dOrderExposure,
    vk0d_order_assignment,
)
from scripts.run_vk0d_training import (
    ARMS,
    validate_arm_identity,
    validate_order_exposure,
)

NUM_ENVS = 4
ROLLOUT_LENGTH = ReferenceConfig.rollout_length  # 40; skill_interval=5 -> 8 checks/env
SEED = 2026080101


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _build_agent(config, *, seed: int = SEED) -> StandaloneProcessAgent:
    torch.manual_seed(seed)
    agent = StandaloneProcessAgent(
        obs_dim=config.obs_dim,
        action_dim=config.action_dim,
        n_agents=config.n_agents,
        config=config,
        device="cpu",
        action_space_type=config.action_space_type,
        num_envs=NUM_ENVS,
    )
    assert agent.r30_enabled
    return agent


def _drive_rollout(agent, config, *, seed: int = SEED, updates: int = 2):
    """`updates` outer updates' worth of primitive steps through the
    production wiring, including the update boundary
    (`truncate_high_rows_for_update` / `start_high_continuations_after_update`)
    that `train.py` runs. The boundary matters here and not only for realism:
    it is the only thing that produces CONTINUATION rows, which advance the
    buffer's `sequence_indices` without being decisions -- exactly the case
    the order-draw exclusion list has to survive."""
    torch.manual_seed(seed)
    randomize = process_train.vk0d_order_randomized(config)
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    observations = [obs for _ in range(NUM_ENVS)]
    states = [None for _ in range(NUM_ENVS)]
    for update in range(updates):
        for step in range(ROLLOUT_LENGTH):
            for env_id in range(NUM_ENVS):
                check_index = process_train.vk0d_pre_call_check_index(agent, env_id)
                agent.maybe_assign_skills(
                    obs,
                    state=None,
                    step=step,
                    env_id=env_id,
                    deterministic=False,
                    agent_order=(
                        vk0d_order_assignment(
                            training_seed=seed,
                            env_id=env_id,
                            episode_id=int(agent.episode_ids[env_id]),
                            check_index=check_index,
                        )
                        if randomize
                        else None
                    ),
                )
                process_train.vk0d_record_committed_order(agent, env_id, check_index)
                agent.record_environment_step(
                    env_id, reward=0.01, next_obs=obs, next_state=None, done=False
                )
        agent.truncate_high_rows_for_update(observations, states)
        agent.segments.flush(reason="update")
        if update + 1 < updates:
            agent.start_high_continuations_after_update(
                observations, states, policy_update=update + 1
            )


def _decision_rows(agent):
    return [row for row in agent.high_check_buffer.rows if bool(row.decision_mask)]


# ---------------------------------------------------------------------------
# 1. The assignment function is pure, stable and actually random
# ---------------------------------------------------------------------------


def test_order_assignment_is_deterministic_for_one_identity():
    first = vk0d_order_assignment(SEED, 3, 11, 7)
    for _ in range(16):
        assert vk0d_order_assignment(SEED, 3, 11, 7) == first
    assert first in (VK0D_ORDER_CANONICAL, VK0D_ORDER_REVERSED)


def test_order_assignment_consumes_no_global_rng_state():
    """The whole V-K0D comparison rests on this: an order draw that moved any
    global stream would shift every model-init / `Categorical.sample` /
    `rand_like` draw on the randomized arm relative to the canonical ones, and
    the A-VD-7 reference digests would stop reproducing. Mutating the draw to
    use `np.random.randint` or `torch.randint` turns this test red."""
    torch.manual_seed(1234)
    np.random.seed(1234)
    torch_state = torch.get_rng_state().clone()
    numpy_state = np.random.get_state()

    for check_index in range(512):
        vk0d_order_assignment(SEED, check_index % 7, check_index % 5, check_index)

    assert torch.equal(torch.get_rng_state(), torch_state)
    after = np.random.get_state()
    assert after[0] == numpy_state[0]
    assert np.array_equal(after[1], numpy_state[1])
    assert after[2:] == numpy_state[2:]


def test_order_assignment_realizes_both_orders_at_about_one_half():
    """A constant or near-constant assignment would satisfy purity and
    determinism while destroying the treatment. 4096 fair draws have
    sigma = 32; the band below is +-6 sigma, so a correct implementation
    effectively never trips it and a biased one does."""
    reversed_count = sum(
        vk0d_order_assignment(SEED, index % 16, index // 16, index)
        == VK0D_ORDER_REVERSED
        for index in range(4096)
    )
    assert 1856 <= reversed_count <= 2240, reversed_count


def test_order_assignment_separates_every_identity_field():
    """Dropping any one field from the key would collapse distinct decisions
    onto a shared assignment. Each pair below differs in exactly one field and
    is required to be resolvable -- checked as "the four neighbours are not
    all equal to the base", which a key that ignored a field could not
    satisfy across the whole sweep."""
    disagreements = {"seed": 0, "env": 0, "episode": 0, "check": 0}
    for index in range(256):
        base = vk0d_order_assignment(SEED, index % 4, index % 3, index)
        disagreements["seed"] += (
            vk0d_order_assignment(SEED + 1, index % 4, index % 3, index) != base
        )
        disagreements["env"] += (
            vk0d_order_assignment(SEED, index % 4 + 1, index % 3, index) != base
        )
        disagreements["episode"] += (
            vk0d_order_assignment(SEED, index % 4, index % 3 + 1, index) != base
        )
        disagreements["check"] += (
            vk0d_order_assignment(SEED, index % 4, index % 3, index + 1) != base
        )
    for field, count in disagreements.items():
        assert count > 0, f"{field} does not enter the assignment key"


def test_order_assignment_is_stable_across_processes():
    """Python's builtin `hash()` is salted per process; a key built from it
    would give a different schedule on every run and no offline regeneration
    could ever reproduce it. Two subprocesses with different PYTHONHASHSEED
    must agree with each other and with this process."""
    program = (
        "import sys; sys.path.insert(0, '.');"
        "from ha_ctse_process.standalone_agent import vk0d_order_assignment as f;"
        "print(''.join(str(f(2026080101, i % 4, i % 3, i)[0]) for i in range(64)))"
    )
    outputs = []
    for hash_seed in ("0", "1", "12345"):
        completed = subprocess.run(
            [sys.executable, "-B", "-c", program],
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PYTHONHASHSEED": hash_seed},
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(completed.stdout.strip())
    in_process = "".join(
        str(vk0d_order_assignment(2026080101, i % 4, i % 3, i)[0]) for i in range(64)
    )
    assert len(set(outputs)) == 1, outputs
    assert outputs[0] == in_process


def test_order_assignment_matches_the_frozen_vk0d_order_1_stream():
    """A regression pin on the frozen stream, not an independent derivation:
    if the key construction or the stream-version tag ever changes, every
    already-recorded `schedule_digest` stops being reproducible, so the change
    must be a deliberate act that also re-freezes these literals."""
    assert vk0d_order_assignment(2026080101, 0, 0, 0) == (1, 0)
    assert vk0d_order_assignment(2026080101, 0, 0, 1) == (0, 1)
    assert vk0d_order_assignment(2026080101, 0, 0, 2) == (1, 0)
    assert vk0d_order_assignment(2026080101, 0, 1, 0) == (1, 0)
    assert vk0d_order_assignment(2026080101, 1, 0, 0) == (1, 0)
    assert vk0d_order_assignment(2026080101, 3, 11, 7) == (0, 1)
    assert vk0d_order_assignment(2026080102, 0, 0, 0) == (1, 0)


# ---------------------------------------------------------------------------
# 2. Canonical-path inertia
# ---------------------------------------------------------------------------


def test_canonical_policy_never_reaches_the_order_stream(monkeypatch):
    """A-VD-7 clause 4, at the unit level. Both the assignment function and
    `numpy.random.Philox` itself are replaced by raising stubs; a canonical
    run must complete without touching either, and every committed row must
    carry the ascending order the pre-V-K0D code produced."""

    def _forbidden(*args, **kwargs):
        raise AssertionError("canonical path constructed or consumed the order stream")

    monkeypatch.setattr(process_train, "vk0d_order_assignment", _forbidden)
    monkeypatch.setattr(np.random, "Philox", _forbidden)

    config = ReferenceConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    rows = _decision_rows(agent)
    assert rows
    assert all(tuple(int(a) for a in row.agent_order) == (0, 1) for row in rows)
    assert agent.vk0d_order_exposure.order_stream_version == VK0D_ORDER_STREAM_NONE


def test_uniform_policy_does_reach_the_order_stream(monkeypatch):
    """Paired positive for the guard above: the same two stubs, under the
    order-randomized config, must be hit. Without this, the canonical test
    could pass because the stubs were never wired in at all."""
    calls: list[tuple] = []

    def _spy(*args, **kwargs):
        calls.append((args, kwargs))
        return VK0D_ORDER_REVERSED

    monkeypatch.setattr(process_train, "vk0d_order_assignment", _spy)

    config = ControlConfig()
    agent = _build_agent(config)
    # The driver reads the assignment function off `process_train`, exactly as
    # the rollout loop does, so the spy stands in the production position.
    _drive_rollout_via_train_namespace(agent, config)

    assert calls, "the order-randomized path never called the assignment function"
    rows = _decision_rows(agent)
    assert rows
    assert all(tuple(int(a) for a in row.agent_order) == (1, 0) for row in rows)


def _drive_rollout_via_train_namespace(agent, config, *, seed: int = SEED):
    """Same as `_drive_rollout`, but resolving the assignment function through
    the `ha_ctse_process.train` namespace so a monkeypatch of that name is
    honoured -- which is where `train.py`'s rollout loop resolves it too."""
    torch.manual_seed(seed)
    randomize = process_train.vk0d_order_randomized(config)
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    for step in range(ROLLOUT_LENGTH):
        for env_id in range(NUM_ENVS):
            check_index = process_train.vk0d_pre_call_check_index(agent, env_id)
            agent.maybe_assign_skills(
                obs,
                state=None,
                step=step,
                env_id=env_id,
                deterministic=False,
                agent_order=(
                    process_train.vk0d_order_assignment(
                        training_seed=seed,
                        env_id=env_id,
                        episode_id=int(agent.episode_ids[env_id]),
                        check_index=check_index,
                    )
                    if randomize
                    else None
                ),
            )
            process_train.vk0d_record_committed_order(agent, env_id, check_index)
            agent.record_environment_step(
                env_id, reward=0.01, next_obs=obs, next_state=None, done=False
            )


def test_order_policy_resolution_refuses_an_unknown_policy():
    config = SimpleNamespace(r30_training_order_policy="every_other_check")
    with pytest.raises(ValueError, match="r30_training_order_policy"):
        process_train.vk0d_order_randomized(config)


def test_all_three_arm_configs_resolve_their_frozen_policy():
    assert process_train.vk0d_order_randomized(ReferenceConfig()) is False
    assert process_train.vk0d_order_randomized(PrimaryConfig()) is False
    assert process_train.vk0d_order_randomized(ControlConfig()) is True


# ---------------------------------------------------------------------------
# 3. Schedule regeneration from the committed row identities
# ---------------------------------------------------------------------------


def test_committed_orders_regenerate_from_the_row_identities():
    """The A-VD-4 audit mechanism. The runtime draws with the identity read
    *before* the call (`sequence_indices[env_id]`, `episode_ids[env_id]`);
    this regenerates from the identity the committed row *records*
    (`row.sequence_index`, `row.episode_id`). They are different sources, so
    an off-by-one in the pre-call index, a wrong episode counter, or a draw
    keyed on the call rather than on the decision all go red here."""
    config = ControlConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    rows = _decision_rows(agent)
    assert len(rows) >= 8 * NUM_ENVS - NUM_ENVS

    observed = [tuple(int(a) for a in row.agent_order) for row in rows]
    regenerated = [
        vk0d_order_assignment(
            training_seed=SEED,
            env_id=int(row.env_id),
            episode_id=int(row.episode_id),
            check_index=int(row.sequence_index),
        )
        for row in rows
    ]
    assert observed == regenerated
    # The comparison is only informative if the schedule actually varied.
    assert VK0D_ORDER_CANONICAL in observed
    assert VK0D_ORDER_REVERSED in observed


def test_corrupting_one_scheduled_order_breaks_the_regeneration_check():
    """Planted negative for the guard above: one row's stored order is
    flipped, and the same comparison must reject the schedule. Without this,
    the equality above could be an artefact of both sides being empty or
    constant."""
    config = ControlConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    rows = _decision_rows(agent)
    victim = rows[len(rows) // 2]
    victim.agent_order = np.asarray(
        VK0D_ORDER_REVERSED
        if tuple(int(a) for a in victim.agent_order) == VK0D_ORDER_CANONICAL
        else VK0D_ORDER_CANONICAL,
        dtype=np.int64,
    )

    observed = [tuple(int(a) for a in row.agent_order) for row in rows]
    regenerated = [
        vk0d_order_assignment(
            SEED, int(row.env_id), int(row.episode_id), int(row.sequence_index)
        )
        for row in rows
    ]
    assert observed != regenerated


def test_non_due_calls_draw_no_assignment():
    """A-VD-4's exclusion list, first half. `skill_interval=5` means four of
    every five per-environment calls are non-due; the recorder must count only
    the committed decision rows, so the exposure total must equal the number
    of decision rows and NOT the number of `maybe_assign_skills` calls. A
    recorder keyed on the call rather than on the commit lands on `calls`."""
    config = ControlConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config, updates=2)

    calls = 2 * ROLLOUT_LENGTH * NUM_ENVS
    decisions = len(_decision_rows(agent))

    assert 0 < decisions < calls
    assert decisions == 2 * (ROLLOUT_LENGTH // ReferenceConfig.skill_interval) * NUM_ENVS
    assert agent.vk0d_order_exposure.completed_sequence_total == decisions


def test_continuation_rows_are_not_counted_as_order_assignments():
    """A-VD-4's exclusion list, second half. At the frozen rollout length the
    clock lands exactly on a check boundary, so continuation rows never occur;
    this drives the boundary mid-interval on purpose to manufacture them, and
    requires that a continuation row -- which advances the buffer's
    `sequence_indices` without being a decision -- neither draws nor is
    counted."""
    config = ControlConfig()
    agent = _build_agent(config)
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    observations = [obs for _ in range(NUM_ENVS)]
    states = [None for _ in range(NUM_ENVS)]

    torch.manual_seed(SEED)
    for step in range(3):  # 3 < skill_interval=5: the boundary lands mid-interval
        for env_id in range(NUM_ENVS):
            check_index = process_train.vk0d_pre_call_check_index(agent, env_id)
            agent.maybe_assign_skills(
                obs,
                state=None,
                step=step,
                env_id=env_id,
                deterministic=False,
                agent_order=vk0d_order_assignment(
                    SEED, env_id, int(agent.episode_ids[env_id]), check_index
                ),
            )
            process_train.vk0d_record_committed_order(agent, env_id, check_index)
            agent.record_environment_step(
                env_id, reward=0.01, next_obs=obs, next_state=None, done=False
            )
    agent.truncate_high_rows_for_update(observations, states)
    agent.segments.flush(reason="update")
    total_after_rollout = agent.vk0d_order_exposure.completed_sequence_total

    agent.start_high_continuations_after_update(observations, states, policy_update=1)
    pending = [row for row in agent.high_check_buffer.pending if row is not None]
    assert len(pending) == NUM_ENVS
    assert all(not bool(row.decision_mask) for row in pending), (
        "the update boundary did not open continuation rows"
    )
    assert agent.vk0d_order_exposure.completed_sequence_total == total_after_rollout

    # The continuation rows consumed sequence indices; the next real decision
    # must still regenerate from the identity its own row records.
    for step in range(3, 8):
        for env_id in range(NUM_ENVS):
            check_index = process_train.vk0d_pre_call_check_index(agent, env_id)
            agent.maybe_assign_skills(
                obs,
                state=None,
                step=step,
                env_id=env_id,
                deterministic=False,
                agent_order=vk0d_order_assignment(
                    SEED, env_id, int(agent.episode_ids[env_id]), check_index
                ),
            )
            process_train.vk0d_record_committed_order(agent, env_id, check_index)
            agent.record_environment_step(
                env_id, reward=0.01, next_obs=obs, next_state=None, done=False
            )

    closed_continuations = [
        row for row in agent.high_check_buffer.rows if not bool(row.decision_mask)
    ]
    assert closed_continuations
    # The second batch's decision rows are still pending (nothing has closed
    # them yet), so both the closed and the pending decision rows count.
    decisions = _decision_rows(agent) + [
        row
        for row in agent.high_check_buffer.pending
        if row is not None and bool(row.decision_mask)
    ]
    assert agent.vk0d_order_exposure.completed_sequence_total == len(decisions)
    for row in decisions:
        assert tuple(int(a) for a in row.agent_order) == vk0d_order_assignment(
            SEED, int(row.env_id), int(row.episode_id), int(row.sequence_index)
        )


# ---------------------------------------------------------------------------
# 4. PPO reuses the stored order
# ---------------------------------------------------------------------------


def test_high_ppo_evaluates_each_row_under_its_stored_order():
    """`evaluate_sequence` must consume the committed order, never re-derive
    it. The rows carry a mixed schedule, so an implementation that passed an
    ascending `arange` (or re-drew) would be caught by the first epoch's
    observed order list."""
    config = ControlConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    expected = [tuple(int(a) for a in row.agent_order) for row in _decision_rows(agent)]
    assert VK0D_ORDER_CANONICAL in expected and VK0D_ORDER_REVERSED in expected

    observed: list[tuple[int, ...]] = []
    original = agent.high.evaluate_sequence

    def _spy(*args, **kwargs):
        observed.append(tuple(int(a) for a in kwargs["agent_order"].reshape(-1)))
        return original(*args, **kwargs)

    agent.high.evaluate_sequence = _spy
    try:
        agent.begin_high_epoch_pass_accounting()
        try:
            agent.update_high_from_checks(total_steps=ROLLOUT_LENGTH * NUM_ENVS)
        finally:
            agent.finalize_high_epoch_pass_accounting(None)
    finally:
        agent.high.evaluate_sequence = original

    assert observed, "the high PPO update never evaluated a sequence"
    epochs = len(observed) // len(expected)
    assert epochs >= 1 and len(observed) == epochs * len(expected)
    for epoch in range(epochs):
        assert observed[epoch * len(expected) : (epoch + 1) * len(expected)] == expected


def test_stored_order_is_consequential_and_reproduces_the_sampled_logprob():
    """Makes the guard above non-vacuous: the order genuinely changes the
    factorization. `evaluate_sequence` under the SAMPLED order must reproduce
    the sampler's own recorded per-token log-probabilities -- an independent
    source of truth, produced by `act_sequence`, not recomputed by the
    assertion -- while the swapped order must not."""
    config = ControlConfig()
    agent = _build_agent(config)
    policy = agent.high
    device = agent.device

    # The exact context `_r30_maybe_assign_skills` builds, taken from the
    # agent's own builder rather than from hand-shaped zero tensors, so the
    # replay below exercises the real input geometry.
    joint_obs_np = agent._joint_obs_array(
        np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    )
    state_arr = agent._state_array(None, joint_obs_np)
    with torch.no_grad():
        context = agent._r30_context_tensors(state_arr, joint_obs_np)
    joint_t, compact, team_vector = context[1], context[2], context[4]
    joint_obs = joint_t.squeeze(0)
    prev_skills = torch.tensor([0, 1], dtype=torch.long, device=device)
    prev_ages = torch.tensor([3, 4], dtype=torch.long, device=device)
    prev_active = torch.tensor([True, True], dtype=torch.bool, device=device)

    torch.manual_seed(7)
    sample = policy.act_sequence(
        joint_obs=joint_obs,
        compact=compact,
        team_vector=team_vector,
        prev_skills=prev_skills,
        prev_ages=prev_ages,
        prev_active=prev_active,
        agent_order=torch.tensor(VK0D_ORDER_REVERSED, dtype=torch.long, device=device),
        deterministic=False,
    )

    def _replay(order):
        logp, _entropy = policy.evaluate_sequence(
            joint_obs=joint_obs,
            compact=compact,
            team_vector=team_vector,
            prev_skills=prev_skills,
            prev_ages=prev_ages,
            prev_active=prev_active,
            agent_order=torch.tensor(order, dtype=torch.long, device=device),
            token_kind=sample.token_kind,
            set_skill=sample.set_skill,
        )
        return logp.detach().reshape(-1)

    same = _replay(VK0D_ORDER_REVERSED)
    assert torch.allclose(same, sample.token_logp.detach().reshape(-1), atol=1e-6)

    swapped = _replay(VK0D_ORDER_CANONICAL)
    assert not torch.allclose(
        swapped, sample.token_logp.detach().reshape(-1), atol=1e-6
    ), (
        "evaluating under the wrong order reproduced the sampled log-probs; "
        "the PPO order-reuse guard would be vacuous"
    )


# ---------------------------------------------------------------------------
# 5. Durable order exposure (A-VD-4)
# ---------------------------------------------------------------------------


def test_order_exposure_counts_and_identities_on_a_randomized_run():
    config = ControlConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    exposure = agent.vk0d_order_exposure
    rows = _decision_rows(agent)
    observed = [tuple(int(a) for a in row.agent_order) for row in rows]

    assert exposure.order_stream_version == VK0D_ORDER_STREAM_VERSION
    assert exposure.completed_sequence_total == len(rows)
    assert exposure.completed_canonical_sequences == observed.count(
        VK0D_ORDER_CANONICAL
    )
    assert exposure.completed_reversed_sequences == observed.count(VK0D_ORDER_REVERSED)
    assert exposure.agent0_first_count == exposure.completed_canonical_sequences
    assert exposure.agent1_first_count == exposure.completed_reversed_sequences
    assert (
        exposure.completed_canonical_sequences + exposure.completed_reversed_sequences
        == exposure.completed_sequence_total
    )
    assert exposure.completed_reversed_sequences > 0
    assert exposure.identities_ok()
    assert len(exposure.schedule_digest()) == 64


def test_canonical_run_carries_no_reversed_sequence_and_no_stream_identity():
    config = ReferenceConfig()
    agent = _build_agent(config)
    _drive_rollout(agent, config)

    exposure = agent.vk0d_order_exposure
    assert exposure.order_stream_version == VK0D_ORDER_STREAM_NONE
    assert exposure.completed_reversed_sequences == 0
    assert exposure.agent1_first_count == 0
    assert exposure.completed_sequence_total > 0
    assert exposure.identities_ok()


def test_schedule_digest_is_order_sensitive_and_content_sensitive():
    """The digest must commit to the schedule, not merely to its tallies: two
    records with the same counts but a different assignment sequence, and two
    with the same sequence but different identities, must not collide."""
    base = Vk0dOrderExposure(order_stream_version=VK0D_ORDER_STREAM_VERSION)
    permuted = Vk0dOrderExposure(order_stream_version=VK0D_ORDER_STREAM_VERSION)
    relabelled = Vk0dOrderExposure(order_stream_version=VK0D_ORDER_STREAM_VERSION)
    orders = [VK0D_ORDER_CANONICAL, VK0D_ORDER_REVERSED, VK0D_ORDER_CANONICAL]
    permutation = [VK0D_ORDER_REVERSED, VK0D_ORDER_CANONICAL, VK0D_ORDER_CANONICAL]
    for index, order in enumerate(orders):
        base.record_committed_sequence(
            env_id=0, episode_id=0, check_index=index, assigned_order=order
        )
        relabelled.record_committed_sequence(
            env_id=1, episode_id=0, check_index=index, assigned_order=order
        )
    for index, order in enumerate(permutation):
        permuted.record_committed_sequence(
            env_id=0, episode_id=0, check_index=index, assigned_order=order
        )

    assert base.completed_canonical_sequences == permuted.completed_canonical_sequences
    assert base.completed_reversed_sequences == permuted.completed_reversed_sequences
    assert base.schedule_digest() != permuted.schedule_digest()
    assert base.schedule_digest() != relabelled.schedule_digest()


def test_tampered_exposure_counters_fail_the_identity_helper():
    """Planted negatives for `identities_ok`: each of the three identities is
    broken in turn and must be what rejects the record."""
    exposure = Vk0dOrderExposure(order_stream_version=VK0D_ORDER_STREAM_VERSION)
    for index in range(6):
        exposure.record_committed_sequence(
            env_id=0,
            episode_id=0,
            check_index=index,
            assigned_order=VK0D_ORDER_CANONICAL if index % 2 else VK0D_ORDER_REVERSED,
        )
    assert exposure.identities_ok()

    exposure.completed_reversed_sequences += 1
    assert not exposure.identities_ok()
    exposure.completed_reversed_sequences -= 1

    exposure.agent1_first_count += 1
    assert not exposure.identities_ok()
    exposure.agent1_first_count -= 1

    exposure.order_stream_version = VK0D_ORDER_STREAM_NONE
    assert not exposure.identities_ok(), (
        "a canonical-labelled record carrying reversed sequences was accepted"
    )


def test_exposure_refuses_a_non_permutation_order():
    exposure = Vk0dOrderExposure(order_stream_version=VK0D_ORDER_STREAM_VERSION)
    with pytest.raises(ValueError, match="two two-agent orders"):
        exposure.record_committed_sequence(
            env_id=0, episode_id=0, check_index=0, assigned_order=(0, 0)
        )


# ---------------------------------------------------------------------------
# 6. Launcher arm validation (A-VD-3) and order-exposure audit (A-VD-4)
# ---------------------------------------------------------------------------


def test_launcher_accepts_each_frozen_arm():
    for arm, spec in ARMS.items():
        config = __import__(spec["config"], fromlist=["Config"]).Config()
        assert validate_arm_identity(arm, config) == [], arm


def test_launcher_refuses_a_combination_outside_the_frozen_three():
    """The forbidden fourth cell of the 2x2: the conjugate encoder trained
    under a randomized order. A-VD-3 requires PRIMARY to train canonical, so
    this combination is not a V-K0D arm even though both field values are
    individually legal."""
    rogue = SimpleNamespace(
        high_controller="r30_fixed_clock_ar_edit_conjugate",
        r30_training_order_policy="uniform_per_check",
    )
    violations = validate_arm_identity("primary", rogue)
    assert violations
    assert any("r30_training_order_policy" in v for v in violations)
    assert any("frozen A-VD-3 combinations" in v for v in violations)


def test_launcher_refuses_an_arm_whose_config_lost_the_order_field():
    stripped = SimpleNamespace(high_controller="r30_fixed_clock_ar_edit")
    violations = validate_arm_identity("reference", stripped)
    assert violations
    assert any("r30_training_order_policy: missing" in v for v in violations)


def test_launcher_refuses_a_config_relabelled_as_another_arm():
    reference = ReferenceConfig()
    violations = validate_arm_identity("control", reference)
    assert violations
    assert any("requires 'uniform_per_check'" in v for v in violations)


def _order_block(**overrides):
    block = {
        "order_stream_version": VK0D_ORDER_STREAM_NONE,
        "r30_training_order_policy": "canonical",
        "schedule_digest": "a" * 64,
        "completed_canonical_sequences": {"value": 10, "source": "training_accumulator"},
        "completed_reversed_sequences": {"value": 0, "source": "training_accumulator"},
        "agent0_first_count": {"value": 10, "source": "training_accumulator"},
        "agent1_first_count": {"value": 0, "source": "training_accumulator"},
        "completed_sequence_total": {"value": 10, "source": "training_accumulator"},
    }
    block.update(overrides)
    return block


def test_order_exposure_audit_passes_a_well_formed_canonical_arm():
    assert validate_order_exposure(_order_block(), "reference") == []
    assert validate_order_exposure(_order_block(), "primary") == []


def test_order_exposure_audit_refuses_a_canonical_arm_that_consumed_the_stream():
    block = _order_block(
        order_stream_version=VK0D_ORDER_STREAM_VERSION,
        completed_reversed_sequences={"value": 4, "source": "training_accumulator"},
        completed_canonical_sequences={"value": 6, "source": "training_accumulator"},
        agent0_first_count={"value": 6, "source": "training_accumulator"},
        agent1_first_count={"value": 4, "source": "training_accumulator"},
    )
    violations = validate_order_exposure(block, "reference")
    assert any("order_stream_version" in v for v in violations)
    assert any("completed_reversed_sequences" in v for v in violations)


def test_order_exposure_audit_refuses_a_control_arm_whose_schedule_never_fired():
    """A rate is evidence only if the mechanism fired: an order-randomized arm
    reporting zero reversed sequences is a silent no-op, not a control."""
    block = _order_block(
        order_stream_version=VK0D_ORDER_STREAM_VERSION,
        r30_training_order_policy="uniform_per_check",
    )
    violations = validate_order_exposure(block, "control")
    assert any("realized no reversed sequence" in v for v in violations)


def test_order_exposure_audit_refuses_a_broken_count_identity():
    block = _order_block(
        completed_canonical_sequences={"value": 9, "source": "training_accumulator"}
    )
    violations = validate_order_exposure(block, "reference")
    assert any("N01 + N10 != completed_sequence_total" in v for v in violations)


def test_order_exposure_audit_refuses_an_inadmissible_source_label():
    block = _order_block(
        completed_sequence_total={"value": 10, "source": "derived_from_budget"}
    )
    violations = validate_order_exposure(block, "reference")
    assert any("inadmissible label" in v for v in violations)


def test_order_exposure_audit_refuses_an_empty_schedule_digest():
    import hashlib

    block = _order_block(schedule_digest=hashlib.sha256(b"").hexdigest())
    violations = validate_order_exposure(block, "reference")
    assert any("schedule_digest" in v for v in violations)
