"""Explicit owner-local epoch rollover.

Rollover never authorizes a next scientific, technical, operational, or
portfolio stage beyond the owner's existing authority.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from tools.codex_semantic_mvp.actor_models import ACTOR_COMMIT_KINDS, ActorKind, EpochKind
from tools.codex_semantic_mvp.epochs import close_open_epoch, insert_open_epoch
from tools.codex_semantic_mvp.semantic_commits import (
    COMMIT_PAYLOAD_FIELDS,
    latest_historical_commit,
    write_semantic_commit_unlocked,
)
from tools.codex_semantic_mvp.store import SemanticStore, _json, _new_id, _now

from .authority import require_same_actor, touch_actor_workflow
from .models import PromotionState, RolloverState
from .precedence import assert_authoritative_source
from .retention import mark_refs_audit_only_unlocked

PORTFOLIO_CARRY = frozenset(
    {"open_cross_direction_questions", "revisit_conditions", "pending_packet_decisions"}
)
ROOT_CARRY = frozenset(
    {"pending_l1_milestones", "pending_portfolio_relay", "lease_user_git_obligations"}
)
EM_CARRY = frozenset(
    {
        "strongest_live_alternative",
        "claim_ceiling",
        "next_discriminator",
        "exploration_debt",
        "pending_cm_packet",
    }
)
CM_CARRY = frozenset(
    {
        "protected_semantics",
        "technical_unknowns",
        "retained_output_reference",
        "pending_em_handoff",
    }
)
ROLE_CARRY = {
    ActorKind.PORTFOLIO: PORTFOLIO_CARRY,
    ActorKind.OPERATIONAL_ROOT: ROOT_CARRY,
    ActorKind.EM: EM_CARRY,
    ActorKind.CM: CM_CARRY,
    ActorKind.LEAF: frozenset(),
}


class RolloverError(ValueError):
    """Raised when rollover is unauthorized or incomplete."""


def _actor_kind(store: SemanticStore, actor_context_id: str) -> ActorKind:
    row = store.connection.execute(
        "SELECT actor_kind FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    return ActorKind(str(row[0]))


def _row(row: object) -> dict[str, Any]:
    item = dict(row)
    item["carry_obligation_ids"] = json.loads(item.pop("carry_obligation_ids_json"))
    item["carry_packet_ids"] = json.loads(item.pop("carry_packet_ids_json"))
    item["carry_frontier"] = json.loads(item.pop("carry_frontier_json"))
    item["promotion_ids"] = json.loads(item.pop("promotion_ids_json"))
    item["forgotten_refs"] = json.loads(item.pop("forgotten_refs_json"))
    return item


def validate_carry_frontier(actor_kind: ActorKind, frontier: Mapping[str, Any]) -> None:
    allowed = ROLE_CARRY.get(actor_kind, frozenset())
    extra = set(frontier) - set(allowed)
    if extra:
        raise RolloverError(f"cross-role rollover fields are forbidden: {sorted(extra)}")


def _open_obligations(store: SemanticStore, actor_context_id: str) -> list[dict[str, Any]]:
    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return []
    rows = store.connection.execute(
        """SELECT obligation_id, state, subject, kind FROM obligations
        WHERE workflow_id = ? AND state = 'OPEN'""",
        (workflow["workflow_id"],),
    ).fetchall()
    return [dict(row) for row in rows]


def _epoch_promotions(store: SemanticStore, epoch_id: str) -> list[dict[str, Any]]:
    rows = store.connection.execute(
        "SELECT promotion_id, state FROM promotion_proposals WHERE epoch_id = ?",
        (epoch_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def prepare_rollover(
    store: SemanticStore,
    *,
    actor_context_id: str,
    from_epoch_id: str,
    from_epoch_revision: int,
    next_epoch_kind: EpochKind | str,
    next_objective: str,
    carry_obligation_ids: list[str] | tuple[str, ...] = (),
    carry_packet_ids: list[str] | tuple[str, ...] = (),
    carry_frontier: Mapping[str, Any] | None = None,
    promotion_ids: list[str] | tuple[str, ...] = (),
    forgotten_refs: list[str] | tuple[str, ...] = (),
    source_kind: str = "PLAN_EPOCH",
    requester_actor_context_id: str | None = None,
) -> dict[str, Any]:
    assert_authoritative_source(source_kind, "apply_rollover")
    requester = requester_actor_context_id or actor_context_id
    require_same_actor(requester, actor_context_id, "rollover actor")
    actor_kind = _actor_kind(store, actor_context_id)
    frontier = dict(carry_frontier or {})
    validate_carry_frontier(actor_kind, frontier)
    with store._lock:
        epoch = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?",
            (from_epoch_id,),
        ).fetchone()
        if epoch is None:
            raise KeyError(f"unknown epoch: {from_epoch_id}")
        if str(epoch["actor_context_id"]) != actor_context_id:
            raise RolloverError("epoch does not belong to this actor")
        if str(epoch["state"]) != "OPEN":
            raise RolloverError("only an open epoch can be prepared for rollover")
        if int(epoch["revision"]) != int(from_epoch_revision):
            raise RolloverError("from_epoch_revision does not match the current epoch")
        existing = store.connection.execute(
            """SELECT rollover_id FROM epoch_rollovers
            WHERE actor_context_id = ? AND from_epoch_id = ? AND state IN ('PREPARED', 'OWNER_CONFIRMED')""",
            (actor_context_id, from_epoch_id),
        ).fetchone()
        if existing is not None:
            raise RolloverError("a rollover is already prepared for this epoch")
    now = _now()
    rollover_id = _new_id("roll")
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO epoch_rollovers (
                rollover_id, actor_context_id, from_epoch_id, from_epoch_revision,
                next_epoch_kind, next_objective, carry_obligation_ids_json,
                carry_packet_ids_json, carry_frontier_json, promotion_ids_json,
                forgotten_refs_json, state, created_at, applied_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                rollover_id,
                actor_context_id,
                from_epoch_id,
                int(from_epoch_revision),
                str(next_epoch_kind.value if isinstance(next_epoch_kind, EpochKind) else next_epoch_kind),
                next_objective,
                _json(list(carry_obligation_ids)),
                _json(list(carry_packet_ids)),
                _json(frontier),
                _json(list(promotion_ids)),
                _json(list(forgotten_refs)),
                RolloverState.PREPARED.value,
                now,
            ),
        )
        row = store.connection.execute(
            "SELECT * FROM epoch_rollovers WHERE rollover_id = ?",
            (rollover_id,),
        ).fetchone()
        touch_actor_workflow(store, actor_context_id)
        return _row(row)


def confirm_rollover(
    store: SemanticStore,
    rollover_id: str,
    *,
    requester_actor_context_id: str,
    source_kind: str = "ROLE_CONTRACT",
) -> dict[str, Any]:
    assert_authoritative_source(source_kind, "create_owner_decision")
    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM epoch_rollovers WHERE rollover_id = ?",
            (rollover_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown rollover: {rollover_id}")
        require_same_actor(
            requester_actor_context_id, str(row["actor_context_id"]), "rollover actor"
        )
        if str(row["state"]) != RolloverState.PREPARED.value:
            raise RolloverError("only PREPARED rollovers can be confirmed")
        store.connection.execute(
            "UPDATE epoch_rollovers SET state = ? WHERE rollover_id = ?",
            (RolloverState.OWNER_CONFIRMED.value, rollover_id),
        )
        touch_actor_workflow(store, str(row["actor_context_id"]))
        updated = store.connection.execute(
            "SELECT * FROM epoch_rollovers WHERE rollover_id = ?",
            (rollover_id,),
        ).fetchone()
        return _row(updated)


def current_rollover(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    with store._lock:
        row = store.connection.execute(
            """SELECT * FROM epoch_rollovers
            WHERE actor_context_id = ? AND state IN ('PREPARED', 'OWNER_CONFIRMED')
            ORDER BY created_at DESC, rollover_id DESC LIMIT 1""",
            (actor_context_id,),
        ).fetchone()
        return _row(row) if row is not None else None


def _empty_commit_value(name: str) -> Any:
    if name.endswith("_ids") or name.endswith("_rows") or name.endswith("_relations") or name.endswith("_pairs") or name.endswith("_debt") or name.endswith("_unknowns") or name.endswith("_refs") or name.endswith("_semantics"):
        return []
    return ""


def _carry_commit_payload(actor_kind: ActorKind, previous: Mapping[str, Any] | None, frontier: Mapping[str, Any]) -> dict[str, Any]:
    commit_kind = ACTOR_COMMIT_KINDS[actor_kind]
    fields = COMMIT_PAYLOAD_FIELDS[commit_kind]
    prior = dict(previous or {})
    payload = {name: prior.get(name, _empty_commit_value(name)) for name in fields}
    aliases = {
        "technical_unknowns": "remaining_technical_unknowns",
        "pending_em_handoff": "pending_em_handoff_ref",
        "pending_portfolio_relay": "pending_portfolio_packet_ids",
        "lease_user_git_obligations": "git_obligation_ids",
        "pending_l1_milestones": "pending_l1_milestone_ids",
        "open_cross_direction_questions": "open_questions",
        "revisit_conditions": "open_questions",
    }
    for key, value in frontier.items():
        if key in payload:
            payload[key] = value
            continue
        mapped = aliases.get(key)
        if mapped and mapped in payload:
            payload[mapped] = value
    return payload


def apply_rollover(
    store: SemanticStore,
    *,
    rollover_id: str,
    source_kind: str = "PLAN_EPOCH",
    requester_actor_context_id: str | None = None,
    fail_after: str | None = None,
) -> dict[str, Any]:
    assert_authoritative_source(source_kind, "apply_rollover")

    def _fail(point: str) -> None:
        if fail_after == point:
            raise RolloverError(f"injected failure:{point}")

    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM epoch_rollovers WHERE rollover_id = ?",
            (rollover_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown rollover: {rollover_id}")
        payload = _row(row)
        actor_id = payload["actor_context_id"]
        requester = requester_actor_context_id or actor_id
        require_same_actor(requester, actor_id, "rollover actor")
        if payload["state"] != RolloverState.OWNER_CONFIRMED.value:
            raise RolloverError("apply requires OWNER_CONFIRMED")
        epoch = store.connection.execute(
            "SELECT * FROM plan_epochs WHERE epoch_id = ?",
            (payload["from_epoch_id"],),
        ).fetchone()
        if epoch is None:
            raise KeyError(f"unknown epoch: {payload['from_epoch_id']}")
        if int(epoch["revision"]) != int(payload["from_epoch_revision"]):
            raise RolloverError("from_epoch_revision no longer matches")
        epoch_data = {
            "authority_refs": json.loads(epoch["authority_refs_json"] or "[]"),
            "frozen_invariants": json.loads(epoch["frozen_invariants_json"] or "[]"),
            "navigation_refs": json.loads(epoch["navigation_refs_json"] or "[]"),
            "procedure_refs": json.loads(epoch["procedure_refs_json"] or "[]"),
        }
        open_rows = _open_obligations(store, actor_id)
        carried_promos = set(payload["promotion_ids"])
        auto_carry = {
            item["obligation_id"]
            for item in open_rows
            if item.get("subject") in carried_promos
        }
        open_ids = {item["obligation_id"] for item in open_rows}
        carry_ids = set(payload["carry_obligation_ids"]) | auto_carry
        unresolved = open_ids - carry_ids
        if unresolved:
            raise RolloverError(
                "open obligations must be resolved, cancelled, or listed in carry_obligation_ids"
            )
        for promo in _epoch_promotions(store, payload["from_epoch_id"]):
            state = PromotionState(str(promo["state"]))
            if state in {PromotionState.APPLIED, PromotionState.OWNER_REJECTED}:
                continue
            if promo["promotion_id"] in payload["promotion_ids"]:
                continue
            raise RolloverError(
                "promotions must be APPLIED, OWNER_REJECTED, or listed for carry-forward"
            )
        forgotten = set(payload["forgotten_refs"])
        authority_refs = [item for item in epoch_data["authority_refs"] if item not in forgotten]
        frozen = [item for item in epoch_data["frozen_invariants"] if item not in forgotten]
        navigation_refs = [item for item in epoch_data["navigation_refs"] if item not in forgotten]
        procedure_refs = [item for item in epoch_data["procedure_refs"] if item not in forgotten]
        previous_commit = latest_historical_commit(store, actor_id)

        closed = close_open_epoch(
            store, epoch_id=payload["from_epoch_id"], reason=f"rolled-over:{rollover_id}"
        )
        _fail("after_close")
        now = _now()
        for promo_id in payload["promotion_ids"]:
            store.connection.execute(
                """UPDATE promotion_proposals
                SET state = ?, updated_at = ?
                WHERE promotion_id = ? AND state IN (?, ?)""",
                (
                    PromotionState.CARRIED_FORWARD.value,
                    now,
                    promo_id,
                    PromotionState.PROPOSED.value,
                    PromotionState.CARRIED_FORWARD.value,
                ),
            )
        _fail("after_promotion_carry")
        new_epoch = insert_open_epoch(
            store,
            actor_context_id=actor_id,
            epoch_kind=payload["next_epoch_kind"],
            objective=payload["next_objective"],
            authority_refs=authority_refs,
            frozen_invariants=frozen,
            exit_boundary="owner-local rollover; no new stage authority",
            navigation_refs=navigation_refs,
            procedure_refs=procedure_refs,
            carry_frontier=payload["carry_frontier"],
        )
        for promo_id in payload["promotion_ids"]:
            store.connection.execute(
                """UPDATE promotion_proposals
                SET epoch_id = ?, carried_to_epoch_id = ?, updated_at = ?
                WHERE promotion_id = ?""",
                (new_epoch["epoch_id"], new_epoch["epoch_id"], now, promo_id),
            )
        _fail("after_new_epoch")
        mark_refs_audit_only_unlocked(
            store,
            actor_context_id=actor_id,
            refs=payload["forgotten_refs"],
            reason=f"forgotten during {rollover_id}",
        )
        _fail("after_retention_mark")
        actor_kind = _actor_kind(store, actor_id)
        if actor_kind in ACTOR_COMMIT_KINDS:
            write_semantic_commit_unlocked(
                store,
                actor_context_id=actor_id,
                epoch_id=new_epoch["epoch_id"],
                commit_kind=ACTOR_COMMIT_KINDS[actor_kind],
                payload=_carry_commit_payload(
                    actor_kind,
                    (previous_commit or {}).get("payload"),
                    payload["carry_frontier"],
                ),
                source_refs=list(payload["carry_packet_ids"]),
            )
        _fail("before_final_update")
        store.connection.execute(
            """UPDATE epoch_rollovers
            SET state = ?, applied_at = ?, to_epoch_id = ?
            WHERE rollover_id = ?""",
            (RolloverState.APPLIED.value, now, new_epoch["epoch_id"], rollover_id),
        )
        touch_actor_workflow(store, actor_id)
        workflow = store.current_actor_workflow(actor_id)
        if workflow is not None:
            store._append_event(
                str(workflow["workflow_id"]),
                "EPOCH_ROLLED_OVER",
                rollover_id,
                {
                    "from_epoch_id": payload["from_epoch_id"],
                    "to_epoch_id": new_epoch["epoch_id"],
                },
                f"EPOCH_ROLLED_OVER:{rollover_id}",
            )
        updated = store.connection.execute(
            "SELECT * FROM epoch_rollovers WHERE rollover_id = ?",
            (rollover_id,),
        ).fetchone()
        result = _row(updated)
        result["closed_epoch"] = closed
        result["new_epoch"] = new_epoch
        result["to_epoch_id"] = new_epoch["epoch_id"]
        return result
