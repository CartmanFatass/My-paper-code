"""V-K0B rerun exposure instrumentation (W6-D1) and its frozen amendments.

`docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md` W6-D1, as
amended by A-W6-1 (shared-optimizer parameter-coverage certificate), A-W6-2
(exhaustive high-pass status partition), A-W6-3 (completed-sequence
definition) and A-W6-5 (immutable, source-labelled exposure evidence). The
counters this pins down never gate training -- they observe the standalone
R30 training path used by `config_d7_2b_toy_learned_keep.Config` and record
exactly what happened, including a skip or an abort.

The driver below calls the same production methods `ha_ctse_process/train.py`
calls, in the same order, on a real `StandaloneProcessAgent` built from the
real V-K0B config -- `maybe_assign_skills` / `record_environment_step` every
primitive step, `truncate_high_rows_for_update` and
`start_high_continuations_after_update` at the update boundary, and
`update_high_from_checks` wrapped by the same
`begin_high_epoch_pass_accounting` / `finalize_high_epoch_pass_accounting`
pair `train.py`'s call site uses. It does not run a real environment: the
toy's own observations are zero-signal by construction (see
`config_d7_2b_toy_learned_keep.py`), and nothing this instrumentation touches
depends on reward or observation content, so a tiny synthetic step is a real
exercise of the counted code paths rather than a mock of them. Two updates at
`num_envs=4` (never width 1 or 2 -- see `docs/project/AGENT_CONTEXT.md`) keep
this proof-sized while still driving `high_ppo_epochs=3` real PPO passes per
update through the real `high_opt`.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from config_d7_2b_toy_learned_keep import Config
from ha_ctse_process import train as process_train
from ha_ctse_process.standalone_agent import (
    StandaloneProcessAgent,
    vk0b_high_optimizer_parameter_coverage,
)

NUM_ENVS = 4
ROLLOUT_LENGTH = Config.rollout_length  # 40, matches skill_interval=5: 8 checks/env/update


class _OptimizerDouble:
    """A minimal stand-in exposing only what
    `vk0b_high_optimizer_parameter_coverage` reads (`param_groups`, `state`),
    so a negative witness can tamper membership or state without touching a
    live `torch.optim.Adam` or the agent that owns it."""

    def __init__(self, param_groups, state):
        self.param_groups = param_groups
        self.state = state


def _assert_state_dicts_equal(a, b, path: str = "state") -> None:
    if isinstance(a, dict):
        assert isinstance(b, dict) and set(a) == set(b), path
        for key in a:
            _assert_state_dicts_equal(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, (list, tuple)):
        assert isinstance(b, (list, tuple)) and len(a) == len(b), path
        for index, (left, right) in enumerate(zip(a, b)):
            _assert_state_dicts_equal(left, right, f"{path}[{index}]")
    elif torch.is_tensor(a):
        assert torch.is_tensor(b) and torch.equal(a, b), path
    else:
        assert a == b, path


def _build_agent(*, num_envs: int = NUM_ENVS, seed: int) -> StandaloneProcessAgent:
    torch.manual_seed(seed)
    agent = StandaloneProcessAgent(
        obs_dim=Config.obs_dim,
        action_dim=Config.action_dim,
        n_agents=Config.n_agents,
        config=Config(),
        device="cpu",
        action_space_type=Config.action_space_type,
        num_envs=num_envs,
    )
    assert agent.r30_enabled
    assert agent.high_ppo_epochs == 3
    return agent


def _drive_one_update(agent: StandaloneProcessAgent, *, num_envs: int, seed: int) -> None:
    """One outer update's worth of primitive steps, calling exactly the two
    per-step methods train.py's rollout loop calls for the R30 path."""

    torch.manual_seed(seed)
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    for step in range(ROLLOUT_LENGTH):
        reward = 0.01 * (step + 1)
        for env_id in range(num_envs):
            agent.maybe_assign_skills(
                obs, state=None, step=step, env_id=env_id, deterministic=False
            )
            agent.record_environment_step(
                env_id, reward=reward, next_obs=obs, next_state=None, done=False
            )
    observations = [obs for _ in range(num_envs)]
    states = [None for _ in range(num_envs)]
    agent.truncate_high_rows_for_update(observations, states)
    agent.segments.flush(reason="update")


