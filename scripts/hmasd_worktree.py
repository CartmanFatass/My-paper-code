#!/usr/bin/env python3
"""Fail-closed Git worktree lifecycle for the HMASD workflow.

Git is the source of truth for checkout and ref state;
``.omp/runtime/worktrees.json`` is an ignored, CAS-protected journal maintained
through ``hmasd_state.py``. A receipt captures every fact used by prepare/apply
so Root or the direction/kind-owning EM/CM never applies a stale plan.

"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _datetime
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable, Mapping, Sequence


STATE_SCRIPT = Path(__file__).with_name("hmasd_state.py")
RUNTIME_KIND = "runtime_worktrees"
TARGET_BRANCH = "omp/workflow"
RECEIPT_SCHEMA = "hmasd.worktree-receipt/v1"

_DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_ASSIGNMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_FULL_SHA = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")

INTEGRATION_POLICIES = {"EXACT_HANDOFF", "ORTHOGONAL_DIRECTION"}
EXACT_POLICIES = {"EXACT_HANDOFF"}
PARALLEL_SET_SCHEMA = "hmasd.git-parallel-set/v1"
DELTA_FORMAT = "hmasd.raw-tree-delta/v1"
RUNTIME_REGISTRY_VERSION = 2
CANDIDATE_METADATA_SCHEMA = "hmasd.candidate-metadata/v1"
INTEGRATION_RECEIPT_VERSION = 1

LIFECYCLES = {
    "PROVISIONING",
    "PROVISIONED",
    "READY",
    "INSPECTED",
    "PATCHED",
    "CANDIDATE_READY",
    "PREPARED",
    "PREPARED_FOR_INTEGRATION",
    "INTEGRATED",
    "BLOCKED",
    "UNKNOWN",
    "APPLY_OUTCOME_UNKNOWN",
    "RELEASE_OUTCOME_UNKNOWN",
    "RELEASED",
    "RETAINED_FOR_RECOVERY",
}
TERMINAL_LIFECYCLES = {"RELEASED", "RETAINED_FOR_RECOVERY"}
UNKNOWN_LIFECYCLES = {"APPLY_OUTCOME_UNKNOWN", "RELEASE_OUTCOME_UNKNOWN"}


class WorktreeError(RuntimeError):
    """A directly observed worktree failure with the workflow exit code."""

    code = 1

    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = dict(details or {})


class InvalidInput(WorktreeError):
    code = 2


class Unsupported(WorktreeError):
    code = 3


class StaleFacts(WorktreeError):
    code = 4


class OwnershipRefusal(WorktreeError):
    code = 5


class UnsafeState(WorktreeError):
    code = 6


class DecisionRequired(WorktreeError):
    code = 8


class UnknownApply(WorktreeError):
    code = 1


def _now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _lexical_absolute(raw: os.PathLike[str] | str, *, label: str) -> Path:
    try:
        text = os.fspath(raw)
    except TypeError as exc:
        raise InvalidInput(f"{label} must be a path") from exc
    if not isinstance(text, str) or not text:
        raise InvalidInput(f"{label} must be a non-empty absolute path")
    path = Path(text)
    if not path.is_absolute():
        raise InvalidInput(f"{label} must be absolute")
    if any(part in {".", ".."} for part in path.parts):
        raise OwnershipRefusal(f"{label} contains an alias component")
    if "\x00" in text:
        raise InvalidInput(f"{label} contains NUL")
    return path


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _assert_no_symlink_chain(path: Path, *, label: str, require_existing: bool = False) -> None:
    """Reject symlinks in every existing component of ``path``."""

    current = path
    while True:
        info = _lstat(current)
        if info is not None and stat.S_ISLNK(info.st_mode):
            raise OwnershipRefusal(f"{label} contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    if require_existing and _lstat(path) is None:
        raise OwnershipRefusal(f"{label} does not exist: {path}")



def _canonical_path(
    raw: os.PathLike[str] | str,
    *,
    label: str,
    must_exist: bool = False,
    directory: bool = False,
) -> Path:
    path = _lexical_absolute(raw, label=label)
    _assert_no_symlink_chain(path, label=label, require_existing=must_exist)
    info = _lstat(path)
    if info is not None and directory and not stat.S_ISDIR(info.st_mode):
        raise OwnershipRefusal(f"{label} is not a directory: {path}")
    if info is None:
        parent = path.parent
        _assert_no_symlink_chain(parent, label=f"{label} parent", require_existing=True)
    try:
        resolved = path.resolve(strict=must_exist)
    except OSError as exc:
        raise OwnershipRefusal(f"{label} cannot be resolved safely: {exc}") from exc
    if resolved != path:
        raise OwnershipRefusal(f"{label} is an alias: {path}")
    return path


def _same_path(left: Path, right: Path) -> bool:
    return left == right


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _identity(path: Path) -> dict[str, int]:
    info = os.stat(path)
    return {"device": int(info.st_dev), "inode": int(info.st_ino)}


def _identity_equal(path: Path, expected: Mapping[str, Any]) -> bool:
    try:
        actual = _identity(path)
    except OSError:
        return False
    return actual == {"device": int(expected["device"]), "inode": int(expected["inode"])}


def _validate_direction(value: str) -> str:
    if not isinstance(value, str) or not _DIRECTION.fullmatch(value):
        raise InvalidInput("direction must match [a-z0-9][a-z0-9_-]{1,63}")
    return value


def _validate_assignment(value: str) -> str:
    if not isinstance(value, str) or not _ASSIGNMENT.fullmatch(value) or value in {".", ".."}:
        raise InvalidInput("assignment must be a safe identifier")
    if value.startswith("-") or value.endswith("."):
        raise InvalidInput("assignment is not a valid Git ref component")
    return value


def _validate_commit(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not _FULL_SHA.fullmatch(value):
        raise InvalidInput(f"{label} must be a full commit id")
    return value.lower()




def _validate_kind(value: str) -> str:
    if value not in {"research", "engineering"}:
        raise InvalidInput("kind must be research or engineering")
    return value


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise WorktreeError(f"git {' '.join(args)} failed: {detail}")
    return result


def _run_git_bytes(
    cwd: Path,
    *args: str,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        input=input_bytes,
        env=process_env,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        raise WorktreeError(f"git {' '.join(args)} failed: {detail or f'exit {result.returncode}'}")
    return result


def _git_value(cwd: Path, *args: str) -> str:
    result = _run_git(cwd, *args)
    return result.stdout.strip()


def _repo_context(raw: os.PathLike[str] | str) -> tuple[Path, Path]:
    # The documented non-provision commands are run from the repository and
    # intentionally have no --repo option.  Only that default is resolved;
    # explicit repository paths remain absolute/canonical inputs.
    if os.fspath(raw) == ".":
        raw = Path.cwd()
    repo = _canonical_path(raw, label="repo", must_exist=True, directory=True)
    control = repo / ".omp"
    _canonical_path(control, label="repo .omp", must_exist=True, directory=True)
    if not ((control / "AGENTS.md").is_file() or (control / "config.yml").is_file()):
        raise OwnershipRefusal("repo lacks .omp/AGENTS.md or .omp/config.yml")
    top_raw = _git_value(repo, "rev-parse", "--show-toplevel")
    top = _canonical_path(top_raw, label="repository top", must_exist=True, directory=True)
    if top != repo:
        raise OwnershipRefusal("repo is not the exact Git top-level path")
    common_raw = _git_value(repo, "rev-parse", "--git-common-dir")
    common = Path(common_raw)
    if not common.is_absolute():
        common = repo / common
    common = _canonical_path(common, label="Git common directory", must_exist=True, directory=True)
    if _git_value(repo, "rev-parse", "--is-bare-repository").lower() != "false":
        raise OwnershipRefusal("bare repositories cannot host HMASD worktrees")
    return repo, common


def _validate_container(container: Path, repo: Path, common: Path, *, create: bool) -> Path:
    container = _canonical_path(container, label="container", must_exist=False, directory=False)
    if _under(container, repo) or _under(container, common):
        raise OwnershipRefusal("container cannot be inside the repository or Git common directory")
    if create:
        try:
            container.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OwnershipRefusal(f"cannot create canonical container: {exc}") from exc
    container = _canonical_path(container, label="container", must_exist=True, directory=True)
    parent = _canonical_path(container.parent, label="container parent", must_exist=True, directory=True)
    if _under(parent, repo) or _under(parent, common):
        raise OwnershipRefusal("container parent cannot be inside the repository")
    return container


def _default_container(repo: Path) -> Path:
    return repo.parent / f"{repo.name}-worktrees"


@contextmanager
def _container_lock(container: Path) -> Generator[dict[str, Any], None, None]:
    """Hold the cooperative lock and return identities used for revalidation."""

    lock_path = container / ".hmasd.lock"
    _assert_no_symlink_chain(lock_path.parent, label="container lock parent", require_existing=True)
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except OSError as exc:
        raise OwnershipRefusal(f"cannot open non-symlink container lock: {exc}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OwnershipRefusal("container lock is not a regular file")
        fcntl.flock(fd, fcntl.LOCK_EX)
        current = _canonical_path(container, label="container", must_exist=True, directory=True)
        parent = _canonical_path(current.parent, label="container parent", must_exist=True, directory=True)
        identities = {
            "container": _identity(current),
            "container_parent": _identity(parent),
            "lock": {"device": int(info.st_dev), "inode": int(info.st_ino)},
        }
        yield identities
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _target_lock_key(common: Path, target: str = TARGET_BRANCH) -> str:
    if target != TARGET_BRANCH:
        raise OwnershipRefusal("integration target must be exactly omp/workflow")
    return f"{common}:refs/heads/{target}"


@contextmanager
def _target_lock(common: Path, target: str = TARGET_BRANCH) -> Generator[dict[str, Any], None, None]:
    """Serialize one repository target independently of any worktree container.

    Callers acquire this lock before a worktree/container lock. Registry state
    transitions remain the innermost, short CAS operation.
    """

    key = _target_lock_key(common, target)
    _assert_no_symlink_chain(common, label="Git common directory", require_existing=True)
    lock_dir = common / "hmasd-target-locks"
    try:
        lock_dir.mkdir(mode=0o700, exist_ok=True)
    except OSError as exc:
        raise OwnershipRefusal(f"cannot create target-lock directory: {exc}") from exc
    _assert_no_symlink_chain(lock_dir, label="target-lock directory", require_existing=True)
    lock_name = hashlib.sha256(key.encode("utf-8")).hexdigest() + ".lock"
    lock_path = lock_dir / lock_name
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except OSError as exc:
        raise OwnershipRefusal(f"cannot open repository target lock: {exc}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OwnershipRefusal("repository target lock is not a regular file")
        fcntl.flock(fd, fcntl.LOCK_EX)
        common_identity = _identity(common)
        lock_identity = {"device": int(info.st_dev), "inode": int(info.st_ino)}
        yield {"key": key, "path": str(lock_path), "common": common_identity, "lock": lock_identity}
        if not _identity_equal(common, common_identity) or not _identity_equal(lock_path, lock_identity):
            raise UnsafeState("repository target-lock identity changed during integration")
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _revalidate_container(container: Path, identities: Mapping[str, Any]) -> None:
    lock_path = container / ".hmasd.lock"
    # ``os.stat`` follows symlinks, so identity equality alone is insufficient
    # after a namespace swap.  Check the object types before comparing inode
    # identities.
    for path, label in ((container, "container"), (container.parent, "container parent"), (lock_path, "container lock")):
        info = _lstat(path)
        if info is None:
            raise UnsafeState(f"{label} disappeared during worktree operation")
        if stat.S_ISLNK(info.st_mode):
            raise UnsafeState(f"{label} became a symlink during worktree operation")
    if not _identity_equal(container, identities["container"]):
        raise UnsafeState("container identity changed during worktree operation")
    if not _identity_equal(container.parent, identities["container_parent"]):
        raise UnsafeState("container parent identity changed during worktree operation")
    if not _identity_equal(lock_path, identities["lock"]):
        raise UnsafeState("container lock identity changed during worktree operation")


def _branch_name(direction: str, kind: str, assignment: str) -> str:
    direction = _validate_direction(direction)
    kind = _validate_kind(kind)
    assignment = _validate_assignment(assignment)
    branch = f"omp/{direction}/{kind}/{assignment}"
    if not branch.startswith("omp/"):
        raise OwnershipRefusal("temporary branch escaped omp namespace")
    return branch


def _worktree_ref(direction: str, kind: str, assignment: str) -> str:
    ref = f"wt-{direction}-{kind}-{assignment}"
    if not _ASSIGNMENT.fullmatch(ref) or len(ref) > 128:
        raise InvalidInput("derived worktree_ref is too long or unsafe")
    return ref


def _target_path(container: Path, direction: str, kind: str, assignment: str) -> Path:
    name = f"{_validate_direction(direction)}-{_validate_kind(kind)}-{_validate_assignment(assignment)}"
    target = container / name
    _canonical_path(target, label="worktree target", must_exist=False)
    try:
        target.relative_to(container)
    except ValueError as exc:
        raise OwnershipRefusal("worktree target escaped canonical container") from exc
    return target


def _branch_sha(repo: Path, branch: str) -> str | None:
    if not branch.startswith("omp/"):
        raise OwnershipRefusal("only omp/* branches may be inspected")
    result = _run_git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}", check=False)
    if result.returncode:
        return None
    value = result.stdout.strip().lower()
    return value or None


def _verify_commit(repo: Path, value: str, *, label: str) -> str:
    commit = _validate_commit(value, label=label)
    actual = _git_value(repo, "rev-parse", "--verify", f"{commit}^{{commit}}").lower()
    if actual != commit:
        raise StaleFacts(f"{label} is not the exact existing commit")
    return commit


def _current_branch(repo: Path) -> str | None:
    result = _run_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if result.returncode:
        return None
    value = result.stdout.strip()
    return value or None


def _worktree_records(repo: Path) -> list[dict[str, Any]]:
    result = _run_git(repo, "worktree", "list", "--porcelain")
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in result.stdout.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line[len("worktree ") :]
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD ") :].strip().lower()
        elif line.startswith("branch "):
            current["branch"] = line[len("branch ") :].strip()
        elif line == "detached":
            current["detached"] = True
        elif line == "bare":
            current["bare"] = True
    for record in records:
        raw = record.get("path")
        if isinstance(raw, str):
            record["path_obj"] = Path(raw)
    return records


def _registration(repo: Path, target: Path) -> list[dict[str, Any]]:
    return [record for record in _worktree_records(repo) if _same_path(record.get("path_obj", Path()), target)]


def _status(path: Path) -> dict[str, list[str] | bool]:
    result = _run_git(path, "status", "--porcelain=v1", "--ignored", "--untracked-files=all", "-z")
    tokens = result.stdout.split("\0")
    tracked: list[str] = []
    nonignored: list[str] = []
    ignored: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        if len(token) < 3:
            tracked.append(token)
            continue
        code, name = token[:2], token[3:]
        names = [name]
        if "R" in code or "C" in code:
            if index < len(tokens) and tokens[index]:
                names.append(tokens[index])
                index += 1
        if code == "!!":
            ignored.extend(names)
        elif code == "??":
            nonignored.extend(names)
        else:
            tracked.extend(names)
    return {
        "tracked_dirty": sorted(set(tracked)),
        "nonignored_untracked": sorted(set(nonignored)),
        "ignored_only": sorted(set(ignored)),
        "clean": not tracked and not nonignored and not ignored,
    }


def _validate_relative(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise OwnershipRefusal(f"{label} must be a repository-relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise OwnershipRefusal(f"{label} contains an alias component")
    return "/".join(parts)


def _relative_under(path: str, allowed: str) -> bool:
    return path == allowed or path.startswith(allowed + "/")


def _integration_policy(entry: Mapping[str, Any]) -> str:
    policy = entry.get("integration_policy")
    if policy not in INTEGRATION_POLICIES:
        raise InvalidInput("runtime worktree integration policy must be explicit and current")
    return str(policy)


def _validate_integration_policy(value: str | None) -> str:
    if value not in INTEGRATION_POLICIES:
        raise InvalidInput(
            "integration policy must be explicitly EXACT_HANDOFF or ORTHOGONAL_DIRECTION"
        )
    return value


def _validate_mutation_lease(
    repo: Path,
    manager_assignment_id: str,
    lease: Mapping[str, Any] | None,
    *,
    required: bool,
) -> dict[str, Any] | None:
    if lease is None:
        if required:
            raise OwnershipRefusal("mutating operation lacks an exact manager-to-Clerk lease")
        return None
    normalized = _require_object(
        lease,
        label="mutation lease",
        keys={"manager_assignment_id", "clerk_assignment_id", "handoff_ref", "lease_token"},
    )
    normalized["manager_assignment_id"] = _validate_assignment(
        normalized["manager_assignment_id"]
    )
    if normalized["manager_assignment_id"] != manager_assignment_id:
        raise OwnershipRefusal("mutation lease manager assignment does not own this worktree")
    clerk_assignment = normalized["clerk_assignment_id"]
    if (
        not isinstance(clerk_assignment, str)
        or re.fullmatch(r"[a-z0-9][a-z0-9-]{1,127}", clerk_assignment) is None
    ):
        raise InvalidInput("mutation lease Clerk assignment is invalid")
    normalized["clerk_assignment_id"] = clerk_assignment
    normalized["lease_token"] = _validate_sha256(
        normalized["lease_token"], label="mutation lease token"
    )
    handoff = _require_object(
        normalized["handoff_ref"],
        label="mutation lease handoff_ref",
        keys={"path", "sha256"},
    )
    handoff_path = _validate_relative(handoff["path"], label="mutation lease handoff path")
    expected_digest = _validate_sha256(
        handoff["sha256"], label="mutation lease handoff digest"
    )
    canonical_handoff = _canonical_path(
        repo / Path(handoff_path),
        label="mutation lease handoff",
        must_exist=True,
    )
    if not _under(canonical_handoff, repo):
        raise OwnershipRefusal("mutation lease handoff escaped the repository")
    if _hash_file(canonical_handoff, label="mutation lease handoff") != expected_digest:
        raise StaleFacts("mutation lease handoff digest changed")
    normalized["handoff_ref"] = {"path": handoff_path, "sha256": expected_digest}
    return normalized


def _lease_from_namespace(args: argparse.Namespace) -> dict[str, Any] | None:
    values = (
        getattr(args, "manager_assignment_id", None),
        getattr(args, "clerk_assignment_id", None),
        getattr(args, "handoff_ref", None),
        getattr(args, "handoff_sha256", None),
        getattr(args, "lease_token", None),
    )
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise InvalidInput("all mutation-lease arguments must be supplied together")
    return {
        "manager_assignment_id": values[0],
        "clerk_assignment_id": values[1],
        "handoff_ref": {"path": values[2], "sha256": values[3]},
        "lease_token": values[4],
    }



def _validate_required_dependency_refs(
    repo: Path,
    values: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, value in enumerate(values or []):
        ref = _require_object(
            value,
            label=f"required dependency refs[{index}]",
            keys={"path", "sha256"},
        )
        relative = _validate_relative(
            ref["path"], label=f"required dependency refs[{index}].path"
        )
        digest = _validate_sha256(
            ref["sha256"], label=f"required dependency refs[{index}].sha256"
        )
        path = _canonical_path(
            repo / relative,
            label=f"required dependency refs[{index}]",
            must_exist=True,
        )
        if not _under(path, repo) or _hash_file(
            path, label="required dependency"
        ) != digest:
            raise StaleFacts("required dependency bytes differ from frozen digest")
        normalized.append({"path": relative, "sha256": digest})
    paths = [item["path"] for item in normalized]
    if len(paths) != len(set(paths)):
        raise InvalidInput("required dependency refs must have unique paths")
    return sorted(normalized, key=lambda item: item["path"])

def _expectations_from_namespace(args: argparse.Namespace) -> dict[str, Any] | None:
    core = (
        getattr(args, "expected_registry_revision", None),
        getattr(args, "expected_lifecycle", None),
        getattr(args, "expected_worktree_path", None),
        getattr(args, "expected_container_path", None),
    )
    receipt_sha256 = getattr(args, "expected_receipt_sha256", None)
    if all(value is None for value in core) and receipt_sha256 is None:
        return None
    if any(value is None for value in core):
        raise InvalidInput("all core operation preconditions must be supplied together")
    return {
        "registry_revision": core[0],
        "lifecycle": core[1],
        "worktree_path": core[2],
        "container_path": core[3],
        "receipt_sha256": receipt_sha256,
    }


def _validate_operation_expectations(
    repo: Path,
    container: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    expected: Mapping[str, Any] | None,
    *,
    absent_worktree_path: Path | None = None,
) -> None:
    if expected is None:
        return
    revision = expected.get("registry_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise InvalidInput("expected registry revision must be a positive integer")
    if revision != int(state["revision"]):
        raise StaleFacts("runtime registry differs from the packet precondition")
    expected_container = _canonical_path(
        str(expected.get("container_path", "")),
        label="expected container",
        must_exist=True,
        directory=True,
    )
    if not _same_path(expected_container, container):
        raise OwnershipRefusal("packet expected a different worktree container")
    expected_worktree = _lexical_absolute(
        str(expected.get("worktree_path", "")), label="expected worktree"
    )
    actual_worktree = (
        Path(str(entry["canonical_absolute_path"])) if entry is not None else absent_worktree_path
    )
    if actual_worktree is None or not _same_path(expected_worktree, actual_worktree):
        raise OwnershipRefusal("packet expected a different worktree path")
    expected_lifecycle = expected.get("lifecycle")
    actual_lifecycle = entry.get("lifecycle") if entry is not None else "ABSENT"
    if expected_lifecycle != actual_lifecycle:
        raise StaleFacts("worktree lifecycle differs from the packet precondition")
    expected_receipt = expected.get("receipt_sha256")
    if expected_receipt is not None:
        expected_receipt = _validate_sha256(
            expected_receipt, label="expected receipt digest"
        )
        if receipt is None or hashlib.sha256(_json_bytes(receipt)).hexdigest() != expected_receipt:
            raise StaleFacts("worktree receipt differs from the packet precondition")
    elif receipt is not None and entry is not None:
        raise InvalidInput("existing worktree precondition requires --expected-receipt-sha256")

def _path_collision(left: str, right: str) -> bool:
    return _relative_under(left, right) or _relative_under(right, left)


def _strict_path_list(values: Sequence[Any], *, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(values, list) or (not values and not allow_empty):
        qualifier = "an array" if allow_empty else "a non-empty array"
        raise InvalidInput(f"{label} must be {qualifier}")
    normalized = [_validate_relative(value, label=label) for value in values]
    if len(normalized) != len(set(normalized)):
        raise InvalidInput(f"{label} must not contain duplicates")
    return sorted(normalized)


def _hash_file(path: Path, *, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise StaleFacts(f"{label} cannot be read: {exc}") from exc


def _length_prefixed(fields: Sequence[bytes]) -> bytes:
    return b"".join(len(field).to_bytes(8, "big") + field for field in fields)


def _canonical_tree_delta(repo: Path, old: str, new: str) -> dict[str, Any]:
    """Return a rename-disabled, binary-safe structural tree delta."""

    object_format = _git_value(repo, "rev-parse", "--show-object-format")
    oid_length = {"sha1": 40, "sha256": 64}.get(object_format)
    if oid_length is None:
        raise Unsupported(f"unsupported Git object format: {object_format}")
    result = _run_git_bytes(
        repo,
        "diff-tree",
        "-r",
        "--raw",
        "-z",
        "--no-renames",
        "--no-commit-id",
        f"--abbrev={oid_length}",
        old,
        new,
    )
    raw = result.stdout
    offset = 0
    records: list[dict[str, str]] = []
    while offset < len(raw):
        header_end = raw.find(b"\0", offset)
        if header_end < 0:
            raise UnsafeState("Git raw tree delta has an unterminated header")
        header = raw[offset:header_end]
        offset = header_end + 1
        if not header.startswith(b":"):
            raise UnsafeState("Git raw tree delta header is malformed")
        fields = header[1:].split()
        if len(fields) != 5:
            raise UnsafeState("Git raw tree delta header has an unexpected field count")
        old_mode, new_mode, old_oid, new_oid, status_code = fields
        if status_code not in {b"A", b"D", b"M", b"T"}:
            raise UnsafeState("Git raw tree delta contains a rename/copy or unsupported status")
        path_end = raw.find(b"\0", offset)
        if path_end < 0:
            raise UnsafeState("Git raw tree delta has an unterminated path")
        path_bytes = raw[offset:path_end]
        offset = path_end + 1
        try:
            path = _validate_relative(path_bytes.decode("utf-8", errors="strict"), label="delta path")
        except UnicodeDecodeError as exc:
            raise OwnershipRefusal("delta path is not strict UTF-8") from exc
        for mode in (old_mode, new_mode):
            if not re.fullmatch(rb"[0-7]{6}", mode):
                raise UnsafeState("Git raw tree delta contains an invalid mode")
            if mode in {b"120000", b"160000"}:
                raise Unsupported("symlink and submodule tree deltas are not supported")
        for oid in (old_oid, new_oid):
            if len(oid) != oid_length or not re.fullmatch(rb"[0-9a-f]+", oid):
                raise UnsafeState("Git raw tree delta contains an invalid object id")
        records.append(
            {
                "path": path,
                "old_mode": old_mode.decode("ascii"),
                "old_oid": old_oid.decode("ascii"),
                "new_mode": new_mode.decode("ascii"),
                "new_oid": new_oid.decode("ascii"),
            }
        )
    records.sort(key=lambda row: row["path"].encode("utf-8"))
    if len({row["path"] for row in records}) != len(records):
        raise UnsafeState("Git raw tree delta contains duplicate paths")
    serialized = [DELTA_FORMAT.encode("ascii"), str(len(records)).encode("ascii")]
    for record in records:
        serialized.extend(
            [
                record["path"].encode("utf-8"),
                record["old_mode"].encode("ascii"),
                record["old_oid"].encode("ascii"),
                record["new_mode"].encode("ascii"),
                record["new_oid"].encode("ascii"),
            ]
        )
    return {
        "format": DELTA_FORMAT,
        "object_format": object_format,
        "records": records,
        "sha256": hashlib.sha256(_length_prefixed(serialized)).hexdigest(),
    }


def _require_object(value: Any, *, label: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise InvalidInput(f"{label} must contain exactly: {', '.join(sorted(keys))}")
    return dict(value)


def _validate_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise InvalidInput(f"{label} must be a lowercase SHA-256")
    return value


def _parallel_set_manifest_path(repo: Path, raw: str) -> Path:
    relative = _validate_relative(raw, label="parallel-set manifest")
    path = repo / Path(relative)
    if not _under(path, repo):
        raise OwnershipRefusal("parallel-set manifest escaped repository")
    return _canonical_path(path, label="parallel-set manifest", must_exist=True)


def _validate_parallel_direction(value: Any, *, index: int) -> dict[str, Any]:
    label = f"parallel-set directions[{index}]"
    row = _require_object(
        value,
        label=label,
        keys={
            "direction_id",
            "assignment_id",
            "kind",
            "allowed_roots",
            "expected_changed_paths",
            "dependency_paths",
            "verification",
            "prospective_checks",
            "required_handoff_sha",
            "required_dependencies",
        },
    )
    row["direction_id"] = _validate_direction(row["direction_id"])
    row["assignment_id"] = _validate_assignment(row["assignment_id"])
    row["kind"] = _validate_kind(row["kind"])
    row["allowed_roots"] = _strict_path_list(row["allowed_roots"], label=f"{label}.allowed_roots")
    row["expected_changed_paths"] = _strict_path_list(
        row["expected_changed_paths"], label=f"{label}.expected_changed_paths"
    )
    row["dependency_paths"] = _strict_path_list(
        row["dependency_paths"], label=f"{label}.dependency_paths", allow_empty=True
    )
    if row["required_handoff_sha"] is not None or row["required_dependencies"] != []:
        raise OwnershipRefusal("orthogonal authorization cannot carry a required handoff or dependency")
    out_of_scope = [
        path
        for path in row["expected_changed_paths"]
        if not any(_relative_under(path, root) for root in row["allowed_roots"])
    ]
    if out_of_scope:
        raise OwnershipRefusal(
            f"parallel-set expected paths are outside allowed roots: {', '.join(out_of_scope)}"
        )
    verification = row["verification"]
    if not isinstance(verification, list):
        raise InvalidInput(f"{label}.verification must be an array")
    normalized_verification: list[dict[str, str]] = []
    for evidence_index, evidence_value in enumerate(verification):
        evidence = _require_object(
            evidence_value,
            label=f"{label}.verification[{evidence_index}]",
            keys={"path", "sha256"},
        )
        normalized_verification.append(
            {
                "path": _validate_relative(evidence["path"], label="verification path"),
                "sha256": _validate_sha256(evidence["sha256"], label="verification digest"),
            }
        )
    verification_paths = [item["path"] for item in normalized_verification]
    if len(verification_paths) != len(set(verification_paths)):
        raise InvalidInput(f"{label}.verification must have unique paths")
    row["verification"] = sorted(
        normalized_verification, key=lambda item: item["path"]
    )
    checks = row["prospective_checks"]
    if not isinstance(checks, list) or not checks:
        raise InvalidInput(f"{label}.prospective_checks must be a non-empty array")
    normalized_checks: list[dict[str, Any]] = []
    for check_index, check_value in enumerate(checks):
        check = _require_object(
            check_value,
            label=f"{label}.prospective_checks[{check_index}]",
            keys={"check_id", "argv", "cwd"},
        )
        check_id = _validate_assignment(check["check_id"])
        argv = check["argv"]
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(arg, str) or not arg or "\0" in arg for arg in argv)
        ):
            raise InvalidInput(f"{label}.prospective_checks[{check_index}].argv is invalid")
        cwd = check["cwd"]
        if cwd != "":
            cwd = _validate_relative(cwd, label="prospective check cwd")
        normalized_checks.append({"check_id": check_id, "argv": list(argv), "cwd": cwd})
    if [item["check_id"] for item in normalized_checks] != sorted(
        {item["check_id"] for item in normalized_checks}
    ):
        raise InvalidInput(f"{label}.prospective_checks must be sorted by unique check_id")
    row["prospective_checks"] = normalized_checks
    return row


def _load_parallel_set_manifest(
    repo: Path,
    raw_path: str,
    *,
    expected_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = _parallel_set_manifest_path(repo, raw_path)
    try:
        manifest_bytes = path.read_bytes()
        manifest_value = json.loads(manifest_bytes.decode("utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise InvalidInput(f"parallel-set manifest is unreadable: {exc}") from exc
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if expected_sha256 is not None and manifest_sha256 != expected_sha256:
        raise StaleFacts("parallel-set manifest digest changed")
    manifest = _require_object(
        manifest_value,
        label="parallel-set manifest",
        keys={
            "schema",
            "parallel_set_id",
            "common_epoch_sha",
            "target_branch",
            "remote",
            "directions",
        },
    )
    if manifest["schema"] != PARALLEL_SET_SCHEMA:
        raise InvalidInput("parallel-set manifest schema is invalid")
    manifest["parallel_set_id"] = _validate_assignment(manifest["parallel_set_id"])
    manifest["common_epoch_sha"] = _validate_commit(
        manifest["common_epoch_sha"], label="parallel-set common epoch"
    )
    if manifest["target_branch"] != TARGET_BRANCH:
        raise OwnershipRefusal("parallel-set target must be exactly omp/workflow")
    remote = _require_object(
        manifest["remote"],
        label="parallel-set remote",
        keys={"name", "ref", "url_sha256"},
    )
    if (
        not isinstance(remote["name"], str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", remote["name"]) is None
    ):
        raise InvalidInput("parallel-set remote name is invalid")
    if remote["ref"] != f"refs/heads/{TARGET_BRANCH}":
        raise OwnershipRefusal("parallel-set remote ref must be refs/heads/omp/workflow")
    remote["url_sha256"] = _validate_sha256(remote["url_sha256"], label="remote URL digest")
    observed_url = _git_value(repo, "remote", "get-url", "--push", remote["name"])
    if hashlib.sha256(observed_url.encode("utf-8")).hexdigest() != remote["url_sha256"]:
        raise StaleFacts("configured push remote identity differs from the frozen manifest")
    manifest["remote"] = remote
    directions = manifest["directions"]
    if not isinstance(directions, list) or len(directions) < 2:
        raise InvalidInput("parallel-set manifest requires at least two directions")
    normalized_directions = [
        _validate_parallel_direction(value, index=index) for index, value in enumerate(directions)
    ]
    identities = [
        (row["direction_id"], row["kind"], row["assignment_id"]) for row in normalized_directions
    ]
    if identities != sorted(set(identities)):
        raise InvalidInput("parallel-set directions must be sorted and uniquely identified")
    for left_index, left in enumerate(normalized_directions):
        for right in normalized_directions[left_index + 1 :]:
            collisions = [
                (left_path, right_path)
                for left_path in left["expected_changed_paths"]
                for right_path in right["expected_changed_paths"]
                if _path_collision(left_path, right_path)
            ]
            if collisions:
                raise OwnershipRefusal("parallel-set sibling expected paths overlap")
    manifest["directions"] = normalized_directions
    authority = {
        "manifest_path": str(Path(raw_path)),
        "manifest_sha256": manifest_sha256,
        "parallel_set_id": manifest["parallel_set_id"],
        "common_epoch_sha": manifest["common_epoch_sha"],
    }
    return manifest, authority


def _parallel_direction(
    manifest: Mapping[str, Any],
    *,
    direction_id: str,
    kind: str,
    assignment_id: str,
) -> dict[str, Any]:
    matches = [
        dict(row)
        for row in manifest["directions"]
        if row["direction_id"] == direction_id
        and row["kind"] == kind
        and row["assignment_id"] == assignment_id
    ]
    if len(matches) != 1:
        raise OwnershipRefusal("worktree is not exactly authorized by the parallel-set manifest")
    return matches[0]


def _changed_paths(repo: Path, base: str, candidate: str) -> list[str]:
    result = _run_git(repo, "diff", "--name-only", "--no-renames", "-z", base, candidate)
    names = [name for name in result.stdout.split("\0") if name]
    normalized = sorted({_validate_relative(name, label="changed path") for name in names})
    for name in normalized:
        # A tracked symlink is an explicit path escape even if the lexical name
        # itself is inside the repository.
        tree = _run_git(repo, "ls-tree", "-r", "-z", candidate, "--", name)
        for entry in tree.stdout.split("\0"):
            if not entry:
                continue
            header = entry.split("\t", 1)[0].split()
            if header and header[0] == "120000":
                raise OwnershipRefusal(f"changed path is a tracked symlink: {name}")
    return normalized


def _candidate_parent(repo: Path, candidate: str) -> str:
    line = _git_value(repo, "rev-list", "--parents", "-n", "1", candidate)
    values = line.split()
    if len(values) != 2:
        raise UnsafeState("candidate must be one non-merge commit")
    return values[1].lower()


def _ensure_controlled_checkout(
    repo: Path,
    entry: Mapping[str, Any],
    *,
    candidate: str | None = None,
    check_head: bool = True,
) -> tuple[Path, dict[str, Any], dict[str, list[str] | bool]]:
    target = _canonical_path(str(entry["canonical_absolute_path"]), label="registered worktree", must_exist=True, directory=True)
    branch = str(entry["branch"])
    if not branch.startswith("omp/"):
        raise OwnershipRefusal("registered worktree branch is outside omp/*")
    registrations = _registration(repo, target)
    if len(registrations) != 1:
        raise UnsafeState("registered worktree does not have exactly one Git registration")
    registration = registrations[0]
    expected_branch = f"refs/heads/{branch}"
    if registration.get("branch") != expected_branch:
        raise UnsafeState("registered worktree branch identity changed")
    head = str(registration.get("head", "")).lower()
    expected_head = (candidate or entry.get("candidate_sha") or entry["base_sha"]).lower()
    if check_head and head != expected_head:
        raise StaleFacts("worktree HEAD does not match the recorded fact")
    actual_branch_sha = _branch_sha(repo, branch)
    if actual_branch_sha != head:
        raise StaleFacts("temporary branch ref does not match worktree HEAD")
    status = _status(target)
    return target, registration, status


def _runtime_path(repo: Path) -> Path:
    runtime = repo / ".omp" / "runtime"
    _assert_no_symlink_chain(runtime.parent, label="runtime parent", require_existing=True)
    if _lstat(runtime) is None:
        runtime.mkdir(mode=0o700)
    _assert_no_symlink_chain(runtime, label="runtime", require_existing=True)
    path = runtime / "worktrees.json"
    if _lstat(path) is not None:
        _assert_no_symlink_chain(path, label="runtime registry", require_existing=True)
    return path


def _receipt_path(repo: Path, entry: Mapping[str, Any]) -> Path:
    relative = _validate_relative(str(entry["receipt_path"]), label="receipt_path")
    path = repo / Path(relative)
    if not _under(path, repo):
        raise OwnershipRefusal("receipt_path escaped repository")
    _assert_no_symlink_chain(path.parent, label="receipt parent", require_existing=False)
    return path


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_chain(path.parent, label="atomic-write parent", require_existing=True)
    if _lstat(path) is not None:
        _assert_no_symlink_chain(path, label="atomic-write target", require_existing=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def _state_call(command: str, *, path: Path, input_path: Path | None = None, expected_revision: int | None = None) -> None:
    if not STATE_SCRIPT.is_file():
        raise WorktreeError(f"state helper is unavailable: {STATE_SCRIPT}")
    args = [sys.executable, str(STATE_SCRIPT), command, "--kind", RUNTIME_KIND, "--path", str(path)]
    if command != "validate":
        args.extend(["--writer", "Root"])
    if input_path is not None:
        args.extend(["--input", str(input_path)])
    if expected_revision is not None:
        args.extend(["--expected-revision", str(expected_revision)])
    result = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"state helper exit {result.returncode}"
        if result.returncode == 2:
            raise InvalidInput(detail)
        if result.returncode == 3:
            raise Unsupported(detail)
        if result.returncode == 4:
            raise StaleFacts(detail)
        if result.returncode == 5:
            raise OwnershipRefusal(detail)
        if result.returncode == 6:
            raise UnsafeState(detail)
        raise WorktreeError(detail)


def _load_registry(
    repo: Path,
    *,
    required: bool = True,
) -> tuple[Path, dict[str, Any]] | None:
    path = _runtime_path(repo)
    if _lstat(path) is None:
        if required:
            raise UnsafeState("runtime worktree registry is absent")
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidInput(f"runtime registry is unreadable: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(state.get("worktrees"), list):
        raise InvalidInput("runtime registry has invalid shape")
    if not isinstance(state.get("revision"), int) or state["revision"] < 1:
        raise InvalidInput("runtime registry revision is invalid")
    if state.get("schema_version") != RUNTIME_REGISTRY_VERSION:
        raise InvalidInput("runtime worktree registry must use current schema version 2")
    _state_call("validate", path=path)
    return path, state


def _state_input(value: Mapping[str, Any]) -> Path:
    fd, path = tempfile.mkstemp(prefix="hmasd-worktree-state-", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return Path(path)


def _initialize_registry(repo: Path) -> tuple[Path, dict[str, Any]]:
    loaded = _load_registry(repo, required=False)
    if loaded is not None:
        return loaded
    path = _runtime_path(repo)
    state = {
        "schema_version": RUNTIME_REGISTRY_VERSION,
        "revision": 1,
        "updated_at": _now(),
        "writer": "Root",
        "worktrees": [],
    }
    input_path = _state_input(state)
    try:
        try:
            _state_call("initialize", path=path, input_path=input_path)
        except StaleFacts:
            pass
    finally:
        try:
            input_path.unlink()
        except OSError:
            pass
    loaded = _load_registry(repo, required=True)
    assert loaded is not None
    return loaded


def _replace_registry(path: Path, state: Mapping[str, Any], expected_revision: int) -> dict[str, Any]:
    replacement = dict(state)
    replacement["revision"] = expected_revision + 1
    replacement["updated_at"] = _now()
    replacement["writer"] = "Root"
    replacement["worktrees"] = sorted(list(state.get("worktrees", [])), key=lambda row: str(row.get("worktree_ref", "")))
    input_path = _state_input(replacement)
    try:
        _state_call("replace", path=path, input_path=input_path, expected_revision=expected_revision)
    finally:
        try:
            input_path.unlink()
        except OSError:
            pass
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UnknownApply(f"registry replacement succeeded but reread failed: {exc}") from exc
    return result


def _entry(state: Mapping[str, Any], ref: str) -> dict[str, Any]:
    matches = [row for row in state.get("worktrees", []) if isinstance(row, dict) and row.get("worktree_ref") == ref]
    if len(matches) != 1:
        raise UnsafeState("worktree_ref does not identify exactly one registry entry")
    result = dict(matches[0])
    lifecycle = result.get("lifecycle")
    if lifecycle not in LIFECYCLES:
        raise InvalidInput("runtime registry lifecycle is invalid")
    return result


def _put_entry(state: Mapping[str, Any], replacement: Mapping[str, Any], ref: str) -> dict[str, Any]:
    rows = [dict(row) for row in state.get("worktrees", [])]
    found = False
    for index, row in enumerate(rows):
        if row.get("worktree_ref") == ref:
            rows[index] = dict(replacement)
            found = True
    if not found:
        raise UnsafeState("cannot replace missing worktree registry entry")
    updated = dict(state)
    updated["worktrees"] = rows
    return updated


def _reload_locked_entry(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    worktree_ref: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reread every routing authority while the canonical container is locked."""

    _revalidate_container(container, identities)
    current_repo, current_common = _repo_context(str(repo))
    if not _same_path(current_repo, repo) or not _same_path(current_common, common):
        raise UnsafeState("repository identity changed while the container lock was held")
    loaded = _load_registry(repo)
    assert loaded is not None
    current_state_path, state = loaded
    if not _same_path(current_state_path, state_path):
        raise UnsafeState("runtime registry path changed while the container lock was held")
    entry = _entry(state, worktree_ref)
    current_container = _validate_container(
        Path(str(entry["canonical_absolute_path"])).parent,
        repo,
        common,
        create=False,
    )
    if not _same_path(current_container, container):
        raise StaleFacts("worktree registry moved to a different container before lock acquisition")
    _revalidate_container(container, identities)
    return state, entry


