from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.test_request_retry import _client
from tools.codex_supervisor.client import MUTATING_OWNER_MESSAGE
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.store import ObserverStore


def _run(coro):
    return asyncio.run(coro)


def test_prepare_request_sends_no_bytes(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _delays, sent = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        sent.clear()
        prepared = client.prepare_request("thread/list", {})
        assert prepared.method == "thread/list"
        assert prepared.request_id
        assert sent == []
        await transport.stop()

    _run(body())


def test_send_prepared_sends_once_and_await_does_not_resend(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _delays, sent = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        sent.clear()
        prepared = client.prepare_request("thread/list", {})
        await client.send_prepared(prepared)
        response = await client.await_prepared(prepared)
        assert "result" in response
        assert [item.get("method") for item in sent] == ["thread/list"]
        await transport.stop()

    _run(body())


def test_request_rejects_mutating_methods(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _delays, _sent = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        with pytest.raises(RuntimeError, match=MUTATING_OWNER_MESSAGE):
            await client.request("turn/start", {"threadId": "thr1", "input": []})
        await transport.stop()

    _run(body())


def test_record_effect_write_start_is_one_transaction(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    run_id = store.start_run(
        codex_binary="b",
        codex_version="v",
        client_name="c",
        process_id=None,
    )
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="turn1",
        binding_id="bind1",
        method="turn/start",
        client_key="msg1",
        request={"threadId": "thr1"},
    )
    with store._lock, DurabilityTransaction(store.connection):
        result = store._record_authorized_effect_claim(
            effect_id=effect.effect_id,
            run_id=run_id,
            method="turn/start",
            payload={"id": 9, "method": "turn/start", "params": {"threadId": "thr1"}},
            params={"threadId": "thr1"},
            request_class="MUTATING_NO_RETRY",
        )
    updated = journal.get(effect.effect_id)
    assert updated.state == EffectState.WRITE_STARTED.value
    assert updated.raw_request_seq == result["raw_request_seq"]
    raw = store.connection.execute(
        "SELECT effect_id, method FROM raw_messages WHERE effect_id = ?",
        (effect.effect_id,),
    ).fetchone()
    rpc = store.connection.execute(
        "SELECT effect_id, method FROM rpc_requests WHERE effect_id = ?",
        (effect.effect_id,),
    ).fetchone()
    audit = store.connection.execute(
        "SELECT to_state FROM control_transitions WHERE aggregate_id = ?",
        (effect.effect_id,),
    ).fetchone()
    assert raw[0] == effect.effect_id
    assert rpc[0] == effect.effect_id
    assert audit[0] == "WRITE_STARTED"
    store.close()


def test_write_start_rolls_back_if_claim_fails(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    run_id = store.start_run(
        codex_binary="b",
        codex_version="v",
        client_name="c",
        process_id=None,
    )
    journal = EffectJournal(store.connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="turn1",
        binding_id="bind1",
        method="turn/start",
        client_key="msg1",
        request={"threadId": "thr1"},
    )
    with store._lock, DurabilityTransaction(store.connection):
        store._record_authorized_effect_claim(
            effect_id=effect.effect_id,
            run_id=run_id,
            method="turn/start",
            payload={"id": 1, "method": "turn/start", "params": {}},
            params={},
            request_class="MUTATING_NO_RETRY",
        )
    with pytest.raises(Exception):
        with store._lock, DurabilityTransaction(store.connection):
            store._record_authorized_effect_claim(
                effect_id=effect.effect_id,
                run_id=run_id,
                method="turn/start",
                payload={"id": 2, "method": "turn/start", "params": {}},
                params={},
                request_class="MUTATING_NO_RETRY",
            )
    assert store.connection.execute("SELECT COUNT(*) FROM rpc_requests").fetchone()[0] == 1
    assert journal.get(effect.effect_id).state == EffectState.WRITE_STARTED.value
    store.close()
