"""Role-scoped plan epochs. Compaction never revises an epoch."""

from __future__ import annotations

import json
from typing import Any

from .actor_models import ACTOR_EPOCH_KINDS, ActorKind, EpochKind
from .store import SemanticStore, _json, _new_id, _now


class EpochRevisionConflict(ValueError):
    """Raised when a revise sees a stale revision."""


def _actor_kind(store: SemanticStore, actor_context_id: str) -> ActorKind:
    row = store.connection.execute(
        "SELECT actor_kind FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    return ActorKind(str(row[0]))


def _require_compatible(actor_kind: ActorKind, epoch_kind: EpochKind) -> None:
    allowed = ACTOR_EPOCH_KINDS.get(actor_kind)
    if allowed != epoch_kind:
        raise ValueError(f"{actor_kind.value} cannot open {epoch_kind.value}")


def _row(row: object) -> dict[str, Any]:
    item = dict(row)
    item["authority_refs"] = json.loads(item.pop("authority_refs_json"))
    item["frozen_invariants"] = json.loads(item.pop("frozen_invariants_json"))
    return item


def plan_epoch_open(
    store: SemanticStore,
    *,
    actor_context_id: str,
    epoch_kind: EpochKind | str,
    objective: str,
    authority_refs: list[str],
    frozen_invariants: list[str],
    exit_boundary: str,
) -> dict[str, Any]:
    kind = epoch_kind if isinstance(epoch_kind, EpochKind) else EpochKind(str(epoch_kind))
    with store._lock, store.connection:
        actor_kind = _actor_kind(store, actor_context_id)
        _require_compatible(actor_kind, kind)
        now = _now()
        epoch_id = _new_id("epoch")
        store.connection.execute(
            """INSERT INTO plan_epochs (
                epoch_id, actor_context_id, epoch_kind, revision, objective,
                authority_refs_json, frozen_invariants_json, exit_boundary,
                state, created_at, updated_at
            ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'OPEN', ?, ?)""",
            (
                epoch_id,
                actor_context_id,
                kind.value,
                objective,
                _json(list(authority_refs)),
                _json(list(frozen_invariants)),
                exit_boundary,
                now,
                now,
            ),
        )
        row = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?", (epoch_id,)
        ).fetchone()
        return _row(row)


def plan_epoch_current(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM plan_epochs
            WHERE actor_context_id = ? AND state = 'OPEN'
            ORDER BY updated_at DESC, created_at DESC LIMIT 1""",
            (actor_context_id,),
        ).fetchone()
        return _row(row) if row is not None else None


def revise_epoch(
    store: SemanticStore,
    *,
    epoch_id: str,
    expected_revision: int,
    objective: str,
    authority_refs: list[str],
    frozen_invariants: list[str],
    exit_boundary: str,
    reason: str,
) -> dict[str, object]:
    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?", (epoch_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown epoch: {epoch_id}")
        if str(row["state"]) != "OPEN":
            raise ValueError(f"epoch is not open: {epoch_id}")
        if int(row["revision"]) != int(expected_revision):
            raise EpochRevisionConflict("epoch revision conflict")
        now = _now()
        store.connection.execute(
            """UPDATE plan_epochs SET revision = revision + 1, objective = ?,
            authority_refs_json = ?, frozen_invariants_json = ?, exit_boundary = ?,
            updated_at = ? WHERE epoch_id = ?""",
            (
                objective,
                _json(list(authority_refs)),
                _json(list(frozen_invariants)),
                exit_boundary,
                now,
                epoch_id,
            ),
        )
        updated = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?", (epoch_id,)
        ).fetchone()
        result = _row(updated)
        result["reason"] = reason
        return result


def plan_epoch_close(store: SemanticStore, *, epoch_id: str, reason: str = "") -> dict[str, Any]:
    with store._lock, store.connection:
        cursor = store.connection.execute(
            """UPDATE plan_epochs SET state = 'CLOSED', updated_at = ?
            WHERE epoch_id = ? AND state = 'OPEN'""",
            (_now(), epoch_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(f"open epoch not found: {epoch_id}")
        row = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?", (epoch_id,)
        ).fetchone()
        result = _row(row)
        result["reason"] = reason
        return result
