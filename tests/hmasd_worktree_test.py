"""Focused current-only tests for prospective worktree and candidate mechanics."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts import hmasd_state
from scripts import hmasd_worktree as worktree


def git(cwd: Path, *args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(hmasd_state.canonical_bytes(value))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def lease(repo: Path, assignment: str, clerk_assignment: str) -> dict[str, Any]:
    handoff = repo / "handoffs" / f"{clerk_assignment}.json"
    write_json(handoff, {"assignment_id": assignment, "terminal": True})
    return {
        "manager_assignment_id": assignment,
        "clerk_assignment_id": clerk_assignment,
        "handoff_ref": {
            "path": handoff.relative_to(repo).as_posix(),
            "sha256": sha256(handoff),
        },
        "lease_token": hashlib.sha256(f"lease:{clerk_assignment}".encode()).hexdigest(),
    }


def expected(
    repo: Path,
    container: Path,
    entry: dict[str, Any] | None,
    revision: int,
    lifecycle: str,
    receipt: Path | None,
    *,
    worktree_path: Path,
) -> dict[str, Any]:
    return {
        "registry_revision": revision,
        "lifecycle": lifecycle,
        "worktree_path": str(worktree_path),
        "container_path": str(container),
        "receipt_sha256": sha256(receipt) if receipt is not None else None,
    }


def provision_exact(
    repo: Path,
    container: Path,
    base: str,
    *,
    direction: str = "example",
    assignment: str = "assignment-one",
    clerk_assignment: str = "provision-clerk",
) -> tuple[dict[str, Any], Path, Path]:
    target = container / f"{direction}-engineering-{assignment}"
    result = worktree.provision(
        str(repo),
        str(container),
        direction,
        "engineering",
        assignment,
        base,
        "EXACT_HANDOFF",
        None,
        base,
        [],
        lease(repo, assignment, clerk_assignment),
        {
            "registry_revision": 1,
            "lifecycle": "ABSENT",
            "worktree_path": str(target),
            "container_path": str(container),
            "receipt_sha256": None,
        },
    )
    entry = result["worktree"]
    entry["_registry_revision"] = result["registry_revision"]
    receipt = repo / entry["receipt_path"]
    return entry, target, receipt


def patch_file(repo: Path) -> Path:
    patch = repo / "packets" / "candidate.patch"
    patch.parent.mkdir(parents=True, exist_ok=True)
    patch.write_text(
        """diff --git a/owned-a.txt b/owned-a.txt
