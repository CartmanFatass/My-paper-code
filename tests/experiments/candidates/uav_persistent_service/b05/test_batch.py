"""No launch: runner admission order and explicit constructor-failure evidence."""

import json

import pytest

from experiments.candidates.uav_persistent_service.b05 import batch, run_b05


def test_missing_admission_precedes_scientific_effects(monkeypatch, tmp_path):
    from scripts import hmasd_admission

    def refused(*args, **kwargs):
        raise RuntimeError("admission refused")
    monkeypatch.setattr(hmasd_admission, "require_admission", refused)
    with pytest.raises(RuntimeError, match="admission refused"):
        run_b05.main(["--out", str(tmp_path/"new"), "--launch-sha", "unpublished"])
    assert not (tmp_path/"new").exists()


def test_constructor_failure_is_explicit_and_not_retried(monkeypatch, tmp_path):
    calls = []
    def refused(seed):
        calls.append(seed)
        raise ValueError("fixture construction failure")
    monkeypatch.setattr(batch, "ServiceShiftEpisode", refused)
    (tmp_path/"raw").mkdir()
    job = batch.plan()[0]
    result = batch.worker((job, str(tmp_path)))
    assert result["status"] == "failed"
    assert result["episode_constructed"] is False
    assert result["partial_observed_steps"] == 0
    assert calls == [job["seed"]]
    progress = json.loads((tmp_path/"raw"/f"S_{job['seed']}.progress.json").read_text())
    assert progress["status"] == "failed" and progress["steps"] == 0
