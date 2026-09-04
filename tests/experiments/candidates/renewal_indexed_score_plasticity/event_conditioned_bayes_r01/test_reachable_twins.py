from fractions import Fraction

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    make_test_history,
    registered_spec,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reachable_twins import (
    TwinCensusError,
    make_test_twin,
    registered_twins,
    validate_pairing,
)


def test_registered_census_is_exactly_two_literal_pairs_without_search():
    twins = registered_twins(registered_spec())
    assert tuple(twin.twin_id for twin in twins) == (
        "PRIOR_HISTORY_ACK_TWIN",
        "DURATION_ORDER_TWIN",
    )
    assert tuple(row.side for twin in twins for row in twin.rows) == ("A", "B", "A", "B")
    assert sum((row.population_weight for row in twins[0].rows), Fraction()) == 1
    validate_pairing(twins, binding_class="REGISTERED")


def test_test_only_pairing_requires_common_declared_view_and_distinct_full_history():
    first = make_test_history(
        "TEST_ONLY_PAIR_A", (4, 4, 8), ("LEFT", "CENTER", "RIGHT"), ("+", "+", "+")
    )
    second = make_test_history(
        "TEST_ONLY_PAIR_B", (4, 8, 8), ("LEFT", "CENTER", "RIGHT"), ("+", "+", "+")
    )
    twin = make_test_twin(
        "TEST_ONLY_DURATION_PAIR", "FULL_BAYES_K_ERASED", (first, second)
    )
    validate_pairing((twin,), binding_class="TEST_ONLY")

    identical = make_test_history(
        "TEST_ONLY_PAIR_C", (4, 4, 8), ("LEFT", "CENTER", "RIGHT"), ("+", "+", "+")
    )
    bad = make_test_twin(
        "TEST_ONLY_IDENTICAL_PAIR", "FULL_BAYES_K_ERASED", (first, identical)
    )
    with pytest.raises(TwinCensusError, match="full histories must differ"):
        validate_pairing((bad,), binding_class="TEST_ONLY")


def test_pairing_rejects_duration_erased_reconstruction_through_final_packet():
    first = make_test_history(
        "TEST_ONLY_ERASE_A", (4, 8), ("CENTER", "LEFT"), ("+", "+")
    )
    second = make_test_history(
        "TEST_ONLY_ERASE_B", (8, 4), ("CENTER", "LEFT"), ("+", "+")
    )
    twin = make_test_twin(
        "TEST_ONLY_BAD_ERASE", "FULL_BAYES_K_ERASED", (first, second)
    )
    with pytest.raises(TwinCensusError, match="coarsened twin keys"):
        validate_pairing((twin,), binding_class="TEST_ONLY")
