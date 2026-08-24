from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.mailbox_fixtures import prepare_resume_batch, seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient, MUTATING_OWNER_MESSAGE
from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.durability.operator_resolution import (
    OperatorResolutionError,
    OperatorResolutionService,
    ResolutionDisposition,
)
from tools.codex_supervisor.durability.reconciliation import EffectReconciler, ReconciliationError
from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner, SessionOwnerError
from tools.codex_supervisor.durability.static_guards import scan_package, scan_source_text, summarize_guard_violations
from tools.codex_supervisor.mailbox_store import MailboxStore
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, SubmissionState, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns
from tools.codex_supervisor.mutation_intents import MutationIntentError, MutationIntentStore
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def _run(coro):
    return asyncio.run(coro)


def _client(tmp_path: Path, mode: str, timeout: float = 0.4):
    config = make_observer_config(tmp_path, request_timeout_seconds=timeout)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        tmp_path,
        tmp_path / "err.log",
        extra_env={"FAKE_APP_SERVER_MODE": mode},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )
    return transport, AppServerClient(transport, config)


def test_timeout_result_cannot_advance_managed_turn_to_submitted(tmp_path: Path) -> None:
    async def body() -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        transport, client = _client(tmp_path, "turn_start_hang", timeout=0.2)
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        with pytest.raises(ManagedTurnError, match="uncertain"):
            await turns.submit(intent_id, "hello")
        row = turns._row(intent_id)
        assert row["submission_state"] == SubmissionState.SUBMISSION_UNCERTAIN.value
        effect = EffectJournal(store.store.connection).get(str(row["effect_id"]))
        assert effect.state == EffectState.SUBMISSION_UNCERTAIN.value
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_timeout_result_cannot_advance_wake_to_active(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system="OPERATOR",
            source_event_key="k1",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind="OPERATOR_ATTENTION_REQUEST",
            subject_ref="s",
            payload_ref="p",
        )
        mailbox.mark_eligible(message.message_id)
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
        leases = SchedulerLeases(seeded["supervisor"])
        lease = leases.acquire(seeded["portfolio_binding_id"], "sched")
        batch = batches.prepare(
            binding_id=seeded["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[message],
            lease_generation=int(lease["generation"]),
            lease_holder="sched",
        )
        transport, client = _client(tmp_path, "turn_start_hang", timeout=0.2)
        await transport.start()
        await client.initialize()
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            leases,
            WakeRecovery(seeded["bindings"], mailbox, batches, client, leases, "sched"),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="sched",
        )
        with pytest.raises(WakeSchedulerError, match="uncertain"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        row = batches.get(str(batch["wake_batch_id"]))
        assert row is not None
        assert row["state"] == "SUBMISSION_UNCERTAIN"
        assert mailbox.get(message.message_id).delivery_state.value == "SUBMISSION_UNCERTAIN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_timeout_result_cannot_mark_messages_delivered(tmp_path: Path) -> None:
    test_timeout_result_cannot_advance_wake_to_active(tmp_path)


def test_wake_claim_and_effect_write_start_are_one_transaction(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    run_id = store.start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    store.connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,
            lease_holder,lease_generation,effect_id
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t','sched',1,?)""",
        (effect.effect_id,),
    )
    store.connection.commit()
    from tools.codex_supervisor.durability.models import AggregateKind, TransitionCause, TransitionRequest

    def boom(_connection):
        raise RuntimeError("failpoint")

    with pytest.raises(RuntimeError, match="failpoint"):
        store.record_effect_write_start(
            effect_id=effect.effect_id,
            run_id=run_id,
            method="turn/start",
            payload={"id": 1, "method": "turn/start", "params": {}},
            params={},
            request_class="MUTATING_NO_RETRY",
            extra_transitions=[
                TransitionRequest(
                    aggregate_kind=AggregateKind.WAKE_BATCH,
                    aggregate_id="wake1",
                    expected_state="PREPARED",
                    expected_version=0,
                    target_state="SUBMITTING",
                    cause_kind=TransitionCause.APP_SERVER_EFFECT,
                    cause_ref=effect.effect_id,
                )
            ],
            extra_hooks=[boom],
        )
    assert journal.get(effect.effect_id).state == "PREPARED"
    assert store.connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "PREPARED"
    store.close()


def test_completed_managed_turn_requires_confirmed_effect(tmp_path: Path) -> None:
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
    store.attach_thread_for_tests(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    turns = ManagedTurns(store, object())  # type: ignore[arg-type]
    intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    from tests.codex_supervisor.helpers import drive_turn_intent

    drive_turn_intent(store.store.connection, intent_id, "OBSERVED", app_server_turn_id="turn1")
    with pytest.raises(ManagedTurnError, match="EFFECT_CONFIRMED"):
        turns.record_completion(intent_id, "completed")
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_completed_wake_requires_confirmed_effect(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k2",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind="OPERATOR_ATTENTION_REQUEST",
        subject_ref="s",
        payload_ref="p",
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=1,
        lease_holder="sched",
    )
    from tests.codex_supervisor.helpers import drive_wake_batch

    drive_wake_batch(batches, str(batch["wake_batch_id"]), "ACTIVE")
    scheduler = WakeScheduler(
        seeded["bindings"],
        mailbox,
        batches,
        SchedulerLeases(seeded["supervisor"]),
        WakeRecovery(seeded["bindings"], mailbox, batches),
        SemanticScanner(mailbox, seeded["bridge"]),
        seeded["bridge"],
        None,
        instance_id="sched",
    )
    with pytest.raises(WakeSchedulerError, match="EFFECT_CONFIRMED"):
        scheduler.observe_completion(str(batch["wake_batch_id"]), "completed")
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_later_server_request_does_not_incident_a_completed_confirmed_effect(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.observe_response(effect.effect_id, response={"ok": True}, turn_id="turn1")
    journal.confirm_effect(effect.effect_id, evidence_ref="turn:turn1")
    owner = AppServerSessionOwner(object(), store)  # type: ignore[arg-type]
    owner._open_effect_ids.add(effect.effect_id)
    owner._mark_open_effects_incident({"id": "sreq", "method": "item/command/request"})
    assert journal.get(effect.effect_id).state == EffectState.EFFECT_CONFIRMED.value
    store.close()


def test_session_owner_compatibility_rejects_every_mutating_method(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        store = ObserverStore(tmp_path / "runtime")
        owner = AppServerSessionOwner.for_client(client, store)
        for method in ("thread/start", "thread/resume", "turn/start", "thread/memoryMode/set"):
            with pytest.raises((SessionOwnerError, RuntimeError), match="submit_effect"):
                await owner.request(method, {})
        await owner.close()
        await transport.stop()
        store.close()

    _run(body())


def test_wake_recovery_creates_no_mutation_intent(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        recovery = WakeRecovery(
            seeded["bindings"],
            seeded["mailbox"],
            WakeBatchStore(seeded["supervisor"], seeded["mailbox"]),
            client,
        )
        batch_id = prepare_resume_batch(
            seeded, seeded["root_binding_id"], "kernel:resume:no-intent"
        )
        await recovery.resume_once(
            seeded["root_binding_id"], wake_batch_id=batch_id
        )
        count = seeded["supervisor"].connection.execute("SELECT COUNT(*) FROM mutation_intents").fetchone()[0]
        assert int(count) == 0
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_new_mutation_intent_writes_are_disabled(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    mutations = MutationIntentStore(store)
    with pytest.raises(MutationIntentError, match="disabled"):
        mutations.begin("turn/start", "k1")
    store.close()


def test_legacy_rows_are_conservatively_migrated(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO mutation_intents(
            intent_id,method,binding_id,client_key,state,request_json,created_at,updated_at
        ) VALUES ('mut1','thread/resume','b1','thread/resume:thr','SUBMITTING','{}','t','t')"""
    )
    connection.commit()
    initialize_database(connection)
    row = connection.execute("SELECT superseded_by_effect_id, state FROM mutation_intents").fetchone()
    assert row[0]
    effect = connection.execute("SELECT state FROM app_server_effects WHERE effect_id = ?", (row[0],)).fetchone()
    assert str(effect[0]) == "SUBMISSION_UNCERTAIN"
    connection.close()


def test_linked_wake_and_effect_incident_resolution_commits_atomically(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute("INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1','msg1',0)")
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.mark_incident(effect.effect_id, evidence_ref="sr1", incident={"reason": "server_request"})
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id = 'wake1'", (effect.effect_id,))
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'thr1', 'active', 't')"""
    )
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            run_id, direction, transport_seq, rpc_shape, turn_id, canonical_json, observed_at
        ) VALUES ('run1', 'stdout', 1, 'notification', 'turn1', '{"clientUserMessageId":"hmasd-wake:wake1"}', 't')"""
    )
    connection.commit()
    OperatorResolutionService(connection).resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
        evidence_kind="TURN",
        evidence_ref="turn1",
        turn_id="turn1",
    )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "ACTIVE"
    assert connection.execute("SELECT state FROM app_server_effects").fetchone()[0] == "OPERATOR_RESOLVED"
    assert connection.execute("SELECT delivery_state FROM mailbox_messages").fetchone()[0] == "DELIVERED_TO_TURN"
    kinds = {
        str(row[0])
        for row in connection.execute("SELECT aggregate_kind FROM operator_resolutions").fetchall()
    }
    assert kinds == {"WAKE_BATCH", "APP_SERVER_EFFECT"}
    connection.close()


def test_operator_turn_observation_requires_exact_thread(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'other', 'active', 't')"""
    )
    connection.commit()
    with pytest.raises(OperatorResolutionError, match="thread"):
        OperatorResolutionService(connection).resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
            evidence_kind="TURN",
            evidence_ref="turn1",
            turn_id="turn1",
        )
    connection.close()


def test_operator_turn_observation_requires_exact_client_message_id(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'thr1', 'active', 't')"""
    )
    connection.commit()
    with pytest.raises(OperatorResolutionError, match="clientUserMessageId"):
        OperatorResolutionService(connection).resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
            evidence_kind="TURN",
            evidence_ref="turn1",
            turn_id="turn1",
        )
    connection.close()


def test_resolution_disposition_matches_target_state(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO operator_resolutions(
            resolution_id,aggregate_kind,aggregate_id,operator,disposition,evidence_kind,evidence_ref,payload_json,created_at
        ) VALUES ('r1','WAKE_BATCH','wake1','op','ABANDON','OPERATOR','x','{}','t')"""
    )
    connection.commit()
    with pytest.raises(Exception):
        connection.execute("UPDATE wake_batches SET state='ACTIVE', version = version + 1")
    connection.close()


def test_reconciler_rejects_unstored_turn_evidence(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    reconciler = EffectReconciler(connection)
    with pytest.raises(ReconciliationError, match="caller-authored"):
        asyncio.run(reconciler.reconcile(effect.effect_id, evidence={"turn_id": "turnx"}))
    remaining = asyncio.run(reconciler.reconcile(effect.effect_id))
    assert remaining.state == EffectState.SUBMISSION_UNCERTAIN.value
    connection.close()


def test_reconciler_rejects_caller_asserted_loaded_state(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id="b1",
        binding_id="b1",
        method="thread/resume",
        client_key="thread/resume:thr1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    reconciler = EffectReconciler(connection)
    with pytest.raises(ReconciliationError, match="caller-authored"):
        asyncio.run(reconciler.reconcile(effect.effect_id, evidence={"readiness": "IDLE_LOADED"}))
    connection.close()


def test_reconciler_updates_effect_and_domain_in_one_transaction(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO managed_turn_intents(
            turn_intent_id,binding_id,intent_kind,client_user_message_id,input_ref,
            submission_state,app_server_thread_id,prepared_at,version
        ) VALUES ('t1','b1','BOOTSTRAP','k1','in','SUBMISSION_UNCERTAIN','thr1','t',1)"""
    )
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    connection.execute("UPDATE managed_turn_intents SET effect_id = ? WHERE turn_intent_id = 't1'", (effect.effect_id,))
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'thr1', 'active', 't')"""
    )
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            run_id, direction, transport_seq, rpc_shape, turn_id, canonical_json, observed_at
        ) VALUES ('run1', 'stdout', 1, 'notification', 'turn1', '{"clientUserMessageId":"k1"}', 't')"""
    )
    connection.commit()
    confirmed = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert confirmed.state == EffectState.EFFECT_CONFIRMED.value
    assert connection.execute("SELECT submission_state FROM managed_turn_intents").fetchone()[0] == "OBSERVED"
    connection.close()


def test_released_actor_before_managed_turn_write_cancels_effect(tmp_path: Path) -> None:
    from tools.codex_semantic_mvp.actor_registry import release_actor_context

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
    store.attach_thread_for_tests(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    turns = ManagedTurns(store, object())  # type: ignore[arg-type]
    intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    release_actor_context(seeded["semantic"], seeded["root"].actor_context_id)
    row = turns._row(intent_id)
    with pytest.raises(ManagedTurnError):
        asyncio.run(turns.submit(intent_id, "hello"))
    row = turns._row(intent_id)
    assert row["submission_state"] == "CANCELLED"
    effect = EffectJournal(store.store.connection).get(str(row["effect_id"]))
    assert effect.state == "CANCELLED_BEFORE_WRITE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_prepared_future_is_removed_when_write_recording_fails(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        store = ObserverStore(tmp_path / "runtime")
        store.start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id="t1",
            binding_id="b1",
            method="turn/start",
            client_key="k1",
            request={"threadId": "thr_canary", "input": []},
        )
        journal.claim_write(effect.effect_id, run_id="runx", client_request_id="1", request_row_id="r1", raw_request_seq=1)
        pending_before = dict(client._pending)
        with pytest.raises(Exception):
            await owner.submit_effect(effect.effect_id)
        assert client._pending.keys() == pending_before.keys()
        await owner.close()
        await transport.stop()
        store.close()

    _run(body())


def test_effect_raw_request_seq_points_to_exact_raw_message_row(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    run_id = store.start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    result = store.record_effect_write_start(
        effect_id=effect.effect_id,
        run_id=run_id,
        method="turn/start",
        payload={"id": 9, "method": "turn/start", "params": {"threadId": "thr1"}},
        params={"threadId": "thr1"},
        request_class="MUTATING_NO_RETRY",
    )
    updated = journal.get(effect.effect_id)
    raw = store.connection.execute(
        "SELECT raw_message_seq, effect_id FROM raw_messages WHERE raw_message_seq = ?",
        (updated.raw_request_seq,),
    ).fetchone()
    assert raw is not None
    assert int(raw[0]) == int(result["raw_message_seq"])
    assert str(raw[1]) == effect.effect_id
    store.close()


def test_doctor_reports_injected_guard_violation() -> None:
    violating = '''
def bad(client):
    client.request("turn/start", {})
    connection.execute("UPDATE wake_batches SET state='COMPLETED'")
    connection.execute("INSERT INTO mutation_intents (intent_id) VALUES ('x')")
'''
    found = scan_source_text(violating, name="bad.py")
    counts = summarize_guard_violations(found)
    assert counts["direct_mutation_call_violations"] >= 1
    assert counts["direct_state_write_violations"] >= 1
    assert counts["new_legacy_mutation_writes"] >= 1


def test_doctor_reports_actual_static_guard_results() -> None:
    from tools.codex_supervisor.doctor import collect_doctor

    report = collect_doctor(Path(__file__).resolve().parents[3])
    assert report["direct_state_write_violations"] == len(
        [item for item in scan_package() if "protected state" in item]
    )
    assert "static_guard_violations" in report


def test_real_package_static_scan_has_zero_violations() -> None:
    assert scan_package() == []


class _TimeoutResumeClient:
    def __init__(self) -> None:
        self.server_requests = asyncio.Queue()

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method, params=None):
        from types import SimpleNamespace

        return SimpleNamespace(
            request_id="1",
            method=method,
            params=dict(params or {}),
            payload={"id": 1, "method": method, "params": dict(params or {})},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
            future=None,
        )

    def discard_prepared(self, prepared) -> None:
        return None

    async def send_prepared(self, prepared) -> None:
        return None

    async def await_prepared(self, prepared, timeout=None):
        raise TimeoutError("resume timeout")

    async def request(self, method, params=None, timeout=None):
        if method == "thread/read":
            return {"result": {"thread": {"id": params.get("threadId"), "status": {"type": "idle"}, "turns": []}}}
        raise AssertionError(method)

    async def read_thread(self, thread_id: str, include_turns: bool = False):
        return {"thread": {"id": thread_id, "status": {"type": "idle"}, "turns": []}}


def test_adopt_existing_thread_timeout_does_not_attach(tmp_path: Path) -> None:
    async def body() -> None:
        from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError

        seeded = seed_managed_actors(tmp_path)
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, _TimeoutResumeClient())  # type: ignore[arg-type]
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        with pytest.raises(ProvisioningError, match="uncertain"):
            await provisioner.adopt_existing_thread(
                snapshot,
                thread_id="thr_adopt",
                repo_root=tmp_path,
                operator="operator",
                allow_existing_history=True,
                confirm_history_nonauthoritative=True,
            )
        rows = seeded["supervisor"].connection.execute(
            "SELECT binding_state FROM managed_actor_bindings"
        ).fetchall()
        assert all(str(row[0]) == "PREPARED" for row in rows)
        effect = seeded["supervisor"].connection.execute(
            "SELECT state FROM app_server_effects WHERE method = 'thread/resume'"
        ).fetchone()
        assert effect is not None
        assert str(effect[0]) == "SUBMISSION_UNCERTAIN"
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_adopt_existing_thread_uncertain_effect_is_not_confirmed(tmp_path: Path) -> None:
    test_adopt_existing_thread_timeout_does_not_attach(tmp_path)


def test_attach_rejects_effect_owned_by_another_binding(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    first = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    port = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    second = store.prepare_binding(
        port,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    journal = EffectJournal(store.store.connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id=first,
        binding_id=first,
        method="thread/resume",
        client_key="thread/resume:thr_x",
        request={"threadId": "thr_x"},
    )
    journal.claim_write(effect.effect_id, run_id="r", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.observe_response(effect.effect_id, response={"ok": True}, thread_id="thr_x")
    from tools.codex_supervisor.binding_store import BindingError

    with pytest.raises(BindingError, match="another binding"):
        store.attach_thread(second, "thr_x", effect_id=effect.effect_id)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_prepared_wake_recovery_cancels_linked_effect(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k-prep",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind="OPERATOR_ATTENTION_REQUEST",
        subject_ref="s",
        payload_ref="p",
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=1,
        lease_holder="sched",
    )
    recovery = WakeRecovery(seeded["bindings"], mailbox, batches, None)
    updated = asyncio.run(recovery.reconcile_batch(str(batch["wake_batch_id"])))
    assert updated["state"] == "CANCELLED"
    effect = EffectJournal(seeded["supervisor"].connection).get(str(batch["effect_id"]))
    assert effect.state == "CANCELLED_BEFORE_WRITE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_cancelled_owner_effect_cannot_be_submitted(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO managed_actor_bindings(
            binding_id,actor_context_id,actor_kind,semantic_scope_key,thread_id,
            thread_origin,history_trust,binding_state,memory_policy_state,
            repo_root,thread_cwd,created_by_operator,created_at
        ) VALUES ('bind1','act1','ROOT','root','thr1','NEW','FRESH','ACTIVE',
                  'OPERATOR_CONFIRMED_GLOBAL_DISABLED','r','r','op','t')"""
    )
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t',0)"""
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg-cancelled-owner','OPERATOR','src-cancelled-owner','act1',
                  'OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute(
        """INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal)
        VALUES ('wake1','msg-cancelled-owner',0)"""
    )
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1", "clientUserMessageId": "hmasd-wake:wake1"},
    )
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id='wake1'", (effect.effect_id,))
    connection.commit()
    from tools.codex_supervisor.durability.effects import cancel_prepared_wake

    cancel_prepared_wake(connection, "wake1", cause_ref="test")
    store = ObserverStore(tmp_path / "runtime")
    owner = AppServerSessionOwner(object(), store)  # type: ignore[arg-type]
    owner.journal = journal
    owner.store.connection = connection
    with pytest.raises(Exception, match="CANCELLED_BEFORE_WRITE|cannot submit"):
        asyncio.run(owner.submit_effect(effect.effect_id))
    connection.close()
    store.close()


