from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.epochs import plan_epoch_open
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


def em_frontier_payload(**overrides):
    payload = {
        "direction_id": "risp",
        "stage_envelope_ref": "docs/envelope.md",
        "current_science_object_ref": "docs/card.md",
        "current_question": "q",
        "strongest_live_alternative": "alt",
        "claim_ceiling": "toy only",
        "next_discriminator": "held-out N",
        "exploration_debt": ["bridge"],
        "cm_counterpart_actor_context_id": "",
        "root_return_trigger": "milestone",
    }
    payload.update(overrides)
    return payload


def open_em_epoch(store: SemanticStore, em, objective: str = "stage"):
    return plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective=objective,
        authority_refs=["AGENTS.md"],
        frozen_invariants=["claim ceiling"],
        exit_boundary="rollover",
    )
