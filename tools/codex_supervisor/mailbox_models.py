"""Stage 4 mailbox and wake types. No semantic authority lives here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MailboxMessageKind(str, Enum):
    ROOT_TO_PORTFOLIO_REVIEW = "ROOT_TO_PORTFOLIO_REVIEW"
    PORTFOLIO_TO_ROOT_DECISION = "PORTFOLIO_TO_ROOT_DECISION"
    ROOT_TO_PORTFOLIO_APPLIED_ACK = "ROOT_TO_PORTFOLIO_APPLIED_ACK"
    OBLIGATION_AVAILABLE = "OBLIGATION_AVAILABLE"
    PACKET_AVAILABLE = "PACKET_AVAILABLE"
    REPORT_AVAILABLE = "REPORT_AVAILABLE"
    REANCHOR_REQUIRED = "REANCHOR_REQUIRED"
    OPERATOR_ATTENTION_REQUEST = "OPERATOR_ATTENTION_REQUEST"


class MailboxSourceSystem(str, Enum):
    SEMANTIC_LEDGER = "SEMANTIC_LEDGER"
    MANAGED_ACTOR = "MANAGED_ACTOR"
    OPERATOR = "OPERATOR"


class DeliveryState(str, Enum):
    ENQUEUED = "ENQUEUED"
    ELIGIBLE = "ELIGIBLE"
    BATCHED = "BATCHED"
    DELIVERED_TO_TURN = "DELIVERED_TO_TURN"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    CANCELLED_SOURCE_RESOLVED = "CANCELLED_SOURCE_RESOLVED"
    DEAD_LETTER = "DEAD_LETTER"


class IntakeState(str, Enum):
    NOT_ACKNOWLEDGED = "NOT_ACKNOWLEDGED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INTAKEN = "INTAKEN"
    APPLIED = "APPLIED"


class WakeBatchState(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    INCIDENT = "INCIDENT"
    CANCELLED = "CANCELLED"


class ThreadWakeReadiness(str, Enum):
    ACTIVE_TURN = "ACTIVE_TURN"
    IDLE_LOADED = "IDLE_LOADED"
    IDLE_NOT_LOADED = "IDLE_NOT_LOADED"
    UNKNOWN = "UNKNOWN"
    REVOKED = "REVOKED"


class WakeAttemptOutcome(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    RECONCILED = "RECONCILED"
    RESUMED = "RESUMED"
    QUEUED_ACTIVE_TURN = "QUEUED_ACTIVE_TURN"
    SKIPPED_UNKNOWN = "SKIPPED_UNKNOWN"
    CANCELLED = "CANCELLED"
    INCIDENT = "INCIDENT"


FORBIDDEN_MAILBOX_KINDS = frozenset(
    {"BLOCKED", "FAILED", "SUCCESS", "RETIRED", "PAUSED", "PARKED", "RELEASED"}
)

STAGE4_ACTIONS = frozenset(
    {
        "NO_CONTROL_ACTION",
        "CONTEXT_REANCHOR_ACK",
        "MAILBOX_ACK",
        "MAILBOX_INTAKE",
        "MANAGED_PACKET_SEND",
    }
)

WAKE_ENVELOPE_HEADER = "[HMASD_RUNTIME_WAKE_V1]"
MAX_WAKE_MESSAGES = 16
MAX_WAKE_INPUT_BYTES = 24 * 1024
DEFAULT_LEASE_SECONDS = 30.0
SCANNER_ID = "semantic_liveness_v1"


@dataclass(frozen=True)
class MailboxMessage:
    message_id: str
    source_system: str
    source_event_key: str
    sender_actor_context_id: str | None
    target_actor_context_id: str
    message_kind: MailboxMessageKind
    subject_ref: str
    payload_ref: str
    direction_id: str | None
    epoch_id: str | None
    priority: int
    delivery_state: DeliveryState
    intake_state: IntakeState
    created_at: str
    dead_letter_reason: str | None = None
    source_resolved_after_submission: bool = False
