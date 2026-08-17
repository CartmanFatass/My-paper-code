import pytest

from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import create_promotion_proposal, resolve_promotion_proposal
from tools.codex_context_lifecycle.rollover import (
    RolloverError,
    apply_rollover,
    confirm_rollover,
    prepare_rollover,
)
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_current, plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore


def test_rollover_carries_em_frontier_and_forgets_ephemeral(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="old question",
        authority_refs=[],
        frozen_invariants=["claim ceiling"],
        exit_boundary="rollover",
    )
    create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="scratch",
        rationale="local note",
        source_refs=["raw"],
        owner_actor_context_id=em.actor_context_id,
    )
    rejected = store.connection.execute(
        "SELECT promotion_id FROM promotion_proposals WHERE epoch_id = ?",
        (epoch["epoch_id"],),
    ).fetchone()[0]
    resolve_promotion_proposal(
        store,
        promotion_id=rejected,
        next_state=PromotionState.OWNER_REJECTED,
        disposition={"owner": "em"},
    )
    prepared = prepare_rollover(
        store,
        actor_context_id=em.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=EpochKind.DIRECTION_STAGE,
        next_objective="Define the next authorized single-axis discriminator.",
        carry_frontier={
            "strongest_live_alternative": "fixed-N baseline",
            "claim_ceiling": "toy only",
            "next_discriminator": "held-out N",
            "exploration_debt": ["bridge map"],
        },
        forgotten_refs=["scratch-note"],
    )
    confirm_rollover(store, prepared["rollover_id"])
    applied = apply_rollover(store, rollover_id=prepared["rollover_id"])
    current = plan_epoch_current(store, em.actor_context_id)
    assert current["epoch_id"] != epoch["epoch_id"]
    assert current["objective"] == "Define the next authorized single-axis discriminator."
    assert applied["forgotten_refs"] == ["scratch-note"]
    mark = store.connection.execute(
        "SELECT retention_class FROM context_retention_marks WHERE object_id = 'scratch-note'"
    ).fetchone()
    assert mark[0] == "AUDIT_ONLY"


def test_rollover_rejects_cross_role_fields_and_lost_obligations(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="old",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="exit",
    )
    store.open_obligation(
        store.current_actor_workflow(em.actor_context_id)["workflow_id"],
        "REPORT_INTAKE_REQUIRED",
        em.actor_context_id,
        "rep-1",
        "intake",
        "rep-1",
        touch=False,
    )
    with pytest.raises(RolloverError, match="cross-role"):
        prepare_rollover(
            store,
            actor_context_id=em.actor_context_id,
            from_epoch_id=epoch["epoch_id"],
            from_epoch_revision=1,
            next_epoch_kind=EpochKind.DIRECTION_STAGE,
            next_objective="next",
            carry_frontier={"pending_l1_milestones": ["x"]},
        )
    prepared = prepare_rollover(
        store,
        actor_context_id=em.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=1,
        next_epoch_kind=EpochKind.DIRECTION_STAGE,
        next_objective="next",
        carry_frontier={"claim_ceiling": "toy"},
    )
    confirm_rollover(store, prepared["rollover_id"])
    with pytest.raises(RolloverError, match="open obligations"):
        apply_rollover(store, rollover_id=prepared["rollover_id"])
