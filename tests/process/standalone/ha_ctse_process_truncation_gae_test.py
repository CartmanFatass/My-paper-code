"""Terminated vs. truncated boundaries in the low-level GAE.

A terminal state has no future, so its bootstrap is zero.  A truncation is a time limit
imposed from outside the environment: the state still has future value, so the bootstrap
must survive even though advantage credit must not flow across the boundary.  Before
2026-09-17 the trainer collapsed the two into one `done` flag and zeroed the bootstrap for
both, which biases every value target near a time limit.

These tests pin the corrected arithmetic, the mid-rollout case, and the legacy-reproduction
flag.  They assert on ``returns`` rather than ``advantages`` because ``_low_returns``
normalises the advantages before returning them, while the returns are the raw value
targets - which is exactly what the defect corrupted.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process import standalone_train_runner
from ha_ctse_process.standalone_segments import Rollout

from tests.process.standalone.ha_ctse_process_standalone_test import (
    make_agent,
    make_process_config,
)


N_AGENTS = 2
HIDDEN = 8


def _rollout(
    *,
    rewards,
    values,
    env_ids=None,
    terminated=None,
    truncated=None,
    bootstrap_values=None,
    truncation_bootstrap_values=None,
    include_reason_flags=True,
) -> Rollout:
    """A rollout carrying only what ``_low_returns`` reads.

    ``include_reason_flags=False`` omits the terminated/truncated lists entirely, which is
    how a caller that only knows about ``dones`` reaches the collapsed fallback.
    """

    rows = len(rewards)
    terminated = [False] * rows if terminated is None else list(terminated)
    truncated = [False] * rows if truncated is None else list(truncated)
    dones = [bool(a or b) for a, b in zip(terminated, truncated)]
    rollout = Rollout(
        env_ids=list(range(rows)) if env_ids is None else list(env_ids),
        rewards=[np.full(N_AGENTS, float(value), dtype=np.float32) for value in rewards],
        values=[np.full(N_AGENTS, float(value), dtype=np.float32) for value in values],
        dones=dones,
        bootstrap_values=dict(bootstrap_values or {}),
        truncation_bootstrap_values={
            int(row): np.full(N_AGENTS, float(value), dtype=np.float32)
            for row, value in (truncation_bootstrap_values or {}).items()
        },
    )
    if env_ids is None:
        rollout.env_ids = [0] * rows
    if include_reason_flags:
        rollout.terminated = terminated
        rollout.truncated = truncated
    return rollout


def _agent(**config_overrides):
    config = make_process_config(**config_overrides)
    agent = make_agent(config=config)
    return agent


def _returns(agent, rollout) -> np.ndarray:
    returns, _advantages, _values, _env_ids = agent._low_returns(rollout)
    # Every agent row is identical in these fixtures, so collapse to one column.
    assert np.allclose(returns, returns[:, :1])
    return returns[:, 0].astype(np.float64)


# --------------------------------------------------------------------------------------
# Termination vs. truncation
# --------------------------------------------------------------------------------------


def test_termination_zeroes_the_bootstrap():
    """A real terminal state's value target is its own reward and nothing more."""

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        terminated=[False, False, True],
    )
    returns = _returns(agent, rollout)
    # delta = r - V, return = delta + V = r.
    assert returns[2] == pytest.approx(3.0)


def test_truncation_preserves_the_bootstrap():
    """A time limit is not a terminal state: V(s') still enters the target."""

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        truncated=[False, False, True],
        truncation_bootstrap_values={2: 40.0},
    )
    returns = _returns(agent, rollout)
    assert returns[2] == pytest.approx(3.0 + agent.gamma * 40.0)


def test_the_two_boundaries_differ_by_exactly_the_discounted_bootstrap():
    """The crisp statement of the fix, with everything else held identical."""

    agent = _agent()
    shared = {"rewards": [1.0, 2.0, 3.0], "values": [10.0, 20.0, 30.0]}
    terminated = _returns(
        agent, _rollout(**shared, terminated=[False, False, True])
    )
    truncated = _returns(
        agent,
        _rollout(
            **shared,
            truncated=[False, False, True],
            truncation_bootstrap_values={2: 40.0},
        ),
    )
    assert truncated[2] - terminated[2] == pytest.approx(agent.gamma * 40.0)

    # The boundary row's own TD error belongs to the current episode, so the correction
    # propagates backwards through the GAE recursion with the usual (gamma * lambda)^k
    # decay. That is the quantitative size of the defect: earlier rows were wrong too,
    # not just the boundary row.
    decay = agent.gamma * agent.low_gae_lambda
    correction = agent.gamma * 40.0
    assert truncated[1] - terminated[1] == pytest.approx(decay * correction)
    assert truncated[0] - terminated[0] == pytest.approx(decay * decay * correction)


