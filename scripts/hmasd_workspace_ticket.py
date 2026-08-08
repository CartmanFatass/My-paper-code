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
import tempfile
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


class IntegrationError(TicketError):
    """Typed, fail-closed integration error."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _git(root: Path, *args: str) -> str:
    git_args = list(args)
    if list(LONG_PATH_GIT_ARGS) not in [
        git_args[index : index + len(LONG_PATH_GIT_ARGS)]
        for index in range(max(0, len(git_args) - len(LONG_PATH_GIT_ARGS) + 1))
    ]:
        git_args = [*LONG_PATH_GIT_ARGS, *git_args]
    completed = subprocess.run(
        ["git", "-C", str(root), *git_args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise TicketError(f"git {' '.join(git_args)} failed: {detail}")
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
    ticket_path: Path, expected_assignment: str | None, *, allow_missing_worktree: bool = False
) -> tuple[dict[str, Any], Path, list[str]]:
    canonical_ticket = _canonical(ticket_path, label="workspace ticket")
    payload = _load_ticket(canonical_ticket, expected_assignment)
    raw_worktree = payload.get("resolved_worktree")
    if not isinstance(raw_worktree, str):
        raise TicketError("workspace ticket has no resolved_worktree")
    try:
        worktree = _canonical(Path(raw_worktree), label="ticket worktree")
    except TicketError:
        if not allow_missing_worktree:
            raise
        worktree = Path(raw_worktree).resolve(strict=False)
    if not _same_path(worktree, Path(raw_worktree)):
        raise TicketError("ticket worktree is not canonical")
    root = _worktree_root()
    if not _same_path(worktree.parent, root):
        raise TicketError("ticket worktree is outside the registered worktree root")

    recorded_admin = payload.get("git_admin_dir")
    if not isinstance(recorded_admin, str):
        raise TicketError("workspace ticket has no git_admin_dir")
    actual_admin = (
        Path(recorded_admin).resolve(strict=False)
        if allow_missing_worktree and not worktree.exists()
        else _git_admin_dir(worktree)
    )
    recorded_admin_path = (
        Path(recorded_admin).resolve(strict=False)
        if allow_missing_worktree and not worktree.exists()
        else _canonical(Path(recorded_admin), label="recorded git admin directory")
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
        "git_visible_changed_paths": changed_paths,
    }


INTEGRATION_SCHEMA_VERSION = 1
INTEGRATION_OPERATIONS = {"ADD", "MODIFY", "DELETE"}


def _integration_failure(code: str, detail: str) -> IntegrationError:
    return IntegrationError(code, detail)


def _status_entries(worktree: Path) -> list[tuple[str, str]]:
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
    result: list[tuple[str, str]] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4:
            raise TicketError("malformed git status entry")
        status = entry[:2].decode("ascii", errors="strict")
        path = entry[3:].decode("utf-8", errors="strict").replace("\\", "/")
        result.append((status, path))
        if "R" in status or "C" in status:
            if index >= len(entries) or not entries[index]:
                raise TicketError("malformed rename/copy status entry")
            result.append(
                (
                    status,
                    entries[index].decode("utf-8", errors="strict").replace("\\", "/"),
                )
            )
            index += 1
    return result


def _integration_status_entries(worktree: Path) -> list[tuple[str, str]]:
    try:
        return _status_entries(worktree)
    except TicketError as exc:
        raise _integration_failure("GIT_STATUS_FAILED", str(exc)) from exc


def _regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and not _is_reparse_point(path)


def _safe_descendant(root: Path, relative: str) -> Path:
    candidate = root / Path(relative)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise _integration_failure(
            "PATH_OUTSIDE_SCOPE", f"path escapes repository: {relative}"
        ) from exc
    current = candidate.parent
    while _same_path(current, root) is False:
        if current.is_symlink() or (current.exists() and _is_reparse_point(current)):
            raise _integration_failure(
                "PATH_REDIRECTED", f"path parent is redirected: {relative}"
            )
        current = current.parent
    if candidate.exists() and (candidate.is_symlink() or _is_reparse_point(candidate)):
        raise _integration_failure("PATH_REDIRECTED", f"path is redirected: {relative}")
    return candidate


def _source_operations(source: Path, allowed: list[str]) -> list[dict[str, str]]:
    entries = _integration_status_entries(source)
    changed = sorted({path for _status, path in entries})
    disallowed = [path for path in changed if not _is_allowed(path, allowed)]
    if disallowed:
        raise _integration_failure(
            "SOURCE_SCOPE_VIOLATION",
            "changed path outside ticket scope: " + ", ".join(disallowed),
        )
    operations: list[dict[str, str]] = []
    for status, relative in sorted(entries, key=lambda item: item[1]):
        if "R" in status or "C" in status:
            raise _integration_failure(
                "SOURCE_OPERATION_UNSUPPORTED",
                f"rename/copy is not a concrete regular-file operation: {relative}",
            )
        path = _safe_descendant(source, relative)
        deleted = "D" in status and not path.exists()
        if deleted:
            kind = "DELETE"
        elif not _regular_file(path):
            raise _integration_failure(
                "SOURCE_OPERATION_UNSUPPORTED",
                f"source path is not a concrete regular file: {relative}",
            )
        elif status == "??" or "A" in status:
            kind = "ADD"
        else:
            kind = "MODIFY"
        operations.append({"path": relative, "operation": kind})
    deduped: dict[str, dict[str, str]] = {}
    for operation in operations:
        previous = deduped.get(operation["path"])
        if previous is not None and previous["operation"] != operation["operation"]:
            raise _integration_failure(
                "SOURCE_OPERATION_UNSUPPORTED",
                f"conflicting status for source path: {operation['path']}",
            )
        deduped[operation["path"]] = operation
    return [deduped[path] for path in sorted(deduped)]


def _target_changed_paths(target: Path, base: str, head: str) -> list[str]:
    try:
        output = _git(target, "diff", "--name-only", "--no-renames", base, head, "--")
    except TicketError as exc:
        raise _integration_failure("TARGET_DIFF_FAILED", str(exc)) from exc
    return sorted(
        {
            line.replace("\\", "/")
            for line in output.splitlines()
            if line.strip()
        }
    )


def _target_head(target: Path, base: str) -> str:
    try:
        head = _git(target, "rev-parse", "HEAD")
    except TicketError as exc:
        raise _integration_failure("TARGET_INVALID", str(exc)) from exc
    try:
        _git(target, "merge-base", "--is-ancestor", base, head)
    except TicketError as exc:
        raise _integration_failure(
            "TARGET_HEAD_DIVERGENCE",
            f"ticket base is not an ancestor of target HEAD: {head}",
        ) from exc
    return head


def _operations_from_receipt(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise _integration_failure("RECEIPT_INVALID", "operations must be a list")
    operations: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise _integration_failure("RECEIPT_INVALID", "invalid integration operation")
        path = item.get("path")
        operation = item.get("operation", item.get("kind"))
        if not isinstance(path, str) or not isinstance(operation, str):
            raise _integration_failure("RECEIPT_INVALID", "invalid integration operation")
        try:
            normalized = _normalize_allowed(path)
        except TicketError as exc:
            raise _integration_failure("RECEIPT_INVALID", str(exc)) from exc
        if normalized != path or operation not in INTEGRATION_OPERATIONS:
            raise _integration_failure("RECEIPT_INVALID", "invalid integration operation")
        operations.append({"path": path, "operation": operation})
    if len({item["path"] for item in operations}) != len(operations):
        raise _integration_failure("RECEIPT_INVALID", "duplicate integration operation")
    return sorted(operations, key=lambda item: item["path"])


def _integration_context(
    ticket: Path,
    assignment_id: str | None,
    target_raw: Path,
    *,
    allow_target_allowed_dirty: bool = False,
) -> tuple[dict[str, Any], Path, list[str], Path, str, list[dict[str, str]], str]:
    try:
        payload, source, allowed = _resolve_payload(ticket, assignment_id)
    except IntegrationError:
        raise
    except TicketError as exc:
        raise _integration_failure("TICKET_INVALID", str(exc)) from exc
    try:
        target = _main_repository(target_raw)
    except TicketError as exc:
        raise _integration_failure("TARGET_INVALID", str(exc)) from exc
    if _same_path(source, target):
        raise _integration_failure("TARGET_INVALID", "source worktree and target repository must differ")
    try:
        base = payload["base_commit"]
        if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
            raise ValueError
        source_head = _git(source, "rev-parse", "HEAD")
    except (TicketError, ValueError) as exc:
        if isinstance(exc, TicketError):
            detail = str(exc)
        else:
            detail = "workspace ticket base commit is invalid"
        raise _integration_failure("SOURCE_DRIFT", detail) from exc
    if source_head != base:
        raise _integration_failure(
            "SOURCE_DRIFT", f"source HEAD drift: expected {base}, got {source_head}"
        )
    operations = _source_operations(source, allowed)
    head = _target_head(target, base)
    target_changed = _target_changed_paths(target, base, head)
    target_allowed_divergence = [
        path for path in target_changed if _is_allowed(path, allowed)
    ]
    if target_allowed_divergence:
        raise _integration_failure(
            "TARGET_ALLOWED_DIVERGENCE",
            "target changed an allowed path: " + ", ".join(target_allowed_divergence),
        )
    target_entries = _integration_status_entries(target)
    target_changed_worktree = sorted({path for _status, path in target_entries})
    target_allowed_dirty = [
        path for path in target_changed_worktree if _is_allowed(path, allowed)
    ]
    if target_allowed_dirty and not allow_target_allowed_dirty:
        raise _integration_failure(
            "TARGET_ALLOWED_DIRTY",
            "target allowed path is dirty: " + ", ".join(target_allowed_dirty),
        )
    return payload, source, allowed, target, base, operations, head


def _receipt_path(raw: Path) -> Path:
    candidate = raw.expanduser().resolve(strict=False)
    if candidate.exists() and candidate.is_dir():
        raise _integration_failure("RECEIPT_INVALID", "receipt path is a directory")
    if not candidate.parent.exists() or not candidate.parent.is_dir():
        raise _integration_failure("RECEIPT_INVALID", "receipt parent directory does not exist")
    return candidate


def _receipt_payload(
    *,
    status: str,
    operation: str,
    ticket: Path,
    source: Path,
    target: Path,
    base: str,
    prepared_head: str,
    allowed: list[str],
    operations: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": INTEGRATION_SCHEMA_VERSION,
        "operation": operation,
        "status": status,
        "assignment_id": None,
        "ticket": str(ticket),
        "source_worktree": str(source),
        "target_repo": str(target),
        "base_commit": base,
        "prepared_target_head": prepared_head,
        "allowed_paths": allowed,
        "concrete_changed_paths": [item["path"] for item in operations],
        "operations": operations,
    }


def _write_receipt(path: Path, payload: dict[str, Any]) -> None:
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    except OSError as exc:
        try:
            if "temporary" in locals() and temporary.exists():
                temporary.unlink()
        except OSError:
            pass
        raise _integration_failure("RECEIPT_WRITE_FAILED", str(exc)) from exc


def _load_integration_receipt(path: Path) -> tuple[dict[str, Any], Path]:
    receipt = _receipt_path(path)
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _integration_failure("RECEIPT_INVALID", str(exc)) from exc
    required = (
        "schema_version",
        "operation",
        "status",
        "assignment_id",
        "ticket",
        "source_worktree",
        "target_repo",
        "base_commit",
        "prepared_target_head",
        "allowed_paths",
        "concrete_changed_paths",
        "operations",
    )
    if any(key not in payload for key in required):
        raise _integration_failure("RECEIPT_INVALID", "receipt is missing required metadata")
    if payload["schema_version"] != INTEGRATION_SCHEMA_VERSION:
        raise _integration_failure("RECEIPT_INVALID", "unsupported integration receipt schema")
    if payload["operation"] != "prepare-integrate":
        raise _integration_failure("RECEIPT_INVALID", "receipt operation is not prepare-integrate")
    if payload["status"] not in {"WORKSPACE_INTEGRATION_READY", "WORKSPACE_INTEGRATED"}:
        raise _integration_failure("RECEIPT_INVALID", "receipt status is invalid")
    if not isinstance(payload["assignment_id"], str):
        raise _integration_failure("RECEIPT_INVALID", "receipt assignment_id is invalid")
    operations = _operations_from_receipt(payload["operations"])
    if payload["concrete_changed_paths"] != [item["path"] for item in operations]:
        raise _integration_failure("RECEIPT_INVALID", "receipt changed paths do not match operations")
    return payload, receipt


def _target_matches_operations(
    source: Path, target: Path, operations: list[dict[str, str]]
) -> bool:
    for item in operations:
        source_path = _safe_descendant(source, item["path"])
        target_path = _safe_descendant(target, item["path"])
        if item["operation"] == "DELETE":
            if target_path.exists() or target_path.is_symlink():
                return False
            continue
        if not _regular_file(source_path) or not _regular_file(target_path):
            return False
        try:
            if not _files_equal(source_path, target_path):
                return False
        except OSError:
            return False
    return True


def _files_equal(left: Path, right: Path) -> bool:
    with left.open("rb") as left_stream, right.open("rb") as right_stream:
        while True:
            left_chunk = left_stream.read(1024 * 1024)
            right_chunk = right_stream.read(1024 * 1024)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def _snapshot_target(
    target: Path, operations: list[dict[str, str]], temporary_root: Path
) -> list[tuple[Path, Path | None]]:
    snapshots: list[tuple[Path, Path | None]] = []
    for item in operations:
        target_path = _safe_descendant(target, item["path"])
        if target_path.exists() or target_path.is_symlink():
            if not _regular_file(target_path):
                raise _integration_failure(
                    "TARGET_OPERATION_UNSUPPORTED",
                    f"target path is not a regular file: {item['path']}",
                )
            backup = temporary_root / Path(item["path"])
            backup.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(target_path, backup)
            except OSError as exc:
                raise _integration_failure("INTEGRATION_PREPARE_FAILED", str(exc)) from exc
            snapshots.append((target_path, backup))
        else:
            snapshots.append((target_path, None))
    return snapshots


def _planned_target_directories(
    target: Path, operations: list[dict[str, str]]
) -> list[Path]:
    missing: set[Path] = set()
    for item in operations:
        current = (target / Path(item["path"])).parent
        while not _same_path(current, target):
            if not current.exists():
                missing.add(current)
            current = current.parent
    return sorted(missing, key=lambda path: len(path.parts), reverse=True)


def _restore_snapshot(
    snapshots: list[tuple[Path, Path | None]], created_dirs: list[Path]
) -> None:
    failures: list[str] = []
    for target_path, backup in reversed(snapshots):
        try:
            if backup is None:
                if target_path.exists() or target_path.is_symlink():
                    target_path.unlink()
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(backup, target_path)
        except OSError as exc:
            failures.append(f"{target_path}: {exc}")
    if failures:
        raise _integration_failure("INTEGRATION_ROLLBACK_FAILED", "; ".join(failures))
    for directory in created_dirs:
        try:
            if directory.is_dir() and not directory.is_symlink() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError as exc:
            failures.append(f"{directory}: {exc}")
    if failures:
        raise _integration_failure("INTEGRATION_ROLLBACK_FAILED", "; ".join(failures))


def prepare_integrate(args: argparse.Namespace) -> dict[str, Any]:
    receipt = _receipt_path(Path(args.receipt))
    target_raw = Path(getattr(args, "target_repo", getattr(args, "target", REGISTERED_REPOSITORY)))
    assignment_id = getattr(args, "assignment_id", None)
    try:
        payload, source, allowed, target, base, operations, head = _integration_context(
            Path(args.ticket), assignment_id, target_raw
        )
    except IntegrationError:
        raise
    receipt_payload = _receipt_payload(
        status="WORKSPACE_INTEGRATION_READY",
        operation="prepare-integrate",
        ticket=_canonical(Path(args.ticket), label="workspace ticket"),
        source=source,
        target=target,
        base=base,
        prepared_head=head,
        allowed=allowed,
        operations=operations,
    )
    receipt_payload["assignment_id"] = payload["assignment_id"]
    _write_receipt(receipt, receipt_payload)
    return {**receipt_payload, "receipt": str(receipt)}


def finalize_integrate(args: argparse.Namespace) -> dict[str, Any]:
    receipt_payload, receipt = _load_integration_receipt(Path(args.receipt))
    assignment_id = receipt_payload["assignment_id"]
    target_raw = Path(receipt_payload["target_repo"])
    ticket = Path(receipt_payload["ticket"])
    payload, source, allowed, target, base, operations, head = _integration_context(
        ticket, assignment_id, target_raw, allow_target_allowed_dirty=True
    )
    if str(source) != receipt_payload["source_worktree"] or str(target) != receipt_payload["target_repo"]:
        raise _integration_failure("RECEIPT_INVALID", "receipt repository identity changed")
    if base != receipt_payload["base_commit"] or allowed != receipt_payload["allowed_paths"]:
        raise _integration_failure("RECEIPT_INVALID", "receipt ticket metadata changed")
    if operations != _operations_from_receipt(receipt_payload["operations"]):
        raise _integration_failure("SOURCE_DRIFT", "source operations changed after prepare")

    target_entries = _integration_status_entries(target)
    target_dirty = sorted({path for _status, path in target_entries if _is_allowed(path, allowed)})
    if receipt_payload["status"] == "WORKSPACE_INTEGRATED" and not target_dirty:
        if _target_matches_operations(source, target, operations):
            return {
                **receipt_payload,
                "operation": "finalize-integrate",
                "status": "WORKSPACE_ALREADY_INTEGRATED",
                "receipt": str(receipt),
            }
        raise _integration_failure(
            "INTEGRATION_VERIFY_FAILED",
            "integrated receipt no longer matches the source and target files",
        )
    if target_dirty:
        if operations and _target_matches_operations(source, target, operations):
            return {
                **receipt_payload,
                "operation": "finalize-integrate",
                "status": "WORKSPACE_ALREADY_INTEGRATED",
                "receipt": str(receipt),
            }
        raise _integration_failure(
            "TARGET_ALLOWED_DIRTY",
            "target allowed path is dirty: " + ", ".join(target_dirty),
        )

    with tempfile.TemporaryDirectory(prefix="hmasd-ticket-integrate-") as temporary:
        snapshots: list[tuple[Path, Path | None]] = []
        created_dirs = _planned_target_directories(target, operations)
        try:
            snapshots = _snapshot_target(target, operations, Path(temporary))
            for item in operations:
                source_path = _safe_descendant(source, item["path"])
                target_path = _safe_descendant(target, item["path"])
                if item["operation"] == "DELETE":
                    if target_path.exists() or target_path.is_symlink():
                        target_path.unlink()
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source_path, target_path)
            if not _target_matches_operations(source, target, operations):
                raise _integration_failure(
                    "INTEGRATION_VERIFY_FAILED", "integrated files do not match source"
                )
            integrated_payload = dict(receipt_payload)
            integrated_payload["status"] = "WORKSPACE_INTEGRATED"
            _write_receipt(receipt, integrated_payload)
        except IntegrationError:
            try:
                _restore_snapshot(snapshots, created_dirs)
            except IntegrationError:
                raise
            raise
        except OSError as exc:
            try:
                _restore_snapshot(snapshots, created_dirs)
            except IntegrationError:
                raise
            raise _integration_failure("INTEGRATION_FAILED", str(exc)) from exc

    return {
        **integrated_payload,
        "operation": "finalize-integrate",
        "status": "WORKSPACE_INTEGRATED",
        "receipt": str(receipt),
    }


def _expected_head(raw: str) -> str:
    expected = raw.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise TicketError("expected head must be exactly forty lowercase hexadecimal characters")
    return expected


def _retire_removed_ticket(args: argparse.Namespace) -> dict[str, Any]:
    payload, worktree, _allowed = _resolve_payload(
        args.ticket, args.assignment_id, allow_missing_worktree=True
    )
    if worktree.exists() or worktree.is_symlink():
        raise TicketError("retire retry requires the registered worktree to be absent")
    repo = _main_repository(REGISTERED_REPOSITORY)
    if _worktree_is_registered(repo, worktree):
        raise TicketError("retire retry requires registered worktree state to be absent")
    expected = _expected_head(args.expected_head)
    try:
        _git(repo, "merge-base", "--is-ancestor", payload["base_commit"], expected)
    except TicketError as exc:
        raise TicketError("ticket base is not an ancestor of expected head") from exc
    ticket_path = _canonical(args.ticket, label="workspace ticket")
    try:
        ticket_path.unlink()
    except OSError as exc:
        raise TicketError(f"cannot remove workspace ticket after worktree removal: {exc}") from exc
    _verify_worktree_absent(repo, worktree, ticket_path)
    return {
        "status": "WORKSPACE_TICKET_RETIRED",
        "assignment_id": payload["assignment_id"],
        "resolved_worktree": str(worktree),
        "expected_head": expected,
        "git_visible_changed_paths": [],
        "retry": True,
    }


def retire_ticket(args: argparse.Namespace) -> dict[str, Any]:
    expected = _expected_head(args.expected_head)
    try:
        payload, worktree, allowed = _resolve_payload(args.ticket, args.assignment_id)
    except TicketError:
        return _retire_removed_ticket(args)

    repo = _main_repository(REGISTERED_REPOSITORY)
    actual_head = _git(worktree, "rev-parse", "HEAD")
    if actual_head != expected:
        raise TicketError(f"expected HEAD mismatch: expected {expected}, got {actual_head}")
    if _git(worktree, "rev-parse", "--abbrev-ref", "HEAD") != "HEAD":
        raise TicketError("retire requires a detached HEAD")
    try:
        _git(worktree, "merge-base", "--is-ancestor", payload["base_commit"], expected)
    except TicketError as exc:
        raise TicketError("ticket base is not an ancestor of expected head") from exc
    changed_paths = _status_paths(worktree)
    if changed_paths:
        raise TicketError("cannot retire dirty worktree; git-visible paths: " + ", ".join(changed_paths))
    _verify_registered_worktree_identity(worktree, _common_git_dir(repo))
    _worktree_git(repo, "remove", str(worktree))
    if worktree.exists() or _worktree_is_registered(repo, worktree):
        raise TicketError("retire did not remove the registered worktree")
    ticket_path = _canonical(args.ticket, label="workspace ticket")
    try:
        ticket_path.unlink()
    except OSError as exc:
        raise TicketError(
            f"worktree retired but ticket removal failed; retry retire: {exc}"
        ) from exc
    _verify_worktree_absent(repo, worktree, ticket_path)
    return {
        "status": "WORKSPACE_TICKET_RETIRED",
        "assignment_id": payload["assignment_id"],
        "resolved_worktree": str(worktree),
        "expected_head": expected,
        "git_visible_changed_paths": [],
        "retry": False,
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
    retire = subparsers.add_parser("retire")
    retire.add_argument("--ticket", type=Path, required=True)
    retire.add_argument("--assignment-id", required=True)
    retire.add_argument("--expected-head", required=True)
    retire.set_defaults(handler=retire_ticket)
    prepare = subparsers.add_parser("prepare-integrate")
    prepare.add_argument("--ticket", type=Path, required=True)
    prepare.add_argument("--assignment-id", required=True)
    prepare.add_argument("--target-repo", type=Path, required=True)
    prepare.add_argument("--receipt", type=Path, required=True)
    prepare.set_defaults(handler=prepare_integrate)
    finalize = subparsers.add_parser("finalize-integrate")
    finalize.add_argument("--receipt", type=Path, required=True)
    finalize.set_defaults(handler=finalize_integrate)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = args.handler(args)
    except IntegrationError as exc:
        print(f"WORKSPACE_TICKET_ERROR {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    except TicketError as exc:
        print(f"WORKSPACE_TICKET_ERROR {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
