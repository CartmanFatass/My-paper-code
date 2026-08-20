"""Immutable durability-kernel types. Business modules must not invent states."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class AggregateKind(str, Enum):
    MANAGED_BINDING = "MANAGED_BINDING"
    MANAGED_TURN = "MANAGED_TURN"
    WAKE_BATCH = "WAKE_BATCH"
    MAILBOX_DELIVERY = "MAILBOX_DELIVERY"
    MAILBOX_INTAKE = "MAILBOX_INTAKE"
    MANAGED_COMMAND = "MANAGED_COMMAND"
    APP_SERVER_EFFECT = "APP_SERVER_EFFECT"


class TransitionCause(str, Enum):
    OPERATOR_ACTION = "OPERATOR_ACTION"
    APP_SERVER_EFFECT = "APP_SERVER_EFFECT"
    APP_SERVER_RESPONSE = "APP_SERVER_RESPONSE"
    APP_SERVER_EVENT = "APP_SERVER_EVENT"
    SERVER_REQUEST_INCIDENT = "SERVER_REQUEST_INCIDENT"
    RECONCILIATION = "RECONCILIATION"
    SOURCE_RESOLUTION = "SOURCE_RESOLUTION"
    OPERATOR_RESOLUTION = "OPERATOR_RESOLUTION"
    CONTROL_COMMAND = "CONTROL_COMMAND"
    MIGRATION = "MIGRATION"
    PRE_WRITE_CANCEL = "PRE_WRITE_CANCEL"
    OPERATOR_NO_SUBMISSION = "OPERATOR_NO_SUBMISSION"
    SOURCE_INVALID_PREPARED_BATCH = "SOURCE_INVALID_PREPARED_BATCH"


class EffectState(str, Enum):
    PREPARED = "PREPARED"
    WRITE_STARTED = "WRITE_STARTED"
    RESPONSE_OBSERVED = "RESPONSE_OBSERVED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    EFFECT_CONFIRMED = "EFFECT_CONFIRMED"
    CANCELLED_BEFORE_WRITE = "CANCELLED_BEFORE_WRITE"
    INCIDENT = "INCIDENT"
    OPERATOR_RESOLVED = "OPERATOR_RESOLVED"


class EffectOwnerKind(str, Enum):
    THREAD_PROVISION = "THREAD_PROVISION"
    THREAD_RESUME = "THREAD_RESUME"
    THREAD_MEMORY = "THREAD_MEMORY"
    MANAGED_TURN = "MANAGED_TURN"
    WAKE_BATCH = "WAKE_BATCH"
    EPHEMERAL_CANARY = "EPHEMERAL_CANARY"


SUBMISSION_RESULT_STATES = frozenset(
    {
        EffectState.RESPONSE_OBSERVED.value,
        EffectState.SUBMISSION_UNCERTAIN.value,
        EffectState.INCIDENT.value,
    }
)


@dataclass(frozen=True)
class TransitionRequest:
    aggregate_kind: AggregateKind
    aggregate_id: str
    expected_state: str
    expected_version: int
    target_state: str
    cause_kind: TransitionCause
    cause_ref: str
    evidence_ref: str | None = None
    field_updates: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TransitionResult:
    transition_id: str
    aggregate_kind: AggregateKind
    aggregate_id: str
    from_state: str
    to_state: str
    from_version: int
    to_version: int
    row: Mapping[str, object]
