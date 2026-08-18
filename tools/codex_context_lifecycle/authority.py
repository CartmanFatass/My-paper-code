"""Trusted requester and typed user-authority records.

MCP callers cannot self-assert P0 USER_AUTHORITY. Mutations require a
session-bound requester. A P0 grant is a ledger row created only by the
library/CLI/hook path, never by a generic MCP argument.
"""

from __future__ import annotations

import os
from pathlib import Path

from tools.codex_semantic_mvp.actor_models import ActorState, actor_context_from_row
from tools.codex_semantic_mvp.store import SemanticStore, _new_id, _now

from .precedence import assert_authoritative_source

BOUND_ACTOR_ENV = "HMASD_BOUND_ACTOR_CONTEXT_ID"
REPO_ROOT_ENV = "HMASD_REPO_ROOT"

_bound_requester_actor_context_id: str | None = None


class AuthorityError(PermissionError):
    """Raised when a mutation lacks a trusted requester or typed P0 grant."""


def bind_requester(actor_context_id: str | None) -> None:
    """Bind the process-local MCP requester. None makes mutations read-only."""
    global _bound_requester_actor_context_id
    _bound_requester_actor_context_id = actor_context_id


def current_bound_requester() -> str | None:
    return os.environ.get(BOUND_ACTOR_ENV) or _bound_requester_actor_context_id


def default_repo_root() -> Path:
    env = os.environ.get(REPO_ROOT_ENV)
    if env:
        return Path(env)
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "AGENTS.md").is_file() and (
            candidate / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
        ).is_file():
            return candidate
    return Path(__file__).resolve().parents[2]


def require_requester(store: SemanticStore, actor_context_id: str, *, require_active: bool = True):
    if not actor_context_id:
        raise AuthorityError("requester_actor_context_id is required")
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise AuthorityError(f"unknown requester: {actor_context_id}")
    actor = actor_context_from_row(row)
    if require_active and actor.state is not ActorState.ACTIVE:
        raise AuthorityError("requester actor is not ACTIVE")
    return actor


def require_same_actor(requester_id: str, owner_id: str, label: str) -> None:
    if requester_id != owner_id:
        raise AuthorityError(f"requester is not the {label}")


def resolve_mcp_requester(store: SemanticStore, claimed_requester: str | None) -> str:
    bound = current_bound_requester()
    if not bound:
        raise AuthorityError(
            "MCP mutations require a session-bound requester; generic MCP is read-only"
        )
    if claimed_requester and claimed_requester != bound:
        raise AuthorityError("requester_actor_context_id does not match the bound session actor")
    return require_requester(store, bound).actor_context_id


def grant_user_authority(
    store: SemanticStore,
    *,
    actor_context_id: str,
    operation: str,
) -> dict[str, str]:
    """Create a typed P0 record. Not exposed on generic MCP."""
    require_requester(store, actor_context_id)
    grant_id = _new_id("uauth")
    now = _now()
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO user_authority_grants (
                grant_id, actor_context_id, operation, created_at, consumed_at
            ) VALUES (?, ?, ?, ?, NULL)""",
            (grant_id, actor_context_id, operation, now),
        )
    return {
        "grant_id": grant_id,
        "actor_context_id": actor_context_id,
        "operation": operation,
    }


def consume_user_authority(
    store: SemanticStore,
    *,
    grant_id: str,
    actor_context_id: str,
    operation: str,
) -> None:
    if not grant_id:
        raise AuthorityError("USER_AUTHORITY requires an existing grant id")
    with store._lock:
        row = store.connection.execute(
            """SELECT grant_id, actor_context_id, operation, consumed_at
            FROM user_authority_grants WHERE grant_id = ?""",
            (grant_id,),
        ).fetchone()
        if row is None:
            raise AuthorityError("USER_AUTHORITY grant does not exist")
        if str(row["actor_context_id"]) != actor_context_id:
            raise AuthorityError("USER_AUTHORITY grant belongs to a different actor")
        if str(row["operation"]) != operation:
            raise AuthorityError("USER_AUTHORITY grant does not cover this operation")
        if row["consumed_at"] is not None:
            raise AuthorityError("USER_AUTHORITY grant was already consumed")
        store.connection.execute(
            "UPDATE user_authority_grants SET consumed_at = ? WHERE grant_id = ?",
            (_now(), grant_id),
        )


def assert_mutation_source(
    store: SemanticStore,
    source_kind: str | None,
    operation: str,
    *,
    requester_actor_context_id: str,
    user_authority_id: str | None = None,
) -> None:
    if source_kind is None or str(source_kind).strip() == "":
        raise AuthorityError("source_kind is required; USER_AUTHORITY is not the default")
    kind = str(source_kind)
    if kind == "USER_AUTHORITY":
        consume_user_authority(
            store,
            grant_id=str(user_authority_id or ""),
            actor_context_id=requester_actor_context_id,
            operation=operation,
        )
    assert_authoritative_source(kind, operation)


def touch_actor_workflow(store: SemanticStore, actor_context_id: str) -> None:
    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return
    store._touch_workflow(str(workflow["workflow_id"]))
