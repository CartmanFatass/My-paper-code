"""B02 admission, pairing, bounded costs and partial-evidence behavior."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from experiments.candidates.uav_energy_coordination import run_b02
from experiments.candidates.uav_energy_coordination.b01 import readout
from experiments.candidates.uav_energy_coordination.b02 import runner


FIXTURE_SEEDS = tuple(range(990101, 990109))


def _keys(arms=("I", "P")):
    return [f"{arm}/{seed}" for seed in FIXTURE_SEEDS for arm in arms]


def _row(arm, seed, *, qos=0.5, cost=0.1, digest="same"):
    row = {field: 0.0 for field in readout.ENDPOINTS}
    row.update(job_key=f"{arm}/{seed}", arm=arm, seed=seed, status="completed",
               actual_length=3000, terminal_type="truncated",
               raw_native_J=qos * 3000 - cost * 6000,
               native_J_per_step=qos - 2 * cost, qos_per_step=qos,
               return_constraint_cost_per_step=cost,
               below_fixed_reserve_uav_step_fraction=cost,
               service_cutoff_uav_step_fraction=cost,
               initial_state_sha256=digest, user_xy_trace_sha256=digest,
               rng_state_stream_sha256=digest)
    return row


def test_entry_admission_precedes_import_and_effects(monkeypatch, tmp_path):
    calls = []

    def denied(*args, **kwargs):
        calls.append("admission")
        raise RuntimeError("denied")

    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission",
                        types.SimpleNamespace(require_admission=denied))
    monkeypatch.delitem(sys.modules, "experiments.candidates.uav_energy_coordination.b02.runner",
                        raising=False)
    with pytest.raises(RuntimeError, match="denied"):
        run_b02.main(["--out", str(tmp_path), "--seed", str(runner.SEEDS[0]),
                      "--launch-sha", "a" * 40])
    assert calls == ["admission"] and not any(tmp_path.iterdir())
    with pytest.raises(ValueError, match="requires seed"):
        run_b02.main(["--out", str(tmp_path), "--seed", "990101",
                      "--launch-sha", "a" * 40])
    assert calls == ["admission"]
    with pytest.raises(ValueError, match="two workers"):
        run_b02.main(["--out", str(tmp_path), "--seed", str(runner.SEEDS[0]),
                      "--workers", "4", "--launch-sha", "a" * 40])
    assert calls == ["admission"]


def test_exact_plan_and_world_cost_bounds():
    assert len(runner.plan()) == 16
    assert runner.HORIZON == 3000
    assert runner.SEEDS == tuple(range(41092801, 41092809))
    assert [job["arm"] for job in runner.plan()[:2]] == ["I", "P"]
    with pytest.raises(ValueError, match="fixed 16-job"):
        runner.validate_plan(runner.plan()[:-1])
    with pytest.raises(ValueError, match="two workers"):
        runner.run(None, "a" * 40, workers=4)
    costs = {key: 0 for key in runner.COST_KEYS}
    costs.update(score_requests=2700, p_shared_baseline_snapshots=300,
                 service_snapshots=5700, decision_clocks=300)
    runner._check_world_costs("P", costs)
    costs["service_snapshots"] = 5701
    with pytest.raises(ValueError, match="P exceeded"):
        runner._check_world_costs("P", costs)
    costs["service_snapshots"] = 0
    costs["primitive_forecast_steps"] = 1
    with pytest.raises(ValueError, match="zero primitive"):
        runner._check_world_costs("P", costs)
    readings = runner._p_readings({
        "transit_fallback": np.asarray(["", "mode_active", ""]),
        "transit_candidate_count": np.asarray([3, 1, 2]),
        "transit_selected_hold_uav": np.asarray([1, -1, 2]),
        "transit_selected_proxy_gain": np.asarray([1e-13, np.nan, 0.2]),
    })
    assert readings["P_active_windows"] == 2
    assert readings["P_fallback_windows"] == 1
    assert readings["P_candidate_scores"] == 5
    assert readings["P_selected_hold_near_tie_windows"] == 1


def test_two_arm_adverse_pairing_and_b01_default():
    rows = [_row(arm, seed, qos=0.4 if arm == "I" else 0.5,
                 cost=0.2 if arm == "I" else 0.1)
            for seed in FIXTURE_SEEDS for arm in ("I", "P")]
    result = readout.summarize(rows, FIXTURE_SEEDS, _keys(), arms=("I", "P"),
                               comparisons=(("I", "P"),), interpretation=runner.INTERPRETATION)
    assert result["status"] == "complete"
    assert list(result["contrasts"]) == ["I-P"]
    contrast = result["contrasts"]["I-P"]
    assert contrast["status"] == "paired_primary"
    assert contrast["endpoints"]["raw_native_J"]["mean"] < 0
    assert contrast["endpoints"]["raw_native_J"]["t95_descriptive"] is not None
    assert contrast["loss_worlds"]["return_constraint_cost_per_step"] == list(FIXTURE_SEEDS)
    assert contrast["loss_worlds"]["service_cutoff_uav_step_fraction"] == list(FIXTURE_SEEDS)
    assert "energy_consumed_wh" not in contrast["loss_worlds"]
    assert result["interpretation"] == runner.INTERPRETATION

    incomplete = readout.summarize(rows[:-1], FIXTURE_SEEDS, _keys(), arms=("I", "P"),
                                   comparisons=(("I", "P"),), interpretation=runner.INTERPRETATION)
    assert incomplete["status"] == "incomplete"
    assert incomplete["contrasts"]["I-P"]["endpoints"]["raw_native_J"]["t95_descriptive"] is None
    mismatched = [dict(row) for row in rows]
    mismatched[-1]["rng_state_stream_sha256"] = "different"
    assert readout.summarize(mismatched, FIXTURE_SEEDS, _keys(), arms=("I", "P"),
                             comparisons=(("I", "P"),))["status"] == "incomplete"

    b01_rows = [_row(arm, seed) for seed in FIXTURE_SEEDS for arm in ("H", "I", "C")]
    default = readout.summarize(b01_rows, FIXTURE_SEEDS, _keys(("H", "I", "C")))
    assert default["status"] == "complete"
    assert list(default["panels"]) == ["H", "I", "C"]
    assert list(default["contrasts"]) == ["C-I", "C-H", "I-H"]
    assert default["interpretation"] == (
        "native closed-loop endpoints; H is a competence reference, not a clock-matched causal control")


@pytest.mark.parametrize("failure_stage", ["planner", "postprocessing", "metric_mismatch"])
def test_worker_preserves_costs_and_native_arrays_on_failure(monkeypatch, tmp_path, failure_stage):
    (tmp_path / "raw").mkdir()
    job = {"arm": "P", "seed": FIXTURE_SEEDS[0], "job_key": f"P/{FIXTURE_SEEDS[0]}"}
    monkeypatch.setattr(runner, "plan", lambda: [job])
    raw = types.SimpleNamespace(
        np_random=np.random.RandomState(4),
        user_positions=np.zeros((30, 3)), uav_positions=np.zeros((8, 3)),
        charging_station_positions=np.zeros((2, 3)), uav_battery_ratios=np.ones(8),
        last_reward_demand_bps=np.ones(30), last_delivered_traffic_bps=np.ones(30),
        last_actual_velocities=np.zeros((8, 3)), last_energy_charged_wh=np.zeros(8),
        last_energy_consumed_wh=np.zeros(8),
        _energy_metrics_dict=lambda: {field: 0.0 for field in readout.TRACE_FIELDS},
        last_constrained_reward_metrics={field: 0.0 for field in readout.TRACE_FIELDS})
    env = types.SimpleNamespace(env=raw, close=lambda: None)
    costs = {key: 0 for key in runner.COST_KEYS}
    costs.update(score_requests=3, service_snapshots=7, p_shared_baseline_snapshots=1)
    controller = types.SimpleNamespace(costs=costs, plan_input_steps=[0],
                                       decision_arrays=lambda: {"transit_step": np.asarray([0])},
                                       validate_trace=lambda length: (_ for _ in ()).throw(
                                           RuntimeError("postprocessing failure")),
                                       targets_xy=np.zeros((8, 2)), close=lambda: None)
    monkeypatch.setattr(runner, "make_eval_config", lambda *a: types.SimpleNamespace(time_step=1.0))
    monkeypatch.setattr(runner, "make_env", lambda *a: env)
    monkeypatch.setattr(runner, "_effective_s2", lambda *a: {})
    monkeypatch.setattr(runner, "FrozenController", lambda *a: controller)

    def evaluate(_, __, ___, ____, _____, *, progress, observer):
        with observer.attach(controller):
            observer.on_step(t=0, proposal_t=np.zeros((8, 4)),
                             submitted_t=np.zeros((8, 4)), controller=controller)
            progress(1)
            if failure_stage == "planner":
                raise RuntimeError("planner failure")
        metrics = np.zeros((1, len(readout.TRACE_FIELDS)))
        if failure_stage == "metric_mismatch":
            metrics[0, 0] = 1.0
        return ({"actual_length": 1}, {"reward": np.asarray([0.0]),
                                       "metrics": metrics,
                                       "battery": np.ones((1, 8))})

    monkeypatch.setattr(runner, "evaluate_world", evaluate)
    result = runner._worker((job, str(tmp_path), 1))
    assert result["status"] == "failed" and result["partial_observed_steps"] == 1, result["error"]
    if failure_stage == "metric_mismatch":
        assert "failure-preserving native trace differs" in result["error"]
    assert result["known_completed_clock_costs"]["score_requests"] == 3
    assert result["in_progress_clock_costs"] == "unknown after failure"
    with np.load(tmp_path / result["partial_path"], allow_pickle=False) as data:
        assert data["transit_step"].tolist() == [0]
        assert data["submitted_actions"].shape == (1, 8, 4)
        assert data["observed_native_metrics"].shape == (1, len(readout.TRACE_FIELDS))
        assert ("reward" in data) == (failure_stage != "planner")
    assert result["partial_native_steps"] == (1 if failure_stage != "planner" else None)
