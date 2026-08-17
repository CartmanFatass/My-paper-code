from tests.codex_context_lifecycle.helpers import make_pair
from tools.codex_context_lifecycle.retention import apply_gc_marks, plan_gc
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_close, plan_epoch_open
from tools.codex_semantic_mvp.store import SemanticStore


def test_dry_run_never_deletes(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    first = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="old",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="next",
    )
    plan_epoch_close(store, epoch_id=first["epoch_id"], reason="advance")
    plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="current",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="next",
    )
    plan = plan_gc(store, actor_context_id=em.actor_context_id)
    assert plan["mode"] == "DRY_RUN"
    assert plan["deletions"] == []
    assert any(item["object_id"] == first["epoch_id"] for item in plan["would_mark_audit_only"])
    current = plan_epoch_open  # keep import used
    assert any(item["object_kind"] == "epoch" for item in plan["would_keep_active"])


def test_mark_archived_does_not_delete_rows(store: SemanticStore) -> None:
    _root, em, _cm = make_pair(store)
    first = plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="old",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="next",
    )
    plan_epoch_close(store, epoch_id=first["epoch_id"], reason="advance")
    plan_epoch_open(
        store,
        actor_context_id=em.actor_context_id,
        epoch_kind=EpochKind.DIRECTION_STAGE,
        objective="current",
        authority_refs=[],
        frozen_invariants=[],
        exit_boundary="next",
    )
    before = store.connection.execute("SELECT COUNT(*) FROM plan_epochs").fetchone()[0]
    applied = apply_gc_marks(store, actor_context_id=em.actor_context_id)
    after = store.connection.execute("SELECT COUNT(*) FROM plan_epochs").fetchone()[0]
    assert before == after
    assert applied["deletions"] == []
    marked = store.connection.execute(
        "SELECT retention_class FROM context_retention_marks WHERE object_id = ?",
        (first["epoch_id"],),
    ).fetchone()
    assert marked[0] == "AUDIT_ONLY"
