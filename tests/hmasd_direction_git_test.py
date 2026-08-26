"""Public CLI tests for direction-owned Git commit and push effects."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from scripts import hmasd_direction_git
from scripts import hmasd_work_packet


SCRIPT = Path(__file__).parents[1] / "scripts" / "hmasd_direction_git.py"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(repo)],
        check=True,
        capture_output=True,
    )
    _git(repo, "config", "user.name", "HMASD Test")
    _git(repo, "config", "user.email", "hmasd-test@example.invalid")
    _write(repo / ".gitignore", "/.codex/runtime/\n")
    _write(
        repo / "docs/research/candidates/alpha/STATE.json",
        '{"direction":"alpha","revision":7}\n',
    )
    _write(
        repo / "docs/research/candidates/alpha/DIRECTION.json",
        '{"direction":"alpha","revision":3}\n',
    )
    _write(repo / "experiments/candidates/alpha/change.py", "VALUE = 1\n")
    _write(
        repo / "docs/research/candidates/beta/STATE.json",
        '{"direction":"beta","revision":7}\n',
    )
    _write(
        repo / "docs/research/candidates/beta/DIRECTION.json",
        '{"direction":"beta","revision":3}\n',
    )
    _write(repo / "experiments/candidates/beta/change.py", "VALUE = 1\n")
    _write(repo / "shared/core.py", "VALUE = 1\n")
    _write(repo / "notes.txt", "base\n")
    _write(repo / "dirty.txt", "base\n")
    _git(repo, "add", "--all")
    _git(repo, "commit", "-m", "initial")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    return repo, origin


def _publish(
    repo: Path,
    *,
    direction: str = "alpha",
    owned_paths: list[str] | None = None,
) -> dict[str, Any]:
    source = {
        "schema_version": 1,
        "scope_ref": {
            "path": f"docs/research/candidates/{direction}/STATE.json",
            "revision": 7,
        },
        "sender_identity": f"EM-{direction}",
        "target_identity": f"CM-{direction}",
        "authority_refs": [
            {
                "path": f"docs/research/candidates/{direction}/DIRECTION.json",
                "revision": 3,
            }
        ],
        "objective": f"implement the {direction} direction discriminator",
        "non_goals": ["do not change shared core"],
        "owned_paths": owned_paths or [f"experiments/candidates/{direction}"],
        "done_criteria": ["return one tested candidate"],
        "effect_refs": [],
    }
    packet = hmasd_work_packet.build_packet(source, repo=repo)
    hmasd_work_packet.publish_packet(packet, repo=repo)
    return packet


def _cli(repo: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert completed.stdout.strip(), completed.stderr
    return completed, json.loads(completed.stdout)


def test_commit_push_isolates_exact_path_and_preserves_unrelated_staged_change(
    tmp_path: Path,
) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    _write(repo / "notes.txt", "user staged change\n")
    _git(repo, "add", "notes.txt")
    _write(repo / "dirty.txt", "user unstaged change\n")
    _write(repo / "untracked.txt", "user untracked change\n")

    completed, result = _cli(
        repo,
        "commit-push",
        "--repo",
        str(repo),
        "--work-id",
        packet["work_id"],
        "--path",
        assigned,
    )

    assert completed.returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["changed_paths"] == [assigned]
    candidate = result["candidate_sha"]
    candidate_paths = _git(
        repo, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate
    ).stdout.splitlines()
    assert candidate_paths == [assigned]
    assert _git(repo, "diff", "--cached", "--name-only").stdout.splitlines() == ["notes.txt"]
    assert (repo / "notes.txt").read_text(encoding="utf-8") == "user staged change\n"
    assert _git(repo, "diff", "--name-only").stdout.splitlines() == ["dirty.txt"]
    assert (repo / "untracked.txt").read_text(encoding="utf-8") == "user untracked change\n"
    message = _git(repo, "show", "-s", "--format=%B", candidate).stdout
    assert f"HMASD-Work-ID: {packet['work_id']}" in message.splitlines()
    assert "HMASD-Base-SHA: " in message
    assert "HMASD-Assignment: CM-alpha" in message.splitlines()


def test_commit_push_recovers_exact_work_id_candidate_below_later_head_without_push(
    tmp_path: Path,
) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo / assigned, "VALUE = 2\n")
    _git(repo, "add", assigned)
    message = (
        f"hmasd({packet['work_id'][:12]}): implement the alpha direction discriminator\n\n"
        f"HMASD-Work-ID: {packet['work_id']}\n"
        f"HMASD-Base-SHA: {base}\n"
        "HMASD-Assignment: CM-alpha\n"
    )
    _git(repo, "commit", "--only", "-m", message, "--", assigned)
    candidate = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo / "later.txt", "a later independent commit\n")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later independent work")
    later_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert later_head != candidate

    completed, result = _cli(
        repo,
        "commit-push",
        "--repo",
        str(repo),
        "--work-id",
        packet["work_id"],
        "--path",
        assigned,
    )

    assert completed.returncode == 3, result
    assert result == {
        "base_sha": base,
        "candidate_sha": candidate,
        "changed_paths": [assigned],
        "integrated_sha": None,
        "push_attempted": False,
        "reason": "candidate already exists; run observe-push",
        "relation": "ANCESTOR",
        "remote_sha": base,
        "status": "OBSERVE_REQUIRED",
        "work_id": packet["work_id"],
    }
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == later_head
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == base
    matching_commits = _git(
        repo,
        "log",
        "--format=%H",
        f"--grep=HMASD-Work-ID: {packet['work_id']}",
    ).stdout.splitlines()
    assert len(matching_commits) == 1


def test_ambiguous_push_is_sent_once_and_resolved_only_by_observe_push(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    real_run = subprocess.run
    push_calls = 0

    def ambiguous_push(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal push_calls
        command = args[0]
        if command[:2] == ["git", "push"]:
            push_calls += 1
            raise subprocess.TimeoutExpired(command, timeout=60)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(hmasd_direction_git.subprocess, "run", ambiguous_push)
    returncode = hmasd_direction_git.main(
        [
            "commit-push",
            "--repo",
            str(repo),
            "--work-id",
            packet["work_id"],
            "--path",
            assigned,
        ]
    )
    unknown = json.loads(capsys.readouterr().out)

    assert returncode == 7
    assert unknown["status"] == "PUSH_OUTCOME_UNKNOWN"
    assert unknown["push_attempted"] is True
    assert unknown["integrated_sha"] is None
    assert unknown["relation"] == "ANCESTOR"
    assert push_calls == 1
    candidate = unknown["candidate_sha"]

    # A later observation proves that the ambiguous send landed. The public
    # observer itself remains unable to resend it.
    monkeypatch.setattr(hmasd_direction_git.subprocess, "run", real_run)
    _git(repo, "push", "origin", f"{candidate}:refs/heads/main")
    completed, observed = _cli(
        repo,
        "observe-push",
        "--repo",
        str(repo),
        "--work-id",
        packet["work_id"],
    )

    assert completed.returncode == 0, observed
    assert observed["status"] == "SUCCEEDED"
    assert observed["candidate_sha"] == candidate
    assert observed["integrated_sha"] == observed["remote_sha"] == candidate
    assert observed["relation"] == "EQUAL"
    assert observed["push_attempted"] is False
    assert push_calls == 1


def test_timed_out_push_that_landed_uses_one_post_error_observation(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    real_run = subprocess.run
    push_calls = 0
    fetch_calls = 0

    def landed_but_timed_out(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal push_calls, fetch_calls
        command = args[0]
        if command[:2] == ["git", "fetch"]:
            fetch_calls += 1
        if command[:2] == ["git", "push"]:
            push_calls += 1
            landed = real_run(*args, **kwargs)
            assert landed.returncode == 0, landed.stderr
            raise subprocess.TimeoutExpired(command, timeout=60)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(hmasd_direction_git.subprocess, "run", landed_but_timed_out)
    returncode = hmasd_direction_git.main(
        [
            "commit-push",
            "--repo",
            str(repo),
            "--work-id",
            packet["work_id"],
            "--path",
            assigned,
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["relation"] == "EQUAL"
    assert result["push_attempted"] is True
    assert push_calls == 1
    assert fetch_calls == 2  # one pre-push and exactly one post-error observation


def test_failed_pre_push_observation_preserves_candidate_for_observe_only_recovery(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    real_run = subprocess.run
    push_calls = 0

    def failed_fetch(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal push_calls
        command = args[0]
        if command[:2] == ["git", "fetch"]:
            raise subprocess.TimeoutExpired(command, timeout=60)
        if command[:2] == ["git", "push"]:
            push_calls += 1
        return real_run(*args, **kwargs)

    monkeypatch.setattr(hmasd_direction_git.subprocess, "run", failed_fetch)
    returncode = hmasd_direction_git.main(
        [
            "commit-push",
            "--repo",
            str(repo),
            "--work-id",
            packet["work_id"],
            "--path",
            assigned,
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert returncode == 3, result
    assert result["status"] == "OBSERVE_REQUIRED"
    assert result["candidate_sha"] == _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert result["changed_paths"] == [assigned]
    assert result["integrated_sha"] is None
    assert result["remote_sha"] is None
    assert result["relation"] == "OBSERVATION_FAILED"
    assert result["push_attempted"] is False
    assert push_calls == 0


def test_shared_core_request_is_refused_before_any_git_mutation(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path)
    packet = _publish(repo, owned_paths=["shared/core.py"])
    _write(repo / "shared/core.py", "VALUE = 2\n")
    before_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    before_status = _git(repo, "status", "--porcelain=v1").stdout
    before_remote = _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()

    completed, result = _cli(
        repo,
        "commit-push",
        "--repo",
        str(repo),
        "--work-id",
        packet["work_id"],
        "--path",
        "shared/core.py",
    )

    assert completed.returncode == 5, result
    assert result["status"] == "SHARED_CORE_ACTION_REQUIRED"
    assert result["changed_paths"] == ["shared/core.py"]
    assert result["push_attempted"] is False
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before_head
    assert _git(repo, "status", "--porcelain=v1").stdout == before_status
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == before_remote


def test_observe_push_accepts_remote_descendant_that_contains_candidate(tmp_path: Path) -> None:
    repo, origin = _repository(tmp_path)
    packet = _publish(repo)
    assigned = "experiments/candidates/alpha/change.py"
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo / assigned, "VALUE = 2\n")
    _git(repo, "add", assigned)
    message = (
        f"hmasd({packet['work_id'][:12]}): implement the alpha direction discriminator\n\n"
        f"HMASD-Work-ID: {packet['work_id']}\n"
        f"HMASD-Base-SHA: {base}\n"
        "HMASD-Assignment: CM-alpha\n"
    )
    _git(repo, "commit", "--only", "-m", message, "--", assigned)
    candidate = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "push", "origin", f"{candidate}:refs/heads/main")

    peer = tmp_path / "peer"
    subprocess.run(
        ["git", "clone", "--branch", "main", str(origin), str(peer)],
        check=True,
        capture_output=True,
    )
    _git(peer, "config", "user.name", "HMASD Peer")
    _git(peer, "config", "user.email", "hmasd-peer@example.invalid")
    _write(peer / "remote-followup.txt", "remote descendant\n")
    _git(peer, "add", "remote-followup.txt")
    _git(peer, "commit", "-m", "remote follow-up")
    descendant = _git(peer, "rev-parse", "HEAD").stdout.strip()
    _git(peer, "push", "origin", "main")

    completed, result = _cli(
        repo,
        "observe-push",
        "--repo",
        str(repo),
        "--work-id",
        packet["work_id"],
    )

    assert completed.returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["candidate_sha"] == candidate
    assert result["remote_sha"] == result["integrated_sha"] == descendant
    assert result["relation"] == "DESCENDANT"
    assert result["push_attempted"] is False


def test_disjoint_commit_push_calls_serialize_only_the_git_transaction(
    tmp_path: Path,
) -> None:
    repo, _ = _repository(tmp_path)
    alpha = _publish(repo, direction="alpha")
    beta = _publish(repo, direction="beta")
    alpha_path = "experiments/candidates/alpha/change.py"
    beta_path = "experiments/candidates/beta/change.py"
    _write(repo / alpha_path, "VALUE = 2\n")
    _write(repo / beta_path, "VALUE = 2\n")

    def invoke(
        packet: dict[str, Any], path: str
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        return _cli(
            repo,
            "commit-push",
            "--repo",
            str(repo),
            "--work-id",
            packet["work_id"],
            "--path",
            path,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        alpha_future = executor.submit(invoke, alpha, alpha_path)
        beta_future = executor.submit(invoke, beta, beta_path)
        completed_results = [alpha_future.result(), beta_future.result()]

    for completed, result in completed_results:
        assert completed.returncode == 0, result
        assert result["status"] == "SUCCEEDED"
        assert result["push_attempted"] is True
    candidates = {result["candidate_sha"] for _, result in completed_results}
    assert len(candidates) == 2
    assert all(
        _git(repo, "merge-base", "--is-ancestor", candidate, "HEAD").returncode == 0
        for candidate in candidates
    )
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    remote = _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    assert head == remote
    assert _git(repo, "status", "--porcelain=v1").stdout == ""
