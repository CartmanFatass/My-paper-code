"""Focused engineering checks for the fixed B03 S4 energy-allocation comparison."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.energy_relay_availability import b03_runner
from experiments.candidates.energy_relay_availability.b03_energy_cost import (
    B03Controller,
    S4_ENERGY_MODEL,
)
from experiments.candidates.energy_relay_availability.b03_readout import summarize
from experiments.candidates.energy_relay_availability.configuration import (
    make_config,
    make_env,
)
from experiments.candidates.energy_relay_availability.run_b03 import ROOT
from scripts.hmasd_launch import LaunchRefusal, _resolve_runner_and_output


def test_fixed_plan_output_collision_and_missing_admission(tmp_path):
    jobs = b03_runner.plan()
    b03_runner.validate_plan(jobs)
    assert len(jobs) == 64
    assert [job["seed"] for job in jobs[:32]] == list(range(970001, 970033))
    assert [job["seed"] for job in jobs[32:]] == list(range(970001, 970033))
    with pytest.raises(ValueError, match="immutable"):
        b03_runner.validate_plan(jobs[:-1])

    existing = tmp_path / "occupied"
    (existing / "raw").mkdir(parents=True)
    with pytest.raises(FileExistsError, match="scientific artifacts"):
        b03_runner.run(existing, "0" * 40)

    output = tmp_path / "unadmitted"
    result = subprocess.run(
        [sys.executable, str(ROOT / "experiments/candidates/energy_relay_availability/run_b03.py"),
         "--out", str(output), "--launch-sha", "unadmitted"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not output.exists()


def test_launcher_binds_runner_output_to_exact_tag():
    runner = "experiments/candidates/energy_relay_availability/run_b03.py"
    output = "runs/energy_relay_availability/b03_energy_assignment_a01"
    resolved_runner, resolved_output, _ = _resolve_runner_and_output(
        ROOT, "energy_relay_availability", output,
        [runner, "--out", output, "--launch-sha", "a" * 40],
        validate_runner=False)
    assert resolved_runner == ROOT / runner
    assert resolved_output == ROOT / output

    with pytest.raises(LaunchRefusal, match="bind the declared output exactly once"):
        _resolve_runner_and_output(
            ROOT, "energy_relay_availability", output,
            [runner, "--out", "runs/energy_relay_availability/other_tag",
             "--launch-sha", "a" * 40], validate_runner=False)


def test_native_power_station_choice_budget_normalization_and_clock30(tmp_path):
    config = make_config(35)
    env = make_env(config, 42, True)
    try:
        raw = env.env
        for horizontal, vertical in ((0.0, 0.0), (3.0, 0.0), (30.0, 0.0), (7.5, 2.5)):
            assert float(S4_ENERGY_MODEL.power_w(horizontal, vertical)) == pytest.approx(
                float(raw._calculate_power_consumption(horizontal, vertical)), abs=1e-12)

        own = np.asarray([[0.0, 0.0, 100.0], [0.0, 0.0, 100.0]])
        battery = np.asarray([0.8, 0.5])
        targets = np.asarray([[1000.0, 0.0], [5000.0, 0.0]])
        stations = np.asarray([[0.0, 0.0, 0.0], [6000.0, 0.0, 0.0]])
        missions = S4_ENERGY_MODEL.target_missions(own, battery, targets, stations, 100.0)
        np.testing.assert_array_equal(missions["chosen_station"], [0, 1])
        np.testing.assert_allclose(missions["usable_wh"], [112.0, 64.0])
        np.testing.assert_allclose(
            missions["cost_fraction"], missions["mission_wh"] / np.asarray([112.0, 64.0])[:, None])
        assert missions["hysteresis_wh"] == pytest.approx(
            10.0 * float(raw._calculate_power_consumption(30.0, 0.0)) / 3600.0)

        observations, _ = env.reset(seed=42)
        controllers = [B03Controller("distance_hysteresis"), B03Controller("energy_fraction")]
        modes = np.zeros(8, dtype=bool)
        previous_done = np.zeros(1, dtype=bool)
        rng_before = b03_runner._rng_state_bytes(raw)
        for controller in controllers:
            controller.propose(observations, None, 0, previous_done, modes)
        assert b03_runner._rng_state_bytes(raw) == rng_before
        baseline_plan = controllers[0].heuristic.last_plan
        candidate_plan = controllers[1].heuristic.last_plan
        for field in ("users", "bs_xy", "station_xy", "centroids", "counts", "relays",
                      "priority", "kinds", "search", "search_uavs", "search_waypoints"):
            left, right = baseline_plan[field], candidate_plan[field]
            if isinstance(left, np.ndarray):
                np.testing.assert_array_equal(left, right)
            else:
                assert left == right
        assert controllers[1].assignment_records

        # Holding the reset observation isolates the planner clock from environment movement.
        for step in range(1, 35):
            controllers[1].propose(observations, None, step, previous_done, modes)
        decisions = controllers[1].as_arrays()
        np.testing.assert_array_equal(np.flatnonzero(decisions["regular_replan"]), [0, 30])
        np.testing.assert_array_equal(np.flatnonzero(decisions["executed_replan"]), [0, 30])
        assert not decisions["extra_replan"].any()
        assert len(controllers[1].assignment_records) == 2
    finally:
        env.close()


def test_short_nonpanel_pair_preserves_hashes_and_complete_raw_trace(tmp_path, monkeypatch):
    monkeypatch.setattr(b03_runner, "HORIZON", 5)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    rows = []
    for arm in ("distance_hysteresis", "energy_fraction"):
        row = b03_runner._simulate_world(
            {"arm": arm, "seed": 43, "job_key": f"{arm}/43"}, tmp_path, 1, 5)
        assert row["status"] == "completed", row
        rows.append(row)
        trace_path = tmp_path / row["raw_path"]
        with np.load(trace_path, allow_pickle=False) as trace:
            assert int(trace["metrics"].shape[0]) == 5
            assert trace["fault_user_xy_m"].shape == (6, 30, 2)
            assert trace["decision_available"].shape == (5, 8)
            if arm == "energy_fraction":
                records = json.loads(str(trace["assignment_records_json"].item()))
                assert records and records[0]["selected"]
                selected = records[0]["selected"][0]
                assert "assignment_cost_after_hysteresis" in selected
                assert "predicted_reserve_slack_wh" in selected
                assert "station_index" in selected
    assert rows[0]["initial_state_sha256"] == rows[1]["initial_state_sha256"]
    assert rows[0]["user_xy_trace_sha256"] == rows[1]["user_xy_trace_sha256"]
    assert rows[0]["failure_trace_sha256"] == rows[1]["failure_trace_sha256"]
    assert rows[0]["rng_state_stream_sha256"] == rows[1]["rng_state_stream_sha256"]


def test_readout_retains_all_adverse_and_positive_pairs():
    seeds = list(range(970001, 970033))
    expected = [f"{arm}/{seed}" for arm in b03_runner.ALL_ARMS for seed in seeds]
    rows = []
    deltas = []
    for seed in seeds:
        index = seed - seeds[0]
        delta = 0.2 if index % 2 == 0 else -0.1
        deltas.append(delta)
        for arm in b03_runner.ALL_ARMS:
            candidate = arm == "energy_fraction"
            rows.append({
                "arm": arm, "seed": seed, "job_key": f"{arm}/{seed}",
                "status": "completed", "initial_state_sha256": f"reset-{seed}",
                "user_xy_trace_sha256": f"users-{seed}",
                "failure_trace_sha256": f"failures-{seed}",
                "rng_state_stream_sha256": f"rng-{seed}-{int(candidate and index % 2 == 1)}",
                "qos_per_step": 0.5 + index * 0.001 + (delta if candidate else 0.0),
                "raw_native_J": 1.0 + (delta if candidate else 0.0),
                "native_J_per_step": 0.1 + (delta if candidate else 0.0),
                "return_constraint_cost_raw_per_step": 0.2,
                "return_constraint_cost_per_step": 0.15,
                "episode_minimum_battery_ratio": 0.3,
                "negative_return_margin_uav_step_fraction": 0.05,
                "below_dynamic_return_threshold_uav_step_fraction": 0.08,
                "below_fixed_reserve_uav_step_fraction": 0.01,
                "service_cutoff_uav_step_fraction": 0.0,
                "cutoff_event_count_sum": 0,
                "depletion_event_count_sum": 0,
                "actual_length": 3000,
                "zero_service": index == 31 and not candidate,
                "terminal_type": "horizon",
            })
    summary = summarize(rows, expected, seeds)
    assert summary["status"] == "complete"
    assert len(summary["world_pairs"]) == 32
    assert summary["pairing_diagnostics"]["initial_state_pairs_valid"]
    assert not summary["pairing_diagnostics"]["strict_exogenous_trace_pairing"]
    assert summary["pairing_diagnostics"]["hash_agreement"]["rng_state_stream_sha256"] == {
        "equal_pairs": 16, "different_pairs": 16, "unobserved_pairs": 0}
    contrast = summary["contrasts_energy_minus_distance"]["qos_per_step"]
    assert contrast["status"] == "paired" and contrast["n"] == 32
    assert contrast["mean"] == pytest.approx(np.mean(deltas))
    assert any(delta > 0 for delta in deltas) and any(delta < 0 for delta in deltas)
    assert summary["panels"]["distance_hysteresis"]["zero_service_worlds"] == 1
    arm_qos = summary["panels"]["distance_hysteresis"]["metrics"]["qos_per_step"]
    assert arm_qos["n"] == 32 and arm_qos["df"] == 31
    assert arm_qos["se"] == pytest.approx(arm_qos["sd"] / np.sqrt(32))
    assert arm_qos["t95"][0] < arm_qos["mean"] < arm_qos["t95"][1]
