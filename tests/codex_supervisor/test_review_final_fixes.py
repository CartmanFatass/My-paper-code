from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import (
    make_observer_config,
    record_completed_agent_item,
    write_fake_codex,
)
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_semantic_mvp.packet_refs import packet_register
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.client import AppServerClient, UnexpectedServerRequest
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_runtime import ManagedRuntime, ManagedRuntimeError
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns
from tools.codex_supervisor.mutation_intents import MutationIntentError, MutationIntentStore
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.session_guard import ManagedAppServerSession
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.scheduler_leases import SchedulerLeases


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _prepared_binding(tmp_path: Path):
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
    return seeded, store, binding_id, snapshot


def _ack_text(checkpoint: dict) -> str:
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
    return "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(payload) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"


def test_server_request_incident_cannot_be_completed_or_activated(tmp_path: Path) -> None:
    seeded, store, binding_id, snapshot = _prepared_binding(tmp_path)
    store.attach_thread_for_tests(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    intent_id = turns.prepare(
        binding_id,
        intent_kind=ManagedIntentKind.BOOTSTRAP,
        input_ref="bootstrap",
        checkpoint_id=snapshot.checkpoint_id,
        expected_state_version=snapshot.state_version,
        expected_epoch_id=snapshot.epoch_id,
        expected_epoch_revision=snapshot.epoch_revision,
    )
    from tests.codex_supervisor.helpers import drive_turn_intent

    drive_turn_intent(
        seeded["supervisor"].connection,
        intent_id,
        "INCIDENT",
        app_server_turn_id="turn_inc",
        incident_json='{"reason":"server_request"}',
    )
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_inc",
        text=_ack_text(checkpoint),
        item_id="itm_inc",
    )
    runtime = ManagedRuntime(store, turns, CommandGateway(store, seeded["bridge"]), seeded["bridge"])
    with pytest.raises(ManagedRuntimeError, match="INCIDENT"):
        runtime.complete_activation(binding_id, raw_message_seq=seq)
    with pytest.raises(ManagedTurnError, match="incident is terminal"):
        turns.record_completion(intent_id, "completed")
    assert turns._row(intent_id)["submission_state"] == "INCIDENT"
    command = seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE turn_id = 'turn_inc'"
    ).fetchone()
    assert command is None
    _close(seeded)


def test_thread_start_incident_cannot_be_overwritten_by_attach(tmp_path: Path) -> None:
    seeded, store, binding_id, _snapshot = _prepared_binding(tmp_path)
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    mutations = MutationIntentStore(seeded["supervisor"])
    intent_id = insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="thread/start",
        client_key=f"thread/start:{binding_id}",
        state="INCIDENT",
        binding_id=binding_id,
    )
    with pytest.raises(BindingError, match="not SUBMITTING"):
        store.attach_thread(binding_id, "thr_root", mutation_intent_id=intent_id)
    binding = store.get(binding_id)
    assert binding is not None
    assert binding.binding_state.value == "PREPARED"
    assert binding.thread_id is None
    row = seeded["supervisor"].connection.execute(
        "SELECT state FROM mutation_intents WHERE intent_id = ?",
        (intent_id,),
    ).fetchone()
    assert str(row[0]) == "INCIDENT"
    _close(seeded)


def test_thread_resume_incident_requires_operator_resolution(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    mutations = MutationIntentStore(seeded["supervisor"])
    insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="thread/resume",
        client_key="thread/resume:thr_adopt",
        state="INCIDENT",
        binding_id="bind_x",
    )
    with pytest.raises(MutationIntentError, match="disabled"):
        mutations.begin("thread/resume", "thread/resume:thr_adopt", binding_id="bind_x")
    _close(seeded)


def test_wake_incident_cannot_be_overwritten_by_completion(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:wake-inc",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
    )
    batches.set_state(str(batch["wake_batch_id"]), state="INCIDENT")
    leases = SchedulerLeases(seeded["supervisor"])
    scheduler = WakeScheduler(
        seeded["bindings"],
        mailbox,
        batches,
        leases,
        WakeRecovery(seeded["bindings"], mailbox, batches, None, leases, "sched"),
        SemanticScanner(mailbox, seeded["bridge"]),
        seeded["bridge"],
        None,
        instance_id="sched",
    )
    with pytest.raises(WakeSchedulerError, match="incident is terminal"):
        scheduler.observe_completion(str(batch["wake_batch_id"]), "completed")
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "INCIDENT"
    _close(seeded)


