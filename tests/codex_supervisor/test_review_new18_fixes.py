from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import (
    make_observer_config,
    record_completed_agent_item,
    write_fake_codex,
)
from tests.codex_supervisor.mailbox_fixtures import (
    activate_binding,
    plant_verification_receipt,
    seed_active_root_portfolio,
)
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.checkpoints import materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_packet_send import ManagedPacketSendError, ManagedPacketSender
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns
from tools.codex_supervisor.observer_evidence import ObserverEvidenceError, load_completed_final_item
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.session_guard import ManagedAppServerSession
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verification_ready(tmp_path: Path):
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
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    plant_verification_receipt(store, binding_id, snapshot, "thr_root")
    return seeded, store, binding_id


def _close(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


async def _client(tmp_path: Path, extra: dict[str, str], timeout: float = 0.4):
    config = make_observer_config(tmp_path, request_timeout_seconds=timeout)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        tmp_path,
        tmp_path / "err.log",
        extra_env=extra,
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )
    client = AppServerClient(transport, config)
    await transport.start()
    await client.initialize()
    return client, transport


def test_activation_rejects_checkpoint_changed_after_ack(tmp_path: Path) -> None:
    seeded, store, binding_id = _verification_ready(tmp_path)
    materialize_checkpoint(seeded["semantic"], seeded["root"].actor_context_id)
    with pytest.raises(BindingError, match="stale|currentness|tuple"):
        store.activate(binding_id)
    _close(seeded)


def test_activation_rejects_state_version_changed_after_ack(tmp_path: Path) -> None:
    seeded, store, binding_id = _verification_ready(tmp_path)
    seeded["semantic"].connection.execute(
        "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
        (seeded["root"].actor_context_id,),
    )
    seeded["semantic"].connection.commit()
    with pytest.raises(BindingError, match="stale|currentness|tuple"):
        store.activate(binding_id)
    _close(seeded)


def test_activation_rejects_epoch_changed_after_ack(tmp_path: Path) -> None:
    seeded, store, binding_id = _verification_ready(tmp_path)
    plan_epoch_open(
        seeded["semantic"],
        actor_context_id=seeded["root"].actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="post-ack",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="none",
    )
    with pytest.raises(BindingError, match="stale|currentness|tuple"):
        store.activate(binding_id)
    _close(seeded)


def test_verified_checkpoint_is_exactly_the_acknowledged_checkpoint(tmp_path: Path) -> None:
    seeded, store, binding_id = _verification_ready(tmp_path)
    command = seeded["supervisor"].connection.execute(
        """SELECT payload_json FROM managed_actor_commands
        WHERE command_kind = 'CONTEXT_REANCHOR_ACK' ORDER BY applied_at DESC"""
    ).fetchone()
    import json

    expected = json.loads(str(command[0]))["expected"]
    active = store.activate(binding_id)
    assert active.verified_checkpoint_id == expected["checkpoint_id"]
    assert active.verified_state_version == int(expected["state_version"] or 0)
    _close(seeded)


def test_managed_turn_submit_rejects_persisted_submitting(tmp_path: Path) -> None:
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
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    seeded["supervisor"].connection.execute(
        "UPDATE managed_turn_intents SET submission_state = 'SUBMITTING' WHERE turn_intent_id = ?",
        (intent_id,),
    )
    seeded["supervisor"].connection.commit()

    async def body() -> None:
        with pytest.raises(ManagedTurnError, match="reconcile"):
            await turns.submit(intent_id, "hello")

    asyncio.run(body())
    _close(seeded)


def test_wake_submit_rejects_persisted_submitting(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:submitting",
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
    scheduler.begin_submission(str(batch["wake_batch_id"]))

    async def body() -> None:
        with pytest.raises(WakeSchedulerError, match="reconcile"):
            await scheduler.submit_batch(str(batch["wake_batch_id"]), "no", lease_generation=1)

    asyncio.run(body())
    _close(seeded)


def test_thread_start_response_attach_is_one_durable_apply(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "handshake_ok"})
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        sent: list[str] = []
        original = transport.send

        async def capture(message: dict) -> bytes:
            sent.append(str(message.get("method") or ""))
            return await original(message)

        transport.send = capture  # type: ignore[method-assign]

        def crash(*_args, **_kwargs):
            raise RuntimeError("crash after response before attach")

        store.attach_thread = crash  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="crash after response"):
            await provisioner.create_fresh_thread(binding_id)
        with pytest.raises(ProvisioningError, match="unresolved intent"):
            await provisioner.create_fresh_thread(binding_id)
        assert sent.count("thread/start") == 1
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


