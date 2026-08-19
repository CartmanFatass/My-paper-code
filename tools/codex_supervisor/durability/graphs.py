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


def transition_trigger_sql(
    *,
    kind: AggregateKind,
    table: str,
    id_column: str,
    state_column: str,
    version_column: str,
) -> tuple[str, str]:
    """Generate one BEFORE UPDATE guard from ALLOWED_TRANSITIONS."""
    edges = ALLOWED_TRANSITIONS[kind]
    legal_terms: list[str] = []
    for from_state, targets in edges.items():
        automatic = sorted(target for target in targets if not is_operator_only_edge(kind, from_state, target))
        if automatic:
            allowed = ", ".join(f"'{target}'" for target in automatic)
            legal_terms.append(f"(OLD.{state_column} = '{from_state}' AND NEW.{state_column} IN ({allowed}))")
        operator_targets = sorted(target for target in targets if is_operator_only_edge(kind, from_state, target))
        if operator_targets:
            allowed = ", ".join(f"'{target}'" for target in operator_targets)
            legal_terms.append(
                "("
                f"OLD.{state_column} = '{from_state}' AND NEW.{state_column} IN ({allowed}) "
                "AND EXISTS ("
                "SELECT 1 FROM operator_resolutions "
                f"WHERE aggregate_kind = '{kind.value}' AND aggregate_id = OLD.{id_column}"
                ")"
                ")"
            )
    legal_sql = " OR ".join(legal_terms) if legal_terms else "0"
    trigger_name = f"durability_{table}_{state_column}_guard"
    drop_sql = f"DROP TRIGGER IF EXISTS {trigger_name}"
    create_sql = f"""CREATE TRIGGER {trigger_name}
    BEFORE UPDATE OF {state_column} ON {table}
    FOR EACH ROW
    WHEN NEW.{state_column} IS NOT OLD.{state_column}
    BEGIN
      SELECT CASE
        WHEN NOT ({legal_sql}) THEN
          RAISE(ABORT, 'illegal {kind.value} transition')
        WHEN NEW.{version_column} != OLD.{version_column} + 1 THEN
          RAISE(ABORT, '{kind.value} version must increment by 1')
        ELSE NULL
      END;
    END"""
    return drop_sql, create_sql
