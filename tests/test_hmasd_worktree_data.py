"""Data retention checks use only temporary Git repositories and destinations."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from scripts import hmasd_worktree_data as data


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True,
                            text=True, capture_output=True)
    return result.stdout.strip()


@pytest.fixture
def worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / ".gitignore").write_text("runs/\ntemp/\nignored.bin\n.venv/\n")
    (repo / "modified.txt").write_text("original")
    (repo / "deleted.txt").write_text("deleted")
    git(repo, "add", ".gitignore", "modified.txt", "deleted.txt")
    git(repo, "commit", "-qm", "initial")
    source = tmp_path / "source"
    git(repo, "worktree", "add", "-qb", "side", str(source))
    dest = tmp_path / "durable"
    monkeypatch.setattr(data, "_process_check", lambda root, sudo: None)
    return repo, source, dest


def populate(source: Path) -> None:
    (source / "modified.txt").write_text("changed")
    (source / "deleted.txt").unlink()
    (source / "untracked.txt").write_text("untracked")
    (source / "ignored.bin").write_bytes(b"ignored")
    (source / "runs" / "d" / "partial").parent.mkdir(parents=True)
    (source / "runs" / "d" / "partial").write_bytes(b"failed-partial")
    (source / "temp").mkdir()
    (source / "temp" / "output").write_bytes(b"scratch-data")
    (source / "runs" / "__pycache__").mkdir()
    (source / "runs" / "__pycache__" / "skip.pyc").write_bytes(b"cache")
    (source / ".venv").mkdir()
    (source / ".venv" / "skip").write_bytes(b"cache")


def test_retains_dirty_ignored_partial_and_verifies_without_source(worktree: tuple[Path, Path, Path]) -> None:
    repo, source, dest = worktree
    populate(source)
    selected = data._selected(source)
    assert set(selected["files"]) == {
        "modified.txt", "untracked.txt", "ignored.bin", "runs/d/partial", "temp/output"
    }
    assert selected["deleted_tracked"] == ["deleted.txt"]
    assert data.main(["preview", "--root", str(source), "--dest", str(dest)]) == 0
    assert not dest.exists()
    assert data.main(["retain", "--root", str(source), "--dest", str(dest)]) == 0
    assert data._verify(dest)["verified"] == 5
    git(repo, "worktree", "remove", "--force", str(source))
    assert data.main(["verify", "--dest", str(dest)]) == 0


def test_destination_and_source_links_refused(worktree: tuple[Path, Path, Path], tmp_path: Path) -> None:
    _, source, dest = worktree
    (source / "link").symlink_to(source / "modified.txt")
    with pytest.raises(data.Refusal, match="symlink"):
        data._selected(source)
    (source / "link").unlink()
    redirected = tmp_path / "redirected"
    redirected.symlink_to(source, target_is_directory=True)
    with pytest.raises(data.Refusal, match="symlink"):
        data._destination(source, redirected / "data")
    with pytest.raises(data.Refusal, match="overlaps registered worktree"):
        data._destination(source, source / "backup")
    (source / "runs").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(data.Refusal, match="symlink"):
        data._selected(source)


def test_destination_ancestor_of_source_or_other_worktree_refused(
    worktree: tuple[Path, Path, Path]
) -> None:
    repo, source, dest = worktree
    nested = dest / "files"
    git(repo, "worktree", "add", "-qb", "nested", str(nested))
    with pytest.raises(data.Refusal, match="overlaps registered worktree"):
        data._destination(nested, dest)
    with pytest.raises(data.Refusal, match="overlaps registered worktree"):
        data._destination(source, dest)


def test_corruption_and_malicious_manifest_refused(worktree: tuple[Path, Path, Path]) -> None:
    _, source, dest = worktree
    populate(source)
    data._retain(source, dest, False)
    (dest / "files" / "ignored.bin").write_bytes(b"corrupt")
    with pytest.raises(data.Refusal, match="differs"):
        data._verify(dest)
    manifest = json.loads((dest / data.MANIFEST).read_text())
    manifest["files"]["../escape"] = manifest["files"].pop("ignored.bin")
    (dest / data.MANIFEST).write_text(json.dumps(manifest))
    with pytest.raises(data.Refusal, match="unsafe manifest path"):
        data._verify(dest)


def test_interrupted_copy_resumes_but_change_never_completes(
    worktree: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, source, dest = worktree
    populate(source)
    original = data._copy_one
    calls = 0

    def interrupt(src: Path, target: Path, expected: dict[str, object]) -> None:
        nonlocal calls
        original(src, target, expected)
        calls += 1
        if calls == 1:
            raise RuntimeError("interrupted")

    monkeypatch.setattr(data, "_copy_one", interrupt)
    with pytest.raises(RuntimeError, match="interrupted"):
        data._retain(source, dest, False)
    assert not (dest / data.MANIFEST).exists()
    monkeypatch.setattr(data, "_copy_one", original)
    data._retain(source, dest, False)
    assert data._verify(dest)["verified"] == 5

    other = dest.parent / "changed"

    def mutate(src: Path, target: Path, expected: dict[str, object]) -> None:
        original(src, target, expected)
        (source / "modified.txt").write_text("changed again")

    monkeypatch.setattr(data, "_copy_one", mutate)
    with pytest.raises(data.Refusal, match="source changed"):
        data._retain(source, other, False)
    assert not (other / data.MANIFEST).exists()


def test_live_process_and_missing_durable_ref(worktree: tuple[Path, Path, Path],
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    _, source, dest = worktree
    monkeypatch.undo()  # Exercise the actual process-check wrapper with a controlled scan.
    monkeypatch.setattr(data.gc, "_process_references", lambda root: ["pid 4321 cwd"])
    with pytest.raises(data.Refusal, match="live or uncertain"):
        data._process_check(source, False)
    git(source, "switch", "--detach", "-q")
    (source / "unique.txt").write_text("unreferenced commit")
    git(source, "add", "unique.txt")
    git(source, "commit", "-qm", "unique")
    with pytest.raises(data.Refusal, match="durable"):
        data._selected(source)
    assert not dest.exists()


def test_changed_tracked_and_nonignored_cache_named_files_are_kept(
    worktree: tuple[Path, Path, Path]
) -> None:
    _, source, _ = worktree
    (source / "__pycache__").mkdir()
    (source / "__pycache__" / "tracked.pyc").write_bytes(b"before")
    git(source, "add", "-f", "__pycache__/tracked.pyc")
    git(source, "commit", "-qm", "cache fixture")
    (source / "__pycache__" / "tracked.pyc").write_bytes(b"after")
    (source / "__pycache__" / "untracked.pyc").write_bytes(b"new")
    selected = data._selected(source)
    assert "__pycache__/tracked.pyc" in selected["files"]
    assert "__pycache__/untracked.pyc" in selected["files"]


@pytest.mark.parametrize("working", ["original", "third version"])
def test_staged_blob_refused_even_when_working_file_differs(
    worktree: tuple[Path, Path, Path], working: str
) -> None:
    _, source, dest = worktree
    path = source / "modified.txt"
    path.write_text("staged version")
    git(source, "add", "modified.txt")
    path.write_text(working)
    with pytest.raises(data.Refusal, match="index differs from HEAD"):
        data._retain(source, dest, False)
    assert not dest.exists()
