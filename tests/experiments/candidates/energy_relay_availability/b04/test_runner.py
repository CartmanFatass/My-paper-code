import numpy as np

from experiments.candidates.energy_relay_availability.b04 import runner
from experiments.candidates.energy_relay_availability.b04.readout import PRIMARY_FIELDS, summarize
from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config


def test_native_worker_rows_complete_the_paired_readout(tmp_path, monkeypatch):
    # A previously exposed technical seed; never one of the unlaunched panel seeds.
    seed = 973001
    monkeypatch.setattr(runner, "_CONFIG", make_eval_config(20, policy_seed=0))
    (tmp_path / "raw").mkdir()
    rows = []
    for arm in runner.ARMS:
        job = {"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
        row = runner._simulate_world(job, tmp_path, threads=1)
        assert row["status"] == "completed", row.get("traceback", row)
        assert row["actual_length"] == 20
        assert all(field in row for field in PRIMARY_FIELDS)
        assert row["fixed_reserve_ratio"] == 0.1
        assert row["service_cutoff_ratio"] == 0.02
        rows.append(row)
    result = summarize(rows, (seed,), [r["job_key"] for r in rows])
    assert result["status"] == "complete"
    assert result["exogenous_pairing_valid"]
    candidate = rows[1]
    assert candidate["planner_windows"] == 2
    assert candidate["service_snapshot_calls"] > 0
    with np.load(tmp_path / candidate["raw_path"], allow_pickle=False) as trace:
        np.testing.assert_array_equal(trace["planner_step"], [0, 10])
        assert trace["planner_h1_targets_xy"].shape == (2, 8, 2)
