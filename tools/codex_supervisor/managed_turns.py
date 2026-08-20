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
from .semantic_bridge import SemanticBridgeError
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
        with self.bindings.store._lock:
            with DurabilityTransaction(self.bindings.store.connection):
                effect = self.journal.prepare_effect(
                    owner_kind="MANAGED_TURN",
                    owner_id=intent_id,
                    binding_id=binding_id,
                    method="turn/start",
                    client_key=message_id,
                    request={"threadId": binding.thread_id, "clientUserMessageId": message_id},
                )
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

    def _cancel_prepared(self, turn_intent_id: str, effect_id: str, reason: str) -> None:
        from .durability.effects import cancel_prepared_turn

        cancel_prepared_turn(
            self.bindings.store.connection,
            turn_intent_id,
            effect_id,
            cause_ref=reason,
        )

    def _assert_submit_fence(self, turn_intent_id: str, effect_id: str) -> None:
        row = self._row(turn_intent_id)
        binding = self.bindings.get(str(row["binding_id"]))
        intent_kind = ManagedIntentKind(str(row["intent_kind"]))
        allowed = (
            BindingState.VERIFICATION_REQUIRED
            if intent_kind in {ManagedIntentKind.BOOTSTRAP, ManagedIntentKind.IDENTITY_VERIFICATION}
            else BindingState.ACTIVE
        )
        if binding is None or binding.binding_state is not allowed:
            self._cancel_prepared(turn_intent_id, effect_id, "binding_ineligible")
            raise ManagedTurnError("binding is not eligible for this managed turn")
        bridge = getattr(self.bindings, "bridge", None)
        if bridge is None:
            return
        try:
            actor = bridge.require_eligible(binding.actor_context_id)
        except SemanticBridgeError as exc:
            self._cancel_prepared(turn_intent_id, effect_id, "actor_ineligible")
            raise ManagedTurnError(str(exc)) from exc
        if actor.actor_kind.value != binding.actor_kind.value or actor.scope_key != binding.semantic_scope_key:
            self._cancel_prepared(turn_intent_id, effect_id, "actor_mismatch")
            raise ManagedTurnError("semantic actor no longer matches binding")
        snapshot = bridge.snapshot(binding.actor_context_id)
        if row["checkpoint_id"] and snapshot.checkpoint_id != row["checkpoint_id"]:
            self._cancel_prepared(turn_intent_id, effect_id, "checkpoint_mismatch")
            raise ManagedTurnError("checkpoint no longer matches managed turn")
        if row["expected_state_version"] is not None and snapshot.state_version != int(row["expected_state_version"]):
            self._cancel_prepared(turn_intent_id, effect_id, "state_version_mismatch")
            raise ManagedTurnError("state version no longer matches managed turn")

    def _effect_is_confirmed(self, effect_id: str | None) -> bool:
        if not effect_id:
            return False
        try:
            return self.journal.get(str(effect_id)).state == "EFFECT_CONFIRMED"
        except Exception:
            return False

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
        self._assert_submit_fence(turn_intent_id, effect_id)
        owner = self._owner()
        try:
            self._assert_submit_fence(turn_intent_id, effect_id)
            result = await owner.submit_effect(
                effect_id,
                request_override=params,
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
            current = self._row(turn_intent_id)
            if current["submission_state"] == SubmissionState.SUBMITTING.value:
                self._apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.SUBMITTING.value,
                        expected_version=int(current["version"] or 0),
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
            if current["submission_state"] == SubmissionState.SUBMITTING.value:
                self._apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.SUBMITTING.value,
                        expected_version=int(current["version"] or 0),
                        target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=type(exc).__name__,
                        field_updates={"incident_json": json.dumps({"reason": type(exc).__name__})},
                    )
                )
            raise ManagedTurnError("turn/start uncertain; do not retry") from exc
        kind = owner.classify_submission(result)
        current = self._row(turn_intent_id)
        if kind == "incident" or current["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("turn/start incident; do not retry")
        if kind == "uncertain":
            if current["submission_state"] == SubmissionState.SUBMITTING.value:
                self._apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.SUBMITTING.value,
                        expected_version=int(current["version"] or 0),
                        target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref="uncertain",
                        field_updates={"incident_json": json.dumps({"reason": "timeout"})},
                    )
                )
            raise ManagedTurnError("turn/start uncertain; do not retry")
        response = result.response or {}
        turn_id = None
        inner = response.get("result") if isinstance(response.get("result"), dict) else {}
        if isinstance(inner.get("turn"), dict):
            turn_id = inner["turn"].get("id")
        if not turn_id:
            current = self._row(turn_intent_id)
            if current["submission_state"] == SubmissionState.SUBMITTING.value:
                self._apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.SUBMITTING.value,
                        expected_version=int(current["version"] or 0),
                        target_state=SubmissionState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref="missing_turn",
                    )
                )
            raise ManagedTurnError("turn/start uncertain; do not retry")
        now = _now()
        current = self._row(turn_intent_id)
        try:
            with DurabilityTransaction(self.bindings.store.connection):
                self.journal.confirm_effect(effect_id, evidence_ref=f"turn:{turn_id}")
                submitted = self.kernel.apply(
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
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=turn_intent_id,
                        expected_state=SubmissionState.SUBMITTED.value,
                        expected_version=submitted.to_version,
                        target_state=SubmissionState.OBSERVED.value,
                        cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                        cause_ref=effect_id,
                        field_updates={"observed_at": now},
                    )
                )
        except TransitionError as exc:
            row = self._row(turn_intent_id)
            if row["submission_state"] == SubmissionState.INCIDENT.value:
                raise ManagedTurnError("turn/start incident; do not retry")
            raise ManagedTurnError(str(exc)) from exc
        owner.release_open_effect(effect_id)
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                "UPDATE managed_actor_bindings SET last_turn_id = ? WHERE binding_id = ?",
                (turn_id, row["binding_id"]),
            )
        return self._row(turn_intent_id)

    async def reconcile_uncertain(self, turn_intent_id: str) -> dict[str, Any]:
        from .durability.reconciliation import EffectReconciler, ReconciliationError

        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        if row["submission_state"] not in {
            SubmissionState.SUBMISSION_UNCERTAIN.value,
            SubmissionState.SUBMITTING.value,
            SubmissionState.SUBMITTED.value,
        }:
            return row
        effect_id = str(row.get("effect_id") or "")
        if not effect_id:
            return row
        effect = self.journal.get(effect_id)
        if effect.state == "PREPARED":
            return row
        if effect.state == "INCIDENT":
            raise ManagedTurnError("incident is terminal; operator recovery required")
        try:
            await EffectReconciler(self.bindings.store.connection, self._owner()).reconcile(effect_id)
        except ReconciliationError as exc:
            raise ManagedTurnError(str(exc)) from exc
        return self._row(turn_intent_id)

    def record_completion(self, turn_intent_id: str, status: str) -> dict[str, Any]:
        row = self._row(turn_intent_id)
        if row["submission_state"] == SubmissionState.INCIDENT.value:
            raise ManagedTurnError("incident is terminal; operator recovery required")
        if not self._effect_is_confirmed(str(row.get("effect_id") or "")):
            raise ManagedTurnError("completion requires EFFECT_CONFIRMED linked effect")
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
