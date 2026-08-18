"""Supervisor-owned App Server thread to semantic actor bindings."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any  # noqa: F401 - used by row helpers

from .managed_models import (
    BindingState,
    HistoryTrust,
    ManagedActorBinding,
    ManagedActorKind,
    MemoryPolicyState,
    ThreadOrigin,
)
from .semantic_bridge import ManagedActorSnapshot, SemanticBridge
from .store import ObserverStore


class BindingError(ValueError):
    """Raised when a binding transition or uniqueness rule is violated."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _row_value(row: Any, key: str) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def _row_to_binding(row: Any) -> ManagedActorBinding:
    return ManagedActorBinding(
        binding_id=str(row["binding_id"]),
        actor_context_id=str(row["actor_context_id"]),
        actor_kind=ManagedActorKind(str(row["actor_kind"])),
        semantic_scope_key=str(row["semantic_scope_key"]),
        direction_id=None if row["direction_id"] is None else str(row["direction_id"]),
        thread_id=None if row["thread_id"] is None else str(row["thread_id"]),
        thread_origin=ThreadOrigin(str(row["thread_origin"])),
        history_trust=HistoryTrust(str(row["history_trust"])),
        binding_state=BindingState(str(row["binding_state"])),
        memory_policy_state=MemoryPolicyState(str(row["memory_policy_state"])),
        repo_root=str(row["repo_root"]),
        thread_cwd=str(row["thread_cwd"]),
        created_by_operator=str(row["created_by_operator"]),
        created_at=str(row["created_at"]),
        verification_turn_intent_id=None
        if _row_value(row, "verification_turn_intent_id") is None
        else str(row["verification_turn_intent_id"]),
        verification_turn_id=None
        if _row_value(row, "verification_turn_id") is None
        else str(row["verification_turn_id"]),
        verification_command_id=None
        if _row_value(row, "verification_command_id") is None
        else str(row["verification_command_id"]),
        verification_receipt_id=None
        if _row_value(row, "verification_receipt_id") is None
        else str(row["verification_receipt_id"]),
        verified_checkpoint_id=None
        if _row_value(row, "verified_checkpoint_id") is None
        else str(row["verified_checkpoint_id"]),
    )


