"""B02 engineering fixtures use only synthetic traces and nonpanel seeds 42/43."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.energy_relay_availability import b02_runner
from experiments.candidates.energy_relay_availability.b02_controller import (
    B02Controller, response_lags,
)
from experiments.candidates.energy_relay_availability.b02_readout import summarize
from experiments.candidates.energy_relay_availability.configuration import (
    AvailableH1Controller, make_config, make_env,
)
from experiments.candidates.energy_relay_availability.runner import execute_bounded, _sha256
from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT


def _own_field(observations, uav, field, value):
    copy = observations.copy()
    index = S7S2_LAYOUT.energy_uavs.start + uav * S7S2_LAYOUT.energy_uav_fields + field
    copy[uav, index] = value
    return copy


def test_fixed_plan_and_admission(tmp_path):
    jobs = b02_runner.plan()
    b02_runner.validate_plan(jobs)
    assert len(jobs) == 64
    assert [job["seed"] for job in jobs[:32]] == list(range(969001, 969033))
    assert [job["seed"] for job in jobs[32:]] == list(range(969001, 969033))
    with pytest.raises(ValueError, match="sealed"):
        b02_runner.validate_plan([{**jobs[0], "seed": 957001}, *jobs[1:]])
    with pytest.raises(ValueError, match="immutable"):
        b02_runner.validate_plan(jobs[:-1])
    output = tmp_path / "unadmitted"
    result = subprocess.run(
        [sys.executable, "experiments/candidates/energy_relay_availability/run_b02.py",
         "--out", str(output), "--launch-sha", "unadmitted"],
        capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not output.exists()


def test_legal_change_clock_and_coincident_plan():
    env = make_env(make_config(35), 42, True)
    try:
        obs, _ = env.reset(seed=42)
        control = B02Controller("availability_event")
        changed = _own_field(obs, 0, 5, 0.0)
        simultaneous = _own_field(changed, 1, 5, 0.0)
        charged = _own_field(simultaneous, 2, 4, 1.0)
        for step in range(35):
            current = obs if step == 0 else (
                charged if step >= 30 else simultaneous if step >= 1 else obs)
            modes = np.zeros(8, bool)
            if step == 10:
                modes[3] = True  # Shield mode alone never enters the trigger.
            control.propose(current, None, step, np.zeros(1, bool), modes)
        trace = control.as_arrays()
        assert trace["regular_replan"].nonzero()[0].tolist() == [0, 30]
        assert trace["extra_replan"].nonzero()[0].tolist() == [1]
        assert trace["executed_replan"].nonzero()[0].tolist() == [0, 1, 30]
        assert trace["plan_call_count"][[0, 1, 30]].tolist() == [1, 2, 3]
        assert not trace["availability_changed"][0]
        assert not trace["availability_changed"][30]  # Charging is separate.
        assert not trace["extra_replan"][10]
        assert trace["plan_wall_seconds"].sum() >= 0
        control.reset()
        control.propose(changed, None, 0, np.ones(1, bool), np.zeros(8, bool))
        assert not control.as_arrays()["availability_changed"][0]
        assert control.as_arrays()["regular_replan"][0]

        # An observed change exactly at 30 is one scheduled call, not an extra call.
        control.reset()
        for step in range(31):
            current = obs if step < 30 else changed
            control.propose(current, None, step, np.zeros(1, bool), np.zeros(8, bool))
        trace = control.as_arrays()
        assert trace["coincident_trigger"][30]
        assert trace["executed_replan"].sum() == 2
        assert trace["extra_replan"].sum() == 0
    finally:
        env.close()


def test_response_lags_and_last_transition_censoring():
    available = np.ones((32, 8), bool)
    available[1:, 0] = False
    available[31:, 1] = False
    decisions = {"available": available,
                 "availability_changed": np.array([False] + [i in (1, 31) for i in range(1, 32)]),
                 "executed_replan": np.array([i in (0, 30) for i in range(32)])}
    terminal = available[-1].copy()
    terminal[2] = False
    clock = response_lags(decisions, terminal)
    assert [row["lag"] for row in clock["rows"]] == [29, None, None]
    assert clock["censored_lags"] == 2 and clock["terminal_changes"] == 1
    decisions["executed_replan"][1] = True
    event = response_lags(decisions, terminal)
    assert event["rows"][0]["lag"] == 0
    # Timer expiry/refault with unchanged legal availability is not a decision trigger.
    assert not decisions["availability_changed"][2]


def test_clock30_native_identity_with_b01_short_world():
    config = make_config(35)
    traces = []
    for controller in (AvailableH1Controller("local"), B02Controller("clock30")):
        env = make_env(config, 43, True)
        try:
            row, arrays = evaluate_world(controller, env, config, 43, PRODUCTION_PARAMS)
            traces.append((row, arrays))
        finally:
            env.close()
    old, new = traces
    assert old[0]["raw_native_J"] == new[0]["raw_native_J"]
    assert old[0]["qos_per_step"] == new[0]["qos_per_step"]
    for key in ("reward", "metrics", "ends", "target_xy"):
        np.testing.assert_array_equal(old[1][key], new[1][key])
    assert new[0]["actual_length"] == 35


def test_worker_serialization_and_native_event_activation(tmp_path, monkeypatch):
    job = {"arm": "availability_event", "seed": 42, "job_key": "availability_event/42"}
    monkeypatch.setattr(b02_runner, "plan", lambda: [job])
    monkeypatch.setattr(b02_runner, "HORIZON", 5)
    native_make_env = b02_runner.make_env

    def injected_env(config, seed, fault_on):
        env = native_make_env(config, seed, fault_on)
        native_update = env.env._update_uav_failures
        calls = 0

        def update():
            nonlocal calls
            native_update()
            if calls == 0:
                env.env.uav_failure_timers[0] = 2
                env.env.uav_failed[0] = True
            calls += 1

        env.env.uav_failure_probability = 0.0
        env.env._update_uav_failures = update
        return env

    monkeypatch.setattr(b02_runner, "make_env", injected_env)
    (tmp_path / "raw").mkdir()
    row = b02_runner._worker((job, str(tmp_path), 1))
    assert row["status"] == "completed", row.get("error")
    assert row["actual_length"] == 5
    assert row["extra_plan_count"] >= 1
    path = tmp_path / row["raw_path"]
    assert row["raw_sha256"] == _sha256(path)
    with np.load(path) as data:
        assert data["fault_onset"][0, 0]
        assert data["decision_extra_replan"][1]
        assert data["decision_plan_call_count"][1] == 2
        assert data["target_xy"].shape[0] == 5
        assert data["response_lag"][0] == 0
        assert data["metrics"].shape[0] == 5


def test_paired_readout_nullable_and_all_worlds():
    events = {kind: {"events": 0, "complete20": 0, "censored20": 0,
                     "overlapping_events": 0, "world_mean_delta20": None,
                     "complete60": 0 if kind == "recovery" else None,
                     "censored60": 0 if kind == "recovery" else None,
                     "world_mean_full_post60": None}
              for kind in ("onset", "recovery")}
    jobs = b02_runner.plan()
    rows = []
    for job in jobs:
        offset = job["seed"] - 969001
        event = job["arm"] == "availability_event"
        rows.append({**job, "status": "completed", "events": events,
                     "terminal_type": "truncated", "actual_length": 3000,
                     "zero_service": bool(event and offset == 0),
                     "raw_native_J": 100 + offset + (2 if event else 0),
                     "qos_per_step": .3 + offset / 1000 + (-.01 if event and offset == 0 else
                                                       .02 if event else 0),
                     "return_constraint_cost_per_step": .01,
                     "episode_minimum_battery_ratio": .1,
                     "first_service_step": None if offset == 0 else 2,
                     "plan_call_count": 100 + (5 if event else 0),
                     "extra_plan_count": 5 if event else 0,
                     "planning_cpu_seconds": 2 if event else 1,
                     "planning_wall_seconds": 3 if event else 2,
                     "world_mean_response_lag": 0 if event else 10,
                     "response_changes": 5, "response_censored": 1,
                     "terminal_changes": 1, "fault_trace_sha256": str(job["seed"])})
    readout = summarize(rows, [job["job_key"] for job in jobs])
    assert readout["status"] == "complete"
    assert len(readout["world_pairs"]) == 32
    assert readout["world_pairs"][0]["deltas_event_minus_clock"]["qos_per_step"] < 0
    assert readout["world_pairs"][0]["event_zero_service"]
    assert readout["panels"]["availability_event"]["zero_service_worlds"] == 1
    assert readout["contrasts_event_minus_clock"]["raw_native_J"]["mean"] == pytest.approx(2)
    assert readout["contrasts_event_minus_clock"]["raw_native_J"]["n"] == 32
    assert readout["contrasts_event_minus_clock"]["first_service_step"]["status"] == "not_comparable"
    assert readout["fault_trace_agreement"]["equal_pairs"] == 32


def test_b02_callback_stops_submission_on_failed_world():
    jobs = [{"job_key": str(i), "seed": i} for i in range(5)]

    def worker(payload):
        job = payload[0]
        return {**job, "status": "failed" if job["seed"] == 0 else "completed"}

    rows = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        submitted, errors = execute_bounded(
            executor, jobs, 2, lambda job: (job,), rows.append, worker_fn=worker)
    assert submitted == ["0", "1"]
    assert {row["job_key"] for row in rows} == {"0", "1"}
    assert errors == []
