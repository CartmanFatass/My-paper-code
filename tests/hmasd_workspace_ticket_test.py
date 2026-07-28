from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import hmasd_workspace_ticket as ticketing  # noqa: E402


def git(root: Path, *args: str) -> str:
    return ticketing._git(root, *args)


def repository(tmp_path: Path) -> tuple[Path, Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init")
    git(source, "config", "user.name", "HMASD Ticket Test")
    git(source, "config", "user.email", "ticket-test@example.invalid")
    (source / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(source, "add", "seed.txt")
    git(source, "commit", "-m", "seed")
    worktree_root = tmp_path / "worktrees" / "HMASD"
    worktree_root.mkdir(parents=True)
    return source, worktree_root, git(source, "rev-parse", "HEAD")


def provision(
    monkeypatch: pytest.MonkeyPatch,
    source: Path,
    worktree_root: Path,
    base: str,
    assignment: str = "TASK_A",
    allowed: tuple[str, ...] = ("pkg/worker.py", "tests/worker_test.py"),
) -> dict[str, object]:
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    args = argparse.Namespace(
        repo=source,
        assignment_id=assignment,
        base_commit=base,
        allow=list(allowed),
    )
    return ticketing.provision_ticket(args)


def test_provision_resolve_and_verify_exact_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(monkeypatch, source, worktree_root, base)
    assert created["status"] == "WORKSPACE_TICKET_PROVISIONED"
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))
    assert worktree.parent == worktree_root.resolve()
    assert ticket.parent == source / ".git" / ticketing.TICKET_DIRECTORY

    resolved = ticketing.resolve_ticket(
        argparse.Namespace(ticket=ticket, assignment_id="TASK_A")
    )
    assert resolved["status"] == "WORKSPACE_TICKET_READY"
    assert Path(str(resolved["resolved_worktree"])) == worktree.resolve()

    (worktree / "pkg").mkdir(exist_ok=True)
    (worktree / "pkg" / "worker.py").write_text("VALUE = 1\n", encoding="utf-8")
    verified = ticketing.verify_ticket(
        argparse.Namespace(ticket=ticket, assignment_id="TASK_A")
    )
    assert verified["status"] == "WORKSPACE_TICKET_VERIFIED"
    assert verified["changed_paths"] == ["pkg/worker.py"]


def test_ticket_rejects_external_substitution_and_out_of_scope_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(monkeypatch, source, worktree_root, base)
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))

    external = tmp_path / "unregistered"
    git(source, "worktree", "add", "--detach", str(external), base)
    payload = json.loads(ticket.read_text(encoding="utf-8"))
    payload["resolved_worktree"] = str(external.resolve())
    payload["git_admin_dir"] = str(ticketing._git_admin_dir(external))
    ticket.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ticketing.TicketError, match="outside the registered worktree root"):
        ticketing.resolve_ticket(
            argparse.Namespace(ticket=ticket, assignment_id="TASK_A")
        )

    payload["resolved_worktree"] = str(worktree)
    payload["git_admin_dir"] = str(ticketing._git_admin_dir(worktree))
    ticket.write_text(json.dumps(payload), encoding="utf-8")
    (worktree / "outside.txt").write_text("not allowed\n", encoding="utf-8")
    with pytest.raises(ticketing.TicketError, match="outside ticket scope: outside.txt"):
        ticketing.verify_ticket(
            argparse.Namespace(ticket=ticket, assignment_id="TASK_A")
        )


def test_provision_rejects_traversal_bad_identity_and_commit_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    with pytest.raises(ticketing.TicketError, match="unsafe allowed path"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_TRAVERSAL",
            allowed=("../escape.py",),
        )
    with pytest.raises(ticketing.TicketError, match="unsafe assignment_id"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="../escape",
        )
    with pytest.raises(ticketing.TicketError, match="forty lowercase hexadecimal"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            "A" * 40,
            assignment="TASK_BAD_HASH",
        )

    created = provision(monkeypatch, source, worktree_root, base, assignment="TASK_DRIFT")
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))
    (worktree / "seed.txt").write_text("changed\n", encoding="utf-8")
    git(worktree, "add", "seed.txt")
    git(worktree, "commit", "-m", "drift")
    with pytest.raises(ticketing.TicketError, match="worktree HEAD drift"):
        ticketing.verify_ticket(
            argparse.Namespace(ticket=ticket, assignment_id="TASK_DRIFT")
        )


def test_failed_ticket_write_removes_new_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    blocker = tmp_path / "ticket-parent-is-a-file"
    blocker.write_text("blocked\n", encoding="utf-8")
    monkeypatch.setattr(
        ticketing,
        "_ticket_path",
        lambda _common, assignment: blocker / f"{assignment}.json",
    )
    with pytest.raises(ticketing.TicketError, match="cannot write workspace ticket"):
        provision(monkeypatch, source, worktree_root, base, assignment="TASK_ROLLBACK")
    assert not (worktree_root / "TASK_ROLLBACK").exists()
    assert "TASK_ROLLBACK" not in git(source, "worktree", "list")
