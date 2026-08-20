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
        raise MutationIntentError(
            "new mutation_intents writes are disabled; use AppServerSessionOwner.submit_effect"
        )

    def set_state(
        self,
        intent_id: str,
        state: str,
        *,
        expected_state: str | None = None,
        expected_states: frozenset[str] | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        raise MutationIntentError("mutation_intents rows are read-only legacy evidence")

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
