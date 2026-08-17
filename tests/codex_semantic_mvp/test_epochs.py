import inspect
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind, EpochKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.epochs import (
    EpochRevisionConflict,
    plan_epoch_close,
    plan_epoch_current,
    plan_epoch_open,
    revise_epoch,
)
from tools.codex_semantic_mvp.hook_entry import handle_hook
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def _open(store: SemanticStore, actor_id: str, kind: EpochKind) -> dict:
    return plan_epoch_open(
        store,
        actor_context_id=actor_id,
        epoch_kind=kind,
        objective="objective",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="explicit close",
    )


def test_em_cannot_open_technical_closure(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-em")
    em = register_child_actor(
        store,
        session_id="s-em",
        actor_kind=ActorKind.EM,
        scope_key="direction:a:em",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
    )
    with pytest.raises(ValueError, match="EM cannot open TECHNICAL_CLOSURE"):
        _open(store, em.actor_context_id, EpochKind.TECHNICAL_CLOSURE)


def test_cm_cannot_open_direction_stage(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-cm")
    cm = register_child_actor(
        store,
        session_id="s-cm",
        actor_kind=ActorKind.CM,
        scope_key="direction:a:cm",
        direction_id="a",
        parent_actor_context_id=root.actor_context_id,
    )
    with pytest.raises(ValueError, match="CM cannot open DIRECTION_STAGE"):
        _open(store, cm.actor_context_id, EpochKind.DIRECTION_STAGE)


def test_leaf_cannot_open_portfolio_inquiry(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-leaf")
    leaf = register_child_actor(
        store,
        session_id="s-leaf",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:scout",
        direction_id=None,
        parent_actor_context_id=root.actor_context_id,
    )
    with pytest.raises(ValueError, match="LEAF cannot open PORTFOLIO_INQUIRY"):
        _open(store, leaf.actor_context_id, EpochKind.PORTFOLIO_INQUIRY)


def test_compatible_epochs_and_one_open_per_actor(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-ok")
    opened = _open(store, root.actor_context_id, EpochKind.OPERATIONAL_COORDINATION)
    assert opened["revision"] == 1
    current = plan_epoch_current(store, root.actor_context_id)
    assert current is not None
    assert current["epoch_id"] == opened["epoch_id"]
    with pytest.raises(Exception):
        _open(store, root.actor_context_id, EpochKind.OPERATIONAL_COORDINATION)


def test_stale_revision_raises_conflict(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-rev")
    opened = _open(store, root.actor_context_id, EpochKind.OPERATIONAL_COORDINATION)
    revise_epoch(
        store,
        epoch_id=opened["epoch_id"],
        expected_revision=1,
        objective="revised",
        authority_refs=["AGENTS.md"],
        frozen_invariants=["no file-hash gate"],
        exit_boundary="explicit close",
        reason="owner revise",
    )
    with pytest.raises(EpochRevisionConflict, match="epoch revision conflict"):
        revise_epoch(
            store,
            epoch_id=opened["epoch_id"],
            expected_revision=1,
            objective="stale",
            authority_refs=["AGENTS.md"],
            frozen_invariants=["no file-hash gate"],
            exit_boundary="explicit close",
            reason="stale",
        )
    current = plan_epoch_current(store, root.actor_context_id)
    assert current is not None
    assert current["revision"] == 2
    assert current["objective"] == "revised"


def test_compaction_hooks_do_not_call_plan_epoch_revise() -> None:
    source = inspect.getsource(handle_hook)
    assert "revise_epoch" not in source
    assert "plan_epoch_revise" not in source
    import tools.codex_semantic_mvp.hook_entry as hook_entry

    text = inspect.getsource(hook_entry)
    assert "revise_epoch" not in text


def test_close_epoch_clears_open_slot(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="s-close")
    opened = _open(store, root.actor_context_id, EpochKind.OPERATIONAL_COORDINATION)
    plan_epoch_close(store, epoch_id=opened["epoch_id"], reason="done")
    assert plan_epoch_current(store, root.actor_context_id) is None
    again = _open(store, root.actor_context_id, EpochKind.OPERATIONAL_COORDINATION)
    assert again["epoch_id"] != opened["epoch_id"]
