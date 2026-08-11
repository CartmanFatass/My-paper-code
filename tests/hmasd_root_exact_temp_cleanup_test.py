"""Hermetic contracts for the exact assignment temporary-tree helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_root_exact_temp_cleanup.py"


def run_helper(
    repo: Path,
    assignment: Path,
    target: str | Path,
    *extra: str,
    actor: str = "root",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--actor",
            actor,
            "--repo-top",
            str(repo),
            "--assignment-root",
            str(assignment),
            "--target",
            str(target),
            *extra,
        ],
        cwd=str(repo),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "--initial-branch=main")
    git(repo, "config", "user.email", "root@example.invalid")
    git(repo, "config", "user.name", "Root")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-m", "base")
    assignment = repo / "temp" / "sessions" / "owner" / "assignment-1"
    assignment.mkdir(parents=True)
    target = assignment / "canonical-verify"
    target.mkdir()
    (target / "nested").mkdir()
    sibling = assignment / "sibling"
    sibling.mkdir()
    return repo, assignment, target


def test_preview_is_safe_and_apply_removes_only_the_exact_tree(
    fixture_repo: tuple[Path, Path, Path],
) -> None:
    repo, assignment, target = fixture_repo
    nested = target / "nested"
    before = {assignment, target, nested, assignment / "sibling"}
    preview = run_helper(repo, assignment, target)
    assert preview.returncode == 0
    assert preview.stdout.strip() == "PREVIEW_SAFE"
    assert {path for path in before if path.exists()} == before
    applied = run_helper(repo, assignment, target, "--apply")
    assert applied.returncode == 0
    assert applied.stdout.strip() == "REMOVED"
    assert not target.exists()
    assert assignment.is_dir()
    assert (assignment / "sibling").is_dir()


def test_absent_target_is_reported_without_touching_assignment(
    fixture_repo: tuple[Path, Path, Path],
) -> None:
    repo, assignment, target = fixture_repo
    (target / "nested").rmdir()
    target.rmdir()
    result = run_helper(repo, assignment, target, "--apply")
    assert result.returncode == 0
    assert result.stdout.strip() == "ALREADY_ABSENT"
    assert assignment.is_dir()


@pytest.mark.parametrize("actor", ["user", "rootish", ""])
def test_only_exact_root_actor_is_admitted(
    fixture_repo: tuple[Path, Path, Path], actor: str,
) -> None:
    repo, assignment, target = fixture_repo
    result = run_helper(repo, assignment, target, actor=actor)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "REFUSED" in result.stderr


@pytest.mark.parametrize(
    "assignment_text",
    [
        "relative-assignment",
        "../assignment-1",
    ],
)
def test_path_syntax_and_escape_are_refused(
    fixture_repo: tuple[Path, Path, Path], assignment_text: str,
) -> None:
    repo, assignment, target = fixture_repo
    result = run_helper(repo, assignment_text, target)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr

    escaped = run_helper(repo, assignment, repo.parent / "outside")
    assert escaped.returncode != 0
    assert "REFUSED" in escaped.stderr


def test_dot_pattern_and_canonical_alias_inputs_are_refused(
    fixture_repo: tuple[Path, Path, Path],
) -> None:
    repo, assignment, target = fixture_repo
    dotted = str(assignment.parent / ".." / assignment.parent.name / assignment.name)
    for raw in (dotted, str(assignment / "*")):
        result = run_helper(repo, raw, target)
        assert result.returncode != 0
        assert "REFUSED" in result.stderr


@pytest.mark.parametrize("broad", ["repo", "temp", "sessions", "owner"])
def test_broad_assignment_roots_are_refused(
    fixture_repo: tuple[Path, Path, Path], broad: str,
) -> None:
    repo, assignment, _target = fixture_repo
    paths = {
        "repo": repo,
        "temp": repo / "temp",
        "sessions": repo / "temp" / "sessions",
        "owner": repo / "temp" / "sessions" / "owner",
    }
    broad_root = paths[broad]
    broad_root.mkdir(parents=True, exist_ok=True)
    result = run_helper(repo, broad_root, broad_root)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr


@pytest.mark.parametrize("kind", ["file", "nonignored", "tracked"])
def test_file_and_content_targets_are_refused(
    fixture_repo: tuple[Path, Path, Path], kind: str,
) -> None:
    repo, assignment, target = fixture_repo
    if kind == "file":
        (target / "nested").rmdir()
        target.rmdir()
        target.write_text("not a directory\n", encoding="utf-8")
    elif kind == "nonignored":
        (target / "untracked.txt").write_text("content\n", encoding="utf-8")
    else:
        tracked = target / "tracked.txt"
        tracked.write_text("tracked\n", encoding="utf-8")
        git(repo, "add", str(tracked.relative_to(repo)))
        git(repo, "commit", "-m", "tracked target content")
    result = run_helper(repo, assignment, target)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr


def test_symlink_target_is_refused_when_supported(
    fixture_repo: tuple[Path, Path, Path],
) -> None:
    repo, assignment, target = fixture_repo
    outside = repo.parent / "outside"
    outside.mkdir()
    link = assignment / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory links are unavailable on this platform")
    result = run_helper(repo, assignment, link)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
