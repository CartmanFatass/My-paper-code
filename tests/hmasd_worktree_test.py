"""Phase 3 RED/GREEN contract tests for the HMASD worktree helper.

The cases deliberately use disposable repositories and explicit sibling
containers.  They exercise the public CLI rather than importing helper
internals, because Root and recovery callers are required to cross this
boundary through the documented commands.
"""

from __future__ import annotations
from contextlib import contextmanager

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_worktree.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hmasd_worktree" / "candidate_metadata.json"


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode:
        raise AssertionError((args, result.stdout, result.stderr))
    return result


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def payload(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(result.stdout)
    except ValueError as exc:  # pragma: no cover - keeps failures diagnosable
        raise AssertionError((result.returncode, result.stdout, result.stderr)) from exc
    assert isinstance(value, dict), value
    return value


def commit(cwd: Path, message: str) -> str:
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.name=HMASD Test", "-c", "user.email=hmasd@example.invalid", "commit", "-m", message)
    return git(cwd, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo_and_container(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    container = tmp_path / "explicit-worktrees"
    repo.mkdir()
    (repo / ".omp").mkdir()
    (repo / ".omp" / "AGENTS.md").write_text("# test\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".omp/runtime/\ntemp/\n*.ignored\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "owned.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(repo, "init", "-b", "omp/workflow")
    base = commit(repo, "base")
    assert len(base) in {40, 64}
    return repo, container


def provision(
    repo: Path,
    container: Path,
    assignment: str = "assignment-one",
    kind: str = "engineering",
) -> dict[str, Any]:
    base = git(repo, "rev-parse", "omp/workflow").stdout.strip()
    result = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(container),
        "--direction",
        "example-direction",
        "--kind",
        kind,
        "--assignment",
        assignment,
        "--base",
        base,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return payload(result)


def entry(result: dict[str, Any]) -> dict[str, Any]:
    value = result["worktree"]
    assert isinstance(value, dict)
    return value


def provision_orphan(
    repo: Path,
    container: Path,
    assignment: str,
) -> tuple[dict[str, Any], Path, Path]:
    provisioned = provision(repo, container, assignment)
    worktree = entry(provisioned)
    target = Path(worktree["canonical_absolute_path"])
    git(repo, "worktree", "remove", "--force", str(target))
    git(repo, "update-ref", "-d", f"refs/heads/{worktree['branch']}", worktree["base_sha"])

    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    row = next(item for item in registry["worktrees"] if item["worktree_ref"] == worktree["worktree_ref"])
    row["lifecycle"] = "PROVISIONING"
    registry["revision"] += 1
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt_path = Path(provisioned["receipt"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["lifecycle"] = "PROVISIONING"
    receipt["registry_revision"] = registry["revision"]
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dict(row), target, receipt_path


def prepared_candidate(
    repo: Path,
    container: Path,
    assignment: str,
    kind: str = "engineering",
) -> tuple[dict[str, Any], Path, str, Path]:
    worktree = entry(provision(repo, container, assignment, kind))
    path = Path(worktree["canonical_absolute_path"])
    (path / "src" / "owned.py").write_text(f"VALUE = {assignment!r}\n", encoding="utf-8")
    candidate = commit(path, "candidate")
    recorded = run_cli(
        repo,
        "record-candidate",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--candidate",
        candidate,
    )
    assert recorded.returncode == 0, (recorded.stdout, recorded.stderr)
    prepared = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src/owned.py",
    )
    assert prepared.returncode == 0, (prepared.stdout, prepared.stderr)
    return worktree, path, candidate, Path(payload(prepared)["receipt"])


def advance_registry(path: Path) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["revision"] += 1
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def test_clean_candidate_prepare_apply_and_release_once(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container)
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    path.joinpath("src", "owned.py").write_text("VALUE = 2\n", encoding="utf-8")
    candidate = commit(path, "candidate")
    recorded = run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate)
    assert recorded.returncode == 0, recorded.stderr
    prepared = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src/owned.py",
    )
    assert prepared.returncode == 0, prepared.stderr
    receipt = payload(prepared)["receipt"]
    assert payload(prepared)["verification_evidence"]["status"] == "MISSING"
    refused = run_cli(
        repo,
        "apply",
        "--receipt",
        receipt,
        "--actor",
        "em:example-direction",
    )
    assert refused.returncode == 5
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() != candidate
    applied = run_cli(
        repo,
        "apply",
        "--receipt",
        receipt,
        "--actor",
        "cm:example-direction",
    )
    assert applied.returncode == 0, applied.stderr
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == candidate
    second = run_cli(repo, "apply", "--receipt", receipt, "--actor", "root")
    assert second.returncode == 4
    released = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "root")
    assert released.returncode == 0, released.stderr
    assert not path.exists()
    assert git(repo, "show-ref", "--verify", "refs/heads/" + worktree["branch"], check=False).returncode != 0


def test_research_candidate_accepts_only_matching_em_actor(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree, path, candidate, receipt = prepared_candidate(
        repo,
        container,
        "research-actor",
        "research",
    )
    refused = run_cli(
        repo,
        "apply",
        "--receipt",
        str(receipt),
        "--actor",
        "cm:example-direction",
    )
    assert refused.returncode == 5
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() != candidate
    applied = run_cli(
        repo,
        "apply",
        "--receipt",
        str(receipt),
        "--actor",
        "em:example-direction",
    )
    assert applied.returncode == 0, applied.stderr
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == candidate
    released = run_cli(
        repo,
        "release",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--actor",
        "root",
    )
    assert released.returncode == 0, released.stderr
    assert not path.exists()


def test_default_container_uses_linux_sibling_root(repo_and_container: tuple[Path, Path]) -> None:
    repo, _ = repo_and_container
    base = git(repo, "rev-parse", "HEAD").stdout.strip()
    result = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--direction",
        "example-direction",
        "--kind",
        "research",
        "--assignment",
        "default-container",
        "--base",
        base,
    )
    assert result.returncode == 0, result.stderr
    path = Path(entry(payload(result))["canonical_absolute_path"])
    assert path.parent == repo.parent / f"{repo.name}-worktrees"
    run_cli(repo, "retain", "--worktree-ref", entry(payload(result))["worktree_ref"], "--actor", "root", "--reason", "test cleanup")
    shutil.rmtree(path, ignore_errors=True)


def test_canonical_path_escape_and_initial_symlink_container_refuse(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    outside = repo.parent / "outside"
    outside.mkdir()
    escaped = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(repo.parent / "explicit-worktrees" / ".." / "outside"),
        "--direction",
        "example-direction",
        "--kind",
        "engineering",
        "--assignment",
        "escape-case",
        "--base",
        git(repo, "rev-parse", "HEAD").stdout.strip(),
    )
    assert escaped.returncode in {2, 5}
    link = repo.parent / "container-link"
    link.symlink_to(outside, target_is_directory=True)

    symlinked = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(link),
        "--direction",
        "example-direction",
        "--kind",
        "engineering",
        "--assignment",
        "symlink-case",
        "--base",
        git(repo, "rev-parse", "HEAD").stdout.strip(),
    )
    assert symlinked.returncode == 5
    assert not (outside / "example-direction-engineering-symlink-case").exists()
def test_mid_provision_container_swap_fails_closed(repo_and_container: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    backup = container.with_name("swapped-container")
    original_run_git = worktree_module._run_git
    swapped = False

    def run_git(cwd: Path, *args: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal swapped
        result = original_run_git(cwd, *args, **kwargs)
        if not swapped and args[:3] == ("worktree", "add", "-b"):
            container.rename(backup)
            container.symlink_to(backup, target_is_directory=True)
            swapped = True
        return result

    monkeypatch.setattr(worktree_module, "_run_git", run_git)
    base = git(repo, "rev-parse", "HEAD").stdout.strip()
    with pytest.raises(worktree_module.WorktreeError) as failure:
        worktree_module.provision(str(repo), str(container), "example-direction", "engineering", "mid-swap", base)
    assert failure.value.code in {5, 6}
    if container.is_symlink():
        container.unlink()
    if backup.exists():
        backup.rename(container)


def test_target_preexisting_and_mid_provision_namespace_are_recoverable(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    target = container / "example-direction-engineering-target-exists"
    target.mkdir(parents=True)
    result = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(container),
        "--direction",
        "example-direction",
        "--kind",
        "engineering",
        "--assignment",
        "target-exists",
        "--base",
        git(repo, "rev-parse", "HEAD").stdout.strip(),
    )
    assert result.returncode == 5
    assert target.is_dir()


def test_target_outside_omp_namespace_is_refused(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    result = provision(repo, container, "outside-target")
    worktree = entry(result)
    path = Path(worktree["canonical_absolute_path"])
    run_cli(repo, "retain", "--worktree-ref", worktree["worktree_ref"], "--actor", "root", "--reason", "cleanup")
    bad = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "main",
        "--allowed-path",
        "src/owned.py",
    )
    assert bad.returncode in {5, 6}
    assert path.exists()


def test_dirty_worktree_and_extra_commit_are_rejected(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "dirty-case")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    target = path / "src" / "owned.py"
    target.write_text("dirty\n", encoding="utf-8")
    dirty = run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", git(path, "rev-parse", "HEAD").stdout.strip())
    assert dirty.returncode == 6
    candidate = commit(path, "candidate")
    target.write_text("second\n", encoding="utf-8")
    commit(path, "extra")
    extra = run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate)
    assert extra.returncode == 6


def test_allowed_path_and_symlink_escape_are_refused(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "allowlist-case")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "src" / "other.py").write_text("other\n", encoding="utf-8")
    candidate = commit(path, "out of scope")
    assert run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate).returncode == 0
    out_scope = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src/owned.py",
    )
    assert out_scope.returncode in {5, 6}

    provisioned = provision(repo, container, "symlink-change")
    second = entry(provisioned)
    second_path = Path(second["canonical_absolute_path"])
    (second_path / "src" / "escape").symlink_to(repo.parent, target_is_directory=True)
    candidate = commit(second_path, "tracked symlink")
    assert run_cli(repo, "record-candidate", "--worktree-ref", second["worktree_ref"], "--candidate", candidate).returncode == 0
    result = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        second["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src",
    )
    assert result.returncode in {5, 6}


