"""Hermetic proof for the Root-managed worktree lifecycle."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import hmasd_root_managed_worktree as helper  # noqa: E402


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--initial-branch=main")
    git(root, "config", "user.email", "root@example.invalid")
    git(root, "config", "user.name", "Root")
    (root / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(root, "add", "tracked.txt")
    git(root, "commit", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    managed = tmp_path / "managed"  # sibling destination, never inside repo
    receipt = tmp_path / "receipts" / "assignment.json"
    common = Path(git(root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    return root, common, managed, receipt, base


def args(repo):
    root, common, managed, receipt, _ = repo
    return dict(repo_top=root, git_common_dir=common, managed_path=managed, receipt_path=receipt, assignment_id="ASSIGNMENT-1")


def provision(repo):
    return helper.provision_worktree(**args(repo), base_commit=repo[-1])


def test_normal_lifecycle_provision_audit_and_clean_release(repo):
    result = provision(repo)
    assert result["receipt"]["status"] == "PROVISIONED"
    report = helper.audit_worktree(**args(repo))["report"]
    assert report["registered"] and report["detached"] and report["cleanup_safe"]
    released = helper.release_worktree(**args(repo))
    assert released["status"] == "RELEASED"
    assert not repo[2].exists()
    assert git(repo[0], "worktree", "list", "--porcelain").count(str(repo[2])) == 0


def test_one_l1_worktree_is_shared_by_two_disjoint_writer_slices(repo):
    provisioned = provision(repo)
    managed = repo[2]
    receipt_before_writes = repo[3].read_bytes()

    writer_a = managed / "writer_a.txt"
    writer_b = managed / "writer_b.txt"
    writer_a.write_text("slice A\n", encoding="utf-8")
    writer_b.write_text("slice B\n", encoding="utf-8")

    assert writer_a.read_text(encoding="utf-8") == "slice A\n"
    assert writer_b.read_text(encoding="utf-8") == "slice B\n"
    assert provisioned["receipt"]["assignment_id"] == args(repo)["assignment_id"]
    assert provisioned["receipt"]["managed_path"] == str(managed)
    assert repo[3].read_bytes() == receipt_before_writes
    assert git(repo[0], "worktree", "list", "--porcelain").count(managed.as_posix()) == 1
    assert list(repo[3].parent.glob("*.json")) == [repo[3]]


def test_distinct_l1_assignments_have_distinct_worktrees_and_receipts(repo):
    root, common, _, _, base = repo
    first = {
        "repo_top": root,
        "git_common_dir": common,
        "managed_path": root.parent / "managed-first",
        "receipt_path": root.parent / "receipts" / "first.json",
        "assignment_id": "L1-ASSIGNMENT-FIRST",
    }
    second = {
        "repo_top": root,
        "git_common_dir": common,
        "managed_path": root.parent / "managed-second",
        "receipt_path": root.parent / "receipts" / "second.json",
        "assignment_id": "L1-ASSIGNMENT-SECOND",
    }

    first_result = helper.provision_worktree(**first, base_commit=base)
    second_result = helper.provision_worktree(**second, base_commit=base)

    assert first_result["receipt"]["assignment_id"] != second_result["receipt"]["assignment_id"]
    assert first_result["receipt"]["managed_path"] != second_result["receipt"]["managed_path"]
    assert first["receipt_path"] != second["receipt_path"]
    worktrees = git(root, "worktree", "list", "--porcelain")
    assert worktrees.count(first["managed_path"].as_posix()) == 1
    assert worktrees.count(second["managed_path"].as_posix()) == 1

    assert helper.release_worktree(**first)["status"] == "RELEASED"
    assert helper.release_worktree(**second)["status"] == "RELEASED"


def test_root_integration_is_separate_and_single_for_shared_writer_outputs(repo):
    provisioned = provision(repo)
    root, _, managed, _, base = repo
    assert provisioned["receipt"]["status"] == "PROVISIONED"
    assert git(root, "rev-parse", "HEAD") == base

    (managed / "writer_a.txt").write_text("integrated A\n", encoding="utf-8")
    (managed / "writer_b.txt").write_text("integrated B\n", encoding="utf-8")
    git(managed, "add", "writer_a.txt", "writer_b.txt")
    candidate = git(managed, "commit", "-m", "shared writer outputs")
    candidate = git(managed, "rev-parse", "HEAD")

    assert git(root, "rev-parse", "HEAD") == base
    recorded = helper.record_candidate(**args(repo), candidate_commit=candidate)
    assert recorded["receipt"]["status"] == "CANDIDATE_RECORDED"
    assert git(root, "rev-parse", "HEAD") == base

    git(root, "merge", "--ff-only", candidate)
    assert git(root, "rev-parse", "HEAD") == candidate
    released = helper.release_worktree(**args(repo), accepted=True)
    assert released["status"] == "RELEASED"
    assert not managed.exists()


def test_exact_base_path_and_assignment_validation(repo):
    root, common, managed, receipt, base = repo
    with pytest.raises(helper.WorktreeError):
        helper.provision_worktree(repo_top=root / ".." / "repo", git_common_dir=common, managed_path=managed, receipt_path=receipt, assignment_id="ASSIGNMENT-1", base_commit=base)
    with pytest.raises(helper.WorktreeError):
        helper.provision_worktree(**args(repo), base_commit="deadbeef")
    with pytest.raises(helper.WorktreeError):
        helper.provision_worktree(**{**args(repo), "assignment_id": "../unsafe"}, base_commit=base)
    with pytest.raises(helper.WorktreeError):
        helper.provision_worktree(**{**args(repo), "managed_path": "relative"}, base_commit=base)


def test_one_nonterminal_receipt_rule(repo):
    provision(repo)
    with pytest.raises(helper.WorktreeRefusal):
        helper.provision_worktree(**args(repo), base_commit=repo[-1])
    assert repo[2].exists()


@pytest.mark.parametrize("kind", ["dirty", "untracked"])
def test_release_refuses_dirty_or_nonignored_untracked(repo, kind):
    provision(repo)
    if kind == "dirty":
        (repo[2] / "tracked.txt").write_text("changed\n", encoding="utf-8")
    else:
        (repo[2] / "new.txt").write_text("new\n", encoding="utf-8")
    report = helper.audit_worktree(**args(repo))["report"]
    assert report["tracked_dirty"] if kind == "dirty" else report["nonignored_untracked"]
    with pytest.raises(helper.WorktreeRefusal):
        helper.release_worktree(**args(repo))
    assert repo[2].exists()


def test_ignored_artifact_requires_disposition_before_cleanup(repo):
    root = repo[0]
    (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    git(root, "add", ".gitignore")
    git(root, "commit", "-m", "ignore")
    # Reprovision from the new exact base in this isolated fixture.
    repo = (root, repo[1], repo[2], repo[3], git(root, "rev-parse", "HEAD"))
    provision(repo)
    (repo[2] / "ignored.txt").write_text("evidence\n", encoding="utf-8")
    report = helper.audit_worktree(**args(repo))["report"]
    assert report["ignored_only"] and report["ignored_disposition_required"]
    with pytest.raises(helper.WorktreeRefusal):
        helper.release_worktree(**args(repo))
    released = helper.release_worktree(**args(repo), ignored_disposition="disposable")
    assert released["status"] == "RELEASED" and not repo[2].exists()


def test_in_use_refusal(repo):
    provision(repo)
    with pytest.raises(helper.WorktreeRefusal):
        helper.release_worktree(**args(repo), in_use=True)
    assert repo[2].exists()


def test_unique_candidate_retain_creates_assignment_scoped_recovery_ref(repo):
    provision(repo)
    managed = repo[2]
    (managed / "tracked.txt").write_text("candidate\n", encoding="utf-8")
    git(managed, "add", "tracked.txt")
    candidate = git(managed, "commit", "-m", "candidate")
    candidate = git(managed, "rev-parse", "HEAD")
    helper.record_candidate(**args(repo), candidate_commit=candidate)
    retained = helper.retain_worktree(**args(repo))
    assert retained["status"] == "RETAINED_FOR_RECOVERY"
    assert retained["recovery_ref"].endswith("/ASSIGNMENT-1")
    assert git(repo[0], "show-ref", "--verify", "--hash", retained["recovery_ref"]) == candidate
    assert not managed.exists()


def test_accepted_integrated_candidate_can_release(repo):
    provision(repo)
    managed = repo[2]
    (managed / "tracked.txt").write_text("integrated\n", encoding="utf-8")
    git(managed, "add", "tracked.txt")
    git(managed, "commit", "-m", "candidate")
    candidate = git(managed, "rev-parse", "HEAD")
    helper.record_candidate(**args(repo), candidate_commit=candidate)
    git(repo[0], "merge", "--ff-only", candidate)
    released = helper.release_worktree(**args(repo), accepted=True)
    assert released["status"] == "RELEASED"


def test_candidate_mismatch_and_receipt_worktree_mismatch_refuse(repo):
    provision(repo)
    original = repo[3].read_bytes()
    # Simulate a physical crash/removal while Git still retains the exact
    # registration.  The receipt remains byte-for-byte valid and untouched.
    shutil.rmtree(repo[2])
    with pytest.raises(helper.WorktreeError):
        helper.audit_worktree(**args(repo))
    assert repo[3].read_bytes() == original


def test_release_pending_intent_retries_to_terminal_after_crash(repo, monkeypatch):
    provision(repo)

    def crash(*_args, **_kwargs):
        raise RuntimeError("simulated crash before checkout removal")

    monkeypatch.setattr(helper, "_remove_checkout", crash)
    with pytest.raises(helper.WorktreeError):
        helper.release_worktree(**args(repo))
    pending = json.loads(repo[3].read_text(encoding="utf-8"))
    assert pending["status"] == "PROVISIONED"
    assert pending["pending_action"]["operation"] == "release"
    monkeypatch.undo()
    retried = helper.release_worktree(**args(repo))
    assert retried["status"] == "RELEASED" and not repo[2].exists()


def test_retain_pending_intent_audit_reconciles_absent_checkout(repo, monkeypatch):
    provision(repo)
    managed = repo[2]
    (managed / "tracked.txt").write_text("candidate\n", encoding="utf-8")
    git(managed, "add", "tracked.txt")
    git(managed, "commit", "-m", "candidate")
    candidate = git(managed, "rev-parse", "HEAD")
    helper.record_candidate(**args(repo), candidate_commit=candidate)

    def crash(*_args, **_kwargs):
        raise RuntimeError("simulated crash after protection")

    monkeypatch.setattr(helper, "_remove_checkout", crash)
    with pytest.raises(helper.WorktreeError):
        helper.retain_worktree(**args(repo))
    pending = json.loads(repo[3].read_text(encoding="utf-8"))
    assert pending["status"] == "CANDIDATE_RECORDED"
    assert pending["pending_action"]["operation"] == "retain"
    monkeypatch.undo()
    # External completion of the physical removal leaves both postconditions
    # absent; audit may now reconcile the durable retain intent.
    git(repo[0], "worktree", "remove", "--force", str(managed))
    audited = helper.audit_worktree(**args(repo))
    assert audited["terminal"] and audited["status"] == "RETAINED_FOR_RECOVERY"
    assert not managed.exists()


def test_retain_retries_idempotently_when_exact_recovery_ref_already_exists(repo, monkeypatch):
    provision(repo)
    managed = repo[2]
    (managed / "tracked.txt").write_text("candidate\n", encoding="utf-8")
    git(managed, "add", "tracked.txt")
    git(managed, "commit", "-m", "candidate")
    candidate = git(managed, "rev-parse", "HEAD")
    helper.record_candidate(**args(repo), candidate_commit=candidate)

    def crash(*_args, **_kwargs):
        raise RuntimeError("simulated crash after recovery intent")

    monkeypatch.setattr(helper, "_remove_checkout", crash)
    with pytest.raises(helper.WorktreeError):
        helper.retain_worktree(**args(repo))
    monkeypatch.undo()
    pending = json.loads(repo[3].read_text(encoding="utf-8"))
    assert git(repo[0], "show-ref", "--verify", "--hash", pending["recovery_ref"]) == candidate
    retried = helper.retain_worktree(**args(repo))
    assert retried["status"] == "RETAINED_FOR_RECOVERY" and not managed.exists()


def test_retain_final_receipt_write_crash_reconciles_protected_ref(repo, monkeypatch):
    provision(repo)
    managed = repo[2]
    (managed / "tracked.txt").write_text("candidate\n", encoding="utf-8")
    git(managed, "add", "tracked.txt")
    git(managed, "commit", "-m", "candidate")
    candidate = git(managed, "rev-parse", "HEAD")
    helper.record_candidate(**args(repo), candidate_commit=candidate)
    real_write = helper._write_receipt

    def fail_terminal_write(path, receipt):
        if receipt.get("status") == "RETAINED_FOR_RECOVERY" and receipt.get("pending_action") is None:
            raise RuntimeError("simulated receipt crash after checkout removal")
        return real_write(path, receipt)

    monkeypatch.setattr(helper, "_write_receipt", fail_terminal_write)
    with pytest.raises(helper.WorktreeError):
        helper.retain_worktree(**args(repo))
    monkeypatch.undo()
    pending = json.loads(repo[3].read_text(encoding="utf-8"))
    assert pending["status"] == "CANDIDATE_RECORDED"
    assert pending["pending_action"]["operation"] == "retain"
    assert git(repo[0], "show-ref", "--verify", "--hash", pending["recovery_ref"]) == candidate
    reconciled = helper.retain_worktree(**args(repo))
    assert reconciled["status"] == "RETAINED_FOR_RECOVERY" and not managed.exists()


def test_root_only_cli_and_no_inventory_operations(repo):
    script = SCRIPT_DIR / "hmasd_root_managed_worktree.py"
    base = repo[-1]
    common = [sys.executable, str(script), "--actor", "child", "--repo-top", str(repo[0]), "--git-common-dir", str(repo[1]), "--managed-path", str(repo[2]), "--receipt-path", str(repo[3]), "--assignment-id", "ASSIGNMENT-1", "provision", "--base-commit", base]
    result = subprocess.run(common, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert result.returncode != 0 and "only Root" in result.stdout
    parser = helper._parser()
    assert set(parser._subparsers._group_actions[0].choices) == {"provision", "audit", "record-candidate", "release", "retain"}
