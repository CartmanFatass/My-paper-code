from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import (
    insert_submittable_owner_for_effect,
    make_observer_config,
    submit_typed_for_test,
    write_fake_codex,
)
from tools.codex_supervisor.client import UnexpectedServerRequest
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def _stack(tmp_path: Path, mode: str):
    config = make_observer_config(tmp_path)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        process_cwd=tmp_path,
        stderr_path=tmp_path / "stderr.log",
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
        extra_env={"FAKE_APP_SERVER_MODE": mode},
    )
    from tools.codex_supervisor.client import AppServerClient

    client = AppServerClient(transport, config)
    store = ObserverStore(tmp_path / "runtime")
    store.start_run(codex_binary="b", codex_version="v", client_name="c", process_id=None)
    return transport, client, store


def test_server_request_before_response_marks_effect_incident(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "server_request_on_turn")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id="turn1",
            binding_id="bind1",
            method="turn/start",
            client_key="wake-1",
            request={"threadId": "thr_canary", "input": [{"type": "text", "text": "test"}], "approvalPolicy": "never", "clientUserMessageId": "PLACEHOLDER"},
        )
        insert_submittable_owner_for_effect(store.connection, effect)
        with pytest.raises(UnexpectedServerRequest):
            await submit_typed_for_test(owner, effect.effect_id)
        assert journal.get(effect.effect_id).state == EffectState.INCIDENT.value
        assert AppServerSessionOwner.active_watcher_count() == 1
        await owner.close()
        await transport.stop()

    _run(body())


def test_server_request_with_response_still_incidents(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "server_request_then_thread_start_response")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="THREAD_PROVISION",
            owner_id="bind1",
            binding_id="bind1",
            method="thread/start",
            client_key="thread/start:bind1",
            request={"cwd": str(tmp_path), "ephemeral": False, "approvalPolicy": "never"},
        )
        insert_submittable_owner_for_effect(store.connection, effect)
        with pytest.raises(UnexpectedServerRequest):
            await submit_typed_for_test(owner, effect.effect_id)
        assert journal.get(effect.effect_id).state == EffectState.INCIDENT.value
        await owner.close()
        await transport.stop()

    _run(body())


def test_server_request_after_response_marks_linked_effect(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "server_request_after_turn_start")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id="turn1",
            binding_id="bind1",
            method="turn/start",
            client_key="hmasd-managed:turn1",
            request={"threadId": "thr_canary", "input": [{"type": "text", "text": "test"}], "approvalPolicy": "never", "clientUserMessageId": "PLACEHOLDER"},
        )
        insert_submittable_owner_for_effect(store.connection, effect)
        try:
            result = await submit_typed_for_test(owner, effect.effect_id)
            assert result.state in {EffectState.RESPONSE_OBSERVED.value, EffectState.INCIDENT.value}
        except UnexpectedServerRequest:
            pass
        await asyncio.sleep(0.1)
        assert journal.get(effect.effect_id).state == EffectState.INCIDENT.value
        assert owner.terminated
        await owner.close()
        await transport.stop()

    _run(body())


def test_two_simultaneous_read_rpc_responses(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        first, second = await asyncio.gather(
            owner.request_read("thread/list", {}),
            owner.request_read("thread/list", {}),
        )
        assert "result" in first
        assert "result" in second
        await owner.close()
        await transport.stop()

    _run(body())


def test_one_server_request_consumer_per_client(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        first = AppServerSessionOwner.for_client(client, store)
        second = AppServerSessionOwner.for_client(client, store)
        assert first is second
        assert AppServerSessionOwner.active_watcher_count() == 1
        await first.close()
        await transport.stop()

    _run(body())


def test_effect_incident_persists_after_response_race(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "server_request_then_thread_start_response")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="THREAD_PROVISION",
            owner_id="bind1",
            binding_id="bind1",
            method="thread/start",
            client_key="thread/start:bind1",
            request={"cwd": str(tmp_path), "ephemeral": False, "approvalPolicy": "never"},
        )
        insert_submittable_owner_for_effect(store.connection, effect)
        with pytest.raises(UnexpectedServerRequest):
            await submit_typed_for_test(owner, effect.effect_id)
        later = journal.get(effect.effect_id)
        assert later.state == EffectState.INCIDENT.value
        with pytest.raises(Exception):
            journal.observe_response(effect.effect_id, response={"ok": True})
        await owner.close()
        await transport.stop()

    _run(body())


def test_write_started_effect_is_not_resubmitted(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, store = _stack(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        owner = AppServerSessionOwner.for_client(client, store)
        journal = EffectJournal(store.connection)
        effect = journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id="turn1",
            binding_id="bind1",
            method="turn/start",
            client_key="k1",
            request={"threadId": "thr_canary", "input": [{"type": "text", "text": "test"}], "approvalPolicy": "never", "clientUserMessageId": "PLACEHOLDER"},
        )
        insert_submittable_owner_for_effect(store.connection, effect)
        first = await submit_typed_for_test(owner, effect.effect_id)
        assert first.state == EffectState.RESPONSE_OBSERVED.value
        with pytest.raises(Exception, match="not PREPARED|never automatically submitted"):
            await submit_typed_for_test(owner, effect.effect_id)
        await owner.close()
        await transport.stop()

    _run(body())
