"""Create and validate machine-resolved HMASD isolated-worktree tickets."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 2
WORKTREE_ROOT = Path(r"C:\worktrees\HMASD")
REGISTERED_REPOSITORY = Path(__file__).resolve().parents[1]
TICKET_DIRECTORY = "hmasd-workspace-tickets"
ASSIGNMENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")


class TicketError(RuntimeError):
    """Fail-closed workspace-ticket error."""


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise TicketError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def _canonical(path: Path, *, label: str) -> Path:
    try:
        return path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise TicketError(f"{label} does not resolve: {path}: {exc}") from exc


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _is_reparse_point(path: Path) -> bool:
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _worktree_root() -> Path:
    root = _canonical(WORKTREE_ROOT, label="registered worktree root")
    if not _same_path(root, WORKTREE_ROOT) or root.is_symlink() or _is_reparse_point(root):
        raise TicketError("registered worktree root is redirected")
    return root


def _assignment_id(raw: str) -> str:
    if not ASSIGNMENT_ID.fullmatch(raw):
        raise TicketError(f"unsafe assignment_id: {raw!r}")
    return raw


def _main_repository(raw: Path) -> Path:
    repo = _canonical(raw, label="source repository")
    registered = _canonical(REGISTERED_REPOSITORY, label="registered repository")
    if not _same_path(repo, registered):
        raise TicketError("source repository is not the registered HMASD checkout")
    top = _canonical(Path(_git(repo, "rev-parse", "--show-toplevel")), label="git top")
    if not _same_path(repo, top) or not (repo / ".git").is_dir():
        raise TicketError("provision requires the main HMASD checkout root")
    return repo


def _common_git_dir(repo: Path) -> Path:
    raw = Path(_git(repo, "rev-parse", "--git-common-dir"))
    if not raw.is_absolute():
        raw = repo / raw
    return _canonical(raw, label="common git directory")


def _ticket_path(common_git_dir: Path, assignment_id: str) -> Path:
    return common_git_dir / TICKET_DIRECTORY / f"{assignment_id}.json"


def _normalize_allowed(raw: str) -> str:
    normalized = raw.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        not normalized
        or normalized in {".", "/"}
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or ":" in candidate.parts[0]
    ):
        raise TicketError(f"unsafe allowed path: {raw!r}")
    return candidate.as_posix()


def _git_admin_dir(worktree: Path) -> Path:
    marker = worktree / ".git"
    if not marker.is_file():
        raise TicketError(f"isolated worktree has no .git file: {worktree}")
    text = marker.read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    if not text.lower().startswith(prefix):
        raise TicketError(f"invalid worktree .git marker: {marker}")
    raw = text[len(prefix) :].strip()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = marker.parent / candidate
    return _canonical(candidate, label="worktree git admin directory")


def _load_ticket(ticket_path: Path, expected_assignment: str | None) -> dict[str, Any]:
    ticket_path = _canonical(ticket_path, label="workspace ticket")
    try:
        payload = json.loads(ticket_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TicketError(f"invalid workspace ticket: {ticket_path}: {exc}") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise TicketError("unsupported workspace ticket schema")
    assignment_id = payload.get("assignment_id")
    if not isinstance(assignment_id, str) or not assignment_id:
        raise TicketError("workspace ticket has no assignment_id")
    if expected_assignment is not None and assignment_id != expected_assignment:
        raise TicketError(
            f"assignment mismatch: expected {expected_assignment}, got {assignment_id}"
        )
    return payload


def _resolve_payload(
    ticket_path: Path, expected_assignment: str | None
) -> tuple[dict[str, Any], Path, list[str]]:
    canonical_ticket = _canonical(ticket_path, label="workspace ticket")
    payload = _load_ticket(canonical_ticket, expected_assignment)
    raw_worktree = payload.get("resolved_worktree")
    if not isinstance(raw_worktree, str):
        raise TicketError("workspace ticket has no resolved_worktree")
    worktree = _canonical(Path(raw_worktree), label="ticket worktree")
    if not _same_path(worktree, Path(raw_worktree)):
        raise TicketError("ticket worktree is not canonical")
    root = _worktree_root()
    if not _same_path(worktree.parent, root):
        raise TicketError("ticket worktree is outside the registered worktree root")

    recorded_admin = payload.get("git_admin_dir")
    if not isinstance(recorded_admin, str):
        raise TicketError("workspace ticket has no git_admin_dir")
    actual_admin = _git_admin_dir(worktree)
    recorded_admin_path = _canonical(
        Path(recorded_admin), label="recorded git admin directory"
    )
    if not _same_path(actual_admin, recorded_admin_path):
        raise TicketError("worktree git identity changed after ticket creation")
    common_git_dir = actual_admin.parent.parent
    expected_ticket = _ticket_path(common_git_dir, payload["assignment_id"])
    if not _same_path(canonical_ticket, expected_ticket):
        raise TicketError("workspace ticket is outside the registered ticket directory")

    raw_allowed = payload.get("allowed_paths")
    if not isinstance(raw_allowed, list) or not raw_allowed:
        raise TicketError("workspace ticket has no allowed_paths")
    allowed = [_normalize_allowed(value) for value in raw_allowed if isinstance(value, str)]
    if len(allowed) != len(raw_allowed) or len(set(allowed)) != len(allowed):
        raise TicketError("workspace ticket allowed_paths are invalid or duplicated")
    for relative in allowed:
        candidate = (worktree / Path(relative)).resolve(strict=False)
        try:
            candidate.relative_to(worktree)
        except ValueError as exc:
            raise TicketError(f"allowed path escapes worktree: {relative}") from exc
    return payload, worktree, allowed


def _status_paths(worktree: Path) -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(worktree),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "-z",
        ],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise TicketError(f"git status failed: {detail}")
    entries = completed.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4:
            raise TicketError("malformed git status entry")
        status = entry[:2]
        paths.append(entry[3:].decode("utf-8", errors="strict").replace("\\", "/"))
        if b"R" in status or b"C" in status:
            if index >= len(entries) or not entries[index]:
                raise TicketError("malformed rename/copy status entry")
            paths.append(
                entries[index].decode("utf-8", errors="strict").replace("\\", "/")
            )
            index += 1
    return sorted(set(paths))


def _is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == root or path.startswith(root + "/") for root in allowed)


def provision_ticket(args: argparse.Namespace) -> dict[str, Any]:
    repo = _main_repository(args.repo)
    assignment_id = _assignment_id(args.assignment_id)
    root = _worktree_root()
    worktree = root / assignment_id
    if worktree.exists():
        raise TicketError(f"worktree destination already exists: {worktree}")

    expected_commit = args.base_commit.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise TicketError("base commit must be exactly forty lowercase hexadecimal characters")
    actual_commit = _git(repo, "rev-parse", f"{expected_commit}^{{commit}}")
    if actual_commit != expected_commit:
        raise TicketError(
            f"base commit mismatch: expected {expected_commit}, got {actual_commit}"
        )
    allowed = [_normalize_allowed(value) for value in args.allow]
    if not allowed or len(set(allowed)) != len(allowed):
        raise TicketError("at least one unique allowed path is required")
    ticket_path = _ticket_path(_common_git_dir(repo), assignment_id)
    if ticket_path.exists():
        raise TicketError(f"workspace ticket already exists: {ticket_path}")

    created = False
    try:
        _git(repo, "worktree", "add", "--detach", str(worktree), expected_commit)
        created = True
        canonical_worktree = _canonical(worktree, label="provisioned worktree")
        if not _same_path(canonical_worktree.parent, root):
            raise TicketError("provisioned worktree escaped the registered root")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "assignment_id": assignment_id,
            "resolved_worktree": str(canonical_worktree),
            "git_admin_dir": str(_git_admin_dir(canonical_worktree)),
            "base_commit": actual_commit,
            "allowed_paths": allowed,
        }
        ticket_path.parent.mkdir(parents=True, exist_ok=True)
        ticket_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, TicketError) as exc:
        if ticket_path.exists():
            ticket_path.unlink()
        if created:
            cleanup = subprocess.run(
                ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if cleanup.returncode != 0:
                detail = cleanup.stderr.strip() or cleanup.stdout.strip()
                raise TicketError(f"provision failed and cleanup failed: {exc}; {detail}") from exc
        if isinstance(exc, TicketError):
            raise
        raise TicketError(f"cannot write workspace ticket: {exc}") from exc
    return {"status": "WORKSPACE_TICKET_PROVISIONED", "ticket": str(ticket_path), **payload}


def resolve_ticket(args: argparse.Namespace) -> dict[str, Any]:
    payload, worktree, allowed = _resolve_payload(args.ticket, args.assignment_id)
    return {
        "status": "WORKSPACE_TICKET_READY",
        "assignment_id": payload["assignment_id"],
        "resolved_worktree": str(worktree),
        "base_commit": payload["base_commit"],
        "allowed_paths": allowed,
    }


def verify_ticket(args: argparse.Namespace) -> dict[str, Any]:
    payload, worktree, allowed = _resolve_payload(args.ticket, args.assignment_id)
    actual_commit = _git(worktree, "rev-parse", "HEAD")
    if actual_commit != payload.get("base_commit"):
        raise TicketError(
            f"worktree HEAD drift: expected {payload.get('base_commit')}, got {actual_commit}"
        )
    changed_paths = _status_paths(worktree)
    disallowed = [path for path in changed_paths if not _is_allowed(path, allowed)]
    if disallowed:
        raise TicketError("changed path outside ticket scope: " + ", ".join(disallowed))
    return {
        "status": "WORKSPACE_TICKET_VERIFIED",
        "assignment_id": payload["assignment_id"],
        "resolved_worktree": str(worktree),
        "base_commit": actual_commit,
        "allowed_paths": allowed,
        "changed_paths": changed_paths,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    provision = subparsers.add_parser("provision")
    provision.add_argument("--repo", type=Path, required=True)
    provision.add_argument("--assignment-id", required=True)
    provision.add_argument("--base-commit", required=True)
    provision.add_argument("--allow", action="append", default=[], required=True)
    provision.set_defaults(handler=provision_ticket)

    for name, handler in (("resolve", resolve_ticket), ("verify", verify_ticket)):
        command = subparsers.add_parser(name)
        command.add_argument("--ticket", type=Path, required=True)
        command.add_argument("--assignment-id")
        command.set_defaults(handler=handler)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = args.handler(args)
    except TicketError as exc:
        print(f"WORKSPACE_TICKET_ERROR {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