@contextmanager
def _locked_entry(
    repo: Path,
    common: Path,
    worktree_ref: str,
) -> Generator[tuple[Path, Path, dict[str, Any], dict[str, Any], Mapping[str, Any]], None, None]:
    """Use the unlocked registry only to route to a lock, never for effects."""

    loaded = _load_registry(repo)
    assert loaded is not None
    state_path, route_state = loaded
    route_entry = _entry(route_state, worktree_ref)
    container = _validate_container(
        Path(str(route_entry["canonical_absolute_path"])).parent,
        repo,
        common,
        create=False,
    )
    route_revision = int(route_state["revision"])
    route_entry_sha256 = _digest(route_entry)
    with _container_lock(container) as identities:
        state, entry = _reload_locked_entry(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
        )
        if int(state["revision"]) != route_revision or _digest(entry) != route_entry_sha256:
            raise StaleFacts("runtime registry changed before the canonical container lock was acquired")
        yield state_path, container, state, entry, identities


def _replace_registry_observed(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    state: Mapping[str, Any],
    desired_entry: Mapping[str, Any],
    worktree_ref: str,
) -> dict[str, Any]:
    """Resolve a CAS exception by observing whether its exact write landed."""

    try:
        return _replace_registry(
            state_path,
            _put_entry(state, desired_entry, worktree_ref),
            int(state["revision"]),
        )
    except Exception:
        current_state, current_entry = _reload_locked_entry(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
        )
        if _digest(current_entry) == _digest(desired_entry):
            return current_state
        raise


def _new_entry(
    container: Path,
    direction: str,
    kind: str,
    assignment: str,
    base: str,
    token: str,
    integration_policy: str,
    parallel_set_authorization: Mapping[str, Any] | None,
    required_handoff_sha: str | None,
    required_dependency_refs: Sequence[Mapping[str, str]],
    mutation_lease: Mapping[str, Any] | None,
) -> dict[str, Any]:
    ref = _worktree_ref(direction, kind, assignment)
    target = _target_path(container, direction, kind, assignment)
    branch = _branch_name(direction, kind, assignment)
    return {
        "assignment_id": assignment,
        "base_sha": base,
        "branch": branch,
        "candidate_sha": None,
        "canonical_absolute_path": str(target),
        "direction_id": direction,
        "integrated_sha": None,
        "integration_policy": integration_policy,
        "kind": kind,
        "lifecycle": "PROVISIONING",
        "operation_token": token,
        "parallel_set_authorization": (
            dict(parallel_set_authorization) if parallel_set_authorization is not None else None
        ),
        "receipt_path": f"temp/runtime/receipts/{ref}.json",
        "mutation_lease": dict(mutation_lease) if mutation_lease is not None else None,
        "required_dependency_refs": [
            dict(item) for item in required_dependency_refs
        ],
        "required_handoff_sha": required_handoff_sha,
        "unknown_outcome": None,
        "worktree_ref": ref,
    }


def _receipt_skeleton(repo: Path, container: Path, entry: Mapping[str, Any], registry_revision: int) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "worktree_ref": entry["worktree_ref"],
        "operation_token": entry["operation_token"],
        "repo": str(repo),
        "container": str(container),
        "direction_id": entry["direction_id"],
        "kind": entry["kind"],
        "assignment_id": entry["assignment_id"],
        "worktree_path": entry["canonical_absolute_path"],
        "branch": entry["branch"],
        "base_sha": entry["base_sha"],
        "candidate_sha": entry.get("candidate_sha"),
        "integration_policy": _integration_policy(entry),
        "parallel_set_authorization": entry.get("parallel_set_authorization"),
        "required_handoff_sha": entry.get("required_handoff_sha"),
        "required_dependency_refs": list(entry.get("required_dependency_refs", [])),
        "registry_revision": registry_revision,
        "lifecycle": entry["lifecycle"],
        "changed_paths": [],
        "allowed_paths": [],
        "mutation_lease": entry.get("mutation_lease"),
        "verification_evidence": {"status": "MISSING", "refs": [], "missing": []},
        "conflict": {"status": "NOT_CHECKED", "detail": None},
        "facts": None,
        "facts_sha256": None,
        "integration": None,
        "created_at": _now(),
        "last_failure": None,
        "apply_outcome": None,
        "release_outcome": None,
        "discarded_paths": [],
        "retention_reason": None,
        "unknown_outcome": None,
        "history": [],
        "provision_failures": [],
    }


def _write_receipt_for(repo: Path, entry: Mapping[str, Any], receipt: Mapping[str, Any]) -> Path:
    path = _receipt_path(repo, entry)
    _atomic_write(path, receipt)
    return path


