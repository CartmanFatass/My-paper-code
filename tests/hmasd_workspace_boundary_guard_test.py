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


def invoke(
    repo: Path,
    tool: str,
    tool_input: object,
    *,
    session_id: str = "guard-test",
) -> dict[str, object] | None:
    payload = {
        "session_id": session_id,
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


def test_registered_research_session_writes_only_local_research(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    (repo / "AGENTS.md").write_text(
        "independent_research_explorer_session=research-session\n"
        "independent_research_review_operator_session=review-session\n"
        "hmasd_python_interpreter=C:/Python/python.exe\n",
        encoding="utf-8",
    )
    local_research = repo / "local_research"
    local_research.mkdir()
    pro_reviews = local_research / "pro_reviews"
    pro_reviews.mkdir()

    inside = local_research / "note.md"
    outside = repo / "outside.md"
    assert_denied(
        invoke(
            local_research,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{inside}" -Value ok'},
            session_id="research-session",
        ),
        "shell mutation is forbidden",
    )
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": "Get-Content -Raw AGENTS.md"},
            session_id="research-session",
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/.agents/skills/'
                    "hmasd-independent-research-exploration/scripts/"
                    'research_portfolio_gate.py" check --record '
                    f'"{pro_reviews / "forbidden.json"}" --phase merge'
                )
            },
            session_id="research-session",
        ),
        "use a registered research script or apply_patch",
    )
    assert (
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/.agents/skills/'
                    "hmasd-independent-research-exploration/scripts/"
                    'research_portfolio_gate.py" check --record '
                    f'"{local_research / "portfolio.json"}" --phase merge'
                )
            },
            session_id="research-session",
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "apply_patch",
            "*** Begin Patch\n*** Add File: local_research/pro_reviews/forbidden.md\n*** End Patch",
            session_id="research-session",
        ),
        "reserved for another role",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/.agents/skills/'
                    "hmasd-independent-research-exploration/scripts/"
                    'unregistered.py"'
                )
            },
            session_id="research-session",
        ),
        "use a registered research script or apply_patch",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/.agents/skills/'
                    "hmasd-independent-research-exploration/scripts/"
                    'research_portfolio_gate.py" (Start-Process cmd.exe)'
                )
            },
            session_id="research-session",
        ),
        "nested or executable shell expression",
    )
    assert (
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/.agents/skills/'
                    "hmasd-independent-research-exploration/scripts/"
                    'mylib_research_probe.py" --local-research-root '
                    f'"{local_research}" status'
                )
            },
            session_id="research-session",
        )
        is None
    )
    assert (
        invoke(
            repo,
            "apply_patch",
            "*** Begin Patch\n*** Add File: local_research/patch-note.md\n*** End Patch",
            session_id="research-session",
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "apply_patch",
            "*** Begin Patch\n*** Add File: project-note.md\n*** End Patch",
            session_id="research-session",
        ),
        "outside the writable scope",
    )
    assert_denied(
        invoke(
            repo,
            "apply_patch",
            (
                "*** Begin Patch\n"
                "*** Update File: local_research/patch-note.md\n"
                "*** Move to: AGENTS.md\n"
                "*** End Patch"
            ),
            session_id="research-session",
        ),
        "outside the writable scope",
    )
    assert_denied(
        invoke(
            local_research,
            "shell_command",
            {"command": "Set-Content -LiteralPath ..\\AGENTS.md -Value bad"},
            session_id="research-session",
        ),
        "shell mutation is forbidden",
    )
    assert_denied(
        invoke(
            local_research,
            "shell_command",
            {"command": f'Copy-Item -LiteralPath "{inside}" -Destination ..\\AGENTS.md'},
            session_id="research-session",
        ),
        "shell mutation is forbidden",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{outside}" -Value blocked'},
            session_id="research-session",
        ),
        "shell mutation is forbidden",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "git add local_research/note.md"},
            session_id="research-session",
        ),
        "Git mutation is forbidden",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "python -c \"from pathlib import Path; Path('AGENTS.md').write_text('bad')\""},
            session_id="research-session",
        ),
        "nested or executable shell expression",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "[IO.File]::WriteAllText('AGENTS.md','bad')"},
            session_id="research-session",
        ),
        "nested or executable shell expression",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": f"Get-Item ([IO.File]::WriteAllText('{outside}','bad'))"},
            session_id="research-session",
        ),
        "nested or executable shell expression",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "Get-Item (Start-Process cmd.exe)"},
            session_id="research-session",
        ),
        "nested or executable shell expression",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "rg --pre malicious pattern ."},
            session_id="research-session",
        ),
        "option can execute or write",
    )
    executable = local_research / "escape.cmd"
    executable.write_text("@echo off\r\necho bad>..\\AGENTS.md\r\n", encoding="utf-8")
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": f'rg --hostname-bin="{executable}" pattern .'},
            session_id="research-session",
        ),
        "option can execute or write",
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "git diff --output=AGENTS.md"},
            session_id="research-session",
        ),
        "option can execute or write",
    )
    for option in ("--ext-diff", "--textconv"):
        assert_denied(
            invoke(
                repo,
                "shell_command",
                {"command": f"git diff {option}"},
                session_id="research-session",
            ),
            "option can execute or write",
        )
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": "git status --short"},
            session_id="research-session",
        )
        is None
    )


