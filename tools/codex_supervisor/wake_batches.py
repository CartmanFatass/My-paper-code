"""Neutral wake envelopes. Typed references only; no child prose."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from dataclasses import dataclass

from .mailbox_models import (
    MAX_WAKE_INPUT_BYTES,
    MAX_WAKE_MESSAGES,
    WAKE_ENVELOPE_HEADER,
    MailboxRefError,
    MailboxMessage,
    WakeBatchState,
    validate_mailbox_ref,
)
from .mailbox_store import MailboxStore
from .managed_context import record_context_injection
from .semantic_bridge import ManagedActorSnapshot
from .store import ObserverStore


class WakeBatchError(ValueError):
    """Raised when a wake batch cannot be prepared."""


@dataclass(frozen=True)
class WakeEnvelope:
    text: str
    included_message_ids: tuple[str, ...]
    excluded_message_ids: tuple[str, ...]


def wake_client_user_message_id(wake_batch_id: str) -> str:
    return f"hmasd-wake:{wake_batch_id}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_wake_text(
    snapshot: ManagedActorSnapshot,
    *,
    wake_batch_id: str,
    messages: list[MailboxMessage],
) -> WakeEnvelope:
    validated_messages: list[tuple[MailboxMessage, str, str]] = []
    try:
        for message in messages:
            validated_messages.append(
                (
                    message,
                    validate_mailbox_ref(message.subject_ref, field_name="subject_ref"),
                    validate_mailbox_ref(message.payload_ref, field_name="payload_ref"),
                )
            )
    except MailboxRefError as exc:
        raise WakeBatchError(f"invalid mailbox reference: {exc}") from exc

    lines = [
        WAKE_ENVELOPE_HEADER,
        "",
        "new_user_authority=false",
        "disposition_implied=false",
        "target_identity_is_runtime_bound=true",
        f"wake_batch_id={wake_batch_id}",
        f"checkpoint_id={snapshot.checkpoint_id or 'none'}",
        f"state_version={snapshot.state_version}",
        f"epoch_id={snapshot.epoch_id or 'none'}",
        f"epoch_revision={snapshot.epoch_revision if snapshot.epoch_revision is not None else 'none'}",
        "",
        "MESSAGES",
    ]
    included: list[MailboxMessage] = []
    for message, subject_ref, payload_ref in validated_messages[:MAX_WAKE_MESSAGES]:
        block = [
            f"- message_id={message.message_id}",
            f"  kind={message.message_kind.value}",
            f"  subject_ref={subject_ref}",
            f"  payload_ref={payload_ref}",
        ]
        candidate = "\n".join(lines + block + ["", "Required:", "1. inspect each typed reference;"])
        if len(candidate.encode("utf-8")) > MAX_WAKE_INPUT_BYTES:
            break
        lines.extend(block)
        included.append(message)
    lines.extend(
        [
            "",
            "Required:",
            "1. inspect each typed reference;",
            "2. do not infer global disposition;",
            "3. return at most one HMASD_MANAGED_ACTOR_COMMAND_V1 envelope.",
            "",
        ]
    )
    text = "\n".join(lines)
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_WAKE_INPUT_BYTES:
        text = encoded[:MAX_WAKE_INPUT_BYTES].decode("utf-8", errors="ignore")
    included_ids = tuple(item.message_id for item in included)
    excluded_ids = tuple(
        item.message_id for item in messages if item.message_id not in set(included_ids)
    )
    return WakeEnvelope(text=text, included_message_ids=included_ids, excluded_message_ids=excluded_ids)


class WakeBatchStore:
    def __init__(self, store: ObserverStore, mailbox: MailboxStore) -> None:
        self.store = store
        self.mailbox = mailbox

    def open_batch_for_binding(self, binding_id: str) -> dict[str, object] | None:
        row = self.store.connection.execute(
            """SELECT * FROM wake_batches
            WHERE binding_id = ? AND state IN ('PREPARED', 'SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'ACTIVE')
            ORDER BY prepared_at DESC""",
            (binding_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def get(self, wake_batch_id: str) -> dict[str, object] | None:
        row = self.store.connection.execute(
            "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
            (wake_batch_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def messages_for(self, wake_batch_id: str) -> list[MailboxMessage]:
        rows = self.store.connection.execute(
            """SELECT m.* FROM mailbox_messages m
            JOIN wake_batch_messages b ON b.message_id = m.message_id
            WHERE b.wake_batch_id = ?
            ORDER BY b.ordinal""",
            (wake_batch_id,),
        ).fetchall()
        from .mailbox_store import _row_to_message

        return [_row_to_message(row) for row in rows]

    def prepare(
        self,
        *,
        binding_id: str,
        thread_id: str,
        snapshot: ManagedActorSnapshot,
        messages: list[MailboxMessage],
        lease_generation: int | None = None,
        lease_holder: str | None = None,
    ) -> dict[str, object]:
        existing = self.open_batch_for_binding(binding_id)
        if existing is not None:
            raise WakeBatchError("binding already has an open wake batch")
        if not messages:
            raise WakeBatchError("wake batch requires at least one message")
        ordered = sorted(
            messages,
            key=lambda item: (-item.priority, item.created_at, item.message_id),
        )[:MAX_WAKE_MESSAGES]
        wake_batch_id = f"wake_{uuid.uuid4().hex}"
        client_id = wake_client_user_message_id(wake_batch_id)
        envelope = build_wake_text(snapshot, wake_batch_id=wake_batch_id, messages=ordered)
        included = [item for item in ordered if item.message_id in set(envelope.included_message_ids)]
        if not included:
            raise WakeBatchError("wake envelope could not include any message")
        now = _now()
        from .durability.effects import EffectJournal
        from .durability.transaction import DurabilityTransaction

        with self.store._lock:
            with DurabilityTransaction(self.store.connection):
                effect = EffectJournal(self.store.connection).prepare_effect(
                    owner_kind="WAKE_BATCH",
                    owner_id=wake_batch_id,
                    binding_id=binding_id,
                    method="turn/start",
                    client_key=client_id,
                    request={"threadId": thread_id, "clientUserMessageId": client_id},
                )
                self.store.connection.execute(
                    """INSERT INTO wake_batches (
                        wake_batch_id, binding_id, thread_id, state, client_user_message_id,
                        prepared_at, lease_generation, lease_holder, effect_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        wake_batch_id,
                        binding_id,
                        thread_id,
                        WakeBatchState.PREPARED.value,
                        client_id,
                        now,
                        lease_generation,
                        lease_holder,
                        effect.effect_id,
                    ),
                )
                for ordinal, message in enumerate(included):
                    self.store.connection.execute(
                        """INSERT INTO wake_batch_messages (wake_batch_id, message_id, ordinal)
                        VALUES (?, ?, ?)""",
                        (wake_batch_id, message.message_id, ordinal),
                    )
                for message in included:
                    if message.delivery_state.value == "ENQUEUED":
                        self.mailbox.mark_eligible(message.message_id)
                    self.mailbox.mark_batched(message.message_id)
        record_context_injection(
            self.store,
            binding_id=binding_id,
            turn_intent_id=wake_batch_id,
            snapshot=snapshot,
            input_text=envelope.text,
            mailbox_message_ids=envelope.included_message_ids,
        )
        row = self.get(wake_batch_id)
        assert row is not None
        row["input_text"] = envelope.text
        row["included_message_ids"] = envelope.included_message_ids
        row["excluded_message_ids"] = envelope.excluded_message_ids
        return row

    def set_state(self, wake_batch_id: str, **fields: object) -> dict[str, object]:
        from .durability.models import AggregateKind, TransitionCause, TransitionRequest
        from .durability.transaction import DurabilityTransaction
        from .durability.transitions import TransitionError, TransitionKernel

        expected = fields.pop("expected_state", None)
        current = self.get(wake_batch_id)
        if current is None:
            raise WakeBatchError("unknown wake batch")
        if "state" in fields and fields["state"] != current["state"]:
            target = str(fields["state"])
            if str(current["state"]) == WakeBatchState.PREPARED.value and target == WakeBatchState.SUBMITTING.value:
                raise WakeBatchError("PREPARED → SUBMITTING is only allowed in record_effect_write_start")
            version = int(current.get("version") or 0)
            cause = fields.pop("cause_kind", TransitionCause.CONTROL_COMMAND)
            if isinstance(cause, str):
                cause = TransitionCause(cause)
            try:
                with self.store._lock:
                    with DurabilityTransaction(self.store.connection):
                        TransitionKernel(self.store.connection).apply(
                            TransitionRequest(
                                aggregate_kind=AggregateKind.WAKE_BATCH,
                                aggregate_id=wake_batch_id,
                                expected_state=str(expected or current["state"]),
                                expected_version=version,
                                target_state=str(fields.pop("state")),
                                cause_kind=cause,
                                cause_ref=str(fields.get("completion_status") or "wake"),
                                field_updates=fields,
                            )
                        )
            except TransitionError as exc:
                raise WakeBatchError(str(exc)) from exc
        elif fields:
            assignments = ", ".join(f"{key} = ?" for key in fields)
            values = list(fields.values()) + [wake_batch_id]
            sql = f"UPDATE wake_batches SET {assignments} WHERE wake_batch_id = ?"
            if expected is not None:
                sql += " AND state = ?"
                values.append(expected)
            with self.store._lock, self.store.connection:
                self.store.connection.execute(sql, values)
        row = self.get(wake_batch_id)
        assert row is not None
        return row
