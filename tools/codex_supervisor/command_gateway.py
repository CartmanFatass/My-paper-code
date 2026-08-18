"""Apply commands only from the bound App Server thread."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .command_protocol import CommandProtocolError, extract_from_completed_item
from .mailbox_store import MailboxStore
from .managed_models import BindingState, CommandValidationState, ManagedActionKind
from .managed_packet_send import ManagedPacketSendError, ManagedPacketSender
from .observer_evidence import ObserverEvidenceError, load_completed_final_item
from .semantic_bridge import SemanticBridge, SemanticBridgeError


class CommandGatewayError(RuntimeError):
    """Raised when a managed command cannot be accepted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommandGateway:
    def __init__(
        self,
        bindings: BindingStore,
        bridge: SemanticBridge,
        mailbox: MailboxStore | None = None,
        packets: ManagedPacketSender | None = None,
    ) -> None:
        self.bindings = bindings
        self.bridge = bridge
        self.mailbox = mailbox
        self.packets = packets

    def ingest_final_item(self, *, raw_message_seq: int) -> dict[str, Any]:
        try:
            observed = load_completed_final_item(self.bindings.store, raw_message_seq)
        except ObserverEvidenceError as exc:
            raise CommandGatewayError(str(exc)) from exc
        thread_id = str(observed["thread_id"])
        turn_id = str(observed["turn_id"])
        binding = self.bindings.binding_for_thread(thread_id)
        if binding is None or binding.binding_state not in {
            BindingState.ACTIVE,
            BindingState.VERIFICATION_REQUIRED,
        }:
            raise CommandGatewayError("no eligible binding for thread")
        existing = self.bindings.store.connection.execute(
            """SELECT * FROM managed_actor_commands
            WHERE binding_id = ? AND turn_id = ? AND raw_message_seq = ?""",
            (binding.binding_id, turn_id, raw_message_seq),
        ).fetchone()
        if existing is not None:
            receipt = self.bindings.store.get_command_receipt(str(existing["command_id"]))
            return {
                "validation_state": CommandValidationState.DUPLICATE.value,
                "command_id": existing["command_id"],
                "receipt": receipt,
            }
        command_id = f"cmd_{uuid.uuid4().hex}"
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                """INSERT INTO managed_actor_commands (
                    command_id, binding_id, thread_id, turn_id, raw_message_seq,
                    command_kind, payload_json, validation_state, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    command_id,
                    binding.binding_id,
                    thread_id,
                    turn_id,
                    raw_message_seq,
                    ManagedActionKind.NO_CONTROL_ACTION.value,
                    "{}",
                    CommandValidationState.RECEIVED.value,
                    _now(),
                ),
            )
        try:
            parsed = extract_from_completed_item(
                item_type=str(observed["item_type"]),
                lifecycle=str(observed["lifecycle"]),
                text=str(observed["text"]),
            )
        except CommandProtocolError as exc:
            self._reject(command_id, str(exc))
            raise CommandGatewayError(str(exc)) from exc
        if parsed is None:
            parsed = {
                "schema_version": "1.0",
                "packet_kind": "MANAGED_ACTOR_COMMAND",
                "action_kind": ManagedActionKind.NO_CONTROL_ACTION.value,
                "payload": {},
            }
        action = ManagedActionKind(str(parsed["action_kind"]))
        self._update_command(command_id, command_kind=action.value, payload_json=json.dumps(parsed), validation_state=CommandValidationState.VALIDATED.value)
        try:
            result = self._apply_action(action, parsed, binding, command_id, turn_id)
        except (SemanticBridgeError, ValueError, CommandGatewayError) as exc:
            self._reject(command_id, str(exc))
            raise CommandGatewayError(str(exc)) from exc
        receipt_id = self.bindings.store.record_command_receipt(
            command_id=command_id,
            effect_kind=action.value,
            semantic_ref=str(result.get("ack_id") or ""),
            result=result,
        )
        self._update_command(
            command_id,
            validation_state=CommandValidationState.APPLIED.value,
            applied_at=_now(),
            validated_at=_now(),
        )
        return {"validation_state": CommandValidationState.APPLIED.value, "command_id": command_id, "receipt_id": receipt_id, "result": result}

    def _apply_action(
        self,
        action: ManagedActionKind,
        parsed: dict[str, Any],
        binding: Any,
        command_id: str,
        turn_id: str,
    ) -> dict[str, Any]:
        if action is ManagedActionKind.NO_CONTROL_ACTION:
            return {"effect": "none"}
        if action is ManagedActionKind.CONTEXT_REANCHOR_ACK:
            expected = parsed.get("expected") if isinstance(parsed.get("expected"), dict) else {}
            return self.bridge.acknowledge_reanchor(
                actor_context_id=binding.actor_context_id,
                checkpoint_id=str(expected.get("checkpoint_id") or ""),
                expected_state_version=int(expected.get("state_version") or 0),
                expected_epoch_id=expected.get("epoch_id"),
                expected_epoch_revision=expected.get("epoch_revision"),
                app_server_turn_id=turn_id,
                supervisor_command_id=command_id,
            )
        inner = parsed.get("payload") if isinstance(parsed.get("payload"), dict) else {}
        if action is ManagedActionKind.MAILBOX_ACK:
            return self._mailbox_ack(binding, command_id, turn_id, inner)
        if action is ManagedActionKind.MAILBOX_INTAKE:
            return self._mailbox_intake(binding, command_id, turn_id, inner)
        if action is ManagedActionKind.MANAGED_PACKET_SEND:
            return self._packet_send(binding, inner)
        raise CommandGatewayError(f"unsupported action: {action.value}")

    def _require_mailbox(self) -> MailboxStore:
        if self.mailbox is None:
            raise CommandGatewayError("mailbox store is not configured")
        return self.mailbox

    def _message_owned_and_delivered(self, binding: Any, message_id: str) -> None:
        mailbox = self._require_mailbox()
        message = mailbox.get(message_id)
        if message is None:
            raise CommandGatewayError(f"unknown mailbox message: {message_id}")
        if message.target_actor_context_id != binding.actor_context_id:
            raise CommandGatewayError("mailbox message is not owned by this binding")
        delivered = mailbox.store.connection.execute(
            """SELECT b.app_server_turn_id FROM wake_batch_messages w
            JOIN wake_batches b ON b.wake_batch_id = w.wake_batch_id
            WHERE w.message_id = ? AND b.binding_id = ?
              AND b.state IN ('ACTIVE', 'COMPLETED')""",
            (message_id, binding.binding_id),
        ).fetchone()
        if delivered is None or message.delivery_state.value != "DELIVERED_TO_TURN":
            raise CommandGatewayError("mailbox message was not delivered to this binding")

    def _command_turn_follows_wake(self, binding: Any, turn_id: str, message_id: str) -> None:
        row = self.bindings.store.connection.execute(
            """SELECT b.app_server_turn_id, t.started_at AS wake_started
            FROM wake_batch_messages w
            JOIN wake_batches b ON b.wake_batch_id = w.wake_batch_id
            LEFT JOIN turn_snapshots t ON t.turn_id = b.app_server_turn_id
            WHERE w.message_id = ? AND b.binding_id = ?""",
            (message_id, binding.binding_id),
        ).fetchone()
        if row is None or not row["app_server_turn_id"]:
            return
        if str(row["app_server_turn_id"]) == turn_id:
            return
        command_turn = self.bindings.store.connection.execute(
            "SELECT started_at FROM turn_snapshots WHERE turn_id = ? AND thread_id = ?",
            (turn_id, binding.thread_id),
        ).fetchone()
        if command_turn is None:
            raise CommandGatewayError("command turn does not belong to this binding")
        wake_started = row["wake_started"]
        command_started = command_turn["started_at"]
        if wake_started and command_started and str(command_started) < str(wake_started):
            raise CommandGatewayError("command turn predates the wake turn")

    def _mailbox_ack(self, binding: Any, command_id: str, turn_id: str, inner: dict[str, Any]) -> dict[str, Any]:
        mailbox = self._require_mailbox()
        receipts = []
        for message_id in inner.get("message_ids") or []:
            self._message_owned_and_delivered(binding, str(message_id))
            self._command_turn_follows_wake(binding, turn_id, str(message_id))
            mailbox.acknowledge(str(message_id))
            receipts.append(mailbox.record_command_receipt(command_id=command_id, message_id=str(message_id), action="ACK"))
        return {"effect": "MAILBOX_ACK", "receipts": receipts, "turn_id": turn_id}

    def _mailbox_intake(self, binding: Any, command_id: str, turn_id: str, inner: dict[str, Any]) -> dict[str, Any]:
        mailbox = self._require_mailbox()
        receipts = []
        for item in inner.get("items") or []:
            message_id = str(item.get("message_id") or "")
            self._message_owned_and_delivered(binding, message_id)
            self._command_turn_follows_wake(binding, turn_id, message_id)
            mailbox.intake(message_id)
            receipts.append(mailbox.record_command_receipt(command_id=command_id, message_id=message_id, action="INTAKE"))
        return {"effect": "MAILBOX_INTAKE", "receipts": receipts, "turn_id": turn_id}

    def _packet_send(self, binding: Any, inner: dict[str, Any]) -> dict[str, Any]:
        if self.packets is None:
            raise CommandGatewayError("packet sender is not configured")
        try:
            packet = self.packets.send(
                source_binding_id=binding.binding_id,
                packet_kind=str(inner.get("packet_kind") or ""),
                target_alias=str(inner.get("target_alias") or ""),
                payload_ref=str(inner.get("payload_ref") or ""),
                marker=str(inner.get("marker") or ""),
                direction_id=inner.get("direction_id"),
            )
        except ManagedPacketSendError as exc:
            raise CommandGatewayError(str(exc)) from exc
        return {"effect": "MANAGED_PACKET_SEND", "packet_id": packet.get("packet_id"), "marker": packet.get("marker")}

    def _update_command(self, command_id: str, **fields: Any) -> None:
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                f"UPDATE managed_actor_commands SET {assignments} WHERE command_id = ?",
                list(fields.values()) + [command_id],
            )

    def _reject(self, command_id: str, reason: str) -> None:
        self._update_command(
            command_id,
            validation_state=CommandValidationState.REJECTED.value,
            rejection_reason=reason,
        )
