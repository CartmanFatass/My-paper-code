from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.uav_information_value import batch, readout, run_b01


def test_fixed_panel_and_native_entry_rejects_missing_admission(tmp_path, monkeypatch):
    jobs = batch.plan()
    batch.validate_plan(jobs)
    assert len(jobs) == 192 and len({job["job_key"] for job in jobs}) == 192
    assert batch.HORIZON * len(jobs) == 576000
    assert sorted({job["seed"] for job in jobs}) == list(range(28100101, 28100133))
    assert all(sum(job["arm"] == arm for job in jobs) == 32 for arm in batch.ARMS)
    with pytest.raises(ValueError, match="fixed"):
        batch.validate_plan(jobs[::-1])
    monkeypatch.delenv("HMASD_ADMISSION_TOKEN", raising=False)
    monkeypatch.delenv("HMASD_LAUNCH_MANIFEST", raising=False)
    out = tmp_path / "not-admitted"
    with pytest.raises((RuntimeError, SystemExit), match="admission|launch"):
        run_b01.main(["--out", str(out), "--launch-sha", "0" * 40])
    assert not out.exists()


def synthetic_rows():
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in (17, 18) for arm in batch.ARMS]
    values = dict(L=1, U=2, B=4, F=9, R=10, H_BS=3)
    rows = [{**job, "status": "completed", "qos_per_step": values[job["arm"]] * job["seed"],
             "raw_native_J": values[job["arm"]] * job["seed"] - 200,
             "zero_service": False, "terminal_type": "truncated", "actual_length": 31,
             "episode_minimum_battery_ratio": 0.2, "cutoff_event_count_sum": 0,
             "return_constraint_cost_per_step": 0.0, "return_constraint_cost_raw_per_step": 0.1}
            for job in jobs]
    return jobs, rows


def test_complete_readout_preserves_pairing_interaction_and_risk_tails():
    jobs, rows = synthetic_rows()
    result = readout.summarize(rows[::-1], jobs)
    assert result["status"] == "complete" and result["completed_jobs"] == 12
    expected = {"U-L": 1, "F-B": 5, "B-L": 3, "F-U": 7, "interaction": 4,
                "F-L": 8, "R-F": 1, "R-L": 9, "H_BS-L": 2}
    for name, coefficient in expected.items():
        contrast = result["contrasts"]["qos_per_step"][name]
        assert contrast["mean"] == 17.5 * coefficient
        assert contrast["by_seed"] == {"17": 17 * coefficient, "18": 18 * coefficient}
        assert contrast["positive"] == 2 and contrast["negative"] == 0
    assert result["panels"]["L"]["metrics"]["raw_native_J"]["min"] == -183
    assert result["contrasts"]["return_constraint_cost_raw_per_step"]["R-L"]["mean"] == 0
    json.dumps(result, allow_nan=False)
    rows[0]["return_constraint_cost_raw_per_step"] = None
    result = readout.summarize(rows, jobs)
    assert result["contrasts"]["return_constraint_cost_raw_per_step"]["U-L"]["status"] == "not_comparable"
    assert result["panels"]["L"]["metrics"]["return_constraint_cost_raw_per_step"]["missing"] == 1


def test_incomplete_and_identity_mismatches_never_get_full_contrasts():
    jobs, rows = synthetic_rows()
    result = readout.summarize(rows[:-1], jobs)
    assert result["status"] == "incomplete" and result["contrasts"] == {}
    assert result["missing_jobs"] == [jobs[-1]["job_key"]]
    rows[-1] = {**jobs[-1], "status": "failed", "error": "synthetic failure"}
    result = readout.summarize(rows, jobs)
    assert result["status"] == "incomplete" and result["contrasts"] == {}
    assert result["failed_jobs"] == [jobs[-1]["job_key"]]
    with pytest.raises(ValueError, match="duplicate"):
        readout.summarize(rows + [rows[0]], jobs)
    rows[0] = {**rows[0], "seed": 19}
    with pytest.raises(ValueError, match="identity"):
        readout.summarize(rows, jobs)


