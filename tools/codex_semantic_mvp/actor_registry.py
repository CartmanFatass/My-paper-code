"""Explicit actor registration and layered identity resolution.

Never infer EM/CM from natural-language output. Releasing an actor context
does not change direction or portfolio disposition.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping

from .actor_models import ActorContext, ActorKind, ActorState, actor_context_from_row
from .store import SemanticStore, _new_id, _now


DEFAULT_ACTORS_PATH = Path(".codex/semantic-actors.toml")
DEFAULT_PORTFOLIO_SESSION_ID = "019ffc20-5001-7453-a08a-dac783cf4d80"
DEFAULT_SESSION_ROOT_KIND = ActorKind.OPERATIONAL_ROOT


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_actor_mapping(path: Path | None = None) -> dict[str, Any]:
    mapping_path = path or (_repo_root() / DEFAULT_ACTORS_PATH)
    portfolio_ids = [DEFAULT_PORTFOLIO_SESSION_ID]
    default_kind = DEFAULT_SESSION_ROOT_KIND
    if mapping_path.is_file():
        text = mapping_path.read_text(encoding="utf-8")
        ids: list[str] = []
        in_ids = False
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("default_session_root_kind"):
                value = line.split("=", 1)[1].strip().strip('"')
                default_kind = ActorKind(value)
                continue
            if line.startswith("portfolio_session_ids"):
                in_ids = True
                remainder = line.split("=", 1)[1].strip()
                if remainder.startswith("["):
                    remainder = remainder[1:]
                    if remainder.endswith("]"):
                        remainder = remainder[:-1]
                        in_ids = False
                    for item in remainder.split(","):
                        item = item.strip().strip('"').strip(",")
                        if item:
                            ids.append(item)
                continue
            if in_ids:
                if line.startswith("]"):
                    in_ids = False
                    continue
                item = line.strip().strip('"').strip(",")
                if item:
                    ids.append(item)
        if ids:
            portfolio_ids = ids
    return {
        "portfolio_session_ids": portfolio_ids,
        "default_session_root_kind": default_kind,
    }


def session_root_kind(session_id: str, mapping: Mapping[str, Any] | None = None) -> ActorKind:
    config = mapping or load_actor_mapping()
    if session_id in set(config["portfolio_session_ids"]):
        return ActorKind.PORTFOLIO
    kind = config.get("default_session_root_kind") or DEFAULT_SESSION_ROOT_KIND
    return kind if isinstance(kind, ActorKind) else ActorKind(str(kind))


def _row_to_actor(row: sqlite3.Row | None) -> ActorContext | None:
    return actor_context_from_row(row) if row is not None else None


def _insert_actor(
    store: SemanticStore,
    *,
    session_id: str,
    actor_kind: ActorKind,
    scope_key: str,
    identity_source: str,
    agent_id: str | None = None,
    canonical_path: str | None = None,
    direction_id: str | None = None,
    parent_actor_context_id: str | None = None,
    counterpart_actor_context_id: str | None = None,
    actor_context_id: str | None = None,
    state: ActorState = ActorState.ACTIVE,
) -> ActorContext:
    actor_context_id = actor_context_id or _new_id("actor")
    now = _now()
    store.connection.execute(
        """INSERT INTO actor_contexts (
            actor_context_id, session_id, agent_id, canonical_path, actor_kind,
            scope_key, direction_id, parent_actor_context_id,
            counterpart_actor_context_id, identity_source, state,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            actor_context_id,
            session_id,
            agent_id or None,
            canonical_path or None,
            actor_kind.value,
            scope_key,
            direction_id or None,
            parent_actor_context_id or None,
            counterpart_actor_context_id or None,
            identity_source,
            state.value,
            now,
            now,
        ),
    )
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"failed to insert actor: {actor_context_id}")
    return actor_context_from_row(row)


def register_session_root(
    store: SemanticStore,
    *,
    session_id: str,
    mapping_path: Path | None = None,
) -> ActorContext:
    """Register or return the explicit session-root actor. Never infers EM/CM."""
    if not session_id:
        raise ValueError("session_id is required")
    mapping = load_actor_mapping(mapping_path)
    kind = session_root_kind(session_id, mapping)
    with store._lock, store.connection:
        existing = store.connection.execute(
            """SELECT * FROM actor_contexts
            WHERE session_id = ? AND actor_kind IN ('PORTFOLIO', 'OPERATIONAL_ROOT', 'SESSION_ROOT_UNCLASSIFIED')
            ORDER BY CASE actor_kind
                WHEN 'PORTFOLIO' THEN 0
                WHEN 'OPERATIONAL_ROOT' THEN 1
                ELSE 2
            END, created_at
            LIMIT 1""",
            (session_id,),
        ).fetchone()
        if existing is not None:
            actor = actor_context_from_row(existing)
            if actor.actor_kind == ActorKind.SESSION_ROOT_UNCLASSIFIED and kind != ActorKind.SESSION_ROOT_UNCLASSIFIED:
                now = _now()
                store.connection.execute(
                    """UPDATE actor_contexts
                    SET actor_kind = ?, identity_source = 'SESSION_ROOT_MAPPING', updated_at = ?
                    WHERE actor_context_id = ?""",
                    (kind.value, now, actor.actor_context_id),
                )
                row = store.connection.execute(
                    "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
                    (actor.actor_context_id,),
                ).fetchone()
                return actor_context_from_row(row)
            return actor
        return _insert_actor(
            store,
            session_id=session_id,
            actor_kind=kind,
            scope_key=f"session:{session_id}",
            identity_source="SESSION_ROOT_MAPPING",
        )


