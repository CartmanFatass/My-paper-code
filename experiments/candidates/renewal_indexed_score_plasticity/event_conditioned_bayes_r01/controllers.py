"""Exact controller views, marginalization, and complete twin evaluation."""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Mapping, Sequence

from .contract import (
    ACTIONS,
    REGISTERED_BINDING,
    SPEC_SCHEMA,
    TEST_ONLY_BINDING,
    TWIN_CENSUS_SCHEMA,
    fraction_pair,
    validate_registered_spec,
)
from .exact_probability import UNIFORM_BELIEF, replay_public_history
from .native_backend import (
    NATIVE_REGISTRY_KEY as BACKEND_REGISTRY_KEY,
    REFERENCE_FALLBACK_KEY,
    evaluate_history,
    native_status,
)
from .reachable_twins import (
    CensusRow,
    TwinDefinition,
    VIEW_FUNCTIONS,
    full_bayes_k_erased_view,
    last_ack_bayes_view,
    registered_twins,
    validate_pairing,
)
from .reference_host import (
    account_physical_time,
    choose_action,
    history_path_mass,
    q_values,
    raw_history_bayes,
    replay_full_bayes,
)


class ControllerError(RuntimeError):
    """Exact controller evaluation or marginalization failed closed."""


Belief = tuple[Fraction, Fraction, Fraction]


def _wire_fraction(value: Fraction) -> list[int]:
    return fraction_pair(value)


def _wire_belief(values: Sequence[Fraction]) -> list[list[int]]:
    return [_wire_fraction(value) for value in values]


def _wire_q(values: Mapping[str, Fraction]) -> dict[str, list[int]]:
    return {action: _wire_fraction(values[action]) for action in ACTIONS}


def _wire_view(value: object) -> object:
    if isinstance(value, tuple):
        return [_wire_view(item) for item in value]
    if isinstance(value, list):
        return [_wire_view(item) for item in value]
    return value


def _unique_choice(values: Mapping[str, Fraction]) -> tuple[str, Fraction, bool]:
    action, value = choose_action(values)
    return action, value, sum(candidate == value for candidate in values.values()) == 1


def last_ack_g_masses(history: Mapping[str, object]) -> Belief:
    """Independent encoding of the existing exact fixed G recurrence map.

    Historical source arithmetic freezes logits ``(+30,-30,-30)`` after a
    positive ACK and ``(-30,0,0)`` after a negative ACK, permuted by the final
    action.  Prior belief, completed duration, clocks, and next duration are not
    read here.
    """

    events = history.get("events")
    if not isinstance(events, list) or not events or not isinstance(events[-1], dict):
        raise ControllerError("LAST_ACK_G requires a final public event")
    final = events[-1]
    action = final.get("action")
    ack = final.get("ack")
    if action not in ACTIONS or ack not in ("+", "-"):
        raise ControllerError("LAST_ACK_G final packet is malformed")
    selected = ACTIONS.index(str(action))
    if ack == "+":
        masses = [Fraction(17, 171)] * 3
        masses[selected] = Fraction(137, 171)
    else:
        masses = [Fraction(52, 121)] * 3
        masses[selected] = Fraction(17, 121)
    if sum(masses, Fraction()) != 1:
        raise AssertionError("fixed G masses must normalize exactly")
    return tuple(masses)  # type: ignore[return-value]


def _weighted_belief(
    rows: Sequence[CensusRow],
    posteriors: Mapping[str, Belief],
) -> Belief:
    total_weight = sum((row.population_weight for row in rows), Fraction())
    if total_weight <= 0:
        raise ControllerError("marginal population has no positive weight")
    result = tuple(
        sum(
            (
                row.population_weight
                * posteriors[str(row.history["history_id"])][sector]
                for row in rows
            ),
            Fraction(),
        )
        / total_weight
        for sector in range(3)
    )
    if sum(result, Fraction()) != 1:
        raise ControllerError("marginalized belief did not normalize exactly")
    return result  # type: ignore[return-value]


def _groups(
    rows: Sequence[CensusRow],
    controller: str,
) -> dict[tuple[object, ...], list[CensusRow]]:
    view = VIEW_FUNCTIONS[controller]
    result: dict[tuple[object, ...], list[CensusRow]] = {}
    for row in rows:
        result.setdefault(view(row.history), []).append(row)
    return result


def _pre_last_belief(history: Mapping[str, object]) -> Belief:
    events = history["events"]
    assert isinstance(events, list)
    if len(events) == 1:
        return UNIFORM_BELIEF
    belief, _ = replay_public_history(events[:-1], initial_belief=UNIFORM_BELIEF)
    return belief


