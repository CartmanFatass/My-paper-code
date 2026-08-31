from fractions import Fraction

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.vqfp_controls import (
    ActionSeamAbsent, FRRIE_ACTION_SEAM_ABSENT, association_did,
    assert_half_cycle_laws, half_cycle, largest_remainder, marginal_heap,
    mass_weights, require_action_seam, uniform_absorption_witness,
)


def test_lr_legality_and_physical_coordinate_ties():
    weights = [Fraction(1), Fraction(1), Fraction(1)]
    coordinates = [Fraction(5), Fraction(1), Fraction(3)]
    command = largest_remainder(weights, coordinates)
    assert command == (40, 40, 40) and sum(command) == 120


def test_marginal_heap_equal_delta_uses_coordinate_not_index():
    command = marginal_heap([1, 1], [1, 1], [Fraction(10), Fraction(1)])
    # With symmetric curves, the lower-coordinate cell receives the first tie.
    assert sum(command) == 120 and command[1] >= command[0]


def test_half_cycle_uniform_absorption_mass_p_and_did_order():
    uniform = [Fraction(1, 4)] * 4
    assert_half_cycle_laws(uniform)
    assert half_cycle(half_cycle(uniform)) == tuple(uniform)
    assert uniform_absorption_witness(uniform, Fraction(2))
    v = [Fraction(1, 8), Fraction(2, 8), Fraction(3, 8), Fraction(2, 8)]
    d = [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
    assert mass_weights(v, d, reassociated=True) == tuple(a * b for a, b in zip(half_cycle(v), d))
    assert association_did(Fraction(9), Fraction(6), Fraction(8), Fraction(7)) == 2


def test_vqfp_remains_output_disconnected():
    with pytest.raises(ActionSeamAbsent, match=FRRIE_ACTION_SEAM_ABSENT):
        require_action_seam()
