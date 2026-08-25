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


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink privilege is unavailable")
        raise


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


def test_native_path_comparison_matches_windows_case_insensitivity() -> None:
    from scripts import hmasd_worktree

    if os.name == "nt":
        assert hmasd_worktree._same_path(Path("C:/Projects/HMASD"), Path("c:/projects/hmasd"))
    else:
        assert not hmasd_worktree._same_path(Path("/tmp/HMASD"), Path("/tmp/hmasd"))


def test_windows_rejects_posix_absolute_worktree_paths_with_actionable_error() -> None:
    from scripts import hmasd_worktree

    if os.name != "nt":
        pytest.skip("POSIX hosts accept POSIX absolute paths")
    with pytest.raises(hmasd_worktree.InvalidInput, match="POSIX/WSL"):
        hmasd_worktree._lexical_absolute("/mnt/c/Projects/HMASD-worktrees", label="container")


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
    (repo / ".gitignore").write_text(".omp/runtime/\n.codex/runtime/\ntemp/\n*.ignored\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "owned.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(repo, "init", "-b", "main")
    base = commit(repo, "base")
    assert len(base) in {40, 64}
    return repo, container


def provision(repo: Path, container: Path, assignment: str = "assignment-one") -> dict[str, Any]:
    base = git(repo, "rev-parse", "main").stdout.strip()
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


def prepared_candidate(
    repo: Path,
    container: Path,
    assignment: str,
) -> tuple[dict[str, Any], Path, str, Path]:
    worktree = entry(provision(repo, container, assignment))
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
        "main",
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
        "main",
        "--allowed-path",
        "src/owned.py",
    )
    assert prepared.returncode == 0, prepared.stderr
    receipt = payload(prepared)["receipt"]
    assert payload(prepared)["verification_evidence"]["status"] == "MISSING"
    applied = run_cli(repo, "apply", "--receipt", receipt, "--actor", "root")
    assert applied.returncode == 0, applied.stderr
    assert git(repo, "rev-parse", "main").stdout.strip() == candidate
    second = run_cli(repo, "apply", "--receipt", receipt, "--actor", "root")
    assert second.returncode == 4
    released = run_cli(repo, "release", "--worktree-ref", worktree["worktree_ref"], "--actor", "root")
    assert released.returncode == 0, released.stderr
    assert not path.exists()
    assert git(repo, "show-ref", "--verify", "refs/heads/" + worktree["branch"], check=False).returncode != 0


def test_default_container_uses_native_sibling_root(repo_and_container: tuple[Path, Path]) -> None:
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


def test_fresh_worktree_journal_is_codex_owned(repo_and_container: tuple[Path, Path]) -> None:
    repo, container = repo_and_container
    provision(repo, container, "fresh-codex-journal")
    canonical = repo / ".codex" / "runtime" / "worktrees.json"
    legacy = repo / ".omp" / "runtime" / "worktrees.json"
    assert canonical.is_file()
    assert not legacy.exists()


def test_canonical_worktree_operation_survives_missing_omp_control(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "no-legacy-control"))
    # The real repository retains root AGENTS.md after the OMP tree is retired;
    # provide the same Codex identity marker in this minimal fixture.
    (repo / "AGENTS.md").write_text("# Codex control marker\n", encoding="utf-8")
    shutil.rmtree(repo / ".omp")

    inspected = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 0, (inspected.stdout, inspected.stderr)
    assert not (repo / ".omp").exists()


def test_canonical_operation_ignores_omp_runtime_residue_without_control_markers(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "legacy-runtime-residue"))
    (repo / "AGENTS.md").write_text("# Codex control marker\n", encoding="utf-8")
    shutil.rmtree(repo / ".omp")
    locks = repo / ".omp" / "runtime" / "locks"
    locks.mkdir(parents=True)
    (locks / "retired.lock").write_text("1", encoding="utf-8")

    inspected = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 0, (inspected.stdout, inspected.stderr)
    assert (locks / "retired.lock").read_text(encoding="utf-8") == "1"


def test_legacy_only_journal_is_validated_imported_once_and_left_read_only(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "legacy-import"))
    canonical = repo / ".codex" / "runtime" / "worktrees.json"
    legacy = repo / ".omp" / "runtime" / "worktrees.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(canonical.read_bytes())
    legacy_bytes = legacy.read_bytes()
    canonical.unlink()

    inspected = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 0, (inspected.stdout, inspected.stderr)
    assert canonical.is_file()
    assert legacy.read_bytes() == legacy_bytes
    assert payload(inspected)["worktree"]["worktree_ref"] == worktree["worktree_ref"]


