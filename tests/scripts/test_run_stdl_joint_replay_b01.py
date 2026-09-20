"""Admission and retained-output checks; no scientific training is run here."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import numpy as np
import pytest

from scripts import run_stdl_joint_replay_b01 as runner
from scripts import hmasd_launch


SHA = "1" * 40
STUDY = "experiments.candidates.skill_teammate_drift_learning.joint_replay_b01.study"


def argv(out, sha=SHA):
    return ["--arm", "joint_is", "--seed", "91001", "--launch-sha", sha, "--out", str(out)]


def fake_study(monkeypatch, run_fit=None):
    @dataclass(frozen=True)
    class Config:
        engineering_fixture: bool = True
        version_order: tuple = (0, 1)

    module = ModuleType(STUDY)
    module.Config = Config
    module.run_fit = run_fit or (
        lambda cfg, *, arm, seed: {
            "summary": {"fixture_only": True},
            "curves": [{"fixture_only": True}],
            "transitions": {"positions": np.array([[0, 4], [1, 4]], dtype=np.int64)},
            "q_values": np.array([0.0, 1.0], dtype=np.float64),
        }
    )
    monkeypatch.setitem(sys.modules, STUDY, module)


def test_admission_refusal_precedes_science_and_output(tmp_path, monkeypatch):
    out = tmp_path / "refused"

    def refuse(*args, **kwargs):
        assert kwargs["direction"] == "skill_teammate_drift_learning"
        raise PermissionError("fixture admission refusal")

    monkeypatch.setattr(runner, "require_admission", refuse)
    with pytest.raises(PermissionError, match="admission refusal"):
        runner.main(argv(out))
    assert not out.exists()


def test_runner_satisfies_native_static_admission_contract():
    hmasd_launch._validate_guard_contract(Path(runner.__file__), runner.DIRECTION)


def test_real_cli_refuses_missing_admission_without_creating_output(tmp_path):
    out = tmp_path / "not-admitted"
    environment = dict(os.environ)
    environment.pop("HMASD_ADMISSION_V1", None)
    result = subprocess.run(
        [sys.executable, str(Path(runner.__file__).resolve()), *argv(out)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()


def test_sha_mismatch_precedes_output(tmp_path, monkeypatch):
    out = tmp_path / "wrong-sha"
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "2" * 40})
    with pytest.raises(SystemExit):
        runner.main(argv(out))
    assert not out.exists()


def test_frozen_cli_rejects_unplanned_seed_before_admission(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: called.append(True))
    args = argv(tmp_path / "invalid")
    args[3] = "91004"
    with pytest.raises(SystemExit):
        runner.main(args)
    assert not called


def test_publication_retains_nonpickle_arrays_and_identity(tmp_path, monkeypatch):
    out = tmp_path / "retained"
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch)
    assert runner.main(argv(out)) == 0
    summary = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    assert summary["status"] == "complete"
    assert summary["launch_sha"] == config["launch_sha"] == SHA
    assert summary["started_fits"] == 1
    assert summary["learning"] == {"fixture_only": True}
    assert config["config"] == {"engineering_fixture": True, "version_order": [0, 1]}
    with np.load(out / "transitions.npz", allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays["positions"], [[0, 4], [1, 4]])
    assert np.load(out / "q_values.npy", allow_pickle=False).tolist() == [0.0, 1.0]
    assert not list(out.glob("*.tmp"))
    # The scientific outputs cannot be reused even with a mocked fresh admission.
    before = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.main(argv(out))
    assert (out / "summary.json").read_bytes() == before


def test_fit_error_retains_technical_failure_without_score(tmp_path, monkeypatch):
    out = tmp_path / "failed"

    def fail(*args, **kwargs):
        raise ArithmeticError("fixture failure")

    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch, fail)
    with pytest.raises(ArithmeticError, match="fixture failure"):
        runner.main(argv(out))
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "technical_failure"
    assert summary["error_type"] == "ArithmeticError"
    assert summary["started_fits"] == 1
    assert "learning" not in summary
    assert (out / "config.json").is_file()
