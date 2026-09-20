"""Correctness fixtures only: no A01 learning result or seed selection."""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.host import (
    Episode, STATE_COUNT, State, addressed_randomness, behavior_episode, closed_loop_move, step,
)
from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.learning import (
    forward_targets, greedy_probabilities, option_kernel, update_chunk,
)
from experiments.candidates.termination_rule_experience_reuse.off_termination_a01.study import (
    Config, evaluate, run_study,
)


def fixture_episode(states, options, rewards, renewals):
    count = len(rewards)
    options = np.asarray(options, dtype=np.int8)
    return Episode(np.asarray(states, dtype=np.int16), options,
                   np.asarray(rewards, dtype=np.float64), np.asarray(renewals, dtype=np.bool_),
                   np.zeros(count, dtype=np.bool_),
                   np.where(options[1:] == options[:-1], 15 / 16, 1 / 16))


def test_state_round_trip_and_actual_remaining_commitment():
    assert {State.decode(i).encode() for i in range(STATE_COUNT)} == set(range(STATE_COUNT))
    held = State(2, 2, 1, 0, 2)
    released = replace(held, teammate_remaining=1)
    next_held, _, flag_held = step(held, 1, .9, .1)
    next_released, _, flag_released = step(released, 1, .9, .1)
    assert next_held.teammate_position == next_released.teammate_position == 1
    assert (next_held.teammate_skill, next_held.teammate_remaining, flag_held) == (0, 1, False)
    assert (next_released.teammate_skill, next_released.teammate_remaining, flag_released) == (1, 4, True)


def test_closed_loop_skill_moves_then_holds_and_reward_precedes_new_demand():
    assert [closed_loop_move(p, 0) for p in range(5)] == [0, 0, 1, 2, 3]
    assert [closed_loop_move(p, 1) for p in range(5)] == [1, 2, 3, 4, 4]
    state = State(3, 3, 1, 1, 1)
    nxt, reward, renewed = step(state, 1, .01, .1)
    assert reward == .7  # Duplicate high-site coverage is not 1.4.
    assert nxt.demand == nxt.teammate_skill == 0 and renewed


def test_behavior_support_and_addressed_streams_are_arm_independent():
    first = behavior_episode(81, 7, 64, .125)
    second = behavior_episode(81, 7, 64, .125)
    for field in first.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(first, field), getattr(second, field))
    expected = np.where(first.options[1:] == first.options[:-1], 15 / 16, 1 / 16)
    np.testing.assert_array_equal(first.next_option_probability, expected)
    first.validate()
    assert not np.array_equal(addressed_randomness(81, 0, 7, 64)[2],
                              addressed_randomness(81, 1, 7, 64)[2])


def test_greedy_ties_and_marginal_option_kernel():
    values = np.array([[1., 1.], [2., 1.], [1., 2.]])
    np.testing.assert_array_equal(greedy_probabilities(values), [[.5, .5], [1., 0.], [0., 1.]])
    np.testing.assert_array_equal(option_kernel(values, np.array([0, 0, 0]), .5),
                                  [[.75, .25], [1., 0.], [.5, .5]])


def test_qbeta_cuts_same_label_renewal_but_retrace_uses_marginal_probability():
    q = np.zeros((STATE_COUNT, 2))
    q[:, 1] = 1.
    data = fixture_episode([0, 1, 2], [0, 0, 0], [1., 2.], [True, False])
    qbeta = forward_targets(q, data, 0, 2, "qbeta", .9, .5)
    retrace = forward_targets(q, data, 0, 2, "retrace", .9, .5)
    assert qbeta["coefficients"][1] == 0
    assert retrace["coefficients"][1] == pytest.approx(8 / 15)
    assert retrace["raw_ratios"][0] == pytest.approx(.5 / (15 / 16))
    assert qbeta["target"][0] == pytest.approx(1 + .9 * .5)
    data_no_renewal = replace(data, renewed=np.array([False, False]))
    assert forward_targets(q, data_no_renewal, 0, 2, "qbeta", .9, .5)["coefficients"][1] == .5


