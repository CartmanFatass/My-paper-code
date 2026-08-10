"""Root-owned lifecycle helper for one explicitly managed Git worktree.

This module deliberately has no ticket compatibility layer and no inventory,
prune, repair, or background behaviour.  Every operation names exactly one
repository, one destination, one receipt, and one assignment.  The helper is
intended to be called by Root; the ``actor`` guard is therefore part of the
model and the command line interface.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


SCHEMA = "hmasd.root-managed-worktree/v1"
WORKTREE_ID = "hmasd-root-managed-v1"
TERMINAL_STATUSES = {"RELEASED", "RETAINED_FOR_RECOVERY"}
NONTERMINAL_STATUSES = {
    "PROVISIONED",
    "CANDIDATE_RECORDED",
    "FAILED",
}
IGNORED_DISPOSITIONS = {"relayed", "archived", "disposable"}
_SAFE_ASSIGNMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_FULL_COMMIT = re.compile(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}\Z")
_REPARSE_POINT = 0x0400


class WorktreeError(RuntimeError):
    """A validation, identity, lifecycle, or safe-postcondition failure."""


class WorktreeRefusal(WorktreeError):
    """The requested lifecycle action is unsafe in the observed state."""


def _now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _has_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & _REPARSE_POINT)


def _absolute_no_alias(value: os.PathLike[str] | str, *, label: str, must_exist: bool = False) -> Path:
    raw = os.fspath(value)
    path = Path(raw)
    if not path.is_absolute():
        raise WorktreeError(f"{label} must be absolute")
    if any(part in {".", ".."} for part in path.parts):
        raise WorktreeError(f"{label} contains an alias component")
    if _has_reparse(path):
        raise WorktreeError(f"{label} is a reparse point or symlink")
    if must_exist and not path.exists():
        raise WorktreeError(f"{label} does not exist: {path}")
    if path.exists():
        resolved = path.resolve(strict=True)
        if not _same_path(path, resolved):
            raise WorktreeError(f"{label} is an alias")
        # Verify each existing ancestor.  This catches junctions/symlinks in
        # an otherwise ordinary-looking destination on Windows and POSIX.
        current = path
        while current != current.parent:
            if current.exists() and _has_reparse(current):
                raise WorktreeError(f"{label} has a reparse-point ancestor")
            current = current.parent
    else:
        parent = path.parent
        if not parent.exists():
            raise WorktreeError(f"{label} parent does not exist: {parent}")
        parent_resolved = parent.resolve(strict=True)
        if not _same_path(parent, parent_resolved):
            raise WorktreeError(f"{label} parent is an alias")
        current = parent
        while current != current.parent:
            if current.exists() and _has_reparse(current):
                raise WorktreeError(f"{label} has a reparse-point ancestor")
            current = current.parent
    if must_exist and not path.is_dir():
        raise WorktreeError(f"{label} is not a directory: {path}")
    return path


def _validate_assignment(assignment_id: str) -> str:
    if not isinstance(assignment_id, str) or not _SAFE_ASSIGNMENT.fullmatch(assignment_id):
        raise WorktreeError("assignment_id is not a safe identifier")
    if assignment_id in {".", ".."} or assignment_id.startswith("-"):
        raise WorktreeError("assignment_id is not a safe identifier")
    return assignment_id


def _validate_commit(commit: str, label: str = "commit") -> str:
    if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit):
        raise WorktreeError(f"{label} must be a full commit id")
    return commit.lower()


def _run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["git", *args]
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise WorktreeError(f"git {' '.join(args)} failed: {detail}")
    return result


def _git_value(cwd: Path, *args: str) -> str:
    result = _run(cwd, *args)
    return result.stdout.strip()


def _repo_context(repo_top: Path, git_common_dir: Path) -> tuple[Path, Path]:
    repo_top = _absolute_no_alias(repo_top, label="repo_top", must_exist=True)
    git_common_dir = _absolute_no_alias(git_common_dir, label="git_common_dir", must_exist=True)
    actual_top = _absolute_no_alias(_git_value(repo_top, "rev-parse", "--show-toplevel"), label="actual repository top", must_exist=True)
    actual_common_raw = _git_value(repo_top, "rev-parse", "--git-common-dir")
    actual_common = Path(actual_common_raw)
    if not actual_common.is_absolute():
        actual_common = repo_top / actual_common
    actual_common = _absolute_no_alias(actual_common, label="actual common Git dir", must_exist=True)
    if not _same_path(repo_top, actual_top):
        raise WorktreeError("repo_top is not the exact Git top-level path")
    if not _same_path(git_common_dir, actual_common):
        raise WorktreeError("git_common_dir is not the exact common Git directory")
    if _git_value(repo_top, "rev-parse", "--is-bare-repository").lower() != "false":
        raise WorktreeError("a bare repository cannot host this managed worktree")
    return actual_top, actual_common


def _validate_destination(destination: Path, repo_top: Path, common_dir: Path, *, must_exist: bool) -> Path:
    destination = _absolute_no_alias(destination, label="managed_path", must_exist=must_exist)
    if _same_path(destination, repo_top) or _same_path(destination, common_dir):
        raise WorktreeError("managed_path cannot be the repository or common Git directory")
    try:
        if os.path.commonpath([str(destination), str(repo_top)]) == str(repo_top):
            raise WorktreeError("managed_path cannot be inside the repository top")
        if os.path.commonpath([str(destination), str(common_dir)]) == str(common_dir):
            raise WorktreeError("managed_path cannot be inside the common Git directory")
    except ValueError:
        pass
    return destination


def _receipt_path(path: os.PathLike[str] | str, managed: Path) -> Path:
    raw = os.fspath(path)
    receipt = Path(raw)
    if not receipt.is_absolute():
        raise WorktreeError("receipt_path must be absolute")
    if any(part in {".", ".."} for part in receipt.parts):
        raise WorktreeError("receipt_path contains an alias component")
    if receipt.exists():
        receipt = _absolute_no_alias(receipt, label="receipt_path")
    else:
        # Receipt parents are created atomically with the first receipt.  The
        # nearest existing ancestor is still checked for aliases/reparse
        # points before any directory is created.
        anchor = receipt.parent
        while not anchor.exists() and anchor != anchor.parent:
            anchor = anchor.parent
        if not anchor.exists():
            raise WorktreeError("receipt_path has no existing safe ancestor")
        _absolute_no_alias(anchor, label="receipt_path parent", must_exist=True)
    if receipt.exists() and receipt.is_dir():
        raise WorktreeError("receipt_path must be a file")
    # A receipt in the checkout would be removed with the checkout and could
    # not remain durable creation evidence.
    try:
        if os.path.commonpath([str(receipt), str(managed)]) == str(managed):
            raise WorktreeError("receipt_path cannot be inside managed_path")
    except ValueError:
        pass
    return receipt


def _verify_base(repo_top: Path, base_commit: str) -> str:
    base = _validate_commit(base_commit, "base_commit")
    actual = _git_value(repo_top, "rev-parse", "--verify", f"{base}^{{commit}}").lower()
    if actual != base:
        raise WorktreeError("base_commit is not the exact existing commit")
    return base


def _worktrees(repo_top: Path) -> list[dict[str, Any]]:
    result = _run(repo_top, "worktree", "list", "--porcelain")
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in result.stdout.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):].strip().lower()
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):].strip()
    for record in records:
        raw = record.get("path")
        if raw:
            path = Path(raw)
            if path.is_absolute():
                try:
                    record["canonical_path"] = path.resolve(strict=False)
                except OSError:
                    record["canonical_path"] = path
    return records


def _registered(repo_top: Path, managed: Path) -> dict[str, Any]:
    matches = [r for r in _worktrees(repo_top) if _same_path(r.get("canonical_path", Path("")), managed)]
    if len(matches) != 1:
        raise WorktreeError("managed_path does not have exactly one registered Git worktree")
    record = matches[0]
    if not record.get("detached") or not record.get("head"):
        raise WorktreeError("managed worktree is not registered detached")
    return record


def _status(managed: Path) -> dict[str, Any]:
    result = _run(managed, "status", "--porcelain=v1", "--ignored", "--untracked-files=all", "-z")
    entries = result.stdout.split("\0")
    tracked_dirty: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []
    for entry in entries:
        if not entry:
            continue
        if len(entry) < 3:
            tracked_dirty.append(entry)
            continue
        code, path = entry[:2], entry[3:]
        if code == "!!":
            ignored.append(path)
        elif code == "??":
            untracked.append(path)
        else:
            tracked_dirty.append(path)
    return {
        "tracked_dirty": tracked_dirty,
        "nonignored_untracked": untracked,
        "ignored_only": ignored,
        "clean": not tracked_dirty and not untracked and not ignored,
    }


def _refs_containing(repo_top: Path, commit: str) -> list[str]:
    result = _run(repo_top, "for-each-ref", "--format=%(refname)", "--contains", commit)
    return sorted(x.strip() for x in result.stdout.splitlines() if x.strip())


def _candidate_observation(repo_top: Path, managed: Path, receipt: Mapping[str, Any], registered: Mapping[str, Any]) -> dict[str, Any]:
    candidate = receipt.get("candidate_commit")
    if not candidate:
        return {
            "candidate_commit": None,
            "candidate_reachable": None,
            "candidate_unique": False,
            "candidate_refs": [],
            "candidate_mismatch": False,
        }
    candidate = str(candidate).lower()
    head = _git_value(managed, "rev-parse", "--verify", "HEAD").lower()
    reachable = False
    exists = bool(_run(repo_top, "cat-file", "-e", f"{candidate}^{{commit}}", check=False).returncode == 0)
    if exists:
        reachable = head == candidate and registered.get("head", "").lower() == candidate
    refs = _refs_containing(repo_top, candidate) if exists else []
    recovery = receipt.get("recovery_ref")
    external_refs = [ref for ref in refs if ref != recovery]
    return {
        "candidate_commit": candidate,
        "candidate_reachable": reachable,
        "candidate_unique": bool(exists and not external_refs),
        "candidate_refs": refs,
        "candidate_mismatch": not reachable,
    }


def _creation_evidence(receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    evidence = receipt.get("creation_evidence")
    if not isinstance(evidence, dict):
        raise WorktreeError("receipt lacks creation evidence")
    expected = receipt.get("creation_evidence_sha256")
    if not isinstance(expected, str) or _digest(evidence) != expected:
        raise WorktreeError("receipt creation evidence is not immutable")
    return evidence


def _load_receipt(path: Path, assignment_id: str, managed: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise WorktreeError(f"receipt does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8") as stream:
            receipt = json.load(stream)
    except (OSError, ValueError) as exc:
        raise WorktreeError(f"receipt is unreadable: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise WorktreeError("receipt schema is invalid")
    if receipt.get("assignment_id") != assignment_id:
        raise WorktreeError("receipt assignment_id mismatch")
    if not _same_path(Path(str(receipt.get("managed_path", ""))), managed):
        raise WorktreeError("receipt managed_path mismatch")
    _creation_evidence(receipt)
    status = receipt.get("status")
    if status not in NONTERMINAL_STATUSES | TERMINAL_STATUSES:
        raise WorktreeError("receipt status is invalid")
    pending = receipt.get("pending_action")
    if pending is not None:
        if not isinstance(pending, dict) or pending.get("operation") not in {"release", "retain"}:
            raise WorktreeError("receipt pending_action is invalid")
        if pending.get("terminal_status") not in TERMINAL_STATUSES:
            raise WorktreeError("receipt pending_action terminal status is invalid")
        if status in TERMINAL_STATUSES:
            raise WorktreeError("terminal receipt cannot carry a pending action")
    return receipt


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _registration_count(repo_top: Path, managed: Path) -> int:
    return sum(1 for record in _worktrees(repo_top) if _same_path(record.get("canonical_path", Path("")), managed))


def _reconcile_pending(
    top: Path,
    common: Path,
    managed: Path,
    receipt_path: Path,
    receipt: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Finalize only a durable intent whose two absence postconditions hold.

    This is deliberately an exact-path check.  It does not search for another
    workspace and never removes or edits a registration other than the named
    one.  A pending retain additionally requires its recovery ref to exist.
    """
    pending = receipt.get("pending_action")
    if not pending:
        return receipt, False
    if not _same_path(Path(str(receipt.get("git_top", ""))), top) or not _same_path(Path(str(receipt.get("git_common_dir", ""))), common):
        raise WorktreeError("pending receipt repository identity mismatch")
    evidence = _creation_evidence(receipt)
    if not _same_path(Path(str(evidence.get("git_top", ""))), top) or not _same_path(Path(str(evidence.get("git_common_dir", ""))), common):
        raise WorktreeError("pending receipt creation repository identity mismatch")
    registered_count = _registration_count(top, managed)
    if managed.exists() or registered_count:
        return receipt, False
    operation = pending["operation"]
    if operation == "retain":
        recovery_ref = pending.get("recovery_ref")
        candidate = str(receipt.get("candidate_commit") or "").lower()
        if not recovery_ref or not candidate:
            raise WorktreeError("pending retain lacks candidate recovery evidence")
        protected = _run(top, "rev-parse", "--verify", "--quiet", str(recovery_ref), check=False)
        if protected.returncode != 0 or protected.stdout.strip().lower() != candidate:
            raise WorktreeError("pending retain recovery ref is absent or mismatched")
    updated = dict(receipt)
    updated["status"] = pending["terminal_status"]
    updated["pending_action"] = None
    updated["checkout_removed"] = True
    updated["reconciled_at"] = _now()
    updated["last_failure"] = None
    _write_receipt(receipt_path, updated)
    return updated, True