def register_child_actor(
    store: SemanticStore,
    *,
    session_id: str,
    actor_kind: ActorKind,
    scope_key: str,
    direction_id: str | None,
    parent_actor_context_id: str,
    counterpart_actor_context_id: str | None = None,
    canonical_path: str | None = None,
) -> ActorContext:
    """Create an unbound child actor before spawn_agent."""
    if actor_kind not in {ActorKind.EM, ActorKind.CM, ActorKind.LEAF}:
        raise ValueError(f"child actor kind must be EM, CM, or LEAF: {actor_kind}")
    if not parent_actor_context_id:
        raise ValueError("parent_actor_context_id is required")
    with store._lock, store.connection:
        parent = store.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (parent_actor_context_id,),
        ).fetchone()
        if parent is None:
            raise KeyError(f"unknown parent actor: {parent_actor_context_id}")
        actor = _insert_actor(
            store,
            session_id=session_id,
            actor_kind=actor_kind,
            scope_key=scope_key,
            identity_source="EXPLICIT_REGISTRATION",
            canonical_path=canonical_path,
            direction_id=direction_id,
            parent_actor_context_id=parent_actor_context_id,
            counterpart_actor_context_id=counterpart_actor_context_id,
        )
        if counterpart_actor_context_id:
            store.connection.execute(
                """UPDATE actor_contexts
                SET counterpart_actor_context_id = ?, updated_at = ?
                WHERE actor_context_id = ? AND (counterpart_actor_context_id IS NULL OR counterpart_actor_context_id = '')""",
                (actor.actor_context_id, _now(), counterpart_actor_context_id),
            )
        return actor


def bind_agent_identity(
    store: SemanticStore,
    *,
    actor_context_id: str,
    agent_id: str,
    canonical_path: str | None = None,
) -> ActorContext:
    if not actor_context_id:
        raise ValueError("actor_context_id is required")
    if not agent_id:
        raise ValueError("agent_id is required")
    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown actor: {actor_context_id}")
        current = actor_context_from_row(row)
        if current.agent_id and current.agent_id != agent_id:
            raise sqlite3.IntegrityError(
                f"actor {actor_context_id} already bound to {current.agent_id}"
            )
        try:
            store.connection.execute(
                """UPDATE actor_contexts
                SET agent_id = ?, canonical_path = COALESCE(?, canonical_path), updated_at = ?
                WHERE actor_context_id = ?""",
                (agent_id, canonical_path or None, _now(), actor_context_id),
            )
        except sqlite3.IntegrityError as exc:
            raise sqlite3.IntegrityError(
                f"duplicate session/agent binding for {current.session_id}/{agent_id}"
            ) from exc
        bound = store.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchone()
        return actor_context_from_row(bound)


def link_counterparts(
    store: SemanticStore,
    first_actor_context_id: str,
    second_actor_context_id: str,
) -> None:
    if not first_actor_context_id or not second_actor_context_id:
        raise ValueError("both counterpart actor IDs are required")
    now = _now()
    with store._lock, store.connection:
        store.connection.execute(
            """UPDATE actor_contexts SET counterpart_actor_context_id = ?, updated_at = ?
            WHERE actor_context_id = ?""",
            (second_actor_context_id, now, first_actor_context_id),
        )
        store.connection.execute(
            """UPDATE actor_contexts SET counterpart_actor_context_id = ?, updated_at = ?
            WHERE actor_context_id = ?""",
            (first_actor_context_id, now, second_actor_context_id),
        )


def release_actor_context(store: SemanticStore, actor_context_id: str) -> ActorContext:
    with store._lock, store.connection:
        store.connection.execute(
            """UPDATE actor_contexts SET state = ?, updated_at = ?
            WHERE actor_context_id = ?""",
            (ActorState.RELEASED.value, _now(), actor_context_id),
        )
        row = store.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown actor: {actor_context_id}")
        return actor_context_from_row(row)


def resolve_actor_context(
    store: SemanticStore,
    *,
    session_id: str,
    agent_id: str = "",
    canonical_path: str = "",
    task_id: str = "",
    workflow_id: str = "",
) -> ActorContext | None:
    """Resolve by exact identity layers. Never infer EM/CM from prose."""
    if not session_id:
        return None
    with store._lock:
        if agent_id:
            row = store.connection.execute(
                """SELECT * FROM actor_contexts
                WHERE session_id = ? AND agent_id = ? AND state = 'ACTIVE'""",
                (session_id, agent_id),
            ).fetchone()
            if row is not None:
                return actor_context_from_row(row)
        if canonical_path:
            row = store.connection.execute(
                """SELECT * FROM actor_contexts
                WHERE session_id = ? AND canonical_path = ? AND state = 'ACTIVE'""",
                (session_id, canonical_path),
            ).fetchone()
            if row is not None:
                return actor_context_from_row(row)
        if workflow_id and task_id:
            row = store.connection.execute(
                """SELECT actor_contexts.* FROM tasks
                JOIN actor_contexts ON actor_contexts.actor_context_id = tasks.child_actor_context_id
                WHERE tasks.workflow_id = ? AND tasks.task_id = ?
                  AND actor_contexts.session_id = ?""",
                (workflow_id, task_id, session_id),
            ).fetchone()
            if row is not None:
                return actor_context_from_row(row)
        mapped = register_session_root(store, session_id=session_id)
        if mapped.actor_kind != ActorKind.SESSION_ROOT_UNCLASSIFIED:
            return mapped
        row = store.connection.execute(
            """SELECT * FROM actor_contexts
            WHERE session_id = ? AND actor_kind = 'SESSION_ROOT_UNCLASSIFIED'
            ORDER BY created_at LIMIT 1""",
            (session_id,),
        ).fetchone()
        return actor_context_from_row(row) if row is not None else mapped
