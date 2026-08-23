import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

import tools.codex_supervisor.managed_packet_send as managed_packet_send_module
import tools.codex_supervisor.semantic_bridge as semantic_bridge_module

from tests.codex_supervisor.helpers import ingest_recorded_command, record_completed_agent_item
from tests.codex_supervisor.mailbox_fixtures import activate_binding, seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_semantic_mvp.actor_registry import register_session_root
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.managed_packet_send import ManagedPacketSender
from tools.codex_supervisor.managed_models import BindingState, HistoryTrust, ThreadOrigin


def _ready_binding(tmp_path: Path):
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread_for_tests(binding_id, "thr_cmd")
    store.mark_verification_required(binding_id)
    return seeded, store, CommandGateway(store, seeded["bridge"])


def _assert_semantic_writer_blocked(path: Path) -> None:
    writer = sqlite3.connect(path, timeout=0.0, isolation_level=None)
    try:
        writer.execute("PRAGMA busy_timeout = 0")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            writer.execute("BEGIN IMMEDIATE")
    finally:
        writer.close()


def test_no_control_action_and_duplicate(tmp_path: Path) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    first = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_1",
        text="no envelope",
        item_id="itm_turn_1",
    )
    assert first["validation_state"] == "APPLIED"
    raw_seq = seeded["supervisor"].connection.execute(
        "SELECT raw_message_seq FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()[0]
    second = gateway.ingest_final_item(raw_message_seq=int(raw_seq))
    assert second["validation_state"] == "DUPLICATE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_reanchor_and_stale_and_unbound_thread(tmp_path: Path) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(payload) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    applied = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_ack",
        text=text,
        item_id="itm_ack",
    )
    assert applied["validation_state"] == "APPLIED"
    with pytest.raises(CommandGatewayError):
        ingest_recorded_command(
            gateway,
            seeded["supervisor"],
            thread_id="thr_other",
            turn_id="turn_ack2",
            text="x",
            item_id="itm_other",
        )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_bad",
        text="x",
        item_id="itm_bad",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE item_snapshots SET lifecycle = 'STARTED' WHERE item_id = 'itm_bad'"
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(CommandGatewayError):
        gateway.ingest_final_item(raw_message_seq=seq)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize(
    "action,inner",
    [
        ("MAILBOX_ACK", {"message_ids": ["msg_missing"]}),
        ("MAILBOX_INTAKE", {"items": [{"message_id": "msg_missing", "intake_kind": "READ"}]}),
        ("MANAGED_PACKET_SEND", {"packet_kind": "X", "target_alias": "root", "payload_ref": "ref", "marker": "marker-stale"}),
        ("CONTEXT_REANCHOR_ACK", {}),
    ],
)
def test_stale_currentness_rejects_every_mutating_action_before_effect(
    tmp_path: Path, action: str, inner: dict
) -> None:
    seeded, store, gateway = _ready_binding(tmp_path)
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": action,
        "expected": {
            "checkpoint_id": "ctx_stale" if action == "CONTEXT_REANCHOR_ACK" else snapshot.checkpoint_id,
            "state_version": snapshot.state_version + 1,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": inner,
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(payload) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    with pytest.raises(CommandGatewayError, match="currentness"):
        ingest_recorded_command(
            gateway, seeded["supervisor"], thread_id="thr_cmd",
            turn_id=f"turn_{action}", text=text, item_id=f"item_{action}"
        )
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_command_receipts"
    ).fetchone()[0] == 0
    assert store.binding_for_thread("thr_cmd").binding_state is BindingState.VERIFICATION_REQUIRED
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_holds_semantic_writer_guard_through_reanchor_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded, _store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    original = semantic_bridge_module.context_reanchor_ack
    observed = {"blocked_at_effect": False}

    def checked_reanchor(*args, **kwargs):
        _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
        observed["blocked_at_effect"] = True
        return original(*args, **kwargs)

    monkeypatch.setattr(
        semantic_bridge_module,
        "context_reanchor_ack",
        checked_reanchor,
    )
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(payload)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    applied = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_guarded_ack",
        text=text,
        item_id="item_guarded_ack",
    )
    assert applied["validation_state"] == "APPLIED"
    assert observed["blocked_at_effect"] is True
    writer = sqlite3.connect(
        seeded["bridge"].semantic_state_path,
        timeout=0.0,
        isolation_level=None,
    )
    try:
        writer.execute("BEGIN IMMEDIATE")
        writer.rollback()
    finally:
        writer.close()
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_records_reanchor_receipt_only_after_semantic_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded, _store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    original_record = seeded["supervisor"].record_command_receipt
    observed = {"durable_before_receipt": False}

    def checked_record(**kwargs):
        if kwargs["effect_kind"] == "CONTEXT_REANCHOR_ACK":
            reader = sqlite3.connect(seeded["bridge"].semantic_state_path)
            try:
                ack_id = str(kwargs["result"]["ack_id"])
                assert reader.execute(
                    "SELECT 1 FROM reanchor_acks WHERE ack_id = ?", (ack_id,)
                ).fetchone() is not None
                assert reader.execute(
                    "SELECT state FROM obligations WHERE subject = ?",
                    (checkpoint["checkpoint_id"],),
                ).fetchone()[0] == "RESOLVED"
                observed["durable_before_receipt"] = True
            finally:
                reader.close()
        return original_record(**kwargs)

    monkeypatch.setattr(seeded["supervisor"], "record_command_receipt", checked_record)
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(payload)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    result = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_post_commit_receipt",
        text=text,
        item_id="item_post_commit_receipt",
    )
    assert result["validation_state"] == "APPLIED"
    assert observed["durable_before_receipt"] is True
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_reanchor_crash_rollback_has_no_receipt_and_cannot_recover_applied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded, _store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    expected = {
        "checkpoint_id": checkpoint["checkpoint_id"],
        "state_version": int(checkpoint["state_version"]),
        "epoch_id": checkpoint.get("epoch_id"),
        "epoch_revision": checkpoint.get("epoch_revision"),
    }
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": expected,
        "payload": {},
    }

    @contextmanager
    def rollback_guard(actor_context_id: str, **kwargs):
        connection = seeded["bridge"].semantic.connection
        with seeded["bridge"].semantic._lock:
            connection.execute("BEGIN IMMEDIATE")
            try:
                snapshot = seeded["bridge"]._snapshot_unlocked(actor_context_id)
                assert (
                    snapshot.checkpoint_id,
                    snapshot.state_version,
                    snapshot.epoch_id,
                    snapshot.epoch_revision,
                ) == (
                    kwargs["checkpoint_id"],
                    kwargs["state_version"],
                    kwargs["epoch_id"],
                    kwargs["epoch_revision"],
                )
                yield snapshot
                connection.rollback()
                raise RuntimeError("crash-equivalent before semantic commit")
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

    monkeypatch.setattr(seeded["bridge"], "currentness_guard", rollback_guard)
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(payload)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_crash_rollback",
        text=text,
        item_id="item_crash_rollback",
    )
    with pytest.raises(RuntimeError, match="crash-equivalent"):
        gateway.ingest_final_item(raw_message_seq=seq)
    row = seeded["supervisor"].connection.execute(
        "SELECT command_id, validation_state FROM managed_actor_commands WHERE raw_message_seq = ?",
        (seq,),
    ).fetchone()
    assert str(row["validation_state"]) == "VALIDATED"
    assert seeded["supervisor"].get_command_receipt(str(row["command_id"])) is None
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT 1 FROM reanchor_acks WHERE actor_turn_id = 'turn_crash_rollback'"
    ).fetchone() is None
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT state FROM obligations WHERE subject = ?",
        (checkpoint["checkpoint_id"],),
    ).fetchone()[0] == "OPEN"
    with pytest.raises(CommandGatewayError, match="receipt is missing"):
        gateway.ingest_final_item(raw_message_seq=seq)
    assert seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE command_id = ?",
        (row["command_id"],),
    ).fetchone()[0] == "INCIDENT"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_recovers_committed_reanchor_when_supervisor_receipt_was_not_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded, _store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(payload)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_committed_orphan",
        text=text,
        item_id="item_committed_orphan",
    )
    original_record = seeded["supervisor"].record_command_receipt

    def fail_receipt(**kwargs):
        raise RuntimeError("forced receipt crash gap")

    monkeypatch.setattr(seeded["supervisor"], "record_command_receipt", fail_receipt)
    with pytest.raises(RuntimeError, match="forced receipt crash gap"):
        gateway.ingest_final_item(raw_message_seq=seq)
    row = seeded["supervisor"].connection.execute(
        "SELECT command_id, validation_state FROM managed_actor_commands WHERE raw_message_seq = ?",
        (seq,),
    ).fetchone()
    assert str(row["validation_state"]) == "VALIDATED"
    assert seeded["supervisor"].get_command_receipt(str(row["command_id"])) is None
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM reanchor_acks WHERE actor_turn_id = 'turn_committed_orphan'"
    ).fetchone()[0] == 1

    monkeypatch.setattr(seeded["supervisor"], "record_command_receipt", original_record)
    recovered = gateway.ingest_final_item(raw_message_seq=seq)
    assert recovered["validation_state"] == "APPLIED"
    assert recovered["reconciled"] is True
    assert seeded["supervisor"].get_command_receipt(str(row["command_id"])) is not None
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM reanchor_acks WHERE actor_turn_id = 'turn_committed_orphan'"
    ).fetchone()[0] == 1
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_recovery_rejects_orphan_reanchor_receipt_without_semantic_effect(
    tmp_path: Path,
) -> None:
    seeded, _store, gateway = _ready_binding(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "CONTEXT_REANCHOR_ACK",
        "expected": {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "state_version": int(checkpoint["state_version"]),
            "epoch_id": checkpoint.get("epoch_id"),
            "epoch_revision": checkpoint.get("epoch_revision"),
        },
        "payload": {},
    }
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(payload)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    first = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_orphan_receipt",
        text=text,
        item_id="item_orphan_receipt",
    )
    from tests.codex_supervisor.helpers import rewind_command_validation

    rewind_command_validation(
        seeded["supervisor"].connection, str(first["command_id"]), "VALIDATED"
    )
    semantic = seeded["bridge"].semantic.connection
    semantic.execute(
        "DELETE FROM reanchor_acks WHERE actor_turn_id = 'turn_orphan_receipt'"
    )
    semantic.execute(
        "UPDATE obligations SET state = 'OPEN', resolved_at = NULL WHERE subject = ?",
        (checkpoint["checkpoint_id"],),
    )
    semantic.commit()
    raw_seq = seeded["supervisor"].connection.execute(
        "SELECT raw_message_seq FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()[0]
    with pytest.raises(CommandGatewayError, match="no durable semantic effect"):
        gateway.ingest_final_item(raw_message_seq=int(raw_seq))
    assert seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()[0] == "INCIDENT"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_packet_write_joins_guard_without_premature_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    payload_path = tmp_path / "guarded-packet.md"
    payload_path.write_text("guarded packet", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    gateway = CommandGateway(
        seeded["bindings"],
        seeded["bridge"],
        seeded["mailbox"],
        sender,
    )
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MANAGED_PACKET_SEND",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {
            "packet_kind": "ROOT_TO_PORTFOLIO_REVIEW",
            "target_alias": "PORTFOLIO",
            "payload_ref": payload_path.name,
            "marker": "guarded-packet-marker",
            "direction_id": None,
        },
    }
    original = managed_packet_send_module.packet_register
    observed = {"joined": False}

    def checked_packet_register(*args, **kwargs):
        _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
        result = original(*args, **kwargs)
        assert seeded["bridge"].semantic.connection.in_transaction
        _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
        observed["joined"] = True
        return result

    monkeypatch.setattr(
        managed_packet_send_module,
        "packet_register",
        checked_packet_register,
    )
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(body)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    applied = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_guarded_packet",
        text=text,
        item_id="item_guarded_packet",
    )
    assert applied["validation_state"] == "APPLIED"
    assert observed["joined"] is True
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_eligibility_decision_uses_only_guarded_state_at_former_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    payload_path = tmp_path / "guarded-eligibility-packet.md"
    payload_path.write_text("guarded eligibility", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    gateway = CommandGateway(
        seeded["bindings"], seeded["bridge"], seeded["mailbox"], sender
    )
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MANAGED_PACKET_SEND",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {
            "packet_kind": "ROOT_TO_PORTFOLIO_REVIEW",
            "target_alias": "PORTFOLIO",
            "payload_ref": payload_path.name,
            "marker": "guarded-eligibility-marker",
            "direction_id": None,
        },
    }
    with seeded["semantic"]._lock, seeded["semantic"].connection:
        seeded["semantic"].connection.execute(
            "UPDATE actor_contexts SET state = 'RELEASED' WHERE actor_context_id = ?",
            (seeded["root"].actor_context_id,),
        )

    original_guard = seeded["bridge"].currentness_guard
    interleaving = {"writer_ran": False}

    @contextmanager
    def invalid_to_valid_before_guard(actor_context_id: str, **expected):
        with seeded["semantic"]._lock, seeded["semantic"].connection:
            seeded["semantic"].connection.execute(
                "UPDATE actor_contexts SET state = 'ACTIVE' WHERE actor_context_id = ?",
                (actor_context_id,),
            )
        interleaving["writer_ran"] = True
        with original_guard(actor_context_id, **expected) as guarded:
            yield guarded

    monkeypatch.setattr(
        seeded["bridge"], "currentness_guard", invalid_to_valid_before_guard
    )
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(body)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    applied = ingest_recorded_command(
        gateway,
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_guarded_eligibility",
        text=text,
        item_id="item_guarded_eligibility",
    )
    assert applied["validation_state"] == "APPLIED"
    assert interleaving["writer_ran"] is True
    assert seeded["bindings"].get(seeded["root_binding_id"]).binding_state is BindingState.ACTIVE
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM packet_refs WHERE marker = 'guarded-eligibility-marker'"
    ).fetchone()[0] == 1
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages"
    ).fetchone()[0] == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_stable_guarded_ineligibility_suspends_without_action_effect(
    tmp_path: Path,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    payload_path = tmp_path / "stable-ineligible-packet.md"
    payload_path.write_text("must not register", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    gateway = CommandGateway(
        seeded["bindings"], seeded["bridge"], seeded["mailbox"], sender
    )
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    with seeded["semantic"]._lock, seeded["semantic"].connection:
        seeded["semantic"].connection.execute(
            "UPDATE actor_contexts SET state = 'RELEASED' WHERE actor_context_id = ?",
            (seeded["root"].actor_context_id,),
        )
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MANAGED_PACKET_SEND",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {
            "packet_kind": "ROOT_TO_PORTFOLIO_REVIEW",
            "target_alias": "PORTFOLIO",
            "payload_ref": payload_path.name,
            "marker": "stable-ineligible-marker",
        },
    }
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(body)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_stable_ineligible",
        text=text,
        item_id="item_stable_ineligible",
    )
    with pytest.raises(CommandGatewayError, match="not ACTIVE"):
        gateway.ingest_final_item(raw_message_seq=seq)
    command = seeded["supervisor"].connection.execute(
        "SELECT command_id FROM managed_actor_commands WHERE raw_message_seq = ?", (seq,)
    ).fetchone()
    assert seeded["bindings"].get(seeded["root_binding_id"]).binding_state is BindingState.SUSPENDED
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM packet_refs WHERE marker = 'stable-ineligible-marker'"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].get_command_receipt(str(command["command_id"])) is None
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages"
    ).fetchone()[0] == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_gateway_packet_alias_ambiguity_fails_before_any_action_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    second_root = register_session_root(
        seeded["semantic"], session_id="session-second-operational-root"
    )
    seeded["semantic"].open_actor_workflow(
        second_root.actor_context_id,
        "turn-second-root",
        "second-root",
        "coordinate",
    )
    second_snapshot = seeded["bridge"].snapshot(second_root.actor_context_id)
    second_root_binding_id = activate_binding(
        seeded["bindings"], second_snapshot, tmp_path, "thr_second_root"
    )
    payload_path = tmp_path / "ambiguous-target-packet.md"
    payload_path.write_text("must not register", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    gateway = CommandGateway(
        seeded["bindings"], seeded["bridge"], seeded["mailbox"], sender
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MANAGED_PACKET_SEND",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {
            "packet_kind": "PORTFOLIO_TO_ROOT_DECISION",
            "target_alias": "OPERATIONAL_ROOT",
            "payload_ref": payload_path.name,
            "marker": "ambiguous-target-marker",
        },
    }
    packet_count = seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM packet_refs"
    ).fetchone()[0]
    mailbox_count = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages"
    ).fetchone()[0]
    mailbox_receipt_count = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0]
    binding_event_count = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_binding_events"
    ).fetchone()[0]
    packet_register_called = {"value": False}

    def forbidden_packet_register(*args, **kwargs):
        packet_register_called["value"] = True
        pytest.fail("ambiguous target reached packet_register")

    monkeypatch.setattr(
        managed_packet_send_module, "packet_register", forbidden_packet_register
    )
    text = (
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
        + json.dumps(body)
        + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_ambiguous_target",
        text=text,
        item_id="item_ambiguous_target",
    )
    with pytest.raises(CommandGatewayError, match="exactly one ACTIVE binding"):
        gateway.ingest_final_item(raw_message_seq=seq)
    command = seeded["supervisor"].connection.execute(
        "SELECT command_id FROM managed_actor_commands WHERE raw_message_seq = ?", (seq,)
    ).fetchone()
    assert seeded["bridge"].semantic.connection.execute(
        "SELECT COUNT(*) FROM packet_refs"
    ).fetchone()[0] == packet_count
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages"
    ).fetchone()[0] == mailbox_count
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == mailbox_receipt_count
    assert seeded["supervisor"].get_command_receipt(str(command["command_id"])) is None
    assert packet_register_called["value"] is False
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM managed_binding_events"
    ).fetchone()[0] == binding_event_count
    assert seeded["bindings"].get(seeded["root_binding_id"]).binding_state is BindingState.ACTIVE
    assert seeded["bindings"].get(second_root_binding_id).binding_state is BindingState.ACTIVE
    assert seeded["bindings"].get(seeded["portfolio_binding_id"]).binding_state is BindingState.ACTIVE
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