def _failure(path: Path, receipt: Optional[dict[str, Any]], message: str) -> None:
    if receipt is None:
        return
    updated = dict(receipt)
    updated["status"] = receipt.get("status", "FAILED") if receipt.get("status") in NONTERMINAL_STATUSES else "FAILED"
    updated["last_failure"] = {"at": _now(), "message": message}
    try:
        _write_receipt(path, updated)
    except OSError:
        # The original safety failure is more useful to the caller; receipt
        # write failure is reported in that same exception text by the CLI.
        pass


def _validate_registered_context(repo_top: Path, common_dir: Path, managed: Path, receipt: Mapping[str, Any], *, allow_unrecorded_head: bool = False) -> dict[str, Any]:
    expected_top = Path(str(receipt.get("git_top", "")))
    expected_common = Path(str(receipt.get("git_common_dir", "")))
    if not _same_path(expected_top, repo_top) or not _same_path(expected_common, common_dir):
        raise WorktreeError("receipt repository identity mismatch")
    evidence = _creation_evidence(receipt)
    if not _same_path(Path(str(evidence.get("managed_path", ""))), managed):
        raise WorktreeError("receipt creation managed_path mismatch")
    if not _same_path(Path(str(evidence.get("git_top", ""))), repo_top) or not _same_path(Path(str(evidence.get("git_common_dir", ""))), common_dir):
        raise WorktreeError("receipt creation repository identity mismatch")
    if not managed.exists() or not managed.is_dir():
        raise WorktreeError("managed checkout is absent")
    _validate_destination(managed, repo_top, common_dir, must_exist=True)
    registered = _registered(repo_top, managed)
    actual_top, actual_common = _repo_context(managed, common_dir)
    if not _same_path(actual_top, managed) or not _same_path(actual_common, common_dir):
        raise WorktreeError("managed checkout Git identity mismatch")
    head = _git_value(managed, "rev-parse", "--verify", "HEAD").lower()
    if registered.get("head") != head:
        raise WorktreeError("receipt/worktree HEAD agreement is absent")
    if receipt.get("candidate_commit"):
        if head != str(receipt["candidate_commit"]).lower():
            raise WorktreeError("receipt/worktree candidate agreement is absent")
    elif not allow_unrecorded_head and head != str(receipt.get("base_commit", "")).lower():
        raise WorktreeError("receipt/worktree base agreement is absent")
    return registered


