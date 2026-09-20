"""Real tiny-host executions of both persistence arms, and the capture's inertness.

Two lanes, twenty-step episodes, two rollouts, the real Scenario 1 environment and the real D
agent, through the frozen runner's own learner construction, evaluator construction, collector
loop and evaluation panels. Technical checks, no result: nothing here asserts the direction or the
size of any measured quantity. Kept apart from the fake-learner tests, whose helper forbids real
construction.
"""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_persistence_b07 as persistence  # noqa: E402

SEED = sorted(persistence.BLOCKS)[0]
LANES, HORIZON, ROLLOUTS = 2, 20, 2
N_UAVS, SKILL_PERIOD = 6, 10
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}


@pytest.fixture
def tiny(monkeypatch):
    shared = b01.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", LANES)
    monkeypatch.setattr(shared, "EVAL_LANES", LANES)
    monkeypatch.setattr(shared, "HORIZON", HORIZON)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    monkeypatch.setattr(persistence, "ROLLOUTS", ROLLOUTS)
    monkeypatch.setattr(persistence, "PANEL_ROLLOUTS", tuple(range(1, ROLLOUTS + 1)))
    monkeypatch.setattr(persistence, "DIAGNOSTIC_ROLLOUTS", (1, ROLLOUTS))
    monkeypatch.setattr(persistence, "BEHAVIOUR_EARLY_ROLLOUTS", (1,))
    monkeypatch.setattr(persistence, "BEHAVIOUR_LATE_ROLLOUTS", (ROLLOUTS,))
    return shared


def fit(arm, out):
    assert persistence.run_fit(arm, SEED, out, admission=ADMISSION) == 0
    return json.loads((out / "summary.json").read_text())


def fit_without_the_capture(arm, out):
    """The same route with nothing attached: the frozen `build_learner`, this object otherwise."""
    persistence.bind(wrap=True)
    persistence.CURRENT.update(persistence_arm=arm, admission=ADMISSION, capture=None)
    b01.build_learner = persistence._orig_build_learner  # the only difference
    try:
        assert b01.run_fit(arm, SEED, out) == 0
    finally:
        persistence.CURRENT.update(persistence_arm=None, admission=None, summary=None, capture=None)
        if persistence.shared.base_summary is persistence.base_summary:
            persistence.shared.base_summary = persistence._orig_base_summary
    summary = json.loads((out / "summary.json").read_text())
    assert summary["behaviour"] == [] and summary["behaviour_capture"] is None
    return summary


