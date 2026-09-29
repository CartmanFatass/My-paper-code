"""B04 binding and runner contracts; no native environment construction."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_availability.runner import execute_bounded
from experiments.candidates.uav_persistent_service.b04 import batch, binding, readout, run_b04


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw(path, length, *, changed_state=None):
    users = np.zeros((length+1, 30, 2))
    if changed_state is not None:
        users[changed_state, 0, 0] = 1
    rng = np.asarray(["a"*64]*(length+1), dtype="U64")
    ends = np.zeros((length, 2), dtype=bool)
    ends[-1, 0] = True
    np.savez(path, user_xy_m=users, rng_state_sha256_by_step=rng,
             ends=ends, reward=np.zeros(length))


def _row(root, arm, seed, length, *, changed_state=None):
    raw = root/f"{arm}_{seed}.npz"
    decisions = root/f"{arm}_{seed}.json"
    _raw(raw, length, changed_state=changed_state)
    decisions.write_text("{}")
    return {"job_key": f"{arm}/{seed}", "arm": arm, "seed": seed,
            "actual_length": length, "effective_config": {"max_steps": 12000},
            "initial_state_sha256": "b", "ground_bs_sha256": "c",
            "user_xy_trace_sha256": "d"*64, "rng_state_stream_sha256": "e"*64,
            "raw_path": raw.name, "raw_sha256": _sha(raw), "raw_bytes": raw.stat().st_size,
            "decisions_path": decisions.name, "decisions_sha256": _sha(decisions)}


def test_fixed_r_only_plan_and_old_root_refusal(tmp_path):
    jobs = readout.plan()
    assert len(jobs) == 8
    assert {job["seed"] for job in jobs} == set(binding.SEEDS)
    assert {job["arm"] for job in jobs} == {"R"}
    out = tmp_path/"out"
    with pytest.raises(ValueError, match="root cannot be changed"):
        batch.run(out, "sha", old_root=tmp_path/"alternate")
    assert not out.exists()


def test_source_blob_refuses_changed_or_linked_file(tmp_path):
    source = tmp_path/"module.py"
    source.write_text("x = 1\n")
    blob = binding.git_blob_id(source.read_bytes())
    report = binding.verify_blob_map(tmp_path, {source.name: blob})
    assert report["file_count"] == 1
    source.write_text("x = 2\n")
    with pytest.raises(ValueError, match="source blob differs"):
        binding.verify_blob_map(tmp_path, {source.name: blob})
    source.unlink()
    source.symlink_to(tmp_path/"missing")
    with pytest.raises(ValueError, match="missing or linked"):
        binding.verify_blob_map(tmp_path, {source.name: blob})


def test_exact_original_manifest_and_path_digest_refusals(tmp_path, monkeypatch):
    artifacts = {}
    expected = {"config.json", "perworld.json", "summary.json"}
    for job in binding.old_plan():
        stem = job["job_key"].replace("/", "_")
        expected.update({f"raw/{stem}.npz", f"raw/{stem}.decisions.json",
                         f"raw/{stem}.progress.json"})
    for name in expected:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        artifacts[name] = {"sha256": _sha(path), "bytes": path.stat().st_size}
    manifest = {"launch_sha": binding.OLD_SOURCE, "artifacts": artifacts,
                "storage_bytes": sum(item["bytes"] for item in artifacts.values())}
    manifest_path = tmp_path/"manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(binding, "ORIGINAL_MANIFEST_SHA256", _sha(manifest_path))
    assert binding.verify_manifest(tmp_path)[1]["verified_artifacts"] == 51
    (tmp_path/"raw/O_H_52292801.npz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="artifact missing or changed"):
        binding.verify_manifest(tmp_path)
    with pytest.raises(ValueError, match="invalid artifact path"):
        binding.verified_path(tmp_path, "../outside", "x")


def test_original_config_rejects_seed_and_effective_config():
    config = {"launch_sha": binding.OLD_SOURCE, "batch": "b02_long_mission_a01",
              "direction": "uav_persistent_service", "jobs": binding.old_plan(),
              "arms": list(binding.OLD_ARMS), "seeds": list(binding.SEEDS),
              "horizon": 12000, "evaluation_workers": 4, "numeric_threads_per_worker": 1,
              "fits": 0, "optimizer_updates": 0, "max_native_transitions": 192000,
              "mission_service_denominator": 12000, "late_window": [6000, 12000],
              "fixed_bins": 3000, "final_reserve_window": [11700, 12000],
              "shield": {"enter_margin": 0.0, "exit_margin": 0.05}}
    effective = {"max_steps": 12000, "n_uavs": 8, "n_users": 30,
                 "n_charging_stations": 2, "charging_station_capacity": [1, 1]}
    rows = [job | {"status": "completed", "actual_length": 12000,
                   "effective_config": effective.copy()} for job in binding.old_plan()]
    summary = {"status": "complete", "planned_jobs": 16, "completed_jobs": 16,
               "launch_sha": binding.OLD_SOURCE,
               "pairing": {str(seed): {"status": "verified"} for seed in binding.SEEDS}}
    assert binding.verify_old_config(config, rows, summary) == effective
    bad = [row.copy() for row in rows]
    bad[0]["seed"] += 1
    with pytest.raises(ValueError, match="identity"):
        binding.verify_old_config(config, bad, summary)
    bad = [row.copy() for row in rows]
    bad[0]["effective_config"] = effective | {"max_steps": 3000}
    with pytest.raises(ValueError, match="effective configuration"):
        binding.verify_old_config(config, bad, summary)


def test_old_station_geometry_and_native_metric_preservation():
    length = 4
    xyz = np.zeros((length, 8, 3))
    xyz[:, :, 2] = 50
    xyz[:, 1, 0] = 100
    eligible = np.zeros((length, 8), dtype=bool)
    eligible[:, :2] = True
    charging = eligible.copy()
    consumed = np.ones((length, 8))*.1
    consumed[:, 0] = .4
    charged = np.zeros((length, 8))
    charged[:, :2] = .2
    raw = {"native_post_xyz": xyz, "native_charging_eligible": eligible,
           "charging": charging, "native_consumed_wh": consumed,
           "native_charger_input_wh": charged, "native_battery": np.ones((length, 8))*.5,
           "nearest_station": np.asarray([[0, 1, 0, 0, 0, 0, 0, 0]]*length),
           "native_station_occupancy": np.ones((length, 2), dtype=int),
           "native_station_queue": np.zeros((length, 2), dtype=int)}
    row = {"actual_length": length, "station_xy": [[0, 0], [100, 0]],
           "gross_charger_input_wh": float(charged.sum()),
           "native_consumed_wh": float(consumed.sum()),
           "native_station_occupancy_uav_steps": 8, "raw_native_J": 123.0}
    original = row.copy()
    derived = readout.reconstruct_old_station(row, raw, station_z=50)
    assert row == original
    assert derived["station0_overload_ticks"] == length
    assert derived["station1_overload_ticks"] == 0
    assert derived["station0_eligible_uav_steps"] == length
    assert derived["station1_eligible_uav_steps"] == length
    assert "raw_native_J" not in derived
    raw["native_post_xyz"] = xyz.copy()
    raw["native_post_xyz"][0, 0, 0] = 30
    with pytest.raises(ValueError, match="geometry differs"):
        readout.reconstruct_old_station(row, raw, station_z=50)


def test_new_r_pairing_unequal_terminal_and_equal_hash(tmp_path):
    old = tmp_path/"old"
    new = tmp_path/"new"
    old.mkdir()
    new.mkdir()
    seed = binding.SEEDS[0]
    rows = {f"{arm}/{seed}": _row(old, arm, seed, 4) for arm in binding.OLD_ARMS}
    r = _row(new, "R", seed, 2)
    assert readout.verify_new_triplet(old, new, rows, r)["status"] == "verified"
    r = _row(new, "R", seed, 2, changed_state=1)
    result = readout.verify_new_triplet(old, new, rows, r)
    assert result["status"] == "failed"
    assert result["pairs"]["O_H"]["users_equal"] is False
    r = _row(new, "R", seed, 4)
    r["rng_state_stream_sha256"] = "f"*64
    result = readout.verify_new_triplet(old, new, rows, r)
    assert result["status"] == "failed"
    assert result["pairs"]["P"]["equal_length_full_stream_equal"] is False


def test_incomplete_suppresses_all_contrasts():
    old = {f"{arm}/{seed}": {"arm": arm, "seed": seed, "actual_length": 12000,
                             "terminal_zero_service": False,
                             "final300_persistent_reserve_members": 0}
           for seed in binding.SEEDS for arm in binding.OLD_ARMS}
    assert readout.summarize([], old)["contrasts"] == {}
    rows = [job | {"status": "incompatible_comparator", "native_completed": True,
                   "actual_length": 12000} for job in readout.plan()]
    result = readout.summarize(rows, old)
    assert result["status"] == "incomplete"
    assert result["native_completed_new_jobs"] == 8
    assert result["contrasts"] == {}


def test_incompatible_result_stops_submission_and_drains_started_jobs():
    gate = threading.Event()
    begun = threading.Barrier(4)
    jobs = [{"job_key": str(index)} for index in range(8)]
    submitted = []
    received = []

    def worker(job):
        begun.wait(5)
        if job["job_key"] != "0":
            assert gate.wait(5)
        return job | {"status": "completed", "native_completed": True,
                      "actual_length": 12000, "raw_path": job["job_key"]+".npz"}

    def on_result(row):
        if row["job_key"] == "0":
            row["status"] = "incompatible_comparator"
            gate.set()
        received.append(row)

    with ThreadPoolExecutor(max_workers=4) as executor:
        execute_bounded(executor, jobs, 4, lambda job: job, on_result,
                        submitted, worker_fn=worker)
    assert submitted == ["0", "1", "2", "3"]
    assert {row["job_key"] for row in received} == set(submitted)
    assert all(row["native_completed"] and row["raw_path"] for row in received)


def test_admission_precedes_batch_import_or_outputs(tmp_path, monkeypatch):
    import sys

    called = []
    def reject(*args, **kwargs):
        called.append("admission")
        raise RuntimeError("admission rejected")
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission",
                        SimpleNamespace(require_admission=reject))
    out = tmp_path/"out"
    with pytest.raises(RuntimeError, match="admission rejected"):
        run_b04.main(["--out", str(out), "--launch-sha", "any"])
    assert called == ["admission"]
    assert not out.exists()
