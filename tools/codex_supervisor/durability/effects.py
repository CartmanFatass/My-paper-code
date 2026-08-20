"""App Server effect journal. WRITE_STARTED means possible submission."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .models import AggregateKind, EffectOwnerKind, EffectState, TransitionCause, TransitionRequest
from .transaction import DurabilityTransaction
from .transitions import TransitionError, TransitionKernel


class EffectError(RuntimeError):
    """Raised when an App Server effect cannot be prepared or advanced."""


@dataclass(frozen=True)
class EffectRecord:
    effect_id: str
    owner_kind: str
    owner_id: str
    binding_id: str | None
    method: str
    client_key: str
    request: Mapping[str, object]
    state: str
    version: int
    run_id: str | None = None
    client_request_id: str | None = None
    request_row_id: str | None = None
    raw_request_seq: int | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    response_json: str | None = None
    incident_json: str | None = None
    prepared_at: str = ""
    write_started_at: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"eff_{uuid.uuid4().hex}"


def _canonical_request(request: Mapping[str, object]) -> str:
    return json.dumps(dict(request), sort_keys=True, separators=(",", ":"))


def _record(row: Mapping[str, Any] | sqlite3.Row) -> EffectRecord:
    data = dict(row)
    raw_seq = data.get("raw_request_seq")
    payload = data.get("request_json") or "{}"
    parsed = json.loads(str(payload))
    return EffectRecord(
        effect_id=str(data["effect_id"]),
        owner_kind=str(data["owner_kind"]),
        owner_id=str(data["owner_id"]),
        binding_id=None if data["binding_id"] is None else str(data["binding_id"]),
        method=str(data["method"]),
        client_key=str(data["client_key"]),
        request=dict(parsed) if isinstance(parsed, Mapping) else {},
        state=str(data["state"]),
        version=int(data["version"] or 0),
        run_id=None if data["run_id"] is None else str(data["run_id"]),
        client_request_id=None if data["client_request_id"] is None else str(data["client_request_id"]),
        request_row_id=None if data["request_row_id"] is None else str(data["request_row_id"]),
        raw_request_seq=None if raw_seq is None else int(raw_seq),
        thread_id=None if data["thread_id"] is None else str(data["thread_id"]),
        turn_id=None if data["turn_id"] is None else str(data["turn_id"]),
        response_json=None if data["response_json"] is None else str(data["response_json"]),
        incident_json=None if data["incident_json"] is None else str(data["incident_json"]),
        prepared_at=str(data["prepared_at"] or ""),
        write_started_at=None if data["write_started_at"] is None else str(data["write_started_at"]),
    )


class EffectJournal:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.kernel = TransitionKernel(connection)

    def _tx(self):
        if self.connection.in_transaction:
            return nullcontext()
        return DurabilityTransaction(self.connection)

    def get(self, effect_id: str) -> EffectRecord:
        row = self.connection.execute(
            "SELECT * FROM app_server_effects WHERE effect_id = ?",
            (effect_id,),
        ).fetchone()
        if row is None:
            raise EffectError(f"unknown effect: {effect_id}")
        return _record(row)

    def get_by_key(self, method: str, client_key: str) -> EffectRecord | None:
        row = self.connection.execute(
            "SELECT * FROM app_server_effects WHERE method = ? AND client_key = ?",
            (method, client_key),
        ).fetchone()
        return None if row is None else _record(row)

    def prepare_effect(
        self,
        *,
        owner_kind: str,
        owner_id: str,
        binding_id: str | None,
        method: str,
        client_key: str,
        request: Mapping[str, object],
    ) -> EffectRecord:
        EffectOwnerKind(owner_kind)
        request_json = _canonical_request(request)
        existing = self.get_by_key(method, client_key)
        if existing is not None:
            same = (
                existing.owner_kind == owner_kind
                and existing.owner_id == owner_id
                and existing.binding_id == binding_id
                and existing.method == method
                and existing.client_key == client_key
                and _canonical_request(existing.request) == request_json
            )
            if not same:
                raise EffectError(f"effect key conflict for {method} {client_key}")
            if existing.state != EffectState.PREPARED.value:
                raise EffectError(
                    f"{method} {client_key} already {existing.state}; cannot prepare again"
                )
            return existing
        effect_id = _new_id()
        now = _now()
        with self._tx():
            self.connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id, owner_kind, owner_id, binding_id, method, client_key,
                    request_json, state, version, prepared_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    effect_id,
                    owner_kind,
                    owner_id,
                    binding_id,
                    method,
                    client_key,
                    request_json,
                    EffectState.PREPARED.value,
                    now,
                ),
            )
        return self.get(effect_id)

    def claim_write(
        self,
        effect_id: str,
        *,
        run_id: str,
        client_request_id: str,
        request_row_id: str,
        raw_request_seq: int,
        transport_seq: int | None = None,
    ) -> EffectRecord:
        current = self.get(effect_id)
        if current.state != EffectState.PREPARED.value:
            raise EffectError(f"only PREPARED can claim write; {effect_id} is {current.state}")
        fields: dict[str, object] = {
            "run_id": run_id,
            "client_request_id": client_request_id,
            "request_row_id": request_row_id,
            "raw_request_seq": raw_request_seq,
            "write_started_at": _now(),
        }
        if transport_seq is not None:
            fields["transport_seq"] = transport_seq
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=EffectState.PREPARED.value,
                        expected_version=current.version,
                        target_state=EffectState.WRITE_STARTED.value,
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref=client_request_id,
                        evidence_ref=request_row_id,
                        field_updates=fields,
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def observe_response(
        self,
        effect_id: str,
        *,
        response: Mapping[str, object],
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.RESPONSE_OBSERVED.value,
                        cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                        cause_ref=current.client_request_id or effect_id,
                        field_updates={
                            "response_json": json.dumps(dict(response), sort_keys=True),
                            "response_observed_at": _now(),
                            "thread_id": thread_id,
                            "turn_id": turn_id,
                        },
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def mark_uncertain(self, effect_id: str, *, reason: str) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=reason,
                        field_updates={"incident_json": json.dumps({"reason": reason})},
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def confirm_effect(self, effect_id: str, *, evidence_ref: str) -> EffectRecord:
        if not evidence_ref:
            raise EffectError("confirmation requires evidence_ref")
        current = self.get(effect_id)
        if current.state == EffectState.EFFECT_CONFIRMED.value:
            return current
        with self._tx():
            try:
                if current.state == EffectState.WRITE_STARTED.value:
                    self.kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                            aggregate_id=effect_id,
                            expected_state=EffectState.WRITE_STARTED.value,
                            expected_version=current.version,
                            target_state=EffectState.SUBMISSION_UNCERTAIN.value,
                            cause_kind=TransitionCause.RECONCILIATION,
                            cause_ref=evidence_ref,
                            evidence_ref=evidence_ref,
                        )
                    )
                    current = self.get(effect_id)
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.EFFECT_CONFIRMED.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=evidence_ref,
                        evidence_ref=evidence_ref,
                        field_updates={"confirmed_at": _now(), "reconciled_at": _now()},
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def mark_incident(
        self,
        effect_id: str,
        *,
        evidence_ref: str,
        incident: Mapping[str, object],
    ) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.INCIDENT.value,
                        cause_kind=TransitionCause.SERVER_REQUEST_INCIDENT,
                        cause_ref=evidence_ref,
                        evidence_ref=evidence_ref,
                        field_updates={
                            "incident_json": json.dumps(dict(incident), sort_keys=True),
                        },
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def cancel_before_write(self, effect_id: str, *, cause_ref: str) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.CANCELLED_BEFORE_WRITE.value,
                        cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                        cause_ref=cause_ref,
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def cancel_prepared_if_present(self, effect_id: str | None, *, cause_ref: str) -> None:
        if not effect_id:
            return
        try:
            current = self.get(effect_id)
        except EffectError:
            return
        if current.state != EffectState.PREPARED.value:
            return
        self.cancel_before_write(effect_id, cause_ref=cause_ref)

    def has_possible_submission(self, effect_id: str) -> bool:
        current = self.get(effect_id)
        return current.state != EffectState.PREPARED.value or current.raw_request_seq is not None


def cancel_prepared_wake(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    cause_ref: str,
    message_target: str = "ELIGIBLE",
) -> dict[str, object]:
    """Cancel a PREPARED wake, its messages, and its PREPARED effect in one txn."""
    from .models import AggregateKind, TransitionCause, TransitionRequest
    from .transaction import DurabilityTransaction
    from .transitions import TransitionError, TransitionKernel

    journal = EffectJournal(connection)
    kernel = TransitionKernel(connection)
    owns = not connection.in_transaction
    if owns:
        connection.execute("BEGIN IMMEDIATE")
    try:
        batch = connection.execute(
            "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
            (wake_batch_id,),
        ).fetchone()
        if batch is None:
            raise EffectError(f"unknown wake batch: {wake_batch_id}")
        if str(batch["state"]) != "PREPARED":
            if owns:
                connection.commit()
            return dict(batch)
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id=wake_batch_id,
                expected_state="PREPARED",
                expected_version=int(batch["version"] or 0),
                target_state="CANCELLED",
                cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                cause_ref=cause_ref,
            )
        )
        rows = connection.execute(
            """SELECT m.message_id, m.delivery_state, m.delivery_version
            FROM mailbox_messages m
            JOIN wake_batch_messages b ON b.message_id = m.message_id
            WHERE b.wake_batch_id = ?""",
            (wake_batch_id,),
        ).fetchall()
        for row in rows:
            state = str(row["delivery_state"])
            if state not in {"BATCHED", "SUBMISSION_UNCERTAIN"}:
                continue
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                    aggregate_id=str(row["message_id"]),
                    expected_state=state,
                    expected_version=int(row["delivery_version"] or 0),
                    target_state=message_target,
                    cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                    cause_ref=cause_ref,
                )
            )
        journal.cancel_prepared_if_present(
            None if batch["effect_id"] is None else str(batch["effect_id"]),
            cause_ref=cause_ref,
        )
        if owns:
            connection.commit()
    except Exception:
        if owns:
            connection.rollback()
        raise
    row = connection.execute(
        "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()
    return dict(row)


def cancel_prepared_turn(connection: sqlite3.Connection, turn_intent_id: str, effect_id: str, *, cause_ref: str) -> None:
    from .models import AggregateKind, TransitionCause, TransitionRequest
    from .transitions import TransitionKernel

    journal = EffectJournal(connection)
    kernel = TransitionKernel(connection)
    with journal._tx():
        row = connection.execute(
            "SELECT submission_state, version FROM managed_turn_intents WHERE turn_intent_id = ?",
            (turn_intent_id,),
        ).fetchone()
        if row is not None and str(row["submission_state"]) == "PREPARED":
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state="PREPARED",
                    expected_version=int(row["version"] or 0),
                    target_state="CANCELLED",
                    cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                    cause_ref=cause_ref,
                )
            )
        journal.cancel_prepared_if_present(effect_id, cause_ref=cause_ref)


    def has_possible_submission(self, effect_id: str) -> bool:
        current = self.get(effect_id)
        return current.state != EffectState.PREPARED.value or current.raw_request_seq is not None
