from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.stop_policy import stop_decision_for_actor
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_root_ignores_em_child_task(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-stop")
    em = register_child_actor(
        store,
        session_id="session-stop",
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
    )
    store.open_actor_workflow(root.actor_context_id, "turn-root", "root", "coordinate")
    em_wf = store.open_actor_workflow(em.actor_context_id, "turn-em", "em", "research")
    store.register_task(em_wf, "scout", "worker", "inspect", True)
    decision = stop_decision_for_actor(store, root.actor_context_id, "turn-1", False)
    assert decision.get("decision") != "block"
    em_decision = stop_decision_for_actor(store, em.actor_context_id, "turn-1", False)
    assert em_decision.get("decision") == "block"


def test_loop_protection_uses_actor_key(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-loop")
    wf = store.open_actor_workflow(root.actor_context_id, "turn-root", "root", "coordinate")
    store.open_obligation(
        wf,
        "USER_DECISION_REQUIRED",
        root.actor_context_id,
        "user",
        "need user",
        "user:1",
    )
    first = stop_decision_for_actor(store, root.actor_context_id, "turn-9", False)
    second = stop_decision_for_actor(store, root.actor_context_id, "turn-9", False)
    assert first.get("decision") == "block"
    assert second.get("loop_prevented") is True