def _load_receipt(repo: Path, entry: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = _receipt_path(repo, entry)
    if _lstat(path) is None or not path.is_file():
        raise UnsafeState(f"worktree receipt is absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidInput(f"worktree receipt is unreadable: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != RECEIPT_SCHEMA:
        raise InvalidInput("worktree receipt schema is invalid")
    for key in ("worktree_ref", "operation_token", "repo", "worktree_path", "branch", "base_sha"):
        if key not in value:
            raise InvalidInput(f"worktree receipt lacks {key}")
    if value["worktree_ref"] != entry["worktree_ref"] or value["operation_token"] != entry.get("operation_token"):
        raise StaleFacts("worktree receipt operation token does not match registry")
    if Path(str(value["repo"])) != repo or Path(str(value["worktree_path"])) != Path(str(entry["canonical_absolute_path"])):
        raise OwnershipRefusal("worktree receipt repository/path identity mismatch")
    if value["branch"] != entry["branch"] or value["base_sha"] != entry["base_sha"]:
        raise StaleFacts("worktree receipt base or branch fact changed")
    return path, value


def _load_current_receipt(
    repo: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    path, receipt = _load_receipt(repo, entry)
    revision = receipt.get("registry_revision")
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision < 1
        or revision > int(state["revision"])
    ):
        raise StaleFacts("worktree receipt registry revision is invalid or newer than the locked registry")
    if receipt.get("lifecycle") != entry.get("lifecycle"):
        raise StaleFacts("worktree receipt lifecycle does not match the locked registry")
    if receipt.get("candidate_sha") != entry.get("candidate_sha"):
        raise StaleFacts("worktree receipt candidate does not match the locked registry")
    if entry.get("lifecycle") == "INTEGRATED" and receipt.get("applied_sha") != entry.get("integrated_sha"):
        raise StaleFacts("integrated receipt SHA does not match the locked registry")
    return path, receipt


def _refresh_locked_documents(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    worktree_ref: str,
    expected_state: Mapping[str, Any],
    expected_entry: Mapping[str, Any],
    expected_receipt_path: Path,
    expected_receipt: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    if _digest(state) != _digest(expected_state) or _digest(entry) != _digest(expected_entry):
        raise StaleFacts("runtime registry advanced while the canonical container lock was held")
    receipt_path, receipt = _load_current_receipt(repo, state, entry)
    if not _same_path(receipt_path, expected_receipt_path) or _digest(receipt) != _digest(expected_receipt):
        raise StaleFacts("worktree receipt advanced while the canonical container lock was held")
    return state, entry, receipt


def _documents_after_registry_transition(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    worktree_ref: str,
    desired_entry: Mapping[str, Any],
    previous_receipt_path: Path,
    previous_receipt: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    if _digest(entry) != _digest(desired_entry):
        raise UnknownApply("registry transition outcome changed before receipt persistence")
    receipt_path, receipt = _load_receipt(repo, entry)
    if not _same_path(receipt_path, previous_receipt_path) or _digest(receipt) != _digest(previous_receipt):
        raise UnknownApply("registry transitioned but its receipt changed before persistence")
    return state, entry, receipt


def _observation(repo: Path, entry: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(str(entry["canonical_absolute_path"]))
    branch = str(entry["branch"])
    observed: dict[str, Any] = {
        "worktree_ref": entry["worktree_ref"],
        "lifecycle": entry.get("lifecycle"),
        "path": str(target),
        "branch": branch,
        "base_sha": str(entry.get("base_sha", "")).lower(),
        "candidate_sha": entry.get("candidate_sha"),
        "target_exists": bool(_lstat(target)),
        "registration_count": 0,
        "registration_branch": None,
        "registration_head": None,
        "branch_sha": _branch_sha(repo, branch),
        "status": None,
    }
    try:
        _canonical_path(target, label="registered worktree", must_exist=False)
    except WorktreeError as exc:
        observed["path_error"] = str(exc)
    registrations = _registration(repo, target)
    observed["registration_count"] = len(registrations)
    if len(registrations) == 1:
        observed["registration_branch"] = registrations[0].get("branch")
        observed["registration_head"] = registrations[0].get("head")
    if target.is_dir() and not target.is_symlink() and len(registrations) == 1:
        try:
            observed["status"] = _status(target)
        except WorktreeError as exc:
            observed["status_error"] = str(exc)
    exact = (
        target.is_dir()
        and not target.is_symlink()
        and len(registrations) == 1
        and registrations[0].get("branch") == f"refs/heads/{branch}"
        and str(registrations[0].get("head", "")).lower() == str(entry.get("candidate_sha") or entry.get("base_sha", "")).lower()
        and observed["branch_sha"] == str(registrations[0].get("head", "")).lower()
    )
    observed["exact_registration"] = exact
    if entry.get("lifecycle") == "PROVISIONING":
        if exact:
            observed["orphaned"] = True
            observed["orphan_reason"] = "PROVISIONING_GIT_MUTATION_UNCOMMITTED"
        elif not observed["target_exists"] and observed["registration_count"] == 0:
            observed["orphaned"] = True
            observed["orphan_reason"] = "PROVISIONING_JOURNAL_WITHOUT_GIT_MUTATION"
        else:
            observed["orphaned"] = True
            observed["orphan_reason"] = "PROVISIONING_IDENTITY_MISMATCH"
    elif entry.get("lifecycle") in UNKNOWN_LIFECYCLES:
        observed["orphaned"] = True
        observed["orphan_reason"] = entry["lifecycle"]
        observed["unknown_outcome"] = entry.get("unknown_outcome")
    elif entry.get("lifecycle") == "RETAINED_FOR_RECOVERY":
        observed["orphaned"] = not exact
        if observed["orphaned"]:
            observed["orphan_reason"] = "RETAINED_REGISTRATION_MISMATCH"
    elif entry.get("lifecycle") == "RELEASED":
        observed["orphaned"] = not (
            not observed["target_exists"]
            and observed["registration_count"] == 0
            and observed["branch_sha"] is None
        )
        if observed["orphaned"]:
            observed["orphan_reason"] = "RELEASED_REGISTRATION_REMAINS"
    else:
        observed["orphaned"] = False
        if not exact:
            observed["orphaned"] = True
            observed["orphan_reason"] = "REGISTERED_WORKTREE_FACT_MISMATCH"
    return observed


def _effect_observation(repo: Path, entry: Mapping[str, Any]) -> dict[str, Any]:
    target = Path(str(entry["canonical_absolute_path"]))
    registrations = _registration(repo, target)
    registration = registrations[0] if len(registrations) == 1 else {}
    return {
        "target_sha": _branch_sha(repo, TARGET_BRANCH),
        "worktree_exists": _lstat(target) is not None,
        "registration_count": len(registrations),
        "registration_branch": registration.get("branch"),
        "registration_head": registration.get("head"),
        "branch_sha": _branch_sha(repo, str(entry["branch"])),
    }


def _entry_authority(entry: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "worktree_ref",
        "direction_id",
        "kind",
        "assignment_id",
        "canonical_absolute_path",
        "branch",
        "base_sha",
        "candidate_sha",
        "operation_token",
        "receipt_path",
        "integration_policy",
        "parallel_set_authorization",
        "required_handoff_sha",
        "required_dependency_refs",
        "mutation_lease",
    )
    return {key: entry.get(key) for key in keys}


def _landed_registry_transition(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    worktree_ref: str,
    desired_entry: Mapping[str, Any],
) -> dict[str, Any] | None:
    state, entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    return state if _digest(entry) == _digest(desired_entry) else None


def _journal_unknown_after_effect(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    worktree_ref: str,
    prior_state: Mapping[str, Any],
    prior_entry: Mapping[str, Any],
    prior_receipt_path: Path,
    prior_receipt: Mapping[str, Any],
    *,
    operation: str,
    error: str,
) -> dict[str, Any]:
    if operation not in {"APPLY", "RELEASE"}:
        raise ValueError(f"unsupported unknown worktree operation: {operation}")
    state, entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    if _entry_authority(entry) != _entry_authority(prior_entry):
        raise UnknownApply(
            f"{operation.lower()} effect occurred but registry authority changed; receipt cannot be safely rewritten",
            details={"observation": _effect_observation(repo, prior_entry)},
        )
    receipt_path, receipt = _load_receipt(repo, entry)
    if not _same_path(receipt_path, prior_receipt_path):
        raise UnknownApply(f"{operation.lower()} effect occurred but the authorized receipt path changed")
    observed_at = _now()
    journal = {
        "operation": operation,
        "status": "UNKNOWN",
        "recorded_at": observed_at,
        "error": error or f"{operation.lower()} registry transition failed",
        "registry_revision_before": int(prior_state["revision"]),
        "registry_revision_observed": int(state["revision"]),
        "observation": _effect_observation(repo, entry),
    }
    receipt_journal = dict(journal)
    receipt_journal["receipt_sha256_before"] = _digest(prior_receipt)
    receipt_journal["receipt_sha256_observed"] = _digest(receipt)
    receipt_journal["receipt_advanced"] = (
        receipt_journal["receipt_sha256_before"] != receipt_journal["receipt_sha256_observed"]
    )
    can_record_registry = _digest(entry) == _digest(prior_entry)
    receipt_journal["registry_reconciliation"] = "PENDING" if can_record_registry else "REFUSED_CHANGED_ENTRY"
    unknown_receipt = dict(receipt)
    unknown_receipt["unknown_outcome"] = receipt_journal
    unknown_receipt[f"{operation.lower()}_outcome"] = "UNKNOWN"
    unknown_receipt[f"{operation.lower()}_error"] = journal["error"]
    unknown_receipt["last_failure"] = {"at": observed_at, "message": journal["error"]}
    _atomic_write(receipt_path, unknown_receipt)
    if not can_record_registry:
        return receipt_journal

    current_state, current_entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    current_receipt_path, current_receipt = _load_receipt(repo, current_entry)
    if (
        _digest(current_entry) != _digest(prior_entry)
        or not _same_path(current_receipt_path, receipt_path)
        or current_receipt.get("unknown_outcome") != receipt_journal
    ):
        receipt_journal["registry_reconciliation"] = "REFUSED_CHANGED_FACTS"
        current_receipt["unknown_outcome"] = receipt_journal
        _atomic_write(current_receipt_path, current_receipt)
        return receipt_journal

    unknown_entry = dict(current_entry)
    unknown_entry["lifecycle"] = f"{operation}_OUTCOME_UNKNOWN"
    unknown_entry["unknown_outcome"] = journal
    try:
        reconciled_state = _replace_registry(
            state_path,
            _put_entry(current_state, unknown_entry, worktree_ref),
            int(current_state["revision"]),
        )
    except Exception as exc:
        landed = _landed_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            unknown_entry,
        )
        if landed is None:
            receipt_journal["registry_reconciliation"] = "CAS_FAILED"
            receipt_journal["registry_reconciliation_error"] = str(exc)
            latest_path, latest_receipt = _load_receipt(repo, current_entry)
            latest_receipt["unknown_outcome"] = receipt_journal
            _atomic_write(latest_path, latest_receipt)
            return receipt_journal
        reconciled_state = landed

    reconciled_state, reconciled_entry = _reload_locked_entry(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
    )
    if _digest(reconciled_entry) != _digest(unknown_entry):
        receipt_journal["registry_reconciliation"] = "CHANGED_AFTER_RECORD"
        latest_path, latest_receipt = _load_receipt(repo, reconciled_entry)
        latest_receipt["unknown_outcome"] = receipt_journal
        _atomic_write(latest_path, latest_receipt)
        return receipt_journal
    latest_path, latest_receipt = _load_receipt(repo, reconciled_entry)
    receipt_journal["registry_reconciliation"] = "RECORDED"
    latest_receipt["unknown_outcome"] = receipt_journal
    latest_receipt["lifecycle"] = reconciled_entry["lifecycle"]
    latest_receipt["registry_revision"] = int(reconciled_state["revision"])
    _atomic_write(latest_path, latest_receipt)
    return receipt_journal


def _facts(
    repo: Path,
    common: Path,
    container: Path,
    entry: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    target_sha: str,
    changed_paths: Sequence[str],
    allowed_paths: Sequence[str],
    verification: Mapping[str, Any],
    conflict: Mapping[str, Any],
) -> dict[str, Any]:
    target = Path(str(entry["canonical_absolute_path"]))
    registrations = _registration(repo, target)
    status = _status(target)
    registration = registrations[0] if len(registrations) == 1 else {}
    parent = _candidate_parent(repo, str(entry["candidate_sha"])) if entry.get("candidate_sha") else None
    return {
        "registry_revision": int(state["revision"]),
        "registry_entry_sha256": _digest(entry),
        "repo": str(repo),
        "git_common_dir": str(common),
        "container": str(container),
        "container_identity": _identity(container),
        "container_parent_identity": _identity(container.parent),
        "worktree": str(target),
        "worktree_identity": _identity(target),
        "worktree_ref": entry["worktree_ref"],
        "operation_token": entry["operation_token"],
        "branch": entry["branch"],
        "branch_sha": _branch_sha(repo, str(entry["branch"])),
        "registration_branch": registration.get("branch"),
        "registration_head": registration.get("head"),
        "candidate_sha": entry.get("candidate_sha"),
        "candidate_parent": parent,
        "base_sha": entry["base_sha"],
        "target_branch": TARGET_BRANCH,
        "target_sha": target_sha,
        "current_branch": _current_branch(repo),
        "changed_paths": list(changed_paths),
        "allowed_paths": list(allowed_paths),
        "status": status,
        "verification": dict(verification),
        "conflict": dict(conflict),
    }


def _target_observation(repo: Path, target: str) -> tuple[str, dict[str, list[str] | bool]]:
    if target != TARGET_BRANCH:
        raise OwnershipRefusal("integration target must be exactly omp/workflow")
    if not target.startswith("omp/"):
        raise OwnershipRefusal("target branch is outside omp/*")
    sha = _branch_sha(repo, target)
    if sha is None:
        raise UnsafeState("target branch does not exist")
    if _current_branch(repo) != target:
        raise OwnershipRefusal("Root integration requires omp/workflow checked out")
    status = _status(repo)
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("target worktree is dirty")
    return sha, status


def _verification(refs: Sequence[str], repo: Path) -> dict[str, Any]:
    normalized: list[str] = []
    missing: list[str] = []
    observed: list[dict[str, str]] = []
    for raw in refs:
        value = _validate_relative(raw, label="verification reference")
        if value in normalized:
            raise InvalidInput("verification references contain duplicate paths")
        normalized.append(value)
        candidate = repo / Path(value)
        if not candidate.is_file():
            missing.append(value)
            continue
        path = _canonical_path(
            candidate, label="verification reference", must_exist=True
        )
        if not _under(path, repo):
            raise OwnershipRefusal("verification reference escaped the repository")
        observed.append(
            {
                "path": value,
                "sha256": _hash_file(path, label="verification reference"),
            }
        )
    observed.sort(key=lambda item: item["path"])
    missing.sort()
    return {
        "status": "PRESENT" if normalized and not missing else "MISSING",
        "refs": observed,
        "missing": missing,
    }


def _safe_provision_observation(repo: Path, entry: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return _observation(repo, entry)
    except Exception as exc:
        return {
            "worktree_ref": entry.get("worktree_ref"),
            "path": entry.get("canonical_absolute_path"),
            "branch": entry.get("branch"),
            "observation_error": str(exc),
        }


def _failure_status(
    observation: Mapping[str, Any],
    observed_status: Mapping[str, Any] | None,
) -> dict[str, list[str]]:
    source = observed_status if observed_status is not None else observation.get("status")
    if not isinstance(source, Mapping):
        source = {}
    result: dict[str, list[str]] = {}
    for key in ("tracked_dirty", "nonignored_untracked", "ignored_only"):
        value = source.get(key)
        result[key] = sorted({str(path) for path in value}) if isinstance(value, list) else []
    return result


def _begin_provision_failure(
    receipt_path: Path,
    receipt: Mapping[str, Any],
    *,
    operation: str,
    phase: str,
    message: str,
    observation: Mapping[str, Any],
    observed_status: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    at = _now()
    status = _failure_status(observation, observed_status)
    failure = {
        "failure_id": secrets.token_hex(8),
        "at": at,
        "operation": operation,
        "phase": phase,
        "message": message,
        **status,
        "observation": dict(observation),
        "rollback": {
            "outcome": "PENDING",
            "before": dict(observation),
            "after": None,
        },
    }
    updated = dict(receipt)
    failures = list(receipt.get("provision_failures", [])) if isinstance(receipt.get("provision_failures"), list) else []
    failures.append(failure)
    history = list(receipt.get("history", [])) if isinstance(receipt.get("history"), list) else []
    history.append(
        {
            "at": at,
            "event": f"{operation.replace('-', '_').upper()}_FAILED",
            "failure_id": failure["failure_id"],
            "phase": phase,
        }
    )
    updated["last_failure"] = failure
    updated["provision_failures"] = failures
    updated["history"] = history
    try:
        _atomic_write(receipt_path, updated)
    except Exception as exc:
        failure["diagnostic_write_error"] = str(exc)
        failures[-1] = failure
        updated["last_failure"] = failure
        updated["provision_failures"] = failures
    return updated, failure


def _complete_provision_failure(
    receipt_path: Path,
    receipt: Mapping[str, Any],
    failure: Mapping[str, Any],
    rollback: Mapping[str, Any],
) -> dict[str, Any]:
    completed = dict(failure)
    completed["rollback"] = dict(rollback)
    updated = dict(receipt)
    failures = list(receipt.get("provision_failures", [])) if isinstance(receipt.get("provision_failures"), list) else []
    for index in range(len(failures) - 1, -1, -1):
        candidate = failures[index]
        if isinstance(candidate, Mapping) and candidate.get("failure_id") == failure.get("failure_id"):
            failures[index] = completed
            break
    updated["last_failure"] = completed
    updated["provision_failures"] = failures
    try:
        _atomic_write(receipt_path, updated)
    except Exception:
        pass
    return updated


def _rollback_provision_effect(
    repo: Path,
    entry: Mapping[str, Any],
    *,
    add_attempted: bool,
    target_identity: Mapping[str, Any] | None,
    before: Mapping[str, Any],
) -> dict[str, Any]:
    target = Path(str(entry["canonical_absolute_path"]))
    branch = str(entry["branch"])
    base = str(entry["base_sha"]).lower()
    rollback: dict[str, Any] = {
        "attempted": False,
        "outcome": "NOT_ATTEMPTED",
        "before": dict(before),
        "after": None,
    }
    if not add_attempted:
        rollback["after"] = _safe_provision_observation(repo, entry)
        return rollback
    all_absent = (
        not before.get("target_exists")
        and before.get("registration_count") == 0
        and before.get("branch_sha") is None
    )
    if all_absent:
        rollback["outcome"] = "NO_EFFECT"
        rollback["after"] = dict(before)
        return rollback
    exact_created = (
        target_identity is not None
        and target.is_dir()
        and not target.is_symlink()
        and _identity_equal(target, target_identity)
        and before.get("registration_count") == 1
        and before.get("registration_branch") == f"refs/heads/{branch}"
        and str(before.get("registration_head", "")).lower() == base
        and before.get("branch_sha") == base
    )
    if not exact_created:
        rollback["outcome"] = "REFUSED_CHANGED_FACTS"
        rollback["after"] = dict(before)
        return rollback
    rollback["attempted"] = True
    try:
        _run_git(repo, "worktree", "remove", "--force", str(target))
        after_remove = _safe_provision_observation(repo, entry)
        if (
            not after_remove.get("target_exists")
            and after_remove.get("registration_count") == 0
            and after_remove.get("branch_sha") == base
        ):
            _run_git(repo, "update-ref", "-d", f"refs/heads/{branch}", base)
        after = _safe_provision_observation(repo, entry)
        rollback["after"] = after
        if (
            not after.get("target_exists")
            and after.get("registration_count") == 0
            and after.get("branch_sha") is None
        ):
            rollback["outcome"] = "COMPLETE"
        else:
            rollback["outcome"] = "INCOMPLETE"
    except Exception as exc:
        rollback["outcome"] = "FAILED"
        rollback["error"] = str(exc)
        rollback["after"] = _safe_provision_observation(repo, entry)
    return rollback


def _verify_added_worktree(
    repo: Path,
    entry: Mapping[str, Any],
    target_identity: Mapping[str, Any],
) -> dict[str, list[str] | bool]:
    target = Path(str(entry["canonical_absolute_path"]))
    branch = str(entry["branch"])
    base = str(entry["base_sha"]).lower()
    if not _identity_equal(target, target_identity):
        raise UnsafeState("worktree target identity changed after git worktree add")
    registrations = _registration(repo, target)
    branch_sha = _branch_sha(repo, branch)
    if (
        len(registrations) != 1
        or registrations[0].get("branch") != f"refs/heads/{branch}"
        or str(registrations[0].get("head", "")).lower() != base
        or branch_sha != base
    ):
        raise UnsafeState("created worktree registration failed exact identity checks")
    status = _status(target)
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("created worktree is not clean", details={"status": status})
    return status




def _reconcile_provisioning(state_path: Path, state: dict[str, Any], entry: dict[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    if entry.get("lifecycle") != "PROVISIONING" or not observation.get("exact_registration"):
        raise UnsafeState("an existing worktree journal requires exact Root reconciliation", details={"observation": observation})
    updated_entry = dict(entry)
    updated_entry["lifecycle"] = "PROVISIONED"
    updated_state = _put_entry(state, updated_entry, str(entry["worktree_ref"]))
    final = _replace_registry(state_path, updated_state, int(state["revision"]))
    return _entry(final, str(entry["worktree_ref"]))


def provision(
    repo_raw: str,
    container_raw: str | None,
    direction: str,
    kind: str,
    assignment: str,
    base_raw: str,
    integration_policy_raw: str | None = None,
    parallel_set_manifest_raw: str | None = None,
    required_handoff_raw: str | None = None,
    required_dependency_refs_raw: Sequence[Mapping[str, Any]] | None = None,
    mutation_lease_raw: Mapping[str, Any] | None = None,
    expected_raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    direction = _validate_direction(direction)
    kind = _validate_kind(kind)
    assignment = _validate_assignment(assignment)
    base = _verify_commit(repo, base_raw, label="base")
    integration_policy = _validate_integration_policy(integration_policy_raw)
    mutation_lease = _validate_mutation_lease(
        repo,
        assignment,
        mutation_lease_raw,
        required=True,
    )
    required_dependency_refs = _validate_required_dependency_refs(
        repo, required_dependency_refs_raw
    )
    if integration_policy in EXACT_POLICIES and required_handoff_raw is None:
        raise InvalidInput("exact provision requires --required-handoff-sha")
    if integration_policy == "ORTHOGONAL_DIRECTION" and required_handoff_raw is not None:
        raise OwnershipRefusal("orthogonal provision cannot carry a required handoff")
    required_handoff_sha = (
        _validate_commit(required_handoff_raw, label="required handoff")
        if required_handoff_raw is not None
        else None
    )
    parallel_set_authorization: dict[str, Any] | None = None
    if integration_policy == "ORTHOGONAL_DIRECTION":
        if parallel_set_manifest_raw is None:
            raise InvalidInput("orthogonal provision requires --parallel-set-manifest")
        manifest, parallel_set_authorization = _load_parallel_set_manifest(
            repo, parallel_set_manifest_raw
        )
        if manifest["common_epoch_sha"] != base:
            raise StaleFacts("worktree base differs from the parallel-set common epoch")
        direction_authority = _parallel_direction(
            manifest,
            direction_id=direction,
            kind=kind,
            assignment_id=assignment,
        )
        if required_handoff_sha != direction_authority["required_handoff_sha"]:
            raise StaleFacts("required handoff differs from parallel-set authorization")
        if required_dependency_refs != direction_authority["required_dependencies"]:
            raise StaleFacts(
                "required dependency refs differ from parallel-set authorization"
            )
    elif parallel_set_manifest_raw is not None:
        raise OwnershipRefusal("exact integration policy cannot carry a parallel-set manifest")
    if integration_policy in EXACT_POLICIES and required_handoff_sha != base:
        raise StaleFacts("exact integration required handoff must equal the declared base")
    container = _validate_container(Path(container_raw) if container_raw else _default_container(repo), repo, common, create=True)
    target = _target_path(container, direction, kind, assignment)
    branch = _branch_name(direction, kind, assignment)
    ref = _worktree_ref(direction, kind, assignment)
    with _container_lock(container) as identities:
        _revalidate_container(container, identities)
        state_path, state = _initialize_registry(repo)
        _validate_operation_expectations(
            repo,
            container,
            state,
            None,
            None,
            expected_raw,
            absent_worktree_path=target,
        )
        existing = [
            row
            for row in state.get("worktrees", [])
            if isinstance(row, dict)
            and (
                row.get("worktree_ref") == ref
                or row.get("canonical_absolute_path") == str(target)
                or row.get("branch") == branch
            )
        ]
        if existing:
            old = dict(existing[0])
            observation = _observation(repo, old)
            if old.get("lifecycle") == "PROVISIONING" and observation.get("exact_registration"):
                reconciled = _reconcile_provisioning(state_path, state, old, observation)
                return {"ok": True, "operation": "provision", "reconciled": True, "worktree": reconciled, "observation": observation}
            raise UnsafeState("worktree_ref is already journaled", details={"worktree": old, "observation": observation})
        if _lstat(target) is not None:
            raise OwnershipRefusal(f"worktree target already exists: {target}")
        if _branch_sha(repo, branch) is not None:
            raise UnsafeState("temporary branch already exists")
        if _registration(repo, target):
            raise UnsafeState("worktree target is already registered by Git")
        token = secrets.token_hex(16)
        entry = _new_entry(
            container,
            direction,
            kind,
            assignment,
            base,
            token,
            integration_policy,
            parallel_set_authorization,
            required_handoff_sha,
            required_dependency_refs,
            mutation_lease,
        )
        state_with_entry = dict(state)
        state_with_entry["worktrees"] = [*state.get("worktrees", []), entry]

        journal = _replace_registry(state_path, state_with_entry, int(state["revision"]))
        receipt = _receipt_skeleton(repo, container, entry, int(journal["revision"]))
        receipt_path = _write_receipt_for(repo, entry, receipt)
        add_attempted = False
        target_identity: Mapping[str, Any] | None = None
        observed_status: Mapping[str, Any] | None = None
        phase = "PRE_ADD_VALIDATION"
        try:
            _revalidate_container(container, identities)
            if _lstat(target) is not None or _branch_sha(repo, branch) is not None:
                raise UnsafeState("worktree namespace changed after PROVISIONING journal")
            phase = "GIT_WORKTREE_ADD"
            add_attempted = True
            _run_git(repo, "worktree", "add", "-b", branch, str(target), base)
            phase = "TARGET_IDENTITY"
            target_identity = _identity(target)
            _revalidate_container(container, identities)
            phase = "POST_ADD_VALIDATION"
            observed_status = _verify_added_worktree(repo, entry, target_identity)
            phase = "REGISTRY_TRANSITION"
            final_entry = dict(entry)
            final_entry["lifecycle"] = "PROVISIONED"
            final_state = _replace_registry_observed(
                repo,
                common,
                container,
                identities,
                state_path,
                journal,
                final_entry,
                ref,
            )
        except Exception as exc:
            if observed_status is None and isinstance(exc, WorktreeError):
                detail_status = exc.details.get("status")
                if isinstance(detail_status, Mapping):
                    observed_status = detail_status
            if target_identity is None and target.is_dir() and not target.is_symlink():
                try:
                    target_identity = _identity(target)
                except OSError:
                    pass
            observation = _safe_provision_observation(repo, entry)
            if observed_status is not None:
                observation["status"] = dict(observed_status)
            failed_receipt, failure = _begin_provision_failure(
                receipt_path,
                receipt,
                operation="provision",
                phase=phase,
                message=str(exc),
                observation=observation,
                observed_status=observed_status,
            )
            rollback = _rollback_provision_effect(
                repo,
                entry,
                add_attempted=add_attempted,
                target_identity=target_identity,
                before=observation,
            )
            _complete_provision_failure(receipt_path, failed_receipt, failure, rollback)
            if isinstance(exc, WorktreeError):
                raise
            raise WorktreeError(str(exc)) from exc
        receipt["registry_revision"] = int(final_state["revision"])
        receipt["lifecycle"] = "PROVISIONED"
        receipt["provisioned_at"] = _now()
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "provision",
            "worktree": final_entry,
            "receipt": str(receipt_path),
            "registry_revision": final_state["revision"],
        }





def inspect(
    repo_raw: str,
    worktree_ref: str,
    expected_raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    loaded = _load_registry(repo)
    assert loaded is not None
    state_path, route_state = loaded
    route_entry = _entry(route_state, worktree_ref)
    container = _validate_container(
        Path(str(route_entry["canonical_absolute_path"])).parent,
        repo,
        common,
        create=False,
    )
    with _container_lock(container) as identities:
        state, entry = _reload_locked_entry(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
        )
        receipt_path, receipt = _load_receipt(repo, entry)
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        observation = _observation(repo, entry)
        parallel_direction = None
        if _integration_policy(entry) == "ORTHOGONAL_DIRECTION":
            _, parallel_direction, _ = _orthogonal_authorization(repo, entry)
    result = {
        "ok": True,
        "operation": "inspect",
        "worktree": entry,
        "observation": observation,
        "receipt_ref": {
            "path": receipt_path.relative_to(repo).as_posix(),
            "sha256": _hash_file(receipt_path, label="worktree receipt"),
        },
        "parallel_direction": parallel_direction,
        "orphaned": bool(observation.get("orphaned")),
        "orphan_reason": observation.get("orphan_reason"),
        "registry_revision": state["revision"],
    }
    if observation.get("orphaned"):
        raise UnsafeState(
            "worktree journal and Git registration require reconciliation",
            details=result,
        )
    return result


def inspect_repository(
    repo_raw: str,
    target: str,
    remote_name: str | None = None,
    remote_ref: str | None = None,
) -> dict[str, Any]:
    """Return exact read-only repository and optional remote-target facts."""

    repo, common = _repo_context(repo_raw)
    target_key = _target_lock_key(common, target)
    target_sha = _branch_sha(repo, target)
    if (remote_name is None) != (remote_ref is None):
        raise InvalidInput("remote name and ref must be supplied together")
    result: dict[str, Any] = {
        "ok": True,
        "operation": "inspect-repository",
        "common_path": str(common),
        "target_lock_key": target_key,
        "target_sha": target_sha,
    }
    if remote_name is None or remote_ref is None:
        return result
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", remote_name) is None:
        raise InvalidInput("remote name is invalid")
    if (
        not remote_ref.startswith("refs/heads/")
        or _run_git(repo, "check-ref-format", remote_ref, check=False).returncode
    ):
        raise InvalidInput("remote ref is invalid")
    remote_result = _run_git(
        repo,
        "ls-remote",
        "--refs",
        remote_name,
        remote_ref,
        check=False,
    )
    rows = [
        line.split()
        for line in remote_result.stdout.splitlines()
        if line.strip()
    ]
    remote_sha = None
    if (
        remote_result.returncode == 0
        and len(rows) == 1
        and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", rows[0][0])
    ):
        remote_sha = rows[0][0]
    result["remote_target"] = {
        "local_sha": target_sha,
        "remote_sha": remote_sha,
        "remote_observation_succeeded": remote_result.returncode == 0,
    }
    return result


def validate_candidate(
    repo_raw: str,
    base_raw: str,
    candidate_raw: str,
    allowed_paths_raw: Sequence[str],
    expected_changed_paths_raw: Sequence[str],
    expected_diff_sha256_raw: str,
) -> dict[str, Any]:
    """Validate one frozen candidate tree without mutating Git or runtime state."""

    repo, _ = _repo_context(repo_raw)
    base = _verify_commit(repo, base_raw, label="candidate base")
    candidate = _verify_commit(repo, candidate_raw, label="candidate")
    allowed_paths = _strict_path_list(
        list(allowed_paths_raw),
        label="candidate allowed paths",
    )
    expected_changed_paths = _strict_path_list(
        list(expected_changed_paths_raw),
        label="candidate expected changed paths",
    )
    expected_diff_sha256 = _validate_sha256(
        expected_diff_sha256_raw,
        label="candidate expected structural delta",
    )
    delta = _canonical_tree_delta(repo, base, candidate)
    changed_paths = [record["path"] for record in delta["records"]]
    if (
        changed_paths != expected_changed_paths
        or delta["sha256"] != expected_diff_sha256
    ):
        raise StaleFacts("candidate structural delta differs from frozen facts")
    out_of_scope = [
        path
        for path in changed_paths
        if not any(_relative_under(path, allowed) for allowed in allowed_paths)
    ]
    if out_of_scope:
        raise OwnershipRefusal(
            "candidate changed paths outside frozen allowlist: "
            + ", ".join(out_of_scope)
        )
    return {
        "ok": True,
        "operation": "validate-candidate",
        "base_sha": base,
        "candidate_sha": candidate,
        "allowed_paths": allowed_paths,
        "changed_paths": changed_paths,
        "delta": delta,
    }


def observe(repo_raw: str, worktree_ref: str) -> dict[str, Any]:
    """Return result-blind worktree facts without acquiring mutation authority."""

    repo, _ = _repo_context(repo_raw)
    loaded = _load_registry(repo)
    if loaded is None:
        return {
            "ok": True,
            "operation": "observe",
            "registry": {"status": "ABSENT"},
            "worktree": {"worktree_ref": worktree_ref, "status": "ABSENT"},
            "integration": None,
        }
    state_path, state = loaded
    registry = {
        "path": state_path.relative_to(repo).as_posix(),
        "sha256": _hash_file(state_path, label="runtime worktree registry"),
        "revision": state["revision"],
    }
    try:
        entry = _entry(state, worktree_ref)
    except WorktreeError:
        return {
            "ok": True,
            "operation": "observe",
            "registry": registry,
            "worktree": {"worktree_ref": worktree_ref, "status": "ABSENT"},
            "integration": None,
        }
    worktree = {
        "worktree_ref": entry["worktree_ref"],
        "lifecycle": entry.get("lifecycle"),
        "candidate_sha": entry.get("candidate_sha"),
        "integrated_sha": entry.get("integrated_sha"),
        "receipt_ref": None,
        "physical": _effect_observation(repo, entry),
    }
    integration = None
    try:
        receipt_path, receipt = _load_receipt(repo, entry)
        worktree["receipt_ref"] = {
            "path": receipt_path.relative_to(repo).as_posix(),
            "sha256": _hash_file(receipt_path, label="worktree receipt"),
        }
        receipt_integration = receipt.get("integration")
        if isinstance(receipt_integration, Mapping):
            candidate_facts = receipt_integration.get("candidate")
            integration = {
                "integration_policy": receipt_integration.get("policy"),
                "integration_phase": receipt_integration.get("phase"),
                "candidate_sha": (
                    candidate_facts.get("candidate_sha")
                    if isinstance(candidate_facts, Mapping)
                    else receipt_integration.get("candidate_sha")
                ),
                "integrated_sha": receipt_integration.get("integration_sha"),
                "remote_prefetch_sha": receipt_integration.get(
                    "remote_prefetch_sha"
                ),
                "remote_post_observation_sha": receipt_integration.get(
                    "remote_post_observation_sha"
                ),
                "reconciliation_observations": receipt_integration.get(
                    "reconciliation_observations"
                ),
                "push_attempts": receipt_integration.get("push_attempts"),
                "local_apply_attempts": receipt_integration.get(
                    "local_apply_attempts"
                ),
            }
    except WorktreeError as exc:
        worktree["receipt_status"] = type(exc).__name__
    return {
        "ok": True,
        "operation": "observe",
        "registry": registry,
        "worktree": worktree,
        "integration": integration,
    }

def _require_exact_worktree_mutation(
    expected: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if expected is None:
        raise InvalidInput("exact worktree mutation preconditions are required")
    return expected








def _reject_nested_repository_paths(worktree: Path, paths: Sequence[str]) -> None:
    for relative in paths:
        current = worktree / Path(relative)
        if current.is_dir():
            current = current / "__hmasd_leaf__"
        for parent in current.parents:
            if _same_path(parent, worktree):
                break
            if _lstat(parent / ".git") is not None:
                raise Unsupported(f"nested repository path is unsupported: {relative}")


def _validate_safe_content_delta(
    delta: Mapping[str, Any],
    *,
    expected_paths: Sequence[str],
    allowed_paths: Sequence[str],
) -> None:
    records = delta.get("records")
    if not isinstance(records, list):
        raise UnsafeState("canonical tree delta records are absent")
    changed = [str(record.get("path")) for record in records if isinstance(record, Mapping)]
    if changed != sorted(expected_paths):
        raise StaleFacts("computed changed paths differ from the frozen exact path set")
    out_of_scope = [
        path
        for path in changed
        if not any(_relative_under(path, allowed) for allowed in allowed_paths)
    ]
    if out_of_scope:
        raise OwnershipRefusal(
            "computed tree delta escapes the exact allowlist",
            details={"out_of_scope": out_of_scope},
        )
    for record in records:
        assert isinstance(record, Mapping)
        old_mode = str(record["old_mode"])
        new_mode = str(record["new_mode"])
        for mode in (old_mode, new_mode):
            if mode not in {"000000", "100644", "100755"}:
                raise Unsupported("symlink, submodule, and non-regular-file deltas are unsupported")
        if old_mode != "000000" and new_mode != "000000" and old_mode != new_mode:
            raise Unsupported("mode or type changes are unsupported")


def _reject_nested_repositories(worktree: Path) -> None:
    for root, directories, files in os.walk(worktree, followlinks=False):
        current = Path(root)
        if not _same_path(current, worktree) and ".git" in {*directories, *files}:
            raise Unsupported(f"nested repository is unsupported: {current}")
        directories[:] = [
            name
            for name in directories
            if name != ".git" and not (current / name).is_symlink()
        ]


def _write_immutable_json(
    root: Path,
    value: Mapping[str, Any],
) -> tuple[Path, dict[str, str]]:
    data = _json_bytes(value)
    digest = hashlib.sha256(data).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_chain(root, label="immutable receipt directory", require_existing=True)
    path = root / f"{digest}.json"
    fd, temporary = tempfile.mkstemp(prefix=f".{digest}.", suffix=".new", dir=root)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise UnsafeState("immutable receipt digest path contains different bytes")
        directory_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary_path.unlink()
    return path, {"path": path.as_posix(), "sha256": digest}


def _load_prepared_tree_receipt(
    repo: Path,
    raw_path: str,
    expected_sha256_raw: str,
) -> tuple[Path, dict[str, Any], dict[str, str]]:
    path = _canonical_path(raw_path, label="prepared-tree receipt", must_exist=True)
    if not _under(path, repo):
        raise OwnershipRefusal("prepared-tree receipt must be inside the canonical repository")
    expected_sha256 = _validate_sha256(
        expected_sha256_raw, label="prepared-tree receipt"
    )
    if _hash_file(path, label="prepared-tree receipt") != expected_sha256:
        raise StaleFacts("prepared-tree receipt bytes differ from the frozen digest")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidInput(f"prepared-tree receipt is unreadable: {exc}") from exc
    prepared = _require_object(
        value,
        label="prepared-tree receipt",
        keys={
            "schema",
            "worktree_ref",
            "operation_token",
            "base_sha",
            "baseline_tree_sha",
            "result_tree_sha",
            "patch_ref",
            "allowed_paths",
            "changed_paths",
            "diff_sha256",
            "delta",
            "manager_checkout",
        },
    )
    if prepared["schema"] != "hmasd.prepared-tree/v1":
        raise InvalidInput("prepared-tree receipt schema is invalid")
    return (
        path,
        prepared,
        {
            "path": path.relative_to(repo).as_posix(),
            "sha256": expected_sha256,
        },
    )


def _candidate_ref(worktree_ref: str, candidate: str) -> str:
    identity = hashlib.sha256(worktree_ref.encode("utf-8")).hexdigest()
    return f"refs/hmasd/candidates/{identity}/{candidate}"


def _ref_sha(repo: Path, ref: str) -> str | None:
    result = _run_git(repo, "rev-parse", "--verify", "--quiet", ref, check=False)
    if result.returncode:
        return None
    value = result.stdout.strip().lower()
    return value if _FULL_SHA.fullmatch(value) else None


def apply_patch(
    repo_raw: str,
    worktree_ref: str,
    base_raw: str,
    baseline_tree_raw: str,
    patch_raw: str,
    patch_sha256_raw: str,
    allowed_paths_raw: Sequence[str],
    expected_changed_paths_raw: Sequence[str],
    expected_delta_sha256_raw: str,
    expected_result_tree_raw: str,
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Prepare one exact patch tree without changing checkout, index, or HEAD."""

    expected = _require_exact_worktree_mutation(expected_raw)
    repo, common = _repo_context(repo_raw)
    base = _verify_commit(repo, base_raw, label="patch baseline")
    baseline_tree = _validate_commit(baseline_tree_raw, label="baseline tree")
    expected_result_tree = _validate_commit(expected_result_tree_raw, label="result tree")
    expected_delta_sha256 = _validate_sha256(
        expected_delta_sha256_raw, label="expected patch delta"
    )
    patch_sha256 = _validate_sha256(patch_sha256_raw, label="patch")
    patch_path = _canonical_path(patch_raw, label="patch", must_exist=True)
    if not _under(patch_path, repo):
        raise OwnershipRefusal("patch must be inside the canonical repository")
    if _hash_file(patch_path, label="patch") != patch_sha256:
        raise StaleFacts("patch bytes differ from the frozen digest")
    patch_bytes = patch_path.read_bytes()
    if b"GIT binary patch" in patch_bytes or b"Binary files " in patch_bytes:
        raise Unsupported("binary patches are unsupported")
    allowed_paths = _strict_path_list(list(allowed_paths_raw), label="allowed paths")
    expected_changed_paths = _strict_path_list(
        list(expected_changed_paths_raw), label="expected changed paths"
    )

    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(repo, container, state, entry, receipt, expected)
        if entry["lifecycle"] != "PROVISIONED":
            raise StaleFacts("apply-patch requires an exactly PROVISIONED worktree")
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        target, registration, status = _ensure_controlled_checkout(
            repo, entry, candidate=base
        )
        if status["tracked_dirty"] or status["nonignored_untracked"]:
            raise UnsafeState("apply-patch requires a clean baseline worktree")
        _reject_nested_repositories(target)
        baseline_entries = _run_git(target, "ls-tree", "-r", baseline_tree).stdout.splitlines()
        if any(line.startswith("160000 ") for line in baseline_entries):
            raise Unsupported("repositories with submodules are unsupported")
        head = _git_value(target, "rev-parse", "--verify", "HEAD").lower()
        if head != base or registration.get("head") != base:
            raise StaleFacts("worktree HEAD differs from the exact patch baseline")
        actual_baseline_tree = _git_value(
            target, "rev-parse", f"{base}^{{tree}}"
        ).lower()
        if actual_baseline_tree != baseline_tree:
            raise StaleFacts("baseline commit tree differs from the frozen tree")
        if _git_value(target, "write-tree").lower() != baseline_tree:
            raise StaleFacts("worktree index differs from the frozen baseline tree")
        _reject_nested_repository_paths(target, expected_changed_paths)

        fd, temporary = tempfile.mkstemp(prefix="hmasd-patch-index-")
        os.close(fd)
        temp_index = Path(temporary)
        temp_index.unlink()
        temp_env = {"GIT_INDEX_FILE": str(temp_index)}
        try:
            _run_git_bytes(target, "read-tree", baseline_tree, env=temp_env)
            numstat = _run_git_bytes(
                target,
                "apply",
                "--numstat",
                "-z",
                str(patch_path),
                env=temp_env,
            ).stdout
            if b"-\t-\t" in numstat:
                raise Unsupported("binary patches are unsupported")
            _run_git_bytes(
                target,
                "apply",
                "--cached",
                "--check",
                "--whitespace=nowarn",
                str(patch_path),
                env=temp_env,
            )
            _run_git_bytes(
                target,
                "apply",
                "--cached",
                "--whitespace=nowarn",
                str(patch_path),
                env=temp_env,
            )
            prospective_tree = (
                _run_git_bytes(target, "write-tree", env=temp_env)
                .stdout.decode("ascii", errors="strict")
                .strip()
                .lower()
            )
        finally:
            with contextlib.suppress(FileNotFoundError):
                temp_index.unlink()
        if prospective_tree != expected_result_tree:
            raise StaleFacts("prospective patch tree differs from the frozen result tree")
        delta = _canonical_tree_delta(repo, baseline_tree, prospective_tree)
        _validate_safe_content_delta(
            delta,
            expected_paths=expected_changed_paths,
            allowed_paths=allowed_paths,
        )
        if delta["sha256"] != expected_delta_sha256:
            raise StaleFacts("prospective patch delta digest differs from the frozen digest")

        prepared = {
            "schema": "hmasd.prepared-tree/v1",
            "worktree_ref": worktree_ref,
            "operation_token": entry["operation_token"],
            "base_sha": base,
            "baseline_tree_sha": baseline_tree,
            "result_tree_sha": prospective_tree,
            "patch_ref": {
                "path": patch_path.relative_to(repo).as_posix(),
                "sha256": patch_sha256,
            },
            "allowed_paths": allowed_paths,
            "changed_paths": expected_changed_paths,
            "diff_sha256": delta["sha256"],
            "delta": delta,
            "manager_checkout": {
                "head_sha": head,
                "index_tree_sha": baseline_tree,
            },
        }
        prepared_path, prepared_absolute_ref = _write_immutable_json(
            repo / ".omp" / "runtime" / "worktrees" / "prepared-trees" / worktree_ref,
            prepared,
        )
        prepared_ref = {
            "path": prepared_path.relative_to(repo).as_posix(),
            "sha256": prepared_absolute_ref["sha256"],
        }

        updated_entry = dict(entry)
        updated_entry["lifecycle"] = "PATCHED"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        updated = _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        updated, updated_entry, receipt = _documents_after_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            updated_entry,
            receipt_path,
            receipt,
        )
        receipt.update(
            {
                "registry_revision": int(updated["revision"]),
                "lifecycle": "PATCHED",
                "mutation_lease": mutation_lease,
                "patch": {
                    "prepared_tree_receipt_ref": prepared_ref,
                    "path": str(patch_path),
                    "sha256": patch_sha256,
                    "baseline_tree": baseline_tree,
                    "result_tree": prospective_tree,
                    "delta": delta,
                    "changed_paths": expected_changed_paths,
                    "allowed_paths": allowed_paths,
                },
                "patched_at": _now(),
                "last_failure": None,
                "unknown_outcome": None,
            }
        )
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "apply-patch",
            "result_tree_sha": prospective_tree,
            "prepared_tree_receipt_ref": prepared_ref,
            "diff_sha256": delta["sha256"],
            "changed_paths": expected_changed_paths,
            "worktree": updated_entry,
            "receipt": str(receipt_path),
            "registry_revision": updated["revision"],
        }


def _load_candidate_metadata(
    repo: Path,
    raw_path: str,
    expected_sha256_raw: str,
) -> tuple[Path, dict[str, str], str]:
    path = _canonical_path(raw_path, label="candidate metadata", must_exist=True)
    if not _under(path, repo):
        raise OwnershipRefusal("candidate metadata must be inside the canonical repository")
    digest = _validate_sha256(expected_sha256_raw, label="candidate metadata")
    if _hash_file(path, label="candidate metadata") != digest:
        raise StaleFacts("candidate metadata bytes differ from the frozen digest")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidInput(f"candidate metadata is unreadable: {exc}") from exc
    keys = {
        "schema",
        "author_name",
        "author_email",
        "author_date",
        "committer_name",
        "committer_email",
        "committer_date",
        "message",
    }
    metadata = _require_object(value, label="candidate metadata", keys=keys)
    if metadata["schema"] != CANDIDATE_METADATA_SCHEMA:
        raise InvalidInput("candidate metadata schema is invalid")
    for key in keys - {"schema"}:
        item = metadata[key]
        if not isinstance(item, str) or not item or "\x00" in item:
            raise InvalidInput(f"candidate metadata {key} is invalid")
    for key in {"author_name", "author_email", "committer_name", "committer_email"}:
        if "\n" in metadata[key] or "\r" in metadata[key]:
            raise InvalidInput(f"candidate metadata {key} must be one line")
    return path, {key: str(value) for key, value in metadata.items()}, digest


def create_candidate(
    repo_raw: str,
    worktree_ref: str,
    base_raw: str,
    prepared_receipt_raw: str,
    prepared_receipt_sha256_raw: str,
    allowed_paths_raw: Sequence[str],
    expected_changed_paths_raw: Sequence[str],
    expected_delta_sha256_raw: str,
    expected_tree_raw: str,
    metadata_raw: str,
    metadata_sha256_raw: str,
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Create an immutable candidate object/ref from one exact prepared tree."""

    expected = _require_exact_worktree_mutation(expected_raw)
    repo, common = _repo_context(repo_raw)
    base = _verify_commit(repo, base_raw, label="candidate base")
    expected_tree = _validate_commit(expected_tree_raw, label="candidate tree")
    expected_delta_sha256 = _validate_sha256(
        expected_delta_sha256_raw, label="candidate delta"
    )
    allowed_paths = _strict_path_list(list(allowed_paths_raw), label="allowed paths")
    expected_changed_paths = _strict_path_list(
        list(expected_changed_paths_raw), label="expected changed paths"
    )
    metadata_path, metadata, metadata_sha256 = _load_candidate_metadata(
        repo, metadata_raw, metadata_sha256_raw
    )
    _, prepared, prepared_ref = _load_prepared_tree_receipt(
        repo, prepared_receipt_raw, prepared_receipt_sha256_raw
    )

    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(repo, container, state, entry, receipt, expected)
        if entry["lifecycle"] != "PATCHED":
            raise StaleFacts("create-candidate requires an exactly PATCHED worktree")
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        target, registration, status = _ensure_controlled_checkout(
            repo, entry, candidate=base
        )
        head = _git_value(target, "rev-parse", "--verify", "HEAD").lower()
        baseline_tree = _git_value(target, "write-tree").lower()
        if head != base or registration.get("head") != base:
            raise StaleFacts("manager checkout HEAD differs from the declared base")
        if status["tracked_dirty"] or status["nonignored_untracked"]:
            raise UnsafeState("manager checkout changed after prepared-tree creation")
        if prepared.get("schema") != "hmasd.prepared-tree/v1":
            raise InvalidInput("candidate prepared-tree receipt schema is invalid")
        exact_prepared = {
            "worktree_ref": worktree_ref,
            "operation_token": entry["operation_token"],
            "base_sha": base,
            "baseline_tree_sha": baseline_tree,
            "result_tree_sha": expected_tree,
            "allowed_paths": allowed_paths,
            "changed_paths": expected_changed_paths,
            "diff_sha256": expected_delta_sha256,
        }
        for key, value in exact_prepared.items():
            if prepared.get(key) != value:
                raise StaleFacts(
                    f"prepared-tree receipt {key} differs from candidate packet"
                )
        patch_facts = receipt.get("patch")
        if (
            not isinstance(patch_facts, Mapping)
            or patch_facts.get("prepared_tree_receipt_ref") != prepared_ref
        ):
            raise StaleFacts(
                "current worktree receipt does not bind the exact prepared tree"
            )
        delta = _canonical_tree_delta(repo, base, expected_tree)
        _validate_safe_content_delta(
            delta,
            expected_paths=expected_changed_paths,
            allowed_paths=allowed_paths,
        )
        if delta["sha256"] != expected_delta_sha256 or prepared.get("delta") != delta:
            raise StaleFacts("prepared candidate delta differs from the frozen digest")

        env = {
            "GIT_AUTHOR_NAME": metadata["author_name"],
            "GIT_AUTHOR_EMAIL": metadata["author_email"],
            "GIT_AUTHOR_DATE": metadata["author_date"],
            "GIT_COMMITTER_NAME": metadata["committer_name"],
            "GIT_COMMITTER_EMAIL": metadata["committer_email"],
            "GIT_COMMITTER_DATE": metadata["committer_date"],
        }
        candidate = (
            _run_git_bytes(
                repo,
                "commit-tree",
                expected_tree,
                "-p",
                base,
                env=env,
                input_bytes=metadata["message"].encode("utf-8"),
            )
            .stdout.decode("ascii", errors="strict")
            .strip()
            .lower()
        )
        candidate = _verify_commit(repo, candidate, label="created candidate")
        if _candidate_parent(repo, candidate) != base:
            raise UnsafeState("created candidate has an unexpected parent")
        if _git_value(repo, "rev-parse", f"{candidate}^{{tree}}").lower() != expected_tree:
            raise UnsafeState("created candidate has an unexpected tree")
        candidate_ref = _candidate_ref(worktree_ref, candidate)
        observed_ref = _ref_sha(repo, candidate_ref)
        if observed_ref is None:
            created = _run_git(
                repo,
                "update-ref",
                candidate_ref,
                candidate,
                "0" * len(candidate),
                check=False,
            )
            observed_ref = _ref_sha(repo, candidate_ref)
            if created.returncode or observed_ref != candidate:
                raise UnknownApply(
                    "candidate object was created but its dedicated ref outcome is unknown",
                    details={
                        "candidate_sha": candidate,
                        "candidate_ref": candidate_ref,
                    },
                )
        elif observed_ref != candidate:
            raise UnsafeState("dedicated candidate ref already names another object")

        updated_entry = dict(entry)
        updated_entry["candidate_sha"] = candidate
        updated_entry["lifecycle"] = "CANDIDATE_READY"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        updated = _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        updated, updated_entry, receipt = _documents_after_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            updated_entry,
            receipt_path,
            receipt,
        )
        receipt.update(
            {
                "registry_revision": int(updated["revision"]),
                "candidate_sha": candidate,
                "lifecycle": "CANDIDATE_READY",
                "mutation_lease": mutation_lease,
                "candidate_creation": {
                    "phase": "OBJECT_REF_AND_REGISTRY_COMMITTED",
                    "base_sha": base,
                    "tree_sha": expected_tree,
                    "candidate_sha": candidate,
                    "candidate_ref": candidate_ref,
                    "prepared_tree_receipt_ref": prepared_ref,
                    "delta": delta,
                    "changed_paths": expected_changed_paths,
                    "allowed_paths": allowed_paths,
                    "metadata_ref": {
                        "path": metadata_path.relative_to(repo).as_posix(),
                        "sha256": metadata_sha256,
                    },
                },
                "candidate_created_at": _now(),
                "last_failure": None,
                "unknown_outcome": None,
            }
        )
        _atomic_write(receipt_path, receipt)
        if (
            _git_value(target, "rev-parse", "--verify", "HEAD").lower() != base
            or _git_value(target, "write-tree").lower() != baseline_tree
            or _status(target)["tracked_dirty"]
        ):
            raise UnknownApply(
                "manager checkout identity changed while candidate objects were prepared"
            )
        return {
            "ok": True,
            "operation": "create-candidate",
            "candidate_sha": candidate,
            "candidate_ref": candidate_ref,
            "prepared_tree_receipt_ref": prepared_ref,
            "tree_sha": expected_tree,
            "diff_sha256": delta["sha256"],
            "changed_paths": expected_changed_paths,
            "worktree": updated_entry,
            "receipt": str(receipt_path),
            "registry_revision": updated["revision"],
        }


def _record_candidate_facts(repo: Path, entry: Mapping[str, Any], candidate_raw: str) -> str:
    candidate = _verify_commit(repo, candidate_raw, label="candidate")
    base = str(entry["base_sha"]).lower()
    target, registration, status = _ensure_controlled_checkout(
        repo,
        entry,
        candidate=base,
    )
    head = _git_value(target, "rev-parse", "--verify", "HEAD").lower()
    if head != base or registration.get("head") != base:
        raise StaleFacts("candidate recording cannot change the manager checkout")
    if candidate == base:
        raise UnsafeState("base commit cannot be recorded as a candidate")
    if _candidate_parent(repo, candidate) != base:
        raise UnsafeState("candidate must be one clean commit directly descended from base")
    candidate_ref = _candidate_ref(str(entry["worktree_ref"]), candidate)
    if _ref_sha(repo, candidate_ref) != candidate:
        raise StaleFacts("dedicated immutable candidate ref does not match the candidate")
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("manager checkout is dirty while recording the candidate")
    return candidate


def record_candidate(
    repo_raw: str,
    worktree_ref: str,
    candidate_raw: str,
    mutation_lease_raw: Mapping[str, Any] | None = None,
    expected_raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    _validate_commit(candidate_raw, label="candidate")
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if entry["lifecycle"] != "CANDIDATE_READY":
            raise UnsafeState("record-candidate requires a created candidate object")
        state, entry, receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            receipt_path,
            receipt,
        )
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        candidate = _record_candidate_facts(repo, entry, candidate_raw)
        updated_entry = dict(entry)
        updated_entry["candidate_sha"] = candidate
        updated_entry["lifecycle"] = "CANDIDATE_READY"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        updated, updated_entry, receipt = _documents_after_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            updated_entry,
            receipt_path,
            receipt,
        )
        _record_candidate_facts(repo, updated_entry, candidate)
        receipt["candidate_sha"] = candidate
        receipt["lifecycle"] = "CANDIDATE_READY"
        receipt["registry_revision"] = updated["revision"]
        receipt["candidate_recorded_at"] = _now()
        receipt["last_failure"] = None
        receipt["unknown_outcome"] = None
        receipt["mutation_lease"] = mutation_lease
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "record-candidate",
            "candidate_sha": candidate,
            "worktree": updated_entry,
            "registry_revision": updated["revision"],
        }


def _prepare_integration_facts(
    repo: Path,
    entry: Mapping[str, Any],
    target: str,
    normalized_allowed: Sequence[str],
    verification_refs: Sequence[str],
) -> tuple[str, str, list[str], dict[str, Any], dict[str, Any]]:
    candidate = str(entry.get("candidate_sha") or "").lower()
    if not _FULL_SHA.fullmatch(candidate):
        raise UnsafeState("candidate SHA is absent")
    _, _, status = _ensure_controlled_checkout(
        repo, entry, candidate=str(entry["base_sha"]).lower()
    )
    if _ref_sha(repo, _candidate_ref(str(entry["worktree_ref"]), candidate)) != candidate:
        raise StaleFacts("dedicated candidate ref changed before integration preparation")
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("manager checkout is dirty")
    if _candidate_parent(repo, candidate) != str(entry["base_sha"]).lower():
        raise StaleFacts("candidate base changed")
    target_sha, _ = _target_observation(repo, target)
    if target_sha != str(entry["base_sha"]).lower():
        raise StaleFacts("integration target advanced from recorded base")
    changed = _changed_paths(repo, str(entry["base_sha"]), candidate)
    out_of_scope = [
        path
        for path in changed
        if not any(_relative_under(path, allowed) for allowed in normalized_allowed)
    ]
    if out_of_scope:
        raise OwnershipRefusal(
            f"candidate changed paths outside assignment allowlist: {', '.join(out_of_scope)}"
        )
    merge_result = _run_git(repo, "merge-tree", "--write-tree", target_sha, candidate, check=False)
    if merge_result.returncode:
        conflict = {
            "status": "CONFLICT",
            "detail": merge_result.stdout.strip() or merge_result.stderr.strip(),
        }
        raise UnsafeState("candidate has an integration conflict", details={"conflict": conflict})
    conflict = {"status": "CLEAN", "detail": None}
    evidence = _verification(verification_refs, repo)
    return candidate, target_sha, changed, conflict, evidence


def _orthogonal_authorization(
    repo: Path,
    entry: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authority = entry.get("parallel_set_authorization")
    if not isinstance(authority, dict):
        raise OwnershipRefusal("orthogonal worktree lacks frozen parallel-set authorization")
    required = {"manifest_path", "manifest_sha256", "parallel_set_id", "common_epoch_sha"}
    if set(authority) != required:
        raise InvalidInput("parallel-set authorization fields are invalid")
    manifest, observed = _load_parallel_set_manifest(
        repo,
        str(authority["manifest_path"]),
        expected_sha256=_validate_sha256(
            authority["manifest_sha256"], label="parallel-set authorization digest"
        ),
    )
    if observed != authority:
        raise StaleFacts("parallel-set authorization facts changed")
    if manifest["common_epoch_sha"] != str(entry["base_sha"]).lower():
        raise StaleFacts("parallel-set common epoch differs from candidate base")
    direction = _parallel_direction(
        manifest,
        direction_id=str(entry["direction_id"]),
        kind=str(entry["kind"]),
        assignment_id=str(entry["assignment_id"]),
    )
    if entry.get("required_handoff_sha") is not None or entry.get("required_dependency_refs", []) != []:
        raise OwnershipRefusal("orthogonal worktree carries a handoff or dependency edge")
    return manifest, direction, observed


def _verify_evidence_digests(root: Path, evidence: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    observed: list[dict[str, str]] = []
    for item in evidence:
        path = root / Path(item["path"])
        digest = _hash_file(path, label=f"verification evidence {item['path']}")
        if digest != item["sha256"]:
            raise StaleFacts(f"verification evidence digest changed: {item['path']}")
        observed.append({"path": item["path"], "sha256": digest})
    return observed


def _orthogonal_candidate_scope(
    repo: Path,
    entry: Mapping[str, Any],
    normalized_allowed: Sequence[str],
    verification_refs: Sequence[str],
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidate = str(entry.get("candidate_sha") or "").lower()
    if not _FULL_SHA.fullmatch(candidate):
        raise UnsafeState("candidate SHA is absent")
    _, _, status = _ensure_controlled_checkout(repo, entry, candidate=str(entry["base_sha"]).lower())
    if _ref_sha(repo, _candidate_ref(str(entry["worktree_ref"]), candidate)) != candidate:
        raise StaleFacts("dedicated candidate ref changed")
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("manager checkout is dirty")
    base = str(entry["base_sha"]).lower()
    if _candidate_parent(repo, candidate) != base:
        raise StaleFacts("candidate must remain one direct non-merge child of common epoch")
    manifest, direction, authority = _orthogonal_authorization(repo, entry)
    if list(normalized_allowed) != direction["allowed_roots"]:
        raise OwnershipRefusal("allowed paths differ from frozen parallel-set roots")
    expected_verification_refs = [item["path"] for item in direction["verification"]]
    normalized_verification_refs = [
        _validate_relative(path, label="verification reference")
        for path in verification_refs
    ]
    if len(normalized_verification_refs) != len(set(normalized_verification_refs)):
        raise InvalidInput("verification references contain duplicate paths")
    normalized_verification_refs.sort()
    if normalized_verification_refs != expected_verification_refs:
        raise OwnershipRefusal("verification references differ from frozen parallel-set evidence")
    candidate_delta = _canonical_tree_delta(repo, base, candidate)
    changed_paths = [record["path"] for record in candidate_delta["records"]]
    if changed_paths != direction["expected_changed_paths"]:
        raise OwnershipRefusal("candidate changed paths differ from frozen exact paths")
    evidence = {
        "status": "VERIFIED",
        "refs": _verify_evidence_digests(repo, direction["verification"]),
        "missing": [],
    }
    candidate_facts = {
        "base_sha": base,
        "candidate_sha": candidate,
        "candidate_parent": _candidate_parent(repo, candidate),
        "candidate_tree": _git_value(repo, "rev-parse", f"{candidate}^{{tree}}").lower(),
        "candidate_delta": candidate_delta,
        "allowed_roots": list(direction["allowed_roots"]),
        "expected_changed_paths": list(direction["expected_changed_paths"]),
        "dependency_paths": list(direction["dependency_paths"]),
        "evidence": evidence,
        "parallel_set_authorization": authority,
    }
    return candidate, candidate_delta, candidate_facts, manifest, direction


def _first_parent_lineage(
    repo: Path,
    state: Mapping[str, Any],
    *,
    base: str,
    target_sha: str,
    direction_id: str,
    authority: Mapping[str, Any],
) -> list[dict[str, Any]]:
    ancestor = _run_git(repo, "merge-base", "--is-ancestor", base, target_sha, check=False)
    if ancestor.returncode:
        raise StaleFacts("integration target is not a descendant of the common epoch")
    commits = [
        value.lower()
        for value in _git_value(repo, "rev-list", "--first-parent", "--reverse", f"{base}..{target_sha}").splitlines()
        if value
    ]
    lineage: list[dict[str, Any]] = []
    expected_parent = base
    for commit in commits:
        if _candidate_parent(repo, commit) != expected_parent:
            raise OwnershipRefusal("target first-parent lineage contains a merge or unexpected parent")
        rows = [
            dict(row)
            for row in state.get("worktrees", [])
            if isinstance(row, dict) and str(row.get("integrated_sha") or "").lower() == commit
        ]
        if len(rows) != 1:
            raise OwnershipRefusal("target lineage contains an unreceipted/shared/recovery commit")
        row = rows[0]
        if str(row.get("direction_id")) == direction_id:
            raise OwnershipRefusal("target lineage contains a same-direction integration")
        if _integration_policy(row) != "ORTHOGONAL_DIRECTION":
            raise OwnershipRefusal("target lineage contains a non-orthogonal integration")
        if row.get("parallel_set_authorization") != authority:
            raise OwnershipRefusal("target lineage belongs to another parallel-set authorization")
        receipt_path, receipt = _load_receipt(repo, row)
        integration = receipt.get("integration")
        if (
            not isinstance(integration, dict)
            or integration.get("phase") not in {"REMOTE_PUSH_COMMITTED", "RECONCILED_COMMITTED", "LOCAL_APPLY_COMMITTED"}
            or str(integration.get("integration_sha") or "").lower() != commit
            or integration.get("candidate_applied_delta_equal") is not True
        ):
            raise OwnershipRefusal("target lineage receipt is absent or not terminally proven")
        lineage.append(
            {
                "integrated_sha": commit,
                "direction_id": row["direction_id"],
                "receipt_path": str(receipt_path.relative_to(repo)),
                "receipt_sha256": _digest(receipt),
            }
        )
        expected_parent = commit
    if expected_parent != target_sha:
        raise StaleFacts("target first-parent lineage observation is incomplete")
    return lineage


def _prospective_tree_checks(
    repo: Path,
    tree: str,
    checks: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="hmasd-prospective-") as temporary:
        temporary_root = Path(temporary)
        index_path = temporary_root / "index"
        checkout = temporary_root / "tree"
        checkout.mkdir()
        env = {"GIT_INDEX_FILE": str(index_path)}
        _run_git_bytes(repo, "read-tree", tree, env=env)
        _run_git_bytes(
            repo,
            "checkout-index",
            "--all",
            "--force",
            f"--prefix={checkout}{os.sep}",
            env=env,
        )
        _verify_evidence_digests(checkout, evidence)
        for check in checks:
            cwd = checkout / Path(check["cwd"]) if check["cwd"] else checkout
            if not cwd.is_dir() or not _under(cwd, checkout):
                raise OwnershipRefusal(f"prospective check cwd is absent: {check['check_id']}")
            result = subprocess.run(
                list(check["argv"]),
                cwd=str(cwd),
                check=False,
                capture_output=True,
                env={**os.environ, "HMASD_PROSPECTIVE_TREE": tree},
            )
            result_fact = {
                "check_id": check["check_id"],
                "argv_sha256": hashlib.sha256(_canonical_json(check["argv"])).hexdigest(),
                "returncode": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            }
            results.append(result_fact)
            if result.returncode:
                raise UnsafeState(
                    f"prospective integration check failed: {check['check_id']}",
                    details={"prospective_check": result_fact},
                )
    return results


def _orthogonal_target_proof(
    repo: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any],
    candidate: str,
    candidate_delta: Mapping[str, Any],
    manifest: Mapping[str, Any],
    direction: Mapping[str, Any],
) -> dict[str, Any]:
    base = str(entry["base_sha"]).lower()
    target_sha, _ = _target_observation(repo, TARGET_BRANCH)
    merge_base = _git_value(repo, "merge-base", target_sha, candidate).lower()
    if merge_base != base:
        raise StaleFacts("candidate and target do not share exactly the frozen common epoch")
    authority = dict(entry["parallel_set_authorization"])
    lineage = _first_parent_lineage(
        repo,
        state,
        base=base,
        target_sha=target_sha,
        direction_id=str(entry["direction_id"]),
        authority=authority,
    )
    target_delta = _canonical_tree_delta(repo, base, target_sha)
    candidate_paths = [record["path"] for record in candidate_delta["records"]]
    target_paths = [record["path"] for record in target_delta["records"]]
    collisions = sorted(
        {
            f"{candidate_path}:{target_path}"
            for candidate_path in candidate_paths
            for target_path in target_paths
            if _path_collision(candidate_path, target_path)
        }
    )
    if collisions:
        raise OwnershipRefusal(
            "target changes overlap candidate exact paths or roots",
            details={"path_collisions": collisions},
        )
    dependency_collisions = sorted(
        {
            f"{dependency}:{target_path}"
            for dependency in direction["dependency_paths"]
            for target_path in target_paths
            if _path_collision(dependency, target_path)
        }
    )
    if dependency_collisions:
        raise StaleFacts(
            "target changed the candidate authority/input/interface dependency footprint",
            details={"dependency_collisions": dependency_collisions},
        )
    merge = _run_git(repo, "merge-tree", "--write-tree", target_sha, candidate, check=False)
    if merge.returncode:
        conflict = {
            "status": "CONFLICT",
            "detail": merge.stdout.strip() or merge.stderr.strip(),
        }
        raise UnsafeState("candidate has an integration conflict", details={"conflict": conflict})
    merge_tree = merge.stdout.splitlines()[0].strip().lower()
    if not _FULL_SHA.fullmatch(merge_tree):
        raise UnsafeState("prospective merge did not produce one exact tree")
    checks = _prospective_tree_checks(
        repo,
        merge_tree,
        direction["prospective_checks"],
        direction["verification"],
    )
    return {
        "target_sha": target_sha,
        "target_tree": _git_value(repo, "rev-parse", f"{target_sha}^{{tree}}").lower(),
        "merge_base": merge_base,
        "target_delta": target_delta,
        "lineage": lineage,
        "collision_status": "DISJOINT",
        "dependency_status": "UNCHANGED",
        "merge_status": "CLEAN",
        "merge_tree": merge_tree,
        "prospective_checks": checks,
        "parallel_set_id": manifest["parallel_set_id"],
    }


def _prepare_orthogonal_integration(
    repo_raw: str,
    worktree_ref: str,
    target: str,
    allowed_paths: Sequence[str],
    verification_refs: Sequence[str],
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    if target != TARGET_BRANCH:
        raise OwnershipRefusal("integration target must be exactly omp/workflow")
    if not allowed_paths:
        raise InvalidInput("at least one --allowed-path is required")
    normalized_allowed = sorted(
        {_validate_relative(path, label="allowed path") for path in allowed_paths}
    )
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        if _integration_policy(entry) != "ORTHOGONAL_DIRECTION":
            raise OwnershipRefusal("worktree is not provisioned for orthogonal integration")
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if entry["lifecycle"] not in {"CANDIDATE_READY", "PREPARED_FOR_INTEGRATION"}:
            raise UnsafeState("worktree lifecycle is not candidate-ready")
        state, entry, receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            receipt_path,
            receipt,
        )
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        candidate, candidate_delta, candidate_facts, manifest, direction = (
            _orthogonal_candidate_scope(
                repo, entry, normalized_allowed, verification_refs
            )
        )
        target_proof = _orthogonal_target_proof(
            repo, state, entry, candidate, candidate_delta, manifest, direction
        )
        updated_entry = dict(entry)
        updated_entry["lifecycle"] = "PREPARED_FOR_INTEGRATION"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        updated, updated_entry, receipt = _documents_after_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            updated_entry,
            receipt_path,
            receipt,
        )
        current_candidate, current_delta, current_facts, current_manifest, current_direction = (
            _orthogonal_candidate_scope(
                repo, updated_entry, normalized_allowed, verification_refs
            )
        )
        current_target = _orthogonal_target_proof(
            repo,
            updated,
            updated_entry,
            current_candidate,
            current_delta,
            current_manifest,
            current_direction,
        )
        if (
            current_candidate != candidate
            or current_delta != candidate_delta
            or current_facts != candidate_facts
            or current_manifest != manifest
            or current_direction != direction
            or current_target != target_proof
        ):
            raise UnknownApply("orthogonal prepare facts changed after registry transition")
        integration = {
            "version": INTEGRATION_RECEIPT_VERSION,
            "policy": "ORTHOGONAL_DIRECTION",
            "phase": "PREPARED",
            "operation_token": entry["operation_token"],
            "effect_fingerprint": None,
            "candidate": candidate_facts,
            "prepared_target": target_proof,
            "final_target": None,
            "integration_sha": None,
            "integration_tree": None,
            "candidate_applied_delta_equal": None,
            "push_attempts": 0,
            "local_apply_attempts": 0,
            "reconciliation_observations": 0,
            "remote": dict(manifest["remote"]),
            "remote_prefetch_sha": None,
            "remote_post_observation_sha": None,
            "unknown_reason": None,
        }
        facts = _facts(
            repo,
            common,
            container,
            updated_entry,
            updated,
            target_sha=target_proof["target_sha"],
            changed_paths=direction["expected_changed_paths"],
            allowed_paths=direction["allowed_roots"],
            verification=candidate_facts["evidence"],
            conflict={"status": "CLEAN", "detail": None},
        )
        receipt.update(
            {
                "registry_revision": updated["revision"],
                "lifecycle": "PREPARED_FOR_INTEGRATION",
                "candidate_sha": candidate,
                "integration_policy": "ORTHOGONAL_DIRECTION",
                "parallel_set_authorization": entry["parallel_set_authorization"],
                "changed_paths": direction["expected_changed_paths"],
                "allowed_paths": direction["allowed_roots"],
                "mutation_lease": mutation_lease,
                "verification_evidence": candidate_facts["evidence"],
                "conflict": {"status": "CLEAN", "detail": None},
                "facts": facts,
                "facts_sha256": _digest(facts),
                "integration": integration,
                "prepared_at": _now(),
                "last_failure": None,
                "unknown_outcome": None,
            }
        )
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "prepare-integration",
            "integration_policy": "ORTHOGONAL_DIRECTION",
            "integration_phase": "PREPARED",
            "receipt": str(receipt_path),
            "worktree": updated_entry,
            "changed_paths": direction["expected_changed_paths"],
            "verification_evidence": candidate_facts["evidence"],
            "conflict": {"status": "CLEAN", "detail": None},
            "registry_revision": updated["revision"],
        }


def _prepare_exact_integration(
    repo_raw: str,
    worktree_ref: str,
    target: str,
    allowed_paths: Sequence[str],
    verification_refs: Sequence[str],
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    if not allowed_paths:
        raise InvalidInput("at least one --allowed-path is required")
    normalized_allowed = sorted(
        {_validate_relative(path, label="allowed path") for path in allowed_paths}
    )
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if entry["lifecycle"] not in {"CANDIDATE_READY", "PREPARED_FOR_INTEGRATION"}:
            raise UnsafeState("worktree lifecycle is not candidate-ready")
        state, entry, receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            receipt_path,
            receipt,
        )
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        candidate, target_sha, changed, conflict, evidence = _prepare_integration_facts(
            repo,
            entry,
            target,
            normalized_allowed,
            verification_refs,
        )
        updated_entry = dict(entry)
        updated_entry["lifecycle"] = "PREPARED_FOR_INTEGRATION"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        updated, updated_entry, receipt = _documents_after_registry_transition(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            updated_entry,
            receipt_path,
            receipt,
        )
        current = _prepare_integration_facts(
            repo,
            updated_entry,
            target,
            normalized_allowed,
            verification_refs,
        )
        if current != (candidate, target_sha, changed, conflict, evidence):
            raise UnknownApply("integration facts changed after the registry prepared transition")
        facts = _facts(
            repo,
            common,
            container,
            updated_entry,
            updated,
            target_sha=target_sha,
            changed_paths=changed,
            allowed_paths=normalized_allowed,
            verification=evidence,
            conflict=conflict,
        )
        receipt.update(
            {
                "registry_revision": updated["revision"],
                "lifecycle": "PREPARED_FOR_INTEGRATION",
                "candidate_sha": candidate,
                "changed_paths": changed,
                "allowed_paths": normalized_allowed,
                "verification_evidence": evidence,
                "conflict": conflict,
                "mutation_lease": mutation_lease,
                "facts": facts,
                "facts_sha256": _digest(facts),
                "prepared_at": _now(),
                "last_failure": None,
                "unknown_outcome": None,
            }
        )
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "prepare-integration",
            "receipt": str(receipt_path),
            "worktree": updated_entry,
            "changed_paths": changed,
            "verification_evidence": evidence,
            "conflict": conflict,
            "registry_revision": updated["revision"],
        }


def prepare_integration(
    repo_raw: str,
    worktree_ref: str,
    target: str,
    allowed_paths: Sequence[str],
    verification_refs: Sequence[str],
    mutation_lease_raw: Mapping[str, Any] | None = None,
    expected_raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    loaded = _load_registry(repo)
    assert loaded is not None
    policy = _integration_policy(_entry(loaded[1], worktree_ref))
    with _target_lock(common, target):
        if policy == "ORTHOGONAL_DIRECTION":
            return _prepare_orthogonal_integration(
                repo_raw,
                worktree_ref,
                target,
                allowed_paths,
                verification_refs,
                mutation_lease_raw,
                expected_raw,
            )
        return _prepare_exact_integration(
            repo_raw,
            worktree_ref,
            target,
            allowed_paths,
            verification_refs,
            mutation_lease_raw,
            expected_raw,
        )


def _apply_facts(repo: Path, common: Path, container: Path, entry: Mapping[str, Any], state: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    target_sha, _ = _target_observation(repo, TARGET_BRANCH)
    return _facts(repo, common, container, entry, state, target_sha=target_sha, changed_paths=list(receipt.get("changed_paths", [])), allowed_paths=list(receipt.get("allowed_paths", [])), verification=dict(receipt.get("verification_evidence", {})), conflict=dict(receipt.get("conflict", {})))


def _validated_apply_candidate(
    repo: Path,
    common: Path,
    container: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    expected_facts = receipt.get("facts")
    if not isinstance(expected_facts, dict) or receipt.get("facts_sha256") != _digest(expected_facts):
        raise InvalidInput("receipt facts are missing or tampered")
    current_facts = _apply_facts(repo, common, container, entry, state, receipt)
    if current_facts != expected_facts:
        raise StaleFacts("one or more prepare/apply facts changed")
    if receipt.get("conflict", {}).get("status") != "CLEAN":
        raise UnsafeState("receipt does not contain a clean conflict result")
    candidate = str(entry.get("candidate_sha") or "").lower()
    if not _FULL_SHA.fullmatch(candidate):
        raise UnsafeState("prepared registry candidate is absent")
    if str(expected_facts.get("target_sha", "")).lower() != str(entry["base_sha"]).lower():
        raise StaleFacts("receipt target is not the recorded base")
    return candidate, expected_facts


def _validate_apply_actor(actor: str, entry: Mapping[str, Any]) -> None:
    if actor == "root":
        return
    role = {"research": "em", "engineering": "cm"}.get(str(entry.get("kind")))
    expected = f"{role}:{entry.get('direction_id')}" if role is not None else None
    if actor != expected:
        raise OwnershipRefusal(
            "integration actor must be Root or the direction/kind-owning EM/CM"
        )


def _read_receipt_input(receipt_raw: str) -> tuple[Path, dict[str, Any], str, Path, Path]:
    receipt_input = Path(receipt_raw)
    if not receipt_input.is_absolute():
        receipt_input = Path.cwd() / receipt_input
    receipt_input = _canonical_path(receipt_input, label="receipt", must_exist=True)
    try:
        preliminary = json.loads(receipt_input.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidInput(f"receipt is unreadable: {exc}") from exc
    if not isinstance(preliminary, dict) or preliminary.get("schema") != RECEIPT_SCHEMA:
        raise InvalidInput("receipt schema is invalid")
    worktree_ref = str(preliminary.get("worktree_ref", ""))
    repo, common = _repo_context(str(preliminary.get("repo", "")))
    return receipt_input, preliminary, worktree_ref, repo, common


def _persist_integration(
    receipt_path: Path,
    receipt: dict[str, Any],
    integration: Mapping[str, Any],
) -> None:
    receipt["integration"] = dict(integration)
    _atomic_write(receipt_path, receipt)


def _create_orthogonal_integration_object(
    repo: Path,
    entry: Mapping[str, Any],
    actor: str,
    candidate: str,
    candidate_delta: Mapping[str, Any],
    target_proof: Mapping[str, Any],
) -> tuple[str, str]:
    target_sha = str(target_proof["target_sha"])
    tree = str(target_proof["merge_tree"])
    authority = dict(entry["parallel_set_authorization"])
    message = (
        f"Integrate orthogonal direction {entry['direction_id']}\n\n"
        f"HMASD-Policy: ORTHOGONAL_DIRECTION\n"
        f"HMASD-Parallel-Set: {authority['parallel_set_id']}\n"
        f"HMASD-Common-Epoch: {entry['base_sha']}\n"
        f"HMASD-Candidate: {candidate}\n"
        f"HMASD-Candidate-Delta-SHA256: {candidate_delta['sha256']}\n"
    ).encode("utf-8")
    candidate_time = _git_value(repo, "show", "-s", "--format=%ct", candidate)
    identity = actor.replace(":", "-")
    env = {
        "GIT_AUTHOR_NAME": f"HMASD {identity}",
        "GIT_AUTHOR_EMAIL": "hmasd@example.invalid",
        "GIT_AUTHOR_DATE": f"{candidate_time} +0000",
        "GIT_COMMITTER_NAME": f"HMASD {identity}",
        "GIT_COMMITTER_EMAIL": "hmasd@example.invalid",
        "GIT_COMMITTER_DATE": f"{candidate_time} +0000",
    }
    result = _run_git_bytes(
        repo,
        "commit-tree",
        tree,
        "-p",
        target_sha,
        env=env,
        input_bytes=message,
    )
    integration_sha = result.stdout.decode("ascii", errors="strict").strip().lower()
    if not _FULL_SHA.fullmatch(integration_sha):
        raise UnknownApply("integration object creation returned no exact commit")
    if _candidate_parent(repo, integration_sha) != target_sha:
        raise UnknownApply("integration object has an unexpected parent")
    if _git_value(repo, "rev-parse", f"{integration_sha}^{{tree}}").lower() != tree:
        raise UnknownApply("integration object has an unexpected tree")
    return integration_sha, hashlib.sha256(message).hexdigest()


def _fetch_remote_target(
    repo: Path,
    remote: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    result = _run_git(
        repo,
        "fetch",
        "--no-tags",
        "--force",
        str(remote["name"]),
        str(remote["ref"]),
        check=False,
    )
    if result.returncode:
        return None, result.stderr.strip() or result.stdout.strip() or "remote fetch failed"
    value = _git_value(repo, "rev-parse", "--verify", "FETCH_HEAD").lower()
    if not _FULL_SHA.fullmatch(value):
        return None, "remote fetch returned no exact commit"
    return value, None

def _integration_observation(
    integration: Mapping[str, Any],
    *,
    local_sha: str | None = None,
) -> dict[str, Any]:
    predecessor = integration.get("predecessor_sha")
    if predecessor is None and isinstance(integration.get("final_target"), Mapping):
        predecessor = integration["final_target"].get("target_sha")
    return {
        "integration_policy": integration.get("policy"),
        "integration_phase": integration.get("phase"),
        "candidate_sha": integration.get("candidate_sha")
        or (
            integration.get("candidate", {}).get("candidate_sha")
            if isinstance(integration.get("candidate"), Mapping)
            else None
        ),
        "integrated_sha": integration.get("integration_sha"),
        "expected_target_predecessor_sha": predecessor,
        "expected_remote_predecessor_sha": predecessor,
        "remote_prefetch_sha": integration.get("remote_prefetch_sha"),
        "remote_post_observation_sha": integration.get(
            "remote_post_observation_sha"
        ),
        "local_sha": local_sha,
        "reconciliation_observations": integration.get(
            "reconciliation_observations"
        ),
        "push_attempts": integration.get("push_attempts"),
        "local_apply_attempts": integration.get("local_apply_attempts"),
    }



def _mark_orthogonal_unknown(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any],
    worktree_ref: str,
    receipt_path: Path,
    receipt: dict[str, Any],
    integration: Mapping[str, Any],
    reason: str,
) -> None:
    observation = _effect_observation(repo, entry)
    unknown = {
        "operation": "APPLY",
        "status": "UNKNOWN",
        "recorded_at": _now(),
        "error": reason,
        "registry_revision_before": int(state["revision"]),
        "registry_revision_observed": int(state["revision"]) + 1,
        "observation": observation,
    }
    updated_entry = dict(entry)
    updated_entry["lifecycle"] = "APPLY_OUTCOME_UNKNOWN"
    updated_entry["unknown_outcome"] = unknown
    updated = _replace_registry_observed(
        repo,
        common,
        container,
        identities,
        state_path,
        state,
        updated_entry,
        worktree_ref,
    )
    unknown["registry_revision_observed"] = int(updated["revision"])
    updated_entry["unknown_outcome"] = unknown
    receipt["registry_revision"] = int(updated["revision"])
    receipt["lifecycle"] = "APPLY_OUTCOME_UNKNOWN"
    receipt["unknown_outcome"] = unknown
    receipt["integration"] = dict(integration)
    _atomic_write(receipt_path, receipt)

def _validate_integrate_push_contract(
    repo: Path,
    state: Mapping[str, Any],
    entry: Mapping[str, Any],
    receipt: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "policy",
        "candidate_sha",
        "base_sha",
        "target_local_ref",
        "target_remote_ref",
        "remote_name",
        "expected_target_predecessor_sha",
        "expected_remote_predecessor_sha",
        "prepared_operation_id",
        "prepared_receipt_sha256",
        "allowed_paths",
        "changed_paths",
        "dependency_paths",
        "diff_sha256",
        "verification_refs",
        "push_authorization_ref",
    }
    normalized = _require_object(contract, label="integrate-push contract", keys=required)
    policy = _validate_integration_policy(str(normalized["policy"]))
    if policy != _integration_policy(entry) or receipt.get("integration_policy") != policy:
        raise StaleFacts("integrate-push policy differs from registry or prepared receipt")
    candidate = _validate_commit(str(normalized["candidate_sha"]), label="frozen candidate")
    base = _validate_commit(str(normalized["base_sha"]), label="frozen base")
    if candidate != str(entry.get("candidate_sha") or "").lower() or candidate != str(
        receipt.get("candidate_sha") or ""
    ).lower():
        raise StaleFacts("integrate-push candidate differs from prepared authority")
    if base != str(entry["base_sha"]).lower() or base != str(receipt["base_sha"]).lower():
        raise StaleFacts("integrate-push base differs from prepared authority")
    if normalized["target_local_ref"] != TARGET_BRANCH:
        raise OwnershipRefusal("integrate-push local target must be exactly omp/workflow")
    remote_name = normalized["remote_name"]
    if not isinstance(remote_name, str) or re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", remote_name
    ) is None:
        raise InvalidInput("integrate-push remote name is invalid")
    remote_ref = normalized["target_remote_ref"]
    if (
        not isinstance(remote_ref, str)
        or not remote_ref.startswith("refs/heads/")
        or _run_git(repo, "check-ref-format", remote_ref, check=False).returncode
    ):
        raise InvalidInput("integrate-push remote ref is invalid")
    target_predecessor = _validate_commit(
        str(normalized["expected_target_predecessor_sha"]),
        label="target predecessor",
    )
    remote_predecessor = _validate_commit(
        str(normalized["expected_remote_predecessor_sha"]),
        label="remote predecessor",
    )
    facts = receipt.get("facts")
    if not isinstance(facts, Mapping) or receipt.get("facts_sha256") != _digest(facts):
        raise InvalidInput("prepared receipt facts are missing or tampered")
    if target_predecessor != str(facts.get("target_sha") or "").lower():
        raise StaleFacts("target predecessor differs from prepared receipt")
    if remote_predecessor != target_predecessor:
        raise StaleFacts("remote and local predecessor bindings differ")
    allowed_paths = _strict_path_list(
        list(normalized["allowed_paths"]), label="integrate-push allowed paths"
    )
    changed_paths = _strict_path_list(
        list(normalized["changed_paths"]), label="integrate-push changed paths"
    )
    dependency_paths = _strict_path_list(
        list(normalized["dependency_paths"]),
        label="integrate-push dependency paths",
        allow_empty=True,
    )
    if allowed_paths != list(receipt.get("allowed_paths", [])):
        raise StaleFacts("integrate-push allowlist differs from prepared receipt")
    if changed_paths != list(receipt.get("changed_paths", [])):
        raise StaleFacts("integrate-push changed paths differ from prepared receipt")
    delta = _canonical_tree_delta(repo, base, candidate)
    diff_sha256 = _validate_sha256(
        normalized["diff_sha256"], label="integrate-push diff"
    )
    if delta["sha256"] != diff_sha256:
        raise StaleFacts("integrate-push canonical delta differs from frozen digest")
    refs = normalized["verification_refs"]
    if not isinstance(refs, list) or not refs:
        raise InvalidInput("integrate-push verification refs are required")
    verified_refs: list[dict[str, str]] = []
    for index, ref in enumerate(refs):
        exact = _require_object(
            ref,
            label=f"integrate-push verification_refs[{index}]",
            keys={"path", "sha256"},
        )
        relative = _validate_relative(
            exact["path"], label=f"integrate-push verification_refs[{index}].path"
        )
        digest = _validate_sha256(
            exact["sha256"],
            label=f"integrate-push verification_refs[{index}].sha256",
        )
        path = _canonical_path(
            repo / relative,
            label=f"integrate-push verification_refs[{index}]",
            must_exist=True,
        )
        if not _under(path, repo) or _hash_file(path, label="verification ref") != digest:
            raise StaleFacts("integrate-push verification evidence changed")
        verified_refs.append({"path": relative, "sha256": digest})
    verified_paths = [item["path"] for item in verified_refs]
    if len(verified_paths) != len(set(verified_paths)):
        raise InvalidInput("integrate-push verification refs contain duplicate paths")
    verified_refs.sort(key=lambda item: item["path"])
    prepared_evidence = receipt.get("verification_evidence")
    if not isinstance(prepared_evidence, Mapping):
        raise InvalidInput("prepared verification evidence is absent")
    prepared_refs = prepared_evidence.get("refs")
    if not isinstance(prepared_refs, list):
        raise InvalidInput("prepared verification refs are absent")
    if all(isinstance(item, Mapping) for item in prepared_refs):
        prepared_exact = sorted(
            (
                {"path": str(item.get("path")), "sha256": str(item.get("sha256"))}
                for item in prepared_refs
            ),
            key=lambda item: item["path"],
        )
        if prepared_exact != sorted(verified_refs, key=lambda item: item["path"]):
            raise StaleFacts(
                "integrate-push evidence digests differ from prepared receipt"
            )
    else:
        prepared_paths = sorted(str(item) for item in prepared_refs)
        if prepared_paths != sorted(item["path"] for item in verified_refs):
            raise StaleFacts(
                "integrate-push verification refs differ from prepared receipt"
            )
    if policy in EXACT_POLICIES:
        if dependency_paths:
            raise OwnershipRefusal("exact integration cannot carry orthogonal dependency paths")
        if target_predecessor != base:
            raise StaleFacts("exact integration predecessor must equal the declared base")
        if entry.get("required_handoff_sha") not in {None, base}:
            raise StaleFacts("exact integration handoff binding differs from base")
    else:
        _, direction, _ = _orthogonal_authorization(repo, entry)
        if dependency_paths != list(direction["dependency_paths"]):
            raise StaleFacts("orthogonal dependency footprint differs from authorization")
        integration = receipt.get("integration")
        if not isinstance(integration, Mapping) or integration.get("policy") != policy:
            raise InvalidInput("orthogonal prepared integration facts are absent")
        remote = integration.get("remote")
        if not isinstance(remote, Mapping):
            raise InvalidInput("orthogonal remote binding is absent")
        if (
            normalized["remote_name"] != remote.get("name")
            or normalized["target_remote_ref"] != remote.get("ref")
        ):
            raise StaleFacts("orthogonal remote binding differs from the manifest")
    _validate_assignment(
        str(normalized["prepared_operation_id"])
    )
    normalized["prepared_receipt_sha256"] = _validate_sha256(
        normalized["prepared_receipt_sha256"],
        label="prepared Clerk receipt",
    )
    push_ref = _require_object(
        normalized["push_authorization_ref"],
        label="push authorization ref",
        keys={"path", "sha256"},
    )
    push_path = _validate_relative(
        push_ref["path"], label="push authorization path"
    )
    push_digest = _validate_sha256(
        push_ref["sha256"], label="push authorization digest"
    )
    canonical_push = _canonical_path(
        repo / push_path, label="push authorization", must_exist=True
    )
    if not _under(canonical_push, repo) or _hash_file(
        canonical_push, label="push authorization"
    ) != push_digest:
        raise StaleFacts("push authorization bytes changed")
    return {
        **normalized,
        "policy": policy,
        "candidate_sha": candidate,
        "base_sha": base,
        "expected_target_predecessor_sha": target_predecessor,
        "expected_remote_predecessor_sha": remote_predecessor,
        "allowed_paths": allowed_paths,
        "changed_paths": changed_paths,
        "dependency_paths": dependency_paths,
        "diff_sha256": diff_sha256,
        "verification_refs": verified_refs,
        "push_authorization_ref": {"path": push_path, "sha256": push_digest},
        "prepared_registry_revision": int(state["revision"]),
    }


def _require_frozen_target_predecessor(
    observed_sha: Any,
    expected_sha: Any,
    *,
    phase: str,
) -> str:
    observed = _validate_commit(str(observed_sha), label="observed target predecessor")
    expected = _validate_commit(str(expected_sha), label="expected target predecessor")
    if observed != expected:
        raise StaleFacts(
            "orthogonal target differs from the frozen expected predecessor",
            details={
                "integration_phase": phase,
                "expected_target_predecessor_sha": expected,
                "local_sha": observed,
            },
        )
    return observed


def _apply_orthogonal(
    receipt_raw: str,
    actor: str,
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
    integrate_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipt_input, preliminary, worktree_ref, repo, common = _read_receipt_input(receipt_raw)
    preliminary_sha256 = _digest(preliminary)
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        _validate_apply_actor(actor, entry)
        if _integration_policy(entry) != "ORTHOGONAL_DIRECTION":
            raise OwnershipRefusal("worktree is not provisioned for orthogonal integration")
        actual_receipt_path, receipt = _load_receipt(repo, entry)
        if not _same_path(actual_receipt_path, receipt_input):
            raise OwnershipRefusal("receipt path is not the registry-authorized receipt")
        if _digest(receipt) != preliminary_sha256:
            raise StaleFacts("integration receipt changed before the worktree lock was acquired")
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if integrate_contract is None:
            raise InvalidInput("orthogonal integration requires the frozen push contract")
        frozen_contract = _validate_integrate_push_contract(
            repo, state, entry, receipt, integrate_contract
        )
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        entry = dict(entry)
        entry["mutation_lease"] = mutation_lease
        receipt["mutation_lease"] = mutation_lease
        _atomic_write(actual_receipt_path, receipt)
        integration_value = receipt.get("integration")
        if not isinstance(integration_value, dict) or integration_value.get("policy") != "ORTHOGONAL_DIRECTION":
            raise InvalidInput("orthogonal integration receipt is missing or invalid")
        integration = dict(integration_value)
        phase = integration.get("phase")
        if entry["lifecycle"] == "INTEGRATED":
            raise StaleFacts("orthogonal integration attempt is already terminal")
        if entry["lifecycle"] == "APPLY_OUTCOME_UNKNOWN":
            raise UnknownApply(
                "orthogonal integration has a terminal unknown outcome",
                details=_integration_observation(integration),
            )
        if entry["lifecycle"] != "PREPARED_FOR_INTEGRATION":
            raise StaleFacts("receipt is not prepared for orthogonal integration")
        terminal_noncommitted = {
            "REMOTE_PUSH_REJECTED",
            "RECONCILED_NOT_COMMITTED",
            "RECONCILED_CONFLICTED",
        }
        if phase in terminal_noncommitted:
            raise StaleFacts(
                "orthogonal integration attempt is terminal and cannot be retried",
                details={"integration_phase": phase},
            )
        if phase == "REMOTE_PUSH_UNKNOWN" and int(integration.get("reconciliation_observations", 0)) >= 1:
            raise UnknownApply(
                "orthogonal remote outcome remains unknown after its one observation",
                details=_integration_observation(integration),
            )

        allowed_paths = list(receipt.get("allowed_paths", []))
        evidence_refs = [
            item["path"]
            for item in receipt.get("verification_evidence", {}).get("refs", [])
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        ]
        candidate, candidate_delta, candidate_facts, manifest, direction = (
            _orthogonal_candidate_scope(repo, entry, allowed_paths, evidence_refs)
        )
        integration_sha = str(integration.get("integration_sha") or "").lower()
        final_target = integration.get("final_target")
        if integration.get("candidate") != candidate_facts:
            raise StaleFacts("frozen candidate scope or canonical delta digest changed")
        expected_facts = receipt.get("facts")
        if (
            not isinstance(expected_facts, dict)
            or receipt.get("facts_sha256") != _digest(expected_facts)
        ):
            raise InvalidInput("receipt facts are missing or tampered")
        if phase == "PREPARED":
            final_target = _orthogonal_target_proof(
                repo, state, entry, candidate, candidate_delta, manifest, direction
            )
            _require_frozen_target_predecessor(
                final_target["target_sha"],
                frozen_contract["expected_target_predecessor_sha"],
                phase="PREPARED",
            )
            integration_sha, message_sha256 = _create_orthogonal_integration_object(
                repo, entry, actor, candidate, candidate_delta, final_target
            )
            applied_delta = _canonical_tree_delta(
                repo, str(final_target["target_sha"]), integration_sha
            )
            if applied_delta != candidate_delta:
                raise UnsafeState(
                    "candidate and prospective applied canonical deltas differ"
                )
            integration.update(
                {
                    "phase": "INTEGRATION_OBJECT_CREATED",
                    "final_target": final_target,
                    "integration_sha": integration_sha,
                    "integration_tree": final_target["merge_tree"],
                    "integration_message_sha256": message_sha256,
                    "applied_delta": applied_delta,
                    "candidate_applied_delta_equal": True,
                }
            )
            integration["effect_fingerprint"] = _digest(
                {
                    "operation_token": entry["operation_token"],
                    "candidate_sha": candidate,
                    "candidate_delta_sha256": candidate_delta["sha256"],
                    "target_sha": final_target["target_sha"],
                    "integration_sha": integration_sha,
                    "remote": manifest["remote"],
                }
            )
            _persist_integration(actual_receipt_path, receipt, integration)
            phase = "INTEGRATION_OBJECT_CREATED"
        else:
            if (
                not _FULL_SHA.fullmatch(integration_sha)
                or not isinstance(final_target, dict)
            ):
                raise InvalidInput("frozen integration object facts are absent")
            _require_frozen_target_predecessor(
                final_target["target_sha"],
                frozen_contract["expected_target_predecessor_sha"],
                phase=str(phase),
            )
            if _candidate_parent(repo, integration_sha) != str(
                final_target.get("target_sha")
            ):
                raise StaleFacts("frozen integration object parent changed")
            if _git_value(
                repo, "rev-parse", f"{integration_sha}^{{tree}}"
            ).lower() != integration.get("integration_tree"):
                raise StaleFacts("frozen integration object tree changed")
            if (
                _canonical_tree_delta(
                    repo, str(final_target["target_sha"]), integration_sha
                )
                != candidate_delta
            ):
                raise StaleFacts("frozen integration object delta changed")

        target_predecessor = str(final_target["target_sha"]).lower()
        remote = dict(integration["remote"])
        if phase == "INTEGRATION_OBJECT_CREATED":
            current_target, _ = _target_observation(repo, TARGET_BRANCH)
            if current_target != target_predecessor:
                integration["phase"] = "REMOTE_PUSH_REJECTED"
                integration["unknown_reason"] = "local target advanced after integration object creation"
                _persist_integration(actual_receipt_path, receipt, integration)
                raise StaleFacts("local target advanced after the frozen integration object was created")
            remote_sha, fetch_error = _fetch_remote_target(repo, remote)
            integration["remote_prefetch_sha"] = remote_sha
            if fetch_error is not None or remote_sha != target_predecessor:
                integration["phase"] = "REMOTE_PUSH_REJECTED"
                integration["unknown_reason"] = fetch_error or "remote predecessor changed"
                _persist_integration(actual_receipt_path, receipt, integration)
                raise StaleFacts("remote target does not equal the frozen predecessor")
            integration["phase"] = "PUSH_ATTEMPTED"
            integration["push_attempts"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            push = _run_git(
                repo,
                "push",
                "--porcelain",
                f"--force-with-lease={remote['ref']}:{target_predecessor}",
                str(remote["name"]),
                f"{integration_sha}:{remote['ref']}",
                check=False,
            )
            if push.returncode == 0:
                integration["phase"] = "REMOTE_PUSH_COMMITTED"
                integration["remote_post_observation_sha"] = integration_sha
                integration["unknown_reason"] = None
                _persist_integration(actual_receipt_path, receipt, integration)
            else:
                integration["phase"] = "REMOTE_PUSH_UNKNOWN"
                integration["unknown_reason"] = (
                    push.stderr.strip() or push.stdout.strip() or "push outcome is unknown"
                )
                _persist_integration(actual_receipt_path, receipt, integration)
            phase = str(integration["phase"])

        if phase in {"PUSH_ATTEMPTED", "REMOTE_PUSH_UNKNOWN"}:
            if int(integration.get("reconciliation_observations", 0)) != 0:
                raise UnknownApply("orthogonal push has already consumed its reconciliation observation")
            integration["reconciliation_observations"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            observed_remote, reconciliation_error = _fetch_remote_target(repo, remote)
            integration["remote_post_observation_sha"] = observed_remote
            if reconciliation_error is not None:
                integration["phase"] = "REMOTE_PUSH_UNKNOWN"
                integration["unknown_reason"] = reconciliation_error
                _persist_integration(actual_receipt_path, receipt, integration)
                _mark_orthogonal_unknown(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    state,
                    entry,
                    worktree_ref,
                    actual_receipt_path,
                    receipt,
                    integration,
                    "remote push remains unknown after one fetch reconciliation",
                )
                raise UnknownApply(
                    "remote push remains unknown after one fetch reconciliation",
                    details=_integration_observation(integration),
                )
            if observed_remote == integration_sha:
                integration["phase"] = "RECONCILED_COMMITTED"
                integration["unknown_reason"] = None
            elif observed_remote == target_predecessor:
                integration["phase"] = "RECONCILED_NOT_COMMITTED"
                integration["unknown_reason"] = "one push attempt was not observed"
            else:
                integration["phase"] = "RECONCILED_CONFLICTED"
                integration["unknown_reason"] = "remote advanced to an unexpected commit"
            _persist_integration(actual_receipt_path, receipt, integration)
            phase = str(integration["phase"])

        if phase in {"RECONCILED_NOT_COMMITTED", "RECONCILED_CONFLICTED"}:
            raise UnknownApply(
                "orthogonal push attempt did not produce the frozen integration",
                details=_integration_observation(integration),
            )
        if phase not in {"REMOTE_PUSH_COMMITTED", "RECONCILED_COMMITTED", "LOCAL_APPLY_ATTEMPTED"}:
            raise UnknownApply(
                "orthogonal integration is not proven remotely committed",
                details={"integration_phase": phase},
            )

        local_sha, _ = _target_observation(repo, TARGET_BRANCH)
        if local_sha == integration_sha:
            integration["phase"] = "LOCAL_APPLY_COMMITTED"
        elif local_sha != target_predecessor:
            integration["phase"] = "LOCAL_APPLY_UNKNOWN"
            integration["unknown_reason"] = "local target changed after remote proof"
            _persist_integration(actual_receipt_path, receipt, integration)
            _mark_orthogonal_unknown(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                entry,
                worktree_ref,
                actual_receipt_path,
                receipt,
                integration,
                "local target changed after remote proof",
            )
            raise UnknownApply("local target changed after remote proof")
        else:
            integration["phase"] = "LOCAL_APPLY_ATTEMPTED"
            integration["local_apply_attempts"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            local_apply = _run_git(repo, "merge", "--ff-only", integration_sha, check=False)
            observed_local = _branch_sha(repo, TARGET_BRANCH)
            if observed_local == integration_sha:
                integration["phase"] = "LOCAL_APPLY_COMMITTED"
                integration["unknown_reason"] = None
            else:
                integration["phase"] = "LOCAL_APPLY_UNKNOWN"
                integration["unknown_reason"] = (
                    local_apply.stderr.strip()
                    or local_apply.stdout.strip()
                    or "local fast-forward outcome is unknown"
                )
                _persist_integration(actual_receipt_path, receipt, integration)
                _mark_orthogonal_unknown(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    state,
                    entry,
                    worktree_ref,
                    actual_receipt_path,
                    receipt,
                    integration,
                    "local fast-forward outcome is unknown",
                )
                raise UnknownApply("local fast-forward outcome is unknown")
        _persist_integration(actual_receipt_path, receipt, integration)
        if _branch_sha(repo, TARGET_BRANCH) != integration_sha or _status(repo)[
            "tracked_dirty"
        ]:
            raise UnknownApply("local target proof changed before registry transition")

        updated_entry = dict(entry)
        updated_entry["integrated_sha"] = integration_sha
        updated_entry["lifecycle"] = "INTEGRATED"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        updated = _replace_registry_observed(
            repo,
            common,
            container,
            identities,
            state_path,
            state,
            updated_entry,
            worktree_ref,
        )
        receipt["apply_outcome"] = "APPLIED"
        receipt["applied_sha"] = integration_sha
        receipt["applied_at"] = _now()
        receipt["registry_revision"] = updated["revision"]
        receipt["lifecycle"] = "INTEGRATED"
        receipt["last_failure"] = None
        receipt["unknown_outcome"] = None
        receipt["mutation_lease"] = mutation_lease
        receipt["integration"] = integration
        _atomic_write(actual_receipt_path, receipt)
        return {
            "ok": True,
            "operation": "apply",
            "integration_policy": "ORTHOGONAL_DIRECTION",
            "integration_phase": integration["phase"],
            "integrated_sha": integration_sha,
            "worktree": updated_entry,
            "registry_revision": updated["revision"],
        }





def _integrate_push_exact(
    receipt_raw: str,
    actor: str,
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_input, preliminary, worktree_ref, repo, common = _read_receipt_input(
        receipt_raw
    )
    preliminary_sha256 = _digest(preliminary)
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        _validate_apply_actor(actor, entry)
        policy = _integration_policy(entry)
        if policy not in EXACT_POLICIES:
            raise OwnershipRefusal("exact integrate-push requires an exact policy")
        actual_receipt_path, receipt = _load_current_receipt(repo, state, entry)
        if not _same_path(actual_receipt_path, receipt_input):
            raise OwnershipRefusal("receipt path is not the registry-authorized receipt")
        if _digest(receipt) != preliminary_sha256:
            raise StaleFacts("prepared receipt changed before the worktree lock was acquired")
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if entry["lifecycle"] != "PREPARED_FOR_INTEGRATION":
            raise StaleFacts("integrate-push requires a prepared worktree")
        frozen = _validate_integrate_push_contract(
            repo, state, entry, receipt, contract
        )
        candidate, _ = _validated_apply_candidate(
            repo, common, container, state, entry, receipt
        )
        if candidate != frozen["candidate_sha"]:
            raise StaleFacts("validated candidate differs from integrate-push contract")
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        predecessor = frozen["expected_target_predecessor_sha"]
        remote = {
            "name": frozen["remote_name"],
            "ref": frozen["target_remote_ref"],
        }
        integration_value = receipt.get("integration")
        if integration_value is None:
            integration: dict[str, Any] = {
                "version": INTEGRATION_RECEIPT_VERSION,
                "policy": policy,
                "phase": "PREPARED",
                "operation_token": entry["operation_token"],
                "effect_fingerprint": _digest(
                    {
                        "operation_token": entry["operation_token"],
                        "candidate_sha": candidate,
                        "predecessor_sha": predecessor,
                        "remote": remote,
                        "prepared_operation_id": frozen["prepared_operation_id"],
                        "prepared_receipt_sha256": frozen[
                            "prepared_receipt_sha256"
                        ],
                    }
                ),
                "candidate_sha": candidate,
                "predecessor_sha": predecessor,
                "remote": remote,
                "push_attempts": 0,
                "local_apply_attempts": 0,
                "reconciliation_observations": 0,
                "remote_prefetch_sha": None,
                "remote_post_observation_sha": None,
                "unknown_reason": None,
                "prepared_operation_id": frozen["prepared_operation_id"],
                "prepared_receipt_sha256": frozen["prepared_receipt_sha256"],
                "push_authorization_ref": frozen["push_authorization_ref"],
            }
            _persist_integration(actual_receipt_path, receipt, integration)
        elif isinstance(integration_value, Mapping):
            integration = dict(integration_value)
            immutable = {
                "policy": policy,
                "candidate_sha": candidate,
                "predecessor_sha": predecessor,
                "remote": remote,
                "prepared_operation_id": frozen["prepared_operation_id"],
                "prepared_receipt_sha256": frozen["prepared_receipt_sha256"],
                "push_authorization_ref": frozen["push_authorization_ref"],
            }
            if any(integration.get(key) != value for key, value in immutable.items()):
                raise StaleFacts("persisted exact integration intent differs from packet")
        else:
            raise InvalidInput("exact integration receipt has an invalid phase journal")

        phase = str(integration.get("phase"))
        terminal_noncommitted = {
            "REMOTE_PUSH_REJECTED",
            "RECONCILED_NOT_COMMITTED",
            "RECONCILED_CONFLICTED",
        }
        if phase in terminal_noncommitted:
            raise StaleFacts(
                "exact integrate-push attempt is terminal and cannot be retried",
                details={"integration_phase": phase},
            )
        if (
            phase == "REMOTE_PUSH_UNKNOWN"
            and int(integration.get("reconciliation_observations", 0)) >= 1
        ):
            raise UnknownApply(
                "exact push remains unknown after its one observation",
                details=_integration_observation(integration),
            )

        if phase == "PREPARED":
            local_sha, local_status = _target_observation(repo, TARGET_BRANCH)
            if (
                local_sha != predecessor
                or local_status["tracked_dirty"]
                or local_status["nonignored_untracked"]
            ):
                integration["phase"] = "REMOTE_PUSH_REJECTED"
                integration["unknown_reason"] = (
                    "clean local target differs from the frozen predecessor"
                )
                _persist_integration(actual_receipt_path, receipt, integration)
                raise StaleFacts(
                    "clean local target differs from the frozen predecessor"
                )
            remote_sha, fetch_error = _fetch_remote_target(repo, remote)
            integration["remote_prefetch_sha"] = remote_sha
            if fetch_error is not None or remote_sha != predecessor:
                integration["phase"] = "REMOTE_PUSH_REJECTED"
                integration["unknown_reason"] = (
                    fetch_error or "remote predecessor changed"
                )
                _persist_integration(actual_receipt_path, receipt, integration)
                raise StaleFacts("remote target differs from the frozen predecessor")
            integration["phase"] = "PUSH_ATTEMPTED"
            integration["push_attempts"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            push = _run_git(
                repo,
                "push",
                "--porcelain",
                f"--force-with-lease={remote['ref']}:{predecessor}",
                str(remote["name"]),
                f"{candidate}:{remote['ref']}",
                check=False,
            )
            integration["push_reported_success"] = push.returncode == 0
            if push.returncode:
                integration["phase"] = "REMOTE_PUSH_UNKNOWN"
                integration["unknown_reason"] = (
                    push.stderr.strip()
                    or push.stdout.strip()
                    or "push outcome is unknown"
                )
            _persist_integration(actual_receipt_path, receipt, integration)
            phase = str(integration["phase"])

        if phase in {"PUSH_ATTEMPTED", "REMOTE_PUSH_UNKNOWN"}:
            if int(integration.get("reconciliation_observations", 0)) != 0:
                raise UnknownApply(
                    "exact push has already consumed its reconciliation observation"
                )
            integration["reconciliation_observations"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            observed_remote, reconciliation_error = _fetch_remote_target(repo, remote)
            integration["remote_post_observation_sha"] = observed_remote
            if reconciliation_error is not None:
                integration["phase"] = "REMOTE_PUSH_UNKNOWN"
                integration["unknown_reason"] = reconciliation_error
            elif observed_remote == candidate:
                integration["phase"] = (
                    "REMOTE_PUSH_COMMITTED"
                    if integration.get("push_reported_success") is True
                    else "RECONCILED_COMMITTED"
                )
                integration["unknown_reason"] = None
            elif observed_remote == predecessor:
                integration["phase"] = "RECONCILED_NOT_COMMITTED"
                integration["unknown_reason"] = "one push attempt was not observed"
            else:
                integration["phase"] = "RECONCILED_CONFLICTED"
                integration["unknown_reason"] = "remote advanced to an unexpected commit"
            _persist_integration(actual_receipt_path, receipt, integration)
            phase = str(integration["phase"])
            if phase in {
                "REMOTE_PUSH_UNKNOWN",
                "RECONCILED_NOT_COMMITTED",
                "RECONCILED_CONFLICTED",
            }:
                _mark_orthogonal_unknown(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    state,
                    entry,
                    worktree_ref,
                    actual_receipt_path,
                    receipt,
                    integration,
                    str(integration["unknown_reason"]),
                )
                raise UnknownApply(
                    "exact remote push outcome is not safely committed",
                    details=_integration_observation(integration),
                )

        if phase not in {
            "REMOTE_PUSH_COMMITTED",
            "RECONCILED_COMMITTED",
            "LOCAL_APPLY_ATTEMPTED",
        }:
            raise UnknownApply(
                "exact integration is not proven remotely committed",
                details={"integration_phase": phase},
            )
        local_sha, local_status = _target_observation(repo, TARGET_BRANCH)
        if local_status["tracked_dirty"] or local_status["nonignored_untracked"]:
            integration["phase"] = "LOCAL_APPLY_UNKNOWN"
            integration["unknown_reason"] = "local target became dirty after remote proof"
            _persist_integration(actual_receipt_path, receipt, integration)
            _mark_orthogonal_unknown(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                entry,
                worktree_ref,
                actual_receipt_path,
                receipt,
                integration,
                str(integration["unknown_reason"]),
            )
            raise UnknownApply(str(integration["unknown_reason"]))
        if local_sha == candidate:
            integration["phase"] = "LOCAL_APPLY_COMMITTED"
        elif local_sha != predecessor:
            integration["phase"] = "LOCAL_APPLY_UNKNOWN"
            integration["unknown_reason"] = "local target changed after remote proof"
            _persist_integration(actual_receipt_path, receipt, integration)
            _mark_orthogonal_unknown(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                entry,
                worktree_ref,
                actual_receipt_path,
                receipt,
                integration,
                str(integration["unknown_reason"]),
            )
            raise UnknownApply(str(integration["unknown_reason"]))
        else:
            integration["phase"] = "LOCAL_APPLY_ATTEMPTED"
            integration["local_apply_attempts"] = 1
            _persist_integration(actual_receipt_path, receipt, integration)
            local_apply = _run_git(repo, "merge", "--ff-only", candidate, check=False)
            if (
                local_apply.returncode
                or _branch_sha(repo, TARGET_BRANCH) != candidate
                or _current_branch(repo) != TARGET_BRANCH
            ):
                integration["phase"] = "LOCAL_APPLY_UNKNOWN"
                integration["unknown_reason"] = (
                    local_apply.stderr.strip()
                    or local_apply.stdout.strip()
                    or "local fast-forward outcome is unknown"
                )
                _persist_integration(actual_receipt_path, receipt, integration)
                _mark_orthogonal_unknown(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    state,
                    entry,
                    worktree_ref,
                    actual_receipt_path,
                    receipt,
                    integration,
                    str(integration["unknown_reason"]),
                )
                raise UnknownApply(str(integration["unknown_reason"]))
            integration["phase"] = "LOCAL_APPLY_COMMITTED"
            integration["unknown_reason"] = None
        _persist_integration(actual_receipt_path, receipt, integration)

        updated_entry = dict(entry)
        updated_entry["integrated_sha"] = candidate
        updated_entry["lifecycle"] = "INTEGRATED"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        try:
            updated = _replace_registry_observed(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                updated_entry,
                worktree_ref,
            )
        except Exception as exc:
            _mark_orthogonal_unknown(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                entry,
                worktree_ref,
                actual_receipt_path,
                receipt,
                integration,
                f"remote and local committed but registry outcome is unknown: {exc}",
            )
            raise UnknownApply(
                "remote and local committed but registry outcome is unknown"
            ) from exc
        receipt.update(
            {
                "apply_outcome": "APPLIED",
                "applied_sha": candidate,
                "applied_at": _now(),
                "registry_revision": updated["revision"],
                "lifecycle": "INTEGRATED",
                "last_failure": None,
                "unknown_outcome": None,
                "mutation_lease": mutation_lease,
                "integration": integration,
            }
        )
        _atomic_write(actual_receipt_path, receipt)
        return {
            "ok": True,
            "operation": "integrate-push",
            "integration_policy": policy,
            "integration_phase": integration["phase"],
            "integrated_sha": candidate,
            "worktree": updated_entry,
            "receipt": str(actual_receipt_path),
            "registry_revision": updated["revision"],
            "validated_contract": frozen,
        }


def integrate_push(
    receipt_raw: str,
    actor: str,
    contract_raw: Mapping[str, Any],
    mutation_lease_raw: Mapping[str, Any] | None,
    expected_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Execute one current-policy remote-first integration."""

    expected = _require_exact_worktree_mutation(expected_raw)
    _, preliminary, worktree_ref, repo, common = _read_receipt_input(receipt_raw)
    loaded = _load_registry(repo)
    assert loaded is not None
    entry = _entry(loaded[1], worktree_ref)
    policy = _integration_policy(entry)
    if preliminary.get("integration_policy") != policy:
        raise StaleFacts("receipt and registry integration policies differ")
    if contract_raw.get("policy") != policy:
        raise StaleFacts("integrate-push contract policy differs from registry")
    with _target_lock(common, TARGET_BRANCH):
        if policy == "ORTHOGONAL_DIRECTION":
            result = _apply_orthogonal(
                receipt_raw,
                actor,
                mutation_lease_raw,
                expected,
                integrate_contract=contract_raw,
            )
            result = dict(result)
            result["operation"] = "integrate-push"
            result["receipt"] = str(
                _receipt_path(repo, result["worktree"])
            )
            loaded_after = _load_registry(repo)
            assert loaded_after is not None
            result["validated_contract"] = _validate_integrate_push_contract(
                repo,
                loaded_after[1],
                result["worktree"],
                _load_receipt(repo, result["worktree"])[1],
                contract_raw,
            )
            return result
        return _integrate_push_exact(
            receipt_raw,
            actor,
            mutation_lease_raw,
            expected,
            contract_raw,
        )


def _residue_paths(target: Path, status: Mapping[str, Any]) -> list[str]:
    paths = list(status.get("ignored_only", []))
    for raw in paths:
        if not isinstance(raw, str) or not raw or raw.startswith("/") or ".." in Path(raw).parts:
            raise UnsafeState("ignored residue path is not a safe worktree-relative path")
        candidate = target / Path(raw)
        _assert_no_symlink_chain(candidate, label="ignored residue", require_existing=True)
        if not _under(candidate, target):
            raise UnsafeState("ignored residue escaped worktree")
    return sorted(set(paths))

def _remove_exact(repo: Path, entry: Mapping[str, Any], *, force: bool, expected_branch_sha: str) -> None:
    target = _canonical_path(str(entry["canonical_absolute_path"]), label="worktree", must_exist=True, directory=True)
    branch = str(entry["branch"])
    if not branch.startswith("omp/"):
        raise OwnershipRefusal("refusing to mutate a non-OMP branch")
    registrations = _registration(repo, target)
    if len(registrations) != 1 or registrations[0].get("branch") != f"refs/heads/{branch}" or str(registrations[0].get("head", "")).lower() != expected_branch_sha:
        raise UnsafeState("worktree registration changed before release")
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(target))
    _run_git(repo, *args)
    if _lstat(target) is not None or _registration(repo, target):
        raise UnknownApply("Git worktree removal outcome is unknown")
    if _branch_sha(repo, branch) != expected_branch_sha:
        raise StaleFacts("temporary branch changed before deletion")
    _run_git(repo, "update-ref", "-d", f"refs/heads/{branch}", expected_branch_sha)
    if _branch_sha(repo, branch) is not None:
        raise UnknownApply("temporary branch deletion outcome is unknown")


def _retain_locked(
    repo: Path,
    common: Path,
    container: Path,
    identities: Mapping[str, Any],
    state_path: Path,
    state: dict[str, Any],
    entry: dict[str, Any],
    receipt_path: Path,
    receipt: dict[str, Any],
    worktree_ref: str,
    reason: str,
    mutation_lease_raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if entry["lifecycle"] in TERMINAL_LIFECYCLES or entry["lifecycle"] in UNKNOWN_LIFECYCLES:
        raise UnsafeState("terminal or unknown-outcome worktree cannot be retained")
    state, entry, receipt = _refresh_locked_documents(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
        state,
        entry,
        receipt_path,
        receipt,
    )
    mutation_lease = _validate_mutation_lease(
        repo,
        str(entry["assignment_id"]),
        mutation_lease_raw,
        required=True,
    )
    _ensure_controlled_checkout(repo, entry, candidate=str(entry["base_sha"]).lower())
    updated_entry = dict(entry)
    updated_entry["lifecycle"] = "RETAINED_FOR_RECOVERY"
    updated_entry["unknown_outcome"] = None
    updated_entry["mutation_lease"] = mutation_lease
    _replace_registry_observed(
        repo,
        common,
        container,
        identities,
        state_path,
        state,
        updated_entry,
        worktree_ref,
    )
    updated, updated_entry, receipt = _documents_after_registry_transition(
        repo,
        common,
        container,
        identities,
        state_path,
        worktree_ref,
        updated_entry,
        receipt_path,
        receipt,
    )
    _ensure_controlled_checkout(
        repo, updated_entry, candidate=str(updated_entry["base_sha"]).lower()
    )
    receipt["lifecycle"] = "RETAINED_FOR_RECOVERY"
    receipt["retention_reason"] = reason
    receipt["retained_at"] = _now()
    receipt["registry_revision"] = updated["revision"]
    receipt["last_failure"] = None
    receipt["unknown_outcome"] = None
    receipt["mutation_lease"] = mutation_lease
    _atomic_write(receipt_path, receipt)
    return {
        "ok": True,
        "operation": "retain",
        "status": "RETAINED_FOR_RECOVERY",
        "reason": reason,
        "worktree": updated_entry,
        "registry_revision": updated["revision"],
    }


def _release_worktree_facts(
    repo: Path,
    entry: Mapping[str, Any],
    ignored_artifacts: str,
    *,
    require_disposable: bool,
) -> tuple[Path, list[str], str]:
    target, _, status = _ensure_controlled_checkout(
        repo, entry, candidate=str(entry["base_sha"]).lower()
    )
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("release refused: tracked, staged, or non-ignored residue exists")
    ignored = _residue_paths(target, status) if status["ignored_only"] else []
    if ignored and ignored_artifacts == "refuse":
        raise DecisionRequired("release requires an ignored-artifact disposition")
    branch_sha = _branch_sha(repo, str(entry["branch"]))
    if not require_disposable:
        if branch_sha is None:
            raise StaleFacts("temporary branch disappeared before retain")
        return target, ignored, branch_sha
    candidate = str(entry.get("candidate_sha") or "").lower()
    if candidate:
        integrated_sha = str(entry.get("integrated_sha") or "").lower()
        if entry["lifecycle"] != "INTEGRATED" or not _FULL_SHA.fullmatch(integrated_sha):
            raise UnsafeState("release requires an integrated candidate or explicit retain")
        reachable_sha = (
            integrated_sha
            if _integration_policy(entry) == "ORTHOGONAL_DIRECTION"
            else candidate
        )
        target_sha = _branch_sha(repo, TARGET_BRANCH)
        if (
            target_sha is None
            or _run_git(
                repo,
                "merge-base",
                "--is-ancestor",
                reachable_sha,
                TARGET_BRANCH,
                check=False,
            ).returncode
            != 0
        ):
            raise StaleFacts("integrated result is not reachable from omp/workflow")
        if branch_sha != str(entry["base_sha"]).lower():
            raise StaleFacts("temporary base branch changed before release")
    elif (
        entry["lifecycle"] not in {"PROVISIONED", "CANDIDATE_READY", "PREPARED_FOR_INTEGRATION"}
        or branch_sha != str(entry["base_sha"]).lower()
    ):
        raise UnsafeState("worktree without a candidate is not safely disposable")
    assert branch_sha is not None
    return target, ignored, branch_sha




def release(
    repo_raw: str,
    worktree_ref: str,
    actor: str,
    ignored_artifacts: str,
    mutation_lease_raw: Mapping[str, Any] | None = None,
    expected_raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if actor != "root":
        raise OwnershipRefusal("only Root may release a worktree")
    if ignored_artifacts not in {"refuse", "discard", "retain"}:
        raise InvalidInput("ignored-artifacts must be refuse, discard, or retain")
    if ignored_artifacts == "refuse":
        raise DecisionRequired("release disposition refuse authorizes zero effect")
    repo, common = _repo_context(repo_raw)
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        _validate_operation_expectations(
            repo, container, state, entry, receipt, expected_raw
        )
        if entry["lifecycle"] in TERMINAL_LIFECYCLES or entry["lifecycle"] in UNKNOWN_LIFECYCLES:
            raise UnsafeState("worktree is terminal or has an unknown effect outcome")
        state, entry, receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            receipt_path,
            receipt,
        )
        mutation_lease = _validate_mutation_lease(
            repo,
            str(entry["assignment_id"]),
            mutation_lease_raw,
            required=True,
        )
        target, ignored, branch_sha = _release_worktree_facts(
            repo,
            entry,
            ignored_artifacts,
            require_disposable=ignored_artifacts != "retain",
        )
        if ignored_artifacts == "retain":
            retained = _retain_locked(
                repo,
                common,
                container,
                identities,
                state_path,
                state,
                entry,
                receipt_path,
                receipt,
                worktree_ref,
                "Root retained ignored artifacts for recovery",
                mutation_lease_raw,
            )
            retained["operation"] = "release"
            return retained

        intent_receipt = dict(receipt)
        intent_receipt["release_intent"] = "DISCARD_IGNORED" if ignored else "EMPTY"
        intent_receipt["release_outcome"] = "PENDING"
        intent_receipt["discarded_paths"] = ignored
        intent_receipt["release_requested_at"] = _now()
        intent_receipt["last_failure"] = None
        intent_receipt["unknown_outcome"] = None
        intent_receipt["mutation_lease"] = mutation_lease
        _atomic_write(receipt_path, intent_receipt)

        state, entry, intent_receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            receipt_path,
            intent_receipt,
        )
        current_target, current_ignored, current_branch_sha = _release_worktree_facts(
            repo,
            entry,
            ignored_artifacts,
            require_disposable=True,
        )
        if (
            not _same_path(current_target, target)
            or current_ignored != ignored
            or current_branch_sha != branch_sha
        ):
            raise StaleFacts("release facts advanced after intent journaling")
        try:
            _remove_exact(
                repo,
                entry,
                force=bool(ignored),
                expected_branch_sha=branch_sha,
            )
        except Exception as exc:
            message = f"release Git/path effect is unknown: {exc}"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                receipt_path,
                intent_receipt,
                operation="RELEASE",
                error=message,
            )
            raise UnknownApply(message) from exc

        try:
            _refresh_locked_documents(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                receipt_path,
                intent_receipt,
            )
            observation = _effect_observation(repo, entry)
            if (
                observation["worktree_exists"]
                or observation["registration_count"] != 0
                or observation["branch_sha"] is not None
            ):
                raise UnsafeState("release removal could not be proven exact")
        except WorktreeError as exc:
            message = f"release effect completed but locked facts advanced before registry CAS: {exc}"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                receipt_path,
                intent_receipt,
                operation="RELEASE",
                error=message,
            )
            raise UnknownApply(message) from exc

        updated_entry = dict(entry)
        updated_entry["lifecycle"] = "RELEASED"
        updated_entry["unknown_outcome"] = None
        updated_entry["mutation_lease"] = mutation_lease
        try:
            updated = _replace_registry(
                state_path,
                _put_entry(state, updated_entry, worktree_ref),
                int(state["revision"]),
            )
        except Exception as exc:
            landed = _landed_registry_transition(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                updated_entry,
            )
            if landed is not None:
                updated = landed
            else:
                message = f"release effect completed but registry CAS is unknown: {exc}"
                _journal_unknown_after_effect(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    worktree_ref,
                    state,
                    entry,
                    receipt_path,
                    intent_receipt,
                    operation="RELEASE",
                    error=message,
                )
                raise UnknownApply(message) from exc

        try:
            updated, updated_entry, receipt = _documents_after_registry_transition(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                updated_entry,
                receipt_path,
                intent_receipt,
            )
            observation = _effect_observation(repo, updated_entry)
            if (
                observation["worktree_exists"]
                or observation["registration_count"] != 0
                or observation["branch_sha"] is not None
            ):

                raise UnsafeState("release facts changed before final receipt persistence")
        except WorktreeError as exc:
            message = f"release registry landed but receipt persistence facts are unknown: {exc}"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                receipt_path,
                intent_receipt,
                operation="RELEASE",
                error=message,
            )
            raise UnknownApply(message) from exc

        receipt["release_outcome"] = "RELEASED"
        receipt["lifecycle"] = "RELEASED"
        receipt["released_at"] = _now()
        receipt["registry_revision"] = updated["revision"]
        receipt["last_failure"] = None
        receipt["unknown_outcome"] = None
        receipt["mutation_lease"] = mutation_lease
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "release",
            "status": "RELEASED",
            "discarded_paths": ignored,
            "worktree": updated_entry,
            "registry_revision": updated["revision"],
        }


def _content_refs_from_arguments(
    values: Sequence[str],
    *,
    label: str,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for raw in values:
        if "=" not in raw:
            raise InvalidInput(f"{label} must be PATH=SHA256")
        path, digest = raw.rsplit("=", 1)
        refs.append({"path": path, "sha256": digest})
    return refs


def _add_precondition_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-registry-revision", type=int)
    parser.add_argument("--expected-lifecycle")
    parser.add_argument("--expected-worktree-path")
    parser.add_argument("--expected-container-path")
    parser.add_argument("--expected-receipt-sha256")


def _add_mutation_lease_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manager-assignment-id")
    parser.add_argument("--clerk-assignment-id")
    parser.add_argument("--handoff-ref")
    parser.add_argument("--handoff-sha256")
    parser.add_argument("--lease-token")

def _integrate_contract_from_namespace(args: argparse.Namespace) -> dict[str, Any]:
    verification_refs: list[dict[str, str]] = []
    for raw in args.verification_content_ref:
        if "=" not in raw:
            raise InvalidInput(
                "--verification-content-ref must be PATH=SHA256"
            )
        path, digest = raw.rsplit("=", 1)
        verification_refs.append({"path": path, "sha256": digest})
    return {
        "policy": args.policy,
        "candidate_sha": args.candidate,
        "base_sha": args.base,
        "target_local_ref": args.target_local_ref,
        "target_remote_ref": args.target_remote_ref,
        "remote_name": args.remote_name,
        "expected_target_predecessor_sha": args.expected_target_predecessor,
        "expected_remote_predecessor_sha": args.expected_remote_predecessor,
        "prepared_operation_id": args.prepared_operation_id,
        "prepared_receipt_sha256": args.prepared_receipt_sha256,
        "allowed_paths": args.allowed_path,
        "changed_paths": args.changed_path,
        "dependency_paths": args.dependency_path,
        "diff_sha256": args.diff_sha256,
        "verification_refs": verification_refs,
        "push_authorization_ref": {
            "path": args.push_authorization_ref,
            "sha256": args.push_authorization_sha256,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    provision_parser = sub.add_parser("provision")
    provision_parser.add_argument("--repo", required=True)
    provision_parser.add_argument("--container")
    provision_parser.add_argument("--direction", required=True)
    provision_parser.add_argument("--kind", required=True, choices=["research", "engineering"])
    provision_parser.add_argument("--assignment", required=True)
    provision_parser.add_argument("--base", required=True)
    provision_parser.add_argument(
        "--integration-policy",
        required=True,
        choices=sorted(INTEGRATION_POLICIES),
    )
    provision_parser.add_argument("--parallel-set-manifest")
    provision_parser.add_argument("--required-handoff-sha")
    provision_parser.add_argument(
        "--required-dependency-ref", action="append", default=[]
    )
    _add_mutation_lease_args(provision_parser)
    _add_precondition_args(provision_parser)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--worktree-ref", required=True)
    inspect_parser.add_argument("--repo", default=".")
    _add_precondition_args(inspect_parser)
    repository_parser = sub.add_parser(
        "inspect-repository",
        help="read exact local and optional remote target facts without mutation",
    )
    repository_parser.add_argument("--repo", default=".")
    repository_parser.add_argument(
        "--target",
        required=True,
        choices=[TARGET_BRANCH],
    )
    repository_parser.add_argument("--remote-name")
    repository_parser.add_argument("--remote-ref")
    observe_parser = sub.add_parser(
        "observe",
        help="read result-blind registry, receipt, and physical worktree facts",
    )
    observe_parser.add_argument("--repo", default=".")
    observe_parser.add_argument("--worktree-ref", required=True)
    validate_candidate_parser = sub.add_parser(
        "validate-candidate",
        help="validate frozen candidate tree facts without mutation",
    )
    validate_candidate_parser.add_argument("--repo", default=".")
    validate_candidate_parser.add_argument("--base", required=True)
    validate_candidate_parser.add_argument("--candidate", required=True)
    validate_candidate_parser.add_argument(
        "--allowed-path",
        action="append",
        required=True,
    )
    validate_candidate_parser.add_argument(
        "--expected-changed-path",
        action="append",
        required=True,
    )
    validate_candidate_parser.add_argument(
        "--expected-diff-sha256",
        required=True,
    )
    patch_parser = sub.add_parser(
        "apply-patch",
        help="prospectively prepare one exact patch tree in a temporary index",
    )
    patch_parser.add_argument("--repo", default=".")
    patch_parser.add_argument("--worktree-ref", required=True)
    patch_parser.add_argument("--base", required=True)
    patch_parser.add_argument("--baseline-tree", required=True)
    patch_parser.add_argument("--patch", required=True)
    patch_parser.add_argument("--patch-sha256", required=True)
    patch_parser.add_argument("--allowed-path", action="append", required=True)
    patch_parser.add_argument("--expected-changed-path", action="append", required=True)
    patch_parser.add_argument("--expected-diff-sha256", required=True)
    patch_parser.add_argument("--expected-result-tree", required=True)
    _add_mutation_lease_args(patch_parser)
    _add_precondition_args(patch_parser)
    create_parser = sub.add_parser(
        "create-candidate",
        help="create one immutable candidate commit/ref from a prepared-tree receipt",
    )
    create_parser.add_argument("--repo", default=".")
    create_parser.add_argument("--worktree-ref", required=True)
    create_parser.add_argument("--base", required=True)
    create_parser.add_argument("--prepared-tree-receipt", required=True)
    create_parser.add_argument("--prepared-tree-receipt-sha256", required=True)
    create_parser.add_argument("--allowed-path", action="append", required=True)
    create_parser.add_argument("--expected-changed-path", action="append", required=True)
    create_parser.add_argument("--expected-diff-sha256", required=True)
    create_parser.add_argument("--expected-tree", required=True)
    create_parser.add_argument("--metadata", required=True)
    create_parser.add_argument("--metadata-sha256", required=True)
    _add_mutation_lease_args(create_parser)
    _add_precondition_args(create_parser)
    candidate_parser = sub.add_parser("record-candidate")
    candidate_parser.add_argument("--worktree-ref", required=True)
    candidate_parser.add_argument("--candidate", required=True)
    candidate_parser.add_argument("--repo", default=".")
    _add_mutation_lease_args(candidate_parser)
    _add_precondition_args(candidate_parser)
    prepare_parser = sub.add_parser("prepare-integration")
    prepare_parser.add_argument("--worktree-ref", required=True)
    prepare_parser.add_argument("--target", required=True)
    prepare_parser.add_argument("--allowed-path", action="append", required=True)
    prepare_parser.add_argument("--verification-ref", action="append", default=[])
    prepare_parser.add_argument("--repo", default=".")
    _add_mutation_lease_args(prepare_parser)
    _add_precondition_args(prepare_parser)
    integrate_parser = sub.add_parser(
        "integrate-push",
        help="execute one exact remote-first integration and local fast-forward",
    )
    integrate_parser.add_argument("--receipt", required=True)
    integrate_parser.add_argument("--actor", required=True)
    integrate_parser.add_argument(
        "--policy", required=True, choices=sorted(INTEGRATION_POLICIES)
    )
    integrate_parser.add_argument("--candidate", required=True)
    integrate_parser.add_argument("--base", required=True)
    integrate_parser.add_argument(
        "--target-local-ref", required=True, choices=[TARGET_BRANCH]
    )
    integrate_parser.add_argument("--target-remote-ref", required=True)
    integrate_parser.add_argument("--remote-name", required=True)
    integrate_parser.add_argument("--expected-target-predecessor", required=True)
    integrate_parser.add_argument("--expected-remote-predecessor", required=True)
    integrate_parser.add_argument("--prepared-operation-id", required=True)
    integrate_parser.add_argument("--prepared-receipt-sha256", required=True)
    integrate_parser.add_argument("--allowed-path", action="append", required=True)
    integrate_parser.add_argument("--changed-path", action="append", required=True)
    integrate_parser.add_argument("--dependency-path", action="append", default=[])
    integrate_parser.add_argument("--diff-sha256", required=True)
    integrate_parser.add_argument(
        "--verification-content-ref", action="append", required=True
    )
    integrate_parser.add_argument("--push-authorization-ref", required=True)
    integrate_parser.add_argument("--push-authorization-sha256", required=True)
    _add_mutation_lease_args(integrate_parser)
    _add_precondition_args(integrate_parser)
    release_parser = sub.add_parser("release")
    release_parser.add_argument("--worktree-ref", required=True)
    release_parser.add_argument("--actor", required=True)
    release_parser.add_argument(
        "--ignored-artifacts",
        choices=["refuse", "discard", "retain"],
        required=True,
    )
    release_parser.add_argument("--repo", default=".")
    _add_mutation_lease_args(release_parser)
    _add_precondition_args(release_parser)
    return parser


def _emit_error(operation: str, exc: WorktreeError) -> int:
    value: dict[str, Any] = {"ok": False, "operation": operation, "error": str(exc), "code": exc.code}
    value.update(exc.details)
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return exc.code


def main(argv: Iterable[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        if args.operation == "provision":
            result = provision(
                args.repo,
                args.container,
                args.direction,
                args.kind,
                args.assignment,
                args.base,
                args.integration_policy,
                args.parallel_set_manifest,
                args.required_handoff_sha,
                _content_refs_from_arguments(
                    args.required_dependency_ref,
                    label="--required-dependency-ref",
                ),
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "inspect":
            result = inspect(
                args.repo,
                args.worktree_ref,
                _expectations_from_namespace(args),
            )
        elif args.operation == "inspect-repository":
            result = inspect_repository(
                args.repo,
                args.target,
                args.remote_name,
                args.remote_ref,
            )
        elif args.operation == "observe":
            result = observe(
                args.repo,
                args.worktree_ref,
            )
        elif args.operation == "validate-candidate":
            result = validate_candidate(
                args.repo,
                args.base,
                args.candidate,
                args.allowed_path,
                args.expected_changed_path,
                args.expected_diff_sha256,
            )
        elif args.operation == "apply-patch":
            result = apply_patch(
                args.repo,
                args.worktree_ref,
                args.base,
                args.baseline_tree,
                args.patch,
                args.patch_sha256,
                args.allowed_path,
                args.expected_changed_path,
                args.expected_diff_sha256,
                args.expected_result_tree,
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "create-candidate":
            result = create_candidate(
                args.repo,
                args.worktree_ref,
                args.base,
                args.prepared_tree_receipt,
                args.prepared_tree_receipt_sha256,
                args.allowed_path,
                args.expected_changed_path,
                args.expected_diff_sha256,
                args.expected_tree,
                args.metadata,
                args.metadata_sha256,
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "record-candidate":
            result = record_candidate(
                args.repo,
                args.worktree_ref,
                args.candidate,
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "prepare-integration":
            result = prepare_integration(
                args.repo,
                args.worktree_ref,
                args.target,
                args.allowed_path,
                args.verification_ref,
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "integrate-push":
            result = integrate_push(
                args.receipt,
                args.actor,
                _integrate_contract_from_namespace(args),
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        elif args.operation == "release":
            result = release(
                args.repo,
                args.worktree_ref,
                args.actor,
                args.ignored_artifacts,
                _lease_from_namespace(args),
                _expectations_from_namespace(args),
            )
        else:
            raise InvalidInput("unsupported worktree operation")
    except WorktreeError as exc:
        return _emit_error(getattr(locals().get("args", None), "operation", "unknown"), exc)
    except (OSError, subprocess.SubprocessError) as exc:
        return _emit_error(getattr(locals().get("args", None), "operation", "unknown"), WorktreeError(str(exc)))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
