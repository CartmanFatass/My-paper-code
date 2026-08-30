#!/usr/bin/env python3
"""Execute one bounded local-project Clerk chore from ordinary CLI flags."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Sequence
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any


IDENTITY = "Clerk"
OPERATION = "integrate-candidate"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ACTOR_RE = re.compile(r"^(?:root|em:[a-z0-9][a-z0-9_-]{1,63}|cm:[a-z0-9][a-z0-9_-]{1,63})$")
REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
BRANCH_RE = re.compile(r"^omp/[A-Za-z0-9][A-Za-z0-9._/-]*$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")

CommandRunner = Callable[
    [Sequence[str], Path, bytes | None], subprocess.CompletedProcess[bytes]
]


class ClerkRefusal(Exception):
    """A fail-closed precondition or known-effect refusal."""

    def __init__(self, code: str, message: str, exit_code: int = 5) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class GitFailure(Exception):
    """A nonzero Git command result retained for exact classification."""

    def __init__(self, argv: Sequence[str], result: subprocess.CompletedProcess[bytes]) -> None:
        super().__init__(_result_detail(result))
        self.argv = tuple(argv)
        self.result = result


def _default_runner(
    argv: Sequence[str], cwd: Path, input_bytes: bytes | None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(argv),
        cwd=str(cwd),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _decoded(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def _result_detail(result: subprocess.CompletedProcess[bytes]) -> str:
    return _decoded(result.stderr).strip() or _decoded(result.stdout).strip() or (
        f"Git exited {result.returncode}"
    )


class Git:
    """Small dependency-injectable Git command surface."""

    def __init__(self, repo: Path, runner: CommandRunner) -> None:
        self.repo = repo
        self.runner = runner

    def raw(
        self,
        *args: str,
        cwd: Path | None = None,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return self.runner(("git", *args), cwd or self.repo, input_bytes)

    def run(
        self,
        *args: str,
        cwd: Path | None = None,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        result = self.raw(*args, cwd=cwd, input_bytes=input_bytes)
        if result.returncode:
            raise GitFailure(("git", *args), result)
        return result

    def text(self, *args: str, cwd: Path | None = None) -> str:
        return _decoded(self.run(*args, cwd=cwd).stdout).strip()


def _canonical_repo(raw: str, runner: CommandRunner) -> tuple[Path, Git]:
    try:
        supplied = Path(raw).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ClerkRefusal("INVALID_REPOSITORY", f"repository cannot be resolved: {exc}") from exc
    if not supplied.is_dir():
        raise ClerkRefusal("INVALID_REPOSITORY", "repository is not a directory")
    git = Git(supplied, runner)
    try:
        discovered = Path(git.text("rev-parse", "--show-toplevel")).resolve(strict=True)
    except (GitFailure, OSError, RuntimeError) as exc:
        raise ClerkRefusal("INVALID_REPOSITORY", f"Git repository discovery failed: {exc}") from exc
    if discovered != supplied:
        raise ClerkRefusal(
            "NONCANONICAL_REPOSITORY",
            f"--repo must identify the canonical Git top level ({discovered})",
        )
    return supplied, git


def _validate_job_id(value: str) -> str:
    if not ID_RE.fullmatch(value):
        raise ClerkRefusal("INVALID_JOB_ID", "job ID is not a valid stable assignment identifier")
    return value


def _validate_actor(value: str) -> str:
    if not ACTOR_RE.fullmatch(value):
        raise ClerkRefusal("INVALID_ACTOR", "actor must be root, em:<direction>, or cm:<direction>")
    return value


def _validate_branch(value: str) -> str:
    if not BRANCH_RE.fullmatch(value) or "//" in value or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ClerkRefusal("NON_OMP_TARGET", "target branch must be a canonical omp/* branch")
    return value


def _validate_sha(value: str, label: str) -> str:
    if not GIT_SHA_RE.fullmatch(value):
        raise ClerkRefusal("INVALID_GIT_IDENTITY", f"{label} must be one full lowercase Git object ID")
    return value


def _canonical_allowed_paths(repo: Path, raw_paths: Sequence[str]) -> tuple[str, ...]:
    if not raw_paths:
        raise ClerkRefusal("EMPTY_ALLOWLIST", "at least one --allowed-path is required")
    normalized: list[str] = []
    for raw in raw_paths:
        if not raw or "\\" in raw:
            raise ClerkRefusal("INVALID_ALLOWED_PATH", f"noncanonical allowed path: {raw!r}")
        path = PurePosixPath(raw)
        if path.is_absolute() or path.as_posix() != raw or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ClerkRefusal("INVALID_ALLOWED_PATH", f"noncanonical allowed path: {raw!r}")
        current = repo
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise ClerkRefusal("INVALID_ALLOWED_PATH", f"allowed path traverses a symlink: {raw}")
        normalized.append(raw)
    if len(set(normalized)) != len(normalized):
        raise ClerkRefusal("INVALID_ALLOWED_PATH", "allowed paths must be unique")
    return tuple(sorted(normalized))


def _exact_commit(git: Git, value: str, label: str) -> str:
    value = _validate_sha(value, label)
    try:
        observed = git.text("rev-parse", "--verify", f"{value}^{{commit}}")
    except GitFailure as exc:
        raise ClerkRefusal("MISSING_GIT_OBJECT", f"{label} is not a local commit: {value}") from exc
    if observed != value:
        raise ClerkRefusal("GIT_IDENTITY_DRIFT", f"{label} did not resolve exactly")
    return value


def _require_clean_target(git: Git, branch: str, expected: str) -> None:
    try:
        current = git.text("symbolic-ref", "--quiet", "--short", "HEAD")
        if current != branch:
            raise ClerkRefusal(
                "TARGET_BRANCH_MISMATCH",
                f"checked-out branch {current!r} is not target {branch!r}",
            )
        if git.run("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout:
            raise ClerkRefusal("DIRTY_TARGET", "target worktree must be completely clean", 6)
        tip = git.text("rev-parse", "--verify", f"refs/heads/{branch}^{{commit}}")
    except GitFailure as exc:
        raise ClerkRefusal("INVALID_TARGET", f"cannot inspect target branch: {exc}") from exc
    if tip != expected:
        raise ClerkRefusal(
            "STALE_LOCAL_PREDECESSOR",
            f"local target is {tip}, expected {expected}",
            4,
        )


def _require_direct_candidate(git: Git, source_base: str, candidate: str) -> None:
    try:
        lineage = git.text("rev-list", "--parents", "-n", "1", candidate).split()
    except GitFailure as exc:
        raise ClerkRefusal("CANDIDATE_PARENT_DRIFT", f"cannot inspect candidate parent: {exc}") from exc
    if lineage != [candidate, source_base]:
        raise ClerkRefusal(
            "CANDIDATE_PARENT_DRIFT",
            "candidate must be one non-merge commit whose sole parent is --source-base",
        )


def _candidate_paths(git: Git, source_base: str, candidate: str) -> tuple[str, ...]:
    try:
        raw = git.run(
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            source_base,
            candidate,
            "--",
        ).stdout
        paths = tuple(
            sorted(part.decode("utf-8", errors="strict") for part in raw.split(b"\0") if part)
        )
    except (GitFailure, UnicodeDecodeError) as exc:
        raise ClerkRefusal("INVALID_CANDIDATE_PATHS", f"cannot read canonical candidate paths: {exc}") from exc
    return paths


def _upstream(git: Git, branch: str) -> tuple[str, str]:
    local_ref = f"refs/heads/{branch}"
    try:
        raw = git.run(
            "for-each-ref",
            "--format=%(upstream:remotename)%00%(upstream:remoteref)",
            local_ref,
        ).stdout.rstrip(b"\n")
        if raw:
            remote_raw, remote_ref_raw = raw.split(b"\0", 1)
        else:
            remote_raw = remote_ref_raw = b""
        remote = remote_raw.decode("utf-8", errors="strict")
        remote_ref = remote_ref_raw.decode("utf-8", errors="strict")
    except (GitFailure, ValueError, UnicodeDecodeError) as exc:
        raise ClerkRefusal("INVALID_TARGET_UPSTREAM", f"cannot discover target upstream: {exc}") from exc

    if remote or remote_ref:
        if not REMOTE_RE.fullmatch(remote) or remote_ref != local_ref:
            raise ClerkRefusal(
                "INVALID_TARGET_UPSTREAM",
                "target must track the same canonical branch on one configured remote",
            )
        return remote, remote_ref

    try:
        remotes = git.run("remote").stdout.decode("utf-8", errors="strict").splitlines()
    except (GitFailure, UnicodeDecodeError) as exc:
        raise ClerkRefusal(
            "INVALID_TARGET_UPSTREAM", f"cannot discover configured remotes: {exc}"
        ) from exc
    if len(remotes) != 1 or not REMOTE_RE.fullmatch(remotes[0]):
        raise ClerkRefusal(
            "INVALID_TARGET_UPSTREAM",
            "target has no upstream and requires exactly one canonical configured remote",
        )
    return remotes[0], local_ref


def _build_integration_commit(
    git: Git,
    source_base: str,
    candidate: str,
    expected_predecessor: str,
    actor: str,
    commit_message: str,
    allowed_paths: tuple[str, ...],
) -> tuple[str, Path, tempfile.TemporaryDirectory[str]]:
    try:
        patch = git.run(
            "diff",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-renames",
            source_base,
            candidate,
            "--",
        ).stdout
    except GitFailure as exc:
        raise ClerkRefusal("CANDIDATE_DIFF_FAILED", f"cannot construct candidate diff: {exc}") from exc

    temporary = tempfile.TemporaryDirectory(prefix="hmasd-clerk-")
    worktree = (Path(temporary.name) / "checkout").resolve()
    try:
        git.run("worktree", "add", "--detach", str(worktree), expected_predecessor)
        checked = git.raw("apply", "--check", "--index", "-", cwd=worktree, input_bytes=patch)
        if checked.returncode:
            raise ClerkRefusal("CANDIDATE_CONFLICT", _result_detail(checked), 6)
        applied = git.raw("apply", "--index", "-", cwd=worktree, input_bytes=patch)
        if applied.returncode:
            raise ClerkRefusal("CANDIDATE_CONFLICT", _result_detail(applied), 6)
        staged = tuple(
            sorted(
                part.decode("utf-8", errors="strict")
                for part in git.run(
                    "diff", "--cached", "--name-only", "--no-renames", "-z", cwd=worktree
                ).stdout.split(b"\0")
                if part
            )
        )
        if staged != allowed_paths:
            raise ClerkRefusal(
                "APPLIED_PATH_DRIFT",
                f"applied paths {list(staged)!r} differ from allowlist {list(allowed_paths)!r}",
            )
        email_actor = actor.replace(":", "-")
        git.run(
            "-c",
            f"user.name={actor}",
            "-c",
            f"user.email={email_actor}@hmasd.local",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--no-gpg-sign",
            "-m",
            commit_message,
            cwd=worktree,
        )
        integrated = git.text("rev-parse", "HEAD", cwd=worktree)
        lineage = git.text("rev-list", "--parents", "-n", "1", integrated, cwd=worktree).split()
        if lineage != [integrated, expected_predecessor]:
            raise ClerkRefusal("INTEGRATION_PARENT_DRIFT", "integration commit parent changed unexpectedly")
        return integrated, worktree, temporary
    except Exception:
        _remove_worktree(git, worktree)
        temporary.cleanup()
        raise


def _remove_worktree(git: Git, worktree: Path) -> None:
    try:
        git.raw("worktree", "remove", "--force", str(worktree))
    except Exception:
        pass


def _fetch_tip(git: Git, remote: str, remote_ref: str) -> str:
    git.run("fetch", "--no-tags", remote, remote_ref)
    return git.text("rev-parse", "--verify", "FETCH_HEAD^{commit}")


def _known_push_rejection(result: subprocess.CompletedProcess[bytes] | None) -> bool:
    if result is None:
        return False
    text = f"{_decoded(result.stdout)}\n{_decoded(result.stderr)}".lower()
    return any(
        marker in text
        for marker in ("[rejected]", "remote rejected", "non-fast-forward", "stale info")
    )


def _observe_ambiguous_push(
    git: Git,
    remote: str,
    remote_ref: str,
    expected_predecessor: str,
    integrated: str,
) -> dict[str, Any]:
    try:
        observed = _fetch_tip(git, remote, remote_ref)
    except Exception as exc:
        return {
            "kind": "push-observation",
            "state": "UNKNOWN",
            "observed_remote_sha": None,
            "detail": str(exc),
        }
    if observed == integrated:
        state = "COMMITTED"
    elif observed == expected_predecessor:
        state = "NOT_COMMITTED"
    else:
        state = "DIVERGED"
    return {
        "kind": "push-observation",
        "state": state,
        "observed_remote_sha": observed,
    }


def integrate_candidate(
    *,
    job_id: str,
    repo_raw: str,
    source_base_raw: str,
    candidate_raw: str,
    target_branch_raw: str,
    expected_predecessor_raw: str,
    actor_raw: str,
    commit_message: str,
    allowed_paths_raw: Sequence[str],
    runner: CommandRunner = _default_runner,
) -> tuple[int, dict[str, Any]]:
    """Integrate one exact candidate and return one compact Clerk job result."""

    job_id = _validate_job_id(job_id)
    actor = _validate_actor(actor_raw)
    branch = _validate_branch(target_branch_raw)
    if not commit_message.strip():
        raise ClerkRefusal("EMPTY_COMMIT_MESSAGE", "commit message must be nonempty")
    repo, git = _canonical_repo(repo_raw, runner)
    allowed_paths = _canonical_allowed_paths(repo, allowed_paths_raw)
    source_base = _exact_commit(git, source_base_raw, "source base")
    candidate = _exact_commit(git, candidate_raw, "candidate")
    expected_predecessor = _exact_commit(git, expected_predecessor_raw, "expected predecessor")
    _require_clean_target(git, branch, expected_predecessor)
    _require_direct_candidate(git, source_base, candidate)
    changed_paths = _candidate_paths(git, source_base, candidate)
    if changed_paths != allowed_paths:
        raise ClerkRefusal(
            "PATH_ALLOWLIST_MISMATCH",
            f"candidate paths {list(changed_paths)!r} differ from exact allowlist {list(allowed_paths)!r}",
        )
    remote, remote_ref = _upstream(git, branch)

    integrated, worktree, temporary = _build_integration_commit(
        git,
        source_base,
        candidate,
        expected_predecessor,
        actor,
        commit_message,
        allowed_paths,
    )
    try:
        try:
            observed_predecessor = _fetch_tip(git, remote, remote_ref)
        except Exception as exc:
            raise ClerkRefusal("REMOTE_OBSERVATION_FAILED", str(exc), 1) from exc
        if observed_predecessor != expected_predecessor:
            raise ClerkRefusal(
                "STALE_REMOTE_PREDECESSOR",
                f"remote target is {observed_predecessor}, expected {expected_predecessor}",
                4,
            )

        push_args = (
            "push",
            "--porcelain",
            f"--force-with-lease={remote_ref}:{expected_predecessor}",
            remote,
            f"{integrated}:{remote_ref}",
        )
        push_result: subprocess.CompletedProcess[bytes] | None = None
        try:
            push_result = git.raw(*push_args)
        except Exception as exc:
            push_error = str(exc)
        else:
            push_error = _result_detail(push_result) if push_result.returncode else ""

        if push_result is None or push_result.returncode:
            observation = _observe_ambiguous_push(
                git, remote, remote_ref, expected_predecessor, integrated
            )
            if _known_push_rejection(push_result) and observation["state"] != "COMMITTED":
                return 6, {
                    "logical_identity": IDENTITY,
                    "job_id": job_id,
                    "operation": OPERATION,
                    "outcome": "REFUSED",
                    "observations": [
                        {
                            "kind": "refusal",
                            "code": "PUSH_REJECTED",
                            "message": push_error,
                        },
                        observation,
                    ],
                }
            return 1, {
                "logical_identity": IDENTITY,
                "job_id": job_id,
                "operation": OPERATION,
                "outcome": "UNKNOWN",
                "observations": [
                    {
                        "kind": "push-attempt",
                        "attempts": 1,
                        "detail": push_error,
                    },
                    observation,
                ],
            }

        try:
            git.run("merge", "--ff-only", integrated)
        except GitFailure as exc:
            return 1, {
                "logical_identity": IDENTITY,
                "job_id": job_id,
                "operation": OPERATION,
                "outcome": "UNKNOWN",
                "observations": [
                    {
                        "kind": "remote-integration",
                        "state": "COMMITTED",
                        "integrated_sha": integrated,
                    },
                    {
                        "kind": "local-fast-forward",
                        "state": "UNKNOWN",
                        "detail": str(exc),
                    },
                ],
            }
        return 0, {
            "logical_identity": IDENTITY,
            "job_id": job_id,
            "operation": OPERATION,
            "outcome": "COMPLETED",
            "observations": [
                {
                    "kind": "integration",
                    "repository": str(repo),
                    "target_branch": branch,
                    "remote": remote,
                    "actor": actor,
                    "source_base": source_base,
                    "candidate": candidate,
                    "expected_predecessor": expected_predecessor,
                    "changed_paths": list(changed_paths),
                    "integrated_sha": integrated,
                    "push_attempts": 1,
                }
            ],
        }
    finally:
        _remove_worktree(git, worktree)
        temporary.cleanup()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one bounded Clerk project chore.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    integrate = subparsers.add_parser(
        OPERATION,
        help="apply one exact candidate and push it once with predecessor protection",
    )
    integrate.add_argument("--job-id", required=True)
    integrate.add_argument("--repo", required=True)
    integrate.add_argument("--source-base", required=True)
    integrate.add_argument("--candidate", required=True)
    integrate.add_argument("--target-branch", required=True)
    integrate.add_argument("--expected-predecessor", required=True)
    integrate.add_argument("--actor", required=True)
    integrate.add_argument("--commit-message", required=True)
    integrate.add_argument("--allowed-path", action="append", required=True)
    return parser


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def main(
    argv: Iterable[str] | None = None,
    *,
    runner: CommandRunner = _default_runner,
) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        code, result = integrate_candidate(
            job_id=args.job_id,
            repo_raw=args.repo,
            source_base_raw=args.source_base,
            candidate_raw=args.candidate,
            target_branch_raw=args.target_branch,
            expected_predecessor_raw=args.expected_predecessor,
            actor_raw=args.actor,
            commit_message=args.commit_message,
            allowed_paths_raw=args.allowed_path,
            runner=runner,
        )
    except ClerkRefusal as exc:
        code = exc.exit_code
        result = {
            "logical_identity": IDENTITY,
            "job_id": getattr(args, "job_id", "invalid"),
            "operation": OPERATION,
            "outcome": "REFUSED",
            "observations": [
                {"kind": "refusal", "code": exc.code, "message": str(exc)}
            ],
        }
    except Exception as exc:
        code = 1
        result = {
            "logical_identity": IDENTITY,
            "job_id": getattr(args, "job_id", "invalid"),
            "operation": OPERATION,
            "outcome": "UNKNOWN",
            "observations": [
                {"kind": "failure", "code": "UNEXPECTED_FAILURE", "message": str(exc)}
            ],
        }
    _emit(result)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
