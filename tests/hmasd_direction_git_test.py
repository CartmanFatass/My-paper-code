"""Observable repository/remote tests for the Session Envelope v2 Git seam."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/hmasd_direction_git.py"
ENVELOPE_SCRIPT = ROOT / "scripts/hmasd_session_envelope.py"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, check=check, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    subprocess.run(["git", "init", "--initial-branch=main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.name", "HMASD Test")
    _git(repo, "config", "user.email", "hmasd-test@example.invalid")
    _write(repo / ".gitignore", "/.codex/runtime/\n")
    _write(repo / "docs/research/candidates/alpha/DIRECTION.md", "alpha authority\n")
    _write(repo / "experiments/candidates/alpha/change.py", "VALUE = 1\n")
    _write(repo / "experiments/candidates/beta/change.py", "VALUE = 1\n")
    _write(repo / "shared/core.py", "VALUE = 1\n")
    _write(repo / "notes.txt", "base\n")
    _write(repo / "dirty.txt", "base\n")
    _write(
        repo / "docs/project/git-path-policy-v1.json",
        json.dumps(
            {
                "schema_version": 1,
                "default_classification": "shared-core",
                "rules": [
                    {"classification": "direction-owned", "path": "experiments/candidates", "type": "prefix"},
                    {"classification": "direction-owned", "path": "tests/experiments/candidates", "type": "prefix"},
                    {"classification": "direction-owned", "path": "docs/research/candidates", "type": "prefix"},
                    {"classification": "direction-owned", "path": "temp/directions", "type": "prefix"},
                ],
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
    )
    _git(repo, "add", "--all")
    _git(repo, "commit", "-m", "initial")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    return repo, origin


def _assignment(
    repo: Path, *, direction: str = "alpha", owned_paths: list[str] | None = None,
    workspace_mode: str = "shared-main",
) -> dict[str, Any]:
    authority = repo / f"docs/research/candidates/{direction}/DIRECTION.md"
    if not authority.exists():
        _write(authority, f"{direction} authority\n")
    body = repo / f"assignment-{direction}.json"
    body.write_text(
        json.dumps(
            {
                "objective": f"implement the {direction} direction discriminator",
                "context_refs": [{
                    "path": f"docs/research/candidates/{direction}/DIRECTION.md",
                    "sha256": hashlib.sha256(authority.read_bytes()).hexdigest(),
                }],
                "owned_paths": owned_paths or [f"experiments/candidates/{direction}/"],
                "effects": ["commit and push exact direction-owned paths once"],
                "constraints": ["preserve unrelated workspace state"],
                "done_when": ["origin/main contains the candidate"],
                "workspace_mode": workspace_mode,
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(ENVELOPE_SCRIPT), "assignment", "--repo", str(repo),
         "--direction-id", direction, "--sender-identity", "Workflow-Clerk",
         "--sender-thread-id", "thread-clerk", "--recipient-identity", f"CM/{direction}/g1",
         "--recipient-thread-id", f"thread-cm-{direction}", "--body", str(body)],
        cwd=repo, check=True, capture_output=True, text=True,
    )
    body.unlink()
    output = json.loads(completed.stdout)
    envelope = json.loads((repo / output["locator"]).read_text(encoding="utf-8"))
    return {**output, "envelope": envelope}


def _cli(repo: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=repo, check=False, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    assert completed.stdout.strip(), completed.stderr
    return completed, json.loads(completed.stdout)


def test_assignment_commit_push_isolates_exact_path_and_publishes_candidate(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path)
    assignment = _assignment(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    _write(repo / "notes.txt", "user staged change\n")
    _git(repo, "add", "notes.txt")
    _write(repo / "dirty.txt", "user unstaged change\n")
    _write(repo / "untracked.txt", "user untracked change\n")

    completed, result = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment", assignment["locator"],
        "--path", assigned,
    )

    assert completed.returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["message_id"] == assignment["envelope"]["message_id"]
    assert result["assignment_locator"] == assignment["locator"]
    assert result["workspace_mode"] == "shared-main"
    assert result["changed_paths"] == [assigned]
    candidate = result["candidate_sha"]
    assert _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate).stdout.splitlines() == [assigned]
    assert _git(repo, "diff", "--cached", "--name-only").stdout.splitlines() == ["notes.txt"]
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == candidate
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == candidate
    assert (repo / "dirty.txt").read_text(encoding="utf-8") == "user unstaged change\n"
    assert (repo / "untracked.txt").read_text(encoding="utf-8") == "user untracked change\n"


def test_assignment_can_publish_one_exact_new_direction_owned_path(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path)
    assignment = _assignment(repo)
    added = "experiments/candidates/alpha/new.py"
    _write(repo / added, "VALUE = 'new'\n")

    completed, result = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        assignment["locator"], "--path", added,
    )

    assert completed.returncode == 0, result
    assert result["changed_paths"] == [added]
    candidate = result["candidate_sha"]
    assert _git(repo, "show", "--format=", "--name-only", candidate).stdout.splitlines() == [added]
    assert _git(repo, "status", "--porcelain=v1", "--", added).stdout == ""


def test_failed_push_becomes_unknown_and_only_observe_can_resolve(tmp_path: Path) -> None:
    repo, origin = _repository(tmp_path)
    assignment = _assignment(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    hook = origin / "hooks/pre-receive"
    _write(hook, "#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)

    failed, unknown = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        assignment["locator"], "--path", assigned,
    )

    assert failed.returncode == 7, unknown
    assert unknown["status"] == "PUSH_OUTCOME_UNKNOWN"
    assert unknown["push_attempted"] is True
    assert unknown["relation"] == "ANCESTOR"
    candidate = unknown["candidate_sha"]
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == base

    hook.unlink()
    repeated, observe_required = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        assignment["locator"], "--path", assigned,
    )
    assert repeated.returncode == 3, observe_required
    assert observe_required["status"] == "OBSERVE_REQUIRED"
    assert observe_required["candidate_sha"] == candidate
    assert observe_required["push_attempted"] is False
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == base

    _git(repo, "push", "origin", f"{candidate}:refs/heads/main")
    observed, resolved = _cli(
        repo, "observe-push", "--repo", str(repo), "--assignment",
        assignment["locator"],
    )
    assert observed.returncode == 0, resolved
    assert resolved["status"] == "SUCCEEDED"
    assert resolved["candidate_sha"] == candidate
    assert resolved["integrated_sha"] == candidate
    assert resolved["relation"] == "EQUAL"
    assert resolved["push_attempted"] is False


def test_shared_core_is_refused_by_exact_fence_before_git_mutation(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path)
    assignment = _assignment(repo, owned_paths=["shared/core.py"])
    _write(repo / "shared/core.py", "VALUE = 2\n")
    before_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    before_remote = _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    before_status = _git(repo, "status", "--porcelain=v1").stdout

    completed, refused = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        assignment["locator"], "--path", "shared/core.py",
    )

    assert completed.returncode == 5, refused
    assert refused["status"] == "SHARED_CORE_ACTION_REQUIRED"
    assert refused["changed_paths"] == ["shared/core.py"]
    assert refused["push_attempted"] is False
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before_head
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == before_remote
    assert _git(repo, "status", "--porcelain=v1").stdout == before_status


def test_invalid_or_wrong_workspace_assignment_is_refused_without_git_mutation(
    tmp_path: Path,
) -> None:
    repo, _ = _repository(tmp_path)
    assigned = "experiments/candidates/alpha/change.py"
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    tampered = _assignment(repo)
    envelope_path = repo / tampered["locator"]
    document = json.loads(envelope_path.read_text(encoding="utf-8"))
    document["body"]["objective"] = "tampered after hashing"
    envelope_path.write_text(json.dumps(document), encoding="utf-8")
    rejected, invalid = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        tampered["locator"], "--path", assigned,
    )
    assert rejected.returncode == 2, invalid
    assert invalid["status"] == "REFUSED"
    assert "invalid" in invalid["reason"]

    separate = _assignment(repo, workspace_mode="separate-worktree")
    refused, wrong_workspace = _cli(
        repo, "commit-push", "--repo", str(repo), "--assignment",
        separate["locator"], "--path", assigned,
    )
    assert refused.returncode == 2, wrong_workspace
    assert wrong_workspace["status"] == "REFUSED"
    assert wrong_workspace["workspace_mode"] == "separate-worktree"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before


def test_disjoint_assignments_serialize_without_index_cross_pollution(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path)
    alpha = _assignment(repo)
    beta = _assignment(repo, direction="beta")
    alpha_path = "experiments/candidates/alpha/change.py"
    beta_path = "experiments/candidates/beta/change.py"
    _write(repo / alpha_path, "VALUE = 2\n")
    _write(repo / beta_path, "VALUE = 2\n")

    def invoke(assignment: dict[str, Any], path: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        return _cli(
            repo, "commit-push", "--repo", str(repo), "--assignment",
            assignment["locator"], "--path", path,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(invoke, alpha, alpha_path),
            executor.submit(invoke, beta, beta_path),
        ]
        results = [future.result() for future in futures]

    for completed, result in results:
        assert completed.returncode == 0, result
        assert result["status"] == "SUCCEEDED"
        assert result["changed_paths"] in ([alpha_path], [beta_path])
    candidates = [result["candidate_sha"] for _, result in results]
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    remote = _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    assert head == remote
    assert all(
        _git(repo, "merge-base", "--is-ancestor", candidate, head, check=False).returncode == 0
        for candidate in candidates
    )
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""
