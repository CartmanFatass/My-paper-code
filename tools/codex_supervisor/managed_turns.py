"""Operator-explicit managed turns. No Stage 3 service loop submits these."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired, UnexpectedServerRequest
from .durability.effects import EffectJournal
from .durability.models import AggregateKind, TransitionCause, TransitionRequest
from .durability.session_owner import AppServerSessionOwner
from .durability.transaction import DurabilityTransaction
from .durability.transitions import TransitionError, TransitionKernel
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
        self.journal = EffectJournal(bindings.store.connection)
        self.kernel = TransitionKernel(bindings.store.connection)

    def _owner(self) -> AppServerSessionOwner:
        return AppServerSessionOwner.for_client(self.client, self.bindings.store)

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
        effect = self.journal.prepare_effect(
            owner_kind="MANAGED_TURN",
            owner_id=intent_id,
            binding_id=binding_id,
            method="turn/start",
            client_key=message_id,
            request={"threadId": binding.thread_id, "clientUserMessageId": message_id},
        )
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                """INSERT INTO managed_turn_intents (
                    turn_intent_id, binding_id, intent_kind, client_user_message_id,
                    checkpoint_id, expected_state_version, expected_epoch_id,
                    expected_epoch_revision, input_ref, submission_state,
                    app_server_thread_id, prepared_at, version, effect_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
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
                    effect.effect_id,
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

    def _apply(self, request: TransitionRequest) -> None:
        try:
            with DurabilityTransaction(self.bindings.store.connection):
                self.kernel.apply(request)
        except TransitionError as exc:
            raise ManagedTurnError(str(exc)) from exc

    async def submit(self, turn_intent_id: str, input_text: str) -> dict[str, Any]:
        import asyncio

        row = self._row(turn_intent_id)
        if row["submission_state"] != SubmissionState.PREPARED.value:
            raise ManagedTurnError("intent is not PREPARED; reconcile, do not resend")
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        effect_id = str(row["effect_id"] or "")
        if not effect_id:
            raise ManagedTurnError("managed turn has no linked effect")
        params = {
            "threadId": row["app_server_thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": row["client_user_message_id"],
        }
        existing = self.journal.get(effect_id)
        if existing.state != "PREPARED":
            raise ManagedTurnError("linked effect is not PREPARED; reconcile, do not resend")
        if dict(existing.request) != {"threadId": row["app_server_thread_id"], "clientUserMessageId": row["client_user_message_id"]}:
            raise ManagedTurnError("linked effect request tuple mismatch")
        self.bindings.store.connection.execute(
            "UPDATE app_server_effects SET request_json = ? WHERE effect_id = ? AND state = 'PREPARED'",
            (json.dumps(params, sort_keys=True, separators=(",", ":")), effect_id),
        )
        owner = self._owner()
        try:
            result = await owner.submit_effect(
                effect_id,
                extra_transitions=[
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.PREPARED.value,
                        expected_version=int(row["version"] or 0),
                        target_state=SubmissionState.SUBMITTING.value,
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref=effect_id,
                    )
                ],
            )
        except RetryRequired as exc:
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTING.value,
                    expected_version=int(self._row(turn_intent_id)["version"] or 0),
                    target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                    cause_kind=TransitionCause.RECONCILIATION,
                    cause_ref="overload",
                    field_updates={"incident_json": json.dumps({"reason": "overload"})},
                )
            )
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        except UnexpectedServerRequest as exc:
            raise ManagedTurnError("turn/start incident; do not retry") from exc
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError) as exc:
            current = self._row(turn_intent_id)
            if current["submission_state"] != SubmissionState.INCIDENT.value:
                self._apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=str(current["submission_state"]),
                        expected_version=int(current["version"] or 0),
                        target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=type(exc).__name__,
                        field_updates={"incident_json": json.dumps({"reason": type(exc).__name__})},
                    )
                )
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        current = self._row(turn_intent_id)
        if current["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("turn/start incident; do not retry")
        response = result.response or {}
        turn_id = None
        inner = response.get("result") if isinstance(response.get("result"), dict) else {}
        if isinstance(inner.get("turn"), dict):
            turn_id = inner["turn"].get("id")
        now = _now()
        try:
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTING.value,
                    expected_version=int(current["version"] or 0),
                    target_state=SubmissionState.SUBMITTED.value,
                    cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                    cause_ref=effect_id,
                    field_updates={
                        "app_server_turn_id": turn_id,
                        "submitted_at": now,
                        "observed_at": now,
                    },
                )
            )
        except ManagedTurnError:
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
        return self._row(turn_intent_id)

    async def reconcile_uncertain(self, turn_intent_id: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        if row["submission_state"] not in {
            SubmissionState.SUBMISSION_UNCERTAIN.value,
            SubmissionState.SUBMITTING.value,
            SubmissionState.SUBMITTED.value,
        }:
            return row
        owner = self._owner()
        read = await owner.request_read(
            "thread/read",
            {"threadId": str(row["app_server_thread_id"]), "includeTurns": True},
        )
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        thread = read.get("result") if isinstance(read.get("result"), dict) else read
        thread_obj = thread.get("thread") if isinstance(thread.get("thread"), dict) else thread
        turns = thread_obj.get("turns") if isinstance(thread_obj.get("turns"), list) else []
        wanted = row["client_user_message_id"]
        for turn in turns:
            if isinstance(turn, dict) and turn.get("clientUserMessageId") == wanted:
                effect_id = row.get("effect_id")
                if effect_id:
                    try:
                        self.journal.confirm_effect(str(effect_id), evidence_ref=f"turn:{turn.get('id')}")
                    except Exception:
                        pass
                try:
                    self._apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MANAGED_TURN,
                            aggregate_id=turn_intent_id,
                            expected_state=str(row["submission_state"]),
                            expected_version=int(row["version"] or 0),
                            target_state=SubmissionState.OBSERVED.value,
                            cause_kind=TransitionCause.RECONCILIATION,
                            cause_ref=str(turn.get("id") or wanted),
                            evidence_ref=str(turn.get("id") or ""),
                            field_updates={
                                "app_server_turn_id": turn.get("id"),
                                "observed_at": _now(),
                            },
                        )
                    )
                except ManagedTurnError:
                    row = self._row(turn_intent_id)
                    if row["submission_state"] == SubmissionState.INCIDENT.value:
                        raise ManagedTurnError("incident is terminal; operator recovery required")
                    return row
                return self._row(turn_intent_id)
        return row

    def record_completion(self, turn_intent_id: str, status: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        now = _now()
        if row["submission_state"] == SubmissionState.SUBMITTED.value:
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTED.value,
                    expected_version=int(row["version"] or 0),
                    target_state=SubmissionState.OBSERVED.value,
                    cause_kind=TransitionCause.RECONCILIATION,
                    cause_ref=str(row.get("app_server_turn_id") or turn_intent_id),
                    field_updates={"observed_at": now},
                )
            )
            row = self._row(turn_intent_id)
        try:
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=str(row["submission_state"]),
                    expected_version=int(row["version"] or 0),
                    target_state=SubmissionState.COMPLETED.value,
                    cause_kind=TransitionCause.APP_SERVER_EVENT,
                    cause_ref=status,
                    field_updates={"completion_status": status, "completed_at": now},
                )
            )
        except ManagedTurnError as exc:
            row = self._row(turn_intent_id)
            if row["submission_state"] == SubmissionState.INCIDENT.value:
                raise ManagedTurnError("incident is terminal; operator recovery required")
            raise ManagedTurnError("only OBSERVED turns may complete") from exc
        return self._row(turn_intent_id)
