"""Caught ordinary exceptions retain a traceback without changing stop/count behavior."""
from types import SimpleNamespace
import time

from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study


def test_caught_exception_retains_traceback(monkeypatch, tmp_path, capsys):
    authority = SimpleNamespace(root_digest="supplied", certificate={"native": {}})
    monkeypatch.setattr(study, "make_rng", lambda seed: (authority, object()))

    def supplied_failure(rng, count):
        return iter(range(2)) * 3

    monkeypatch.setattr(study.host, "evaluate_scripted", supplied_failure)
    result = study.run("reference", tmp_path, "supplied-source", tmp_path / "no-admission",
                       time.perf_counter(), 30, seed=22, updates=1000)
    stderr = capsys.readouterr().err
    assert "Traceback (most recent call last):" in stderr
    assert "test_exception_diagnostics.py" in stderr and "supplied_failure" in stderr
    assert result["stop_reason"] == "TypeError: unsupported operand type(s) for *: 'range_iterator' and 'int'"
    assert result["stop_reason"] in stderr and result["status"] == "TECHNICAL_STOP"
    assert all(value == 0 for value in result["counts"].values())
    assert result["scenarios"] == [] and result["curves"] == []
