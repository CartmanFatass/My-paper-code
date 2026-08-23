"""Internal, non-MCP bridge from supervisor bindings to the semantic ledger."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from tools.codex_semantic_mvp.actor_models import ActorKind, ActorState, actor_context_from_row
from tools.codex_semantic_mvp.checkpoints import context_reanchor_ack, current_checkpoint
from tools.codex_semantic_mvp.epochs import plan_epoch_current
from tools.codex_semantic_mvp.models import ObligationKind
from tools.codex_semantic_mvp.store import SemanticStore

from .managed_models import ManagedActorKind
from .store import ObserverStore

ELIGIBLE_KINDS = frozenset({ActorKind.OPERATIONAL_ROOT, ActorKind.PORTFOLIO})


class SemanticBridgeError(ValueError):
    """Raised when a managed actor is ineligible or a reanchor is invalid."""


class SemanticActorEligibilityError(SemanticBridgeError):
    """Raised only when the guarded semantic actor is not managed and ACTIVE."""


class SemanticCurrentnessError(SemanticBridgeError):
    """Raised only when the guarded four-field currentness tuple changed."""


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
        self.semantic = SemanticStore.open_existing(self.semantic_state_path)
        self.supervisor_store = supervisor_store

    def close(self) -> None:
        self.semantic.close()

    def _require_eligible_unlocked(self, actor_context_id: str):
        row = self.semantic.connection.execute(
            "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
            (actor_context_id,),
        ).fetchone()
        if row is None:
            raise SemanticActorEligibilityError(f"unknown actor: {actor_context_id}")
        actor = actor_context_from_row(row)
        if actor.actor_kind not in ELIGIBLE_KINDS:
            raise SemanticActorEligibilityError(
                f"actor kind is not managed: {actor.actor_kind.value}"
            )
        if actor.state is not ActorState.ACTIVE:
            raise SemanticActorEligibilityError(
                f"actor is not ACTIVE: {actor.state.value}"
            )
        return actor

    def require_eligible(self, actor_context_id: str):
        with self.semantic._lock:
            return self._require_eligible_unlocked(actor_context_id)

    def _snapshot_unlocked(self, actor_context_id: str) -> ManagedActorSnapshot:
        connection = self.semantic.connection
        actor = self._require_eligible_unlocked(actor_context_id)
        workflow = self.semantic.current_actor_workflow(actor_context_id)
        epoch = plan_epoch_current(self.semantic, actor_context_id)
        checkpoint = current_checkpoint(self.semantic, actor_context_id)
        capsule: dict[str, Any] = {}
        if checkpoint is not None and isinstance(checkpoint.get("capsule"), dict):
            capsule = checkpoint["capsule"]
        obligation_ids: list[str] = []
        if workflow is not None:
            rows = connection.execute(
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

    def snapshot(self, actor_context_id: str) -> ManagedActorSnapshot:
        with self.semantic._lock:
            connection = self.semantic.connection
            owns_transaction = not connection.in_transaction
            if owns_transaction:
                connection.execute("BEGIN")
            try:
                result = self._snapshot_unlocked(actor_context_id)
                if owns_transaction:
                    connection.commit()
                return result
            except Exception:
                if owns_transaction and connection.in_transaction:
                    connection.rollback()
                raise

    @contextmanager
    def currentness_guard(
        self,
        actor_context_id: str,
        *,
        checkpoint_id: str | None,
        state_version: int,
        epoch_id: str | None,
        epoch_revision: int | None,
    ) -> Iterator[ManagedActorSnapshot]:
        """Hold one exact semantic writer fence through a caller's first effect.

        The guard owns ``BEGIN IMMEDIATE``.  Semantic write helpers invoked by
        the caller must therefore join the ambient transaction rather than
        committing it.  Network waits are intentionally outside this scope.
        """

        with self.semantic._lock:
            connection = self.semantic.connection
            if connection.in_transaction:
                raise SemanticBridgeError("semantic currentness guard requires transaction ownership")
            connection.execute("BEGIN IMMEDIATE")
            try:
                snapshot = self._snapshot_unlocked(actor_context_id)
                expected = (checkpoint_id, state_version, epoch_id, epoch_revision)
                actual = (
                    snapshot.checkpoint_id,
                    snapshot.state_version,
                    snapshot.epoch_id,
                    snapshot.epoch_revision,
                )
                if actual != expected:
                    raise SemanticCurrentnessError(
                        "semantic currentness tuple no longer matches"
                    )
                yield snapshot
                if not connection.in_transaction:
                    raise SemanticBridgeError("semantic currentness guard was released prematurely")
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

    @contextmanager
    def writer_guard(self) -> Iterator[None]:
        """Own the semantic writer fence for a cross-ledger operation."""

        with self.semantic._lock:
            connection = self.semantic.connection
            if connection.in_transaction:
                raise SemanticBridgeError("semantic writer guard requires transaction ownership")
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield
                if not connection.in_transaction:
                    raise SemanticBridgeError("semantic writer guard was released prematurely")
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

    @contextmanager
    def actor_pair_guard(
        self,
        source_actor_context_id: str,
        target_actor_context_id: str,
    ) -> Iterator[tuple[ManagedActorSnapshot, ManagedActorSnapshot]]:
        """Return two eligible snapshots from one semantic writer snapshot."""

        with self.writer_guard():
            source = self._snapshot_unlocked(source_actor_context_id)
            target = self._snapshot_unlocked(target_actor_context_id)
            yield source, target

    def assert_currentness(
        self,
        actor_context_id: str,
        *,
        checkpoint_id: str | None,
        state_version: int,
        epoch_id: str | None,
        epoch_revision: int | None,
    ) -> ManagedActorSnapshot:
        snapshot = self.snapshot(actor_context_id)
        expected = (checkpoint_id, state_version, epoch_id, epoch_revision)
        actual = (
            snapshot.checkpoint_id,
            snapshot.state_version,
            snapshot.epoch_id,
            snapshot.epoch_revision,
        )
        if actual != expected:
            raise SemanticCurrentnessError("semantic currentness tuple no longer matches")
        return snapshot

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
                payload = json.loads(existing["result_json"])
                self.require_durable_reanchor_effect(
                    actor_context_id=actor_context_id,
                    checkpoint_id=checkpoint_id,
                    state_version=expected_state_version,
                    epoch_id=expected_epoch_id,
                    epoch_revision=expected_epoch_revision,
                    actor_turn_id=str(payload.get("actor_turn_id") or app_server_turn_id),
                    payload=payload,
                )
                return payload

        # A cheap exact-ack lookup distinguishes recovery from a new effect.
        # The new-effect path performs no eligibility/currentness/checkpoint/
        # epoch/obligation read before currentness_guard owns BEGIN IMMEDIATE.
        with self.semantic._lock:
            existing_ack = self.semantic.connection.execute(
                """SELECT 1 FROM reanchor_acks
                WHERE actor_context_id = ? AND checkpoint_id = ?
                  AND state_version = ? AND epoch_id IS ?
                  AND epoch_revision IS ? AND actor_turn_id = ?""",
                (
                    actor_context_id,
                    checkpoint_id,
                    expected_state_version,
                    expected_epoch_id,
                    expected_epoch_revision,
                    app_server_turn_id,
                ),
            ).fetchone()
        recovered = (
            self.recover_durable_reanchor_effect(
                actor_context_id=actor_context_id,
                checkpoint_id=checkpoint_id,
                state_version=expected_state_version,
                epoch_id=expected_epoch_id,
                epoch_revision=expected_epoch_revision,
                actor_turn_id=app_server_turn_id,
            )
            if existing_ack is not None
            else None
        )
        if recovered is not None:
            recovered["supervisor_command_id"] = supervisor_command_id
            if self.supervisor_store is not None:
                self.supervisor_store.record_command_receipt(
                    command_id=supervisor_command_id,
                    effect_kind="CONTEXT_REANCHOR_ACK",
                    semantic_ref=str(recovered.get("ack_id") or ""),
                    result=recovered,
                )
            return recovered

        with self.semantic._lock:
            connection = self.semantic.connection
            joined_ambient_transaction = connection.in_transaction
            if joined_ambient_transaction:
                self._require_eligible_unlocked(actor_context_id)
                result = context_reanchor_ack(
                    self.semantic,
                    actor_context_id=actor_context_id,
                    checkpoint_id=checkpoint_id,
                    state_version=expected_state_version,
                    epoch_id=expected_epoch_id,
                    epoch_revision=expected_epoch_revision,
                    actor_turn_id=app_server_turn_id,
                )
            else:
                # Direct bridge callers use the same writer/currentness guard
                # as the command gateway.  Eligibility, tuple, checkpoint and
                # obligation reads therefore occur only after BEGIN IMMEDIATE.
                with self.currentness_guard(
                    actor_context_id,
                    checkpoint_id=checkpoint_id,
                    state_version=expected_state_version,
                    epoch_id=expected_epoch_id,
                    epoch_revision=expected_epoch_revision,
                ):
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
        payload["actor_turn_id"] = app_server_turn_id
        # An ambient transaction (the gateway currentness guard) has not
        # committed when this method returns.  Its caller owns the post-commit
        # receipt.  Without an ambient transaction, context_reanchor_ack has
        # already committed successfully, so direct bridge calls may record it.
        if self.supervisor_store is not None and not joined_ambient_transaction:
            self.supervisor_store.record_command_receipt(
                command_id=supervisor_command_id,
                effect_kind="CONTEXT_REANCHOR_ACK",
                semantic_ref=str(payload.get("ack_id") or ""),
                result=payload,
            )
        return payload

    def recover_durable_reanchor_effect(
        self,
        *,
        actor_context_id: str,
        checkpoint_id: str,
        state_version: int,
        epoch_id: str | None,
        epoch_revision: int | None,
        actor_turn_id: str,
    ) -> dict[str, Any] | None:
        """Return one exact committed ack/resolution pair without reapplying it."""

        with self.semantic._lock:
            connection = self.semantic.connection
            owns_transaction = not connection.in_transaction
            if owns_transaction:
                connection.execute("BEGIN")
            try:
                ack = connection.execute(
                    """SELECT ack_id FROM reanchor_acks
                    WHERE actor_context_id = ? AND checkpoint_id = ?
                      AND state_version = ? AND epoch_id IS ?
                      AND epoch_revision IS ? AND actor_turn_id = ?""",
                    (
                        actor_context_id,
                        checkpoint_id,
                        state_version,
                        epoch_id,
                        epoch_revision,
                        actor_turn_id,
                    ),
                ).fetchone()
                obligations = connection.execute(
                    """SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN obligations.state = 'RESOLVED'
                                      AND obligations.resolved_at IS NOT NULL
                                 THEN 1 ELSE 0 END) AS resolved
                    FROM obligations
                    JOIN workflows ON workflows.workflow_id = obligations.workflow_id
                    WHERE workflows.actor_context_id = ?
                      AND obligations.kind = ? AND obligations.subject = ?""",
                    (
                        actor_context_id,
                        ObligationKind.CONTEXT_REANCHOR_REQUIRED.value,
                        checkpoint_id,
                    ),
                ).fetchone()
                durable = (
                    ack is not None
                    and obligations is not None
                    and int(obligations["total"] or 0) > 0
                    and int(obligations["resolved"] or 0)
                    == int(obligations["total"] or 0)
                )
                if owns_transaction:
                    connection.commit()
            except Exception:
                if owns_transaction and connection.in_transaction:
                    connection.rollback()
                raise
        if not durable:
            return None
        return {
            "ack_id": str(ack["ack_id"]),
            "actor_context_id": actor_context_id,
            "checkpoint_id": checkpoint_id,
            "state_version": state_version,
            "epoch_id": epoch_id,
            "epoch_revision": epoch_revision,
            "actor_turn_id": actor_turn_id,
        }

    def require_durable_reanchor_effect(
        self,
        *,
        actor_context_id: str,
        checkpoint_id: str,
        state_version: int,
        epoch_id: str | None,
        epoch_revision: int | None,
        actor_turn_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Reject a supervisor receipt unless its exact semantic effect committed."""

        expected_ack_id = str(payload.get("ack_id") or "")
        if not expected_ack_id:
            raise SemanticBridgeError("reanchor receipt has no durable semantic effect")
        recovered = self.recover_durable_reanchor_effect(
            actor_context_id=actor_context_id,
            checkpoint_id=checkpoint_id,
            state_version=state_version,
            epoch_id=epoch_id,
            epoch_revision=epoch_revision,
            actor_turn_id=actor_turn_id,
        )
        if recovered is None or str(recovered["ack_id"]) != expected_ack_id:
            raise SemanticBridgeError("reanchor receipt has no durable semantic effect")


def managed_kind_from_snapshot(snapshot: ManagedActorSnapshot) -> ManagedActorKind:
    return ManagedActorKind(snapshot.actor_kind)