def _audit_loaded(repo_top: Path, common_dir: Path, managed: Path, receipt: dict[str, Any], *, in_use: bool = False, ignored_disposition: Optional[str] = None) -> dict[str, Any]:
    registered = _validate_registered_context(repo_top, common_dir, managed, receipt)
    state = _status(managed)
    candidate = _candidate_observation(repo_top, managed, receipt, registered)
    if ignored_disposition is not None and ignored_disposition not in IGNORED_DISPOSITIONS:
        raise WorktreeError("ignored disposition must be relayed, archived, or disposable")
    disposition_required = bool(state["ignored_only"] and ignored_disposition is None)
    report = {
        "schema": SCHEMA,
        "assignment_id": receipt["assignment_id"],
        "status": receipt["status"],
        "registered": True,
        "detached": bool(registered.get("detached")),
        "in_use": bool(in_use),
        "tracked_dirty": state["tracked_dirty"],
        "nonignored_untracked": state["nonignored_untracked"],
        "ignored_only": state["ignored_only"],
        "ignored_disposition": ignored_disposition,
        "ignored_disposition_required": disposition_required,
        "pending_action": receipt.get("pending_action"),
        **candidate,
        "cleanup_safe": not state["tracked_dirty"] and not state["nonignored_untracked"] and not in_use and not candidate["candidate_mismatch"] and not disposition_required,
    }
    return report