def test_stale_base_target_advance_and_conflict_are_fail_closed(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "stale-case")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "src" / "owned.py").write_text("candidate\n", encoding="utf-8")
    candidate = commit(path, "candidate")
    assert run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate).returncode == 0
    prepared = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src/owned.py",
    )
    assert prepared.returncode == 0
    (repo / "src" / "owned.py").write_text("target advance\n", encoding="utf-8")
    target_advance = commit(repo, "target advance")
    assert target_advance != git(repo, "rev-parse", "HEAD~1").stdout.strip()
    applied = run_cli(repo, "apply", "--receipt", payload(prepared)["receipt"], "--actor", "root")
    assert applied.returncode == 4
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == target_advance


def test_release_registry_race_before_lock_has_no_git_or_path_effect(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "release-registry-race"))
    path = Path(worktree["canonical_absolute_path"])
    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    branch_before = git(repo, "rev-parse", worktree["branch"]).stdout.strip()
    original_lock = worktree_module._container_lock
    raced = False

    @contextmanager
    def racing_lock(candidate_container: Path) -> Any:
        nonlocal raced
        if not raced:
            advance_registry(registry_path)
            raced = True
        with original_lock(candidate_container) as identities:
            yield identities

    monkeypatch.setattr(worktree_module, "_container_lock", racing_lock)
    with pytest.raises(worktree_module.WorktreeError) as failure:
        worktree_module.release(str(repo), worktree["worktree_ref"], "root", "refuse")
    assert failure.value.code == 4
    assert path.is_dir()
    assert git(repo, "rev-parse", worktree["branch"]).stdout.strip() == branch_before
    current = json.loads(registry_path.read_text(encoding="utf-8"))
    current_entry = next(row for row in current["worktrees"] if row["worktree_ref"] == worktree["worktree_ref"])
    assert current_entry["lifecycle"] == "PROVISIONED"


