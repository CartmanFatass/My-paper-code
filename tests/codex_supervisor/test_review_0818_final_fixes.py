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
from tools.codex_semantic_mvp.actor_registry import release_actor_context
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurns
from tools.codex_supervisor.mutation_intents import MutationIntentError, MutationIntentStore
from tools.codex_supervisor.client import UnexpectedServerRequest
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.session_guard import ManagedAppServerSession, mark_related_incidents
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close(seeded) -> None:
    ManagedAppServerSession.close_all()
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


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


class ScriptedClient:
    def __init__(self) -> None:
        self.server_requests: asyncio.Queue = asyncio.Queue()
        self.resumes = 0
        self.status = "notLoaded"
        self.loaded: list[str] = []
        self.loaded_error = False

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method: str, params=None):
        from types import SimpleNamespace

        params = dict(params or {})
        return SimpleNamespace(
            request_id="1",
            method=method,
            params=params,
            payload={"id": 1, "method": method, "params": params},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
            future=None,
        )

    def discard_prepared(self, prepared) -> None:
        return None

    async def send_prepared(self, prepared) -> None:
        return None

    async def await_prepared(self, prepared, timeout=None):
        return await self.request(prepared.method, prepared.params)

    async def request(self, method: str, params=None, timeout=None):
        params = params or {}
        if method == "thread/resume":
            self.resumes += 1
            return {"id": "1", "result": {"thread": {"id": params.get("threadId"), "status": {"type": "idle"}}}}
        if method == "thread/read":
            return {
                "id": "2",
                "result": {"thread": {"id": params.get("threadId"), "status": {"type": self.status}, "turns": []}},
            }
        if method == "thread/loaded/list":
            if self.loaded_error:
                from tools.codex_supervisor.client import AppServerRpcError

                raise AppServerRpcError(-32000, "loaded list failed", {})
            return {"id": "3", "result": {"data": list(self.loaded)}}
        raise AssertionError(method)

    async def read_thread(self, thread_id: str, include_turns: bool = False):
        response = await self.request("thread/read", {"threadId": thread_id})
        result = response.get("result")
        return dict(result) if isinstance(result, dict) else {}

    async def list_loaded_threads(self):
        if self.loaded_error:
            from tools.codex_supervisor.client import AppServerRpcError

            raise AppServerRpcError(-32000, "loaded list failed", {})
        return list(self.loaded)


def test_binding_store_activate_rejects_incident_verification(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    store = seeded["bindings"]
    binding_id = seeded["root_binding_id"]
    store.suspend(binding_id)
    seeded["supervisor"].connection.execute(
        """UPDATE managed_actor_bindings
        SET binding_state = 'VERIFICATION_REQUIRED', version = version + 1
        WHERE binding_id = ?""",
        (binding_id,),
    )
    seeded["supervisor"].connection.commit()
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    from tests.codex_supervisor.helpers import drive_turn_intent

    drive_turn_intent(
        seeded["supervisor"].connection,
        intent_id,
        "INCIDENT",
        app_server_turn_id="turn_inc",
        incident_json='{"reason":"server_request"}',
    )
    with pytest.raises(BindingError, match="INCIDENT"):
        store.activate(binding_id)
    assert store.get(binding_id).binding_state.value == "VERIFICATION_REQUIRED"
    _close(seeded)


def test_attach_without_mutation_intent_cannot_bypass_incident(tmp_path: Path) -> None:
    seeded, store, binding_id, _snapshot = _prepared_binding(tmp_path)
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    mutations = MutationIntentStore(seeded["supervisor"])
    insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="thread/start",
        client_key=f"thread/start:{binding_id}",
        state="INCIDENT",
        binding_id=binding_id,
    )
    with pytest.raises(BindingError, match="effect id is required"):
        store.attach_thread(binding_id, "thr_root")
    with pytest.raises(BindingError, match="INCIDENT"):
        store.attach_thread_for_tests(binding_id, "thr_root")
    binding = store.get(binding_id)
    assert binding is not None
    assert binding.binding_state.value == "PREPARED"
    assert binding.thread_id is None
    _close(seeded)


