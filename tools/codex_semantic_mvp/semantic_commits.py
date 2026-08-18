"""Owner-authored reanchor snapshots. They do not create acceptance."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .actor_models import ACTOR_COMMIT_KINDS, ActorKind, SemanticCommitKind
from .epochs import plan_epoch_current
from .store import SemanticStore, _json, _new_id, _now


COMMIT_PAYLOAD_FIELDS: dict[SemanticCommitKind, tuple[str, ...]] = {
    SemanticCommitKind.PORTFOLIO_FRONTIER: (
        "current_cut_ref",
        "bounded_objective",
        "direction_rows",
        "cross_direction_relations",
        "open_questions",
    ),
    SemanticCommitKind.ROOT_COORDINATION_FRONTIER: (
        "current_user_goal",
        "direction_pairs",
        "pending_l1_milestone_ids",
        "pending_portfolio_packet_ids",
        "lease_refs",
        "user_decision_obligation_ids",
        "git_obligation_ids",
    ),
    SemanticCommitKind.EM_DIRECTION_FRONTIER: (
        "direction_id",
        "stage_envelope_ref",
        "current_science_object_ref",
        "current_question",
        "strongest_live_alternative",
        "claim_ceiling",
        "next_discriminator",
        "exploration_debt",
        "cm_counterpart_actor_context_id",
        "root_return_trigger",
    ),
    SemanticCommitKind.CM_TECHNICAL_FRONTIER: (
        "direction_id",
        "stage_envelope_ref",
        "science_card_ref",
        "protected_semantics",
        "technical_objective",
        "owned_paths",
        "worktree_ref",
        "remaining_technical_unknowns",
        "lease_ref",
        "pending_em_handoff_ref",
    ),
    SemanticCommitKind.LEAF_ASSIGNMENT_FRONTIER: (
        "task_id",
        "exact_assignment",
        "named_sources_or_interfaces",
        "protected_assumptions",
        "completion_evidence",
        "return_contract",
    ),
}


def _actor_kind(store: SemanticStore, actor_context_id: str) -> ActorKind:
    row = store.connection.execute(
        "SELECT actor_kind FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    return ActorKind(str(row[0]))


def _validate_payload(commit_kind: SemanticCommitKind, payload: Mapping[str, Any]) -> dict[str, Any]:
    required = COMMIT_PAYLOAD_FIELDS[commit_kind]
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"semantic commit payload missing {', '.join(missing)}")
    extra = [name for name in payload if name not in required]
    if extra:
        raise ValueError(f"semantic commit payload has unexpected fields: {', '.join(extra)}")
    refs = payload
    for name, value in refs.items():
        if name.endswith("_ref") and value not in (None, "") and not isinstance(value, str):
            raise ValueError(f"{name} must be a path or packet id, never a hash object")
    return {name: payload[name] for name in required}


def semantic_commit_write(
    store: SemanticStore,
    *,
    actor_context_id: str,
    epoch_id: str,
    commit_kind: SemanticCommitKind | str,
    payload: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, Any]:
    kind = (
        commit_kind
        if isinstance(commit_kind, SemanticCommitKind)
        else SemanticCommitKind(str(commit_kind))
    )
    if any("sha256" in str(item).lower() or len(str(item)) == 64 and str(item).isalnum() for item in source_refs):
        # Source refs must be paths or packet IDs. A 64-char hex string is rejected
        # only when it has no path separator, to avoid file-hash gates.
        for item in source_refs:
            text = str(item)
            if "/" not in text and "\\" not in text and ":" not in text and len(text) == 64:
                raise ValueError("source references must be paths or packet IDs, never file hashes")
    with store._lock, store.connection:
        actor_kind = _actor_kind(store, actor_context_id)
        allowed = ACTOR_COMMIT_KINDS.get(actor_kind)
        if allowed != kind:
            raise ValueError(f"{actor_kind.value} cannot write {kind.value}")
        epoch = store.connection.execute(
            "SELECT epoch_id, actor_context_id, state FROM plan_epochs WHERE epoch_id = ?",
            (epoch_id,),
        ).fetchone()
        if epoch is None:
            raise KeyError(f"unknown epoch: {epoch_id}")
        if str(epoch["actor_context_id"]) != actor_context_id:
            raise ValueError("epoch does not belong to this actor")
        if str(epoch["state"]) != "OPEN":
            raise ValueError("epoch is not open")
        validated = _validate_payload(kind, payload)
        commit_id = _new_id("scommit")
        store.connection.execute(
            """INSERT INTO semantic_commits (
                semantic_commit_id, actor_context_id, epoch_id, commit_kind,
                payload_json, source_refs_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                commit_id,
                actor_context_id,
                epoch_id,
                kind.value,
                _json(validated),
                _json(list(source_refs)),
                _now(),
            ),
        )
        row = store.connection.execute(
            "SELECT * FROM semantic_commits WHERE semantic_commit_id = ?",
            (commit_id,),
        ).fetchone()
        return _commit_row(row)


