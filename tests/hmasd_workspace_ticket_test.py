from __future__ import annotations

import argparse
import json
import os
import shutil
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
    recover_partial_assignment: str | None = None,
) -> dict[str, object]:
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    args = argparse.Namespace(
        repo=source,
        assignment_id=assignment,
        base_commit=base,
        allow=list(allowed),
        recover_partial_assignment=recover_partial_assignment,
    )
    return ticketing.provision_ticket(args)


def retire(ticket: Path, assignment: str, expected_head: str) -> dict[str, object]:
    return ticketing.retire_ticket(
        argparse.Namespace(
            ticket=ticket,
            assignment_id=assignment,
            expected_head=expected_head,
        )
    )


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
    assert verified["git_visible_changed_paths"] == ["pkg/worker.py"]


def test_retire_clean_detached_ticket_removes_worktree_and_ticket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(monkeypatch, source, worktree_root, base, assignment="TASK_RETIRE")
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))

    result = retire(ticket, "TASK_RETIRE", base)

    assert result["status"] == "WORKSPACE_TICKET_RETIRED"
    assert result["retry"] is False
    assert not worktree.exists()
    assert not ticket.exists()
    assert "TASK_RETIRE" not in git(source, "worktree", "list")


def test_retire_refuses_tracked_and_untracked_git_visible_dirtiness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    tracked = provision(monkeypatch, source, worktree_root, base, assignment="TASK_DIRTY_TRACKED")
    tracked_worktree = Path(str(tracked["resolved_worktree"]))
    tracked_ticket = Path(str(tracked["ticket"]))
    (tracked_worktree / "seed.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ticketing.TicketError, match="dirty worktree"):
        retire(tracked_ticket, "TASK_DIRTY_TRACKED", base)
    assert tracked_worktree.exists()
    assert ticketing._worktree_is_registered(source, tracked_worktree)

    untracked = provision(monkeypatch, source, worktree_root, base, assignment="TASK_DIRTY_UNTRACKED")
    untracked_worktree = Path(str(untracked["resolved_worktree"]))
    untracked_ticket = Path(str(untracked["ticket"]))
    (untracked_worktree / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    with pytest.raises(ticketing.TicketError, match="dirty worktree"):
        retire(untracked_ticket, "TASK_DIRTY_UNTRACKED", base)
    assert untracked_worktree.exists()
    assert ticketing._worktree_is_registered(source, untracked_worktree)


def test_retire_refuses_attached_branch_and_expected_head_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    attached = provision(monkeypatch, source, worktree_root, base, assignment="TASK_ATTACHED")
    attached_worktree = Path(str(attached["resolved_worktree"]))
    attached_ticket = Path(str(attached["ticket"]))
    git(attached_worktree, "switch", "-c", "attached-branch")
    with pytest.raises(ticketing.TicketError, match="detached HEAD"):
        retire(attached_ticket, "TASK_ATTACHED", base)
    assert attached_worktree.exists()

    mismatch = provision(monkeypatch, source, worktree_root, base, assignment="TASK_HEAD_MISMATCH")
    mismatch_worktree = Path(str(mismatch["resolved_worktree"]))
    mismatch_ticket = Path(str(mismatch["ticket"]))
    with pytest.raises(ticketing.TicketError, match="expected HEAD mismatch"):
        retire(mismatch_ticket, "TASK_HEAD_MISMATCH", "0" * 40)
    assert mismatch_worktree.exists()


def test_retire_rejects_ticket_identity_substitution_and_non_ancestor_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(monkeypatch, source, worktree_root, base, assignment="TASK_IDENTITY")
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))
    payload = json.loads(ticket.read_text(encoding="utf-8"))
    outside = tmp_path / "outside"
    outside.mkdir()
    payload["resolved_worktree"] = str(outside)
    ticket.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ticketing.TicketError, match="outside the registered worktree root"):
        retire(ticket, "TASK_IDENTITY", base)
    assert worktree.exists()

    payload["resolved_worktree"] = str(worktree)
    ticket.write_text(json.dumps(payload), encoding="utf-8")
    tree = git(worktree, "write-tree")
    unrelated = git(worktree, "commit-tree", tree, "-m", "unrelated")
    git(worktree, "checkout", "--detach", unrelated)
    with pytest.raises(ticketing.TicketError, match="ancestor"):
        retire(ticket, "TASK_IDENTITY", unrelated)
    assert worktree.exists()


