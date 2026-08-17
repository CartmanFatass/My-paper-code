"""Cross-owner packet references. Delivery is not a decision."""

from __future__ import annotations

from typing import Any

from .models import ObligationKind
from .store import SemanticStore, _new_id, _now


PACKET_KINDS = frozenset(
    {
        "EM_TO_CM_SCIENCE_CARD",
        "CM_TO_EM_TECHNICAL_RESULT",
        "EM_TO_ROOT_MILESTONE",
        "CM_TO_ROOT_AUTHORITY_REQUEST",
        "ROOT_TO_PORTFOLIO_REVIEW",
        "PORTFOLIO_TO_ROOT_DECISION",
        "ROOT_TO_PORTFOLIO_APPLIED_ACK",
    }
)
DELIVERY_STATES = frozenset(
    {"PREPARED", "SUBMISSION_UNCERTAIN", "DELIVERED_VISIBLE_TARGET", "ACKNOWLEDGED"}
)
INTAKE_STATES = frozenset({"NOT_INTAKEN", "INTAKEN", "APPLIED"})


def _row(row: object) -> dict[str, Any]:
    return dict(row)


def packet_register(
    store: SemanticStore,
    *,
    packet_kind: str,
    source_actor_context_id: str,
    target_actor_context_id: str,
    payload_ref: str,
    marker: str | None = None,
    direction_id: str | None = None,
) -> dict[str, Any]:
    if packet_kind not in PACKET_KINDS:
        raise ValueError(f"unknown packet kind: {packet_kind}")
    if not payload_ref:
        raise ValueError("payload_ref is required")
    packet_id = _new_id("pkt")
    marker = marker or f"marker:{packet_id}"
    now = _now()
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO packet_refs (
                packet_id, packet_kind, source_actor_context_id, target_actor_context_id,
                direction_id, marker, payload_ref, delivery_state, intake_state,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PREPARED', 'NOT_INTAKEN', ?, ?)""",
            (
                packet_id,
                packet_kind,
                source_actor_context_id,
                target_actor_context_id,
                direction_id,
                marker,
                payload_ref,
                now,
                now,
            ),
        )
        target_workflow = store.current_actor_workflow(target_actor_context_id)
        if target_workflow is not None:
            store._insert_obligation(
                store.connection,
                str(target_workflow["workflow_id"]),
                ObligationKind.PACKET_INTAKE_REQUIRED,
                target_actor_context_id,
                packet_id,
                "A typed packet requires target-local intake.",
                packet_id,
                owner_actor_context_id=target_actor_context_id,
                source_actor_context_id=source_actor_context_id,
            )
            store._touch_workflow(str(target_workflow["workflow_id"]))
        row = store.connection.execute(
            "SELECT * FROM packet_refs WHERE packet_id = ?", (packet_id,)
        ).fetchone()
        return _row(row)


def _set_delivery(store: SemanticStore, packet_id: str, state: str) -> dict[str, Any]:
    if state not in DELIVERY_STATES:
        raise ValueError(f"unknown delivery state: {state}")
    with store._lock, store.connection:
        store.connection.execute(
            "UPDATE packet_refs SET delivery_state = ?, updated_at = ? WHERE packet_id = ?",
            (state, _now(), packet_id),
        )
        row = store.connection.execute(
            "SELECT * FROM packet_refs WHERE packet_id = ?", (packet_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown packet: {packet_id}")
        return _row(row)


def packet_mark_delivery(store: SemanticStore, packet_id: str, state: str) -> dict[str, Any]:
    return _set_delivery(store, packet_id, state)


def packet_acknowledge(store: SemanticStore, packet_id: str) -> dict[str, Any]:
    return _set_delivery(store, packet_id, "ACKNOWLEDGED")


def _set_intake(store: SemanticStore, packet_id: str, state: str) -> dict[str, Any]:
    if state not in INTAKE_STATES:
        raise ValueError(f"unknown intake state: {state}")
    with store._lock, store.connection:
        store.connection.execute(
            "UPDATE packet_refs SET intake_state = ?, updated_at = ? WHERE packet_id = ?",
            (state, _now(), packet_id),
        )
        row = store.connection.execute(
            "SELECT * FROM packet_refs WHERE packet_id = ?", (packet_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown packet: {packet_id}")
        return _row(row)


def packet_mark_intaken(store: SemanticStore, packet_id: str) -> dict[str, Any]:
    return _set_intake(store, packet_id, "INTAKEN")


def packet_mark_applied(store: SemanticStore, packet_id: str, decision_ref: str | None = None) -> dict[str, Any]:
    with store._lock, store.connection:
        store.connection.execute(
            """UPDATE packet_refs
            SET intake_state = 'APPLIED', decision_ref = COALESCE(?, decision_ref), updated_at = ?
            WHERE packet_id = ?""",
            (decision_ref, _now(), packet_id),
        )
        row = store.connection.execute(
            "SELECT * FROM packet_refs WHERE packet_id = ?", (packet_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown packet: {packet_id}")
        return _row(row)
