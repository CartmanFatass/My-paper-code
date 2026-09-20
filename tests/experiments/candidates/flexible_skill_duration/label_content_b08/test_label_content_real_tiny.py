"""Real tiny-host executions of the label-content fit and probe.

Two lanes, twenty-step episodes, two rollouts, the real Scenario 1 environment and the real D agent,
through the frozen runner's own learner construction, evaluator construction, collector loop and
evaluation panels; then the real checkpoint, the real `load_model` and the four execution rules on
the real D2 route. Technical checks, no result: nothing here asserts the direction or the size of
any measured quantity. Kept apart from the fake-learner tests, whose helper forbids real
construction.
"""
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_label_content_b08 as label  # noqa: E402

SEED = sorted(label.BLOCKS)[0]
EVALUATION_SEED = label.BLOCKS[SEED]
LANES, HORIZON, ROLLOUTS = 2, 20, 2
N_UAVS, N_Z, N_z, SKILL_PERIOD = 6, 6, 6, 10
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}


@contextmanager
def shrunken():
    """The tiny host, applied to the shared module and to this object's own rollout schedule."""
    shared = b01.shared
    saved = {"TRAIN_LANES": shared.TRAIN_LANES, "EVAL_LANES": shared.EVAL_LANES,
             "HORIZON": shared.HORIZON, "PROCESS_START": shared.PROCESS_START}
    mine = {"ROLLOUTS": label.ROLLOUTS, "PANEL_ROLLOUTS": label.PANEL_ROLLOUTS}
    shared.TRAIN_LANES = shared.EVAL_LANES = LANES
    shared.HORIZON = HORIZON
    shared.PROCESS_START = shared.time.perf_counter()
    label.ROLLOUTS, label.PANEL_ROLLOUTS = ROLLOUTS, tuple(range(1, ROLLOUTS + 1))
    try:
        yield shared
    finally:
        for name, value in saved.items():
            setattr(shared, name, value)
        for name, value in mine.items():
            setattr(label, name, value)


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


@pytest.fixture(scope="module")
def tiny_fit(tmp_path_factory):
    """One tiny fit, run once: its summary, its output root and its checkpoint."""
    out = tmp_path_factory.mktemp("label_content_fit")
    with shrunken():
        assert label.run_fit(label.SAVE_ARM, SEED, out, admission=ADMISSION) == 0
    return json.loads((out / "summary.json").read_text()), out


def fit_without_the_save(out):
    """The same route with the save left out: this object's identity, the frozen `run_fit` only."""
    label.bind(wrap=True)
    label.CURRENT.update(label_content_arm=label.SAVE_ARM, admission=ADMISSION, agent=None)
    try:
        assert b01.run_fit(label.SAVE_ARM, SEED, out) == 0
    finally:
        label.CURRENT.update(label_content_arm=None, admission=None, summary=None, agent=None)
        if label.shared.base_summary is label.base_summary:
            label.shared.base_summary = label._orig_base_summary
        if b01.build_learner is label.build_learner:
            b01.build_learner = label._orig_build_learner
    summary = json.loads((out / "summary.json").read_text())
    assert summary["final_weights"] is None
    assert not (out / label.WEIGHTS_NAME).exists()
    return summary


def comparable_metrics(metrics):
    """The d2 metrics without the wall-clock fields, which are not a property of the run."""
    return {key: value for key, value in metrics.items()
            if key != "coordinator_inference_seconds"}


def point_at_the_tiny_fit(monkeypatch, fit_summary_path):
    """`faithful_load` reads the tiny fit's own last panel; the D1280 config guard is untouched."""
    monkeypatch.setitem(label.REFERENCE_FITS, SEED, Path(fit_summary_path))
    monkeypatch.setitem(label.REFERENCE, "object_id", label.OBJECT_ID)
    monkeypatch.setitem(label.REFERENCE, "factorial_arm", label.SAVE_ARM)
    monkeypatch.setitem(label.REFERENCE, "panel_rollouts", ROLLOUTS)


# ---------------------------------------------------------------------------
# the fit
# ---------------------------------------------------------------------------


