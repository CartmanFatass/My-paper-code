"""Small durable at-most-once App Server mutation outbox."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping

from ..protocol import encode_jsonl
from .transaction import DurabilityTransaction


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeliveryClass(str, Enum):
    READ_IDEMPOTENT = "READ_IDEMPOTENT"
    MUTATION_AT_MOST_ONCE = "MUTATION_AT_MOST_ONCE"


class OperationState(str, Enum):
    READY = "READY"
    SENDING = "SENDING"
    DONE = "DONE"
    UNKNOWN = "UNKNOWN"


class OutboxError(RuntimeError):
    pass


class DuplicateOperation(OutboxError):
    pass


class ClaimRejected(OutboxError):
    pass


@dataclass(frozen=True)
class MutationSpec:
    dedupe_key: str
    protocol_session_id: str
    run_id: str
    method: str
    params: Mapping[str, object]
    target: str
    thread_id: str | None = None
    binding_id: str | None = None
    delivery_class: DeliveryClass = DeliveryClass.MUTATION_AT_MOST_ONCE


@dataclass(frozen=True)
class OperationRecord:
    operation_id: str
    dedupe_key: str
    protocol_session_id: str
    run_id: str
    binding_id: str | None
    target: str
    thread_id: str | None
    rpc_request_id: int
    method: str
    wire_bytes: bytes
    delivery_class: DeliveryClass
    state: OperationState
    claim_token: str | None
    created_at: str
    claimed_at: str | None
    completed_at: str | None
    outcome: str | None
    error: str | None
    response_raw_ref: str | None


@dataclass(frozen=True)
class OperationClaim:
    operation_id: str
    claim_token: str
    protocol_session_id: str
    rpc_request_id: int
    method: str
    wire_bytes: bytes


def _record(row: sqlite3.Row) -> OperationRecord:
    return OperationRecord(
        operation_id=str(row["operation_id"]),
        dedupe_key=str(row["dedupe_key"]),
        protocol_session_id=str(row["protocol_session_id"]),
        run_id=str(row["run_id"]),
        binding_id=None if row["binding_id"] is None else str(row["binding_id"]),
        target=str(row["target"]),
        thread_id=None if row["thread_id"] is None else str(row["thread_id"]),
        rpc_request_id=int(row["rpc_request_id"]),
        method=str(row["method"]),
        wire_bytes=bytes(row["wire_bytes"]),
        delivery_class=DeliveryClass(str(row["delivery_class"])),
        state=OperationState(str(row["state"])),
        claim_token=None if row["claim_token"] is None else str(row["claim_token"]),
        created_at=str(row["created_at"]),
        claimed_at=None if row["claimed_at"] is None else str(row["claimed_at"]),
        completed_at=None if row["completed_at"] is None else str(row["completed_at"]),
        outcome=None if row["outcome"] is None else str(row["outcome"]),
        error=None if row["error"] is None else str(row["error"]),
        response_raw_ref=(
            None if row["response_raw_ref"] is None else str(row["response_raw_ref"])
        ),
    )


class AppServerOutbox:
    """The only persistent source of mutation request bytes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get(self, operation_id: str) -> OperationRecord:
        row = self.connection.execute(
            "SELECT * FROM app_server_outbox WHERE operation_id = ?", (operation_id,)
        ).fetchone()
        if row is None:
            raise OutboxError(f"unknown operation: {operation_id}")
        return _record(row)

    def get_by_dedupe(self, dedupe_key: str) -> OperationRecord | None:
        row = self.connection.execute(
            "SELECT * FROM app_server_outbox WHERE dedupe_key = ?", (dedupe_key,)
        ).fetchone()
        return None if row is None else _record(row)

    @staticmethod
    def _same_spec(record: OperationRecord, spec: MutationSpec) -> bool:
        try:
            payload = json.loads(record.wire_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return (
            record.protocol_session_id == spec.protocol_session_id
            and record.run_id == spec.run_id
            and record.binding_id == spec.binding_id
            and record.target == spec.target
            and record.thread_id == spec.thread_id
            and record.method == spec.method
            and record.delivery_class is spec.delivery_class
            and payload
            == {
                "id": record.rpc_request_id,
                "method": spec.method,
                "params": dict(spec.params),
            }
        )

    def enqueue(self, spec: MutationSpec) -> OperationRecord:
        if not spec.dedupe_key or not spec.protocol_session_id or not spec.run_id:
            raise OutboxError("dedupe, protocol-session, and run identity are required")
        if spec.delivery_class is not DeliveryClass.MUTATION_AT_MOST_ONCE:
            raise OutboxError("persistent outbox accepts mutations only")
        if not spec.target:
            raise OutboxError("mutation target is required")
        if spec.method not in {
            "thread/start", "thread/resume", "turn/start", "thread/memoryMode/set"
        }:
            raise OutboxError(f"unsupported V1 mutation method: {spec.method}")
        if spec.binding_id is not None and spec.target != f"binding:{spec.binding_id}":
            raise OutboxError("mutation target does not match binding identity")
        if spec.method == "thread/start":
            if spec.thread_id is not None or "threadId" in spec.params:
                raise OutboxError("thread/start must not carry a thread identity")
        elif (
            not isinstance(spec.thread_id, str)
            or not spec.thread_id
            or not isinstance(spec.params.get("threadId"), str)
            or spec.params.get("threadId") != spec.thread_id
        ):
            raise OutboxError("mutation params.threadId does not match thread identity")
        with DurabilityTransaction(self.connection):
            existing = self.get_by_dedupe(spec.dedupe_key)
            if existing is not None:
                if not self._same_spec(existing, spec):
                    raise DuplicateOperation(
                        f"dedupe key {spec.dedupe_key!r} identifies different immutable bytes"
                    )
                return existing
            seq = self.connection.execute(
                """UPDATE app_server_rpc_sequence SET next_id = next_id + 1
                WHERE singleton = 1 RETURNING next_id - 1"""
            ).fetchone()
            if seq is None:
                raise OutboxError("durable RPC sequence is unavailable")
            request_id = int(seq[0])
            wire = encode_jsonl(
                {"id": request_id, "method": spec.method, "params": dict(spec.params)}
            )
            operation_id = f"op_{uuid.uuid4().hex}"
            now = _now()
            inserted = self.connection.execute(
                """INSERT INTO app_server_outbox (
                    operation_id, dedupe_key, protocol_session_id, run_id, binding_id,
                    target, thread_id, rpc_request_id, method, wire_bytes,
                    delivery_class, state, claim_token, created_at, claimed_at,
                    completed_at, outcome, error, response_raw_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'READY', NULL, ?, NULL,
                          NULL, NULL, NULL, NULL)
                RETURNING *""",
                (
                    operation_id,
                    spec.dedupe_key,
                    spec.protocol_session_id,
                    spec.run_id,
                    spec.binding_id,
                    spec.target,
                    spec.thread_id,
                    request_id,
                    spec.method,
                    wire,
                    spec.delivery_class.value,
                    now,
                ),
            ).fetchone()
            assert inserted is not None
            record = _record(inserted)
        return record

    def claim(
        self,
        operation_id: str,
        *,
        protocol_session_id: str,
        target: str,
        thread_id: str | None,
        enforce_target: bool = True,
    ) -> OperationClaim:
        token = f"claim_{uuid.uuid4().hex}"
        now = _now()
        with DurabilityTransaction(self.connection):
            if enforce_target:
                sql = """UPDATE app_server_outbox
                    SET state = 'SENDING', claim_token = ?, claimed_at = ?
                    WHERE operation_id = ? AND state = 'READY'
                      AND protocol_session_id = ? AND target = ? AND thread_id IS ?
                    RETURNING operation_id, protocol_session_id, rpc_request_id,
                              method, wire_bytes"""
                values = (token, now, operation_id, protocol_session_id, target, thread_id)
            else:
                sql = """UPDATE app_server_outbox
                    SET state = 'SENDING', claim_token = ?, claimed_at = ?
                    WHERE operation_id = ? AND state = 'READY' AND protocol_session_id = ?
                    RETURNING operation_id, protocol_session_id, rpc_request_id,
                              method, wire_bytes"""
                values = (token, now, operation_id, protocol_session_id)
            row = self.connection.execute(sql, values).fetchone()
        if row is None:
            current = self.get(operation_id)
            raise ClaimRejected(
                f"operation is not claimable for this session/target/thread: {current.state.value}"
            )
        return OperationClaim(
            operation_id=str(row["operation_id"]),
            claim_token=token,
            protocol_session_id=str(row["protocol_session_id"]),
            rpc_request_id=int(row["rpc_request_id"]),
            method=str(row["method"]),
            wire_bytes=bytes(row["wire_bytes"]),
        )

    def complete(
        self,
        claim: OperationClaim,
        *,
        outcome: str,
        response_raw_ref: str | None = None,
        error: str | None = None,
    ) -> OperationRecord:
        with DurabilityTransaction(self.connection):
            changed = self.connection.execute(
                """UPDATE app_server_outbox
                SET state = 'DONE', claim_token = NULL, completed_at = ?, outcome = ?, error = ?,
                    response_raw_ref = ?
                WHERE operation_id = ? AND state = 'SENDING' AND claim_token = ?""",
                (
                    _now(), outcome, error, response_raw_ref,
                    claim.operation_id, claim.claim_token,
                ),
            )
            if changed.rowcount != 1:
                raise ClaimRejected("claim no longer owns SENDING operation")
        return self.get(claim.operation_id)

    def mark_unknown(self, claim: OperationClaim, *, error: str) -> OperationRecord:
        with DurabilityTransaction(self.connection):
            changed = self.connection.execute(
                """UPDATE app_server_outbox
                SET state = 'UNKNOWN', claim_token = NULL, completed_at = ?, outcome = 'AMBIGUOUS', error = ?
                WHERE operation_id = ? AND state = 'SENDING' AND claim_token = ?""",
                (_now(), error, claim.operation_id, claim.claim_token),
            )
            if changed.rowcount != 1:
                raise ClaimRejected("claim no longer owns SENDING operation")
        return self.get(claim.operation_id)

    def reject_ready(self, operation_id: str, *, error: str) -> OperationRecord:
        with DurabilityTransaction(self.connection):
            changed = self.connection.execute(
                """UPDATE app_server_outbox
                SET state = 'DONE', completed_at = ?, outcome = 'LOCAL_REJECTED', error = ?
                WHERE operation_id = ? AND state = 'READY'""",
                (_now(), error, operation_id),
            )
            if changed.rowcount != 1:
                raise ClaimRejected("only READY operations can be locally rejected")
        return self.get(operation_id)

    def cancel_ready(self, operation_id: str, *, reason: str) -> OperationRecord:
        return self.reject_ready(operation_id, error=f"cancelled:{reason}")

    def recover_stale_sessions(self, protocol_session_id: str) -> tuple[int, int]:
        """Contain old-session work without scanning unrelated history."""
        with DurabilityTransaction(self.connection):
            unknown = self.connection.execute(
                """UPDATE app_server_outbox SET state = 'UNKNOWN', claim_token = NULL, completed_at = ?,
                   outcome = 'SESSION_LOST', error = 'session changed while SENDING'
                   WHERE state = 'SENDING' AND protocol_session_id != ?""",
                (_now(), protocol_session_id),
            ).rowcount
            cancelled = self.connection.execute(
                """UPDATE app_server_outbox SET state = 'DONE', completed_at = ?,
                   outcome = 'LOCAL_CANCELLED', error = 'unsent operation belongs to old session'
                   WHERE state = 'READY' AND protocol_session_id != ?""",
                (_now(), protocol_session_id),
            ).rowcount
        return int(unknown), int(cancelled)

    def mark_session_sending_unknown(self, protocol_session_id: str, *, error: str) -> int:
        with DurabilityTransaction(self.connection):
            changed = self.connection.execute(
                """UPDATE app_server_outbox SET state = 'UNKNOWN', claim_token = NULL, completed_at = ?,
                   outcome = 'SESSION_LOST', error = ?
                   WHERE state = 'SENDING' AND protocol_session_id = ?""",
                (_now(), error, protocol_session_id),
            )
        return int(changed.rowcount)