def test_termination_wins_when_both_flags_are_set():
    """A genuinely terminal state is not made non-terminal by also hitting a limit."""

    agent = _agent()
    rollout = Rollout(
        env_ids=[0, 0],
        rewards=[np.full(N_AGENTS, 1.0, dtype=np.float32)] * 2,
        values=[np.full(N_AGENTS, 10.0, dtype=np.float32)] * 2,
        dones=[False, True],
    )
    rollout.terminated = [False, True]
    rollout.truncated = [False, True]
    returns = _returns(agent, rollout)
    assert returns[1] == pytest.approx(1.0)  # no bootstrap, and none was required


# --------------------------------------------------------------------------------------
# Mid-rollout truncation
# --------------------------------------------------------------------------------------


def test_a_mid_rollout_truncation_uses_its_own_stored_bootstrap():
    """Row 1 truncates inside the pass; row 3 ends the pass without a boundary.

    The two must use different bootstrap values: the row's own captured V(s') for the
    truncation, and the end-of-pass ``bootstrap_values`` for the final row.
    """

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0, 4.0],
        values=[10.0, 20.0, 30.0, 40.0],
        truncated=[False, True, False, False],
        truncation_bootstrap_values={1: 100.0},
        bootstrap_values={0: np.full(N_AGENTS, 7.0, dtype=np.float32)},
    )
    returns = _returns(agent, rollout)
    assert returns[1] == pytest.approx(2.0 + agent.gamma * 100.0)
    assert returns[3] == pytest.approx(4.0 + agent.gamma * 7.0)


def test_a_mid_rollout_truncation_cuts_credit_across_the_boundary():
    """Rewards after the truncation must not reach rows before it.

    Stated behaviourally rather than arithmetically: perturbing a post-boundary reward
    changes only post-boundary targets.
    """

    agent = _agent()

    def targets(late_reward):
        return _returns(
            agent,
            _rollout(
                rewards=[1.0, 2.0, late_reward, 4.0],
                values=[10.0, 20.0, 30.0, 40.0],
                truncated=[False, True, False, False],
                truncation_bootstrap_values={1: 100.0},
            ),
        )

    base = targets(3.0)
    perturbed = targets(3.0 + 50.0)
    assert perturbed[0] == pytest.approx(base[0])
    assert perturbed[1] == pytest.approx(base[1])
    assert perturbed[2] != pytest.approx(base[2])


def test_credit_does_flow_across_an_interior_row():
    """The companion check: without a boundary, a later reward does reach earlier rows.

    Without this the cut test above would pass trivially on a rollout where credit never
    propagates at all.
    """

    agent = _agent()

    def targets(late_reward):
        return _returns(
            agent,
            _rollout(
                rewards=[1.0, 2.0, late_reward, 4.0],
                values=[10.0, 20.0, 30.0, 40.0],
            ),
        )

    base = targets(3.0)
    perturbed = targets(3.0 + 50.0)
    assert perturbed[0] != pytest.approx(base[0])
    assert perturbed[1] != pytest.approx(base[1])


def test_a_truncation_in_one_environment_does_not_touch_another():
    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 1.0, 2.0],
        values=[10.0, 20.0, 10.0, 20.0],
        env_ids=[0, 0, 1, 1],
        truncated=[False, True, False, False],
        truncation_bootstrap_values={1: 100.0},
        bootstrap_values={
            0: np.full(N_AGENTS, 5.0, dtype=np.float32),
            1: np.full(N_AGENTS, 5.0, dtype=np.float32),
        },
    )
    returns = _returns(agent, rollout)
    assert returns[1] == pytest.approx(2.0 + agent.gamma * 100.0)
    assert returns[3] == pytest.approx(2.0 + agent.gamma * 5.0)


def test_several_truncations_each_use_their_own_row_value():
    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0, 4.0],
        values=[10.0, 20.0, 30.0, 40.0],
        truncated=[True, False, True, False],
        truncation_bootstrap_values={0: 100.0, 2: 200.0},
        bootstrap_values={0: np.full(N_AGENTS, 5.0, dtype=np.float32)},
    )
    returns = _returns(agent, rollout)
    assert returns[0] == pytest.approx(1.0 + agent.gamma * 100.0)
    assert returns[2] == pytest.approx(3.0 + agent.gamma * 200.0)


