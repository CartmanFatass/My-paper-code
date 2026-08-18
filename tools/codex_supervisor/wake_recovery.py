"""Reconcile managed-thread wake readiness. No automatic turn/steer."""

from __future__ import annotations

import asyncio
from typing import Any

from .binding_store import BindingStore
from .client import AppServerClient, AppServerRpcError, UnexpectedServerRequest
from .mailbox_models import ThreadWakeReadiness, WakeAttemptOutcome, WakeBatchState
from .mailbox_store import MailboxStore
from .managed_models import BindingState
from .mutation_intents import MutationIntentError, MutationIntentStore
from .scheduler_leases import LeaseError, SchedulerLeases
from .session_guard import SessionGuard
from .transport import TransportClosed
from .wake_batches import WakeBatchStore


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

    async def resume_once(self, binding_id: str) -> ThreadWakeReadiness:
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id or self.client is None:
            return ThreadWakeReadiness.UNKNOWN
        client_key = f"thread/resume:{binding.thread_id}"
        existing = self.mutations.get_open("thread/resume", client_key)
        if existing is not None:
            return ThreadWakeReadiness.UNKNOWN
        try:
            intent = self.mutations.begin("thread/resume", client_key, binding_id=binding_id)
        except MutationIntentError:
            return ThreadWakeReadiness.UNKNOWN

        def _incident(_payload: object) -> None:
            self.mutations.mark_incident(str(intent["intent_id"]), "server_request")

        guard = SessionGuard(self.client, self.bindings.store, on_incident=_incident)
        try:
            await guard.request("thread/resume", {"threadId": binding.thread_id})
        except asyncio.TimeoutError:
            self.mutations.mark_uncertain(str(intent["intent_id"]), "timeout")
            return ThreadWakeReadiness.UNKNOWN
        except UnexpectedServerRequest:
            return ThreadWakeReadiness.UNKNOWN
        except (AppServerRpcError, TransportClosed):
            self.mutations.mark_uncertain(str(intent["intent_id"]), "transport")
            return ThreadWakeReadiness.UNKNOWN
        self.mutations.mark_submitted(str(intent["intent_id"]))
        return await self.classify(binding_id)

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

                    self.batches.set_state(
                        wake_batch_id,
                        state=WakeBatchState.ACTIVE.value,
                        app_server_turn_id=turn_id,
                        observed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    for message in self.batches.messages_for(wake_batch_id):
                        if message.delivery_state.value != "DELIVERED_TO_TURN":
                            self.mailbox.mark_delivered(message.message_id)
                    self._record_attempt(wake_batch_id, WakeAttemptOutcome.RECONCILED)
                    row = self.batches.get(wake_batch_id)
                    assert row is not None
                    return row
        return batch

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
