from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.candidates.variable_n_fleet_churn_r02.contract import ContractViolation, MASS_TOTAL
from experiments.candidates.variable_n_fleet_churn_r02.probability import (
    categorical_logprob_adjoint,
    choose_diagnostic_u,
    choose_production_word,
    clamp_centered_max_adjoint,
    construct_probability,
    construct_probability_from_centered,
    construct_fixed_probability,
    deterministic_choice,
    diagnostic_cdf_probes,
    entropy_adjoint,
    entropy,
    forced_log_probability,
)
from experiments.candidates.variable_n_fleet_churn_r02.scalar import (
    binary64_bits,
    exact_roster_mean,
    prefix_max,
    strict_roster_max,
    update_prefix,
)


class FakeKernel:
    """Deliberately injected exact test table, not a production approximation."""

    def sigmoid_R02(self, value: float) -> float:
        if value == 0.0:
            return 0.5
        raise AssertionError("unlisted fake sigmoid input")

    def exp_R02(self, value: float) -> float:
        table = {0.0: 1.0, -1.0: 0.5, -2.0: 0.25, -3.0: 0.125, -16.0: 2.0**-16}
        if value < 0.0 and value > -1.0:
            return 1.0  # the NEXTAFTER primitive intentionally exercises equal weight bits
        return table[value]

    def log_R02(self, value: float) -> float:
        if value == 0.5:
            return -1.0
        if value == 1.0:
            return 0.0
        return -2.0

    def sqrt_R02(self, value: float) -> float:
        table = {0.0: 0.0, 0.25: 0.5, 1.0: 1.0, 25.0: 5.0}
        return table[value]


KERNEL = FakeKernel()


def test_exact_roster_mean_strict_max_and_prefix_ties() -> None:
    mean = exact_roster_mean(((1.0e16,), (1.0,), (-1.0e16,)))
    assert mean == (float(Fraction(1, 3)),)
    maximum, winners = strict_roster_max(((1.0, -0.0), (1.0, 0.0), (0.0, -1.0)))
    assert maximum == (1.0, 0.0)
    assert winners == (0, 0)
    assert binary64_bits(maximum[1]) == 0

    earlier = (0.0, 2.0, -1.0)
    assert prefix_max(earlier, (0.0, 1.0, -1.0)) == earlier
    unchanged_fixed = update_prefix((0.0,) * 3, (0.0,) * 3, (1.0,) * 3, max_has_value=False, variable=False, selected_null=False)
    unchanged_null = update_prefix((0.0,) * 3, (0.0,) * 3, (1.0,) * 3, max_has_value=False, variable=True, selected_null=True)
    assert unchanged_fixed == unchanged_null == ((0.0,) * 3, (0.0,) * 3, False)
    assert update_prefix((0.0,) * 3, (0.0,) * 3, (-2.0, -3.0, -1.0), max_has_value=False, variable=True, selected_null=False) == (
        (-2.0, -3.0, -1.0),
        (-2.0, -3.0, -1.0),
        True,
    )
    assert update_prefix((-2.0, -3.0, -1.0), (-2.0, -3.0, -1.0), (1.0, -4.0, -1.0), max_has_value=True, variable=True, selected_null=False) == (
        (-1.0, -7.0, -2.0),
        (1.0, -3.0, -1.0),
        True,
    )


def test_q52_exact_sum_positivity_and_remainder_tie_order() -> None:
    probability = construct_probability((0.0, 0.0, 0.0), (1, 2, None), KERNEL)
    quotient, remainder = divmod(MASS_TOTAL, 3)
    assert remainder == 1
    assert probability.masses == (quotient + 1, quotient, quotient)
    assert all(mass > 0 for mass in probability.masses)
    assert sum(probability.masses) == MASS_TOTAL
    assert sum(Fraction.from_float(p) for p in probability.probabilities) == 1
    assert deterministic_choice(probability) == 1


