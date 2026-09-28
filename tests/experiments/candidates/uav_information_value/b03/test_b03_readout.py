from __future__ import annotations

import json

import pytest

from experiments.candidates.uav_information_value.b03 import readout


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


def test_three_paired_contrasts():
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