@pytest.mark.parametrize("arm", ["D_K10", "D_K1"])
def test_the_caps_set_the_decision_cadence_of_the_real_d_route(tmp_path, tiny, arm):
    summary = fit(arm, tmp_path / arm)
    period = SKILL_PERIOD if arm == "D_K10" else 1
    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["persistence_arm"] == arm and summary["factorial_arm"] == arm
    caps = persistence.ARM_CAPS[arm]
    for phase in ("learner_config", "evaluation_config"):
        assert (summary[phase]["skill_cap_k_max"], summary[phase]["team_cap_k_Z"]) == caps
        assert summary[phase]["k"] == SKILL_PERIOD  # the low-level chunk length, both arms
        assert summary[phase]["coordinator_batch_size"] == persistence.ARMS[arm][1]
        # The construction is the published D1280 fit's up to the shrunken host and the overrides.
        recorded = summary[f"{phase}_differences_from_recorded_d1280"]
        assert recorded["available"] is True and recorded["reason"] is None
        assert set(recorded["differences"]) == set(persistence.GEOMETRY_FIELDS) | set(
            persistence.ARM_OVERRIDES[arm])

    # One full-pool coordinator minibatch per epoch in both arms: the declared package equalisation.
    epochs = summary["learner_config"]["ppo_epochs"]
    assert summary["optimizer_calls"]["coordinator"] == epochs * ROLLOUTS
    # The low-level update is the same law in both arms, and its count does not depend on the caps:
    # `config.k` is its chunk length (hmasd/agent.py:6301-6311) and neither arm sets
    # `sequence_batch_size`, so the sampler's default 32 applies to both.
    config = b01.make_config(arm, [SimpleNamespace(state_dim=119, obs_dim=104)] * LANES, SEED)
    assert not hasattr(config, "sequence_batch_size") and config.k == SKILL_PERIOD
    sequences = LANES * N_UAVS * (HORIZON // SKILL_PERIOD)
    expected = epochs * math.ceil(sequences / 32) * ROLLOUTS
    assert summary["optimizer_calls"]["discoverer_actor"] == expected
    assert summary["optimizer_calls"]["discoverer_critic"] == expected

    for row in summary["training_rows"]:
        segments = row["segments"]
        assert segments["agent"]["min"] == segments["agent"]["max"] == period
        assert segments["team"]["min"] == segments["team"]["max"] == period
        assert segments["agent"]["count"] == LANES * N_UAVS * (HORIZON // period)
        assert segments["team"]["count"] == LANES * (HORIZON // period)
        metrics = row["d2_metrics"]
        assert metrics["steps"] == LANES * HORIZON
        assert metrics["decision_steps"] == metrics["team_decisions"] == LANES * (HORIZON // period)

    for row in summary["behaviour"]:
        assert row["steps"] == HORIZON and row["lanes"] == LANES and row["agents"] == N_UAVS
        assert row["team_decision_fraction"] == pytest.approx(1. / period)
        assert row["agent_sampled_fraction"] == pytest.approx(1. / period)
        assert row["skill_change_comparisons"] == LANES * (HORIZON - 1)
        # A decision every step is an opportunity to change every step; a decision every ten steps
        # can change on at most one step in ten. Neither bound is a claim about how often it does.
        assert row["agent_skill_change_fraction"] <= 1. / period + 1e-12
        assert row["team_skill_change_fraction"] <= 1. / period + 1e-12
        assert row["episode_series"] == LANES * N_UAVS and row["cells_visited_mean"] >= 1.
        assert row["path_length_metres_mean"] >= row["net_displacement_metres_mean"] - 1e-9
        assert row["action_series"] == LANES * N_UAVS * 3
        assert row["action_series_used"] + row["action_series_skipped"] == row["action_series"]
        assert row["action_autocorrelation"]["20"] is None  # a lag as long as this tiny rollout
    assert set(persistence.fit_endpoint(summary)) == set(range(1, ROLLOUTS + 1))
    assert persistence.CURRENT == {"persistence_arm": None, "admission": None, "summary": None,
                                   "capture": None}
    assert b01.build_learner is persistence._orig_build_learner


@pytest.mark.parametrize("arm", ["D_K10", "D_K1"])
def test_the_capture_leaves_the_fit_bit_identical(tmp_path, tiny, arm):
    """The same tiny fit with and without the capture: panels and training returns are equal."""
    captured = fit(arm, tmp_path / f"{arm}_captured")
    plain = fit_without_the_capture(arm, tmp_path / f"{arm}_plain")
    assert [p["panel_rollouts"] for p in captured["panels"]] == [
        p["panel_rollouts"] for p in plain["panels"]]
    for mine, theirs in zip(captured["panels"], plain["panels"]):
        assert mine["native_scores_J"] == theirs["native_scores_J"]
        assert mine["returns_U"] == theirs["returns_U"]
        assert mine["component_means"] == theirs["component_means"]
    for mine, theirs in zip(captured["training_rows"], plain["training_rows"]):
        assert mine["episode_returns_U"] == theirs["episode_returns_U"]
        assert mine["return_sums"] == theirs["return_sums"]
        assert mine["losses"] == theirs["losses"]
        assert mine["relative_initialization_displacement"] == theirs["relative_initialization_displacement"]
        assert mine["segments"] == theirs["segments"]
    assert captured["learner_config"] == plain["learner_config"]
    assert captured["evaluation_config"] == plain["evaluation_config"]
    assert captured["initial_parameter_norms"] == plain["initial_parameter_norms"]
    assert captured["optimizer_calls"] == plain["optimizer_calls"]
    assert persistence.bit_identical_panels(captured, plain)["bit_identical"] is True


def test_this_readers_panel_law_agrees_with_the_frozen_one_on_the_frozen_caps(tmp_path, tiny):
    summary = fit("D_K10", tmp_path / "D_K10")
    persistence.bind()
    mine, frozen = persistence.persistence_panels(summary), b01.arm_panels(summary)
    assert set(mine) == set(frozen)
    for rollout, values in mine.items():
        assert values.tolist() == frozen[rollout].tolist()
