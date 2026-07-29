from __future__ import annotations

import json
import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
PROBE = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py"
)
GUARD = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_route_guard.py"
)
PAYLOAD = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py"
)
HOOKS = ROOT / ".codex/hooks.json"
WDM_SESSION = "019f9d2f-e0ea-7411-9fd7-386f45f76909"
CPM_SESSION = "019f9e4f-f4d0-7fe0-b214-c47fd034e84d"
ROM_SESSION = "019f9c6a-9401-7ae0-ace5-dd827dccba2b"
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/RESEARCH_OPERATIONS_MANAGER.md",
)
PAYLOAD_SURFACES = PERSISTENT_ROLES + (
    ROOT / ".agents/skills/hmasd-review-round/SKILL.md",
    ROOT / ".agents/skills/hmasd-review-round/agents/openai.yaml",
)


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Fixed session addresses",
        "fixed session addresses only",
        "Live-settings preservation",
        "SQLite `mode=ro`",
        "visible `send_message_to_thread`",
        "returned `model` as `model`",
        "returned `thinking` as `thinking`",
        "PreToolUse guard",
        "supplies missing settings",
        "replaces mismatched settings",
        "updatedInput",
        "never creates a second message",
        "ROUTE_SENT",
        "ROUTE_SOURCE_MISMATCH",
        "ROUTE_UNAVAILABLE",
        "ROUTE_SETTINGS_UNAVAILABLE",
        "ROUTE_SETTINGS_DRIFT",
        "codex_delegation.source_thread_id",
        "explicit user-directed workflow-design commit",
        "live_target_model",
        "live_target_effort",
        "live_target_thinking",
        "never retry or resend automatically",
        "Long-text file handoff",
        "larger than 8 KiB",
        "temp/handoffs/",
        "LONG_TEXT_HANDOFF_VERIFIED",
        "LONG_TEXT_HANDOFF_INVALID",
        "HANDOFF_CONSUMED",
        "Neither role deletes a payload automatically",
    )
    for token in required:
        assert token in text, token
    for retired in (
        "ROLE_ROUTE_PROBE",
        "ROLE_ROUTE_CONFIRM",
        "ROLE_ROUTE_ANNOUNCE",
        "Conversation-local route cache",
        "fixed route triples",
        "user supplies the new session, model and effort",
        "pre_send_read_only_probe_explicit_echo",
    ):
        assert retired not in text, retired


def _payload_command(repo: Path, *args: str, stdin: bytes | None = None):
    return subprocess.run(
        (sys.executable, str(PAYLOAD), "--repo", str(repo), *args),
        input=stdin,
        check=False,
        capture_output=True,
    )


def _handoff_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "AGENTS.md").write_text("document_kind=role_router\n", encoding="utf-8")
    return repo


def test_long_text_handoff_preserves_exact_utf8_and_identity(tmp_path: Path) -> None:
    repo = _handoff_repo(tmp_path)
    payload = ("G46 候选计划\r\n" + "exact-byte-line\n" * 700).encode("utf-8")
    source = tmp_path / "candidate.txt"
    source.write_bytes(payload)

    written = _payload_command(repo, "write", "--label", "g46-candidate", "--source", str(source))
    assert written.returncode == 0, written.stderr.decode()
    metadata = json.loads(written.stdout)
    assert metadata["status"] == "LONG_TEXT_HANDOFF_WRITTEN"
    assert metadata["handoff_bytes"] == len(payload)
    assert metadata["handoff_sha256"] == hashlib.sha256(payload).hexdigest()
    assert metadata["handoff_encoding"] == "utf-8"
    target = repo / metadata["handoff_path"]
    assert target.read_bytes() == payload

    verified = _payload_command(
        repo,
        "verify",
        "--path",
        metadata["handoff_path"],
        "--bytes",
        str(metadata["handoff_bytes"]),
        "--sha256",
        metadata["handoff_sha256"],
    )
    assert verified.returncode == 0, verified.stderr.decode()
    assert json.loads(verified.stdout)["status"] == "LONG_TEXT_HANDOFF_VERIFIED"


def test_long_text_handoff_rejects_tamper_truncation_and_path_escape(
    tmp_path: Path,
) -> None:
    repo = _handoff_repo(tmp_path)
    written = _payload_command(repo, "write", "--label", "tamper", stdin=b"complete payload")
    metadata = json.loads(written.stdout)
    target = repo / metadata["handoff_path"]
    target.write_bytes(target.read_bytes()[:-1])

    for args in (
        (
            "verify",
            "--path",
            metadata["handoff_path"],
            "--bytes",
            str(metadata["handoff_bytes"]),
            "--sha256",
            metadata["handoff_sha256"],
        ),
        (
            "verify",
            "--path",
            "AGENTS.md",
            "--bytes",
            "26",
            "--sha256",
            hashlib.sha256(b"document_kind=role_router\n").hexdigest(),
        ),
    ):
        rejected = _payload_command(repo, *args)
        assert rejected.returncode != 0
        assert json.loads(rejected.stdout)["status"] == "LONG_TEXT_HANDOFF_INVALID"


