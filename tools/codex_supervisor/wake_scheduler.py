"""Submit at most one idle-thread wake batch without mutation retries."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient
from .durability.outbox import AppServerOutbox, MutationSpec, OperationState
from .durability.session_owner import AppServerSessionOwner
from .durability.transaction import DurabilityTransaction
from .mailbox_models import ThreadWakeReadiness, WakeAttemptOutcome, WakeBatchState
from .mailbox_store import MailboxStore
from .managed_models import BindingState, ManagedActorKind
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import SemanticBridge
from .semantic_scanner import SemanticScanner
from .wake_batches import WakeBatchStore
from .wake_recovery import WakeRecovery


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WakeSchedulerError(RuntimeError):
    pass


class WakeScheduler:
    def __init__(
        self,
        bindings: BindingStore,
        mailbox: MailboxStore,
        batches: WakeBatchStore,
        leases: SchedulerLeases,
        recovery: WakeRecovery,
        scanner: SemanticScanner,
        bridge: SemanticBridge,
        client: AppServerClient | None = None,
        *,
        instance_id: str = "scheduler",
    ) -> None:
        self.bindings = bindings
        self.mailbox = mailbox
        self.batches = batches
        self.leases = leases
        self.recovery = recovery
        self.scanner = scanner
        self.bridge = bridge
        self.client = client
        self.instance_id = instance_id
        if recovery.leases is None:
            recovery.leases = leases
        recovery.instance_id = instance_id
        recovery.bridge = bridge

    def _sender_kinds(self) -> dict[str, str | None]:
        return {
            binding.actor_context_id: binding.actor_kind.value
            for binding in self.bindings.list_bindings()
        }

    def _eligible_messages(self, binding_id: str) -> list[Any]:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE:
            return []
        return self.mailbox.select_eligible(
            target_actor_context_id=binding.actor_context_id,
            target_kind=binding.actor_kind.value,
            target_binding_state=binding.binding_state.value,
            sender_kind_for=self._sender_kinds(),
        )

    def _validate_once(self, binding_id: str, wake_batch_id: str, generation: int) -> tuple[Any, dict[str, object]]:
        self.leases.assert_held(binding_id, self.instance_id, generation)
        binding = self.bindings.get(binding_id)
        batch = self.batches.get(wake_batch_id)
        if (
            binding is None
            or binding.binding_state is not BindingState.ACTIVE
            or not binding.thread_id
            or batch is None
            or batch["state"] != WakeBatchState.PREPARED.value
            or str(batch["binding_id"]) != binding_id
            or str(batch["thread_id"]) != binding.thread_id
            or batch.get("lease_holder") != self.instance_id
            or int(batch.get("lease_generation") or -1) != generation
        ):
            raise WakeSchedulerError("wake admission tuple is no longer eligible")
        context = self.bindings.store.connection.execute(
            """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
            FROM managed_context_injections
            WHERE turn_intent_id = ? AND binding_id = ?""",
            (wake_batch_id, binding_id),
        ).fetchall()
        if len(context) != 1:
            raise WakeSchedulerError("wake has no unique context snapshot")
        snapshot = self.bridge.snapshot(binding.actor_context_id)
        expected = tuple(context[0])
        actual = (
            snapshot.checkpoint_id, snapshot.state_version,
            snapshot.epoch_id, snapshot.epoch_revision,
        )
        if (
            actual != expected
            or snapshot.actor_kind != binding.actor_kind.value
            or snapshot.scope_key != binding.semantic_scope_key
        ):
            raise WakeSchedulerError("wake semantic context changed before READY")
        return binding, batch

    async def submit_batch(
        self,
        wake_batch_id: str,
        input_text: str,
        *,
        lease_generation: int | None = None,
    ) -> dict[str, object]:
        if self.client is None or lease_generation is None:
            raise WakeSchedulerError("wake submission requires client and lease generation")
        preliminary = self.batches.get(wake_batch_id)
        if preliminary is None:
            raise WakeSchedulerError("unknown wake batch")
        binding_id = str(preliminary["binding_id"])
        generation = int(lease_generation)
        binding, batch = self._validate_once(binding_id, wake_batch_id, generation)
        params = {
            "threadId": batch["thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": batch["client_user_message_id"],
        }
        owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            operation = owner.enqueue_mutation(
                MutationSpec(
                    dedupe_key=f"wake-turn:{wake_batch_id}",
                    protocol_session_id=owner.protocol_session_id,
                    run_id=owner.protocol_session_id,
                    method="turn/start",
                    params=params,
                    target=f"binding:{binding_id}",
                    thread_id=str(batch["thread_id"]),
                    binding_id=binding_id,
                )
            )
            changed = self.bindings.store.connection.execute(
                """UPDATE wake_batches
                SET state = 'SUBMITTING', version = version + 1, effect_id = ?
                WHERE wake_batch_id = ? AND state = 'PREPARED'""",
                (operation.operation_id, wake_batch_id),
            )
            if changed.rowcount != 1:
                raise WakeSchedulerError("wake ceased to be PREPARED before enqueue")
            self.bindings.store.connection.execute(
                """INSERT INTO wake_attempts(
                    wake_attempt_id, wake_batch_id, attempt_number, request_id,
                    outcome, error_json, created_at
                ) VALUES (?, ?, 1, ?, 'SUBMITTING', NULL, ?)""",
                (
                    f"watt_{uuid.uuid4().hex}", wake_batch_id,
                    str(operation.rpc_request_id), _now(),
                ),
            )
        submitted = await owner.submit(operation.operation_id)
        if submitted.state is OperationState.UNKNOWN:
            self._mark_uncertain(wake_batch_id, {"reason": submitted.error or "ambiguous"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry")
        if submitted.outcome != "OK":
            self.batches.set_state(
                wake_batch_id,
                state=WakeBatchState.INCIDENT.value,
                incident_json=json.dumps({"reason": submitted.outcome}),
                expected_state=WakeBatchState.SUBMITTING.value,
            )
            raise WakeSchedulerError("wake turn/start provider-rejected")
        response = submitted.response or {}
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turn_id = str(turn.get("id") or "")
        if not turn_id:
            raise WakeSchedulerError("wake response is DONE but missing turn id")
        now = _now()
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            first = self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'SUBMITTED', version = version + 1,
                   app_server_turn_id = ?, submitted_at = ?
                   WHERE wake_batch_id = ? AND state = 'SUBMITTING'""",
                (turn_id, now, wake_batch_id),
            )
            if first.rowcount != 1:
                raise WakeSchedulerError("wake completion requires SUBMITTING")
            self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'ACTIVE', version = version + 1,
                   observed_at = ? WHERE wake_batch_id = ? AND state = 'SUBMITTED'""",
                (now, wake_batch_id),
            )
            self.bindings.store.connection.execute(
                """UPDATE mailbox_messages
                SET delivery_state = 'DELIVERED_TO_TURN',
                    delivery_version = delivery_version + 1, delivered_at = ?
                WHERE delivery_state = 'BATCHED' AND message_id IN (
                    SELECT message_id FROM wake_batch_messages WHERE wake_batch_id = ?
                )""",
                (now, wake_batch_id),
            )
        self.recovery._record_attempt(
            wake_batch_id, WakeAttemptOutcome.SUBMITTED,
            request_id=str(response.get("id") or operation.rpc_request_id),
        )
        updated = self.batches.get(wake_batch_id)
        assert updated is not None
        return updated

    def _mark_uncertain(self, wake_batch_id: str, error: dict[str, object]) -> None:
        now = _now()
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            self.bindings.store.connection.execute(
                """UPDATE wake_batches SET state = 'SUBMISSION_UNCERTAIN',
                   version = version + 1, incident_json = ?
                   WHERE wake_batch_id = ? AND state = 'SUBMITTING'""",
                (json.dumps(error), wake_batch_id),
            )
            self.bindings.store.connection.execute(
                """UPDATE mailbox_messages
                SET delivery_state = 'SUBMISSION_UNCERTAIN', delivery_version = delivery_version + 1
                WHERE delivery_state = 'BATCHED' AND message_id IN (
                    SELECT message_id FROM wake_batch_messages WHERE wake_batch_id = ?
                )""",
                (wake_batch_id,),
            )
        self.recovery._record_attempt(
            wake_batch_id, WakeAttemptOutcome.SUBMISSION_UNCERTAIN, error=error
        )

    def observe_completion(self, wake_batch_id: str, status: str) -> dict[str, object]:
        current = self.batches.get(wake_batch_id)
        if current is None or current["state"] != WakeBatchState.ACTIVE.value:
            raise WakeSchedulerError("only ACTIVE wake batches may complete")
        operation_id = str(current.get("effect_id") or "")
        operation = AppServerOutbox(self.bindings.store.connection).get(operation_id)
        if operation.state is not OperationState.DONE or operation.outcome != "OK":
            raise WakeSchedulerError("completion requires a successful DONE operation")
        return self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.COMPLETED.value,
            completion_status=status,
            completed_at=_now(),
            expected_state=WakeBatchState.ACTIVE.value,
        )

    async def schedule_binding(self, binding_id: str, *, lease_generation: int) -> dict[str, object] | None:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE or not binding.thread_id:
            return None
        self.leases.assert_held(binding_id, self.instance_id, lease_generation)
        if self.batches.open_batch_for_binding(binding_id) is not None:
            return None
        messages = self._eligible_messages(binding_id)
        if not messages:
            return None
        readiness = await self.recovery.classify(binding_id)
        if readiness is ThreadWakeReadiness.ACTIVE_TURN:
            return {"binding_id": binding_id, "readiness": readiness.value, "queued": True}
        if readiness not in {ThreadWakeReadiness.IDLE_NOT_LOADED, ThreadWakeReadiness.IDLE_LOADED}:
            return {"binding_id": binding_id, "readiness": readiness.value}
        snapshot = self.bridge.snapshot(binding.actor_context_id)
        batch = self.batches.prepare(
            binding_id=binding_id,
            thread_id=binding.thread_id,
            snapshot=snapshot,
            messages=messages,
            lease_generation=lease_generation,
            lease_holder=self.instance_id,
        )
        if readiness is ThreadWakeReadiness.IDLE_NOT_LOADED:
            readiness = await self.recovery.resume_once(
                binding_id, wake_batch_id=str(batch["wake_batch_id"])
            )
        if readiness is not ThreadWakeReadiness.IDLE_LOADED:
            return {"binding_id": binding_id, "readiness": readiness.value, "resumed": False}
        return await self.submit_batch(
            str(batch["wake_batch_id"]), str(batch["input_text"]),
            lease_generation=lease_generation,
        )

    async def once(self) -> dict[str, object]:
        await self.recovery.recover()
        scanned = self.scanner.scan()
        scheduled = None
        for binding in self.bindings.list_bindings():
            if binding.binding_state is not BindingState.ACTIVE or binding.actor_kind not in {
                ManagedActorKind.OPERATIONAL_ROOT, ManagedActorKind.PORTFOLIO
            }:
                continue
            try:
                lease = self.leases.acquire(binding.binding_id, self.instance_id)
            except LeaseError:
                continue
            try:
                scheduled = await self.schedule_binding(
                    binding.binding_id, lease_generation=int(lease["generation"])
                )
            finally:
                self.leases.release(
                    binding.binding_id, self.instance_id,
                    generation=int(lease["generation"]),
                )
            if scheduled is not None and scheduled.get("queued") is not True:
                break
        return {"scanned": scanned, "scheduled": scheduled}
