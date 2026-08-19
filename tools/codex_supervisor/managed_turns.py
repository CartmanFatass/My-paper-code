"""Operator-explicit managed turns. No Stage 3 service loop submits these."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired, UnexpectedServerRequest
from .managed_models import BindingState, ManagedIntentKind, SubmissionState
from .mutation_intents import MutationIntentStore
from .session_guard import SessionGuard
from .transport import TransportClosed

STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP = True


def client_user_message_id(turn_intent_id: str) -> str:
    return f"hmasd-managed:{turn_intent_id}"


class ManagedTurnError(RuntimeError):
    """Raised when a managed turn cannot be prepared or submitted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ManagedTurns:
    def __init__(self, bindings: BindingStore, client: AppServerClient) -> None:
        self.bindings = bindings
        self.client = client
        self.mutations = MutationIntentStore(bindings.store)

    def prepare(
        self,
        binding_id: str,
        *,
        intent_kind: ManagedIntentKind,
        input_ref: str,
        checkpoint_id: str | None = None,
        expected_state_version: int | None = None,
        expected_epoch_id: str | None = None,
        expected_epoch_revision: int | None = None,
    ) -> str:
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id:
            raise ManagedTurnError("binding has no thread")
        if intent_kind in {ManagedIntentKind.BOOTSTRAP, ManagedIntentKind.IDENTITY_VERIFICATION}:
            if binding.binding_state is not BindingState.VERIFICATION_REQUIRED:
                raise ManagedTurnError("bootstrap requires VERIFICATION_REQUIRED")
        elif binding.binding_state is not BindingState.ACTIVE:
            raise ManagedTurnError("manual turn requires ACTIVE binding")
        intent_id = f"intent_{uuid.uuid4().hex}"
        message_id = client_user_message_id(intent_id)
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                """INSERT INTO managed_turn_intents (
                    turn_intent_id, binding_id, intent_kind, client_user_message_id,
                    checkpoint_id, expected_state_version, expected_epoch_id,
                    expected_epoch_revision, input_ref, submission_state,
                    app_server_thread_id, prepared_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    intent_id,
                    binding_id,
                    intent_kind.value,
                    message_id,
                    checkpoint_id,
                    expected_state_version,
                    expected_epoch_id,
                    expected_epoch_revision,
                    input_ref,
                    SubmissionState.PREPARED.value,
                    binding.thread_id,
                    _now(),
                ),
            )
        return intent_id

    def _row(self, turn_intent_id: str) -> dict[str, Any]:
        row = self.bindings.store.connection.execute(
            "SELECT * FROM managed_turn_intents WHERE turn_intent_id = ?",
            (turn_intent_id,),
        ).fetchone()
        if row is None:
            raise ManagedTurnError(f"unknown turn intent: {turn_intent_id}")
        return dict(row)

    def _set_state(self, turn_intent_id: str, **fields: Any) -> bool:
        expected = fields.pop("expected_state", None)
        expected_states = fields.pop("expected_states", None)
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [turn_intent_id]
        sql = f"UPDATE managed_turn_intents SET {assignments} WHERE turn_intent_id = ?"
        allowed = expected_states
        if expected is not None:
            allowed = frozenset({expected}) if allowed is None else set(allowed) | {expected}
        if allowed is not None:
            sql += " AND submission_state IN (" + ", ".join("?" for _ in allowed) + ")"
            values.extend(sorted(allowed))
        with self.bindings.store._lock, self.bindings.store.connection:
            cursor = self.bindings.store.connection.execute(sql, values)
            return cursor.rowcount == 1

    def _refuse_incident_mutation(self, client_key: str) -> None:
        if self.mutations.get_unresolved_incident("turn/start", client_key) is not None:
            raise ManagedTurnError("incident is terminal; operator recovery required")

    def _claim_prepared(self, turn_intent_id: str) -> bool:
        with self.bindings.store._lock, self.bindings.store.connection:
            cursor = self.bindings.store.connection.execute(
                """UPDATE managed_turn_intents
                SET submission_state = ?
                WHERE turn_intent_id = ? AND submission_state = ?""",
                (
                    SubmissionState.SUBMITTING.value,
                    turn_intent_id,
                    SubmissionState.PREPARED.value,
                ),
            )
            return cursor.rowcount == 1

    async def submit(self, turn_intent_id: str, input_text: str) -> dict[str, Any]:
        import asyncio

        row = self._row(turn_intent_id)
        if row["submission_state"] != SubmissionState.PREPARED.value:
            raise ManagedTurnError("intent is not PREPARED; reconcile, do not resend")
        self.mutations.begin(
            "turn/start",
            str(row["client_user_message_id"]),
            binding_id=str(row["binding_id"]),
            request={"turn_intent_id": turn_intent_id},
        )
        if not self._claim_prepared(turn_intent_id):
            raise ManagedTurnError("intent is not PREPARED; reconcile, do not resend")
        params = {
            "threadId": row["app_server_thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": row["client_user_message_id"],
        }

        def _incident(_payload: object) -> None:
            self._set_state(
                turn_intent_id,
                submission_state=SubmissionState.INCIDENT.value,
                incident_json=json.dumps({"reason": "server_request"}),
            )
            open_intent = self.mutations.get_open("turn/start", str(row["client_user_message_id"]))
            if open_intent is not None:
                try:
                    self.mutations.mark_incident(str(open_intent["intent_id"]), "server_request")
                except Exception:
                    pass

        guard = SessionGuard(self.client, self.bindings.store, on_incident=_incident)
        try:
            response = await guard.request("turn/start", params)
        except RetryRequired as exc:
            self._set_state(
                turn_intent_id,
                submission_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                incident_json=json.dumps({"reason": "overload"}),
            )
            open_intent = self.mutations.get_open("turn/start", str(row["client_user_message_id"]))
            if open_intent is not None:
                try:
                    self.mutations.mark_uncertain(str(open_intent["intent_id"]), "overload")
                except Exception:
                    pass
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        except UnexpectedServerRequest as exc:
            raise ManagedTurnError("turn/start incident; do not retry") from exc
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError) as exc:
            self._set_state(
                turn_intent_id,
                submission_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                incident_json=json.dumps({"reason": type(exc).__name__}),
            )
            open_intent = self.mutations.get_open("turn/start", str(row["client_user_message_id"]))
            if open_intent is not None:
                try:
                    self.mutations.mark_uncertain(str(open_intent["intent_id"]), type(exc).__name__)
                except Exception:
                    pass
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        turn_id = None
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        if isinstance(result.get("turn"), dict):
            turn_id = result["turn"].get("id")
        now = _now()
        applied = self._set_state(
            turn_intent_id,
            submission_state=SubmissionState.SUBMITTED.value,
            app_server_turn_id=turn_id,
            submitted_at=now,
            observed_at=now,
            expected_state=SubmissionState.SUBMITTING.value,
        )
        if not applied:
            row = self._row(turn_intent_id)
            if row["submission_state"] == SubmissionState.INCIDENT.value:
                raise ManagedTurnError("turn/start incident; do not retry")
            return row
        if turn_id:
            with self.bindings.store._lock, self.bindings.store.connection:
                self.bindings.store.connection.execute(
                    "UPDATE managed_actor_bindings SET last_turn_id = ? WHERE binding_id = ?",
                    (turn_id, row["binding_id"]),
                )
        open_intent = self.mutations.get_open("turn/start", str(row["client_user_message_id"]))
        if open_intent is not None:
            try:
                self.mutations.mark_submitted(str(open_intent["intent_id"]))
            except Exception:
                row = self._row(turn_intent_id)
                if row["submission_state"] == SubmissionState.INCIDENT.value:
                    raise ManagedTurnError("turn/start incident; do not retry")
        return self._row(turn_intent_id)

    async def reconcile_uncertain(self, turn_intent_id: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        if row["submission_state"] not in {
            SubmissionState.SUBMISSION_UNCERTAIN.value,
            SubmissionState.SUBMITTING.value,
        }:
            return row
        client_key = str(row["client_user_message_id"])
        self._refuse_incident_mutation(client_key)
        read = await self.client.read_thread(str(row["app_server_thread_id"]), include_turns=True)
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        self._refuse_incident_mutation(client_key)
        if row["submission_state"] not in {
            SubmissionState.SUBMISSION_UNCERTAIN.value,
            SubmissionState.SUBMITTING.value,
        }:
            return row
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        turns = thread.get("turns") if isinstance(thread.get("turns"), list) else []
        wanted = row["client_user_message_id"]
        for turn in turns:
            if isinstance(turn, dict) and turn.get("clientUserMessageId") == wanted:
                applied = self._set_state(
                    turn_intent_id,
                    submission_state=SubmissionState.OBSERVED.value,
                    app_server_turn_id=turn.get("id"),
                    observed_at=_now(),
                    expected_states={
                        SubmissionState.SUBMISSION_UNCERTAIN.value,
                        SubmissionState.SUBMITTING.value,
                    },
                )
                if not applied:
                    row = self._row(turn_intent_id)
                    if row["submission_state"] == SubmissionState.INCIDENT.value:
                        raise ManagedTurnError("incident is terminal; operator recovery required")
                    return row
                return self._row(turn_intent_id)
        return row

    def record_completion(self, turn_intent_id: str, status: str) -> dict[str, Any]:
        now = _now()
        with self.bindings.store._lock, self.bindings.store.connection:
            cursor = self.bindings.store.connection.execute(
                """UPDATE managed_turn_intents
                SET submission_state = ?, completion_status = ?, completed_at = ?
                WHERE turn_intent_id = ? AND submission_state IN (?, ?)""",
                (
                    SubmissionState.COMPLETED.value,
                    status,
                    now,
                    turn_intent_id,
                    SubmissionState.SUBMITTED.value,
                    SubmissionState.OBSERVED.value,
                ),
            )
            if cursor.rowcount != 1:
                row = self._row(turn_intent_id)
                if row["submission_state"] == SubmissionState.INCIDENT.value:
                    raise ManagedTurnError("incident is terminal; operator recovery required")
                raise ManagedTurnError(
                    "only SUBMITTED or OBSERVED turns may complete"
                )
        return self._row(turn_intent_id)