def test_temp_handoff_payloads_are_git_ignored_but_contract_is_tracked() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/temp/*" in ignore
    assert "!/temp/README.md" in ignore
    contract = (ROOT / "temp/README.md").read_text(encoding="utf-8")
    assert "temp/handoffs/" in contract
    assert "Payloads are never deleted automatically" in contract


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]


def test_router_contains_fixed_sessions_without_model_or_effort() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    required = (
        "cross_task_routing=fixed_role_sessions_plus_live_settings_canonicalization",
        "cross_task_model_thinking_preservation=pre_send_probe_plus_pretool_canonicalization",
        "cross_task_route_guard=pretool_live_settings_canonicalization",
        f"workflow_design_manager_session={WDM_SESSION}",
        f"code_project_manager_session={CPM_SESSION}",
        f"research_operations_manager_session={ROM_SESSION}",
    )
    for token in required:
        assert agents.count(token) == 1, token
    for session in (
        WDM_SESSION,
        CPM_SESSION,
        ROM_SESSION,
    ):
        assert skill.count(session) == 1, session
    for retired in (
        "workflow_design_manager_route=",
        "code_project_manager_route=",
        "research_operations_manager_route=",
    ):
        assert retired not in agents, retired


def test_persistent_roles_use_fixed_sessions_and_live_settings_without_cache() -> None:
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert (
            "cross_task_target_identity=fixed_router_role_session" in text
            or "cross_task_target_identity=exact_fixed_requester_role_session" in text
        )
        assert "cross_task_route_cache=forbidden" in text
        assert (
            "cross_task_model_thinking_preservation="
            "pre_send_probe_plus_pretool_canonicalization"
        ) in text
        assert "cross_task_route_guard=pretool_live_settings_canonicalization" in text


def test_review_registry_is_local_to_operations_manager_transport() -> None:
    registry = json.loads(
        (ROOT / "docs/external-review/REVIEWER_CONVERSATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    contract = registry["transport_contract"]
    assert registry["schema_version"] == 38
    assert contract["transport_owner"] == "research_operations_manager"
    assert "intertask_transport_contract" not in registry
    for retired in (
        "cross_task_routing_skill",
        "target_identity",
        "live_settings_probe",
        "payload_route_settings",
    ):
        assert retired not in contract


def _make_state(path: Path, cwd: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads ("
        "id TEXT PRIMARY KEY, cwd TEXT, archived INTEGER, model TEXT, "
        "reasoning_effort TEXT, updated_at_ms INTEGER)"
    )
    connection.executemany(
        "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)",
        (
            ("live", str(cwd), 0, "gpt-5.6-sol", "medium", 100),
            ("archived", str(cwd), 1, "gpt-5.6-sol", "high", 101),
            ("incomplete", str(cwd), 0, "gpt-5.6-sol", None, 102),
            (WDM_SESSION, str(cwd), 0, "gpt-5.6-sol", "high", 103),
        ),
    )
    connection.commit()
    connection.close()


def _probe(state: Path, cwd: Path, thread_id: str, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        (
            sys.executable,
            str(PROBE),
            "--state-db",
            str(state),
            "--thread-id",
            thread_id,
            "--expect-cwd",
            str(cwd),
            *extra,
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def _write_router(repo: Path) -> None:
    (repo / "AGENTS.md").write_text(
        "\n".join(
            (
                f"workflow_design_manager_session={WDM_SESSION}",
                f"code_project_manager_session={CPM_SESSION}",
                f"research_operations_manager_session={ROM_SESSION}",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _guard(state: Path, repo: Path, tool_input: dict) -> tuple[int, dict | None]:
    payload = {
        "session_id": CPM_SESSION,
        "cwd": str(repo),
        "hook_event_name": "PreToolUse",
        "tool_name": "codex_app__send_message_to_thread",
        "tool_input": tool_input,
    }
    result = subprocess.run(
        (
            sys.executable,
            str(GUARD),
            "--repo",
            str(repo),
            "--state-db",
            str(state),
        ),
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, output


def test_live_settings_probe_is_read_only_and_supports_drift_diagnostic(
    tmp_path: Path,
) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    state = tmp_path / "state.sqlite"
    _make_state(state, cwd)
    before = state.read_bytes()

    code, payload = _probe(state, cwd, "live")
    assert code == 0
    assert payload["status"] == "LIVE_SETTINGS"
    assert payload["model"] == "gpt-5.6-sol"
    assert payload["thinking"] == "medium"

    code, payload = _probe(
        state,
        cwd,
        "live",
        "--expect-model",
        "gpt-5.6-sol",
        "--expect-thinking",
        "high",
    )
    assert code != 0
    assert payload["status"] == "SETTINGS_DRIFT"
    assert state.read_bytes() == before


def test_live_settings_probe_fails_closed(tmp_path: Path) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    state = tmp_path / "state.sqlite"
    _make_state(state, cwd)

    expected = {
        "missing": "THREAD_NOT_FOUND",
        "archived": "THREAD_ARCHIVED",
        "incomplete": "THREAD_SETTINGS_INCOMPLETE",
    }
    for thread_id, status in expected.items():
        code, payload = _probe(state, cwd, thread_id)
        assert code != 0
        assert payload["status"] == status

    other = tmp_path / "other"
    other.mkdir()
    code, payload = _probe(state, other, "live")
    assert code != 0
    assert payload["status"] == "THREAD_WORKSPACE_MISMATCH"


def test_route_guard_canonicalizes_missing_mismatched_and_matching_settings(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_router(repo)
    state = tmp_path / "state.sqlite"
    _make_state(state, repo)

    cases = (
        {"threadId": WDM_SESSION, "prompt": "missing", "hostId": "local"},
        {
            "threadId": WDM_SESSION,
            "prompt": "mismatched",
            "model": "gpt-5.6-luna",
            "thinking": "max",
        },
        {
            "threadId": WDM_SESSION,
            "prompt": "matching",
            "model": "gpt-5.6-sol",
            "thinking": "high",
        },
    )
    for tool_input in cases:
        code, decision = _guard(state, repo, tool_input)
        assert code == 0
        output = decision["hookSpecificOutput"]
        assert output["hookEventName"] == "PreToolUse"
        assert output["permissionDecision"] == "allow"
        updated = output["updatedInput"]
        assert updated["threadId"] == WDM_SESSION
        assert updated["prompt"] == tool_input["prompt"]
        assert updated["model"] == "gpt-5.6-sol"
        assert updated["thinking"] == "high"
        assert updated.get("hostId") == tool_input.get("hostId")


def test_route_guard_leaves_other_targets_unchanged_and_denies_unavailable_settings(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_router(repo)
    state = tmp_path / "state.sqlite"
    _make_state(state, repo)

    code, decision = _guard(
        state,
        repo,
        {"threadId": "unrelated", "prompt": "ordinary", "model": "gpt-5.6-luna"},
    )
    assert code == 0
    assert decision is None

    connection = sqlite3.connect(state)
    connection.execute("UPDATE threads SET archived = 1 WHERE id = ?", (WDM_SESSION,))
    connection.commit()
    connection.close()
    code, decision = _guard(state, repo, {"threadId": WDM_SESSION, "prompt": "blocked"})
    assert code == 0
    output = decision["hookSpecificOutput"]
    assert output["permissionDecision"] == "deny"
    assert "THREAD_ARCHIVED" in output["permissionDecisionReason"]

    (repo / "AGENTS.md").write_text(
        f"workflow_design_manager_session={WDM_SESSION}\n", encoding="utf-8"
    )
    code, decision = _guard(state, repo, {"threadId": WDM_SESSION, "prompt": "blocked"})
    assert code == 0
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_project_hook_canonicalizes_cross_task_calls_and_preserves_readiness_stop() -> None:
    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
    pre = hooks["PreToolUse"]
    assert len(pre) == 2
    routes = {entry["matcher"]: entry for entry in pre}
    route = routes["^codex_app__send_message_to_thread$"]
    boundary = routes[
        "^(shell_command|Bash|unified_exec|exec_command|apply_patch|ApplyPatch)$"
    ]
    assert len(route["hooks"]) == 1
    handler = route["hooks"][0]
    assert handler["type"] == "command"
    assert "hmasd_cross_task_route_guard.py" in handler["command"]
    assert handler["timeout"] == 5
    assert len(boundary["hooks"]) == 1
    assert "hmasd_workspace_boundary_guard.py" in boundary["hooks"][0]["command"]
    assert boundary["hooks"][0]["timeout"] == 5
    assert len(hooks["Stop"]) == 1
    assert "hmasd_execution_readiness.py" in hooks["Stop"][0]["hooks"][0]["command"]

    payload = {
        "session_id": WDM_SESSION,
        "cwd": str(ROOT),
        "hook_event_name": "PreToolUse",
        "tool_name": "codex_app__send_message_to_thread",
        "tool_input": {"threadId": "unrelated", "prompt": "configured hook smoke"},
    }
    result = subprocess.run(
        handler["command"],
        cwd=ROOT,
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0, result.stderr
    assert not result.stdout.strip()


def test_route_settings_are_forbidden_from_message_payload_surfaces() -> None:
    for path in PAYLOAD_SURFACES:
        text = path.read_text(encoding="utf-8")
        for forbidden in (
            "live_target_model=",
            "live_target_effort=",
            "live_target_thinking=",
            "return_model=",
            "return_effort=",
        ):
            assert forbidden not in text, (path, forbidden)
