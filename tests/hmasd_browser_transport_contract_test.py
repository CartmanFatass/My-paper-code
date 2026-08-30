from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import hmasd_state
_validate_transport_facts = getattr(hmasd_state, "_validate_transport_facts")
_validate_transport_transition = getattr(hmasd_state, "_validate_transport_transition")


REPO_ROOT = Path(__file__).resolve().parents[1]
BROWSER_AGENT = REPO_ROOT / ".omp" / "agents" / "hmasd-browser-transport.md"
BROWSER_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-browser-transport" / "SKILL.md"
ROOT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
RESULT_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json"
RUNTIME_SCHEMA = REPO_ROOT / "scripts" / "schemas" / "hmasd_runtime_browser_assignments.schema.json"


def _transport_facts(**changes: object) -> dict[str, object]:
    result: dict[str, object] = {
        "provider": "chatgpt",
        "product_model": "GPT-5.6 Sol",
        "reasoning_effort": "Pro",
        "operation_id": "operation-1",
        "idempotency_key": "idempotency:1",
        "operation_ref": "agentify-operation:operation-1",
        "provider_conversation_ref": None,
        "provider_conversation_id": None,
        "phase": "PREPARE_UI",
        "commitment": "ZERO_PROVEN",
        "recoverability": "PRECOMMIT_REPAIR",
        "observability": "FRESH_COMPLETE",
        "message_capability": "AVAILABLE",
        "failure": {"locus": "PRECOMMIT_UI", "code": "DIRECT_NO_ACTIVATION_RECEIPT"},
        "provider_user_message_count": 0,
        "send_activation_count": 0,
        "user_message_id": None,
        "assistant_message_id": None,
        "archive_ref": None,
        "handoff_ref": None,
    }
    result.update(changes)
    return result


def _result(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 2,
        "role": "hmasd-browser-transport",
        "logical_identity": "BrowserTransport",
        "generation": 1,
        "assignment_id": "transport-1",
        "status": "PARTIAL",
        "materiality": "LOCAL",
        "summary": "Observed current transport facts.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_actions": [],
        "payload": {
            "kind": "transport",
            "browser_identity": "BrowserTransport",
            "transport_assignment": "transport-1",
            "requester": "Root",
            "mode": "INNOVATOR",
            "effect_ref": None,
            "browser_tab_ref": None,
            **payload,
        },
    }


def test_current_schemas_expose_only_orthogonal_transport_fields() -> None:
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    assert result_schema["properties"]["schema_version"]["const"] == 2
    assert runtime_schema["properties"]["schema_version"]["const"] == 2
    flat_field = "_".join(("transport", "state"))
    contracts = (
        result_schema["$defs"]["transport_payload"],
        runtime_schema["$defs"]["assignment"],
    )
    for contract in contracts:
        required = set(contract["required"])
        assert flat_field not in required
        assert {
            "product_model",
            "reasoning_effort",
            "phase",
            "commitment",
            "recoverability",
            "observability",
            "message_capability",
            "failure",
            "provider_user_message_count",
            "send_activation_count",
            "user_message_id",
            "assistant_message_id",
        } <= required


def test_proven_zero_failure_remains_repairable_in_same_assignment() -> None:
    document = _result(_transport_facts())
    assert hmasd_state.validate_document("agent_result", document) == document
    old_flat = copy.deepcopy(document)
    payload = old_flat["payload"]
    assert isinstance(payload, dict)
    payload["_".join(("transport", "state"))] = "_".join(("ZERO", "SEND", "FAILED"))
    with pytest.raises(hmasd_state.ValidationError):
        hmasd_state.validate_document("agent_result", old_flat)


def test_reserved_crash_becomes_sealed_observe_only() -> None:
    reserved = _transport_facts(
        phase="ARMED",
        message_capability="RESERVED",
        failure={"locus": "NONE", "code": "NONE"},
    )
    unresolved = _transport_facts(
        phase="VERIFY_COMMITMENT",
        commitment="UNRESOLVED",
        recoverability="OBSERVE_ONLY",
        observability="LOST",
        message_capability="SEALED",
        failure={"locus": "COMMIT_BOUNDARY", "code": "NATIVE_ACTIVATION_UNRESOLVED"},
    )
    _validate_transport_facts(reserved, "reserved")
    _validate_transport_facts(unresolved, "unresolved")
    _validate_transport_transition(reserved, unresolved, "assignment")
    with pytest.raises(hmasd_state.ObservedConflictError):
        _validate_transport_transition(reserved, copy.deepcopy(reserved), "assignment")


