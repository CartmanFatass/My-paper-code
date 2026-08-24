from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.managed_models import (
    HistoryTrust,
    ManagedIntentKind,
    SubmissionState,
    ThreadOrigin,
)
from tools.codex_supervisor.managed_turns import (
    STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP,
    ManagedTurnError,
    ManagedTurns,
    client_user_message_id,
)
from tools.codex_supervisor.protocol import decode_jsonl_line
from tools.codex_supervisor.transport import AppServerTransport


def test_stage3_has_no_automatic_turn_loop() -> None:
    assert STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP is True


def test_submit_once_uses_exact_byte_transport(tmp_path: Path) -> None:
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
            write_fake_codex(tmp_path), config, tmp_path, tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4, terminate_timeout=0.4,
        )
        await transport.start()
        client = AppServerClient(transport, config)
        await client.initialize()
        exact_writes: list[bytes] = []
        original = transport.send_bytes

        async def capture(wire: bytes) -> bytes:
            exact_writes.append(bytes(wire))
            return await original(wire)

        transport.send_bytes = capture  # type: ignore[method-assign]
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
        assert len(exact_writes) == 1
        payload = decode_jsonl_line(exact_writes[0], config.max_jsonl_line_bytes)
        assert payload["method"] == "turn/start"
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    asyncio.run(body())


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
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    with pytest.raises(ManagedTurnError, match="ACTIVE"):
        turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.MANUAL_OPERATOR,
            input_ref="manual",
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