def test_imported_journal_allows_canonical_progress_without_legacy_write(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "import-progress"))
    canonical = repo / ".codex" / "runtime" / "worktrees.json"
    legacy = repo / ".omp" / "runtime" / "worktrees.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(canonical.read_bytes())
    canonical.unlink()

    imported = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert imported.returncode == 0, (imported.stdout, imported.stderr)
    legacy_bytes = legacy.read_bytes()
    legacy_revision = json.loads(legacy_bytes)["revision"]

    progressed = run_cli(
        repo,
        "retain",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--actor",
        "root",
        "--reason",
        "preserve post-import state",
    )
    assert progressed.returncode == 0, (progressed.stdout, progressed.stderr)
    canonical_document = json.loads(canonical.read_text(encoding="utf-8"))
    assert canonical_document["revision"] > legacy_revision
    assert legacy.read_bytes() == legacy_bytes

    inspected = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert inspected.returncode == 0, (inspected.stdout, inspected.stderr)


def test_legacy_import_refuses_stale_receipt_before_creating_canonical(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "legacy-stale-receipt"))
    canonical = repo / ".codex" / "runtime" / "worktrees.json"
    legacy = repo / ".omp" / "runtime" / "worktrees.json"
    legacy.parent.mkdir(parents=True)
    document = json.loads(canonical.read_text(encoding="utf-8"))
    document["worktrees"][0]["canonical_absolute_path"] = str(
        Path(worktree["canonical_absolute_path"]).with_name("wrong-worktree-path")
    )
    legacy.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    canonical.unlink()

    refused = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert refused.returncode == 5
    assert not canonical.exists()