def _run_high_update(agent: StandaloneProcessAgent, *, total_steps: int) -> dict:
    """Exactly the accounting wrapper `train.py`'s call site around
    `agent.update_high_from_checks` uses (A-W6-2): begin before the call,
    finalize in both the success and the exception path, never suppressing
    what update_high_from_checks itself does or raises."""

    agent.begin_high_epoch_pass_accounting()
    try:
        metrics = agent.update_high_from_checks(total_steps=total_steps)
    except Exception as exc:  # pragma: no cover - exercised only if training raises
        agent.finalize_high_epoch_pass_accounting(exc)
        raise
    agent.finalize_high_epoch_pass_accounting(None)
    return metrics


def _drive_updates(
    agent: StandaloneProcessAgent, *, num_updates: int, num_envs: int, base_seed: int
) -> None:
    for update in range(num_updates):
        _drive_one_update(agent, num_envs=num_envs, seed=base_seed + update)
        _run_high_update(agent, total_steps=(update + 1) * ROLLOUT_LENGTH * num_envs)
        observations = [
            np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
            for _ in range(num_envs)
        ]
        states = [None for _ in range(num_envs)]
        agent.start_high_continuations_after_update(
            observations, states, policy_update=update + 2
        )


# ---------------------------------------------------------------------------
# Positive path
# ---------------------------------------------------------------------------


def test_two_updates_exact_exposure_partition_and_token_identity(monkeypatch):
    agent = _build_agent(seed=20260801)

    # Independent ground truth for high_check_sequences_completed: a spy on
    # the real buffer commit method, counted outside the instrumentation
    # under test.
    commit_calls = {"count": 0}
    original_start_decision = agent.high_check_buffer.start_decision

    def _spy_start_decision(**kwargs):
        commit_calls["count"] += 1
        return original_start_decision(**kwargs)

    monkeypatch.setattr(agent.high_check_buffer, "start_decision", _spy_start_decision)

    num_updates = 2
    _drive_updates(agent, num_updates=num_updates, num_envs=NUM_ENVS, base_seed=777)

    exposure = agent.exposure
    expected_attempted = num_updates * agent.high_ppo_epochs
    assert exposure.high_epoch_passes_attempted == expected_attempted
    assert exposure.high_epoch_passes_stepped == expected_attempted
    assert exposure.high_epoch_passes_skipped == 0
    assert exposure.high_epoch_passes_aborted == 0
    assert exposure.epoch_pass_partition_ok()
    assert exposure.high_epoch_pass_skip_reasons == []
    assert exposure.high_epoch_pass_abort_reasons == []

    assert commit_calls["count"] > 0
    assert exposure.high_check_sequences_completed == commit_calls["count"]
    assert exposure.high_check_sequences_failed_or_skipped == 0
    assert exposure.token_identity_ok()
    assert (
        exposure.agent_tokens_keep + exposure.agent_tokens_set
        == 2 * exposure.high_check_sequences_completed
    )

    # A-W6-1: the coverage certificate on the real high_opt/high/high_value,
    # after real optimizer.step() calls -- not a mock optimizer.
    coverage = agent.high_optimizer_coverage_certificate()
    assert coverage["high_optimizer_parameter_coverage_ok"] is True
    assert coverage["high_optimizer_steps_shared"] == expected_attempted
    assert coverage["high_optimizer_step_min"] == coverage["high_optimizer_step_max"]
    actor_params = list(agent.high.parameters())
    value_params = list(agent.high_value.parameters())
    assert coverage["high_actor_parameter_count_expected"] == len(actor_params)
    assert coverage["high_actor_parameter_count_with_step_state"] == len(actor_params)
    assert coverage["high_value_parameter_count_expected"] == len(value_params)
    assert coverage["high_value_parameter_count_with_step_state"] == len(value_params)

    low_steps, low_source = agent.low_level_optimizer_exposure()
    # config_d7_2b_toy_learned_keep sets r39_toy_fixed_skill_primitives=True:
    # no low optimizer exists to step at all.
    assert agent.low_opt is None
    assert agent.low_actor_opt is None
    assert agent.low_critic_opt is None
    assert low_steps == 0
    assert low_source == "checkpoint_optimizer_absence"