def current_open_epoch_commit(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    epoch = plan_epoch_current(store, actor_context_id)
    if epoch is None:
        return None
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM semantic_commits
            WHERE actor_context_id = ? AND epoch_id = ?
            ORDER BY created_at DESC, semantic_commit_id DESC LIMIT 1""",
            (actor_context_id, epoch["epoch_id"]),
        ).fetchone()
        return _commit_row(row) if row is not None else None


def latest_historical_commit(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM semantic_commits WHERE actor_context_id = ?
            ORDER BY created_at DESC, semantic_commit_id DESC LIMIT 1""",
            (actor_context_id,),
        ).fetchone()
        return _commit_row(row) if row is not None else None


def semantic_commit_current(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    """Latest commit on the current OPEN epoch only. Closed epochs are historical."""
    return current_open_epoch_commit(store, actor_context_id)


def write_semantic_commit_unlocked(
    store: SemanticStore,
    *,
    actor_context_id: str,
    epoch_id: str,
    commit_kind: SemanticCommitKind | str,
    payload: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, Any]:
    """Write a commit on the current connection. Caller owns the transaction."""
    kind = (
        commit_kind
        if isinstance(commit_kind, SemanticCommitKind)
        else SemanticCommitKind(str(commit_kind))
    )
    actor_kind = _actor_kind(store, actor_context_id)
    allowed = ACTOR_COMMIT_KINDS.get(actor_kind)
    if allowed != kind:
        raise ValueError(f"{actor_kind.value} cannot write {kind.value}")
    epoch = store.connection.execute(
        "SELECT epoch_id, actor_context_id, state FROM plan_epochs WHERE epoch_id = ?",
        (epoch_id,),
    ).fetchone()
    if epoch is None:
        raise KeyError(f"unknown epoch: {epoch_id}")
    if str(epoch["actor_context_id"]) != actor_context_id:
        raise ValueError("epoch does not belong to this actor")
    if str(epoch["state"]) != "OPEN":
        raise ValueError("epoch is not open")
    validated = _validate_payload(kind, payload)
    commit_id = _new_id("scommit")
    store.connection.execute(
        """INSERT INTO semantic_commits (
            semantic_commit_id, actor_context_id, epoch_id, commit_kind,
            payload_json, source_refs_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            commit_id,
            actor_context_id,
            epoch_id,
            kind.value,
            _json(validated),
            _json(list(source_refs)),
            _now(),
        ),
    )
    row = store.connection.execute(
        "SELECT * FROM semantic_commits WHERE semantic_commit_id = ?",
        (commit_id,),
    ).fetchone()
    return _commit_row(row)


def _commit_row(row: object) -> dict[str, Any]:
    item = dict(row)
    item["payload"] = json.loads(item.pop("payload_json"))
    item["source_refs"] = json.loads(item.pop("source_refs_json"))
    return item
