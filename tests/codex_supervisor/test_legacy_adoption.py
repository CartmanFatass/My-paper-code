from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.managed_context import build_bootstrap_text
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.protocol import decode_jsonl_line
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def test_adopt_requires_flags_and_rejects_active(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok", "FAKE_THREAD_STATUS": "active"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        with pytest.raises(ProvisioningError, match="history flags"):
            await provisioner.adopt_existing_thread(
                snapshot,
                thread_id="thr_old",
                repo_root=tmp_path,
                operator="operator",
                allow_existing_history=False,
                confirm_history_nonauthoritative=True,
            )
        with pytest.raises(ProvisioningError, match="in-progress"):
            await provisioner.adopt_existing_thread(
                snapshot,
                thread_id="thr_old",
                repo_root=tmp_path,
                operator="operator",
                allow_existing_history=True,
                confirm_history_nonauthoritative=True,
            )
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_adopt_idle_thread_is_legacy(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok", "FAKE_THREAD_STATUS": "idle"},
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
        binding_id = await provisioner.adopt_existing_thread(
            snapshot,
            thread_id="thr_old",
            repo_root=tmp_path,
            operator="operator",
            allow_existing_history=True,
            confirm_history_nonauthoritative=True,
        )
        binding = store.get(binding_id)
        assert binding.thread_origin is ThreadOrigin.ADOPTED_EXISTING
        assert binding.history_trust is HistoryTrust.LEGACY_UNTRUSTED_HISTORY
        assert binding.thread_id == "thr_old"
        assert sent.count("thread/resume") == 1
        assert "LEGACY_HISTORY_AUTHORITY=NONE" in build_bootstrap_text(snapshot, history_trust=binding.history_trust)
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())
