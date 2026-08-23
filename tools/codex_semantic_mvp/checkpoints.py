"""Deterministic actor checkpoints. Compaction count is not an identity input."""

from __future__ import annotations

import json
from typing import Any

from .capsules import build_capsule, render_capsule
from .epochs import plan_epoch_current
from .semantic_commits import semantic_commit_current
from .store import SemanticStore, _json, _new_id, _now


def _identity_tuple(
    actor_context_id: str,
    epoch_id: str | None,
    epoch_revision: int | None,
    state_version: int,
    semantic_commit_id: str | None,
) -> tuple[str, str | None, int | None, int, str | None]:
    return (actor_context_id, epoch_id, epoch_revision, state_version, semantic_commit_id)


def materialize_checkpoint(store: SemanticStore, actor_context_id: str) -> dict[str, object]:
    workflow = store.current_actor_workflow(actor_context_id)
    epoch = plan_epoch_current(store, actor_context_id)
    commit = semantic_commit_current(store, actor_context_id)
    state_version = int((workflow or {}).get("state_version") or 0)
    epoch_id = str(epoch["epoch_id"]) if epoch else None
    epoch_revision = int(epoch["revision"]) if epoch else None
    semantic_commit_id = str(commit["semantic_commit_id"]) if commit else None
    with store._lock, store.connection:
        existing = store.connection.execute(
            """SELECT * FROM context_checkpoints
            WHERE actor_context_id = ?
              AND IFNULL(epoch_id, '') = IFNULL(?, '')
              AND IFNULL(epoch_revision, -1) = IFNULL(?, -1)
              AND state_version = ?
              AND IFNULL(semantic_commit_id, '') = IFNULL(?, '')
            ORDER BY created_at DESC LIMIT 1""",
            (actor_context_id, epoch_id, epoch_revision, state_version, semantic_commit_id),
        ).fetchone()
        if existing is not None:
            item = dict(existing)
            item["capsule"] = json.loads(item.pop("capsule_json"))
            item["reused"] = True
            return item
        capsule = build_capsule(store, actor_context_id)
        checkpoint_id = _new_id("ctx")
        capsule["checkpoint_id"] = checkpoint_id
        store.connection.execute(
            """INSERT INTO context_checkpoints (
                checkpoint_id, actor_context_id, epoch_id, epoch_revision,
                state_version, semantic_commit_id, capsule_kind, capsule_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                checkpoint_id,
                actor_context_id,
                epoch_id,
                epoch_revision,
                state_version,
                semantic_commit_id,
                str(capsule.get("capsule_kind") or "ACTOR_CAPSULE"),
                _json(capsule),
                _now(),
            ),
        )
        row = store.connection.execute(
            "SELECT * FROM context_checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,),
        ).fetchone()
        item = dict(row)
        item["capsule"] = json.loads(item.pop("capsule_json"))
        item["reused"] = False
        item["rendered"] = render_capsule(item["capsule"])
        return item


def compatible_identity(store: SemanticStore, actor_context_id: str) -> tuple[str | None, int | None, int, str | None]:
    workflow = store.current_actor_workflow(actor_context_id)
    epoch = plan_epoch_current(store, actor_context_id)
    commit = semantic_commit_current(store, actor_context_id)
    state_version = int((workflow or {}).get("state_version") or 0)
    epoch_id = str(epoch["epoch_id"]) if epoch else None
    epoch_revision = int(epoch["revision"]) if epoch else None
    semantic_commit_id = str(commit["semantic_commit_id"]) if commit else None
    return epoch_id, epoch_revision, state_version, semantic_commit_id


def current_checkpoint(store: SemanticStore, actor_context_id: str) -> dict[str, object] | None:
    """Return the checkpoint matching the current open epoch and workflow state."""
    epoch_id, epoch_revision, state_version, semantic_commit_id = compatible_identity(
        store, actor_context_id
    )
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM context_checkpoints
            WHERE actor_context_id = ?
              AND IFNULL(epoch_id, '') = IFNULL(?, '')
              AND IFNULL(epoch_revision, -1) = IFNULL(?, -1)
              AND state_version = ?
              AND IFNULL(semantic_commit_id, '') = IFNULL(?, '')
            ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1""",
            (actor_context_id, epoch_id, epoch_revision, state_version, semantic_commit_id),
        ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["capsule"] = json.loads(item.pop("capsule_json"))
        return item


def ensure_reanchor_obligation(
    store: SemanticStore,
    *,
    actor_context_id: str,
    checkpoint_id: str,
) -> str | None:
    from .models import ObligationKind

    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return None
    return store.ensure_open_obligation(
        str(workflow["workflow_id"]),
        ObligationKind.CONTEXT_REANCHOR_REQUIRED,
        actor_context_id,
        checkpoint_id,
        "A compact/resume checkpoint is available and must be acknowledged.",
        f"reanchor:{actor_context_id}:{checkpoint_id}",
        touch=False,
    )


def context_reanchor_ack(
    store: SemanticStore,
    *,
    actor_context_id: str,
    checkpoint_id: str,
    state_version: int,
    epoch_id: str | None,
    epoch_revision: int | None,
    actor_turn_id: str,
) -> dict[str, object]:
    from .models import ObligationKind

    with store._lock:
        owns_transaction = not store.connection.in_transaction
        if owns_transaction:
            store.connection.execute("BEGIN IMMEDIATE")
        try:
            existing = store.connection.execute(
                """SELECT ack_id FROM reanchor_acks
                WHERE actor_context_id = ? AND checkpoint_id = ?
                  AND state_version = ? AND epoch_id IS ?
                  AND epoch_revision IS ? AND actor_turn_id = ?""",
                (
                    actor_context_id,
                    checkpoint_id,
                    state_version,
                    epoch_id,
                    epoch_revision,
                    actor_turn_id,
                ),
            ).fetchone()
            if existing is not None:
                resolved = store.connection.execute(
                    """SELECT COUNT(*) AS total,
                        SUM(CASE WHEN obligations.state = 'RESOLVED'
                                      AND obligations.resolved_at IS NOT NULL
                                 THEN 1 ELSE 0 END) AS resolved
                    FROM obligations
                    JOIN workflows ON workflows.workflow_id = obligations.workflow_id
                    WHERE workflows.actor_context_id = ?
                      AND obligations.kind = ? AND obligations.subject = ?""",
                    (
                        actor_context_id,
                        ObligationKind.CONTEXT_REANCHOR_REQUIRED.value,
                        checkpoint_id,
                    ),
                ).fetchone()
                if (
                    resolved is None
                    or int(resolved["total"] or 0) == 0
                    or int(resolved["resolved"] or 0) != int(resolved["total"] or 0)
                ):
                    raise ValueError("existing reanchor ack has no durable obligation resolution")
                if owns_transaction:
                    store.connection.commit()
                return {
                    "ack_id": str(existing["ack_id"]),
                    "actor_context_id": actor_context_id,
                    "checkpoint_id": checkpoint_id,
                }

            checkpoint = store.connection.execute(
                "SELECT * FROM context_checkpoints WHERE checkpoint_id = ? AND actor_context_id = ?",
                (checkpoint_id, actor_context_id),
            ).fetchone()
            if checkpoint is None:
                raise ValueError("checkpoint does not belong to actor")
            workflow = store.current_actor_workflow(actor_context_id)
            current_version = int((workflow or {}).get("state_version") or 0)
            epoch = plan_epoch_current(store, actor_context_id)
            current_epoch = str(epoch["epoch_id"]) if epoch else None
            current_revision = int(epoch["revision"]) if epoch else None
            if int(state_version) != current_version:
                raise ValueError("reanchor ack is stale: state_version differs")
            if (
                (epoch_id or None) != current_epoch
                or (epoch_revision if epoch_revision is not None else None)
                != current_revision
            ):
                raise ValueError("reanchor ack is stale: epoch differs")
            if workflow is None:
                raise ValueError("matching CONTEXT_REANCHOR_REQUIRED is not open")
            obligation = store.connection.execute(
                """SELECT obligation_id FROM obligations
                WHERE workflow_id = ? AND kind = ? AND subject = ? AND state = 'OPEN'""",
                (
                    workflow["workflow_id"],
                    ObligationKind.CONTEXT_REANCHOR_REQUIRED.value,
                    checkpoint_id,
                ),
            ).fetchone()
            if obligation is None:
                raise ValueError("matching CONTEXT_REANCHOR_REQUIRED is not open")
            ack_id = _new_id("ack")
            store.connection.execute(
                """INSERT INTO reanchor_acks (
                    ack_id, actor_context_id, checkpoint_id, state_version, epoch_id,
                    epoch_revision, actor_turn_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ack_id,
                    actor_context_id,
                    checkpoint_id,
                    state_version,
                    epoch_id,
                    epoch_revision,
                    actor_turn_id,
                    _now(),
                ),
            )
            store.connection.execute(
                "UPDATE obligations SET state = 'RESOLVED', resolved_at = ? WHERE obligation_id = ?",
                (_now(), obligation[0]),
            )
            store._touch_workflow(str(workflow["workflow_id"]))
            if owns_transaction:
                store.connection.commit()
        except Exception:
            if owns_transaction and store.connection.in_transaction:
                store.connection.rollback()
            raise
    return {"ack_id": ack_id, "actor_context_id": actor_context_id, "checkpoint_id": checkpoint_id}


def is_actor_reanchored(store: SemanticStore, actor_context_id: str) -> bool:
    from .models import ObligationKind

    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return True
    open_reanchor = store.connection.execute(
        """SELECT 1 FROM obligations
        WHERE workflow_id = ? AND kind = ? AND state = 'OPEN' LIMIT 1""",
        (workflow["workflow_id"], ObligationKind.CONTEXT_REANCHOR_REQUIRED.value),
    ).fetchone()
    return open_reanchor is None


def require_actor_reanchored(store: SemanticStore, actor_context_id: str) -> None:
    if not is_actor_reanchored(store, actor_context_id):
        raise ValueError("actor reanchor acknowledgment is required")