def test_no_submission_resolution_cancels_prepared_effect(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT','hmasd-wake:wake1','t',1)"""
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute("INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1','msg1',0)")
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="hmasd-wake:wake1",
        request={"threadId": "thr1"},
    )
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id='wake1'", (effect.effect_id,))
    connection.commit()
    OperatorResolutionService(connection).resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.NO_SUBMISSION_EVIDENCE,
        evidence_kind="NONE",
        evidence_ref="none",
    )
    assert journal.get(effect.effect_id).state == "CANCELLED_BEFORE_WRITE"
    connection.close()


def test_resume_reconciler_uses_thread_snapshot_status_type(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id="b1",
        binding_id="b1",
        method="thread/resume",
        client_key="thread/resume:thr1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            raw_message_seq, run_id, direction, transport_seq, rpc_shape, thread_id, canonical_json, observed_at
        ) VALUES (2, 'run1', 'stdout', 2, 'notification', 'thr1', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO normalized_events(
            event_seq, run_id, raw_message_seq, event_kind, thread_id, payload_json, observed_at
        ) VALUES (2, 'run1', 2, 'THREAD_STATUS', 'thr1', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO thread_snapshots(thread_id, status_type, last_event_seq, first_observed_at, updated_at)
        VALUES ('thr1', 'idle', 2, 't', 't')"""
    )
    connection.commit()
    confirmed = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert confirmed.state == EffectState.EFFECT_CONFIRMED.value
    connection.close()


def test_write_started_wake_reconciliation_confirms_effect_before_delivery(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version,effect_id
        ) VALUES ('wake1','bind1','thr1','SUBMITTING','k1','t',1, NULL)"""
    )
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=1)
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id='wake1'", (effect.effect_id,))
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'thr1', 'active', 't')"""
    )
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            run_id, direction, transport_seq, rpc_shape, turn_id, canonical_json, observed_at
        ) VALUES ('run1', 'stdout', 1, 'notification', 'turn1', '{"clientUserMessageId":"k1"}', 't')"""
    )
    connection.commit()
    confirmed = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert confirmed.state == EffectState.EFFECT_CONFIRMED.value
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "ACTIVE"
    connection.close()


