"""Real tiny-host executions of the label-map probe.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real D agent, through the
frozen runner's own learner construction, evaluator construction and evaluation panels; then B08's
real checkpoint, B08's real `load_model` and this object's eight execution rules on the real D2
route. The tiny fit and the tiny harness are B08's own test fixtures, loaded by path, because this
object probes B08's checkpoints and must be checked against B08's panel and not against a second
copy of it. Technical checks, no result: nothing here asserts the direction or the size of any
measured quantity.
"""
import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_label_map_b08_tiny",
    Path(__file__).parents[1] / "label_content_b08/test_label_content_real_tiny.py")
b08tiny = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b08tiny)

import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402

shrunken = b08tiny.shrunken
build_harness = b08tiny.build_harness
point_at_the_tiny_fit = b08tiny.point_at_the_tiny_fit
comparable_metrics = b08tiny.comparable_metrics
SEED, EVALUATION_SEED = b08tiny.SEED, b08tiny.EVALUATION_SEED
LANES, HORIZON = b08tiny.LANES, b08tiny.HORIZON
N_UAVS, N_z, SKILL_PERIOD = b08tiny.N_UAVS, b08tiny.N_z, b08tiny.SKILL_PERIOD
ROLLOUTS, ADMISSION = b08tiny.ROLLOUTS, b08tiny.ADMISSION
PANEL_ROWS = HORIZON * LANES * N_UAVS  # executed (step, lane, agent) positions of one panel


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


@pytest.fixture(scope="module")
def tiny_fit(tmp_path_factory):
    """B08's own tiny fit, run once: its summary, its output root and its checkpoint."""
    out = tmp_path_factory.mktemp("label_map_fit")
    with shrunken():
        assert b08.run_fit(b08.SAVE_ARM, SEED, out, admission=ADMISSION) == 0
    return json.loads((out / "summary.json").read_text()), out


@pytest.fixture
def harness(tmp_path, tiny, tiny_fit):
    """B08's probe harness: its learner with the checkpoint loaded, and its evaluator."""
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(tmp_path / "harness",
                                                fit_out / b08.WEIGHTS_NAME)
    return summary, learner, evaluator, tmp_path / "harness"


