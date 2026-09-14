from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from hmasd_pro_conversation_binding_test import _bind_args, _module


def test_new_round_clears_all_request_facts_and_preserves_complete_history(tmp_path: Path) -> None:
    binder = _module("transport_round_reset_binder", "bind_conversation.py")
    args = _bind_args(
        tmp_path / "registry.json",
        workflow_node="em_innovator",
        binding_key="em:alpha:innovator",
        direction_id="alpha",
        direction_ids=["alpha"],
        conversation_id="55555555-5555-5555-5555-555555555555",
        request_id="old-round",
    )
    assert binder.bind(args) == 0
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    key = args.conversation_binding_key
    old = registry["bindings"][key]
    stale = {
        "timestamps": {"archived_at": "2026-09-10T00:00:00Z"},
        "user_message_id": "old-user",
        "assistant_message_id": "old-assistant",
        "archive_status": "ARCHIVED",
        "scientific_decision_formed": True,
        "send_attempted_at": "2026-09-09T00:00:00Z",
        "send_confirmed_at": "2026-09-09T00:00:01Z",
        "generation_started_at": "2026-09-09T00:00:02Z",
        "natural_completion_observed": True,
        "github_delivery": {"status": "DELIVERED", "sha": "old-sha"},
        "send_evidence": {"user_node_exact": True, "send_click_count": 1},
        "unanticipated_request_observation": {"nested": ["old-value"]},
    }
    old.update(stale)
    old.update(
        state="ARCHIVED",
        archive={"response_file": "old-response.md"},
        response_sha256="f" * 64,
        request_history=[{"request_id": "earlier-round", "custom_evidence": "preserve"}],
        quarantined_provider_conversations=[{"conversation_id": "quarantined-id"}],
        last_provider_context_reset={"evidence": {"owner_direct": True}},
    )
    original = copy.deepcopy(old)
    registry["directions"][args.direction_id] = copy.deepcopy(old)
    args.registry.write_text(json.dumps(registry), encoding="utf-8")

    args.request_id = "new-round"
    args.source_thread_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    args.parent_thread_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    args.operator_thread_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    assert binder.bind(args) == 0
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    current = registry["bindings"][key]
    assert all(field not in current for field in stale)
    assert current["request_history"][:-1] == original["request_history"]
    archived = dict(current["request_history"][-1])
    assert archived.pop("binding_reconciliation")["kind"] == "archived_direction_mirror"
    assert archived == {
        field: value for field, value in original.items() if field != "request_history"
    }
    for field in (
        "conversation_binding_key", "workflow_node", "direction_id", "decision_authority",
        "conversation_id", "provider_url", "quarantined_provider_conversations",
        "last_provider_context_reset",
    ):
        assert current[field] == original[field]
    assert current["state"] == "DIRECTION_VERIFIED"
    assert current["send_click_count"] == 0
    assert current["archive"] is None
    assert current["response_sha256"] is None
    assert current["monitor"]["last_observed_at"] is None
    assert current["source_thread_id"] == args.source_thread_id
    assert current["creator_thread_id"] == args.source_thread_id
    assert current["parent_thread_id"] == args.parent_thread_id
    assert current["operator_thread_id"] == args.operator_thread_id
    assert current["return_receipt"]["status"] == "PENDING"
    assert current["return_receipt"]["attempt_count"] == 0
    assert registry["directions"][args.direction_id] == current
    assert binder.bind(args) == 0
    assert json.loads(args.registry.read_text(encoding="utf-8"))["bindings"][key] == current


@pytest.mark.parametrize("location", ["bindings", "directions"])
def test_observed_prebinding_recovery_preserves_attempts_and_receipts(tmp_path: Path, location: str) -> None:
    binder = _module("transport_prebinding_recovery_binder", "bind_conversation.py")
    args = _bind_args(
        tmp_path / "registry.json", workflow_node="em_innovator",
        binding_key="em:alpha:innovator", direction_id="alpha", direction_ids=["alpha"],
        conversation_id="55555555-5555-5555-5555-555555555555", request_id="recovered-round",
    )
    args.tab_id = "original-home-tab"
    assert binder.bind(args) == 0
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    old = registry["bindings"][args.conversation_binding_key]
    old.update(
        conversation_id=None, provider_url="https://chatgpt.com/", state="SEND_ATTEMPTED",
        send_click_count=3,
        send_reconciliation_history=[{"outcome": "NOT_ACCEPTED", "prior_record": {"send_click_count": 2}}],
        return_receipt={"status": "SENT", "attempt_count": 1, "message_key": "blocker-receipt"},
        timestamps={"send_attempted_at": "2026-09-11T00:00:00Z"},
    )
    registry["bindings"] = {args.conversation_binding_key: old} if location == "bindings" else {}
    registry["directions"] = {args.direction_id: old}
    args.registry.write_text(json.dumps(registry), encoding="utf-8")
    before = args.registry.read_bytes()
    assert binder.bind(args) == 3
    assert args.registry.read_bytes() == before
    args.observed_after_successful_send = True
    args.prompt_sha256 = "a" * 64
    assert binder.bind(args) == 3
    assert args.registry.read_bytes() == before
    args.prompt_sha256 = old["prompt_sha256"]
    args.tab_id = "other-tab"
    assert binder.bind(args) == 3
    assert args.registry.read_bytes() == before
    args.tab_id = old["tab_id"]
    assert binder.bind(args) == 0
    current = json.loads(args.registry.read_text(encoding="utf-8"))["bindings"][args.conversation_binding_key]
    for field in old.keys() - {"conversation_id", "provider_url", "state", "monitor", "send_evidence"}:
        assert current[field] == old[field]
    assert current["conversation_id"] == args.conversation_id
    assert current["provider_url"] == args.provider_url
    assert current["state"] == "SEND_CONFIRMED"
    assert current["send_evidence"]["observed_after_successful_send"] is True
    assert current["monitor"]["identity_key"] == binder.monitor_identity_key(current)
    assert binder.bind(args) == 0
    assert json.loads(args.registry.read_text(encoding="utf-8"))["bindings"][args.conversation_binding_key] == current
    contract = _module("transport_prebinding_composition_contract", "transport_contract.py")
    current["state"] = "BLOCKED"
    blocked = copy.deepcopy(current)
    with pytest.raises(ValueError, match="accepted"):
        contract.reconcile_send_effect(
            current, request_id=args.request_id, conversation_binding_key=args.conversation_binding_key,
            prompt_sha256=args.prompt_sha256, conversation_id=args.conversation_id,
            provider_url=args.provider_url, tab_id=args.tab_id, outcome="NOT_ACCEPTED",
            evidence="fresh empty composer", observed_at="2026-09-11T01:00:00Z",
            now="2026-09-11T01:00:01Z", repaired_surface="refreshed tab",
            exact_composer_payload=True, current_user_absent=True, generation_absent=True,
        )
    assert current == blocked