ADMISSIBLE_SOURCES = {
    "runtime_counter",
    "training_accumulator",
    "optimizer_state",
    "checkpoint_optimizer_absence",
}

WRAPPED_EXPOSURE_FIELDS = (
    "environment_interactions",
    "completed_outer_updates",
    "high_optimizer_steps_shared",
    "high_actor_optimizer_steps",
    "high_value_optimizer_steps",
    "high_actor_parameter_count_expected",
    "high_actor_parameter_count_with_step_state",
    "high_value_parameter_count_expected",
    "high_value_parameter_count_with_step_state",
    "high_optimizer_step_min",
    "high_optimizer_step_max",
    "high_optimizer_parameter_coverage_ok",
    "high_check_sequences_completed",
    "high_check_sequences_failed_or_skipped",
    "agent_tokens_keep",
    "agent_tokens_set",
    "high_epoch_passes_attempted",
    "high_epoch_passes_stepped",
    "high_epoch_passes_skipped",
    "high_epoch_passes_aborted",
    "low_level_optimizer_steps",
)


def test_manifest_actual_exposure_block_matches_frozen_schema(tmp_path):
    agent = _build_agent(seed=555555)
    _drive_updates(agent, num_updates=1, num_envs=NUM_ENVS, base_seed=222)

    args = SimpleNamespace(log_dir=str(tmp_path))
    process_train.export_run_manifest(
        args,
        Config(),
        env=None,
        agent=agent,
        total_steps=ROLLOUT_LENGTH * NUM_ENVS,
        update_idx=1,
        mode="train",
    )

    manifest_path = tmp_path / "metadata" / "run_manifest.json"
    assert manifest_path.exists()
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    block = manifest["actual_exposure"]

    assert block["actual_exposure_schema"] == "vk0b-exposure-1"
    assert block["high_optimizer_semantics"] == "SHARED_ACTOR_VALUE_OPTIMIZER"
    assert isinstance(block["high_epoch_pass_skip_reasons"], list)
    assert isinstance(block["high_epoch_pass_abort_reasons"], list)
    for field in WRAPPED_EXPOSURE_FIELDS:
        entry = block[field]
        assert set(entry.keys()) == {"value", "source"}, field
        assert entry["source"] in ADMISSIBLE_SOURCES, field

    # The three semantic views of the one shared counter must actually agree,
    # not merely all be present.
    assert (
        block["high_optimizer_steps_shared"]["value"]
        == block["high_actor_optimizer_steps"]["value"]
        == block["high_value_optimizer_steps"]["value"]
        == agent.exposure.high_epoch_passes_stepped
    )
    assert block["high_optimizer_parameter_coverage_ok"]["value"] is True
    assert block["low_level_optimizer_steps"] == {
        "value": 0,
        "source": "checkpoint_optimizer_absence",
    }
    assert block["environment_interactions"] == {
        "value": ROLLOUT_LENGTH * NUM_ENVS,
        "source": "runtime_counter",
    }
    assert block["completed_outer_updates"] == {
        "value": 1,
        "source": "runtime_counter",
    }
    assert (
        block["high_check_sequences_completed"]["value"]
        == agent.exposure.high_check_sequences_completed
        > 0
    )


# ---------------------------------------------------------------------------
# Negative witnesses (Pro-named)
# ---------------------------------------------------------------------------


