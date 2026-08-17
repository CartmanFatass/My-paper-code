import pytest

from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.models import ContextSourceKind
from tools.codex_context_lifecycle.precedence import assert_authoritative_source
from tools.codex_context_lifecycle.promotion import PromotionError, create_promotion_proposal
from tools.codex_context_lifecycle.rollover import prepare_rollover
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.capsules import render_capsule, build_capsule
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore

ADVISORY = (
    "The user prefers field models.",
    "The direction was released and should remain inactive.",
    "The previous agent considered the task blocked.",
    "Architecture B was historically favored.",
    "The Portfolio should backfill two directions.",
)


@pytest.mark.parametrize("kind", [ContextSourceKind.AUTOMATIC_MEMORY, ContextSourceKind.COMPACTION_SUMMARY])
@pytest.mark.parametrize(
    "operation",
    [
        "open_epoch",
        "revise_epoch",
        "resolve_obligation",
        "create_promotion_proposal",
        "apply_rollover",
        "close_workflow",
        "create_portfolio_decision",
        "change_actor_state",
    ],
)
def test_memory_cannot_mutate(kind, operation) -> None:
    with pytest.raises(PermissionError):
        assert_authoritative_source(kind, operation)


def test_memory_cannot_open_promotion_or_rollover(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="q",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="exit",
    )
    with pytest.raises(PromotionError):
        create_promotion_proposal(
            store,
            actor_context_id=em.actor_context_id,
            epoch_id=epoch["epoch_id"],
            promotion_kind="EPHEMERAL",
            summary=ADVISORY[0],
            rationale=ADVISORY[1],
            source_refs=list(ADVISORY),
            owner_actor_context_id=em.actor_context_id,
            source_kind=ContextSourceKind.AUTOMATIC_MEMORY,
        )
    with pytest.raises(PermissionError):
        prepare_rollover(
            store,
            actor_context_id=em.actor_context_id,
            from_epoch_id=epoch["epoch_id"],
            from_epoch_revision=1,
            next_epoch_kind=EpochKind.DIRECTION_STAGE,
            next_objective="next",
            source_kind="COMPACTION_SUMMARY",
        )


def test_capsule_is_hint_only(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    text = render_capsule(build_capsule(store, em.actor_context_id))
    assert "AUTOMATIC_MEMORY_AUTHORITY=NONE" in text
    assert "COMPACTION_SUMMARY_AUTHORITY=NONE" in text
    assert "CONTEXT PRECEDENCE" in text
    for line in ADVISORY:
        assert line not in text


def test_close_workflow_rejects_memory_source() -> None:
    with pytest.raises(PermissionError):
        assert_authoritative_source(ContextSourceKind.AUTOMATIC_MEMORY, "close_workflow")
