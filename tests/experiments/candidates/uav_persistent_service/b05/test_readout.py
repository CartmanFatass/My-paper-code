"""Synthetic complete-panel, early-ending and no-service reading contracts."""

import numpy as np

from experiments.candidates.uav_persistent_service.b05 import readout


def _row(seed, arm="R"):
    return {"seed": seed, "arm": arm, "job_key": f"{arm}/{seed}", "status": "completed",
            "actual_length": 12000, "horizon_normalized_qos": .5, "late6000_mission_qos": .5,
            "raw_native_J": 100., "late6000_native_J": 50., "late_zero_service_steps": 100,
            "late_longest_zero_service_spell": 20, "native_reserve_uav_step_fraction": .01,
            "cutoff_event_count_sum": 0, "depletion_event_count_sum": 0,
            "final300_persistent_reserve_members": 0, "terminal_zero_service": False,
            "unserved_remaining_mission_steps": 0}


def test_all_sixteen_complete_pairs_and_declared_use_rule():
    controls = {s: _row(s) for s in readout.SEEDS}
    rows = [_row(s, "S") | {"late6000_mission_qos": .52, "late_zero_service_steps": 80}
            for s in readout.SEEDS]
    pairing = {s: {"status": "verified"} for s in readout.SEEDS}
    result = readout.summarize(rows, controls, pairing)
    assert result["status"] == "complete"
    assert result["use_rule"]["status"] == "pass"
    assert result["contrasts"]["late6000_mission_qos"]["df"] == 15
    assert result["panel_contrasts"]["original"]["late6000_mission_qos"]["df"] == 7
    rows[0]["cutoff_event_count_sum"] = 1
    assert readout.summarize(rows, controls, pairing)["use_rule"]["status"] == "fail"
    rows[0]["final300_persistent_reserve_members"] = None
    assert readout.summarize(rows, controls, pairing)["use_rule"]["status"] == "unresolved"


def test_incomplete_panel_never_exports_primary_contrasts():
    controls = {s: _row(s) for s in readout.SEEDS}
    rows = [_row(s, "S") for s in readout.SEEDS[:-1]]
    pairing = {s: {"status": "verified"} for s in readout.SEEDS}
    result = readout.summarize(rows, controls, pairing)
    assert result["status"] == "incomplete"
    assert result["contrasts"] == result["panel_contrasts"] == {}
    assert result["missing_new_jobs"] == [f"S/{readout.SEEDS[-1]}"]


def test_all_f_is_not_a_zero_service_label():
    length = 12000
    metrics = np.zeros((length, readout.QOS+1))
    metrics[:, readout.QOS] = .75
    metrics[-3:, readout.QOS] = 0
    raw = {"metrics": metrics, "mode": np.ones((length, 8), dtype=bool),
           "commit_active": np.zeros((length, 8), dtype=bool),
           "native_load": np.ones((length, 8))}
    row = readout.continuity_readings(raw)
    assert row["late_all_f_steps"] == 6000
    assert row["late_all_f_zero_service_steps"] == row["terminal_zero_service_suffix"] == 3
    assert row["late_zero_service_steps"] == row["late_longest_zero_service_spell"] == 3
    assert row["final300_mission_qos"] == .75*297/300
    early = {key: value[:100] for key, value in raw.items()}
    assert readout.continuity_readings(early)["final300_mission_qos"] is None
    assert readout.continuity_readings(early)["late_observed_steps"] == 0


def test_release_followup_stops_at_next_start_and_uses_post_time():
    raw = {"mode": np.zeros((8, 8), dtype=bool),
           "commit_active": np.zeros((8, 8), dtype=bool), "native_load": np.zeros((8, 8))}
    raw["native_load"][3, 0] = 1
    events = [{"kind": "release", "member": 0, "step": 2},
              {"kind": "start", "member": 0, "step": 5},
              {"kind": "release", "member": 0, "step": 7}]
    result = readout.recovery_readings(raw, events)["release_recovery"]
    assert result[0]["first_positive_load_delay_s"] == 2
    assert result[0]["followup_steps"] == 3
    assert result[1]["first_positive_load_delay_s"] is None
