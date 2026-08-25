"""Control tables, the coefficient oracle, executable mutants, numerics."""

from fractions import Fraction

import pytest

from experiments.candidates.orbit_owner_match import canon
from experiments.candidates.orbit_owner_match import controls
from experiments.candidates.orbit_owner_match import discriminator
from experiments.candidates.orbit_owner_match import numerics


def test_two_independent_generators_agree_with_the_oracle():
    """Rejects: an oracle that merely restates one generator.

    The staged route never forms ``m*b*r`` and never branches on ``m``: it
    builds the two B x role interaction functionals and subtracts them, so
    the ``m`` dependence emerges from the subtraction.
    """
    controls.coefficient_oracle_gate()
    assert len(controls.COEFFICIENT_ORACLE) == 16
    # The staged route's ingredient really is m-independent before the
    # difference is taken -- otherwise "independent construction" is a story.
    positive = controls.interaction_functional(1, 0)
    negative = controls.interaction_functional(-1, 0)
    assert sorted(positive.values()) == sorted(negative.values())
    assert all(weight in (Fraction(1, 2), Fraction(-1, 2))
               for weight in positive.values())


def test_mutating_the_staged_route_breaks_the_oracle_agreement():
    """Rejects: a gate that would pass even if a generator were wrong."""
    original = controls.interaction_functional
    controls.interaction_functional = (
        lambda m, q: {(q, m, b, r): Fraction(b, 2)
                      for b in controls.SIGNS for r in controls.SIGNS})
    try:
        with pytest.raises(canon.ContractError):
            controls.coefficient_oracle_gate()
    finally:
        controls.interaction_functional = original
    controls.coefficient_oracle_gate()


def test_separable_logit_control_has_no_three_factor_component():
    """Rejects: a target that would fire on a purely separable signal."""
    controls.logit_control_gates()


def test_kernel_control_is_on_the_simplex_and_three_factor_zero():
    controls.kernel_control_gates()
    for row in controls.KERNEL_ZERO_CONTROL:
        assert row.k1.as_fraction() + row.k2.as_fraction() == 1
        assert row.k1.as_fraction() >= Fraction(1, 4)


def test_mutants_are_executable_not_prose():
    """Rejects: six no-op transforms.

    Asserting ``callable(...)`` would pass against
    ``{k: (lambda c: c) for k in ...}``.  Every transform must actually
    change the coefficient map it is handed.
    """
    controls.mutant_dispatch_gate()
    baseline = controls.coefficient_map()
    for row in controls.MUTANT_MATRIX:
        transform = controls.MUTANT_TRANSFORMS[row.transform_id]
        mutated = transform(controls.coefficient_map())
        if row.transform_id in controls.SWAP_COMPONENT_MUTANTS:
            # M5 mutates orientation, not weights; it is exercised by the
            # curvature gate instead.
            assert mutated == baseline
            continue
        assert mutated != baseline, row.mutant_id


def test_every_curvature_mutant_is_actually_run():
    """Rejects: frozen multipliers that no code ever checks.

    M3-M6 used to be consumed only as numbers; a typo in the multiplier
    table would have frozen a wrong margin argument undetected.
    """
    numerics.curvature_mutant_response_gate()
    original = dict(controls.MUTANT_CURVATURE_MULTIPLIERS)
    controls.MUTANT_CURVATURE_MULTIPLIERS["M6"] = Fraction(3, 4)
    try:
        with pytest.raises(canon.ContractError):
            numerics.curvature_mutant_response_gate()
    finally:
        controls.MUTANT_CURVATURE_MULTIPLIERS.clear()
        controls.MUTANT_CURVATURE_MULTIPLIERS.update(original)
    numerics.curvature_mutant_response_gate()


def test_blind_nulls_collapse_to_a_positively_signed_zero():
    """Rejects: nulls that are fingerprinted but never executed."""
    controls.null_orientation_gate()


def test_mutant_exact_responses_match_the_hand_derivation():
    """Rejects: a coefficient bug that the zero control cannot separate.

    M1 drops ``r``, leaving ``sum m*b*(m*b) = 8`` as the only surviving term:
    ``(1/2)(1/128)(8)`` per alias, doubled over q, giving +1/16.  M2 flips one
    ``+1/2`` to ``-1/2`` for both aliases, giving ``-2*K(1,1,1)``.
    """
    assert controls.run_mutant_exact("M1") == (Fraction(1, 16),
                                               Fraction(-1, 16))
    assert controls.run_mutant_exact("M2") == (Fraction(-71, 64),
                                               Fraction(-57, 64))
    controls.mutant_response_gate()


