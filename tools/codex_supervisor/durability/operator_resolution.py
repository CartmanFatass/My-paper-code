"""One-shot evidence-bound incident resolution."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping

from .effects import EffectJournal
from .models import AggregateKind, TransitionCause, TransitionRequest
from .transaction import DurabilityTransaction
from .transitions import TransitionError, TransitionKernel


class ResolutionDisposition(str, Enum):
    NO_SUBMISSION_EVIDENCE = "NO_SUBMISSION_EVIDENCE"
    TURN_OBSERVED_ACTIVE = "TURN_OBSERVED_ACTIVE"
    TURN_OBSERVED_COMPLETED = "TURN_OBSERVED_COMPLETED"
    RECEIPT_CONFIRMED = "RECEIPT_CONFIRMED"
    ABANDON = "ABANDON"


class OperatorResolutionError(RuntimeError):
    """Raised when an incident cannot be resolved."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mechanical_status(status: object) -> str | None:
    if isinstance(status, dict):
        status = status.get("type") or status.get("status")
    if status is None:
        return None
    text = str(status)
    if text in {"completed", "interrupted", "failed"}:
        return text
    if text in {"inProgress", "active"}:
        return "active"
    return None


class OperatorResolutionService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.kernel = TransitionKernel(connection)
        self.journal = EffectJournal(connection)

    def resolve_wake(
        self,
        wake_batch_id: str,
        *,
        operator: str,
        disposition: ResolutionDisposition,
        evidence_kind: str,
        evidence_ref: str,
        payload: Mapping[str, object] | None = None,
        turn_id: str | None = None,
        completion_status: str | None = None,
    ) -> str:
        if not operator:
            raise OperatorResolutionError("operator identity is required")
        with DurabilityTransaction(self.connection):
            existing = self.connection.execute(
                """SELECT resolution_id FROM operator_resolutions
                WHERE aggregate_kind = ? AND aggregate_id = ?""",
                (AggregateKind.WAKE_BATCH.value, wake_batch_id),
            ).fetchone()
            if existing is not None:
                raise OperatorResolutionError("incident already has an operator resolution")
            batch = self.connection.execute(
                "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
                (wake_batch_id,),
            ).fetchone()
            if batch is None:
                raise OperatorResolutionError("unknown wake batch")
            if str(batch["state"]) != "INCIDENT":
                raise OperatorResolutionError("wake batch is not INCIDENT")
            effect_id = None if batch["effect_id"] is None else str(batch["effect_id"])
            effect = self.journal.get(effect_id) if effect_id else None
            observed = disposition in {
                ResolutionDisposition.TURN_OBSERVED_ACTIVE,
                ResolutionDisposition.TURN_OBSERVED_COMPLETED,
            }
            if observed:
                self._require_turn_evidence(
                    thread_id=str(batch["thread_id"]),
                    turn_id=turn_id,
                    client_key=str(batch["client_user_message_id"]),
                    completion_status=completion_status,
                    require_completed=disposition is ResolutionDisposition.TURN_OBSERVED_COMPLETED,
                )
                if effect is not None and effect.state == "PREPARED":
                    raise OperatorResolutionError(
                        "TURN_OBSERVED cannot apply to a PREPARED effect"
                    )
            target, message_target = self._wake_targets(
                disposition,
                effect=effect,
                turn_id=turn_id,
                completion_status=completion_status,
            )
            resolution_id = f"ores_{uuid.uuid4().hex}"
            payload_json = json.dumps(dict(payload or {}), sort_keys=True)
            self._insert_resolution(
                resolution_id=resolution_id,
                aggregate_kind=AggregateKind.WAKE_BATCH.value,
                aggregate_id=wake_batch_id,
                effect_id=effect_id,
                operator=operator,
                disposition=disposition,
                evidence_kind=evidence_kind,
                evidence_ref=evidence_ref,
                payload_json=payload_json,
            )
            self.kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.WAKE_BATCH,
                    aggregate_id=wake_batch_id,
                    expected_state="INCIDENT",
                    expected_version=int(batch["version"] or 0),
                    target_state=target,
                    cause_kind=TransitionCause.OPERATOR_RESOLUTION,
                    cause_ref=resolution_id,
                    evidence_ref=evidence_ref,
                    field_updates={"app_server_turn_id": turn_id} if turn_id else {},
                )
            )
            rows = self.connection.execute(
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
                try:
                    self.kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                            aggregate_id=str(row["message_id"]),
                            expected_state=state,
                            expected_version=int(row["delivery_version"] or 0),
                            target_state=message_target,
                            cause_kind=TransitionCause.OPERATOR_NO_SUBMISSION
                            if disposition is ResolutionDisposition.NO_SUBMISSION_EVIDENCE
                            else TransitionCause.OPERATOR_RESOLUTION,
                            cause_ref=resolution_id,
                            evidence_ref=evidence_ref,
                        )
                    )
                except TransitionError as exc:
                    raise OperatorResolutionError(str(exc)) from exc
            if effect is not None and effect.state == "PREPARED":
                if observed:
                    raise OperatorResolutionError(
                        "TURN_OBSERVED cannot apply to a PREPARED effect"
                    )
                self.journal.cancel_before_write(effect.effect_id, cause_ref=resolution_id)
            if effect is not None and effect.state in {
                "WRITE_STARTED",
                "RESPONSE_OBSERVED",
                "SUBMISSION_UNCERTAIN",
            }:
                if observed:
                    self.journal.confirm_effect(effect.effect_id, evidence_ref=evidence_ref)
                    effect = self.journal.get(effect.effect_id)
            if effect is not None and effect.state == "INCIDENT":
                effect_resolution_id = f"ores_{uuid.uuid4().hex}"
                self._insert_resolution(
                    resolution_id=effect_resolution_id,
                    aggregate_kind=AggregateKind.APP_SERVER_EFFECT.value,
                    aggregate_id=effect.effect_id,
                    effect_id=effect.effect_id,
                    operator=operator,
                    disposition=disposition,
                    evidence_kind=evidence_kind,
                    evidence_ref=evidence_ref,
                    payload_json=payload_json,
                )
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect.effect_id,
                        expected_state="INCIDENT",
                        expected_version=effect.version,
                        target_state="OPERATOR_RESOLVED",
                        cause_kind=TransitionCause.OPERATOR_RESOLUTION,
                        cause_ref=effect_resolution_id,
                        evidence_ref=evidence_ref,
                    )
                )
            return resolution_id

    def _insert_resolution(
        self,
        *,
        resolution_id: str,
        aggregate_kind: str,
        aggregate_id: str,
        effect_id: str | None,
        operator: str,
        disposition: ResolutionDisposition,
        evidence_kind: str,
        evidence_ref: str,
        payload_json: str,
    ) -> None:
        self.connection.execute(
            """INSERT INTO operator_resolutions(
                resolution_id, aggregate_kind, aggregate_id, effect_id, operator,
                disposition, evidence_kind, evidence_ref, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                resolution_id,
                aggregate_kind,
                aggregate_id,
                effect_id,
                operator,
                disposition.value,
                evidence_kind,
                evidence_ref,
                payload_json,
                _now(),
            ),
        )

    def _require_turn_evidence(
        self,
        *,
        thread_id: str,
        turn_id: str | None,
        client_key: str,
        completion_status: str | None,
        require_completed: bool,
    ) -> None:
        if not turn_id:
            raise OperatorResolutionError("turn observed requires exact turn id")
        snap = self.connection.execute(
            "SELECT thread_id, status FROM turn_snapshots WHERE turn_id = ?",
            (turn_id,),
        ).fetchone()
        if snap is None:
            raise OperatorResolutionError("turn evidence is not stored")
        if str(snap["thread_id"]) != thread_id:
            raise OperatorResolutionError("turn thread does not match wake binding thread")
        mechanical = _mechanical_status(snap["status"])
        if require_completed:
            if not completion_status:
                raise OperatorResolutionError("completed observation requires turn id and status")
            if mechanical != completion_status:
                raise OperatorResolutionError("mechanical status does not match operator status")
        elif mechanical != "active":
            raise OperatorResolutionError("turn is not mechanically active")
        raw = self.connection.execute(
            """SELECT 1 FROM raw_messages
            WHERE turn_id = ? AND canonical_json LIKE ?""",
            (turn_id, f"%{client_key}%"),
        ).fetchone()
        effect = self.connection.execute(
            """SELECT 1 FROM app_server_effects
            WHERE turn_id = ? AND client_key = ?""",
            (turn_id, client_key),
        ).fetchone()
        if raw is None and effect is None:
            raise OperatorResolutionError("turn evidence missing clientUserMessageId")

    def _wake_targets(
        self,
        disposition: ResolutionDisposition,
        *,
        effect,
        turn_id: str | None,
        completion_status: str | None,
    ) -> tuple[str, str]:
        if disposition is ResolutionDisposition.NO_SUBMISSION_EVIDENCE:
            if effect is not None and (
                effect.state != "PREPARED"
                or effect.raw_request_seq is not None
                or effect.client_request_id is not None
                or effect.write_started_at is not None
            ):
                raise OperatorResolutionError("write_started effect cannot use no-submission resolution")
            return "CANCELLED", "ELIGIBLE"
        if disposition is ResolutionDisposition.TURN_OBSERVED_ACTIVE:
            if not turn_id:
                raise OperatorResolutionError("turn observed requires exact turn id")
            return "ACTIVE", "DELIVERED_TO_TURN"
        if disposition is ResolutionDisposition.TURN_OBSERVED_COMPLETED:
            if not turn_id or not completion_status:
                raise OperatorResolutionError("completed observation requires turn id and status")
            return "COMPLETED", "DELIVERED_TO_TURN"
        if disposition is ResolutionDisposition.ABANDON:
            return "ABANDONED", "DEAD_LETTER"
        raise OperatorResolutionError(f"unsupported wake disposition {disposition.value}")
