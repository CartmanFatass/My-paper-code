from pathlib import Path

from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import (
    create_promotion_proposal,
    mark_promotion_applied,
    resolve_promotion_proposal,
)
from tools.codex_context_lifecycle.retention import apply_gc_marks
from tools.codex_context_lifecycle.source_registry import load_registry
from tools.codex_context_lifecycle.working_set import build_working_set
from tools.codex_context_lifecycle.rollover import apply_rollover, confirm_rollover, prepare_rollover
from tools.codex_semantic_mvp.actor_models import EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.checkpoints import materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


def test_end_to_end_em_lifecycle(store: SemanticStore, repo_root: Path) -> None:
    _root, em, _cm = make_pair(store)
    registry = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
    epoch = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="define discriminator",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["toy claim ceiling"],
        exit_boundary="owner rollover",
        procedure_refs=("em-procedure",),
        registry=registry,
    )
    semantic_commit_write(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
        payload={
            "direction_id": "risp",
            "stage_envelope_ref": "docs/envelope.md",
            "current_science_object_ref": "docs/card.md",
            "current_question": "does carry survive?",
            "strongest_live_alternative": "fixed-N baseline",
            "claim_ceiling": "toy only",
            "next_discriminator": "held-out N",
            "exploration_debt": ["bridge"],
            "cm_counterpart_actor_context_id": "",
            "root_return_trigger": "milestone",
        },
        source_refs=["docs/card.md"],
    )
    first_checkpoint = materialize_checkpoint(store, em.actor_context_id)
    adr = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="scratch",
        rationale="do not promote",
        source_refs=["raw"],
        owner_actor_context_id=em.actor_context_id,
    )
    resolve_promotion_proposal(
        store,
        promotion_id=adr["promotion_id"],
        next_state=PromotionState.OWNER_REJECTED,
        disposition={"owner": "em"},
    )
    science = create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.SCIENTIFIC_ARTIFACT,
        summary="keep science card",
        rationale="existing EM artifact",
        source_refs=["docs/research/candidates/variable_n_fleet_churn/"],
        owner_actor_context_id=em.actor_context_id,
        target_ref="docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
    )
    resolve_promotion_proposal(
        store,
        promotion_id=science["promotion_id"],
        next_state=PromotionState.OWNER_ACCEPTED,
        disposition={"owner": "em"},
    )
    applied = mark_promotion_applied(
        store,
        promotion_id=science["promotion_id"],
        canonical_ref="docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
        repo_root=repo_root,
    )
    prepared = prepare_rollover(
        store,
        actor_context_id=em.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=EpochKind.DIRECTION_STAGE,
        next_objective="next discriminator",
        carry_frontier={
            "strongest_live_alternative": "fixed-N baseline",
            "claim_ceiling": "toy only",
            "next_discriminator": "held-out N",
            "exploration_debt": ["bridge"],
        },
        forgotten_refs=["scratch"],
    )
    confirm_rollover(store, prepared["rollover_id"])
    apply_rollover(store, rollover_id=prepared["rollover_id"])
    apply_gc_marks(store, actor_context_id=em.actor_context_id)
    working = build_working_set(store, em.actor_context_id)
    capsule = build_capsule(store, em.actor_context_id)
    text = render_capsule(capsule)
    assert working.epoch_id != epoch["epoch_id"]
    assert epoch["epoch_id"] not in {working.epoch_id}
    assert "scratch" not in text
    assert applied["canonical_ref"].endswith(".md")
    assert store.connection.execute(
        "SELECT COUNT(*) FROM plan_epochs WHERE epoch_id = ?",
        (epoch["epoch_id"],),
    ).fetchone()[0] == 1
    assert first_checkpoint["checkpoint_id"]
    assert "AUTOMATIC_MEMORY_AUTHORITY=NONE" in text
    assert capsule["epoch_id"] == working.epoch_id