def test_thread_resume_response_attach_is_one_durable_apply(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "handshake_ok"})
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        sent: list[str] = []
        original = transport.send

        async def capture(message: dict) -> bytes:
            sent.append(str(message.get("method") or ""))
            return await original(message)

        transport.send = capture  # type: ignore[method-assign]

        def crash(*_args, **_kwargs):
            raise RuntimeError("crash after resume before attach")

        store.attach_thread = crash  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="crash after resume"):
            await provisioner.adopt_existing_thread(
                snapshot,
                thread_id="thr_adopt",
                repo_root=tmp_path,
                operator="operator",
                allow_existing_history=True,
                confirm_history_nonauthoritative=True,
            )
        with pytest.raises((ProvisioningError, BindingError), match="already has|unresolved intent"):
            await provisioner.adopt_existing_thread(
                snapshot,
                thread_id="thr_adopt",
                repo_root=tmp_path,
                operator="operator",
                allow_existing_history=True,
                confirm_history_nonauthoritative=True,
            )
        assert sent.count("thread/resume") == 1
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


def test_server_request_after_turn_start_response_terminates(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(
            tmp_path,
            {"FAKE_APP_SERVER_MODE": "server_request_after_turn_start"},
        )
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
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        try:
            await turns.submit(intent_id, "hello")
        except ManagedTurnError:
            pass
        deadline = asyncio.get_event_loop().time() + 2
        while asyncio.get_event_loop().time() < deadline:
            current = turns._row(intent_id)
            if current["submission_state"] == "INCIDENT":
                break
            await asyncio.sleep(0.05)
        assert turns._row(intent_id)["submission_state"] == "INCIDENT"
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


def test_server_request_during_active_wake_marks_batch_incident(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(
            tmp_path,
            {
                "FAKE_APP_SERVER_MODE": "server_request_after_turn_start",
                "FAKE_THREAD_STATUS": "idle",
                "FAKE_LOADED_THREADS": "thr_port",
            },
        )
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:after",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="s",
            payload_ref="p",
        )
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        leases = SchedulerLeases(seeded["supervisor"])
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
        try:
            await scheduler.once()
        except WakeSchedulerError:
            pass
        deadline = asyncio.get_event_loop().time() + 2
        state = None
        while asyncio.get_event_loop().time() < deadline:
            row = seeded["supervisor"].connection.execute(
                "SELECT state FROM wake_batches ORDER BY prepared_at DESC"
            ).fetchone()
            state = None if row is None else str(row[0])
            if state == "INCIDENT":
                break
            await asyncio.sleep(0.05)
        assert state == "INCIDENT"
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


def test_one_session_level_watcher_handles_concurrent_rpc_responses(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "handshake_ok"})
        first = ManagedAppServerSession.for_client(client, seeded["supervisor"])
        second = ManagedAppServerSession.for_client(client, seeded["supervisor"])
        assert first is second
        assert ManagedAppServerSession.active_watcher_count() >= 1
        await asyncio.gather(
            first.request("thread/list", {}),
            first.request("thread/read", {"threadId": "thr_canary"}),
        )
        assert first._task is not None and not first._task.done()
        await transport.stop()
        _close(seeded)

    asyncio.run(body())


class _StubClient:
    def __init__(self, turns: list[dict[str, object]]) -> None:
        self.turns = turns

    async def read_thread(self, thread_id: str, include_turns: bool = False) -> dict[str, object]:
        return {
            "thread": {
                "id": thread_id,
                "status": {"type": "idle"},
                "turns": list(self.turns) if include_turns else [],
            }
        }


