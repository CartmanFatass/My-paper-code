from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, SubmissionState, ThreadOrigin
from tools.codex_supervisor.managed_turns import STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP, ManagedTurnError, ManagedTurns, client_user_message_id
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


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
        intent_id = turns.prepare(binding_id, intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
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