# --------------------------------------------------------------------------------------
# Nothing else changed
# --------------------------------------------------------------------------------------


def test_a_rollout_with_no_boundary_is_unchanged_by_the_new_semantics():
    """Interior arithmetic is identical with the flag on and off, to float equality."""

    rollout = _rollout(rewards=[1.0, 2.0, 3.0, 4.0], values=[10.0, 20.0, 30.0, 40.0])
    corrected = _returns(_agent(), rollout)
    legacy = _returns(_agent(legacy_truncation_as_termination=True), rollout)
    np.testing.assert_array_equal(corrected, legacy)


def test_a_rollout_whose_only_boundary_is_a_termination_is_unchanged():
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0, 4.0],
        values=[10.0, 20.0, 30.0, 40.0],
        terminated=[False, True, False, False],
    )
    corrected = _returns(_agent(), rollout)
    legacy = _returns(_agent(legacy_truncation_as_termination=True), rollout)
    np.testing.assert_array_equal(corrected, legacy)


# --------------------------------------------------------------------------------------
# Legacy reproduction
# --------------------------------------------------------------------------------------


def test_the_legacy_flag_reproduces_the_collapsed_arithmetic():
    """With the flag set, a truncation is scored exactly as a termination was."""

    legacy_agent = _agent(legacy_truncation_as_termination=True)
    truncating = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        truncated=[False, False, True],
        truncation_bootstrap_values={2: 40.0},
    )
    terminating = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        terminated=[False, False, True],
    )
    np.testing.assert_array_equal(
        _returns(legacy_agent, truncating), _returns(legacy_agent, terminating)
    )
    # And the stored bootstrap is genuinely ignored rather than coincidentally equal.
    assert _returns(legacy_agent, truncating)[2] == pytest.approx(3.0)


def test_the_legacy_flag_is_off_by_default_everywhere():
    """Correct semantics are the default: the flag must be opt-in at every layer."""

    from ha_ctse_process import config as process_config

    assert process_config.Config.legacy_truncation_as_termination is False
    assert _agent().legacy_truncation_as_termination is False
    # A config object that never heard of the flag also gets the fix, so an older
    # harness or a candidate config does not silently inherit the old arithmetic.
    bare = make_process_config()
    assert not hasattr(bare, "legacy_truncation_as_termination")
    assert make_agent(config=bare).legacy_truncation_as_termination is False


def test_the_flag_is_recorded_in_the_run_manifest():
    """A run must say which boundary semantics produced it."""

    from ha_ctse_process import standalone_manifest

    assert (
        "legacy_truncation_as_termination"
        in standalone_manifest.TRAINING_MANIFEST_FIELDS
    )


def test_the_cli_exposes_the_legacy_flag():
    from ha_ctse_process import standalone_cli

    source = inspect.getsource(standalone_cli)
    assert '"--legacy_truncation_as_termination"' in source
    assert "config.legacy_truncation_as_termination = True" in source


# --------------------------------------------------------------------------------------
# Fallbacks and refusals
# --------------------------------------------------------------------------------------


def test_a_rollout_without_reason_flags_falls_back_to_the_collapsed_flag():
    """A caller that supplies only ``dones`` cannot be given the fix, and is not guessed at.

    ``experiments`` code and older harnesses build rollouts with ``dones`` alone; they must
    keep working, with today's arithmetic, rather than raising or silently inventing a
    bootstrap.
    """

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        terminated=[False, False, True],
        include_reason_flags=False,
    )
    assert not hasattr(rollout, "terminated") or not rollout.terminated
    returns = _returns(agent, rollout)
    assert returns[2] == pytest.approx(3.0)


def test_reason_flags_that_disagree_with_dones_are_refused():
    """A malformed rollout must not quietly use different boundaries than the reset masks."""

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        terminated=[False, False, True],
    )
    rollout.truncated = [True, False, False]  # dones says row 0 is interior
    with pytest.raises(ValueError, match="disagree with dones"):
        agent._low_returns(rollout)


def test_a_truncated_row_without_a_stored_bootstrap_is_refused():
    """Silently substituting zero would reintroduce exactly the bias being fixed."""

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0, 3.0],
        values=[10.0, 20.0, 30.0],
        truncated=[False, False, True],
    )
    with pytest.raises(ValueError, match="no .*truncation bootstrap value"):
        agent._low_returns(rollout)


