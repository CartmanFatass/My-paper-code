from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import Future
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.energy_relay_diagnostics import run_b01
from experiments.candidates.energy_relay_diagnostics.b01 import study


def test_optional_size_telemetry_failure_does_not_abort_collection(tmp_path, monkeypatch):
    volatile = tmp_path / "ephemeral.log"
    volatile.write_text("fixture")
    original = Path.stat

    def gone(path, *args, **kwargs):
        if path == volatile:
            raise FileNotFoundError("synthetic concurrent removal")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", gone)
    cost = study._costs(time.perf_counter(), tmp_path, [])
    assert cost["output_allocated_bytes"] is None
    assert cost["output_bytes_telemetry"] == "resources_unmeasured"
    assert cost["output_bytes_telemetry_error"] == "FileNotFoundError"


def test_frozen_plan_and_forbidden_worlds():
    jobs = study.fixed_plan()
    assert len(jobs) == len(set(jobs)) == 136
    assert {job.seed for job in jobs} == set(range(955001, 955033))
    assert sum(job.capture_inputs for job in jobs) == 8
    assert sum(job.collector for job in jobs) == 8
    assert {job.panel for job in jobs} == {entry[0] for entry in study.PANEL_LAYOUT}
    for job in jobs:
        study.validate_job(job)
        assert job.action_mode == "stochastic" or job.draw is None
        if job.collector:
            assert job.seed in study.FULL_WORLDS and job.draw == 0
    with pytest.raises(ValueError, match="holdout"):
        study.validate_job(replace(jobs[0], seed=957001))
    with pytest.raises(ValueError, match="outside frozen"):
        study.validate_job(replace(jobs[0], panel="extra_panel"))
    with pytest.raises(ValueError, match="outside frozen"):
        study.validate_job(replace(jobs[0], seed=955033))


