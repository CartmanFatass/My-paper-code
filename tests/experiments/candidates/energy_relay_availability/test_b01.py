"""Short engineering checks; no B01 development or sealed panel world is evaluated."""

from __future__ import annotations

import numpy as np
import pytest
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

from experiments.candidates.energy_relay_availability.configuration import (
    AvailableH1Controller, make_config, make_env,
)
from experiments.candidates.energy_relay_availability.events import FaultObserver, event_windows
from experiments.candidates.energy_relay_availability.readout import summarize
from experiments.candidates.energy_relay_availability import runner
from experiments.candidates.energy_relay_availability.runner import plan, validate_plan
from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS, apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_energy,
)


def test_fixed_plan_and_sealed_rejection():
    jobs = plan()
    validate_plan(jobs)
    assert len(jobs) == 128
    assert {(j["condition"], j["controller"]) for j in jobs} == {
        (c, h) for c in ("fault_off", "fault_on") for h in ("H_local", "H_central")}
    assert {j["seed"] for j in jobs if j["condition"] == "fault_off"} == set(range(965001, 965033))
    with pytest.raises(ValueError, match="sealed"):
        validate_plan([{**jobs[0], "seed": 957001}, *jobs[1:]])
    with pytest.raises(ValueError, match="immutable"):
        validate_plan(jobs[:-1])


@pytest.mark.parametrize("fault_on", [False, True])
def test_effective_s4_profile_and_legal_target_mask(fault_on):
    config = make_config(3)
    env = make_env(config, 42, fault_on)
    try:
        obs, _ = env.reset(seed=42)
        assert env.env.failure_enabled is fault_on
        assert env.env.uav_failure_probability == (0.001 if fault_on else 0.0)
        assert env.env.max_steps == 3
        assert obs.shape == (8, 365)
        # Modify only own legal availability in a copied observation, never raw diagnostics.
        modified = np.asarray(obs, dtype=np.float32).copy()
        index = S7S2_LAYOUT.energy_uavs.start + 2 * S7S2_LAYOUT.energy_uav_fields + 5
        modified[2, index] = 0.0
        charging_index = S7S2_LAYOUT.energy_uavs.start + 3 * S7S2_LAYOUT.energy_uav_fields + 4
        modified[3, charging_index] = 1.0
        assert not own_energy(modified)["available"][2]
        assert own_energy(modified)["available"][3] and own_energy(modified)["charging"][3]
        for information in ("local", "central"):
            controller = AvailableH1Controller(information, env=env)
            controller.reset()
            action = controller.propose(modified, None, 0, np.ones(1, bool), np.zeros(8, bool))
            assert action.shape == (8, 4)
            assert np.isnan(controller.targets_xy[2]).all()
            assert np.isfinite(controller.targets_xy[3]).all()
            assert controller.heuristic.calls == 1
            # The production shield sees the unchanged legal observation and proposal.
            direct = apply_feedback_params(modified, action, np.zeros(8, bool), PRODUCTION_PARAMS)
            assert direct.submitted_actions.shape == (8, 4)
    finally:
        env.close()


def test_fault_timer_expiry_refault_recovery_and_censoring():
    class Raw:
        uav_failure_timers = np.zeros(8, dtype=int)
        uav_failed = np.zeros(8, dtype=bool)

    raw = Raw()
    raw.uav_failure_timers[0] = 1
    raw.uav_failed[0] = True
    observer = FaultObserver(raw)
    obs = np.ones((8, 365), np.float32)
    failed_obs = obs.copy()
    failed_obs[0, S7S2_LAYOUT.energy_uavs.start + 5] = 0.0
    with observer.attach(None):
        raw.uav_failure_timers[0] = 30  # timer 1 expired and immediately refaulted
        raw.uav_failed[0] = True
        observer.on_step(t=0, observations_t=failed_obs, observations_t1=failed_obs)
        raw.uav_failure_timers[0] = 0
        raw.uav_failed[0] = False
        observer.on_step(t=1, observations_t=failed_obs, observations_t1=obs)
    arrays = observer.as_arrays()
    assert arrays["onset"][0, 0] and arrays["expiry"][0, 0]
    assert arrays["refault"][0, 0] and not arrays["recovery"][0, 0]
    assert arrays["recovery"][1, 0]
    assert arrays["pre_timer"][0, 0] == 1 and arrays["post_timer"][0, 0] == 30
    event = event_windows(np.array([.3, .6]), arrays)
    assert event["onset"]["events"] == 1 and event["onset"]["complete20"] == 0
    assert event["recovery"]["rows"][0]["post60_length"] == 1
    assert event["expiry_count"] == event["refault_count"] == 1


