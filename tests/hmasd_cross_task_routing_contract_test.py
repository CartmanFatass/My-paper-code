from __future__ import annotations

import json
import re
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
RESEARCH_EXPLORER_SESSION = "019fbded-24cb-7541-aa16-0111b626b945"
RETIRED_RESEARCH_EXPLORER_SESSION = "019fb2e1-d153-7043-b2e9-58690f9bd48d"
LOCKED_ROUTES = {
    "workflow_design_manager": (WDM_SESSION, "gpt-5.6-sol", "high"),
    "code_project_manager": (CPM_SESSION, "gpt-5.6-sol", "max"),
    "independent_research_explorer": (
        RESEARCH_EXPLORER_SESSION,
        "gpt-5.6-sol",
        "ultra",
    ),
}
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
)
PAYLOAD_SURFACES = PERSISTENT_ROLES


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "sole persistent-task address source",
        "role_id",
        "session_id",
        "model",
        "thinking",
        "Native send",
        "codex_app__send_message_to_thread",
        "native tool is unavailable",
        "Passing model and thinking is mandatory",
        "sender-setting substitution",
        "ROUTE_SENT",
        "ROUTE_CONFIGURATION_MISMATCH",
        "ROUTE_IDENTITY_MISMATCH",
        "ROUTE_HANDOFF_INVALID",
        "ROUTE_UNAVAILABLE",
        "source_thread_id",
        "workflow commit",
        "Do not retry automatically",
        "Long-text file handoff",
        "larger than 8 KiB",
        "temp/sessions/<role>/handoffs/",
        "handoff_owner_role",
        "locked-source-role",
        "LONG_TEXT_HANDOFF_VERIFIED",
        "LONG_TEXT_HANDOFF_INVALID",
        "HANDOFF_CONSUMED",
        "Only the source owner may later perform an explicit cleanup",
        "WORKFLOW_DEFECT_REPORT",
        "suggested_repair",
        "delivery neither preempts the active item nor transfers authority",
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

    written = _payload_command(
        repo,
        "write",
        "--owner-role",
        "workflow_design_manager",
        "--label",
        "g46-candidate",
        "--source",
        str(source),
    )
    assert written.returncode == 0, written.stderr.decode()
    metadata = json.loads(written.stdout)
    assert metadata["status"] == "LONG_TEXT_HANDOFF_WRITTEN"
    assert metadata["handoff_encoding"] == "utf-8"
    assert metadata["handoff_owner_role"] == "workflow_design_manager"
    assert metadata["handoff_path"].startswith(
        "temp/sessions/workflow_design_manager/handoffs/"
    )
    target = repo / metadata["handoff_path"]
    assert target.read_bytes() == payload

    verified = _payload_command(
        repo,
        "verify",
        "--owner-role",
        "workflow_design_manager",
        "--path",
        metadata["handoff_path"],
    )
    assert verified.returncode == 0, verified.stderr.decode()
    assert json.loads(verified.stdout)["status"] == "LONG_TEXT_HANDOFF_VERIFIED"


