from fractions import Fraction

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    make_test_history,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.exact_probability import (
    ACTIONS,
    UNIFORM_BELIEF,
    bayes_step,
    condition_on_ack,
    predict,
    raw_hidden_path_sum,
    replay_public_history,
    transition_matrix,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reference_host import (
    choose_action,
    history_path_mass,
    q_values,
    raw_history_bayes,
    replay_full_bayes,
)


def _history(events, *, next_duration=4):
    rows = tuple(events)
    history = make_test_history(
        "TEST_ONLY_RAW_FULL",
        tuple(row[0] for row in rows),
        tuple(row[1] for row in rows),
        tuple(row[2] for row in rows),
    )
    if next_duration != 4:
        decision = history["decision"]
        decision["next_duration"] = next_duration
        decision["next_hold_credit"]["primitive_end"] = (
            decision["primitive_time"] + next_duration
        )
    return history


@pytest.mark.parametrize("duration", (4, 8, 12))
def test_transition_and_prediction_normalize_exactly(duration):
    matrix = transition_matrix(duration)
    assert all(sum(row, Fraction(0)) == 1 for row in matrix)
    predicted = predict((Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)), duration)
    assert sum(predicted, Fraction(0)) == 1
    assert all(value > 0 for value in predicted)


def test_ack_conditioning_and_bayes_step_have_positive_exact_mass():
    predicted = predict(UNIFORM_BELIEF, 4)
    posterior, mass = condition_on_ack(predicted, "LEFT", "+")
    stepped, stepped_mass = bayes_step(UNIFORM_BELIEF, "LEFT", "+", 4)
    assert posterior == stepped
    assert mass == stepped_mass == Fraction(2, 5)
    assert posterior == (Fraction(2, 3), Fraction(1, 6), Fraction(1, 6))


def test_raw_hidden_path_sum_is_exactly_equal_to_public_replay():
    history = _history(((4, "LEFT", "+"), (8, "RIGHT", "-"), (12, "CENTER", "+")))
    replay_posterior, replay_mass = replay_public_history(history)
    raw_posterior, raw_mass = raw_hidden_path_sum(history)
    assert raw_posterior == replay_posterior
    assert raw_mass == replay_mass > 0
    assert raw_history_bayes(history) == replay_full_bayes(history)
    assert history_path_mass(history) == raw_mass * Fraction(1, 3) ** len(history["events"])


def test_replay_ignores_stored_intermediate_belief_fields():
    history = _history(((4, "CENTER", "+"), (4, "RIGHT", "-")))
    for event in history["events"]:
        event["stored_belief"] = [[1, 1], [0, 1], [0, 1]]
    assert replay_full_bayes(history) == raw_history_bayes(history)


def test_q_formula_and_printed_tie_order_on_test_only_fixture():
    values = q_values(UNIFORM_BELIEF, 4)
    assert tuple(values) == ACTIONS
    assert set(values.values()) == {Fraction(-4, 5)}
    assert choose_action(values) == ("LEFT", Fraction(-4, 5))


def test_positive_ack_favors_matching_completion_sector():
    posterior, _ = bayes_step(UNIFORM_BELIEF, "RIGHT", "+", 8)
    assert posterior[2] > posterior[0] == posterior[1]
