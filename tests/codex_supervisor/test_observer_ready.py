from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.cli import _archive_host_signal, _parser, _require_external_path
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.session_guard import ManagedAppServerSession
from tools.codex_supervisor.store import ObserverStore


def test_serve_cli_accepts_profile_ready_and_control_paths() -> None:
    args = _parser().parse_args(
        [
            "serve",
            "--profile",
            "MAILBOX_MANUAL",
            "--ready-file",
            "C:/runtime/ready.json",
            "--control-home",
            "C:/runtime/control",
        ]
    )
    assert args.profile == "MAILBOX_MANUAL"
    assert args.ready_file == "C:/runtime/ready.json"
    assert args.control_home == "C:/runtime/control"


def test_cli_rejects_ready_and_control_paths_under_repo(repo_root: Path) -> None:
    with pytest.raises(SystemExit, match="ready file"):
        _require_external_path(repo_root, repo_root / "runtime" / "ready.json", "ready file")
    with pytest.raises(SystemExit, match="control home"):
        _require_external_path(repo_root, repo_root / "runtime" / "control", "control home")


def test_cli_archives_stale_ready_and_invalidates_live_signal(tmp_path: Path) -> None:
    runtime_home = tmp_path / "runtime"
    ready = tmp_path / "external-ready.json"
    ready.write_text('{"schema":"HMASD_SUPERVISOR_READY_V2"}\n', encoding="utf-8")

    archived = _archive_host_signal(ready, runtime_home, "ready-prelaunch")

    assert archived is not None and archived.is_file()
    assert not ready.exists()
    assert archived.read_text(encoding="utf-8") == '{"schema":"HMASD_SUPERVISOR_READY_V2"}\n'


def _service(tmp_path: Path) -> ObserverService:
    return ObserverService(
        make_observer_config(tmp_path, reconcile_interval_seconds=0.02),
        binary=write_fake_codex(tmp_path),
        store=ObserverStore(tmp_path / "runtime"),
        process_cwd=tmp_path,
        extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )


def test_ready_hook_runs_after_initialize_watcher_and_reconciliation(tmp_path: Path) -> None:
    async def body() -> None:
        service = _service(tmp_path)
        observed: list[dict[str, object]] = []

        async def ready_hook(payload: dict[str, object]) -> None:
            run = service.store.connection.execute(
                "SELECT initialized_at FROM observer_runs WHERE run_id = ?", (service.run_id,)
            ).fetchone()
            reconciliation = service.store.connection.execute(
                "SELECT outcome FROM reconciliation_runs ORDER BY reconciliation_id DESC LIMIT 1"
            ).fetchone()
            assert run is not None and run[0]
            assert reconciliation is not None and reconciliation[0] == "OK"
            assert ManagedAppServerSession.active_watcher_count() == 1
            observed.append(payload)

        result = await service.serve(duration_seconds=0.05, ready_hook=ready_hook)

        assert result.end_kind == "NORMAL"
        assert len(observed) == 1
        assert observed[0]["watcher_active"] is True
        assert observed[0]["first_reconciliation_completed"] is True
        assert observed[0]["run_id"]
        assert observed[0]["process_id"] == os.getpid()
        child = service.store.connection.execute(
            "SELECT process_id FROM observer_runs WHERE run_id = ?", (result.run_id,)
        ).fetchone()
        assert child is not None and child[0]
        assert child[0] != observed[0]["process_id"]
        service.store.close()

    import asyncio

    asyncio.run(body())


def test_partial_start_failure_stops_created_transport_and_ends_run(tmp_path: Path) -> None:
    async def body() -> None:
        service = _service(tmp_path)

        class PartialTransport:
            process_id = 8123
            _process = None

            def __init__(self) -> None:
                self.stop_calls = 0

            async def stop(self) -> str:
                self.stop_calls += 1
                return "terminated"

        transport = PartialTransport()

        async def partial_start() -> None:
            service.run_id = service.store.start_run(
                codex_binary="partial-start-fixture",
                codex_version="fixture",
                client_name="partial-start-test",
                process_id=transport.process_id,
            )
            service.transport = transport  # type: ignore[assignment]
            raise RuntimeError("partial start failed")

        service.start = partial_start  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="partial start failed"):
            await service.serve(duration_seconds=0.01)

        assert transport.stop_calls == 1
        row = service.store.connection.execute(
            "SELECT ended_at, end_kind FROM observer_runs WHERE run_id = ?",
            (service.run_id,),
        ).fetchone()
        assert row is not None and row[0]
        assert row[1] == "PROTOCOL_INCIDENT"
        service.store.close()

    import asyncio

    asyncio.run(body())


@pytest.mark.parametrize("failure_point", ["initialize", "reconcile_threads"])
def test_ready_hook_is_not_called_when_startup_gate_fails(tmp_path: Path, failure_point: str) -> None:
    async def body() -> None:
        service = _service(tmp_path)
        observed: list[dict[str, object]] = []

        async def fail() -> None:
            raise RuntimeError(f"{failure_point} failed")

        async def fail_reconciliation() -> dict[str, object]:
            raise RuntimeError(f"{failure_point} failed")

        if failure_point == "initialize":
            service.initialize = fail  # type: ignore[method-assign]
        else:
            service.reconcile_threads = fail_reconciliation  # type: ignore[method-assign]

        with pytest.raises(RuntimeError, match="failed"):
            await service.serve(duration_seconds=0.01, ready_hook=observed.append)

        assert observed == []
        service.store.close()

    import asyncio

    asyncio.run(body())