def test_the_end_of_pass_bootstrap_is_not_used_for_a_truncated_final_row():
    """``bootstrap_values`` is read after the environment was reset, so it is the wrong episode.

    A truncated final row must therefore require its own captured value rather than
    falling back to the end-of-pass one.
    """

    agent = _agent()
    rollout = _rollout(
        rewards=[1.0, 2.0],
        values=[10.0, 20.0],
        truncated=[False, True],
        bootstrap_values={0: np.full(N_AGENTS, 999.0, dtype=np.float32)},
    )
    with pytest.raises(ValueError, match="truncation bootstrap value"):
        agent._low_returns(rollout)


# --------------------------------------------------------------------------------------
# The collector side
# --------------------------------------------------------------------------------------


def test_single_env_bootstrap_matches_the_batched_call():
    """``low_bootstrap_value_for_env`` must be the batched value, not a second definition."""

    agent = make_agent(num_envs=3)
    rng = np.random.default_rng(7)
    observations = [
        rng.normal(size=(agent.n_agents, agent.obs_dim)).astype(np.float32)
        for _ in range(agent.num_envs)
    ]
    states = [
        rng.normal(size=agent.state_dim).astype(np.float32)
        for _ in range(agent.num_envs)
    ]
    batched = agent.low_bootstrap_values(observations, states)
    for env_id in range(agent.num_envs):
        single = agent.low_bootstrap_value_for_env(
            env_id, observations[env_id], states[env_id]
        )
        np.testing.assert_allclose(single, batched[env_id], rtol=0.0, atol=1e-6)


def test_single_env_bootstrap_refuses_an_out_of_range_environment():
    agent = make_agent(num_envs=2)
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    state = np.zeros(agent.state_dim, dtype=np.float32)
    with pytest.raises(ValueError, match="out of range"):
        agent.low_bootstrap_value_for_env(2, obs, state)


def test_single_env_bootstrap_reads_that_environment_own_recurrent_state():
    """The value must depend on the target env's critic state, not on env 0's."""

    agent = make_agent(num_envs=2)
    if not agent.use_recurrent_low_level:
        pytest.skip("non-recurrent low level has no hidden state to distinguish")
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    state = np.zeros(agent.state_dim, dtype=np.float32)
    agent.low_critic_hxs[0, :, :] = 0.0
    agent.low_critic_hxs[1, :, :] = 1.0
    first = agent.low_bootstrap_value_for_env(0, obs, state)
    second = agent.low_bootstrap_value_for_env(1, obs, state)
    assert not np.allclose(first, second)


def test_the_collector_records_both_reason_flags():
    source = inspect.getsource(standalone_train_runner.train_loop)
    assert "rollout.terminated.append(bool(terminated))" in source
    assert "rollout.truncated.append(bool(truncated))" in source
    assert "rollout.dones.append(done)" in source  # the collapsed flag is still recorded


def test_the_collector_captures_the_bootstrap_before_resetting():
    """Ordering is the whole correctness argument for the mid-rollout case.

    ``reset_one`` replaces the post-truncation observation and ``reset_env_state`` clears
    the recurrent critic state, so the capture must precede both.
    """

    source = inspect.getsource(standalone_train_runner.train_loop)
    capture = source.index("low_bootstrap_value_for_env")
    assert capture < source.index("collector.reset_one(env_id)")
    assert capture < source.index("agent.reset_env_state(env_id)")
    # And it is guarded on truncation only, never on a genuine termination.
    guard = source.rindex("if bool(truncated) and not bool(terminated):", 0, capture)
    assert guard < capture


def test_the_capture_sits_inside_the_episode_boundary_branch():
    """A syntactic check that the capture cannot run on a non-boundary step."""

    source = inspect.getsource(standalone_train_runner)
    tree = ast.parse(source)
    loop = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "train_loop"
    )
    captures = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Attribute) and node.attr == "low_bootstrap_value_for_env"
    ]
    assert len(captures) == 1
    guarded = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.If)
        and any(
            isinstance(inner, ast.Attribute)
            and inner.attr == "low_bootstrap_value_for_env"
            for inner in ast.walk(node)
        )
    ]
    # The capture is nested inside at least the `if done:` and `if truncated...` guards.
    assert len(guarded) >= 2


# --------------------------------------------------------------------------------------
# End to end, through the real collector and a real legacy environment
# --------------------------------------------------------------------------------------


