"""Focused contracts for the stable sequential HMASD Clerk service."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

import pytest

import scripts.hmasd_clerk as clerk


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, Path, str, str]:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "init", "-b", "omp/workflow", str(repo)],
        check=True,
        capture_output=True,
    )
    git(repo, "config", "user.name", "Test Author")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "owned.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "owned.txt")
    git(repo, "commit", "-m", "base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "omp/workflow")

    git(repo, "switch", "-c", "candidate-source")
    (repo / "owned.txt").write_text("candidate\n", encoding="utf-8")
    git(repo, "add", "owned.txt")
    git(repo, "commit", "-m", "candidate")
    candidate = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "omp/workflow")
    return repo, remote, base, candidate


def argv(repo: Path, base: str, candidate: str, *, job_id: str = "job-001") -> list[str]:
    return [
        "integrate-candidate",
        "--job-id",
        job_id,
        "--repo",
        str(repo),
        "--source-base",
        base,
        "--candidate",
        candidate,
        "--target-branch",
        "omp/workflow",
        "--expected-predecessor",
        base,
        "--actor",
        "cm:example",
        "--commit-message",
        "Integrate exact candidate",
        "--allowed-path",
        "owned.txt",
    ]


def invoke(
    arguments: Sequence[str],
    capsys: pytest.CaptureFixture[str],
    *,
    runner: clerk.CommandRunner = clerk._default_runner,
) -> tuple[int, dict[str, Any]]:
    code = clerk.main(arguments, runner=runner)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    return code, json.loads(captured.out)


def test_successful_integration_uses_exact_allowlist_and_one_push(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, remote, base, candidate = make_repo(tmp_path)
    calls: list[tuple[str, ...]] = []

    def recording_runner(
        command: Sequence[str], cwd: Path, input_bytes: bytes | None
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append(tuple(command))
        return clerk._default_runner(command, cwd, input_bytes)

    code, result = invoke(argv(repo, base, candidate), capsys, runner=recording_runner)

    assert code == 0
    assert result["logical_identity"] == "Clerk"
    assert result["job_id"] == "job-001"
    assert result["operation"] == "integrate-candidate"
    assert result["outcome"] == "COMPLETED"
    observations = result["observations"]
    assert isinstance(observations, list)
    integrated = observations[0]["integrated_sha"]
    assert observations[0]["changed_paths"] == ["owned.txt"]
    assert observations[0]["push_attempts"] == 1
    assert git(repo, "rev-parse", "HEAD") == integrated
    assert git(remote, "rev-parse", "refs/heads/omp/workflow") == integrated
    assert sum(call[1:2] == ("push",) for call in calls) == 1


def test_candidate_path_set_must_equal_allowlist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    arguments = argv(repo, base, candidate)
    arguments.extend(["--allowed-path", "unused.txt"])

    code, result = invoke(arguments, capsys)

    assert code == 5
    assert result["outcome"] == "REFUSED"
    assert result["observations"][0]["code"] == "PATH_ALLOWLIST_MISMATCH"


def test_dirty_target_refuses_before_integration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    (repo / "untracked.txt").write_text("user work\n", encoding="utf-8")

    code, result = invoke(argv(repo, base, candidate), capsys)

    assert code == 6
    assert result["observations"][0]["code"] == "DIRTY_TARGET"
    assert git(repo, "rev-parse", "HEAD") == base


def test_candidate_parent_drift_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    arguments = argv(repo, base, candidate)
    source_index = arguments.index("--source-base") + 1
    arguments[source_index] = candidate

    code, result = invoke(arguments, capsys)

    assert code == 5
    assert result["observations"][0]["code"] == "CANDIDATE_PARENT_DRIFT"


def test_non_omp_target_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    arguments = argv(repo, base, candidate)
    arguments[arguments.index("--target-branch") + 1] = "main"

    code, result = invoke(arguments, capsys)

    assert code == 5
    assert result["observations"][0]["code"] == "NON_OMP_TARGET"


def test_conflicting_candidate_refuses_without_target_change(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    (repo / "owned.txt").write_text("target\n", encoding="utf-8")
    git(repo, "add", "owned.txt")
    git(repo, "commit", "-m", "advance target incompatibly")
    predecessor = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "omp/workflow")
    arguments = argv(repo, base, candidate)
    arguments[arguments.index("--expected-predecessor") + 1] = predecessor

    code, result = invoke(arguments, capsys)

    assert code == 6
    assert result["observations"][0]["code"] == "CANDIDATE_CONFLICT"
    assert git(repo, "rev-parse", "HEAD") == predecessor


def test_stale_remote_predecessor_refuses_before_push(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    git(repo, "push", "origin", f"{candidate}:refs/heads/omp/workflow")
    calls: list[tuple[str, ...]] = []

    def recording_runner(
        command: Sequence[str], cwd: Path, input_bytes: bytes | None
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append(tuple(command))
        return clerk._default_runner(command, cwd, input_bytes)

    code, result = invoke(argv(repo, base, candidate), capsys, runner=recording_runner)

    assert code == 4
    assert result["observations"][0]["code"] == "STALE_REMOTE_PREDECESSOR"
    assert not any(call[1:2] == ("push",) for call in calls)
    assert git(repo, "rev-parse", "HEAD") == base


def test_ambiguous_push_is_observed_once_and_never_retried(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    calls: list[tuple[str, ...]] = []

    def ambiguous_runner(
        command: Sequence[str], cwd: Path, input_bytes: bytes | None
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append(tuple(command))
        if len(command) > 1 and command[1] == "push":
            return subprocess.CompletedProcess(
                list(command), 1, stdout=b"", stderr=b"connection closed without status"
            )
        return clerk._default_runner(command, cwd, input_bytes)

    code, result = invoke(argv(repo, base, candidate), capsys, runner=ambiguous_runner)

    assert code == 1
    assert result["outcome"] == "UNKNOWN"
    assert result["observations"][0]["attempts"] == 1
    assert result["observations"][1]["state"] == "NOT_COMMITTED"
    assert sum(call[1:2] == ("push",) for call in calls) == 1
    assert sum(call[1:2] == ("fetch",) for call in calls) == 2
    assert git(repo, "rev-parse", "HEAD") == base


def test_stable_identity_spans_sequential_job_ids(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _remote, base, candidate = make_repo(tmp_path)
    first = argv(repo, base, candidate, job_id="job-001")
    second = argv(repo, base, candidate, job_id="job-002")
    first[first.index("--target-branch") + 1] = "main"
    second[second.index("--target-branch") + 1] = "main"

    _, first_result = invoke(first, capsys)
    _, second_result = invoke(second, capsys)

    assert first_result["logical_identity"] == second_result["logical_identity"] == "Clerk"
    assert first_result["job_id"] == "job-001"
    assert second_result["job_id"] == "job-002"


def test_help_exposes_only_ordinary_job_flags_and_no_json_draft(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as stopped:
        clerk.main(["integrate-candidate", "--help"])
    assert stopped.value.code == 0
    help_text = capsys.readouterr().out
    for flag in (
        "--job-id",
        "--repo",
        "--source-base",
        "--candidate",
        "--target-branch",
        "--expected-predecessor",
        "--actor",
        "--commit-message",
        "--allowed-path",
    ):
        assert flag in help_text
    assert "--draft" not in help_text
    assert "--packet" not in help_text
    assert " build " not in help_text
    assert " execute " not in help_text
