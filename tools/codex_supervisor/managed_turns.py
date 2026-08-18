"""Operator-explicit managed turns. No Stage 3 service loop submits these."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired
from .managed_models import BindingState, ManagedIntentKind, SubmissionState
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

    def _set_state(self, turn_intent_id: str, **fields: Any) -> None:
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [turn_intent_id]
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                f"UPDATE managed_turn_intents SET {assignments} WHERE turn_intent_id = ?",
                values,
            )

    async def submit(self, turn_intent_id: str, input_text: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] != SubmissionState.PREPARED.value:
            raise ManagedTurnError("intent is not PREPARED")
        params = {
            "threadId": row["app_server_thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
            "clientUserMessageId": row["client_user_message_id"],
        }
        try:
            response = await self.client.request("turn/start", params)
        except RetryRequired as exc:
            self._set_state(
                turn_intent_id,
                submission_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                incident_json=json.dumps({"reason": "overload"}),
            )
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        except (AppServerRpcError, TransportClosed) as exc:
            self._set_state(
                turn_intent_id,
                submission_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                incident_json=json.dumps({"reason": type(exc).__name__}),
            )
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        turn_id = None
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        if isinstance(result.get("turn"), dict):
            turn_id = result["turn"].get("id")
        now = _now()
        self._set_state(
            turn_intent_id,
            submission_state=SubmissionState.SUBMITTED.value,
            app_server_turn_id=turn_id,
            submitted_at=now,
            observed_at=now,
        )
        if turn_id:
            with self.bindings.store._lock, self.bindings.store.connection:
                self.bindings.store.connection.execute(
                    "UPDATE managed_actor_bindings SET last_turn_id = ? WHERE binding_id = ?",
                    (turn_id, row["binding_id"]),
                )
        return self._row(turn_intent_id)

    async def reconcile_uncertain(self, turn_intent_id: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] != SubmissionState.SUBMISSION_UNCERTAIN.value:
            return row
        read = await self.client.read_thread(str(row["app_server_thread_id"]), include_turns=True)
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        turns = thread.get("turns") if isinstance(thread.get("turns"), list) else []
        wanted = row["client_user_message_id"]
        for turn in turns:
            if isinstance(turn, dict) and turn.get("clientUserMessageId") == wanted:
                self._set_state(
                    turn_intent_id,
                    submission_state=SubmissionState.OBSERVED.value,
                    app_server_turn_id=turn.get("id"),
                    observed_at=_now(),
                )
                return self._row(turn_intent_id)
        return row

    def record_completion(self, turn_intent_id: str, status: str) -> dict[str, Any]:
        self._set_state(
            turn_intent_id,
            submission_state=SubmissionState.COMPLETED.value,
            completion_status=status,
            completed_at=_now(),
        )
        return self._row(turn_intent_id)