def test_the_fit_is_the_frozen_route_with_the_weights_written_after_it(tmp_path, tiny, tiny_fit):
    saved, out = tiny_fit
    plain = fit_without_the_save(tmp_path / "plain")

    assert saved["status"] == "complete" and saved["failure"] is None
    assert saved["label_content_object"] == label.OBJECT_ID
    assert saved["label_content_arm"] == saved["factorial_arm"] == label.SAVE_ARM
    assert saved["arm_overrides"] == {}
    for phase in ("learner_config", "evaluation_config"):
        assert (saved[phase]["skill_cap_k_max"], saved[phase]["team_cap_k_Z"]) == label.ARM_CAPS
        assert saved[phase]["k"] == SKILL_PERIOD
        assert saved[phase]["n_Z"] == saved[phase]["n_z"] == N_Z
        recorded = saved[f"{phase}_differences_from_recorded_d1280"]
        assert recorded["available"] is True and recorded["reason"] is None
        # the only differences from the published D1280 fit are the shrunken host's geometry
        assert set(recorded["differences"]) == set(label.GEOMETRY_FIELDS)

    # With and without the save: the same panels, the same training rows, the same construction.
    assert [p["panel_rollouts"] for p in saved["panels"]] == [
        p["panel_rollouts"] for p in plain["panels"]]
    for mine, theirs in zip(saved["panels"], plain["panels"]):
        assert mine["native_scores_J"] == theirs["native_scores_J"]
        assert mine["returns_U"] == theirs["returns_U"]
        assert mine["component_means"] == theirs["component_means"]
        assert comparable_metrics(mine["d2_metrics"]) == comparable_metrics(
            theirs["d2_metrics"])
    for mine, theirs in zip(saved["training_rows"], plain["training_rows"]):
        assert mine["episode_returns_U"] == theirs["episode_returns_U"]
        assert mine["return_sums"] == theirs["return_sums"]
        assert mine["losses"] == theirs["losses"]
        assert mine["relative_initialization_displacement"] == theirs[
            "relative_initialization_displacement"]
        assert mine["segments"] == theirs["segments"]
    assert saved["learner_config"] == plain["learner_config"]
    assert saved["evaluation_config"] == plain["evaluation_config"]
    assert saved["initial_parameter_norms"] == plain["initial_parameter_norms"]
    assert saved["optimizer_calls"] == plain["optimizer_calls"]
    assert label.bit_identical_panels(saved, plain)["bit_identical"] is True

    weights = saved["final_weights"]
    path = out / label.WEIGHTS_NAME
    assert path.exists() and weights["sha256"] == label.file_sha256(path)
    assert weights["bytes"] == path.stat().st_size > 0
    assert weights["block_seed"] == SEED and weights["arm"] == label.SAVE_ARM
    assert json.loads((out / label.SIDECAR_NAME).read_text()) == weights
    inventory = weights["inventory"]
    assert {"skill_coordinator", "skill_discoverer", "config"} <= set(inventory["keys"])
    # the state-independent log-std the deterministic action's Gaussian uses is in the file
    assert inventory["low_level_actor_logstd_key"] == "actor.act.action_out.logstd._bias"
    # `use_valuenorm` is True on this construction and `use_obsnorm`/`use_statenorm` are False
    assert inventory["valuenorm_state"] == ["coordinator", "discoverer"]
    assert inventory["normalization_state"] == []
    assert saved["learner_config"]["use_valuenorm"] is True
    assert saved["learner_config"]["use_obsnorm"] is False
    assert saved["learner_config"]["use_statenorm"] is False
    assert label.CURRENT["agent"] is None
    assert b01.build_learner is label._orig_build_learner


