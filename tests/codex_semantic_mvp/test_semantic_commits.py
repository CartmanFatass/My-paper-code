import inspect
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_current, semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore
import tools.codex_semantic_mvp.hook_entry as hook_entry


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def _root_payload() -> dict:
    return {
        "current_user_goal": "Continue authorized portfolio and direction stages.",
        "direction_pairs": [],
        "pending_l1_milestone_ids": [],
        "pending_portfolio_packet_ids": [],
        "lease_refs": [],
        "user_decision_obligation_ids": [],
        "git_obligation_ids": [],
    }


def test_role_commit_kind_compatibility(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-root")
    cm = register_child_actor(
        store,
        session_id="s-root",
        actor_kind=ActorKind.CM,
        scope_key="direction:a:cm",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
    )
    epoch = plan_epoch_open(
        store,
        actor_context_id=cm.actor_context_id,
        epoch_kind=EpochKind.TECHNICAL_CLOSURE,
        objective="implement",
        authority_refs=["docs/card.md"],
        frozen_invariants=["protected semantics"],
        exit_boundary="technical acceptance",
    )
    with pytest.raises(ValueError, match="CM cannot write EM_DIRECTION_FRONTIER"):
        semantic_commit_write(
            store,
            actor_context_id=cm.actor_context_id,
            epoch_id=epoch["epoch_id"],
            commit_kind=SemanticCommitKind.EM_DIRECTION_FRONTIER,
            payload={
                "direction_id": "a",
                "stage_envelope_ref": "docs/env.md",
                "current_science_object_ref": "docs/card.md",
                "current_question": "q",
                "strongest_live_alternative": "alt",
                "claim_ceiling": "ceiling",
                "next_discriminator": "next",
                "exploration_debt": [],
                "cm_counterpart_actor_context_id": cm.actor_context_id,
                "root_return_trigger": None,
            },
            source_refs=["docs/card.md"],
        )


def test_leaf_cannot_write_root_frontier(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-leaf")
    leaf = register_child_actor(
        store,
        session_id="s-leaf",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:1",
        direction_id=None,
        parent_actor_context_id=root.actor_context_id,
    )
    epoch = plan_epoch_open(
        store,
        actor_context_id=leaf.actor_context_id,
        epoch_kind=EpochKind.ASSIGNMENT,
        objective="do one task",
        authority_refs=["assignment"],
        frozen_invariants=["exact assignment"],
        exit_boundary="return envelope",
    )
    with pytest.raises(ValueError, match="LEAF cannot write ROOT_COORDINATION_FRONTIER"):
        semantic_commit_write(
            store,
            actor_context_id=leaf.actor_context_id,
            epoch_id=epoch["epoch_id"],
            commit_kind=SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
            payload=_root_payload(),
            source_refs=["assignment"],
        )


def test_owner_commit_is_local_and_path_referenced(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-ok")
    epoch = plan_epoch_open(
        store,
        actor_context_id=root.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="coordinate",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="user decision",
    )
    written = semantic_commit_write(
        store,
        actor_context_id=root.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
        payload=_root_payload(),
        source_refs=["AGENTS.md", ".agents/roles/ROOT.md"],
    )
    current = semantic_commit_current(store, root.actor_context_id)
    assert current is not None
    assert current["semantic_commit_id"] == written["semantic_commit_id"]
    assert current["source_refs"] == ["AGENTS.md", ".agents/roles/ROOT.md"]
    assert current["payload"]["current_user_goal"]


def test_file_hash_source_ref_rejected(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-hash")
    epoch = plan_epoch_open(
        store,
        actor_context_id=root.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="coordinate",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="user decision",
    )
    with pytest.raises(ValueError, match="never file hashes"):
        semantic_commit_write(
            store,
            actor_context_id=root.actor_context_id,
            epoch_id=epoch["epoch_id"],
            commit_kind=SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
            payload=_root_payload(),
            source_refs=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
        )


def test_hooks_never_write_semantic_commits() -> None:
    assert "semantic_commit_write" not in inspect.getsource(hook_entry)
