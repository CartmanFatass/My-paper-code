from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "hmasd_workspace_boundary_guard.py"
sys.path.insert(0, str(REPO / "scripts"))
import hmasd_workspace_boundary_guard as guard  # noqa: E402
import hmasd_workspace_ticket as ticketing  # noqa: E402


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "HMASD Guard Test")
    git(repo, "config", "user.email", "guard-test@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-m", "seed")
    return repo, git(repo, "rev-parse", "HEAD")


def invoke(repo: Path, tool: str, tool_input: object) -> dict[str, object] | None:
    payload = {
        "session_id": "guard-test",
        "cwd": str(repo),
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout) if result.stdout.strip() else None


def assert_denied(payload: dict[str, object] | None, fragment: str) -> None:
    assert payload is not None
    output = payload["hookSpecificOutput"]
    assert isinstance(output, dict)
    assert output["permissionDecision"] == "deny"
    assert fragment in str(output["permissionDecisionReason"])


def test_main_checkout_allows_reads_and_internal_writes_but_denies_external_writes(
    tmp_path: Path,
) -> None:
    repo, _ = repository(tmp_path)
    outside = tmp_path / "outside.txt"
    assert invoke(repo, "shell_command", {"command": f'Get-Content "{outside}"'}) is None
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{repo / "inside.txt"}" -Value ok'},
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{outside}" -Value blocked'},
        ),
        "outside the writable scope",
    )
    assert not outside.exists()


@pytest.mark.parametrize(
    "command",
    (
        r"subst X: C:\repo",
        r"New-PSDrive -Name X -PSProvider FileSystem -Root C:\repo",
        r"git worktree add C:\wtp HEAD",
        r"New-Item -ItemType Junction -Path C:\wtp -Target C:\repo",
        r"New-Item -ItemType Directory -Path C:\wtp_tmp",
        r"Set-Content -Path \\server\share\outside.txt -Value blocked",
    ),
)
def test_drive_alias_raw_worktree_and_external_directory_commands_fail_closed(
    tmp_path: Path, command: str
) -> None:
    repo, _ = repository(tmp_path)
    assert_denied(invoke(repo, "Bash", {"command": command}), "HMASD_WORKSPACE_BOUNDARY_DENY")


def test_apply_patch_targets_are_normalized_against_the_checkout(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    inside = "*** Begin Patch\n*** Update File: seed.txt\n*** End Patch"
    outside = (
        "*** Begin Patch\n*** Add File: "
        + str(tmp_path / "outside.txt")
        + "\n*** End Patch"
    )
    assert invoke(repo, "apply_patch", inside) is None
    assert_denied(invoke(repo, "ApplyPatch", {"patch": outside}), "outside the writable scope")


def test_only_registered_provision_command_can_cross_the_main_checkout_boundary(
    tmp_path: Path,
) -> None:
    repo, base = repository(tmp_path)
    command = (
        f'"{sys.executable}" scripts/hmasd_workspace_ticket.py provision '
        f'--repo "{repo}" --assignment-id TASK_A --base-commit {base} '
        "--allow pkg/worker.py"
    )
    assert invoke(repo, "shell_command", {"command": command}) is None
    assert_denied(
        invoke(repo, "shell_command", {"command": command + "; New-Item C:\\wtp"}),
        "outside the writable scope",
    )


def test_ticketed_worktree_limits_patch_and_absolute_shell_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = repository(tmp_path)
    worktree_root = tmp_path / "worktrees" / "HMASD"
    worktree_root.mkdir(parents=True)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", repo)
    created = ticketing.provision_ticket(
        argparse.Namespace(
            repo=repo,
            assignment_id="TASK_A",
            base_commit=base,
            allow=["pkg/worker.py"],
        )
    )
    worktree = Path(str(created["resolved_worktree"]))
    allowed = worktree / "pkg" / "worker.py"
    outside_scope = worktree / "other.py"

    _, allowed_roots, linked = guard._workspace_scope(worktree)
    assert linked is True
    guard._guard_patch(
        worktree,
        allowed_roots,
        "*** Begin Patch\n*** Add File: pkg/worker.py\n*** End Patch",
    )
    guard._guard_shell(
        worktree,
        worktree,
        allowed_roots,
        linked,
        {"command": f'Set-Content -Path "{allowed}" -Value ok'},
    )
    with pytest.raises(guard.GuardError, match="outside the writable scope"):
        guard._guard_patch(
            worktree,
            allowed_roots,
            "*** Begin Patch\n*** Add File: other.py\n*** End Patch",
        )
    with pytest.raises(guard.GuardError, match="outside the writable scope"):
        guard._guard_shell(
            worktree,
            worktree,
            allowed_roots,
            linked,
            {"command": f'Set-Content -Path "{outside_scope}" -Value blocked'},
        )


def test_unregistered_linked_worktree_cannot_mutate(tmp_path: Path) -> None:
    repo, base = repository(tmp_path)
    unregistered = tmp_path / "unregistered"
    git(repo, "worktree", "add", "--detach", str(unregistered), base)
    assert_denied(
        invoke(
            unregistered,
            "shell_command",
            {"command": "Set-Content -Path seed.txt -Value blocked"},
        ),
        "no unique valid workspace ticket",
    )
