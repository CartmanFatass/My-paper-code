from __future__ import annotations

import math

import numpy as np
import pytest

from experiments.candidates.optimizer_entropy_exposure_boundary_relay import experiment as oeer


def test_adam_formula_and_reset_carry_semantics() -> None:
    theta = oeer.THETA0.copy()
    gradient = np.asarray((0.1, -0.2, 0.3, -0.4))
    reset_theta, reset = oeer.adam_step(theta, gradient, oeer.fresh_adam())
    assert reset.t == 1
    assert np.allclose(reset.m, 0.1 * gradient)
    assert np.allclose(reset.v, 0.001 * gradient**2)
    assert np.allclose(reset_theta, theta - oeer.LEARNING_RATE * gradient / (np.abs(gradient) + oeer.EPSILON))
    carry_theta, carry = oeer.adam_step(theta, gradient, oeer.carried_adam())
    assert carry.t == 13
    assert np.allclose(carry.m, 0.9 * oeer.M0 + 0.1 * gradient)
    assert np.allclose(carry.v, 0.999 * oeer.V0 + 0.001 * gradient**2)
    assert not np.allclose(carry_theta, reset_theta)


def test_philox_tape_counter_keying_and_exact_mirroring() -> None:
    tapes = oeer.build_tapes(oeer.MASTER_SEEDS[0])
    assert tapes == oeer.build_tapes(oeer.MASTER_SEEDS[0])
    assert tapes != oeer.build_tapes(oeer.MASTER_SEEDS[1])
    for positive, negative in (((1, 1), (-1, -1)), ((1, -1), (-1, 1))):
        left, right = tapes[oeer._root_label(positive)], tapes[oeer._root_label(negative)]
        assert np.allclose(np.asarray(left["action_uniforms"]) + right["action_uniforms"], 1.0)
        assert np.array_equal(-np.asarray(left["nuisance_bits"]), right["nuisance_bits"])
        assert all(tuple(-x for x in a) == tuple(b) for a, b in zip(left["yoked_roots"], right["yoked_roots"]))
    for tape in tapes.values():
        assert tuple(tape["yoked_roots"][0]) == tuple(tape["start_root"])
        assert all({tuple(root) for root in tape["yoked_roots"][j : j + 4]} == set(oeer.ROOTS) for j in range(0, 64, 4))


def test_boundary_barrier_delta_match_and_generic_geometry() -> None:
    boundary = oeer.build_boundary()
    assert boundary["mutation_barrier"]["four_main_updates_completed_before_continuation"]
    assert len(boundary["main_cells"]) == 4
    for cell in boundary["main_cells"].values():
        assert np.allclose(cell["theta1_main"], cell["delta_match"]["theta1"], rtol=1e-6, atol=1e-8)
        assert cell["delta_match"]["adam_state"] == oeer.fresh_adam().as_dict()
    for memory in oeer.MEMORIES:
        generic = boundary["generic"][memory]
        d = np.asarray(generic["entropy_displacement_difference"])
        kicks = [np.asarray(generic["states"][name]["kick"]) for name in oeer.GENERIC_KICKS]
        assert all(np.dot(d, kick) == pytest.approx(0.0, abs=1e-12) for kick in kicks)
        assert all(np.linalg.norm(kick) == pytest.approx(np.linalg.norm(d), rel=1e-6, abs=1e-8) for kick in kicks)
        assert np.allclose(sum(kicks), 0.0)


def test_arm_count_continuation_rows_and_all_observable_trajectories() -> None:
    boundary = oeer.build_boundary()
    conditions = oeer._initial_conditions(boundary)
    assert len(conditions) == 32
    assert sum(arm.startswith("MAIN|") for arm, *_rest in conditions) == 8
    assert sum(arm.startswith("DELTA_MATCH|") for arm, *_rest in conditions) == 8
    assert sum(arm.startswith("GENERIC|") for arm, *_rest in conditions) == 16
    arm_id, family, memory, variant, theta, state = conditions[0]
    tape = oeer.build_tapes(oeer.MASTER_SEEDS[0])[oeer._root_label((1, 1))]
    arm = oeer.run_continuation(arm_id, family, memory, variant, "YOKED", theta, state, tape)
    assert len(arm["future_rows"]) == 64
    assert set(arm["trajectories"]) == set(oeer.TRAJECTORY_FIELDS)
    assert all(len(values) == 65 for values in arm["trajectories"].values())
    assert arm["U"] == pytest.approx(np.mean(arm["trajectories"]["correct_probability"]))


