"""Binding, complete-panel and rejected-branch refusal; zero native transitions."""
from copy import deepcopy
import json
import os
import sys
import time

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b03 import reader, study
from experiments.candidates.uav_fleet_transmission.b03.host import WORLD_IDS, seed
from experiments.candidates.uav_fleet_transmission.b03.surrogate import simulate_continuation
from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state
from experiments.candidates.uav_fleet_transmission.reader import _public_state
from experiments.candidates.uav_fleet_transmission.study import artifact, write_json
from scripts import hmasd_admission


@pytest.fixture
def real_guard_result(monkeypatch, tmp_path):
    """Use the real guard's return mapping after a mocked, effect-free grant."""
    runner = study.REPO / "experiments/candidates/uav_fleet_transmission/b03/run.py"
    argv = [str(runner), "--out", str(tmp_path), "--launch-sha", "a" * 40]
    monkeypatch.setattr(sys, "argv", argv)
    digest = hmasd_admission.command_digest(sys.executable, runner, argv[1:])
    spec = {"schema_version": 1, "direction": study.DIRECTION, "runner": str(runner),
        "python": sys.executable, "source_root": str(study.REPO), "sha": "a" * 40,
        "parent_pid": os.getppid(), "command_sha256": digest,
        "endpoint": ["127.0.0.1", 9], "nonce": "fixture-no-network", "expires_at": time.time() + 30}
    monkeypatch.setattr(hmasd_admission, "_attempted", False)
    monkeypatch.setattr(hmasd_admission, "_load_spec", lambda: spec)
    monkeypatch.setattr(hmasd_admission, "_git_head", lambda root: "a" * 40)
    class GrantedChannel:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def settimeout(self, value): pass
        def makefile(self, *args, **kwargs): return self
        def write(self, value): return len(value)
        def flush(self): pass
        def readline(self, *args):
            return (json.dumps({"kind": "grant", "nonce": spec["nonce"], "pid": os.getpid()}) + "\n").encode()
    monkeypatch.setattr(hmasd_admission.socket, "create_connection", lambda *a, **kw: GrantedChannel())
    result = hmasd_admission.require_admission(runner, direction=study.DIRECTION)
    assert result["command_sha256"] == digest
    assert "operation_id" not in result
    return result


def completed_metadata(out):
    config = dict(study.fixed_config(), launch_sha="a" * 40, admission_command_sha256="f" * 64,
                  versions={"python": "fixture", "numpy": "fixture", "torch": "fixture"})
    write_json(out / "config.json", config)
    write_json(out / "launch-manifest.json", {"acceptance": "accepted", "sha": "a" * 40,
        "direction": study.DIRECTION, "command_sha256": "f" * 64})
    rows = [{"arm": study.ARMS[(i + j) % 3], "world_id": w, "n": 8, "steps": 500,
             "complete": True, "runtime_seed": seed(w, 3, 8)}
            for i, w in enumerate(WORLD_IDS) for j in range(3)]
    return {"worker_status": "complete", "status": "collected", "new_fits": 0, "updates": 0,
            "launch_sha": "a" * 40, "config": config, "config_artifact": artifact(out / "config.json", out),
            "episodes": rows}


def test_refuses_incomplete_or_failed_worker_before_replay(tmp_path):
    for status in ("worker", "failed"):
        with pytest.raises(ValueError, match="not completed"):
            reader.validate_worker({"worker_status": "complete", "status": status}, tmp_path)
    with pytest.raises(ValueError, match="not completed"):
        reader.validate_worker({"worker_status": "incomplete", "status": "collected"}, tmp_path)