def test_dual_journal_agreement_then_conflict_fails_closed(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "dual-journal"))
    canonical = repo / ".codex" / "runtime" / "worktrees.json"
    legacy = repo / ".omp" / "runtime" / "worktrees.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(canonical.read_bytes())

    agreement = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert agreement.returncode == 0, (agreement.stdout, agreement.stderr)

    conflicting = json.loads(legacy.read_text(encoding="utf-8"))
    conflicting["worktrees"][0]["lifecycle"] = "CANDIDATE_READY"
    legacy.write_text(json.dumps(conflicting, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    same_revision_conflict = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert same_revision_conflict.returncode == 6
    assert "conflict" in payload(same_revision_conflict)["error"]

    conflicting = json.loads(canonical.read_text(encoding="utf-8"))
    conflicting["revision"] += 1
    legacy.write_text(json.dumps(conflicting, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    refused = run_cli(repo, "inspect", "--worktree-ref", worktree["worktree_ref"])
    assert refused.returncode == 6
    assert "conflict" in payload(refused)["error"]


def test_codex_runtime_reparse_alias_is_refused(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    outside = repo.parent / "codex-runtime-outside"
    outside.mkdir()
    codex = repo / ".codex"
    _symlink_or_skip(codex, outside, target_is_directory=True)
    refused = run_cli(
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
        "codex-reparse",
        "--base",
        git(repo, "rev-parse", "HEAD").stdout.strip(),
    )
    assert refused.returncode == 5


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
    _symlink_or_skip(link, outside, target_is_directory=True)

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
            _symlink_or_skip(container, backup, target_is_directory=True)
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


def test_target_other_than_main_is_refused(repo_and_container: tuple[Path, Path]) -> None:
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
        "omp/workflow",
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
        "main",
        "--allowed-path",
        "src/owned.py",
    )
    assert out_scope.returncode in {5, 6}

    provisioned = provision(repo, container, "symlink-change")
    second = entry(provisioned)
    second_path = Path(second["canonical_absolute_path"])
    _symlink_or_skip(
        second_path / "src" / "escape", repo.parent, target_is_directory=True
    )
    candidate = commit(second_path, "tracked symlink")
    assert run_cli(repo, "record-candidate", "--worktree-ref", second["worktree_ref"], "--candidate", candidate).returncode == 0
    result = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        second["worktree_ref"],
        "--target",
        "main",
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
        "main",
        "--allowed-path",
        "src/owned.py",
    )
    assert prepared.returncode == 0
    (repo / "src" / "owned.py").write_text("target advance\n", encoding="utf-8")
    target_advance = commit(repo, "target advance")
    assert target_advance != git(repo, "rev-parse", "HEAD~1").stdout.strip()
    applied = run_cli(repo, "apply", "--receipt", payload(prepared)["receipt"], "--actor", "root")
    assert applied.returncode == 4
    assert git(repo, "rev-parse", "main").stdout.strip() == target_advance


def test_release_registry_race_before_lock_has_no_git_or_path_effect(
    repo_and_container: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, container = repo_and_container
    worktree = entry(provision(repo, container, "release-registry-race"))
    path = Path(worktree["canonical_absolute_path"])
    registry_path = repo / ".codex" / "runtime" / "worktrees.json"
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
    registry_path = repo / ".codex" / "runtime" / "worktrees.json"
    registry_before = registry_path.read_bytes()
    target_before = git(repo, "rev-parse", "main").stdout.strip()
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
    assert git(repo, "rev-parse", "main").stdout.strip() == target_before
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
    registry_path = repo / ".codex" / "runtime" / "worktrees.json"
    target_before = git(repo, "rev-parse", "main").stdout.strip()
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
    assert git(repo, "rev-parse", "main").stdout.strip() == expected_target
    assert git(repo, "rev-parse", "main").stdout.strip() != candidate
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
        if not injected and git(repo, "rev-parse", "main").stdout.strip() == candidate:
            advance_registry(path)
            injected = True
        return original_replace(path, state, expected_revision)

    monkeypatch.setattr(worktree_module, "_replace_registry", racing_replace)
    with pytest.raises(worktree_module.UnknownApply):
        worktree_module.apply(str(receipt_path), "root")
    assert git(repo, "rev-parse", "main").stdout.strip() == candidate
    registry = json.loads((repo / ".codex" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
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
    registry = json.loads((repo / ".codex" / "runtime" / "worktrees.json").read_text(encoding="utf-8"))
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
    registry_path = repo / ".codex" / "runtime" / "worktrees.json"
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
        "main",
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


def _write_path_policy(repo: Path, rules: list[dict[str, str]]) -> Path:
    path = repo / "docs" / "project" / "git-path-policy-v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "default_classification": "shared-core",
                "rules": rules,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_path_policy_ordered_exact_prefix_default_and_alias_refusal(repo_and_container: tuple[Path, Path]) -> None:
    from scripts import hmasd_worktree as worktree_module

    repo, _ = repo_and_container
    policy = {
        "schema_version": 1,
        "default_classification": "shared-core",
        "rules": [
            {"type": "prefix", "path": "src", "classification": "direction-owned"},
            {"type": "exact", "path": "src/owned.py", "classification": "shared-core"},
        ],
    }
    assert worktree_module.classify_path("src/owned.py", policy) == "direction-owned"
    assert worktree_module.classify_path("unmatched/file.py", policy) == "shared-core"
    with pytest.raises(worktree_module.OwnershipRefusal):
        worktree_module.classify_path("src/../owned.py", policy)

    _write_path_policy(
        repo,
        [{"type": "prefix", "path": "../escaped", "classification": "direction-owned"}],
    )
    with pytest.raises(worktree_module.OwnershipRefusal):
        worktree_module._load_path_policy(repo)


def test_policy_classification_is_receipted_but_cannot_bypass_assignment_allowlist(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    _write_path_policy(
        repo,
        [
            {"type": "exact", "path": "src/owned.py", "classification": "shared-core"},
            {"type": "prefix", "path": "src", "classification": "direction-owned"},
        ],
    )
    commit(repo, "path policy")
    worktree = entry(provision(repo, container, "policy-receipt"))
    path = Path(worktree["canonical_absolute_path"])
    (path / "src" / "owned.py").write_text("VALUE = 'policy'\n", encoding="utf-8")
    candidate = commit(path, "candidate")
    assert run_cli(repo, "record-candidate", "--worktree-ref", worktree["worktree_ref"], "--candidate", candidate).returncode == 0
    prepared = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        worktree["worktree_ref"],
        "--target",
        "main",
        "--allowed-path",
        "src",
    )
    assert prepared.returncode == 0, prepared.stderr
    receipt = Path(payload(prepared)["receipt"])
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert document["path_classifications"] == [
        {"path": "src/owned.py", "classification": "shared-core"}
    ]

    # The classification is provenance, never a substitute for the existing
    # assignment allowlist.
    other = entry(provision(repo, container, "policy-allowlist"))
    other_path = Path(other["canonical_absolute_path"])
    (other_path / "src" / "owned.py").write_text("VALUE = 'blocked'\n", encoding="utf-8")
    other_candidate = commit(other_path, "candidate")
    assert run_cli(repo, "record-candidate", "--worktree-ref", other["worktree_ref"], "--candidate", other_candidate).returncode == 0
    refused = run_cli(
        repo,
        "prepare-integration",
        "--worktree-ref",
        other["worktree_ref"],
        "--target",
        "main",
        "--allowed-path",
        "experiments/candidates",
    )
    assert refused.returncode in {5, 6}


def test_receipt_rejects_policy_field_tamper_and_policy_fact_advance(
    repo_and_container: tuple[Path, Path],
) -> None:
    repo, container = repo_and_container
    policy_path = _write_path_policy(
        repo,
        [{"type": "prefix", "path": "src", "classification": "direction-owned"}],
    )
    commit(repo, "path policy")
    _, _, _, receipt_path = prepared_candidate(repo, container, "policy-tamper")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["path_policy_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tampered = run_cli(repo, "apply", "--receipt", str(receipt_path), "--actor", "root")
    assert tampered.returncode == 2

    # Restore a freshly prepared receipt, then advance only the versioned
    # policy.  Applying must re-read and reject changed policy facts.
    _, _, _, fresh_receipt = prepared_candidate(repo, container, "policy-advance")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["rules"][0]["classification"] = "shared-core"
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    commit(repo, "path policy advanced")
    advanced = run_cli(repo, "apply", "--receipt", str(fresh_receipt), "--actor", "root")
    assert advanced.returncode == 4
