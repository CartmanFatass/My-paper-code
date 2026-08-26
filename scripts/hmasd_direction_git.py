#!/usr/bin/env python3
"""Commit and observe exact direction-owned Git changes for one Work Packet."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import hmasd_platform, hmasd_work_packet, hmasd_worktree
except ImportError:
    import hmasd_platform
    import hmasd_work_packet
    import hmasd_worktree


_WORK_ID = re.compile(r"[0-9a-f]{64}\Z")
_FULL_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_FETCH_TIMEOUT_SECONDS = 60
_PUSH_TIMEOUT_SECONDS = 60


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


def _run_git(
    repo: Path,
    *args: str,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
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
    try:
        classifications = hmasd_worktree.observe_path_classifications(repo, normalized)
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
    return normalized


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
    try:
        changed = hmasd_worktree._changed_paths(repo, base, candidate)
    except hmasd_worktree.WorktreeError as exc:
        raise GitConflict(f"cannot verify work-ID candidate changed paths: {exc}") from exc
    normalized = _normalize_paths(repo, packet, changed)
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
    return base, changed


def _fetch_remote(repo: Path) -> str:
    try:
        _run_git(
            repo,
            "fetch",
            "--no-tags",
            "origin",
            "+refs/heads/main:refs/remotes/origin/main",
            timeout=_FETCH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise DirectionGitError("origin/main observation timed out") from exc
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
) -> dict[str, Any]:
    return {
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


class _GitLock:
    def __init__(self, common: Path):
        self.path = common / "hmasd-direction-git.lock"
        self.stream = None
        self.lock = None

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
        self.stream = os.fdopen(descriptor, "r+b", buffering=0)
        try:
            hmasd_work_packet._verify_lock_identity(self.path, self.stream.fileno())
        except hmasd_work_packet.WorkPacketError as exc:
            self.stream.close()
            raise DirectionGitError(f"Git transaction lock identity is unsafe: {exc}") from exc
        self.lock = hmasd_platform.exclusive_file_lock(self.stream.fileno())
        try:
            self.lock.__enter__()
        except Exception:
            self.stream.close()
            raise
        try:
            hmasd_work_packet._verify_lock_identity(self.path, self.stream.fileno())
        except hmasd_work_packet.WorkPacketError as exc:
            self.lock.__exit__(None, None, None)
            self.stream.close()
            raise DirectionGitError(f"Git transaction lock identity changed: {exc}") from exc

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        assert self.lock is not None and self.stream is not None
        try:
            self.lock.__exit__(exc_type, exc, traceback)
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
            return _result(
                status="OBSERVE_REQUIRED",
                reason="candidate already exists; run observe-push",
                work_id=work_id,
                base_sha=base,
                candidate_sha=candidate,
                integrated_sha=remote if relation in {"EQUAL", "DESCENDANT"} else None,
                changed_paths=changed,
                remote_sha=remote,
                relation=relation,
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
        _run_git(repo, "add", "--", *requested)
        _run_git(repo, "commit", "--only", "-m", message, "--", *requested)
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
        push_attempted = True
        try:
            _run_git(
                repo,
                "push",
                "origin",
                f"{candidate}:refs/heads/main",
                timeout=_PUSH_TIMEOUT_SECONDS,
            )
        except (DirectionGitError, subprocess.TimeoutExpired):
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
