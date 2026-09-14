from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".agents/skills/hmasd-chatgpt-pro-transport/scripts/transport_contract.py"
spec = importlib.util.spec_from_file_location("recovery_contract", SCRIPT)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def record():
    return {"state": "SEND_UNCERTAIN", "request_id": "r1",
            "conversation_binding_key": "em:alpha:convergence", "direction_id": "alpha",
            "prompt_sha256": "a" * 64, "conversation_id": "c1",
            "provider_url": "https://chatgpt.com/c/c1", "tab_id": "original-tab",
            "parent_thread_id": "11111111-1111-1111-1111-111111111111",
            "send_click_count": 1, "updated_at": "2026-09-11T12:00:00Z",
            "timestamps": {"send_attempted_at": "2026-09-11T12:00:00Z"}}


def reconcile(rec, **changes):
    args = {key: rec.get(key) for key in ("request_id", "conversation_binding_key",
            "prompt_sha256", "conversation_id", "provider_url", "tab_id")}
    args.update(outcome="NOT_ACCEPTED", evidence="provider shows original composer and no accepted turn",
                observed_at="2026-09-11T12:01:00Z", repaired_surface="restored logged-in composer",
                exact_composer_payload=True, current_user_absent=True, generation_absent=True,
                exact_paired_user=True, message_identity_kind="PROVIDER",
                now="2026-09-11T12:01:00Z")
    args.update(changes)
    return contract.reconcile_send_effect(rec, **args)


@pytest.mark.parametrize("state", ["SEND_UNCERTAIN", "BLOCKED", "SEND_FAILED_PRE_SEND"])
def test_verified_nonacceptance_rearms_once_preserving_original_attempt(state):
    rec = record()
    rec["state"] = state
    before = copy.deepcopy(rec)
    reconcile(rec)
    assert rec["state"] == "PROMPT_READY"
    assert rec["send_click_count"] == 1
    assert rec["send_reconciliation_history"][0]["prior_record"] == before
    contract.transition_record(rec, "SEND_ATTEMPTED", now="2026-09-11T12:02:00Z")
    contract.transition_record(rec, "SEND_UNCERTAIN", now="2026-09-11T12:02:01Z")
    before = copy.deepcopy(rec)
    with pytest.raises(ValueError):
        reconcile(rec, observed_at="2026-09-11T12:03:00Z", now="2026-09-11T12:03:00Z")
    assert rec == before


def test_confirmed_effect_observes_without_another_send():
    rec = record()
    reconcile(rec, outcome="ACCEPTED", user_message_id="actual-user-turn", repaired_surface=None)
    assert rec["state"] == "SEND_CONFIRMED"
    assert rec["user_message_id"] == "actual-user-turn"
    assert rec["send_click_count"] == 1
    with pytest.raises(ValueError):
        contract.transition_record(rec, "SEND_ATTEMPTED")
    contract.transition_record(rec, "WAITING_GENERATION")


def test_home_tab_recovery_keeps_absent_conversation_id():
    rec = record()
    rec.update(conversation_id=None, provider_url="https://chatgpt.com/", state="SEND_FAILED_PRE_SEND")
    reconcile(rec)
    assert rec["conversation_id"] is None
    assert rec["tab_id"] == "original-tab"
    assert rec["provider_url"] == "https://chatgpt.com/"


def test_distinct_repair_can_rearm_after_new_proven_nonacceptance():
    rec = record()
    reconcile(rec)
    contract.transition_record(rec, "SEND_ATTEMPTED", now="2026-09-11T12:02:00Z")
    contract.transition_record(rec, "SEND_UNCERTAIN", now="2026-09-11T12:02:01Z")
    reconcile(rec, repaired_surface="repaired upload finalization", evidence="new turn absent after upload repair",
              observed_at="2026-09-11T12:03:00Z", now="2026-09-11T12:03:00Z")
    assert len(rec["send_reconciliation_history"]) == 2
    assert rec["send_click_count"] == 1


def test_dom_identity_is_labeled_without_fabricating_provider_uuid():
    rec = record()
    reconcile(rec, outcome="ACCEPTED", user_message_id="exact original payload DOM turn 3",
              message_identity_kind="DOM")
    assert rec["user_message_identity_kind"] == "DOM"


