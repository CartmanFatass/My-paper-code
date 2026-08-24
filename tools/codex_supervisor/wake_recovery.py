"""Finite, no-resend reconciliation for managed-thread wake state."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError
from .durability.outbox import AppServerOutbox, MutationSpec, OperationState
from .durability.session_owner import AppServerSessionOwner
from .durability.transaction import DurabilityTransaction
from .mailbox_models import (
    ThreadWakeReadiness,
    WakeAttemptOutcome,
    WakeBatchState,
    WakeIncidentDisposition,
)
from .mailbox_store import MailboxStore
from .managed_models import BindingState
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import SemanticBridge
from .transport import TransportClosed
from .wake_batches import WakeBatchStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WakeIncidentError(RuntimeError):
    pass


class WakeRecovery:
    def __init__(
        self,
        bindings: BindingStore,
        mailbox: MailboxStore,
        batches: WakeBatchStore,
        client: AppServerClient | None = None,
        leases: SchedulerLeases | None = None,
        instance_id: str = "recovery",
        bridge: SemanticBridge | None = None,
    ) -> None:
        self.bindings = bindings
        self.mailbox = mailbox
        self.batches = batches
        self.client = client
        self.leases = leases
        self.instance_id = instance_id
        self.bridge = bridge

    async def list_loaded_ids(self) -> set[str] | None:
        if self.client is None:
            return None
        try:
            return set(await self.client.list_loaded_threads())
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return None

    async def classify(self, binding_id: str) -> ThreadWakeReadiness:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is BindingState.REVOKED:
            return ThreadWakeReadiness.REVOKED
        if binding.binding_state is not BindingState.ACTIVE or not binding.thread_id or self.client is None:
            return ThreadWakeReadiness.UNKNOWN
        try:
            read = await self.client.read_thread(binding.thread_id, include_turns=True)
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return ThreadWakeReadiness.UNKNOWN
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        status = thread.get("status")
        status_type = status.get("type") if isinstance(status, dict) else status
        if status_type == "active":
            return ThreadWakeReadiness.ACTIVE_TURN
        if status_type == "notLoaded":
            return ThreadWakeReadiness.IDLE_NOT_LOADED
        if status_type == "idle":
            loaded = await self.list_loaded_ids()
            if loaded is None:
                return ThreadWakeReadiness.UNKNOWN
            return (
                ThreadWakeReadiness.IDLE_LOADED
                if binding.thread_id in loaded
                else ThreadWakeReadiness.IDLE_NOT_LOADED
            )
        return ThreadWakeReadiness.UNKNOWN

    def _wake_context(self, binding_id: str, wake_batch_id: str) -> Any | None:
        rows = self.bindings.store.connection.execute(
            """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
            FROM managed_context_injections
            WHERE turn_intent_id = ? AND binding_id = ?""",
            (wake_batch_id, binding_id),
        ).fetchall()
        return rows[0] if len(rows) == 1 else None

    def _validate_resume_once(self, binding: Any, wake_batch_id: str) -> None:
        batch = self.batches.get(wake_batch_id)
        context = self._wake_context(binding.binding_id, wake_batch_id)
        if (
            batch is None
            or batch["state"] != WakeBatchState.PREPARED.value
            or str(batch["binding_id"]) != binding.binding_id
            or str(batch["thread_id"]) != binding.thread_id
            or context is None
        ):
            raise WakeIncidentError("wake resume tuple is not uniquely PREPARED")
        bridge = self.bridge or getattr(self.bindings, "bridge", None)
        if bridge is None:
            raise WakeIncidentError("wake resume requires a semantic bridge")
        snapshot = bridge.snapshot(binding.actor_context_id)
        if (
            (
                snapshot.checkpoint_id, snapshot.state_version,
                snapshot.epoch_id, snapshot.epoch_revision,
            )
            != tuple(context)
            or snapshot.actor_kind != binding.actor_kind.value
            or snapshot.scope_key != binding.semantic_scope_key
        ):
            raise WakeIncidentError("wake resume context changed before READY")

    async def resume_once(
        self, binding_id: str, *, wake_batch_id: str | None = None
    ) -> ThreadWakeReadiness:
        binding = self.bindings.get(binding_id)
        if (
            binding is None
            or binding.binding_state is not BindingState.ACTIVE
            or not binding.thread_id
            or self.client is None
            or wake_batch_id is None
        ):
            return ThreadWakeReadiness.UNKNOWN
        try:
            self._validate_resume_once(binding, wake_batch_id)
        except WakeIncidentError:
            return ThreadWakeReadiness.UNKNOWN
        owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
        operation = owner.enqueue_mutation(
            MutationSpec(
                dedupe_key=f"wake-resume:{wake_batch_id}:{binding.thread_id}",
                protocol_session_id=owner.protocol_session_id,
                run_id=owner.protocol_session_id,
                method="thread/resume",
                params={"threadId": binding.thread_id},
                target=f"binding:{binding_id}",
                thread_id=binding.thread_id,
                binding_id=binding_id,
            )
        )
        if operation.state is not OperationState.READY:
            return await self.classify(binding_id)
        result = await owner.submit(operation.operation_id)
        if result.state is OperationState.UNKNOWN:
            self._contain_prepared_resume(
                wake_batch_id, operation.operation_id,
                reason=result.error or result.outcome or "ambiguous",
            )
        self._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.RESUMED
            if result.state is OperationState.DONE and result.outcome == "OK"
            else WakeAttemptOutcome.SUBMISSION_UNCERTAIN,
            request_id=str(operation.rpc_request_id),
            error=None if result.outcome == "OK" else {"reason": result.error or result.outcome},
        )
        return await self.classify(binding_id)

    def _contain_prepared_resume(
        self, wake_batch_id: str, operation_id: str, *, reason: str
    ) -> None:
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            changed = self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'SUBMITTING',
                   version = version + 1, effect_id = ?
                   WHERE wake_batch_id = ? AND state = 'PREPARED'""",
                (operation_id, wake_batch_id),
            )
            if changed.rowcount:
                self.bindings.store.connection.execute(
                    """UPDATE wake_batches SET state = 'SUBMISSION_UNCERTAIN',
                       version = version + 1, incident_json = ?
                       WHERE wake_batch_id = ? AND state = 'SUBMITTING'""",
                    (json.dumps({"reason": reason}), wake_batch_id),
                )
                self.bindings.store.connection.execute(
                    """UPDATE mailbox_messages
                    SET delivery_state = 'SUBMISSION_UNCERTAIN', delivery_version = delivery_version + 1
                    WHERE delivery_state = 'BATCHED' AND message_id IN (
                        SELECT message_id FROM wake_batch_messages WHERE wake_batch_id = ?
                    )""",
                    (wake_batch_id,),
                )

    def _record_attempt(
        self,
        wake_batch_id: str,
        outcome: WakeAttemptOutcome,
        *,
        request_id: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            self.bindings.store.connection.execute(
                """INSERT INTO wake_attempts(
                    wake_attempt_id, wake_batch_id, attempt_number, request_id,
                    outcome, error_json, created_at
                ) SELECT ?, ?, COALESCE(MAX(attempt_number), 0) + 1, ?, ?, ?, ?
                  FROM wake_attempts WHERE wake_batch_id = ?""",
                (
                    f"watt_{uuid.uuid4().hex}", wake_batch_id, request_id,
                    outcome.value, None if error is None else json.dumps(error),
                    _now(), wake_batch_id,
                ),
            )

    def _response_for(self, operation: Any) -> dict[str, object] | None:
        row = self.bindings.store.connection.execute(
            """SELECT canonical_json FROM raw_messages
            WHERE run_id = ? AND direction = 'stdout' AND request_id = ?
            ORDER BY raw_message_seq DESC LIMIT 1""",
            (operation.run_id, str(operation.rpc_request_id)),
        ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(str(row[0]))
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def _activate_done(self, wake_batch_id: str, operation: Any) -> dict[str, object]:
        response = self._response_for(operation)
        result = response.get("result") if isinstance(response, dict) and isinstance(response.get("result"), dict) else {}
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turn_id = str(turn.get("id") or "")
        if not turn_id:
            current = self.batches.get(wake_batch_id)
            assert current is not None
            return current
        now = _now()
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'SUBMITTED', version = version + 1,
                   app_server_turn_id = ?, submitted_at = ?
                   WHERE wake_batch_id = ? AND state IN ('SUBMITTING','SUBMISSION_UNCERTAIN')""",
                (turn_id, now, wake_batch_id),
            )
            self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'ACTIVE', version = version + 1,
                   observed_at = ? WHERE wake_batch_id = ? AND state = 'SUBMITTED'""",
                (now, wake_batch_id),
            )
        current = self.batches.get(wake_batch_id)
        assert current is not None
        return current

    async def reconcile_batch(self, wake_batch_id: str) -> dict[str, object]:
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise WakeIncidentError(f"unknown wake batch: {wake_batch_id}")
        operation_id = str(batch.get("effect_id") or "")
        state = WakeBatchState(str(batch["state"]))
        if state is WakeBatchState.PREPARED:
            resume = AppServerOutbox(self.bindings.store.connection).get_by_dedupe(
                f"wake-resume:{wake_batch_id}:{batch['thread_id']}"
            )
            rejected = (
                resume is not None
                and resume.state is OperationState.DONE
                and resume.outcome in {"PROVIDER_REJECTED", "LOCAL_REJECTED", "LOCAL_CANCELLED"}
            )
            if resume is not None and not rejected:
                self._contain_prepared_resume(
                    wake_batch_id, resume.operation_id,
                    reason=f"resume_{resume.state.value.lower()}_{resume.outcome or 'pending'}",
                )
                current = self.batches.get(wake_batch_id)
                assert current is not None
                return current
            # A PREPARED domain row has no frozen new-session wire identity.
            # Dispose it locally; a later scheduler may construct a new batch.
            with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
                self.bindings.store.connection.execute(
                    """UPDATE wake_batches SET state = 'CANCELLED', version = version + 1,
                       incident_json = '{"reason":"restart_prepared_rebuild_required"}'
                       WHERE wake_batch_id = ? AND state = 'PREPARED'""",
                    (wake_batch_id,),
                )
                self.bindings.store.connection.execute(
                    """UPDATE mailbox_messages SET delivery_state = 'ELIGIBLE',
                       delivery_version = delivery_version + 1, batched_at = NULL, eligible_at = ?
                       WHERE delivery_state = 'BATCHED' AND message_id IN (
                           SELECT message_id FROM wake_batch_messages WHERE wake_batch_id = ?
                       )""",
                    (_now(), wake_batch_id),
                )
            self._record_attempt(wake_batch_id, WakeAttemptOutcome.CANCELLED)
        elif operation_id and state in {
            WakeBatchState.SUBMITTING,
            WakeBatchState.SUBMISSION_UNCERTAIN,
            WakeBatchState.SUBMITTED,
        }:
            operation = AppServerOutbox(self.bindings.store.connection).get(operation_id)
            if operation.state is OperationState.DONE and operation.outcome == "OK":
                batch = self._activate_done(wake_batch_id, operation)
            elif operation.state is OperationState.UNKNOWN:
                with self.bindings.store._lock, self.bindings.store.connection:
                    self.bindings.store.connection.execute(
                        """UPDATE wake_batches SET state = 'SUBMISSION_UNCERTAIN',
                           version = version + CASE WHEN state = 'SUBMITTING' THEN 1 ELSE 0 END
                           WHERE wake_batch_id = ? AND state IN ('SUBMITTING','SUBMISSION_UNCERTAIN')""",
                        (wake_batch_id,),
                    )
        batch = self.batches.get(wake_batch_id)
        assert batch is not None
        if batch["state"] == WakeBatchState.ACTIVE.value:
            status = await self._lookup_turn_status(batch)
            if status in {"completed", "interrupted", "failed"}:
                return self.batches.set_state(
                    wake_batch_id,
                    state=WakeBatchState.COMPLETED.value,
                    completion_status=status,
                    completed_at=_now(),
                    expected_state=WakeBatchState.ACTIVE.value,
                )
        return batch

    async def _lookup_turn_status(self, batch: dict[str, object]) -> str | None:
        if self.client is None:
            return None
        try:
            read = await self.client.read_thread(str(batch["thread_id"]), include_turns=True)
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError):
            return None
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        for turn in thread.get("turns") if isinstance(thread.get("turns"), list) else []:
            if isinstance(turn, dict) and str(turn.get("id") or "") == str(batch.get("app_server_turn_id") or ""):
                status = turn.get("status")
                return str(status.get("type") if isinstance(status, dict) else status)
        return None

    def resolve_incident(
        self,
        wake_batch_id: str,
        *,
        operator: str,
        disposition: str | WakeIncidentDisposition,
        turn_id: str | None = None,
        completion_status: str | None = None,
    ) -> dict[str, object]:
        if not operator.strip():
            raise WakeIncidentError("operator identity is required")
        chosen = disposition if isinstance(disposition, WakeIncidentDisposition) else WakeIncidentDisposition(str(disposition))
        batch = self.batches.get(wake_batch_id)
        if batch is None or batch["state"] != WakeBatchState.INCIDENT.value:
            raise WakeIncidentError("only INCIDENT wake batches may be resolved")
        if chosen is WakeIncidentDisposition.TURN_OBSERVED:
            target = "COMPLETED" if completion_status else "ACTIVE"
        elif chosen is WakeIncidentDisposition.NO_SUBMISSION_EVIDENCE:
            operation_id = str(batch.get("effect_id") or "")
            if operation_id:
                operation = AppServerOutbox(self.bindings.store.connection).get(operation_id)
                if operation.state in {OperationState.SENDING, OperationState.UNKNOWN}:
                    raise WakeIncidentError("possible submission cannot be requeued")
            target = "CANCELLED"
        else:
            target = "ABANDONED"
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = ?, version = version + 1,
                   app_server_turn_id = COALESCE(?, app_server_turn_id),
                   completion_status = COALESCE(?, completion_status)
                   WHERE wake_batch_id = ? AND state = 'INCIDENT'""",
                (target, turn_id, completion_status, wake_batch_id),
            )
        updated = self.batches.get(wake_batch_id)
        assert updated is not None
        return updated

    async def recover(self) -> dict[str, object]:
        rows = self.bindings.store.connection.execute(
            """SELECT wake_batch_id, binding_id FROM wake_batches
            WHERE state IN ('PREPARED','SUBMITTING','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE')"""
        ).fetchall()
        recovered: list[dict[str, object]] = []
        for row in rows:
            lease = None
            if self.leases is not None:
                try:
                    lease = self.leases.acquire(str(row["binding_id"]), self.instance_id)
                except LeaseError:
                    continue
            try:
                recovered.append(await self.reconcile_batch(str(row["wake_batch_id"])))
            finally:
                if lease is not None and self.leases is not None:
                    self.leases.release(
                        str(row["binding_id"]), self.instance_id,
                        generation=int(lease["generation"]),
                    )
        return {"batches": recovered}