def test_released_actor_cannot_create_managed_thread(tmp_path: Path) -> None:
    from tools.codex_semantic_mvp.actor_registry import release_actor_context
    from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError

    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    provisioner = ManagedProvisioner(store, object())  # type: ignore[arg-type]
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
    release_actor_context(seeded["semantic"], seeded["root"].actor_context_id)
    with pytest.raises(ProvisioningError, match="ACTIVE"):
        asyncio.run(provisioner.create_fresh_thread(binding_id))
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _incident_wake(connection, *, effect_state: str, client_key: str = "hmasd-wake:wake1"):
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at,version
        ) VALUES ('wake1','bind1','thr1','INCIDENT',?,'t',1)""",
        (client_key,),
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute("INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('wake1','msg1',0)")
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="wake1",
        binding_id="bind1",
        method="turn/start",
        client_key=client_key,
        request={"threadId": "thr1"},
    )
    if effect_state != "PREPARED":
        journal.claim_write(
            effect.effect_id,
            run_id="run1",
            client_request_id="1",
            request_row_id="r1",
            raw_request_seq=1,
        )
        if effect_state == "INCIDENT":
            journal.mark_incident(effect.effect_id, evidence_ref="sr1", incident={"reason": "server_request"})
        elif effect_state == "SUBMISSION_UNCERTAIN":
            journal.mark_uncertain(effect.effect_id, reason="timeout")
        elif effect_state == "RESPONSE_OBSERVED":
            journal.observe_response(effect.effect_id, response={"ok": True}, turn_id="turn1")
    connection.execute("UPDATE wake_batches SET effect_id = ? WHERE wake_batch_id = 'wake1'", (effect.effect_id,))
    connection.execute(
        """INSERT INTO turn_snapshots(turn_id, thread_id, status, updated_at)
        VALUES ('turn1', 'thr1', 'active', 't')"""
    )
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            run_id, direction, transport_seq, rpc_shape, turn_id, canonical_json, observed_at
        ) VALUES ('run1', 'stdout', 1, 'notification', 'turn1', ?, 't')""",
        (f'{{"clientUserMessageId":"{client_key}"}}',),
    )
    connection.commit()
    return effect


