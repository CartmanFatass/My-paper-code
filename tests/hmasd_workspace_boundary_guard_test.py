"""Proof-sized, identity-neutral contracts for the global PreToolUse guard."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_workspace_boundary_guard.py"


def workspace(tmp_path: Path) -> Path:
    """Create a Gitless fixture with the stable project-root markers."""

    root = tmp_path / "workspace"
    (root / ".codex").mkdir(parents=True)
    (root / ".codex" / "config.toml").write_text("[features]\nmulti_agent_v2 = true\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# fixture root\n", encoding="utf-8")
    (root / "inside.txt").write_text("seed\n", encoding="utf-8")
    return root


def invoke(
    root: Path,
    tool: str,
    tool_input: object,
    *,
    session_id: str = "session-a",
    agent_type: str | None = None,
    agent_id: str | None = None,
) -> dict[str, object] | None:
    payload: dict[str, object] = {
        "session_id": session_id,
        "cwd": str(root),
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }
    if agent_type is not None:
        payload["agent_type"] = agent_type
    if agent_id is not None:
        payload["agent_id"] = agent_id
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


def assert_denied(payload: dict[str, object] | None, fragment: str | None = None) -> None:
    assert payload is not None
    output = payload.get("hookSpecificOutput")
    assert isinstance(output, dict)
    assert output.get("hookEventName") == "PreToolUse"
    assert output.get("permissionDecision") == "deny"
    reason = output.get("permissionDecisionReason")
    assert isinstance(reason, str)
    assert reason.startswith("HMASD_WORKSPACE_BOUNDARY_DENY ")
    if fragment:
        assert fragment.lower() in reason.lower()


def test_gitless_stable_markers_allow_reads_and_in_scope_writes(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    outside = tmp_path / "outside.txt"
    assert invoke(root, "Bash", {"command": "Get-Content AGENTS.md"}) is None
    assert invoke(root, "Bash", {"command": f'Set-Content -LiteralPath "{root / "new.txt"}" -Value ok'}) is None
    assert_denied(
        invoke(root, "Bash", {"command": f'Set-Content -LiteralPath "{outside}" -Value blocked'}),
        "outside the writable scope",
    )


def test_apply_patch_uses_canonical_tool_input_command_and_normalizes_targets(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    inside = "*** Begin Patch\n*** Add File: patch-note.md\n*** End Patch"
    outside = "*** Begin Patch\n*** Add File: " + str(tmp_path / "outside.md") + "\n*** End Patch"
    assert invoke(root, "apply_patch", {"command": inside}) is None
    assert_denied(invoke(root, "apply_patch", {"command": outside}), "outside the writable scope")


def test_nearest_marker_ancestor_controls_a_child_working_directory(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    child = root / "nested"
    child.mkdir()
    assert invoke(child, "Bash", {"command": f'Set-Content -LiteralPath "{child / "new.txt"}" -Value ok'}) is None


def test_identity_fields_do_not_change_global_policy(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    command = f'Set-Content -LiteralPath "{tmp_path / "outside.txt"}" -Value blocked'
    first = invoke(root, "Bash", {"command": command}, session_id="one", agent_type="manager", agent_id="a")
    second = invoke(root, "Bash", {"command": command}, session_id="two", agent_type="leaf", agent_id="b")
    assert_denied(first, "outside the writable scope")
    assert_denied(second, "outside the writable scope")
    assert first == second


@pytest.mark.parametrize(
    "command,fragment",
    (
        (r"subst X: C:\workspace", "boundary"),
        (r"New-PSDrive -Name X -PSProvider FileSystem -Root C:\workspace", "boundary"),
        (r"New-Item -ItemType Junction -Path C:\alias -Target C:\workspace", "boundary"),
        (r"Remove-Item -LiteralPath . -Recurse -Force", "recursive deletion"),
    ),
)
def test_alias_and_broad_destruction_fail_closed(
    tmp_path: Path, command: str, fragment: str
) -> None:
    assert_denied(invoke(workspace(tmp_path), "Bash", {"command": command}), fragment)


def test_recursive_deletion_of_marker_root_or_an_unresolved_scope_fails_closed(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    assert_denied(
        invoke(root, "Bash", {"command": f'Remove-Item -LiteralPath "{root}" -Recurse -Force'}),
        "recursive deletion",
    )
    assert_denied(
        invoke(root, "Bash", {"command": "Remove-Item -Recurse -Force"}),
        "recursive deletion",
    )


def test_git_add_and_commit_remain_syntactically_allowed(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    assert invoke(root, "Bash", {"command": "git add inside.txt"}) is None
    assert invoke(root, "Bash", {"command": "git commit -m local"}) is None


def test_relative_path_aliases_fail_closed(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    assert_denied(
        invoke(root, "Bash", {"command": r"Set-Content -LiteralPath ..\outside.txt -Value blocked"}),
        "path alias",
    )


def test_symlink_target_alias_fails_closed_when_supported(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = root / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")
    assert_denied(
        invoke(root, "Bash", {"command": f'Set-Content -LiteralPath "{alias / "new.txt"}" -Value blocked'}),
        "path alias",
    )


def test_external_unc_and_dynamic_targets_fail_closed(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    for command in (
        r"Set-Content -LiteralPath \\server\share\outside.txt -Value blocked",
        r"Set-Content -LiteralPath $env:TEMP\outside.txt -Value blocked",
    ):
        assert_denied(invoke(root, "Bash", {"command": command}))


def test_unsupported_payload_is_a_valid_json_deny_not_a_hook_process_failure(tmp_path: Path) -> None:
    payload = invoke(workspace(tmp_path), "apply_patch", {"unexpected": "shape"})
    assert_denied(payload, "payload")
