"""Literal twin-census construction and information-view projections.

Registered rows are read in their frozen order from :mod:`contract`; this
module never searches, filters, scores, or substitutes histories.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping, Sequence

from .contract import (
    REGISTERED_BINDING,
    TEST_ONLY_BINDING,
    ContractError,
    parse_fraction_pair,
    validate_public_history,
    validate_registered_spec,
)


class TwinCensusError(ValueError):
    """A twin definition violates pairing or information-view semantics."""


@dataclass(frozen=True)
class CensusRow:
    twin_id: str
    side: str
    population_weight: Fraction
    expected_raw_action: str | None
    history: Mapping[str, object]


@dataclass(frozen=True)
class TwinDefinition:
    twin_id: str
    coarsened_controller: str
    rows: tuple[CensusRow, CensusRow]


def _events(history: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    value = history["events"]
    if not isinstance(value, list) or any(not isinstance(event, dict) for event in value):
        raise TwinCensusError("validated history events must be plain mappings")
    return tuple(value)  # type: ignore[return-value]


def _decision(history: Mapping[str, object]) -> Mapping[str, object]:
    value = history["decision"]
    if not isinstance(value, dict):
        raise TwinCensusError("validated decision must be a plain mapping")
    return value


def full_bayes_k_view(history: Mapping[str, object]) -> tuple[object, ...]:
    """Full ordered public history; IDs and stored beliefs are excluded."""

    events = _events(history)
    decision = _decision(history)
    return (
        "FULL_BAYES_K",
        tuple(
            (
                event["renewal_index"],
                event["primitive_start"],
                event["primitive_end"],
                event["completed_duration"],
                event["action"],
                event["ack"],
                event["action_event_index"],
                event["hold_completion_event_index"],
                event["motion_event_index"],
                event["ack_event_index"],
                event["private_update_event_index"],
            )
            for event in events
        ),
        decision["renewal_index"],
        decision["primitive_time"],
        decision["next_duration"],
        decision["next_action_event_index"],
        (
            _credit(decision)["primitive_start"],
            _credit(decision)["primitive_end"],
        ),
    )


def full_bayes_k_erased_view(history: Mapping[str, object]) -> tuple[object, ...]:
    """Duration-erased view with no reconstructing earlier clock surface.

    Ordered actions/ACKs, the final completed duration, renewal count, and the
    legally action-visible next duration remain.  Earlier duration allocation,
    primitive timestamps, event indices, schedule labels, and credit endpoints
    are absent.
    """

    events = _events(history)
    decision = _decision(history)
    final = events[-1]
    return (
        "FULL_BAYES_K_ERASED",
        tuple((event["action"], event["ack"]) for event in events),
        final["completed_duration"],
        decision["renewal_index"],
        decision["next_duration"],
    )


def _credit(decision: Mapping[str, object]) -> Mapping[str, object]:
    value = decision["next_hold_credit"]
    if not isinstance(value, dict):
        raise TwinCensusError("next_hold_credit must be a mapping")
    return value


def last_ack_bayes_view(history: Mapping[str, object]) -> tuple[object, ...]:
    """Current decision plus only the final public outcome packet."""

    final = _events(history)[-1]
    decision = _decision(history)
    return (
        "LAST_ACK_BAYES",
        final["action"],
        final["ack"],
        final["completed_duration"],
        decision["renewal_index"],
        decision["primitive_time"],
        decision["next_duration"],
    )


def last_ack_g_view(history: Mapping[str, object]) -> tuple[object, ...]:
    """Historical fixed G map: only last action and ACK enter."""

    final = _events(history)[-1]
    return ("LAST_ACK_G", final["action"], final["ack"])


VIEW_FUNCTIONS = {
    "FULL_BAYES_K": full_bayes_k_view,
    "FULL_BAYES_K_ERASED": full_bayes_k_erased_view,
    "LAST_ACK_BAYES": last_ack_bayes_view,
    "LAST_ACK_G": last_ack_g_view,
}


def registered_twins(spec: object) -> tuple[TwinDefinition, TwinDefinition]:
    """Materialize exactly four registered rows without evaluating them."""

    validated = validate_registered_spec(spec)
    support = validated["support"]
    assert isinstance(support, dict)
    raw_twins = support["twins"]
    assert isinstance(raw_twins, list)
    twins: list[TwinDefinition] = []
    for raw_twin in raw_twins:
        assert isinstance(raw_twin, dict)
        raw_rows = raw_twin["rows"]
        assert isinstance(raw_rows, list)
        rows: list[CensusRow] = []
        for raw_row in raw_rows:
            assert isinstance(raw_row, dict)
            history = raw_row["history"]
            assert isinstance(history, dict)
            rows.append(
                CensusRow(
                    twin_id=str(raw_twin["twin_id"]),
                    side=str(raw_row["side"]),
                    population_weight=parse_fraction_pair(
                        raw_row["population_weight"], "population_weight"
                    ),
                    expected_raw_action=str(raw_row["expected_raw_action"]),
                    history=history,
                )
            )
        twins.append(
            TwinDefinition(
                twin_id=str(raw_twin["twin_id"]),
                coarsened_controller=str(raw_twin["coarsened_controller"]),
                rows=(rows[0], rows[1]),
            )
        )
    return (twins[0], twins[1])


def make_test_twin(
    twin_id: str,
    coarsened_controller: str,
    histories: Sequence[Mapping[str, object]],
    *,
    expected_raw_actions: Sequence[str | None] = (None, None),
) -> TwinDefinition:
    """Construct a separate two-side TEST_ONLY fixture population."""

    if not twin_id.startswith("TEST_ONLY_"):
        raise TwinCensusError("TEST_ONLY twin id must begin with TEST_ONLY_")
    if coarsened_controller not in ("FULL_BAYES_K_ERASED", "LAST_ACK_BAYES"):
        raise TwinCensusError("unsupported TEST_ONLY coarsened controller")
    if len(histories) != 2 or len(expected_raw_actions) != 2:
        raise TwinCensusError("a TEST_ONLY twin requires exactly two sides")
    rows: list[CensusRow] = []
    for index, history in enumerate(histories):
        try:
            validated = validate_public_history(history, expected_binding=TEST_ONLY_BINDING)
        except ContractError as error:
            raise TwinCensusError(str(error)) from error
        rows.append(
            CensusRow(
                twin_id=twin_id,
                side=("A", "B")[index],
                population_weight=Fraction(1, 2),
                expected_raw_action=expected_raw_actions[index],
                history=validated,
            )
        )
    return TwinDefinition(twin_id, coarsened_controller, (rows[0], rows[1]))


def validate_pairing(twins: Iterable[TwinDefinition], *, binding_class: str) -> None:
    seen_ids: set[str] = set()
    seen_histories: set[str] = set()
    for twin in twins:
        if twin.twin_id in seen_ids:
            raise TwinCensusError("twin IDs must be unique")
        seen_ids.add(twin.twin_id)
        if len(twin.rows) != 2 or tuple(row.side for row in twin.rows) != ("A", "B"):
            raise TwinCensusError("each twin must contain ordered sides A and B")
        if sum((row.population_weight for row in twin.rows), Fraction()) != 1:
            raise TwinCensusError("twin population weights must normalize exactly")
        if any(row.population_weight != Fraction(1, 2) for row in twin.rows):
            raise TwinCensusError("twin sides must have equal exact weight")
        view = VIEW_FUNCTIONS[twin.coarsened_controller]
        if view(twin.rows[0].history) != view(twin.rows[1].history):
            raise TwinCensusError("declared coarsened twin keys do not match")
        if full_bayes_k_view(twin.rows[0].history) == full_bayes_k_view(twin.rows[1].history):
            raise TwinCensusError("twin full histories must differ")
        for row in twin.rows:
            validated = validate_public_history(row.history, expected_binding=binding_class)
            history_id = str(validated["history_id"])
            if history_id in seen_histories:
                raise TwinCensusError("history IDs must be unique")
            seen_histories.add(history_id)


__all__ = [
    "CensusRow",
    "TwinCensusError",
    "TwinDefinition",
    "VIEW_FUNCTIONS",
    "full_bayes_k_erased_view",
    "full_bayes_k_view",
    "last_ack_bayes_view",
    "last_ack_g_view",
    "make_test_twin",
    "registered_twins",
    "validate_pairing",
]