def test_apply_receipt_race_before_lock_has_no_git_or_registry_effect(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    _, _, _, receipt_path = prepared_candidate(repo, container, "apply-receipt-race")
    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    registry_before = registry_path.read_bytes()
    target_before = git(repo, "rev-parse", "omp/workflow").stdout.strip()
    original_lock = worktree_module._container_lock
    raced = False

    @contextmanager
    def racing_lock(candidate_container: Path) -> Any:
        nonlocal raced
        if not raced:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            conflict = {"status": "CONFLICT", "detail": "concurrent receipt advance"}
            receipt["conflict"] = conflict
            receipt["facts"]["conflict"] = conflict
            receipt["facts_sha256"] = worktree_module._digest(receipt["facts"])
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raced = True
        with original_lock(candidate_container) as identities:
            yield identities

    monkeypatch.setattr(worktree_module, "_container_lock", racing_lock)
    with pytest.raises(worktree_module.WorktreeError):
        worktree_module.apply(str(receipt_path), "root")
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == target_before
    assert registry_path.read_bytes() == registry_before
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["conflict"]["status"] == "CONFLICT"


@pytest.mark.parametrize("advanced_fact", ["target", "registry"])
def test_apply_refuses_target_or_registry_advance_while_container_lock_is_held(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    advanced_fact: str,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    worktree, _, candidate, receipt_path = prepared_candidate(repo, container, f"locked-{advanced_fact}-race")
    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    target_before = git(repo, "rev-parse", "omp/workflow").stdout.strip()
    expected_target = target_before
    original_lock = worktree_module._container_lock
    raced = False

    @contextmanager
    def racing_lock(candidate_container: Path) -> Any:
        nonlocal expected_target, raced
        with original_lock(candidate_container) as identities:
            if not raced:
                if advanced_fact == "target":
                    (repo / "src" / "target-race.py").write_text("RACE = True\n", encoding="utf-8")
                    expected_target = commit(repo, "target advanced while container lock held")
                else:
                    advance_registry(registry_path)
                raced = True
            yield identities

    monkeypatch.setattr(worktree_module, "_container_lock", racing_lock)
    with pytest.raises(worktree_module.WorktreeError):
        worktree_module.apply(str(receipt_path), "root")
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == expected_target
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() != candidate
    current = json.loads(registry_path.read_text(encoding="utf-8"))
    current_entry = next(row for row in current["worktrees"] if row["worktree_ref"] == worktree["worktree_ref"])
    assert current_entry["lifecycle"] == "PREPARED_FOR_INTEGRATION"


def test_apply_post_effect_cas_failure_is_recoverably_journaled(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    worktree, _, candidate, receipt_path = prepared_candidate(repo, container, "apply-cas-race")
    original_replace = worktree_module._replace_registry
    injected = False

    def racing_replace(path: Path, state: dict[str, Any], expected_revision: int) -> dict[str, Any]:
        nonlocal injected
        if not injected and git(repo, "rev-parse", "omp/workflow").stdout.strip() == candidate:
            advance_registry(path)
            injected = True
        return original_replace(path, state, expected_revision)

    monkeypatch.setattr(worktree_module, "_replace_registry", racing_replace)
    with pytest.raises(worktree_module.UnknownApply):
        worktree_module.apply(str(receipt_path), "root")
    assert git(repo, "rev-parse", "omp/workflow").stdout.strip() == candidate
    registry = json.loads((repo / ".omp" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
    current = next(row for row in registry["worktrees"] if row["worktree_ref"] == worktree["worktree_ref"])
    assert current["lifecycle"] == "APPLY_OUTCOME_UNKNOWN"
    assert current["unknown_outcome"]["operation"] == "APPLY"
    assert current["unknown_outcome"]["observation"]["target_sha"] == candidate
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["apply_outcome"] == "UNKNOWN"
    assert receipt["unknown_outcome"]["registry_reconciliation"] == "RECORDED"
    with pytest.raises(worktree_module.UnsafeState) as inspection:
        worktree_module.inspect(str(repo), worktree["worktree_ref"])
    assert inspection.value.details["orphan_reason"] == "APPLY_OUTCOME_UNKNOWN"


def test_release_post_effect_cas_failure_is_recoverably_journaled(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    provisioned = provision(repo, container, "release-cas-race")
    worktree = entry(provisioned)
    target = Path(worktree["canonical_absolute_path"])
    receipt_path = Path(provisioned["receipt"])
    original_replace = worktree_module._replace_registry
    injected = False

    def racing_replace(path: Path, state: dict[str, Any], expected_revision: int) -> dict[str, Any]:
        nonlocal injected
        if not injected and not target.exists():
            advance_registry(path)
            injected = True
        return original_replace(path, state, expected_revision)

    monkeypatch.setattr(worktree_module, "_replace_registry", racing_replace)
    with pytest.raises(worktree_module.UnknownApply):
        worktree_module.release(str(repo), worktree["worktree_ref"], "root", "refuse")
    assert not target.exists()
    assert git(repo, "show-ref", "--verify", "refs/heads/" + worktree["branch"], check=False).returncode != 0
    registry = json.loads((repo / ".omp" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
    current = next(row for row in registry["worktrees"] if row["worktree_ref"] == worktree["worktree_ref"])
    assert current["lifecycle"] == "RELEASE_OUTCOME_UNKNOWN"
    assert current["unknown_outcome"]["operation"] == "RELEASE"
    assert current["unknown_outcome"]["observation"]["worktree_exists"] is False
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["release_outcome"] == "UNKNOWN"
    assert receipt["unknown_outcome"]["registry_reconciliation"] == "RECORDED"


def test_orphaned_provision_is_reported_exactly_and_not_duplicated(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "orphan-case")
    worktree = entry(provisioned)
    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    row = next(item for item in registry["worktrees"] if item["worktree_ref"] == worktree["worktree_ref"])
    row["lifecycle"] = "PROVISIONING"
    registry["revision"] += 1
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inspected = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 6
    detail = payload(inspected)
    assert detail["orphaned"] is True
    reconciled = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(container),
        "--direction",
        worktree["direction_id"],
        "--kind",
        worktree["kind"],
        "--assignment",
        worktree["assignment_id"],
        "--base",
        worktree["base_sha"],
    )
    assert reconciled.returncode == 0, reconciled.stderr
    assert payload(reconciled)["reconciled"] is True
    duplicate = run_cli(
        repo,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(container),
        "--direction",
        worktree["direction_id"],
        "--kind",
        worktree["kind"],
        "--assignment",
        worktree["assignment_id"],
        "--base",
        worktree["base_sha"],
    )
    assert duplicate.returncode == 6


def test_dirty_provision_records_paths_then_exact_orphan_recovery_succeeds(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    base = git(repo, "rev-parse", "HEAD").stdout.strip()
    original_status = worktree_module._status
    injected = False

    def dirty_once(path: Path) -> dict[str, list[str] | bool]:
        nonlocal injected
        if not injected:
            injected = True
            return {
                "tracked_dirty": ["src/owned.py"],
                "nonignored_untracked": ["scratch.txt"],
                "ignored_only": ["cache.ignored"],
                "clean": False,
            }
        return original_status(path)

    monkeypatch.setattr(worktree_module, "_status", dirty_once)
    with pytest.raises(worktree_module.UnsafeState):
        worktree_module.provision(
            str(repo),
            str(container),
            "example-direction",
            "engineering",
            "recover-dirty",
            base,
        )

    registry_path = repo / ".omp" / "runtime" / "worktrees.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["worktrees"]) == 1
    orphan = registry["worktrees"][0]
    token = orphan["operation_token"]
    target = Path(orphan["canonical_absolute_path"])
    receipt_path = repo / orphan["receipt_path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    failure = receipt["provision_failures"][-1]
    assert failure["phase"] == "POST_ADD_VALIDATION"
    assert failure["tracked_dirty"] == ["src/owned.py"]
    assert failure["nonignored_untracked"] == ["scratch.txt"]
    assert failure["ignored_only"] == ["cache.ignored"]
    assert failure["rollback"]["outcome"] == "COMPLETE"
    assert not target.exists()
    assert git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{orphan['branch']}", check=False).returncode != 0

    recovered = run_cli(
        repo,
        "recover-provision",
        "--repo",
        str(repo),
        "--worktree-ref",
        orphan["worktree_ref"],
    )
    assert recovered.returncode == 0, (recovered.stdout, recovered.stderr)
    recovered_payload = payload(recovered)
    assert recovered_payload["recovered"] is True
    assert recovered_payload["worktree"]["operation_token"] == token
    final_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(final_registry["worktrees"]) == 1
    final_row = final_registry["worktrees"][0]
    assert final_row["lifecycle"] == "PROVISIONED"
    assert final_row["operation_token"] == token
    assert git(target, "status", "--porcelain").stdout == ""
    assert git(repo, "worktree", "list", "--porcelain").stdout.count(f"worktree {target}\n") == 1
    final_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert final_receipt["operation_token"] == token
    assert final_receipt["recovered_at"] == final_receipt["provisioned_at"]
    assert final_receipt["provision_failures"][-1] == failure
    assert final_receipt["history"][-1]["event"] == "PROVISION_RECOVERED"

    duplicate = run_cli(
        repo,
        "recover-provision",
        "--repo",
        str(repo),
        "--worktree-ref",
        orphan["worktree_ref"],
    )
    assert duplicate.returncode == 6
    assert git(repo, "worktree", "list", "--porcelain").stdout.count(f"worktree {target}\n") == 1


@pytest.mark.parametrize("survivor", ["target", "branch", "registration", "unknown-outcome"])
def test_recover_provision_refuses_surviving_or_unknown_facts_without_effect(
    repo_and_container: tuple[Path, Path],
    survivor: str,
) -> None:
    repo, container = repo_and_container
    worktree, target, receipt_path = provision_orphan(repo, container, f"recover-refuse-{survivor}")
    if survivor == "target":
        target.mkdir()
    elif survivor == "branch":
        git(repo, "branch", worktree["branch"], worktree["base_sha"])
    elif survivor == "registration":
        git(repo, "worktree", "add", "-b", worktree["branch"], str(target), worktree["base_sha"])
    else:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["unknown_outcome"] = {"operation": "PROVISION", "outcome": "UNKNOWN"}
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    before_registrations = git(repo, "worktree", "list", "--porcelain").stdout
    before_branch = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{worktree['branch']}", check=False).stdout
    before_target = target.exists()
    refused = run_cli(
        repo,
        "recover-provision",
        "--repo",
        str(repo),
        "--worktree-ref",
        worktree["worktree_ref"],
    )
    assert refused.returncode == 6
    assert git(repo, "worktree", "list", "--porcelain").stdout == before_registrations
    assert git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{worktree['branch']}", check=False).stdout == before_branch
    assert target.exists() is before_target
    registry = json.loads((repo / ".omp" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
    current = next(item for item in registry["worktrees"] if item["worktree_ref"] == worktree["worktree_ref"])
    assert current["lifecycle"] == "PROVISIONING"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["last_failure"]["phase"] == "PREFLIGHT"
    assert receipt["last_failure"]["rollback"]["outcome"] == "NOT_ATTEMPTED"


def test_failed_recover_provision_rolls_back_only_its_effect_and_stays_diagnosable(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    worktree, target, receipt_path = provision_orphan(repo, container, "recover-fails")
    original_status = worktree_module._status
    injected = False

    def dirty_once(path: Path) -> dict[str, list[str] | bool]:
        nonlocal injected
        if not injected:
            injected = True
            return {
                "tracked_dirty": ["src/owned.py"],
                "nonignored_untracked": ["failed-recovery.txt"],
                "ignored_only": ["failed-recovery.ignored"],
                "clean": False,
            }
        return original_status(path)

    monkeypatch.setattr(worktree_module, "_status", dirty_once)
    with pytest.raises(worktree_module.UnsafeState):
        worktree_module.recover_provision(str(repo), worktree["worktree_ref"])

    registry = json.loads((repo / ".omp" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
    current = next(item for item in registry["worktrees"] if item["worktree_ref"] == worktree["worktree_ref"])
    assert current["lifecycle"] == "PROVISIONING"
    assert current["operation_token"] == worktree["operation_token"]
    assert not target.exists()
    assert git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{worktree['branch']}", check=False).returncode != 0
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    failure = receipt["last_failure"]
    assert failure["operation"] == "recover-provision"
    assert failure["phase"] == "POST_ADD_VALIDATION"
    assert failure["tracked_dirty"] == ["src/owned.py"]
    assert failure["nonignored_untracked"] == ["failed-recovery.txt"]
    assert failure["ignored_only"] == ["failed-recovery.ignored"]
    assert failure["rollback"]["outcome"] == "COMPLETE"
    inspected = run_cli(repo, "inspect", "--repo", str(repo), "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 6
    assert payload(inspected)["orphan_reason"] == "PROVISIONING_JOURNAL_WITHOUT_GIT_MUTATION"


def test_ignored_release_refuse_discard_and_retain(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "ignored-refuse")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "cache.ignored").write_text("cache\n", encoding="utf-8")
    refused = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "root")
    assert refused.returncode == 8
    discarded = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "root", "--ignored-artifacts", "discard")
    assert discarded.returncode == 0, discarded.stderr
    assert not path.exists()

    retained = provision(repo, container, "ignored-retain")
    retained_entry = entry(retained)
    retained_path = Path(retained_entry["canonical_absolute_path"])
    (retained_path / "cache.ignored").write_text("cache\n", encoding="utf-8")
    retained_result = run_cli(repo, "release", "--worktree-ref", retained_entry["worktree_ref"], "--actor", "root", "--ignored-artifacts", "retain")
    assert retained_result.returncode == 0
    assert retained_path.exists()
    inspected = run_cli(repo, "inspect", "--worktree-ref", retained_entry["worktree_ref"])
    assert inspected.returncode == 0
    assert payload(inspected)["worktree"]["lifecycle"] == "RETAINED_FOR_RECOVERY"


def test_nonignored_residue_and_actor_boundary_refuse_release(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "residue-case")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "untracked.txt").write_text("not ignored\n", encoding="utf-8")
    refused = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "not-root", "--ignored-artifacts", "discard")
    assert refused.returncode == 5
    refused = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "root", "--ignored-artifacts", "discard")
    assert refused.returncode == 6
    assert path.exists()


def test_retain_requires_reason_and_keeps_dirty_worktree(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "retain-dirty")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "dirty.txt").write_text("retain me\n", encoding="utf-8")
    missing_reason = run_cli(repo, "retain", "--worktree-ref", worktree["worktree_ref"], "--actor", "root", "--reason", "")
    assert missing_reason.returncode == 2
    retained = run_cli(repo, "retain", "--worktree-ref", worktree["worktree_ref"], "--actor", "root", "--reason", "preserve dirty recovery state")
    assert retained.returncode == 0, retained.stderr
    assert path.exists()
    assert payload(retained)["status"] == "RETAINED_FOR_RECOVERY"


def test_missing_verification_is_receipted_not_authority(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provisioned = provision(repo, container, "missing-evidence")
    worktree = entry(provisioned)
    path = Path(worktree["canonical_absolute_path"])
    (path / "src" / "owned.py").write_text("evidence-independent\n", encoding="utf-8")
    candidate = commit(path, "candidate")
    assert run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate).returncode == 0
    prepared = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "omp/workflow",
        "--allowed-path",
        "src/owned.py",
        "--verification-ref",
        "temp/missing-verification.json",
    )
    assert prepared.returncode == 0, prepared.stderr
    evidence = payload(prepared)["verification_evidence"]
    assert evidence["status"] == "MISSING"
    assert evidence["missing"] == ["temp/missing-verification.json"]


def test_fixture_declares_candidate_contract() -> None:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert value == {
        "allowed_paths": ["src/owned.py"],
        "assignment": "assignment-one",
        "direction": "example-direction",
        "kind": "engineering",
    }
