from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
PAYLOAD = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py"
)
HOOKS = ROOT / ".codex/hooks.json"
WDM_SESSION = "019fb73d-5635-7b63-b165-6c5129bc0217"
RETIRED_WDM_SESSION = "019f9d2f-e0ea-7411-9fd7-386f45f76909"
CPM_SESSION = "019f9e4f-f4d0-7fe0-b214-c47fd034e84d"
RESEARCH_REVIEW_SESSION = "019fb311-6137-7781-9708-3df24da34a4b"
RESEARCH_EXPLORER_SESSION = "019fbd62-3440-7dd1-8d41-c72c15cb8d4e"
RETIRED_RESEARCH_EXPLORER_SESSION = "019fb2e1-d153-7043-b2e9-58690f9bd48d"
LOCKED_ROUTES = {
    "workflow_design_manager": (WDM_SESSION, "gpt-5.6-sol", "high"),
    "code_project_manager": (CPM_SESSION, "gpt-5.6-sol", "max"),
    "independent_research_explorer": (
        RESEARCH_EXPLORER_SESSION,
        "gpt-5.6-sol",
        "ultra",
    ),
    "independent_research_review_operator": (
        RESEARCH_REVIEW_SESSION,
        "gpt-5.6-luna",
        "medium",
    ),
}
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
    ROOT / ".agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md",
)
PAYLOAD_SURFACES = PERSISTENT_ROLES


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Locked route table",
        "role_id",
        "session_id",
        "model",
        "thinking",
        "Native send",
        "codex_app__send_message_to_thread",
        "runtime capability",
        "Passing both `model` and `thinking` is mandatory",
        "substituting the sender's settings",
        "ROUTE_SENT",
        "ROUTE_CONFIGURATION_MISMATCH",
        "ROUTE_IDENTITY_MISMATCH",
        "ROUTE_HANDOFF_INVALID",
        "ROUTE_UNAVAILABLE",
        "codex_delegation.source_thread_id",
        "explicit user-directed workflow-design commit",
        "Do not retry automatically",
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
        "pre_send_read_only_probe_explicit_echo",
        "Live-settings preservation",
        "ROUTE_SETTINGS_UNAVAILABLE",
        "ROUTE_SETTINGS_DRIFT",
        "read_codex_thread_settings.py",
        "hmasd_cross_task_route_guard.py",
        "SQLite `mode=ro`",
        "PreToolUse guard",
        "session identity only",
        "does not inspect, select, transmit, preserve, compare or restore",
        "makes no claim about the target task's model or reasoning effort",
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
    assert "locked session, model, and thinking" in interface["interface"]["default_prompt"]


def test_router_and_skill_lock_exact_role_routes() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    required = (
        "cross_task_routing=locked_role_session_model_thinking",
        "cross_task_routing_skill=hmasd-cross-task-routing",
        f"workflow_design_manager_session={WDM_SESSION}",
        f"code_project_manager_session={CPM_SESSION}",
        f"independent_research_explorer_session={RESEARCH_EXPLORER_SESSION}",
        f"independent_research_review_operator_session={RESEARCH_REVIEW_SESSION}",
    )
    for token in required:
        assert agents.count(token) == 1, token
    for role_id, (session_id, model, thinking) in LOCKED_ROUTES.items():
        row = f"| `{role_id}` | `{session_id}` | `{model}` | `{thinking}` |"
        assert skill.count(row) == 1, row
    for retired in (RETIRED_RESEARCH_EXPLORER_SESSION, RETIRED_WDM_SESSION):
        assert retired not in agents
        assert retired not in skill
    for retired in (
        "cross_task_routing=fixed_role_sessions",
        "workflow_design_manager_route=",
        "code_project_manager_route=",
        "research_operations_manager_route=",
        "research_operations_manager_session=",
        "cross_task_model_thinking_preservation=",
        "cross_task_route_guard=",
        "live_settings_canonicalization",
    ):
        assert retired not in agents, retired


def test_persistent_roles_require_locked_target_settings() -> None:
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert (
            "cross_task_target_identity=fixed_router_role_session" in text
            or "cross_task_target_identity=exact_fixed_requester_role_session" in text
        )
        assert "cross_task_target_settings=locked_role_session_model_thinking" in text
        assert "cross_task_route_cache=forbidden" in text
        assert "does not inspect, select, preserve or restore" not in text
        assert "cross_task_model_thinking_preservation=" not in text
        assert "cross_task_route_guard=" not in text


def test_independent_review_operator_routes_only_terminal_methodology_to_wdm() -> None:
    role = " ".join(
        (ROOT / ".agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md")
        .read_text(encoding="utf-8")
        .split()
    )
    skill = " ".join(SKILL.read_text(encoding="utf-8").split())
    for token in (
        "formal_workflow_authority=none",
        "write_scope=local_research/pro_reviews_only",
        "formal_review_conversation_access=forbidden",
        "A format-complete",
        "Workflow Design Manager",
    ):
        assert token in role, token
    assert "may route only an exact terminal methodology" in skill
    assert "Direction review is a native-child final to Explorer" in skill
    assert "does not use this Skill" in skill
    assert "direction packet directly to the locked Independent Research Explorer" not in role


def test_project_hooks_preserve_workspace_boundary_and_readiness_stop() -> None:
    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
    pre = hooks["PreToolUse"]
    assert len(pre) == 1
    routes = {entry["matcher"]: entry for entry in pre}
    boundary = routes[
        "^(shell_command|Bash|unified_exec|exec_command|apply_patch|ApplyPatch)$"
    ]
    assert "^codex_app__send_message_to_thread$" not in routes
    assert len(boundary["hooks"]) == 1
    assert "hmasd_workspace_boundary_guard.py" in boundary["hooks"][0]["command"]
    assert boundary["hooks"][0]["timeout"] == 5
    assert len(hooks["Stop"]) == 1
    assert "hmasd_execution_readiness.py" in hooks["Stop"][0]["hooks"][0]["command"]


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
