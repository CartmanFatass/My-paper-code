"""Focused non-Clerk safety tests for public worktree and candidate mechanics."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import hmasd_worktree as worktree


def git(
    cwd: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=process_env,
    )


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "omp/workflow")
    git(repo, "config", "user.name", "HMASD Test")
    git(repo, "config", "user.email", "hmasd@example.invalid")
    (repo / ".omp").mkdir()
    (repo / ".omp" / "AGENTS.md").write_text("# test repository\n", encoding="utf-8")
    (repo / "owned-a.txt").write_text("old-a\n", encoding="utf-8")
    (repo / "owned-b.txt").write_text("old-b\n", encoding="utf-8")
    git(repo, "add", ".omp/AGENTS.md", "owned-a.txt", "owned-b.txt")
    git(repo, "commit", "-m", "base")
    return repo, git(repo, "rev-parse", "HEAD").stdout.strip()


def test_policy_and_registry_are_current_only(tmp_path: Path) -> None:
    repo, _ = init_repo(tmp_path)
    with pytest.raises(worktree.InvalidInput):
        worktree._validate_integration_policy(None)
    with pytest.raises(worktree.InvalidInput):
        worktree._validate_integration_policy("OBSOLETE_EXACT_POLICY")
    assert worktree._validate_integration_policy("EXACT_HANDOFF") == "EXACT_HANDOFF"
    assert (
        worktree._validate_integration_policy("ORTHOGONAL_DIRECTION")
        == "ORTHOGONAL_DIRECTION"
    )

    registry = repo / ".omp" / "runtime" / "worktrees.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "revision": 1,
                "updated_at": "2026-08-30T00:00:00Z",
                "writer": "Root",
                "worktrees": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(worktree.InvalidInput, match="current schema version 2"):
        worktree._load_registry(repo)
    parser = worktree._parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["apply"])
    with pytest.raises(SystemExit):
        parser.parse_args(["recover-provision"])
    with pytest.raises(SystemExit):
        parser.parse_args(["retain"])


def test_path_arrays_are_sorted_but_duplicates_refuse() -> None:
    assert worktree._strict_path_list(["z/file", "a/file"], label="paths") == [
        "a/file",
        "z/file",
    ]
    with pytest.raises(worktree.InvalidInput, match="duplicates"):
        worktree._strict_path_list(["a/file", "a/file"], label="paths")


def test_orthogonal_prepared_object_requires_frozen_target_predecessor() -> None:
    assert (
        worktree._require_frozen_target_predecessor(
            "a" * 40,
            "a" * 40,
            phase="PREPARED",
        )
        == "a" * 40
    )
    with pytest.raises(worktree.StaleFacts) as caught:
        worktree._require_frozen_target_predecessor(
            "b" * 40,
            "a" * 40,
            phase="PREPARED",
        )
    assert caught.value.details == {
        "integration_phase": "PREPARED",
        "expected_target_predecessor_sha": "a" * 40,
        "local_sha": "b" * 40,
    }


def test_candidate_inspection_classifies_absent_commit_as_stale(
    tmp_path: Path,
) -> None:
    repo, base = init_repo(tmp_path)
    with pytest.raises(worktree.StaleFacts):
        worktree.inspect_candidate(str(repo), "f" * 40, base)
