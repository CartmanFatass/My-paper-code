from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
import sys

import pytest

from scripts import hmasd_launch
from scripts import hmasd_snapshot_gc as gc


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True,
                            capture_output=True, check=True, timeout=30)
    return result.stdout.strip()


@pytest.fixture
def operation(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    (repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (repo / "source.txt").write_text("source", encoding="utf-8")
    git(repo, "add", ".gitignore", "source.txt")
    git(repo, "commit", "-m", "source")
    sha = git(repo, "rev-parse", "HEAD")
    common = repo / ".git"
    parent = common / "hmasd-launch-sources"
    parent.mkdir()
    snapshot_id = "a" * 32
    snapshot = parent / snapshot_id
    git(repo, "worktree", "add", "--detach", "--lock", str(snapshot), sha)
    output = repo / "runs" / "demo" / "attempt"
    output.mkdir(parents=True)
    claim_root = common / "hmasd-admission"
    claim_root.mkdir()
    claim_path = claim_root / ("b" * 64 + ".json")
    manifest_path = output / "launch-manifest.json"
    identity = {"kind": "linux_pid_start_ticks", "pid": 999999999,
                "boot_id": "fixture", "start_ticks": 1, "session_id": 999999999}
    runner_identity = dict(identity, pid=999999998, session_id=999999998)
    shared = {"claim_key": "b" * 64, "direction": "demo", "sha": sha,
              "node": "fixture", "host_identity": platform.node(),
              "source_root": str(snapshot), "output_root": str(output),
              "identity_command": ["python", "runner.py"], "command_sha256": "c" * 64}
    claim = dict(shared, manifest_ref=str(manifest_path), status="accepted", acceptance="accepted")
    manifest = dict(shared, cwd=str(snapshot), claim_ref=str(claim_path),
                    process={"identity": identity}, runner_process={"identity": runner_identity},
                    process_exit=str(output / "process-exit.json"))
    claim_path.write_text(json.dumps(claim), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    witness = {"status": "exited", "process_identity": runner_identity,
               "supervisor_identity": identity, "exit_code": 0}
    (output / "process-exit.json").write_text(json.dumps(witness), encoding="utf-8")
    monkeypatch.setattr(gc, "_process_references", lambda _snapshot: [])
    return repo, snapshot_id, snapshot, output, claim_path


def test_preview_and_explicit_apply_preserve_operation_records(operation):
    repo, snapshot_id, snapshot, output, claim_path = operation
    preview = gc.inspect(repo, snapshot_id)
    assert preview["eligible"] and snapshot.is_dir()
    assert "worktree " + str(snapshot) in git(repo, "worktree", "list", "--porcelain")
    evidence = {path: path.read_bytes() for path in
                (claim_path, output / "launch-manifest.json", output / "process-exit.json")}
    applied = gc.inspect(repo, snapshot_id, apply=True)
    assert applied["removed"] and not snapshot.exists()
    assert all(path.read_bytes() == content for path, content in evidence.items())
    recovered = hmasd_launch.status(claim_path)
    assert recovered["execution"]["state"] == "exited"
    assert recovered["execution"]["exit_witness"]["state"] == "valid"
    assert gc.inspect(repo, snapshot_id, apply=True)["reason"] == "absent"


@pytest.mark.parametrize("change", ["tracked", "untracked", "ignored"])
def test_changed_snapshot_refused(operation, change):
    repo, snapshot_id, snapshot, _output, _claim = operation
    if change == "tracked":
        (snapshot / "source.txt").write_text("changed", encoding="utf-8")
    elif change == "untracked":
        (snapshot / "new.txt").write_text("new", encoding="utf-8")
    else:
        (snapshot / "ignored").mkdir()
        (snapshot / "ignored" / "data.bin").write_bytes(b"data")
    result = gc.inspect(repo, snapshot_id, apply=True)
    assert not result["eligible"] and "files" in result["reason"]
    assert snapshot.exists()


def test_missing_witness_and_unclaimed_snapshot_refused(operation):
    repo, snapshot_id, snapshot, output, claim = operation
    (output / "process-exit.json").unlink()
    assert "witness" in gc.inspect(repo, snapshot_id, apply=True)["reason"]
    (output / "process-exit.json").write_text("{}", encoding="utf-8")
    claim.unlink()
    assert "associated claim" in gc.inspect(repo, snapshot_id, apply=True)["reason"]
    assert snapshot.exists()


def test_commit_must_have_durable_ref(operation):
    repo, snapshot_id, snapshot, _output, _claim = operation
    git(repo, "checkout", "--detach")
    git(repo, "branch", "-D", "main")
    result = gc.inspect(repo, snapshot_id, apply=True)
    assert "not reachable" in result["reason"]
    assert snapshot.exists()


@pytest.mark.parametrize("record,key,value", [
    ("claim", "sha", "0" * 40),
    ("manifest", "sha", "0" * 40),
    ("claim", "host_identity", "another-host"),
    ("manifest", "host_identity", "another-host"),
])
def test_inconsistent_operation_metadata_refused(operation, record, key, value):
    repo, snapshot_id, snapshot, output, claim_path = operation
    path = claim_path if record == "claim" else output / "launch-manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = value
    path.write_text(json.dumps(payload), encoding="utf-8")
    before = path.read_bytes()
    result = gc.inspect(repo, snapshot_id, apply=True)
    assert not result["eligible"] and snapshot.exists()
    assert path.read_bytes() == before


@pytest.mark.parametrize("role,state", [
    ("runner", "running"),
    ("supervisor", "running"),
    ("runner", "unavailable"),
    ("supervisor", "unknown"),
])
def test_native_process_uncertainty_refused(operation, monkeypatch, role, state):
    repo, snapshot_id, snapshot, output, claim_path = operation
    real_status = gc.hmasd_launch.status(claim_path)
    real_status["execution"][role] = {"state": state}
    monkeypatch.setattr(gc.hmasd_launch, "status", lambda _claim: real_status)
    claim_before = claim_path.read_bytes()
    manifest_before = (output / "launch-manifest.json").read_bytes()
    result = gc.inspect(repo, snapshot_id, apply=True)
    assert role in result["reason"] and snapshot.exists()
    assert claim_path.read_bytes() == claim_before
    assert (output / "launch-manifest.json").read_bytes() == manifest_before


def test_redirected_snapshot_refused(operation):
    repo, snapshot_id, snapshot, output, claim_path = operation
    moved = snapshot.with_name("moved")
    snapshot.rename(moved)
    snapshot.symlink_to(moved, target_is_directory=True)
    result = gc.inspect(repo, snapshot_id, apply=True)
    assert "redirected" in result["reason"]
    assert snapshot.is_symlink() and moved.exists()
    assert claim_path.is_file() and (output / "launch-manifest.json").is_file()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc inspection")
def test_live_cwd_process_blocks_reclamation(operation, monkeypatch):
    repo, snapshot_id, snapshot, _output, _claim = operation
    child = subprocess.Popen(["sleep", "30"], cwd=snapshot, start_new_session=True)
    try:
        monkeypatch.undo()
        scan = gc._process_references
        assert any(f"pid {child.pid} cwd" in item for item in scan(snapshot, pids=[child.pid]))
        monkeypatch.setattr(gc, "_process_references",
                            lambda path: scan(path, pids=[child.pid]))
        result = gc.inspect(repo, snapshot_id, apply=True)
        assert "referenced by" in result["reason"]
        assert snapshot.exists()
    finally:
        child.terminate()
        child.wait(timeout=5)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc inspection")
def test_non_dumpable_same_uid_process_is_not_skipped(operation, monkeypatch):
    _repo, _snapshot_id, snapshot, _output, _claim = operation
    monkeypatch.undo()
    child = subprocess.Popen(
        [sys.executable, "-c",
         "import ctypes,time; assert ctypes.CDLL(None).prctl(4,0,0,0,0)==0; "
         "print('ready',flush=True); time.sleep(30)"],
        cwd=snapshot, stdout=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        assert child.stdout is not None and child.stdout.readline().strip() == "ready"
        # A denied /proc read is a refusal; a privileged scan can identify its
        # cwd. Either outcome is safe. Returning [] would skip the live child.
        try:
            references = gc._process_references(snapshot, pids=[child.pid])
        except gc.Refusal:
            pass
        else:
            assert references
    finally:
        child.terminate()
        child.wait(timeout=5)