def test_operator_resolved_active_wake_can_complete(tmp_path: Path) -> None:
    from tools.codex_supervisor.durability.effects import effect_is_completion_ready
    from tools.codex_supervisor.mailbox_store import MailboxStore
    from tools.codex_supervisor.wake_batches import WakeBatchStore
    from tools.codex_supervisor.wake_scheduler import WakeScheduler

    store = ObserverStore(tmp_path / "runtime")
    _incident_wake(store.connection, effect_state="INCIDENT")
    OperatorResolutionService(store.connection).resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
        evidence_kind="TURN",
        evidence_ref="turn1",
        turn_id="turn1",
    )
    assert store.connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "ACTIVE"
    effect_id = store.connection.execute("SELECT effect_id FROM wake_batches").fetchone()[0]
    assert effect_is_completion_ready(store.connection, str(effect_id))
    batches = WakeBatchStore(store, MailboxStore(store))
    scheduler = WakeScheduler.__new__(WakeScheduler)
    scheduler.batches = batches
    scheduler.bindings = type("Bindings", (), {"store": store})()
    updated = scheduler.observe_completion("wake1", "completed")
    assert updated["state"] == "COMPLETED"
    store.close()


def test_operator_observed_active_reconciles_nonincident_effect(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    effect = _incident_wake(connection, effect_state="WRITE_STARTED")
    OperatorResolutionService(connection).resolve_wake(
        "wake1",
        operator="op",
        disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
        evidence_kind="TURN",
        evidence_ref="turn1",
        turn_id="turn1",
    )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "ACTIVE"
    assert EffectJournal(connection).get(effect.effect_id).state == EffectState.EFFECT_CONFIRMED.value
    connection.close()


def test_turn_observed_resolution_rejects_prepared_effect(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    _incident_wake(connection, effect_state="PREPARED")
    with pytest.raises(OperatorResolutionError, match="PREPARED"):
        OperatorResolutionService(connection).resolve_wake(
            "wake1",
            operator="op",
            disposition=ResolutionDisposition.TURN_OBSERVED_ACTIVE,
            evidence_kind="TURN",
            evidence_ref="turn1",
            turn_id="turn1",
        )
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "INCIDENT"
    assert connection.execute("SELECT state FROM app_server_effects").fetchone()[0] == "PREPARED"
    connection.close()


def test_no_domain_only_wake_claim_api_exists() -> None:
    import ast

    from tools.codex_supervisor.durability.static_guards import PACKAGE_ROOT

    forbidden = {"begin_submission", "claim_first_submission"}
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in forbidden:
                pytest.fail(f"{path} still defines {node.name}")


def test_wake_submitting_always_has_write_started_effect(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k-submit",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind="OPERATOR_ATTENTION_REQUEST",
        subject_ref="s",
        payload_ref="p",
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=1,
        lease_holder="sched",
    )
    run_id = seeded["supervisor"].start_run(
        codex_binary="b",
        codex_version="v",
        client_name="c",
        process_id=None,
    )
    from tools.codex_supervisor.durability.models import AggregateKind, TransitionCause, TransitionRequest

    seeded["supervisor"].record_effect_write_start(
        effect_id=str(batch["effect_id"]),
        run_id=run_id,
        method="turn/start",
        payload={"id": 1, "method": "turn/start", "params": {}},
        params={},
        request_class="MUTATING_NO_RETRY",
        extra_transitions=[
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id=str(batch["wake_batch_id"]),
                expected_state="PREPARED",
                expected_version=int(batch["version"] or 0),
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref=str(batch["effect_id"]),
            )
        ],
    )
    updated = batches.get(str(batch["wake_batch_id"]))
    assert updated is not None
    assert updated["state"] == "SUBMITTING"
    effect = EffectJournal(seeded["supervisor"].connection).get(str(batch["effect_id"]))
    assert effect.state == EffectState.WRITE_STARTED.value
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_released_actor_cannot_receive_recovery_resume(tmp_path: Path) -> None:
    from tools.codex_semantic_mvp.actor_registry import release_actor_context

    seeded = seed_active_root_portfolio(tmp_path)
    batch_id = prepare_resume_batch(
        seeded, seeded["root_binding_id"], "kernel:resume:released"
    )
    release_actor_context(seeded["semantic"], seeded["root"].actor_context_id)
    recovery = WakeRecovery(
        seeded["bindings"],
        seeded["mailbox"],
        WakeBatchStore(seeded["supervisor"], seeded["mailbox"]),
        object(),
        bridge=seeded["bridge"],
    )
    readiness = asyncio.run(
        recovery.resume_once(seeded["root_binding_id"], wake_batch_id=batch_id)
    )
    assert readiness.value == "UNKNOWN"
    count = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM app_server_effects WHERE method = 'thread/resume'"
    ).fetchone()[0]
    assert int(count) == 1
    assert seeded["supervisor"].connection.execute(
        "SELECT state FROM app_server_effects WHERE method = 'thread/resume'"
    ).fetchone()[0] == "CANCELLED_BEFORE_WRITE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_nonactive_binding_cannot_receive_recovery_resume(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    batch_id = prepare_resume_batch(
        seeded, seeded["root_binding_id"], "kernel:resume:suspended"
    )
    from tools.codex_supervisor.durability.effects import (
        EffectError,
        cancel_exact_prepared_wake,
    )
    from tools.codex_supervisor.durability.transaction import DurabilityTransaction

    batch = WakeBatchStore(seeded["supervisor"], seeded["mailbox"]).get(batch_id)
    assert batch is not None
    with seeded["supervisor"]._lock, DurabilityTransaction(
        seeded["supervisor"].connection
    ):
        cancel_exact_prepared_wake(
            seeded["supervisor"].connection,
            batch_id,
            effect_id=str(batch["effect_id"]),
            binding_id=str(batch["binding_id"]),
            cause_ref="test-explicit-prepared-containment",
        )
    seeded["bindings"].suspend(seeded["root_binding_id"])
    recovery = WakeRecovery(
        seeded["bindings"],
        seeded["mailbox"],
        WakeBatchStore(seeded["supervisor"], seeded["mailbox"]),
        object(),
        bridge=seeded["bridge"],
    )
    with pytest.raises(EffectError):
        asyncio.run(
            recovery.resume_once(seeded["root_binding_id"], wake_batch_id=batch_id)
        )
    count = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM app_server_effects WHERE method = 'thread/resume'"
    ).fetchone()[0]
    assert int(count) == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_managed_turn_prepare_rolls_back_effect_when_owner_insert_fails(tmp_path, monkeypatch) -> None:
    import uuid

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
    store.attach_thread_for_tests(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    fixed = uuid.UUID(int=7)
    intent_id = f"intent_{fixed.hex}"
    seeded["supervisor"].connection.execute(
        """INSERT INTO managed_turn_intents (
            turn_intent_id, binding_id, intent_kind, client_user_message_id,
            input_ref, submission_state, app_server_thread_id, prepared_at, version
        ) VALUES (?, ?, 'BOOTSTRAP', 'dup-key', 'ref', 'PREPARED', 'thr_root', 't', 0)""",
        (intent_id, binding_id),
    )
    seeded["supervisor"].connection.commit()
    monkeypatch.setattr("tools.codex_supervisor.managed_turns.uuid.uuid4", lambda: fixed)
    turns = ManagedTurns(store, object())  # type: ignore[arg-type]
    with pytest.raises(Exception):
        turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    leftover = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM app_server_effects WHERE owner_id = ?",
        (intent_id,),
    ).fetchone()[0]
    assert int(leftover) == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_wake_prepare_rolls_back_effect_when_batch_insert_fails(tmp_path, monkeypatch) -> None:
    import uuid

    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k-rollback",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind="OPERATOR_ATTENTION_REQUEST",
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    fixed = uuid.UUID(int=9)
    wake_id = f"wake_{fixed.hex}"
    seeded["supervisor"].connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at
        ) VALUES (?, 'bindx', 'thr_port', 'PREPARED', 'dup-wake-key', 't')""",
        (wake_id,),
    )
    seeded["supervisor"].connection.commit()
    monkeypatch.setattr("tools.codex_supervisor.wake_batches.uuid.uuid4", lambda: fixed)
    with pytest.raises(Exception):
        batches.prepare(
            binding_id=seeded["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[message],
            lease_generation=1,
            lease_holder="sched",
        )
    leftover = seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM app_server_effects WHERE owner_id = ?",
        (wake_id,),
    ).fetchone()[0]
    assert int(leftover) == 0
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_orphan_effect_cannot_be_submitted(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="WAKE_BATCH",
        owner_id="missing-wake",
        binding_id="bind1",
        method="turn/start",
        client_key="orphan-key",
        request={"threadId": "thr1"},
    )
    owner = AppServerSessionOwner(object(), store)  # type: ignore[arg-type]
    with pytest.raises(SessionOwnerError, match="missing"):
        asyncio.run(owner.submit_effect(effect.effect_id))
    store.close()


def test_stale_stored_resume_snapshot_does_not_confirm(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id="b1",
        binding_id="b1",
        method="thread/resume",
        client_key="thread/resume:thr-stale",
        request={"threadId": "thr-stale"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=5)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    connection.execute(
        """INSERT INTO thread_snapshots(thread_id, status_type, last_event_seq, first_observed_at, updated_at)
        VALUES ('thr-stale', 'idle', 5, 't', 't')"""
    )
    connection.commit()
    result = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert result.state == EffectState.SUBMISSION_UNCERTAIN.value
    connection.close()


def _assert_write_start_visible(path: Path, *, effect_id: str, owner_kind: str, owner_id: str) -> None:
    other = sqlite3.connect(str(path))
    other.row_factory = sqlite3.Row
    try:
        effect = other.execute(
            "SELECT state FROM app_server_effects WHERE effect_id = ?",
            (effect_id,),
        ).fetchone()
        assert effect is not None
        assert str(effect[0]) == EffectState.WRITE_STARTED.value
        if owner_kind == "MANAGED_TURN":
            owner = other.execute(
                "SELECT submission_state FROM managed_turn_intents WHERE turn_intent_id = ?",
                (owner_id,),
            ).fetchone()
        else:
            owner = other.execute(
                "SELECT state FROM wake_batches WHERE wake_batch_id = ?",
                (owner_id,),
            ).fetchone()
        assert owner is not None
        assert str(owner[0]) == "SUBMITTING"
        raw = other.execute(
            "SELECT 1 FROM raw_messages WHERE effect_id = ? AND direction = 'stdin'",
            (effect_id,),
        ).fetchone()
        rpc = other.execute(
            "SELECT 1 FROM rpc_requests WHERE effect_id = ?",
            (effect_id,),
        ).fetchone()
        assert raw is not None
        assert rpc is not None
    finally:
        other.close()


def test_write_started_is_committed_before_transport_send_with_existing_run(tmp_path: Path) -> None:
    async def body() -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        seeded["supervisor"].start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        row = turns._row(intent_id)
        effect_id = str(row["effect_id"])
        original = client.send_prepared

        async def checking_send(prepared):
            assert not seeded["supervisor"].connection.in_transaction
            _assert_write_start_visible(
                seeded["supervisor"].path,
                effect_id=effect_id,
                owner_kind="MANAGED_TURN",
                owner_id=intent_id,
            )
            await original(prepared)

        client.send_prepared = checking_send  # type: ignore[method-assign]
        await turns.submit(intent_id, "hello")
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_crash_after_send_before_response_cannot_revert_effect_to_prepared(tmp_path: Path) -> None:
    async def body() -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        seeded["supervisor"].start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        row = turns._row(intent_id)
        effect_id = str(row["effect_id"])
        original = client.send_prepared

        async def checking_send(prepared):
            seeded["supervisor"].connection.rollback()
            _assert_write_start_visible(
                seeded["supervisor"].path,
                effect_id=effect_id,
                owner_kind="MANAGED_TURN",
                owner_id=intent_id,
            )
            await original(prepared)

        client.send_prepared = checking_send  # type: ignore[method-assign]
        await turns.submit(intent_id, "hello")
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_managed_turn_submit_has_no_ambient_transaction_at_send(tmp_path: Path) -> None:
    async def body() -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        seeded["supervisor"].start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        seen = {"in_txn": True}
        original = client.send_prepared

        async def checking_send(prepared):
            seen["in_txn"] = seeded["supervisor"].connection.in_transaction
            await original(prepared)

        client.send_prepared = checking_send  # type: ignore[method-assign]
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        await turns.submit(intent_id, "hello")
        assert seen["in_txn"] is False
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_wake_submit_has_no_ambient_transaction_at_send(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        mailbox = seeded["mailbox"]
        message = mailbox.enqueue(
            source_system="OPERATOR",
            source_event_key="k-commit",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind="OPERATOR_ATTENTION_REQUEST",
            subject_ref="s",
            payload_ref="p",
        )
        mailbox.mark_eligible(message.message_id)
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
        leases = SchedulerLeases(seeded["supervisor"])
        lease = leases.acquire(seeded["portfolio_binding_id"], "sched")
        batch = batches.prepare(
            binding_id=seeded["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[message],
            lease_generation=int(lease["generation"]),
            lease_holder="sched",
        )
        seeded["supervisor"].start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        seen = {"in_txn": True}
        original = client.send_prepared

        async def checking_send(prepared):
            seen["in_txn"] = seeded["supervisor"].connection.in_transaction
            _assert_write_start_visible(
                seeded["supervisor"].path,
                effect_id=str(batch["effect_id"]),
                owner_kind="WAKE_BATCH",
                owner_id=str(batch["wake_batch_id"]),
            )
            await original(prepared)

        client.send_prepared = checking_send  # type: ignore[method-assign]
        scheduler = WakeScheduler(
            seeded["bindings"],
            mailbox,
            batches,
            leases,
            WakeRecovery(seeded["bindings"], mailbox, batches, client, leases, "sched"),
            SemanticScanner(mailbox, seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="sched",
        )
        await scheduler.submit_batch(
            str(batch["wake_batch_id"]),
            str(batch["input_text"]),
            lease_generation=int(lease["generation"]),
        )
        assert seen["in_txn"] is False
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_prepared_request_materialization_is_retry_idempotent(tmp_path: Path) -> None:
    async def body() -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_canary")
        store.mark_verification_required(binding_id)
        transport, client = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        row = turns._row(intent_id)
        effect_id = str(row["effect_id"])
        original = seeded["supervisor"].record_effect_write_start

        def boom(*args, **kwargs):
            raise RuntimeError("materialized but not claimed")

        seeded["supervisor"].record_effect_write_start = boom  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="not claimed"):
            await turns.submit(intent_id, "hello")
        effect = EffectJournal(store.store.connection).get(effect_id)
        assert effect.state == EffectState.PREPARED.value
        assert dict(effect.request) == {
            "threadId": "thr_canary",
            "clientUserMessageId": row["client_user_message_id"],
        }
        seeded["supervisor"].record_effect_write_start = original  # type: ignore[method-assign]
        await turns.submit(intent_id, "hello")
        updated = turns._row(intent_id)
        assert updated["submission_state"] in {SubmissionState.OBSERVED.value, SubmissionState.SUBMITTED.value, "OBSERVED"}
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_generic_wake_set_state_cannot_claim_submission(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system="OPERATOR",
        source_event_key="k-set-state",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind="OPERATOR_ATTENTION_REQUEST",
        subject_ref="s",
        payload_ref="p",
    )
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
        lease_generation=1,
        lease_holder="sched",
    )
    from tools.codex_supervisor.wake_batches import WakeBatchError

    with pytest.raises(WakeBatchError, match="record_effect_write_start"):
        batches.set_state(str(batch["wake_batch_id"]), state="SUBMITTING", expected_state="PREPARED")
    row = batches.get(str(batch["wake_batch_id"]))
    assert row is not None
    assert row["state"] == "PREPARED"
    effect = EffectJournal(seeded["supervisor"].connection).get(str(batch["effect_id"]))
    assert effect.state == EffectState.PREPARED.value
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_stale_snapshot_with_larger_normalized_seq_does_not_confirm_resume(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id="b1",
        binding_id="b1",
        method="thread/resume",
        client_key="thread/resume:thr-mix",
        request={"threadId": "thr-mix"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=50)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            raw_message_seq, run_id, direction, transport_seq, rpc_shape, thread_id, canonical_json, observed_at
        ) VALUES (40, 'run1', 'stdout', 1, 'notification', 'thr-mix', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO normalized_events(
            event_seq, run_id, raw_message_seq, event_kind, thread_id, payload_json, observed_at
        ) VALUES (100, 'run1', 40, 'THREAD_STATUS', 'thr-mix', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO thread_snapshots(thread_id, status_type, last_event_seq, first_observed_at, updated_at)
        VALUES ('thr-mix', 'idle', 100, 't', 't')"""
    )
    connection.commit()
    result = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert result.state == EffectState.SUBMISSION_UNCERTAIN.value
    connection.close()