def test_negative_witness_missing_actor_parameter_breaks_coverage():
    """(a): remove one actor parameter from the optimizer's param_groups in a
    test double -- coverage_ok must flip True -> False."""

    agent = _build_agent(seed=90909)
    _drive_updates(agent, num_updates=1, num_envs=NUM_ENVS, base_seed=44)

    actor_params = list(agent.high.parameters())
    value_params = list(agent.high_value.parameters())
    assert len(actor_params) > 1

    baseline = vk0b_high_optimizer_parameter_coverage(
        actor_params, value_params, agent.high_opt
    )
    assert baseline["high_optimizer_parameter_coverage_ok"] is True  # green

    missing = actor_params[0]
    patched_groups = [
        {"params": [p for p in group["params"] if p is not missing]}
        for group in agent.high_opt.param_groups
    ]
    tampered_opt = _OptimizerDouble(patched_groups, agent.high_opt.state)
    tampered = vk0b_high_optimizer_parameter_coverage(
        actor_params, value_params, tampered_opt
    )
    assert tampered["high_optimizer_parameter_coverage_ok"] is False  # red
    assert tampered["high_actor_parameter_count_expected"] == len(actor_params)
    assert tampered["high_actor_parameter_count_with_step_state"] == len(actor_params) - 1


def test_negative_witness_missing_optimizer_state_breaks_coverage():
    """(b): delete one parameter's optimizer-state step entry -- coverage_ok
    must flip True -> False."""

    agent = _build_agent(seed=90910)
    _drive_updates(agent, num_updates=1, num_envs=NUM_ENVS, base_seed=45)

    actor_params = list(agent.high.parameters())
    value_params = list(agent.high_value.parameters())
    assert len(value_params) >= 1

    baseline = vk0b_high_optimizer_parameter_coverage(
        actor_params, value_params, agent.high_opt
    )
    assert baseline["high_optimizer_parameter_coverage_ok"] is True  # green

    victim = value_params[0]
    tampered_state = dict(agent.high_opt.state)
    del tampered_state[victim]
    tampered_opt = _OptimizerDouble(agent.high_opt.param_groups, tampered_state)
    tampered = vk0b_high_optimizer_parameter_coverage(
        actor_params, value_params, tampered_opt
    )
    assert tampered["high_optimizer_parameter_coverage_ok"] is False  # red
    assert tampered["high_value_parameter_count_expected"] == len(value_params)
    assert tampered["high_value_parameter_count_with_step_state"] == len(value_params) - 1


def test_negative_witness_empty_high_check_rows_is_skipped_normal():
    """(c): a due call to update_high_from_checks with no completed rows to
    process -- the real early-return guard (A-W6-2's exhaustive-partition
    boundary), not a mock. A freshly built agent has never had a check close,
    so this is the guard's genuine natural trigger."""

    agent = _build_agent(seed=1)
    assert agent.high_check_buffer.pop_completed() == []  # sanity: truly empty
    # pop_completed() above already drained it (it was already empty); call
    # the real accounting-wrapped update once more to exercise the guard.
    _run_high_update(agent, total_steps=0)

    exposure = agent.exposure
    assert exposure.high_epoch_passes_skipped == agent.high_ppo_epochs
    assert exposure.high_epoch_passes_stepped == 0
    assert exposure.high_epoch_passes_aborted == 0
    assert exposure.high_epoch_passes_attempted == agent.high_ppo_epochs
    assert exposure.epoch_pass_partition_ok()
    assert exposure.high_epoch_pass_skip_reasons == (
        ["empty_high_check_rows"] * agent.high_ppo_epochs
    )