def _common_inputs(repo_top: os.PathLike[str] | str, git_common_dir: os.PathLike[str] | str, managed_path: os.PathLike[str] | str, receipt_path: os.PathLike[str] | str, assignment_id: str) -> tuple[Path, Path, Path, Path, str]:
    assignment = _validate_assignment(assignment_id)
    top, common = _repo_context(Path(repo_top), Path(git_common_dir))
    managed = Path(os.fspath(managed_path))
    receipt = _receipt_path(receipt_path, managed)
    return top, common, managed, receipt, assignment


def provision_worktree(
    *,
    repo_top: os.PathLike[str] | str,
    git_common_dir: os.PathLike[str] | str,
    managed_path: os.PathLike[str] | str,
    receipt_path: os.PathLike[str] | str,
    assignment_id: str,
    base_commit: str,
    actor: str = "root",
) -> dict[str, Any]:
    _require_root(actor)
    top, common, managed, receipt_path, assignment = _common_inputs(repo_top, git_common_dir, managed_path, receipt_path, assignment_id)
    if receipt_path.exists():
        raise WorktreeRefusal("a receipt already exists for this assignment; one nonterminal receipt is allowed")
    _validate_destination(managed, top, common, must_exist=False)
    if managed.exists():
        raise WorktreeRefusal("managed_path already exists")
    base = _verify_base(top, base_commit)
    if any(_same_path(r.get("canonical_path", Path("")), managed) for r in _worktrees(top)):
        raise WorktreeRefusal("managed_path is already registered as a Git worktree")
    created = False
    try:
        _run(top, "worktree", "add", "--detach", str(managed), base)
        created = True
        registered = _registered(top, managed)
        actual_top, actual_common = _repo_context(managed, common)
        if not _same_path(actual_top, managed) or not _same_path(actual_common, common):
            raise WorktreeError("created worktree repository identity mismatch")
        head = _git_value(managed, "rev-parse", "--verify", "HEAD").lower()
        state = _status(managed)
        if not registered.get("detached") or head != base or not state["clean"]:
            raise WorktreeError("created worktree was not detached and clean at the exact base")
        evidence = {
            "worktree_id": WORKTREE_ID,
            "assignment_id": assignment,
            "managed_path": str(managed),
            "git_top": str(top),
            "git_common_dir": str(common),
            "base_commit": base,
            "detached": True,
            "clean_at_creation": True,
            "created_at": _now(),
        }
        receipt = {
            "schema": SCHEMA,
            "worktree_id": WORKTREE_ID,
            "assignment_id": assignment,
            "managed_path": str(managed),
            "receipt_path": str(receipt_path),
            "git_top": str(top),
            "git_common_dir": str(common),
            "base_commit": base,
            "candidate_commit": None,
            "recovery_ref": None,
            "pending_action": None,
            "status": "PROVISIONED",
            "created_at": evidence["created_at"],
            "creation_evidence": evidence,
            "creation_evidence_sha256": _digest(evidence),
            "last_failure": None,
            "last_audit": None,
        }
        _write_receipt(receipt_path, receipt)
        return {"ok": True, "operation": "provision", "receipt": receipt}
    except Exception as exc:
        if created:
            try:
                _run(top, "worktree", "remove", "--force", str(managed))
            except Exception:
                pass
        raise WorktreeError(str(exc)) from exc


