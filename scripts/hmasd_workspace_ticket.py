"""Create and validate machine-resolved HMASD isolated-worktree tickets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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
LONG_PATH_GIT_ARGS = ("-c", "core.longpaths=true")


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


def _filesystem_cleanup_path(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    if os.name != "nt":
        return resolved
    text = str(resolved)
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


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


def _worktree_git(repo: Path, *args: str) -> str:
    return _git(repo, *LONG_PATH_GIT_ARGS, "worktree", *args)


def _registered_worktrees(repo: Path) -> list[Path]:
    paths: list[Path] = []
    for line in _worktree_git(repo, "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line[len("worktree ") :]).resolve(strict=False))
    return paths


def _worktree_is_registered(repo: Path, worktree: Path) -> bool:
    candidate = worktree.resolve(strict=False)
    return any(_same_path(candidate, path) for path in _registered_worktrees(repo))


def _verify_worktree_absent(repo: Path, worktree: Path, ticket_path: Path) -> None:
    if worktree.exists() or worktree.is_symlink() or _worktree_is_registered(repo, worktree):
        raise TicketError("partial worktree cleanup did not remove the registered state")
    if ticket_path.exists():
        raise TicketError("partial worktree cleanup left a workspace ticket")


def _cleanup_current_attempt(
    repo: Path, root: Path, worktree: Path, ticket_path: Path
) -> None:
    if ticket_path.exists():
        ticket_path.unlink()
    registered = _worktree_is_registered(repo, worktree)
    if registered:
        _worktree_git(repo, "remove", "--force", str(worktree))
    elif worktree.exists():
        if (
            not _same_path(worktree.parent, root)
            or worktree.is_symlink()
            or _is_reparse_point(worktree)
        ):
            raise TicketError("partial worktree destination is redirected")
        shutil.rmtree(_filesystem_cleanup_path(worktree))
    _verify_worktree_absent(repo, worktree, ticket_path)


def _recover_partial_assignment(
    repo: Path, root: Path, common_git_dir: Path, assignment_id: str
) -> dict[str, str]:
    worktree = root / assignment_id
    ticket_path = _ticket_path(common_git_dir, assignment_id)
    if ticket_path.exists():
        raise TicketError("partial assignment recovery refuses an existing workspace ticket")
    registered = _worktree_is_registered(repo, worktree)
    destination_present = worktree.exists() or worktree.is_symlink()
    if not registered and not destination_present:
        _verify_worktree_absent(repo, worktree, ticket_path)
        return {
            "recovered_assignment_id": assignment_id,
            "recovery_status": "PARTIAL_WORKSPACE_CLEANED",
            "recovery_observation": "ALREADY_CLEAN",
        }
    if not registered:
        raise TicketError("partial assignment is not the registered worktree identity")
    if not destination_present:
        _worktree_git(repo, "remove", "--force", str(worktree))
        _verify_worktree_absent(repo, worktree, ticket_path)
        return {
            "recovered_assignment_id": assignment_id,
            "recovery_status": "PARTIAL_WORKSPACE_CLEANED",
            "recovery_observation": "REGISTERED_STATE_REMOVED",
        }
    if (
        not _same_path(worktree.parent, root)
        or worktree.is_symlink()
        or _is_reparse_point(worktree)
    ):
        raise TicketError("partial assignment worktree is redirected")
    _verify_registered_worktree_identity(worktree, common_git_dir)
    _worktree_git(repo, "remove", "--force", str(worktree))
    _verify_worktree_absent(repo, worktree, ticket_path)
    return {
        "recovered_assignment_id": assignment_id,
        "recovery_status": "PARTIAL_WORKSPACE_CLEANED",
        "recovery_observation": "REGISTERED_WORKTREE_REMOVED",
    }


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


def _git_admin_reference(worktree: Path) -> Path:
    marker = worktree / ".git"
    if (
        not marker.is_file()
        or marker.is_symlink()
        or _is_reparse_point(marker)
    ):
        raise TicketError(f"isolated worktree has no .git file: {worktree}")
    text = marker.read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    if not text.lower().startswith(prefix):
        raise TicketError(f"invalid worktree .git marker: {marker}")
    raw = text[len(prefix) :].strip()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = marker.parent / candidate
    return candidate


def _git_admin_dir(worktree: Path) -> Path:
    candidate = _git_admin_reference(worktree)
    if candidate.is_symlink() or _is_reparse_point(candidate):
        raise TicketError("worktree git admin directory is redirected")
    return _canonical(candidate, label="worktree git admin directory")


def _verify_registered_worktree_identity(
    worktree: Path, common_git_dir: Path
) -> None:
    marker = worktree / ".git"
    admin = _git_admin_dir(worktree)
    linked_admin_root = _canonical(
        common_git_dir / "worktrees", label="linked-worktree admin root"
    )
    if not _same_path(admin.parent, linked_admin_root):
        raise TicketError("partial assignment git admin identity mismatch")

    backlink = admin / "gitdir"
    if (
        not backlink.is_file()
        or backlink.is_symlink()
        or _is_reparse_point(backlink)
    ):
        raise TicketError("partial assignment gitdir backlink is invalid")
    raw = backlink.read_text(encoding="utf-8").strip()
    backlink_target = Path(raw)
    if not backlink_target.is_absolute():
        backlink_target = admin / backlink_target
    resolved_target = _canonical(
        backlink_target, label="partial assignment gitdir backlink"
    )
    resolved_marker = _canonical(marker, label="partial assignment .git marker")
    if not _same_path(resolved_target, resolved_marker):
        raise TicketError("partial assignment gitdir backlink identity mismatch")


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
            *LONG_PATH_GIT_ARGS,
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
    common_git_dir = _common_git_dir(repo)
    ticket_path = _ticket_path(common_git_dir, assignment_id)
    if ticket_path.exists():
        raise TicketError(f"workspace ticket already exists: {ticket_path}")

    recovery: dict[str, str] = {}
    raw_recovery = getattr(args, "recover_partial_assignment", None)
    if raw_recovery is not None:
        recovery_assignment = _assignment_id(raw_recovery)
        if recovery_assignment == assignment_id:
            raise TicketError("new assignment must differ from recovered assignment")
        recovery = _recover_partial_assignment(
            repo, root, common_git_dir, recovery_assignment
        )

    try:
        _worktree_git(repo, "add", "--detach", str(worktree), expected_commit)
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
        try:
            _cleanup_current_attempt(repo, root, worktree, ticket_path)
        except (OSError, TicketError) as cleanup_exc:
            raise TicketError(
                f"provision failed and cleanup failed: {exc}; {cleanup_exc}"
            ) from exc
        if isinstance(exc, TicketError):
            raise
        raise TicketError(f"cannot write workspace ticket: {exc}") from exc
    return {
        "status": "WORKSPACE_TICKET_PROVISIONED",
        "ticket": str(ticket_path),
        **recovery,
        **payload,
    }


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
    provision.add_argument("--recover-partial-assignment")
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
