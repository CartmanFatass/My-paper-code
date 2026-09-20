"""Admission ordering and fixed B06 CLI checks without scientific execution."""

import importlib.util
from pathlib import Path

import pytest
import torch


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / "scripts/run_ucope_gaussian_scale_initialization_b06.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def argv(out, master=8941, launch_sha="admitted"):
    return ["--master", str(master), "--out", str(out), "--launch-sha", launch_sha]


def test_admission_refusal_precedes_output_threads_and_scientific_import(tmp_path, monkeypatch):
    runner = load_runner("ucope_b06_refusal")
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
    assert not out.exists() and thread_calls == []


@pytest.mark.parametrize("bad_args", [
    ["--master", "8940"],
    ["--master", "8941", "--fixture"],
    ["--master", "8941"],
])
def test_unselected_extra_or_unbound_scope_refuses_before_admission(tmp_path, monkeypatch, bad_args):
    runner = load_runner("ucope_b06_bad_scope_" + str(len(bad_args)))
    calls = []
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_k: calls.append(True))
    with pytest.raises(SystemExit):
        runner.main([*bad_args, "--out", str(tmp_path / "unused")])
    assert calls == []
    assert not (tmp_path / "unused").exists()


def test_launch_sha_mismatch_precedes_threads_output_and_workload(tmp_path, monkeypatch):
    runner = load_runner("ucope_b06_sha_mismatch")
    out = tmp_path / "unused"
    thread_calls = []
    monkeypatch.setattr(torch, "set_num_threads", lambda value: thread_calls.append(value))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda value: thread_calls.append(value))
    monkeypatch.setattr(
        runner,
        "require_admission",
        lambda *_a, **_k: {"sha": "admitted", "command_sha256": "digest", "child_pid": 42},
    )
    with pytest.raises(SystemExit):
        runner.main(argv(out, launch_sha="other"))
    assert not out.exists() and thread_calls == []


def test_admitted_runner_passes_only_fixed_config_and_original_admission(tmp_path, monkeypatch):
    runner = load_runner("ucope_b06_accepted")
    from experiments.candidates.ucope.gaussian_scale_initialization_b06 import study

    calls = []

    def fake_run(config, out, admission, start=None):
        calls.append((config, out, admission, start))
        return {
            "status": "COMPLETE",
            "fit_accounting": {"started_fits": 2},
            "counts": {"optimizer_steps": 4096},
        }

    admitted = {"sha": "admitted", "command_sha256": "digest", "child_pid": 42}
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_k: admitted)
    monkeypatch.setattr(study, "run", fake_run)
    monkeypatch.setattr(torch, "set_num_threads", lambda _value: None)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _value: None)
    out = tmp_path / "synthetic"
    assert runner.main(argv(out, master=8942)) == 0
    config, observed_out, observed_admission, start = calls.pop()
    assert config == study.Config(master=8942)
    assert observed_out == out and observed_admission == admitted
    assert isinstance(start, float)
