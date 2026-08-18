from pathlib import Path

from tests.codex_context_lifecycle.helpers import em_frontier_payload, make_pair, open_em_epoch
from tools.codex_context_lifecycle.models import PromotionKind, PromotionState
from tools.codex_context_lifecycle.promotion import create_promotion_proposal
from tools.codex_context_lifecycle.retention import mark_refs_audit_only
from tools.codex_context_lifecycle.rollover import apply_rollover, confirm_rollover, prepare_rollover
from tools.codex_context_lifecycle.working_set import build_working_set
from tools.codex_semantic_mvp.actor_models import EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_session_root
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.checkpoints import current_checkpoint, materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_close, plan_epoch_open
from tools.codex_semantic_mvp.hook_entry import handle_hook
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_current, semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


def test_resume_after_rollover_does_not_inject_closed_epoch_checkpoint(
    store: SemanticStore,
) -> None:
    root, _em, _cm = make_pair(store, session_id="session-root")
    epoch = plan_epoch_open(
        store,
        actor_context_id=root.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="old-root-objective",
        authority_refs=["AGENTS.md"],
        frozen_invariants=[],
        exit_boundary="rollover",
    )
    semantic_commit_write(
        store,
        actor_context_id=root.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
        payload={
            "current_user_goal": "old goal",
            "direction_pairs": [],
            "pending_l1_milestone_ids": [],
            "pending_portfolio_packet_ids": [],
            "lease_refs": [],
            "user_decision_obligation_ids": [],
            "git_obligation_ids": [],
        },
        source_refs=["AGENTS.md"],
    )
    materialize_checkpoint(store, root.actor_context_id)
    prepared = prepare_rollover(
        store,
        actor_context_id=root.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        next_objective="new-root-objective",
        carry_frontier={"pending_l1_milestones": []},
    )
    confirm_rollover(
        store, prepared["rollover_id"], requester_actor_context_id=root.actor_context_id
    )
    applied = apply_rollover(
        store,
        rollover_id=prepared["rollover_id"],
        requester_actor_context_id=root.actor_context_id,
    )
    stale = current_checkpoint(store, root.actor_context_id)
    assert stale is None or stale.get("epoch_id") == applied["new_epoch"]["epoch_id"]
    result = handle_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "session-root",
            "turn_id": "turn-resume",
            "source": "resume",
        },
        "active",
        store,
    )
    text = str(result.get("additionalContext") or "")
    assert "new-root-objective" in text
    assert "old-root-objective" not in text


def test_promotion_mutation_invalidates_checkpoint(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    first = materialize_checkpoint(store, em.actor_context_id)
    create_promotion_proposal(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        promotion_kind=PromotionKind.EPHEMERAL,
        summary="note",
        rationale="local",
        source_refs=[],
        owner_actor_context_id=em.actor_context_id,
    )
    assert current_checkpoint(store, em.actor_context_id) is None
    second = materialize_checkpoint(store, em.actor_context_id)
    assert second["reused"] is False
    assert second["checkpoint_id"] != first["checkpoint_id"]


def test_prepared_rollover_and_open_promotion_are_visible_in_capsule(
    store: SemanticStore,
) -> None:
    _root, em, _cm = make_pair(store)
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
    prepared = prepare_rollover(
        store,
        actor_context_id=em.actor_context_id,
        from_epoch_id=epoch["epoch_id"],
        from_epoch_revision=epoch["revision"],
        next_epoch_kind=EpochKind.DIRECTION_STAGE,
        next_objective="next",
        promotion_ids=[proposed["promotion_id"]],
        carry_frontier={"claim_ceiling": "toy only"},
    )
    capsule = build_capsule(store, em.actor_context_id)
    text = render_capsule(capsule)
    assert proposed["promotion_id"] in capsule["promotion_ids"]
    assert capsule["rollover_id"] == prepared["rollover_id"]
    assert proposed["promotion_id"] in text
    assert prepared["rollover_id"] in text


def test_capsule_contains_exact_actor_role_and_required_contract(
    store: SemanticStore,
) -> None:
    root, em, cm = make_pair(store)
    portfolio = register_session_root(
        store, session_id="019ffc20-5001-7453-a08a-dac783cf4d80"
    )
    store.open_actor_workflow(portfolio.actor_context_id, "turn-p", "p", "portfolio")
    root_refs = build_capsule(store, root.actor_context_id)["canonical_refs"]
    em_refs = build_capsule(store, em.actor_context_id)["canonical_refs"]
    cm_refs = build_capsule(store, cm.actor_context_id)["canonical_refs"]
    port_refs = build_capsule(store, portfolio.actor_context_id)["canonical_refs"]
    assert ".agents/roles/ROOT.md" in root_refs
    assert ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md" in em_refs
    assert ".agents/roles/CODE_PROJECT_MANAGER.md" in cm_refs
    assert ".agents/roles/ROOT.md" in port_refs
    assert any("CROSS_DIRECTION_PORTFOLIO_HANDOFF" in item for item in port_refs)


def test_closed_epoch_commit_is_historical_only(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    semantic_commit_write(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
        payload=em_frontier_payload(),
        source_refs=["scratch-note"],
    )
    plan_epoch_close(store, epoch_id=epoch["epoch_id"], reason="done")
    assert semantic_commit_current(store, em.actor_context_id) is None
    working = build_working_set(store, em.actor_context_id)
    assert working.semantic_commit_id is None
    assert working.epoch_id is None
    capsule = build_capsule(store, em.actor_context_id)
    assert capsule["epoch_id"] is None


def test_audit_only_mark_removes_active_source_ref(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    epoch = open_em_epoch(store, em)
    semantic_commit_write(
        store,
        actor_context_id=em.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
        payload=em_frontier_payload(),
        source_refs=["scratch-note"],
    )
    working_before = build_working_set(store, em.actor_context_id)
    assert "scratch-note" in working_before.canonical_refs
    mark_refs_audit_only(
        store,
        actor_context_id=em.actor_context_id,
        refs=["scratch-note"],
        reason="forget scratch",
    )
    working = build_working_set(store, em.actor_context_id)
    capsule = render_capsule(build_capsule(store, em.actor_context_id))
    assert "scratch-note" not in working.canonical_refs
    assert "scratch-note" not in capsule
    row = store.connection.execute(
        "SELECT retention_class FROM context_retention_marks WHERE object_id = 'scratch-note'"
    ).fetchone()
    assert row[0] == "AUDIT_ONLY"
