"""Stage 3 managed-actor types. No semantic authority lives here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ManagedActorKind(str, Enum):
    OPERATIONAL_ROOT = "OPERATIONAL_ROOT"
    PORTFOLIO = "PORTFOLIO"


class BindingState(str, Enum):
    PREPARED = "PREPARED"
    THREAD_CREATED = "THREAD_CREATED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class ThreadOrigin(str, Enum):
    NEW = "NEW"
    ADOPTED_EXISTING = "ADOPTED_EXISTING"


class HistoryTrust(str, Enum):
    FRESH = "FRESH"
    LEGACY_UNTRUSTED_HISTORY = "LEGACY_UNTRUSTED_HISTORY"


class MemoryPolicyState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    DISABLED_BY_THREAD_API = "DISABLED_BY_THREAD_API"
    OPERATOR_CONFIRMED_GLOBAL_DISABLED = "OPERATOR_CONFIRMED_GLOBAL_DISABLED"


class ManagedIntentKind(str, Enum):
    BOOTSTRAP = "BOOTSTRAP"
    IDENTITY_VERIFICATION = "IDENTITY_VERIFICATION"
    MANUAL_OPERATOR = "MANUAL_OPERATOR"
    REANCHOR = "REANCHOR"


class SubmissionState(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    OBSERVED = "OBSERVED"
    COMPLETED = "COMPLETED"
    INCIDENT = "INCIDENT"


class CommandValidationState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"


class ManagedActionKind(str, Enum):
    NO_CONTROL_ACTION = "NO_CONTROL_ACTION"
    CONTEXT_REANCHOR_ACK = "CONTEXT_REANCHOR_ACK"
    MAILBOX_ACK = "MAILBOX_ACK"
    MAILBOX_INTAKE = "MAILBOX_INTAKE"
    MANAGED_PACKET_SEND = "MANAGED_PACKET_SEND"


FORBIDDEN_COMMAND_KEYS = frozenset(
    {
        "actor_context_id",
        "owner_actor_context_id",
        "requester_actor_context_id",
        "binding_id",
        "thread_id",
        "source_kind",
        "user_authority",
        "new_user_authority",
        "portfolio_authority",
        "scientific_authority",
        "technical_authority",
    }
)

STAGE3_ACTIONS = frozenset(
    {
        ManagedActionKind.NO_CONTROL_ACTION,
        ManagedActionKind.CONTEXT_REANCHOR_ACK,
    }
)

STAGE4_ACTIONS = frozenset(
    {
        ManagedActionKind.NO_CONTROL_ACTION,
        ManagedActionKind.CONTEXT_REANCHOR_ACK,
        ManagedActionKind.MAILBOX_ACK,
        ManagedActionKind.MAILBOX_INTAKE,
        ManagedActionKind.MANAGED_PACKET_SEND,
    }
)


@dataclass(frozen=True)
class ManagedActorBinding:
    binding_id: str
    actor_context_id: str
    actor_kind: ManagedActorKind
    semantic_scope_key: str
    direction_id: str | None
    thread_id: str | None
    thread_origin: ThreadOrigin
    history_trust: HistoryTrust
    binding_state: BindingState
    memory_policy_state: MemoryPolicyState
    repo_root: str
    thread_cwd: str
    created_by_operator: str
    created_at: str
    verification_turn_intent_id: str | None = None
    verification_turn_id: str | None = None
    verification_command_id: str | None = None
    verification_receipt_id: str | None = None
    verified_checkpoint_id: str | None = None
    verified_state_version: int | None = None
    verified_epoch_id: str | None = None
    verified_epoch_revision: int | None = None
