"""B10 production binding checks; no native environment or optimization."""
from dataclasses import replace
import importlib.util

import pytest
import torch

from experiments.candidates.ucope.paired_branch_credit_b10 import study


def test_declared_scope_and_missing_admission_refuse_before_output(tmp_path):
    for config, admission in ((study.Config(8971), {}), (study.Config(8974), {"direction": "ucope"}),
                              (replace(study.Config.engineering(), horizon=9), {})):
        out = tmp_path / str(config)
        with pytest.raises(ValueError):
            study.run(config, out, admission)
        assert not out.exists()
    for master in study.MASTERS:
        study.require_config(study.Config(master))


def test_optimizer_cannot_expose_foundation_or_borrow_another_gates_parameters():
    gate = study.ScalarGate("scalar", 7, 0.0, 1.0)
    other = study.ScalarGate("scalar", 8, 0.0, 1.0)
    good = torch.optim.Adam(gate.parameters(), lr=3e-4)
    study._validate_paired_optimizer(gate, good)
    bad = torch.optim.Adam(other.parameters(), lr=3e-4)
    with pytest.raises(ValueError, match="only its model parameters"):
        study._validate_paired_optimizer(gate, bad)
    assert not good.state and not bad.state  # Construction is zero optimization steps.


def test_reducer_keeps_full_ppo_and_practical_g_as_distinct_references():
    panels = {"R_CF": [0.21, 0.24], "R_FULL": [0.23, 0.24], "S_CF": [0.22, 0.22], "G": [0.22, 0.23]}
    result = study.reduce_panels(panels, 2)
    assert result["complete"] and result["primary"] == "R_CF_minus_R_FULL"
    assert result["R_CF_minus_R_FULL"]["mean"] == pytest.approx(-0.01)
    assert result["R_CF_minus_G"]["mean"] == pytest.approx(0.0)
    assert result["R_CF_minus_S_CF"]["mean"] == pytest.approx(0.005)
    partial = study.reduce_panels({**panels, "S_CF": [0.22]}, 2)
    assert not partial["complete"] and "R_CF_minus_G" not in partial


def test_runner_admission_and_sha_refuse_before_science(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("b10_runner", study.REPO / "scripts/run_ucope_paired_branch_credit_b10.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    calls = []
    monkeypatch.setattr(torch, "set_num_threads", lambda n: calls.append(n))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: calls.append(n))
    out = tmp_path / "not-created"
    args = ["--master", "8971", "--out", str(out), "--launch-sha", "expected"]

    def refuse(*args, **kwargs):
        raise RuntimeError("admission refused")

    monkeypatch.setattr(runner, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="admission refused"):
        runner.main(args)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "different"})
    with pytest.raises(SystemExit):
        runner.main(args)
    with pytest.raises(SystemExit):
        runner.main(args + ["--fixture"])
    assert not out.exists() and calls == []
