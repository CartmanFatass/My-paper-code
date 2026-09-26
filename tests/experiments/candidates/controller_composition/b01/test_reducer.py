import numpy as np

from experiments.candidates.controller_composition.b01.reducer import contrasts, reduce_panel


def test_additive_role_quality_has_zero_interaction():
    row = np.array([1., 3., -2.])
    column = np.array([4., -1., 5.])
    value = row[:, None] + column[None, :]
    reading = contrasts(value)
    np.testing.assert_allclose(reading["C"], 0, atol=1e-14)
    np.testing.assert_allclose(reading["D"], 0, atol=1e-14)
    np.testing.assert_allclose(reading["R"], 0, atol=1e-14)
    assert reading["kappa"] == 0


def test_cyclic_interaction_can_be_invisible_to_matching_contrasts():
    cycle = np.array([[0., 2., -2.], [-2., 0., 2.], [2., -2., 0.]])
    reading = contrasts(cycle)
    np.testing.assert_allclose(reading["C"], 0)
    np.testing.assert_allclose(reading["R_symmetric"], 0)
    np.testing.assert_allclose(reading["R_antisymmetric"], cycle)
    assert reading["kappa"] == 2


def test_opposing_world_residuals_and_joint_bootstrap_coupling():
    effect = np.array([[2., -1., -1.], [-1., 2., -1.], [-1., -1., 2.]])
    j = np.stack([10 + effect, 10 - effect])
    service = 2 * j + 5
    reading = reduce_panel(j, service, draws=301, seed=194)
    np.testing.assert_allclose(reading["J"]["finite_panel"]["R"], 0)
    np.testing.assert_allclose(reading["J"]["per_world"]["R"], [effect, -effect])
    np.testing.assert_allclose(reading["J"]["finite_panel"]["D"], 0)
    for key in ("V", "C", "D", "R", "kappa", "mixed_minus_source_diagonals"):
        j_bounds = np.asarray(reading["J"]["pointwise_95_percentiles"][key])
        s_bounds = np.asarray(reading["S_served_users_per_step"]["pointwise_95_percentiles"][key])
        if key == "V":
            np.testing.assert_allclose(s_bounds, 2 * j_bounds + 5)
        else:
            np.testing.assert_allclose(s_bounds, 2 * j_bounds, atol=1e-12)
