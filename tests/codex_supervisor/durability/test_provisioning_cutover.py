from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.managed_models import BindingState
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def _provisioner(tmp_path: Path, mode: str = "handshake_ok"):
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    config = make_observer_config(tmp_path)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        tmp_path,
        tmp_path / "err.log",
        extra_env={"FAKE_APP_SERVER_MODE": mode},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )
    client = AppServerClient(transport, config)
    return ManagedProvisioner(store, client), store, transport, seeded


def test_thread_start_effect_confirm_and_attach_are_one_tx(tmp_path: Path) -> None:
    async def body() -> None:
        provisioner, store, transport, seeded = _provisioner(tmp_path)
        await transport.start()
        await provisioner.client.initialize()
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        thread_id = await provisioner.create_fresh_thread(binding_id)
        binding = store.get(binding_id)
        assert binding is not None
        assert binding.thread_id == thread_id
        assert binding.binding_state is BindingState.THREAD_CREATED
        journal = EffectJournal(store.store.connection)
        effect = journal.get_by_key("thread/start", f"thread/start:{binding_id}")
        assert effect is not None
        assert effect.state == EffectState.EFFECT_CONFIRMED.value
        assert store.store.connection.execute(
            "SELECT COUNT(*) FROM control_transitions WHERE aggregate_id = ?",
            (binding_id,),
        ).fetchone()[0] >= 1
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_unresolved_write_started_prevents_second_thread_start(tmp_path: Path) -> None:
    async def body() -> None:
        provisioner, store, transport, seeded = _provisioner(tmp_path)
        await transport.start()
        await provisioner.client.initialize()
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        journal = EffectJournal(store.store.connection)
        journal.prepare_effect(
            owner_kind="THREAD_PROVISION",
            owner_id=binding_id,
            binding_id=binding_id,
            method="thread/start",
            client_key=f"thread/start:{binding_id}",
            request={"cwd": str(tmp_path)},
        )
        journal._claim_write(
            journal.get_by_key("thread/start", f"thread/start:{binding_id}").effect_id,
            run_id="run1",
            client_request_id="1",
            request_row_id="r1",
            raw_request_seq=1,
        )
        with pytest.raises(ProvisioningError, match="unresolved"):
            await provisioner.create_fresh_thread(binding_id)
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_binding_transition_uses_expected_version(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="op",
        thread_origin=__import__("tools.codex_supervisor.managed_models", fromlist=["ThreadOrigin"]).ThreadOrigin.NEW,
        history_trust=__import__("tools.codex_supervisor.managed_models", fromlist=["HistoryTrust"]).HistoryTrust.FRESH,
    )
    first = store.get(binding_id)
    assert first is not None
    version = store.store.connection.execute(
        "SELECT version FROM managed_actor_bindings WHERE binding_id = ?",
        (binding_id,),
    ).fetchone()[0]
    assert version == 0
    store.attach_thread_for_tests(binding_id, "thr_x")
    after = store.store.connection.execute(
        "SELECT version, binding_state FROM managed_actor_bindings WHERE binding_id = ?",
        (binding_id,),
    ).fetchone()
    assert after[0] == 1
    assert after[1] == "THREAD_CREATED"
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
