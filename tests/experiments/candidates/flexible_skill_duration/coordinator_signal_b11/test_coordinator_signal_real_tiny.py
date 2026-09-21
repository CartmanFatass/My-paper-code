"""Real tiny-host executions of the coordinator-signal probe.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real D agent, through the
frozen runner's own learner construction, evaluator construction and evaluation panel; then B08's
real checkpoint, B08's real `load_model`, the frozen collector's own per-step calls on the real D2
route, and the real `update_coordinator_d2` path on a copy of the agent for the comparison. The
tiny fit and the tiny harness are B08's own test fixtures, loaded by path, because this object
probes B08's checkpoints and is read against B09's and B10's panels, and all of them must be
checked against one panel and not against copies of it. Technical checks, no result: nothing here
asserts the direction or the size of any measured quantity.
"""
import copy
import importlib.util
import json
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
    "fsd_coordinator_signal_b08_tiny",
    Path(__file__).parents[1] / "label_content_b08/test_label_content_real_tiny.py")
b08tiny = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b08tiny)

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_coordinator_signal_b11 as b11  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

shrunken = b08tiny.shrunken
build_harness = b08tiny.build_harness
point_at_the_tiny_fit = b08tiny.point_at_the_tiny_fit
SEED, EVALUATION_SEED = b08tiny.SEED, b08tiny.EVALUATION_SEED
LANES, HORIZON = b08tiny.LANES, b08tiny.HORIZON
N_UAVS, N_z, SKILL_PERIOD = b08tiny.N_UAVS, b08tiny.N_z, b08tiny.SKILL_PERIOD
ROLLOUTS = 2  # the tiny host's collection; the production default is 4
DECISIONS = HORIZON // SKILL_PERIOD  # team decisions per lane-episode on the frozen cadence


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


@pytest.fixture(scope="module")
def tiny_fit(tmp_path_factory):
    """B08's own tiny fit, run once: its summary, its output root and its checkpoint."""
    out = tmp_path_factory.mktemp("coordinator_signal_fit")
    with shrunken():
        assert b08.run_fit(b08.SAVE_ARM, SEED, out, admission=b08tiny.ADMISSION) == 0
    return json.loads((out / "summary.json").read_text()), out


@pytest.fixture
def harness(tmp_path, tiny, tiny_fit):
    """B08's probe harness: its learner with the checkpoint loaded, and its evaluator."""
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(tmp_path / "harness",
                                                fit_out / b08.WEIGHTS_NAME)
    out = tmp_path / "harness"
    return summary, learner, evaluator, out


def collection_envs(seed=SEED):
    return b11.shared.e0._make_envs(LANES, b11.world_base_seed(seed), N_UAVS,
                                    b11.shared.N_USERS, HORIZON)


