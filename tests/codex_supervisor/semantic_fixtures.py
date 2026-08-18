from pathlib import Path

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import (
    DEFAULT_PORTFOLIO_SESSION_ID,
    register_child_actor,
    register_session_root,
    release_actor_context,
)
from tools.codex_semantic_mvp.checkpoints import ensure_reanchor_obligation, materialize_checkpoint
from tools.codex_semantic_mvp.store import SemanticStore
from tools.codex_supervisor.semantic_bridge import SemanticBridge
from tools.codex_supervisor.store import ObserverStore


def open_semantic(tmp_path: Path) -> SemanticStore:
    return SemanticStore(tmp_path / "semantic.sqlite3").initialize()


def seed_managed_actors(tmp_path: Path) -> dict[str, object]:
    semantic = open_semantic(tmp_path)
    root = register_session_root(semantic, session_id="session-root")
    semantic.open_actor_workflow(root.actor_context_id, "turn-root", "root", "coordinate")
    portfolio = register_session_root(semantic, session_id=DEFAULT_PORTFOLIO_SESSION_ID)
    semantic.open_actor_workflow(portfolio.actor_context_id, "turn-port", "portfolio", "review")
    em = register_child_actor(
        semantic,
        session_id="session-root",
        actor_kind=ActorKind.EM,
        scope_key="direction:demo",
        direction_id="demo",
        parent_actor_context_id=root.actor_context_id,
    )
    cm = register_child_actor(
        semantic,
        session_id="session-root",
        actor_kind=ActorKind.CM,
        scope_key="direction:demo",
        direction_id="demo",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
    )
    leaf = register_child_actor(
        semantic,
        session_id="session-root",
        actor_kind=ActorKind.LEAF,
        scope_key="direction:demo/leaf",
        direction_id="demo",
        parent_actor_context_id=em.actor_context_id,
    )
    released = register_session_root(semantic, session_id="session-released")
    release_actor_context(semantic, released.actor_context_id)
    supervisor = ObserverStore(tmp_path / "supervisor")
    bridge = SemanticBridge(tmp_path / "semantic.sqlite3", supervisor)
    return {
        "semantic": semantic,
        "supervisor": supervisor,
        "bridge": bridge,
        "root": root,
        "portfolio": portfolio,
        "em": em,
        "cm": cm,
        "leaf": leaf,
        "released": released,
    }


def seed_reanchor(semantic: SemanticStore, actor_context_id: str) -> dict[str, object]:
    checkpoint = materialize_checkpoint(semantic, actor_context_id)
    ensure_reanchor_obligation(
        semantic,
        actor_context_id=actor_context_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
    )
    return checkpoint