def test_resume_response_then_incident_cannot_become_submitted(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    mutations = MutationIntentStore(seeded["supervisor"])
    intent_id = insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="thread/resume",
        client_key="thread/resume:thr_root",
        state="INCIDENT",
        binding_id="bind_x",
    )
    with pytest.raises(MutationIntentError, match="read-only"):
        mutations.mark_submitted(intent_id)
    with pytest.raises(MutationIntentError, match="read-only"):
        mutations.mark_submitted_unreconciled(intent_id)
    row = seeded["supervisor"].connection.execute(
        "SELECT state FROM mutation_intents WHERE intent_id = ?",
        (intent_id,),
    ).fetchone()
    assert str(row[0]) == "INCIDENT"
    _close(seeded)


def test_observed_turn_is_marked_incident_by_server_request(tmp_path: Path) -> None:
    seeded, store, binding_id, snapshot = _prepared_binding(tmp_path)
    store.attach_thread_for_tests(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
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
        "OBSERVED",
        app_server_turn_id="turn_obs",
    )
    mark_related_incidents(
        seeded["supervisor"],
        {"id": "sreq_obs", "method": "item/command/request", "params": {"threadId": "thr_root", "turnId": "turn_obs"}},
    )
    assert turns._row(intent_id)["submission_state"] == "INCIDENT"
    _close(seeded)


def test_recovery_cannot_overwrite_incident_with_active(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:rec-active",
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
        batches.set_state(str(batch["wake_batch_id"]), state="SUBMITTING")
        batches.set_state(str(batch["wake_batch_id"]), state="INCIDENT")
        client = ScriptedClient()
        client.status = "idle"
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, client)  # type: ignore[arg-type]
        updated = await recovery.reconcile_batch(str(batch["wake_batch_id"]))
        assert updated["state"] == "INCIDENT"
        _close(seeded)

    asyncio.run(body())


def test_recovery_cannot_overwrite_incident_with_completed(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:rec-done",
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
        from tests.codex_supervisor.helpers import drive_wake_batch

        drive_wake_batch(
            batches, str(batch["wake_batch_id"]), "ACTIVE", app_server_turn_id="turn_done"
        )
        seeded["supervisor"].connection.execute(
            """INSERT OR REPLACE INTO turn_snapshots (
                turn_id, thread_id, status, updated_at
            ) VALUES ('turn_done', 'thr_port', 'completed', ?)""",
            (_now(),),
        )
        seeded["supervisor"].connection.commit()
        batches.set_state(str(batch["wake_batch_id"]), state="INCIDENT")
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, None)
        updated = await recovery.reconcile_batch(str(batch["wake_batch_id"]))
        assert updated["state"] == "INCIDENT"
        _close(seeded)

    asyncio.run(body())


def test_command_from_incident_turn_has_no_control_effect(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:inc-cmd",
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
    batches.set_state(str(batch["wake_batch_id"]), state="INCIDENT", app_server_turn_id="turn_inc")
    record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_inc",
        text="wake",
        item_id="itm_wake_inc",
        item_type="userMessage",
    )
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MAILBOX_ACK",
        "payload": {"message_ids": [message.message_id]},
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(body) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_inc",
        text=text,
        item_id="itm_inc_cmd",
    )
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    with pytest.raises(CommandGatewayError, match="INCIDENT"):
        gateway.ingest_final_item(raw_message_seq=seq)
    assert mailbox.get(message.message_id).intake_state.value == "NOT_ACKNOWLEDGED"
    row = seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE turn_id = 'turn_inc' ORDER BY created_at DESC"
    ).fetchone()
    assert row is not None
    assert str(row[0]) != "APPLIED"
    _close(seeded)


