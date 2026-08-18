"""Apply commands only from the bound App Server thread."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore, currentness_tuple
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
            return self._reconcile_existing_command(existing)
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
        expected = parsed.get("expected") if isinstance(parsed.get("expected"), dict) else {}
        self._update_command(
            command_id,
            command_kind=action.value,
            payload_json=json.dumps(parsed),
            validation_state=CommandValidationState.VALIDATED.value,
            expected_checkpoint_id=expected.get("checkpoint_id"),
            expected_state_version=expected.get("state_version"),
            expected_epoch_id=expected.get("epoch_id"),
            expected_epoch_revision=expected.get("epoch_revision"),
        )
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
        self._refuse_incident_source(binding, turn_id)
        if action is not ManagedActionKind.NO_CONTROL_ACTION:
            try:
                actor = self.bridge.require_eligible(binding.actor_context_id)
            except SemanticBridgeError as exc:
                try:
                    self.bindings.suspend(binding.binding_id)
                except Exception:
                    pass
                raise CommandGatewayError(str(exc)) from exc
            if actor.actor_kind.value != binding.actor_kind.value:
                raise CommandGatewayError("actor kind no longer matches binding")
        if action is ManagedActionKind.CONTEXT_REANCHOR_ACK:
            expected = parsed.get("expected") if isinstance(parsed.get("expected"), dict) else {}
            result = self.bridge.acknowledge_reanchor(
                actor_context_id=binding.actor_context_id,
                checkpoint_id=str(expected.get("checkpoint_id") or ""),
                expected_state_version=int(expected.get("state_version") or 0),
                expected_epoch_id=expected.get("epoch_id"),
                expected_epoch_revision=expected.get("epoch_revision"),
                app_server_turn_id=turn_id,
                supervisor_command_id=command_id,
            )
            result["checkpoint_id"] = str(expected.get("checkpoint_id") or result.get("checkpoint_id") or "")
            result["state_version"] = int(expected.get("state_version") or 0)
            result["epoch_id"] = expected.get("epoch_id")
            result["epoch_revision"] = expected.get("epoch_revision")
            return result
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
            raise CommandGatewayError("command/wake ordering cannot be proven")
        if str(row["app_server_turn_id"]) == turn_id:
            return
        wake_key = self._turn_order_key(str(row["app_server_turn_id"]), binding.thread_id)
        command_key = self._turn_order_key(turn_id, binding.thread_id)
        if wake_key is None or command_key is None or wake_key[0] != command_key[0]:
            raise CommandGatewayError("command/wake ordering cannot be proven")
        if command_key[1] < wake_key[1]:
            raise CommandGatewayError("command turn predates the wake turn")

    def _refuse_incident_source(self, binding: Any, turn_id: str) -> None:
        turn = self.bindings.store.connection.execute(
            """SELECT submission_state FROM managed_turn_intents
            WHERE binding_id = ? AND app_server_turn_id = ?""",
            (binding.binding_id, turn_id),
        ).fetchone()
        if turn is not None and str(turn[0]) == "INCIDENT":
            raise CommandGatewayError("command turn is INCIDENT; no control effect")
        batch = self.bindings.store.connection.execute(
            """SELECT state FROM wake_batches
            WHERE binding_id = ? AND app_server_turn_id = ?""",
            (binding.binding_id, turn_id),
        ).fetchone()
        if batch is not None and str(batch[0]) == "INCIDENT":
            raise CommandGatewayError("wake batch is INCIDENT; no control effect")

    def _turn_order_key(self, turn_id: str, thread_id: str | None) -> tuple[str, object] | None:
        first_event = self.bindings.store.connection.execute(
            """SELECT MIN(raw_message_seq) FROM normalized_events
            WHERE turn_id = ? AND thread_id = ?""",
            (turn_id, thread_id),
        ).fetchone()
        first_raw = self.bindings.store.connection.execute(
            """SELECT MIN(raw_message_seq) FROM raw_messages
            WHERE turn_id = ? AND thread_id = ? AND direction = 'stdout'""",
            (turn_id, thread_id),
        ).fetchone()
        candidates = [
            int(row[0])
            for row in (first_event, first_raw)
            if row is not None and row[0] is not None
        ]
        if not candidates:
            return None
        return ("seq", min(candidates))

    def _effect_receipt_exists(self, existing: Any) -> bool:
        command_id = str(existing["command_id"])
        kind = str(existing["command_kind"] or "")
        if kind in {
            ManagedActionKind.MAILBOX_ACK.value,
            ManagedActionKind.MAILBOX_INTAKE.value,
        }:
            if self.mailbox is None:
                return False
            row = self.mailbox.store.connection.execute(
                "SELECT 1 FROM mailbox_command_receipts WHERE command_id = ?",
                (command_id,),
            ).fetchone()
            return row is not None
        if kind == ManagedActionKind.MANAGED_PACKET_SEND.value:
            payload = json.loads(str(existing["payload_json"] or "{}"))
            inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
            marker = inner.get("marker")
            if not marker:
                return False
            found = self.bridge.semantic.connection.execute(
                "SELECT 1 FROM packet_refs WHERE marker = ?",
                (str(marker),),
            ).fetchone()
            return found is not None
        return False

    def _mark_command_incident(self, command_id: str, reason: str) -> None:
        self._update_command(
            command_id,
            validation_state=CommandValidationState.INCIDENT.value,
            rejection_reason=reason,
        )

    def _reconcile_existing_command(self, existing: Any) -> dict[str, Any]:
        command_id = str(existing["command_id"])
        state = str(existing["validation_state"])
        if state == CommandValidationState.INCIDENT.value:
            raise CommandGatewayError(
                "command is in INCIDENT; operator reconciliation required"
            )
        receipt = self.bindings.store.get_command_receipt(command_id)
        if state in {
            CommandValidationState.RECEIVED.value,
            CommandValidationState.VALIDATED.value,
        }:
            if receipt is None:
                if self._effect_receipt_exists(existing):
                    self._mark_command_incident(
                        command_id,
                        "command effect requires operator reconciliation; supervisor receipt is missing",
                    )
                    raise CommandGatewayError(
                        "command effect requires operator reconciliation; supervisor receipt is missing"
                    )
                self._mark_command_incident(
                    command_id,
                    "command effect requires operator reconciliation; receipt is missing",
                )
                raise CommandGatewayError(
                    "command effect requires operator reconciliation; receipt is missing"
                )
            payload = json.loads(str(existing["payload_json"] or "{}"))
            expected = payload.get("expected") if isinstance(payload.get("expected"), dict) else {}
            receipt_result = json.loads(str(receipt["result_json"] or "{}"))
            expected_tuple = currentness_tuple(
                expected.get("checkpoint_id"),
                expected.get("state_version"),
                expected.get("epoch_id"),
                expected.get("epoch_revision"),
            )
            receipt_tuple = currentness_tuple(
                receipt_result["checkpoint_id"] if "checkpoint_id" in receipt_result else expected.get("checkpoint_id"),
                receipt_result["state_version"] if "state_version" in receipt_result else expected.get("state_version"),
                receipt_result["epoch_id"] if "epoch_id" in receipt_result else expected.get("epoch_id"),
                receipt_result["epoch_revision"] if "epoch_revision" in receipt_result else expected.get("epoch_revision"),
            )
            if expected_tuple != receipt_tuple:
                self._mark_command_incident(command_id, "receipt tuple does not match command")
                raise CommandGatewayError("receipt tuple does not match command")
            self._update_command(
                command_id,
                validation_state=CommandValidationState.APPLIED.value,
                applied_at=_now(),
                validated_at=_now(),
            )
            return {
                "validation_state": CommandValidationState.APPLIED.value,
                "command_id": command_id,
                "receipt": receipt,
                "reconciled": True,
            }
        return {
            "validation_state": CommandValidationState.DUPLICATE.value,
            "command_id": command_id,
            "receipt": receipt,
        }

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
