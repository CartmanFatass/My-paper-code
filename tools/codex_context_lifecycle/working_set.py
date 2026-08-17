"""Active working-set computation. Forgetting is exclusion, not deletion."""

from __future__ import annotations

import json
from typing import Any

from tools.codex_semantic_mvp.actor_models import ActorKind, ActorState, actor_context_from_row
from tools.codex_semantic_mvp.checkpoints import current_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_current
from tools.codex_semantic_mvp.models import normalize_obligation_kind
from tools.codex_semantic_mvp.semantic_commits import semantic_commit_current
from tools.codex_semantic_mvp.store import SemanticStore

from .models import WorkingSet

ACTIVE_PACKET_DELIVERY = frozenset(
    {"PREPARED", "SUBMISSION_UNCERTAIN", "DELIVERED_VISIBLE_TARGET", "ACKNOWLEDGED"}
)
TERMINAL_PROMOTIONS = frozenset({"APPLIED", "OWNER_REJECTED"})


def _open_obligations(store: SemanticStore, actor_context_id: str) -> list[dict[str, Any]]:
    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return []
    rows = store.connection.execute(
        """SELECT * FROM obligations
        WHERE workflow_id = ? AND state = 'OPEN'
        ORDER BY created_at, obligation_id""",
        (workflow["workflow_id"],),
    ).fetchall()
    return [dict(row) for row in rows]


