from __future__ import annotations

import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def test_thread_list_pagination_and_read_retry(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "stderr.log",
            extra_env={"FAKE_APP_SERVER_MODE": "two_pages", "FAKE_OVERLOADS": "1"},
        )
        sent: list[dict] = []
        original = transport.send

        async def capture(message: dict) -> bytes:
            sent.append(dict(message))
            return await original(message)

        transport.send = capture  # type: ignore[method-assign]
        delays: list[float] = []

        async def sleep(delay: float) -> None:
            delays.append(delay)

        client = AppServerClient(transport, config, sleep=sleep, jitter=lambda: 0.0)
        await transport.start()
        await client.initialize()
        threads = await client.list_threads()
        assert [item["id"] for item in threads] == ["thr_a", "thr_b"]
        list_params = [item.get("params") for item in sent if item.get("method") == "thread/list"]
        assert list_params[0] == {}
        assert list_params[1] == {"cursor": "page-2"}
        read = await client.read_thread("thr_a")
        assert read["thread"]["id"] == "thr_a"
        await transport.stop()

    _run(body())


def test_reconcile_does_not_resume(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path)
        store = ObserverStore(tmp_path / "runtime")
        outbound: list[str] = []
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=store,
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "two_pages"},
            outbound_hook=lambda message: outbound.append(str(message.get("method") or "")),
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        await service.start()
        await service.initialize()
        await service.reconcile_threads()
        await service.stop("NORMAL")
        assert "thread/resume" not in outbound
        assert "turn/start" not in outbound
        assert outbound.count("thread/list") >= 1
        assert outbound.count("thread/read") == 2
        store.close()

    _run(body())
