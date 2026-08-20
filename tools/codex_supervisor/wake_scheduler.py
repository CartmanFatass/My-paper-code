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
        if batch is None:
            return
        if str(batch["state"]) == WakeBatchState.PREPARED.value:
            from .durability.effects import cancel_prepared_wake

            cancel_prepared_wake(
                self.bindings.store.connection,
                wake_batch_id,
                cause_ref="actor-ineligible",
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
        params = {
            "threadId": batch["thread_id"],
            "input": [{"type": "text", "text": input_text}],
            "approvalPolicy": "never",
            "clientUserMessageId": batch["client_user_message_id"],
        }
        effect_id = str(batch.get("effect_id") or "")
        if not effect_id:
            raise WakeSchedulerError("wake batch has no linked effect")
        from .durability.effects import EffectJournal
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.session_owner import AppServerSessionOwner
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionError, TransitionKernel

        self.bindings.store.connection.execute(
            "UPDATE app_server_effects SET request_json = ? WHERE effect_id = ? AND state = 'PREPARED'",
            (json.dumps(params, sort_keys=True, separators=(",", ":")), effect_id),
        )
        holder = self.instance_id
        version = int(batch.get("version") or 0)

        def _lease_and_attempt(connection) -> None:
            current = connection.execute(
                """SELECT state, lease_holder, lease_generation FROM wake_batches
                WHERE wake_batch_id = ?""",
                (wake_batch_id,),
            ).fetchone()
            if (
                current is None
                or str(current["state"]) != WakeBatchState.PREPARED.value
                or current["lease_holder"] != holder
                or current["lease_generation"] != generation
            ):
                raise WakeSchedulerError("wake batch is not PREPARED for this lease")
            import uuid

            connection.execute(
                """INSERT INTO wake_attempts (
                    wake_attempt_id, wake_batch_id, attempt_number, request_id,
                    outcome, error_json, created_at
                ) VALUES (?, ?, 1, NULL, ?, NULL, ?)""",
                (
                    f"watt_{uuid.uuid4().hex}",
                    wake_batch_id,
                    WakeAttemptOutcome.SUBMITTING.value,
                    _now(),
                ),
            )

        owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
        try:
            self._assert_submit_fence(str(batch["binding_id"]), generation, wake_batch_id=wake_batch_id)
            submitted = await owner.submit_effect(
                effect_id,
                extra_transitions=[
                    TransitionRequest(
                        aggregate_kind=AggregateKind.WAKE_BATCH,
                        aggregate_id=wake_batch_id,
                        expected_state=WakeBatchState.PREPARED.value,
                        expected_version=version,
                        target_state=WakeBatchState.SUBMITTING.value,
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref=effect_id,
                    )
                ],
                extra_hooks=[_lease_and_attempt],
            )
            response = dict(submitted.response or {})
        except RetryRequired as exc:
            self._mark_uncertain(wake_batch_id, {"reason": "overload"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        except UnexpectedServerRequest as exc:
            raise WakeSchedulerError("wake turn/start incident; do not retry") from exc
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError) as exc:
            self._mark_uncertain(wake_batch_id, {"reason": type(exc).__name__})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        kind = owner.classify_submission(submitted)
        current = self.batches.get(wake_batch_id)
        if current is None:
            raise WakeSchedulerError("unknown wake batch")
        if kind == "incident" or current["state"] == WakeBatchState.INCIDENT.value:
            raise WakeSchedulerError("wake turn/start incident; do not retry")
        if kind == "uncertain":
            self._mark_uncertain(wake_batch_id, {"reason": "timeout"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry")
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turn_id = turn.get("id")
        if not turn_id:
            self._mark_uncertain(wake_batch_id, {"reason": "missing_turn"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry")
        now = _now()
        current = self.batches.get(wake_batch_id)
        assert current is not None
        try:
            with self.bindings.store._lock:
                with DurabilityTransaction(self.bindings.store.connection):
                    journal = EffectJournal(self.bindings.store.connection)
                    kernel = TransitionKernel(self.bindings.store.connection)
                    journal.confirm_effect(effect_id, evidence_ref=f"turn:{turn_id}")
                    submitted_row = kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.WAKE_BATCH,
                            aggregate_id=wake_batch_id,
                            expected_state=WakeBatchState.SUBMITTING.value,
                            expected_version=int(current["version"] or 0),
                            target_state=WakeBatchState.SUBMITTED.value,
                            cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                            cause_ref=effect_id,
                            field_updates={"app_server_turn_id": turn_id, "submitted_at": now},
                        )
                    )
                    kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.WAKE_BATCH,
                            aggregate_id=wake_batch_id,
                            expected_state=WakeBatchState.SUBMITTED.value,
                            expected_version=submitted_row.to_version,
                            target_state=WakeBatchState.ACTIVE.value,
                            cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                            cause_ref=effect_id,
                            field_updates={"observed_at": now},
                        )
                    )
                    message_rows = self.bindings.store.connection.execute(
                        """SELECT m.message_id, m.delivery_state, m.delivery_version
                        FROM mailbox_messages m
                        JOIN wake_batch_messages b ON b.message_id = m.message_id
                        WHERE b.wake_batch_id = ?""",
                        (wake_batch_id,),
                    ).fetchall()
                    for message in message_rows:
                        if str(message["delivery_state"]) not in {"BATCHED", "SUBMISSION_UNCERTAIN"}:
                            continue
                        kernel.apply(
                            TransitionRequest(
                                aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                                aggregate_id=str(message["message_id"]),
                                expected_state=str(message["delivery_state"]),
                                expected_version=int(message["delivery_version"] or 0),
                                target_state="DELIVERED_TO_TURN",
                                cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                                cause_ref=effect_id,
                            )
                        )
        except TransitionError as exc:
            raise WakeSchedulerError(str(exc)) from exc
        owner.release_open_effect(effect_id)
        self.recovery._record_attempt(
            wake_batch_id,
            WakeAttemptOutcome.SUBMITTED,
            request_id=str(response.get("id") or ""),
        )
        updated = self.batches.get(wake_batch_id)
        assert updated is not None
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
        from .durability.effects import EffectJournal

        current = self.batches.get(wake_batch_id)
        if current is None:
            raise WakeSchedulerError("unknown wake batch")
        if current["state"] == WakeBatchState.INCIDENT.value:
            raise WakeSchedulerError("incident is terminal; operator recovery required")
        if current["state"] != WakeBatchState.ACTIVE.value:
            raise WakeSchedulerError("only ACTIVE wake batches may complete")
        effect_id = str(current.get("effect_id") or "")
        if effect_id:
            effect = EffectJournal(self.bindings.store.connection).get(effect_id)
            if effect.state != "EFFECT_CONFIRMED":
                raise WakeSchedulerError("completion requires EFFECT_CONFIRMED linked effect")
        updated = self.batches.set_state(
            wake_batch_id,
            state=WakeBatchState.COMPLETED.value,
            completion_status=status,
            completed_at=_now(),
            expected_state=WakeBatchState.ACTIVE.value,
        )
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