def test_stored_resume_requires_supporting_raw_message_after_effect_write(tmp_path: Path) -> None:
    connection = connect(tmp_path / "s.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_RESUME",
        owner_id="b1",
        binding_id="b1",
        method="thread/resume",
        client_key="thread/resume:thr-late",
        request={"threadId": "thr-late"},
    )
    journal.claim_write(effect.effect_id, run_id="run1", client_request_id="1", request_row_id="r1", raw_request_seq=5)
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    connection.execute(
        """INSERT INTO observer_runs(run_id, codex_binary, codex_version, client_name, started_at, runtime_home)
        VALUES ('run1', 'b', 'v', 'c', 't', '.')"""
    )
    connection.execute(
        """INSERT INTO raw_messages(
            raw_message_seq, run_id, direction, transport_seq, rpc_shape, thread_id, canonical_json, observed_at
        ) VALUES (3, 'run1', 'stdout', 1, 'notification', 'thr-late', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO normalized_events(
            event_seq, run_id, raw_message_seq, event_kind, thread_id, payload_json, observed_at
        ) VALUES (3, 'run1', 3, 'THREAD_STATUS', 'thr-late', '{}', 't')"""
    )
    connection.execute(
        """INSERT INTO thread_snapshots(thread_id, status_type, last_event_seq, first_observed_at, updated_at)
        VALUES ('thr-late', 'idle', 3, 't', 't')"""
    )
    connection.commit()
    first = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert first.state == EffectState.SUBMISSION_UNCERTAIN.value
    connection.execute(
        """INSERT INTO raw_messages(
            raw_message_seq, run_id, direction, transport_seq, rpc_shape, thread_id, canonical_json, observed_at
        ) VALUES (6, 'run1', 'stdout', 2, 'notification', 'thr-late', '{}', 't')"""
    )
    connection.commit()
    second = asyncio.run(EffectReconciler(connection).reconcile(effect.effect_id))
    assert second.state == EffectState.EFFECT_CONFIRMED.value
    connection.close()