def _prepared_two_message_batch(tmp_path: Path) -> dict[str, object]:
    seeded = seed_active_root_portfolio(tmp_path)
    seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    packet_register(
        seeded["semantic"],
        packet_kind="PORTFOLIO_TO_ROOT_DECISION",
        source_actor_context_id=seeded["portfolio"].actor_context_id,
        target_actor_context_id=seeded["root"].actor_context_id,
        payload_ref="docs/canary.md",
        marker="marker-sibling",
        direction_id="demo",
    )
    scanner = SemanticScanner(seeded["mailbox"], seeded["bridge"])
    scanner.scan()
    messages = [
        item
        for item in seeded["mailbox"].list_messages()
        if item.source_system == MailboxSourceSystem.SEMANTIC_LEDGER.value
        and item.target_actor_context_id == seeded["root"].actor_context_id
    ]
    assert len(messages) >= 2
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], seeded["mailbox"])
    batch = batches.prepare(
        binding_id=seeded["root_binding_id"],
        thread_id="thr_root",
        snapshot=snapshot,
        messages=messages,
        lease_generation=1,
        lease_holder="sched",
    )
    return {
        "seeded": seeded,
        "scanner": scanner,
        "batches": batches,
        "batch_id": str(batch["wake_batch_id"]),
        "messages": messages,
    }


def test_prepared_batch_source_resolution_returns_valid_siblings_to_eligible(tmp_path: Path) -> None:
    planted = _prepared_two_message_batch(tmp_path)
    seeded = planted["seeded"]
    obligation = next(item for item in planted["messages"] if item.source_event_key.startswith("semantic:obligation:"))
    packet = next(item for item in planted["messages"] if item.source_event_key.startswith("semantic:packet:"))
    seeded["semantic"].connection.execute("UPDATE obligations SET state = 'RESOLVED' WHERE state = 'OPEN'")
    seeded["semantic"].connection.commit()
    planted["scanner"].scan()
    cancelled = seeded["mailbox"].get(obligation.message_id)
    sibling = seeded["mailbox"].get(packet.message_id)
    assert cancelled.delivery_state.value == "CANCELLED_SOURCE_RESOLVED"
    assert sibling.delivery_state.value == "ELIGIBLE"
    assert planted["batches"].get(planted["batch_id"])["state"] == "CANCELLED"
    selected = seeded["mailbox"].select_eligible(
        target_actor_context_id=seeded["root"].actor_context_id,
        target_kind="OPERATIONAL_ROOT",
        target_binding_state="ACTIVE",
        sender_kind_for={seeded["portfolio"].actor_context_id: "PORTFOLIO"},
    )
    assert any(item.message_id == packet.message_id for item in selected)
    _close(seeded)


def test_cancelled_batch_contains_no_batched_messages(tmp_path: Path) -> None:
    planted = _prepared_two_message_batch(tmp_path)
    seeded = planted["seeded"]
    seeded["semantic"].connection.execute("UPDATE obligations SET state = 'RESOLVED' WHERE state = 'OPEN'")
    seeded["semantic"].connection.commit()
    planted["scanner"].scan()
    assert planted["batches"].get(planted["batch_id"])["state"] == "CANCELLED"
    for message in planted["batches"].messages_for(planted["batch_id"]):
        assert message.delivery_state.value != "BATCHED"
    _close(seeded)


