from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-cross-task-routing/SKILL.md"
UI = ROOT / ".agents/skills/hmasd-cross-task-routing/agents/openai.yaml"
PERSISTENT_ROLES = (
    ROOT / ".agents/roles/PROJECT_MANAGER.md",
    ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ROOT / ".agents/roles/EXTERNAL_REVIEW_OPERATOR.md",
)


def test_cross_task_routing_protocol_is_bounded_and_fail_closed() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    required = (
        "Conversation-local route cache",
        "at most three candidates",
        "within 120 wall-clock seconds",
        "Polling is forbidden",
        "ROLE_ROUTE_PROBE",
        "ROLE_ROUTE_CONFIRM",
        "ROLE_ROUTE_ANNOUNCE",
        "codex_delegation.source_thread_id",
        "ROUTE_CONFIRMED",
        "ROUTE_AMBIGUOUS",
        "ROUTE_UNAVAILABLE",
        "omitting both `model` and `thinking`",
        "do not automatically resend",
    )
    for token in required:
        assert token in text, token


def test_cross_task_routing_skill_is_explicit_only() -> None:
    interface = yaml.safe_load(UI.read_text(encoding="utf-8"))
    assert interface["policy"]["allow_implicit_invocation"] is False
    assert "$hmasd-cross-task-routing" in interface["interface"]["default_prompt"]


def test_persistent_roles_do_not_pin_live_session_model_or_effort() -> None:
    forbidden = re.compile(
        r"(?m)^(?:session|model|reasoning_effort|\w+_(?:target|return)_"
        r"(?:session|model|effort))="
    )
    for path in PERSISTENT_ROLES:
        text = path.read_text(encoding="utf-8")
        assert forbidden.search(text) is None, path
        assert "cross_task_routing_skill=hmasd-cross-task-routing" in text
        assert "cross_task_model_thinking_override=omitted" in text


def test_static_review_registry_contains_no_live_codex_route() -> None:
    registry = json.loads(
        (ROOT / "docs/external-review/REVIEWER_CONVERSATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    contract = registry["intertask_transport_contract"]
    assert contract["cross_task_routing_skill"] == "$hmasd-cross-task-routing"
    assert contract["model_thinking_override"] == "omitted"
    forbidden = {
        "operator_task_id",
        "operator_model",
        "operator_effort",
        "project_manager_return_task_id",
        "project_manager_return_model",
        "project_manager_return_effort",
        "cross_task_send_requires_explicit_model_effort",
    }
    assert forbidden.isdisjoint(contract)
