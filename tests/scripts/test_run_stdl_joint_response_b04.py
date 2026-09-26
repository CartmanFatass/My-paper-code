"""B04 fixed mapping, native admission and output handling without result fits."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from scripts import hmasd_launch
from scripts import run_stdl_joint_response_b04 as runner


SHA = "4" * 40
STUDY = "experiments.candidates.skill_teammate_drift_learning.joint_response_b03.study"


def argv(out, arm="joint_product", seed="94001", sha=SHA):
    return ["--arm", arm, "--seed", seed, "--launch-sha", sha, "--out", str(out)]


def fake_study(monkeypatch, fit=None):
    @dataclass(frozen=True)
    class Config:
        source_schedule: str
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
    monkeypatch.setattr(runner, "support_diagnostics", lambda *a: {"fixture_only": True})


def test_native_guard_and_missing_admission_refuse(tmp_path):
    hmasd_launch._validate_guard_contract(Path(runner.__file__), runner.DIRECTION)
    out = tmp_path / "not-admitted"
    env = dict(os.environ)
    env.pop("HMASD_ADMISSION_V1", None)
    result = subprocess.run(
        [sys.executable, str(Path(runner.__file__).resolve()), *argv(out)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()


def test_sha_and_unplanned_inputs_refuse_before_outputs(tmp_path, monkeypatch):
    out = tmp_path / "refused"
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "5" * 40})
    with pytest.raises(SystemExit):
        runner.main(argv(out))
    assert not out.exists()
    called = []
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: called.append(True))
    for arm, seed, sha in (("other","94001",SHA),("joint_product","93001",SHA),("joint_product","94004",SHA),("joint_product","94001","short")):
        with pytest.raises(SystemExit):
            runner.main(argv(out,arm,seed,sha))
    assert not called


@pytest.mark.parametrize("arm", tuple(runner.ARM_CONFIG))
def test_frozen_assignment_and_retained_outputs(tmp_path, monkeypatch, arm):
    out = tmp_path / arm
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    fake_study(monkeypatch)
    assert runner.main(argv(out,arm)) == 0
    summary = json.loads((out/"summary.json").read_text())
    config = json.loads((out/"config.json").read_text())
    learner, schedule = runner.ARM_CONFIG[arm]
    assert summary["arm"] == config["arm"] == arm
    assert summary["learner_arm"] == summary["learning"]["arm"] == learner
    assert summary["source_schedule"] == config["config"]["source_schedule"] == schedule
    assert config["config"]["source_macros"] == 2048
    assert config["config"]["target_macros"] == 256
    assert config["config"]["skill_ticks"] == 3
    assert summary["object"] == summary["learning"]["object"] == runner.OBJECT
    assert summary["status"] == "complete" and summary["started_fits"] == 1
    assert summary["launch_sha"] == SHA
    assert set(config["numeric_thread_environment"].values()) == {"1"}
    with np.load(out/"transitions.npz",allow_pickle=False) as z:
        np.testing.assert_array_equal(z["outcomes"],[[0,1],[1,1]])
    before = (out/"summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.main(argv(out,arm))
    assert (out/"summary.json").read_bytes() == before


def test_failure_is_retained_as_technical(tmp_path, monkeypatch):
    def fail(*a, **k):
        raise ArithmeticError("fixture failure")
    out = tmp_path/"failed"
    fake_study(monkeypatch,fail)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": SHA})
    with pytest.raises(ArithmeticError):
        runner.main(argv(out))
    s = json.loads((out/"summary.json").read_text())
    assert s["status"] == "technical_failure" and s["started_fits"] == 1
    assert "learning" not in s


def test_source_diagnostics_are_descriptive_and_use_one_svd(monkeypatch):
    config = SimpleNamespace(source_macros=4)
    result = {
        "transitions": {
            "collection_skill": np.ones(5,dtype=int),
            "u": np.array([.2,.2,.8,.8,.87]),
            "v": np.array([.2,.8,.2,.8,.89]),
        },
        "curves": {
            "raw_predictions": [[.5,.5]]*5,
            "true_values": [[.6,.7]]*5,
            "greedy_action": [0]*5,
            "value_mae": [.15]*5,
        },
    }
    calls=[]
    original=np.linalg.svd
    def counted(*a,**k):
        calls.append(True)
        return original(*a,**k)
    monkeypatch.setattr(np.linalg,"svd",counted)
    d=runner.support_diagnostics(result,config,np)
    assert len(calls)==d["source_design_svd_calls"]==1
    assert d["saturated_source_rank"]==4
    np.testing.assert_allclose(d["saturated_source_singular_values"],[1,.6,.6,.36])
    assert d["first_target_raw_predictions"]==[.5,.5]
    assert d["cooperative_source_rows"]==4
    result["transitions"]["collection_skill"][:4] = 0
    empty = runner.support_diagnostics(result,config,np)
    assert empty["saturated_source_rank"] == 0
    assert empty["saturated_source_singular_values"] == []
    assert empty["cooperative_source_rows"] == 0
