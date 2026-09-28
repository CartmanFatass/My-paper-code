from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_information_value import run_b02
from experiments.candidates.uav_information_value.b02 import batch, readout
from experiments.candidates.uav_information_value.controllers import make_controller as make_reference


def test_fixed_fresh_panel_and_entry_admission(tmp_path, monkeypatch):
    jobs = batch.plan()
    batch.validate_plan(jobs)
    assert len(jobs) == len({job["job_key"] for job in jobs}) == 64
    assert sorted({job["seed"] for job in jobs}) == list(range(28100201, 28100233))
    assert all(sum(job["arm"] == arm for job in jobs) == 32 for arm in batch.ARMS)
    assert len(jobs) * batch.HORIZON == 192000
    assert type(batch.make_controller("H_BS")) is type(make_reference("H_BS"))
    with pytest.raises(ValueError, match="fixed"):
        batch.validate_plan(jobs[::-1])
    with pytest.raises(ValueError, match="unknown"):
        batch.make_controller("L")
    monkeypatch.delenv("HMASD_ADMISSION_TOKEN", raising=False)
    monkeypatch.delenv("HMASD_LAUNCH_MANIFEST", raising=False)
    out = tmp_path / "not-admitted"
    with pytest.raises((RuntimeError, SystemExit), match="admission|launch"):
        run_b02.main(["--out", str(out), "--launch-sha", "0" * 40])
    assert not out.exists()


def synthetic_rows():
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in (17, 18) for arm in batch.ARMS]
    rows = []
    for job in jobs:
        candidate = job["arm"] == "P_BS"
        delta = (0.2 if job["seed"] == 17 else -0.1) if candidate else 0.0
        rows.append({**job, "status": "completed", "qos_per_step": 0.5 + delta,
                     "raw_native_J": 100.0 + 100 * delta, "actual_length": 31,
                     "zero_service": False, "terminal_type": "truncated",
                     "first_legal_bs_step": None,
                     "native_final_reserve_uav_count": int(candidate and job["seed"] == 18),
                     "cutoff_event_count_sum": 0, "depletion_event_count_sum": 0,
                     "return_constraint_cost_raw_per_step": 0.1,
                     "episode_minimum_battery_ratio": 0.09 if candidate else 0.11})
    return jobs, rows


def test_complete_reading_preserves_signed_losses_and_final_reserve_tail():
    jobs, rows = synthetic_rows()
    result = readout.summarize(rows[::-1], jobs)
    contrast = result["contrasts"]["qos_per_step"]["P_BS-H_BS"]
    assert contrast["mean"] == pytest.approx(0.05)
    assert contrast["positive"] == contrast["negative"] == 1 and contrast["ties"] == 0
    assert contrast["by_seed"] == pytest.approx({"17": 0.2, "18": -0.1})
    assert result["practical_risk"]["native_final_reserve_uav_count"]["additional_worlds"] == [18]
    assert result["panels"]["H_BS"]["never_seen_bs_worlds"] == [18, 17]
    json.dumps(result, allow_nan=False)
    rows[0]["return_constraint_cost_raw_per_step"] = None
    result = readout.summarize(rows, jobs)
    assert result["contrasts"]["return_constraint_cost_raw_per_step"]["P_BS-H_BS"]["status"] == "not_comparable"


def test_incomplete_and_identity_mismatches_do_not_get_paired_reading():
    jobs, rows = synthetic_rows()
    result = readout.summarize(rows[:-1], jobs)
    assert result["status"] == "incomplete" and not result["contrasts"] and not result["practical_risk"]
    rows[-1] = {**jobs[-1], "status": "failed", "error": "synthetic"}
    assert readout.summarize(rows, jobs)["failed_jobs"] == [jobs[-1]["job_key"]]
    with pytest.raises(ValueError, match="duplicate"):
        readout.summarize(rows + [rows[0]], jobs)
    rows[0] = {**rows[0], "seed": 19}
    with pytest.raises(ValueError, match="identity"):
        readout.summarize(rows, jobs)


def test_exact_native_battery_risk_accounting():
    battery = np.full((3, 8), 0.2, dtype=np.float64)
    battery[0, 0] = 0.10
    battery[1, 0] = 0.099
    battery[2, 2:4] = [0.09, 0.08]
    result = readout.battery_reading(battery)
    assert result["native_reserve_uav_steps"] == 4
    assert result["native_reserve_uav_step_fraction"] == 4 / 24
    assert result["native_final_reserve_uav_count"] == 2
    assert result["native_minimum_battery_ratio"] == result["native_final_minimum_battery_ratio"] == 0.08
    for bad in (np.zeros((0, 8)), np.zeros((3, 7)), np.full((1, 8), np.nan), np.full((1, 8), 1.1)):
        with pytest.raises(ValueError, match="native"):
            readout.battery_reading(bad)


