"""Exact probability primitives for the RISP event-conditioned Bayes host.

This module is intentionally isolated from the historical RISP/APFI hosts.  All
scientific quantities are :class:`fractions.Fraction` values; floats are never
accepted as probability inputs.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Iterable, Mapping, Sequence


ACTIONS = ("LEFT", "CENTER", "RIGHT")
SECTORS = ACTIONS
SUPPORTED_DURATIONS = (4, 8, 12)
UNIFORM_BELIEF = (Fraction(1, 3),) * 3
ACK_MATCH = Fraction(4, 5)
ACK_MISMATCH = Fraction(1, 5)

Belief = tuple[Fraction, Fraction, Fraction]
Matrix3 = tuple[Belief, Belief, Belief]


class ExactProbabilityError(ValueError):
    """Raised when an input violates the frozen exact-probability contract."""


def _duration(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExactProbabilityError("duration must be an integer")
    if value not in SUPPORTED_DURATIONS:
        raise ExactProbabilityError(
            f"duration must be one of {SUPPORTED_DURATIONS}, got {value!r}"
        )
    return value


def _action(value: object) -> str:
    if not isinstance(value, str) or value not in ACTIONS:
        raise ExactProbabilityError(f"action must be one of {ACTIONS}")
    return value


def ack_is_positive(value: object) -> bool:
    """Parse the public ACK without conflating booleans and integers.

    The wire spelling is ``"+"``/``"-"``.  ``True``/``False`` is accepted for
    small synthetic callers, while integer 1/0 is rejected to keep schemas
    unambiguous.
    """

    if type(value) is bool:
        return value
    if value == "+":
        return True
    if value == "-":
        return False
    raise ExactProbabilityError("ack must be '+'/'-' or a bool")


def _belief(values: Sequence[Fraction]) -> Belief:
    if len(values) != 3:
        raise ExactProbabilityError("belief must have exactly three sectors")
    if any(not isinstance(value, Fraction) for value in values):
        raise ExactProbabilityError("belief entries must be Fraction values")
    result = tuple(values)
    if any(value < 0 for value in result):
        raise ExactProbabilityError("belief entries must be nonnegative")
    if sum(result, Fraction(0)) != 1:
        raise ExactProbabilityError("belief must normalize exactly to one")
    return result  # type: ignore[return-value]


def transition_matrix(duration: int) -> Matrix3:
    """Return ``P_k = J/3 + (15/16)^k (I-J/3)`` exactly."""

    k = _duration(duration)
    persistence = Fraction(15, 16) ** k
    off_diagonal = (1 - persistence) / 3
    diagonal = off_diagonal + persistence
    return tuple(
        tuple(diagonal if row == column else off_diagonal for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def predict(belief: Sequence[Fraction], duration: int) -> Belief:
    """Predict the completion-sector distribution for one completed hold."""

    prior = _belief(belief)
    matrix = transition_matrix(duration)
    return tuple(
        sum((prior[row] * matrix[row][column] for row in range(3)), Fraction(0))
        for column in range(3)
    )  # type: ignore[return-value]


def ack_likelihood(action: str, ack: object, completion_sector: str) -> Fraction:
    """Return the exact likelihood of an ACK given the completion sector."""

    chosen = _action(action)
    sector = _action(completion_sector)
    positive = ack_is_positive(ack)
    success = ACK_MATCH if chosen == sector else ACK_MISMATCH
    return success if positive else 1 - success


def condition_on_ack(
    completion_prior: Sequence[Fraction], action: str, ack: object
) -> tuple[Belief, Fraction]:
    """Condition a completion-sector prior and return posterior and ACK mass."""

    prior = _belief(completion_prior)
    chosen = _action(action)
    positive = ack_is_positive(ack)
    weights = tuple(
        prior[index] * ack_likelihood(chosen, positive, sector)
        for index, sector in enumerate(SECTORS)
    )
    evidence = sum(weights, Fraction(0))
    if evidence <= 0:
        raise ExactProbabilityError("ACK event has non-positive exact mass")
    posterior = tuple(weight / evidence for weight in weights)
    return posterior, evidence  # type: ignore[return-value]


def bayes_step(
    belief: Sequence[Fraction], action: str, ack: object, completed_duration: int
) -> tuple[Belief, Fraction]:
    """Apply motion then public ACK conditioning for one completed event."""

    return condition_on_ack(predict(belief, completed_duration), action, ack)


def _event_fields(event: Mapping[str, object]) -> tuple[str, bool, int]:
    if not isinstance(event, Mapping):
        raise ExactProbabilityError("history events must be mappings")
    missing = {"action", "ack", "completed_duration"}.difference(event)
    if missing:
        raise ExactProbabilityError(f"history event missing fields: {sorted(missing)}")
    return (
        _action(event["action"]),
        ack_is_positive(event["ack"]),
        _duration(event["completed_duration"]),
    )


def _history_events(
    history: Iterable[Mapping[str, object]] | Mapping[str, object],
) -> Iterable[Mapping[str, object]]:
    """Accept either the public-history envelope or its event sequence."""

    if isinstance(history, Mapping):
        events = history.get("events")
        if not isinstance(events, (list, tuple)):
            raise ExactProbabilityError("public history must contain an events sequence")
        return events  # type: ignore[return-value]
    return history


def replay_public_history(
    history: Iterable[Mapping[str, object]] | Mapping[str, object],
    *,
    initial_belief: Sequence[Fraction] = UNIFORM_BELIEF,
) -> tuple[Belief, Fraction]:
    """Replay public events in their supplied event order.

    Returns the posterior after the final ACK and the positive joint mass of
    the observed ACK sequence conditional on the public actions/durations.
    """

    belief = _belief(initial_belief)
    history_mass = Fraction(1)
    for event in _history_events(history):
        action, ack, duration = _event_fields(event)
        belief, event_mass = bayes_step(belief, action, ack, duration)
        history_mass *= event_mass
    if history_mass <= 0:
        raise ExactProbabilityError("history must have positive exact mass")
    return belief, history_mass


def raw_hidden_path_sum(
    history: Iterable[Mapping[str, object]] | Mapping[str, object],
    *,
    initial_belief: Sequence[Fraction] = UNIFORM_BELIEF,
) -> tuple[Belief, Fraction]:
    """Independently sum every hidden-sector path compatible with a history.

    This ceiling deliberately does not call :func:`predict`,
    :func:`condition_on_ack`, :func:`bayes_step`, or
    :func:`replay_public_history`.  For ``n`` completed events it sums the
    ``3**(n+1)`` paths ``(s_0, ..., s_n)`` directly.
    """

    prior = _belief(initial_belief)
    events = tuple(_event_fields(event) for event in _history_events(history))
    matrices = tuple(transition_matrix(duration) for _, _, duration in events)
    likelihoods = tuple(
        tuple(ack_likelihood(action, ack, sector) for sector in SECTORS)
        for action, ack, _ in events
    )
    terminal_masses = [Fraction(0), Fraction(0), Fraction(0)]

    for hidden_path in product(range(3), repeat=len(events) + 1):
        path_mass = prior[hidden_path[0]]
        for event_index in range(len(events)):
            previous = hidden_path[event_index]
            completion = hidden_path[event_index + 1]
            path_mass *= matrices[event_index][previous][completion]
            path_mass *= likelihoods[event_index][completion]
        terminal_masses[hidden_path[-1]] += path_mass

    history_mass = sum(terminal_masses, Fraction(0))
    if history_mass <= 0:
        raise ExactProbabilityError("history must have positive exact mass")
    posterior = tuple(mass / history_mass for mass in terminal_masses)
    return posterior, history_mass  # type: ignore[return-value]


def fraction_pair(value: Fraction) -> tuple[int, int]:
    """Return the canonical reduced numerator/denominator wire pair."""

    if not isinstance(value, Fraction):
        raise ExactProbabilityError("wire rational must be a Fraction")
    return value.numerator, value.denominator


def fraction_from_pair(value: object) -> Fraction:
    """Decode a strict two-integer rational pair."""

    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ExactProbabilityError("rational must be a numerator/denominator pair")
    numerator, denominator = value
    if (
        isinstance(numerator, bool)
        or isinstance(denominator, bool)
        or not isinstance(numerator, int)
        or not isinstance(denominator, int)
        or denominator <= 0
    ):
        raise ExactProbabilityError("rational pair must contain integers with denominator > 0")
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise ExactProbabilityError("rational pair must already be reduced and canonical")
    return result


# Short integration aliases used by controller/analysis layers.
P_k = transition_matrix
replay = replay_public_history
raw_sum = raw_hidden_path_sum


__all__ = [
    "ACK_MATCH",
    "ACK_MISMATCH",
    "ACTIONS",
    "Belief",
    "ExactProbabilityError",
    "Matrix3",
    "P_k",
    "SECTORS",
    "SUPPORTED_DURATIONS",
    "UNIFORM_BELIEF",
    "ack_is_positive",
    "ack_likelihood",
    "bayes_step",
    "condition_on_ack",
    "fraction_from_pair",
    "fraction_pair",
    "predict",
    "raw_hidden_path_sum",
    "raw_sum",
    "replay",
    "replay_public_history",
    "transition_matrix",
]
