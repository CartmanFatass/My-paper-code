import sqlite3
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind, ActorState
from tools.codex_semantic_mvp.actor_registry import (
    _insert_actor,
    bind_agent_identity,
    link_counterparts,
    reconcile_session_root_actor,
    register_child_actor,
    register_session_root,
    release_actor_context,
    resolve_actor_context,
)
from tools.codex_semantic_mvp.store import SemanticStore


PORTFOLIO_SESSION = "01a03351-e8ef-7620-b2ab-b77b9512f499"


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_portfolio_session_maps_to_portfolio(store: SemanticStore) -> None:
    actor = register_session_root(store, session_id=PORTFOLIO_SESSION)
    assert actor.actor_kind == ActorKind.PORTFOLIO
    assert actor.scope_key == f"session:{PORTFOLIO_SESSION}"


def test_unknown_root_session_maps_to_operational_root(store: SemanticStore) -> None:
    actor = register_session_root(store, session_id="session-unknown-root")
    assert actor.actor_kind == ActorKind.OPERATIONAL_ROOT
    assert actor.identity_source == "SESSION_ROOT_MAPPING"


def test_explicit_child_registration_maps_em_and_cm(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-root")
    em = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.EM,
        scope_key="direction:risp:em",
        direction_id="renewal_indexed_score_plasticity",
        parent_actor_context_id=root.actor_context_id,
        canonical_path="/root/em_risp",
    )
    cm = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.CM,
        scope_key="direction:risp:cm",
        direction_id="renewal_indexed_score_plasticity",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
        canonical_path="/root/cm_risp",
    )
    assert em.actor_kind == ActorKind.EM
    assert cm.actor_kind == ActorKind.CM
    assert cm.counterpart_actor_context_id == em.actor_context_id
    refreshed_em = resolve_actor_context(
        store, session_id="session-root", canonical_path="/root/em_risp"
    )
    assert refreshed_em is not None
    assert refreshed_em.counterpart_actor_context_id == cm.actor_context_id


def test_same_session_may_hold_root_and_two_pairs(store: SemanticStore) -> None:
    session_id = "session-multi"
    root = register_session_root(store, session_id=session_id)
    em_a = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="dir-a",
        parent_actor_context_id=root.actor_context_id,
    )
    cm_a = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.CM,
        scope_key="direction:a:cm",
        direction_id="dir-a",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em_a.actor_context_id,
    )
    em_b = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.EM,
        scope_key="direction:b:em",
        direction_id="dir-b",
        parent_actor_context_id=root.actor_context_id,
    )
    cm_b = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.CM,
        scope_key="direction:b:cm",
        direction_id="dir-b",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em_b.actor_context_id,
    )
    ids = {
        root.actor_context_id,
        em_a.actor_context_id,
        cm_a.actor_context_id,
        em_b.actor_context_id,
        cm_b.actor_context_id,
    }
    assert len(ids) == 5


def test_duplicate_session_agent_binding_fails(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-bind")
    first = register_child_actor(
        store,
        session_id="session-bind",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:scout",
        direction_id=None,
        parent_actor_context_id=root.actor_context_id,
    )
    second = register_child_actor(
        store,
        session_id="session-bind",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:other",
        direction_id=None,
        parent_actor_context_id=root.actor_context_id,
    )
    bind_agent_identity(store, actor_context_id=first.actor_context_id, agent_id="agent-1")
    with pytest.raises(sqlite3.IntegrityError):
        bind_agent_identity(store, actor_context_id=second.actor_context_id, agent_id="agent-1")


def test_counterpart_links_are_symmetric_only_when_explicitly_set(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-link")
    em = register_child_actor(
        store,
        session_id="session-link",
        actor_kind=ActorKind.EM,
        scope_key="direction:x:em",
        direction_id="x",
        parent_actor_context_id=root.actor_context_id,
    )
    cm = register_child_actor(
        store,
        session_id="session-link",
        actor_kind=ActorKind.CM,
        scope_key="direction:x:cm",
        direction_id="x",
        parent_actor_context_id=root.actor_context_id,
    )
    assert em.counterpart_actor_context_id is None
    assert cm.counterpart_actor_context_id is None
    link_counterparts(store, em.actor_context_id, cm.actor_context_id)
    em_after = resolve_actor_context(store, session_id="session-link", canonical_path="")
    em_row = store.connection.execute(
        "SELECT counterpart_actor_context_id FROM actor_contexts WHERE actor_context_id = ?",
        (em.actor_context_id,),
    ).fetchone()
    cm_row = store.connection.execute(
        "SELECT counterpart_actor_context_id FROM actor_contexts WHERE actor_context_id = ?",
        (cm.actor_context_id,),
    ).fetchone()
    assert em_row[0] == cm.actor_context_id
    assert cm_row[0] == em.actor_context_id
    assert em_after is not None
    assert em_after.actor_kind == ActorKind.OPERATIONAL_ROOT


def test_session_id_alone_never_identifies_em_or_cm(store: SemanticStore) -> None:
    register_session_root(store, session_id="session-plain")
    resolved = resolve_actor_context(store, session_id="session-plain")
    assert resolved is not None
    assert resolved.actor_kind == ActorKind.OPERATIONAL_ROOT


def test_releasing_actor_does_not_change_kind(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-release")
    em = register_child_actor(
        store,
        session_id="session-release",
        actor_kind=ActorKind.EM,
        scope_key="direction:y:em",
        direction_id="y",
        parent_actor_context_id=root.actor_context_id,
    )
    released = release_actor_context(store, em.actor_context_id)
    assert released.state == ActorState.RELEASED
    assert released.actor_kind == ActorKind.EM
    assert released.direction_id == "y"


def test_session_root_cutover_reconciles_the_existing_actor_only(store: SemanticStore) -> None:
    actor_id = "actor-cutover"
    session_id = PORTFOLIO_SESSION
    _insert_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.OPERATIONAL_ROOT,
        scope_key=f"session:{session_id}",
        identity_source="TEST_PRECUTOVER",
        actor_context_id=actor_id,
    )
    transitioned = reconcile_session_root_actor(
        store,
        actor_context_id=actor_id,
        session_id=session_id,
        cutover_evidence_ref="docs/session/PORTFOLIO_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260824.md",
    )
    assert transitioned.actor_context_id == actor_id
    assert transitioned.actor_kind is ActorKind.PORTFOLIO
    assert transitioned.session_id == session_id
    assert transitioned.scope_key == f"session:{session_id}"
    assert transitioned.state is ActorState.ACTIVE
    assert "PORTFOLIO_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260824" in transitioned.identity_source