def test_successful_resume_not_loaded_is_not_resubmitted(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client = ScriptedClient()
        client.status = "notLoaded"
        recovery = WakeRecovery(seeded["bindings"], seeded["mailbox"], WakeBatchStore(seeded["supervisor"], seeded["mailbox"]), client)  # type: ignore[arg-type]
        first = await recovery.resume_once(seeded["root_binding_id"])
        assert first.value == "IDLE_NOT_LOADED"
        assert client.resumes == 1
        row = seeded["supervisor"].connection.execute(
            "SELECT state FROM app_server_effects WHERE method = 'thread/resume' ORDER BY prepared_at DESC"
        ).fetchone()
        assert str(row[0]) != "PREPARED"
        second = await recovery.resume_once(seeded["root_binding_id"])
        assert second.value == "IDLE_NOT_LOADED"
        assert client.resumes == 1
        _close(seeded)

    asyncio.run(body())


def test_successful_resume_unknown_is_reconciled_not_restarted(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client = ScriptedClient()
        client.status = "idle"
        client.loaded_error = True
        recovery = WakeRecovery(seeded["bindings"], seeded["mailbox"], WakeBatchStore(seeded["supervisor"], seeded["mailbox"]), client)  # type: ignore[arg-type]
        first = await recovery.resume_once(seeded["root_binding_id"])
        assert first.value == "UNKNOWN"
        assert client.resumes == 1
        second = await recovery.resume_once(seeded["root_binding_id"])
        assert second.value == "UNKNOWN"
        assert client.resumes == 1
        row = seeded["supervisor"].connection.execute(
            "SELECT state FROM app_server_effects WHERE method = 'thread/resume' ORDER BY prepared_at DESC"
        ).fetchone()
        assert str(row[0]) != "PREPARED"
        _close(seeded)

    asyncio.run(body())


def test_resume_intent_becomes_applied_only_after_loaded_observation(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client = ScriptedClient()
        client.status = "notLoaded"
        recovery = WakeRecovery(seeded["bindings"], seeded["mailbox"], WakeBatchStore(seeded["supervisor"], seeded["mailbox"]), client)  # type: ignore[arg-type]
        await recovery.resume_once(seeded["root_binding_id"])
        row = seeded["supervisor"].connection.execute(
            "SELECT state FROM app_server_effects WHERE method = 'thread/resume' ORDER BY prepared_at DESC"
        ).fetchone()
        assert str(row[0]) != "PREPARED"
        client.status = "idle"
        client.loaded = ["thr_root"]
        ready = await recovery.resume_once(seeded["root_binding_id"])
        assert ready.value == "IDLE_LOADED"
        assert client.resumes == 1
        row = seeded["supervisor"].connection.execute(
            "SELECT state FROM app_server_effects WHERE method = 'thread/resume' ORDER BY prepared_at DESC"
        ).fetchone()
        assert str(row[0]) == "EFFECT_CONFIRMED"
        _close(seeded)

    asyncio.run(body())


def test_server_request_during_initial_reconcile_terminates(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, request_timeout_seconds=2.0)
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "server_request_on_thread_list"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        await service.start()
        await service.initialize()
        assert service.session is not None
        with pytest.raises(UnexpectedServerRequest):
            await service.reconcile_threads()
        await service.stop("UNEXPECTED_SERVER_REQUEST")
        rows = service.store.connection.execute("SELECT handling FROM server_requests").fetchall()
        assert rows
        service.store.close()

    asyncio.run(body())


def test_server_request_during_snapshot_terminates(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, request_timeout_seconds=2.0)
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "server_request_on_thread_list"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        result = await service.run_snapshot()
        assert getattr(result, "end_kind", None) == "UNEXPECTED_SERVER_REQUEST"
        service.store.close()

    asyncio.run(body())


def test_serve_establishes_session_watcher_before_thread_list(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, reconcile_interval_seconds=0.2, request_timeout_seconds=2.0)
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        seen: dict[str, bool] = {}

        def hook(message: dict) -> None:
            if message.get("method") == "thread/list":
                seen["watcher"] = (
                    service.session is not None
                    and service.session._task is not None
                    and not service.session._task.done()
                )

        service.outbound_hook = hook
        result = await service.serve(duration_seconds=0.4)
        assert result.end_kind == "NORMAL"
        assert seen.get("watcher") is True
        service.store.close()

    asyncio.run(body())


def test_validated_command_without_receipt_becomes_durable_incident(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"])
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_missing",
        text=_ack_text(checkpoint),
        item_id="itm_missing",
    )
    first = gateway.ingest_final_item(raw_message_seq=seq)
    assert first["validation_state"] == "APPLIED"
    from tests.codex_supervisor.helpers import rewind_command_validation

    rewind_command_validation(seeded["supervisor"].connection, str(first["command_id"]), "VALIDATED")
    seeded["supervisor"].connection.execute(
        "DELETE FROM managed_command_receipts WHERE command_id = ?",
        (first["command_id"],),
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(CommandGatewayError, match="receipt is missing"):
        gateway.ingest_final_item(raw_message_seq=seq)
    row = seeded["supervisor"].connection.execute(
        "SELECT validation_state, rejection_reason FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()
    assert str(row[0]) == "INCIDENT"
    assert "receipt is missing" in str(row[1])
    _close(seeded)


def test_reconciled_reanchor_receipt_requires_exact_normalized_tuple(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"])
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_tuple",
        text=_ack_text(checkpoint),
        item_id="itm_tuple",
    )
    first = gateway.ingest_final_item(raw_message_seq=seq)
    from tests.codex_supervisor.helpers import rewind_command_validation

    rewind_command_validation(seeded["supervisor"].connection, str(first["command_id"]), "VALIDATED")
    receipt = seeded["supervisor"].get_command_receipt(str(first["command_id"]))
    result = json.loads(str(receipt["result_json"]))
    result["epoch_id"] = "different-epoch"
    seeded["supervisor"].connection.execute(
        "UPDATE managed_command_receipts SET result_json = ? WHERE command_id = ?",
        (json.dumps(result), first["command_id"]),
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(CommandGatewayError, match="tuple"):
        gateway.ingest_final_item(raw_message_seq=seq)
    row = seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE command_id = ?",
        (first["command_id"],),
    ).fetchone()
    assert str(row[0]) == "INCIDENT"
    _close(seeded)


def test_mailbox_command_started_before_wake_but_completed_after_is_rejected(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:overlap",
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
    command_seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_cmd_early",
        text="command started first",
        item_id="itm_cmd_start",
        item_type="userMessage",
    )
    record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_wake_late",
        text="wake started later",
        item_id="itm_wake_late",
        item_type="userMessage",
    )
    from tests.codex_supervisor.helpers import drive_wake_batch

    drive_wake_batch(
        batches,
        str(batch["wake_batch_id"]),
        "COMPLETED",
        app_server_turn_id="turn_wake_late",
    )
    body = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MAILBOX_ACK",
        "payload": {"message_ids": [message.message_id]},
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(body) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_port",
        turn_id="turn_cmd_early",
        text=text,
        item_id="itm_cmd_final",
    )
    assert seq > command_seq
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
    with pytest.raises(CommandGatewayError, match="predates|ordering"):
        gateway.ingest_final_item(raw_message_seq=seq)
    assert mailbox.get(message.message_id).intake_state.value == "NOT_ACKNOWLEDGED"
    _close(seeded)


def test_semantic_actor_released_after_batch_prepare_prevents_wake_submit(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:released",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="s",
            payload_ref="p",
        )
        snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        leases = SchedulerLeases(seeded["supervisor"])
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            leases,
            WakeRecovery(seeded["bindings"], mailbox, batches, None, leases, "sched"),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client=object(),  # type: ignore[arg-type]
            instance_id="sched",
        )
        batch = batches.prepare(
            binding_id=seeded["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[message],
            lease_generation=1,
            lease_holder="sched",
        )
        lease = leases.acquire(seeded["portfolio_binding_id"], "sched")
        release_actor_context(seeded["semantic"], seeded["portfolio"].actor_context_id)
        with pytest.raises(WakeSchedulerError, match="not ACTIVE"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        assert seeded["bindings"].get(seeded["portfolio_binding_id"]).binding_state.value == "SUSPENDED"
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert mailbox.get(message.message_id).delivery_state.value == "ELIGIBLE"
        _close(seeded)

    asyncio.run(body())
