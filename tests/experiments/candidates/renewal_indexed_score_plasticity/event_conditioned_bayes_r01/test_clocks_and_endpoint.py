from fractions import Fraction

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    make_test_history,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reference_host import (
    ReferenceHostError,
    account_physical_time,
    validate_clocks,
)


def _history():
    return make_test_history(
        "TEST_ONLY_CLOCKS", (4, 8), ("LEFT", "CENTER"), ("+", "-")
    )


def test_clocks_keep_completed_time_and_next_hold_credit_distinct():
    clocks = validate_clocks(_history())
    assert clocks == {
        "completed_renewals": 2,
        "primitive_start": 0,
        "primitive_time": 12,
        "completed_physical_time": 12,
        "next_duration": 4,
        "next_hold_credit_start": 12,
        "next_hold_credit_end": 16,
    }


def test_physical_time_accounting_uses_completed_duration_once():
    accounting = account_physical_time(_history())
    assert accounting["realized_utility"] == -4
    assert accounting["completed_physical_time"] == 12
    assert accounting["physical_time_normalized_return"] == Fraction(-1, 3)


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda item: item["events"][1].update(primitive_start=5, primitive_end=13), "contiguous"),
        (lambda item: item["decision"].update(primitive_time=11), "final primitive_end"),
        (
            lambda item: item["decision"]["next_hold_credit"].update(primitive_end=20),
            "span next_duration",
        ),
        (
            lambda item: item["events"][0].update(motion_event_index=3, ack_event_index=2),
            "frozen",
        ),
    ],
)
def test_clock_and_endpoint_mismatches_are_rejected(mutate, match):
    history = _history()
    mutate(history)
    with pytest.raises(ReferenceHostError, match=match):
        validate_clocks(history)


def test_nonuniform_stored_initial_belief_cannot_be_injected():
    history = _history()
    history["initial_belief"] = [[1, 1], [0, 1], [0, 1]]
    with pytest.raises(ReferenceHostError, match="uniform"):
        validate_clocks(history)
