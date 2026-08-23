"""Submit at most one idle-thread wake batch. Never blind-retry."""

from __future__ import annotations

import asyncio
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired, UnexpectedServerRequest
from .mailbox_models import ThreadWakeReadiness, WakeAttemptOutcome, WakeBatchState
from .mailbox_store import MailboxStore
from .managed_models import BindingState, ManagedActorKind
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import (
    SemanticActorEligibilityError,
    SemanticBridge,
    SemanticBridgeError,
)
from .semantic_scanner import SemanticScanner
from .transport import TransportClosed
from .wake_batches import WakeBatchStore
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
        self.recovery.bridge = bridge

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
        """Cancel/requeue only; plain snapshot failures never suspend actors."""

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
                cause_ref="prewrite-snapshot-failed",
            )

    def _contain_guarded_ineligible_actor(self, binding_id: str, wake_batch_id: str) -> None:
        """Atomically suspend and cancel only after typed guarded ineligibility."""

        from .durability.effects import cancel_prepared_wake
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionKernel

        with self.bindings.store._lock, DurabilityTransaction(
            self.bindings.store.connection
        ):
            row = self.bindings.store.connection.execute(
                "SELECT binding_state, version FROM managed_actor_bindings WHERE binding_id = ?",
                (binding_id,),
            ).fetchone()
            if row is not None and str(row["binding_state"]) == BindingState.ACTIVE.value:
                TransitionKernel(self.bindings.store.connection).apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_BINDING,
                        aggregate_id=binding_id,
                        expected_state=BindingState.ACTIVE.value,
                        expected_version=int(row["version"] or 0),
                        target_state=BindingState.SUSPENDED.value,
                        cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                        cause_ref="guarded_actor_ineligible",
                        field_updates={"suspended_at": _now()},
                    )
                )
            cancel_prepared_wake(
                self.bindings.store.connection,
                wake_batch_id,
                cause_ref="guarded_actor_ineligible",
            )

    def _cancel_currentness_drift(self, wake_batch_id: str, reason: str) -> None:
        from .durability.effects import cancel_prepared_wake

        cancel_prepared_wake(
            self.bindings.store.connection,
            wake_batch_id,
            cause_ref=reason,
        )

    def _contain_raw_submit_failure(self, wake_batch_id: str, effect_id: str) -> str:
        """Cancel only an exactly PREPARED effect after an unexpected submit failure.

        The state observation and prepared-wake cancellation share one immediate
        transaction.  Any unknown/crossed state or containment failure therefore
        fails closed without making a second requeue decision.
        """

        from .durability.effects import cancel_prepared_wake
        from .durability.transaction import DurabilityTransaction

        connection = self.bindings.store.connection
        with self.bindings.store._lock:
            if connection.in_transaction:
                raise WakeSchedulerError(
                    "wake submit containment cannot own the durability transaction"
                )
            with DurabilityTransaction(connection):
                effect_row = connection.execute(
                    "SELECT state FROM app_server_effects WHERE effect_id = ?",
                    (effect_id,),
                ).fetchone()
                if effect_row is None:
                    raise WakeSchedulerError(
                        "wake submit containment cannot establish the linked effect state"
                    )
                effect_state = str(effect_row["state"])
                if effect_state != "PREPARED":
                    return effect_state

                cancel_prepared_wake(
                    connection,
                    wake_batch_id,
                    cause_ref="raw_prewrite_submit_failure",
                )
                final_effect = connection.execute(
                    "SELECT state FROM app_server_effects WHERE effect_id = ?",
                    (effect_id,),
                ).fetchone()
                final_batch = connection.execute(
                    "SELECT state FROM wake_batches WHERE wake_batch_id = ?",
                    (wake_batch_id,),
                ).fetchone()
                noneligible_messages = int(
                    connection.execute(
                        """SELECT COUNT(*)
                        FROM mailbox_messages m
                        JOIN wake_batch_messages b ON b.message_id = m.message_id
                        WHERE b.wake_batch_id = ? AND m.delivery_state <> 'ELIGIBLE'""",
                        (wake_batch_id,),
                    ).fetchone()[0]
                )
                if (
                    final_effect is None
                    or str(final_effect["state"]) != "CANCELLED_BEFORE_WRITE"
                    or final_batch is None
                    or str(final_batch["state"]) != WakeBatchState.CANCELLED.value
                    or noneligible_messages != 0
                ):
                    raise WakeSchedulerError(
                        "wake submit containment did not reach the exact cancelled/requeued state"
                    )
                return "CANCELLED_BEFORE_WRITE"

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
        context_row = None
        if wake_batch_id is not None:
            rows = self.bindings.store.connection.execute(
                """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
                FROM managed_context_injections
                WHERE turn_intent_id = ? AND binding_id = ?
                ORDER BY created_at, injection_id""",
                (wake_batch_id, binding_id),
            ).fetchall()
            if len(rows) != 1:
                self._cancel_currentness_drift(wake_batch_id, "missing_or_ambiguous_context_binding")
                raise WakeSchedulerError("wake batch has no exact durable context binding")
            context_row = rows[0]
        try:
            snapshot = self.bridge.snapshot(binding.actor_context_id)
        except SemanticBridgeError as exc:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError(str(exc)) from exc
        if snapshot.actor_kind != binding.actor_kind.value:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError("actor kind no longer matches binding")
        if snapshot.scope_key != binding.semantic_scope_key:
            self._abort_unsubmitted_wake(binding_id, wake_batch_id)
            raise WakeSchedulerError("actor scope no longer matches binding")
        if context_row is not None:
            row = context_row
            expected = (
                row["checkpoint_id"],
                None if row["state_version"] is None else int(row["state_version"]),
                row["epoch_id"],
                None if row["epoch_revision"] is None else int(row["epoch_revision"]),
            )
            actual = (
                snapshot.checkpoint_id,
                snapshot.state_version,
                snapshot.epoch_id,
                snapshot.epoch_revision,
            )
            if actual != expected:
                self._cancel_currentness_drift(wake_batch_id, "semantic_currentness_mismatch")
                raise WakeSchedulerError("wake batch semantic currentness no longer matches")

    @contextmanager
    def _semantic_write_guard(
        self,
        *,
        binding_id: str,
        generation: int,
        wake_batch_id: str,
    ) -> Iterator[object]:
        self.leases.assert_held(binding_id, self.instance_id, generation)
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.ACTIVE:
            raise WakeSchedulerError("binding is not ACTIVE")
        rows = self.bindings.store.connection.execute(
            """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
            FROM managed_context_injections
            WHERE turn_intent_id = ? AND binding_id = ?
            ORDER BY created_at, injection_id""",
            (wake_batch_id, binding_id),
        ).fetchall()
        if len(rows) != 1:
            raise WakeSchedulerError("wake batch has no exact durable context binding")
        expected = rows[0]
        with self.bridge.currentness_guard(
            binding.actor_context_id,
            checkpoint_id=expected["checkpoint_id"],
            state_version=(
                None if expected["state_version"] is None else int(expected["state_version"])
            ),
            epoch_id=expected["epoch_id"],
            epoch_revision=(
                None
                if expected["epoch_revision"] is None
                else int(expected["epoch_revision"])
            ),
        ) as snapshot:
            if snapshot.actor_kind != binding.actor_kind.value:
                raise WakeSchedulerError("actor kind no longer matches binding")
            if snapshot.scope_key != binding.semantic_scope_key:
                raise WakeSchedulerError("actor scope no longer matches binding")
            yield snapshot

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
        binding = self.bindings.get(str(batch["binding_id"]))
        if binding is None:
            raise WakeSchedulerError("wake binding is missing")
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
            binding_row = connection.execute(
                "SELECT * FROM managed_actor_bindings WHERE binding_id = ?",
                (str(batch["binding_id"]),),
            ).fetchone()
            if binding_row is None:
                raise WakeSchedulerError("binding is missing at wake write start")
            self.bindings.require_exact_binding_in_transaction(
                str(batch["binding_id"]),
                expected_state=BindingState.ACTIVE,
                actor_context_id=binding.actor_context_id,
                actor_kind=binding.actor_kind.value,
                semantic_scope_key=binding.semantic_scope_key,
                thread_id=str(batch["thread_id"]),
                direction_id=binding.direction_id,
            )
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
                request_override=params,
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
                pre_write_guard=lambda: self._semantic_write_guard(
                    binding_id=str(batch["binding_id"]),
                    generation=generation,
                    wake_batch_id=wake_batch_id,
                ),
            )
            response = dict(submitted.response or {})
        except SemanticActorEligibilityError as exc:
            from .durability.effects import EffectJournal

            if EffectJournal(self.bindings.store.connection).get(effect_id).state == "PREPARED":
                self._contain_guarded_ineligible_actor(
                    str(batch["binding_id"]), wake_batch_id
                )
            raise WakeSchedulerError(str(exc)) from exc
        except SemanticBridgeError as exc:
            from .durability.effects import EffectJournal

            if EffectJournal(self.bindings.store.connection).get(effect_id).state == "PREPARED":
                self._cancel_currentness_drift(wake_batch_id, "semantic_currentness_mismatch")
            raise WakeSchedulerError(str(exc)) from exc
        except WakeSchedulerError:
            from .durability.effects import EffectJournal

            if EffectJournal(self.bindings.store.connection).get(effect_id).state == "PREPARED":
                self._cancel_currentness_drift(wake_batch_id, "pre_write_fence_failed")
            raise
        except LeaseError:
            from .durability.effects import EffectJournal

            if EffectJournal(self.bindings.store.connection).get(effect_id).state == "PREPARED":
                self._cancel_currentness_drift(wake_batch_id, "lease_lost_before_write")
            raise
        except RetryRequired as exc:
            self._mark_uncertain(wake_batch_id, {"reason": "overload"})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        except UnexpectedServerRequest as exc:
            raise WakeSchedulerError("wake turn/start incident; do not retry") from exc
        except (AppServerRpcError, TransportClosed, asyncio.TimeoutError) as exc:
            self._mark_uncertain(wake_batch_id, {"reason": type(exc).__name__})
            raise WakeSchedulerError("wake turn/start uncertain; do not retry") from exc
        except Exception as exc:
            try:
                effect_state = self._contain_raw_submit_failure(wake_batch_id, effect_id)
            except Exception as containment_exc:
                raise WakeSchedulerError(
                    "wake submit failure containment failed closed; "
                    f"{type(containment_exc).__name__}: {containment_exc}; do not retry"
                ) from exc
            if effect_state == "CANCELLED_BEFORE_WRITE":
                raise WakeSchedulerError(
                    f"wake submit failed before write and was cancelled: {exc}"
                ) from exc
            raise WakeSchedulerError(
                "wake turn/start uncertain after linked effect reached "
                f"{effect_state}; do not retry"
            ) from exc
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
        current = self.batches.get(wake_batch_id)
        if current is None:
            raise WakeSchedulerError("unknown wake batch")
        if current["state"] == WakeBatchState.INCIDENT.value:
            raise WakeSchedulerError("incident is terminal; operator recovery required")
        if current["state"] != WakeBatchState.ACTIVE.value:
            raise WakeSchedulerError("only ACTIVE wake batches may complete")
        effect_id = str(current.get("effect_id") or "")
        if effect_id:
            from .durability.effects import effect_is_completion_ready

            if not effect_is_completion_ready(self.bindings.store.connection, effect_id):
                raise WakeSchedulerError(
                    "completion requires EFFECT_CONFIRMED or TURN_OBSERVED operator-resolved effect"
                )
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
        if readiness not in {
            ThreadWakeReadiness.IDLE_NOT_LOADED,
            ThreadWakeReadiness.IDLE_LOADED,
        }:
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
        if readiness is ThreadWakeReadiness.IDLE_NOT_LOADED:
            readiness = await self.recovery.resume_once(
                binding_id, wake_batch_id=str(batch["wake_batch_id"])
            )
            if readiness is not ThreadWakeReadiness.IDLE_LOADED:
                return {"binding_id": binding_id, "readiness": readiness.value, "resumed": False}
        if readiness is not ThreadWakeReadiness.IDLE_LOADED:
            return {"binding_id": binding_id, "readiness": readiness.value}
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
