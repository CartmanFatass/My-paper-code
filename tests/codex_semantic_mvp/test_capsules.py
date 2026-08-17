from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind, SemanticCommitKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.capsules import build_capsule, render_capsule
from tools.codex_semantic_mvp.constants import MAX_CAPSULE_BYTES
from tools.codex_semantic_mvp.epochs import plan_epoch_open
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_write
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def test_max_capsule_bytes_constant() -> None:
    assert MAX_CAPSULE_BYTES == 16384


def test_portfolio_capsule_excludes_runtime(store: SemanticStore) -> None:
    actor = register_session_root(store, session_id="019ffc20-5001-7453-a08a-dac783cf4d80")
    epoch = plan_epoch_open(
        store,
        actor_context_id=actor.actor_context_id,
        epoch_kind=EpochKind.PORTFOLIO_INQUIRY,
        objective="Choose current variable-N/k investments.",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="portfolio decision",
    )
    semantic_commit_write(
        store,
        actor_context_id=actor.actor_context_id,
        epoch_id=epoch["epoch_id"],
        commit_kind=SemanticCommitKind.PORTFOLIO_FRONTIER,
        payload={
            "current_cut_ref": "docs/cut.md",
            "bounded_objective": "Choose current variable-N/k investments.",
            "direction_rows": [{"direction_id": "vnfc", "decision": "invest"}],
            "cross_direction_relations": [],
            "open_questions": [],
        },
        source_refs=["docs/cut.md"],
    )
    capsule = build_capsule(store, actor.actor_context_id)
    text = render_capsule(capsule)
    assert "CPU" not in text
    assert "implementer" not in text.lower()
    assert capsule["actor_kind"] == "PORTFOLIO"
    assert "docs/cut.md" in capsule["canonical_refs"]


def test_render_is_deterministic(store: SemanticStore) -> None:
    actor = register_session_root(store, session_id="session-root")
    first = render_capsule(build_capsule(store, actor.actor_context_id))
    second = render_capsule(build_capsule(store, actor.actor_context_id))
    assert first == second
    assert "BLOCKED" not in first
