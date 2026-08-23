"""Reconcile managed-thread wake readiness. No automatic turn/steer."""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Any, Iterator

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
from .scheduler_leases import LeaseError, SchedulerLeases
from .semantic_bridge import SemanticBridge, SemanticBridgeError
from .transport import TransportClosed
from .wake_batches import WakeBatchStore


class WakeIncidentError(RuntimeError):
    """Raised when an operator cannot legally resolve a wake incident."""


async def _legacy_confirm_if_loaded(recovery, binding_id, effect_id, journal):
    """Observe/reconcile a pre-cutover resume without creating a new send."""

    from .durability.reconciliation import EffectReconciler
    from .durability.session_owner import AppServerSessionOwner

    owner = AppServerSessionOwner.for_client(recovery.client, recovery.bindings.store)
    readiness = await recovery.classify(binding_id)
    try:
        await EffectReconciler(recovery.bindings.store.connection, owner).reconcile(
            effect_id
        )
    except Exception:
        if readiness is ThreadWakeReadiness.IDLE_LOADED:
            try:
                journal.confirm_effect(effect_id, evidence_ref="resume:idle_loaded")
            except Exception:
                pass
    return readiness


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

    async def resume_once(
        self, binding_id: str, *, wake_batch_id: str | None = None
    ) -> ThreadWakeReadiness:
        from .durability.effects import EffectJournal
        from .durability.reconciliation import EffectReconciler
        from .durability.session_owner import AppServerSessionOwner
        from .durability.transaction import DurabilityTransaction

        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id or self.client is None:
            return ThreadWakeReadiness.UNKNOWN
        journal = EffectJournal(self.bindings.store.connection)
        if wake_batch_id is None:
            # Compatibility is reconciliation-only.  A new resume submission
            # always requires a wake batch's exact durable context tuple.
            legacy = journal.get_by_key(
                "thread/resume", f"thread/resume:{binding.thread_id}"
            )
            if legacy is not None and legacy.state != "PREPARED":
                return await _legacy_confirm_if_loaded(
                    self, binding_id, legacy.effect_id, journal
                )
            return ThreadWakeReadiness.UNKNOWN
        context_row = self._wake_context(binding_id, wake_batch_id)
        if context_row is None:
            self._cancel_resume_and_wake(
                wake_batch_id, None, cause_ref="missing_or_ambiguous_context_binding"
            )
            return ThreadWakeReadiness.UNKNOWN
        client_key = f"thread/resume:{binding.thread_id}:{wake_batch_id}"
        existing = journal.get_by_key("thread/resume", client_key)

        async def _confirm_if_loaded(effect_id: str) -> ThreadWakeReadiness:
            owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
            readiness = await self.classify(binding_id)
            if readiness is ThreadWakeReadiness.IDLE_LOADED:
                try:
                    await EffectReconciler(self.bindings.store.connection, owner).reconcile(effect_id)
                except Exception:
                    try:
                        journal.confirm_effect(effect_id, evidence_ref="resume:idle_loaded")
                    except Exception:
                        pass
            else:
                try:
                    await EffectReconciler(self.bindings.store.connection, owner).reconcile(effect_id)
                except Exception:
                    pass
            return readiness

        if existing is not None and existing.state != "PREPARED":
            return await _confirm_if_loaded(existing.effect_id)
        if existing is None:
            try:
                with self.bindings.store._lock, DurabilityTransaction(
                    self.bindings.store.connection
                ):
                    self.bindings.require_exact_binding_in_transaction(
                        binding_id,
                        expected_state=BindingState.ACTIVE,
                        actor_context_id=binding.actor_context_id,
                        actor_kind=binding.actor_kind.value,
                        semantic_scope_key=binding.semantic_scope_key,
                        thread_id=binding.thread_id,
                        direction_id=binding.direction_id,
                    )
                    existing = journal.prepare_effect(
                        owner_kind="THREAD_RESUME",
                        owner_id=binding_id,
                        binding_id=binding_id,
                        method="thread/resume",
                        client_key=client_key,
                        request={"threadId": binding.thread_id},
                    )
            except Exception:
                self._cancel_resume_and_wake(
                    wake_batch_id,
                    None,
                    cause_ref="wake_resume_binding_not_active",
                )
                return ThreadWakeReadiness.UNKNOWN
        owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
        try:
            def _binding_hook(connection) -> None:
                self.bindings.require_exact_binding_in_transaction(
                    binding_id,
                    expected_state=BindingState.ACTIVE,
                    actor_context_id=binding.actor_context_id,
                    actor_kind=binding.actor_kind.value,
                    semantic_scope_key=binding.semantic_scope_key,
                    thread_id=binding.thread_id,
                    direction_id=binding.direction_id,
                )
                batch = connection.execute(
                    "SELECT state FROM wake_batches WHERE wake_batch_id = ? AND binding_id = ?",
                    (wake_batch_id, binding_id),
                ).fetchone()
                if batch is None or str(batch["state"]) != WakeBatchState.PREPARED.value:
                    raise WakeIncidentError("wake batch is not PREPARED at resume write start")
                rows = connection.execute(
                    """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
                    FROM managed_context_injections
                    WHERE turn_intent_id = ? AND binding_id = ?
                    ORDER BY created_at, injection_id""",
                    (wake_batch_id, binding_id),
                ).fetchall()
                if len(rows) != 1 or tuple(rows[0]) != tuple(context_row):
                    raise WakeIncidentError(
                        "wake context binding changed before resume write start"
                    )

            result = await owner.submit_effect(
                existing.effect_id,
                extra_hooks=[_binding_hook],
                pre_write_guard=lambda: self._resume_semantic_guard(
                    binding, context_row
                ),
            )
            kind = owner.classify_submission(result)
        except SemanticBridgeError:
            self._cancel_resume_and_wake(
                wake_batch_id,
                existing.effect_id,
                cause_ref="wake_resume_semantic_drift",
            )
            return ThreadWakeReadiness.UNKNOWN
        except Exception as exc:
            # A guard failure occurs before WRITE_STARTED and is safely
            # cancellable.  Transport failures after that boundary remain
            # uncertain and are handled below rather than requeued.
            current = journal.get(existing.effect_id)
            if current.state == "PREPARED":
                self._cancel_resume_and_wake(
                    wake_batch_id,
                    existing.effect_id,
                    cause_ref="wake_resume_prewrite_guard_failed",
                )
                return ThreadWakeReadiness.UNKNOWN
            if isinstance(exc, UnexpectedServerRequest):
                return ThreadWakeReadiness.UNKNOWN
            if isinstance(exc, (AppServerRpcError, TransportClosed, asyncio.TimeoutError)):
                return ThreadWakeReadiness.UNKNOWN
            raise
        if kind != "observed":
            return await self.classify(binding_id)
        return await _confirm_if_loaded(existing.effect_id)

    def _wake_context(self, binding_id: str, wake_batch_id: str):
        rows = self.bindings.store.connection.execute(
            """SELECT checkpoint_id, state_version, epoch_id, epoch_revision
            FROM managed_context_injections
            WHERE turn_intent_id = ? AND binding_id = ?
            ORDER BY created_at, injection_id""",
            (wake_batch_id, binding_id),
        ).fetchall()
        return rows[0] if len(rows) == 1 else None

    @contextmanager
    def _resume_semantic_guard(self, binding, context_row) -> Iterator[object]:
        bridge = self.bridge or getattr(self.bindings, "bridge", None)
        if bridge is None:
            raise WakeIncidentError("wake resume has no semantic bridge")
        with bridge.currentness_guard(
            binding.actor_context_id,
            checkpoint_id=context_row["checkpoint_id"],
            state_version=int(context_row["state_version"] or 0),
            epoch_id=context_row["epoch_id"],
            epoch_revision=(
                None
                if context_row["epoch_revision"] is None
                else int(context_row["epoch_revision"])
            ),
        ) as snapshot:
            if (
                snapshot.actor_kind != binding.actor_kind.value
                or snapshot.scope_key != binding.semantic_scope_key
            ):
                raise WakeIncidentError("wake resume actor identity changed")
            yield snapshot

    def _cancel_resume_and_wake(
        self,
        wake_batch_id: str,
        effect_id: str | None,
        *,
        cause_ref: str,
    ) -> None:
        from .durability.effects import EffectJournal, cancel_prepared_wake
        from .durability.transaction import DurabilityTransaction

        with self.bindings.store._lock, DurabilityTransaction(
            self.bindings.store.connection
        ):
            EffectJournal(self.bindings.store.connection).cancel_prepared_if_present(
                effect_id, cause_ref=cause_ref
            )
            cancel_prepared_wake(
                self.bindings.store.connection,
                wake_batch_id,
                cause_ref=cause_ref,
            )

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
        from .durability.reconciliation import EffectReconciler
        from .durability.session_owner import AppServerSessionOwner

        batch = self.batches.get(wake_batch_id)
        if batch is None:
            raise RuntimeError(f"unknown wake batch: {wake_batch_id}")
        state = WakeBatchState(str(batch["state"]))
        effect_id = str(batch.get("effect_id") or "")
        if state is WakeBatchState.PREPARED:
            from .durability.effects import cancel_prepared_wake

            updated = cancel_prepared_wake(
                self.bindings.store.connection,
                wake_batch_id,
                cause_ref="restart-prepared",
            )
            self._record_attempt(wake_batch_id, WakeAttemptOutcome.CANCELLED)
            return updated
        if effect_id and self.client is not None and state in {
            WakeBatchState.SUBMITTING,
            WakeBatchState.SUBMITTED,
            WakeBatchState.SUBMISSION_UNCERTAIN,
            WakeBatchState.ACTIVE,
        }:
            owner = AppServerSessionOwner.for_client(self.client, self.bindings.store)
            try:
                await EffectReconciler(self.bindings.store.connection, owner).reconcile(effect_id)
            except Exception:
                pass
            batch = self.batches.get(wake_batch_id)
            assert batch is not None
            state = WakeBatchState(str(batch["state"]))
        if state is WakeBatchState.ACTIVE:
            return await self._reconcile_active(wake_batch_id, batch)
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
            from .durability.effects import EffectJournal
            from .durability.models import AggregateKind, TransitionCause, TransitionRequest
            from .durability.transaction import DurabilityTransaction
            from .durability.transitions import TransitionError, TransitionKernel

            effect_id = str(batch.get("effect_id") or "")
            kernel = TransitionKernel(self.bindings.store.connection)
            journal = EffectJournal(self.bindings.store.connection)
            now = datetime.now(timezone.utc).isoformat()
            with DurabilityTransaction(self.bindings.store.connection):
                if effect_id:
                    from .durability.effects import effect_is_completion_ready

                    effect = journal.get(effect_id)
                    if effect.state in {"RESPONSE_OBSERVED", "SUBMISSION_UNCERTAIN", "WRITE_STARTED"}:
                        turn_ref = str(batch.get("app_server_turn_id") or status)
                        journal.confirm_effect(effect_id, evidence_ref=f"turn:{turn_ref}:{status}")
                    if not effect_is_completion_ready(self.bindings.store.connection, effect_id):
                        raise RuntimeError("wake completion requires EFFECT_CONFIRMED")
                current = self.batches.get(wake_batch_id)
                assert current is not None
                kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.WAKE_BATCH,
                        aggregate_id=wake_batch_id,
                        expected_state=WakeBatchState.ACTIVE.value,
                        expected_version=int(current["version"] or 0),
                        target_state=WakeBatchState.COMPLETED.value,
                        cause_kind=TransitionCause.APP_SERVER_EVENT,
                        cause_ref=status,
                        field_updates={"completion_status": status, "completed_at": now},
                    )
                )
                rows = self.bindings.store.connection.execute(
                    """SELECT m.message_id, m.delivery_state, m.delivery_version
                    FROM mailbox_messages m
                    JOIN wake_batch_messages b ON b.message_id = m.message_id
                    WHERE b.wake_batch_id = ?""",
                    (wake_batch_id,),
                ).fetchall()
                for row in rows:
                    delivery = str(row["delivery_state"])
                    if delivery not in {"BATCHED", "SUBMISSION_UNCERTAIN"}:
                        continue
                    kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                            aggregate_id=str(row["message_id"]),
                            expected_state=delivery,
                            expected_version=int(row["delivery_version"] or 0),
                            target_state="DELIVERED_TO_TURN",
                            cause_kind=TransitionCause.APP_SERVER_EVENT,
                            cause_ref=status,
                        )
                    )
            self._record_attempt(wake_batch_id, WakeAttemptOutcome.RECONCILED)
            updated = self.batches.get(wake_batch_id)
            assert updated is not None
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
