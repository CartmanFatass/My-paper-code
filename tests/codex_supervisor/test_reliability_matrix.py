from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.client import AppServerClient, RetryRequired, request_class_for
from tools.codex_supervisor.models import ProtocolIds, RequestClass, RpcShape
from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


MUTATING = (
    "thread/start",
    "thread/resume",
    "thread/fork",
    "turn/start",
    "turn/steer",
    "turn/interrupt",
    "thread/compact/start",
    "review/start",
)

HAZARDS = (
    "BLOCKED",
    "FAILED",
    "RELEASED",
    "PAUSE",
    "PARK",
    "RETIRE",
    "Portfolio should stop",
    "No further action",
)


def test_one_thousand_synthetic_events_are_neutral(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)
    for index in range(1000):
        thread_id = f"thr_{index % 100}"
        if index < 100:
            message = {"method": "thread/started", "params": {"thread": {"id": thread_id, "ephemeral": False}}}
        else:
            message = {
                "method": "item/agentMessage/delta",
                "params": {
                    "threadId": thread_id,
                    "turnId": f"turn_{index}",
                    "itemId": f"itm_{index}",
                    "delta": " ".join(HAZARDS),
                },
            }
        raw = store.record_raw_message(
            run_id=run_id,
            direction="stdout",
            transport_seq=index + 1,
            rpc_shape=RpcShape.NOTIFICATION,
            ids=ProtocolIds(
                None,
                str(message["method"]),
                thread_id,
                None if index < 100 else f"turn_{index}",
                None if index < 100 else f"itm_{index}",
            ),
            payload=message,
        )
        event = normalize_message(message, raw, run_id, "t")
        assert event is not None
        apply_normalized_event(store, event)
    raw_count = store.connection.execute("SELECT COUNT(*) FROM raw_messages").fetchone()[0]
    norm_count = store.connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0]
    threads = store.connection.execute("SELECT COUNT(*) FROM thread_snapshots").fetchone()[0]
    assert raw_count == 1000
    assert norm_count == 1000
    assert threads == 100
    payload_blob = "\n".join(
        row[0] for row in store.connection.execute("SELECT payload_json FROM normalized_events")
    )
    for word in ("BLOCKED", "FAILED", "RELEASED", "Portfolio"):
        assert word not in payload_blob
    store.close()


@pytest.mark.parametrize("overloads,expected_sends,expect_error", [(0, 1, False), (1, 2, False), (4, 5, False), (5, 5, True)])
def test_read_overload_matrix(tmp_path: Path, overloads: int, expected_sends: int, expect_error: bool) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, read_retry_attempts=5)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={
                "FAKE_APP_SERVER_MODE": "overload_then_ok" if overloads else "handshake_ok",
                "FAKE_OVERLOADS": str(overloads),
            },
        )
        sent: list[str] = []
        original = transport.send

        async def capture(message: dict) -> bytes:
            sent.append(str(message.get("method") or ""))
            return await original(message)

        transport.send = capture  # type: ignore[method-assign]
        client = AppServerClient(transport, config, sleep=lambda _delay: asyncio.sleep(0), jitter=lambda: 0.0)
        await transport.start()
        await client.initialize()
        if expect_error:
            with pytest.raises(Exception):
                await client.request("thread/list", {})
        else:
            await client.request("thread/list", {})
        assert sent.count("thread/list") == expected_sends
        await transport.stop()

    _run(body())


@pytest.mark.parametrize("method", MUTATING)
def test_mutation_overload_sends_once(tmp_path: Path, method: str) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "mutation_overload"},
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
        prepared = client.prepare_request(method, {"threadId": "thr_x"})
        with pytest.raises(RuntimeError, match="typed AppServerSessionOwner"):
            await client.send_prepared(prepared)
        assert sent.count(method) == 0
        client.discard_prepared(prepared)
        await transport.stop()

    _run(body())


@pytest.mark.parametrize(
    "server_method",
    (
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
        "attestation/generate",
        "unknown/server/method",
    ),
)
def test_unexpected_server_methods_terminate(tmp_path: Path, server_method: str) -> None:
    async def body() -> None:
        service = ObserverService(
            make_observer_config(tmp_path, reconcile_interval_seconds=0.2),
            binary=write_fake_codex(tmp_path),
            store=ObserverStore(tmp_path / "runtime"),
            process_cwd=tmp_path,
            extra_env={
                "FAKE_APP_SERVER_MODE": "unexpected_request",
                "FAKE_SERVER_REQUEST_METHOD": server_method,
            },
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        result = await service.serve(duration_seconds=2)
        assert result.end_kind == "UNEXPECTED_SERVER_REQUEST"
        row = service.store.connection.execute("SELECT method, handling FROM server_requests").fetchone()
        assert row[0] == server_method
        assert row[1] == "TERMINATE"
        service.store.close()

    _run(body())


def test_request_class_defaults_unknown_to_no_retry() -> None:
    assert request_class_for("thread/list") is RequestClass.READ_IDEMPOTENT
    assert request_class_for("mystery/method") is RequestClass.MUTATING_NO_RETRY