def plain_measure(learner):
    """The probe's own measurement, with nothing else attached."""
    def measure(rollout, states, observations):
        frame = b11.rollout_frame(learner, HORIZON, states.copy(), observations.copy(),
                                  rollout, LANES)
        return frame, {"rows_M": frame["rows_M"], "rows_M_agent": frame["rows_M_agent"],
                       "rows_M_team": frame["rows_M_team"],
                       "flushed_open_segments": frame["flushed_open_segments"],
                       "standardisation": frame["standardisation"],
                       "coordinator_bootstrap": frame["bootstrap"]}
    return measure


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_collects_training_law_rollouts_and_takes_no_step(
        tmp_path, tiny, tiny_fit, monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    out = tmp_path / "probe"
    head = b11.shared.e0._git("rev-parse", "HEAD")
    assert b11.main(["probe", "--seed", str(SEED), "--weights",
                     str(fit_out / b08.WEIGHTS_NAME), "--launch-sha", head,
                     "--output-root", str(out), "--rollouts", str(ROLLOUTS)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == b11.OBJECT_ID and summary["command"] == "probe"
    assert summary["card"] == b11.CARD and "B11" in summary["card"]
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["rollouts"] == ROLLOUTS

    # the probe takes no optimizer step and moves no parameter or running statistic
    assert summary["optimizer_steps"] == 0 and not any(summary["optimizer_calls"].values())
    state = summary["learner_state"]
    assert state["unchanged"] is True
    assert state["before"]["parameter_digest"] == state["after"]["parameter_digest"]
    assert state["before"]["value_norm_coordinator"] == state["after"]["value_norm_coordinator"]
    assert state["before"]["value_norm_discoverer"] == state["after"]["value_norm_discoverer"]
    assert "update_coordinator_d2" in state["definition"]
    assert summary["collection_rng"]["restored"] is True
    assert (summary["collection_rng"]["digest_before"]
            == summary["collection_rng"]["digest_after"])

    # (a) the frozen panel, and the faithful-load check B09 does not relax
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True and faithful["first_differing_world"] is None
    assert faithful["worlds"] == LANES and "not relaxed" in faithful["definition"]
    final_panel = [p for p in fit_summary["panels"]
                   if p["panel_rollouts"] == b08tiny.ROLLOUTS][0]
    assert summary["as_trained_world_scores"] == final_panel["native_scores_J"]
    assert summary["rules_measured"]["as_trained"]["J_world_scores"] == final_panel[
        "native_scores_J"]
    assert summary["weights_record"]["sha256"] == fit_summary["final_weights"]["sha256"]
    assert summary["evaluation_panels"] == 1

    # (b) the collection: the frozen loop's exposure, on this object's own worlds
    assert summary["collection_lanes"] == LANES
    assert summary["collection_transitions"] == LANES * HORIZON * ROLLOUTS
    assert summary["collection_episodes"] == LANES * ROLLOUTS
    assert summary["collection_agent_step_batches"] == HORIZON * ROLLOUTS
    assert summary["collection_lane_seeds"] == list(
        range(SEED + 500, SEED + 500 + b11.shared.TRAIN_LANES))
    assert summary["collection_seeds"] == {str(r): b11.collection_seed(SEED, r)
                                           for r in range(ROLLOUTS)}
    assert "not the fit's training worlds" in summary["collection_worlds"]
    assert len(summary["collection_rows"]) == ROLLOUTS == len(summary["collection_geometry"])
    lines = (out / "construction" / "collection.jsonl").read_text().strip().splitlines()
    assert len(lines) == ROLLOUTS

    for index, geometry in enumerate(summary["collection_geometry"]):
        assert geometry["rows_M"] == LANES * DECISIONS
        assert geometry["rows_M_agent"] == LANES * DECISIONS * N_UAVS
        assert geometry["rows_M_team"] == LANES * DECISIONS
        assert geometry["flushed_open_segments"] == 0  # every lane ends terminal
        assert geometry["segment_length_agent_mean"] == float(SKILL_PERIOD)
        assert geometry["segment_length_team_mean"] == float(SKILL_PERIOD)
        assert set(geometry["cause_counts"]) == {"reset", "team_gap", "team_cap", "gap", "cap"}
        assert geometry["cause_counts"]["reset"] == LANES
        assert geometry["cause_counts"]["team_cap"] == LANES * (DECISIONS - 1)
        assert not any(geometry["cause_counts"][name] for name in ("team_gap", "gap", "cap"))
        assert geometry["frozen_host_geometry"] is False  # the shrunken host, never the frozen one
        row = summary["collection_rows"][index]
        assert row["rollout_index"] == index
        assert row["collection_seed"] == b11.collection_seed(SEED, index)
        assert row["completed_episodes"] == LANES
        assert row["standardisation"]["masked_entries"] == geometry["rows_M"] * (1 + N_UAVS)
        assert not any(row["optimizer_calls_total"].values())  # after every rollout, not only once
    # the recorded D1280 fit's own row geometry is published even where it is not enforced
    assert summary["recorded_row_geometry"]["rows_M"] == 800
    assert summary["recorded_row_geometry"]["rows_M_agent"] == 4800

    # the measures
    measures = summary["measures"]
    assert measures["rollouts"] == ROLLOUTS
    assert measures["agent_rows"] == LANES * DECISIONS * N_UAVS * ROLLOUTS
    assert measures["team_rows"] == LANES * DECISIONS * ROLLOUTS
    assert measures["clusters"] == LANES * ROLLOUTS
    assert sorted(measures["agent_label_table"]) == [str(label) for label in range(N_z)]
    counts = [measures["agent_label_table"][str(label)]["count"] for label in range(N_z)]
    assert sum(counts) == measures["agent_rows"]
    assert sorted(measures["agent_label_ranking"]) == sorted(
        label for label in range(N_z) if counts[label])
    assert measures["agent_label_spread"]["max_minus_min"] >= 0.
    assert measures["additive_reference"]["segments"] == measures["team_rows"]
    assert measures["additive_reference"]["clusters"] == measures["clusters"]
    assert measures["additive_reference_with_state_control"]["state_control"] is True
    assert measures["label_law"]["uniform_entropy"] == pytest.approx(float(np.log(N_z)))
    assert sum(measures["label_law"]["agent_label_counts"]) == measures["agent_rows"]
    assert measures["policy_gradient"]["entropy_coefficient_lambda_h"] == pytest.approx(.07)
    assert len(measures["per_rollout"]) == ROLLOUTS
    assert summary["update_law"]["ppo_epochs"] == 15
    assert summary["update_law"]["coordinator_batch_size"] == 1280
    assert "takes 15 optimizer steps" in summary["update_law"]["note"]
    assert summary["coordinator_training_mode"] is False  # put back after the collection
    assert (out / "construction" / "summary.json").exists()
    assert "wsl_4070" in summary["interpretation_limit"]
    assert summary["wall_seconds"] > 0.


def test_an_unfaithful_load_stops_the_probe_before_any_collection(tmp_path, tiny, tiny_fit,
                                                                  monkeypatch):
    """The reference is a panel this checkpoint cannot reproduce, so nothing is ever collected."""
    _fit_summary, fit_out = tiny_fit
    reference = tmp_path / "reference_summary.json"
    damaged = json.loads((fit_out / "summary.json").read_text())
    for panel in damaged["panels"]:
        panel["native_scores_J"] = [value + 1. for value in panel["native_scores_J"]]
    reference.write_text(json.dumps(damaged), encoding="utf-8")
    point_at_the_tiny_fit(monkeypatch, reference)
    out = tmp_path / "probe"
    assert b11.run_probe(SEED, fit_out / b08.WEIGHTS_NAME, out, rollouts=ROLLOUTS) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["faithful_load"]["faithful_load"] is False
    assert "first differing world index 0" in summary["failure"]
    assert "measures" not in summary and "collection_rows" not in summary


# ---------------------------------------------------------------------------
# the credit arithmetic, against the real update path
# ---------------------------------------------------------------------------


def test_the_probe_advantages_are_the_real_update_paths_own(harness):
    """The copy runs `update_coordinator` for real; the probed agent takes no step at all.

    The copy is a fresh agent of the same construction carrying a deep copy of the probed agent's
    rollout buffer and open-segment state, so the real `update_coordinator_d2` path computes its
    advantages from exactly the buffer the probe read, with the same bootstrap dictionary.
    """
    summary, learner, _evaluator, out = harness
    restore = b08.scale._forbid_optimizer_steps(learner)  # the probed agent may never step
    captured = {}

    def measure(rollout, states, observations):
        bootstrap = b11.coordinator_bootstrap_values(learner, states.copy(), observations.copy())
        other = HMASDAgent(copy.deepcopy(learner.config),
                           log_dir=str(out / f"copy_logs_{rollout}"), device=torch.device("cpu"))
        other.skill_coordinator.load_state_dict(learner.skill_coordinator.state_dict())
        other.value_norm_coordinator = copy.deepcopy(learner.value_norm_coordinator)
        other.rollout_buffer = copy.deepcopy(learner.rollout_buffer)
        other.d2_open_agent_segments = copy.deepcopy(learner.d2_open_agent_segments)
        other.d2_open_team_segments = copy.deepcopy(learner.d2_open_team_segments)
        other.d2_metrics = copy.deepcopy(learner.d2_metrics)
        original = other.rollout_buffer.compute_high_level_advantages

        def wrapped(*args, **kwargs):  # capture the tables the update path just filled
            value = original(*args, **kwargs)
            tables = other.rollout_buffer.get_d2_tables(HORIZON)
            captured[rollout] = {key: np.array(tables[key], copy=True) for key in
                                 ("agent_advantages", "team_advantages", "agent_returns",
                                  "team_returns", "agent_valid", "team_valid")}
            captured[rollout]["gamma"] = kwargs.get("gamma")
            captured[rollout]["value_normalizer"] = kwargs.get("value_normalizer", "absent")
            return value

        other.rollout_buffer.compute_high_level_advantages = wrapped
        other.update_coordinator(HORIZON, bootstrap_values=copy.deepcopy(bootstrap))
        assert other.d2_metrics["optimizer_steps"] > 0  # the copy really ran the update
        frame = b11.rollout_frame(learner, HORIZON, states.copy(), observations.copy(),
                                  rollout, LANES)
        return frame, {"rows_M": frame["rows_M"]}

    try:
        with b11.shared.e0._preserve_rng():
            frames = b11.collect_training_law(collection_envs(), learner, summary, out,
                                              rollouts=1, training_seed=SEED, measure=measure)
    finally:
        for optimizer, original in restore:
            optimizer.step = original

    frame = frames[0]
    tables = captured[0]
    assert tables["gamma"] == learner.config.gamma and tables["value_normalizer"] is None
    steps, lanes = np.where(tables["team_valid"])
    assert len(steps) == frame["rows_M"] == frame["rows_M_team"]
    assert np.array_equal(steps, frame["team"]["step"]) and np.array_equal(
        lanes, frame["team"]["lane"])
    # exact equality, not a tolerance: the same arithmetic on the same buffer
    assert np.array_equal(frame["team"]["advantage"],
                          tables["team_advantages"][steps, lanes].astype(np.float64))
    assert np.array_equal(frame["agent"]["advantage"],
                          tables["agent_advantages"][steps, lanes].reshape(-1).astype(np.float64))
    assert np.array_equal(frame["team"]["return"],
                          tables["team_returns"][steps, lanes].astype(np.float64))
    assert np.array_equal(frame["agent"]["return"],
                          tables["agent_returns"][steps, lanes].reshape(-1).astype(np.float64))
    assert np.array_equal(tables["agent_valid"][steps, lanes],
                          np.ones((frame["rows_M"], N_UAVS), dtype=bool))


def test_the_collection_is_reproducible_for_the_same_seed(tmp_path, tiny, tiny_fit):
    """Two fresh harnesses, the same weights and the same seeds: the same rows, exactly."""
    _fit_summary, fit_out = tiny_fit
    frames = []
    for index in range(2):
        summary, learner, _evaluator = build_harness(tmp_path / f"harness_{index}",
                                                     fit_out / b08.WEIGHTS_NAME)
        restore = b08.scale._forbid_optimizer_steps(learner)
        try:
            with b11.shared.e0._preserve_rng():
                frames.append(b11.collect_training_law(
                    collection_envs(), learner, summary, tmp_path / f"harness_{index}",
                    rollouts=1, training_seed=SEED, measure=plain_measure(learner))[0])
        finally:
            for optimizer, original in restore:
                optimizer.step = original
    first, second = frames
    for side in ("team", "agent"):
        for column in ("label", "advantage", "standardised_advantage", "return", "value",
                       "reward", "step", "lane"):
            assert np.array_equal(first[side][column], second[side][column]), (side, column)
    assert first["standardisation"] == second["standardisation"]
    assert first["bootstrap"] == second["bootstrap"]
    # and a different collection seed is a different collection
    summary, learner, _evaluator = build_harness(tmp_path / "harness_other",
                                                 fit_out / b08.WEIGHTS_NAME)
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        with b11.shared.e0._preserve_rng():
            other = b11.collect_training_law(
                collection_envs(), learner, summary, tmp_path / "harness_other",
                rollouts=1, training_seed=SEED + 1, measure=plain_measure(learner))[0]
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    assert not np.array_equal(other["agent"]["label"], first["agent"]["label"])


def test_the_collection_consumes_randomness_and_the_probe_gives_it_back(harness):
    """The collection really draws from the global streams; the probe's wrapper restores them."""
    summary, learner, _evaluator, out = harness
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        before = b11.rng_digest()
        with b11.shared.e0._preserve_rng():
            b11.collect_training_law(collection_envs(), learner, summary, out, rollouts=1,
                                     training_seed=SEED, measure=plain_measure(learner))
        assert b11.rng_digest() == before  # the probe's own wrapper, as `_run` applies it
        b11.collect_training_law(collection_envs(), learner, summary, out, rollouts=1,
                                 training_seed=SEED, measure=plain_measure(learner))
        assert b11.rng_digest() != before  # without it, a collection moves every stream
    finally:
        for optimizer, original in restore:
            optimizer.step = original


def test_the_collection_moves_no_parameter_and_takes_no_step(harness):
    summary, learner, _evaluator, out = harness
    before = b11.learner_state_record(learner)
    counters = b11.shared.optimizer_counters(learner)
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        with b11.shared.e0._preserve_rng():
            frames = b11.collect_training_law(collection_envs(), learner, summary, out,
                                              rollouts=1, training_seed=SEED,
                                              measure=plain_measure(learner))
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    after = b11.learner_state_record(learner)
    assert after["parameter_digest"] == before["parameter_digest"]
    assert after["value_norm_coordinator"] == before["value_norm_coordinator"]
    assert not any(b11.shared.optimizer_counts(counters).values())
    # the buffer is left cleared, exactly as the fit's own loop leaves it
    assert frames[0]["rows_M"] == LANES * DECISIONS
    assert not learner.rollout_buffer.d2_team_valid.any()
    assert not learner.rollout_buffer.d2_agent_valid.any()
    assert learner.d2_metrics["optimizer_steps"] == 0
    assert "_batched_assign_skills" not in learner.__dict__  # this object wraps nothing
    assert "_batched_select_action" not in learner.__dict__
    assert b01.collect_training.__module__ == "run_fsd_baseline_interruption_b01"


def test_every_valid_row_is_a_sampled_position_and_the_team_renews_with_the_agents(harness):
    summary, learner, _evaluator, out = harness
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        with b11.shared.e0._preserve_rng():
            frame = b11.collect_training_law(collection_envs(), learner, summary, out,
                                             rollouts=1, training_seed=SEED,
                                             measure=plain_measure(learner))[0]
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    # `rollout_frame` refuses a rollout whose rows do not satisfy either invariant; here they do
    assert frame["rows_M_agent"] == frame["rows_M_team"] * N_UAVS
    assert frame["team"]["counts"].sum(axis=1).tolist() == [float(N_UAVS)] * frame["rows_M"]
    assert set(frame["agent"]["label"].tolist()) <= set(range(N_z))
    assert frame["team"]["elapsed"].tolist() == [SKILL_PERIOD] * frame["rows_M"]
    assert frame["team"]["terminal"].sum() == LANES  # one terminal segment per lane-episode
    # the standardisation is the rollout's own single minibatch
    assert frame["standardisation"]["masked_entries"] == frame["rows_M"] * (1 + N_UAVS)
    assert frame["standardisation"]["std"] > 0.