def test_window_denominators_and_incomplete_batch_readout():
    qos = np.arange(75, dtype=float) / 100
    mask = np.zeros((75, 8), bool)
    mask[20, 0] = True
    mask[30, 1] = True
    mask[74, 2] = True
    events = {"onset": mask, "recovery": mask.copy(),
              "expiry": np.zeros_like(mask), "refault": np.zeros_like(mask)}
    out = event_windows(qos, events)
    assert out["onset"]["events"] == 3
    assert out["onset"]["complete20"] == 2
    assert out["onset"]["censored20"] == 1
    assert out["onset"]["overlapping_events"] >= 2
    assert out["recovery"]["complete60"] == 0
    rows = [{"job_key": plan()[0]["job_key"], "condition": "fault_off",
             "controller": "H_local", "seed": 965001, "status": "failed"}]
    summary = summarize(rows, [job["job_key"] for job in plan()])
    assert summary["status"] == "incomplete"
    assert len(summary["failed_jobs"]) == 1 and len(summary["missing_jobs"]) == 127
    assert not summary["contrasts"]

    complete_rows = []
    empty_events = {kind: {"events": 0, "complete20": 0, "censored20": 0,
                           "overlapping_events": 0, "world_mean_delta20": None,
                           "complete60": 0 if kind == "recovery" else None,
                           "censored60": 0 if kind == "recovery" else None,
                           "world_mean_full_post60": None}
                    for kind in ("onset", "recovery")}
    empty_events.update(expiry_count=0, refault_count=0)
    for job in plan():
        offset = job["seed"] - (966001 if job["condition"] == "fault_on" else 965001)
        complete_rows.append({**job, "status": "completed", "events": empty_events,
                              "terminal_type": "truncated", "actual_length": 3,
                              "first_service_step": None if offset % 2 else 1,
                              "qos_per_step": .2 + offset / 1000
                              + (.1 if job["controller"] == "H_central" else 0)
                              - (.02 if job["condition"] == "fault_on" else 0)})
    full = summarize(complete_rows, [job["job_key"] for job in plan()])
    assert full["status"] == "complete" and full["completed_jobs"] == 128
    contrast = full["contrasts"]["qos_per_step"]
    assert contrast["central_minus_local"]["fault_off"]["n"] == 32
    assert contrast["central_minus_local"]["fault_off"]["mean"] == pytest.approx(.1)
    assert contrast["on_minus_off"]["H_local"]["mean"] == pytest.approx(-.02)
    assert contrast["on_minus_off"]["H_local"]["se"] > 0
    assert contrast["on_minus_off"]["H_local"]["t95"][1] < 0
    assert contrast["controller_gap_on_minus_off"]["mean"] == pytest.approx(0)
    assert full["panels"]["fault_off/H_local"]["metrics"]["first_service_step"]["missing"] == 16
    assert full["contrasts"]["first_service_step"]["status"] == "not_comparable"


