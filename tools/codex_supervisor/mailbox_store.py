"""Durable mailbox storage. Transitions never skip."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .mailbox_acl import MailboxAclError, evaluate_automatic_delivery
from .mailbox_models import (
    FORBIDDEN_MAILBOX_KINDS,
    DeliveryState,
    IntakeState,
    MailboxMessage,
    MailboxMessageKind,
)
from .store import ObserverStore

FORWARD_DELIVERY = {
    DeliveryState.ENQUEUED: {
        DeliveryState.ELIGIBLE,
        DeliveryState.DEAD_LETTER,
        DeliveryState.CANCELLED_SOURCE_RESOLVED,
    },
    DeliveryState.ELIGIBLE: {
        DeliveryState.BATCHED,
        DeliveryState.DEAD_LETTER,
        DeliveryState.ENQUEUED,
        DeliveryState.CANCELLED_SOURCE_RESOLVED,
    },
    DeliveryState.BATCHED: {
        DeliveryState.DELIVERED_TO_TURN,
        DeliveryState.SUBMISSION_UNCERTAIN,
        DeliveryState.ELIGIBLE,
        DeliveryState.DEAD_LETTER,
        DeliveryState.CANCELLED_SOURCE_RESOLVED,
    },
    DeliveryState.SUBMISSION_UNCERTAIN: {
        DeliveryState.DELIVERED_TO_TURN,
        DeliveryState.DEAD_LETTER,
    },
    DeliveryState.DELIVERED_TO_TURN: {DeliveryState.DEAD_LETTER},
    DeliveryState.CANCELLED_SOURCE_RESOLVED: set(),
    DeliveryState.DEAD_LETTER: set(),
}


class MailboxStoreError(ValueError):
    """Raised when a mailbox transition is illegal."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_message(row: Any) -> MailboxMessage:
    return MailboxMessage(
        message_id=str(row["message_id"]),
        source_system=str(row["source_system"]),
        source_event_key=str(row["source_event_key"]),
        sender_actor_context_id=None
        if row["sender_actor_context_id"] is None
        else str(row["sender_actor_context_id"]),
        target_actor_context_id=str(row["target_actor_context_id"]),
        message_kind=MailboxMessageKind(str(row["message_kind"])),
        subject_ref=str(row["subject_ref"]),
        payload_ref=str(row["payload_ref"]),
        direction_id=None if row["direction_id"] is None else str(row["direction_id"]),
        epoch_id=None if row["epoch_id"] is None else str(row["epoch_id"]),
        priority=int(row["priority"]),
        delivery_state=DeliveryState(str(row["delivery_state"])),
        intake_state=IntakeState(str(row["intake_state"])),
        created_at=str(row["created_at"]),
        dead_letter_reason=None if row["dead_letter_reason"] is None else str(row["dead_letter_reason"]),
        source_resolved_after_submission=bool(row["source_resolved_after_submission"])
        if "source_resolved_after_submission" in row.keys() and row["source_resolved_after_submission"] is not None
        else False,
    )


