"""Synthetic host boundary only: never execute a real scientific episode."""

import json
import math
import random

import pytest

from experiments.candidates.ucope.shared_data_return_model_b02 import model as m
from experiments.candidates.ucope.shared_data_return_model_b02 import evaluation as e
from scripts import run_ucope_shared_data_return_model_b02 as runner


def completed(action, count, period, reward):
    return m.host.Execution(count, action, period, reward, -.02 if action == "PROBE" else 0.,
                            reward + (.02 if action == "PROBE" else 0.), 8 if action == "PROBE" else 2)


def flatten(values):
    for value in values:
        if isinstance(value, list):
            yield from flatten(value)
        else:
            yield value


def test_synthetic_changed_path_and_publication(tmp_path, monkeypatch):
    # Known completed observations pin once-only shared immediate and same-target fits.
    model = m.ReturnModel()
    for reward in (.2, .8):
        model.observe(0, completed("IMMEDIATE", None, 4, reward))
    for count, reward in ((2, 1.), (2, .6), (4, .2)):
        model.observe(0, completed("PROBE", count, 6, reward))
    assert model.q_immediate[0] == pytest.approx(.5) and model.n_immediate[0] == 2
    assert model.q_full[0][2][2] == pytest.approx(.8) and model.n_full[0][2][2] == 2
    assert model.q_blind[0][2] == pytest.approx(.6) and model.n_blind[0][2] == 3
    assert model.histogram[0] == [0, 0, 2, 0, 1, 0, 0]
    assert model.full_values(0, 3)[2] == pytest.approx(.6)  # unobserved: blind fallback
    assert model.full_values(0, 4)[2] == pytest.approx(.2)  # observed: full value
    assert model.final_policies()["FULL"][0]["estimated_probe_return"] == pytest.approx(.6)
    model.n_full[0][0][2] = 1
    assert model.full_values(0, 0)[2] == 0.  # observed zero must not fall back
    empty = m.ReturnModel()
    empty.q_immediate[0] = -.1
    assert empty.final_policies()["FULL"][0]["root_action"] == "IMMEDIATE"
    tied = m.ReturnModel()
    tied.histogram[0][0] = 1
    plans = tied.final_policies()
    assert plans["FULL"][0]["root_action"] == plans["BLIND"][0]["root_action"] == "IMMEDIATE"
    assert plans["FULL"][0]["tail_periods"] == [2] * 7 and plans["BLIND"][0]["tail_period"] == 2

    # Production runner/stream/evaluator, but every host return is a synthetic fixture.
    monkeypatch.setattr(runner, "BATCHES", 1)
    monkeypatch.setattr(runner, "EVAL_EPISODES", 4)
    global_state = random.getstate()
    expected_rng = random.Random(2_006_401)
    uniforms = [expected_rng.random() for _ in range(256)]
    training_rows, eval_rows = [], []

    def synthetic_host(context, **kw):
        c = m.CONTEXTS.index(context)
        assert kw["ancestry"] == ("UCOPE-SHARED-DATA-RETURN-MODEL-B02", "seed-6401", m.context_id(context))
        assert kw["support"] == (2, 4, 6, 8)
        probe = kw["root_action"] == "PROBE"
        if not kw["evaluation"]:
            row = len(training_rows)
            assert c == row // 32 and kw["episode_index"] == row % 32
            assert probe == (row % 32 >= 16)
            count = 6 * (row % 2) if probe else None
            if probe:
                period = kw["tail_selector"](count)
                assert kw["tail_selector"](object()) == period  # behavior ignores display
                assert period == m.K_EVAL[int(4 * uniforms[row])]
                reward = float(period == (2 if count == 0 else 8))
            else:
                assert kw["tail_selector"] is None
                period, reward = kw["immediate_period"], .45
                assert period == 4
            training_rows.append((c, count, period, reward))
        else:
            assert len(training_rows) == 256  # only after the full synthetic dataset
            name = e.POLICIES[len(eval_rows) % 3]
            assert c == len(eval_rows) // 12
            assert kw["episode_index"] == (len(eval_rows) // 3) % 4
            count = 6 * (kw["episode_index"] % 2)
            if probe:
                period = kw["tail_selector"](count if name == "FULL" else object())
            else:
                assert kw["tail_selector"] is None
                period = kw["immediate_period"]
            reward = .35 + .5 * (period == (2 if count == 0 else 8)) - .02 * probe
            reward += 1e-10 * (kw["episode_index"] + 1)
            eval_rows.append((c, name, kw["episode_index"], kw["ancestry"], reward))
        return completed(kw["root_action"], count if probe else None, period, reward)

    monkeypatch.setattr(m.host, "execute_episode", synthetic_host)
    assert runner.run(tmp_path / "complete") == 0
    assert random.getstate() == global_state
    summary = json.loads((tmp_path / "complete" / "summary.json").read_text())
    assert summary["status"] == "COMPLETE" and len(eval_rows) == 96
    assert summary["training"]["behavior_uniforms"] == summary["training"]["episodes"] == 256
    assert summary["training"]["transitions"] == 1280
    assert summary["training"]["probe_episodes"] == summary["training"]["immediate_episodes"] == 128
    assert summary["exposure"]["scalar_value_updates"] == 384
    assert summary["exposure"]["histogram_updates"] == 128
    assert all(summary["exposure"][name]["scalar_updates"] == 128
               for name in ("full", "blind", "shared_immediate"))

    # Independent scalar reference over the recorded mock observations.
    reference, counts = {}, {}
    for c, n, period, reward in training_rows:
        keys = [("shared_immediate", c)] if n is None else [("full", c, n, period), ("blind", c, period)]
        for key in keys:
            count = counts.get(key, 0) + 1
            previous = reference.get(key, 0.0)
            reference[key] = previous + (reward - previous) / count
            counts[key] = count
    saved = summary["learned_values_and_counts"]
    for key, expected in reference.items():
        name, c, *indices = key
        if name == "shared_immediate":
            value, count = saved["q_immediate"][c], saved["n_immediate"][c]
        elif name == "blind":
            k = m.K_EVAL.index(indices[0])
            value, count = saved["q_blind"][c][k], saved["n_blind"][c][k]
        else:
            n, period = indices
            k = m.K_EVAL.index(period)
            value, count = saved["q_full"][c][n][k], saved["n_full"][c][n][k]
        assert value == pytest.approx(expected) and count == counts[key]
    assert sum(len(list(flatten(saved[key]))) for key in ("q_full", "q_blind", "q_immediate")) == 264
    assert all(type(v) is float for key in ("q_full", "q_blind", "q_immediate") for v in flatten(saved[key]))

    # Recompute all paired moments from fixture returns, preserving context strata.
    for key, (a, b) in e.PAIRS.items():
        context_means, variances = [], []
        for c in range(8):
            pair_a = [row[4] for row in eval_rows if row[0] == c and row[1] == a]
            pair_b = [row[4] for row in eval_rows if row[0] == c and row[1] == b]
            diffs = [x - y for x, y in zip(pair_a, pair_b)]
            mean = math.fsum(diffs) / 4
            variance = math.fsum((d - mean) ** 2 for d in diffs) / 3
            context_means.append(mean)
            variances.append(variance)
            observed = summary["evaluation"]["contexts"][c]["differences"][key]
            assert observed == pytest.approx(dict(mean=mean, sample_variance=variance))
        observed = summary["evaluation"]["differences"][key]
        assert observed["mean"] == pytest.approx(math.fsum(context_means) / 8)
        assert observed["conditional_mc_se"] == pytest.approx(math.sqrt(math.fsum(v / 4 for v in variances)) / 8)
    assert summary["evaluation"]["counts"]["FULL"]["probe_episodes"] > 0
    for start in range(0, len(eval_rows), 3):
        assert len({(row[0], row[2], row[3]) for row in eval_rows[start:start + 3]}) == 1

    # Failed synthetic partial dataset still publishes its actual learned state/counts.
    def interrupted_collect(model, training, check_time, batches, seed=m.SEED):
        training.update(m.new_counts())
        observation = completed("IMMEDIATE", None, 4, .25)
        model.observe(0, observation)
        m.count_execution(training, observation)
        raise KeyboardInterrupt("synthetic partial collection")
    monkeypatch.setattr(runner, "collect", interrupted_collect)
    assert runner.run(tmp_path / "partial") == 1
    partial = json.loads((tmp_path / "partial" / "summary.json").read_text())
    assert partial["status"] == partial["branch"] == "INCOMPLETE"
    assert partial["training"]["episodes"] == partial["exposure"]["scalar_value_updates"] == 1
    assert partial["learned_values_and_counts"]["q_immediate"][0] == .25
    assert partial["evaluation"] == {}


@pytest.mark.parametrize("native,information,probes,complete,branch", [
    (.002, .002, 1, True, "RM-A"), (.002, .001, 1, True, "RM-D"),
    (.002, -.1, 1, True, "RM-D"), (.001, .002, 1, True, "RM-B"),
    (-.001, .1, 0, True, "RM-B"), (-.002, .1, 1, True, "RM-C"),
    (0., .1, 0, True, "RM-B"), (.002, .002, 0, True, "INCOMPLETE"),
    (.0005, .002, 0, True, "INCOMPLETE"), (.002, .002, 1, False, "INCOMPLETE"),
    (None, .002, 1, True, "INCOMPLETE"), (.002, None, 1, True, "INCOMPLETE"),
])
def test_rule_boundaries(native, information, probes, complete, branch):
    assert e.reading_rule(native, information, probes, complete)["branch"] == branch
