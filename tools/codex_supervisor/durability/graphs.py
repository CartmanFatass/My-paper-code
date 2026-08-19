"""Authoritative aggregate state graphs. Business modules must not infer edges."""

from __future__ import annotations

from .models import AggregateKind, TransitionCause

ALLOWED_TRANSITIONS: dict[AggregateKind, dict[str, frozenset[str]]] = {
    AggregateKind.MANAGED_BINDING: {
        "PREPARED": frozenset({"THREAD_CREATED", "REVOKED"}),
        "THREAD_CREATED": frozenset({"VERIFICATION_REQUIRED", "REVOKED"}),
        "VERIFICATION_REQUIRED": frozenset({"ACTIVE", "SUSPENDED", "REVOKED"}),
        "ACTIVE": frozenset({"SUSPENDED", "REVOKED"}),
        "SUSPENDED": frozenset({"VERIFICATION_REQUIRED", "REVOKED"}),
        "REVOKED": frozenset(),
    },
    AggregateKind.MANAGED_TURN: {
        "PREPARED": frozenset({"SUBMITTING", "CANCELLED", "INCIDENT"}),
        "SUBMITTING": frozenset({"SUBMITTED", "SUBMISSION_UNCERTAIN", "INCIDENT"}),
        "SUBMITTED": frozenset({"OBSERVED", "SUBMISSION_UNCERTAIN", "INCIDENT"}),
        "SUBMISSION_UNCERTAIN": frozenset({"OBSERVED", "INCIDENT"}),
        "OBSERVED": frozenset({"COMPLETED", "INCIDENT"}),
        "COMPLETED": frozenset(),
        "CANCELLED": frozenset(),
        "INCIDENT": frozenset(),
    },
    AggregateKind.WAKE_BATCH: {
        "PREPARED": frozenset({"SUBMITTING", "CANCELLED", "INCIDENT"}),
        "SUBMITTING": frozenset({"SUBMITTED", "SUBMISSION_UNCERTAIN", "INCIDENT"}),
        "SUBMITTED": frozenset({"ACTIVE", "SUBMISSION_UNCERTAIN", "INCIDENT"}),
        "SUBMISSION_UNCERTAIN": frozenset({"ACTIVE", "INCIDENT"}),
        "ACTIVE": frozenset({"COMPLETED", "INCIDENT"}),
        "INCIDENT": frozenset({"CANCELLED", "ACTIVE", "COMPLETED", "ABANDONED"}),
        "COMPLETED": frozenset(),
        "CANCELLED": frozenset(),
        "ABANDONED": frozenset(),
    },
    AggregateKind.MAILBOX_DELIVERY: {
        "ENQUEUED": frozenset({"ELIGIBLE", "CANCELLED_SOURCE_RESOLVED", "DEAD_LETTER"}),
        "ELIGIBLE": frozenset({"BATCHED", "ENQUEUED", "CANCELLED_SOURCE_RESOLVED", "DEAD_LETTER"}),
        "BATCHED": frozenset(
            {
                "DELIVERED_TO_TURN",
                "SUBMISSION_UNCERTAIN",
                "ELIGIBLE",
                "CANCELLED_SOURCE_RESOLVED",
                "DEAD_LETTER",
            }
        ),
        "SUBMISSION_UNCERTAIN": frozenset({"DELIVERED_TO_TURN", "DEAD_LETTER"}),
        "DELIVERED_TO_TURN": frozenset({"DEAD_LETTER"}),
        "CANCELLED_SOURCE_RESOLVED": frozenset(),
        "DEAD_LETTER": frozenset(),
    },
    AggregateKind.MAILBOX_INTAKE: {
        "NOT_ACKNOWLEDGED": frozenset({"ACKNOWLEDGED"}),
        "ACKNOWLEDGED": frozenset({"INTAKEN"}),
        "INTAKEN": frozenset({"APPLIED"}),
        "APPLIED": frozenset(),
    },
    AggregateKind.MANAGED_COMMAND: {
        "RECEIVED": frozenset({"VALIDATED", "REJECTED", "INCIDENT"}),
        "VALIDATED": frozenset({"APPLIED", "REJECTED", "INCIDENT"}),
        "APPLIED": frozenset(),
        "REJECTED": frozenset(),
        "INCIDENT": frozenset(),
    },
    AggregateKind.APP_SERVER_EFFECT: {
        "PREPARED": frozenset({"WRITE_STARTED", "CANCELLED_BEFORE_WRITE", "INCIDENT"}),
        "WRITE_STARTED": frozenset({"RESPONSE_OBSERVED", "SUBMISSION_UNCERTAIN", "INCIDENT"}),
        "RESPONSE_OBSERVED": frozenset({"EFFECT_CONFIRMED", "INCIDENT"}),
        "SUBMISSION_UNCERTAIN": frozenset({"EFFECT_CONFIRMED", "INCIDENT"}),
        "EFFECT_CONFIRMED": frozenset(),
        "CANCELLED_BEFORE_WRITE": frozenset(),
        "INCIDENT": frozenset({"OPERATOR_RESOLVED"}),
        "OPERATOR_RESOLVED": frozenset(),
    },
}

OPERATOR_ONLY_EDGES: frozenset[tuple[AggregateKind, str, str]] = frozenset(
    {
        (AggregateKind.WAKE_BATCH, "INCIDENT", "CANCELLED"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "ACTIVE"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "COMPLETED"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "ABANDONED"),
        (AggregateKind.APP_SERVER_EFFECT, "INCIDENT", "OPERATOR_RESOLVED"),
    }
)

BATCHED_TO_ELIGIBLE_CAUSES: frozenset[TransitionCause] = frozenset(
    {
        TransitionCause.PRE_WRITE_CANCEL,
        TransitionCause.OPERATOR_NO_SUBMISSION,
        TransitionCause.SOURCE_INVALID_PREPARED_BATCH,
    }
)


def allowed_targets(kind: AggregateKind, from_state: str) -> frozenset[str]:
    return ALLOWED_TRANSITIONS[kind].get(from_state, frozenset())


def is_legal_edge(kind: AggregateKind, from_state: str, to_state: str) -> bool:
    return to_state in allowed_targets(kind, from_state)


def is_operator_only_edge(kind: AggregateKind, from_state: str, to_state: str) -> bool:
    return (kind, from_state, to_state) in OPERATOR_ONLY_EDGES