def audit_worktree(
    *,
    repo_top: os.PathLike[str] | str,
    git_common_dir: os.PathLike[str] | str,
    managed_path: os.PathLike[str] | str,
    receipt_path: os.PathLike[str] | str,
    assignment_id: str,
    actor: str = "root",
    in_use: bool = False,
    ignored_disposition: Optional[str] = None,
) -> dict[str, Any]:
    _require_root(actor)
    top, common, managed, receipt_path, assignment = _common_inputs(repo_top, git_common_dir, managed_path, receipt_path, assignment_id)
    receipt = _load_receipt(receipt_path, assignment, managed)
    receipt, _ = _reconcile_pending(top, common, managed, receipt_path, receipt)
    if receipt["status"] in TERMINAL_STATUSES:
        if managed.exists() or _registration_count(top, managed):
            raise WorktreeError("terminal receipt still has a live checkout or registration")
        return {"ok": True, "operation": "audit", "terminal": True, "status": receipt["status"]}
    report = _audit_loaded(top, common, managed, receipt, in_use=in_use, ignored_disposition=ignored_disposition)
    updated = dict(receipt)
    updated["last_audit"] = {"at": _now(), "report": report}
    _write_receipt(receipt_path, updated)
    return {"ok": True, "operation": "audit", "report": report}