def _active_batch(tmp_path: Path, turn_id: str = "turn_active") -> dict[str, object]:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:active",
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
        lease_generation=1,
        lease_holder="sched",
    )
    mailbox.mark_delivered(message.message_id)
    batches.set_state(
        str(batch["wake_batch_id"]),
        state="ACTIVE",
        app_server_turn_id=turn_id,
        observed_at=_now(),
    )
    return {
        "seeded": seeded,
        "mailbox": mailbox,
        "batches": batches,
        "batch_id": str(batch["wake_batch_id"]),
        "message_id": message.message_id,
    }


def test_active_batch_completed_during_restart_is_reconciled(tmp_path: Path) -> None:
    async def body() -> None:
        planted = _active_batch(tmp_path, "turn_done")
        client = _StubClient(
            [{"id": "turn_done", "clientUserMessageId": f"hmasd-wake:{planted['batch_id']}", "status": "completed"}]
        )
        recovery = WakeRecovery(planted["seeded"]["bindings"], planted["mailbox"], planted["batches"], client)
        await recovery.recover()
        row = planted["batches"].get(planted["batch_id"])
        assert row is not None
        assert row["state"] == "COMPLETED"
        assert planted["mailbox"].get(planted["message_id"]).delivery_state.value == "DELIVERED_TO_TURN"
        _close(planted["seeded"])

    asyncio.run(body())


def test_active_batch_still_running_remains_active(tmp_path: Path) -> None:
    async def body() -> None:
        planted = _active_batch(tmp_path, "turn_run")
        client = _StubClient([{"id": "turn_run", "status": "inProgress"}])
        recovery = WakeRecovery(planted["seeded"]["bindings"], planted["mailbox"], planted["batches"], client)
        await recovery.recover()
        assert planted["batches"].get(planted["batch_id"])["state"] == "ACTIVE"
        _close(planted["seeded"])

    asyncio.run(body())


def test_active_batch_missing_turn_becomes_incident(tmp_path: Path) -> None:
    async def body() -> None:
        planted = _active_batch(tmp_path, "turn_missing")
        client = _StubClient([])
        recovery = WakeRecovery(planted["seeded"]["bindings"], planted["mailbox"], planted["batches"], client)
        await recovery.recover()
        assert planted["batches"].get(planted["batch_id"])["state"] == "INCIDENT"
        _close(planted["seeded"])

    asyncio.run(body())


def test_active_batch_recovery_unblocks_next_wake(tmp_path: Path) -> None:
    async def body() -> None:
        planted = _active_batch(tmp_path, "turn_done")
        client = _StubClient([{"id": "turn_done", "status": "completed"}])
        recovery = WakeRecovery(planted["seeded"]["bindings"], planted["mailbox"], planted["batches"], client)
        await recovery.recover()
        next_message = planted["mailbox"].enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:next",
            target_actor_context_id=planted["seeded"]["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="n",
            payload_ref="n",
        )
        snapshot = planted["seeded"]["bridge"].snapshot(planted["seeded"]["portfolio"].actor_context_id)
        nxt = planted["batches"].prepare(
            binding_id=planted["seeded"]["portfolio_binding_id"],
            thread_id="thr_port",
            snapshot=snapshot,
            messages=[next_message],
            lease_generation=2,
            lease_holder="sched",
        )
        assert nxt["state"] == "PREPARED"
        _close(planted["seeded"])

    asyncio.run(body())


