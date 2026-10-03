"""Finite addresses, identity, stop propagation and effect-free driver wiring."""
from concurrent.futures import Future
import json
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_service_resource_control.b01_native_selector import (
    budget, contract, reading, study,
)
from experiments.candidates.uav_service_resource_control.b01_native_selector.learner import Learner


def test_exact_addresses_full_purchase_and_constant_identity_alias():
    audits = contract.audit_jobs()
    train = sum((contract.training_jobs(i) for i in range(3)), [])
    calibration = contract.calibration_jobs()
    assert len(audits) == 6 and len(train) == 384 and len(calibration) == 96
    assert [contract.training_jobs(i)[-1]["seed"] for i in range(3)] == [40031128, 40032128, 40033128]
    assert len(set(r["seed"] for r in train)) == 384
    assert not ({r["seed"] for r in train} & set(contract.DEV_WORLDS + contract.FINAL_WORLDS))
    for selected, expected in (("C", 160), ("H_T", 160), ("T_20", 192)):
        final = contract.final_jobs(selected)
        assert len(final) == expected
        assert len(audits+train+calibration+final) == (646 if expected == 160 else 678)
        assert len({r["job_key"] for r in audits+train+calibration+final}) == 486+expected
        for index, seed in enumerate(contract.FINAL_WORLDS):
            arms = [r["arm"] for r in final if r["seed"] == seed]
            assert set(arms) == ({"C", "H_T", "L0", "L1", "L2"} | ({"T_star"} if expected == 192 else set()))
            first = [r["arm"] for r in final if r["seed"] == contract.FINAL_WORLDS[0]]
            shift = index % len(first)
            assert arms == first[shift:] + first[:shift]


def test_calibration_fsum_fixed_order_exact_ties_and_no_world_omission():
    rows = [dict(**spec, status="completed", J_total=1.) for spec in contract.calibration_jobs()]
    selected = contract.select_ordinary(rows[::-1])
    assert selected["selected"] == selected["final_identity_alias"] == "C"
    for row in rows:
        if row["arm"] == "T_20":
            row["J_total"] = 1.5
    selected = contract.select_ordinary(rows)
    assert selected["selected"] == "T_20" and selected["final_identity_alias"] is None
    assert selected["program"] == dict(program="T", theta=.20)
    with pytest.raises(ValueError):
        contract.select_ordinary(rows[:-1])
    with pytest.raises(ValueError):
        contract.select_ordinary(rows[:-1]+[rows[0]])
    rows[0]["status"] = "failed"
    with pytest.raises(ValueError):
        contract.select_ordinary(rows)


def test_failure_stops_new_dispatch_and_preserves_first_reason(tmp_path):
    class Executor:
        def submit(self, fn, payload):
            future = Future()
            future.set_result(fn(payload))
            return future
        def shutdown(self, *, wait, cancel_futures):
            assert not wait and cancel_futures
    class Budget:
        out = tmp_path
        def poll(self):
            return not (self.out/budget.STOP_NAME).exists()
    jobs = [dict(job_key=str(i)) for i in range(8)]
    seen, results = [], []
    def worker(spec):
        seen.append(spec["job_key"])
        return dict(**spec, status="failed" if spec["job_key"] == "0" else "completed")
    submitted = budget.execute(Executor(), jobs, 3, worker, lambda spec: spec, results.append, Budget())
    assert submitted == seen == ["0", "1", "2"]
    assert len(results) == 3
    first = json.loads((tmp_path/budget.STOP_NAME).read_text())
    budget.request_stop(tmp_path, "second failure cannot replace first")
    assert json.loads((tmp_path/budget.STOP_NAME).read_text()) == first
    with pytest.raises(budget.BudgetStop):
        budget.check_stop(tmp_path)


