"""B03 admission, fixed assignments and retained output checks without result fits."""

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
from scripts import run_stdl_joint_response_b03 as runner


SHA = "3" * 40
STUDY = "experiments.candidates.skill_teammate_drift_learning.joint_response_b03.study"


def argv(out, arm="joint_response", seed="93001", sha=SHA):
    return ["--arm", arm, "--seed", seed, "--launch-sha", sha, "--out", str(out)]


def fake_study(monkeypatch, fit=None):
    @dataclass(frozen=True)
    class Config:
        source_macros: int = 2048
        target_macros: int = 256
        skill_ticks: int = 3
        recent_window: int = 64
        prior_strength: float = 2.0

    module = ModuleType(STUDY)
    module.Config = Config
    module.run_fit = fit or (
        lambda cfg, *, arm, seed, object_name: {
            "summary": {"fixture_only": True, "object": object_name, "arm": arm, "seed": seed},
            "curves": {"macro": [0, 1], "predictions": [[.5, .5], [.6, .4]]},
            "transitions": {"outcomes": np.array([[0, 1], [1, 1]], dtype=np.int64)},
            "learner_state": {"counts": np.array([[1, 0, 0, 0], [0, 1, 1, 3]])},
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
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "4" * 40})
    with pytest.raises(SystemExit):
        runner.main(argv(out))
    assert not out.exists()


@pytest.mark.parametrize("arm,seed,sha", [
    ("other", "93001", SHA), ("joint_response", "92001", SHA),
    ("joint_response", "93004", SHA), ("joint_response", "93001", "short"),
])
def test_unplanned_inputs_refuse_before_admission(tmp_path, monkeypatch, arm, seed, sha):
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: called.append(True))
    with pytest.raises(SystemExit):
        runner.main(argv(tmp_path / "invalid", arm=arm, seed=seed, sha=sha))
    assert not called


@pytest.mark.parametrize("arm", runner.ARMS)
def test_exact_arm_assignment_retention_and_no_overwrite(tmp_path, monkeypatch, arm):
    out = tmp_path / arm
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch)
    assert runner.main(argv(out, arm=arm)) == 0
    summary = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    assert summary["status"] == "complete"
    assert summary["started_fits"] == 1
    assert summary["arm"] == config["arm"] == summary["learning"]["arm"] == arm
    assert summary["object"] == summary["learning"]["object"] == runner.OBJECT
    assert summary["launch_sha"] == config["launch_sha"] == SHA
    assert config["config"] == {
        "source_macros": 2048, "target_macros": 256, "skill_ticks": 3,
        "recent_window": 64, "prior_strength": 2.0,
    }
    assert set(config["numeric_thread_environment"].values()) == {"1"}
    with np.load(out / "transitions.npz", allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays["outcomes"], [[0, 1], [1, 1]])
    with np.load(out / "learner_state.npz", allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays["counts"], [[1, 0, 0, 0], [0, 1, 1, 3]])
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


@pytest.mark.parametrize("bad", [np.array([object()]), np.array([np.nan]), np.array(["x"])])
def test_nonnumeric_or_nonfinite_arrays_refuse_publication(tmp_path, bad):
    path = tmp_path / "bad.npz"
    with pytest.raises(ValueError):
        runner.write_arrays(path, {"bad": bad}, np)
    assert not path.exists()
