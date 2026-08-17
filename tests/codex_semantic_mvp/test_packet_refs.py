from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.packet_refs import (
    packet_acknowledge,
    packet_mark_applied,
    packet_mark_delivery,
    packet_mark_intaken,
    packet_register,
)
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_delivery_ack_intake_applied_are_distinct(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-pkt")
    em = register_child_actor(
        store,
        session_id="session-pkt",
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
    )
    cm = register_child_actor(
        store,
        session_id="session-pkt",
        actor_kind=ActorKind.CM,
        scope_key="direction:a:cm",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
    )
    store.open_actor_workflow(cm.actor_context_id, "turn-1", "cm", "implement")
    packet = packet_register(
        store,
        packet_kind="EM_TO_CM_SCIENCE_CARD",
        source_actor_context_id=em.actor_context_id,
        target_actor_context_id=cm.actor_context_id,
        payload_ref="docs/card.md",
        direction_id="a",
    )
    assert packet["delivery_state"] == "PREPARED"
    assert packet["intake_state"] == "NOT_INTAKEN"
    delivered = packet_mark_delivery(store, packet["packet_id"], "DELIVERED_VISIBLE_TARGET")
    acked = packet_acknowledge(store, packet["packet_id"])
    intaken = packet_mark_intaken(store, packet["packet_id"])
    applied = packet_mark_applied(store, packet["packet_id"], decision_ref="accepted")
    assert delivered["delivery_state"] == "DELIVERED_VISIBLE_TARGET"
    assert acked["delivery_state"] == "ACKNOWLEDGED"
    assert intaken["intake_state"] == "INTAKEN"
    assert applied["intake_state"] == "APPLIED"
    assert delivered["delivery_state"] != acked["delivery_state"] or intaken["intake_state"] != "ACKNOWLEDGED"
    assert acked["delivery_state"] != "INTAKEN"
    assert intaken["intake_state"] != "APPLIED"
    obligation = store.connection.execute(
        "SELECT kind, owner_actor_context_id FROM obligations WHERE subject = ?",
        (packet["packet_id"],),
    ).fetchone()
    assert obligation[0] == "PACKET_INTAKE_REQUIRED"
    assert obligation[1] == cm.actor_context_id
