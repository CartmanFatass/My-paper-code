"""Deterministic read-only inspection of the local supervisor runtime."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReadOnlyRuntime:
    def __init__(self, runtime_home: Path) -> None:
        database = (Path(runtime_home) / "state.sqlite3").resolve(strict=True)
        self.connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA query_only = ON")

    def __enter__(self) -> "ReadOnlyRuntime":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.connection.close()


def _row(row: Any) -> dict[str, object] | None:
    return None if row is None else dict(row)


def _json(value: object) -> object:
    if not isinstance(value, str) or not value:
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _operation(row: Any) -> dict[str, object] | None:
    if row is None:
        return None
    result = dict(row)
    wire = result.pop("wire_bytes", b"")
    result["wire_byte_length"] = len(wire)
    return result


def inspect_actor(store: Any, actor_context_id: str) -> dict[str, object]:
    bindings = [
        dict(row)
        for row in store.connection.execute(
            "SELECT * FROM managed_actor_bindings WHERE actor_context_id = ? ORDER BY binding_id",
            (actor_context_id,),
        ).fetchall()
    ]
    messages = store.connection.execute(
        """SELECT delivery_state, COUNT(*) AS count FROM mailbox_messages
        WHERE target_actor_context_id = ? GROUP BY delivery_state ORDER BY delivery_state""",
        (actor_context_id,),
    ).fetchall()
    return {
        "actor_context_id": actor_context_id,
        "bindings": bindings,
        "mailbox_by_state": {str(row[0]): int(row[1]) for row in messages},
    }


def inspect_binding(store: Any, binding_id: str) -> dict[str, object]:
    binding = _row(store.connection.execute(
        "SELECT * FROM managed_actor_bindings WHERE binding_id = ?", (binding_id,)
    ).fetchone())
    batches = [dict(row) for row in store.connection.execute(
        "SELECT * FROM wake_batches WHERE binding_id = ? ORDER BY prepared_at, wake_batch_id",
        (binding_id,),
    ).fetchall()]
    operations = [_operation(row) for row in store.connection.execute(
        "SELECT * FROM app_server_outbox WHERE binding_id = ? ORDER BY created_at, operation_id",
        (binding_id,),
    ).fetchall()]
    return {"binding_id": binding_id, "binding": binding, "wake_batches": batches, "operations": operations}


def inspect_thread(store: Any, thread_id: str) -> dict[str, object]:
    return {
        "thread_id": thread_id,
        "snapshot": _row(store.connection.execute(
            "SELECT * FROM thread_snapshots WHERE thread_id = ?", (thread_id,)
        ).fetchone()),
        "binding": _row(store.connection.execute(
            "SELECT * FROM managed_actor_bindings WHERE thread_id = ?", (thread_id,)
        ).fetchone()),
        "wake_batches": [dict(row) for row in store.connection.execute(
            "SELECT * FROM wake_batches WHERE thread_id = ? ORDER BY prepared_at, wake_batch_id",
            (thread_id,),
        ).fetchall()],
    }


def inspect_effect(store: Any, effect_id: str) -> dict[str, object]:
    current = _operation(store.connection.execute(
        "SELECT * FROM app_server_outbox WHERE operation_id = ?", (effect_id,)
    ).fetchone())
    legacy = _row(store.connection.execute(
        "SELECT * FROM app_server_effects WHERE effect_id = ?", (effect_id,)
    ).fetchone())
    return {"effect_id": effect_id, "operation": current, "legacy_effect": legacy}


def inspect_incident(store: Any, incident_id: str) -> dict[str, object]:
    records: list[dict[str, object]] = []
    operation = store.connection.execute(
        """SELECT * FROM app_server_outbox WHERE operation_id = ?
        AND (state = 'UNKNOWN' OR error IS NOT NULL)""",
        (incident_id,),
    ).fetchone()
    if operation is not None:
        records.append({"kind": "operation", "value": _operation(operation)})
    for kind, table, key in (
        ("wake_batch", "wake_batches", "wake_batch_id"),
        ("managed_turn", "managed_turn_intents", "turn_intent_id"),
    ):
        row = store.connection.execute(
            f"SELECT * FROM {table} WHERE {key} = ? AND incident_json IS NOT NULL",
            (incident_id,),
        ).fetchone()
        if row is not None:
            value = dict(row)
            value["incident_json"] = _json(value.get("incident_json"))
            records.append({"kind": kind, "value": value})
    request = store.connection.execute(
        "SELECT * FROM server_requests WHERE server_request_row_id = ? OR server_request_id = ?",
        (incident_id, incident_id),
    ).fetchone()
    if request is not None:
        records.append({"kind": "server_request", "value": dict(request)})
    return {"incident_id": incident_id, "records": records}


def explain_why_not_wake(
    store: Any, binding_id: str, *, single_wake_state: str | None = None
) -> dict[str, object]:
    reasons: list[str] = []
    binding = store.connection.execute(
        "SELECT * FROM managed_actor_bindings WHERE binding_id = ?", (binding_id,)
    ).fetchone()
    if binding is None or str(binding["binding_state"]) != "ACTIVE":
        reasons.append("binding_not_active")
    if binding is not None and str(binding["actor_kind"]) not in {"OPERATIONAL_ROOT", "PORTFOLIO"}:
        reasons.append("semantic_actor_not_eligible")
    thread_id = None if binding is None else binding["thread_id"]
    snapshot = None if not thread_id else store.connection.execute(
        "SELECT status_type FROM thread_snapshots WHERE thread_id = ?", (thread_id,)
    ).fetchone()
    status = None if snapshot is None else snapshot[0]
    if not thread_id or status is None:
        reasons.append("unknown_readiness")
    elif str(status) not in {"idle", "notLoaded"}:
        reasons.append("thread_not_idle")
    open_batch = store.connection.execute(
        """SELECT 1 FROM wake_batches WHERE binding_id = ?
        AND state IN ('PREPARED','SUBMITTING','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE') LIMIT 1""",
        (binding_id,),
    ).fetchone()
    if open_batch is not None:
        reasons.append("open_batch_exists")
    actor_id = None if binding is None else binding["actor_context_id"]
    mailbox_count = 0 if actor_id is None else int(store.connection.execute(
        """SELECT COUNT(*) FROM mailbox_messages WHERE target_actor_context_id = ?
        AND delivery_state IN ('ENQUEUED','ELIGIBLE')""",
        (actor_id,),
    ).fetchone()[0])
    if mailbox_count == 0:
        reasons.append("mailbox_empty")
    if single_wake_state == "UNARMED":
        reasons.append("single_wake_not_armed")
    elif single_wake_state in {"CONSUMED", "CANCELLED"}:
        reasons.append("single_wake_consumed")
    if single_wake_state == "ATTEMPTING" and store.connection.execute(
        "SELECT 1 FROM scheduler_leases WHERE lease_key = ? AND expires_at > ?",
        (f"wake:{binding_id}", datetime.now(timezone.utc).isoformat()),
    ).fetchone() is None:
        reasons.append("lease_missing")
    if store.connection.execute(
        """SELECT 1 FROM app_server_outbox WHERE binding_id = ?
        AND state IN ('SENDING','UNKNOWN') LIMIT 1""", (binding_id,)
    ).fetchone() is not None:
        reasons.append("effect_unreconciled")
    if store.connection.execute(
        """SELECT 1 FROM wake_batches WHERE binding_id = ? AND state = 'INCIDENT'
        UNION ALL SELECT 1 FROM managed_turn_intents WHERE binding_id = ? AND submission_state = 'INCIDENT'
        LIMIT 1""", (binding_id, binding_id)
    ).fetchone() is not None:
        reasons.append("incident_requires_operator")
    return {
        "binding_id": binding_id,
        "reasons": reasons,
        "facts": {"thread_id": thread_id, "recorded_thread_status": status, "mailbox_candidate_count": mailbox_count},
    }