def test_worker_seed_binding_failure_count_and_preservation_error(tmp_path, monkeypatch):
    # Stubbed native execution tests plumbing without exposing a declared panel world.
    (tmp_path / "raw").mkdir()
    jobs = [{"arm": "L", "seed": 17, "job_key": "L/17"}]
    monkeypatch.setattr(batch, "plan", lambda: jobs)
    seen = []
    env = SimpleNamespace(close=lambda: seen.append("closed"))
    monkeypatch.setattr(batch, "make_env", lambda config, seed: seen.append(seed) or env)
    monkeypatch.setattr(batch, "effective_config", lambda env, horizon: {"horizon": horizon})
    monkeypatch.setattr(batch, "make_controller", lambda *args: object())

    def fail(controller, env, config, seed, params, observer, progress):
        seen.append(seed)
        observer.bs_present.append(True)
        observer.bs_seen.append(True)
        progress(1)
        raise ValueError("synthetic native failure")

    monkeypatch.setattr(batch, "evaluate_world", fail)
    row = batch.worker((jobs[0], str(tmp_path), 1))
    assert seen == [17, 17, "closed"] and row["status"] == "failed"
    assert row["partial_observed_steps"] == 1 and row["error_type"] == "ValueError"
    assert row["error"] == "synthetic native failure"
    assert (tmp_path / row["partial_path"]).is_file()
    assert json.loads((tmp_path / "raw/L_17.progress.json").read_text())["steps"] == 1
    monkeypatch.setattr(batch, "_write_json", lambda *args: (_ for _ in ()).throw(OSError("disk full")))
    row = batch.worker((jobs[0], str(tmp_path), 1))
    assert row["error"] == "synthetic native failure" and "disk full" in row["partial_preservation_error"]


@pytest.mark.parametrize("failure", [False, True])
def test_batch_artifact_counts_and_stop_on_failure(tmp_path, monkeypatch, failure):
    # The executor and entire scientific worker are replaced, retaining persistence logic.
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
    stored = json.loads((tmp_path / "summary.json").read_text())
    assert result == stored
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert all(batch._sha256(tmp_path / name) == value["sha256"]
               for name, value in manifest["artifacts"].items())
    if failure:
        assert result["status"] == "incomplete" and result["contrasts"] == {}
        assert result["submitted_jobs"] == [jobs[0]["job_key"], jobs[1]["job_key"]]
        assert result["known_transition_lower_bound"] == 3007
        assert result["actual_transitions"] is None
        assert result["orphan_raw"][0]["path"] == "raw/orphan.npz"
        assert len(result["unstarted_jobs"]) == 190
    else:
        assert result["status"] == "complete" and result["completed_jobs"] == 192
        assert result["actual_transitions"] == 576000
        assert result["fits"] == result["optimizer_updates"] == 0
        assert result["worker_resources_unmeasured"] == [job["job_key"] for job in jobs]
    with pytest.raises(FileExistsError, match="scientific artifacts"):
        batch.run(tmp_path, "a" * 40)


@pytest.mark.parametrize("arm", ["L", "U", "B", "F", "R", "H_BS"])
def test_native_nonpanel_wiring_and_observer_parity(arm):
    # 31 steps crosses one replan. These are correctness fixtures, not panel outcomes.
    config = batch.make_eval_config(31, 0)
    seed = 17
    outputs = []
    for observed in (False, True):
        env = batch.make_env(config, seed)
        try:
            effective = batch.effective_config(env, 31)
            assert effective["energy_stage"] == "S2"
            if not observed and arm == "R":
                controller = HeuristicController(variant("H1", information="central"), env)
            else:
                controller = batch.make_controller(arm, env)
            observer = batch.InformationObserver(arm) if observed else None
            row, steps = batch.evaluate_world(controller, env, config, seed, batch.PRODUCTION_PARAMS,
                                              observer=observer)
            assert row["actual_length"] == 31 and row["terminal_type"] == "truncated"
            assert steps["metrics"].shape == (31, len(batch.TRACE_FIELDS))
            json.dumps(row, allow_nan=False)
            if observed:
                assert len(observer.bs_present) == 31
                assert [plan["step"] for plan in observer.plans] == [0, 30]
                assert observer.arrays()["info_plan_step"].tolist() == [0, 30]
                json.dumps(observer.reading(), allow_nan=False)
            outputs.append((row, steps))
        finally:
            env.close()
    assert outputs[0][0] == outputs[1][0]
    for key in outputs[0][1]:
        np.testing.assert_array_equal(outputs[0][1][key], outputs[1][1][key], err_msg=key)
