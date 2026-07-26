from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
RETIRED_PROBE = (
    ROOT / ".agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py"
)
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/EXTERNAL_REVIEW_OPERATOR.md",
)
PAYLOAD_SURFACES = PERSISTENT_ROLES + (
    ROOT / ".agents/skills/hmasd-review-round/SKILL.md",
    ROOT / ".agents/skills/hmasd-review-round/agents/openai.yaml",
)


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Fixed routes",
        "fixed route triples in the root `AGENTS.md`",
        "same tool call",
        "ROUTE_SENT",
        "ROUTE_SOURCE_MISMATCH",
        "ROUTE_UNAVAILABLE",
        "codex_delegation.source_thread_id",
        "explicit user-directed workflow-design commit",
        "live_target_model",
        "live_target_effort",
        "live_target_thinking",
        "never retry automatically",
    )
    for token in required:
        assert token in text, token
    for retired in (
        "ROLE_ROUTE_PROBE",
        "ROLE_ROUTE_CONFIRM",
        "ROLE_ROUTE_ANNOUNCE",
        "state_5.sqlite",
        "read_codex_thread_settings.py",
        "Conversation-local route cache",
        "ROUTE_SETTINGS_DRIFT",
    ):
        assert retired not in text, retired


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]


def test_router_contains_exact_fixed_role_triples() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    required = (
        "cross_task_routing=fixed_role_triples_from_router",
        "workflow_design_manager_route=019f9d2f-e0ea-7411-9fd7-386f45f76909|gpt-5.6-sol|high",
        "project_manager_route=019f9e4f-f4d0-7fe0-b214-c47fd034e84d|gpt-5.6-sol|xhigh",
        "external_review_operator_route=019f9c6a-9401-7ae0-ace5-dd827dccba2b|gpt-5.6-luna|medium",
    )
    for token in required:
        assert agents.count(token) == 1, token


def test_persistent_roles_use_router_triples_without_cache() -> None:
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert "cross_task_target_identity=fixed_router_role_triple" in text
        assert "cross_task_route_cache=forbidden" in text
        assert "cross_task_model_thinking_source=fixed_router_role_triple" in text


def test_static_review_registry_uses_router_triples() -> None:
    registry = json.loads(
        (ROOT / "docs/external-review/REVIEWER_CONVERSATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    contract = registry["intertask_transport_contract"]
    assert registry["schema_version"] == 36
    assert contract["cross_task_routing_skill"] == "$hmasd-cross-task-routing"
    assert contract["target_identity"] == "fixed_role_triple_from_AGENTS.md"
    assert contract["route_cache"] == "forbidden"
    assert contract["model_thinking_source"] == "fixed_role_triple_from_AGENTS.md"
    assert contract["payload_route_settings"] == "forbidden"
    assert (
        contract["route_replacement"]
        == "explicit_user_direction_then_workflow_design_commit"
    )


def test_dynamic_probe_script_is_retired() -> None:
    assert not RETIRED_PROBE.exists()


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