def test_registered_independent_review_operator_is_confined_to_pro_reviews_and_helpers(
    tmp_path: Path,
) -> None:
    repo, _ = repository(tmp_path)
    (repo / "AGENTS.md").write_text(
        "independent_research_explorer_session=research-session\n"
        "independent_research_review_operator_session=review-session\n"
        "hmasd_python_interpreter=C:/Python/python.exe\n",
        encoding="utf-8",
    )
    pro_reviews = repo / "local_research" / "pro_reviews"
    pro_reviews.mkdir(parents=True)
    review = pro_reviews / "audit-1"
    review.mkdir()
    sentinel = review / "sentinel.jsonl"
    packet = review / "60_METHODOLOGY_PACKET.md"
    packet.write_text("packet\n", encoding="utf-8")

    assert (
        invoke(
            repo,
            "apply_patch",
            "*** Begin Patch\n*** Add File: local_research/pro_reviews/audit-1/raw.md\n*** End Patch",
            session_id="review-session",
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "apply_patch",
            "*** Begin Patch\n*** Add File: local_research/explorer-note.md\n*** End Patch",
            session_id="review-session",
        ),
        "outside the writable scope",
    )
    sentinel_command = (
        f'C:/Python/python.exe "{repo}/scripts/hmasd_pro_response_sentinel.py" init '
        f'--state "{sentinel}" --conversation-id c1 --fence-identity f1'
    )
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": sentinel_command},
            session_id="review-session",
        )
        is None
    )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {
                "command": (
                    f'C:/Python/python.exe "{repo}/scripts/hmasd_pro_response_sentinel.py" init '
                    f'--state "{repo / "outside.jsonl"}" --conversation-id c1 --fence-identity f1'
                )
            },
            session_id="review-session",
        ),
        "use a registered research script or apply_patch",
    )
    handoff_command = (
        f'C:/Python/python.exe "{repo}/.agents/skills/hmasd-cross-task-routing/scripts/'
        f'hmasd_cross_task_payload.py" --repo "{repo}" write --label methodology '
        f'--source "{packet}"'
    )
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": handoff_command},
            session_id="review-session",
        )
        is None
    )
    for basename in ("verify_pro_review_boundary.ps1", "render_review_fence.ps1"):
        command = (
            'powershell -ExecutionPolicy Bypass -File '
            f'"{repo}/.agents/skills/hmasd-review-round/scripts/{basename}"'
        )
        assert (
            invoke(
                repo,
                "shell_command",
                {"command": command},
                session_id="review-session",
            )
            is None
        )
    assert_denied(
        invoke(
            repo,
            "shell_command",
            {"command": "git status --short"},
            session_id="review-session",
        ),
        "Git mutation is forbidden",
    )


def test_other_session_keeps_main_checkout_scope_when_research_is_registered(
    tmp_path: Path,
) -> None:
    repo, _ = repository(tmp_path)
    (repo / "AGENTS.md").write_text(
        "independent_research_explorer_session=research-session\n",
        encoding="utf-8",
    )
    ordinary = repo / "ordinary.md"
    assert (
        invoke(
            repo,
            "shell_command",
            {"command": f'Set-Content -LiteralPath "{ordinary}" -Value ok'},
            session_id="another-session",
        )
        is None
    )
