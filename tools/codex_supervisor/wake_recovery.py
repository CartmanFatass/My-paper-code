"""Reconcile managed-thread wake readiness. No automatic turn/steer."""

from __future__ import annotations

import asyncio
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, UnexpectedServerRequest
from .mailbox_models import (
    ThreadWakeReadiness,
    WakeAttemptOutcome,
    WakeBatchState,
    WakeIncidentDisposition,
)
from .mailbox_store import MailboxStore
from .managed_models import BindingState
from .mutation_intents import MutationIntentError, MutationIntentStore
from .scheduler_leases import LeaseError, SchedulerLeases
from .session_guard import SessionGuard
from .transport import TransportClosed
from .wake_batches import WakeBatchStore


class WakeIncidentError(RuntimeError):
    """Raised when an operator cannot legally resolve a wake incident."""


class WakeRecovery:
    def __init__(
        self,
        bindings: BindingStore,
        mailbox: MailboxStore,
        batches: WakeBatchStore,
        client: AppServerClient | None = None,
        leases: SchedulerLeases | None = None,
        instance_id: str = "recovery",
    ) -> None:
        self.bindings = bindings
        self.mailbox = mailbox
        self.batches = batches
        self.client = client
        self.leases = leases
        self.instance_id = instance_id
        self.mutations = MutationIntentStore(bindings.store)

    async def list_loaded_ids(self) -> set[str] | None:
        if self.client is None:
            return None
        try:
            loaded = await self.client.list_loaded_threads()
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return None
        return set(loaded)

    async def classify(self, binding_id: str) -> ThreadWakeReadiness:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is BindingState.REVOKED:
            return ThreadWakeReadiness.REVOKED
        if binding.binding_state is not BindingState.ACTIVE or not binding.thread_id:
            return ThreadWakeReadiness.UNKNOWN
        if self.client is None:
            return ThreadWakeReadiness.UNKNOWN
        try:
            read = await self.client.read_thread(binding.thread_id, include_turns=True)
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return ThreadWakeReadiness.UNKNOWN
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        status = thread.get("status")
        status_type = None
        if isinstance(status, dict):
            status_type = status.get("type")
        elif isinstance(status, str):
            status_type = status
        if status_type == "active":
            return ThreadWakeReadiness.ACTIVE_TURN
        if status_type == "idle":
            loaded = await self.list_loaded_ids()
            if loaded is None:
                return ThreadWakeReadiness.UNKNOWN
            if binding.thread_id in loaded:
                return ThreadWakeReadiness.IDLE_LOADED
            return ThreadWakeReadiness.IDLE_NOT_LOADED
        if status_type == "notLoaded":
            return ThreadWakeReadiness.IDLE_NOT_LOADED
        return ThreadWakeReadiness.UNKNOWN

    async def _reconcile_resume_intent(self, intent_id: str, binding_id: str) -> ThreadWakeReadiness:
        readiness = await self.classify(binding_id)
        if readiness is ThreadWakeReadiness.IDLE_LOADED:
            try:
                self.mutations.mark_applied_after_loaded_observation(intent_id)
            except MutationIntentError:
                pass
        return readiness

    async def resume_once(self, binding_id: str) -> ThreadWakeReadiness:
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id or self.client is None:
            return ThreadWakeReadiness.UNKNOWN
        client_key = f"thread/resume:{binding.thread_id}"
        existing = self.mutations.get_open("thread/resume", client_key)
        if existing is not None:
            return await self._reconcile_resume_intent(str(existing["intent_id"]), binding_id)
        try:
            intent = self.mutations.begin("thread/resume", client_key, binding_id=binding_id)
        except MutationIntentError:
            return ThreadWakeReadiness.UNKNOWN

        def _incident(_payload: object) -> None:
            try:
                self.mutations.mark_incident(str(intent["intent_id"]), "server_request")
            except MutationIntentError:
                pass

        guard = SessionGuard(self.client, self.bindings.store, on_incident=_incident)
        try:
            await guard.request("thread/resume", {"threadId": binding.thread_id})
        except asyncio.TimeoutError:
            try:
                self.mutations.mark_uncertain(str(intent["intent_id"]), "timeout")
            except MutationIntentError:
                pass
            return ThreadWakeReadiness.UNKNOWN
        except UnexpectedServerRequest:
            return ThreadWakeReadiness.UNKNOWN
        except (AppServerRpcError, TransportClosed):
            try:
                self.mutations.mark_uncertain(str(intent["intent_id"]), "transport")
            except MutationIntentError:
                pass
            return ThreadWakeReadiness.UNKNOWN
        try:
            self.mutations.mark_submitted_unreconciled(str(intent["intent_id"]))
        except MutationIntentError:
            return ThreadWakeReadiness.UNKNOWN
        return await self._reconcile_resume_intent(str(intent["intent_id"]), binding_id)

    def _record_attempt(
        self,
        wake_batch_id: str,
        outcome: WakeAttemptOutcome,
        *,
        request_id: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        import json
        import uuid

        from datetime import datetime, timezone

        existing = self.bindings.store.connection.execute(
            "SELECT COALESCE(MAX(attempt_number), 0) FROM wake_attempts WHERE wake_batch_id = ?",
            (wake_batch_id,),
        ).fetchone()[0]
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                """INSERT INTO wake_attempts (
                    wake_attempt_id, wake_batch_id, attempt_number, request_id, outcome, error_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"watt_{uuid.uuid4().hex}",
                    wake_batch_id,
                    int(existing) + 1,
                    request_id,
                    outcome.value,
                    None if error is None else json.dumps(error),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    async def reconcile_batch(self, wake_batch_id: str) -> dict[str, object]:
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise RuntimeError(f"unknown wake batch: {wake_batch_id}")
        state = WakeBatchState(str(batch["state"]))
        if state is WakeBatchState.PREPARED:
            for message in self.batches.messages_for(wake_batch_id):
                self.mailbox.return_to_eligible(message.message_id)
            updated = self.batches.set_state(
                wake_batch_id,
                state=WakeBatchState.CANCELLED.value,
            )
            self._record_attempt(wake_batch_id, WakeAttemptOutcome.CANCELLED)
            return updated
        if state is WakeBatchState.ACTIVE:
            return await self._reconcile_active(wake_batch_id, batch)
        if state in {
            WakeBatchState.SUBMITTING,
            WakeBatchState.SUBMITTED,
            WakeBatchState.SUBMISSION_UNCERTAIN,
        } and self.client is not None:
            try:
                read = await self.client.read_thread(str(batch["thread_id"]), include_turns=True)
            except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
                return batch
            thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
            turns = thread.get("turns") if isinstance(thread.get("turns"), list) else []
            wanted = batch["client_user_message_id"]
            for turn in turns:
                if isinstance(turn, dict) and turn.get("clientUserMessageId") == wanted:
                    turn_id = turn.get("id")
                    from datetime import datetime, timezone

                    expected = state.value
                    if state is WakeBatchState.SUBMITTING:
                        self.batches.set_state(
                            wake_batch_id,
                            state=WakeBatchState.SUBMITTED.value,
                            app_server_turn_id=turn_id,
                            expected_state=WakeBatchState.SUBMITTING.value,
                        )
                        expected = WakeBatchState.SUBMITTED.value
                    updated = self.batches.set_state(
                        wake_batch_id,
                        state=WakeBatchState.ACTIVE.value,
                        app_server_turn_id=turn_id,
                        observed_at=datetime.now(timezone.utc).isoformat(),
                        expected_state=expected,
                    )
                    if updated["state"] == WakeBatchState.INCIDENT.value:
                        return updated
                    for message in self.batches.messages_for(wake_batch_id):
                        if message.delivery_state.value != "DELIVERED_TO_TURN":
                            self.mailbox.mark_delivered(message.message_id)
                    self._record_attempt(wake_batch_id, WakeAttemptOutcome.RECONCILED)
                    row = self.batches.get(wake_batch_id)
                    assert row is not None
                    return row
        return batch

    def _mechanical_status(self, status: object) -> str | None:
        if isinstance(status, dict):
            status = status.get("type") or status.get("status")
        if status is None:
            return None
        text = str(status)
        if text in {"completed", "interrupted", "failed"}:
            return text
        if text in {"inProgress", "active"}:
            return "active"
        return None

    async def _lookup_turn_status(self, batch: dict[str, object]) -> str | None:
        turn_id = str(batch.get("app_server_turn_id") or "")
        if turn_id:
            snap = self.bindings.store.connection.execute(
                "SELECT status FROM turn_snapshots WHERE turn_id = ?",
                (turn_id,),
            ).fetchone()
            if snap is not None:
                mechanical = self._mechanical_status(snap["status"])
                if mechanical is not None:
                    return mechanical
        if self.client is None:
            return None
        try:
            read = await self.client.read_thread(str(batch["thread_id"]), include_turns=True)
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return None
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        turns = thread.get("turns") if isinstance(thread.get("turns"), list) else []
        wanted_id = str(batch.get("app_server_turn_id") or "")
        wanted_client = batch.get("client_user_message_id")
        for turn in turns:
            if not isinstance(turn, dict):
                continue
            if wanted_id and str(turn.get("id") or "") == wanted_id:
                return self._mechanical_status(turn.get("status"))
            if wanted_client and turn.get("clientUserMessageId") == wanted_client:
                return self._mechanical_status(turn.get("status"))
        return "missing"

    async def _reconcile_active(self, wake_batch_id: str, batch: dict[str, object]) -> dict[str, object]:
        from datetime import datetime, timezone

        status = await self._lookup_turn_status(batch)
        if status == "active":
            return batch
        if status in {"completed", "interrupted", "failed"}:
            for message in self.batches.messages_for(wake_batch_id):
                if message.delivery_state.value != "DELIVERED_TO_TURN":
                    try:
                        self.mailbox.mark_delivered(message.message_id)
                    except Exception:
                        pass
            updated = self.batches.set_state(
                wake_batch_id,
                state=WakeBatchState.COMPLETED.value,
                completion_status=status,
                completed_at=datetime.now(timezone.utc).isoformat(),
                expected_state=WakeBatchState.ACTIVE.value,
            )
            if updated["state"] == WakeBatchState.INCIDENT.value:
                return updated
            self._record_attempt(wake_batch_id, WakeAttemptOutcome.RECONCILED)
            return updated
        updated = self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.INCIDENT.value,
            incident_json='{"reason":"active_turn_missing"}',
            expected_state=WakeBatchState.ACTIVE.value,
        )
        self._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.INCIDENT,
            error={"reason": "active_turn_missing"},
        )
        return updated

    def _has_possible_submission(self, wake_batch_id: str, batch: dict[str, object]) -> bool:
        if batch.get("app_server_turn_id") or batch.get("submitted_at") or batch.get("observed_at"):
            return True
        for message in self.batches.messages_for(wake_batch_id):
            if message.delivery_state.value == "DELIVERED_TO_TURN":
                return True
        rows = self.bindings.store.connection.execute(
            """SELECT outcome FROM wake_attempts WHERE wake_batch_id = ?""",
            (wake_batch_id,),
        ).fetchall()
        return any(str(row[0]) in {"SUBMITTED", "RECONCILED"} for row in rows)

    def resolve_incident(
        self,
        wake_batch_id: str,
        *,
        operator: str,
        disposition: str | WakeIncidentDisposition,
        turn_id: str | None = None,
        completion_status: str | None = None,
    ) -> dict[str, object]:
        from .durability.operator_resolution import (
            OperatorResolutionError,
            OperatorResolutionService,
            ResolutionDisposition,
        )

        if not str(operator or "").strip():
            raise WakeIncidentError("operator identity is required to resolve a wake incident")
        if isinstance(disposition, WakeIncidentDisposition):
            chosen = disposition
        else:
            try:
                chosen = WakeIncidentDisposition(str(disposition))
            except ValueError as exc:
                raise WakeIncidentError("unknown wake incident disposition") from exc
        mapping = {
            WakeIncidentDisposition.NO_SUBMISSION_EVIDENCE: ResolutionDisposition.NO_SUBMISSION_EVIDENCE,
            WakeIncidentDisposition.ABANDON: ResolutionDisposition.ABANDON,
        }
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise WakeIncidentError(f"unknown wake batch: {wake_batch_id}")
        if str(batch["state"]) != WakeBatchState.INCIDENT.value:
            raise WakeIncidentError("only INCIDENT wake batches may be operator-resolved")
        if chosen is WakeIncidentDisposition.NO_SUBMISSION_EVIDENCE and self._has_possible_submission(
            wake_batch_id, batch
        ):
            raise WakeIncidentError("cannot requeue incident with possible submission")
        if chosen is WakeIncidentDisposition.TURN_OBSERVED:
            kernel_disposition = (
                ResolutionDisposition.TURN_OBSERVED_COMPLETED
                if completion_status in {"completed", "interrupted", "failed"}
                else ResolutionDisposition.TURN_OBSERVED_ACTIVE
            )
        else:
            kernel_disposition = mapping[chosen]
        try:
            OperatorResolutionService(self.bindings.store.connection).resolve_wake(
                wake_batch_id,
                operator=str(operator).strip(),
                disposition=kernel_disposition,
                evidence_kind="OPERATOR",
                evidence_ref=f"wake-incident:{wake_batch_id}",
                turn_id=turn_id,
                completion_status=completion_status,
            )
        except OperatorResolutionError as exc:
            raise WakeIncidentError(str(exc)) from exc
        updated = self.batches.get(wake_batch_id)
        assert updated is not None
        self._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.CANCELLED
            if kernel_disposition is ResolutionDisposition.NO_SUBMISSION_EVIDENCE
            else WakeAttemptOutcome.RECONCILED,
            error={"operator": str(operator).strip(), "disposition": chosen.value},
        )
        return updated

    async def recover(self) -> dict[str, object]:
        recovered_batches = []
        rows = self.bindings.store.connection.execute(
            """SELECT wake_batch_id, binding_id FROM wake_batches
            WHERE state IN ('PREPARED', 'SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'ACTIVE')"""
        ).fetchall()
        for row in rows:
            binding_id = str(row["binding_id"])
            lease = None
            if self.leases is not None:
                try:
                    lease = self.leases.acquire(binding_id, self.instance_id)
                except LeaseError:
                    continue
            try:
                recovered_batches.append(await self.reconcile_batch(str(row["wake_batch_id"])))
            finally:
                if lease is not None and self.leases is not None:
                    self.leases.release(binding_id, self.instance_id, generation=int(lease["generation"]))
        return {"batches": recovered_batches}
