"""B02's frozen initialization assignments, admission and retained output contract."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import numpy as np
import pytest

from scripts import hmasd_launch
from scripts import run_stdl_joint_replay_b02 as runner


SHA = "2" * 40
STUDY = "experiments.candidates.skill_teammate_drift_learning.joint_replay_b01.study"


def argv(out, arm="joint_is", seed="92001", sha=SHA):
    return ["--arm", arm, "--seed", seed, "--launch-sha", sha, "--out", str(out)]


def fake_study(monkeypatch, fit=None):
    @dataclass(frozen=True)
    class Config:
        initialization: str
        version_names: tuple = ("A", "B")
        primary_evaluation_episodes: tuple = (70, 130)

    module = ModuleType(STUDY)
    module.Config = Config
    module.run_fit = fit or (
        lambda cfg, *, arm, seed, object_name: {
            "summary": {"fixture_only": True, "object": object_name, "arm": arm},
            "curves": {
                "evaluation_episode": [0, 70, 130],
                "version_index": [0, 1, 0],
                "normalized_service_return": [0.0, 0.2, 0.4],
            },
            "transitions": {"positions": np.array([[0, 4], [1, 4]], dtype=np.int64)},
            "q_values": np.array([0.0, 1.0], dtype=np.float64),
        }
    )
    monkeypatch.setitem(sys.modules, STUDY, module)


def test_native_static_contract_and_missing_admission_refusal(tmp_path):
    hmasd_launch._validate_guard_contract(Path(runner.__file__), runner.DIRECTION)
    out = tmp_path / "not-admitted"
    environment = dict(os.environ)
    environment.pop("HMASD_ADMISSION_V1", None)
    completed = subprocess.run(
        [sys.executable, str(Path(runner.__file__).resolve()), *argv(out)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert completed.returncode != 0
    assert "missing HMASD admission" in completed.stderr
    assert not out.exists()


def test_admission_and_sha_refusal_before_science_or_output(tmp_path, monkeypatch):
    out = tmp_path / "refused"

    def refuse(*args, **kwargs):
        assert kwargs["direction"] == runner.DIRECTION
        raise PermissionError("fixture admission refusal")

    monkeypatch.setattr(runner, "require_admission", refuse)
    with pytest.raises(PermissionError):
        runner.main(argv(out))
    assert not out.exists()
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "3" * 40})
    with pytest.raises(SystemExit):
        runner.main(argv(out))
    assert not out.exists()


@pytest.mark.parametrize("arm,seed", [("other", "92001"), ("joint_is", "91001"), ("joint_is", "92004")])
def test_unplanned_arm_or_seed_refuses_before_admission(tmp_path, monkeypatch, arm, seed):
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: called.append(True))
    with pytest.raises(SystemExit):
        runner.main(argv(tmp_path / "invalid", arm=arm, seed=seed))
    assert not called


@pytest.mark.parametrize("arm", runner.ARMS)
def test_exact_arm_assignment_output_identity_and_retention(tmp_path, monkeypatch, arm):
    out = tmp_path / arm
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch)
    assert runner.main(argv(out, arm=arm)) == 0
    summary = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    replay_arm = "fingerprint" if arm == "fingerprint_zero" else arm
    initialization = "zero" if arm == "fingerprint_zero" else "reward_upper"
    assert summary["status"] == "complete"
    assert summary["started_fits"] == 1
    assert summary["arm"] == config["arm"] == arm
    assert summary["replay_arm"] == config["replay_arm"] == replay_arm
    assert summary["initialization"] == config["config"]["initialization"] == initialization
    assert summary["object"] == summary["learning"]["object"] == runner.OBJECT
    assert summary["learning"]["arm"] == replay_arm
    assert summary["launch_sha"] == config["launch_sha"] == SHA
    assert summary["version_adaptation_endpoints"]["A"]["episodes"] == [130]
    assert summary["version_adaptation_endpoints"]["B"]["mean_normalized_service_return"] == 0.2
    with np.load(out / "transitions.npz", allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays["positions"], [[0, 4], [1, 4]])
    assert np.load(out / "q_values.npy", allow_pickle=False).tolist() == [0.0, 1.0]
    assert not list(out.glob("*.tmp"))
    before = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.main(argv(out, arm=arm))
    assert (out / "summary.json").read_bytes() == before


def test_fit_failure_is_retained_without_score(tmp_path, monkeypatch):
    out = tmp_path / "failed"

    def fail(*args, **kwargs):
        raise ArithmeticError("fixture failure")

    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch, fail)
    with pytest.raises(ArithmeticError, match="fixture failure"):
        runner.main(argv(out))
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "technical_failure"
    assert summary["started_fits"] == 1
    assert "learning" not in summary
    assert (out / "config.json").is_file()