def record_candidate(
    *,
    repo_top: os.PathLike[str] | str,
    git_common_dir: os.PathLike[str] | str,
    managed_path: os.PathLike[str] | str,
    receipt_path: os.PathLike[str] | str,
    assignment_id: str,
    candidate_commit: str,
    actor: str = "root",
) -> dict[str, Any]:
    _require_root(actor)
    top, common, managed, receipt_path, assignment = _common_inputs(repo_top, git_common_dir, managed_path, receipt_path, assignment_id)
    receipt = _load_receipt(receipt_path, assignment, managed)
    if receipt["status"] in TERMINAL_STATUSES:
        raise WorktreeRefusal("terminal receipt cannot record a candidate")
    registered = _validate_registered_context(top, common, managed, receipt, allow_unrecorded_head=True)
    candidate = _validate_commit(candidate_commit, "candidate_commit")
    head = _git_value(managed, "rev-parse", "--verify", "HEAD").lower()
    if candidate != head or registered.get("head") != candidate:
        _failure(receipt_path, receipt, "candidate commit does not exactly match registered worktree HEAD")
        raise WorktreeRefusal("candidate commit must exactly match the Root-created worktree HEAD")
    if candidate == str(receipt["base_commit"]).lower():
        raise WorktreeRefusal("base commit cannot be recorded as a candidate")
    if not _run(top, "cat-file", "-e", f"{candidate}^{{commit}}", check=False).returncode == 0:
        raise WorktreeRefusal("candidate commit does not exist")
    updated = dict(receipt)
    updated["candidate_commit"] = candidate
    updated["status"] = "CANDIDATE_RECORDED"
    updated["last_failure"] = None
    _write_receipt(receipt_path, updated)
    return {"ok": True, "operation": "record-candidate", "candidate_commit": candidate, "receipt": updated}


