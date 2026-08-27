from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_control_release.py"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)


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


def test_inspect_includes_dashboard_portfolio_and_real_schema_but_not_scientific_skill(tmp_path: Path) -> None:
    run("git", "init", "-b", "main", cwd=tmp_path)
    run("git", "config", "user.email", "test@example.invalid", cwd=tmp_path)
    run("git", "config", "user.name", "HMASD Test", cwd=tmp_path)
    expected = [
        "scripts/schemas/hmasd_portfolio_registry.schema.json",
        "tests/hmasd_dashboard_test.py",
        "tests/hmasd_portfolio_decision_v2_test.py",
    ]
    excluded = ".agents/skills/hmasd-marl-experiment-design/SKILL.md"
    for path in [*expected, excluded]:
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
    assert excluded not in record["control_paths"]


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