def _load_impact_tool():
    """Import the measurement tool by path; `tools/` is not an importable package."""

    import importlib.util

    path = (
        Path(__file__).resolve().parents[3]
        / "tools"
        / "analysis"
        / "truncation_bootstrap_impact.py"
    )
    spec = importlib.util.spec_from_file_location("truncation_bootstrap_impact", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("scenario", ("belief_map", "base"))
def test_a_real_legacy_rollout_is_all_truncations_and_every_one_is_captured(scenario):
    """The empirical basis for the fix, measured rather than asserted.

    The legacy relay environments never terminate, so every boundary the collector
    produces is a truncation.  Each one must carry a captured V(s'), or the corrected GAE
    would refuse the rollout - which is exactly the guarantee this test is for.
    """

    tool = _load_impact_tool()
    report = tool.run(
        [
            "--scenario",
            scenario,
            "--rollout-length",
            "48",
            "--max-steps",
            "12",
            "--num-envs",
            "2",
            "--seed",
            "12345",
        ]
    )
    rollout = report["rollout"]
    assert rollout["n_boundaries"] > 0, "the episode limit must be hit inside the pass"
    assert rollout["n_terminated"] == 0
    assert rollout["n_truncated"] == rollout["n_boundaries"]
    assert rollout["n_truncation_bootstraps_captured"] == rollout["n_truncated"]
    # Mid-rollout, not only at the end: the last row index is rows - 1.
    assert any(
        row < rollout["rows"] - 1 for row in rollout["truncated_row_indices"]
    ), "this fixture must exercise the mid-rollout case"
    assert report["optimizer_updates"] == 0
    assert report["training_fits_performed"] == 0


def test_the_correction_at_a_real_truncation_row_is_exactly_the_discounted_bootstrap():
    """On real data: corrected - legacy at the truncation rows equals gamma * V(s')."""

    tool = _load_impact_tool()
    report = tool.run(
        [
            "--scenario",
            "belief_map",
            "--rollout-length",
            "48",
            "--max-steps",
            "12",
            "--num-envs",
            "2",
            "--seed",
            "12345",
        ]
    )
    rows = report["at_truncation_rows"]
    observed = rows["corrected_return_mean"] - rows["legacy_return_mean"]
    expected = report["gamma"] * rows["captured_bootstrap_mean"]
    assert observed == pytest.approx(expected, rel=1e-5)
    # And the whole rollout's targets moved, not just the boundary rows: the correction
    # propagates backwards through the recursion.
    assert report["value_target_change"]["n_rows_changed"] > report["rollout"]["n_truncated"]


def test_the_cli_flag_reaches_the_config_through_the_real_override_path():
    """Source inspection is not enough: the flag must actually land on the config."""

    from ha_ctse_process import standalone_cli

    def resolve(extra):
        saved = sys.argv
        sys.argv = [
            "cli",
            "--config",
            "ha_ctse_process.config",
            "--scenario",
            "belief_map",
            *extra,
        ]
        try:
            args = standalone_cli.parse_args()
        finally:
            sys.argv = saved
        config = standalone_cli.load_config(args.config, args.preset or None)
        standalone_cli.apply_standalone_overrides(config, args)
        return config.legacy_truncation_as_termination

    assert resolve([]) is False
    assert resolve(["--legacy_truncation_as_termination"]) is True


def test_the_captured_value_is_not_the_post_reset_one():
    """The discriminating test for the capture ordering, on real data.

    ``bootstrap_values[env_id]`` is read after the collection loop, when a truncated
    environment has already been reset, so it is the next episode's first observation.  If
    the capture had happened after the reset the two would be identical for a truncation
    on an environment's last row.  They must differ.
    """

    tool = _load_impact_tool()
    report = tool.run(
        [
            "--scenario",
            "belief_map",
            "--rollout-length",
            "48",
            "--max-steps",
            "12",
            "--num-envs",
            "2",
            "--seed",
            "12345",
        ]
    )
    evidence = report["capture_is_pre_reset"]
    assert evidence["comparable_rows"] > 0, "the fixture must end a pass on a truncation"
    assert evidence["identical"] is False
    assert evidence["abs_gap_mean"] > 1e-4


# --------------------------------------------------------------------------------------
# The high level: the same distinction, on the critic that chooses skills
# --------------------------------------------------------------------------------------


def test_the_boundary_decision_helper_truth_table():
    """One helper decides for both high-level paths, so pin every case."""

    agent = _agent()
    # Not a boundary at all.
    assert agent._boundary_is_terminal(False, False, False) is False
    assert agent._boundary_is_terminal(False, True, True) is False
    # A real termination.
    assert agent._boundary_is_terminal(True, True, False) is True
    # A pure truncation: the only case that must not zero the bootstrap.
    assert agent._boundary_is_terminal(True, False, True) is False
    # Termination wins when both are set.
    assert agent._boundary_is_terminal(True, True, True) is True
    # A done row with neither reason, and a caller that supplies no reason at all,
    # both keep the collapsed pre-fix reading.
    assert agent._boundary_is_terminal(True, False, False) is True
    assert agent._boundary_is_terminal(True, None, None) is True
    # The legacy flag collapses a truncation back onto a termination.
    legacy = _agent(legacy_truncation_as_termination=True)
    assert legacy._boundary_is_terminal(True, False, True) is True


def _r30_agent(**config_overrides):
    """An R30 agent with one pending high row, plus the arrays the boundary will see.

    Seeded so the critic returns a fixed number rather than a random one, which is what
    lets the assertions below compare against exact values.
    """

    import torch

    torch.manual_seed(0)
    agent = _agent(high_controller="r30_fixed_clock_ar_edit", **config_overrides)
    assert agent.r30_enabled
    assert agent.high_check_buffer is not None

    rng = np.random.default_rng(0)
    joint_obs = rng.normal(size=(agent.n_agents, agent.obs_dim)).astype(np.float32)
    state = rng.normal(size=agent.state_dim).astype(np.float32)
    agent.high_check_buffer.start_decision(
        env_id=0,
        episode_id=0,
        state=state,
        joint_obs=joint_obs,
        prev_skills=np.zeros(agent.n_agents, dtype=np.int64),
        prev_active=np.zeros(agent.n_agents, dtype=bool),
        prev_ages=np.zeros(agent.n_agents, dtype=np.int64),
        steps_to_check=1,
        old_value=0.25,
    )
    return agent, joint_obs, state


def _close_one_r30_step(agent, joint_obs, state, **reason_flags):
    agent.record_environment_step(
        0,
        reward=1.0,
        next_obs=joint_obs,
        next_state=state,
        done=True,
        **reason_flags,
    )
    rows = agent.high_check_buffer.pop_completed()
    assert len(rows) == 1
    return rows[0]


def test_r30_termination_closes_a_terminal_row_with_no_bootstrap():
    agent, joint_obs, state = _r30_agent()
    row = _close_one_r30_step(agent, joint_obs, state, terminated=True, truncated=False)

    assert row.terminal is True
    assert row.policy_truncated is False
    assert row.old_next_value == 0.0


def test_r30_truncation_closes_a_non_terminal_row_with_a_real_bootstrap():
    """The high-level half of the fix: a time limit keeps V(s') and cuts the recursion.

    ``policy_truncated=True`` is the same marking ``truncate_high_rows_for_update``
    already applies at a PPO update boundary, so the corrected episode case reuses
    machinery that existed but was unreachable from an episode truncation.
    """

    agent, joint_obs, state = _r30_agent()
    row = _close_one_r30_step(agent, joint_obs, state, terminated=False, truncated=True)

    assert row.terminal is False
    assert row.policy_truncated is True
    assert row.old_next_value != 0.0
    # The stored bootstrap is the value of the post-truncation observation under the
    # same skill/age arrays the boundary saw.
    expected = agent._r30_value_for_arrays(
        0, state, joint_obs, steps_to_check=int(agent.steps_to_check[0])
    )
    assert row.old_next_value == pytest.approx(expected)


def test_r30_legacy_flag_collapses_the_high_level_boundary_too():
    """Legacy reproduction has to cover the hierarchy, not only the low level."""

    agent, joint_obs, state = _r30_agent(legacy_truncation_as_termination=True)
    row = _close_one_r30_step(agent, joint_obs, state, terminated=False, truncated=True)

    assert row.terminal is True
    assert row.policy_truncated is False
    assert row.old_next_value == 0.0


def test_r30_a_caller_without_reason_flags_keeps_the_collapsed_close():
    agent, joint_obs, state = _r30_agent()
    row = _close_one_r30_step(agent, joint_obs, state)

    assert row.terminal is True
    assert row.policy_truncated is False
    assert row.old_next_value == 0.0


def _segment_with(agent, rng, *, terminated, truncated, supply_flags=True):
    from ha_ctse_process.standalone_segments import Segment

    obs = rng.normal(size=agent.obs_dim).astype(np.float32)
    joint_obs = rng.normal(size=(agent.n_agents, agent.obs_dim)).astype(np.float32)
    state = rng.normal(size=agent.state_dim).astype(np.float32)
    segment = Segment(
        env_id=0,
        agent_id=0,
        skill=0,
        duration_idx=0,
        start_step=0,
        high_obs=obs,
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        high_state=state,
    )
    reasons = {"terminated": terminated, "truncated": truncated} if supply_flags else {}
    segment.append(
        obs,
        np.zeros(1, dtype=np.float32),
        1.0,
        obs,
        0,
        next_joint_obs=joint_obs,
        next_state=state,
        done=bool(terminated or truncated),
        **reasons,
    )
    return segment


def _legacy_high_agent(**config_overrides):
    import torch

    torch.manual_seed(0)
    agent = _agent(**config_overrides)
    assert not agent.r30_enabled
    assert agent.use_smdp_bootstrap, "the SMDP bootstrap is the path under test"
    return agent, np.random.default_rng(0)


def test_the_legacy_high_route_bootstraps_a_truncated_segment_but_not_a_terminated_one():
    """``_bootstrap_high_values`` must skip only genuine terminations.

    This is the non-R30 SMDP path. A truncated segment already stores ``end_state`` and
    ``end_joint_obs``, so it has everything needed to bootstrap; before the fix it was
    skipped because ``Segment.terminal`` could not tell the two reasons apart.
    """

    agent, rng = _legacy_high_agent()
    terminated = _segment_with(agent, rng, terminated=True, truncated=False)
    truncated = _segment_with(agent, rng, terminated=False, truncated=True)
    assert agent._segment_is_terminal(terminated) is True
    assert agent._segment_is_terminal(truncated) is False

    values = agent._bootstrap_high_values([terminated, truncated])
    assert values[0] == 0.0, "a real terminal state has no future value"
    assert values[1] != 0.0, "a time limit must still be bootstrapped"
    assert np.isfinite(values[1])


def test_the_legacy_high_route_collapses_under_the_legacy_flag():
    agent, rng = _legacy_high_agent(legacy_truncation_as_termination=True)
    truncated = _segment_with(agent, rng, terminated=False, truncated=True)

    assert agent._segment_is_terminal(truncated) is True
    assert agent._bootstrap_high_values([truncated])[0] == 0.0


def test_a_segment_built_without_reason_flags_records_the_collapsed_reading():
    """Older callers pass only ``done``; their segments must read exactly as before."""

    agent, rng = _legacy_high_agent()
    segment = _segment_with(agent, rng, terminated=False, truncated=True, supply_flags=False)

    assert segment.terminal is True
    assert segment.terminated is True  # indistinguishable, so read as terminal
    assert segment.truncated is False
    assert agent._segment_is_terminal(segment) is True
    assert agent._bootstrap_high_values([segment])[0] == 0.0


def test_the_runner_passes_both_reason_flags_to_the_high_level_paths():
    """The segment manager and the R30 check buffer must both receive the reasons."""

    source = inspect.getsource(standalone_train_runner.train_loop)
    assert source.count("terminated=bool(terminated),") >= 2
    assert source.count("truncated=bool(truncated),") >= 2


# --------------------------------------------------------------------------------------
# Both low-level architectures, and the whole update rather than only the arithmetic
# --------------------------------------------------------------------------------------


LOW_ARCHITECTURES = ("strict_hmasd_mappo", "feedforward")


@pytest.mark.parametrize("architecture", LOW_ARCHITECTURES)
def test_single_env_bootstrap_matches_a_direct_critic_call(architecture):
    """Independent recomputation, so a shared assembly error cannot pass unnoticed.

    Comparing against ``low_bootstrap_values`` alone only proves the two agree. This
    rebuilds the critic call for one environment by hand - that environment's own skills,
    team code and recurrent critic state, agent ids in order - so a wrong reshape, a
    transposed agent axis or the wrong environment's hidden state would show up.
    """

    import torch

    torch.manual_seed(0)
    agent = make_agent(
        config=make_process_config(low_level_architecture=architecture), num_envs=3
    )
    assert agent.low_level_architecture == architecture
    env_id = 1

    rng = np.random.default_rng(7)
    observations = [
        rng.normal(size=(agent.n_agents, agent.obs_dim)).astype(np.float32)
        for _ in range(agent.num_envs)
    ]
    states = [
        rng.normal(size=agent.state_dim).astype(np.float32)
        for _ in range(agent.num_envs)
    ]
    if agent.use_recurrent_low_level:
        # A distinct hidden state per environment is what makes the check discriminating.
        shape = np.asarray(agent.low_critic_hxs).shape
        agent.low_critic_hxs[:] = rng.normal(size=shape).astype(np.float32)

    joint_obs = agent._joint_obs_array(observations[env_id])
    skills_t = torch.as_tensor(agent.active_skills[env_id], dtype=torch.long)
    if agent.use_recurrent_low_level:
        state_t = (
            torch.as_tensor(
                agent._state_array(states[env_id], joint_obs), dtype=torch.float32
            )
            .unsqueeze(0)
            .expand(agent.n_agents, agent.state_dim)
        )
        team_t = torch.full(
            (agent.n_agents,), int(agent.active_team_codes[env_id]), dtype=torch.long
        )
        hxs_t = torch.as_tensor(
            np.asarray(agent.low_critic_hxs)[env_id], dtype=torch.float32
        )
        agent_ids_t = torch.arange(agent.n_agents, dtype=torch.long)
        with torch.no_grad():
            direct = agent.low.value(state_t, skills_t, team_t, hxs_t, agent_ids_t)
            if agent.low_value_norm is not None:
                direct = agent.low_value_norm.denormalize_tensor(direct)
    else:
        # The feedforward critic reads the observation and is not denormalized here,
        # which is how `low_bootstrap_values` has always read it; this test pins that
        # reading rather than changing it.
        with torch.no_grad():
            _a, _logp, _entropy, direct = agent.low.act(
                torch.as_tensor(joint_obs, dtype=torch.float32),
                skills_t,
                deterministic=True,
            )
    expected = direct.detach().cpu().numpy().reshape(-1)

    single = agent.low_bootstrap_value_for_env(env_id, observations[env_id], states[env_id])
    np.testing.assert_allclose(single, expected, rtol=0.0, atol=1e-6)
    # And still the same number the batched end-of-pass call produces.
    batched = agent.low_bootstrap_values(observations, states)
    np.testing.assert_allclose(single, batched[env_id], rtol=0.0, atol=1e-6)


@pytest.mark.parametrize("architecture", LOW_ARCHITECTURES)
def test_a_truncated_rollout_survives_the_whole_low_level_update(architecture):
    """Past the arithmetic: the value normalizer, the chunking and the PPO epochs.

    ``_low_returns`` is tested directly above. This drives a real rollout containing
    truncations through ``update_low`` itself, which is where the corrected returns meet
    ``low_value_norm.update``, the recurrent sequence chunking and the optimizer. It runs
    on both architectures because only one of them takes the recurrent branch.

    This is a test, not a training fit: one update on a 48-row rollout, weights discarded
    with the agent.
    """

    tool = _load_impact_tool()
    config, args, _args_ns = tool.build_run_inputs(
        [
            "--scenario",
            "belief_map",
            "--rollout-length",
            "24",
            "--max-steps",
            "8",
            "--num-envs",
            "2",
            "--seed",
            "999",
        ]
    )
    config.low_level_architecture = architecture
    agent, rollout = tool._capture_one_rollout(config, args)
    assert agent.low_level_architecture == architecture

    truncated_rows = int(sum(bool(flag) for flag in rollout.truncated))
    assert truncated_rows > 0, "the fixture must contain truncations to be worth running"
    assert int(sum(bool(flag) for flag in rollout.terminated)) == 0
    assert len(rollout.truncation_bootstrap_values) == truncated_rows

    metrics = agent.update_low(rollout)
    assert metrics["low_boundary_flags_resolved"] == 1.0
    assert metrics["low_boundary_legacy_collapse"] == 0.0
    assert metrics["low_truncation_rows"] == float(truncated_rows)
    for name in ("low_loss", "low_value_loss", "low_actor_loss"):
        assert np.isfinite(metrics[name]), f"{name} is not finite"

    # The legacy flag is readable from the metrics of the same rollout. Only the two
    # resolution flags are compared here: the second update starts from the weights the
    # first one left, so its losses are not a before/after pair.
    agent.legacy_truncation_as_termination = True
    legacy_metrics = agent.update_low(rollout)
    assert legacy_metrics["low_boundary_flags_resolved"] == 1.0
    assert legacy_metrics["low_boundary_legacy_collapse"] == 1.0
