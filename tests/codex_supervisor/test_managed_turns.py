from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, SubmissionState, ThreadOrigin
from tools.codex_supervisor.managed_turns import STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP, ManagedTurnError, ManagedTurns, client_user_message_id
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.checkpoints import materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_close, plan_epoch_open, revise_epoch


def _run(coro):
    return asyncio.run(coro)


def _assert_semantic_writer_blocked(path: Path) -> None:
    writer = sqlite3.connect(path, timeout=0.0, isolation_level=None)
    try:
        writer.execute("PRAGMA busy_timeout = 0")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            writer.execute("BEGIN IMMEDIATE")
    finally:
        writer.close()


def test_stage3_has_no_automatic_turn_loop() -> None:
    assert STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP is True


def test_submit_once_and_overload_is_uncertain(tmp_path: Path) -> None:
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
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        sent: list[str] = []
        original = transport.send

        async def capture(message: dict) -> bytes:
            sent.append(str(message.get("method") or ""))
            return await original(message)

        transport.send = capture  # type: ignore[method-assign]
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap",
            checkpoint_id=snapshot.checkpoint_id,
            expected_state_version=snapshot.state_version,
            expected_epoch_id=snapshot.epoch_id,
            expected_epoch_revision=snapshot.epoch_revision,
        )
        assert client_user_message_id(intent_id).startswith("hmasd-managed:")
        row = await turns.submit(intent_id, "hello")
        assert row["submission_state"] == SubmissionState.OBSERVED.value
        assert row["app_server_turn_id"] == "turn_canary"
        assert sent.count("turn/start") == 1
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_manual_turn_requires_active(tmp_path: Path) -> None:
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
    store.attach_thread_for_tests(binding_id, "thr_x")
    config = make_observer_config(tmp_path)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        tmp_path,
        tmp_path / "err.log",
        extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
    )
    client = AppServerClient(transport, config)
    turns = ManagedTurns(store, client)
    with pytest.raises(ManagedTurnError, match="ACTIVE"):
        turns.prepare(binding_id, intent_kind=ManagedIntentKind.MANUAL_OPERATOR, input_ref="manual")
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("drift", ["checkpoint_created", "epoch_replaced", "epoch_revision"])
def test_every_semantic_tuple_drift_cancels_prepared_turn_atomically(
    tmp_path: Path, drift: str
) -> None:
    seeded = seed_managed_actors(tmp_path)
    actor_id = seeded["root"].actor_context_id
    epoch = None
    if drift in {"epoch_replaced", "epoch_revision"}:
        epoch = plan_epoch_open(
            seeded["semantic"], actor_context_id=actor_id,
            epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
            objective="before", authority_refs=[], frozen_invariants=[], exit_boundary="done",
        )
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(actor_id)
    binding_id = store.prepare_binding(
        snapshot, repo_root=str(tmp_path), thread_cwd=str(tmp_path),
        created_by_operator="operator", thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread_for_tests(binding_id, "thr_fence")
    store.mark_verification_required(binding_id)
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    intent_id = turns.prepare(
        binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="fence",
        checkpoint_id=snapshot.checkpoint_id,
        expected_state_version=snapshot.state_version,
        expected_epoch_id=snapshot.epoch_id,
        expected_epoch_revision=snapshot.epoch_revision,
    )
    row = turns._row(intent_id)
    if drift == "checkpoint_created":
        materialize_checkpoint(seeded["semantic"], actor_id)
    elif drift == "epoch_replaced":
        assert epoch is not None
        plan_epoch_close(seeded["semantic"], epoch_id=str(epoch["epoch_id"]))
        plan_epoch_open(
            seeded["semantic"], actor_context_id=actor_id,
            epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
            objective="replacement", authority_refs=[], frozen_invariants=[], exit_boundary="done",
        )
    else:
        assert epoch is not None
        revise_epoch(
            seeded["semantic"], epoch_id=str(epoch["epoch_id"]), expected_revision=1,
            objective="revised", authority_refs=[], frozen_invariants=[],
            exit_boundary="done", reason="fixture",
        )
    with pytest.raises(ManagedTurnError, match="currentness"):
        turns._assert_submit_fence(intent_id, str(row["effect_id"]))
    assert turns._row(intent_id)["submission_state"] == "CANCELLED"
    assert turns.journal.get(str(row["effect_id"])).state == "CANCELLED_BEFORE_WRITE"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_managed_turn_guard_spans_write_started_and_ends_before_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
        store.attach_thread_for_tests(binding_id, "thr_guard")
        store.mark_verification_required(binding_id)
        seeded["supervisor"].start_run(
            codex_binary="fixture", codex_version="v", client_name="guard", process_id=None
        )
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err-guard.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        original_write_start = seeded["supervisor"]._record_authorized_effect_claim
        observed = {"before": False, "after": False, "released_at_send": False}

        def checked_write_start(**kwargs):
            _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
            observed["before"] = True
            result = original_write_start(**kwargs)
            _assert_semantic_writer_blocked(seeded["bridge"].semantic_state_path)
            observed["after"] = True
            return result

        monkeypatch.setattr(
            seeded["supervisor"], "_record_authorized_effect_claim", checked_write_start
        )
        original_send = client.send_prepared

        async def checked_send(prepared, capability=None):
            writer = sqlite3.connect(
                seeded["bridge"].semantic_state_path,
                timeout=0.0,
                isolation_level=None,
            )
            try:
                writer.execute("BEGIN IMMEDIATE")
                writer.rollback()
                observed["released_at_send"] = True
            finally:
                writer.close()
            await original_send(prepared, capability)

        client.send_prepared = checked_send  # type: ignore[method-assign]
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="guard",
        )
        await turns.submit(intent_id, "guarded")
        assert observed == {"before": True, "after": True, "released_at_send": True}
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_managed_turn_drift_immediately_before_guard_writes_no_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        actor_id = seeded["root"].actor_context_id
        snapshot = seeded["bridge"].snapshot(actor_id)
        binding_id = store.prepare_binding(
            snapshot,
            repo_root=str(tmp_path),
            thread_cwd=str(tmp_path),
            created_by_operator="operator",
            thread_origin=ThreadOrigin.NEW,
            history_trust=HistoryTrust.FRESH,
        )
        store.attach_thread_for_tests(binding_id, "thr_drift")
        store.mark_verification_required(binding_id)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err-drift.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        turns = ManagedTurns(store, client)
        intent_id = turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="drift",
        )
        row = turns._row(intent_id)
        owner = turns._owner()
        original_submit = owner.submit_managed_turn

        async def drift_then_submit(*args, **kwargs):
            with seeded["semantic"]._lock, seeded["semantic"].connection:
                seeded["semantic"].connection.execute(
                    "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                    (actor_id,),
                )
            return await original_submit(*args, **kwargs)

        monkeypatch.setattr(owner, "submit_managed_turn", drift_then_submit)
        with pytest.raises(ManagedTurnError, match="currentness"):
            await turns.submit(intent_id, "must-not-send")
        assert turns._row(intent_id)["submission_state"] == "CANCELLED"
        assert turns.journal.get(str(row["effect_id"])).state == "CANCELLED_BEFORE_WRITE"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?",
            (row["effect_id"],),
        ).fetchone()[0] == 0
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())
