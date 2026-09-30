"""Reader checks on the DM's synthetic saved-evidence fixture only."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import Student
from experiments.candidates.uav_fleet_adaptation.b04_native_development import read
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import source_identities
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic


# Reuse the integrated fixture and its paid synthetic support, rather than build
# another fake scientific contract or use a native/canonical asset.
spec = importlib.util.spec_from_file_location("fleet_b04_reader_fixture", Path(__file__).with_name("test_study.py"))
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
study = fixture_module.study


@pytest.fixture
def copied(study, tmp_path):
    out, result, bindings = study
    target = tmp_path / "result"
    shutil.copytree(out, target)
    return target, copy.deepcopy(result)


def publish(out, batch):
    (out / "summary.json").write_text(json.dumps(batch, allow_nan=False))


def rewrite_raw(out, row, mutator):
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    mutator(arrays)
    np.savez_compressed(path, **arrays)
    record = file_identity(path)
    record["path"] = row["raw"]["path"]
    row["raw"] = record


def test_complete_reader_scope_identity_and_forward_budget(study, monkeypatch):
    out, batch, bindings = study
    calls = []
    original = Student.forward
    def observed(self, features):
        calls.append(tuple(features.shape))
        return original(self, features)
    monkeypatch.setattr(Student, "forward", observed)
    def forbidden(*args, **kwargs):
        raise AssertionError("reader attempted a critic forward")
    monkeypatch.setattr(Critic, "forward", forbidden)
    result = read.read_result(out, read.ROOT, allow_fixture=True)
    assert result["status"] == "VERIFIED" and result["scientific_execution"] is False
    assert result["raw_files"] == batch["actual"]["complete_episodes"]
    assert result["raw_bytes"] == sum(row["raw"]["bytes"] for row in batch["rows"])
    work = result["reader_calls"]
    expected_eval = sum(10 for row in batch["rows"] if row["kind"] == "evaluation" and row["candidate"].startswith("S_"))
    assert work["evaluation_actor_rows"] == expected_eval
    assert work["shadow_actor_rows"] == 40 and work["shadow_motion_ticks"] == 160
    assert len(calls) == work["actor_forward_rows"] == expected_eval + 40
    assert set(calls) == {(1, 114)}
    assert work["native_team_ticks_verified"] == batch["actual"]["native_steps"]
    assert work["native_agent_motion_ticks_verified"] == 5 * batch["actual"]["native_steps"]
    assert all(work[key] == 0 for key in ("native", "radio_power_model", "expert_queries", "training_actor_rows",
                                         "calibration_actor_rows", "critic_forward_rows", "optimizer"))
    assert result["calibrations"] == batch["calibrations"]
    assert result["comparisons"] == batch["comparisons"] and result["costs"] == batch["costs"]
    assert result["sources"] == source_identities(read.ROOT)
    assert not (out / "reading.json").exists()  # Library reader has no publication effect.


@pytest.mark.parametrize("case", ["incomplete", "object", "source", "count", "order", "winner", "reuse", "comparison", "initial_asset", "final_asset"])
def test_summary_and_artifact_tamper_rejected(copied, case):
    out, batch = copied
    if case == "incomplete":
        batch["state"] = "INCOMPLETE"
    elif case == "object":
        batch["object"] = "different"
    elif case == "source":
        batch["sources"][next(iter(batch["sources"]))] = "0" * 64
    elif case == "count":
        batch["actual"]["actor_replay_rows"] += 1
    elif case == "order":
        batch["rows"][0], batch["rows"][1] = batch["rows"][1], batch["rows"][0]
    elif case == "winner":
        batch["calibrations"][0]["winner"] = "C_0" if batch["calibrations"][0]["winner"] != "C_0" else "S_greedy"
    elif case == "reuse":
        batch["evaluations"][0]["reused"] = not batch["evaluations"][0]["reused"]
    elif case == "comparison":
        batch["comparisons"]["lineages"][0]["paired"]["R-S"]["J"]["mean"] += .001
    elif case == "initial_asset":
        batch["initial_assets"][0]["sha256"] = "0" * 64
    else:
        path = out / batch["final_assets"][0]["path"]
        path.write_bytes(path.read_bytes() + b"changed")
    publish(out, batch)
    with pytest.raises((AssertionError, ValueError)):
        read.read_result(out, read.ROOT, allow_fixture=True)


@pytest.mark.parametrize("case", ["hold", "motion", "features", "nav", "probability", "uniform", "macro", "critic", "shadow", "reset"])
def test_rehashed_raw_tamper_rejected(copied, case):
    out, batch = copied
    row = next(row for row in batch["rows"] if row["kind"] == ("evaluation" if case == "shadow" else "training") and row["arm"] == "R")
    def corrupt(raw):
        if case == "hold":
            raw["commands"][1, 0, 0] *= -1
            raw["commands"][1, 0, 0] += .5
        elif case == "motion":
            raw["positions"][1, 0, 0] += .1
        elif case == "features":
            raw["features"][0, 0, 3] += .01
        elif case == "nav":
            raw["nav_next"][0, 0] = (raw["nav_next"][0, 0] + 1) % 10
        elif case == "probability":
            raw["probabilities"][0, 0, 0] += 1e-10
        elif case == "uniform":
            raw["innovation"][0, 0] = np.nextafter(raw["innovation"][0, 0], 1.)
        elif case == "macro":
            raw["macro_rewards"][0] += .1
        elif case == "critic":
            raw["critic_features"][0, -1] = 1
        elif case == "shadow":
            raw["shadow_positions"][0, 1, 0, 0] += .1
        else:
            raw["initial_users"][0, 0] += .1
    rewrite_raw(out, row, corrupt)
    publish(out, batch)
    with pytest.raises(AssertionError):
        read.read_result(out, read.ROOT, allow_fixture=True)


def test_update_diagnostics_and_adam_tamper_with_rehashed_checkpoint(copied):
    out, batch = copied
    path = out / batch["final_assets"][0]["path"]
    payload = torch.load(path, weights_only=True)
    next(iter(payload["actor_optimizer"]["state"].values()))["step"] += 1
    torch.save(payload, path)
    record = file_identity(path)
    batch["final_assets"][0].update(sha256=record["sha256"], bytes=record["bytes"])
    publish(out, batch)
    with pytest.raises(AssertionError, match="Adam step"):
        read.read_result(out, read.ROOT, allow_fixture=True)


@pytest.mark.parametrize("case", ["target", "identity", "gradient", "completion", "epoch_step", "first_loss"])
def test_consistently_rehashed_group_diagnostics_rejected(copied, case):
    out, batch = copied
    group = batch["updates"][0]["groups"][0]
    if case == "target":
        group["target_summary"]["mean"] += .01
    elif case == "identity":
        group["initial_identity"]["max_probability_abs"] = 1e-12
    elif case == "gradient":
        group["epochs"][0]["actor_clipped_grad_norm"] = .6
    elif case == "completion":
        group["epochs"][0]["critic_step_completed"] = False
    elif case == "epoch_step":
        group["epochs"][0]["actor_optimizer_step_values"][0] += 1
    else:
        group["epochs"][0]["actor_loss"] += .01
    path = out / batch["final_assets"][0]["path"]
    payload = torch.load(path, weights_only=True)
    payload["groups"] = batch["updates"][0]["groups"]
    torch.save(payload, path)
    record = file_identity(path)
    batch["final_assets"][0].update(sha256=record["sha256"], bytes=record["bytes"])
    publish(out, batch)
    with pytest.raises(AssertionError):
        read.read_result(out, read.ROOT, allow_fixture=True)


def test_unreferenced_raw_and_path_escape_rejected(copied):
    out, batch = copied
    (out / "raw" / "unreferenced.npz").write_bytes((out / batch["rows"][0]["raw"]["path"]).read_bytes())
    with pytest.raises(AssertionError, match="unreferenced"):
        read.read_result(out, read.ROOT, allow_fixture=True)
    (out / "raw" / "unreferenced.npz").unlink()
    batch["rows"][0]["raw"]["path"] = "../outside.npz"
    publish(out, batch)
    with pytest.raises(AssertionError, match="escapes"):
        read.read_result(out, read.ROOT, allow_fixture=True)


def test_production_cli_and_fixture_flags_cannot_read_fixture(copied):
    out, batch = copied
    completed = subprocess.run([sys.executable, str(Path(read.__file__)), "--out", str(out)], capture_output=True, text=True)
    assert completed.returncode != 0 and "frozen scientific" in completed.stderr
    assert json.loads((out / "reading.json").read_text())["status"] == "FAILED"
    with pytest.raises(FileExistsError):
        read.read_result(out, read.ROOT)


def test_production_read_claim_is_exclusive_and_preserves_failure_work(tmp_path, monkeypatch):
    calls = []
    def successful(out, repo, *, allow_fixture, work, start_wall, start_cpu):
        calls.append(1)
        assert json.loads((out / "reading.json").read_text())["status"] == "INCOMPLETE"
        return dict(status="VERIFIED", reader_calls=dict(work))
    monkeypatch.setattr(read, "_read_result", successful)
    out = tmp_path / "successful"
    out.mkdir()
    assert read.read_result(out, read.ROOT)["status"] == "VERIFIED"
    prior = (out / "reading.json").read_bytes()
    with pytest.raises(FileExistsError):
        read.read_result(out, read.ROOT)
    assert calls == [1] and (out / "reading.json").read_bytes() == prior

    def failed(out, repo, *, allow_fixture, work, start_wall, start_cpu):
        work["actor_forward_rows"] = 3
        work["evaluation_actor_rows"] = 3
        raise AssertionError("synthetic verifier failure")
    monkeypatch.setattr(read, "_read_result", failed)
    failure_out = tmp_path / "failed"
    failure_out.mkdir()
    with pytest.raises(AssertionError) as caught:
        read.read_result(failure_out, read.ROOT)
    record = json.loads((failure_out / "reading.json").read_text())
    assert record == caught.value.reader_work and record["status"] == "FAILED"
    assert record["reader_calls"]["actor_forward_rows"] == 3
    with pytest.raises(FileExistsError):
        read.read_result(failure_out, read.ROOT)
