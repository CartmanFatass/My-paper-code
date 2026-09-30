"""Pinned compact Git inputs, with no model/host/production-reader call."""
import hashlib
import json
import subprocess

import pytest

from experiments.candidates.uav_fleet_adaptation.b06_count_development import assets


def saved_calibration(tmp_path, monkeypatch, *, change=None):
    repo = tmp_path / "source"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    record = dict(status="VERIFIED", launch_sha="a" * 40,
                  calibrations=[dict(lineage=0, winner="S_T2"), dict(lineage=1, winner="S_T1")])
    if change == "status": record["status"] = "FAILED"
    if change == "source": record["launch_sha"] = "b" * 40
    if change == "choice": record["calibrations"][1]["winner"] = "S_T2"
    path = repo / "reading.json"
    data = json.dumps(record).encode()
    path.write_bytes(data)
    subprocess.run(["git", "-C", str(repo), "add", "--", path.name], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "compact calibration fixture"], check=True)
    source = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    binding = dict(evidence_commit=source, reading_path="reading.json",
                   reading_sha256=hashlib.sha256(data).hexdigest(), launch_sha="a" * 40,
                   winners=["S_T2", "S_T1"])
    monkeypatch.setattr(assets, "CALIBRATION_SOURCE", binding)
    return repo, path, binding


def test_committed_input_survives_omitted_or_dirty_working_file(tmp_path, monkeypatch):
    repo, path, _ = saved_calibration(tmp_path, monkeypatch)
    # Reproduce the load-bearing sparse condition: tracked path, absent working file.
    subprocess.run(["git", "-C", str(repo), "update-index", "--skip-worktree", path.name], check=True)
    path.unlink()
    assert assets.verify_calibration(repo)
    path.write_text("uncommitted, irrelevant working copy")
    assert assets.verify_calibration(repo)


def test_changed_blob_hash_is_rejected(tmp_path, monkeypatch):
    repo, _, binding = saved_calibration(tmp_path, monkeypatch)
    binding["reading_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source bytes"):
        assets.verify_calibration(repo)


@pytest.mark.parametrize("change", ["status", "source", "choice"])
def test_bound_calibration_metadata_is_checked(tmp_path, monkeypatch, change):
    repo, _, _ = saved_calibration(tmp_path, monkeypatch, change=change)
    with pytest.raises(ValueError, match="choices/source"):
        assets.verify_calibration(repo)
