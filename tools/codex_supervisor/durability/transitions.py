"""CAS aggregate transitions and transition journal."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from .graphs import (
    BATCHED_TO_ELIGIBLE_CAUSES,
    disposition_permits_target,
    is_legal_edge,
    is_operator_only_edge,
)
from .models import AggregateKind, TransitionCause, TransitionRequest, TransitionResult


class TransitionError(RuntimeError):
    """Raised when a requested aggregate transition cannot be applied."""


@dataclass(frozen=True)
class AggregateLocator:
    table: str
    id_column: str
    state_column: str
    version_column: str


AGGREGATE_LOCATORS: dict[AggregateKind, AggregateLocator] = {
    AggregateKind.MANAGED_BINDING: AggregateLocator(
        table="managed_actor_bindings",
        id_column="binding_id",
        state_column="binding_state",
        version_column="version",
    ),
    AggregateKind.MANAGED_TURN: AggregateLocator(
        table="managed_turn_intents",
        id_column="turn_intent_id",
        state_column="submission_state",
        version_column="version",
    ),
    AggregateKind.WAKE_BATCH: AggregateLocator(
        table="wake_batches",
        id_column="wake_batch_id",
        state_column="state",
        version_column="version",
    ),
    AggregateKind.MAILBOX_DELIVERY: AggregateLocator(
        table="mailbox_messages",
        id_column="message_id",
        state_column="delivery_state",
        version_column="delivery_version",
    ),
    AggregateKind.MAILBOX_INTAKE: AggregateLocator(
        table="mailbox_messages",
        id_column="message_id",
        state_column="intake_state",
        version_column="intake_version",
    ),
    AggregateKind.MANAGED_COMMAND: AggregateLocator(
        table="managed_actor_commands",
        id_column="command_id",
        state_column="validation_state",
        version_column="version",
    ),
    AggregateKind.APP_SERVER_EFFECT: AggregateLocator(
        table="app_server_effects",
        id_column="effect_id",
        state_column="state",
        version_column="version",
    ),
}

_FIELD_NAME = frozenset(
    {
        "thread_id",
        "turn_id",
        "app_server_thread_id",
        "app_server_turn_id",
        "app_server_request_id",
        "submitted_at",
        "observed_at",
        "completed_at",
        "completion_status",
        "incident_json",
        "effect_id",
        "eligible_at",
        "batched_at",
        "delivered_at",
        "acknowledged_at",
        "intaken_at",
        "applied_at",
        "dead_letter_reason",
        "source_resolved_after_submission",
        "validated_at",
        "rejection_reason",
        "write_started_at",
        "response_observed_at",
        "confirmed_at",
        "reconciled_at",
        "resolved_at",
        "run_id",
        "client_request_id",
        "request_row_id",
        "raw_request_seq",
        "response_json",
        "legacy_intent_id",
        "last_turn_id",
        "thread_created_at",
        "verified_at",
        "activated_at",
        "suspended_at",
        "revoked_at",
        "last_verified_at",
        "last_thread_status",
        "lease_holder",
        "lease_generation",
        "verification_turn_intent_id",
        "verification_turn_id",
        "verification_command_id",
        "verification_receipt_id",
        "verified_checkpoint_id",
        "verified_state_version",
        "verified_epoch_id",
        "verified_epoch_revision",
        "last_verified_at",
        "command_kind",
        "payload_json",
        "expected_checkpoint_id",
        "expected_state_version",
        "expected_epoch_id",
        "expected_epoch_revision",
        "rejection_reason",
        "transport_seq",
    }
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"tr_{uuid.uuid4().hex}"


class TransitionKernel:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def apply(self, request: TransitionRequest) -> TransitionResult:
        if not is_legal_edge(request.aggregate_kind, request.expected_state, request.target_state):
            raise TransitionError(
                f"illegal {request.aggregate_kind.value} transition "
                f"{request.expected_state} -> {request.target_state}"
            )
        if is_operator_only_edge(request.aggregate_kind, request.expected_state, request.target_state):
            if request.cause_kind != TransitionCause.OPERATOR_RESOLUTION:
                raise TransitionError(
                    f"operator-only {request.aggregate_kind.value} edge "
                    f"{request.expected_state} -> {request.target_state} requires OPERATOR_RESOLUTION"
                )
            self._require_operator_resolution(request)
        if (
            request.aggregate_kind == AggregateKind.MAILBOX_DELIVERY
            and request.expected_state == "BATCHED"
            and request.target_state == "ELIGIBLE"
            and request.cause_kind not in BATCHED_TO_ELIGIBLE_CAUSES
        ):
            raise TransitionError("BATCHED -> ELIGIBLE requires a prepared-batch cancel cause")
        locator = AGGREGATE_LOCATORS[request.aggregate_kind]
        assignments = [f"{locator.state_column} = ?", f"{locator.version_column} = {locator.version_column} + 1"]
        values: list[object] = [request.target_state]
        for name, value in request.field_updates.items():
            if name not in _FIELD_NAME:
                raise TransitionError(f"field update {name!r} is not allowed")
            assignments.append(f"{name} = ?")
            values.append(value)
        values.extend([request.aggregate_id, request.expected_state, request.expected_version])
        cursor = self.connection.execute(
            f"""UPDATE {locator.table}
            SET {', '.join(assignments)}
            WHERE {locator.id_column} = ?
              AND {locator.state_column} = ?
              AND {locator.version_column} = ?""",
            values,
        )
        if cursor.rowcount != 1:
            raise TransitionError(
                f"{request.aggregate_kind.value} {request.aggregate_id} "
                f"CAS failed for {request.expected_state}@{request.expected_version}"
            )
        to_version = request.expected_version + 1
        transition_id = _new_id()
        self.connection.execute(
            """INSERT INTO control_transitions(
                transition_id, aggregate_kind, aggregate_id, state_column,
                from_state, to_state, from_version, to_version,
                cause_kind, cause_ref, evidence_ref, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                transition_id,
                request.aggregate_kind.value,
                request.aggregate_id,
                locator.state_column,
                request.expected_state,
                request.target_state,
                request.expected_version,
                to_version,
                request.cause_kind.value,
                request.cause_ref,
                request.evidence_ref,
                json.dumps(dict(request.metadata), sort_keys=True),
                _now(),
            ),
        )
        row = self.connection.execute(
            f"SELECT * FROM {locator.table} WHERE {locator.id_column} = ?",
            (request.aggregate_id,),
        ).fetchone()
        if row is None:
            raise TransitionError(f"{request.aggregate_kind.value} {request.aggregate_id} disappeared")
        mapping: Mapping[str, object] = dict(row)
        return TransitionResult(
            transition_id=transition_id,
            aggregate_kind=request.aggregate_kind,
            aggregate_id=request.aggregate_id,
            from_state=request.expected_state,
            to_state=request.target_state,
            from_version=request.expected_version,
            to_version=to_version,
            row=mapping,
        )

    def _require_operator_resolution(self, request: TransitionRequest) -> None:
        row = self.connection.execute(
            """SELECT resolution_id, disposition FROM operator_resolutions
            WHERE aggregate_kind = ? AND aggregate_id = ?""",
            (request.aggregate_kind.value, request.aggregate_id),
        ).fetchone()
        if row is None:
            raise TransitionError(
                f"operator-only {request.aggregate_kind.value} exit requires an unconsumed operator_resolutions row"
            )
        if str(row["resolution_id"]) != request.cause_ref:
            raise TransitionError("operator resolution cause_ref must equal resolution_id")
        if not disposition_permits_target(
            str(row["disposition"]),
            request.aggregate_kind,
            request.target_state,
        ):
            raise TransitionError(
                f"resolution disposition {row['disposition']} does not permit {request.target_state}"
            )
