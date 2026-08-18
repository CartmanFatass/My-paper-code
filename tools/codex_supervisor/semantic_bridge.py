"""Internal, non-MCP bridge from supervisor bindings to the semantic ledger."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.codex_semantic_mvp.actor_models import ActorKind, ActorState, actor_context_from_row
from tools.codex_semantic_mvp.checkpoints import context_reanchor_ack, current_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_current
from tools.codex_semantic_mvp.store import SemanticStore

from .managed_models import ManagedActorKind
from .store import ObserverStore

ELIGIBLE_KINDS = frozenset({ActorKind.OPERATIONAL_ROOT, ActorKind.PORTFOLIO})


class SemanticBridgeError(ValueError):
    """Raised when a managed actor is ineligible or a reanchor is invalid."""


@dataclass(frozen=True)
class ManagedActorSnapshot:
    actor_context_id: str
    actor_kind: str
    scope_key: str
    direction_id: str | None
    state: str
    workflow_id: str | None
    state_version: int
    epoch_id: str | None
    epoch_revision: int | None
    checkpoint_id: str | None
    capsule_text: str
    canonical_refs: tuple[str, ...]
    open_obligation_ids: tuple[str, ...]


class SemanticBridge:
    def __init__(self, semantic_state_path: Path, supervisor_store: ObserverStore | None = None) -> None:
        self.semantic_state_path = Path(semantic_state_path)
        self.semantic = SemanticStore(self.semantic_state_path).initialize()
        self.supervisor_store = supervisor_store

    def close(self) -> None:
        self.semantic.close()

    def require_eligible(self, actor_context_id: str):
        row = self.semantic.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchone()
        if row is None:
            raise SemanticBridgeError(f"unknown actor: {actor_context_id}")
        actor = actor_context_from_row(row)
        if actor.actor_kind not in ELIGIBLE_KINDS:
            raise SemanticBridgeError(f"actor kind is not managed: {actor.actor_kind.value}")
        if actor.state is not ActorState.ACTIVE:
            raise SemanticBridgeError(f"actor is not ACTIVE: {actor.state.value}")
        return actor

    def snapshot(self, actor_context_id: str) -> ManagedActorSnapshot:
        actor = self.require_eligible(actor_context_id)
        workflow = self.semantic.current_actor_workflow(actor_context_id)
        epoch = plan_epoch_current(self.semantic, actor_context_id)
        checkpoint = current_checkpoint(self.semantic, actor_context_id)
        capsule: dict[str, Any] = {}
        if checkpoint is not None and isinstance(checkpoint.get("capsule"), dict):
            capsule = checkpoint["capsule"]
        obligation_ids: list[str] = []
        if workflow is not None:
            rows = self.semantic.connection.execute(
                "SELECT obligation_id FROM obligations WHERE workflow_id = ? AND state = 'OPEN'",
                (workflow["workflow_id"],),
            ).fetchall()
            obligation_ids = [str(row[0]) for row in rows]
        refs = capsule.get("canonical_refs") if isinstance(capsule.get("canonical_refs"), list) else []
        return ManagedActorSnapshot(
            actor_context_id=actor.actor_context_id,
            actor_kind=actor.actor_kind.value,
            scope_key=actor.scope_key,
            direction_id=actor.direction_id,
            state=actor.state.value,
            workflow_id=None if workflow is None else str(workflow["workflow_id"]),
            state_version=int((workflow or {}).get("state_version") or 0),
            epoch_id=None if epoch is None else epoch.get("epoch_id"),
            epoch_revision=None if epoch is None else epoch.get("revision"),
            checkpoint_id=None if checkpoint is None else str(checkpoint.get("checkpoint_id") or "") or None,
            capsule_text=json.dumps(capsule, ensure_ascii=False, separators=(",", ":")) if capsule else "",
            canonical_refs=tuple(str(item) for item in refs),
            open_obligation_ids=tuple(obligation_ids),
        )

    def acknowledge_reanchor(
        self,
        *,
        actor_context_id: str,
        checkpoint_id: str,
        expected_state_version: int,
        expected_epoch_id: str | None,
        expected_epoch_revision: int | None,
        app_server_turn_id: str,
        supervisor_command_id: str,
    ) -> dict[str, object]:
        if self.supervisor_store is not None:
            existing = self.supervisor_store.get_command_receipt(supervisor_command_id)
            if existing is not None:
                return json.loads(existing["result_json"])
        self.require_eligible(actor_context_id)
        result = context_reanchor_ack(
            self.semantic,
            actor_context_id=actor_context_id,
            checkpoint_id=checkpoint_id,
            state_version=expected_state_version,
            epoch_id=expected_epoch_id,
            epoch_revision=expected_epoch_revision,
            actor_turn_id=app_server_turn_id,
        )
        payload = dict(result)
        payload["supervisor_command_id"] = supervisor_command_id
        payload["checkpoint_id"] = checkpoint_id
        payload["state_version"] = expected_state_version
        payload["epoch_id"] = expected_epoch_id
        payload["epoch_revision"] = expected_epoch_revision
        if self.supervisor_store is not None:
            self.supervisor_store.record_command_receipt(
                command_id=supervisor_command_id,
                effect_kind="CONTEXT_REANCHOR_ACK",
                semantic_ref=str(payload.get("ack_id") or ""),
                result=payload,
            )
        return payload


def managed_kind_from_snapshot(snapshot: ManagedActorSnapshot) -> ManagedActorKind:
    return ManagedActorKind(snapshot.actor_kind)
