import pytest

from tests.codex_context_lifecycle.helpers import em_frontier_payload, make_pair, open_em_epoch
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import create_promotion_proposal
from tools.codex_context_lifecycle.rollover import (
    RolloverError,
    apply_rollover,
    confirm_rollover,
    prepare_rollover,
)
from tools.codex_semantic_mvp.actor_models import EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.capsules import build_capsule
from tools.codex_semantic_mvp.epochs import plan_epoch_current, plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


def _confirm_apply(store, actor, epoch, **prepare_kwargs):
    prepared = prepare_rollover(
        store,
        actor_context_id=actor.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=epoch["epoch_kind"],
        next_objective="Define the next authorized single-axis discriminator.",
        **prepare_kwargs,
    )
    confirm_rollover(
        store, prepared["rollover_id"], requester_actor_context_id=actor.actor_context_id
    )
    return apply_rollover(
        store,
        rollover_id=prepared["rollover_id"],
        requester_actor_context_id=actor.actor_context_id,
    )


def test_rollover_carries_em_frontier_into_new_capsule(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em, "old question")
    semantic_commit_write(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
        payload=em_frontier_payload(),
        source_refs=[],
    )
    _confirm_apply(
        store,
        em,
        epoch,
        carry_frontier={
            "strongest_live_alternative": "fixed-N baseline",
            "claim_ceiling": "toy only",
            "next_discriminator": "held-out N",
            "exploration_debt": ["bridge map"],
            "pending_cm_packet": "pkt-1",
        },
    )
    current = plan_epoch_current(store, em.actor_context_id)
    capsule = build_capsule(store, em.actor_context_id)
    body = capsule["body"]
    assert current["objective"] == "Define the next authorized single-axis discriminator."
    assert current["carry_frontier"]["claim_ceiling"] == "toy only"
    assert body["strongest_live_alternative"] == "fixed-N baseline"
    assert body["claim_ceiling"] == "toy only"
    assert body["next_discriminator"] == "held-out N"
    assert body["exploration_debt"] == ["bridge map"]


def test_rollover_carries_root_portfolio_and_cm_fields_by_role(store: SemanticStore) -> None:
    root, em, cm = make_pair(store)
    root_epoch = plan_epoch_open(
        store,
        actor_context_id=root.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="old-root",
        authority_refs=["AGENTS.md"],
        frozen_invariants=[],
        exit_boundary="rollover",
    )
    applied = _confirm_apply(
        store,
        root,
        root_epoch,
        carry_frontier={"pending_l1_milestones": ["m1"], "pending_portfolio_relay": ["p1"]},
    )
    assert applied["new_epoch"]["carry_frontier"]["pending_l1_milestones"] == ["m1"]
    cm_epoch = plan_epoch_open(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_kind=EpochKind.TECHNICAL_CLOSURE,
        objective="old-cm",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="rollover",
    )
    applied_cm = _confirm_apply(
        store,
        cm,
        cm_epoch,
        carry_frontier={"protected_semantics": ["s1"], "technical_unknowns": ["u1"]},
    )
    assert applied_cm["new_epoch"]["carry_frontier"]["protected_semantics"] == ["s1"]
    del em


def test_carried_promotion_is_bound_to_new_epoch(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="carry me",
        rationale="open",
        source_refs=[],
        owner_actor_context_id=em.actor_context_id,
    )
    applied = _confirm_apply(
        store,
        em,
        epoch,
        promotion_ids=[proposed["promotion_id"]],
        carry_frontier={"claim_ceiling": "toy only"},
    )
    row = store.connection.execute(
        "SELECT epoch_id, state, carried_to_epoch_id FROM promotion_proposals WHERE promotion_id = ?",
        (proposed["promotion_id"],),
    ).fetchone()
    assert row["epoch_id"] == applied["new_epoch"]["epoch_id"]
    assert row["state"] == PromotionState.CARRIED_FORWARD.value
    assert row["carried_to_epoch_id"] == applied["new_epoch"]["epoch_id"]


@pytest.mark.parametrize(
    "point",
    [
        "after_close",
        "after_promotion_carry",
        "after_new_epoch",
        "after_retention_mark",
        "before_final_update",
    ],
)
def test_rollover_apply_is_atomic_at_every_failure_point(store: SemanticStore, point: str) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    prepared = prepare_rollover(
        store,
        actor_context_id=em.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=EpochKind.DIRECTION_STAGE,
        next_objective="next",
        carry_frontier={"claim_ceiling": "toy only"},
    )
    confirm_rollover(
        store, prepared["rollover_id"], requester_actor_context_id=em.actor_context_id
    )
    with pytest.raises(RolloverError, match=point):
        apply_rollover(
            store,
            rollover_id=prepared["rollover_id"],
            requester_actor_context_id=em.actor_context_id,
            fail_after=point,
        )
    current = plan_epoch_current(store, em.actor_context_id)
    assert current is not None
    assert current["epoch_id"] == epoch["epoch_id"]
    assert current["state"] == "OPEN"
    rollover = store.connection.execute(
        "SELECT state FROM epoch_rollovers WHERE rollover_id = ?",
        (prepared["rollover_id"],),
    ).fetchone()
    assert rollover[0] == "OWNER_CONFIRMED"
    opened = store.connection.execute(
        "SELECT COUNT(*) FROM plan_epochs WHERE actor_context_id = ? AND state = 'OPEN'",
        (em.actor_context_id,),
    ).fetchone()[0]
    assert opened == 1
