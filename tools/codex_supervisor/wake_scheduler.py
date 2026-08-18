"""Submit at most one idle-thread wake batch. Never blind-retry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired
from .mailbox_models import ThreadWakeReadiness, WakeAttemptOutcome, WakeBatchState
from .mailbox_store import MailboxStore
from .managed_models import BindingState, ManagedActorKind
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import SemanticBridge
from .semantic_scanner import SemanticScanner
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

    async def submit_batch(self, wake_batch_id: str, input_text: str) -> dict[str, object]:
        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise WakeSchedulerError("unknown wake batch")
        if batch["state"] != WakeBatchState.PREPARED.value:
            raise WakeSchedulerError("wake batch is not PREPARED")
        if self.client is None:
            raise WakeSchedulerError("client required to submit a wake")
        attempts = self.bindings.store.connection.execute(
            "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id = ? AND outcome = ?",
            (wake_batch_id, WakeAttemptOutcome.SUBMITTED.value),
        ).fetchone()[0]
        if int(attempts) > 0:
            raise WakeSchedulerError("wake batch already has a submission attempt")
        params = {
            "threadId": batch["thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
            "clientUserMessageId": batch["client_user_message_id"],
        }
        try:
            response = await self.client.request("turn/start", params)
        except RetryRequired as exc:
            self._mark_uncertain(wake_batch_id, {"reason": "overload"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        except (AppServerRpcError, TransportClosed) as exc:
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
        )
        for message in self.batches.messages_for(wake_batch_id):
            self.mailbox.mark_delivered(message.message_id)
        self.recovery._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.SUBMITTED,
            request_id=str(response.get("id") or ""),
        )
        return updated

    def _mark_uncertain(self, wake_batch_id: str, error: dict[str, object]) -> None:
        self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.SUBMISSION_UNCERTAIN.value,
            incident_json=json.dumps(error),
        )
        for message in self.batches.messages_for(wake_batch_id):
            self.mailbox.mark_uncertain(message.message_id)
        self.recovery._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.SUBMISSION_UNCERTAIN,
            error=error,
        )

    def observe_completion(self, wake_batch_id: str, status: str) -> dict[str, object]:
        return self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.COMPLETED.value,
            completion_status=status,
            completed_at=_now(),
        )

    async def schedule_binding(self, binding_id: str) -> dict[str, object] | None:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE or not binding.thread_id:
            return None
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
            readiness = await self.recovery.resume_once(binding_id)
            if readiness is not ThreadWakeReadiness.IDLE_LOADED:
                return {"binding_id": binding_id, "readiness": readiness.value, "resumed": False}
        if readiness is not ThreadWakeReadiness.IDLE_LOADED:
            return {"binding_id": binding_id, "readiness": readiness.value}
        snapshot = self.bridge.snapshot(binding.actor_context_id)
        batch = self.batches.prepare(
            binding_id=binding_id,
            thread_id=binding.thread_id,
            snapshot=snapshot,
            messages=messages,
        )
        submitted = await self.submit_batch(str(batch["wake_batch_id"]), str(batch["input_text"]))
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
                self.leases.acquire(binding.binding_id, self.instance_id)
            except LeaseError:
                continue
            try:
                scheduled = await self.schedule_binding(binding.binding_id)
            finally:
                self.leases.release(binding.binding_id, self.instance_id)
            if scheduled is not None and scheduled.get("queued") is not True:
                break
        return {"scanned": scanned, "scheduled": scheduled}
