from pathlib import Path

from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.checkpoints import materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


def _cycle(store: SemanticStore, actor_id: str) -> str:
    checkpoint = materialize_checkpoint(store, actor_id)
    return render_capsule(checkpoint["capsule"])


def test_five_cycles_preserve_typed_state(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    root = register_session_root(store, session_id="session-stress")
    em = register_child_actor(
        store,
        session_id="session-stress",
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="dir-a",
        parent_actor_context_id=root.actor_context_id,
    )
    store.open_actor_workflow(em.actor_context_id, "t1", "em", "research")
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="identify mechanism",
        authority_refs=["docs/card.md"],
        frozen_invariants=["claim ceiling"],
        exit_boundary="milestone",
    )
    semantic_commit_write(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
        payload={
            "direction_id": "dir-a",
            "stage_envelope_ref": "docs/env.md",
            "current_science_object_ref": "docs/card.md",
            "current_question": "does it identify?",
            "strongest_live_alternative": "shortcut",
            "claim_ceiling": "toy only",
            "next_discriminator": "held-out N",
            "exploration_debt": ["bridge"],
            "cm_counterpart_actor_context_id": "actor_cm",
            "root_return_trigger": None,
        },
        source_refs=["docs/card.md"],
    )
    first = _cycle(store, em.actor_context_id)
    for _ in range(4):
        later = _cycle(store, em.actor_context_id)
        assert later == first
    assert "shortcut" in first
    assert "held-out N" in first
    assert "BLOCKED" not in first
    assert "portfolio priority" not in first.lower()
    store.close()


def test_lexical_perturbation_does_not_change_capsule(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    actor = register_session_root(store, session_id="session-lex")
    store.open_actor_workflow(actor.actor_context_id, "t1", "root", "coordinate")
    baseline = render_capsule(build_capsule(store, actor.actor_context_id))
    for word in ("BLOCKED", "FAILED", "RELEASED", "PAUSE", "No further action"):
        store.append_event(None, "PROSE", None, {"last_assistant_message": word}, f"prose:{word}")
        assert render_capsule(build_capsule(store, actor.actor_context_id)) == baseline
    store.close()
