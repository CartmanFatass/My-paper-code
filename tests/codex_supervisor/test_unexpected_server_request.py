from __future__ import annotations

import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.observer import CANARY_TEXT, ObserverService
from tools.codex_supervisor.store import ObserverStore


def _run(coro):
    return asyncio.run(coro)


def _canary(tmp_path: Path, mode: str) -> ObserverService:
    config = make_observer_config(tmp_path)
    return ObserverService(
        config,
        binary=write_fake_codex(tmp_path),
        store=ObserverStore(tmp_path / "runtime"),
        process_cwd=tmp_path,
        extra_env={"FAKE_APP_SERVER_MODE": mode},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )


def test_successful_canary(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "handshake_ok")
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "ok"
        assert result.final_text == CANARY_TEXT
        assert result.thread_id == "thr_canary"
        assert not (tmp_path / "runtime" / "scratch" / result.canary_id).exists()
        methods = [
            row[0]
            for row in service.store.connection.execute(
                "SELECT method FROM app_server_outbox"
            )
        ]
        assert methods.count("thread/start") == 1
        assert methods.count("turn/start") == 1
        service.store.close()

    _run(body())


def test_canary_failed_turn(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "canary_failed")
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "incident"
        assert result.incident == "failed"
        service.store.close()

    _run(body())


def test_canary_timeout(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "canary_timeout")
        result = await service.run_ephemeral_canary(timeout_seconds=0.2)
        assert result.outcome == "incident"
        assert result.incident == "timeout"
        service.store.close()

    _run(body())


def test_canary_unexpected_server_request(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "unexpected_request")
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "incident"
        assert result.incident == "server_request"
        service.store.close()

    _run(body())


def test_canary_not_ephemeral(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "canary_not_ephemeral")
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "incident"
        assert result.incident == "not_ephemeral"
        service.store.close()

    _run(body())


def test_canary_wrong_text(tmp_path: Path) -> None:
    async def body() -> None:
        service = _canary(tmp_path, "canary_wrong_text")
        result = await service.run_ephemeral_canary(timeout_seconds=5)
        assert result.outcome == "incident"
        assert result.final_text == "NOPE"
        service.store.close()

    _run(body())