def test_prebinding_blocker_uses_request_binding_and_parent_without_uuid():
    rec = record()
    rec.update(conversation_id=None, provider_url="https://chatgpt.com/")
    contract.stage_blocker_receipt(rec, "SEND_UNCERTAIN", "no accepted turn found yet")
    assert rec["conversation_id"] is None
    receipt = rec["return_receipt"]
    assert "PREBINDING" in receipt["message_key"]
    assert receipt["status"] == "PENDING"
    assert receipt["destination_thread_id"] == rec["parent_thread_id"]


@pytest.mark.parametrize("changes", [
    {"request_id": "other"}, {"conversation_binding_key": "other"},
    {"prompt_sha256": "b" * 64}, {"conversation_id": "other"},
    {"provider_url": "https://chatgpt.com/c/other"}, {"tab_id": "other-tab"},
    {"outcome": "UNCERTAIN"}, {"evidence": ""}, {"repaired_surface": ""},
    {"observed_at": "2026-09-11T11:59:00Z"},
    {"outcome": "ACCEPTED", "user_message_id": None},
    {"exact_composer_payload": False}, {"current_user_absent": False}, {"generation_absent": False},
    {"outcome": "ACCEPTED", "user_message_id": "u1", "exact_paired_user": False},
    {"outcome": "ACCEPTED", "user_message_id": "manual turn", "message_identity_kind": None},
])
def test_unsafe_reconciliation_refuses_without_mutation(changes):
    rec = record()
    before = copy.deepcopy(rec)
    with pytest.raises(ValueError):
        reconcile(rec, **changes)
    assert rec == before


@pytest.mark.parametrize("prior", [
    {"user_message_id": "u1"}, {"send_evidence": {"user_node_exact": True}},
    {"timestamps": {"sent_at": "2026-09-11T12:00:00Z"}},
    {"timestamps": {"generation_started_at": "2026-09-11T12:00:00Z"}},
    {"timestamps": {"completed_at": "2026-09-11T12:00:00Z"}},
    {"timestamps": {"captured_at": "2026-09-11T12:00:00Z"}},
    {"timestamps": {"archived_at": "2026-09-11T12:00:00Z"}},
    {"response_sha256": "b" * 64},
    {"send_evidence": {"observed_after_successful_send": True}},
    {"send_reconciliation_history": [{"outcome": "ACCEPTED"}]},
])
def test_nonacceptance_refuses_preserved_acceptance(prior):
    rec = record()
    rec["state"] = "BLOCKED"
    rec.update(prior)
    before = copy.deepcopy(rec)
    with pytest.raises(ValueError):
        reconcile(rec)
    assert rec == before


def test_null_completion_placeholders_do_not_block_proven_nonacceptance():
    rec = record()
    rec.update(response_sha256=None, archive={"response_file": None})
    rec["timestamps"].update(completed_at=None, captured_at=None, archived_at=None)
    reconcile(rec)
    assert rec["state"] == "PROMPT_READY"


def test_accepted_requires_real_conversation_binding():
    rec = record()
    rec.update(conversation_id=None, provider_url="https://chatgpt.com/")
    before = copy.deepcopy(rec)
    with pytest.raises(ValueError):
        reconcile(rec, outcome="ACCEPTED", user_message_id="u1")
    assert rec == before


@pytest.mark.parametrize("status", ["SENT", "UNCERTAIN", "FAILED", "PENDING"])
def test_completion_preserves_blocker_and_stages_distinct_receipt(status):
    rec = record()
    contract.stage_blocker_receipt(rec, "SEND_UNCERTAIN", "send effect unknown")
    if status != "PENDING":
        contract.record_receipt_result(rec, status, delivery_status="actual tool result")
    blocker = copy.deepcopy(rec["return_receipt"])
    rec["state"] = "ARCHIVED"
    contract.stage_receipt(rec, {"response_file": "full.md"}, "c" * 64)
    assert rec["return_receipt_history"] == [blocker]
    completion = copy.deepcopy(rec["return_receipt"])
    assert completion["status"] == "PENDING" and completion["attempt_count"] == 0
    assert completion["message_key"] != blocker["message_key"]
    assert completion["destination_thread_id"] == blocker["parent_thread_id"]
    assert "delivery_status" not in completion and "sent_at" not in completion
    contract.stage_receipt(rec, {"response_file": "full.md"}, "c" * 64)
    assert rec["return_receipt"] == completion
    assert rec["return_receipt_history"] == [blocker]
