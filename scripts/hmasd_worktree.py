#!/usr/bin/env python3
"""Root-owned Git worktree lifecycle for the HMASD workflow.

The helper deliberately keeps the lifecycle small and fail-closed.  Git is the
source of truth for checkout and ref state; ``.omp/runtime/worktrees.json`` is
an ignored, CAS-protected journal maintained through ``hmasd_state.py``.  A
receipt captures every fact used by prepare/apply so Root never applies a stale
plan.
"""

from __future__ import annotations

import argparse
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

LIFECYCLES = {
    "PROVISIONING",
    "PROVISIONED",
    "CANDIDATE_READY",
    "PREPARED_FOR_INTEGRATION",
    "INTEGRATED",
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


def _load_registry(repo: Path, *, required: bool = True) -> tuple[Path, dict[str, Any]] | None:
    path = _runtime_path(repo)
    if _lstat(path) is None:
        if required:
            raise UnsafeState("runtime worktree registry is absent")
        return None
    _state_call("validate", path=path)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidInput(f"runtime registry is unreadable: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(state.get("worktrees"), list):
        raise InvalidInput("runtime registry has invalid shape")
    if not isinstance(state.get("revision"), int) or state["revision"] < 1:
        raise InvalidInput("runtime registry revision is invalid")
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
    state = {"schema_version": 1, "revision": 1, "updated_at": _now(), "writer": "Root", "worktrees": []}
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


def _new_entry(container: Path, direction: str, kind: str, assignment: str, base: str, token: str) -> dict[str, Any]:
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
        "kind": kind,
        "lifecycle": "PROVISIONING",
        "operation_token": token,
        "receipt_path": f"temp/runtime/receipts/{ref}.json",
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
        "registry_revision": registry_revision,
        "lifecycle": entry["lifecycle"],
        "changed_paths": [],
        "allowed_paths": [],
        "verification_evidence": {"status": "MISSING", "refs": [], "missing": []},
        "conflict": {"status": "NOT_CHECKED", "detail": None},
        "facts": None,
        "facts_sha256": None,
        "created_at": _now(),
        "last_failure": None,
        "apply_outcome": None,
        "release_outcome": None,
        "discarded_paths": [],
        "retention_reason": None,
        "unknown_outcome": None,
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
    if not isinstance(revision, int) or isinstance(revision, bool) or revision != int(state["revision"]):
        raise StaleFacts("worktree receipt registry revision does not match the locked registry")
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
    for raw in refs:
        value = _validate_relative(raw, label="verification reference")
        if value not in normalized:
            normalized.append(value)
        if not (repo / Path(value)).is_file():
            missing.append(value)
    normalized.sort()
    missing.sort()
    return {"status": "PRESENT" if normalized and not missing else "MISSING", "refs": normalized, "missing": missing}


def _record_failure(receipt_path: Path, receipt: Mapping[str, Any], message: str) -> None:
    updated = dict(receipt)
    updated["last_failure"] = {"at": _now(), "message": message}
    try:
        _atomic_write(receipt_path, updated)
    except OSError:
        pass


def _reconcile_provisioning(state_path: Path, state: dict[str, Any], entry: dict[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    if entry.get("lifecycle") != "PROVISIONING" or not observation.get("exact_registration"):
        raise UnsafeState("an existing worktree journal requires exact Root reconciliation", details={"observation": observation})
    updated_entry = dict(entry)
    updated_entry["lifecycle"] = "PROVISIONED"
    updated_state = _put_entry(state, updated_entry, str(entry["worktree_ref"]))
    final = _replace_registry(state_path, updated_state, int(state["revision"]))
    return _entry(final, str(entry["worktree_ref"]))


def provision(repo_raw: str, container_raw: str | None, direction: str, kind: str, assignment: str, base_raw: str) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    direction = _validate_direction(direction)
    kind = _validate_kind(kind)
    assignment = _validate_assignment(assignment)
    base = _verify_commit(repo, base_raw, label="base")
    container = _validate_container(Path(container_raw) if container_raw else _default_container(repo), repo, common, create=True)
    target = _target_path(container, direction, kind, assignment)
    branch = _branch_name(direction, kind, assignment)
    ref = _worktree_ref(direction, kind, assignment)
    with _container_lock(container) as identities:
        _revalidate_container(container, identities)
        state_loaded = _initialize_registry(repo)
        state_path, state = state_loaded
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
        entry = _new_entry(container, direction, kind, assignment, base, token)
        state_with_entry = dict(state)
        state_with_entry["worktrees"] = [*state.get("worktrees", []), entry]

        journal = _replace_registry(state_path, state_with_entry, int(state["revision"]))
        receipt = _receipt_skeleton(repo, container, entry, int(journal["revision"]))
        receipt_path = _write_receipt_for(repo, entry, receipt)
        created = False
        try:
            _revalidate_container(container, identities)
            if _lstat(target) is not None or _branch_sha(repo, branch) is not None:
                raise UnsafeState("worktree namespace changed after PROVISIONING journal")
            _run_git(repo, "worktree", "add", "-b", branch, str(target), base)
            created = True
            target_identity = _identity(target)
            _revalidate_container(container, identities)
            if not _identity_equal(target, target_identity):
                raise UnsafeState("worktree target identity changed after git worktree add")
            registrations = _registration(repo, target)
            if len(registrations) != 1 or registrations[0].get("branch") != f"refs/heads/{branch}" or str(registrations[0].get("head", "")).lower() != base:
                raise UnsafeState("created worktree registration failed exact identity checks")
            status = _status(target)
            if status["tracked_dirty"] or status["nonignored_untracked"]:
                raise UnsafeState("created worktree is not clean")
            final_entry = dict(entry)
            final_entry["lifecycle"] = "PROVISIONED"
            final_state = _replace_registry(state_path, _put_entry(journal, final_entry, ref), int(journal["revision"]))
            receipt["registry_revision"] = int(final_state["revision"])
            receipt["lifecycle"] = "PROVISIONED"
            receipt["provisioned_at"] = _now()
            _atomic_write(receipt_path, receipt)
            return {"ok": True, "operation": "provision", "worktree": final_entry, "receipt": str(receipt_path), "registry_revision": final_state["revision"]}
        except Exception as exc:
            _record_failure(receipt_path, receipt, str(exc))
            # Roll back only the exact registration created by this operation.
            if created:
                try:
                    registrations = _registration(repo, target)
                    branch_sha = _branch_sha(repo, branch)
                    if len(registrations) == 1 and registrations[0].get("branch") == f"refs/heads/{branch}" and str(registrations[0].get("head", "")).lower() == base and branch_sha == base and _identity_equal(target, _identity(target)):
                        _run_git(repo, "worktree", "remove", "--force", str(target))
                        if _branch_sha(repo, branch) == base:
                            _run_git(repo, "update-ref", "-d", f"refs/heads/{branch}", base)
                except Exception:
                    pass
            if isinstance(exc, WorktreeError):
                raise
            raise WorktreeError(str(exc)) from exc


def inspect(repo_raw: str, worktree_ref: str) -> dict[str, Any]:
    repo, common = _repo_context(repo_raw)
    loaded = _load_registry(repo)
    assert loaded is not None
    _, state = loaded
    entry = _entry(state, worktree_ref)
    container = _validate_container(Path(str(entry["canonical_absolute_path"])).parent, repo, common, create=False)

    with _container_lock(container):
        observation = _observation(repo, entry)
    result = {
        "ok": True,
        "operation": "inspect",
        "worktree": entry,
        "observation": observation,
        "orphaned": bool(observation.get("orphaned")),
        "orphan_reason": observation.get("orphan_reason"),
        "registry_revision": state["revision"],
    }
    if observation.get("orphaned"):
        raise UnsafeState("worktree journal and Git registration require reconciliation", details=result)
    return result


def _record_candidate_facts(repo: Path, entry: Mapping[str, Any], candidate_raw: str) -> str:
    candidate = _verify_commit(repo, candidate_raw, label="candidate")
    target, registration, status = _ensure_controlled_checkout(
        repo,
        entry,
        candidate=candidate,
        check_head=False,
    )
    head = _git_value(target, "rev-parse", "--verify", "HEAD").lower()
    if head != candidate or registration.get("head") != candidate:
        if head != str(entry["base_sha"]).lower():
            raise UnsafeState("candidate is behind an extra commit on the worktree branch")
        raise StaleFacts("candidate must exactly match worktree HEAD")
    if candidate == str(entry["base_sha"]).lower():
        raise UnsafeState("base commit cannot be recorded as a candidate")
    if _candidate_parent(repo, candidate) != str(entry["base_sha"]).lower():
        raise UnsafeState("candidate must be one clean commit directly descended from base")
    if _branch_sha(repo, str(entry["branch"])) != candidate:
        raise StaleFacts("candidate branch ref does not match candidate commit")
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("candidate worktree is dirty")
    return candidate


def record_candidate(repo_raw: str, worktree_ref: str, candidate_raw: str) -> dict[str, Any]:
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
        if entry["lifecycle"] not in {"PROVISIONED", "CANDIDATE_READY", "PREPARED_FOR_INTEGRATION"}:
            raise UnsafeState("worktree lifecycle cannot record a candidate")
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
        candidate = _record_candidate_facts(repo, entry, candidate_raw)
        updated_entry = dict(entry)
        updated_entry["candidate_sha"] = candidate
        updated_entry["lifecycle"] = "CANDIDATE_READY"
        updated_entry["unknown_outcome"] = None
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
    _, _, status = _ensure_controlled_checkout(repo, entry, candidate=candidate)
    if status["tracked_dirty"] or status["nonignored_untracked"]:
        raise UnsafeState("candidate worktree is dirty")
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


def prepare_integration(
    repo_raw: str,
    worktree_ref: str,
    target: str,
    allowed_paths: Sequence[str],
    verification_refs: Sequence[str],
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


def apply(receipt_raw: str, actor: str) -> dict[str, Any]:
    if actor != "root":
        raise OwnershipRefusal("only Root may apply an integration receipt")
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
    preliminary_sha256 = _digest(preliminary)
    worktree_ref = str(preliminary.get("worktree_ref", ""))
    repo, common = _repo_context(str(preliminary.get("repo", "")))
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        actual_receipt_path, receipt = _load_current_receipt(repo, state, entry)
        if not _same_path(actual_receipt_path, receipt_input):
            raise OwnershipRefusal("receipt path is not the registry-authorized receipt")
        if _digest(receipt) != preliminary_sha256:
            raise StaleFacts("integration receipt changed before the canonical container lock was acquired")
        if entry["lifecycle"] != "PREPARED_FOR_INTEGRATION":
            raise StaleFacts("receipt is not prepared for integration")
        _validated_apply_candidate(repo, common, container, state, entry, receipt)
        state, entry, receipt = _refresh_locked_documents(
            repo,
            common,
            container,
            identities,
            state_path,
            worktree_ref,
            state,
            entry,
            actual_receipt_path,
            receipt,
        )
        candidate, _ = _validated_apply_candidate(
            repo,
            common,
            container,
            state,
            entry,
            receipt,
        )

        merge = _run_git(repo, "merge", "--ff-only", candidate, check=False)
        post = _branch_sha(repo, TARGET_BRANCH)
        if merge.returncode:
            if post == candidate:
                message = "git merge returned failure after target reached candidate"
                _journal_unknown_after_effect(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    worktree_ref,
                    state,
                    entry,
                    actual_receipt_path,
                    receipt,
                    operation="APPLY",
                    error=message,
                )
                raise UnknownApply(message)
            raise UnsafeState(
                merge.stderr.strip() or merge.stdout.strip() or "candidate could not be applied"
            )
        if post != candidate or _current_branch(repo) != TARGET_BRANCH:
            message = "apply outcome could not be proven"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                actual_receipt_path,
                receipt,
                operation="APPLY",
                error=message,
            )
            raise UnknownApply(message)

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
                actual_receipt_path,
                receipt,
            )
            if _branch_sha(repo, TARGET_BRANCH) != candidate or _current_branch(repo) != TARGET_BRANCH:
                raise StaleFacts("integration target advanced after the apply effect")
        except WorktreeError as exc:
            message = f"target reached candidate but locked facts advanced before registry CAS: {exc}"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                actual_receipt_path,
                receipt,
                operation="APPLY",
                error=message,
            )
            raise UnknownApply(message) from exc

        updated_entry = dict(entry)
        updated_entry["integrated_sha"] = candidate
        updated_entry["lifecycle"] = "INTEGRATED"
        updated_entry["unknown_outcome"] = None
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
                message = f"target reached candidate but registry CAS is unknown: {exc}"
                _journal_unknown_after_effect(
                    repo,
                    common,
                    container,
                    identities,
                    state_path,
                    worktree_ref,
                    state,
                    entry,
                    actual_receipt_path,
                    receipt,
                    operation="APPLY",
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
                actual_receipt_path,
                receipt,
            )
            if _branch_sha(repo, TARGET_BRANCH) != candidate or _current_branch(repo) != TARGET_BRANCH:
                raise StaleFacts("integration target changed before applied receipt persistence")
        except WorktreeError as exc:
            message = f"apply registry landed but receipt persistence facts are unknown: {exc}"
            _journal_unknown_after_effect(
                repo,
                common,
                container,
                identities,
                state_path,
                worktree_ref,
                state,
                entry,
                actual_receipt_path,
                receipt,
                operation="APPLY",
                error=message,
            )
            raise UnknownApply(message) from exc

        receipt["apply_outcome"] = "APPLIED"
        receipt["applied_sha"] = candidate
        receipt["applied_at"] = _now()
        receipt["registry_revision"] = updated["revision"]
        receipt["lifecycle"] = "INTEGRATED"
        receipt["last_failure"] = None
        receipt["unknown_outcome"] = None
        _atomic_write(actual_receipt_path, receipt)
        return {
            "ok": True,
            "operation": "apply",
            "integrated_sha": candidate,
            "worktree": updated_entry,
            "registry_revision": updated["revision"],
        }


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
    _ensure_controlled_checkout(repo, entry, candidate=None)
    updated_entry = dict(entry)
    updated_entry["lifecycle"] = "RETAINED_FOR_RECOVERY"
    updated_entry["unknown_outcome"] = None
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
    _ensure_controlled_checkout(repo, updated_entry, candidate=None)
    receipt["lifecycle"] = "RETAINED_FOR_RECOVERY"
    receipt["retention_reason"] = reason
    receipt["retained_at"] = _now()
    receipt["registry_revision"] = updated["revision"]
    receipt["last_failure"] = None
    receipt["unknown_outcome"] = None
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
    target, _, status = _ensure_controlled_checkout(repo, entry, candidate=None)
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
        if entry["lifecycle"] != "INTEGRATED" or str(entry.get("integrated_sha") or "").lower() != candidate:
            raise UnsafeState("release requires an integrated candidate or explicit retain")
        target_sha = _branch_sha(repo, TARGET_BRANCH)
        if (
            target_sha is None
            or _run_git(
                repo,
                "merge-base",
                "--is-ancestor",
                candidate,
                TARGET_BRANCH,
                check=False,
            ).returncode
            != 0
        ):
            raise StaleFacts("integrated candidate is not reachable from omp/workflow")
        if branch_sha != candidate:
            raise StaleFacts("temporary candidate branch changed before release")
    elif (
        entry["lifecycle"] not in {"PROVISIONED", "CANDIDATE_READY", "PREPARED_FOR_INTEGRATION"}
        or branch_sha != str(entry["base_sha"]).lower()
    ):
        raise UnsafeState("worktree without a candidate is not safely disposable")
    assert branch_sha is not None
    return target, ignored, branch_sha


def retain(repo_raw: str, worktree_ref: str, actor: str, reason: str) -> dict[str, Any]:
    if actor != "root":
        raise OwnershipRefusal("only Root may retain a worktree")
    if not isinstance(reason, str) or not reason.strip():
        raise InvalidInput("retain requires a non-empty reason")
    repo, common = _repo_context(repo_raw)
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
        return _retain_locked(
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
            reason.strip(),
        )


def release(repo_raw: str, worktree_ref: str, actor: str, ignored_artifacts: str) -> dict[str, Any]:
    if actor != "root":
        raise OwnershipRefusal("only Root may release a worktree")
    if ignored_artifacts not in {"refuse", "discard", "retain"}:
        raise InvalidInput("ignored-artifacts must be refuse, discard, or retain")
    repo, common = _repo_context(repo_raw)
    with _locked_entry(repo, common, worktree_ref) as (
        state_path,
        container,
        state,
        entry,
        identities,
    ):
        receipt_path, receipt = _load_current_receipt(repo, state, entry)
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
        target, ignored, branch_sha = _release_worktree_facts(
            repo,
            entry,
            ignored_artifacts,
            require_disposable=ignored_artifacts != "retain",
        )
        if ignored_artifacts == "retain":
            return _retain_locked(
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
            )

        intent_receipt = dict(receipt)
        intent_receipt["release_intent"] = "DISCARD_IGNORED" if ignored else "EMPTY"
        intent_receipt["release_outcome"] = "PENDING"
        intent_receipt["discarded_paths"] = ignored
        intent_receipt["release_requested_at"] = _now()
        intent_receipt["last_failure"] = None
        intent_receipt["unknown_outcome"] = None
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
        _atomic_write(receipt_path, receipt)
        return {
            "ok": True,
            "operation": "release",
            "status": "RELEASED",
            "discarded_paths": ignored,
            "worktree": updated_entry,
            "registry_revision": updated["revision"],
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
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--worktree-ref", required=True)
    inspect_parser.add_argument("--repo", default=".")
    candidate_parser = sub.add_parser("record-candidate")
    candidate_parser.add_argument("--worktree-ref", required=True)
    candidate_parser.add_argument("--candidate", required=True)
    candidate_parser.add_argument("--repo", default=".")
    prepare_parser = sub.add_parser("prepare-integration")
    prepare_parser.add_argument("--worktree-ref", required=True)
    prepare_parser.add_argument("--target", required=True)
    prepare_parser.add_argument("--allowed-path", action="append", required=True)
    prepare_parser.add_argument("--verification-ref", action="append", default=[])
    prepare_parser.add_argument("--repo", default=".")
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--receipt", required=True)
    apply_parser.add_argument("--actor", required=True)
    release_parser = sub.add_parser("release")
    release_parser.add_argument("--worktree-ref", required=True)
    release_parser.add_argument("--actor", required=True)
    release_parser.add_argument("--ignored-artifacts", choices=["refuse", "discard", "retain"], default="refuse")
    release_parser.add_argument("--repo", default=".")
    retain_parser = sub.add_parser("retain")
    retain_parser.add_argument("--worktree-ref", required=True)
    retain_parser.add_argument("--actor", required=True)
    retain_parser.add_argument("--reason", required=True)
    retain_parser.add_argument("--repo", default=".")
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
            result = provision(args.repo, args.container, args.direction, args.kind, args.assignment, args.base)
        elif args.operation == "inspect":
            result = inspect(args.repo, args.worktree_ref)
        elif args.operation == "record-candidate":
            result = record_candidate(args.repo, args.worktree_ref, args.candidate)
        elif args.operation == "prepare-integration":
            result = prepare_integration(args.repo, args.worktree_ref, args.target, args.allowed_path, args.verification_ref)
        elif args.operation == "apply":
            result = apply(args.receipt, args.actor)
        elif args.operation == "release":
            result = release(args.repo, args.worktree_ref, args.actor, args.ignored_artifacts)
        else:
            result = retain(args.repo, args.worktree_ref, args.actor, args.reason)
    except WorktreeError as exc:
        return _emit_error(getattr(locals().get("args", None), "operation", "unknown"), exc)
    except (OSError, subprocess.SubprocessError) as exc:
        return _emit_error(getattr(locals().get("args", None), "operation", "unknown"), WorktreeError(str(exc)))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
