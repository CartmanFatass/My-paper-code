"""Submit at most one idle-thread wake batch. Never blind-retry."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired, UnexpectedServerRequest
from .mailbox_models import ThreadWakeReadiness, WakeAttemptOutcome, WakeBatchState
from .mailbox_store import MailboxStore
from .managed_models import BindingState, ManagedActorKind
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import SemanticBridge, SemanticBridgeError
from .semantic_scanner import SemanticScanner
from .session_guard import SessionGuard
from .transport import TransportClosed
from .wake_batches import WakeBatchError, WakeBatchStore
from .wake_recovery import WakeRecovery


class WakeSchedulerError(RuntimeError):
    """Raised when a wake cannot be submitted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        if self.recovery.leases is None:
            self.recovery.leases = leases
        self.recovery.instance_id = instance_id

    def _sender_kinds(self) -> dict[str, str | None]:
        kinds: dict[str, str | None] = {}
        for binding in self.bindings.list_bindings():
            kinds[binding.actor_context_id] = binding.actor_kind.value
        return kinds

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

    def _abort_unsubmitted_wake(self, binding_id: str, wake_batch_id: str | None) -> None:
        try:
            self.bindings.suspend(binding_id)
        except Exception:
            pass
        if not wake_batch_id:
            return
        batch = self.batches.get(wake_batch_id)
        if batch is None or str(batch["state"]) not in {
            WakeBatchState.PREPARED.value,
            WakeBatchState.SUBMITTING.value,
        }:
            return
        for message in self.batches.messages_for(wake_batch_id):
            if message.delivery_state.value == "BATCHED":
                self.mailbox.return_to_eligible(message.message_id)
        self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.CANCELLED.value,
            expected_state=str(batch["state"]),
        )

    def _assert_submit_fence(
        self,
        binding_id: str,
        generation: int,
        *,
        wake_batch_id: str | None = None,
    ) -> None:
        self.leases.assert_held(binding_id, self.instance_id, generation)
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE:
            raise WakeSchedulerError("binding is not ACTIVE")
        try:
            actor = self.bridge.require_eligible(binding.actor_context_id)
        except SemanticBridgeError as exc:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError(str(exc)) from exc
        if actor.actor_kind.value != binding.actor_kind.value:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError("actor kind no longer matches binding")
        if actor.scope_key != binding.semantic_scope_key:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError("actor scope no longer matches binding")

    def begin_submission(
        self,
        wake_batch_id: str,
        *,
        lease_holder: object = None,
        lease_generation: object = None,
    ) -> dict[str, object]:
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise WakeSchedulerError("unknown wake batch")
        if batch["state"] != WakeBatchState.PREPARED.value:
            raise WakeSchedulerError("wake batch is not PREPARED")
        holder = lease_holder if lease_holder is not None else batch["lease_holder"]
        generation = lease_generation if lease_generation is not None else batch["lease_generation"]
        try:
            return self.batches.claim_first_submission(
                wake_batch_id,
                lease_holder=holder,
                lease_generation=generation,
            )
        except WakeBatchError as exc:
            raise WakeSchedulerError(str(exc)) from exc

    async def submit_batch(
        self,
        wake_batch_id: str,
        input_text: str,
        *,
        lease_generation: int | None = None,
    ) -> dict[str, object]:
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise WakeSchedulerError("unknown wake batch")
        if batch["state"] != WakeBatchState.PREPARED.value:
            raise WakeSchedulerError("wake batch is not PREPARED; reconcile, do not resend")
        if self.client is None:
            raise WakeSchedulerError("client required to submit a wake")
        if lease_generation is None:
            raise WakeSchedulerError("automatic submit requires lease generation")
        generation = int(lease_generation)
        self._assert_submit_fence(str(batch["binding_id"]), generation, wake_batch_id=wake_batch_id)
        self.leases.renew(str(batch["binding_id"]), self.instance_id, generation=generation)
        batch = self.begin_submission(
            wake_batch_id,
            lease_holder=self.instance_id,
            lease_generation=generation,
        )
        params = {
            "threadId": batch["thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": batch["client_user_message_id"],
        }

        def _incident(_payload: object) -> None:
            self.batches.set_state(
                wake_batch_id,
                state=WakeBatchState.INCIDENT.value,
                incident_json=json.dumps({"reason": "server_request"}),
            )
            self.recovery._record_attempt(
                wake_batch_id,
                WakeAttemptOutcome.INCIDENT,
                error={"reason": "server_request"},
            )

        guard = SessionGuard(self.client, self.bindings.store, on_incident=_incident)
        try:
            self._assert_submit_fence(str(batch["binding_id"]), generation, wake_batch_id=wake_batch_id)
            response = await guard.request("turn/start", params)
        except RetryRequired as exc:
            self._mark_uncertain(wake_batch_id, {"reason": "overload"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        except UnexpectedServerRequest as exc:
            raise WakeSchedulerError("wake turn/start incident; do not retry") from exc
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError) as exc:
            self._mark_uncertain(wake_batch_id, {"reason": type(exc).__name__})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turn_id = turn.get("id")
        now = _now()
        updated = self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.ACTIVE.value,
            app_server_turn_id=turn_id,
            submitted_at=now,
            observed_at=now,
            expected_state=WakeBatchState.SUBMITTING.value,
        )
        if updated["state"] == WakeBatchState.INCIDENT.value:
            raise WakeSchedulerError("wake turn/start incident; do not retry")
        for message in self.batches.messages_for(wake_batch_id):
            self.mailbox.mark_delivered(message.message_id)
        self.recovery._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.SUBMITTED,
            request_id=str(response.get("id") or ""),
        )
        return updated

    def _mark_uncertain(self, wake_batch_id: str, error: dict[str, object]) -> None:
        updated = self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.SUBMISSION_UNCERTAIN.value,
            incident_json=json.dumps(error),
            expected_state=WakeBatchState.SUBMITTING.value,
        )
        if updated["state"] == WakeBatchState.INCIDENT.value:
            return
        for message in self.batches.messages_for(wake_batch_id):
            self.mailbox.mark_uncertain(message.message_id)
        self.recovery._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.SUBMISSION_UNCERTAIN,
            error=error,
        )

    def observe_completion(self, wake_batch_id: str, status: str) -> dict[str, object]:
        updated = self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.COMPLETED.value,
            completion_status=status,
            completed_at=_now(),
            expected_state=WakeBatchState.ACTIVE.value,
        )
        if updated["state"] == WakeBatchState.INCIDENT.value:
            raise WakeSchedulerError("incident is terminal; operator recovery required")
        if updated["state"] != WakeBatchState.COMPLETED.value:
            raise WakeSchedulerError("only ACTIVE wake batches may complete")
        return updated

    async def schedule_binding(
        self,
        binding_id: str,
        *,
        lease_generation: int,
    ) -> dict[str, object] | None:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE or not binding.thread_id:
            return None
        self._assert_submit_fence(binding_id, lease_generation)
        if self.batches.open_batch_for_binding(binding_id) is not None:
            return None
        messages = self._eligible_messages(binding_id)
        if not messages:
            return None
        readiness = await self.recovery.classify(binding_id)
        if readiness is ThreadWakeReadiness.ACTIVE_TURN:
            return {"binding_id": binding_id, "readiness": readiness.value, "queued": True}
        if readiness is ThreadWakeReadiness.UNKNOWN:
            return {"binding_id": binding_id, "readiness": readiness.value}
        if readiness is ThreadWakeReadiness.IDLE_NOT_LOADED:
            self._assert_submit_fence(binding_id, lease_generation)
            readiness = await self.recovery.resume_once(binding_id)
            if readiness is not ThreadWakeReadiness.IDLE_LOADED:
                return {"binding_id": binding_id, "readiness": readiness.value, "resumed": False}
        if readiness is not ThreadWakeReadiness.IDLE_LOADED:
            return {"binding_id": binding_id, "readiness": readiness.value}
        self._assert_submit_fence(binding_id, lease_generation)
        self.leases.renew(binding_id, self.instance_id, generation=lease_generation)
        snapshot = self.bridge.snapshot(binding.actor_context_id)
        batch = self.batches.prepare(
            binding_id=binding_id,
            thread_id=binding.thread_id,
            snapshot=snapshot,
            messages=messages,
            lease_generation=lease_generation,
            lease_holder=self.instance_id,
        )
        submitted = await self.submit_batch(
            str(batch["wake_batch_id"]),
            str(batch["input_text"]),
            lease_generation=lease_generation,
        )
        return submitted

    async def once(self) -> dict[str, object]:
        await self.recovery.recover()
        scanned = self.scanner.scan()
        scheduled = None
        for binding in self.bindings.list_bindings():
            if binding.binding_state is not BindingState.ACTIVE:
                continue
            if binding.actor_kind not in {ManagedActorKind.OPERATIONAL_ROOT, ManagedActorKind.PORTFOLIO}:
                continue
            try:
                lease = self.leases.acquire(binding.binding_id, self.instance_id)
            except LeaseError:
                continue
            try:
                scheduled = await self.schedule_binding(
                    binding.binding_id,
                    lease_generation=int(lease["generation"]),
                )
            except LeaseError:
                scheduled = {"binding_id": binding.binding_id, "lease": "lost"}
            finally:
                self.leases.release(binding.binding_id, self.instance_id, generation=int(lease["generation"]))
            if scheduled is not None and scheduled.get("queued") is not True:
                break
        return {"scanned": scanned, "scheduled": scheduled}
