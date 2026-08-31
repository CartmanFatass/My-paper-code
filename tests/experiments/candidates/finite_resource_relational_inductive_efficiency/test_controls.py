from fractions import Fraction

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.ccic_control import (
    CCIC_EDGES, CCIC_SIGNS_A, CCIC_SIGNS_B, canonical_ccic_fixture, typed_wedge_count,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.egrcr_control import assert_rao_blackwell_equality
from experiments.candidates.finite_resource_relational_inductive_efficiency.controls.raw_value import assert_raw_value_ceiling, balanced_accuracy


def test_ccic_exact_public_typed_wedge_and_m3():
    fixture = canonical_ccic_fixture()
    assert fixture["A"]["wedge"] == 1 and fixture["A"]["m3"] == 12
    assert fixture["B"]["wedge"] == 0 and fixture["B"]["m3"] == -12
    with pytest.raises(ValueError, match="duplicate"):
        typed_wedge_count(CCIC_SIGNS_A, [*CCIC_EDGES, CCIC_EDGES[0]])


def test_egrcr_exact_fraction_rao_blackwell_equality():
    assert assert_rao_blackwell_equality() == (Fraction(0), Fraction(1, 6))


def test_raw_value_opposite_labels_force_half_balanced_accuracy():
    assert balanced_accuracy(lambda raw: int(raw[0] > 0)) == Fraction(1, 2)
    assert_raw_value_ceiling(lambda raw: 0)
    calls = {}
    def stateful(raw):
        calls[raw] = calls.get(raw, 0) + 1
        return calls[raw] % 2
    with pytest.raises(ValueError, match="not deterministic"):
        balanced_accuracy(stateful)