def test_a_real_fit_that_fails_saves_nothing(tmp_path, tiny, monkeypatch):
    out = tmp_path / "broken"

    def broken(*args, **kwargs):
        raise ValueError("synthetic collector failure")

    monkeypatch.setattr(b01, "collect_training", broken)
    assert label.run_fit(label.SAVE_ARM, SEED, out, admission=ADMISSION) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete" and summary["final_weights"] is None
    assert not (out / label.WEIGHTS_NAME).exists()
    assert not (out / label.SIDECAR_NAME).exists()


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_reproduces_the_fits_own_final_panel_and_takes_no_step(
        tmp_path, tiny, tiny_fit, monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    out = tmp_path / "probe"
    head = label.shared.e0._git("rev-parse", "HEAD")
    assert label.main(["probe", "--seed", str(SEED), "--weights",
                       str(fit_out / label.WEIGHTS_NAME), "--launch-sha", head,
                       "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == label.OBJECT_ID and summary["command"] == "probe"
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["optimizer_steps"] == 0 and not any(summary["optimizer_calls"].values())
    assert summary["evaluation_panels"] == len(label.RULES)
    assert summary["evaluation_steps"] == LANES * HORIZON * len(label.RULES)
    assert summary["evaluation_episodes"] == LANES * len(label.RULES)
    assert summary["coordinator_training_mode"] is False

    # (a) the loaded weights reproduce the fit's own rollout-2 panel, bit for bit
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True and faithful["first_differing_world"] is None
    assert faithful["worlds"] == LANES
    assert "Evaluator._sync" in faithful["weight_transfer"]
    final_panel = [p for p in fit_summary["panels"] if p["panel_rollouts"] == ROLLOUTS][0]
    assert summary["rules_measured"]["as_trained"]["J_world_scores"] == final_panel[
        "native_scores_J"]
    assert summary["weights_record"]["sha256"] == fit_summary["final_weights"]["sha256"]
    # the construction is the published D1280 fit's, up to the shrunken host's geometry
    for phase in ("learner", "evaluation"):
        assert set(summary[f"{phase}_config_differences_from_recorded_d1280"]) == set(
            label.GEOMETRY_FIELDS)

    # (b) the capture is the panel's own, and the label sweep reproduces its action exactly
    capture = summary["capture"]
    assert capture["actor"]["actor_calls"] == HORIZON  # once per step, all (lane, agent) rows
    assert capture["actor"]["captured_rows"] == capture["actor"][
        "captured_calls"] * LANES * N_UAVS
    assert capture["low_level_critic"]["critic_calls"] == HORIZON
    action = summary["label_effect"]["action"]
    assert action["labels"] == N_z and action["action_dimensions"] == 3
    assert action["rows"] == capture["actor"]["captured_rows"]
    assert action["recomputed_action_at_held_label_reproduces_the_panel"] is True
    assert action["max_absolute_difference_from_the_panel_action"] == 0.
    assert len(action["action_standard_deviation_per_dimension"]) == 3
    assert all(v > 0. for v in action["action_standard_deviation_per_dimension"])
    assert action["rms_label_deviation_over_std_mean"] >= 0.
    assert summary["label_effect"]["action_standard_deviation"]["head"] == "DiagGaussian"
    assert summary["label_effect"]["action_standard_deviation"][
        "mean_and_std_share_a_space"] is True
    value = summary["label_effect"]["low_level_value"]
    assert value["labels"] == N_Z and value["rows"] == capture["low_level_critic"]["captured_rows"]
    assert value["recomputed_value_at_held_label_reproduces_the_panel"] is True
    assert value["value_norm"]["use_valuenorm"] is True

    # (c) the four rules, on the same worlds, each from a freshly reset evaluator
    measured = summary["rules_measured"]
    assert sorted(measured) == sorted(label.RULES)
    for name in label.RULES:
        record = measured[name]
        assert len(record["J_world_scores"]) == LANES
        assert record["steps"] == LANES * HORIZON
        assert record["lanes"] == LANES and record["steps_recorded"] == HORIZON
        assert record["reset_rows"] == LANES
        assert sum(record["agent_label_histogram"]) == HORIZON * LANES * N_UAVS
        assert sum(record["team_label_histogram"]) == HORIZON * LANES
        assert record["agent_label_comparisons"] == (HORIZON - 1) * LANES * N_UAVS
        assert not any(record["evaluator_optimizer_calls"].values())
    assert measured["as_trained"]["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)
    assert measured["as_trained"]["caps_applied"] == {}
    assert measured["frozen_episode"]["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)
    assert measured["frozen_episode"]["agent_label_change_fraction"] == 0.
    assert measured["frozen_episode"]["team_label_change_fraction"] == 0.
    assert measured["uniform_every_step"]["decision_steps"] == LANES * HORIZON  # every step
    assert measured["uniform_every_step"]["decision_fraction"] == 1.
    assert measured["uniform_every_step"]["caps_applied"] == {"d2_k_max": 1, "d2_k_Z": 1}
    assert measured["uniform_every_step"]["agent_label_change_fraction"] == pytest.approx(
        1. - 1. / N_z, abs=.15)
    assert measured["uniform_every_10"]["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)
    assert measured["uniform_every_10"]["caps_applied"] == {}
    assert measured["uniform_every_10"]["agent_label_change_fraction"] <= 1. / SKILL_PERIOD + 1e-12
    for name in ("uniform_every_step", "uniform_every_10"):
        assert measured[name]["random_labels"]["evaluation_seed"] == EVALUATION_SEED
    assert measured["as_trained"]["random_labels"] is None
    assert summary["J_minus_as_trained"]["as_trained"] == 0.
    assert set(summary["J_by_rule"]) == set(label.RULES)


def test_the_probe_refuses_weights_whose_sha256_is_not_the_sidecars(
        tmp_path, tiny, tiny_fit, monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    copied = tmp_path / "copied"
    copied.mkdir()
    (copied / label.WEIGHTS_NAME).write_bytes(
        (fit_out / label.WEIGHTS_NAME).read_bytes() + b"tamper")
    (copied / label.SIDECAR_NAME).write_text(
        (fit_out / label.SIDECAR_NAME).read_text(), encoding="utf-8")
    out = tmp_path / "probe"
    assert label.run_probe(SEED, copied / label.WEIGHTS_NAME, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert "sha256" in summary["failure"] and summary["faithful_load"] is None


def test_an_unfaithful_load_stops_the_probe_at_the_first_differing_world(
        tmp_path, tiny, tiny_fit, monkeypatch):
    """The reference is a panel this checkpoint cannot reproduce, so the probe stops there."""
    fit_summary, fit_out = tiny_fit
    reference = tmp_path / "reference_summary.json"
    damaged = json.loads((fit_out / "summary.json").read_text())
    for panel in damaged["panels"]:
        panel["native_scores_J"] = [v + 1. for v in panel["native_scores_J"]]
    reference.write_text(json.dumps(damaged), encoding="utf-8")
    point_at_the_tiny_fit(monkeypatch, reference)
    out = tmp_path / "probe"
    assert label.run_probe(SEED, fit_out / label.WEIGHTS_NAME, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["faithful_load"]["faithful_load"] is False
    assert summary["faithful_load"]["first_differing_world"] == 0
    assert "first differing world index 0" in summary["failure"]
    # the label sweep and the other three rules are not run once the load is not faithful
    assert sorted(summary["rules_measured"]) == ["as_trained"]
    assert "label_effect" not in summary


# ---------------------------------------------------------------------------
# the harness: repeatability and the wrappers coming off
# ---------------------------------------------------------------------------


def build_harness(out, weights, seed=SEED):
    """The probe's own construction: a fit's learner with the checkpoint loaded, and an evaluator."""
    label.bind()
    shared = label.shared
    summary = shared.base_summary(label.ARMS[label.SAVE_ARM][0], training_seed=seed,
                                  evaluation_seed=EVALUATION_SEED, object_id=label.OBJECT_ID,
                                  card=label.CARD, caps=None)
    summary.update(command="probe", factorial_arm=label.SAVE_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=label.ARMS[label.SAVE_ARM][1],
                   ordinary_wall_plan_seconds=None, cost_law="zero optimizer steps")
    out.mkdir(parents=True, exist_ok=True)
    _envs, learner, _theta0, _counters = b01.build_learner(label.SAVE_ARM, summary, out, seed)
    learner.load_model(str(weights))
    learner.train(False)
    evaluator = b01.build_evaluator(label.SAVE_ARM, summary, out, EVALUATION_SEED)
    return summary, learner, evaluator


def test_the_same_rule_twice_in_one_harness_gives_identical_scores(tmp_path, tiny, tiny_fit):
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(
        tmp_path / "harness", fit_out / label.WEIGHTS_NAME)
    first = label.run_rule_panel("as_trained", learner, evaluator, summary,
                                 tmp_path / "harness", 0, evaluation_seed=EVALUATION_SEED)
    second = label.run_rule_panel("as_trained", learner, evaluator, summary,
                                  tmp_path / "harness", 1, evaluation_seed=EVALUATION_SEED)
    assert first["J_world_scores"] == second["J_world_scores"]
    assert first["returns_U"] == second["returns_U"]
    assert first["component_means"] == second["component_means"]
    assert comparable_metrics(first["d2_metrics"]) == comparable_metrics(
        second["d2_metrics"])
    assert first["agent_label_histogram"] == second["agent_label_histogram"]

    # A uniform rule is reproducible too: its generator is a function of (block, rule) alone.
    third = label.run_rule_panel("uniform_every_10", learner, evaluator, summary,
                                 tmp_path / "harness", 2, evaluation_seed=EVALUATION_SEED)
    fourth = label.run_rule_panel("uniform_every_10", learner, evaluator, summary,
                                  tmp_path / "harness", 3, evaluation_seed=EVALUATION_SEED)
    assert third["J_world_scores"] == fourth["J_world_scores"]
    assert third["agent_label_histogram"] == fourth["agent_label_histogram"]

    # Every wrapper and every instance override is off again.
    assert "_batched_assign_skills" not in evaluator.agent.__dict__
    assert (evaluator.agent.d2_k_max, evaluator.agent.d2_k_Z) == label.ARM_CAPS
    assert evaluator.agent.skill_discoverer._forward_hooks == {}
    assert evaluator.agent.skill_discoverer.critic._forward_pre_hooks == {}
    assert evaluator.agent.skill_discoverer.critic._forward_hooks == {}


def test_a_rule_that_cannot_be_imposed_leaves_the_agent_untouched(tmp_path, tiny, tiny_fit):
    _fit_summary, fit_out = tiny_fit
    summary, _learner, evaluator = build_harness(
        tmp_path / "harness_guard", fit_out / label.WEIGHTS_NAME)
    agent = evaluator.agent
    original_costs = (agent.d2_cost_c, agent.d2_cost_c_Z)
    agent.d2_cost_c = .25  # a construction the rules are not defined on
    try:
        rule = label.ExecutionRule("uniform_every_step", agent,
                                   generator=label.label_generator(EVALUATION_SEED, "x"))
        with pytest.raises(ValueError, match="infinite interruption costs"):
            with rule.attached():
                pass
    finally:
        agent.d2_cost_c, agent.d2_cost_c_Z = original_costs
    assert "_batched_assign_skills" not in agent.__dict__
    assert (agent.d2_k_max, agent.d2_k_Z) == label.ARM_CAPS


def test_the_captures_leave_the_panel_bit_identical(tmp_path, tiny, tiny_fit):
    """The same panel with and without the actor/critic captures attached."""
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(
        tmp_path / "harness_capture", fit_out / label.WEIGHTS_NAME)
    plain = label.run_rule_panel("as_trained", learner, evaluator, summary,
                                 tmp_path / "harness_capture", 0,
                                 evaluation_seed=EVALUATION_SEED)
    actor = label.ActorCapture(evaluator.agent)
    critic = label.CriticCapture(evaluator.agent)
    captured = label.run_rule_panel("as_trained", learner, evaluator, summary,
                                    tmp_path / "harness_capture", 1,
                                    evaluation_seed=EVALUATION_SEED, captures=(actor, critic))
    assert captured["J_world_scores"] == plain["J_world_scores"]
    assert captured["component_means"] == plain["component_means"]
    assert comparable_metrics(captured["d2_metrics"]) == comparable_metrics(
        plain["d2_metrics"])
    assert actor.calls == HORIZON and critic.calls == HORIZON
    assert all(entry["deterministic"] is True for entry in actor.captured)
    assert all(entry["compact_context"] is None and entry["central_input"] is None
               for entry in actor.captured)
    assert all("value" in entry for entry in critic.captured)
    # the label sweep at the held label is the action the panel produced, row for row
    standard_deviation, _note = label.action_standard_deviation(
        evaluator.agent.skill_discoverer.actor)
    result = label.label_action_effect(evaluator.agent.skill_discoverer, actor.captured,
                                       standard_deviation, n_z=N_z)
    assert result["recomputed_action_at_held_label_reproduces_the_panel"] is True
    assert np.isfinite(result["rms_label_deviation_over_std_mean"])
