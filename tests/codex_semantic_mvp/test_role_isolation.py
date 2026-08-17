from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_role_isolation_projections(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-iso")
    em = register_child_actor(
        store,
        session_id="session-iso",
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="dir-a",
        parent_actor_context_id=root.actor_context_id,
    )
    cm = register_child_actor(
        store,
        session_id="session-iso",
        actor_kind=ActorKind.CM,
        scope_key="direction:a:cm",
        direction_id="dir-a",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
    )
    leaf = register_child_actor(
        store,
        session_id="session-iso",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:scout",
        direction_id="dir-a",
        parent_actor_context_id=em.actor_context_id,
    )
    portfolio = register_session_root(store, session_id="019ffc20-5001-7453-a08a-dac783cf4d80")

    plan_epoch_open(
        store,
        actor_context_id=root.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="coordinate",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no L2 leak"],
        exit_boundary="milestone",
    )
    semantic_commit_write(
        store,
        actor_context_id=root.actor_context_id,
        epoch_id=store.connection.execute(
            "SELECT epoch_id FROM plan_epochs WHERE actor_context_id = ?",
            (root.actor_context_id,),
        ).fetchone()[0],
        commit_kind=SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
        payload={
            "current_user_goal": "Continue authorized stages.",
            "direction_pairs": [{"em": em.actor_context_id, "cm": cm.actor_context_id}],
            "pending_l1_milestone_ids": [],
            "pending_portfolio_packet_ids": [],
            "lease_refs": [],
            "user_decision_obligation_ids": [],
            "git_obligation_ids": [],
        },
        source_refs=["AGENTS.md"],
    )
    plan_epoch_open(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_kind=EpochKind.TECHNICAL_CLOSURE,
        objective="implement",
        authority_refs=["docs/card.md"],
        frozen_invariants=["protected semantics"],
        exit_boundary="technical acceptance",
    )
    semantic_commit_write(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_id=store.connection.execute(
            "SELECT epoch_id FROM plan_epochs WHERE actor_context_id = ?",
            (cm.actor_context_id,),
        ).fetchone()[0],
        commit_kind=SemanticCommitKind.CM_TECHNICAL_FRONTIER,
        payload={
            "direction_id": "dir-a",
            "stage_envelope_ref": "docs/env.md",
            "science_card_ref": "docs/card.md",
            "protected_semantics": ["seed"],
            "technical_objective": "implement host",
            "owned_paths": ["ha_ctse_process/x.py"],
            "worktree_ref": "",
            "remaining_technical_unknowns": [],
            "lease_ref": None,
            "pending_em_handoff_ref": None,
        },
        source_refs=["docs/card.md"],
    )
    plan_epoch_open(
        store,
        actor_context_id=leaf.actor_context_id,
        epoch_kind=EpochKind.ASSIGNMENT,
        objective="inspect",
        authority_refs=["assignment"],
        frozen_invariants=["exact assignment"],
        exit_boundary="return envelope",
    )
    semantic_commit_write(
        store,
        actor_context_id=leaf.actor_context_id,
        epoch_id=store.connection.execute(
            "SELECT epoch_id FROM plan_epochs WHERE actor_context_id = ?",
            (leaf.actor_context_id,),
        ).fetchone()[0],
        commit_kind=SemanticCommitKind.LEAF_ASSIGNMENT_FRONTIER,
        payload={
            "task_id": "task-1",
            "exact_assignment": "inspect one file",
            "named_sources_or_interfaces": ["tools/x.py"],
            "protected_assumptions": ["no sibling state"],
            "completion_evidence": "path list",
            "return_contract": "HMASD_SUBAGENT_RETURN_V1",
        },
        source_refs=["tools/x.py"],
    )
    plan_epoch_open(
        store,
        actor_context_id=portfolio.actor_context_id,
        epoch_kind=EpochKind.PORTFOLIO_INQUIRY,
        objective="allocate",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["destination criterion"],
        exit_boundary="decision",
    )

    portfolio_text = render_capsule(build_capsule(store, portfolio.actor_context_id))
    root_text = render_capsule(build_capsule(store, root.actor_context_id))
    cm_text = render_capsule(build_capsule(store, cm.actor_context_id)).lower()
    leaf_text = render_capsule(build_capsule(store, leaf.actor_context_id))

    assert "CPU" not in portfolio_text
    assert "implementer" not in root_text
    assert "portfolio priority" not in cm_text
    assert "sibling_direction" not in leaf_text
    assert "inspect one file" in leaf_text
    assert "dir-b" not in leaf_text