def test_unmutated_accumulation_is_exactly_zero():
    baseline = controls.exact_accumulate(controls.kernel_control_values(),
                                         controls.coefficient_map())
    assert baseline == (Fraction(0), Fraction(0))


def test_accumulator_rejects_a_missing_key():
    """Rejects: subscripting that raises a bare KeyError mid-accumulation."""
    values = controls.kernel_control_values()
    values.pop((0, 1, 1, 1))
    with pytest.raises(canon.ContractError):
        controls.exact_accumulate(values, controls.coefficient_map())


def test_accumulator_rejects_a_short_vector():
    """Rejects: zip-based accumulation that truncates silently."""
    values = controls.kernel_control_values()
    key = (0, 1, 1, 1)
    values[key] = (values[key][0],)
    with pytest.raises(canon.ContractError):
        controls.exact_accumulate(values, controls.coefficient_map())


def test_accumulator_rejects_an_extra_key():
    values = controls.kernel_control_values()
    values[(0, 1, 1, 0)] = (Fraction(0), Fraction(0))
    with pytest.raises(canon.ContractError):
        controls.exact_accumulate(values, controls.coefficient_map())


def test_pair_first_null_is_positively_oriented():
    """Rejects: an orientation that multiplies a zero difference by -0.5.

    ``(+0.0) * (-0.5)`` is ``-0.0``, so the earlier formulation could not
    claim an exact ``+0.0`` on bit-identical pairs.
    """
    values = {key: (1.0, -1.0) for key in controls.EXPECTED_KEYS}
    total = controls.oriented_pair_first_m_blind(values)
    assert total == (0.0, 0.0)
    import struct
    assert struct.pack(">d", total[0]) == struct.pack(">d", 0.0)


def test_margin_clears_the_smallest_mutant_response():
    """Rejects: a margin verified only against the numerical tolerance.

    1/128 dominates 4*tol_curv by 2^28 and was accepted on that basis, but it
    exceeds M6's response of |D_ref|/2 ~= 0.00735, so under it M6 would be
    undetectable.
    """
    controls.tolerance_gate()
    reference = abs(float(numerics.hp_curvature_reference(60)))
    margin = float(controls.MARGIN.as_fraction())
    smallest = min(abs(float(multiplier) - 1.0) * reference
                   for multiplier in
                   controls.MUTANT_CURVATURE_MULTIPLIERS.values())
    assert margin < smallest
    assert margin > 4 * float(controls.TOL_CURV.as_fraction())


def test_recovery_stays_inside_the_frozen_envelope():
    numerics.recovery_gate()
    assert (numerics.recovery_worst_residual()
            <= controls.TOL_RECOVER.as_fraction())


def test_curvature_reference_is_precision_stable_and_matches_the_literal():
    numerics.curvature_reference_stability_gate()
    numerics.frozen_curvature_literal_gate(
        controls.CURVATURE_REFERENCE_FIRST_COMPONENT.text)
    numerics.curvature_gate()


def test_platform_admission_measures_the_assumed_libm_contract():
    """Rejects: a proof conditional on an unexamined platform."""
    worst_log, worst_exp, _ = numerics.platform_admission()
    bound = float(numerics.LIBM_RELATIVE_ERROR_BOUND)
    assert float(worst_log) <= bound
    assert float(worst_exp) <= bound


def test_binary64_recovery_rejects_a_boundary_kernel():
    with pytest.raises(canon.ContractError):
        numerics.binary64_recovery((0.0, 1.0))


def test_exact_target_contrast_is_the_frozen_algebra():
    """Rejects: a target whose contrast is not the pure three-factor term.

    ``logit = 0.5*m*b*r`` gives ``D = (4, -4)`` and ``Theta_L = 4*sqrt(2)``.
    Computed in exact rationals, so this does not execute the discriminator.
    """
    assert discriminator.exact_target_contrast() == (Fraction(4),
                                                     Fraction(-4))