--- a/owned-a.txt
+++ b/owned-a.txt
@@ -1 +1 @@
-old-a
+new-a
diff --git a/owned-b.txt b/owned-b.txt
--- a/owned-b.txt
+++ b/owned-b.txt
@@ -1 +1 @@
-old-b
+new-b
""",
        encoding="utf-8",
    )
    return patch


def prospective_tree(repo: Path, base: str, patch: Path, index: Path) -> str:
    env = {"GIT_INDEX_FILE": str(index)}
    git(repo, "read-tree", base, env=env)
    git(repo, "apply", "--cached", str(patch), env=env)
    return git(repo, "write-tree", env=env).stdout.strip()


def checkout_snapshot(path: Path) -> dict[str, Any]:
    index_raw = git(path, "rev-parse", "--git-path", "index").stdout.strip()
    index = Path(index_raw)
    if not index.is_absolute():
        index = path / index
    files: dict[str, tuple[int, bytes]] = {}
    for candidate in sorted(path.rglob("*")):
        relative = candidate.relative_to(path).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        info = candidate.lstat()
        if stat.S_ISREG(info.st_mode):
            files[relative] = (stat.S_IMODE(info.st_mode), candidate.read_bytes())
        elif stat.S_ISDIR(info.st_mode):
            files[relative + "/"] = (stat.S_IMODE(info.st_mode), b"")
    return {
        "head": git(path, "rev-parse", "HEAD").stdout.strip(),
        "index_tree": git(path, "write-tree").stdout.strip(),
        "index_bytes": index.read_bytes(),
        "status": git(path, "status", "--porcelain=v1", "--untracked-files=all").stdout,
        "files": files,
    }


def prepare_patch(
    repo: Path,
    container: Path,
    entry: dict[str, Any],
    target: Path,
    receipt: Path,
    base: str,
    patch: Path,
    tree: str,
    *,
    clerk_assignment: str = "patch-clerk",
) -> dict[str, Any]:
    delta = worktree._canonical_tree_delta(repo, base, tree)
    return worktree.apply_patch(
        str(repo),
        entry["worktree_ref"],
        base,
        git(repo, "rev-parse", f"{base}^{{tree}}").stdout.strip(),
        str(patch),
        sha256(patch),
        ["owned-b.txt", "owned-a.txt"],
        ["owned-b.txt", "owned-a.txt"],
        delta["sha256"],
        tree,
        lease(repo, entry["assignment_id"], clerk_assignment),
        expected(
            repo,
            container,
            entry,
            entry["_registry_revision"],
            "PROVISIONED",
            receipt,
            worktree_path=target,
        ),
    )


def test_policy_and_registry_are_current_only(tmp_path: Path) -> None:
    repo, _base = init_repo(tmp_path)
    with pytest.raises(worktree.InvalidInput):
        worktree._validate_integration_policy(None)
    with pytest.raises(worktree.InvalidInput):
        worktree._validate_integration_policy("OBSOLETE_EXACT_POLICY")
    assert worktree._validate_integration_policy("EXACT_HANDOFF") == "EXACT_HANDOFF"
    assert worktree._validate_integration_policy("ORTHOGONAL_DIRECTION") == "ORTHOGONAL_DIRECTION"

    registry = repo / ".omp" / "runtime" / "worktrees.json"
    write_json(
        registry,
        {
            "schema_version": 1,
            "revision": 1,
            "updated_at": "2026-08-30T00:00:00Z",
            "writer": "Root",
            "worktrees": [],
        },
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


def test_patch_is_prospective_and_candidate_ref_does_not_change_checkout(tmp_path: Path) -> None:
    repo, base = init_repo(tmp_path)
    container = tmp_path / "worktrees"
    entry, target, receipt = provision_exact(repo, container, base)
    patch = patch_file(repo)
    tree = prospective_tree(repo, base, patch, tmp_path / "prospective.index")
    before_patch = checkout_snapshot(target)

    patched = prepare_patch(repo, container, entry, target, receipt, base, patch, tree)

    assert checkout_snapshot(target) == before_patch
    prepared_ref = patched["prepared_tree_receipt_ref"]
    prepared_path = repo / prepared_ref["path"]
    assert sha256(prepared_path) == prepared_ref["sha256"]
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    assert prepared["result_tree_sha"] == tree
    assert prepared["changed_paths"] == ["owned-a.txt", "owned-b.txt"]

    metadata = repo / "packets" / "candidate-metadata.json"
    write_json(
        metadata,
        {
            "schema": worktree.CANDIDATE_METADATA_SCHEMA,
            "author_name": "HMASD Test",
            "author_email": "hmasd@example.invalid",
            "author_date": "2026-08-30T00:00:00Z",
            "committer_name": "HMASD Test",
            "committer_email": "hmasd@example.invalid",
            "committer_date": "2026-08-30T00:00:00Z",
            "message": "candidate\n",
        },
    )
    patched_entry = patched["worktree"]
    candidate = worktree.create_candidate(
        str(repo),
        patched_entry["worktree_ref"],
        base,
        str(prepared_path),
        prepared_ref["sha256"],
        ["owned-b.txt", "owned-a.txt"],
        ["owned-b.txt", "owned-a.txt"],
        patched["diff_sha256"],
        tree,
        str(metadata),
        sha256(metadata),
        lease(repo, patched_entry["assignment_id"], "candidate-clerk"),
        expected(
            repo,
            container,
            patched_entry,
            patched["registry_revision"],
            "PATCHED",
            receipt,
            worktree_path=target,
        ),
    )
    assert checkout_snapshot(target) == before_patch
    candidate_sha = candidate["candidate_sha"]
    assert git(repo, "rev-list", "--parents", "-n", "1", candidate_sha).stdout.split() == [
        candidate_sha,
        base,
    ]
    assert git(repo, "rev-parse", f"{candidate_sha}^{{tree}}").stdout.strip() == tree
    assert git(repo, "rev-parse", candidate["candidate_ref"]).stdout.strip() == candidate_sha
    assert git(target, "rev-parse", "HEAD").stdout.strip() == base

    candidate_entry = candidate["worktree"]
    inspected = worktree.inspect(
        str(repo),
        candidate_entry["worktree_ref"],
        expected(
            repo,
            container,
            candidate_entry,
            candidate["registry_revision"],
            "CANDIDATE_READY",
            receipt,
            worktree_path=target,
        ),
    )
    assert inspected["orphaned"] is False
    assert inspected["observation"]["registration_head"] == base

    recorded = worktree.record_candidate(
        str(repo),
        candidate_entry["worktree_ref"],
        candidate_sha,
        lease(repo, candidate_entry["assignment_id"], "record-clerk"),
        expected(
            repo,
            container,
            candidate_entry,
            candidate["registry_revision"],
            "CANDIDATE_READY",
            receipt,
            worktree_path=target,
        ),
    )
    assert recorded["candidate_sha"] == candidate_sha
    assert checkout_snapshot(target) == before_patch


def test_patch_failure_never_needs_rollback_and_leaves_checkout_registry_receipt_unchanged(tmp_path: Path) -> None:
    repo, base = init_repo(tmp_path)
    container = tmp_path / "worktrees"
    entry, target, receipt = provision_exact(
        repo, container, base, assignment="failure-assignment"
    )
    bad_patch = repo / "packets" / "bad.patch"
    bad_patch.parent.mkdir(parents=True, exist_ok=True)
    bad_patch.write_text(
        """diff --git a/owned-a.txt b/owned-a.txt