def test_retrace_uses_observed_option_after_switch_and_clips_ratio():
    q = np.zeros((STATE_COUNT, 2))
    q[:, 1] = 2.
    data = fixture_episode([0, 1, 2], [0, 1, 1], [1., 2.], [True, False])
    value = forward_targets(q, data, 0, 2, "retrace", .9, .5)
    assert value["raw_ratios"][0] == 8.
    assert value["coefficients"][1] == 1.
    # Second residual subtracts Q(x1, observed option 1), not fictitious option 0.
    assert value["delta"][1] == pytest.approx(2 + .9 * 2 - 2)
    assert value["target"][0] == pytest.approx((1 + .9) + .9 * 1.8)


@pytest.mark.parametrize("arm", ["one_step", "qbeta", "retrace"])
def test_forward_recursion_matches_independent_explicit_sum_and_chunk_truncation(arm):
    q = np.arange(STATE_COUNT * 2, dtype=float).reshape(STATE_COUNT, 2) / 100
    data = fixture_episode([0, 1, 2, 3, 4], [0, 0, 1, 1, 1],
                           [.2, .4, .1, .8], [False, True, False, False])
    result = forward_targets(q, data, 1, 4, arm, .95, .5)
    expected = []
    for i in range(1, 4):
        increment, weight = 0., 1.
        for j in range(i, 4):
            if j > i:
                prev, current = data.options[j - 1], data.options[j]
                greedy = np.flatnonzero(q[data.states[j]] == q[data.states[j]].max())
                probability = (1 / len(greedy)) if current in greedy else 0.
                target = .5 * int(current == prev) + .5 * probability
                if arm == "one_step":
                    coefficient = 0.
                elif arm == "qbeta":
                    coefficient = (0. if data.renewed[j - 1] else target)
                else:
                    coefficient = min(1., target / data.next_option_probability[j - 1])
                weight *= .95 * coefficient
            current = data.options[j]
            following = q[data.states[j + 1]]
            delta = data.rewards[j] + .95 * (.5 * following[current] + .5 * max(following))
            delta -= q[data.states[j], current]
            increment += weight * delta
        expected.append(q[data.states[i], data.options[i]] + increment)
    np.testing.assert_allclose(result["target"], expected, rtol=1e-14, atol=1e-14)
    last = forward_targets(q, data, 3, 4, arm, .95, .5)
    assert last["target"][0] > data.rewards[3]  # Bootstrap remains on truncation.


def test_changing_suffix_after_qbeta_renewal_cannot_change_earlier_target():
    q = np.ones((STATE_COUNT, 2))
    original = fixture_episode([0, 1, 2], [0, 1, 1], [1., 2.], [True, False])
    altered = replace(original, rewards=np.array([1., 2000.]))
    before = forward_targets(q, original, 0, 2, "qbeta", .9, .5)["target"][0]
    after = forward_targets(q, altered, 0, 2, "qbeta", .9, .5)["target"][0]
    assert before == after


def test_fixed_denominator_has_zero_expected_one_step_update_at_true_fixed_point():
    gamma = .8
    exact = 2 / (2 - gamma)
    # A hand finite tree: exit immediately; stay then exit; stay twice.
    outcomes = [(.5, [0, 1, 1], [1., 0.]),
                (.25, [0, 0, 1], [1., 1.]),
                (.25, [0, 0, 0], [1., 1.])]
    expected_change = 0.
    for probability, states, rewards in outcomes:
        q = np.zeros((STATE_COUNT, 2))
        q[0, :] = exact
        data = fixture_episode(states, [0, 0, 0], rewards, [False, False])
        visits = np.zeros_like(q, dtype=np.int64)
        stats = update_chunk(q, visits, data, 0, 2, "one_step", gamma, 0., 1.)
        expected_change += probability * (q[0, 0] - exact)
        assert stats["target_rows"] == 2
        assert visits.sum() == 2
    assert expected_change == pytest.approx(0., abs=1e-14)


