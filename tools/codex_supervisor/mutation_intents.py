"""Durable intents for mutating App Server requests. Never blind-retry."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .store import ObserverStore

OPEN_STATES = frozenset({"SUBMITTING", "SUBMISSION_UNCERTAIN", "SUBMITTED_UNRECONCILED"})
UNRESOLVED_INCIDENT = "INCIDENT"
OPERATOR_RESOLVED = "OPERATOR_RESOLVED"
SUBMITTED_UNRECONCILED = "SUBMITTED_UNRECONCILED"


class MutationIntentError(RuntimeError):
    """Raised when a mutating request cannot start or must not be resent."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MutationIntentStore:
    def __init__(self, store: ObserverStore) -> None:
        self.store = store

    def get(self, intent_id: str) -> dict[str, Any] | None:
        row = self.store.connection.execute(
            "SELECT * FROM mutation_intents WHERE intent_id = ?",
            (intent_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_open(self, method: str, client_key: str) -> dict[str, Any] | None:
        row = self.store.connection.execute(
            """SELECT * FROM mutation_intents
            WHERE method = ? AND client_key = ? AND state IN (?, ?, ?)
            ORDER BY created_at DESC""",
            (method, client_key, "SUBMITTING", "SUBMISSION_UNCERTAIN", SUBMITTED_UNRECONCILED),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_unresolved_incident(self, method: str, client_key: str) -> dict[str, Any] | None:
        row = self.store.connection.execute(
            """SELECT * FROM mutation_intents
            WHERE method = ? AND client_key = ? AND state = ?
            ORDER BY created_at DESC""",
            (method, client_key, UNRESOLVED_INCIDENT),
        ).fetchone()
        return dict(row) if row is not None else None

    def begin(
        self,
        method: str,
        client_key: str,
        *,
        binding_id: str | None = None,
        request: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self.get_open(method, client_key)
        if existing is not None:
            raise MutationIntentError(
                f"{method} already has an unresolved intent; reconcile, do not resend"
            )
        incident = self.get_unresolved_incident(method, client_key)
        if incident is not None:
            raise MutationIntentError(
                f"{method} has an unresolved INCIDENT; operator resolution required"
            )
        intent_id = f"mut_{uuid.uuid4().hex}"
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """INSERT INTO mutation_intents (
                    intent_id, method, binding_id, client_key, state, request_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'SUBMITTING', ?, ?, ?)""",
                (
                    intent_id,
                    method,
                    binding_id,
                    client_key,
                    None if request is None else json.dumps(request),
                    now,
                    now,
                ),
            )
        row = self.store.connection.execute(
            "SELECT * FROM mutation_intents WHERE intent_id = ?",
            (intent_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def set_state(
        self,
        intent_id: str,
        state: str,
        *,
        expected_state: str | None = None,
        expected_states: frozenset[str] | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        current = self.get(intent_id)
        if current is None:
            raise MutationIntentError(f"unknown mutation intent: {intent_id}")
        if str(current["state"]) == UNRESOLVED_INCIDENT and state != OPERATOR_RESOLVED:
            raise MutationIntentError("incident is terminal; operator recovery required")
        assignments = ["state = ?", "updated_at = ?"]
        values: list[object] = [state, _now()]
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            values.append(value)
        values.append(intent_id)
        sql = f"UPDATE mutation_intents SET {', '.join(assignments)} WHERE intent_id = ?"
        allowed = expected_states
        if expected_state is not None:
            allowed = frozenset({expected_state}) if allowed is None else allowed | {expected_state}
        if allowed is not None:
            sql += " AND state IN (" + ", ".join("?" for _ in allowed) + ")"
            values.extend(sorted(allowed))
        with self.store._lock, self.store.connection:
            cursor = self.store.connection.execute(sql, values)
            if cursor.rowcount != 1:
                latest = self.get(intent_id)
                if latest is not None and str(latest["state"]) == UNRESOLVED_INCIDENT:
                    raise MutationIntentError("incident is terminal; operator recovery required")
                raise MutationIntentError("invalid mutation intent transition")
        row = self.get(intent_id)
        assert row is not None
        return row

    def mark_uncertain(self, intent_id: str, reason: str) -> dict[str, Any]:
        return self.set_state(
            intent_id,
            "SUBMISSION_UNCERTAIN",
            expected_state="SUBMITTING",
            request_json=json.dumps({"reason": reason}),
        )

    def mark_submitted(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(intent_id, "SUBMITTED", expected_state="SUBMITTING")

    def mark_submitted_unreconciled(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(intent_id, SUBMITTED_UNRECONCILED, expected_state="SUBMITTING")

    def mark_applied(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(intent_id, "APPLIED", expected_state="SUBMITTING")

    def mark_applied_reconciled(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(intent_id, "APPLIED", expected_state=SUBMITTED_UNRECONCILED)

    def mark_applied_after_loaded_observation(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(
            intent_id,
            "APPLIED",
            expected_states=frozenset({"SUBMISSION_UNCERTAIN", SUBMITTED_UNRECONCILED}),
        )

    def mark_incident(self, intent_id: str, reason: str) -> dict[str, Any]:
        return self.set_state(
            intent_id,
            UNRESOLVED_INCIDENT,
            expected_states=OPEN_STATES | frozenset({"SUBMITTED"}),
            request_json=json.dumps({"reason": reason}),
        )

    def resolve_incident(self, intent_id: str, *, operator: str) -> dict[str, Any]:
        if not operator:
            raise MutationIntentError("operator identity is required to resolve an incident")
        return self.set_state(
            intent_id,
            OPERATOR_RESOLVED,
            expected_state=UNRESOLVED_INCIDENT,
            request_json=json.dumps({"reason": "operator_resolved", "operator": operator}),
        )
