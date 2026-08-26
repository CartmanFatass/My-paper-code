#!/usr/bin/env python3
"""Commit and observe exact direction-owned Git changes for one Work Packet."""

from __future__ import annotations

import argparse
from contextvars import ContextVar, Token
import errno
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import hmasd_work_packet, hmasd_worktree
except ImportError:
    import hmasd_work_packet
    import hmasd_worktree


_WORK_ID = re.compile(r"[0-9a-f]{64}\Z")
_FULL_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_TRANSACTION_TIMEOUT_SECONDS = 5
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
        scoped["failure_scope"] = "feature"
        scoped["failure_ref"] = "git_push"
        super().__init__(message, facts=scoped)


def _remaining_timeout(requested: float | None = None) -> float | None:
    deadline = _TRANSACTION_DEADLINE.get()
    if deadline is None:
        return requested
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DirectionGitError("direction Git transaction deadline expired")
    if requested is None:
        return remaining
    return min(float(requested), remaining)


def _run_git(
    repo: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    effective_timeout = _remaining_timeout()
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
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise DirectionGitError(f"git {args[0]} timed out") from exc
        stdout_file.seek(0)
        stderr_file.seek(0)
        result = subprocess.CompletedProcess(
            command,
            completed.returncode,
            stdout=stdout_file.read(),
            stderr=stderr_file.read(),
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
    branch = _git_value(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch != "main":
        raise DirectionGitError("direct direction Git requires checked-out main")
    common = Path(_git_value(repo, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = repo / common
    common = common.absolute()
    if not common.is_dir():
        raise DirectionGitError("Git common directory is missing")
    return repo, common


def _load_packet(repo: Path, work_id: str) -> dict[str, Any]:
    if _WORK_ID.fullmatch(work_id) is None:
        raise DirectionGitError("work_id must be a lowercase SHA256")
    try:
        packet = hmasd_work_packet._load_ready_packet(repo, work_id)
    except hmasd_work_packet.WorkPacketError as exc:
        raise DirectionGitError(f"published Work Packet is invalid: {exc}") from exc
    return packet


def _normalize_paths(repo: Path, packet: Mapping[str, Any], paths: Sequence[str]) -> list[str]:
    if not paths:
        raise DirectionGitError("at least one explicit --path is required")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(paths):
        try:
            path = hmasd_work_packet._normalize_path(value, label=f"path[{index}]")
            hmasd_work_packet._repo_path(
                repo,
                path,
                label=f"path[{index}]",
                require_existing=False,
            )
        except hmasd_work_packet.WorkPacketError as exc:
            raise DirectionGitError(str(exc)) from exc
        if path != value:
            raise DirectionGitError(f"path[{index}] is not canonical")
        folded = path.casefold()
        if folded in seen:
            raise DirectionGitError("requested paths contain a case-insensitive duplicate")
        seen.add(folded)
        normalized.append(path)
    normalized.sort(key=str.casefold)
    owned = [str(path).casefold() for path in packet["owned_paths"]]
    for path in normalized:
        folded = path.casefold()
        if not any(folded == root or folded.startswith(root + "/") for root in owned):
            raise DirectionGitError(f"requested path is not packet-owned: {path}")
    return normalized


def _require_direction_owned(repo: Path, paths: Sequence[str]) -> None:
    try:
        classifications = hmasd_worktree.observe_path_classifications(repo, paths)
    except hmasd_worktree.WorktreeError as exc:
        raise DirectionGitError(f"cannot classify requested paths: {exc}") from exc
    shared = sorted(
        item["path"]
        for item in classifications["classifications"]
        if item["classification"] == "shared-core"
    )
    if shared:
        raise SharedCoreRequired(
            "shared-core action requires the existing exact Root/user confirmation path",
            facts={"changed_paths": shared},
        )


def _working_changes(repo: Path, paths: Sequence[str]) -> list[str]:
    tracked = _run_git(
        repo,
        "diff",
        "--name-only",
        "--no-renames",
        "-z",
        "HEAD",
        "--",
        *paths,
    ).stdout.split("\0")
    untracked = _run_git(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        *paths,
    ).stdout.split("\0")
    return sorted({path for path in [*tracked, *untracked] if path}, key=str.casefold)


def _commit_message(repo: Path, commit: str) -> str:
    return _run_git(repo, "show", "-s", "--format=%B", commit).stdout


def _work_id_candidates(repo: Path, work_id: str) -> list[str]:
    result = _run_git(
        repo,
        "log",
        "--format=%H",
        "--fixed-strings",
        f"--grep=HMASD-Work-ID: {work_id}",
        "HEAD",
    )
    exact = []
    trailer = f"HMASD-Work-ID: {work_id}"
    for commit in result.stdout.splitlines():
        if trailer in _commit_message(repo, commit).splitlines():
            exact.append(commit.lower())
    return exact


def _subject(packet: Mapping[str, Any]) -> str:
    objective = " ".join(str(packet["objective"]).split())
    prefix = f"hmasd({str(packet['work_id'])[:12]}): "
    return (prefix + objective)[:72].rstrip()


def _head(repo: Path) -> str:
    value = _git_value(repo, "rev-parse", "HEAD").lower()
    if _FULL_SHA.fullmatch(value) is None:
        raise DirectionGitError("HEAD is not a full commit SHA")
    return value


def _candidate_changed_paths(repo: Path, base: str, candidate: str) -> list[str]:
    result = _run_git(
        repo,
        "diff",
        "--name-only",
        "--no-renames",
        "-z",
        base,
        candidate,
    )
    changed = sorted({path for path in result.stdout.split("\0") if path}, key=str.casefold)
    for path in changed:
        tree = _run_git(repo, "ls-tree", "-r", "-z", candidate, "--", path)
        for entry in tree.stdout.split("\0"):
            if entry and entry.split("\t", 1)[0].split()[0] == "120000":
                raise GitConflict(f"work-ID candidate contains a tracked symlink: {path}")
    return changed


def _verify_candidate(
    repo: Path,
    packet: Mapping[str, Any],
    candidate: str,
    requested: Sequence[str] | None,
) -> tuple[str, list[str]]:
    message = _commit_message(repo, candidate)
    lines = message.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    trailer_start = len(lines)
    while trailer_start and lines[trailer_start - 1].strip():
        trailer_start -= 1
    trailer_lines = lines[trailer_start:]
    work_trailer = f"HMASD-Work-ID: {packet['work_id']}"
    assignment_trailer = f"HMASD-Assignment: {packet['target_identity']}"
    if trailer_lines.count(work_trailer) != 1:
        raise GitConflict("work-ID candidate has a non-canonical work-ID trailer")
    if trailer_lines.count(assignment_trailer) != 1:
        raise GitConflict("work-ID candidate assignment does not match the Work Packet")
    base_values = [
        line.removeprefix("HMASD-Base-SHA: ")
        for line in trailer_lines
        if line.startswith("HMASD-Base-SHA: ")
    ]
    if len(base_values) != 1 or _FULL_SHA.fullmatch(base_values[0]) is None:
        raise GitConflict("work-ID candidate has a non-canonical base-SHA trailer")
    base = base_values[0]
    parents = _git_value(repo, "rev-list", "--parents", "-n", "1", candidate).split()
    if len(parents) != 2 or parents[1].lower() != base:
        raise GitConflict("work-ID candidate base SHA does not match its sole parent")
    changed = _candidate_changed_paths(repo, base, candidate)
    try:
        normalized = _normalize_paths(repo, packet, changed)
    except DirectionGitError as exc:
        raise GitConflict(
            f"work-ID candidate changed paths do not match packet ownership: {exc}",
            facts={
                "base_sha": base,
                "candidate_sha": candidate,
                "changed_paths": changed,
            },
        ) from exc
    if normalized != changed:
        raise GitConflict("work-ID candidate changed paths are not canonical")
    if requested is not None and list(requested) != changed:
        raise GitConflict(
            "work-ID candidate changed paths do not match the exact requested paths",
            facts={
                "base_sha": base,
                "candidate_sha": candidate,
                "changed_paths": changed,
            },
        )
    try:
        _require_direction_owned(repo, changed)
    except SharedCoreRequired as exc:
        raise GitConflict(
            "work-ID candidate contains a non-direction-owned path",
            facts={
                "base_sha": base,
                "candidate_sha": candidate,
                "changed_paths": changed,
            },
        ) from exc
    return base, changed


def _fetch_remote(repo: Path) -> str:
    _run_git(
        repo,
        "fetch",
        "--no-tags",
        "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    )
    value = _git_value(repo, "rev-parse", "refs/remotes/origin/main").lower()
    if _FULL_SHA.fullmatch(value) is None:
        raise DirectionGitError("origin/main is not a full commit SHA")
    return value


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = _run_git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
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
    *,
    status: str,
    reason: str,
    work_id: str,
    base_sha: str | None = None,
    candidate_sha: str | None = None,
    integrated_sha: str | None = None,
    changed_paths: Sequence[str] = (),
    remote_sha: str | None = None,
    relation: str | None = None,
    push_attempted: bool = False,
    failure_scope: str | None = None,
    failure_ref: str | None = None,
) -> dict[str, Any]:
    result = {
        "status": status,
        "reason": reason,
        "work_id": work_id,
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "integrated_sha": integrated_sha,
        "changed_paths": list(changed_paths),
        "remote_sha": remote_sha,
        "relation": relation,
        "push_attempted": push_attempted,
    }
    if failure_scope is not None:
        result["failure_scope"] = failure_scope
    if failure_ref is not None:
        result["failure_ref"] = failure_ref
    return result


class _GitLock:
    def __init__(self, common: Path):
        self.path = common / "hmasd-direction-git.lock"
        self.stream = None
        self.locked = False
        self.deadline = time.monotonic() + _TRANSACTION_TIMEOUT_SECONDS
        self.deadline_token: Token[float | None] | None = None

    def _acquire(self) -> None:
        assert self.stream is not None
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
                remaining = self.deadline - time.monotonic()
                if remaining <= 0:
                    raise DirectionGitError(
                        "direction Git transaction timed out acquiring the repository lock"
                    ) from exc
                time.sleep(min(0.05, remaining))

    def _release(self) -> None:
        if not self.locked or self.stream is None:
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
            self.path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            os.close(descriptor)
            raise DirectionGitError("Git transaction lock is not a regular file")
        if info.st_size == 0:
            os.write(descriptor, b"\0")
            os.fsync(descriptor)
        self.stream = os.fdopen(descriptor, "r+b", buffering=0)
        try:
            hmasd_work_packet._verify_lock_identity(self.path, self.stream.fileno())
        except hmasd_work_packet.WorkPacketError as exc:
            self.stream.close()
            raise DirectionGitError(f"Git transaction lock identity is unsafe: {exc}") from exc
        try:
            self._acquire()
        except Exception:
            self.stream.close()
            raise
        try:
            hmasd_work_packet._verify_lock_identity(self.path, self.stream.fileno())
        except hmasd_work_packet.WorkPacketError as exc:
            self._release()
            self.stream.close()
            raise DirectionGitError(f"Git transaction lock identity changed: {exc}") from exc
        self.deadline_token = _TRANSACTION_DEADLINE.set(self.deadline)

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        assert self.stream is not None
        try:
            self._release()
        finally:
            try:
                if self.deadline_token is not None:
                    _TRANSACTION_DEADLINE.reset(self.deadline_token)
            finally:
                self.stream.close()


def commit_push(repo_raw: str, work_id: str, paths: Sequence[str]) -> dict[str, Any]:
    repo, common = _repository(repo_raw)
    packet = _load_packet(repo, work_id)
    requested = _normalize_paths(repo, packet, paths)
    with _GitLock(common):
        # All mutable facts are re-observed while holding the one short Git lock.
        if _git_value(repo, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
            raise DirectionGitError("checked-out branch changed before Git transaction")
        locked_packet = _load_packet(repo, work_id)
        if locked_packet != packet:
            raise GitConflict("published Work Packet changed before Git transaction")
        locked_requested = _normalize_paths(repo, locked_packet, paths)
        if locked_requested != requested:
            raise GitConflict("requested path facts changed before Git transaction")
        candidates = _work_id_candidates(repo, work_id)
        if len(candidates) > 1:
            raise GitConflict("multiple reachable commits contain the exact work-ID trailer")
        if candidates:
            candidate = candidates[0]
            base, changed = _verify_candidate(repo, packet, candidate, requested)
            try:
                remote = _fetch_remote(repo)
            except DirectionGitError:
                return _result(
                    status="OBSERVE_REQUIRED",
                    reason="candidate already exists but origin/main observation failed; "
                    "run observe-push",
                    work_id=work_id,
                    base_sha=base,
                    candidate_sha=candidate,
                    changed_paths=changed,
                    relation="OBSERVATION_FAILED",
                )
            relation = _relation(repo, candidate, remote)
            if relation in {"EQUAL", "DESCENDANT"}:
                return _result(
                    status="SUCCEEDED",
                    reason="candidate is contained by origin/main",
                    work_id=work_id,
                    base_sha=base,
                    candidate_sha=candidate,
                    integrated_sha=remote,
                    changed_paths=changed,
                    remote_sha=remote,
                    relation=relation,
                )
            if relation == "DIVERGED":
                raise GitConflict(
                    "origin/main diverged from the existing candidate",
                    facts={
                        "base_sha": base,
                        "candidate_sha": candidate,
                        "changed_paths": changed,
                        "remote_sha": remote,
                        "relation": relation,
                    },
                )
            return _result(
                status="OBSERVE_REQUIRED",
                reason="candidate already exists; run observe-push",
                work_id=work_id,
                base_sha=base,
                candidate_sha=candidate,
                changed_paths=changed,
                remote_sha=remote,
                relation=relation,
            )
        _require_direction_owned(repo, requested)
        local_head = _head(repo)
        try:
            remote_before_commit = _fetch_remote(repo)
        except DirectionGitError:
            return _result(
                status="OBSERVE_REQUIRED",
                reason="origin/main could not be observed before commit",
                work_id=work_id,
                base_sha=local_head,
                changed_paths=requested,
                relation="OBSERVATION_FAILED",
            )
        head_relation = _relation(repo, local_head, remote_before_commit)
        if head_relation == "DIVERGED":
            raise GitConflict(
                "local main diverged from origin/main before commit",
                facts={
                    "base_sha": local_head,
                    "changed_paths": requested,
                    "remote_sha": remote_before_commit,
                    "relation": head_relation,
                },
            )
        if head_relation != "EQUAL":
            return _result(
                status="OBSERVE_REQUIRED",
                reason="local main does not equal observed origin/main; "
                "resolve existing Git state first",
                work_id=work_id,
                base_sha=local_head,
                changed_paths=requested,
                remote_sha=remote_before_commit,
                relation=head_relation,
            )
        changed = _working_changes(repo, requested)
        if changed != requested:
            raise DirectionGitError(
                "requested paths must be the exact changed paths",
                facts={"changed_paths": changed},
            )
        base = _head(repo)
        message = (
            f"{_subject(packet)}\n\n"
            f"HMASD-Work-ID: {work_id}\n"
            f"HMASD-Base-SHA: {base}\n"
            f"HMASD-Assignment: {packet['target_identity']}\n"
        )
        _run_git(
            repo,
            "-c",
            "core.hooksPath=",
            "-c",
            "commit.gpgSign=false",
            "commit",
            "--only",
            "-m",
            message,
            "--",
            *requested,
        )
        candidate = _head(repo)
        verified_base, verified_paths = _verify_candidate(
            repo, packet, candidate, requested
        )
        if verified_base != base or verified_paths != requested:
            raise GitConflict("new candidate verification did not reproduce locked facts")
        try:
            remote = _fetch_remote(repo)
        except DirectionGitError:
            return _result(
                status="OBSERVE_REQUIRED",
                reason="candidate was committed but origin/main observation failed; "
                "run observe-push",
                work_id=work_id,
                base_sha=base,
                candidate_sha=candidate,
                changed_paths=requested,
                relation="OBSERVATION_FAILED",
            )
        relation = _relation(repo, candidate, remote)
        if relation in {"EQUAL", "DESCENDANT"}:
            return _result(
                status="SUCCEEDED",
                reason="candidate is already contained by origin/main",
                work_id=work_id,
                base_sha=base,
                candidate_sha=candidate,
                integrated_sha=remote,
                changed_paths=requested,
                remote_sha=remote,
                relation=relation,
            )
        if relation == "DIVERGED":
            raise GitConflict(
                "origin/main diverged before push",
                facts={
                    "base_sha": base,
                    "candidate_sha": candidate,
                    "changed_paths": requested,
                    "remote_sha": remote,
                    "relation": relation,
                },
            )
        try:
            _remaining_timeout()
        except DirectionGitError:
            return _result(
                status="OBSERVE_REQUIRED",
                reason="transaction deadline expired before push; run observe-push",
                work_id=work_id,
                base_sha=base,
                candidate_sha=candidate,
                changed_paths=requested,
                remote_sha=remote,
                relation=relation,
            )
        push_attempted = True
        try:
            _run_git(
                repo,
                "push",
                "origin",
                f"{candidate}:refs/heads/main",
            )
        except DirectionGitError:
            pass
        try:
            remote = _fetch_remote(repo)
        except DirectionGitError as exc:
            raise PushUnknown(
                "push outcome is unknown because the one post-send observation failed; "
                "use observe-push and never resend",
                facts={
                    "base_sha": base,
                    "candidate_sha": candidate,
                    "changed_paths": requested,
                    "remote_sha": remote,
                    "relation": "OBSERVATION_FAILED",
                    "push_attempted": push_attempted,
                },
            ) from exc
        relation = _relation(repo, candidate, remote)
        if relation not in {"EQUAL", "DESCENDANT"}:
            raise PushUnknown(
                "push outcome is unknown; use observe-push and never resend",
                facts={
                    "base_sha": base,
                    "candidate_sha": candidate,
                    "changed_paths": requested,
                    "remote_sha": remote,
                    "relation": relation,
                    "push_attempted": push_attempted,
                },
            )
        return _result(
            status="SUCCEEDED",
            reason="candidate is contained by origin/main",
            work_id=work_id,
            base_sha=base,
            candidate_sha=candidate,
            integrated_sha=remote,
            changed_paths=requested,
            remote_sha=remote,
            relation=relation,
            push_attempted=push_attempted,
        )


def observe_push(repo_raw: str, work_id: str) -> dict[str, Any]:
    """Observe one trailer-bound candidate and origin/main without pushing."""

    repo, common = _repository(repo_raw)
    packet = _load_packet(repo, work_id)
    with _GitLock(common):
        if _git_value(repo, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
            raise DirectionGitError("checked-out branch changed before push observation")
        candidates = _work_id_candidates(repo, work_id)
        if not candidates:
            raise GitConflict("no reachable commit contains the exact work-ID trailer")
        if len(candidates) > 1:
            raise GitConflict("multiple reachable commits contain the exact work-ID trailer")
        candidate = candidates[0]
        base, changed = _verify_candidate(repo, packet, candidate, None)
        try:
            remote = _fetch_remote(repo)
        except DirectionGitError as exc:
            raise PushUnknown(
                "origin/main observation failed; observe-push cannot resolve the candidate",
                facts={
                    "base_sha": base,
                    "candidate_sha": candidate,
                    "changed_paths": changed,
                    "relation": "OBSERVATION_FAILED",
                    "push_attempted": False,
                },
            ) from exc
        relation = _relation(repo, candidate, remote)
        facts = {
            "base_sha": base,
            "candidate_sha": candidate,
            "changed_paths": changed,
            "remote_sha": remote,
            "relation": relation,
            "push_attempted": False,
        }
        if relation in {"EQUAL", "DESCENDANT"}:
            return _result(
                status="SUCCEEDED",
                reason="candidate is contained by origin/main",
                work_id=work_id,
                integrated_sha=remote,
                **facts,
            )
        if relation == "DIVERGED":
            raise GitConflict("origin/main diverged from the candidate", facts=facts)
        raise PushUnknown(
            "candidate is not yet contained by origin/main; observation cannot resend",
            facts=facts,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    commit = subparsers.add_parser("commit-push")
    commit.add_argument("--repo", required=True)
    commit.add_argument("--work-id", required=True)
    commit.add_argument("--path", action="append", required=True)
    observe = subparsers.add_parser("observe-push")
    observe.add_argument("--repo", required=True)
    observe.add_argument("--work-id", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.operation == "commit-push":
            result = commit_push(args.repo, args.work_id, args.path)
        else:
            result = observe_push(args.repo, args.work_id)
    except DirectionGitError as exc:
        facts = {
            "base_sha": None,
            "candidate_sha": None,
            "integrated_sha": None,
            "changed_paths": [],
            "remote_sha": None,
            "relation": None,
            "push_attempted": False,
        }
        facts.update(exc.facts)
        result = _result(
            status=exc.status,
            reason=str(exc),
            work_id=getattr(args, "work_id", ""),
            **facts,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return exc.code
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 3 if result["status"] == "OBSERVE_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