def test_direct_no_activation_receipt_releases_reservation() -> None:
    reserved = _transport_facts(
        phase="ARMED",
        message_capability="RESERVED",
        failure={"locus": "NONE", "code": "NONE"},
    )
    released = _transport_facts()
    _validate_transport_transition(reserved, released, "assignment")
    wrong_receipt = copy.deepcopy(released)
    wrong_receipt["failure"] = {"locus": "PRECOMMIT_UI", "code": "UI_FAILED"}
    with pytest.raises(hmasd_state.ObservedConflictError):
        _validate_transport_transition(reserved, wrong_receipt, "assignment")


def test_sealed_unresolved_can_advance_by_later_exact_observation() -> None:
    unresolved = _transport_facts(
        provider_conversation_ref="https://chatgpt.com/c/conversation-1",
        provider_conversation_id="conversation-1",
        phase="VERIFY_COMMITMENT",
        commitment="UNRESOLVED",
        recoverability="OBSERVE_ONLY",
        observability="FRESH_PARTIAL",
        message_capability="SEALED",
        failure={"locus": "COMMIT_BOUNDARY", "code": "ACTIVATION_RECEIPT_LOST"},
    )
    exact = _transport_facts(
        provider_conversation_ref="https://chatgpt.com/c/conversation-1",
        provider_conversation_id="conversation-1",
        phase="WAIT_RESPONSE",
        commitment="ONE_EXACT",
        recoverability="POSTCOMMIT_RECOVERY",
        observability="FRESH_COMPLETE",
        message_capability="SEALED",
        failure={"locus": "NONE", "code": "NONE"},
        provider_user_message_count=1,
        send_activation_count=0,
        user_message_id="user-message-1",
    )
    _validate_transport_facts(unresolved, "unresolved")
    _validate_transport_facts(exact, "exact")
    _validate_transport_transition(unresolved, exact, "assignment")


def test_natural_completion_requires_exact_ids_counts_and_archive() -> None:
    terminal = _transport_facts(
        provider_conversation_ref="https://chatgpt.com/c/conversation-1",
        provider_conversation_id="conversation-1",
        phase="TERMINAL",
        commitment="ONE_EXACT",
        recoverability="NONE",
        observability="FRESH_COMPLETE",
        message_capability="SEALED",
        failure={"locus": "NONE", "code": "NONE"},
        provider_user_message_count=1,
        send_activation_count=0,
        user_message_id="user-message-1",
        assistant_message_id="assistant-message-1",
        archive_ref={"path": "response.md", "sha256": "a" * 64},
    )
    _validate_transport_facts(terminal, "terminal")
    inconsistent = copy.deepcopy(terminal)
    inconsistent["provider_user_message_count"] = 0
    with pytest.raises(hmasd_state.ValidationError):
        _validate_transport_facts(inconsistent, "terminal")


def test_chatgpt_product_model_and_reasoning_effort_are_mandatory() -> None:
    for field, value in (("product_model", "GPT-5.6"), ("reasoning_effort", "High")):
        with pytest.raises(hmasd_state.ValidationError):
            _validate_transport_facts(_transport_facts(**{field: value}), "assignment")


def test_gemini_uses_explicit_null_reasoning_effort() -> None:
    facts = _transport_facts(
        provider="gemini",
        product_model="Gemini 3.1 Pro",
        reasoning_effort=None,
    )
    _validate_transport_facts(facts, "assignment")
    assert hmasd_state.validate_document("agent_result", _result(facts))

    with pytest.raises(hmasd_state.ValidationError):
        _validate_transport_facts(
            {**facts, "reasoning_effort": "Pro"},
            "assignment",
        )


def test_current_skills_authorize_one_message_and_same_assignment_repair() -> None:
    text = BROWSER_SKILL.read_text(encoding="utf-8")
    root = ROOT_SKILL.read_text(encoding="utf-8")
    agent = BROWSER_AGENT.read_text(encoding="utf-8")
    for contract in (text, root, agent):
        assert "exactly one provider-visible user message" in " ".join(contract.lower().split())
        assert "GPT-5.6 Sol" in contract
        assert "reasoning effort" in contract
    assert "continue automatically" in " ".join(text.split())
    assert "same assignment" in root
    assert "fresh operation solely" in root
    assert "_".join(("transport", "state")) not in root
