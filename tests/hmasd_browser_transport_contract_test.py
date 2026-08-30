from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import hmasd_state

_validate_transport_facts = getattr(hmasd_state, "_validate_transport_facts")
_validate_transport_update = getattr(hmasd_state, "_validate_transport_update")


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
        "target_conversation_url": None,
        "target_conversation_id": None,
        "prompt_ref": {"path": "prompt.md", "sha256": "1" * 64},
        "response_path": "response.md",
        "operation_id": "operation-1",
        "idempotency_key": "idempotency:1",
        "request_fingerprint": "2" * 64,
        "stable_key": "stable:1",
        "operation_ref": {"path": "operation.json", "sha256": "3" * 64},
        "created_at": 1788000000000,
        "updated_at": 1788000000000,
        "send_attempted": False,
        "send_attempted_at": None,
        "observed_conversation_url": None,
        "observed_conversation_id": None,
        "provider_user_message_id": None,
        "provider_assistant_message_id": None,
        "archive": None,
        "error": {"code": "PRE_SEND_UI"},
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
            **payload,
        },
    }


def test_current_schemas_expose_only_minimal_receipt_facts() -> None:
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    contracts = (
        result_schema["$defs"]["transport_payload"],
        runtime_schema["$defs"]["assignment"],
    )
    deleted = {
        "phase",
        "commitment",
        "recoverability",
        "observability",
        "message_capability",
        "failure",
        "provider_user_message_count",
        "send_activation_count",
    }
    for contract in contracts:
        required = set(contract["required"])
        assert not deleted & required
        assert {
            "request_fingerprint",
            "send_attempted",
            "send_attempted_at",
            "provider_user_message_id",
            "provider_assistant_message_id",
            "archive",
            "error",
        } <= required


def test_pre_send_error_is_retryable_in_same_operation() -> None:
    failed = _transport_facts()
    retrying = _transport_facts(error=None, updated_at=1788000001000)
    _validate_transport_facts(failed, "failed")
    _validate_transport_facts(retrying, "retrying")
    _validate_transport_update(failed, retrying, "operation")
    assert hmasd_state.validate_document("agent_result", _result(retrying))


def test_identity_is_immutable_and_send_attempt_is_monotonic() -> None:
    before = _transport_facts(error=None)
    attempted = _transport_facts(
        error=None,
        send_attempted=True,
        send_attempted_at=1788000001000,
        updated_at=1788000001000,
    )
    _validate_transport_update(before, attempted, "operation")

    resend_capable = copy.deepcopy(attempted)
    resend_capable["send_attempted"] = False
    resend_capable["send_attempted_at"] = None
    with pytest.raises(hmasd_state.ObservedConflictError):
        _validate_transport_update(attempted, resend_capable, "operation")

    changed_identity = copy.deepcopy(attempted)
    changed_identity["idempotency_key"] = "different"
    with pytest.raises(hmasd_state.ObservedConflictError):
        _validate_transport_update(attempted, changed_identity, "operation")


def test_ids_and_archive_are_append_only() -> None:
    attempted = _transport_facts(
        error=None,
        send_attempted=True,
        send_attempted_at=1788000001000,
    )
    observed = _transport_facts(
        error=None,
        send_attempted=True,
        send_attempted_at=1788000001000,
        observed_conversation_url="https://chatgpt.com/c/conversation-1",
        observed_conversation_id="conversation-1",
        provider_user_message_id="user-1",
    )
    complete = {
        **observed,
        "provider_assistant_message_id": "assistant-1",
        "archive": {
            "path": "response.md",
            "sha256": "4" * 64,
            "size_bytes": 5,
            "projection": "exact",
            "verified_at": 1788000000000,
        },
    }
    _validate_transport_update(attempted, observed, "operation")
    _validate_transport_facts(complete, "complete")
    _validate_transport_update(observed, complete, "operation")

    removed = copy.deepcopy(complete)
    removed["provider_user_message_id"] = None
    with pytest.raises(hmasd_state.ObservedConflictError):
        _validate_transport_update(complete, removed, "operation")


def test_minimal_receipt_invariants_reject_impossible_facts() -> None:
    with pytest.raises(hmasd_state.ValidationError, match="paired"):
        _validate_transport_facts(
            _transport_facts(send_attempted=True, send_attempted_at=None),
            "operation",
        )
    with pytest.raises(hmasd_state.ValidationError, match="requires send_attempted"):
        _validate_transport_facts(
            _transport_facts(provider_user_message_id="user-1"),
            "operation",
        )
    with pytest.raises(hmasd_state.ValidationError, match="requires provider_user"):
        _validate_transport_facts(
            _transport_facts(
                send_attempted=True,
                send_attempted_at=1788000001000,
                provider_assistant_message_id="assistant-1",
            ),
            "operation",
        )


def test_active_contract_is_one_linear_native_send_path() -> None:
    browser = BROWSER_SKILL.read_text(encoding="utf-8")
    root = ROOT_SKILL.read_text(encoding="utf-8")
    agent = BROWSER_AGENT.read_text(encoding="utf-8")
    combined = "\n".join((browser, root, agent))
    assert "persist `send_attempted: true` immediately before" in browser
    assert "one hit-tested native pointer activation" in browser
    assert "after `send_attempted`" in browser
    assert "never activate Send again" in browser
    for deleted in (
        "message_capability",
        "recoverability",
        "send_activation_count",
        "provider_user_message_count",
        "human interlock",
        "waiver",
    ):
        assert deleted not in combined.lower()
