from experiments.candidates.energy_relay_availability.b04.readout import (
    ARMS,
    PAIR_HASHES,
    PRIMARY_FIELDS,
    summarize,
)
from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    battery_tail_readings,
)


def test_completed_panel_readout_has_battery_tails_and_hold_window_units():
    seeds = (973001, 973002)
    expected_keys = [f"{arm}/{seed}" for arm in ARMS for seed in seeds]
    rows = []
    for arm in ARMS:
        for offset, seed in enumerate(seeds):
            candidate = arm == "transit_hold"
            row = {
                "job_key": f"{arm}/{seed}",
                "arm": arm,
                "seed": seed,
                "status": "completed",
                "zero_service": False,
                "terminal_type": "horizon",
                "selected_hold_windows": 2 if candidate else 0,
                "service_snapshot_calls": 9 if candidate else 0,
            }
            row.update({field: float(offset + candidate) for field in PRIMARY_FIELDS})
            row.update(battery_tail_readings(
                [[0.15, 0.10], [0.05, 0.02], [0.0, 0.11]],
                reserve_ratio=0.10,
                service_cutoff_ratio=0.02,
            ))
            row.update({name: f"{seed}-{name}" for name in PAIR_HASHES})
            rows.append(row)

    result = summarize(rows, seeds, expected_keys)

    assert result["status"] == "complete"
    assert result["panels"]["transit_hold"]["planner_hold_windows"] == 4
    assert result["panels"]["transit_hold"]["means"][
        "below_fixed_reserve_uav_step_fraction"] == 4.0 / 6.0
    assert result["panels"]["transit_hold"]["means"][
        "service_cutoff_uav_step_fraction"] == 2.0 / 6.0
