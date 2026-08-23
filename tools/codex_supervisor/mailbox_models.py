"""Stage 4 mailbox and wake types. No semantic authority lives here."""

from __future__ import annotations

import re
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


class WakeIncidentDisposition(str, Enum):
    NO_SUBMISSION_EVIDENCE = "NO_SUBMISSION_EVIDENCE"
    TURN_OBSERVED = "TURN_OBSERVED"
    ABANDON = "ABANDON"


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
MAX_MAILBOX_REF_BYTES = 4096

_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_SAFE_REF_SEGMENT = re.compile(r"^[A-Za-z0-9@+_.-]+$")


class MailboxRefError(ValueError):
    """Raised when a mailbox field is not a closed, typed reference."""


@dataclass(frozen=True)
class MailboxRef:
    """A one-line identifier or repository-relative artifact reference."""

    value: str

    @classmethod
    def parse(cls, value: str, *, field_name: str = "mailbox_ref") -> MailboxRef:
        if not isinstance(value, str):
            raise MailboxRefError(f"{field_name} must be a string reference")
        if not value or value != value.strip():
            raise MailboxRefError(f"{field_name} must be non-empty without outer whitespace")
        try:
            encoded = value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise MailboxRefError(f"{field_name} must be valid UTF-8") from exc
        if len(encoded) > MAX_MAILBOX_REF_BYTES:
            raise MailboxRefError(
                f"{field_name} exceeds {MAX_MAILBOX_REF_BYTES} UTF-8 bytes"
            )
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise MailboxRefError(f"{field_name} contains an ASCII control character")
        if any(character.isspace() for character in value):
            raise MailboxRefError(f"{field_name} must not contain whitespace or prose")
        if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
            raise MailboxRefError(f"{field_name} must not be an absolute or drive-relative path")
        if _URI_SCHEME.match(value):
            raise MailboxRefError(f"{field_name} must not be a URI or scheme reference")
        segments = re.split(r"[/\\]", value)
        if any(segment in {"", ".", ".."} for segment in segments):
            raise MailboxRefError(f"{field_name} contains an unsafe path segment")
        if any(_SAFE_REF_SEGMENT.fullmatch(segment) is None for segment in segments):
            raise MailboxRefError(
                f"{field_name} must use only safe identifier or repository-path characters"
            )
        return cls(value=value)


def validate_mailbox_ref(value: str, *, field_name: str = "mailbox_ref") -> str:
    """Validate and return a typed reference without resolving or dereferencing it."""

    return MailboxRef.parse(value, field_name=field_name).value


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
