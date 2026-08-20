from tools.codex_supervisor.durability.graphs import ALLOWED_TRANSITIONS, OPERATOR_ONLY_EDGES
from tools.codex_supervisor.durability.models import AggregateKind


def test_incident_has_no_automatic_exit() -> None:
    for aggregate, edges in ALLOWED_TRANSITIONS.items():
        for target in edges.get("INCIDENT", frozenset()):
            assert (aggregate, "INCIDENT", target) in OPERATOR_ONLY_EDGES


def test_managed_turn_starts_prepared() -> None:
    assert "PREPARED" in ALLOWED_TRANSITIONS[AggregateKind.MANAGED_TURN]


def test_effect_write_started_cannot_return_to_prepared() -> None:
    assert "PREPARED" not in ALLOWED_TRANSITIONS[AggregateKind.APP_SERVER_EFFECT]["WRITE_STARTED"]


def test_operator_only_edges_are_encoded() -> None:
    required = {
        (AggregateKind.WAKE_BATCH, "INCIDENT", "CANCELLED"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "ACTIVE"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "COMPLETED"),
        (AggregateKind.WAKE_BATCH, "INCIDENT", "ABANDONED"),
        (AggregateKind.APP_SERVER_EFFECT, "INCIDENT", "OPERATOR_RESOLVED"),
    }
    assert required <= OPERATOR_ONLY_EDGES


def test_suspended_binding_cannot_return_directly_to_active() -> None:
    assert "ACTIVE" not in ALLOWED_TRANSITIONS[AggregateKind.MANAGED_BINDING]["SUSPENDED"]
    assert "VERIFICATION_REQUIRED" in ALLOWED_TRANSITIONS[AggregateKind.MANAGED_BINDING]["SUSPENDED"]


def test_revoked_and_completed_are_terminal() -> None:
    assert ALLOWED_TRANSITIONS[AggregateKind.MANAGED_BINDING].get("REVOKED", frozenset()) == frozenset()
    assert ALLOWED_TRANSITIONS[AggregateKind.MANAGED_TURN].get("COMPLETED", frozenset()) == frozenset()
    assert ALLOWED_TRANSITIONS[AggregateKind.WAKE_BATCH].get("COMPLETED", frozenset()) == frozenset()
    assert ALLOWED_TRANSITIONS[AggregateKind.WAKE_BATCH].get("CANCELLED", frozenset()) == frozenset()
    assert ALLOWED_TRANSITIONS[AggregateKind.WAKE_BATCH].get("ABANDONED", frozenset()) == frozenset()
    assert ALLOWED_TRANSITIONS[AggregateKind.APP_SERVER_EFFECT].get("EFFECT_CONFIRMED", frozenset()) == frozenset()
