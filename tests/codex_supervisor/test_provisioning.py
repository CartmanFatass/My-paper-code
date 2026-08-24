from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.managed_models import BindingState, HistoryTrust, ThreadOrigin
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.protocol import decode_jsonl_line
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def test_fresh_thread_is_created_once(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
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
        original = transport.send_bytes

        async def capture(wire: bytes) -> bytes:
            message = decode_jsonl_line(wire, config.max_jsonl_line_bytes)
            sent.append(str(message.get("method") or ""))
            return await original(wire)

        transport.send_bytes = capture  # type: ignore[method-assign]
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        thread_id = await provisioner.create_fresh_thread(binding_id)
        assert thread_id == "thr_canary"
        assert store.get(binding_id).binding_state is BindingState.THREAD_CREATED
        assert sent.count("thread/start") == 1
        assert "thread/resume" not in sent
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_thread_start_overload_is_not_retried(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "mutation_overload"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        sent: list[str] = []
        original = transport.send_bytes

        async def capture(wire: bytes) -> bytes:
            message = decode_jsonl_line(wire, config.max_jsonl_line_bytes)
            sent.append(str(message.get("method") or ""))
            return await original(wire)

        transport.send_bytes = capture  # type: ignore[method-assign]
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        with pytest.raises(ProvisioningError, match="PROVIDER_REJECTED"):
            await provisioner.create_fresh_thread(binding_id)
        assert store.get(binding_id).binding_state is BindingState.PREPARED
        assert sent.count("thread/start") == 1
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())
