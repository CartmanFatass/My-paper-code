import pytest

from tools.codex_context_lifecycle.models import ContextSourceKind, PromotionKind
from tools.codex_context_lifecycle.promotion import (
    PromotionError,
    default_target_system,
    validate_promotion_owner,
)
from tools.codex_semantic_mvp.actor_models import ActorKind


def test_owner_matrix_accepts_valid_pairs() -> None:
    validate_promotion_owner(
        PromotionKind.AUTHORITY_RULE, ActorKind.OPERATIONAL_ROOT, "AGENTS.md",
        ContextSourceKind.USER_AUTHORITY,
    )
    validate_promotion_owner(
        PromotionKind.REPOSITORY_NAVIGATION, ActorKind.CM, "docs/project/PROJECT_MAP.md",
        ContextSourceKind.PLAN_EPOCH,
    )
    validate_promotion_owner(
        PromotionKind.SCIENTIFIC_ARTIFACT,
        ActorKind.EM,
        "docs/research/candidates/vnfc/card.md",
        ContextSourceKind.CANONICAL_OWNER_ARTIFACT,
    )
    validate_promotion_owner(
        PromotionKind.PORTFOLIO_ARTIFACT,
        ActorKind.PORTFOLIO,
        "docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md",
        ContextSourceKind.USER_AUTHORITY,
    )
    validate_promotion_owner(PromotionKind.EPHEMERAL, ActorKind.LEAF, None, ContextSourceKind.PLAN_EPOCH)
    assert default_target_system(PromotionKind.SHARED_ARCHITECTURE_DECISION) == "ADR"


@pytest.mark.parametrize(
    "kind, actor, target, match",
    [
        (PromotionKind.PORTFOLIO_ARTIFACT, ActorKind.CM, "docs/x.md", "portfolio"),
        (PromotionKind.TECHNICAL_ARTIFACT, ActorKind.EM, "docs/x.md", "technical"),
        (PromotionKind.SCIENTIFIC_ARTIFACT, ActorKind.OPERATIONAL_ROOT, "docs/research/candidates/x.md", "science"),
        (PromotionKind.REPOSITORY_NAVIGATION, ActorKind.PORTFOLIO, "docs/project/PROJECT_MAP.md", "PROJECT_MAP"),
        (PromotionKind.SHARED_ARCHITECTURE_DECISION, ActorKind.LEAF, "docs/project/decisions/ADR-0001.md", "leaf"),
    ],
)
def test_owner_matrix_rejects_cross_role(kind, actor, target, match) -> None:
    with pytest.raises(PromotionError, match=match):
        validate_promotion_owner(kind, actor, target, ContextSourceKind.USER_AUTHORITY)


@pytest.mark.parametrize(
    "origin",
    [ContextSourceKind.AUTOMATIC_MEMORY, ContextSourceKind.COMPACTION_SUMMARY],
)
def test_memory_and_summary_cannot_propose(origin) -> None:
    with pytest.raises(PromotionError):
        validate_promotion_owner(
            PromotionKind.EPHEMERAL, ActorKind.EM, None, origin
        )
