from pathlib import Path

from tests.codex_supervisor.helpers import record_completed_agent_item
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.command_gateway import CommandGateway
from tools.codex_supervisor.mailbox_store import MailboxStore
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurns


def _ack_text(checkpoint: dict) -> str:
    import json

    payload = {
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
    return "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n" + json.dumps(payload) + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"


def plant_verification_receipt(store: BindingStore, binding_id: str, snapshot, thread_id: str) -> None:
    checkpoint = seed_reanchor(store.bridge.semantic, snapshot.actor_context_id)
    snapshot = store.bridge.snapshot(snapshot.actor_context_id)
    turn_id = f"turn_verify_{binding_id[-8:]}"
    turns = ManagedTurns(store, client=None)  # type: ignore[arg-type]
    # ManagedTurns.prepare does not use the client.
    turns.client = None  # type: ignore[assignment]
    intent_id = turns.prepare(
        binding_id,
        intent_kind=ManagedIntentKind.BOOTSTRAP,
        input_ref="bootstrap",
        checkpoint_id=snapshot.checkpoint_id,
        expected_state_version=snapshot.state_version,
        expected_epoch_id=snapshot.epoch_id,
        expected_epoch_revision=snapshot.epoch_revision,
    )
    store.store.connection.execute(
        """UPDATE managed_turn_intents
        SET app_server_turn_id = ?, submission_state = 'SUBMITTING', version = version + 1
        WHERE turn_intent_id = ?""",
        (turn_id, intent_id),
    )
    store.store.connection.execute(
        """UPDATE managed_turn_intents
        SET submission_state = 'SUBMITTED', version = version + 1
        WHERE turn_intent_id = ?""",
        (intent_id,),
    )
    store.store.connection.commit()
    turns.record_completion(intent_id, "completed")
    seq = record_completed_agent_item(
        store.store,
        thread_id=thread_id,
        turn_id=turn_id,
        text=_ack_text(checkpoint),
        item_id=f"itm_{binding_id[-8:]}",
    )
    CommandGateway(store, store.bridge).ingest_final_item(raw_message_seq=seq)


def activate_binding(store: BindingStore, snapshot, tmp_path: Path, thread_id: str) -> str:
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread_for_tests(binding_id, thread_id)
    store.mark_verification_required(binding_id)
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    plant_verification_receipt(store, binding_id, snapshot, thread_id)
    store.activate(binding_id)
    return binding_id


def seed_active_root_portfolio(tmp_path: Path) -> dict[str, object]:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    root_snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    port_snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    seeded["bindings"] = store
    seeded["mailbox"] = MailboxStore(seeded["supervisor"])
    seeded["root_binding_id"] = activate_binding(store, root_snapshot, tmp_path, "thr_root")
    seeded["portfolio_binding_id"] = activate_binding(store, port_snapshot, tmp_path, "thr_port")
    return seeded