def _prepare_cleanup(
    *,
    top: Path,
    common: Path,
    managed: Path,
    receipt_path: Path,
    receipt: dict[str, Any],
    in_use: bool,
    ignored_disposition: Optional[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if receipt["status"] in TERMINAL_STATUSES:
        raise WorktreeRefusal("receipt is already terminal")
    report = _audit_loaded(top, common, managed, receipt, in_use=in_use, ignored_disposition=ignored_disposition)
    if report["tracked_dirty"]:
        raise WorktreeRefusal("release refused: tracked files are dirty")
    if report["nonignored_untracked"]:
        raise WorktreeRefusal("release refused: nonignored untracked files exist")
    if report["in_use"]:
        raise WorktreeRefusal("release refused: workspace is active/in use")
    if report["candidate_mismatch"]:
        raise WorktreeRefusal("release refused: candidate/receipt/worktree mismatch")
    if report["ignored_disposition_required"]:
        raise WorktreeRefusal("release refused: ignored artifacts require an explicit disposition")
    return report, dict(receipt)


def _remove_checkout(top: Path, managed: Path, *, force: bool) -> None:
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(managed))
    _run(top, *args)
    if managed.exists():
        raise WorktreeError("Git reported removal but the managed checkout remains")
    if any(_same_path(r.get("canonical_path", Path("")), managed) for r in _worktrees(top)):
        raise WorktreeError("Git registration remains after checkout removal")


def release_worktree(
    *,
    repo_top: os.PathLike[str] | str,
    git_common_dir: os.PathLike[str] | str,
    managed_path: os.PathLike[str] | str,
    receipt_path: os.PathLike[str] | str,
    assignment_id: str,
    actor: str = "root",
    accepted: bool = False,
    in_use: bool = False,
    ignored_disposition: Optional[str] = None,
) -> dict[str, Any]:
    _require_root(actor)
    top, common, managed, receipt_path, assignment = _common_inputs(repo_top, git_common_dir, managed_path, receipt_path, assignment_id)
    receipt = _load_receipt(receipt_path, assignment, managed)
    receipt, _ = _reconcile_pending(top, common, managed, receipt_path, receipt)
    if receipt["status"] in TERMINAL_STATUSES:
        if managed.exists() or _registration_count(top, managed):
            raise WorktreeError("terminal receipt still has a live checkout or registration")
        return {"ok": True, "operation": "release", "status": receipt["status"], "receipt": receipt}
    pending_receipt: Optional[dict[str, Any]] = None
    try:
        pending = receipt.get("pending_action")
        if pending and pending.get("operation") != "release":
            raise WorktreeRefusal("a different terminal action is already pending")
        report, updated = _prepare_cleanup(top=top, common=common, managed=managed, receipt_path=receipt_path, receipt=receipt, in_use=in_use, ignored_disposition=ignored_disposition)
        candidate = report.get("candidate_commit")
        if candidate:
            if not accepted:
                raise WorktreeRefusal("release refused: candidate requires accepted-needed integration")
            if report["candidate_unique"]:
                raise WorktreeRefusal("release refused: candidate is uniquely unprotected")
        elif ignored_disposition != "disposable" and report["ignored_only"]:
            raise WorktreeRefusal("release refused: ignored artifacts need disposable or explicit retained handling")
        # An actually empty checkout has no evidence to dispose.  An
        # ignored-only checkout, by contrast, must carry the explicit Root
        # disposition handled above.
        updated["pending_action"] = {
            "operation": "release",
            "terminal_status": "RELEASED",
            "requested_at": _now(),
        }
        _write_receipt(receipt_path, updated)
        pending_receipt = dict(updated)
        _remove_checkout(top, managed, force=bool(report["ignored_only"]))
        updated["status"] = "RELEASED"
        updated["pending_action"] = None
        updated["last_audit"] = {"at": _now(), "report": report}
        updated["released_at"] = _now()
        updated["last_failure"] = None
        _write_receipt(receipt_path, updated)
        return {"ok": True, "operation": "release", "status": "RELEASED", "receipt": updated}
    except Exception as exc:
        _failure(receipt_path, pending_receipt or receipt, str(exc))
        if isinstance(exc, WorktreeError):
            raise
        raise WorktreeError(str(exc)) from exc


def _recovery_ref(assignment: str) -> str:
    return f"refs/hmasd/root-managed-recovery/{assignment}"


def _ensure_recovery_ref(top: Path, recovery_ref: str, candidate: str) -> None:
    """Create the expected ref without replacing a concurrent other value."""
    existing = _run(top, "rev-parse", "--verify", "--quiet", recovery_ref, check=False)
    if existing.returncode == 0:
        if existing.stdout.strip().lower() != candidate:
            raise WorktreeRefusal("assignment recovery ref already protects another commit")
        return
    if existing.returncode != 1:
        raise WorktreeError("unable to inspect assignment recovery ref")
    # An all-zero old value makes creation compare-and-set semantics explicit;
    # an intervening value is never overwritten by this helper.
    _run(top, "update-ref", recovery_ref, candidate, "0" * len(candidate))


def retain_worktree(
    *,
    repo_top: os.PathLike[str] | str,
    git_common_dir: os.PathLike[str] | str,
    managed_path: os.PathLike[str] | str,
    receipt_path: os.PathLike[str] | str,
    assignment_id: str,
    actor: str = "root",
    in_use: bool = False,
    ignored_disposition: Optional[str] = None,
) -> dict[str, Any]:
    _require_root(actor)
    top, common, managed, receipt_path, assignment = _common_inputs(repo_top, git_common_dir, managed_path, receipt_path, assignment_id)
    receipt = _load_receipt(receipt_path, assignment, managed)
    receipt, _ = _reconcile_pending(top, common, managed, receipt_path, receipt)
    if receipt["status"] in TERMINAL_STATUSES:
        if managed.exists() or _registration_count(top, managed):
            raise WorktreeError("terminal receipt still has a live checkout or registration")
        return {"ok": True, "operation": "retain", "status": receipt["status"], "recovery_ref": receipt.get("recovery_ref"), "receipt": receipt}
    protected_receipt: Optional[dict[str, Any]] = None
    try:
        pending = receipt.get("pending_action")
        if pending and pending.get("operation") != "retain":
            raise WorktreeRefusal("a different terminal action is already pending")
        report, updated = _prepare_cleanup(top=top, common=common, managed=managed, receipt_path=receipt_path, receipt=receipt, in_use=in_use, ignored_disposition=ignored_disposition)
        candidate = report.get("candidate_commit")
        if not candidate:
            raise WorktreeRefusal("retain requires a unique candidate")
        if not report["candidate_unique"]:
            raise WorktreeRefusal("retain requires a unique candidate")
        recovery_ref = str(receipt.get("recovery_ref") or _recovery_ref(assignment))
        if not recovery_ref.startswith(_recovery_ref(assignment)):
            raise WorktreeRefusal("recovery ref is not assignment-scoped")
        updated["recovery_ref"] = recovery_ref
        updated["status"] = receipt.get("status", "CANDIDATE_RECORDED")
        updated["pending_action"] = {
            "operation": "retain",
            "terminal_status": "RETAINED_FOR_RECOVERY",
            "recovery_ref": recovery_ref,
            "requested_at": _now(),
        }
        updated["retained_at"] = _now()
        updated["last_audit"] = {"at": _now(), "report": report}
        updated["last_failure"] = None
        # The intent is durable before the recovery ref is touched.  This
        # makes a ref-write crash recoverable and prevents an unaware receipt
        # from being stranded with an external protective ref.
        _write_receipt(receipt_path, updated)
        protected_receipt = dict(updated)
        _ensure_recovery_ref(top, recovery_ref, candidate)
        _remove_checkout(top, managed, force=bool(report["ignored_only"]))
        final = dict(updated)
        final["status"] = "RETAINED_FOR_RECOVERY"
        final["pending_action"] = None
        final["checkout_removed"] = True
        _write_receipt(receipt_path, final)
        return {"ok": True, "operation": "retain", "status": "RETAINED_FOR_RECOVERY", "recovery_ref": recovery_ref, "receipt": final}
    except Exception as exc:
        _failure(receipt_path, protected_receipt or receipt, str(exc))
        if isinstance(exc, WorktreeError):
            raise
        raise WorktreeError(str(exc)) from exc


def _require_root(actor: str) -> None:
    if actor != "root":
        raise WorktreeError("only Root may invoke managed worktree lifecycle operations")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", required=True, help="must be exactly root")
    parser.add_argument("--repo-top", required=True)
    parser.add_argument("--git-common-dir", required=True)
    parser.add_argument("--managed-path", required=True)
    parser.add_argument("--receipt-path", required=True)
    parser.add_argument("--assignment-id", required=True)
    sub = parser.add_subparsers(dest="operation", required=True)
    provision = sub.add_parser("provision")
    provision.add_argument("--base-commit", required=True)
    sub.add_parser("audit").add_argument("--in-use", action="store_true")
    candidate = sub.add_parser("record-candidate")
    candidate.add_argument("--candidate-commit", required=True)
    for name in ("release", "retain"):
        command = sub.add_parser(name)
        command.add_argument("--in-use", action="store_true")
        command.add_argument("--ignored-disposition", choices=sorted(IGNORED_DISPOSITIONS))
        if name == "release":
            command.add_argument("--accepted", action="store_true")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    common = {
        "repo_top": args.repo_top,
        "git_common_dir": args.git_common_dir,
        "managed_path": args.managed_path,
        "receipt_path": args.receipt_path,
        "assignment_id": args.assignment_id,
        "actor": args.actor,
    }
    try:
        if args.operation == "provision":
            result = provision_worktree(**common, base_commit=args.base_commit)
        elif args.operation == "audit":
            result = audit_worktree(**common, in_use=args.in_use)
        elif args.operation == "record-candidate":
            result = record_candidate(**common, candidate_commit=args.candidate_commit)
        elif args.operation == "release":
            result = release_worktree(**common, accepted=args.accepted, in_use=args.in_use, ignored_disposition=args.ignored_disposition)
        else:
            result = retain_worktree(**common, in_use=args.in_use, ignored_disposition=args.ignored_disposition)
    except (WorktreeError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "operation": args.operation, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
