from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import (
    make_observer_config,
    record_completed_agent_item,
    write_fake_codex,
)
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.cli import main
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem, MAX_WAKE_INPUT_BYTES
from tools.codex_supervisor.mailbox_store import MailboxStoreError
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin
from tools.codex_supervisor.managed_packet_send import ManagedPacketSendError, ManagedPacketSender
from tools.codex_supervisor.managed_runtime import ManagedRuntime, ManagedRuntimeError
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.scheduler_leases import LeaseError, SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore, build_wake_text
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def _long_message(mailbox, target: str, index: int):
    return mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"op:overflow:{index}",
        target_actor_context_id=target,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="x" * 4000,
        payload_ref="y" * 4000,
        priority=1,
    )


def test_activate_requires_applied_verification_receipt(tmp_path: Path) -> None:
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
    store.attach_thread(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    with pytest.raises(BindingError, match="verification"):
        store.activate(binding_id)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_cli_activate_cannot_bypass_verification(tmp_path: Path, repo_root: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    observer = ObserverStore(runtime)
    bindings = BindingStore(observer, seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = bindings.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    bindings.attach_thread(binding_id, "thr_cli")
    bindings.mark_verification_required(binding_id)
    bindings.confirm_global_memory_disabled(binding_id, operator="operator")
    observer.close()
    with pytest.raises(SystemExit, match="cannot bypass verification"):
        main(
            [
                "--repo-root",
                str(repo_root),
                "--runtime-home",
                str(runtime),
                "managed",
                "--operator",
                "operator",
                "activate",
                "--binding-id",
                binding_id,
            ]
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_command_gateway_rejects_unrecorded_final_item(tmp_path: Path) -> None:
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
    store.attach_thread(binding_id, "thr_cmd")
    store.mark_verification_required(binding_id)
    gateway = CommandGateway(store, seeded["bridge"])
    with pytest.raises(CommandGatewayError, match="unrecorded"):
        gateway.ingest_final_item(raw_message_seq=999)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_command_gateway_rejects_turn_thread_mismatch(tmp_path: Path) -> None:
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
    store.attach_thread(binding_id, "thr_cmd")
    store.mark_verification_required(binding_id)
    gateway = CommandGateway(store, seeded["bridge"])
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_cmd",
        turn_id="turn_mismatch",
        text="x",
    )
    seeded["supervisor"].connection.execute(
        "UPDATE turn_snapshots SET thread_id = 'thr_other' WHERE turn_id = 'turn_mismatch'"
    )
    seeded["supervisor"].connection.commit()
    with pytest.raises(CommandGatewayError, match="mismatch"):
        gateway.ingest_final_item(raw_message_seq=seq)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_wake_batch_overflow_and_envelope_ids(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    target = seeded["portfolio"].actor_context_id
    messages = [_long_message(mailbox, target, index) for index in range(8)]
    snapshot = seeded["bridge"].snapshot(target)
    envelope = build_wake_text(snapshot, wake_batch_id="wake_budget", messages=messages)
    assert envelope.included_message_ids
    assert envelope.excluded_message_ids
    assert len(envelope.text.encode("utf-8")) <= MAX_WAKE_INPUT_BYTES
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=messages,
    )
    included = set(batch["included_message_ids"])
    batched = {item.message_id for item in batches.messages_for(str(batch["wake_batch_id"]))}
    assert batched == included
    for message in messages:
        if message.message_id in included:
            assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
        else:
            assert mailbox.get(message.message_id).delivery_state.value in {"ENQUEUED", "ELIGIBLE"}
    injection = dict(
        seeded["supervisor"].connection.execute(
            "SELECT mailbox_message_ids_json FROM managed_context_injections WHERE turn_intent_id = ?",
            (batch["wake_batch_id"],),
        ).fetchone()
    )
    recorded = set(json.loads(injection["mailbox_message_ids_json"]))
    assert recorded == included
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_uncertain_message_cannot_be_acknowledged_or_intaken(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:unc",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    mailbox.mark_eligible(message.message_id)
    mailbox.mark_batched(message.message_id)
    mailbox.mark_uncertain(message.message_id)
    with pytest.raises(MailboxStoreError, match="delivered"):
        mailbox.acknowledge(message.message_id)
    with pytest.raises(MailboxStoreError, match="delivered"):
        mailbox.intake(message.message_id)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_packet_marker_conflict(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    payload = tmp_path / "typed-packet.md"
    payload.write_text("typed canary", encoding="utf-8")
    other = tmp_path / "other.md"
    other.write_text("other", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    sender.send(
        source_binding_id=seeded["root_binding_id"],
        packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
        target_alias="PORTFOLIO",
        payload_ref="typed-packet.md",
        marker="ROOT_TO_PORTFOLIO_REVIEW:conflict",
    )
    with pytest.raises(ManagedPacketSendError, match="conflicts"):
        sender.send(
            source_binding_id=seeded["root_binding_id"],
            packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
            target_alias="PORTFOLIO",
            payload_ref="other.md",
            marker="ROOT_TO_PORTFOLIO_REVIEW:conflict",
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_resolved_obligation_and_applied_packet_are_not_deliverable(tmp_path: Path) -> None:
    from tests.codex_supervisor.semantic_fixtures import seed_reanchor
    from tools.codex_semantic_mvp.packet_refs import packet_register

    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    packet = packet_register(
        seeded["semantic"],
        packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
        source_actor_context_id=seeded["root"].actor_context_id,
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        payload_ref="docs/canary.md",
        marker="marker-scan-resolve",
        direction_id="demo",
    )
    scanner = SemanticScanner(seeded["mailbox"], seeded["bridge"])
    scanner.scan()
    seeded["semantic"].connection.execute(
        "UPDATE obligations SET state = 'RESOLVED' WHERE state = 'OPEN'"
    )
    seeded["semantic"].connection.execute(
        "UPDATE packet_refs SET intake_state = 'APPLIED' WHERE packet_id = ?",
        (packet["packet_id"],),
    )
    seeded["semantic"].connection.commit()
    scanner.scan()
    remaining = [
        message
        for message in seeded["mailbox"].list_messages()
        if message.source_system == "SEMANTIC_LEDGER"
        and message.delivery_state.value in {"ENQUEUED", "ELIGIBLE", "BATCHED"}
    ]
    assert remaining == []
    assert checkpoint["checkpoint_id"]
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_two_sqlite_connections_cannot_both_hold_lease(tmp_path: Path) -> None:
    store_a = ObserverStore(tmp_path)
    store_b = ObserverStore(tmp_path)
    first = SchedulerLeases(store_a).acquire("bind_a", "inst-1", ttl_seconds=30)
    assert first["generation"] == 1
    with pytest.raises(LeaseError):
        SchedulerLeases(store_b).acquire("bind_a", "inst-2", ttl_seconds=30)
    store_a.close()
    store_b.close()


def test_timeline_out_rejects_repo_path(tmp_path: Path, repo_root: Path) -> None:
    runtime = Path(tempfile.mkdtemp(prefix="hmasd-obs-cli-"))
    ObserverStore(runtime).close()
    forbidden = repo_root / "AGENTS.md"
    with pytest.raises(SystemExit, match="exports"):
        main(
            [
                "--repo-root",
                str(repo_root),
                "--runtime-home",
                str(runtime),
                "timeline",
                "--thread-id",
                "thr_x",
                "--out",
                str(forbidden),
            ]
        )


def test_crash_after_send_before_response_does_not_requeue(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:crash",
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
    asyncio.run(scheduler.recovery.recover())
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "SUBMITTING"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


async def _client(tmp_path: Path, extra: dict[str, str], timeout: float = 0.3):
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


def test_turn_start_timeout_marks_uncertain(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "turn_start_hang"})
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:to",
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
        with pytest.raises(WakeSchedulerError, match="uncertain"):
            await scheduler.once()
        open_batch = batches.open_batch_for_binding(seeded["portfolio_binding_id"])
        assert open_batch is not None
        assert open_batch["state"] == "SUBMISSION_UNCERTAIN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_resume_timeout_is_not_resubmitted(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(
            tmp_path,
            {"FAKE_APP_SERVER_MODE": "resume_hang", "FAKE_THREAD_STATUS": "notLoaded"},
        )
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:resume",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="s",
            payload_ref="p",
        )
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        leases = SchedulerLeases(seeded["supervisor"])
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, client, leases, "sched")
        first = await recovery.resume_once(seeded["portfolio_binding_id"])
        second = await recovery.resume_once(seeded["portfolio_binding_id"])
        assert first.value == "UNKNOWN"
        assert second.value == "UNKNOWN"
        open_intents = seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM mutation_intents WHERE method = 'thread/resume'"
        ).fetchone()[0]
        assert int(open_intents) == 1
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_thread_start_timeout_requires_reconciliation(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "thread_start_hang"})
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        with pytest.raises(ProvisioningError, match="uncertain"):
            await provisioner.create_fresh_thread(binding_id)
        with pytest.raises(ProvisioningError, match="unresolved intent"):
            await provisioner.create_fresh_thread(binding_id)
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_loaded_list_error_is_unknown(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(
            tmp_path,
            {"FAKE_APP_SERVER_MODE": "loaded_list_error", "FAKE_THREAD_STATUS": "idle"},
        )
        mailbox = seeded["mailbox"]
        batches = WakeBatchStore(seeded["supervisor"], mailbox)
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, client)
        readiness = await recovery.classify(seeded["portfolio_binding_id"])
        assert readiness.value == "UNKNOWN"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_loaded_list_timeout_never_starts_turn(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(
            tmp_path,
            {"FAKE_APP_SERVER_MODE": "loaded_list_hang", "FAKE_THREAD_STATUS": "idle"},
            timeout=0.2,
        )
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:loaded",
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
        result = await scheduler.once()
        assert result["scheduled"] is None or result["scheduled"].get("readiness") == "UNKNOWN"
        assert batches.open_batch_for_binding(seeded["portfolio_binding_id"]) is None
        methods = [
            row[0]
            for row in seeded["supervisor"].connection.execute(
                "SELECT method FROM mutation_intents"
            ).fetchall()
        ]
        assert "turn/start" not in methods
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_server_request_during_bootstrap_and_wake_marks_incident(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        client, transport = await _client(tmp_path, {"FAKE_APP_SERVER_MODE": "server_request_on_turn"})
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        await provisioner.create_fresh_thread(binding_id)
        provisioner.confirm_global_memory_disabled(binding_id, operator="operator")
        runtime = ManagedRuntime(store, ManagedTurns(store, client), CommandGateway(store, seeded["bridge"]), seeded["bridge"])
        with pytest.raises(ManagedTurnError):
            await runtime.submit_verification(binding_id, snapshot)
        intent = store.store.connection.execute(
            "SELECT submission_state FROM managed_turn_intents WHERE binding_id = ?",
            (binding_id,),
        ).fetchone()
        assert intent is not None
        assert str(intent[0]) == "INCIDENT"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


def test_server_request_during_wake_terminates(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        client, transport = await _client(
            tmp_path,
            {
                "FAKE_APP_SERVER_MODE": "server_request_on_turn",
                "FAKE_THREAD_STATUS": "idle",
                "FAKE_LOADED_THREADS": "thr_port",
            },
        )
        mailbox = seeded["mailbox"]
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:wake-req",
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
        with pytest.raises(WakeSchedulerError, match="incident"):
            await scheduler.once()
        open_batch = batches.open_batch_for_binding(seeded["portfolio_binding_id"])
        assert open_batch is None or open_batch["state"] == "INCIDENT"
        row = seeded["supervisor"].connection.execute(
            "SELECT state FROM wake_batches ORDER BY prepared_at DESC"
        ).fetchone()
        assert row is not None
        assert str(row[0]) == "INCIDENT"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())
