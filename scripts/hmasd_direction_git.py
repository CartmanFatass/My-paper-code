#!/usr/bin/env python3
"""Commit, push, or observe exact paths from one Session Envelope v3 assignment."""

from __future__ import annotations

import argparse
from contextvars import ContextVar, Token
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import hmasd_path_policy, hmasd_platform
except ImportError:
    import hmasd_path_policy
    import hmasd_platform


_FULL_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_MANAGER = re.compile(r"(EM|CM)/([a-z0-9][a-z0-9_-]{1,63})/g[1-9][0-9]*\Z")
_GIT_INPUT_FIELDS = {
    "schema_version", "assignment_message_id", "assignment_locator", "direction_id",
    "recipient_identity", "workspace_mode", "owned_paths", "commit_subject",
}
_TRANSACTION_TIMEOUT_SECONDS = 5
_POST_SEND_OBSERVE_RESERVE_SECONDS = 1
_NEW_PATH_CLEANUP_RESERVE_SECONDS = 1
_TRANSACTION_DEADLINE: ContextVar[float | None] = ContextVar(
    "hmasd_direction_git_transaction_deadline", default=None
)


class DirectionGitError(RuntimeError):
    code = 2
    status = "REFUSED"

    def __init__(self, message: str, *, facts: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.facts = dict(facts or {})


class SharedCoreRequired(DirectionGitError):
    code = 5
    status = "SHARED_CORE_ACTION_REQUIRED"


class GitConflict(DirectionGitError):
    code = 6
    status = "CONFLICT"


class PushUnknown(DirectionGitError):
    code = 7
    status = "PUSH_OUTCOME_UNKNOWN"

    def __init__(self, message: str, *, facts: Mapping[str, Any] | None = None):
        scoped = dict(facts or {})
        scoped["failure_scope"] = "effect"
        scoped["failure_ref"] = "git_push"
        super().__init__(message, facts=scoped)


def _remaining_timeout(requested: float | None = None) -> float | None:
    deadline = _TRANSACTION_DEADLINE.get()
    if deadline is None:
        return requested
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DirectionGitError("direction Git transaction deadline expired")
    return remaining if requested is None else min(float(requested), remaining)


def _run_git(
    repo: Path, *args: str, check: bool = True, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    command = ["git", *args]
    with (
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stdout_file,
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr_file,
    ):
        try:
            completed = subprocess.run(
                command,
                cwd=repo,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_remaining_timeout(timeout),
            )
        except subprocess.TimeoutExpired as exc:
            raise DirectionGitError(f"git {args[0]} timed out") from exc
        stdout_file.seek(0)
        stderr_file.seek(0)
        result = subprocess.CompletedProcess(
            command, completed.returncode, stdout_file.read(), stderr_file.read()
        )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise DirectionGitError(f"git {' '.join(args)} failed: {detail}")
    return result


def _git_value(repo: Path, *args: str) -> str:
    return _run_git(repo, *args).stdout.strip()


def _repository(raw: str) -> tuple[Path, Path]:
    repo = Path(raw).absolute()
    if not repo.is_dir():
        raise DirectionGitError("repo must be an existing directory")
    top = Path(_git_value(repo, "rev-parse", "--show-toplevel")).absolute()
    if os.path.normcase(str(top)) != os.path.normcase(str(repo)):
        raise DirectionGitError("repo must be the exact Git top-level path")
    if _git_value(repo, "rev-parse", "--is-bare-repository") != "false":
        raise DirectionGitError("repo must be a non-bare checkout")
    common = Path(_git_value(repo, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = repo / common
    common = common.absolute()
    if not common.is_dir():
        raise DirectionGitError("Git common directory is missing")
    return repo, common


def _load_git_input(repo: Path, raw_path: str) -> tuple[str, dict[str, Any]]:
    try:
        value = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DirectionGitError(f"frozen Git input is not readable JSON: {exc}") from exc
    if not isinstance(value, Mapping) or set(value) != _GIT_INPUT_FIELDS:
        raise DirectionGitError("frozen Git input has an invalid exact shape")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise DirectionGitError("frozen Git input schema_version must be 1")
    try:
        message_id = str(uuid.UUID(str(value["assignment_message_id"])))
    except (TypeError, ValueError) as exc:
        raise DirectionGitError("frozen Git input assignment_message_id is invalid") from exc
    locator = value["assignment_locator"]
    if not isinstance(locator, str) or not locator or "\n" in locator or "\r" in locator:
        raise DirectionGitError("frozen Git input assignment_locator must be one non-empty line")
    direction = value["direction_id"]
    if not isinstance(direction, str) or _DIRECTION.fullmatch(direction) is None:
        raise DirectionGitError("frozen Git input direction_id is invalid")
    recipient = value["recipient_identity"]
    match = _MANAGER.fullmatch(recipient) if isinstance(recipient, str) else None
    if match is None or match.group(2) != direction:
        raise DirectionGitError("frozen Git input recipient_identity is invalid")
    workspace_mode = value["workspace_mode"]
    if workspace_mode != "shared-main":
        raise DirectionGitError(
            "direction Git shared-checkout action requires workspace_mode shared-main",
            facts={"workspace_mode": workspace_mode},
        )
    if not isinstance(value["owned_paths"], list) or not value["owned_paths"]:
        raise DirectionGitError("frozen Git input owned_paths must be a non-empty list")
    owned_paths: list[str] = []
    for index, path in enumerate(value["owned_paths"]):
        if not isinstance(path, str):
            raise DirectionGitError(f"owned_paths[{index}] must be a path")
        is_prefix = path.endswith("/")
        raw = path[:-1] if is_prefix else path
        try:
            normalized = hmasd_path_policy.normalize_repo_path(
                raw, label=f"owned_paths[{index}]",
            )
        except hmasd_path_policy.PathPolicyError as exc:
            raise DirectionGitError(str(exc)) from exc
        if normalized != raw:
            raise DirectionGitError(f"owned_paths[{index}] is not canonical")
        owned_paths.append(normalized + ("/" if is_prefix else ""))
    subject = value["commit_subject"]
    if not isinstance(subject, str) or not subject.strip() or "\n" in subject or "\r" in subject:
        raise DirectionGitError("frozen Git input commit_subject must be one non-empty line")
    if _git_value(repo, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
        raise DirectionGitError("shared-main direction Git requires checked-out main")
    normalized_input = {
        "schema_version": 1, "assignment_message_id": message_id,
        "assignment_locator": locator, "direction_id": direction,
        "recipient_identity": recipient, "workspace_mode": workspace_mode,
        "owned_paths": owned_paths, "commit_subject": subject.strip(),
    }
    assignment = {
        "message_id": message_id,
        "direction_id": direction,
        "recipient": {"identity": recipient},
        "body": {
            "workspace_mode": workspace_mode,
            "owned_paths": owned_paths,
            "objective": subject.strip(),
        },
        "_git_input_sha256": hashlib.sha256(
            json.dumps(
                normalized_input, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
    }
    return locator, assignment


def _normalize_paths(
    repo: Path, assignment: Mapping[str, Any], paths: Sequence[str]
) -> list[str]:
    if not paths:
        raise DirectionGitError("at least one explicit --path is required")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(paths):
        try:
            path = hmasd_path_policy.normalize_repo_path(raw, label=f"path[{index}]")
            hmasd_path_policy.resolve_repo_path(repo, path, label=f"path[{index}]")
        except hmasd_path_policy.PathPolicyError as exc:
            raise DirectionGitError(str(exc)) from exc
        if path != raw:
            raise DirectionGitError(f"path[{index}] is not canonical")
        folded = path.casefold()
        if folded in seen:
            raise DirectionGitError("requested paths contain a case-insensitive duplicate")
        seen.add(folded)
        if not hmasd_path_policy.path_is_owned(path, assignment["body"]["owned_paths"]):
            raise DirectionGitError(f"requested path is not assignment-owned: {path}")
        normalized.append(path)
    return sorted(normalized, key=str.casefold)


def _require_direction_owned(repo: Path, paths: Sequence[str]) -> None:
    try:
        facts = hmasd_path_policy.observe_path_classifications(repo, paths)
    except hmasd_path_policy.PathPolicyError as exc:
        raise DirectionGitError(f"cannot classify requested paths: {exc}") from exc
    shared = sorted(
        item["path"]
        for item in facts["classifications"]
        if item["classification"] == "shared-core"
    )
    if shared:
        raise SharedCoreRequired(
            "shared-core action requires the existing exact Root/user confirmation fence",
            facts={"changed_paths": shared},
        )


def _working_changes(repo: Path, paths: Sequence[str]) -> tuple[list[str], list[str]]:
    tracked = _run_git(
        repo, "diff", "--name-only", "--no-renames", "-z", "HEAD", "--", *paths
    ).stdout.split("\0")
    untracked = _run_git(
        repo, "ls-files", "--others", "--exclude-standard", "-z", "--", *paths
    ).stdout.split("\0")
    new_paths = sorted({path for path in untracked if path}, key=str.casefold)
    changed = sorted({path for path in [*tracked, *new_paths] if path}, key=str.casefold)
    return changed, new_paths


def _commit_message(repo: Path, commit: str) -> str:
    return _run_git(repo, "show", "-s", "--format=%B", commit).stdout


def _assignment_candidates(repo: Path, message_id: str) -> list[str]:
    trailer = f"HMASD-Assignment-ID: {message_id}"
    result = _run_git(
        repo, "log", "--format=%H", "--fixed-strings", f"--grep={trailer}", "HEAD"
    )
    return [
        commit.lower()
        for commit in result.stdout.splitlines()
        if trailer in _commit_message(repo, commit).splitlines()
    ]


def _subject(assignment: Mapping[str, Any]) -> str:
    objective = " ".join(str(assignment["body"]["objective"]).split())
    prefix = f"hmasd({str(assignment['message_id'])[:12]}): "
    return (prefix + objective)[:72].rstrip()


def _head(repo: Path) -> str:
    value = _git_value(repo, "rev-parse", "HEAD").lower()
    if _FULL_SHA.fullmatch(value) is None:
        raise DirectionGitError("HEAD is not a full commit SHA")
    return value


def _candidate_changed_paths(repo: Path, base: str, candidate: str) -> list[str]:
    changed = sorted(
        {
            path
            for path in _run_git(
                repo, "diff", "--name-only", "--no-renames", "-z", base, candidate
            ).stdout.split("\0")
            if path
        },
        key=str.casefold,
    )
    for path in changed:
        hmasd_path_policy.normalize_repo_path(path, label="candidate changed path")
        tree = _run_git(repo, "ls-tree", "-r", "-z", candidate, "--", path)
        for entry in tree.stdout.split("\0"):
            if entry and entry.split("\t", 1)[0].split()[0] == "120000":
                raise GitConflict(f"assignment candidate contains a tracked symlink: {path}")
    return changed


def _verify_candidate(
    repo: Path,
    assignment: Mapping[str, Any],
    candidate: str,
    requested: Sequence[str] | None,
) -> tuple[str, list[str]]:
    lines = _commit_message(repo, candidate).splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    trailer_start = len(lines)
    while trailer_start and lines[trailer_start - 1].strip():
        trailer_start -= 1
    trailers = lines[trailer_start:]
    assignment_trailer = f"HMASD-Assignment-ID: {assignment['message_id']}"
    recipient_trailer = f"HMASD-Assignment-Recipient: {assignment['recipient']['identity']}"
    input_trailer = f"HMASD-Git-Input-SHA256: {assignment['_git_input_sha256']}"
    if trailers.count(assignment_trailer) != 1:
        raise GitConflict("candidate has a non-canonical assignment-ID trailer")
    if trailers.count(recipient_trailer) != 1:
        raise GitConflict("candidate recipient does not match the assignment")
    if trailers.count(input_trailer) != 1:
        raise GitConflict("candidate does not match the frozen Git input")
    bases = [
        line.removeprefix("HMASD-Base-SHA: ")
        for line in trailers
        if line.startswith("HMASD-Base-SHA: ")
    ]
    if len(bases) != 1 or _FULL_SHA.fullmatch(bases[0]) is None:
        raise GitConflict("candidate has a non-canonical base-SHA trailer")
    base = bases[0].lower()
    parents = _git_value(repo, "rev-list", "--parents", "-n", "1", candidate).split()
    if len(parents) != 2 or parents[1].lower() != base:
        raise GitConflict("candidate base SHA does not match its sole parent")
    changed = _candidate_changed_paths(repo, base, candidate)
    try:
        normalized = _normalize_paths(repo, assignment, changed)
        _require_direction_owned(repo, changed)
    except DirectionGitError as exc:
        raise GitConflict(
            f"candidate changed paths violate assignment ownership: {exc}",
            facts={"base_sha": base, "candidate_sha": candidate, "changed_paths": changed},
        ) from exc
    if normalized != changed:
        raise GitConflict("candidate changed paths are not canonical")
    if requested is not None and list(requested) != changed:
        raise GitConflict(
            "candidate changed paths do not match the exact requested paths",
            facts={"base_sha": base, "candidate_sha": candidate, "changed_paths": changed},
        )
    return base, changed


def _fetch_remote(repo: Path) -> str:
    _run_git(
        repo, "fetch", "--no-tags", "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    )
    value = _git_value(repo, "rev-parse", "refs/remotes/origin/main").lower()
    if _FULL_SHA.fullmatch(value) is None:
        raise DirectionGitError("origin/main is not a full commit SHA")
    return value


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = _run_git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode in {0, 1}:
        return result.returncode == 0
    detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
    raise DirectionGitError(f"cannot compare Git ancestry: {detail}")


def _relation(repo: Path, candidate: str, remote: str) -> str:
    if candidate == remote:
        return "EQUAL"
    if _is_ancestor(repo, candidate, remote):
        return "DESCENDANT"
    if _is_ancestor(repo, remote, candidate):
        return "ANCESTOR"
    return "DIVERGED"


def _result(
    *, status: str, reason: str, assignment_locator: str, message_id: str,
    workspace_mode: str | None = None, base_sha: str | None = None,
    candidate_sha: str | None = None, integrated_sha: str | None = None,
    changed_paths: Sequence[str] = (), remote_sha: str | None = None,
    relation: str | None = None, push_attempted: bool = False,
    failure_scope: str | None = None, failure_ref: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status, "reason": reason, "assignment_locator": assignment_locator,
        "message_id": message_id, "workspace_mode": workspace_mode,
        "base_sha": base_sha, "candidate_sha": candidate_sha,
        "integrated_sha": integrated_sha, "changed_paths": list(changed_paths),
        "remote_sha": remote_sha, "relation": relation,
        "push_attempted": push_attempted,
    }
    if status == "SUCCEEDED" and not changed_paths:
        result["git_closure"] = {"kind": "NO_CHANGES"}
    elif status == "SUCCEEDED" and candidate_sha is not None:
        result["git_closure"] = {
            "kind": "PUBLISHED", "branch": "main", "commit_sha": candidate_sha,
            "remote": "origin", "ref": "refs/heads/main", "push_outcome": "SUCCEEDED",
        }
    else:
        result["git_closure"] = None
    if failure_scope is not None:
        result["failure_scope"] = failure_scope
    if failure_ref is not None:
        result["failure_ref"] = failure_ref
    return result


def _verify_lock_identity(path: Path, descriptor: int) -> None:
    try:
        path_info = os.lstat(path)
    except OSError as exc:
        raise DirectionGitError(f"Git transaction lock cannot be observed: {exc}") from exc
    descriptor_info = os.fstat(descriptor)
    if hmasd_platform.is_reparse_or_symlink(path, path_info):
        raise DirectionGitError("Git transaction lock is a symlink or reparse point")
    if not stat.S_ISREG(descriptor_info.st_mode) or not os.path.samestat(
        descriptor_info, path_info
    ):
        raise DirectionGitError("Git transaction lock identity changed")


class _GitLock:
    def __init__(self, common: Path):
        self.path = common / "hmasd-direction-git.lock"
        self.stream: Any = None
        self.locked = False
        self.acquire_deadline = time.monotonic() + _TRANSACTION_TIMEOUT_SECONDS
        self.deadline: float | None = None
        self.deadline_token: Token[float | None] | None = None

    def _acquire(self) -> None:
        descriptor = self.stream.fileno()
        while True:
            os.lseek(descriptor, 0, os.SEEK_SET)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.locked = True
                return
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                remaining = self.acquire_deadline - time.monotonic()
                if remaining <= 0:
                    raise DirectionGitError(
                        "direction Git transaction timed out acquiring the repository lock"
                    ) from exc
                time.sleep(min(0.05, remaining))

    def _release(self) -> None:
        if not self.locked:
            return
        descriptor = self.stream.fileno()
        os.lseek(descriptor, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        self.locked = False

    def __enter__(self) -> None:
        descriptor = os.open(
            self.path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600
        )
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
            os.fsync(descriptor)
        self.stream = os.fdopen(descriptor, "r+b", buffering=0)
        try:
            _verify_lock_identity(self.path, self.stream.fileno())
            self._acquire()
            _verify_lock_identity(self.path, self.stream.fileno())
        except Exception:
            self._release()
            self.stream.close()
            raise
        self.deadline = time.monotonic() + _TRANSACTION_TIMEOUT_SECONDS
        self.deadline_token = _TRANSACTION_DEADLINE.set(self.deadline)

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        try:
            self._release()
        finally:
            if self.deadline_token is not None:
                _TRANSACTION_DEADLINE.reset(self.deadline_token)
            self.stream.close()


def _identity(assignment: Mapping[str, Any]) -> tuple[str, str]:
    return str(assignment["message_id"]), str(assignment["body"]["workspace_mode"])


def commit_push(repo_raw: str, git_input: str, paths: Sequence[str]) -> dict[str, Any]:
    repo, common = _repository(repo_raw)
    assignment_locator, assignment = _load_git_input(repo, git_input)
    message_id, workspace_mode = _identity(assignment)
    requested = _normalize_paths(repo, assignment, paths)
    _require_direction_owned(repo, requested)
    with _GitLock(common):
        if _git_value(repo, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
            raise DirectionGitError("checked-out branch changed before Git transaction")
        locked_locator, locked_assignment = _load_git_input(repo, git_input)
        if locked_locator != assignment_locator or locked_assignment != assignment:
            raise GitConflict("assignment changed before Git transaction")
        candidates = _assignment_candidates(repo, message_id)
        if len(candidates) > 1:
            raise GitConflict("multiple reachable commits contain the assignment-ID trailer")
        if candidates:
            candidate = candidates[0]
            base, changed = _verify_candidate(repo, assignment, candidate, requested)
            try:
                remote = _fetch_remote(repo)
            except DirectionGitError:
                return _result(
                    status="OBSERVE_REQUIRED", reason="candidate exists but origin/main observation failed; run observe-push",
                    assignment_locator=assignment_locator, message_id=message_id,
                    workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
                    changed_paths=changed, relation="OBSERVATION_FAILED",
                )
            relation = _relation(repo, candidate, remote)
            if relation in {"EQUAL", "DESCENDANT"}:
                return _result(
                    status="SUCCEEDED", reason="candidate is contained by origin/main",
                    assignment_locator=assignment_locator, message_id=message_id,
                    workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
                    integrated_sha=remote, changed_paths=changed, remote_sha=remote,
                    relation=relation,
                )
            if relation == "DIVERGED":
                raise GitConflict(
                    "origin/main diverged from the existing candidate",
                    facts={"base_sha": base, "candidate_sha": candidate,
                           "changed_paths": changed, "remote_sha": remote,
                           "relation": relation},
                )
            return _result(
                status="OBSERVE_REQUIRED", reason="candidate already exists; run observe-push",
                assignment_locator=assignment_locator, message_id=message_id,
                workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
                changed_paths=changed, remote_sha=remote, relation=relation,
            )
        local_head = _head(repo)
        remote_before = _fetch_remote(repo)
        head_relation = _relation(repo, local_head, remote_before)
        if head_relation == "DIVERGED":
            raise GitConflict(
                "local main diverged from origin/main before commit",
                facts={"base_sha": local_head, "changed_paths": requested,
                       "remote_sha": remote_before, "relation": head_relation},
            )
        if head_relation != "EQUAL":
            return _result(
                status="OBSERVE_REQUIRED", reason="local main does not equal observed origin/main",
                assignment_locator=assignment_locator, message_id=message_id,
                workspace_mode=workspace_mode, base_sha=local_head,
                changed_paths=requested, remote_sha=remote_before, relation=head_relation,
            )
        changed, new_paths = _working_changes(repo, requested)
        if changed != requested:
            raise DirectionGitError(
                "requested paths must be the exact changed paths",
                facts={"changed_paths": changed},
            )
        base = _head(repo)
        message = (
            f"{_subject(assignment)}\n\n"
            f"HMASD-Assignment-ID: {message_id}\n"
            f"HMASD-Base-SHA: {base}\n"
            f"HMASD-Assignment-Recipient: {assignment['recipient']['identity']}\n"
            f"HMASD-Git-Input-SHA256: {assignment['_git_input_sha256']}\n"
        )
        try:
            if new_paths:
                remaining = _remaining_timeout()
                assert remaining is not None
                if remaining <= _NEW_PATH_CLEANUP_RESERVE_SECONDS:
                    raise DirectionGitError("transaction deadline cannot preserve new-path cleanup budget")
                _run_git(
                    repo, "add", "--intent-to-add", "--", *new_paths,
                    timeout=remaining - _NEW_PATH_CLEANUP_RESERVE_SECONDS,
                )
            commit_timeout = None
            if new_paths:
                remaining = _remaining_timeout()
                assert remaining is not None
                if remaining <= _NEW_PATH_CLEANUP_RESERVE_SECONDS:
                    raise DirectionGitError(
                        "transaction deadline cannot preserve new-path cleanup budget"
                    )
                commit_timeout = remaining - _NEW_PATH_CLEANUP_RESERVE_SECONDS
            _run_git(
                repo, "-c", "core.hooksPath=", "-c", "commit.gpgSign=false",
                "commit", "--only", "-m", message, "--", *requested,
                timeout=commit_timeout,
            )
        except DirectionGitError:
            if new_paths:
                _run_git(repo, "reset", "--quiet", "HEAD", "--", *new_paths)
            raise
        candidate = _head(repo)
        _verify_candidate(repo, assignment, candidate, requested)
        remote = _fetch_remote(repo)
        relation = _relation(repo, candidate, remote)
        if relation == "DIVERGED":
            raise GitConflict(
                "origin/main diverged before push",
                facts={"base_sha": base, "candidate_sha": candidate,
                       "changed_paths": requested, "remote_sha": remote,
                       "relation": relation},
            )
        if relation in {"EQUAL", "DESCENDANT"}:
            return _result(
                status="SUCCEEDED", reason="candidate is already contained by origin/main",
                assignment_locator=assignment_locator, message_id=message_id,
                workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
                integrated_sha=remote, changed_paths=requested, remote_sha=remote,
                relation=relation,
            )
        remaining = _remaining_timeout()
        assert remaining is not None
        if remaining <= _POST_SEND_OBSERVE_RESERVE_SECONDS:
            return _result(
                status="OBSERVE_REQUIRED", reason="transaction deadline expired before push; run observe-push",
                assignment_locator=assignment_locator, message_id=message_id,
                workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
                changed_paths=requested, remote_sha=remote, relation=relation,
            )
        try:
            _run_git(
                repo, "push", "origin", f"{candidate}:refs/heads/main",
                timeout=remaining - _POST_SEND_OBSERVE_RESERVE_SECONDS,
            )
        except DirectionGitError:
            # The send crossed the external-effect boundary.  Its exit status
            # cannot authorize a replay; only a fresh remote observation may
            # resolve whether the exact candidate landed.
            pass
        try:
            remote = _fetch_remote(repo)
        except DirectionGitError as exc:
            raise PushUnknown(
                "push outcome is unknown because post-send observation failed; "
                "use observe-push and never resend",
                facts={"base_sha": base, "candidate_sha": candidate,
                       "changed_paths": requested, "remote_sha": remote,
                       "relation": "OBSERVATION_FAILED", "push_attempted": True},
            ) from exc
        relation = _relation(repo, candidate, remote)
        if relation not in {"EQUAL", "DESCENDANT"}:
            raise PushUnknown(
                "push outcome is unknown; use observe-push and never resend",
                facts={"base_sha": base, "candidate_sha": candidate,
                       "changed_paths": requested, "remote_sha": remote,
                       "relation": relation, "push_attempted": True},
            )
        return _result(
            status="SUCCEEDED", reason="candidate is contained by origin/main",
            assignment_locator=assignment_locator, message_id=message_id,
            workspace_mode=workspace_mode, base_sha=base, candidate_sha=candidate,
            integrated_sha=remote, changed_paths=requested, remote_sha=remote,
            relation=relation, push_attempted=True,
        )


def observe_push(repo_raw: str, git_input: str) -> dict[str, Any]:
    repo, common = _repository(repo_raw)
    assignment_locator, assignment = _load_git_input(repo, git_input)
    message_id, workspace_mode = _identity(assignment)
    with _GitLock(common):
        candidates = _assignment_candidates(repo, message_id)
        if not candidates:
            raise GitConflict("no reachable commit contains the assignment-ID trailer")
        if len(candidates) > 1:
            raise GitConflict("multiple reachable commits contain the assignment-ID trailer")
        candidate = candidates[0]
        base, changed = _verify_candidate(repo, assignment, candidate, None)
        try:
            remote = _fetch_remote(repo)
        except DirectionGitError as exc:
            raise PushUnknown(
                "origin/main observation failed; observe-push cannot resolve the candidate",
                facts={"base_sha": base, "candidate_sha": candidate,
                       "changed_paths": changed, "relation": "OBSERVATION_FAILED",
                       "push_attempted": False},
            ) from exc
        relation = _relation(repo, candidate, remote)
        facts = {
            "base_sha": base, "candidate_sha": candidate, "changed_paths": changed,
            "remote_sha": remote, "relation": relation, "push_attempted": False,
        }
        if relation in {"EQUAL", "DESCENDANT"}:
            return _result(
                status="SUCCEEDED", reason="candidate is contained by origin/main",
                assignment_locator=assignment_locator, message_id=message_id,
                workspace_mode=workspace_mode, integrated_sha=remote, **facts,
            )
        if relation == "DIVERGED":
            raise GitConflict("origin/main diverged from the candidate", facts=facts)
        raise PushUnknown(
            "candidate is not yet contained by origin/main; observation cannot resend",
            facts=facts,
        )


def no_changes(repo_raw: str, git_input: str) -> dict[str, Any]:
    repo, common = _repository(repo_raw)
    assignment_locator, assignment = _load_git_input(repo, git_input)
    message_id, workspace_mode = _identity(assignment)
    with _GitLock(common):
        locked_locator, locked_assignment = _load_git_input(repo, git_input)
        if locked_locator != assignment_locator or locked_assignment != assignment:
            raise GitConflict("frozen Git input changed before no-changes observation")
        owned = assignment["body"]["owned_paths"]
        changed, _ = _working_changes(repo, owned)
        if changed:
            raise DirectionGitError(
                "NO_CHANGES closure requires all frozen owned paths to be unchanged",
                facts={"changed_paths": changed},
            )
        return _result(
            status="SUCCEEDED", reason="frozen owned paths have no Git-visible changes",
            assignment_locator=assignment_locator, message_id=message_id,
            workspace_mode=workspace_mode,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    commit = subparsers.add_parser("commit-push")
    commit.add_argument("--repo", required=True)
    commit.add_argument("--git-input", required=True)
    commit.add_argument("--path", action="append", required=True)
    observe = subparsers.add_parser("observe-push")
    observe.add_argument("--repo", required=True)
    observe.add_argument("--git-input", required=True)
    unchanged = subparsers.add_parser("no-changes")
    unchanged.add_argument("--repo", required=True)
    unchanged.add_argument("--git-input", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    git_input = args.git_input
    try:
        if args.operation == "commit-push":
            result = commit_push(args.repo, git_input, args.path)
        elif args.operation == "observe-push":
            result = observe_push(args.repo, git_input)
        else:
            result = no_changes(args.repo, git_input)
    except DirectionGitError as exc:
        facts: dict[str, Any] = {
            "workspace_mode": None, "base_sha": None, "candidate_sha": None,
            "integrated_sha": None, "changed_paths": [], "remote_sha": None,
            "relation": None, "push_attempted": False,
        }
        facts.update(exc.facts)
        message_id = ""
        assignment_locator = git_input
        try:
            repo = Path(args.repo).absolute()
            assignment_locator, assignment = _load_git_input(repo, git_input)
            message_id, workspace_mode = _identity(assignment)
            facts["workspace_mode"] = workspace_mode
        except DirectionGitError:
            pass
        result = _result(
            status=exc.status, reason=str(exc), assignment_locator=assignment_locator,
            message_id=message_id, **facts,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return exc.code
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 3 if result["status"] == "OBSERVE_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
