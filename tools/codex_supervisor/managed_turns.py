"""Operator-explicit managed turns on the durable at-most-once outbox."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient
from .durability.models import AggregateKind, TransitionCause, TransitionRequest
from .durability.outbox import AppServerOutbox, MutationSpec, OperationState
from .durability.session_owner import AppServerSessionOwner
from .durability.transaction import DurabilityTransaction
from .durability.transitions import TransitionError, TransitionKernel
from .managed_models import BindingState, ManagedIntentKind, SubmissionState
from .semantic_bridge import SemanticBridgeError

STAGE3_HAS_NO_AUTOMATIC_TURN_LOOP = True


def client_user_message_id(turn_intent_id: str) -> str:
    return f"hmasd-managed:{turn_intent_id}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ManagedTurnError(RuntimeError):
    pass


class ManagedTurns:
    def __init__(self, bindings: BindingStore, client: AppServerClient) -> None:
        self.bindings = bindings
        self.client = client
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
        verification = intent_kind in {
            ManagedIntentKind.BOOTSTRAP,
            ManagedIntentKind.IDENTITY_VERIFICATION,
        }
        required = BindingState.VERIFICATION_REQUIRED if verification else BindingState.ACTIVE
        if binding.binding_state is not required:
            raise ManagedTurnError(f"managed turn requires {required.value}")
        bridge = getattr(self.bindings, "bridge", None)
        if bridge is not None and expected_state_version is None:
            snapshot = bridge.snapshot(binding.actor_context_id)
            checkpoint_id = snapshot.checkpoint_id
            expected_state_version = snapshot.state_version
            expected_epoch_id = snapshot.epoch_id
            expected_epoch_revision = snapshot.epoch_revision
        intent_id = f"intent_{uuid.uuid4().hex}"
        message_id = client_user_message_id(intent_id)
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            self.bindings.store.connection.execute(
                """INSERT INTO managed_turn_intents (
                    turn_intent_id, binding_id, intent_kind, client_user_message_id,
                    checkpoint_id, expected_state_version, expected_epoch_id,
                    expected_epoch_revision, input_ref, submission_state,
                    app_server_thread_id, prepared_at, version, effect_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PREPARED', ?, ?, 0, NULL)""",
                (
                    intent_id, binding_id, intent_kind.value, message_id,
                    checkpoint_id, expected_state_version, expected_epoch_id,
                    expected_epoch_revision, input_ref, binding.thread_id, _now(),
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

    def _validate_once(self, row: dict[str, Any]) -> Any:
        binding = self.bindings.get(str(row["binding_id"]))
        intent_kind = ManagedIntentKind(str(row["intent_kind"]))
        required = (
            BindingState.VERIFICATION_REQUIRED
            if intent_kind in {ManagedIntentKind.BOOTSTRAP, ManagedIntentKind.IDENTITY_VERIFICATION}
            else BindingState.ACTIVE
        )
        if binding is None or binding.binding_state is not required:
            raise ManagedTurnError("binding is not eligible for this managed turn")
        bridge = getattr(self.bindings, "bridge", None)
        if bridge is None:
            return binding
        try:
            snapshot = bridge.snapshot(binding.actor_context_id)
        except SemanticBridgeError as exc:
            raise ManagedTurnError(str(exc)) from exc
        expected = (
            row["checkpoint_id"],
            None if row["expected_state_version"] is None else int(row["expected_state_version"]),
            row["expected_epoch_id"],
            None if row["expected_epoch_revision"] is None else int(row["expected_epoch_revision"]),
        )
        actual = (
            snapshot.checkpoint_id, snapshot.state_version,
            snapshot.epoch_id, snapshot.epoch_revision,
        )
        if (
            actual != expected
            or snapshot.actor_kind != binding.actor_kind.value
            or snapshot.scope_key != binding.semantic_scope_key
        ):
            raise ManagedTurnError("semantic currentness no longer matches managed turn")
        return binding

    async def submit(self, turn_intent_id: str, input_text: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] != SubmissionState.PREPARED.value:
            raise ManagedTurnError("intent is not PREPARED; reconcile, do not resend")
        binding = self._validate_once(row)
        params = {
            "threadId": row["app_server_thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": row["client_user_message_id"],
        }
        owner = self._owner()
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            operation = owner.enqueue_mutation(
                MutationSpec(
                    dedupe_key=f"managed-turn:{turn_intent_id}",
                    protocol_session_id=owner.protocol_session_id,
                    run_id=owner.protocol_session_id,
                    method="turn/start",
                    params=params,
                    target=f"binding:{binding.binding_id}",
                    thread_id=str(row["app_server_thread_id"]),
                    binding_id=binding.binding_id,
                )
            )
            self.bindings.store.connection.execute(
                "UPDATE managed_turn_intents SET effect_id = ? WHERE turn_intent_id = ?",
                (operation.operation_id, turn_intent_id),
            )
            self.kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.PREPARED.value,
                    expected_version=int(row["version"] or 0),
                    target_state=SubmissionState.SUBMITTING.value,
                    cause_kind=TransitionCause.APP_SERVER_EFFECT,
                    cause_ref=operation.operation_id,
                )
            )
        submitted = await owner.submit(operation.operation_id)
        current = self._row(turn_intent_id)
        if submitted.state is OperationState.UNKNOWN:
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTING.value,
                    expected_version=int(current["version"] or 0),
                    target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                    cause_kind=TransitionCause.RECONCILIATION,
                    cause_ref=operation.operation_id,
                    field_updates={"incident_json": json.dumps({"reason": submitted.error})},
                )
            )
            raise ManagedTurnError("turn/start uncertain; do not retry")
        if submitted.outcome != "OK":
            self._apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTING.value,
                    expected_version=int(current["version"] or 0),
                    target_state=SubmissionState.INCIDENT.value,
                    cause_kind=TransitionCause.RECONCILIATION,
                    cause_ref=operation.operation_id,
                    field_updates={"incident_json": json.dumps({"reason": submitted.outcome})},
                )
            )
            raise ManagedTurnError("turn/start provider-rejected")
        response = submitted.response or {}
        inner = response.get("result") if isinstance(response.get("result"), dict) else {}
        turn = inner.get("turn") if isinstance(inner.get("turn"), dict) else {}
        turn_id = str(turn.get("id") or "")
        if not turn_id:
            raise ManagedTurnError("turn/start response is missing turn id; operation is DONE")
        now = _now()
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            current = self._row(turn_intent_id)
            submitted_transition = self.kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTING.value,
                    expected_version=int(current["version"] or 0),
                    target_state=SubmissionState.SUBMITTED.value,
                    cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                    cause_ref=operation.operation_id,
                    field_updates={
                        "app_server_turn_id": turn_id,
                        "submitted_at": now,
                        "observed_at": now,
                    },
                )
            )
            self.kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state=SubmissionState.SUBMITTED.value,
                    expected_version=submitted_transition.to_version,
                    target_state=SubmissionState.OBSERVED.value,
                    cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                    cause_ref=operation.operation_id,
                    field_updates={"observed_at": now},
                )
            )
            self.bindings.store.connection.execute(
                "UPDATE managed_actor_bindings SET last_turn_id = ? WHERE binding_id = ?",
                (turn_id, binding.binding_id),
            )
        return self._row(turn_intent_id)

    async def reconcile_uncertain(self, turn_intent_id: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        operation_id = str(row.get("effect_id") or "")
        if not operation_id:
            return row
        operation = AppServerOutbox(self.bindings.store.connection).get(operation_id)
        if operation.state is OperationState.UNKNOWN:
            return row
        return row

    def record_completion(self, turn_intent_id: str, status: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        operation_id = str(row.get("effect_id") or "")
        if not operation_id:
            if self.client is not None:
                raise ManagedTurnError("completion requires a linked operation")
        else:
            operation = AppServerOutbox(self.bindings.store.connection).get(operation_id)
            if operation.state is not OperationState.DONE or operation.outcome != "OK":
                raise ManagedTurnError("completion requires a successful DONE operation")
        if row["submission_state"] != SubmissionState.OBSERVED.value:
            raise ManagedTurnError("only OBSERVED turns may complete")
        self._apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.MANAGED_TURN,
                aggregate_id=turn_intent_id,
                expected_state=SubmissionState.OBSERVED.value,
                expected_version=int(row["version"] or 0),
                target_state=SubmissionState.COMPLETED.value,
                cause_kind=TransitionCause.APP_SERVER_EVENT,
                cause_ref=status,
                field_updates={"completion_status": status, "completed_at": _now()},
            )
        )
        return self._row(turn_intent_id)