def test_source_panel_counts_and_config_cross_binding(tmp_path):
    summary = completed_metadata(tmp_path)
    assert tuple(reader.validate_worker(summary, tmp_path)) == WORLD_IDS
    for change in (lambda s: s["episodes"].pop(), lambda s: s["episodes"].reverse(),
                   lambda s: s["episodes"][0].update(steps=499),
                   lambda s: s["episodes"][0].update(runtime_seed=0),
                   lambda s: s.update(new_fits=1),
                   lambda s: s["config"].update(model_branch_scope="winner only")):
        bad = deepcopy(summary)
        change(bad)
        with pytest.raises(ValueError):
            reader.validate_worker(bad, tmp_path)
    manifest = json.loads((tmp_path / "launch-manifest.json").read_text())
    write_json(tmp_path / "launch-manifest.json", dict(manifest, command_sha256="e" * 64))
    with pytest.raises(ValueError, match="admission differs"):
        reader.validate_worker(summary, tmp_path)
    write_json(tmp_path / "launch-manifest.json", manifest)
    changed_config = deepcopy(summary["config"])
    changed_config["versions"]["numpy"] = "altered"
    write_json(tmp_path / "config.json", changed_config)
    summary["config_artifact"] = artifact(tmp_path / "config.json", tmp_path)
    with pytest.raises(ValueError, match="configuration differs"):
        reader.validate_worker(summary, tmp_path)


def test_full_saved_model_branch_refuses_rehashed_tampering(tmp_path):
    state = _public_state(np.tile([0., 0., 50.], (8, 1)), np.zeros((50, 2)), 40, 500)
    c = OrdinaryController(8)
    c.positions, c.users = decode_public_state(state, 8)
    c.next_t = 40
    result = simulate_continuation(c, state, 255, horizon=41)
    path, trace = tmp_path / "branch.npz", tmp_path / "branch.jsonl.gz"
    with path.open("wb") as stream:
        np.savez_compressed(stream, **result["arrays"])
    study.write_trace(trace, result["decisions"])
    saved = {"id": "stay", "raw": artifact(path, tmp_path), "decisions": artifact(trace, tmp_path),
             "summary": result["summary"]}
    reader.verify_model_branch(tmp_path, saved, "stay", result)
    arrays = deepcopy(result["arrays"])
    arrays["controller_estimates"][0, 0, 0] = 9.
    with path.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    saved["raw"] = artifact(path, tmp_path)
    with pytest.raises(ValueError, match="model branch"):
        reader.verify_model_branch(tmp_path, saved, "stay", result)
    with path.open("wb") as stream:
        np.savez_compressed(stream, **result["arrays"])
    saved["raw"] = artifact(path, tmp_path)
    decisions = deepcopy(result["decisions"])
    decisions[0]["issued_mask"] = 2
    trace.unlink()
    study.write_trace(trace, decisions)
    saved["decisions"] = artifact(trace, tmp_path)
    with pytest.raises(ValueError, match="decision replay"):
        reader.verify_model_branch(tmp_path, saved, "stay", result)
    with pytest.raises(ValueError, match="identity/summary"):
        reader.verify_model_branch(tmp_path, saved, "m7_s0", result)


def test_worker_failure_preserves_completed_cells_and_cannot_be_read(monkeypatch, tmp_path, real_guard_result):
    monkeypatch.setattr(study.torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(study.torch, "set_num_interop_threads", lambda n: None)
    monkeypatch.setattr(study, "bound_worlds", lambda: {w: None for w in WORLD_IDS})
    calls = []
    def fixture_evaluate(arm, scene, horizon, runtime_seed, out):
        calls.append(arm)
        if len(calls) == 2:
            raise RuntimeError("constructed collection failure")
        return {"arm": arm, "world_id": WORLD_IDS[0], "steps": 500, "fixture": True}
    monkeypatch.setattr(study, "evaluate_episode", fixture_evaluate)
    with pytest.raises(RuntimeError, match="constructed collection failure"):
        study.run_study(tmp_path, "a" * 40, real_guard_result)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert calls == ["C", "R"] and len(summary["episodes"]) == 1
    assert summary["worker_status"] == "incomplete"
    assert summary["failure_stage"] == "worker" and summary["status"] == "failed"
    with pytest.raises(ValueError, match="not completed"):
        reader.validate_worker(summary, tmp_path)
    with pytest.raises(FileExistsError, match="existing attempt"):
        study.run_study(tmp_path, "a" * 40, real_guard_result)
