from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, record_completed_agent_item, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_semantic_mvp.actor_registry import release_actor_context
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.command_gateway import CommandGateway
from tools.codex_supervisor.managed_models import BindingState, ManagedIntentKind
from tools.codex_supervisor.managed_runtime import ManagedRuntime, ManagedRuntimeError
from tools.codex_supervisor.managed_turns import ManagedTurns
from tools.codex_supervisor.provisioning import ManagedProvisioner
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def test_verify_activate_and_reject_wrong_thread_or_released_actor(tmp_path: Path) -> None:
    async def body() -> None:
        seeded = seed_managed_actors(tmp_path)
        checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
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
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        store = BindingStore(seeded["supervisor"], seeded["bridge"])
        provisioner = ManagedProvisioner(store, client)
        snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
        binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
        await provisioner.create_fresh_thread(binding_id)
        provisioner.confirm_global_memory_disabled(binding_id, operator="operator")
        runtime = ManagedRuntime(store, ManagedTurns(store, client), CommandGateway(store, seeded["bridge"]), seeded["bridge"])
        ack = {
            "schema_version": "1.0",
            "packet_kind": "MANAGED_ACTOR_COMMAND",
            "action_kind": "CONTEXT_REANCHOR_ACK",
            "expected": {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "state_version": int(checkpoint["state_version"]),
                "epoch_id": checkpoint.get("epoch_id"),
                "epoch_revision": checkpoint.get("epoch_revision"),
            },
            "payload": {},
        }
        text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(ack) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
        submitted = await runtime.submit_verification(binding_id, snapshot)
        turn_id = str(submitted.get("app_server_turn_id") or "turn_canary")
        binding = store.get(binding_id)
        assert binding is not None and binding.thread_id
        seq = record_completed_agent_item(
            seeded["supervisor"],
            thread_id=binding.thread_id,
            turn_id=turn_id,
            text=text,
        )
        result = runtime.complete_activation(binding_id, raw_message_seq=seq)
        assert result["state"] == BindingState.ACTIVE.value
        gateway = CommandGateway(store, seeded["bridge"])
        with pytest.raises(Exception):
            gateway.ingest_final_item(raw_message_seq=99)
        port = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
        other = provisioner.prepare(port, repo_root=tmp_path, operator="operator")
        store.attach_thread_for_tests(other, "thr_port")
        store.confirm_global_memory_disabled(other, operator="operator")
        store.mark_verification_required(other)
        other_intent = ManagedTurns(store, client).prepare(
            other,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap",
        )
        store.store.connection.execute(
            """UPDATE managed_turn_intents
            SET app_server_turn_id = ?, submission_state = 'SUBMITTING', version = version + 1
            WHERE turn_intent_id = ?""",
            ("turn_port", other_intent),
        )
        store.store.connection.execute(
            "UPDATE managed_turn_intents SET submission_state = 'SUBMITTED', version = version + 1 WHERE turn_intent_id = ?",
            (other_intent,),
        )
        store.store.connection.execute(
            "UPDATE managed_turn_intents SET submission_state = 'OBSERVED', version = version + 1 WHERE turn_intent_id = ?",
            (other_intent,),
        )
        store.store.connection.execute(
            "UPDATE managed_turn_intents SET submission_state = 'COMPLETED', version = version + 1 WHERE turn_intent_id = ?",
            (other_intent,),
        )
        store.store.connection.commit()
        release_actor_context(seeded["semantic"], seeded["portfolio"].actor_context_id)
        other_seq = record_completed_agent_item(
            seeded["supervisor"],
            thread_id="thr_port",
            turn_id="turn_port",
            text="no envelope",
            item_id="itm_port",
        )
        with pytest.raises(ManagedRuntimeError):
            runtime.complete_activation(other, raw_message_seq=other_seq)
        assert store.get(other).binding_state is BindingState.SUSPENDED
        await transport.stop()
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())