@pytest.mark.parametrize("pending_future", [False, True])
def test_stop_grace_bounds_live_children_even_after_futures_finish(monkeypatch, tmp_path, pending_future):
    clock = [0.]
    monkeypatch.setattr(budget.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(budget.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0]+1.))
    monkeypatch.setattr(budget, "STOP_GRACE_SECONDS", 3.)
    monkeypatch.setattr(budget, "KILL_GRACE_SECONDS", 2.)
    monkeypatch.setattr(budget, "REAP_GRACE_SECONDS", 2.)
    monkeypatch.setattr(budget, "_descendants", lambda processes: {})
    monkeypatch.setattr(budget, "_live_descendants", lambda identities: [])
    monkeypatch.setattr(budget, "_signal_descendants", lambda *args: None)
    events, futures = [], []
    class Process:
        pid = 12345  # Pure fake; all signal/ancestry methods above are mocked.
        alive = True
        def is_alive(self):
            return self.alive
        def terminate(self):
            events.append("TERM")  # Simulate a worker ignoring SIGTERM.
        def kill(self):
            events.append("KILL")
            self.alive = False
            for future in futures:
                if not future.done():
                    future.set_exception(RuntimeError("fake killed worker"))
        def join(self, timeout):
            assert not self.alive and timeout == 0.
    process = Process()
    class Executor:
        _processes = {12345: process}
        _executor_manager_thread = process  # Fake manager exits when child does.
        def submit(self, fn, spec):
            future = Future()
            if not pending_future:
                future.set_result(dict(**spec, status="failed"))
            else:
                future.set_running_or_notify_cancel()
            futures.append(future)
            budget.request_stop(tmp_path, "fake actual worker failure")
            return future
        def shutdown(self, *, wait, cancel_futures):
            events.append("shutdown")
            assert not wait and cancel_futures
            self._processes = None
    class Budget:
        out = tmp_path
        def poll(self):
            return not (self.out/budget.STOP_NAME).exists()
    def fake_wait(pending, **kwargs):
        clock[0] += 1.
        return {f for f in pending if f.done()}, {f for f in pending if not f.done()}
    monkeypatch.setattr(budget, "wait", fake_wait)
    rows, executor = [], Executor()
    jobs = [dict(job_key=str(i)) for i in range(4)]
    submitted = budget.execute(executor, jobs, 3, lambda spec: None, lambda spec: spec, rows.append, Budget())
    assert submitted == ["0"] and len(rows) == 1
    assert events == ["shutdown", "TERM", "KILL"]
    assert executor._b01_shutdown_started and not getattr(executor, "_b01_nonblocking_shutdown", False)
    record = json.loads((tmp_path/"stop-escalation.json").read_text())
    assert record["status"] == "reaped" and not record["unreaped_worker_pids"]


@pytest.mark.parametrize("manager_stuck", [False, True])
def test_successful_work_shutdown_still_observes_existing_budget(monkeypatch, tmp_path, manager_stuck):
    clock, events = [0.], []
    monkeypatch.setattr(budget.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(budget.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0]+1.))
    monkeypatch.setattr(budget, "STOP_GRACE_SECONDS", 3.)
    monkeypatch.setattr(budget, "KILL_GRACE_SECONDS", 2.)
    monkeypatch.setattr(budget, "REAP_GRACE_SECONDS", 2.)
    monkeypatch.setattr(budget, "_descendants", lambda processes: {})
    monkeypatch.setattr(budget, "_live_descendants", lambda identities: [])
    monkeypatch.setattr(budget, "_signal_descendants", lambda *args: None)
    class Process:
        pid, alive = 12345, True
        def is_alive(self):
            return self.alive
        def terminate(self):
            events.append("TERM")
        def kill(self):
            events.append("KILL")
            self.alive = False
        def join(self, timeout):
            assert not self.alive
    process = Process()
    class Executor:
        _processes = {12345: process}
        _executor_manager_thread = SimpleNamespace(is_alive=lambda: manager_stuck or process.alive)
        def submit(self, fn, spec):
            future = Future()
            future.set_result(dict(**spec, status="completed"))
            return future
        def shutdown(self, *, wait, cancel_futures):
            events.append("shutdown")
            assert not wait and cancel_futures
            self._processes = None
    executor = Executor()
    class Budget:
        out = tmp_path
        def poll(self):
            # Genuine existing purchase limit fires only during fake finalization;
            # successful results alone do not trigger a stop or a new time gate.
            if clock[0] >= 3.:
                budget.request_stop(tmp_path, "fake original wall limit")
            return not (tmp_path/budget.STOP_NAME).exists()
    def fake_wait(pending, **kwargs):
        clock[0] += 1.
        return set(pending), set()
    monkeypatch.setattr(budget, "wait", fake_wait)
    rows = []
    assert budget.execute(executor, [dict(job_key="one")], 1, None, lambda spec: spec,
                          rows.append, Budget()) == ["one"]
    assert rows[0]["status"] == "completed" and events == ["shutdown", "TERM", "KILL"]
    assert bool(getattr(executor, "_b01_nonblocking_shutdown", False)) == manager_stuck
    record = json.loads((tmp_path/"stop-escalation.json").read_text())
    assert record["status"] == ("unreconciled-after-kill" if manager_stuck else "reaped")


def test_selected_linux_runtime_has_pid_identity_signal_api():
    import os
    import signal
    assert callable(os.pidfd_open) and callable(signal.pidfd_send_signal)


