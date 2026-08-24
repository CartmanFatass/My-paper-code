from __future__ import annotations

import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.store import ObserverStore


def _run(coro):
    return asyncio.run(coro)


def _service(tmp_path: Path, mode: str) -> ObserverService:
    config = make_observer_config(tmp_path, reconcile_interval_seconds=0.2)
    store = ObserverStore(tmp_path / "runtime")
    return ObserverService(
        config,
        binary=write_fake_codex(tmp_path),
        store=store,
        process_cwd=tmp_path,
        extra_env={"FAKE_APP_SERVER_MODE": mode},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )


def test_end_to_end_initialize_and_reconcile(tmp_path: Path) -> None:
    async def body() -> None:
        service = _service(tmp_path, "two_pages")
        await service.start()
        await service.initialize()
        result = await service.reconcile_threads()
        await service.stop("NORMAL")
        assert result["outcome"] == "OK"
        assert result["thread_count"] == 2
        methods = [
            row[0]
            for row in service.store.connection.execute(
                "SELECT method FROM raw_messages WHERE direction='stdin' ORDER BY raw_message_seq"
            )
        ]
        assert methods[:2] == ["initialize", "initialized"]
        assert "thread/resume" not in methods
        assert "turn/start" not in methods
        kinds = {
            row[0]
            for row in service.store.connection.execute("SELECT event_kind FROM normalized_events")
        }
        assert "APP_SERVER_INITIALIZED_OBSERVED" in kinds
        assert "RECONCILIATION_COMPLETED_OBSERVED" in kinds
        assert service.store.latest_thread_snapshot("thr_a") is not None
        assert service.store.latest_thread_snapshot("thr_b") is not None
        service.store.close()

    _run(body())


def test_unexpected_request_quarantines_session_but_host_reaches_deadline(tmp_path: Path) -> None:
    async def body() -> None:
        service = _service(tmp_path, "unexpected_request")
        result = await service.serve(duration_seconds=2)
        assert result.end_kind == "NORMAL"
        rows = service.store.connection.execute("SELECT handling, method FROM server_requests").fetchall()
        assert rows
        assert rows[0][0] == "SESSION_QUARANTINE"
        assert rows[0][1] == "item/commandExecution/requestApproval"
        service.store.close()

    _run(body())