def test_source_resolution_during_active_batch_records_flag(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    scanner = SemanticScanner(seeded["mailbox"], seeded["bridge"])
    scanner.scan()
    messages = [
        item
        for item in seeded["mailbox"].list_messages()
        if item.source_system == MailboxSourceSystem.SEMANTIC_LEDGER.value
    ]
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], seeded["mailbox"])
    batch = batches.prepare(
        binding_id=seeded["root_binding_id"],
        thread_id="thr_root",
        snapshot=snapshot,
        messages=messages,
        lease_generation=1,
        lease_holder="sched",
    )
    seeded["mailbox"].mark_delivered(messages[0].message_id)
    from tests.codex_supervisor.helpers import drive_wake_batch

    drive_wake_batch(
        batches, str(batch["wake_batch_id"]), "ACTIVE", app_server_turn_id="turn_live"
    )
    seeded["semantic"].connection.execute("UPDATE obligations SET state = 'RESOLVED' WHERE state = 'OPEN'")
    seeded["semantic"].connection.commit()
    scanner.scan()
    remaining = seeded["mailbox"].get(messages[0].message_id)
    assert remaining.delivery_state.value == "DELIVERED_TO_TURN"
    assert remaining.source_resolved_after_submission is True
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "ACTIVE"
    _close(seeded)


def test_observer_and_managed_runtime_share_one_server_request_consumer(tmp_path: Path) -> None:
    async def body() -> None:
        seeded, store, binding_id, snapshot = _prepared_binding(tmp_path)
        store.attach_thread_for_tests(binding_id, "thr_root")
        store.mark_verification_required(binding_id)
        turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        from tests.codex_supervisor.helpers import drive_turn_intent

        drive_turn_intent(
            seeded["supervisor"].connection,
            intent_id,
            "SUBMITTED",
            app_server_turn_id="turn_watch",
        )
        config = make_observer_config(tmp_path, request_timeout_seconds=0.4)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=seeded["supervisor"],
            process_cwd=tmp_path,
        )
        service.client = client
        session = ManagedAppServerSession.for_client(client, seeded["supervisor"])
        watcher = asyncio.create_task(service._watch_server_requests())
        await asyncio.sleep(0)
        again = ManagedAppServerSession.for_client(client, seeded["supervisor"])
        assert session.owner is again.owner
        assert session._task is not None and not session._task.done()
        await client.server_requests.put(
            {
                "id": "sreq_shared",
                "method": "item/command/request",
                "params": {"threadId": "thr_root", "turnId": "turn_watch"},
            }
        )
        with pytest.raises(UnexpectedServerRequest):
            await asyncio.wait_for(watcher, timeout=2)
        assert turns._row(intent_id)["submission_state"] == "INCIDENT"
        assert client.server_requests.empty()
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


def test_mailbox_command_rejects_timestamp_only_ordering(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:ts-only",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
    )
    mailbox.mark_delivered(message.message_id)
    from tests.codex_supervisor.helpers import drive_wake_batch

    drive_wake_batch(batches, str(batch["wake_batch_id"]), "COMPLETED", app_server_turn_id="turn_wake")
    seeded["supervisor"].connection.execute(
        """INSERT OR REPLACE INTO turn_snapshots (
            turn_id, thread_id, status, started_at, last_event_seq, updated_at
        ) VALUES ('turn_wake', 'thr_port', 'completed', ?, NULL, ?)""",
        (_now(), _now()),
    )
    seeded["supervisor"].connection.commit()
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MAILBOX_ACK",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {"message_ids": [message.message_id]},
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(body) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_later",
        text=text,
        item_id="itm_later",
    )
    with pytest.raises(CommandGatewayError, match="ordering"):
        gateway.ingest_final_item(raw_message_seq=seq)
    _close(seeded)


def test_reanchor_receipt_crash_before_command_applied_is_reconciled(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"])
    text = _ack_text(checkpoint)
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_crash",
        text=text,
        item_id="itm_crash",
    )
    first = gateway.ingest_final_item(raw_message_seq=seq)
    assert first["validation_state"] == "APPLIED"
    from tests.codex_supervisor.helpers import rewind_command_validation

    rewind_command_validation(seeded["supervisor"].connection, str(first["command_id"]), "VALIDATED")
    receipt = seeded["supervisor"].get_command_receipt(str(first["command_id"]))
    assert receipt is not None
    second = gateway.ingest_final_item(raw_message_seq=seq)
    assert second["validation_state"] == "APPLIED"
    assert second.get("reconciled") is True
    row = seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()
    assert str(row[0]) == "APPLIED"
    _close(seeded)