def test_checkpoint_file_state_identity_and_inference_only(tmp_path):
    (tmp_path/"raw").mkdir()
    agent = Learner(**contract.FIT_SEEDS[0])
    initial = study.save_checkpoint(tmp_path, 0, 0, agent)
    loaded = study.load_checkpoint(tmp_path, initial, 0)
    assert loaded.counts() == agent.counts() and loaded.digests() == agent.digests()
    # One synthetic partial block, zero Adam updates; exercises complete checkpoint
    # serialization with numpy PCG64 state, rather than a hand-built digest fixture.
    agent.start_episode(0, True)
    agent.decide(np.zeros(327, np.float32), False, 0)
    agent.observe_reward(.5, True)
    final = study.save_checkpoint(tmp_path, 0, 1, agent)
    loaded = study.load_checkpoint(tmp_path, final, 0)
    assert loaded.inference_only and loaded.updates == 0
    with pytest.raises(RuntimeError):
        loaded.start_episode(1, True)
    with (tmp_path/final["path"]).open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(AssertionError, match="file identity"):
        study.load_checkpoint(tmp_path, final, 0)


def test_reward_hook_after_one_captured_tick_and_terminal_flag(monkeypatch):
    events = []
    def native_step(self, submitted):
        events.append("captured")
        return "obs", .25, False, True, "info"
    monkeypatch.setattr(study.CaptureEnv, "step", native_step)
    learner = SimpleNamespace(observe_reward=lambda reward, terminal: events.append((reward, terminal)))
    env = study.RewardCaptureEnv(None, None, learner)
    assert env.step("command") == ("obs", .25, False, True, "info")
    assert events == ["captured", (.25, True)]


def test_final_checkpoint_load_is_inside_timed_mission_not_worker_preamble(monkeypatch):
    spec, receipt = dict(program="SELECTOR", phase="final", fit=0), {"path": "fixed.pt"}
    def forbidden(*args, **kwargs):
        raise AssertionError("checkpoint loaded before mission timing")
    monkeypatch.setattr(study, "load_checkpoint", forbidden)
    monkeypatch.setattr(study, "episode", lambda actual, out, *, final_checkpoint:
                        (actual, out, final_checkpoint))
    assert study.mission_worker((spec, "owned-output", receipt)) == (spec, "owned-output", receipt)


def test_pure_ordinary_command_nan_hold_and_resource_scales():
    obs = np.zeros((8, 365), np.float32)
    obs[:, :3] = [0., 0., 1./3.]
    targets = np.full((8, 2), np.nan)
    targets[0], targets[1] = [45., 0.], [0., 15.]
    action = reading.ordinary_command(obs, targets)
    np.testing.assert_array_equal(action[:, :2], [[1., 0.], [0., .5]]+[[0., 0.]]*6)
    assert action.dtype == np.float32 and not action[:, 3].any()


def test_public_law_edges_and_return_are_independent_closed_form():
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.energy import (
        PublicLaw, flight_edge, target_return,
    )
    # Eight edges, four returns, one constant bundle. Independent reference power
    # arguments below are finite analytic arithmetic, not native/model queries.
    def reference(v, w=0.):
        return (79.86*(1+3*v*v/120**2) + 88.63*np.sqrt(max(0.,
                np.sqrt(1+v**4/(4*4.03**4))-v*v/(2*4.03**2)))
                + .5*.6*1.225*.05*.503*v**3 + 15*abs(w))
    law, costs = PublicLaw({}), {}
    cases = [([0., 0., 100.], 0, 0.), ([30., 0., 105.], 1, reference(30., 5.)),
             ([45., 0., 107.], 2, reference(30., 5.)+reference(15., 2.)),
             ([0., 0., 111.], 3, 3*reference(0.)+15*11),
             ([60., 0., 100.], 2, 2*reference(30.)),
             ([-30., 0., 95.], 1, reference(30., -5.)),
             ([0., -15., 100.], 1, reference(15.)),
             ([0., 0., 90.], 2, 2*reference(0., -5.))]
    for target, ticks, energy in cases:
        actual = flight_edge([0., 0., 100.], target, .8, 16., law, counters=costs)
        assert actual[0] == ticks
        np.testing.assert_allclose(actual[1], energy/3600., rtol=1e-14, atol=1e-15)
        assert actual[2] == .8-(actual[1]+16.)/160.-.10
    stations = np.array([[-3., 0., 100.], [3., 0., 100.]])
    for target, nearest, distance in (([0., 0., 100.], 0, 3.), ([3., 0., 100.], 1, 0.),
                                     ([-3., 0., 104.], 0, 4.), ([3., 0., 103.], 1, 3.)):
        station, wh = target_return(target, stations, law, counters=costs)
        assert station == nearest
        np.testing.assert_allclose(wh, distance/3*reference(3.)/3600., rtol=1e-14, atol=1e-15)
    assert costs["flight_edges"] == 8 and costs["return_evaluations"] == 4
    assert law.cold_counts["constant_power_evaluations"] == 3
