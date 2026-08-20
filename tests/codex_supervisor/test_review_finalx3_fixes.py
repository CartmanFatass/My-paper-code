from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, record_completed_agent_item, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns, client_user_message_id
from tools.codex_supervisor.mutation_intents import MutationIntentStore
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.session_guard import ManagedAppServerSession, mark_related_incidents
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.wake_batches import WakeBatchError, WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery


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


class MatchingTurnClient:
    def __init__(self, message_id: str, turn_id: str = "turn_found") -> None:
        self.message_id = message_id
        self.turn_id = turn_id

    async def read_thread(self, thread_id: str, include_turns: bool = False):
        return {
            "thread": {
                "id": thread_id,
                "status": {"type": "idle"},
                "turns": [{"id": self.turn_id, "clientUserMessageId": self.message_id}],
            }
        }


def test_uncertain_turn_server_request_marks_turn_incident(tmp_path: Path) -> None:
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
        "SUBMISSION_UNCERTAIN",
        app_server_turn_id="turn_unc",
    )
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="turn/start",
        client_key=client_user_message_id(intent_id),
        state="SUBMISSION_UNCERTAIN",
        binding_id=binding_id,
    )
    mark_related_incidents(
        seeded["supervisor"],
        {
            "id": "sreq_unc",
            "method": "item/command/request",
            "params": {"threadId": "thr_root", "turnId": "turn_unc"},
        },
    )
    assert turns._row(intent_id)["submission_state"] == "INCIDENT"
    _close(seeded)


def test_reconcile_uncertain_cannot_overwrite_incident(tmp_path: Path) -> None:
    async def body() -> None:
        seeded, store, binding_id, snapshot = _prepared_binding(tmp_path)
        store.attach_thread_for_tests(binding_id, "thr_root")
        store.mark_verification_required(binding_id)
        turns = ManagedTurns(store, MatchingTurnClient("pending"))  # type: ignore[arg-type]
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap",
            checkpoint_id=snapshot.checkpoint_id,
            expected_state_version=snapshot.state_version,
            expected_epoch_id=snapshot.epoch_id,
            expected_epoch_revision=snapshot.epoch_revision,
        )
        message_id = str(turns._row(intent_id)["client_user_message_id"])
        turns.client = MatchingTurnClient(message_id)  # type: ignore[assignment]
        from tests.codex_supervisor.helpers import drive_turn_intent

        drive_turn_intent(
            seeded["supervisor"].connection,
            intent_id,
            "INCIDENT",
            app_server_turn_id="turn_inc",
            incident_json=json.dumps({"reason": "server_request"}),
        )
        with pytest.raises(ManagedTurnError, match="terminal"):
            await turns.reconcile_uncertain(intent_id)
        assert turns._row(intent_id)["submission_state"] == "INCIDENT"

        other = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap-2",
            checkpoint_id=snapshot.checkpoint_id,
            expected_state_version=snapshot.state_version,
            expected_epoch_id=snapshot.epoch_id,
            expected_epoch_revision=snapshot.epoch_revision,
        )
        other_key = str(turns._row(other)["client_user_message_id"])
        turns.client = MatchingTurnClient(other_key, "turn_other")  # type: ignore[assignment]
        drive_turn_intent(seeded["supervisor"].connection, other, "SUBMISSION_UNCERTAIN")
        from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

        insert_legacy_mutation_intent(
            seeded["supervisor"].connection,
            method="turn/start",
            client_key=other_key,
            state="INCIDENT",
            binding_id=binding_id,
        )
        remaining = await turns.reconcile_uncertain(other)
        assert remaining["submission_state"] == "SUBMISSION_UNCERTAIN"
        _close(seeded)

    asyncio.run(body())


def test_command_from_uncertain_turn_with_incident_mutation_has_no_effect(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    store = seeded["bindings"]
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    store.suspend(seeded["root_binding_id"])
    store.store.connection.execute(
        """UPDATE managed_actor_bindings
        SET binding_state = 'VERIFICATION_REQUIRED', version = version + 1
        WHERE binding_id = ?""",
        (seeded["root_binding_id"],),
    )
    store.store.connection.commit()
    intent_id = turns.prepare(
        seeded["root_binding_id"],
        intent_kind=ManagedIntentKind.BOOTSTRAP,
        input_ref="bootstrap",
        checkpoint_id=snapshot.checkpoint_id,
        expected_state_version=snapshot.state_version,
        expected_epoch_id=snapshot.epoch_id,
        expected_epoch_revision=snapshot.epoch_revision,
    )
    client_key = str(turns._row(intent_id)["client_user_message_id"])
    from tests.codex_supervisor.helpers import drive_turn_intent

    drive_turn_intent(
        seeded["supervisor"].connection,
        intent_id,
        "OBSERVED",
        app_server_turn_id="turn_unc_cmd",
    )
    from tests.codex_supervisor.helpers import insert_legacy_mutation_intent

    insert_legacy_mutation_intent(
        seeded["supervisor"].connection,
        method="turn/start",
        client_key=client_key,
        state="INCIDENT",
        binding_id=seeded["root_binding_id"],
    )
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_unc_cmd",
        text=_ack_text(checkpoint),
        item_id="itm_unc_cmd",
    )
    gateway = CommandGateway(store, seeded["bridge"])
    with pytest.raises(CommandGatewayError, match="INCIDENT"):
        gateway.ingest_final_item(raw_message_seq=seq)
    row = seeded["supervisor"].connection.execute(
        "SELECT validation_state FROM managed_actor_commands WHERE turn_id = 'turn_unc_cmd' ORDER BY created_at DESC"
    ).fetchone()
    assert row is not None
    assert str(row[0]) != "APPLIED"
    _close(seeded)