def _decision_record(
    controller: str,
    belief: Belief,
    next_duration: int,
) -> dict[str, object]:
    values = q_values(belief, next_duration)
    action, value, unique = _unique_choice(values)
    normalized = value / next_duration
    if not Fraction(-1) <= normalized <= Fraction(1):
        raise ControllerError("next-hold normalized expected return is outside [-1,1]")
    return {
        "controller": controller,
        "state_kind": "EXACT_BELIEF",
        "state": _wire_belief(belief),
        "q_values": _wire_q(values),
        "action": action,
        "value": _wire_fraction(value),
        "decision_state_physical_time_normalized_expected_return": _wire_fraction(normalized),
        "unique_action": unique,
    }


def evaluate_twins(
    twins: Sequence[TwinDefinition],
    *,
    binding_class: str,
    spec_schema: str,
) -> dict[str, object]:
    """Evaluate a complete literal census.

    Registered callers reach this only after exact spec validation in
    :func:`evaluate_registered_census`.  Tests must use TEST_ONLY histories.
    """

    if binding_class not in (REGISTERED_BINDING, TEST_ONLY_BINDING):
        raise ControllerError("unsupported binding class")
    validate_pairing(twins, binding_class=binding_class)
    rows = [row for twin in twins for row in twin.rows]
    posteriors: dict[str, Belief] = {}
    raw_posteriors: dict[str, Belief] = {}
    backends: dict[str, object] = {}

    for row in rows:
        history_id = str(row.history["history_id"])
        full = replay_full_bayes(row.history)
        raw = raw_history_bayes(row.history)
        native = evaluate_history(row.history)
        posteriors[history_id] = full
        raw_posteriors[history_id] = raw
        backends[history_id] = native

    erased_groups = _groups(rows, "FULL_BAYES_K_ERASED")
    last_groups = _groups(rows, "LAST_ACK_BAYES")
    erased_beliefs = {
        key: _weighted_belief(group, posteriors) for key, group in erased_groups.items()
    }
    last_beliefs = {
        key: _weighted_belief(group, posteriors) for key, group in last_groups.items()
    }

    output_rows: list[dict[str, object]] = []
    for row in rows:
        history = row.history
        history_id = str(history["history_id"])
        decision = history["decision"]
        assert isinstance(decision, dict)
        next_duration = int(decision["next_duration"])
        raw_decision = _decision_record(
            "RAW_HISTORY_BAYES", raw_posteriors[history_id], next_duration
        )
        full_decision = _decision_record("FULL_BAYES_K", posteriors[history_id], next_duration)
        erased_decision = _decision_record(
            "FULL_BAYES_K_ERASED",
            erased_beliefs[full_bayes_k_erased_view(history)],
            next_duration,
        )
        last_decision = _decision_record(
            "LAST_ACK_BAYES",
            last_beliefs[last_ack_bayes_view(history)],
            next_duration,
        )
        g_masses = last_ack_g_masses(history)
        g_action = ACTIONS[max(range(3), key=lambda index: g_masses[index])]
        g_unique = sum(value == max(g_masses) for value in g_masses) == 1
        g_q = q_values(g_masses, next_duration)
        g_value = g_q[g_action]
        g_normalized = g_value / next_duration
        if not Fraction(-1) <= g_normalized <= Fraction(1):
            raise ControllerError("LAST_ACK_G normalized expected return is outside [-1,1]")
        g_decision = {
            "controller": "LAST_ACK_G",
            "state_kind": "EXACT_FIXED_G_MASS",
            "state": _wire_belief(g_masses),
            "q_values": _wire_q(g_q),
            "action": g_action,
            "value": _wire_fraction(g_value),
            "decision_state_physical_time_normalized_expected_return": _wire_fraction(
                g_normalized
            ),
            "unique_action": g_unique,
        }
        raw_endpoint_q = q_values(raw_posteriors[history_id], next_duration)
        decisions = (
            raw_decision,
            full_decision,
            erased_decision,
            last_decision,
            g_decision,
        )
        for controller_decision in decisions:
            controller_action = str(controller_decision["action"])
            endpoint_value = raw_endpoint_q[controller_action]
            endpoint_return = endpoint_value / next_duration
            if not Fraction(-1) <= endpoint_return <= Fraction(1):
                raise ControllerError("row-native normalized endpoint return is outside [-1,1]")
            controller_decision["endpoint_value"] = _wire_fraction(endpoint_value)
            controller_decision["physical_time_normalized_endpoint_return"] = (
                _wire_fraction(endpoint_return)
            )
        native = backends[history_id]
        native_agrees = (
            native.posterior == posteriors[history_id]
            and native.action == full_decision["action"]
            and native.value == Fraction(*full_decision["value"])
        )
        accounting = account_physical_time(history)
        credit = decision["next_hold_credit"]
        assert isinstance(credit, dict)
        output_rows.append(
            {
                "twin_id": row.twin_id,
                "side": row.side,
                "history_id": history_id,
                "history": history,
                "population_weight": _wire_fraction(row.population_weight),
                "expected_raw_action": row.expected_raw_action,
                "reference_path_mass": _wire_fraction(history_path_mass(history)),
                "pre_last_belief": _wire_belief(_pre_last_belief(history)),
                "endpoint": {
                    "next_duration": next_duration,
                    "next_hold_credit_start": credit["primitive_start"],
                    "next_hold_credit_end": credit["primitive_end"],
                },
                "physical_accounting": {
                    "realized_utility": accounting["realized_utility"],
                    "completed_physical_time": accounting["completed_physical_time"],
                    "physical_time_normalized_return": _wire_fraction(
                        accounting["physical_time_normalized_return"]  # type: ignore[arg-type]
                    ),
                },
                "controllers": {
                    "RAW_HISTORY_BAYES": raw_decision,
                    "FULL_BAYES_K": full_decision,
                    "FULL_BAYES_K_ERASED": erased_decision,
                    "LAST_ACK_BAYES": last_decision,
                    "LAST_ACK_G": g_decision,
                },
                "raw_full_equal": raw_posteriors[history_id] == posteriors[history_id]
                and raw_decision["action"] == full_decision["action"]
                and raw_decision["value"] == full_decision["value"],
                "native_reference_equal": native_agrees,
                "backend": native.backend,
            }
        )

    twin_summaries: list[dict[str, object]] = []
    for twin in twins:
        pair_rows = [row for row in output_rows if row["twin_id"] == twin.twin_id]
        assert len(pair_rows) == 2
        raw_actions = [
            row["controllers"]["RAW_HISTORY_BAYES"]["action"]  # type: ignore[index]
            for row in pair_rows
        ]
        pre_last = [row["pre_last_belief"] for row in pair_rows]
        regrets: dict[str, list[int]] = {}
        for controller in ("FULL_BAYES_K_ERASED", "LAST_ACK_BAYES", "LAST_ACK_G"):
            total = Fraction()
            for source_row, result_row in zip(twin.rows, pair_rows):
                raw_record = result_row["controllers"]["RAW_HISTORY_BAYES"]  # type: ignore[index]
                chosen = result_row["controllers"][controller]["action"]  # type: ignore[index]
                raw_q = raw_record["q_values"]
                optimal = Fraction(*raw_record["value"])
                chosen_value = Fraction(*raw_q[chosen])
                total += source_row.population_weight * (optimal - chosen_value)
            regrets[controller] = _wire_fraction(total)
        twin_summaries.append(
            {
                "twin_id": twin.twin_id,
                "coarsened_controller": twin.coarsened_controller,
                "coarsened_view": _wire_view(
                    VIEW_FUNCTIONS[twin.coarsened_controller](twin.rows[0].history)
                ),
                "common_key_matches": VIEW_FUNCTIONS[twin.coarsened_controller](
                    twin.rows[0].history
                )
                == VIEW_FUNCTIONS[twin.coarsened_controller](twin.rows[1].history),
                "pre_last_beliefs_differ": pre_last[0] != pre_last[1],
                "raw_actions": raw_actions,
                "raw_actions_opposite": raw_actions[0] != raw_actions[1],
                "equal_weight_regret": regrets,
            }
        )

    status = native_status()
    used = sorted({str(row["backend"]) for row in output_rows})
    return {
        "schema": TWIN_CENSUS_SCHEMA,
        "binding_class": binding_class,
        "spec_schema": spec_schema,
        "complete": True,
        "rows": output_rows,
        "twin_summaries": twin_summaries,
        "backend": {
            "registered_key": BACKEND_REGISTRY_KEY,
            "reference_fallback_key": REFERENCE_FALLBACK_KEY,
            "used": used,
            "native_status": status,
            "all_rows_reference_equal": all(
                bool(row["native_reference_equal"]) for row in output_rows
            ),
        },
    }


def evaluate_registered_census(spec: object) -> dict[str, object]:
    """Result-bearing registered evaluation; never called by pre-result checks."""

    validated = validate_registered_spec(spec)
    return evaluate_twins(
        registered_twins(validated),
        binding_class=REGISTERED_BINDING,
        spec_schema=SPEC_SCHEMA,
    )


def evaluate_test_census(twins: Iterable[TwinDefinition]) -> dict[str, object]:
    fixture = tuple(twins)
    if not fixture:
        raise ControllerError("TEST_ONLY census must be non-empty")
    return evaluate_twins(
        fixture,
        binding_class=TEST_ONLY_BINDING,
        spec_schema="TEST-ONLY-RISP-ECR-R01-SPEC-V1",
    )


__all__ = [
    "ControllerError",
    "evaluate_registered_census",
    "evaluate_test_census",
    "evaluate_twins",
    "last_ack_g_masses",
]
