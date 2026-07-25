from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "hmasd_workspace_ticket.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init")
    git(source, "config", "user.name", "HMASD Ticket Test")
    git(source, "config", "user.email", "ticket-test@example.invalid")
    (source / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(source, "add", "seed.txt")
    git(source, "commit", "-m", "seed")
    base = git(source, "rev-parse", "HEAD")
    worktree = tmp_path / "isolated"
    git(source, "worktree", "add", "--detach", str(worktree), base)
    ticket = tmp_path / "tickets" / "task.json"
    return source, worktree, ticket, base


def create(worktree: Path, ticket: Path, base: str) -> dict[str, object]:
    completed = run(
        "create",
        "--ticket",
        str(ticket),
        "--assignment-id",
        "TASK_A",
        "--worktree",
        str(worktree),
        "--base-commit",
        base,
        "--allow",
        "pkg/worker.py",
        "--allow",
        "tests/worker_test.py",
    )
    return json.loads(completed.stdout)


def test_ticket_resolves_without_child_git_and_verifies_exact_scope(tmp_path: Path) -> None:
    _, worktree, ticket, base = fixture(tmp_path)
    created = create(worktree, ticket, base)
    assert created["status"] == "WORKSPACE_TICKET_CREATED"

    resolved = json.loads(
        run(
            "resolve",
            "--ticket",
            str(ticket),
            "--assignment-id",
            "TASK_A",
        ).stdout
    )
    assert resolved["status"] == "WORKSPACE_TICKET_READY"
    assert Path(str(resolved["resolved_worktree"])) == worktree.resolve()

    (worktree / "pkg").mkdir()
    (worktree / "pkg" / "worker.py").write_text("VALUE = 1\n", encoding="utf-8")
    verified = json.loads(
        run(
            "verify",
            "--ticket",
            str(ticket),
            "--assignment-id",
            "TASK_A",
        ).stdout
    )
    assert verified["status"] == "WORKSPACE_TICKET_VERIFIED"
    assert verified["changed_paths"] == ["pkg/worker.py"]


def test_ticket_rejects_path_substitution_and_out_of_scope_writes(tmp_path: Path) -> None:
    _, worktree, ticket, base = fixture(tmp_path)
    create(worktree, ticket, base)

    payload = json.loads(ticket.read_text(encoding="utf-8"))
    payload["resolved_worktree"] = str(tmp_path / "different-thread-id")
    ticket.write_text(json.dumps(payload), encoding="utf-8")
    substituted = run("resolve", "--ticket", str(ticket), check=False)
    assert substituted.returncode == 1
    assert "ticket worktree does not resolve" in substituted.stderr

    create(worktree, ticket, base)
    (worktree / "outside.txt").write_text("not allowed\n", encoding="utf-8")
    outside = run("verify", "--ticket", str(ticket), check=False)
    assert outside.returncode == 1
    assert "changed path outside ticket scope: outside.txt" in outside.stderr


def test_ticket_rejects_traversal_and_base_commit_drift(tmp_path: Path) -> None:
    _, worktree, ticket, base = fixture(tmp_path)
    traversal = run(
        "create",
        "--ticket",
        str(ticket),
        "--assignment-id",
        "TASK_A",
        "--worktree",
        str(worktree),
        "--base-commit",
        base,
        "--allow",
        "../escape.py",
        check=False,
    )
    assert traversal.returncode == 1
    assert "unsafe allowed path" in traversal.stderr

    wrong_base = "0" * 40
    drift = run(
        "create",
        "--ticket",
        str(ticket),
        "--assignment-id",
        "TASK_A",
        "--worktree",
        str(worktree),
        "--base-commit",
        wrong_base,
        "--allow",
        "pkg/worker.py",
        check=False,
    )
    assert drift.returncode == 1
    assert "base commit mismatch" in drift.stderr
