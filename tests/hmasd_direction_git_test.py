"""Observable repository/remote tests for the Session Envelope v2 Git seam."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import uuid
from typing import Any


ROOT = Path(__file__).parents[1]
PYTHON = Path("C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe")
SCRIPT = ROOT / "scripts/hmasd_direction_git.py"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, check=check, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    subprocess.run(["git", "init", "--initial-branch=main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.name", "HMASD Test")
    _git(repo, "config", "user.email", "hmasd-test@example.invalid")
    _write(repo / ".gitignore", "/.codex/runtime/\n")
    _write(repo / "experiments/candidates/alpha/change.py", "VALUE = 1\n")
    _write(repo / "experiments/candidates/beta/change.py", "VALUE = 1\n")
    _write(repo / "shared/core.py", "VALUE = 1\n")
    _write(repo / "notes.txt", "base\n")
    _write(repo / "dirty.txt", "base\n")
    _write(
        repo / "docs/project/git-path-policy-v1.json",
        json.dumps({
            "schema_version": 1, "default_classification": "shared-core",
            "rules": [
                {"classification": "direction-owned", "path": "experiments/candidates", "type": "prefix"},
                {"classification": "direction-owned", "path": "tests/experiments/candidates", "type": "prefix"},
                {"classification": "direction-owned", "path": "docs/research/candidates", "type": "prefix"},
                {"classification": "direction-owned", "path": "temp/directions", "type": "prefix"},
            ],
        }, indent=2, sort_keys=True) + "\n",
    )
    _git(repo, "add", "--all"); _git(repo, "commit", "-m", "initial")
    _git(repo, "remote", "add", "origin", str(origin)); _git(repo, "push", "-u", "origin", "main")
    return repo, origin


def _git_input(
    repo: Path, *, direction: str = "alpha", owned_paths: list[str] | None = None,
    workspace_mode: str = "shared-main",
) -> dict[str, Any]:
    message_id = str(uuid.uuid4())
    record = {
        "schema_version": 1,
        "assignment_message_id": message_id,
        "assignment_locator": f"native-message:{message_id}",
        "direction_id": direction,
        "recipient_identity": f"CM/{direction}/g1",
        "workspace_mode": workspace_mode,
        "owned_paths": owned_paths or [f"experiments/candidates/{direction}/"],
        "commit_subject": f"Implement {direction} bounded discriminator",
    }
    path = repo / ".codex/runtime" / f"git-input-{message_id}.json"
    _write(path, json.dumps(record))
    return {"path": path, "record": record}


def _cli(repo: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [str(PYTHON), str(SCRIPT), *args], cwd=repo, check=False,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert completed.stdout.strip(), completed.stderr
    return completed, json.loads(completed.stdout)


def _published_closure(candidate: str) -> dict[str, Any]:
    return {
        "kind": "PUBLISHED", "branch": "main", "commit_sha": candidate,
        "remote": "origin", "ref": "refs/heads/main", "push_outcome": "SUCCEEDED",
    }


def test_commit_push_uses_frozen_git_input_and_emits_return_closure(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path); frozen = _git_input(repo)
    assigned = "experiments/candidates/alpha/change.py"
    _write(repo / assigned, "VALUE = 2\n")
    _write(repo / "notes.txt", "user staged change\n"); _git(repo, "add", "notes.txt")
    _write(repo / "dirty.txt", "user unstaged change\n")
    completed, result = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
        "--path", assigned,
    )
    assert completed.returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["message_id"] == frozen["record"]["assignment_message_id"]
    assert result["assignment_locator"] == frozen["record"]["assignment_locator"]
    assert result["changed_paths"] == [assigned]
    candidate = result["candidate_sha"]
    assert result["git_closure"] == _published_closure(candidate)
    assert _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate).stdout.splitlines() == [assigned]
    assert _git(repo, "diff", "--cached", "--name-only").stdout.splitlines() == ["notes.txt"]
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == candidate
    assert (repo / "dirty.txt").read_text(encoding="utf-8") == "user unstaged change\n"


def test_no_changes_checks_owned_paths_and_emits_exact_no_changes(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path); frozen = _git_input(repo)
    completed, result = _cli(repo, "no-changes", "--repo", str(repo), "--git-input", str(frozen["path"]))
    assert completed.returncode == 0, result
    assert result["status"] == "SUCCEEDED"
    assert result["changed_paths"] == []
    assert result["git_closure"] == {"kind": "NO_CHANGES"}
    _write(repo / "experiments/candidates/alpha/change.py", "VALUE = 2\n")
    refused, result = _cli(repo, "no-changes", "--repo", str(repo), "--git-input", str(frozen["path"]))
    assert refused.returncode == 2
    assert result["status"] == "REFUSED"
    assert result["git_closure"] is None


def test_failed_push_is_unknown_and_only_observe_can_resolve(tmp_path: Path) -> None:
    repo, origin = _repository(tmp_path); frozen = _git_input(repo)
    assigned = "experiments/candidates/alpha/change.py"; _write(repo / assigned, "VALUE = 2\n")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    hook = origin / "hooks/pre-receive"; _write(hook, "#!/bin/sh\nexit 1\n"); hook.chmod(0o755)
    failed, unknown = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
        "--path", assigned,
    )
    assert failed.returncode == 7 and unknown["status"] == "PUSH_OUTCOME_UNKNOWN"
    assert unknown["push_attempted"] is True and unknown["git_closure"] is None
    candidate = unknown["candidate_sha"]
    assert _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip() == base
    hook.unlink()
    repeated, observe_required = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
        "--path", assigned,
    )
    assert repeated.returncode == 3 and observe_required["status"] == "OBSERVE_REQUIRED"
    assert observe_required["push_attempted"] is False and observe_required["git_closure"] is None
    _git(repo, "push", "origin", f"{candidate}:refs/heads/main")
    observed, resolved = _cli(
        repo, "observe-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
    )
    assert observed.returncode == 0 and resolved["status"] == "SUCCEEDED"
    assert resolved["git_closure"] == _published_closure(candidate)


def test_shared_core_is_refused_before_git_mutation(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path); frozen = _git_input(repo, owned_paths=["shared/core.py"])
    _write(repo / "shared/core.py", "VALUE = 2\n")
    before_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    completed, refused = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
        "--path", "shared/core.py",
    )
    assert completed.returncode == 5 and refused["status"] == "SHARED_CORE_ACTION_REQUIRED"
    assert refused["git_closure"] is None
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before_head


def test_malformed_or_wrong_workspace_git_input_is_refused_without_mutation(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path); frozen = _git_input(repo)
    assigned = "experiments/candidates/alpha/change.py"
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    record = frozen["record"]; record["unexpected"] = True; _write(frozen["path"], json.dumps(record))
    rejected, invalid = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]),
        "--path", assigned,
    )
    assert rejected.returncode == 2 and invalid["status"] == "REFUSED"
    separate = _git_input(repo, workspace_mode="separate-worktree")
    refused, wrong = _cli(
        repo, "commit-push", "--repo", str(repo), "--git-input", str(separate["path"]),
        "--path", assigned,
    )
    assert refused.returncode == 2 and wrong["workspace_mode"] == "separate-worktree"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before


def test_disjoint_frozen_inputs_serialize_without_index_pollution(tmp_path: Path) -> None:
    repo, _ = _repository(tmp_path); alpha, beta = _git_input(repo), _git_input(repo, direction="beta")
    alpha_path, beta_path = "experiments/candidates/alpha/change.py", "experiments/candidates/beta/change.py"
    _write(repo / alpha_path, "VALUE = 2\n"); _write(repo / beta_path, "VALUE = 2\n")

    def invoke(frozen: dict[str, Any], path: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        return _cli(repo, "commit-push", "--repo", str(repo), "--git-input", str(frozen["path"]), "--path", path)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result() for future in (
            executor.submit(invoke, alpha, alpha_path), executor.submit(invoke, beta, beta_path),
        )]
    for completed, result in results:
        assert completed.returncode == 0, result
        assert result["git_closure"] == _published_closure(result["candidate_sha"])
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == _git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_direction_git_does_not_import_or_parse_session_envelopes() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "hmasd_session_envelope" not in source
    assert "--assignment" not in source