def test_frozen_chunk_duplicate_updates_use_fixed_chunk_mean():
    q = np.zeros((STATE_COUNT, 2))
    visits = np.zeros_like(q, dtype=np.int64)
    data = fixture_episode([0, 0, 1, 2], [0, 0, 0, 0], [1., 2., 3.], [False] * 3)
    stats = update_chunk(q, visits, data, 0, 3, "one_step", .9, .5, 1.)
    assert q[0, 0] == pytest.approx((1 + 2) / 3)
    assert q[1, 0] == pytest.approx(3 / 3)
    assert visits[0, 0] == 2 and stats["table_entries_written"] == 2


def test_evaluation_has_no_update_or_training_stream_mutation():
    q = np.arange(STATE_COUNT * 2, dtype=float).reshape(STATE_COUNT, 2)
    saved = q.copy()
    config = Config(arm="one_step", seed=42, eval_episodes=2, horizon=4, chunk=2)
    before = behavior_episode(42, 3, 4, .125)
    first = evaluate(q, config, 0)
    second = evaluate(q, config, 1)
    np.testing.assert_array_equal(q, saved)
    np.testing.assert_array_equal(before.states, behavior_episode(42, 3, 4, .125).states)
    assert [r["J"] for r in first] == [r["J"] for r in second]
    assert all(r["new_updates"] == 0 for r in first)


def test_fixture_artifacts_counts_hashes_and_no_overwrite(tmp_path):
    config = Config(arm="retrace", seed=42, train_episodes=2, horizon=4,
                    chunk=2, eval_episodes=2, checkpoints=(0, 1, 2))
    admission = {"direction": "termination_rule_experience_reuse", "sha": "a" * 40}
    out = tmp_path / "fixture"
    result = run_study(config, out, admission, time.monotonic())
    assert result["status"] == "COMPLETE"
    assert result["counts"] == {
        "started_fits": 1, "train_episodes": 2, "train_team_steps": 8,
        "evaluation_episodes": 6, "evaluation_team_steps": 24,
        "tabular_update_calls": 4, "target_rows": 8,
        "table_entries_written": result["counts"]["table_entries_written"],
        "evaluation_new_updates": 0, "gradient_optimizer_steps": 0,
    }
    for item in result["artifacts"]:
        path = out / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    with np.load(out / "final.npz") as arrays:
        assert arrays["visits"].sum() == 8
        assert arrays["checkpoint_q"].shape == (3, STATE_COUNT, 2)
    assert json.loads((out / "summary.json").read_text())["launch_sha"] == "a" * 40
    with pytest.raises(FileExistsError, match="no overwrite"):
        run_study(config, out, admission)


def test_failure_preserves_status_partial_counts_and_original_error(tmp_path, monkeypatch):
    from experiments.candidates.termination_rule_experience_reuse.off_termination_a01 import study
    config = Config(arm="one_step", seed=42, train_episodes=2, horizon=4,
                    chunk=2, eval_episodes=1, checkpoints=(0, 2))
    admission = {"direction": "termination_rule_experience_reuse", "sha": "b" * 40}
    monkeypatch.setattr(study, "update_chunk", lambda *args: (_ for _ in ()).throw(ValueError("fixture failure")))
    with pytest.raises(ValueError, match="fixture failure"):
        run_study(config, tmp_path / "failed", admission)
    result = json.loads((tmp_path / "failed" / "summary.json").read_text())
    assert result["status"] == "FAILED" and result["primary_mean_J"] is None
    assert result["counts"]["tabular_update_calls"] == 0
    assert result["error"] == "ValueError: fixture failure"
    assert (tmp_path / "failed" / "behavior.npz").exists()


def test_production_cli_missing_admission_refuses_before_output(tmp_path):
    repo = Path(__file__).resolve().parents[5]
    out = tmp_path / "never_created"
    env = dict(os.environ)
    env.pop("HMASD_ADMISSION_V1", None)
    process = subprocess.run(
        [sys.executable, str(repo / "scripts/run_termination_reuse_a01.py"),
         "--arm", "retrace", "--seed", "91021", "--out", str(out),
         "--launch-sha", "c" * 40], capture_output=True, text=True, env=env,
        cwd=repo, timeout=20,
    )
    assert process.returncode != 0
    assert "missing HMASD admission" in process.stderr
    assert not out.exists()
