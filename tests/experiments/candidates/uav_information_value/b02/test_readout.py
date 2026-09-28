from __future__ import annotations

import json

import numpy as np
import pytest

from experiments.candidates.uav_information_value.b02 import readout


def synthetic_rows():
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in (17, 18) for arm in readout.ARMS]
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