def test_automatic_submit_requires_lease_generation(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:lease",
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
    leases = SchedulerLeases(seeded["supervisor"])
    scheduler = WakeScheduler(
        seeded["bindings"],
        mailbox,
        batches,
        leases,
        WakeRecovery(seeded["bindings"], mailbox, batches, None, leases, "sched"),
        SemanticScanner(mailbox, seeded["bridge"]),
        seeded["bridge"],
        object(),  # type: ignore[arg-type]
        instance_id="sched",
    )

    async def body() -> None:
        with pytest.raises(WakeSchedulerError, match="lease generation"):
            await scheduler.submit_batch(str(batch["wake_batch_id"]), "no")

    asyncio.run(body())
    _close(seeded)


def test_binding_revoked_after_batch_prepare_prevents_submission(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:revoked",
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
        lease_generation=1,
        lease_holder="sched",
    )
    leases = SchedulerLeases(seeded["supervisor"])
    lease = leases.acquire(seeded["portfolio_binding_id"], "sched")
    seeded["bindings"].revoke(seeded["portfolio_binding_id"])
    scheduler = WakeScheduler(
        seeded["bindings"],
        mailbox,
        batches,
        leases,
        WakeRecovery(seeded["bindings"], mailbox, batches, object(), leases, "sched"),  # type: ignore[arg-type]
        SemanticScanner(mailbox, seeded["bridge"]),
        seeded["bridge"],
        object(),  # type: ignore[arg-type]
        instance_id="sched",
    )

    async def body() -> None:
        with pytest.raises(WakeSchedulerError, match="ACTIVE"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                "no",
                lease_generation=int(lease["generation"]),
            )

    asyncio.run(body())
    _close(seeded)


def test_command_evidence_requires_exact_item_completed_method(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_x",
        turn_id="turn_x",
        text="hello",
        item_id="itm_x",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE raw_messages SET method = 'item/started' WHERE raw_message_seq = ?",
        (seq,),
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(ObserverEvidenceError, match="item/completed"):
        load_completed_final_item(seeded["supervisor"], seq)
    _close(seeded)


def test_command_evidence_requires_exact_item_id(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_x",
        turn_id="turn_x",
        text="hello",
        item_id="itm_x",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE raw_messages SET item_id = NULL WHERE raw_message_seq = ?",
        (seq,),
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(ObserverEvidenceError, match="item id"):
        load_completed_final_item(seeded["supervisor"], seq)
    _close(seeded)


def test_released_semantic_actor_cannot_send_managed_packet(tmp_path: Path) -> None:
    from tools.codex_semantic_mvp.actor_registry import release_actor_context

    seeded = seed_active_root_portfolio(tmp_path)
    payload = tmp_path / "typed-packet.md"
    payload.write_text("typed canary", encoding="utf-8")
    release_actor_context(seeded["semantic"], seeded["root"].actor_context_id)
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    with pytest.raises(ManagedPacketSendError):
        sender.send(
            source_binding_id=seeded["root_binding_id"],
            packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
            target_alias="PORTFOLIO",
            payload_ref="typed-packet.md",
            marker="ROOT_TO_PORTFOLIO_REVIEW:released",
        )
    assert seeded["bindings"].get(seeded["root_binding_id"]).binding_state.value == "SUSPENDED"
    _close(seeded)


def test_source_resolution_during_submitting_batch_preserves_reconciliation(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    scanner = SemanticScanner(seeded["mailbox"], seeded["bridge"])
    scanner.scan()
    messages = [
        item
        for item in seeded["mailbox"].list_messages()
        if item.source_system == MailboxSourceSystem.SEMANTIC_LEDGER.value
    ]
    assert messages
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
    leases = SchedulerLeases(seeded["supervisor"])
    scheduler = WakeScheduler(
        seeded["bindings"],
        seeded["mailbox"],
        batches,
        leases,
        WakeRecovery(seeded["bindings"], seeded["mailbox"], batches, None, leases, "sched"),
        scanner,
        seeded["bridge"],
        None,
        instance_id="sched",
    )
    scheduler.begin_submission(str(batch["wake_batch_id"]))
    seeded["semantic"].connection.execute("UPDATE obligations SET state = 'RESOLVED' WHERE state = 'OPEN'")
    seeded["semantic"].connection.commit()
    scanner.scan()
    remaining = seeded["mailbox"].get(messages[0].message_id)
    assert remaining.delivery_state.value == "BATCHED"
    assert remaining.source_resolved_after_submission is True
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "SUBMITTING"
    assert checkpoint["checkpoint_id"]
    _close(seeded)


def test_mailbox_command_with_unknown_ordering_is_rejected(tmp_path: Path) -> None:
    import json

    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:order",
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
    batches.set_state(str(batch["wake_batch_id"]), state="COMPLETED", app_server_turn_id="turn_wake")
    gateway = CommandGateway(seeded["bindings"], seeded["bridge"], mailbox)
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
        turn_id="turn_later",
        text=text,
        item_id="itm_later",
    )
    with pytest.raises(CommandGatewayError, match="ordering"):
        gateway.ingest_final_item(raw_message_seq=seq)
    _close(seeded)
