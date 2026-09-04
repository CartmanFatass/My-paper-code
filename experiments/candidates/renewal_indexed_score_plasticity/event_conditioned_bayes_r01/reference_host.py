"""Exact isolated reference host for the event-conditioned Bayes certificate."""

from __future__ import annotations

from fractions import Fraction
from typing import Mapping, Sequence

from .contract import (
    ACTIONS,
    ALLOWED_DURATIONS,
    EVENT_ORDER,
    MAX_EVENTS_PER_HISTORY,
    PUBLIC_HISTORY_SCHEMA,
)
from .exact_probability import (
    UNIFORM_BELIEF,
    Belief,
    ExactProbabilityError,
    ack_is_positive,
    fraction_from_pair,
    predict,
    raw_hidden_path_sum,
    replay_public_history,
)


class ReferenceHostError(ValueError):
    """Raised when a public-history envelope violates host/event semantics."""


def _plain_mapping(value: object, label: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise ReferenceHostError(f"{label} must be a plain mapping")
    return value  # type: ignore[return-value]


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ReferenceHostError(f"{label} must be an integer >= {minimum}")
    return value


def _duration(value: object, label: str) -> int:
    duration = _integer(value, label, minimum=1)
    if duration not in ALLOWED_DURATIONS:
        raise ReferenceHostError(f"{label} must be one of {ALLOWED_DURATIONS}")
    return duration


def _initial_belief_is_uniform(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return False
    decoded: list[Fraction] = []
    for item in value:
        if isinstance(item, Fraction):
            decoded.append(item)
        else:
            try:
                decoded.append(fraction_from_pair(item))
            except ExactProbabilityError:
                return False
    return tuple(decoded) == UNIFORM_BELIEF


def validate_clocks(history: Mapping[str, object]) -> dict[str, object]:
    """Validate renewal, primitive-time, event-order, and next-credit clocks.

    Stored beliefs are checked only as certificates of the frozen uniform
    initial condition.  They are never used by replay.
    """

    envelope = _plain_mapping(history, "public history")
    required = {
        "schema",
        "history_id",
        "binding_class",
        "initial_belief",
        "events",
        "decision",
    }
    missing = required.difference(envelope)
    if missing:
        raise ReferenceHostError(f"public history missing fields: {sorted(missing)}")
    for label in ("schema", "history_id", "binding_class"):
        if not isinstance(envelope[label], str) or not envelope[label]:
            raise ReferenceHostError(f"{label} must be a non-empty string")
    if envelope["schema"] != PUBLIC_HISTORY_SCHEMA:
        raise ReferenceHostError(f"schema must be {PUBLIC_HISTORY_SCHEMA}")
    if not _initial_belief_is_uniform(envelope.get("initial_belief")):
        raise ReferenceHostError("initial_belief must certify the frozen uniform belief")

    events_value = envelope["events"]
    if not isinstance(events_value, (list, tuple)):
        raise ReferenceHostError("events must be a list or tuple")
    events = tuple(_plain_mapping(event, "event") for event in events_value)
    if not events:
        raise ReferenceHostError("a decision history must contain at least one completed event")
    if len(events) > MAX_EVENTS_PER_HISTORY:
        raise ReferenceHostError(
            f"history is bounded to {MAX_EVENTS_PER_HISTORY} completed events"
        )

    first_start: int | None = None
    prior_end: int | None = None
    prior_renewal: int | None = None
    total_duration = 0
    for position, event in enumerate(events):
        missing_event = {
            "renewal_index",
            "primitive_start",
            "primitive_end",
            "completed_duration",
            "action",
            "ack",
        }.difference(event)
        if missing_event:
            raise ReferenceHostError(
                f"event {position} missing fields: {sorted(missing_event)}"
            )
        renewal = _integer(event["renewal_index"], f"event {position} renewal_index")
        start = _integer(event["primitive_start"], f"event {position} primitive_start")
        end = _integer(event["primitive_end"], f"event {position} primitive_end")
        duration = _duration(event["completed_duration"], f"event {position} completed_duration")
        if end - start != duration:
            raise ReferenceHostError(f"event {position} duration does not match primitive clocks")
        if renewal != position:
            raise ReferenceHostError("renewal indices must be consecutive from zero")
        if position == 0:
            first_start = start
            if start != 0:
                raise ReferenceHostError("first primitive hold must start at zero")
        else:
            if renewal != prior_renewal + 1:  # type: ignore[operator]
                raise ReferenceHostError("renewal indices must increase by one in event order")
            if start != prior_end:
                raise ReferenceHostError("primitive event intervals must be contiguous")
        if event["action"] not in ACTIONS:
            raise ReferenceHostError(f"event {position} has invalid action")
        try:
            ack_is_positive(event["ack"])
        except ExactProbabilityError as error:
            raise ReferenceHostError(f"event {position} has invalid ack") from error

        expected_indices = {
            "action_event_index": 5 * renewal,
            "hold_completion_event_index": 5 * renewal + 1,
            "motion_event_index": 5 * renewal + 2,
            "ack_event_index": 5 * renewal + 3,
            "private_update_event_index": 5 * renewal + 4,
        }
        for field, expected_index in expected_indices.items():
            if field not in event:
                raise ReferenceHostError(f"event {position} missing field: {field}")
            actual_index = _integer(event[field], f"event {position} {field}")
            if actual_index != expected_index:
                raise ReferenceHostError(
                    f"event {position} violates frozen {' < '.join(EVENT_ORDER)} order"
                )
        prior_end = end
        prior_renewal = renewal
        total_duration += duration

    decision = _plain_mapping(envelope["decision"], "decision")
    missing_decision = {
        "renewal_index",
        "primitive_time",
        "next_duration",
        "next_action_event_index",
        "next_hold_credit",
    }.difference(decision)
    if missing_decision:
        raise ReferenceHostError(f"decision missing fields: {sorted(missing_decision)}")
    decision_renewal = _integer(decision["renewal_index"], "decision renewal_index")
    primitive_time = _integer(decision["primitive_time"], "decision primitive_time")
    next_duration = _duration(decision["next_duration"], "decision next_duration")
    next_action_index = _integer(decision["next_action_event_index"], "next_action_event_index")
    credit = _plain_mapping(decision["next_hold_credit"], "next_hold_credit")
    if set(credit) != {"primitive_start", "primitive_end"}:
        raise ReferenceHostError("next_hold_credit must contain primitive_start/end")
    credit_start = _integer(credit["primitive_start"], "next_hold_credit primitive_start")
    credit_end = _integer(credit["primitive_end"], "next_hold_credit primitive_end")
    if decision_renewal != prior_renewal + 1:  # type: ignore[operator]
        raise ReferenceHostError("decision renewal must follow the final completed event")
    if primitive_time != prior_end:
        raise ReferenceHostError("decision primitive_time must equal the final primitive_end")
    if next_action_index != 5 * decision_renewal:
        raise ReferenceHostError("next action must follow the final private update")
    if credit_start != primitive_time or credit_end - credit_start != next_duration:
        raise ReferenceHostError("next-hold credit must start now and span next_duration")
    if primitive_time - first_start != total_duration:  # type: ignore[operator]
        raise ReferenceHostError("completed physical time does not equal duration allocation")

    return {
        "completed_renewals": len(events),
        "primitive_start": first_start,
        "primitive_time": primitive_time,
        "completed_physical_time": total_duration,
        "next_duration": next_duration,
        "next_hold_credit_start": credit_start,
        "next_hold_credit_end": credit_end,
    }


def replay_full_bayes(history: Mapping[str, object]) -> Belief:
    """Replay the full public event history from the frozen uniform belief."""

    validate_clocks(history)
    posterior, _ = replay_public_history(history, initial_belief=UNIFORM_BELIEF)
    return posterior


def raw_history_bayes(history: Mapping[str, object]) -> Belief:
    """Return the independent direct hidden-path RAW posterior."""

    validate_clocks(history)
    posterior, _ = raw_hidden_path_sum(history, initial_belief=UNIFORM_BELIEF)
    return posterior


def history_path_mass(history: Mapping[str, object]) -> Fraction:
    """Return reachability mass under the uniform reference-action law.

    RAW posterior replay conditions on the public action sequence.  Reachability
    additionally includes the frozen full-support probability ``(1/3)**n`` of
    selecting those actions.
    """

    validate_clocks(history)
    events = history["events"]
    assert isinstance(events, (list, tuple))
    _, conditional_mass = raw_hidden_path_sum(history, initial_belief=UNIFORM_BELIEF)
    mass = conditional_mass * Fraction(1, 3) ** len(events)
    if mass <= 0:
        raise ReferenceHostError("reachable history must have positive path mass")
    return mass


def q_values(belief: Sequence[Fraction], next_duration: int) -> dict[str, Fraction]:
    """Compute exact native next-hold values in printed action order."""

    try:
        completion = predict(belief, next_duration)
    except ExactProbabilityError as error:
        raise ReferenceHostError(str(error)) from error
    k = Fraction(next_duration)
    return {
        action: k * (Fraction(-3, 5) + Fraction(6, 5) * completion[index])
        for index, action in enumerate(ACTIONS)
    }


def choose_action(
    belief_or_values: Sequence[Fraction] | Mapping[str, Fraction],
    next_duration: int | None = None,
) -> tuple[str, Fraction]:
    """Choose maximum Q with the frozen ``LEFT < CENTER < RIGHT`` tie order."""

    if isinstance(belief_or_values, Mapping):
        if next_duration is not None:
            raise ReferenceHostError("next_duration is invalid when Q values are supplied")
        if set(belief_or_values) != set(ACTIONS):
            raise ReferenceHostError("Q mapping must contain exactly the three actions")
        values = dict(belief_or_values)
        if any(not isinstance(value, Fraction) for value in values.values()):
            raise ReferenceHostError("Q values must be Fractions")
    else:
        if next_duration is None:
            raise ReferenceHostError("next_duration is required when a belief is supplied")
        values = q_values(belief_or_values, next_duration)
    best_value = max(values.values())
    for action in ACTIONS:
        if values[action] == best_value:
            return action, best_value
    raise AssertionError("non-empty action set has no maximum")


def account_physical_time(history: Mapping[str, object]) -> dict[str, Fraction | int]:
    """Reconcile realized utility and completed physical-time normalization."""

    clocks = validate_clocks(history)
    events = history["events"]
    assert isinstance(events, (list, tuple))  # established by validate_clocks
    realized_utility = 0
    for event in events:
        assert isinstance(event, Mapping)
        duration = event["completed_duration"]
        assert isinstance(duration, int)
        realized_utility += duration if ack_is_positive(event["ack"]) else -duration
    completed_time = clocks["completed_physical_time"]
    assert isinstance(completed_time, int) and completed_time > 0
    normalized = Fraction(realized_utility, completed_time)
    if normalized < -1 or normalized > 1:
        raise ReferenceHostError("physical-time-normalized return lies outside [-1, 1]")
    return {
        "realized_utility": realized_utility,
        "completed_physical_time": completed_time,
        "physical_time_normalized_return": normalized,
    }


def evaluate_full_bayes(history: Mapping[str, object]) -> dict[str, object]:
    """Convenience evaluation for integration code (not used by pre-result checks)."""

    belief = replay_full_bayes(history)
    decision = history["decision"]
    assert isinstance(decision, Mapping)
    next_duration = decision["next_duration"]
    assert isinstance(next_duration, int)
    values = q_values(belief, next_duration)
    action, value = choose_action(values)
    return {"posterior": belief, "q_values": values, "action": action, "value": value}


__all__ = [
    "ReferenceHostError",
    "account_physical_time",
    "choose_action",
    "evaluate_full_bayes",
    "history_path_mass",
    "q_values",
    "raw_history_bayes",
    "replay_full_bayes",
    "validate_clocks",
]