def test_worker_preserves_returned_native_arrays_on_downstream_failure(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    job = {"arm": "H_BS", "seed": 17, "job_key": "H_BS/17"}
    monkeypatch.setattr(batch, "plan", lambda: [job])
    calls = []
    env = SimpleNamespace(env=object(), close=lambda: calls.append("closed"))
    monkeypatch.setattr(batch, "make_env", lambda config, seed: calls.append(seed) or env)
    monkeypatch.setattr(batch, "check_config", lambda env, horizon: {})
    monkeypatch.setattr(batch, "make_controller", lambda arm: object())

    def broken_reading():
        raise ValueError("synthetic readout failure")

    observer = SimpleNamespace(bs_present=[False], native_battery=[np.ones(8)],
                               arrays=lambda: {}, reading=broken_reading)
    monkeypatch.setattr(batch, "PriorObserver", lambda arm, raw: observer)

    def evaluate(controller, env, config, seed, params, observer, progress):
        calls.append(seed)
        progress(1)
        return {"actual_length": 1}, {"rewards": np.asarray([0.5]), "metrics": np.ones((1, 3))}

    monkeypatch.setattr(batch, "evaluate_world", evaluate)
    row = batch.worker((job, str(tmp_path), 1))
    assert calls == [17, 17, "closed"]
    assert row["status"] == "failed" and row["error"] == "synthetic readout failure"
    assert row["partial_observed_steps"] == 1
    with np.load(tmp_path / row["incomplete_raw_path"], allow_pickle=False) as raw:
        np.testing.assert_array_equal(raw["rewards"], [0.5])
        np.testing.assert_array_equal(raw["metrics"], np.ones((1, 3)))


@pytest.mark.parametrize("failure", [False, True])
def test_batch_persistence_and_bounded_failure(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(batch, "ProcessPoolExecutor",
                        lambda max_workers, mp_context: ThreadPoolExecutor(max_workers=max_workers))
    jobs = batch.plan()

    def synthetic_worker(payload):
        job, out_string, threads = payload
        assert threads == 1 and out_string == str(tmp_path)
        if failure and job == jobs[1]:
            batch._write_json(tmp_path / "raw" / "failed.progress.json", {**job, "steps": 7})
            np.savez_compressed(tmp_path / "raw" / "orphan.npz", x=np.zeros(1))
            return {**job, "status": "failed", "error": "synthetic failure"}
        return {**job, "status": "completed", "qos_per_step": 0.5, "raw_native_J": 100.0,
                "actual_length": 3000, "terminal_type": "truncated", "zero_service": False}

    monkeypatch.setattr(batch, "worker", synthetic_worker)
    result = batch.run(tmp_path, "a" * 40, workers=1)
    assert result == json.loads((tmp_path / "summary.json").read_text())
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert all(batch._sha256(tmp_path / name) == value["sha256"]
               for name, value in manifest["artifacts"].items())
    if failure:
        assert result["status"] == "incomplete" and not result["contrasts"] and not result["practical_risk"]
        assert result["submitted_jobs"] == [jobs[0]["job_key"], jobs[1]["job_key"]]
        assert result["known_transition_lower_bound"] == 3007 and result["actual_transitions"] is None
        assert result["orphan_raw"][0]["path"] == "raw/orphan.npz"
        assert len(result["unstarted_jobs"]) == 62
    else:
        assert result["status"] == "complete" and result["completed_jobs"] == 64
        assert result["actual_transitions"] == 192000
        assert result["fits"] == result["optimizer_updates"] == 0
        assert len(result["worker_resources_unmeasured"]) == 64
    with pytest.raises(FileExistsError, match="scientific artifacts"):
        batch.run(tmp_path, "a" * 40)


@pytest.mark.parametrize("arm", ["H_BS", "P_BS"])
def test_nonpanel_native_observer_parity_and_prior_wiring(arm):
    config = batch.make_eval_config(31, 0)
    outputs = []
    for observed in (False, True):
        env = batch.make_env(config, 17)
        try:
            assert batch.check_config(env, 31)["return_reserve_ratio"] == 0.10
            controller = batch.make_controller(arm)
            observer = batch.PriorObserver(arm, env.env) if observed else None
            row, steps = batch.evaluate_world(controller, env, config, 17, batch.PRODUCTION_PARAMS,
                                              observer=observer)
            assert row["actual_length"] == 31 and row["terminal_type"] == "truncated"
            if observed:
                readings = observer.reading()
                assert readings["native_minimum_battery_ratio"] == row["episode_minimum_battery_ratio"]
                assert observer.arrays()["info_native_battery"].shape == (31, 8)
                assert observer.arrays()["info_plan_step"].tolist() == [0, 30]
                if arm == "P_BS":
                    assert readings["prior_bs_xy"] is not None
                else:
                    assert readings["prior_used_plans"] == 0
                json.dumps(readings, allow_nan=False)
            outputs.append((row, steps))
        finally:
            env.close()
    assert outputs[0][0] == outputs[1][0]
    for key in outputs[0][1]:
        np.testing.assert_array_equal(outputs[0][1][key], outputs[1][1][key], err_msg=key)
