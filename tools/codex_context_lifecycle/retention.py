"""Conservative retention marks. The first implementation never deletes rows."""

from __future__ import annotations

import json
from typing import Any

from tools.codex_semantic_mvp.store import SemanticStore, _json, _new_id, _now

from .models import GcMode, RetentionClass
from .working_set import build_working_set


PROTECTED_KINDS = frozenset(
    {
        "epoch",
        "obligation",
        "report",
        "packet",
        "rollover",
        "promotion",
        "checkpoint",
        "semantic_commit",
        "canonical_ref",
    }
)


def mark_refs_audit_only_unlocked(
    store: SemanticStore,
    *,
    actor_context_id: str,
    refs: list[str] | tuple[str, ...],
    reason: str,
) -> None:
    now = _now()
    for ref in refs:
        store.connection.execute(
            """INSERT OR REPLACE INTO context_retention_marks (
                retention_mark_id, actor_context_id, object_kind, object_id,
                retention_class, active_in_working_set, reason, created_at, archived_at
            ) VALUES (?, ?, 'forgotten_ref', ?, ?, 0, ?, ?, ?)""",
            (
                _new_id("ret"),
                actor_context_id,
                ref,
                RetentionClass.AUDIT_ONLY.value,
                reason,
                now,
                now,
            ),
        )


def mark_refs_audit_only(
    store: SemanticStore,
    *,
    actor_context_id: str,
    refs: list[str] | tuple[str, ...],
    reason: str,
) -> None:
    with store._lock, store.connection:
        mark_refs_audit_only_unlocked(
            store, actor_context_id=actor_context_id, refs=refs, reason=reason
        )


def _eligible_historical(store: SemanticStore, actor_context_id: str) -> list[dict[str, str]]:
    working = build_working_set(store, actor_context_id)
    protected_ids = set(working.open_obligation_ids + working.unintaken_report_ids + working.active_packet_ids)
    if working.epoch_id:
        protected_ids.add(working.epoch_id)
    if working.semantic_commit_id:
        protected_ids.add(working.semantic_commit_id)
    if working.checkpoint_id:
        protected_ids.add(working.checkpoint_id)
    if working.rollover_id:
        protected_ids.add(working.rollover_id)
    protected_ids.update(working.promotion_ids)
    candidates: list[dict[str, str]] = []
    closed = store.connection.execute(
        """SELECT epoch_id FROM plan_epochs
        WHERE actor_context_id = ? AND state != 'OPEN'""",
        (actor_context_id,),
    ).fetchall()
    for row in closed:
        if row[0] not in protected_ids:
            candidates.append({"object_kind": "epoch", "object_id": row[0]})
    older_commits = store.connection.execute(
        """SELECT semantic_commit_id FROM semantic_commits
        WHERE actor_context_id = ? ORDER BY created_at DESC, semantic_commit_id DESC""",
        (actor_context_id,),
    ).fetchall()
    for row in older_commits[1:]:
        if row[0] not in protected_ids:
            candidates.append({"object_kind": "semantic_commit", "object_id": row[0]})
    older_checkpoints = store.connection.execute(
        """SELECT checkpoint_id FROM context_checkpoints
        WHERE actor_context_id = ? ORDER BY created_at DESC, checkpoint_id DESC""",
        (actor_context_id,),
    ).fetchall()
    for row in older_checkpoints[1:]:
        if row[0] not in protected_ids:
            candidates.append({"object_kind": "checkpoint", "object_id": row[0]})
    return candidates


def plan_gc(
    store: SemanticStore,
    *,
    actor_context_id: str | None = None,
    mode: GcMode | str = GcMode.DRY_RUN,
) -> dict[str, Any]:
    resolved_mode = mode if isinstance(mode, GcMode) else GcMode(str(mode))
    actors = [actor_context_id] if actor_context_id else [
        str(row[0])
        for row in store.connection.execute(
            "SELECT actor_context_id FROM actor_contexts ORDER BY actor_context_id"
        )
    ]
    would_mark: list[dict[str, str]] = []
    would_keep_active: list[dict[str, str]] = []
    would_keep_raw: list[dict[str, str]] = []
    for actor in actors:
        working = build_working_set(store, actor)
        for object_id, kind in (
            (working.epoch_id, "epoch"),
            (working.checkpoint_id, "checkpoint"),
            (working.semantic_commit_id, "semantic_commit"),
            (working.rollover_id, "rollover"),
        ):
            if object_id:
                would_keep_active.append(
                    {"actor_context_id": actor, "object_kind": kind, "object_id": object_id}
                )
        would_mark.extend(
            {"actor_context_id": actor, **item} for item in _eligible_historical(store, actor)
        )
        reports = store.connection.execute(
            """SELECT report_id FROM reports
            WHERE reporter_actor_context_id = ?""",
            (actor,),
        ).fetchall()
        for row in reports:
            would_keep_raw.append(
                {
                    "actor_context_id": actor,
                    "object_kind": "report",
                    "object_id": row[0],
                    "retention_class": RetentionClass.RAW_EVIDENCE_RETAINED.value,
                }
            )
    return {
        "mode": resolved_mode.value,
        "would_mark_audit_only": would_mark,
        "would_keep_active": would_keep_active,
        "would_keep_raw": would_keep_raw,
        "deletions": [],
    }


def apply_gc_marks(
    store: SemanticStore,
    *,
    actor_context_id: str | None = None,
) -> dict[str, Any]:
    plan = plan_gc(store, actor_context_id=actor_context_id, mode=GcMode.MARK_ARCHIVED)
    now = _now()
    run_id = _new_id("gc")
    with store._lock, store.connection:
        for item in plan["would_mark_audit_only"]:
            store.connection.execute(
                """INSERT OR REPLACE INTO context_retention_marks (
                    retention_mark_id, actor_context_id, object_kind, object_id,
                    retention_class, active_in_working_set, reason, created_at, archived_at
                ) VALUES (?, ?, ?, ?, ?, 0, 'gc mark-archived', ?, ?)""",
                (
                    _new_id("ret"),
                    item["actor_context_id"],
                    item["object_kind"],
                    item["object_id"],
                    RetentionClass.AUDIT_ONLY.value,
                    now,
                    now,
                ),
            )
        store.connection.execute(
            """INSERT INTO context_gc_runs (
                gc_run_id, actor_context_id, mode, plan_json, applied, created_at
            ) VALUES (?, ?, ?, ?, 1, ?)""",
            (
                run_id,
                actor_context_id,
                GcMode.MARK_ARCHIVED.value,
                _json(plan),
                now,
            ),
        )
    plan["gc_run_id"] = run_id
    plan["applied"] = True
    return plan


def record_dry_run(
    store: SemanticStore,
    *,
    actor_context_id: str | None = None,
) -> dict[str, Any]:
    plan = plan_gc(store, actor_context_id=actor_context_id, mode=GcMode.DRY_RUN)
    now = _now()
    run_id = _new_id("gc")
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO context_gc_runs (
                gc_run_id, actor_context_id, mode, plan_json, applied, created_at
            ) VALUES (?, ?, ?, ?, 0, ?)""",
            (run_id, actor_context_id, GcMode.DRY_RUN.value, json.dumps(plan), now),
        )
    plan["gc_run_id"] = run_id
    plan["applied"] = False
    return plan