def test_long_text_handoff_rejects_invalid_utf8_and_path_escape(
    tmp_path: Path,
) -> None:
    repo = _handoff_repo(tmp_path)
    written = _payload_command(
        repo,
        "write",
        "--owner-role",
        "code_project_manager",
        "--label",
        "tamper",
        stdin=b"complete payload",
    )
    metadata = json.loads(written.stdout)
    target = repo / metadata["handoff_path"]
    target.write_bytes(b"\xff")

    for args in (
        (
            "verify",
            "--owner-role",
            "code_project_manager",
            "--path",
            metadata["handoff_path"],
        ),
        (
            "verify",
            "--owner-role",
            "code_project_manager",
            "--path",
            "AGENTS.md",
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
    assert "temp/sessions/<role>/handoffs/" in contract
    assert "Payloads are never deleted automatically" in contract


def test_long_text_handoff_rejects_owner_role_escape_and_cross_role_path(
    tmp_path: Path,
) -> None:
    repo = _handoff_repo(tmp_path)
    written = _payload_command(
        repo,
        "write",
        "--owner-role",
        "workflow_design_manager",
        "--label",
        "owner",
        stdin=b"owner payload",
    )
    metadata = json.loads(written.stdout)
    for owner_role in ("../escape", "role/name", "role\\name", ".."):
        rejected = _payload_command(
            repo,
            "verify",
            "--owner-role",
            owner_role,
            "--path",
            metadata["handoff_path"],
        )
        assert rejected.returncode != 0
        assert json.loads(rejected.stdout)["status"] == "LONG_TEXT_HANDOFF_INVALID"

    cross_role = _payload_command(
        repo,
        "verify",
        "--owner-role",
        "code_project_manager",
        "--path",
        metadata["handoff_path"],
    )
    assert cross_role.returncode != 0
    assert json.loads(cross_role.stdout)["status"] == "LONG_TEXT_HANDOFF_INVALID"


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]
    assert "locked session, model, and thinking" in interface["interface"]["default_prompt"]


def test_workflow_skills_bind_wdm_contract_without_granting_children_authority() -> None:
    for relative in (
        ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md",
        ".agents/skills/hmasd-workflow-change-audit/SKILL.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for token in (
            "workflow_assignment_id",
            "owned_paths",
            "wdm_session_workspace",
            "SESSION_WORKSPACE_CONTRACT",
            "grants no",
            "Workflow Design Manager",
        ):
            assert token in text, (relative, token)


def test_router_and_skill_lock_exact_role_routes() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    assert len(LOCKED_ROUTES) == 3
    assert len(re.findall(r"(?m)^[a-z_]+_session=", agents)) == 3
    route_rows = re.findall(
        r"(?m)^\| `[^`]+` \| `[^`]+` \| `[^`]+` \| `[^`]+` \|$", skill
    )
    assert len(route_rows) == 3
    required = (
        "cross_task_routing=locked_role_session_model_thinking",
        "cross_task_routing_skill=hmasd-cross-task-routing",
        f"workflow_design_manager_session={WDM_SESSION}",
        f"code_project_manager_session={CPM_SESSION}",
        f"independent_research_explorer_session={RESEARCH_EXPLORER_SESSION}",
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
        "independent_research_review_operator_session=",
        "independent_research_review_operator",
        "PROJECT_OPERATIONS_OPERATOR.md",
        "hmasd-project-operations-operator",
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


def test_explorer_owns_independent_pro_review_without_persistent_operator() -> None:
    explorer = " ".join(
        (ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md")
        .read_text(encoding="utf-8")
        .split()
    )
    skill = " ".join(
        (ROOT / ".agents/skills/hmasd-independent-research-pro-review/SKILL.md")
        .read_text(encoding="utf-8")
        .split()
    )
    for token in (
        "independent_pro_review_transport_authority=exclusive_for_explorer_direction_and_methodology_reviews",
        "independent_pro_review_transport_execution=persistent_explorer_session_direct",
        "independent_pro_review_stable_key=hmasd-independent-research-explorer-pro",
        "independent_gemini_advisory_stable_key=hmasd-independent-research-explorer-gemini",
        "independent_pro_review_terminal_intake=exact_archived_response_fifo",
    ):
        assert token in explorer, token
    for token in (
        "invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`",
        "there is no separate persistent review-operator session",
        "chatgpt_stable_key=hmasd-independent-research-explorer-pro",
        "gemini_stable_key=hmasd-independent-research-explorer-gemini",
        "execution=persistent_explorer_session_direct",
        "archive",
        "local FIFO",
    ):
        assert token in skill, token
    assert not (ROOT / ".agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md").exists()
    assert not (ROOT / ".codex/agents/hmasd-independent-research-review-operator.toml").exists()
    assert not (ROOT / ".agents/roles/PROJECT_OPERATIONS_OPERATOR.md").exists()
    assert not (ROOT / ".codex/agents/hmasd-project-operations-operator.toml").exists()


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
