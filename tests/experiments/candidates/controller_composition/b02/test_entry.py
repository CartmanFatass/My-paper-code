from pathlib import Path

import pytest

from scripts import run_controller_composition_b02 as entry


def test_admission_precedes_runner_and_rejects_wrong_sha(tmp_path, monkeypatch):
    called = []
    def admission(*args, **kwargs):
        called.append("admission")
        return {"sha": "admitted"}
    monkeypatch.setattr(entry, "require_admission", admission)
    argv = ["--seed", "92526001", "--launch-sha", "wrong", "--out", str(tmp_path / "unmade"),
            "--checkpoints", "a", "b", "c"]
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main(argv, run_fn=lambda *a, **k: called.append("runner"))
    assert called == ["admission"]
    assert not (tmp_path / "unmade").exists()
    argv[3] = "admitted"
    def run_fn(out, sha, receipt, paths, **kwargs):
        called.append("runner")
        assert out == (tmp_path / "unmade").resolve()
        assert sha == receipt["sha"] == "admitted"
        assert list(paths) == [1, 2, 3]
        return "accepted"
    assert entry.main(argv, run_fn=run_fn) == "accepted"
    assert called == ["admission", "admission", "runner"]