def _checkpoint_fixture(tmp_path, monkeypatch):
    root = tmp_path / "checkpoints"
    root.mkdir()
    config = {"algorithm": "mappo", "k": 10, "distribution": "tanh_gaussian"}
    config_sha = hashlib.sha256(json.dumps(
        config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    pins = {}
    for name, rollout, transitions in (("c00", 0, 0), ("c03", 100, 600000)):
        directory = root / name
        directory.mkdir()
        model = (name + " fixture").encode()
        (directory / "agent.pt").write_bytes(model)
        digest = hashlib.sha256(model).hexdigest()
        pins[name] = {"agent_pt_sha256": digest, "policy_fingerprint": name + "fp",
                      "rollout": rollout, "transitions": transitions}
        record = {"object_id": study.OBJECT_ID, "programme": study.PROGRAMME,
                  "launch_sha": study.SOURCE_SHA, "checkpoint": name,
                  "agent_pt": "agent.pt", "agent_pt_sha256": digest,
                  "agent_pt_bytes": len(model), "policy_fingerprint": name + "fp",
                  "training_seed": study.POLICY_SEED, "rollout": rollout,
                  "transitions": transitions, "config": config}
        (directory / "record.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(study, "PINS", pins)
    monkeypatch.setattr(study, "CONFIG_SHA256", config_sha)
    return root


def test_checkpoint_pins_and_refusals_before_output(tmp_path, monkeypatch):
    root = _checkpoint_fixture(tmp_path, monkeypatch)
    checked = study.validate_checkpoints(root)
    assert set(checked) == {"c00", "c03"}
    assert checked["c03"]["record"]["transitions"] == 600000
    output = tmp_path / "must-not-exist"
    record_path = root / "c03" / "record.json"
    original = record_path.read_bytes()
    record = json.loads(original)
    record["launch_sha"] = "0" * 40
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="pinned identity"):
        study.run_batch(checkpoint_root=root, out=output, launch_sha="a" * 40,
                        workers=1, threads=1)
    assert not output.exists()
    record_path.write_bytes(original)
    model_path = root / "c03" / "agent.pt"
    model_path.write_bytes(b"different")
    with pytest.raises(ValueError, match="actual SHA-256"):
        study.validate_checkpoints(root)
    assert not output.exists()


def test_cli_admits_and_matches_sha_before_study_import(tmp_path, monkeypatch):
    import builtins
    from scripts import hmasd_admission

    original_import = builtins.__import__
    order = []

    def tracked_import(name, *args, **kwargs):
        if name.endswith("energy_relay_diagnostics.b01.study"):
            order.append("study")
        return original_import(name, *args, **kwargs)

    def refuse(*args, **kwargs):
        order.append("admission")
        raise RuntimeError("refused")

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    args = ["--checkpoint-root", str(tmp_path / "checkpoints"), "--out", str(tmp_path / "out"),
            "--launch-sha", "a" * 40]
    with pytest.raises(RuntimeError, match="refused"):
        run_b01.main(args)
    assert order == ["admission"] and not (tmp_path / "out").exists()

    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *_args, **_kwargs: {"sha": "b" * 40})
    with pytest.raises(ValueError, match="admitted source SHA"):
        run_b01.main(args)
    assert order == ["admission"] and not (tmp_path / "out").exists()


def test_cli_exit_witness_follows_batch_summary(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *_args, **_kwargs: {"sha": "a" * 40})
    args = ["--checkpoint-root", str(tmp_path / "checkpoints"), "--out", str(tmp_path / "out"),
            "--launch-sha", "a" * 40]
    monkeypatch.setattr(study, "run_batch", lambda **_kwargs: {"status": "COMPLETE"})
    assert run_b01.main(args) == 0
    monkeypatch.setattr(study, "run_batch", lambda **_kwargs: {"status": "FAILED"})
    assert run_b01.main(args) == 1


def test_worker_saves_one_raw_file_with_comparable_action_digest(tmp_path, monkeypatch):
    job = next(job for job in study.fixed_plan() if job.panel == "c03_eval_deterministic"
               and job.capture_inputs)
    native = {"reward": np.asarray([1.0, 2.0]),
              "mode": np.zeros((2, 8), dtype=bool)}
    obs = {key: np.zeros((2, 8, 4), np.float32) for key in study.ACTION_KEYS[:4]}
    obs.update(own_xyz_t=np.zeros((2, 8, 3), np.float32),
               own_xyz_t1=np.zeros((2, 8, 3), np.float32),
               held_source_t=np.zeros(2, np.int64), held_age=np.arange(2))
    obs["observations_t"] = np.ones((2, 8, 365), np.float32)
    obs["actor_distribution"] = "tanh_gaussian"
    result = {"row": {"seed": job.seed, "actual_length": 2, "failed": False,
                      "worker_peak_rss_kib": 123},
              "arrays": native, "observation": obs, "identity": {}}
    monkeypatch.setattr(study.ev, "evaluate_task", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(study, "action_reading", lambda _result: {"test_reading": 1.0})
    (tmp_path / "logs").mkdir()
    (tmp_path / "raw" / job.panel).mkdir(parents=True)
    records = {"c03": {"directory": str(tmp_path), "agent_pt_sha256": "x" * 64,
                       "config_sha256": "y" * 64}}
    row = study._run_job(job, records, str(tmp_path), 1)
    assert row["native_digest"] == study.arrays_digest(native)
    assert row["action_digest"] == study.arrays_digest({key: obs[key] for key in study.ACTION_KEYS})
    assert row["raw_path"] == f"raw/{job.panel}/{job.seed}.npz"
    assert row["new_optimizer_updates"] == row["new_updates"] == 0
    with np.load(tmp_path / row["raw_path"]) as raw:
        assert set(raw.files) == {"reward", "mode", *("obs_" + key for key in obs)}
        assert np.array_equal(raw["reward"], native["reward"])
        assert np.array_equal(raw["obs_observations_t"], obs["observations_t"])
    with pytest.raises(FileExistsError):
        study._run_job(job, records, str(tmp_path), 1)


def test_batch_records_failed_cell_without_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "validate_checkpoints", lambda _root: {
        name: {"record": {"checkpoint": name}, "directory": str(tmp_path),
               "agent_pt_sha256": "x" * 64, "config_sha256": "y" * 64}
        for name in ("c00", "c03")})
    calls = []

    class Pool:
        def __init__(self, **kwargs):
            assert kwargs["mp_context"].get_start_method() == "spawn"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, _function, job, *_args):
            calls.append(job)
            future = Future()
            if job == study.fixed_plan()[0]:
                future.set_exception(RuntimeError("synthetic failure"))
            else:
                future.set_result({"seed": job.seed, "actual_length": 3000,
                                   "native_signature": {"reward": ("<f8", ())},
                                   "worker_peak_rss_kib": 10})
            return future

    monkeypatch.setattr(study, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(study, "read_panels", lambda panels, raw_root: {"panel_count": len(panels)})
    out = tmp_path / "batch"
    out.mkdir()
    kernel_metadata = out / "launch-manifest.json"
    kernel_metadata.write_text('{"accepted": true}', encoding="utf-8")
    summary = study.run_batch(checkpoint_root=tmp_path, out=out, launch_sha="a" * 40,
                              workers=1, threads=1)
    assert kernel_metadata.read_text(encoding="utf-8") == '{"accepted": true}'
    assert len(calls) == len(set(calls)) == 136
    assert summary["status"] == "FAILED"
    assert summary["counts"] == {"episodes_planned": 136, "episodes_completed": 135,
                                  "episodes_failed": 1, "actual_transitions": 405000,
                                  "steps": 405000, "new_optimizer_updates": 0,
                                  "new_updates": 0, "fits": 0}
    assert summary["failures"][0]["error"] == "RuntimeError: synthetic failure"
    assert (out / "summary.json").is_file() and (out / "progress.jsonl").is_file()
    with pytest.raises(FileExistsError, match="science output"):
        study.run_batch(checkpoint_root=tmp_path, out=out, launch_sha="a" * 40,
                        workers=1, threads=1)
