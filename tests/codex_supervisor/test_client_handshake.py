from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.client import AppServerClient, HandshakeError, request_class_for
from tools.codex_supervisor.models import RequestClass
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def _started(tmp_path: Path, mode: str = "handshake_ok") -> tuple[AppServerTransport, AppServerClient, list[dict[str, Any]]]:
    binary = write_fake_codex(tmp_path)
    config = make_observer_config(tmp_path)
    transport = AppServerTransport(
        binary,
        config,
        process_cwd=tmp_path,
        stderr_path=tmp_path / "stderr.log",
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
        extra_env={"FAKE_APP_SERVER_MODE": mode},
    )
    sent: list[dict[str, Any]] = []
    original = transport.send

    async def capturing_send(message: dict[str, Any]) -> bytes:
        sent.append(dict(message))
        return await original(message)

    transport.send = capturing_send  # type: ignore[method-assign]
    client = AppServerClient(transport, config)
    return transport, client, sent


def test_handshake_sends_initialize_then_initialized(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, sent = _started(tmp_path)
        await transport.start()
        response = await client.initialize()
        assert "result" in response
        assert [item.get("method") for item in sent] == ["initialize", "initialized"]
        initialize = sent[0]
        assert initialize["id"] == 1
        assert "jsonrpc" not in initialize
        assert initialize["params"]["clientInfo"] == {
            "name": "hmasd-codex-app-server-observer",
            "title": "HMASD Codex App Server Observer",
            "version": "0.1.0",
        }
        assert initialize["params"]["capabilities"] == {"experimentalApi": False}
        assert sent[1] == {"method": "initialized", "params": {}}
        await transport.stop()

    _run(body())


def test_other_requests_wait_for_handshake(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _sent = _started(tmp_path)
        await transport.start()
        with pytest.raises(HandshakeError, match="initialize/initialized"):
            await client.request("thread/list", {})
        await transport.stop()

    _run(body())


def test_unknown_client_notification_is_rejected(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _sent = _started(tmp_path)
        await transport.start()
        with pytest.raises(HandshakeError, match="client notification"):
            await client.notify("thread/start", {})
        await transport.stop()

    _run(body())


def test_request_classes_match_docs_and_schema() -> None:
    assert request_class_for("initialize") is RequestClass.HANDSHAKE
    assert request_class_for("thread/list") is RequestClass.READ_IDEMPOTENT
    assert request_class_for("thread/read") is RequestClass.READ_IDEMPOTENT
    for method in (
        "thread/start",
        "thread/resume",
        "thread/fork",
        "turn/start",
        "turn/steer",
        "turn/interrupt",
        "thread/compact/start",
        "review/start",
        "thread/archive",
    ):
        assert request_class_for(method) is RequestClass.MUTATING_NO_RETRY


def test_queues_unexpected_server_request(tmp_path: Path) -> None:
    async def body() -> None:
        transport, client, _sent = _started(tmp_path, "unexpected_request")
        await transport.start()
        await client.initialize()
        inbound = await asyncio.wait_for(client.server_requests.get(), timeout=2)
        assert inbound["method"] == "item/commandExecution/requestApproval"
        assert "id" in inbound
        await transport.stop()

    _run(body())
