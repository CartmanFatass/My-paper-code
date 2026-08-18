from pathlib import Path

import pytest

from tests.codex_context_lifecycle.helpers import make_pair, open_em_epoch
from tools.codex_context_lifecycle.authority import AuthorityError
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import (
    PromotionError,
    create_promotion_proposal,
    mark_promotion_applied,
    resolve_promotion_proposal,
)
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore


def test_promotion_apply_requires_exact_proposed_target(
    store: SemanticStore, repo_root: Path
) -> None:
    _root, em, _cm = make_pair(store, direction_id="variable_n_fleet_churn")
    epoch = open_em_epoch(store, em)
    target = (
        "docs/research/candidates/variable_n_fleet_churn/"
        "VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md"
    )
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
        summary="card",
        rationale="exists",
        source_refs=[],
        owner_actor_context_id=em.actor_context_id,
        target_ref=target,
    )
    resolve_promotion_proposal(
        store,
        promotion_id=proposed["promotion_id"],
        next_state=PromotionState.OWNER_ACCEPTED,
        disposition={"owner": "em"},
        requester_actor_context_id=em.actor_context_id,
    )
    with pytest.raises(PromotionError, match="must equal"):
        mark_promotion_applied(
            store,
            promotion_id=proposed["promotion_id"],
            canonical_ref="docs/project/PROJECT_MAP.md",
            repo_root=repo_root,
            requester_actor_context_id=em.actor_context_id,
            writer_actor_context_id=em.actor_context_id,
        )


def test_promotion_apply_requires_existing_file_and_fixed_repo_root(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store, direction_id="variable_n_fleet_churn")
    epoch = open_em_epoch(store, em)
    proposed = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
        summary="missing",
        rationale="no file",
        source_refs=[],
        owner_actor_context_id=em.actor_context_id,
        target_ref="docs/research/candidates/variable_n_fleet_churn/does-not-exist.md",
    )
    resolve_promotion_proposal(
        store,
        promotion_id=proposed["promotion_id"],
        next_state=PromotionState.OWNER_ACCEPTED,
        disposition={"owner": "em"},
        requester_actor_context_id=em.actor_context_id,
    )
    with pytest.raises(PromotionError, match="does not exist"):
        mark_promotion_applied(
            store,
            promotion_id=proposed["promotion_id"],
            canonical_ref="docs/research/candidates/variable_n_fleet_churn/does-not-exist.md",
            requester_actor_context_id=em.actor_context_id,
            writer_actor_context_id=em.actor_context_id,
        )


@pytest.mark.parametrize(
    "target",
    [
        "docs/research/candidates/x/../../../AGENTS.md",
        "docs/project/current-work/../../AGENTS.md",
        ".agents/skills/x/../../../AGENTS.md",
    ],
)
def test_promotion_rejects_parent_traversal(store: SemanticStore, target: str) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    with pytest.raises(PromotionError, match="parent traversal"):
        create_promotion_proposal(
            store,
            actor_context_id=em.actor_context_id,
            epoch_id=epoch["epoch_id"],
            promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
            summary="escape",
            rationale="bad",
            source_refs=[],
            owner_actor_context_id=em.actor_context_id,
            target_ref=target,
        )


def test_em_cannot_promote_another_direction_artifact(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store, direction_id="a")
    epoch = open_em_epoch(store, em)
    with pytest.raises(PromotionError, match="direction"):
        create_promotion_proposal(
            store,
            actor_context_id=em.actor_context_id,
            epoch_id=epoch["epoch_id"],
            promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
            summary="other",
            rationale="leak",
            source_refs=[],
            owner_actor_context_id=em.actor_context_id,
            target_ref="docs/research/candidates/b/card.md",
        )


def test_cm_technical_promotion_is_assignment_scoped(store: SemanticStore) -> None:
    _root, em, cm = make_pair(store, direction_id="a")
    epoch = plan_epoch_open(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_kind=EpochKind.TECHNICAL_CLOSURE,
        objective="impl",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="done",
    )
    for target in (
        "AGENTS.md",
        ".agents/roles/ROOT.md",
        "docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md",
        "docs/research/candidates/b/card.md",
    ):
        with pytest.raises(PromotionError):
            create_promotion_proposal(
                store,
                actor_context_id=cm.actor_context_id,
                epoch_id=epoch["epoch_id"],
                promotion_kind=PromotionKind.TECHNICAL_ARTIFACT,
                summary="bad",
                rationale="scope",
                source_refs=[],
                owner_actor_context_id=cm.actor_context_id,
                target_ref=target,
            )
    del em


def test_procedure_promotion_requires_registered_procedure_owner(store: SemanticStore) -> None:
    _root, em, cm = make_pair(store)
    epoch = plan_epoch_open(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_kind=EpochKind.TECHNICAL_CLOSURE,
        objective="impl",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="done",
    )
    with pytest.raises(PromotionError, match="procedure owner"):
        create_promotion_proposal(
            store,
            actor_context_id=cm.actor_context_id,
            epoch_id=epoch["epoch_id"],
            promotion_kind=PromotionKind.PROCEDURE,
            summary="skill",
            rationale="wrong owner",
            source_refs=[],
            owner_actor_context_id=cm.actor_context_id,
            target_ref=".agents/skills/hmasd-independent-research-exploration/SKILL.md",
        )
    del em


def test_wrong_requester_cannot_resolve_foreign_promotion(store: SemanticStore) -> None:
    _root, em, cm = make_pair(store)
    epoch = open_em_epoch(store, em)
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
    with pytest.raises(AuthorityError):
        resolve_promotion_proposal(
            store,
            promotion_id=proposed["promotion_id"],
            next_state=PromotionState.OWNER_ACCEPTED,
            disposition={"owner": "cm"},
            requester_actor_context_id=cm.actor_context_id,
        )