--- a/owned-a.txt
+++ b/owned-a.txt
@@ -1 +1 @@
-old-a
+new-a
diff --git a/owned-b.txt b/owned-b.txt
--- a/owned-b.txt
+++ b/owned-b.txt
@@ -1 +1 @@
-not-the-preimage
+new-b
""",
        encoding="utf-8",
    )
    checkout_before = checkout_snapshot(target)
    registry = repo / ".omp" / "runtime" / "worktrees.json"
    registry_before = registry.read_bytes()
    receipt_before = receipt.read_bytes()
    patch_before = bad_patch.read_bytes()
    with pytest.raises(worktree.WorktreeError):
        worktree.apply_patch(
            str(repo),
            entry["worktree_ref"],
            base,
            git(repo, "rev-parse", f"{base}^{{tree}}").stdout.strip(),
            str(bad_patch),
            sha256(bad_patch),
            ["owned-a.txt", "owned-b.txt"],
            ["owned-a.txt", "owned-b.txt"],
            "0" * 64,
            git(repo, "rev-parse", f"{base}^{{tree}}").stdout.strip(),
            lease(repo, entry["assignment_id"], "bad-patch-clerk"),
            expected(
                repo,
                container,
                entry,
                entry["_registry_revision"],
                "PROVISIONED",
                receipt,
                worktree_path=target,
            ),
        )
    assert checkout_snapshot(target) == checkout_before
    assert registry.read_bytes() == registry_before
    assert receipt.read_bytes() == receipt_before
    assert bad_patch.read_bytes() == patch_before


@pytest.mark.parametrize(
    ("disposition", "expected_status", "exists"),
    [("discard", "RELEASED", False), ("retain", "RETAINED_FOR_RECOVERY", True)],
)
def test_release_dispositions_are_exact(
    tmp_path: Path,
    disposition: str,
    expected_status: str,
    exists: bool,
) -> None:
    repo, base = init_repo(tmp_path)
    container = tmp_path / "worktrees"
    entry, target, receipt = provision_exact(
        repo,
        container,
        base,
        assignment=f"release-{disposition}",
        clerk_assignment=f"provision-{disposition}",
    )
    result = worktree.release(
        str(repo),
        entry["worktree_ref"],
        "root",
        disposition,
        lease(repo, entry["assignment_id"], f"release-{disposition}-clerk"),
        expected(
            repo,
            container,
            entry,
            entry["_registry_revision"],
            "PROVISIONED",
            receipt,
            worktree_path=target,
        ),
    )
    assert result["status"] == expected_status
    assert result["worktree"]["lifecycle"] == expected_status
    assert target.exists() is exists


def test_post_prospective_registry_failure_still_leaves_checkout_byte_identical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base = init_repo(tmp_path)
    container = tmp_path / "worktrees"
    entry, target, receipt = provision_exact(
        repo, container, base, assignment="post-proof-failure"
    )
    patch = patch_file(repo)
    tree = prospective_tree(repo, base, patch, tmp_path / "failure.index")
    registry = repo / ".omp" / "runtime" / "worktrees.json"
    before = (checkout_snapshot(target), registry.read_bytes(), receipt.read_bytes())

    def fail_registry(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("injected registry failure after prospective proof")

    monkeypatch.setattr(worktree, "_replace_registry_observed", fail_registry)
    with pytest.raises(RuntimeError, match="injected registry failure"):
        prepare_patch(repo, container, entry, target, receipt, base, patch, tree)

    assert (
        checkout_snapshot(target),
        registry.read_bytes(),
        receipt.read_bytes(),
    ) == before
    assert patch.is_file()


def test_release_refuse_is_zero_effect(tmp_path: Path) -> None:
    repo, base = init_repo(tmp_path)
    container = tmp_path / "worktrees"
    entry, target, receipt = provision_exact(
        repo, container, base, assignment="release-refuse"
    )
    registry = repo / ".omp" / "runtime" / "worktrees.json"
    before = (checkout_snapshot(target), registry.read_bytes(), receipt.read_bytes())
    with pytest.raises(worktree.DecisionRequired):
        worktree.release(
            str(repo),
            entry["worktree_ref"],
            "root",
            "refuse",
            lease(repo, entry["assignment_id"], "release-refuse-clerk"),
            expected(
                repo,
                container,
                entry,
                entry["_registry_revision"],
                "PROVISIONED",
                receipt,
                worktree_path=target,
            ),
        )
    assert (checkout_snapshot(target), registry.read_bytes(), receipt.read_bytes()) == before