def _active_packets(store: SemanticStore, actor_context_id: str) -> list[dict[str, Any]]:
    rows = store.connection.execute(
        """SELECT * FROM packet_refs
        WHERE (source_actor_context_id = ? OR target_actor_context_id = ?)
          AND intake_state != 'APPLIED'
        ORDER BY created_at, packet_id""",
        (actor_context_id, actor_context_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _open_promotions(store: SemanticStore, epoch_id: str | None) -> list[str]:
    if not epoch_id:
        return []
    rows = store.connection.execute(
        """SELECT promotion_id FROM promotion_proposals
        WHERE epoch_id = ? AND state NOT IN ('APPLIED', 'OWNER_REJECTED')
        ORDER BY created_at, promotion_id""",
        (epoch_id,),
    ).fetchall()
    return [str(row[0]) for row in rows]


def _prepared_rollover(store: SemanticStore, actor_context_id: str) -> str | None:
    row = store.connection.execute(
        """SELECT rollover_id FROM epoch_rollovers
        WHERE actor_context_id = ? AND state IN ('PREPARED', 'OWNER_CONFIRMED')
        ORDER BY created_at DESC LIMIT 1""",
        (actor_context_id,),
    ).fetchone()
    return str(row[0]) if row else None


def _excluded(store: SemanticStore, actor_context_id: str, included: set[str]) -> tuple[str, ...]:
    excluded: list[str] = []
    for table, column in (
        ("plan_epochs", "epoch_id"),
        ("semantic_commits", "semantic_commit_id"),
        ("context_checkpoints", "checkpoint_id"),
        ("promotion_proposals", "promotion_id"),
        ("epoch_rollovers", "rollover_id"),
    ):
        rows = store.connection.execute(
            f"SELECT {column} FROM {table} WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchall()
        for row in rows:
            if row[0] not in included:
                excluded.append(str(row[0]))
    return tuple(excluded)


def build_working_set(store: SemanticStore, actor_context_id: str) -> WorkingSet:
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    actor = actor_context_from_row(row)
    epoch = plan_epoch_current(store, actor_context_id)
    commit = semantic_commit_current(store, actor_context_id)
    checkpoint = current_checkpoint(store, actor_context_id)
    obligations = _open_obligations(store, actor_context_id)
    packets = _active_packets(store, actor_context_id)
    report_ids = [
        str(item.get("subject") or "")
        for item in obligations
        if normalize_obligation_kind(str(item.get("kind") or "")) == "REPORT_INTAKE_REQUIRED"
        and item.get("subject")
    ]
    navigation_refs = tuple((epoch or {}).get("navigation_refs") or ())
    procedure_refs = tuple((epoch or {}).get("procedure_refs") or ())
    canonical = ["AGENTS.md"]
    if epoch:
        canonical.extend(str(item) for item in epoch.get("authority_refs") or [] if item)
    if commit:
        payload = commit.get("payload") or {}
        for key, value in payload.items():
            if str(key).endswith("_ref") and isinstance(value, str) and value:
                canonical.append(value)
        canonical.extend(str(item) for item in commit.get("source_refs") or [] if item)
    canonical = tuple(dict.fromkeys(canonical))
    epoch_id = (epoch or {}).get("epoch_id")
    promotions = tuple(_open_promotions(store, epoch_id))
    included = {item for item in (
        epoch_id,
        (commit or {}).get("semantic_commit_id"),
        (checkpoint or {}).get("checkpoint_id"),
        *_open_promotions(store, epoch_id),
        _prepared_rollover(store, actor_context_id),
    ) if item}
    return WorkingSet(
        actor_context_id=actor.actor_context_id,
        actor_kind=actor.actor_kind.value,
        epoch_id=epoch_id,
        semantic_commit_id=(commit or {}).get("semantic_commit_id"),
        checkpoint_id=(checkpoint or {}).get("checkpoint_id"),
        open_obligation_ids=tuple(item.get("obligation_id") for item in obligations),
        unintaken_report_ids=tuple(report_ids),
        active_packet_ids=tuple(item.get("packet_id") for item in packets),
        navigation_refs=navigation_refs,
        procedure_refs=procedure_refs,
        canonical_refs=canonical,
        promotion_ids=promotions,
        rollover_id=_prepared_rollover(store, actor_context_id),
        excluded_object_ids=_excluded(store, actor_context_id, included),
    )


def working_set_refs(store: SemanticStore, actor_context_id: str) -> dict[str, Any]:
    working = build_working_set(store, actor_context_id)
    return {
        "actor_context_id": working.actor_context_id,
        "epoch_id": working.epoch_id,
        "semantic_commit_id": working.semantic_commit_id,
        "checkpoint_id": working.checkpoint_id,
        "navigation_refs": list(working.navigation_refs),
        "procedure_refs": list(working.procedure_refs),
        "canonical_refs": list(working.canonical_refs),
        "open_obligation_ids": list(working.open_obligation_ids),
        "active_packet_ids": list(working.active_packet_ids),
        "promotion_ids": list(working.promotion_ids),
        "rollover_id": working.rollover_id,
    }


def resolve_epoch_context_refs(
    store: SemanticStore,
    actor_context_id: str,
    epoch_id: str,
    registry=None,
    repo_root=None,
) -> dict[str, tuple[str, ...]]:
    from .source_registry import load_registry, sources_for_actor

    row = store.connection.execute(
        "SELECT * FROM plan_epochs WHERE epoch_id = ? AND actor_context_id = ?",
        (epoch_id, actor_context_id),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown epoch: {epoch_id}")
    actor = store.connection.execute(
        "SELECT actor_kind FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if actor is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    nav = json.loads(row["navigation_refs_json"] or "[]")
    proc = json.loads(row["procedure_refs_json"] or "[]")
    if registry is None and repo_root is not None:
        registry = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
    if registry is not None:
        visible = {
            source.id
            for source in sources_for_actor(
                registry,
                ActorKind(str(actor[0])),
                requested_source_ids=tuple(nav + proc),
            )
        }
        nav = [item for item in nav if item in visible]
        proc = [item for item in proc if item in visible]
    return {"navigation_refs": tuple(nav), "procedure_refs": tuple(proc)}


def actor_may_auto_rehydrate(store: SemanticStore, actor_context_id: str) -> bool:
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        return False
    actor = actor_context_from_row(row)
    if actor.state is not ActorState.ACTIVE:
        return False
    return actor.actor_kind in {ActorKind.PORTFOLIO, ActorKind.OPERATIONAL_ROOT}