def test_concurrent_wake_claim_has_exactly_one_winner(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:cas-claim",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    first = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = first.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=1,
        lease_holder="sched",
    )
    wake_batch_id = str(batch["wake_batch_id"])
    init_lock = threading.Lock()
    barrier = threading.Barrier(2)
    winners: list[str] = []
    losers: list[str] = []

    def claim(store_name: str) -> None:
        with init_lock:
            store = ObserverStore(tmp_path / "supervisor")
        try:
            batches = WakeBatchStore(store, mailbox)
            barrier.wait()
            try:
                batches.claim_first_submission(
                    wake_batch_id,
                    lease_holder="sched",
                    lease_generation=1,
                )
                winners.append(store_name)
            except WakeBatchError:
                losers.append(store_name)
        finally:
            store.close()

    threads = [
        threading.Thread(target=claim, args=("first",)),
        threading.Thread(target=claim, args=("second",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(winners) == 1
    assert len(losers) == 1
    row = first.get(wake_batch_id)
    assert row is not None
    assert row["state"] == "SUBMITTING"
    attempts = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()[0]
    assert int(attempts) == 1
    _close(seeded)


def test_stale_lease_claim_cannot_leave_batch_submitting(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:stale-lease",
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
        lease_generation=2,
        lease_holder="current",
    )
    wake_batch_id = str(batch["wake_batch_id"])
    with pytest.raises(WakeBatchError, match="PREPARED"):
        batches.claim_first_submission(
            wake_batch_id,
            lease_holder="stale",
            lease_generation=1,
        )
    row = batches.get(wake_batch_id)
    assert row is not None
    assert row["state"] == "PREPARED"
    attempts = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()[0]
    assert int(attempts) == 0
    _close(seeded)


def test_snapshot_records_server_request_even_when_rpc_response_also_arrives(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, request_timeout_seconds=2.0)
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "server_request_then_thread_list_response"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        result = await service.run_snapshot()
        assert getattr(result, "end_kind", None) == "UNEXPECTED_SERVER_REQUEST"
        rows = service.store.connection.execute("SELECT method FROM server_requests").fetchall()
        assert rows
        service.store.close()

    asyncio.run(body())


def test_uncertain_resume_becomes_applied_after_loaded_observation(tmp_path: Path) -> None:
    async def body() -> None:
        from tools.codex_supervisor.durability.effects import EffectJournal

        seeded = seed_active_root_portfolio(tmp_path)
        journal = EffectJournal(seeded["supervisor"].connection)
        effect = journal.prepare_effect(
            owner_kind="THREAD_RESUME",
            owner_id=seeded["root_binding_id"],
            binding_id=seeded["root_binding_id"],
            method="thread/resume",
            client_key="thread/resume:thr_root",
            request={"threadId": "thr_root"},
        )
        journal.claim_write(
            effect.effect_id,
            run_id="run1",
            client_request_id="1",
            request_row_id="r1",
            raw_request_seq=1,
        )
        journal.mark_uncertain(effect.effect_id, reason="timeout")
        client = type("Client", (), {})()

        async def read_thread(thread_id: str, include_turns: bool = False):
            return {"thread": {"id": thread_id, "status": {"type": "idle"}, "turns": []}}

        async def list_loaded_threads():
            return ["thr_root"]

        client.read_thread = read_thread  # type: ignore[attr-defined]
        client.list_loaded_threads = list_loaded_threads  # type: ignore[attr-defined]
        recovery = WakeRecovery(
            seeded["bindings"],
            seeded["mailbox"],
            WakeBatchStore(seeded["supervisor"], seeded["mailbox"]),
            client,  # type: ignore[arg-type]
        )
        ready = await recovery.resume_once(seeded["root_binding_id"])
        assert ready.value == "IDLE_LOADED"
        assert seeded["supervisor"].connection.execute("SELECT COUNT(*) FROM mutation_intents").fetchone()[0] == 0
        _close(seeded)

    asyncio.run(body())
