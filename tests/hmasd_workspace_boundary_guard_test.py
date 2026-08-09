from __future__ import annotations

import argparse
import io
import json
import os
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


def invoke(
    repo: Path,
    tool: str,
    tool_input: object,
    *,
    session_id: object = "ignored-session-metadata",
    cwd: Path | None = None,
) -> dict[str, object] | None:
    payload = {
        "session_id": session_id,
        "cwd": str(cwd or repo),
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


def invoke_local(
    repo: Path,
    tool: str,
    tool_input: object,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    cwd: Path | None = None,
) -> dict[str, object] | None:
    payload = {
        "session_id": None,
        "cwd": str(cwd or repo),
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }
    monkeypatch.setattr(guard.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 0
    output = capsys.readouterr().out
    return json.loads(output) if output.strip() else None


def assert_denied(payload: dict[str, object] | None, fragment: str) -> None:
    assert payload is not None
    output = payload["hookSpecificOutput"]
    assert isinstance(output, dict)
    assert output["permissionDecision"] == "deny"
    assert fragment in str(output["permissionDecisionReason"])


def test_outer_exec_and_unrecognized_tools_are_ignored(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    assert invoke(repo, "exec", "await tools.shell_command({command: arbitrary()});") is None
    assert invoke(repo, "unknown_tool", {"anything": "goes"}) is None


@pytest.mark.parametrize("session_id", (None, "", "session with whitespace", 17))
def test_main_checkout_scope_is_independent_of_session_metadata(
    tmp_path: Path, session_id: object
) -> None:
    repo, _ = repository(tmp_path)
    target = repo / "ordinary.md"
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{target}" -Value ok'},
            session_id=session_id,
        )
        is None
    )


def test_main_checkout_allows_reads_and_internal_writes_but_denies_external_writes(
    tmp_path: Path,
) -> None:
    repo, _ = repository(tmp_path)
    outside = tmp_path / "outside.txt"
    assert invoke(repo, "shell_command", {"command": f'Get-Content "{outside}"'}) is None
    assert invoke(repo, "shell_command", {"command": f'Set-Content -LiteralPath "{repo / "inside.txt"}" -Value ok'}) is None
    assert_denied(
        invoke(repo, "shell_command", {"command": f'Set-Content -LiteralPath "{outside}" -Value blocked'}),
        "outside the writable scope",
    )


@pytest.mark.parametrize(
    "command",
    (
        r"subst X: C:\repo",
        r"New-PSDrive -Name X -PSProvider FileSystem -Root C:\repo",
        r"git worktree add C:\wtp HEAD",
        r"git worktree remove --force C:\wtp",
        r"git worktree prune",
        r"New-Item -ItemType Junction -Path C:\wtp -Target C:\repo",
        r"New-Item -ItemType Directory -Path C:\wtp_tmp",
        r"Set-Content -Path \\server\share\outside.txt -Value blocked",
    ),
)
def test_drive_alias_worktree_and_unc_mutations_fail_closed(tmp_path: Path, command: str) -> None:
    repo, _ = repository(tmp_path)
    assert_denied(invoke(repo, "Bash", {"command": command}), "HMASD_WORKSPACE_BOUNDARY_DENY")


def test_direct_git_mutations_fail_closed(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    assert_denied(
        invoke(repo, "shell_command", {"command": "git add seed.txt"}),
        "Git mutation is forbidden",
    )


def test_patch_targets_are_normalized_against_the_checkout_and_existing_symlinks(
    tmp_path: Path,
) -> None:
    repo, _ = repository(tmp_path)
    inside = "*** Begin Patch\n*** Update File: seed.txt\n*** End Patch"
    outside = f"*** Begin Patch\n*** Add File: {tmp_path / 'outside.txt'}\n*** End Patch"
    assert invoke(repo, "apply_patch", inside) is None
    assert_denied(invoke(repo, "ApplyPatch", {"patch": outside}), "outside the writable scope")

    escape = repo / "escape"
    try:
        os.symlink(tmp_path, escape, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    assert_denied(
        invoke(repo, "apply_patch", "*** Begin Patch\n*** Add File: escape/outside.txt\n*** End Patch"),
        "outside the writable scope",
    )


def test_only_registered_provision_command_can_cross_the_main_checkout_boundary(tmp_path: Path) -> None:
    repo, base = repository(tmp_path)
    command = (
        f'"{sys.executable}" scripts/hmasd_workspace_ticket.py provision '
        f'--repo "{repo}" --assignment-id TASK_A --base-commit {base} --allow pkg/worker.py'
    )
    assert invoke(repo, "shell_command", {"command": command}) is None
    assert invoke(repo, "shell_command", {"command": command + " --recover-partial-assignment TASK_OLD"}) is None
    assert_denied(
        invoke(repo, "shell_command", {"command": command + "; New-Item C:\\wtp"}),
        "outside the writable scope",
    )


@pytest.mark.parametrize(
    "suffix",
    (
        " > C:/outside.txt",
        " < C:/outside.txt",
        "\nSet-Content -LiteralPath C:/outside.txt -Value blocked",
    ),
)
def test_registered_provision_rejects_redirection_and_newline_suffixes(
    tmp_path: Path, suffix: str
) -> None:
    repo, base = repository(tmp_path)
    command = (
        f'"{sys.executable}" scripts/hmasd_workspace_ticket.py provision '
        f'--repo "{repo}" --assignment-id TASK_A --base-commit {base} --allow pkg/worker.py'
        f"{suffix}"
    )
    assert_denied(
        invoke(repo, "shell_command", {"command": command}),
        "outside the writable scope",
    )


def test_ticketed_worktree_limits_patch_and_absolute_shell_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = repository(tmp_path)
    worktree_root = tmp_path / "worktrees" / "HMASD"
    worktree_root.mkdir(parents=True)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", repo)
    created = ticketing.provision_ticket(
        argparse.Namespace(repo=repo, assignment_id="TASK_A", base_commit=base, allow=["pkg/worker.py"])
    )
    worktree = Path(str(created["resolved_worktree"]))
    allowed = worktree / "pkg" / "worker.py"
    outside_scope = worktree / "other.py"

    assert invoke_local(worktree, "apply_patch", "*** Begin Patch\n*** Add File: pkg/worker.py\n*** End Patch", monkeypatch, capsys) is None
    assert invoke_local(worktree, "shell_command", {"command": f'Set-Content -Path "{allowed}" -Value ok'}, monkeypatch, capsys) is None
    assert_denied(
        invoke_local(worktree, "apply_patch", "*** Begin Patch\n*** Add File: other.py\n*** End Patch", monkeypatch, capsys),
        "outside the writable scope",
    )
    assert_denied(
        invoke_local(worktree, "shell_command", {"command": f'Set-Content -Path "{outside_scope}" -Value blocked'}, monkeypatch, capsys),
        "outside the writable scope",
    )
    assert_denied(
        invoke_local(worktree, "shell_command", {"command": "Set-Content pkg/worker.py -Value blocked"}, monkeypatch, capsys),
        "must name an allowed absolute target",
    )


def test_unregistered_linked_worktree_cannot_mutate(tmp_path: Path) -> None:
    repo, base = repository(tmp_path)
    unregistered = tmp_path / "unregistered"
    git(repo, "worktree", "add", "--detach", str(unregistered), base)
    assert_denied(
        invoke(unregistered, "shell_command", {"command": "Set-Content -Path seed.txt -Value blocked"}),
        "no unique valid workspace ticket",
    )


def test_ticket_registration_is_resolved_from_the_active_worktree_not_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = repository(tmp_path)
    worktree_root = tmp_path / "worktrees" / "HMASD"
    worktree_root.mkdir(parents=True)
    monkeypatch.setattr(ticketing, "WORKTREE_ROOT", worktree_root)
    monkeypatch.setattr(ticketing, "REGISTERED_REPOSITORY", repo)
    created = ticketing.provision_ticket(
        argparse.Namespace(repo=repo, assignment_id="TASK_B", base_commit=base, allow=["pkg/worker.py"])
    )
    worktree = Path(str(created["resolved_worktree"]))
    payload = invoke_local(
        worktree,
        "apply_patch",
        "*** Begin Patch\n*** Add File: pkg/worker.py\n*** End Patch",
        monkeypatch,
        capsys,
    )
    assert payload is None
