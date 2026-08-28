from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_control_release.py"
SPEC = importlib.util.spec_from_file_location("hmasd_control_release", SCRIPT)
assert SPEC and SPEC.loader
CONTROL_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL_RELEASE)


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)


def test_inspect_fails_closed_when_git_status_cannot_be_observed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    (tmp_path / "AGENTS.md").write_bytes(b"control\n")
    run("git", "add", "AGENTS.md", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    real_run = CONTROL_RELEASE.subprocess.run

    def fail_status(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "status" in command:
            return subprocess.CompletedProcess(command, 128, "", "status observation failed")
        return real_run(command, **kwargs)

    monkeypatch.setattr(CONTROL_RELEASE.subprocess, "run", fail_status)

    with pytest.raises(CONTROL_RELEASE.ReleaseError, match="git status.*status observation failed"):
        CONTROL_RELEASE.inspect_repo(tmp_path)


def test_inspect_exits_without_release_when_control_blob_cannot_be_observed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    (tmp_path / "AGENTS.md").write_bytes(b"control\n")
    run("git", "add", "AGENTS.md", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    real_run = CONTROL_RELEASE.subprocess.run

    def fail_blob(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[-1] == "HEAD:AGENTS.md":
            return subprocess.CompletedProcess(command, 128, "", "blob observation failed")
        return real_run(command, **kwargs)

    monkeypatch.setattr(CONTROL_RELEASE.subprocess, "run", fail_blob)

    exit_code = CONTROL_RELEASE.main(["inspect", "--repo", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "git rev-parse HEAD:AGENTS.md failed: blob observation failed" in captured.err


def test_inspect_marks_control_destination_of_staged_rename_dirty(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    source = tmp_path / "docs/research/candidates/ucope/notes.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"same content\n")
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    run("git", "mv", source.relative_to(tmp_path).as_posix(), "AGENTS.md", cwd=tmp_path)

    dirty_control = sorted(
        path for path in CONTROL_RELEASE._dirty_paths(tmp_path)
        if CONTROL_RELEASE.is_control_path(path)
    )

    assert dirty_control == ["AGENTS.md"]


def test_inspect_marks_control_destination_of_staged_copy_dirty(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    run("git", "config", "status.renames", "copies", cwd=tmp_path)
    source = tmp_path / "docs/research/candidates/ucope/notes.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"same content line\n" * 20)
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    source.write_bytes(source.read_bytes() + b"one changed line\n")
    (tmp_path / "AGENTS.md").write_bytes(source.read_bytes())
    run("git", "add", source.relative_to(tmp_path).as_posix(), "AGENTS.md", cwd=tmp_path)
    status = run("git", "status", "--porcelain=v1", "-z", cwd=tmp_path)
    assert status.stdout.startswith("C  AGENTS.md\0"), status.stdout

    dirty_control = sorted(
        path for path in CONTROL_RELEASE._dirty_paths(tmp_path)
        if CONTROL_RELEASE.is_control_path(path)
    )

    assert dirty_control == ["AGENTS.md"]


def test_inspect_marks_control_source_of_staged_rename_dirty(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    (tmp_path / "AGENTS.md").write_bytes(b"control\n")
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    destination = "docs/research/candidates/ucope/notes.md"
    (tmp_path / destination).parent.mkdir(parents=True)
    run("git", "mv", "AGENTS.md", destination, cwd=tmp_path)

    result = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["dirty_control_paths"] == ["AGENTS.md"]
    assert record["publishable"] is False


def test_inspect_marks_control_source_of_staged_copy_dirty(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    run("git", "config", "status.renames", "copies", cwd=tmp_path)
    source = tmp_path / "AGENTS.md"
    source.write_bytes(b"same control line\n" * 20)
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    source.write_bytes(source.read_bytes() + b"one changed line\n")
    destination = tmp_path / "docs/research/candidates/ucope/notes.md"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    run("git", "add", "AGENTS.md", destination.relative_to(tmp_path).as_posix(), cwd=tmp_path)
    status = run("git", "status", "--porcelain=v1", "-z", cwd=tmp_path)
    assert f"C  {destination.relative_to(tmp_path).as_posix()}\0AGENTS.md\0" in status.stdout

    result = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["dirty_control_paths"] == ["AGENTS.md"]
    assert record["publishable"] is False


def test_inspect_reports_publishable_release_and_ignores_direction_dirty(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    control = tmp_path / "AGENTS.md"
    control.write_bytes(b"control\n")
    direction = tmp_path / "docs/research/candidates/ucope/DIRECTION.md"
    direction.parent.mkdir(parents=True)
    direction.write_bytes(b"science\n")
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    direction.write_bytes(b"science remains direction-owned\n")

    result = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["protocol_epoch"] == 2
    assert record["branch"] == "main"
    assert record["head"] == record["origin_main"]
    assert record["control_paths"] == ["AGENTS.md"]
    assert record["dirty_control_paths"] == []
    assert record["publishable"] is True
    assert len(record["control_release_id"]) == 64


def test_verify_rejects_dirty_control_path_and_wrong_release_id(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    (tmp_path / "AGENTS.md").write_bytes(b"published\n")
    run("git", "add", "AGENTS.md", cwd=tmp_path)
    run("git", "commit", "-m", "base", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)
    inspected = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)
    release_id = json.loads(inspected.stdout)["control_release_id"]

    wrong = run(sys.executable, str(SCRIPT), "verify", "--repo", str(tmp_path), "--expected-id", "0" * 64, cwd=ROOT)
    assert wrong.returncode == 2 and "does not match" in wrong.stderr

    (tmp_path / "AGENTS.md").write_bytes(b"dirty\n")
    dirty = run(sys.executable, str(SCRIPT), "verify", "--repo", str(tmp_path), "--expected-id", release_id, cwd=ROOT)
    assert dirty.returncode == 2 and "not publishable" in dirty.stderr


def test_inspect_includes_capability_contract_but_not_evolving_tool_surface(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    expected = [
        ".gitattributes",
        "docs/SCIENTIFIC_CAPABILITY_LAYER_REQUIREMENTS.md",
        "scripts/hmasd_science_capabilities.py",
        "scripts/schemas/hmasd_instrument_evidence_v1.schema.json",
        "scripts/schemas/hmasd_instrument_observation_v1.schema.json",
        "scripts/schemas/hmasd_portfolio_registry.schema.json",
        "tests/codex_config_contract_test.py",
        "tests/fixtures/hmasd_science/case.json",
        "tests/hmasd_dashboard_test.py",
        "tests/hmasd_portfolio_decision_v2_test.py",
        "tests/hmasd_science_capabilities_test.py",
        "tests/hmasd_scientific_control_plane_test.py",
    ]
    excluded = [
        ".agents/skills/hmasd-scientific-critical-thinking/SKILL.md",
        "configs/scientific-capabilities-v1.toml",
        "configs/scientific-capability-sources-v1.json",
        "environments/hmasd-science-tools/manifest.json",
    ]
    for path in [*expected, *excluded]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"{path}\n".encode())
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "control surface", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)

    result = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["control_paths"] == expected
    assert not set(excluded) & set(record["control_paths"])


def test_inspect_includes_current_v2_mechanical_surface_but_not_direction_science(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    expected = sorted([
        "docs/project/git-path-policy-v1.json",
        "scripts/hmasd_direction_git.py",
        "scripts/hmasd_path_policy.py",
        "scripts/hmasd_operator_result.py",
        "scripts/hmasd_protocol_contracts.py",
        "scripts/hmasd_run.py",
        "scripts/schemas/hmasd_operator_result_v2.schema.json",
        "tests/hmasd_direction_git_test.py",
        "tests/hmasd_path_policy_test.py",
        "tests/hmasd_operator_result_test.py",
        "tests/hmasd_protocol_contracts_test.py",
        "tests/hmasd_run_test.py",
    ])
    excluded = "docs/research/candidates/ucope/DIRECTION.md"
    for path in [*expected, excluded]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"{path}\n".encode())
    run("git", "add", ".", cwd=tmp_path)
    run("git", "commit", "-m", "current v2 mechanics", cwd=tmp_path)
    run("git", "remote", "add", "origin", str(tmp_path), cwd=tmp_path)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=tmp_path)

    result = run(sys.executable, str(SCRIPT), "inspect", "--repo", str(tmp_path), cwd=ROOT)

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["control_paths"] == expected
    assert excluded not in record["control_paths"]
