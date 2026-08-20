"""Reconcile App Server effects without resubmission."""

from __future__ import annotations

import sqlite3
from typing import Callable, Mapping

from .effects import EffectJournal
from .models import EffectState
from .session_owner import AppServerSessionOwner


class ReconciliationError(RuntimeError):
    """Raised when an effect cannot be reconciled without a new submission."""


class EffectReconciler:
    def __init__(self, connection: sqlite3.Connection, owner: AppServerSessionOwner | None = None) -> None:
        self.connection = connection
        self.journal = EffectJournal(connection)
        self.owner = owner
        self.handlers: dict[str, Callable[..., object]] = {
            "thread/start": self.reconcile_thread_start,
            "thread/resume": self.reconcile_thread_resume,
            "turn/start": self.reconcile_turn_start,
        }

    def reconcile(self, effect_id: str, *, evidence: Mapping[str, object] | None = None) -> object:
        record = self.journal.get(effect_id)
        if record.state == EffectState.PREPARED.value:
            raise ReconciliationError("PREPARED effects are not automatically sent")
        if record.state == EffectState.INCIDENT.value:
            raise ReconciliationError("INCIDENT requires operator resolution")
        handler = self.handlers.get(record.method)
        if handler is None:
            raise ReconciliationError(f"no reconciler for {record.method}")
        return handler(record, evidence=evidence or {})

    async def _read(self, method: str, params: Mapping[str, object]) -> Mapping[str, object]:
        if self.owner is None:
            raise ReconciliationError("session owner required for App Server reads")
        if method not in {"thread/list", "thread/read", "thread/loaded/list"}:
            raise ReconciliationError("reconciler never calls a mutating method")
        return await self.owner.request_read(method, params)

    def reconcile_turn_start(self, record, *, evidence: Mapping[str, object]) -> object:
        turn_id = evidence.get("turn_id") or record.turn_id
        client_key = evidence.get("clientUserMessageId") or record.client_key
        if not turn_id or client_key != record.client_key:
            return record
        if record.state in {EffectState.RESPONSE_OBSERVED.value, EffectState.SUBMISSION_UNCERTAIN.value}:
            return self.journal.confirm_effect(record.effect_id, evidence_ref=f"turn:{turn_id}")
        return record

    def reconcile_thread_resume(self, record, *, evidence: Mapping[str, object]) -> object:
        readiness = evidence.get("readiness")
        if readiness == "IDLE_LOADED" and record.state in {
            EffectState.RESPONSE_OBSERVED.value,
            EffectState.SUBMISSION_UNCERTAIN.value,
        }:
            return self.journal.confirm_effect(record.effect_id, evidence_ref="resume:idle_loaded")
        return record

    def reconcile_thread_start(self, record, *, evidence: Mapping[str, object]) -> object:
        thread_id = evidence.get("thread_id") or record.thread_id
        if not thread_id:
            return record
        if record.state in {EffectState.RESPONSE_OBSERVED.value, EffectState.SUBMISSION_UNCERTAIN.value}:
            return self.journal.confirm_effect(record.effect_id, evidence_ref=f"thread:{thread_id}")
        return record

    def restart_open_effects(self) -> list[str]:
        rows = self.connection.execute(
            """SELECT effect_id FROM app_server_effects
            WHERE state IN ('WRITE_STARTED', 'RESPONSE_OBSERVED', 'SUBMISSION_UNCERTAIN')"""
        ).fetchall()
        return [str(row[0]) for row in rows]
