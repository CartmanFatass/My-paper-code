"""Unit checks for the UCOPE training-target diagnostic's own machinery.

The diagnostic decides a branch, so its solver, its gradient statistic, its root-target
reconstruction and its five-branch reading rule are pinned here on synthetic inputs whose
answers are known in closed form. These tests train nothing and read no published run.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT = PROJECT_ROOT / "scripts" / "run_ucope_training_target_diagnostic_r01.py"


def _load():
    spec = importlib.util.spec_from_file_location("ucope_training_target_diagnostic", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DIAG = _load()


def test_thresholds_match_the_card():
    assert DIAG.EPSILON == 0.10
    assert DIAG.GRADIENT_RATIO == 10.0
    assert DIAG.BETA_STAR == (0.31, 0.60, 1.35, -1.08, -0.891)
    assert DIAG.LINEAR_ARM == "FT-XF-BC"


def test_solver_recovers_an_exactly_representable_vector():
    design = [
        DIAG.tail_basis(belief=belief, period=period)
        for belief in (0.05, 0.2, 0.5, 0.8, 0.95)
        for period in (1, 3, 5, 7, 9)
    ]
    targets = [sum(c * e for c, e in zip(DIAG.BETA_STAR, row)) for row in design]
    beta = DIAG._solve(design, targets)
    assert max(abs(beta[index] - DIAG.BETA_STAR[index]) for index in range(5)) < 1e-9
    assert DIAG._mse_gradient_infinity_norm(design, targets, DIAG.BETA_STAR) < 1e-12


def test_gradient_statistic_is_zero_only_at_the_optimum():
    design = [
        DIAG.tail_basis(belief=belief, period=period)
        for belief in (0.05, 0.2, 0.5, 0.8, 0.95)
        for period in (1, 3, 5, 7, 9)
    ]
    targets = [sum(c * e for c, e in zip(DIAG.BETA_STAR, row)) for row in design]
    displaced = tuple(value + 0.5 for value in DIAG.BETA_STAR)
    assert DIAG._mse_gradient_infinity_norm(design, targets, displaced) > 0.1


def test_gram_spectrum_reports_a_finite_condition_number():
    design = [
        DIAG.tail_basis(belief=belief, period=period)
        for belief in (0.05, 0.2, 0.5, 0.8, 0.95)
        for period in (1, 3, 5, 7, 9)
    ]
    spectrum = DIAG._gram_spectrum(design)
    assert spectrum["gram_smallest_eigenvalue"] > 0
    assert spectrum["gram_condition_number"] > 1.0


def test_oracle_root_vector_is_the_frozen_one():
    actions = DIAG.oracle_root_actions()
    assert sorted(cell for cell, action in actions.items() if action == "PROBE") == [
        "LINKED-p17_20-c9_100"
    ]
    assert len(actions) == 8


def test_implied_root_actions_reproduce_the_oracle_for_exact_coefficients():
    """The root basis can express the oracle values exactly; the reader must then agree."""
    from fractions import Fraction

    from experiments.candidates.ucope.competence_first_scout_r01.contract import CONTEXTS
    from experiments.candidates.ucope.competence_first_scout_r01.oracle import build_oracle, expected_tail

    oracle = build_oracle()
    b0 = Fraction(61, 100)
    b1 = Fraction(81, 100)
    b2 = Fraction(-891, 1000)
    b4 = Fraction(-1)
    severed = next(context for context in CONTEXTS if context[0] == "SEVERED")
    from experiments.candidates.ucope.competence_first_scout_r01.contract import context_id

    b3 = oracle[context_id(severed)]["probe_value"] + severed[2] - b0
    linked = sorted(
        (context for context in CONTEXTS if context[0] == "LINKED" and context[2] == Fraction(9, 100)),
        key=lambda context: context[1],
    )
    values = [
        (context[1], oracle[context_id(context)]["probe_value"] + context[2] - b0 - b3)
        for context in linked
    ]
    (p_low, i_low), (p_high, i_high) = values
    b6 = (i_high - i_low) / (p_high - p_low)
    b5 = i_low - b6 * p_low
    beta_root = [float(value) for value in (b0, b1, b2, b3, b4, b5, b6)]
    assert DIAG._implied_root_actions(beta_root) == DIAG.oracle_root_actions()
    assert float(expected_tail(4, Fraction(1, 2))) == pytest.approx(0.794)


def _x1_rows(*, d_objective, d_learned, g_star, g_learned):
    return {
        "rows": [
            {
                "seed_id": "s",
                "fold_id": fold,
                "d_objective": d_objective,
                "g_star": g_star,
                "published": {
                    "FT-XF-BC": {"d_learned": d_learned, "g_learned": g_learned},
                    "FT-XF-FLEX": {"d_learned": d_learned, "g_learned": g_learned},
                },
            }
            for fold in (0, 1)
        ]
    }


def _x2_rows(*, oracle_match, star_match, published_match):
    return {
        "rows": [
            {
                "sources": {
                    "a_oracle_tail": {"matches_oracle_root_vector": oracle_match},
                    "b_beta_tail_star": {"matches_oracle_root_vector": star_match},
                    "c_published_FT-XF-BC": {"matches_oracle_root_vector": published_match},
                    "c_published_FT-XF-FLEX": {"matches_oracle_root_vector": published_match},
                }
            }
            for _fold in (0, 1)
        ]
    }


def test_reading_rule_d4_fires_first():
    reading = DIAG.apply_reading_rule(
        _x1_rows(d_objective=0.001, d_learned=0.9, g_star=0.001, g_learned=1.0),
        _x2_rows(oracle_match=False, star_match=False, published_match=False),
    )
    assert reading["branch"] == "D4" and reading["label"] == "TARGET_PACKAGE_CEILING"


def test_reading_rule_d1_when_the_objective_optimum_differs():
    reading = DIAG.apply_reading_rule(
        _x1_rows(d_objective=0.5, d_learned=0.9, g_star=0.001, g_learned=1.0),
        _x2_rows(oracle_match=True, star_match=True, published_match=False),
    )
    assert reading["branch"] == "D1"


def test_reading_rule_d2_on_an_optimization_shortfall():
    reading = DIAG.apply_reading_rule(
        _x1_rows(d_objective=0.001, d_learned=0.9, g_star=0.001, g_learned=1.0),
        _x2_rows(oracle_match=True, star_match=True, published_match=False),
    )
    assert reading["branch"] == "D2" and reading["label"] == "OPTIMIZATION_SHORTFALL"
    assert reading["numbers"]["max_d_objective"] == 0.001
    assert reading["numbers"]["max_d_learned_linear_arm"] == 0.9


def test_reading_rule_d3_when_the_tail_is_converged():
    reading = DIAG.apply_reading_rule(
        _x1_rows(d_objective=0.001, d_learned=0.01, g_star=0.001, g_learned=0.002),
        _x2_rows(oracle_match=True, star_match=True, published_match=False),
    )
    assert reading["branch"] == "D3" and reading["label"] == "TAIL_CONVERGED_ROOT_INHERITS"


def test_reading_rule_d5_when_nothing_matches():
    reading = DIAG.apply_reading_rule(
        _x1_rows(d_objective=0.001, d_learned=0.9, g_star=0.001, g_learned=0.0015),
        _x2_rows(oracle_match=True, star_match=True, published_match=True),
    )
    assert reading["branch"] == "D5" and reading["label"] == "NONE_OF_THESE"


def test_root_targets_use_the_odd_training_periods():
    """The frozen package maximises over K_TRAIN, not K_EVAL; the reconstruction must too."""
    from types import SimpleNamespace

    from experiments.candidates.ucope.competence_first_scout_r01.contract import K_TRAIN

    seen = []

    def tail_value(_belief, period):
        seen.append(period)
        return float(period)

    row = SimpleNamespace(behavior_action="PROBE", belief_short=0.5, probe_primitive=-0.25, tail_return=0.0)
    targets = DIAG._root_targets_from_tail([row], tail_value=tail_value)
    assert sorted(set(seen)) == sorted(K_TRAIN)
    assert targets == [-0.25 + float(max(K_TRAIN))]


def test_immediate_rows_keep_their_realized_return_as_target():
    from types import SimpleNamespace

    row = SimpleNamespace(behavior_action="IMMEDIATE", belief_short=0.5, probe_primitive=0.0, tail_return=0.7)
    assert DIAG._root_targets_from_tail([row], tail_value=lambda *_: 99.0) == [0.7]
