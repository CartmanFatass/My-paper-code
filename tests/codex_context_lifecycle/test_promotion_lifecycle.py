from pathlib import Path

import pytest

from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import (
    PromotionError,
    create_promotion_proposal,
    mark_promotion_applied,
    promotion_proposals_for_epoch,
    resolve_promotion_proposal,
)
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore


def _em_epoch(store: SemanticStore, em) -> dict:
    return plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="define next discriminator",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="owner rollover",
    )


def test_valid_promotion_lifecycle(store: SemanticStore, repo_root: Path) -> None:
    _root, em, _cm = make_pair(store, direction_id="variable_n_fleet_churn")
    epoch = _em_epoch(store, em)
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
        summary="keep science card",
        rationale="owner artifact already exists",
        source_refs=["docs/research/candidates/variable_n_fleet_churn/"],
        owner_actor_context_id=em.actor_context_id,
        target_ref="docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
    )
    assert proposed["state"].value == PromotionState.PROPOSED.value
    obligations = store.connection.execute(
        "SELECT kind FROM obligations WHERE subject = ?",
        (proposed["promotion_id"],),
    ).fetchone()
    assert obligations[0] == "PROMOTION_REVIEW_REQUIRED"
    accepted = resolve_promotion_proposal(
        store,
        promotion_id=proposed["promotion_id"],
        next_state=PromotionState.OWNER_ACCEPTED,
        disposition={"owner": "em", "note": "accepted"},
        requester_actor_context_id=em.actor_context_id,
    )
    applied = mark_promotion_applied(
        store,
        promotion_id=accepted["promotion_id"],
        canonical_ref="docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
        repo_root=repo_root,
        requester_actor_context_id=em.actor_context_id,
        writer_actor_context_id=em.actor_context_id,
    )
    assert applied["state"] is PromotionState.APPLIED


def test_reject_and_invalid_transitions(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = _em_epoch(store, em)
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="note",
        rationale="keep local",
        source_refs=["conversation"],
        owner_actor_context_id=em.actor_context_id,
    )
    rejected = resolve_promotion_proposal(
        store,
        promotion_id=proposed["promotion_id"],
        next_state=PromotionState.OWNER_REJECTED,
        disposition={"owner": "em"},
        requester_actor_context_id=em.actor_context_id,
    )
    assert rejected["state"] is PromotionState.OWNER_REJECTED
    with pytest.raises(PromotionError):
        mark_promotion_applied(
            store,
            promotion_id=proposed["promotion_id"],
            canonical_ref="docs/research/candidates/x.md",
        )
    with pytest.raises(PromotionError):
        resolve_promotion_proposal(
            store,
            promotion_id=proposed["promotion_id"],
            next_state=PromotionState.PROPOSED,
            requester_actor_context_id=em.actor_context_id,
        )


def test_cannot_skip_to_applied(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = _em_epoch(store, em)
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="note",
        rationale="local",
        source_refs=[],
        owner_actor_context_id=em.actor_context_id,
    )
    with pytest.raises(PromotionError, match="invalid promotion transition"):
        resolve_promotion_proposal(
            store,
            promotion_id=proposed["promotion_id"],
            next_state=PromotionState.APPLIED,
            requester_actor_context_id=em.actor_context_id,
        )
    listed = promotion_proposals_for_epoch(store, epoch["epoch_id"])
    assert len(listed) == 1