class BindingStore:
    def __init__(self, store: ObserverStore, bridge: SemanticBridge | None = None) -> None:
        self.store = store
        self.bridge = bridge

    def _record_event(self, binding_id: str, event_kind: str, payload: dict[str, Any]) -> None:
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """INSERT INTO managed_binding_events (
                    binding_id, event_kind, payload_json, created_at
                ) VALUES (?, ?, ?, ?)""",
                (binding_id, event_kind, json.dumps(payload, ensure_ascii=False), _now()),
            )

    def list_bindings(self) -> list[ManagedActorBinding]:
        with self.store._lock:
            rows = self.store.connection.execute(
                "SELECT * FROM managed_actor_bindings ORDER BY created_at, binding_id"
            ).fetchall()
            return [_row_to_binding(row) for row in rows]

    def get(self, binding_id: str) -> ManagedActorBinding | None:
        with self.store._lock:
            row = self.store.connection.execute(
                "SELECT * FROM managed_actor_bindings WHERE binding_id = ?",
                (binding_id,),
            ).fetchone()
            return None if row is None else _row_to_binding(row)

    def binding_for_thread(self, thread_id: str) -> ManagedActorBinding | None:
        with self.store._lock:
            row = self.store.connection.execute(
                "SELECT * FROM managed_actor_bindings WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            return None if row is None else _row_to_binding(row)

    def binding_for_actor(self, actor_context_id: str) -> ManagedActorBinding | None:
        with self.store._lock:
            row = self.store.connection.execute(
                """SELECT * FROM managed_actor_bindings
                WHERE actor_context_id = ? AND binding_state != ?
                ORDER BY created_at DESC""",
                (actor_context_id, BindingState.REVOKED.value),
            ).fetchone()
            return None if row is None else _row_to_binding(row)

    def prepare_binding(
        self,
        actor_snapshot: ManagedActorSnapshot,
        *,
        repo_root: str,
        thread_cwd: str,
        created_by_operator: str,
        thread_origin: ThreadOrigin,
        history_trust: HistoryTrust,
    ) -> str:
        if actor_snapshot.actor_kind not in {kind.value for kind in ManagedActorKind}:
            raise BindingError(f"actor kind cannot be bound: {actor_snapshot.actor_kind}")
        existing = self.binding_for_actor(actor_snapshot.actor_context_id)
        if existing is not None:
            raise BindingError("actor already has a non-revoked binding")
        binding_id = _new_id("bind")
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """INSERT INTO managed_actor_bindings (
                    binding_id, actor_context_id, actor_kind, semantic_scope_key,
                    direction_id, thread_id, thread_origin, history_trust,
                    binding_state, memory_policy_state, repo_root, thread_cwd,
                    created_by_operator, created_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    binding_id,
                    actor_snapshot.actor_context_id,
                    actor_snapshot.actor_kind,
                    actor_snapshot.scope_key,
                    actor_snapshot.direction_id,
                    thread_origin.value,
                    history_trust.value,
                    BindingState.PREPARED.value,
                    MemoryPolicyState.UNVERIFIED.value,
                    repo_root,
                    thread_cwd,
                    created_by_operator,
                    now,
                ),
            )
        self._record_event(binding_id, "BINDING_PREPARED", {"actor_kind": actor_snapshot.actor_kind})
        return binding_id

    def attach_thread(self, binding_id: str, thread_id: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        if binding.binding_state is not BindingState.PREPARED:
            raise BindingError("only PREPARED bindings may attach a thread")
        other = self.binding_for_thread(thread_id)
        if other is not None:
            raise BindingError("thread is already bound")
        if self.bridge is not None:
            snapshot = self.bridge.snapshot(binding.actor_context_id)
            if snapshot.actor_kind != binding.actor_kind.value:
                raise BindingError("actor kind no longer matches binding")
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """UPDATE managed_actor_bindings
                SET thread_id = ?, binding_state = ?, thread_created_at = ?
                WHERE binding_id = ?""",
                (thread_id, BindingState.THREAD_CREATED.value, now, binding_id),
            )
        self._record_event(binding_id, "THREAD_ATTACHED", {"thread_id": thread_id})
        attached = self.get(binding_id)
        assert attached is not None
        return attached

    def mark_verification_required(self, binding_id: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.THREAD_CREATED:
            raise BindingError("only THREAD_CREATED bindings may enter verification")
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                "UPDATE managed_actor_bindings SET binding_state = ? WHERE binding_id = ?",
                (BindingState.VERIFICATION_REQUIRED.value, binding_id),
            )
        self._record_event(binding_id, "VERIFICATION_REQUIRED", {})
        updated = self.get(binding_id)
        assert updated is not None
        return updated

    def confirm_global_memory_disabled(self, binding_id: str, *, operator: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        if binding.binding_state is BindingState.REVOKED:
            raise BindingError("revoked binding cannot change memory policy")
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """UPDATE managed_actor_bindings
                SET memory_policy_state = ?, last_verified_at = ?
                WHERE binding_id = ?""",
                (MemoryPolicyState.OPERATOR_CONFIRMED_GLOBAL_DISABLED.value, now, binding_id),
            )
        self._record_event(binding_id, "MEMORY_OPERATOR_CONFIRMED", {"operator": operator})
        updated = self.get(binding_id)
        assert updated is not None
        return updated

    def _require_verification_receipt(self, binding: ManagedActorBinding) -> dict[str, str]:
        if self.bridge is None:
            raise BindingError("activation requires a semantic bridge and verification receipt")
        snapshot = self.bridge.snapshot(binding.actor_context_id)
        if snapshot.actor_kind != binding.actor_kind.value:
            raise BindingError("actor kind no longer matches binding")
        if snapshot.state != "ACTIVE":
            raise BindingError("actor is not ACTIVE")
        intent = self.store.connection.execute(
            """SELECT * FROM managed_turn_intents
            WHERE binding_id = ? AND intent_kind IN ('BOOTSTRAP', 'IDENTITY_VERIFICATION')
            ORDER BY prepared_at DESC""",
            (binding.binding_id,),
        ).fetchone()
        if intent is None or not intent["app_server_turn_id"]:
            raise BindingError("missing verification turn intent")
        turn_id = str(intent["app_server_turn_id"])
        command = self.store.connection.execute(
            """SELECT * FROM managed_actor_commands
            WHERE binding_id = ? AND thread_id = ? AND turn_id = ?
              AND command_kind = 'CONTEXT_REANCHOR_ACK' AND validation_state = 'APPLIED'
            ORDER BY applied_at DESC""",
            (binding.binding_id, binding.thread_id, turn_id),
        ).fetchone()
        if command is None:
            raise BindingError("missing applied CONTEXT_REANCHOR_ACK")
        receipt = self.store.get_command_receipt(str(command["command_id"]))
        if receipt is None:
            raise BindingError("missing verification receipt")
        payload = json.loads(str(command["payload_json"] or "{}"))
        expected = payload.get("expected") if isinstance(payload.get("expected"), dict) else {}
        intent_checkpoint = "" if intent["checkpoint_id"] is None else str(intent["checkpoint_id"])
        if str(expected.get("checkpoint_id") or "") != intent_checkpoint:
            raise BindingError("ACK does not match verification checkpoint")
        turn = self.store.connection.execute(
            "SELECT * FROM turn_snapshots WHERE turn_id = ? AND status = 'completed'",
            (turn_id,),
        ).fetchone()
        item = self.store.connection.execute(
            """SELECT * FROM item_snapshots
            WHERE thread_id = ? AND turn_id = ? AND item_type = 'agentMessage' AND lifecycle = 'COMPLETED'""",
            (binding.thread_id, turn_id),
        ).fetchone()
        raw = self.store.connection.execute(
            """SELECT 1 FROM raw_messages
            WHERE direction = 'stdout' AND thread_id = ? AND turn_id = ?""",
            (binding.thread_id, turn_id),
        ).fetchone()
        if turn is None or item is None or raw is None:
            raise BindingError("observer has no completed verification turn/item")
        return {
            "verification_turn_intent_id": str(intent["turn_intent_id"]),
            "verification_turn_id": turn_id,
            "verification_command_id": str(command["command_id"]),
            "verification_receipt_id": str(receipt["receipt_id"]),
            "verified_checkpoint_id": str(snapshot.checkpoint_id or ""),
        }

    def activate(self, binding_id: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        if binding.binding_state is not BindingState.VERIFICATION_REQUIRED:
            raise BindingError("only VERIFICATION_REQUIRED bindings may activate")
        if binding.memory_policy_state is MemoryPolicyState.UNVERIFIED:
            raise BindingError("memory policy is unverified")
        if not binding.thread_id:
            raise BindingError("binding has no thread")
        evidence = self._require_verification_receipt(binding)
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                """UPDATE managed_actor_bindings
                SET binding_state = ?, activated_at = ?, last_verified_at = ?,
                    verification_turn_intent_id = ?, verification_turn_id = ?,
                    verification_command_id = ?, verification_receipt_id = ?,
                    verified_checkpoint_id = ?
                WHERE binding_id = ?""",
                (
                    BindingState.ACTIVE.value,
                    now,
                    now,
                    evidence["verification_turn_intent_id"],
                    evidence["verification_turn_id"],
                    evidence["verification_command_id"],
                    evidence["verification_receipt_id"],
                    evidence["verified_checkpoint_id"],
                    binding_id,
                ),
            )
        self._record_event(binding_id, "BINDING_ACTIVATED", evidence)
        updated = self.get(binding_id)
        assert updated is not None
        return updated

    def suspend(self, binding_id: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None or binding.binding_state in {BindingState.REVOKED, BindingState.SUSPENDED}:
            raise BindingError("binding cannot be suspended")
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                "UPDATE managed_actor_bindings SET binding_state = ?, suspended_at = ? WHERE binding_id = ?",
                (BindingState.SUSPENDED.value, now, binding_id),
            )
        self._record_event(binding_id, "BINDING_SUSPENDED", {})
        updated = self.get(binding_id)
        assert updated is not None
        return updated

    def revoke(self, binding_id: str) -> ManagedActorBinding:
        binding = self.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        if binding.binding_state is BindingState.REVOKED:
            raise BindingError("binding is already revoked")
        now = _now()
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                "UPDATE managed_actor_bindings SET binding_state = ?, revoked_at = ? WHERE binding_id = ?",
                (BindingState.REVOKED.value, now, binding_id),
            )
        self._record_event(binding_id, "BINDING_REVOKED", {})
        updated = self.get(binding_id)
        assert updated is not None
        return updated