def test_effect_equations_factorial_and_analyzer_contracts() -> None:
    values: dict[str, float] = {}
    for family, memory, entropy, exposure in product_for_test():
        base = {"CARRY": 2.0, "RESET": 0.0}[memory]
        base += {"SELF": 8.0, "YOKED": 0.0}[exposure]
        # Add explicit interactions that exercise all four relay equations.
        if entropy == "PULSE":
            base += 1.0 + (2.0 if exposure == "SELF" else 0.0)
        if family == "MAIN":
            base += 10.0
            if memory == "CARRY":
                base += 3.0 + (5.0 if exposure == "SELF" else 0.0)
        values[f"{family}|{memory}|{entropy}|{exposure}"] = base
    equations = oeer._effect_equations(values)
    assert float(equations["effects"]["D_M"]) == pytest.approx(1.0)
    assert float(equations["effects"]["A_M"]) == pytest.approx(2.0)
    assert float(equations["effects"]["D_H"]) == pytest.approx(3.0)
    assert float(equations["effects"]["A_H"]) == pytest.approx(5.0)
    p = oeer._sign_flip_p(np.ones(8))
    assert p == pytest.approx(2.0 / 256.0)
    summary = oeer._summary(np.arange(8, dtype=float))
    assert summary["mean"] == pytest.approx(3.5)
    assert len(summary["t_interval_95"]) == 2 and math.isfinite(summary["exact_two_sided_sign_flip_p"])


def product_for_test():
    import itertools

    return itertools.product(("MAIN", "DELTA_MATCH"), oeer.MEMORIES, oeer.ENTROPIES, oeer.EXPOSURES)


def test_claim_qualification_applies_exposure_generic_and_cancellation_gates() -> None:
    primary = {effect: {"directional_material_effect": True} for effect in ("D_M", "D_H", "A_M", "A_H")}
    exposure = {"X_M": {"mean": 0.20}, "X_H": {"mean": 0.20}}
    generic = {
        "D_M_entropy_direction_separated": True,
        "A_M_entropy_direction_separated": True,
    }
    heterogeneity = {
        effect: {"mean_obtained_by_cancellation": False}
        for effect in ("D_M", "D_H", "A_M", "A_H")
    }
    qualified = oeer._claim_qualification(primary, exposure, generic, heterogeneity)
    assert all(row["claim_qualified_directional_effect"] for row in qualified.values())
    assert qualified["D_M"]["claim_qualified_entropy_specific_directional_effect"]
    assert not qualified["D_H"]["claim_qualified_entropy_specific_directional_effect"]

    exposure["X_M"]["mean"] = 0.09
    assert not oeer._claim_qualification(primary, exposure, generic, heterogeneity)["A_M"]["claim_qualified_directional_effect"]
    exposure["X_M"]["mean"] = 0.20
    generic["D_M_entropy_direction_separated"] = False
    assert not oeer._claim_qualification(primary, exposure, generic, heterogeneity)["D_M"]["claim_qualified_directional_effect"]
    generic["D_M_entropy_direction_separated"] = True
    heterogeneity["D_H"]["mean_obtained_by_cancellation"] = True
    assert not oeer._claim_qualification(primary, exposure, generic, heterogeneity)["D_H"]["claim_qualified_directional_effect"]


def test_opposite_sign_heterogeneity_ignores_exact_zero_and_retains_components() -> None:
    assert not oeer._opposite_nonzero_signs((1.0, 0.0, 2.0))
    assert not oeer._opposite_nonzero_signs((0.0, 0.0))
    assert oeer._opposite_nonzero_signs((1.0, 0.0, -2.0))
    starts = {
        oeer._root_label((1, 1)): {"D_M": 0.3},
        oeer._root_label((-1, -1)): {"D_M": -0.1},
        oeer._root_label((1, -1)): {"D_M": 0.0},
        oeer._root_label((-1, 1)): {"D_M": 0.2},
    }
    pairs = oeer._mirror_pairs_for_effect(starts, "D_M")
    assert pairs[0]["opposite_nonzero_signs"]
    assert not pairs[1]["opposite_nonzero_signs"]
    assert pairs[1]["positive_effect"] == 0.0


def test_generic_within_band_uses_mean_paired_margin_not_marginal_means() -> None:
    primary = {"D_M": {"mean": 0.50}, "A_M": {"mean": -0.50}}
    generic = {
        "G_D": {"mean": 0.10},
        "G_A": {"mean": 0.10},
        "D_M_margin": {"mean": 0.01, "t_interval_95": [-0.01, 0.03]},
        "A_M_margin": {"mean": 0.03, "t_interval_95": [0.01, 0.05]},
    }
    oeer._apply_generic_classifications(primary, generic)
    assert generic["D_M_within_0_02_of_generic_envelope"] is True
    assert generic["D_M_entropy_direction_separated"] is False
    assert generic["A_M_within_0_02_of_generic_envelope"] is False
    assert generic["A_M_entropy_direction_separated"] is True
