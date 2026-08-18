from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.working_set import actor_may_auto_rehydrate, build_working_set
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.actor_registry import release_actor_context
from tools.codex_semantic_mvp.capsules import build_capsule
from tools.codex_semantic_mvp.epochs import plan_epoch_close, plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.actor_models import SemanticCommitKind
from tools.codex_semantic_mvp.store import SemanticStore


def test_five_epoch_actor_capsule_stays_current(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    last = None
    for index in range(5):
        if last is not None:
            plan_epoch_close(store, epoch_id=last["epoch_id"], reason="advance")
        last = plan_epoch_open(
            store,
            actor_context_id=em.actor_context_id,
            epoch_kind=EpochKind.DIRECTION_STAGE,
            objective=f"epoch-{index}",
            authority_refs=[],
            frozen_invariants=[],
            exit_boundary="next",
        )
        semantic_commit_write(
            store,
            actor_context_id=em.actor_context_id,
            epoch_id=last["epoch_id"],
            commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
            payload={
                "direction_id": "risp",
                "stage_envelope_ref": "docs/envelope.md",
                "current_science_object_ref": "docs/card.md",
                "current_question": f"q{index}",
                "strongest_live_alternative": "alt",
                "claim_ceiling": "toy",
                "next_discriminator": "held-out N",
                "exploration_debt": [],
                "cm_counterpart_actor_context_id": "",
                "root_return_trigger": "milestone",
            },
            source_refs=[],
        )
        workflow_id = store.current_actor_workflow(em.actor_context_id)["workflow_id"]
        for report_n in range(4):
            store.append_event(
                workflow_id,
                "REPORT_AVAILABLE",
                f"rep-{index}-{report_n}",
                {"n": report_n},
                f"REPORT:{index}:{report_n}",
            )
    working = build_working_set(store, em.actor_context_id)
    capsule = build_capsule(store, em.actor_context_id)
    assert working.epoch_id == last["epoch_id"]
    assert capsule["epoch_id"] == last["epoch_id"]
    assert last["epoch_id"] not in working.excluded_object_ids
    assert any(item != last["epoch_id"] for item in working.excluded_object_ids)
    closed = store.connection.execute(
        "SELECT COUNT(*) FROM plan_epochs WHERE actor_context_id = ? AND state = 'CLOSED'",
        (em.actor_context_id,),
    ).fetchone()[0]
    assert closed == 4
    for epoch_id, in store.connection.execute(
        "SELECT epoch_id FROM plan_epochs WHERE actor_context_id = ? AND state = 'CLOSED'",
        (em.actor_context_id,),
    ):
        assert epoch_id in working.excluded_object_ids
        assert epoch_id != capsule["epoch_id"]


def test_released_em_does_not_auto_rehydrate(store: SemanticStore) -> None:
    root, em, _cm = make_pair(store)
    plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="stage",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="done",
    )
    release_actor_context(store, em.actor_context_id)
    assert actor_may_auto_rehydrate(store, em.actor_context_id) is False
    assert root.direction_id is None
    history = store.connection.execute(
        "SELECT state FROM actor_contexts WHERE actor_context_id = ?",
        (em.actor_context_id,),
    ).fetchone()[0]
    assert history == "RELEASED"
    working = build_working_set(store, em.actor_context_id)
    assert working.actor_context_id == em.actor_context_id
    assert working.epoch_id is None
    assert working.semantic_commit_id is None
    assert working.checkpoint_id is None
    assert working.canonical_refs == ()
