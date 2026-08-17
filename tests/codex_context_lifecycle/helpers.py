from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.store import SemanticStore


def make_pair(store: SemanticStore, session_id: str = "session-root", direction_id: str = "risp"):
    root = register_session_root(store, session_id=session_id)
    em = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.EM,
        scope_key=f"direction:{direction_id}:em",
        direction_id=direction_id,
        parent_actor_context_id=root.actor_context_id,
        canonical_path=f"/root/em_{direction_id}",
    )
    cm = register_child_actor(
        store,
        session_id=session_id,
        actor_kind=ActorKind.CM,
        scope_key=f"direction:{direction_id}:cm",
        direction_id=direction_id,
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
        canonical_path=f"/root/cm_{direction_id}",
    )
    store.open_actor_workflow(em.actor_context_id, "turn-em", "em", "em work")
    store.open_actor_workflow(cm.actor_context_id, "turn-cm", "cm", "cm work")
    store.open_actor_workflow(root.actor_context_id, "turn-root", "root", "root work")
    return root, em, cm
