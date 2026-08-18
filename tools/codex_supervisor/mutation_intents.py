"""Durable intents for mutating App Server requests. Never blind-retry."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .store import ObserverStore

OPEN_STATES = frozenset({"SUBMITTING", "SUBMISSION_UNCERTAIN"})


class MutationIntentError(RuntimeError):
    """Raised when a mutating request cannot start or must not be resent."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MutationIntentStore:
    def __init__(self, store: ObserverStore) -> None:
        self.store = store

    def get_open(self, method: str, client_key: str) -> dict[str, Any] | None:
        row = self.store.connection.execute(
            """SELECT * FROM mutation_intents
            WHERE method = ? AND client_key = ? AND state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN')
            ORDER BY created_at DESC""",
            (method, client_key),
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

    def set_state(self, intent_id: str, state: str, **fields: Any) -> dict[str, Any]:
        assignments = ["state = ?", "updated_at = ?"]
        values: list[object] = [state, _now()]
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            values.append(value)
        values.append(intent_id)
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                f"UPDATE mutation_intents SET {', '.join(assignments)} WHERE intent_id = ?",
                values,
            )
        row = self.store.connection.execute(
            "SELECT * FROM mutation_intents WHERE intent_id = ?",
            (intent_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def mark_uncertain(self, intent_id: str, reason: str) -> dict[str, Any]:
        return self.set_state(intent_id, "SUBMISSION_UNCERTAIN", request_json=json.dumps({"reason": reason}))

    def mark_submitted(self, intent_id: str) -> dict[str, Any]:
        return self.set_state(intent_id, "SUBMITTED")

    def mark_incident(self, intent_id: str, reason: str) -> dict[str, Any]:
        return self.set_state(intent_id, "INCIDENT", request_json=json.dumps({"reason": reason}))
