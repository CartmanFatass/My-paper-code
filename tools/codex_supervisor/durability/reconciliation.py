"""Reconcile App Server effects without resubmission."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Mapping

from .effects import EffectJournal, EffectRecord
from .models import AggregateKind, EffectState, TransitionCause, TransitionRequest
from .session_owner import AppServerSessionOwner
from .transaction import DurabilityTransaction
from .transitions import TransitionError, TransitionKernel


class ReconciliationError(RuntimeError):
    """Raised when an effect cannot be reconciled without a new submission."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EffectReconciler:
    def __init__(self, connection: sqlite3.Connection, owner: AppServerSessionOwner | None = None) -> None:
        self.connection = connection
        self.journal = EffectJournal(connection)
        self.kernel = TransitionKernel(connection)
        self.owner = owner
        self.handlers = {
            "thread/start": self.reconcile_thread_start,
            "thread/resume": self.reconcile_thread_resume,
            "turn/start": self.reconcile_turn_start,
        }

    async def reconcile(self, effect_id: str, *, evidence_row_id: str | None = None, evidence: Mapping[str, object] | None = None) -> object:
        if evidence:
            raise ReconciliationError("reconciler does not accept caller-authored evidence")
        record = self.journal.get(effect_id)
        if record.state == EffectState.PREPARED.value:
            raise ReconciliationError("PREPARED effects are not automatically sent")
        if record.state == EffectState.INCIDENT.value:
            raise ReconciliationError("INCIDENT requires operator resolution")
        handler = self.handlers.get(record.method)
        if handler is None:
            raise ReconciliationError(f"no reconciler for {record.method}")
        return await handler(record, evidence_row_id=evidence_row_id)

    async def _read(self, method: str, params: Mapping[str, object]) -> Mapping[str, object]:
        if self.owner is None:
            raise ReconciliationError("session owner required for App Server reads")
        if method not in {"thread/list", "thread/read", "thread/loaded/list"}:
            raise ReconciliationError("reconciler never calls a mutating method")
        return await self.owner.request_read(method, params)

    def _stored_turn(self, *, turn_id: str | None, client_key: str, thread_id: str | None) -> dict[str, object] | None:
        if turn_id:
            row = self.connection.execute(
                "SELECT turn_id, thread_id, status FROM turn_snapshots WHERE turn_id = ?",
                (turn_id,),
            ).fetchone()
            if row is None:
                return None
            mapping = dict(row)
            if thread_id and str(mapping["thread_id"]) != thread_id:
                return None
            raw = self.connection.execute(
                "SELECT 1 FROM raw_messages WHERE turn_id = ? AND canonical_json LIKE ?",
                (str(mapping["turn_id"]), f"%{client_key}%"),
            ).fetchone()
            keyed = self.connection.execute(
                "SELECT 1 FROM app_server_effects WHERE turn_id = ? AND client_key = ?",
                (str(mapping["turn_id"]), client_key),
            ).fetchone()
            if raw is None and keyed is None:
                return None
            return mapping
        row = self.connection.execute(
            """SELECT turn_id, thread_id, status FROM turn_snapshots
            WHERE thread_id = ? AND turn_id IN (
                SELECT turn_id FROM raw_messages WHERE canonical_json LIKE ?
            )""",
            (thread_id, f"%{client_key}%"),
        ).fetchone()
        return dict(row) if row is not None else None

    async def _observed_turn(self, record: EffectRecord) -> dict[str, object] | None:
        stored = self._stored_turn(
            turn_id=record.turn_id,
            client_key=record.client_key,
            thread_id=record.thread_id or str(record.request.get("threadId") or "") or None,
        )
        if stored is not None:
            return stored
        if self.owner is None:
            return None
        thread_id = record.thread_id or record.request.get("threadId")
        if not thread_id:
            return None
        read = await self._read("thread/read", {"threadId": str(thread_id), "includeTurns": True})
        thread = read.get("result") if isinstance(read.get("result"), Mapping) else read
        thread_obj = thread.get("thread") if isinstance(thread, Mapping) and isinstance(thread.get("thread"), Mapping) else thread
        turns = thread_obj.get("turns") if isinstance(thread_obj, Mapping) and isinstance(thread_obj.get("turns"), list) else []
        for turn in turns:
            if isinstance(turn, Mapping) and turn.get("clientUserMessageId") == record.client_key:
                return {
                    "turn_id": turn.get("id"),
                    "thread_id": thread_id,
                    "status": turn.get("status"),
                }
        return None

    def _confirm_with_owner(self, record: EffectRecord, *, evidence_ref: str, turn_id: str | None = None, thread_id: str | None = None) -> EffectRecord:
        if record.state not in {
            EffectState.RESPONSE_OBSERVED.value,
            EffectState.SUBMISSION_UNCERTAIN.value,
        }:
            return record
        with DurabilityTransaction(self.connection):
            confirmed = self.journal.confirm_effect(record.effect_id, evidence_ref=evidence_ref)
            if turn_id:
                self.connection.execute(
                    "UPDATE app_server_effects SET turn_id = COALESCE(turn_id, ?) WHERE effect_id = ?",
                    (turn_id, record.effect_id),
                )
            if thread_id:
                self.connection.execute(
                    "UPDATE app_server_effects SET thread_id = COALESCE(thread_id, ?) WHERE effect_id = ?",
                    (thread_id, record.effect_id),
                )
            self._advance_owner(record, evidence_ref=evidence_ref, turn_id=turn_id)
            return confirmed

    def _advance_owner(self, record: EffectRecord, *, evidence_ref: str, turn_id: str | None) -> None:
        if record.owner_kind == "MANAGED_TURN":
            row = self.connection.execute(
                "SELECT * FROM managed_turn_intents WHERE turn_intent_id = ?",
                (record.owner_id,),
            ).fetchone()
            if row is None:
                return
            state = str(row["submission_state"])
            version = int(row["version"] or 0)
            if state == "SUBMITTING":
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MANAGED_TURN,
                        aggregate_id=record.owner_id,
                        expected_state="SUBMITTING",
                        expected_version=version,
                        target_state="SUBMITTED",
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=evidence_ref,
                        field_updates={"app_server_turn_id": turn_id, "submitted_at": _now()} if turn_id else {},
                    )
                )
                state = "SUBMITTED"
                version += 1
            if state in {"SUBMITTED", "SUBMISSION_UNCERTAIN"}:
                try:
                    self.kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MANAGED_TURN,
                            aggregate_id=record.owner_id,
                            expected_state=state,
                            expected_version=version,
                            target_state="OBSERVED",
                            cause_kind=TransitionCause.RECONCILIATION,
                            cause_ref=evidence_ref,
                            field_updates={"app_server_turn_id": turn_id, "observed_at": _now()} if turn_id else {"observed_at": _now()},
                        )
                    )
                except TransitionError:
                    return
            return
        if record.owner_kind != "WAKE_BATCH":
            return
        row = self.connection.execute(
            "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
            (record.owner_id,),
        ).fetchone()
        if row is None:
            return
        state = str(row["state"])
        version = int(row["version"] or 0)
        if state == "SUBMITTING":
            self.kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.WAKE_BATCH,
                    aggregate_id=record.owner_id,
                    expected_state="SUBMITTING",
                    expected_version=version,
                    target_state="SUBMITTED",
                    cause_kind=TransitionCause.RECONCILIATION,
                    cause_ref=evidence_ref,
                    field_updates={"app_server_turn_id": turn_id} if turn_id else {},
                )
            )
            state = "SUBMITTED"
            version += 1
        if state in {"SUBMITTED", "SUBMISSION_UNCERTAIN"}:
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.WAKE_BATCH,
                        aggregate_id=record.owner_id,
                        expected_state=state,
                        expected_version=version,
                        target_state="ACTIVE",
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=evidence_ref,
                        field_updates={"app_server_turn_id": turn_id, "observed_at": _now()} if turn_id else {"observed_at": _now()},
                    )
                )
            except TransitionError:
                return
        messages = self.connection.execute(
            """SELECT m.message_id, m.delivery_state, m.delivery_version
            FROM mailbox_messages m
            JOIN wake_batch_messages b ON b.message_id = m.message_id
            WHERE b.wake_batch_id = ?""",
            (record.owner_id,),
        ).fetchall()
        for message in messages:
            delivery = str(message["delivery_state"])
            if delivery not in {"BATCHED", "SUBMISSION_UNCERTAIN"}:
                continue
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                        aggregate_id=str(message["message_id"]),
                        expected_state=delivery,
                        expected_version=int(message["delivery_version"] or 0),
                        target_state="DELIVERED_TO_TURN",
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=evidence_ref,
                    )
                )
            except TransitionError:
                continue

    async def reconcile_turn_start(self, record: EffectRecord, *, evidence_row_id: str | None = None) -> object:
        observed = await self._observed_turn(record)
        if observed is None or not observed.get("turn_id"):
            return record
        return self._confirm_with_owner(
            record,
            evidence_ref=f"turn:{observed['turn_id']}",
            turn_id=str(observed["turn_id"]),
            thread_id=None if observed.get("thread_id") is None else str(observed["thread_id"]),
        )

    async def reconcile_thread_resume(self, record: EffectRecord, *, evidence_row_id: str | None = None) -> object:
        thread_id = record.thread_id or record.request.get("threadId")
        if not thread_id:
            return record
        snap = self.connection.execute(
            "SELECT status FROM thread_snapshots WHERE thread_id = ?",
            (str(thread_id),),
        ).fetchone()
        idle_loaded = False
        if snap is not None:
            status = snap["status"]
            status_type = status.get("type") if isinstance(status, dict) else status
            idle_loaded = str(status_type) in {"idle", "IDLE_LOADED"}
        if self.owner is not None:
            read = await self._read("thread/read", {"threadId": str(thread_id)})
            thread = read.get("result") if isinstance(read.get("result"), Mapping) else read
            thread_obj = thread.get("thread") if isinstance(thread, Mapping) and isinstance(thread.get("thread"), Mapping) else thread
            status = thread_obj.get("status") if isinstance(thread_obj, Mapping) else None
            status_type = status.get("type") if isinstance(status, Mapping) else status
            loaded = await self._read("thread/loaded/list", {})
            result = loaded.get("result") if isinstance(loaded.get("result"), Mapping) else loaded
            data = result.get("data") if isinstance(result, Mapping) else None
            ids = {str(item) for item in data} if isinstance(data, list) else set()
            idle_loaded = str(status_type) == "idle" and str(thread_id) in ids
        if not idle_loaded:
            return record
        return self._confirm_with_owner(record, evidence_ref="resume:idle_loaded", thread_id=str(thread_id))

    async def reconcile_thread_start(self, record: EffectRecord, *, evidence_row_id: str | None = None) -> object:
        thread_id = record.thread_id
        if not thread_id and record.binding_id:
            binding = self.connection.execute(
                "SELECT thread_id FROM managed_actor_bindings WHERE binding_id = ?",
                (record.binding_id,),
            ).fetchone()
            if binding is not None and binding["thread_id"]:
                thread_id = str(binding["thread_id"])
        if not thread_id:
            return record
        stored = self.connection.execute(
            "SELECT thread_id FROM thread_snapshots WHERE thread_id = ?",
            (str(thread_id),),
        ).fetchone()
        if stored is None:
            if self.owner is None:
                return record
            read = await self._read("thread/read", {"threadId": str(thread_id)})
            thread = read.get("result") if isinstance(read.get("result"), Mapping) else read
            thread_obj = thread.get("thread") if isinstance(thread, Mapping) and isinstance(thread.get("thread"), Mapping) else thread
            observed_id = thread_obj.get("id") if isinstance(thread_obj, Mapping) else None
            if str(observed_id or "") != str(thread_id):
                return record
        return self._confirm_with_owner(record, evidence_ref=f"thread:{thread_id}", thread_id=str(thread_id))

    def restart_open_effects(self) -> list[str]:
        rows = self.connection.execute(
            """SELECT effect_id FROM app_server_effects
            WHERE state IN ('WRITE_STARTED', 'RESPONSE_OBSERVED', 'SUBMISSION_UNCERTAIN')"""
        ).fetchall()
        return [str(row[0]) for row in rows]