class MailboxStore:
    def __init__(self, store: ObserverStore) -> None:
        self.store = store

    def get(self, message_id: str) -> MailboxMessage | None:
        with self.store._lock:
            row = self.store.connection.execute(
                "SELECT * FROM mailbox_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            return None if row is None else _row_to_message(row)

    def get_by_source_key(self, source_event_key: str) -> MailboxMessage | None:
        with self.store._lock:
            row = self.store.connection.execute(
                "SELECT * FROM mailbox_messages WHERE source_event_key = ?",
                (source_event_key,),
            ).fetchone()
            return None if row is None else _row_to_message(row)

    def list_messages(self, *, target_actor_context_id: str | None = None) -> list[MailboxMessage]:
        sql = "SELECT * FROM mailbox_messages"
        params: list[object] = []
        if target_actor_context_id:
            sql += " WHERE target_actor_context_id = ?"
            params.append(target_actor_context_id)
        sql += " ORDER BY priority DESC, created_at ASC, message_id ASC"
        with self.store._lock:
            rows = self.store.connection.execute(sql, params).fetchall()
            return [_row_to_message(row) for row in rows]

    def enqueue(
        self,
        *,
        source_system: str,
        source_event_key: str,
        target_actor_context_id: str,
        message_kind: MailboxMessageKind | str,
        subject_ref: str,
        payload_ref: str,
        sender_actor_context_id: str | None = None,
        direction_id: str | None = None,
        epoch_id: str | None = None,
        priority: int = 0,
    ) -> MailboxMessage:
        kind = MailboxMessageKind(message_kind) if not isinstance(message_kind, MailboxMessageKind) else message_kind
        if kind.value in FORBIDDEN_MAILBOX_KINDS:
            raise MailboxStoreError(f"forbidden mailbox kind: {kind.value}")
        existing = self.get_by_source_key(source_event_key)
        if existing is not None:
            same = (
                existing.source_system == source_system
                and existing.sender_actor_context_id == sender_actor_context_id
                and existing.target_actor_context_id == target_actor_context_id
                and existing.message_kind is kind
                and existing.subject_ref == subject_ref
                and existing.payload_ref == payload_ref
                and existing.direction_id == direction_id
            )
            if not same:
                raise MailboxStoreError("source_event_key conflicts with an existing message")
            return existing
        message_id = f"msg_{uuid.uuid4().hex}"
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """INSERT INTO mailbox_messages (
                    message_id, source_system, source_event_key, sender_actor_context_id,
                    target_actor_context_id, message_kind, subject_ref, payload_ref,
                    direction_id, epoch_id, priority, delivery_state, intake_state, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    source_system,
                    source_event_key,
                    sender_actor_context_id,
                    target_actor_context_id,
                    kind.value,
                    subject_ref,
                    payload_ref,
                    direction_id,
                    epoch_id,
                    int(priority),
                    DeliveryState.ENQUEUED.value,
                    IntakeState.NOT_ACKNOWLEDGED.value,
                    now,
                ),
            )
        stored = self.get(message_id)
        assert stored is not None
        return stored

    def _set_delivery(
        self,
        message_id: str,
        new_state: DeliveryState,
        **fields: Any,
    ) -> MailboxMessage:
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionError, TransitionKernel

        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        if new_state is current.delivery_state:
            return current
        allowed = FORWARD_DELIVERY.get(current.delivery_state, set())
        if new_state not in allowed:
            raise MailboxStoreError(
                f"cannot skip {current.delivery_state.value} → {new_state.value}"
            )
        cause = fields.pop("cause_kind", None) or (
            TransitionCause.PRE_WRITE_CANCEL
            if current.delivery_state is DeliveryState.BATCHED and new_state is DeliveryState.ELIGIBLE
            else TransitionCause.CONTROL_COMMAND
        )
        if isinstance(cause, str):
            cause = TransitionCause(cause)
        version = int(
            self.store.connection.execute(
                "SELECT delivery_version FROM mailbox_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()[0]
            or 0
        )
        try:
            with self.store._lock:
                with DurabilityTransaction(self.store.connection):
                    TransitionKernel(self.store.connection).apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                            aggregate_id=message_id,
                            expected_state=current.delivery_state.value,
                            expected_version=version,
                            target_state=new_state.value,
                            cause_kind=cause,
                            cause_ref=str(fields.get("dead_letter_reason") or new_state.value),
                            field_updates=fields,
                        )
                    )
        except TransitionError as exc:
            raise MailboxStoreError(str(exc)) from exc
        updated = self.get(message_id)
        assert updated is not None
        return updated

    def _set_intake(self, message_id: str, new_state: IntakeState, **fields: Any) -> MailboxMessage:
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionError, TransitionKernel

        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        if current.intake_state is new_state:
            return current
        version = int(
            self.store.connection.execute(
                "SELECT intake_version FROM mailbox_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()[0]
            or 0
        )
        try:
            with self.store._lock:
                with DurabilityTransaction(self.store.connection):
                    TransitionKernel(self.store.connection).apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MAILBOX_INTAKE,
                            aggregate_id=message_id,
                            expected_state=current.intake_state.value,
                            expected_version=version,
                            target_state=new_state.value,
                            cause_kind=TransitionCause.CONTROL_COMMAND,
                            cause_ref=new_state.value,
                            field_updates=fields,
                        )
                    )
        except TransitionError as exc:
            raise MailboxStoreError(str(exc)) from exc
        updated = self.get(message_id)
        assert updated is not None
        return updated

    def mark_eligible(self, message_id: str) -> MailboxMessage:
        return self._set_delivery(message_id, DeliveryState.ELIGIBLE, eligible_at=_now())

    def mark_batched(self, message_id: str) -> MailboxMessage:
        return self._set_delivery(message_id, DeliveryState.BATCHED, batched_at=_now())

    def mark_delivered(self, message_id: str) -> MailboxMessage:
        return self._set_delivery(message_id, DeliveryState.DELIVERED_TO_TURN, delivered_at=_now())

    def mark_uncertain(self, message_id: str) -> MailboxMessage:
        return self._set_delivery(message_id, DeliveryState.SUBMISSION_UNCERTAIN)

    def return_to_eligible(self, message_id: str) -> MailboxMessage:
        return self._set_delivery(message_id, DeliveryState.ELIGIBLE, batched_at=None)

    def dead_letter(self, message_id: str, reason: str) -> MailboxMessage:
        return self._set_delivery(
            message_id,
            DeliveryState.DEAD_LETTER,
            dead_letter_reason=reason,
        )

    def note_source_resolved_after_submission(self, message_id: str) -> MailboxMessage:
        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """UPDATE mailbox_messages
                SET source_resolved_after_submission = 1
                WHERE message_id = ?""",
                (message_id,),
            )
        updated = self.get(message_id)
        assert updated is not None
        return updated

    def batch_state_for_message(self, message_id: str) -> str | None:
        row = self.store.connection.execute(
            """SELECT b.state FROM wake_batch_messages w
            JOIN wake_batches b ON b.wake_batch_id = w.wake_batch_id
            WHERE w.message_id = ?
            ORDER BY b.prepared_at DESC""",
            (message_id,),
        ).fetchone()
        return None if row is None else str(row[0])

    def batch_id_for_message(self, message_id: str) -> str | None:
        row = self.store.connection.execute(
            """SELECT b.wake_batch_id FROM wake_batch_messages w
            JOIN wake_batches b ON b.wake_batch_id = w.wake_batch_id
            WHERE w.message_id = ?
            ORDER BY b.prepared_at DESC""",
            (message_id,),
        ).fetchone()
        return None if row is None else str(row[0])

    def cancel_prepared_batch_source_resolved(
        self,
        wake_batch_id: str,
        invalid_message_ids: set[str],
        reason: str = "SOURCE_RESOLVED",
    ) -> bool:
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionError, TransitionKernel

        now = _now()
        kernel = TransitionKernel(self.store.connection)
        with self.store._lock:
            with DurabilityTransaction(self.store.connection):
                batch = self.store.connection.execute(
                    "SELECT state, version FROM wake_batches WHERE wake_batch_id = ?",
                    (wake_batch_id,),
                ).fetchone()
                if batch is None or str(batch["state"]) != "PREPARED":
                    return False
                try:
                    kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.WAKE_BATCH,
                            aggregate_id=wake_batch_id,
                            expected_state="PREPARED",
                            expected_version=int(batch["version"] or 0),
                            target_state="CANCELLED",
                            cause_kind=TransitionCause.SOURCE_RESOLUTION,
                            cause_ref=reason,
                        )
                    )
                except TransitionError:
                    return False
                rows = self.store.connection.execute(
                    """SELECT m.message_id, m.delivery_state, m.delivery_version
                    FROM mailbox_messages m
                    JOIN wake_batch_messages b ON b.message_id = m.message_id
                    WHERE b.wake_batch_id = ?""",
                    (wake_batch_id,),
                ).fetchall()
                for row in rows:
                    message_id = str(row["message_id"])
                    state = str(row["delivery_state"])
                    version = int(row["delivery_version"] or 0)
                    if message_id in invalid_message_ids:
                        if state not in {
                            DeliveryState.DELIVERED_TO_TURN.value,
                            DeliveryState.SUBMISSION_UNCERTAIN.value,
                            DeliveryState.DEAD_LETTER.value,
                            DeliveryState.CANCELLED_SOURCE_RESOLVED.value,
                        }:
                            kernel.apply(
                                TransitionRequest(
                                    aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                                    aggregate_id=message_id,
                                    expected_state=state,
                                    expected_version=version,
                                    target_state=DeliveryState.CANCELLED_SOURCE_RESOLVED.value,
                                    cause_kind=TransitionCause.SOURCE_INVALID_PREPARED_BATCH,
                                    cause_ref=reason,
                                    field_updates={"dead_letter_reason": reason, "batched_at": None},
                                )
                            )
                    elif state == DeliveryState.BATCHED.value:
                        kernel.apply(
                            TransitionRequest(
                                aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                                aggregate_id=message_id,
                                expected_state=state,
                                expected_version=version,
                                target_state=DeliveryState.ELIGIBLE.value,
                                cause_kind=TransitionCause.SOURCE_INVALID_PREPARED_BATCH,
                                cause_ref=reason,
                                field_updates={"batched_at": None, "eligible_at": now},
                            )
                        )
        return True

    def cancel_source_resolved(self, message_id: str, reason: str = "SOURCE_RESOLVED") -> MailboxMessage:
        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        if current.delivery_state in {
            DeliveryState.DELIVERED_TO_TURN,
            DeliveryState.SUBMISSION_UNCERTAIN,
            DeliveryState.DEAD_LETTER,
            DeliveryState.CANCELLED_SOURCE_RESOLVED,
        }:
            return current
        return self._set_delivery(
            message_id,
            DeliveryState.CANCELLED_SOURCE_RESOLVED,
            dead_letter_reason=reason,
        )

    def acknowledge(self, message_id: str) -> MailboxMessage:
        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        if current.delivery_state is not DeliveryState.DELIVERED_TO_TURN:
            raise MailboxStoreError("ACK requires a delivered message")
        if current.intake_state is IntakeState.NOT_ACKNOWLEDGED:
            self._set_intake(message_id, IntakeState.ACKNOWLEDGED, acknowledged_at=_now())
        updated = self.get(message_id)
        assert updated is not None
        return updated

    def intake(self, message_id: str) -> MailboxMessage:
        current = self.get(message_id)
        if current is None:
            raise MailboxStoreError(f"unknown mailbox message: {message_id}")
        if current.intake_state is IntakeState.NOT_ACKNOWLEDGED:
            self.acknowledge(message_id)
            current = self.get(message_id)
            assert current is not None
        if current.intake_state is IntakeState.ACKNOWLEDGED:
            self._set_intake(message_id, IntakeState.INTAKEN, intaken_at=_now())
        updated = self.get(message_id)
        assert updated is not None
        return updated

    def record_command_receipt(self, *, command_id: str, message_id: str, action: str) -> str:
        existing = self.store.connection.execute(
            """SELECT receipt_id FROM mailbox_command_receipts
            WHERE command_id = ? AND message_id = ? AND action = ?""",
            (command_id, message_id, action),
        ).fetchone()
        if existing is not None:
            return str(existing[0])
        receipt_id = f"mrcpt_{uuid.uuid4().hex}"
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """INSERT INTO mailbox_command_receipts (
                    receipt_id, command_id, message_id, action, created_at
                ) VALUES (?, ?, ?, ?, ?)""",
                (receipt_id, command_id, message_id, action, _now()),
            )
        return receipt_id

    def active_batch_message_ids(self) -> set[str]:
        with self.store._lock:
            rows = self.store.connection.execute(
                """SELECT m.message_id
                FROM wake_batch_messages m
                JOIN wake_batches b ON b.wake_batch_id = m.wake_batch_id
                WHERE b.state IN ('PREPARED', 'SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'ACTIVE')"""
            ).fetchall()
            return {str(row[0]) for row in rows}

    def select_eligible(
        self,
        *,
        target_actor_context_id: str,
        target_kind: str,
        target_binding_state: str,
        sender_kind_for: dict[str, str | None],
        limit: int = 16,
    ) -> list[MailboxMessage]:
        in_batch = self.active_batch_message_ids()
        selected: list[MailboxMessage] = []
        for message in self.list_messages(target_actor_context_id=target_actor_context_id):
            if len(selected) >= limit:
                break
            if message.message_id in in_batch:
                continue
            if message.delivery_state not in {DeliveryState.ENQUEUED, DeliveryState.ELIGIBLE}:
                continue
            try:
                evaluate_automatic_delivery(
                    source_system=message.source_system,
                    sender_kind=sender_kind_for.get(message.sender_actor_context_id or ""),
                    sender_actor_context_id=message.sender_actor_context_id,
                    target_kind=target_kind,
                    target_actor_context_id=target_actor_context_id,
                    target_binding_state=target_binding_state,
                    message_kind=message.message_kind,
                )
            except MailboxAclError:
                continue
            if message.delivery_state is DeliveryState.ENQUEUED:
                message = self.mark_eligible(message.message_id)
            selected.append(message)
        return selected
