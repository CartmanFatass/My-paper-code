from __future__ import annotations

import copy
import hashlib
import json

import pytest

from hmasd_pro_conversation_binding_test import _bind_args, _module


def _inputs():
    key = "em:alpha:convergence"
    prompt = "Read the unchanged fixed TASK and its frozen inputs."
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    request = {
        "request_id": "recovery-round", "direction_id": "alpha", "direction_ids": ["alpha"],
        "workflow_node": "em_convergence", "conversation_binding_key": key,
        "decision_authority": "pro_final", "requested_conversation_id": None,
        "reset_invalid_provider_context": True,
        "provider_context_reset_evidence": {
            "previous_request_id": "old-round", "reset_authority": "OWNER_DIRECT",
            "owner_instruction": "Rebind the positively verified never-sent operation with identical inputs.",
        },
        "prompt": prompt, "provider_requirement": {"model": "GPT-6 Astra", "mode": "Pro"},
    }
    operation = {
        "operationId": "11111111-1111-1111-1111-111111111111", "idempotencyKey": "old-round",
        "stableKey": key, "provider": "chatgpt", "productModel": "GPT-6 Astra", "reasoningEffort": "Pro",
        "conversationUrl": "https://chatgpt.com/", "conversationId": "__new__", "promptSha256": digest,
        "sendAttempted": False, "sendAttemptedAt": None, "providerUserMessageId": None,
        "providerAssistantMessageId": None, "observedConversationUrl": None,
        "observedConversationId": None, "archive": None,
    }
    prior = {
        "status": "VERIFIED_NONACCEPTANCE / CONVERSATION_UNRECOVERABLE",
        "request_id": "old-round", "stableKey": key, "old_operation_id": operation["operationId"],
        "old_operation": operation, "old_handoff": {"prompt_sha256": digest, "commit": "a" * 40},
        "old_tab": {"tab_id": "old-tab", "protected": False, "preserved": True, "stable_key": key},
        "old_operation_mutated": False, "durable_prior_receipts": ["old-operation-receipt.json"],
    }
    return request, prior


def test_rebind_preserves_old_evidence_and_only_binds_observed_matching_send(tmp_path):
    binder = _module("unaccepted_rebind_binder", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"version": 4, "bindings": {}, "directions": {}, "unrelated": {"keep": [1]}}))
    request, prior = _inputs()
    original_prior = copy.deepcopy(prior)
    pending = binder.prepare_unaccepted_first_binding_rebind(registry, request=request, prior=prior)
    pending_bytes = registry.read_bytes()
    assert prior == original_prior
    assert pending["send_click_count"] == 0
    assert pending["agentify_stable_key"] == binder._agentify_generation_key(request["conversation_binding_key"], request["request_id"])
    assert pending["request_history"][0]["recovery_audit"] == original_prior
    assert pending["conversation_id"] is None
    binder.prepare_unaccepted_first_binding_rebind(registry, request=request, prior=prior)
    assert registry.read_bytes() == pending_bytes
    args = _bind_args(
        registry, workflow_node="em_convergence", binding_key=request["conversation_binding_key"],
        direction_id="alpha", direction_ids=["alpha"], request_id=request["request_id"],
        conversation_id="22222222-2222-2222-2222-222222222222", reset_invalid_provider_context=True,
        provider_context_reset_evidence=request["provider_context_reset_evidence"],
    )
    args.prompt_sha256 = prior["old_operation"]["promptSha256"]
    args.underlying_model, args.thinking_effort = "GPT-6 Astra", "Pro"
    assert binder.bind(args) == 3
    assert registry.read_bytes() == pending_bytes
    args.observed_after_successful_send = True
    for field, wrong in (("prompt_sha256", "f" * 64), ("underlying_model", "GPT-5.6 Sol"), ("thinking_effort", "Standard")):
        value = getattr(args, field)
        setattr(args, field, wrong)
        assert binder.bind(args) == 3
        assert registry.read_bytes() == pending_bytes
        setattr(args, field, value)
    assert binder.bind(args) == 0
    accepted = json.loads(registry.read_text())
    record = accepted["bindings"][request["conversation_binding_key"]]
    assert record["state"] == "SEND_CONFIRMED" and record["send_click_count"] == 1
    assert record["request_history"][0]["recovery_audit"] == original_prior
    assert accepted["unrelated"] == {"keep": [1]}
    assert accepted["quarantined_conversations"] == {}
    assert binder.bind(args) == 0
    assert json.loads(registry.read_text())["bindings"][request["conversation_binding_key"]]["send_click_count"] == 1
    with pytest.raises(ValueError, match="existing binding"):
        binder.prepare_unaccepted_first_binding_rebind(registry, request=request, prior=prior)


@pytest.mark.parametrize("field,value", [
    ("sendAttempted", True), ("sendAttempted", None), ("sendAttempted", "false"),
    ("providerUserMessageId", "possible-user"), ("providerAssistantMessageId", "possible-assistant"),
    ("observedConversationId", "possible-conversation"), ("archive", {}),
    ("sendAttemptedAt", 1), ("conversationId", "concrete-id"),
    ("stableKey", "em:other:convergence"), ("promptSha256", "f" * 64),
])
def test_uncertain_accepted_or_mismatched_effect_never_mutates_registry(tmp_path, field, value):
    binder = _module("unaccepted_rebind_negative_binder", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    registry.write_text('{"bindings": {}, "directions": {}, "keep": true}')
    before = registry.read_bytes()
    request, prior = _inputs()
    prior["old_operation"][field] = value
    with pytest.raises(ValueError):
        binder.prepare_unaccepted_first_binding_rebind(registry, request=request, prior=prior)
    assert registry.read_bytes() == before


def test_missing_proof_changed_request_and_busy_binding_are_zero_mutation(tmp_path):
    binder = _module("unaccepted_rebind_conflict_binder", "bind_conversation.py")
    registry = tmp_path / "registry.json"
    registry.write_text('{"bindings": {}, "directions": {}}')
    initial = registry.read_bytes()
    request, prior = _inputs()
    missing = copy.deepcopy(prior)
    del missing["old_operation"]["providerUserMessageId"]
    variants = [
        (request, missing), ({**request, "prompt": request["prompt"] + "changed"}, prior),
        ({**request, "request_id": "old-round"}, prior),
        ({**request, "reset_invalid_provider_context": False}, prior),
    ]
    for candidate, audit in variants:
        with pytest.raises(ValueError):
            binder.prepare_unaccepted_first_binding_rebind(registry, request=candidate, prior=audit)
        assert registry.read_bytes() == initial
    binder.prepare_unaccepted_first_binding_rebind(registry, request=request, prior=prior)
    pending = registry.read_bytes()
    with pytest.raises(ValueError, match="existing binding"):
        binder.prepare_unaccepted_first_binding_rebind(registry, request={**request, "request_id": "another-recovery"}, prior=prior)
    assert registry.read_bytes() == pending
