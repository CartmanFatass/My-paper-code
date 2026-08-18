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
    item["navigation_refs"] = json.loads(item.pop("navigation_refs_json") or "[]")
    item["procedure_refs"] = json.loads(item.pop("procedure_refs_json") or "[]")
    item["carry_frontier"] = json.loads(item.pop("carry_frontier_json") or "{}")
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
    navigation_refs: list[str] | tuple[str, ...] = (),
    procedure_refs: list[str] | tuple[str, ...] = (),
    registry: object | None = None,
) -> dict[str, Any]:
    with store._lock, store.connection:
        return insert_open_epoch(
            store,
            actor_context_id=actor_context_id,
            epoch_kind=epoch_kind,
            objective=objective,
            authority_refs=authority_refs,
            frozen_invariants=frozen_invariants,
            exit_boundary=exit_boundary,
            navigation_refs=navigation_refs,
            procedure_refs=procedure_refs,
            registry=registry,
        )


def plan_epoch_current(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM plan_epochs
            WHERE actor_context_id = ? AND state = 'OPEN'
            ORDER BY updated_at DESC, created_at DESC LIMIT 1""",
            (actor_context_id,),
        ).fetchone()
        return _row(row) if row is not None else None


def _validate_registry_refs(
    store: SemanticStore,
    actor_context_id: str,
    navigation_refs: list[str] | tuple[str, ...],
    procedure_refs: list[str] | tuple[str, ...],
    registry: object | None,
) -> None:
    if registry is None:
        return
    from tools.codex_context_lifecycle.source_registry import sources_for_actor

    actor_kind = _actor_kind(store, actor_context_id)
    requested = list(navigation_refs) + list(procedure_refs)
    visible = {
        source.id
        for source in sources_for_actor(
            registry, actor_kind, requested_source_ids=requested
        )
    }
    unknown = [item for item in requested if item not in visible]
    if unknown:
        raise ValueError(f"source not visible to actor: {unknown}")


def insert_open_epoch(
    store: SemanticStore,
    *,
    actor_context_id: str,
    epoch_kind: EpochKind | str,
    objective: str,
    authority_refs: list[str] | tuple[str, ...],
    frozen_invariants: list[str] | tuple[str, ...],
    exit_boundary: str,
    navigation_refs: list[str] | tuple[str, ...] = (),
    procedure_refs: list[str] | tuple[str, ...] = (),
    carry_frontier: dict[str, Any] | None = None,
    registry: object | None = None,
) -> dict[str, Any]:
    """Insert an OPEN epoch on the current connection. Caller owns the transaction."""
    kind = epoch_kind if isinstance(epoch_kind, EpochKind) else EpochKind(str(epoch_kind))
    actor_kind = _actor_kind(store, actor_context_id)
    _require_compatible(actor_kind, kind)
    _validate_registry_refs(store, actor_context_id, navigation_refs, procedure_refs, registry)
    now = _now()
    epoch_id = _new_id("epoch")
    store.connection.execute(
        """INSERT INTO plan_epochs (
            epoch_id, actor_context_id, epoch_kind, revision, objective,
            authority_refs_json, frozen_invariants_json, exit_boundary,
            navigation_refs_json, procedure_refs_json, carry_frontier_json,
            state, created_at, updated_at
        ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)""",
        (
            epoch_id,
            actor_context_id,
            kind.value,
            objective,
            _json(list(authority_refs)),
            _json(list(frozen_invariants)),
            exit_boundary,
            _json(list(navigation_refs)),
            _json(list(procedure_refs)),
            _json(dict(carry_frontier or {})),
            now,
            now,
        ),
    )
    row = store.connection.execute(
        "SELECT * FROM plan_epochs WHERE epoch_id = ?", (epoch_id,)
    ).fetchone()
    return _row(row)


def close_open_epoch(store: SemanticStore, *, epoch_id: str, reason: str = "") -> dict[str, Any]:
    """Close an OPEN epoch on the current connection. Caller owns the transaction."""
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
    navigation_refs: list[str] | tuple[str, ...] | None = None,
    procedure_refs: list[str] | tuple[str, ...] | None = None,
    registry: object | None = None,
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
        current = _row(row)
        nav = list(navigation_refs) if navigation_refs is not None else list(current["navigation_refs"])
        proc = list(procedure_refs) if procedure_refs is not None else list(current["procedure_refs"])
        _validate_registry_refs(store, str(row["actor_context_id"]), nav, proc, registry)
        store.connection.execute(
            """UPDATE plan_epochs SET revision = revision + 1, objective = ?,
            authority_refs_json = ?, frozen_invariants_json = ?, exit_boundary = ?,
            navigation_refs_json = ?, procedure_refs_json = ?,
            updated_at = ? WHERE epoch_id = ?""",
            (
                objective,
                _json(list(authority_refs)),
                _json(list(frozen_invariants)),
                exit_boundary,
                _json(nav),
                _json(proc),
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
        return close_open_epoch(store, epoch_id=epoch_id, reason=reason)
