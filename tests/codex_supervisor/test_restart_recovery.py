from __future__ import annotations

import asyncio
from pathlib import Path

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.store import ObserverStore


def _run(coro):
    return asyncio.run(coro)


def test_recover_incomplete_run_does_not_delete_logs(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=99)
    store.append_raw_file(run_id, "stdout.jsonl", b"{}\n")
    store.close()
    again = ObserverStore(tmp_path)
    recovered = again.recover_incomplete_runs()
    assert recovered == [run_id]
    row = again.connection.execute("SELECT end_kind FROM observer_runs WHERE run_id=?", (run_id,)).fetchone()
    assert row[0] == "PROCESS_EXIT"
    assert (tmp_path / "raw" / run_id / "stdout.jsonl").read_bytes() == b"{}\n"
    again.close()


def test_eof_preserves_snapshots_and_does_not_resume(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path, reconcile_interval_seconds=0.2)
        store = ObserverStore(tmp_path / "runtime")
        outbound: list[str] = []
        service = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=store,
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "exit_after_initialize"},
            outbound_hook=lambda message: outbound.append(str(message.get("method") or "")),
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        await service.start()
        try:
            await service.initialize()
        except Exception:
            pass
        result = await service.stop("TRANSPORT_EOF")
        assert result.end_kind == "TRANSPORT_EOF"
        assert "thread/resume" not in outbound
        assert "turn/start" not in outbound
        kinds = {row[0] for row in store.connection.execute("SELECT event_kind FROM normalized_events")}
        assert "TRANSPORT_EOF_OBSERVED" in kinds or "APP_SERVER_PROCESS_EXITED_OBSERVED" in kinds
        store.close()

    _run(body())


def test_restart_reconciliation_has_no_duplicate_thread_ids(tmp_path: Path) -> None:
    async def body() -> None:
        config = make_observer_config(tmp_path)
        store = ObserverStore(tmp_path / "runtime")
        first = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=store,
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "two_pages"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        await first.start()
        await first.initialize()
        await first.reconcile_threads()
        first_run = first.run_id
        await first.stop("NORMAL")
        second = ObserverService(
            config,
            binary=write_fake_codex(tmp_path),
            store=store,
            process_cwd=tmp_path,
            extra_env={"FAKE_APP_SERVER_MODE": "two_pages"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        await second.start()
        assert second.run_id != first_run
        await second.initialize()
        await second.reconcile_threads()
        await second.stop("NORMAL")
        ids = [row[0] for row in store.connection.execute("SELECT thread_id FROM thread_snapshots ORDER BY thread_id")]
        assert ids == ["thr_a", "thr_b"]
        store.close()

    _run(body())