def test_short_native_evaluator_fixture():
    config = make_config(3)
    env = make_env(config, 43, True)
    try:
        # Inject one native failure on the first transition, then let native timer
        # decrement and recovery run. The nonpanel fixture makes no performance claim.
        native_update = env.env._update_uav_failures
        calls = 0

        def injected_update():
            nonlocal calls
            native_update()
            if calls == 0:
                env.env.uav_failure_timers[0] = 2
                env.env.uav_failed[0] = True
            calls += 1

        env.env.uav_failure_probability = 0.0
        env.env._update_uav_failures = injected_update
        observer = FaultObserver(env.env)
        row, steps = evaluate_world(AvailableH1Controller("local", env=env), env, config,
                                    43, PRODUCTION_PARAMS, observer=observer)
        assert row["actual_length"] == 3
        assert row["terminal_type"] in ("terminated", "truncated")
        assert steps["metrics"].shape[0] == len(observer.as_arrays()["post_timer"]) == 3
        assert observer.as_arrays()["onset"][0, 0]
        assert observer.as_arrays()["recovery"][2, 0]
    finally:
        env.close()


def test_bounded_scheduler_stops_and_drains(monkeypatch):
    jobs = [{"job_key": str(i), "seed": i} for i in range(5)]
    started = []

    def synthetic_worker(payload):
        job = payload[0]
        started.append(job["job_key"])
        return {**job, "status": "failed" if job["seed"] == 0 else "completed"}

    monkeypatch.setattr(runner, "_worker", synthetic_worker)
    rows = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        submitted, errors = runner.execute_bounded(
            executor, jobs, 2, lambda job: (job,), rows.append)
    assert submitted == ["0", "1"]
    assert {row["job_key"] for row in rows} == {"0", "1"}
    assert [row["status"] for row in rows].count("failed") == 1
    assert errors == []


def test_orphan_inventory_and_missing_admission(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "fault_on_H_local_966001.npz").write_bytes(b"unreconciled partial bytes")
    orphan = runner.orphan_raw_files(tmp_path, [])
    assert len(orphan) == 1 and orphan[0]["bytes"] == 26
    assert orphan[0]["status"] == "unreconciled"
    output = tmp_path / "unadmitted"
    result = subprocess.run(
        [sys.executable, "experiments/candidates/energy_relay_availability/run_b01.py",
         "--out", str(output), "--launch-sha", "unadmitted"],
        capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not output.exists()


def test_worker_preserves_native_event_rows_in_npz(tmp_path, monkeypatch):
    # Exercise the actual worker serialization on a short engineering fixture, not a
    # scientific panel seed. Production has no plan/horizon override CLI.
    job = {"condition": "fault_on", "controller": "H_local", "seed": 43,
           "job_key": "fault_on/H_local/43"}
    monkeypatch.setattr(runner, "plan", lambda: [job])
    monkeypatch.setattr(runner, "HORIZON", 3)
    native_make_env = runner.make_env

    def injected_env(*args):
        env = native_make_env(*args)
        raw = env.env
        raw.uav_failure_probability = 0.0
        native_update = raw._update_uav_failures
        calls = 0

        def update():
            nonlocal calls
            native_update()
            if calls == 0:
                raw.uav_failure_timers[0] = 2
                raw.uav_failed[0] = True
            calls += 1

        raw._update_uav_failures = update
        return env

    monkeypatch.setattr(runner, "make_env", injected_env)
    (tmp_path / "raw").mkdir()
    result = runner._worker((job, str(tmp_path), 1))
    assert result["status"] == "completed", result
    assert result["actual_length"] == 3
    with np.load(tmp_path / result["raw_path"], allow_pickle=False) as trace:
        assert trace["event_onset_t"].tolist() == [0]
        assert trace["event_recovery_t"].tolist() == [2]
        assert trace["event_onset_pre_length"].tolist() == [0]
        assert trace["event_recovery_post60_length"].tolist() == [1]
        assert not trace["event_recovery_full_60"].any()
        assert np.isnan(trace["event_onset_delta20"]).all()
        assert trace["reward"].sum() == pytest.approx(result["raw_native_J"])
        assert len(trace["fault_post_timer"]) == 3
    assert result["raw_sha256"] == runner._sha256(tmp_path / result["raw_path"])