def test_aborted_high_epoch_passes_are_recorded_on_exception():
    """A-W6-2's third terminal status, ABORTED(reason). An exception inside
    the real PPO epoch loop -- injected via a flaky high_opt.step, not a
    fabricated code path -- must still propagate untouched (counters never
    gate or swallow), and every expected opportunity that did not actually
    STEP must land in ABORTED so the exhaustive partition still holds even
    though train.py's call site could not know in advance how many epochs
    the callee would reach."""

    agent = _build_agent(seed=31415)
    _drive_one_update(agent, num_envs=NUM_ENVS, seed=9)
    original_step = agent.high_opt.step
    calls = {"n": 0}

    def _flaky_step(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("synthetic optimizer failure")
        return original_step(*args, **kwargs)

    agent.high_opt.step = _flaky_step

    with pytest.raises(RuntimeError, match="synthetic optimizer failure"):
        _run_high_update(agent, total_steps=0)

    exposure = agent.exposure
    assert exposure.high_epoch_passes_attempted == agent.high_ppo_epochs
    assert exposure.high_epoch_passes_stepped == 1
    assert exposure.high_epoch_passes_skipped == 0
    assert exposure.high_epoch_passes_aborted == agent.high_ppo_epochs - 1
    assert exposure.epoch_pass_partition_ok()
    assert exposure.high_epoch_pass_abort_reasons == (
        ["exception:RuntimeError"] * (agent.high_ppo_epochs - 1)
    )


def test_negative_witness_tampered_token_counter_breaks_identity():
    """(d): tamper a token counter directly -- the exposed identity helper
    must be what catches keep + set != 2 * completed."""

    agent = _build_agent(seed=2468)
    _drive_updates(agent, num_updates=1, num_envs=NUM_ENVS, base_seed=13)

    assert agent.exposure.high_check_sequences_completed > 0
    assert agent.exposure.token_identity_ok() is True  # green, real production counts

    agent.exposure.agent_tokens_keep += 1  # tamper
    assert agent.exposure.token_identity_ok() is False  # red


# ---------------------------------------------------------------------------
# Noninterference witness (A-W6-6)
# ---------------------------------------------------------------------------


def test_noninterference_instrumentation_toggle_is_byte_identical():
    """With identical seed/config, enabling vs. disabling
    `exposure_instrumentation_enabled` must not move a single sampled token,
    RNG draw, or optimizer/parameter value -- only the counters and manifest
    fields may differ. This is the toggle Gate-B's noninterference witness
    asks for; if the counters ever gated or perturbed training, this
    comparison would diverge."""

    def _run(*, instrumentation_enabled: bool, agent_seed: int, drive_seed: int):
        agent = _build_agent(seed=agent_seed)
        agent.exposure_instrumentation_enabled = instrumentation_enabled

        captured: list[dict[str, np.ndarray]] = []
        original_start_decision = agent.high_check_buffer.start_decision

        def _spy(**kwargs):
            captured.append(
                {
                    field: np.asarray(kwargs[field]).copy()
                    for field in (
                        "token_kind",
                        "set_skill",
                        "token_valid",
                        "old_token_logp",
                        "keep_prob",
                    )
                }
            )
            return original_start_decision(**kwargs)

        agent.high_check_buffer.start_decision = _spy
        _drive_updates(agent, num_updates=2, num_envs=NUM_ENVS, base_seed=drive_seed)
        rng_state = torch.get_rng_state().clone()
        return agent, captured, rng_state

    agent_on, samples_on, rng_on = _run(
        instrumentation_enabled=True, agent_seed=13579, drive_seed=24680
    )
    agent_off, samples_off, rng_off = _run(
        instrumentation_enabled=False, agent_seed=13579, drive_seed=24680
    )

    assert len(samples_on) == len(samples_off) and len(samples_on) > 0
    for left, right in zip(samples_on, samples_off):
        for field in left:
            np.testing.assert_array_equal(left[field], right[field])

    assert torch.equal(rng_on, rng_off)
    _assert_state_dicts_equal(agent_on.high.state_dict(), agent_off.high.state_dict())
    _assert_state_dicts_equal(
        agent_on.high_value.state_dict(), agent_off.high_value.state_dict()
    )
    _assert_state_dicts_equal(
        agent_on.high_opt.state_dict(), agent_off.high_opt.state_dict()
    )

    # The switch really did switch something -- otherwise this comparison
    # would be vacuously true regardless of whether the toggle does anything.
    assert agent_on.exposure.high_check_sequences_completed > 0
    assert agent_off.exposure.high_check_sequences_completed == 0
    assert agent_on.exposure.high_epoch_passes_attempted > 0
    assert agent_off.exposure.high_epoch_passes_attempted == 0
