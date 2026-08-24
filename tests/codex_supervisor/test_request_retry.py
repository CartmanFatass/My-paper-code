from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.client import MUTATING_OWNER_MESSAGE, AppServerClient
from tools.codex_supervisor.protocol import encode_jsonl
from tools.codex_supervisor.transport import AppServerTransport, TransportClosed


def _run(coro):
    return asyncio.run(coro)


def _client(
    tmp_path: Path,
    mode: str,
    *,
    overloads: str | None = None,
    request_timeout: float = 2.0,
) -> tuple[AppServerTransport, AppServerClient, list[float], list[dict]]:
    binary = write_fake_codex(tmp_path)
    config = make_observer_config(
        tmp_path,
        request_timeout_seconds=request_timeout,
        read_retry_attempts=5,
        read_retry_base_seconds=0.25,
    )
    extra = {"FAKE_APP_SERVER_MODE": mode}
    if overloads is not None:
        extra["FAKE_OVERLOADS"] = overloads
    transport = AppServerTransport(
        binary,
        config,
        process_cwd=tmp_path,
        stderr_path=tmp_path / "stderr.log",
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
        extra_env=extra,
    )
    sent: list[dict] = []
    original = transport.send

    async def capturing_send(message: dict) -> bytes:
        sent.append(dict(message))
        return await original(message)

    transport.send = capturing_send  # type: ignore[method-assign]
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    client = AppServerClient(transport, config, sleep=fake_sleep, jitter=lambda: 0.0)
    return transport, client, delays, sent


def test_read_overload_retries_with_backoff(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, delays, sent = _client(tmp_path, "overload_then_ok", overloads="2")
        await transport.start()
        await client.initialize()
        response = await client.request("thread/list", {})
        assert "result" in response
        list_sends = [item for item in sent if item.get("method") == "thread/list"]
        assert len(list_sends) == 3
        assert delays == [0.25, 0.5]
        await transport.stop()

    _run(body())


def test_loaded_list_read_overload_retries_with_backoff(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, delays, sent = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        original_send = transport.send
        attempts = 0

        async def loaded_overload(message: dict) -> bytes:
            nonlocal attempts
            if message.get("method") != "thread/loaded/list":
                return await original_send(message)
            sent.append(dict(message))
            attempts += 1
            if attempts <= 2:
                await client._route(
                    {"id": message["id"], "error": {"code": -32001, "message": "busy"}}
                )
            else:
                await client._route({"id": message["id"], "result": {"data": []}})
            return encode_jsonl(message)

        transport.send = loaded_overload  # type: ignore[method-assign]
        await client.list_loaded_threads()
        sends = [item for item in sent if item.get("method") == "thread/loaded/list"]
        assert len(sends) == 3
        assert delays == [0.25, 0.5]
        await transport.stop()

    _run(body())


@pytest.mark.parametrize("method", ["thread/start", "turn/start"])
def test_prepared_mutation_is_rejected_before_transport(tmp_path: Path, method: str) -> None:
    async def body() -> None:
        transport, client, delays, sent = _client(tmp_path, "mutation_overload")
        await transport.start()
        await client.initialize()
        prepared = client.prepare_request(method, {"threadId": "thr_x", "input": []})
        with pytest.raises(RuntimeError, match=MUTATING_OWNER_MESSAGE):
            await client.send_prepared(prepared)
        assert not [item for item in sent if item.get("method") == method]
        assert delays == []
        await transport.stop()

    _run(body())


def test_unknown_method_is_rejected_before_transport(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, delays, sent = _client(tmp_path, "handshake_ok")
        await transport.start()
        await client.initialize()
        with pytest.raises(RuntimeError, match=MUTATING_OWNER_MESSAGE):
            await client.request("thread/not-a-method", {})
        assert not [item for item in sent if item.get("method") == "thread/not-a-method"]
        assert delays == []
        await transport.stop()

    _run(body())


def test_transport_close_fails_pending(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _delays, _sent = _client(tmp_path, "no_response", request_timeout=2.0)
        await transport.start()
        await client.initialize()
        task = asyncio.create_task(client.request("thread/list", {}))
        await asyncio.sleep(0.05)
        await transport.stop()
        with pytest.raises(TransportClosed):
            await task

    _run(body())
