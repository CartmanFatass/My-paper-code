"""B01 admission, bounded traces and adverse-inclusive readout contracts."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from experiments.candidates.uav_energy_coordination import run_b01
from experiments.candidates.uav_energy_coordination.b01 import readout, runner


def test_entry_requires_admission_before_runner_import(monkeypatch, tmp_path):
    calls = []

    def denied(*args, **kwargs):
        calls.append("admission")
        raise RuntimeError("denied")

    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission",
                        types.SimpleNamespace(require_admission=denied))
    monkeypatch.delitem(sys.modules, "experiments.candidates.uav_energy_coordination.b01.runner",
                        raising=False)
    with pytest.raises(RuntimeError, match="denied"):
        run_b01.main(["--out", str(tmp_path), "--seed", "31092801",
                      "--launch-sha", "a" * 40])
    assert calls == ["admission"]
    assert list(tmp_path.iterdir()) == []


def test_entry_rejects_wrong_sha_before_runner_import(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission",
                        types.SimpleNamespace(require_admission=lambda *a, **k: {"sha": "b" * 40}))
    with pytest.raises(RuntimeError, match="launch SHA"):
        run_b01.main(["--out", str(tmp_path), "--seed", "31092801",
                      "--launch-sha", "a" * 40])
    assert not any(tmp_path.iterdir())


def test_failed_world_known_costs_are_in_batch_lower_bound():
    complete = {key: 10 for key in runner.COST_KEYS}
    partial = {key: 3 for key in runner.COST_KEYS}
    totals, unknown = runner._aggregate_costs([
        {"job_key": "H/1", "status": "completed", "costs": complete},
        {"job_key": "I/1", "status": "failed", "known_completed_clock_costs": partial},
        {"job_key": "C/1", "status": "unreconciled"},
    ])
    assert totals == {key: 13 for key in runner.COST_KEYS}
    assert unknown == ["I/1", "C/1"]


def _row(arm, seed, *, qos=0.5, cost=0.1, digest="same"):
    row = {field: 0.0 for field in readout.ENDPOINTS}
    row.update({"job_key": f"{arm}/{seed}", "arm": arm, "seed": seed,
           "status": "completed", "actual_length": 3000, "terminal_type": "truncated",
           "raw_native_J": qos * 3000 - cost * 6000, "native_J_per_step": qos - 2 * cost,
           "qos_per_step": qos, "return_constraint_cost_per_step": cost,
           "below_fixed_reserve_uav_step_fraction": cost,
           "service_cutoff_uav_step_fraction": cost,
           "initial_state_sha256": digest, "user_xy_trace_sha256": digest,
           "rng_state_stream_sha256": digest})
    return row


def test_readout_keeps_signed_risk_losses_and_requires_complete_pairing():
    seeds = runner.SEEDS
    keys = [job["job_key"] for job in runner.plan()]
    rows = [_row(arm, seed, qos=0.4 if arm == "C" else 0.5,
                 cost=0.2 if arm == "C" else 0.1)
            for seed in seeds for arm in runner.ARMS]
    full = readout.summarize(rows, seeds, keys)
    assert full["status"] == "complete"
    comparison = full["contrasts"]["C-I"]
    assert comparison["status"] == "paired_primary"
    assert comparison["endpoints"]["qos_per_step"]["mean"] == pytest.approx(-0.1)
    assert comparison["endpoints"]["qos_per_step"]["t95_descriptive"] is not None
    assert comparison["loss_worlds"]["qos_per_step"] == list(seeds)
    assert comparison["loss_worlds"]["return_constraint_cost_per_step"] == list(seeds)
    assert comparison["loss_worlds"]["below_fixed_reserve_uav_step_fraction"] == list(seeds)
    assert comparison["loss_worlds"]["service_cutoff_uav_step_fraction"] == list(seeds)
    assert "energy_input_wh" not in comparison["loss_worlds"]

    partial = readout.summarize(rows[:-1], seeds, keys)
    assert partial["status"] == "incomplete"
    assert partial["contrasts"]["C-I"]["status"] == "descriptive_partial_or_unverified"
    assert partial["contrasts"]["C-I"]["endpoints"]["qos_per_step"]["t95_descriptive"] is None
    mismatch = [dict(row) for row in rows]
    mismatch[-1]["rng_state_stream_sha256"] = "different"
    invalid = readout.summarize(mismatch, seeds, keys)
    assert invalid["status"] == "incomplete"
    assert invalid["pair_hash_agreement"]["rng_state_stream_sha256"]["different"] == 1


def test_enrich_world_uses_post_step_forecast_index_and_censored_gaps():
    metrics = np.zeros((4, len(readout.TRACE_FIELDS)))
    metrics[:, readout.TRACE_FIELDS.index("qos_satisfaction_ratio")] = [0, 0, 0.4, 0.6]
    metrics[:, readout.TRACE_FIELDS.index("step_charger_input_wh")] = [0.1, 0.1, 0.1, 0.1]
    steps = {"metrics": metrics, "battery": np.full((4, 8), 0.2),
             "reward": np.zeros(4)}
    observed = {"actual_energy_input_wh": np.full((4, 8), 0.0125),
                "actual_energy_consumed_wh": np.full((4, 8), 0.02),
                "actual_xyz_post_m": np.zeros((4, 8, 3))}
    decisions = {"planner_step": np.asarray([0]),
                 "planner_sample_times": np.asarray([[1, 2, 3]]),
                 "planner_selected_positions": np.zeros((1, 3, 8, 3)),
                 "planner_selected_batteries": np.full((1, 3, 8), 0.2),
                 "planner_selected_qos": np.asarray([[0.1, 0.2, 0.5]])}
    row = {"actual_length": 4, "step_charger_input_wh_sum": 0.4}
    result = readout.enrich_world(row, steps, observed, decisions,
                                  reserve_ratio=0.1, cutoff_ratio=0.02, time_step=1.0)
    assert result["max_zero_qos_gap"] == 2
    assert result["max_below_half_qos_gap"] == 3
    assert result["forecast_closed_loop_discrepancy"]["qos"]["mean_signed"] == pytest.approx(
        (0.1 + 0.2 + 0.1) / 3)


def test_decision_contract_enforces_clock_and_query_bounds():
    arrays = {
        "planner_step": np.asarray([0, 60]),
        "planner_horizon": np.asarray([600, 600]),
        "planner_sample_times": np.asarray([[200, 400, 600], [200, 400, 600]]),
        "planner_selected_positions": np.zeros((2, 3, 8, 3)),
        "planner_selected_batteries": np.ones((2, 3, 8)),
        "planner_selected_qos": np.zeros((2, 3)),
        "planner_selected_risk": np.zeros((2, 3)),
        "planner_incumbent_score": np.zeros(2), "planner_selected_score": np.zeros(2),
        "planner_goals": np.zeros((2, 8, 3)), "planner_station_ids": np.zeros((2, 8)),
        "planner_score_requests": np.asarray([147, 1]),
        "planner_model_evaluations": np.asarray([140, 1]),
        "planner_service_snapshots": np.asarray([420, 3]),
        "planner_event_count": np.zeros(2),
        "planner_extra_diagnostic": np.zeros(2),
    }
    controller = types.SimpleNamespace(decision_arrays=lambda: arrays,
                                       plan_input_steps=[0, 60], decision_records=[{}, {}])
    assert runner._decisions(controller, "I", 120)["planner_extra_diagnostic"].shape == (2,)
    arrays["planner_score_requests"] = np.asarray([148, 1])
    with pytest.raises(ValueError, match="per-clock"):
        runner._decisions(controller, "I", 120)
    arrays["planner_score_requests"] = np.asarray([147, 1])
    arrays["planner_service_snapshots"] = np.asarray([419, 3])
    with pytest.raises(ValueError, match="per-clock"):
        runner._decisions(controller, "I", 120)


def test_worker_preserves_partial_native_trace_on_failure(monkeypatch, tmp_path):
    (tmp_path / "raw").mkdir()
    raw = types.SimpleNamespace(
        np_random=np.random.RandomState(3),
        user_positions=np.zeros((30, 3)), uav_positions=np.zeros((8, 3)),
        charging_station_positions=np.zeros((2, 3)), uav_battery_ratios=np.ones(8),
        last_reward_demand_bps=np.ones(30), last_delivered_traffic_bps=np.ones(30),
        last_actual_velocities=np.zeros((8, 3)), last_energy_charged_wh=np.zeros(8),
        last_energy_consumed_wh=np.zeros(8),
        last_constrained_reward_metrics={field: 0. for field in runner.TRACE_FIELDS},
        _energy_metrics_dict=lambda: {})
    env = types.SimpleNamespace(env=raw, close=lambda: None)
    controller = types.SimpleNamespace(plan_input_steps=[], targets_xy=np.zeros((8, 2)),
                                       costs={"score_requests": 2},
                                       decision_arrays=lambda: {"planner_step": np.asarray([0])})
    monkeypatch.setattr(runner, "make_eval_config", lambda *a: object())
    monkeypatch.setattr(runner, "make_env", lambda *a: env)
    monkeypatch.setattr(runner, "_effective_s2", lambda *a: {})
    monkeypatch.setattr(runner, "HeuristicController", lambda *a: controller)

    def fail(_, __, ___, ____, _____, *, progress, observer):
        with observer.attach(controller):
            observer.on_step(t=0, proposal_t=np.zeros((8, 4)),
                             submitted_t=np.zeros((8, 4)), controller=controller)
            progress(1)
            raise RuntimeError("mock native failure")

    monkeypatch.setattr(runner, "evaluate_world", fail)
    row = runner._worker((runner.plan()[0], str(tmp_path), 1))
    assert row["status"] == "failed" and row["partial_observed_steps"] == 1
    assert row["known_completed_clock_costs"] == {"score_requests": 2.0}
    assert row["in_progress_clock_costs"] == "unknown after failure"
    assert row["partial_path"] and (tmp_path / row["partial_path"]).is_file()
    with np.load(tmp_path / row["partial_path"], allow_pickle=False) as data:
        assert data["proposed_actions"].shape == (1, 8, 4)
        assert data["actual_user_delivered_ratio"].shape == (1, 30)
        assert data["selected_goals"].shape == (1, 8, 3)
        assert np.all(data["selected_goals"][0, :, 2] == 100.0)
        assert data["planner_step"].tolist() == [0]
        assert data["observed_native_metrics"].shape == (1, len(runner.TRACE_FIELDS))
        assert data["observed_native_reward"].shape == (1,)
        assert data["observed_battery_ratio"].shape == (1, 8)


def test_postprocessing_failure_preserves_returned_native_arrays(monkeypatch, tmp_path):
    (tmp_path / "raw").mkdir()
    raw = types.SimpleNamespace()
    env = types.SimpleNamespace(env=raw, close=lambda: None)
    controller = types.SimpleNamespace(plan_input_steps=[0])
    complete_steps = {"metrics": np.zeros((1, len(runner.TRACE_FIELDS))),
                      "reward": np.asarray([0.]), "battery": np.ones((1, 8)),
                      "ends": np.asarray([[False, True]]), "entered": np.zeros((1, 8), dtype=bool)}
    observed = {"user_xy_m": np.zeros((2, 30, 2)),
                "observed_native_metrics": complete_steps["metrics"],
                "observed_native_reward": complete_steps["reward"],
                "observed_battery_ratio": complete_steps["battery"]}
    observer = types.SimpleNamespace(user_xy=[np.zeros((30, 2))], as_arrays=lambda: observed)
    monkeypatch.setattr(runner, "make_eval_config", lambda *a: types.SimpleNamespace(time_step=1))
    monkeypatch.setattr(runner, "make_env", lambda *a: env)
    monkeypatch.setattr(runner, "_effective_s2", lambda *a: dict(return_reserve_ratio=.1, service_cutoff_threshold=.02))
    monkeypatch.setattr(runner, "HeuristicController", lambda *a: controller)
    monkeypatch.setattr(runner, "CoordinationObserver", lambda *a: observer)

    def evaluate(*args, progress, **kwargs):
        progress(1)
        return {"actual_length": 1}, complete_steps

    monkeypatch.setattr(runner, "evaluate_world", evaluate)
    monkeypatch.setattr(runner, "enrich_world", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("postprocessing failure")))
    row = runner._worker((runner.plan()[0], str(tmp_path), 1))
    assert row["status"] == "failed" and row["error"] == "postprocessing failure"
    assert row["native_evaluator_arrays_returned"]
    with np.load(tmp_path / row["partial_path"], allow_pickle=False) as data:
        for key, values in complete_steps.items():
            np.testing.assert_array_equal(data[key], values)
