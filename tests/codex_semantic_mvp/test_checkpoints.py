from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_session_root
from tools.codex_semantic_mvp.checkpoints import current_checkpoint, materialize_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_same_typed_state_ignores_raw_prose(store: SemanticStore) -> None:
    actor = register_session_root(store, session_id="session-ckpt")
    store.open_actor_workflow(actor.actor_context_id, "turn-1", "scope", "coordinate")
    epoch = plan_epoch_open(
        store,
        actor_context_id=actor.actor_context_id,
        epoch_kind=EpochKind.OPERATIONAL_COORDINATION,
        objective="coordinate",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="user decision",
    )
    semantic_commit_write(
        store,
        actor_context_id=actor.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind="ROOT_COORDINATION_FRONTIER",
        payload={
            "current_user_goal": "Continue authorized portfolio and direction stages.",
            "direction_pairs": [],
            "pending_l1_milestone_ids": [],
            "pending_portfolio_packet_ids": [],
            "lease_refs": [],
            "user_decision_obligation_ids": [],
            "git_obligation_ids": [],
        },
        source_refs=["AGENTS.md"],
    )
    first = materialize_checkpoint(store, actor.actor_context_id)
    second = materialize_checkpoint(store, actor.actor_context_id)
    assert first["checkpoint_id"] == second["checkpoint_id"]
    assert first["capsule"] == second["capsule"]
    text = str(first["capsule"])
    assert "BLOCKED" not in text
    assert "released" not in text
    assert current_checkpoint(store, actor.actor_context_id)["checkpoint_id"] == first["checkpoint_id"]
    assert "compaction" not in first
