"""Apply commands only from the bound App Server thread."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .binding_store import BindingStore
from .command_protocol import CommandProtocolError, extract_from_completed_item
from .managed_models import BindingState, CommandValidationState, ManagedActionKind
from .semantic_bridge import SemanticBridge, SemanticBridgeError


class CommandGatewayError(RuntimeError):
    """Raised when a managed command cannot be accepted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommandGateway:
    def __init__(self, bindings: BindingStore, bridge: SemanticBridge) -> None:
        self.bindings = bindings
        self.bridge = bridge

    def ingest_final_item(
        self,
        *,
        thread_id: str,
        turn_id: str,
        raw_message_seq: int,
        item_type: str,
        lifecycle: str,
        text: str,
    ) -> dict[str, Any]:
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
            parsed = extract_from_completed_item(item_type=item_type, lifecycle=lifecycle, text=text)
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
        if action is ManagedActionKind.NO_CONTROL_ACTION:
            result = {"effect": "none"}
        else:
            expected = parsed.get("expected") if isinstance(parsed.get("expected"), dict) else {}
            try:
                result = self.bridge.acknowledge_reanchor(
                    actor_context_id=binding.actor_context_id,
                    checkpoint_id=str(expected.get("checkpoint_id") or ""),
                    expected_state_version=int(expected.get("state_version") or 0),
                    expected_epoch_id=expected.get("epoch_id"),
                    expected_epoch_revision=expected.get("epoch_revision"),
                    app_server_turn_id=turn_id,
                    supervisor_command_id=command_id,
                )
            except (SemanticBridgeError, ValueError) as exc:
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