def test_retire_retry_removes_ticket_after_worktree_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(monkeypatch, source, worktree_root, base, assignment="TASK_RETRY_RETIRE")
    worktree = Path(str(created["resolved_worktree"]))
    ticket = Path(str(created["ticket"]))
    real_unlink = Path.unlink
    failed = False

    def fail_ticket_unlink(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal failed
        if path == ticket and not failed:
            failed = True
            raise OSError("simulated ticket deletion failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_ticket_unlink)
    with pytest.raises(ticketing.TicketError, match="retry retire"):
        retire(ticket, "TASK_RETRY_RETIRE", base)
    assert not worktree.exists()
    assert ticket.exists()

    result = retire(ticket, "TASK_RETRY_RETIRE", base)
    assert result["retry"] is True
    assert not ticket.exists()


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


def test_long_checkout_uses_command_local_longpaths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, _ = repository(tmp_path)
    git(source, "config", "core.longpaths", "false")
    segment = "long-checkout-segment-" + ("x" * 20)
    relative = Path(*([segment] * 7)) / "payload.txt"
    blob_source = source / "long-path-payload.txt"
    blob_source.write_text("long path\n", encoding="utf-8")
    blob = git(source, "hash-object", "-w", str(blob_source))
    blob_source.unlink()
    git(
        source,
        "-c",
        "core.longpaths=true",
        "update-index",
        "--add",
        "--cacheinfo",
        f"100644,{blob},{relative.as_posix()}",
    )
    git(source, "commit", "-m", "long checkout fixture")
    base = git(source, "rev-parse", "HEAD")

    calls: list[tuple[str, ...]] = []
    real_git = ticketing._git

    def capture_git(root: Path, *args: str) -> str:
        if "worktree" in args:
            calls.append(args)
        return real_git(root, *args)

    monkeypatch.setattr(ticketing, "_git", capture_git)
    created = provision(
        monkeypatch,
        source,
        worktree_root,
        base,
        assignment="TASK_LONG_PATH",
    )
    worktree = Path(str(created["resolved_worktree"]))
    assert len(str(worktree / relative)) > 260
    checked_out = worktree / relative
    if os.name == "nt":
        checked_out = Path("\\\\?\\" + str(checked_out))
    assert checked_out.is_file()
    assert git(worktree, "-c", "core.longpaths=true", "status", "--short") == ""
    verified = ticketing.verify_ticket(
        argparse.Namespace(ticket=Path(str(created["ticket"])), assignment_id="TASK_LONG_PATH")
    )
    assert verified["git_visible_changed_paths"] == []
    assert git(source, "config", "core.longpaths") == "false"
    assert any(
        args[:4] == ("-c", "core.longpaths=true", "worktree", "add")
        for args in calls
    )


def test_partial_add_failure_is_cleaned_even_when_add_does_not_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    real_git = ticketing._git
    failed = False

    def fail_after_add(root: Path, *args: str) -> str:
        nonlocal failed
        if (
            not failed
            and args[:4] == ("-c", "core.longpaths=true", "worktree", "add")
        ):
            failed = True
            real_git(root, *args)
            raise ticketing.TicketError("simulated post-registration add failure")
        return real_git(root, *args)

    monkeypatch.setattr(ticketing, "_git", fail_after_add)
    with pytest.raises(ticketing.TicketError, match="simulated post-registration"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_PARTIAL_ADD",
        )
    assert not (worktree_root / "TASK_PARTIAL_ADD").exists()
    assert "TASK_PARTIAL_ADD" not in real_git(source, "worktree", "list")
    ticket = source / ".git" / ticketing.TICKET_DIRECTORY / "TASK_PARTIAL_ADD.json"
    assert not ticket.exists()


def test_unregistered_directory_from_current_attempt_is_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    real_git = ticketing._git

    def fail_before_registration(root: Path, *args: str) -> str:
        if args[:4] == ("-c", "core.longpaths=true", "worktree", "add"):
            partial = Path(args[-2])
            partial.mkdir()
            (partial / "partial.txt").write_text("partial\n", encoding="utf-8")
            raise ticketing.TicketError("simulated pre-registration add failure")
        return real_git(root, *args)

    monkeypatch.setattr(ticketing, "_git", fail_before_registration)
    with pytest.raises(ticketing.TicketError, match="simulated pre-registration"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_UNREGISTERED_PARTIAL",
        )
    assert not (worktree_root / "TASK_UNREGISTERED_PARTIAL").exists()
    assert "TASK_UNREGISTERED_PARTIAL" not in real_git(source, "worktree", "list")


def test_new_provision_recovers_one_registered_unticketed_partial_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    old_worktree = worktree_root / "TASK_R2"
    ticketing._worktree_git(
        source, "add", "--detach", str(old_worktree), base
    )
    real_git = ticketing._git
    invocations: list[tuple[str, ...]] = []

    def record_git(root: Path, *args: str) -> str:
        invocations.append(args)
        return real_git(root, *args)

    monkeypatch.setattr(ticketing, "_git", record_git)

    created = provision(
        monkeypatch,
        source,
        worktree_root,
        base,
        assignment="TASK_R3",
        recover_partial_assignment="TASK_R2",
    )
    assert created["recovered_assignment_id"] == "TASK_R2"
    assert created["recovery_status"] == "PARTIAL_WORKSPACE_CLEANED"
    assert created["recovery_observation"] == "REGISTERED_WORKTREE_REMOVED"
    assert not old_worktree.exists()
    assert "TASK_R2" not in git(source, "worktree", "list")
    assert Path(str(created["resolved_worktree"])).exists()
    assert any(
        args[:5]
        == ("-c", "core.longpaths=true", "worktree", "remove", "--force")
        for args in invocations
    )


def test_new_provision_accepts_idempotent_already_clean_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    created = provision(
        monkeypatch,
        source,
        worktree_root,
        base,
        assignment="TASK_R4",
        recover_partial_assignment="TASK_R2_ALREADY_CLEAN",
    )

    assert created["recovered_assignment_id"] == "TASK_R2_ALREADY_CLEAN"
    assert created["recovery_status"] == "PARTIAL_WORKSPACE_CLEANED"
    assert created["recovery_observation"] == "ALREADY_CLEAN"
    assert not (worktree_root / "TASK_R2_ALREADY_CLEAN").exists()
    assert "TASK_R2_ALREADY_CLEAN" not in git(source, "worktree", "list")
    assert Path(str(created["resolved_worktree"])).exists()


def test_new_provision_removes_registered_state_with_missing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    old_worktree = worktree_root / "TASK_REGISTERED_WITHOUT_DESTINATION"
    ticketing._worktree_git(source, "add", "--detach", str(old_worktree), base)
    shutil.rmtree(old_worktree)
    assert not old_worktree.exists()
    assert ticketing._worktree_is_registered(source, old_worktree)

    created = provision(
        monkeypatch,
        source,
        worktree_root,
        base,
        assignment="TASK_AFTER_MISSING_DESTINATION",
        recover_partial_assignment="TASK_REGISTERED_WITHOUT_DESTINATION",
    )

    assert created["recovery_status"] == "PARTIAL_WORKSPACE_CLEANED"
    assert created["recovery_observation"] == "REGISTERED_STATE_REMOVED"
    assert not ticketing._worktree_is_registered(source, old_worktree)
    assert Path(str(created["resolved_worktree"])).exists()


def test_partial_recovery_refuses_ticketed_or_unregistered_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    old = provision(
        monkeypatch,
        source,
        worktree_root,
        base,
        assignment="TASK_TICKETED",
    )
    with pytest.raises(ticketing.TicketError, match="existing workspace ticket"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_AFTER_TICKETED",
            recover_partial_assignment="TASK_TICKETED",
        )
    assert Path(str(old["resolved_worktree"])).exists()

    unregistered = worktree_root / "TASK_UNREGISTERED"
    unregistered.mkdir()
    with pytest.raises(ticketing.TicketError, match="not the registered worktree"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_AFTER_UNREGISTERED",
            recover_partial_assignment="TASK_UNREGISTERED",
        )
    assert unregistered.exists()


def test_partial_recovery_refuses_registered_path_with_mismatched_git_backlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    old_worktree = worktree_root / "TASK_REPLACED_IDENTITY"
    ticketing._worktree_git(source, "add", "--detach", str(old_worktree), base)
    admin = ticketing._git_admin_dir(old_worktree)
    (admin / "gitdir").write_text(f"{source / '.git'}\n", encoding="utf-8")
    real_registered = ticketing._worktree_is_registered

    def retain_registered_metadata(root: Path, path: Path) -> bool:
        if ticketing._same_path(path, old_worktree):
            return True
        return real_registered(root, path)

    monkeypatch.setattr(ticketing, "_worktree_is_registered", retain_registered_metadata)
    sentinel = old_worktree / "must-remain.txt"
    sentinel.write_text("owned before recovery\n", encoding="utf-8")

    with pytest.raises(ticketing.TicketError, match="backlink identity mismatch"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_AFTER_REPLACED_IDENTITY",
            recover_partial_assignment="TASK_REPLACED_IDENTITY",
        )

    assert sentinel.read_text(encoding="utf-8") == "owned before recovery\n"
    assert admin.exists()
    assert not (worktree_root / "TASK_AFTER_REPLACED_IDENTITY").exists()
    new_ticket = source / ".git" / ticketing.TICKET_DIRECTORY / "TASK_AFTER_REPLACED_IDENTITY.json"
    assert not new_ticket.exists()


def test_partial_recovery_refuses_redirected_registered_destination_without_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    old_worktree = worktree_root / "TASK_REDIRECTED_DESTINATION"
    ticketing._worktree_git(source, "add", "--detach", str(old_worktree), base)
    real_reparse = ticketing._is_reparse_point
    real_worktree_git = ticketing._worktree_git
    remove_called = False

    def report_redirect(path: Path) -> bool:
        if ticketing._same_path(path, old_worktree):
            return True
        return real_reparse(path)

    def forbid_remove(root: Path, *args: str) -> str:
        nonlocal remove_called
        if args[:2] == ("remove", "--force"):
            remove_called = True
            raise AssertionError("redirected recovery must not invoke worktree remove")
        return real_worktree_git(root, *args)

    monkeypatch.setattr(ticketing, "_is_reparse_point", report_redirect)
    monkeypatch.setattr(ticketing, "_worktree_git", forbid_remove)
    with pytest.raises(ticketing.TicketError, match="worktree is redirected"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_AFTER_REDIRECTED_DESTINATION",
            recover_partial_assignment="TASK_REDIRECTED_DESTINATION",
        )

    assert not remove_called
    assert old_worktree.exists()
    assert not (worktree_root / "TASK_AFTER_REDIRECTED_DESTINATION").exists()
    new_ticket = source / ".git" / ticketing.TICKET_DIRECTORY / "TASK_AFTER_REDIRECTED_DESTINATION.json"
    assert not new_ticket.exists()


def test_partial_recovery_fails_if_registered_state_remains_after_remove(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, worktree_root, base = repository(tmp_path)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", source)
    old_worktree = worktree_root / "TASK_RESIDUAL_STATE"
    ticketing._worktree_git(source, "add", "--detach", str(old_worktree), base)
    real_worktree_git = ticketing._worktree_git

    def leave_registered_state(root: Path, *args: str) -> str:
        if args[:2] == ("remove", "--force"):
            return ""
        return real_worktree_git(root, *args)

    monkeypatch.setattr(ticketing, "_worktree_git", leave_registered_state)
    with pytest.raises(ticketing.TicketError, match="cleanup did not remove"):
        provision(
            monkeypatch,
            source,
            worktree_root,
            base,
            assignment="TASK_AFTER_RESIDUAL_STATE",
            recover_partial_assignment="TASK_RESIDUAL_STATE",
        )

    assert old_worktree.exists()
    assert "TASK_RESIDUAL_STATE" in git(source, "worktree", "list")
    assert not (worktree_root / "TASK_AFTER_RESIDUAL_STATE").exists()
    new_ticket = source / ".git" / ticketing.TICKET_DIRECTORY / "TASK_AFTER_RESIDUAL_STATE.json"
    assert not new_ticket.exists()
