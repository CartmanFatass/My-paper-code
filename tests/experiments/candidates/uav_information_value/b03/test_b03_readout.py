from __future__ import annotations

import json

import pytest

from experiments.candidates.uav_information_value.b03 import batch, readout


def rows():
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in (17, 18) for arm in readout.ARMS]
    result = []
    for job in jobs:
        arm, seed = job["arm"], job["seed"]
        increment = {"H_BS": 0, "P_BS": 2, "S0_BS": 1}[arm] * (1 if seed == 17 else -1)
        result.append({**job, "status": "completed", "raw_native_J": 100 + increment,
                       "qos_per_step": 0.5 + increment / 100,
                       "actual_length": 31, "zero_service": False, "terminal_type": "truncated",
                       "first_legal_bs_step": None,
                       "cutoff_event_count_sum": int(arm == "P_BS" and seed == 18),
                       "depletion_event_count_sum": 0,
                       "native_final_reserve_uav_count": int(arm == "S0_BS" and seed == 17),
                       "native_minimum_battery_ratio": 0.08 if arm == "S0_BS" else 0.1})
    return jobs, result


def test_fixed_plan_and_three_paired_contrasts():
    jobs = batch.plan()
    batch.validate_plan(jobs)
    assert len(jobs) == 96 and batch.HORIZON == 3000 and jobs[0]["arm"] == "H_BS"
    test_jobs, data = rows()
    result = readout.summarize(data, test_jobs)
    assert result["status"] == "complete"
    assert set(result["contrasts"]["raw_native_J"]) == {
        "P_BS-S0_BS", "P_BS-H_BS", "S0_BS-H_BS"}
    assert result["contrasts"]["raw_native_J"]["P_BS-S0_BS"]["by_seed"] == {
        "17": 1, "18": -1}
    assert result["practical_risk"]["cutoff_event_count_sum"]["P_BS-S0_BS"]["additional_worlds"] == [18]
    assert result["practical_risk"]["native_final_reserve_uav_count"]["S0_BS-H_BS"]["additional_worlds"] == [17]
    json.dumps(result, allow_nan=False)


def test_incomplete_suppresses_paired_claims_and_rejects_identity_errors():
    jobs, data = rows()
    partial = readout.summarize(data[:-1], jobs)
    assert partial["status"] == "incomplete" and partial["contrasts"] == partial["practical_risk"] == {}
    data[-1] = {**jobs[-1], "status": "failed", "error": "synthetic"}
    assert readout.summarize(data, jobs)["failed_jobs"] == [jobs[-1]["job_key"]]
    with pytest.raises(ValueError, match="duplicate"):
        readout.summarize(data + [data[0]], jobs)
    data[0] = {**data[0], "seed": 19}
    with pytest.raises(ValueError, match="identity"):
        readout.summarize(data, jobs)


def test_invalid_worker_job_preserves_failure_record_without_native_launch(tmp_path):
    (tmp_path / "raw").mkdir()
    job = {"arm": "S0_BS", "seed": 17, "job_key": "S0_BS/17"}
    record = batch.worker((job, str(tmp_path), 1))
    assert record["status"] == "failed" and record["partial_observed_steps"] == 0
    assert "undeclared job" in record["error"]
    progress = json.loads((tmp_path / "raw" / "S0_BS_17.progress.json").read_text())
    assert progress["status"] == "failed" and progress["steps"] == 0


def test_admission_rejection_precedes_output_creation(monkeypatch, tmp_path):
    from experiments.candidates.uav_information_value import run_b03
    import scripts.hmasd_admission as admission

    def reject(*args, **kwargs):
        raise RuntimeError("synthetic admission rejection")

    monkeypatch.setattr(admission, "require_admission", reject)
    out = tmp_path / "no-output"
    with pytest.raises(RuntimeError, match="synthetic admission rejection"):
        run_b03.main(["--out", str(out), "--launch-sha", "synthetic"])
    assert not out.exists()
