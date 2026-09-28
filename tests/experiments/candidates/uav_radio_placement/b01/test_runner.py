"""Native short integration and admission-before-science checks."""

import json

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    HeuristicController, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_radio_placement.b01 import runner
from experiments.candidates.uav_radio_placement.b01.readout import summarize
from experiments.candidates.uav_radio_placement.b01.read_existing import read


def test_short_native_three_program_panel_keeps_clocks_pairing_and_raw(tmp_path):
    (tmp_path / "raw").mkdir()
    config = make_eval_config(31, policy_seed=0)
    seed = 976801
    rows = []
    for arm in runner.ARMS:
        job = {"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
        row = runner._simulate_world(job, tmp_path, 1, config=config)
        assert row["status"] == "completed", row
        assert row["actual_length"] == 31
        assert row["planner_windows"] == 2
        with np.load(tmp_path / row["raw_path"], allow_pickle=False) as arrays:
            assert arrays["user_xy_m"].shape == (32, 30, 2)
            assert arrays["physical_xyz_m"].shape == (32, 8, 3)
            assert arrays["proposal_actions"].shape == (31, 8, 4)
            records = json.loads(str(arrays["planner_records_json"]))
            assert [record["step"] for record in records] == [0, 30]
            assert sum(record["query_count"] for record in records) == row["service_snapshot_calls"]
            assert np.isclose(arrays["reward"].sum(), row["raw_native_J"], atol=1e-12)
        rows.append(row)
    result = summarize(rows, (seed,), [row["job_key"] for row in rows])
    assert result["status"] == "complete"
    assert result["exogenous_pairing_valid"]
    result["service_snapshot_calls"] = sum(row["service_snapshot_calls"] for row in rows)
    artifacts = {"config.json": {"world_seeds": [seed], "horizon": 31},
                 "summary.json": result, "perworld.json": rows}
    for name, value in artifacts.items():
        (tmp_path / name).write_text(json.dumps(value, allow_nan=False))
    manifest = {"launch_sha": "engineering-only", "artifacts": {
        name: {"sha256": runner._sha256(tmp_path / name), "bytes": (tmp_path / name).stat().st_size}
        for name in artifacts}, "raw": {row["job_key"]: {
            "path": row["raw_path"], "sha256": row["raw_sha256"], "bytes": row["raw_bytes"]}
            for row in rows}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    reading = read(tmp_path)
    assert reading["status"] == "verified"
    assert reading["all_search_decisions_reconstructed"]
    assert reading["worlds_verified"] == 3
    with (tmp_path / rows[0]["raw_path"]).open("ab") as handle:
        handle.write(b"corruption")
    with pytest.raises(AssertionError):
        read(tmp_path)


def test_native_admission_precedes_scientific_runner(monkeypatch, tmp_path):
    from experiments.candidates.uav_radio_placement import run_b01
    import scripts.hmasd_admission as admission

    def refused(*args, **kwargs):
        assert kwargs["direction"] == "uav_radio_placement"
        raise RuntimeError("test admission refusal")

    monkeypatch.setattr(admission, "require_admission", refused)
    monkeypatch.setattr(runner, "run", lambda *a, **k: pytest.fail("science before admission"))
    with pytest.raises(RuntimeError, match="test admission refusal"):
        run_b01.main(["--out", str(tmp_path / "out"), "--seed", "36092801", "--launch-sha", "test"])
    assert not (tmp_path / "out").exists()


def test_native_H_diagnostic_queries_preserve_original_H1_trajectory(tmp_path):
    (tmp_path / "raw").mkdir()
    config = make_eval_config(35, policy_seed=0)
    seed = 976802
    row = runner._simulate_world({"arm": "H", "seed": seed, "job_key": f"H/{seed}"},
                                 tmp_path, 1, config=config)
    assert row["status"] == "completed", row
    env = make_env(config, seed)
    try:
        original = HeuristicController(variant("H1", information="central", replan_period=30), env)
        original_row, original_steps = evaluate_world(original, env, config, seed, PRODUCTION_PARAMS)
    finally:
        env.close()
    assert row["raw_native_J"] == original_row["raw_native_J"]
    with np.load(tmp_path / row["raw_path"], allow_pickle=False) as arrays:
        for key in ("own_xyz", "reward", "metrics", "battery", "mode", "target_xy"):
            np.testing.assert_array_equal(arrays[key], original_steps[key])


def test_failed_native_step_preserves_already_spent_model_queries(monkeypatch, tmp_path):
    (tmp_path / "raw").mkdir()
    original_factory = runner.make_env
    seed = 976803

    def factory(config, world_seed):
        env = original_factory(config, world_seed)
        if world_seed == seed:
            def fail_step(_actions):
                raise RuntimeError("injected after first proposal")
            env.step = fail_step
        return env

    monkeypatch.setattr(runner, "make_env", factory)
    row = runner._simulate_world({"arm": "H", "seed": seed, "job_key": f"H/{seed}"},
        tmp_path, 1, config=make_eval_config(31, policy_seed=0))
    assert row["status"] == "failed"
    assert row["service_snapshot_calls"] == row["service_snapshot_calls_completed"] == 1
    assert row["partial_observed_steps"] == 0
    with np.load(tmp_path / row["partial_path"], allow_pickle=False) as arrays:
        assert json.loads(str(arrays["planner_records_json"]))[0]["query_count"] == 1
