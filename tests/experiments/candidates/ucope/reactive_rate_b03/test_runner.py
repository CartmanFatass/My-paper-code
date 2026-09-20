"""Admission ordering and fixed B03 CLI checks without scientific execution."""

import importlib.util
from pathlib import Path

import pytest
import torch


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / "scripts/run_ucope_reactive_rate_b03.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def argv(out, master=8921, launch_sha=None):
    result = ["--master", str(master), "--out", str(out)]
    if launch_sha is not None:
        result.extend(("--launch-sha", launch_sha))
    return result


def test_admission_refusal_precedes_output_threads_and_workload_import(tmp_path, monkeypatch):
    _, runner = load_runner("ucope_b03_refusal")
    out = tmp_path / "unused"
    thread_calls = []
    monkeypatch.setattr(torch, "set_num_threads", lambda value: thread_calls.append(value))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda value: thread_calls.append(value))
    monkeypatch.setattr(
        runner,
        "require_admission",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("refused")),
    )
    with pytest.raises(RuntimeError, match="refused"):
        runner.main(argv(out))
    assert not out.exists()
    assert thread_calls == []


@pytest.mark.parametrize("bad_args", [["--master", "8920"], ["--master", "8921", "--fixture"]])
def test_unselected_scope_refuses_before_spending_admission(tmp_path, monkeypatch, bad_args):
    _, runner = load_runner("ucope_b03_bad_scope_" + str(len(bad_args)))
    calls = []
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_k: calls.append(True))
    with pytest.raises(SystemExit):
        runner.main([*bad_args, "--out", str(tmp_path / "unused")])
    assert calls == []
    assert not (tmp_path / "unused").exists()


def test_optional_launch_sha_must_match_before_workload(tmp_path, monkeypatch):
    _, runner = load_runner("ucope_b03_sha_mismatch")
    out = tmp_path / "unused"
    monkeypatch.setattr(
        runner,
        "require_admission",
        lambda *_a, **_k: {"sha": "admitted", "command_sha256": "digest", "child_pid": 42},
    )
    with pytest.raises(SystemExit):
        runner.main(argv(out, launch_sha="other"))
    assert not out.exists()


def test_admitted_runner_passes_exact_config_and_admission(tmp_path, monkeypatch):
    _, runner = load_runner("ucope_b03_accepted")
    from experiments.candidates.ucope.reactive_rate_b03 import study

    calls = []

    def fake_run(config, out, admission, start=None):
        calls.append((config, out, admission, start))
        return {"status": "COMPLETE", "counts": {"team_steps": 1, "optimizer_steps": 2}}

    admitted = {"sha": "admitted", "command_sha256": "digest", "child_pid": 42}
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_k: admitted)
    monkeypatch.setattr(study, "run", fake_run)
    monkeypatch.setattr(torch, "set_num_threads", lambda _value: None)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _value: None)
    out = tmp_path / "synthetic"
    assert runner.main(argv(out, master=8922, launch_sha="admitted")) == 0
    config, observed_out, observed_admission, start = calls.pop()
    assert observed_out == out and observed_admission == admitted
    assert isinstance(start, float)
    assert config == study.Config(seed=8922)