def tables_are_b08s():
    """B08's rule tables, after a B09 run: the binding is off and nothing of B09's is left."""
    return (b08.ExecutionRule is not b09.MapExecutionRule
            and all(name not in b08.RULE_DEFINITIONS for name in b09.MAP_RULES)
            and b09.FROZEN_RULE not in b08.RANDOM_RULES
            and sorted(b08.RULE_DEFINITIONS) == sorted(b08.RULES))


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_runs_one_panel_per_label_and_takes_no_step(tmp_path, tiny, tiny_fit,
                                                              monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    out = tmp_path / "probe"
    head = b09.shared.e0._git("rev-parse", "HEAD")
    assert b09.main(["probe", "--seed", str(SEED), "--weights",
                     str(fit_out / b08.WEIGHTS_NAME), "--launch-sha", head,
                     "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == b09.OBJECT_ID and summary["command"] == "probe"
    assert summary["card"] == b09.CARD and "B09 prospective entry" in summary["card"]
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["reference_object_id"] == b08.OBJECT_ID
    assert summary["optimizer_steps"] == 0 and not any(summary["optimizer_calls"].values())
    assert summary["evaluation_panels"] == len(b09.RULES) == 8
    assert summary["evaluation_steps"] == LANES * HORIZON * len(b09.RULES)
    assert summary["evaluation_episodes"] == LANES * len(b09.RULES)
    assert summary["coordinator_training_mode"] is False
    assert (out / "construction" / "summary.json").exists()

    # (a) the loaded weights reproduce B08's own fit panel, bit for bit; B08's check, unrelaxed
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True and faithful["first_differing_world"] is None
    assert faithful["worlds"] == LANES and "not relaxed" in faithful["definition"]
    final_panel = [p for p in fit_summary["panels"] if p["panel_rollouts"] == ROLLOUTS][0]
    assert summary["rules_measured"]["as_trained"]["J_world_scores"] == final_panel[
        "native_scores_J"]
    assert summary["weights_record"]["sha256"] == fit_summary["final_weights"]["sha256"]
    for phase in ("learner", "evaluation"):
        assert set(summary[f"{phase}_config_differences_from_recorded_d1280"]) == set(
            b08.GEOMETRY_FIELDS)

    # (b) one panel per constant label, executed everywhere, at the frozen caps-10 cadence
    measured = summary["rules_measured"]
    assert sorted(measured) == sorted(b09.RULES)
    for label in range(N_z):
        record = measured[b09.constant_rule(label)]
        assert record["constant_label"] == label and record["constant_team_label"] == label
        assert record["agent_label_histogram"] == [
            PANEL_ROWS if index == label else 0 for index in range(N_z)]
        assert record["team_label_histogram"][label] == HORIZON * LANES
        assert record["agent_label_change_fraction"] == 0.
        assert record["team_label_change_fraction"] == 0.
        assert record["caps_applied"] == {}
        assert record["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)
        assert record["steps"] == LANES * HORIZON and record["lanes"] == LANES
        assert len(record["J_world_scores"]) == LANES
        assert not any(record["evaluator_optimizer_calls"].values())
        assert record["random_labels"] is None

    # (c) one uniformly drawn assignment per lane-episode, held for the whole episode
    frozen = measured[b09.FROZEN_RULE]
    assert frozen["agent_label_change_fraction"] == 0.
    assert frozen["team_label_change_fraction"] == 0.
    assert frozen["episodes"] == LANES and frozen["episodes_per_lane"] == [1] * LANES
    assert [entry["lane"] for entry in frozen["episode_labels"]] == list(range(LANES))
    assert [entry["step"] for entry in frozen["episode_labels"]] == [0] * LANES
    for entry in frozen["episode_labels"]:
        assert len(entry["agent_labels"]) == N_UAVS
        assert all(0 <= value < N_z for value in entry["agent_labels"])
        assert entry["distinct_agent_labels"] == len(set(entry["agent_labels"]))
        assert 0 <= entry["team_label"] < N_z
    # the drawn labels are the executed ones: the histogram is the drawn tuples, held all episode
    drawn = [label for entry in frozen["episode_labels"] for label in entry["agent_labels"]]
    assert frozen["agent_label_histogram"] == [HORIZON * drawn.count(label)
                                               for label in range(N_z)]
    assert frozen["random_labels"]["rule"] == b09.FROZEN_RULE
    assert frozen["random_labels"]["evaluation_seed"] == EVALUATION_SEED
    assert measured["as_trained"]["random_labels"] is None

    # the readings the notebook entry asked for
    assert set(summary["J_by_rule"]) == set(b09.RULES)
    assert summary["J_minus_as_trained"]["as_trained"] == 0.
    constants = {label: summary["J_by_rule"][b09.constant_rule(label)] for label in range(N_z)}
    best = summary["best_constant_label"]
    assert best["J"] == max(constants.values()) and best["label"] in constants
    assert sorted(best["ranking"]) == list(range(N_z))
    assert best["J_minus_as_trained"] == pytest.approx(
        best["J"] - summary["J_by_rule"]["as_trained"])
    assert best["max_minus_min"] == pytest.approx(max(constants.values()) - min(constants.values()))
    per_world = summary["per_world_best_constant"]
    assert len(per_world) == LANES
    for record in per_world:
        values = [measured[b09.constant_rule(label)]["J_world_scores"][record["world"]]
                  for label in range(N_z)]
        assert record["J"] == max(values)
        assert record["label"] == values.index(max(values))
        assert record["as_trained_J"] == measured["as_trained"]["J_world_scores"][record["world"]]
    assert summary["oracle_constant_envelope_J"] == pytest.approx(
        float(np.mean([record["J"] for record in per_world])))
    assert summary["oracle_envelope_minus_as_trained"] == pytest.approx(
        summary["oracle_constant_envelope_J"] - summary["J_by_rule"]["as_trained"])
    assert sum(summary["per_world_best_constant_label_counts"].values()) == LANES
    assert "upper envelope" in summary["oracle_envelope_selection_note"]
    assert "wsl_4070" in summary["interpretation_limit"]
    assert sorted(summary["rule_definitions"]) == sorted(b09.RULES)
    assert summary["wall_seconds"] > 0.

    # B08's tables are the ones B08 published with
    assert tables_are_b08s()


def test_the_probe_refuses_weights_whose_sha256_is_not_the_sidecars(tmp_path, tiny, tiny_fit,
                                                                    monkeypatch):
    _fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    copied = tmp_path / "copied"
    copied.mkdir()
    (copied / b08.WEIGHTS_NAME).write_bytes(
        (fit_out / b08.WEIGHTS_NAME).read_bytes() + b"tamper")
    (copied / b08.SIDECAR_NAME).write_text(
        (fit_out / b08.SIDECAR_NAME).read_text(), encoding="utf-8")
    out = tmp_path / "probe"
    assert b09.run_probe(SEED, copied / b08.WEIGHTS_NAME, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert "sha256" in summary["failure"] and summary["faithful_load"] is None
    assert "rules_measured" not in summary


def test_an_unfaithful_load_stops_the_probe_before_any_label_panel(tmp_path, tiny, tiny_fit,
                                                                   monkeypatch):
    """The reference is a panel this checkpoint cannot reproduce, so no label is ever executed."""
    _fit_summary, fit_out = tiny_fit
    reference = tmp_path / "reference_summary.json"
    damaged = json.loads((fit_out / "summary.json").read_text())
    for panel in damaged["panels"]:
        panel["native_scores_J"] = [value + 1. for value in panel["native_scores_J"]]
    reference.write_text(json.dumps(damaged), encoding="utf-8")
    point_at_the_tiny_fit(monkeypatch, reference)
    out = tmp_path / "probe"
    assert b09.run_probe(SEED, fit_out / b08.WEIGHTS_NAME, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["faithful_load"]["faithful_load"] is False
    assert summary["faithful_load"]["first_differing_world"] == 0
    assert "first differing world index 0" in summary["failure"]
    assert sorted(summary["rules_measured"]) == ["as_trained"]
    assert "best_constant_label" not in summary and "J_by_rule" not in summary
    assert tables_are_b08s()


# ---------------------------------------------------------------------------
# the panels, in B08's own harness
# ---------------------------------------------------------------------------


def test_the_as_trained_panel_is_the_same_panel_with_the_map_rules_bound(harness):
    """The baseline panel is B08's: binding this object's rules changes nothing about it."""
    summary, learner, evaluator, out = harness
    plain = b08.run_rule_panel("as_trained", learner, evaluator, summary, out, 0,
                               evaluation_seed=EVALUATION_SEED)
    with b09.bound_rules():
        assert b08.ExecutionRule is b09.MapExecutionRule
        mapped = b09.run_rule_panel("as_trained", learner, evaluator, summary, out, 1,
                                    evaluation_seed=EVALUATION_SEED)
    assert mapped["J_world_scores"] == plain["J_world_scores"]
    assert mapped["returns_U"] == plain["returns_U"]
    assert mapped["component_means"] == plain["component_means"]
    assert comparable_metrics(mapped["d2_metrics"]) == comparable_metrics(plain["d2_metrics"])
    assert mapped["agent_label_histogram"] == plain["agent_label_histogram"]
    assert mapped["team_label_histogram"] == plain["team_label_histogram"]
    assert mapped["agent_label_change_fraction"] == plain["agent_label_change_fraction"]
    assert mapped["decision_steps"] == plain["decision_steps"]
    assert mapped["definition"] == plain["definition"]  # B08's own definition, not a copy
    assert "constant_label" not in mapped and "episode_labels" not in mapped
    assert tables_are_b08s()


def test_a_constant_panel_executes_its_label_on_the_real_d2_route(harness):
    summary, learner, evaluator, out = harness
    agent = evaluator.agent
    with b09.bound_rules():
        record = b09.run_rule_panel("constant_3", learner, evaluator, summary, out, 0,
                                    evaluation_seed=EVALUATION_SEED)
    assert record["agent_label_histogram"] == [0, 0, 0, PANEL_ROWS, 0, 0]
    assert record["team_label_histogram"] == [0, 0, 0, HORIZON * LANES, 0, 0]
    assert record["agent_label_change_fraction"] == 0.
    assert record["caps_applied"] == {}
    assert record["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)  # the frozen cadence
    assert not any(record["evaluator_optimizer_calls"].values())
    # the write-back: the label the agent holds at the end of the panel is the executed one
    for lane in range(LANES):
        assert agent.env_agent_skills[lane].tolist() == [3] * N_UAVS
        assert agent.env_team_skills[lane] == 3
    # every wrapper and every instance override is off again
    assert "_batched_assign_skills" not in agent.__dict__
    assert (agent.d2_k_max, agent.d2_k_Z) == b08.ARM_CAPS
    assert agent.skill_discoverer._forward_hooks == {}
    assert tables_are_b08s()


def test_the_frozen_random_panel_is_reproducible_and_leaves_the_streams_untouched(harness):
    summary, learner, evaluator, out = harness
    before = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    with b09.bound_rules():
        first = b09.run_rule_panel(b09.FROZEN_RULE, learner, evaluator, summary, out, 0,
                                   evaluation_seed=EVALUATION_SEED)
        second = b09.run_rule_panel(b09.FROZEN_RULE, learner, evaluator, summary, out, 1,
                                    evaluation_seed=EVALUATION_SEED)
        other = b09.run_rule_panel(b09.FROZEN_RULE, learner, evaluator, summary, out, 2,
                                   evaluation_seed=EVALUATION_SEED + 100)
    after = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    # the generator is a function of (block, rule) alone, so the same panel twice agrees exactly
    assert first["J_world_scores"] == second["J_world_scores"]
    assert first["episode_labels"] == second["episode_labels"]
    assert first["agent_label_histogram"] == second["agent_label_histogram"]
    assert first["agent_label_change_fraction"] == 0.
    assert first["episodes_per_lane"] == [1] * LANES
    assert other["episode_labels"] != first["episode_labels"]  # another block, another stream
    # the draws touch no global NumPy, Python or torch stream
    assert before[0] == after[0]
    assert before[1][0] == after[1][0] and before[1][2:] == after[1][2:]
    np.testing.assert_array_equal(before[1][1], after[1][1])
    assert torch.equal(before[2], after[2])
    # the held assignment of the last panel is the one the agent still holds
    for entry in other["episode_labels"]:
        assert evaluator.agent.env_agent_skills[entry["lane"]].tolist() == entry["agent_labels"]
        assert evaluator.agent.env_team_skills[entry["lane"]] == entry["team_label"]
    assert "_batched_assign_skills" not in evaluator.agent.__dict__
    assert tables_are_b08s()