def test_nextafter_strict_determinism_is_not_replaced_by_probability_tie() -> None:
    negative_min_subnormal = -float.fromhex("0x0.0000000000001p-1022")
    probability = construct_probability_from_centered(
        (0.0, negative_min_subnormal, -16.0), (1, 2, None), KERNEL
    )
    assert probability.weights[0] == probability.weights[1]
    assert deterministic_choice(probability) == 1


def test_exact_cdf_boundaries_midpoint_words_endpoints_and_cardinality() -> None:
    probability = construct_probability((0.0, -1.0), (1, None), KERNEL)
    first_boundary = probability.cumulative[0]
    assert choose_diagnostic_u(probability, Fraction(0)) == 1
    assert choose_diagnostic_u(probability, Fraction(first_boundary, MASS_TOTAL)) is None
    assert choose_production_word(probability, 4096 * first_boundary - 1) == 1
    assert choose_production_word(probability, 4096 * first_boundary) is None

    probes = diagnostic_cdf_probes(probability)
    assert len(probes) == 5 * 2 + 3
    names_by_edge = {(probe.edge_index, probe.name) for probe in probes}
    assert (0, "PRODUCTION_WORD_BELOW") not in names_by_edge
    assert (2, "PRODUCTION_WORD_ABOVE") not in names_by_edge
    assert next(probe for probe in probes if probe.edge_index == 0 and probe.name == "NEXTAFTER_LOWER").rejected
    assert next(probe for probe in probes if probe.edge_index == 2 and probe.name == "EXACT").rejected
    assert next(probe for probe in probes if probe.edge_index == 2 and probe.name == "NEXTAFTER_UPPER").rejected
    assert next(probe for probe in probes if probe.edge_index == 2 and probe.name == "NEXTAFTER_LOWER").action is None

    with pytest.raises(ContractViolation):
        choose_diagnostic_u(probability, Fraction(-1, MASS_TOTAL))
    with pytest.raises(ContractViolation):
        choose_diagnostic_u(probability, Fraction(1))
    with pytest.raises(ContractViolation):
        choose_production_word(probability, 1 << 64)


def test_categorical_entropy_and_center_clamp_custom_adjoints() -> None:
    equal = construct_probability((0.0, 0.0), (1, None), KERNEL)
    assert equal.probabilities == (0.5, 0.5)
    assert categorical_logprob_adjoint(equal, 1) == (0.5, -0.5)
    assert entropy_adjoint(equal, KERNEL) == (0.0, 0.0)

    clamped = construct_probability((0.0, -16.0), (1, None), KERNEL)
    assert clamp_centered_max_adjoint(clamped, (3.0, 2.0)) == (0.0, 0.0)


def test_fixed_probability_is_exact_and_has_no_rng_cdf_or_transcendental_call() -> None:
    fixed = construct_fixed_probability(7)
    assert deterministic_choice(fixed) == 7
    assert fixed.masses == (MASS_TOTAL,)
    assert fixed.probabilities == (1.0,)
    assert forced_log_probability(fixed, 7, KERNEL) == 0.0
    assert entropy(fixed, KERNEL) == 0.0
    assert categorical_logprob_adjoint(fixed, 7) == (0.0,)
    assert entropy_adjoint(fixed, KERNEL) == (0.0,)
    with pytest.raises(ContractViolation):
        choose_production_word(fixed, 0)
    with pytest.raises(ContractViolation):
        diagnostic_cdf_probes(fixed)


def test_shape_order_nonfinite_and_null_last_drift_fail_closed() -> None:
    with pytest.raises(ContractViolation):
        construct_probability((0.0, 0.0), (None, 1), KERNEL)
    with pytest.raises(ContractViolation):
        construct_probability((0.0,), (1, None), KERNEL)
    with pytest.raises(ContractViolation):
        construct_probability((float("nan"),), (None,), KERNEL)
