"""Counter-only hot progress and complete atomic JSON replacement."""

import json

import pytest

from experiments.candidates.uav_service_auxiliary.b09.persistence import append_progress, write_summary


def test_progress_excludes_growing_payload_and_summary_replaces_atomically(tmp_path, monkeypatch):
    large = {"worlds": [{"seed": n} for n in range(1000)]}
    summary = tmp_path / "summary.json"
    write_summary(summary, {"status": "INCOMPLETE", "payload": large})
    first = summary.read_bytes()
    assert b"\n " not in first
    append_progress(tmp_path, {"event": "collection", "phase": 1, "steps": 100},
                    {"transitions": 200})
    row = json.loads((tmp_path / "progress.jsonl").read_text())
    assert row == {"event": {"event": "collection", "phase": 1, "steps": 100},
                   "counts": {"transitions": 200}}
    assert b"worlds" not in (tmp_path / "progress.jsonl").read_bytes()
    assert summary.read_bytes() == first

    from experiments.candidates.uav_service_auxiliary.b09 import persistence
    real_replace = persistence.os.replace
    def inspect_replace(source, destination):
        assert summary.read_bytes() == first
        assert json.loads(open(source, encoding="utf-8").read())["status"] == "COMPLETE"
        return real_replace(source, destination)
    monkeypatch.setattr(persistence.os, "replace", inspect_replace)
    write_summary(summary, {"status": "COMPLETE", "payload": large})
    assert json.loads(summary.read_text())["status"] == "COMPLETE"
    assert not list(tmp_path.glob(".summary-*.json"))


def test_failed_serialization_keeps_prior_complete_summary(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path, {"status": "COMPLETE"})
    before = path.read_bytes()
    with pytest.raises(ValueError):
        write_summary(path, {"bad": float("nan")})
    assert path.read_bytes() == before
