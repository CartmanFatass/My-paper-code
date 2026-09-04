"""Unit checks for the UCOPE optimiser-and-conditioning object's own machinery.

The object decides a branch, so its batch indexing, its whitening contract, its
reparameterisation algebra, its exact solve and its five-branch reading rule are pinned here
on inputs whose answers are known in closed form. These tests train no scientific arm.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT = PROJECT_ROOT / "scripts" / "run_ucope_optimiser_conditioning_r01.py"


def _load():
    spec = importlib.util.spec_from_file_location("ucope_optimiser_conditioning", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OBJ = _load()


def test_frozen_constants_match_the_card():
    assert OBJ.ARM_ID == "FT-XF-BC"
    assert OBJ.BASE_UPDATES == 160
    assert OBJ.EXTENDED_UPDATES == 1_600
    assert OBJ.LEARNING_RATE == 3e-3
    assert OBJ.BATCH_SIZE == 256
    assert OBJ.EPS_L == 0.10
    assert OBJ.RHO == 5.0
    assert OBJ.CHOLESKY_TOLERANCE == 1e-10
    assert OBJ.MINIMUM_GRAM_EIGENVALUE == 1e-6
    assert OBJ.BETA_STAR == (0.31, 0.60, 1.35, -1.08, -0.891)


def test_base_budget_is_the_frozen_rung_one_configuration():
    from experiments.candidates.ucope.competence_first_scout_r01.contract import ScoutConfig

    config = ScoutConfig.ladder_rung_1()
    assert config.tail_updates == OBJ.BASE_UPDATES
    assert config.learning_rate == OBJ.LEARNING_RATE
    assert config.batch_size == OBJ.BATCH_SIZE


def test_cyclic_indices_match_the_frozen_batch_schedule():
    """The precomputed-tensor path must select exactly the rows training._cyclic_batch does."""
    from experiments.candidates.ucope.competence_first_scout_r01.training import _cyclic_batch

    rows = tuple(range(1_000))
    for update in (0, 1, 3, 7, 159, 1_599):
        expected = list(_cyclic_batch(rows, update, OBJ.BATCH_SIZE))
        assert OBJ._cyclic_indices(len(rows), update, OBJ.BATCH_SIZE) == expected


def test_whitening_contract_accepts_a_well_conditioned_design():
    numpy = pytest.importorskip("numpy")
    generator = numpy.random.default_rng(0)
    design = generator.normal(size=(4_000, 5))
    white = OBJ.whitening(design)
    assert white["source"] == "training_rows_only"
    assert white["cholesky_reconstruction_max_abs"] <= OBJ.CHOLESKY_TOLERANCE
    assert white["gram_smallest_eigenvalue"] > OBJ.MINIMUM_GRAM_EIGENVALUE
    factor = white["_factor"]
    gram = design.T @ design / design.shape[0]
    assert float(numpy.abs(factor @ factor.T - gram).max()) <= OBJ.CHOLESKY_TOLERANCE


def test_whitening_refuses_a_rank_deficient_design():
    numpy = pytest.importorskip("numpy")
    generator = numpy.random.default_rng(1)
    design = generator.normal(size=(4_000, 5))
    design[:, 4] = design[:, 3]  # exact collinearity
    with pytest.raises(OBJ.LaunchRefusal):
        OBJ.whitening(design)


def test_whitening_actually_whitens_and_preserves_the_prediction():
    numpy = pytest.importorskip("numpy")
    generator = numpy.random.default_rng(2)
    design = generator.normal(size=(4_000, 5)) @ numpy.diag([1.0, 4.0, 0.2, 9.0, 0.5])
    white = OBJ.whitening(design)
    factor, inverse = white["_factor"], white["_inverse"]
    whitened = design @ inverse.T
    identity = whitened.T @ whitened / whitened.shape[0]
    assert float(numpy.abs(identity - numpy.eye(5)).max()) < 1e-8
    beta = numpy.array(OBJ.BETA_STAR)
    beta_tilde = factor.T @ beta
    assert float(numpy.abs(whitened @ beta_tilde - design @ beta).max()) < 1e-9
    assert float(numpy.abs(numpy.linalg.solve(factor.T, beta_tilde) - beta).max()) < 1e-12


def test_exact_solve_recovers_an_exactly_representable_vector():
    numpy = pytest.importorskip("numpy")
    from experiments.candidates.ucope.competence_first_scout_r01.model import tail_basis

    design = numpy.array(
        [tail_basis(belief=b, period=k) for b in (0.05, 0.2, 0.5, 0.8, 0.95) for k in (1, 3, 5, 7, 9)],
        dtype=numpy.float64,
    )
    targets = design @ numpy.array(OBJ.BETA_STAR)
    beta = OBJ.exact_solve(design, targets)
    assert float(numpy.abs(beta - numpy.array(OBJ.BETA_STAR)).max()) < 1e-9
    assert OBJ.gradient_infinity_norm(design, targets, OBJ.BETA_STAR) < 1e-12


def _policies(*, raw_base, whitened_base, raw_10x, whitened_10x):
    rows = []
    for index in range(6):
        rows.append({
            "arms": {
                "RAW": {"d_learned": {"160": raw_base[index], "1600": raw_10x[index]}},
                "WHITENED": {"d_learned": {"160": whitened_base[index], "1600": whitened_10x[index]}},
            }
        })
    return rows


def test_rule_o_a_when_whitening_closes_it_at_the_base_budget():
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[0.01] * 6, raw_10x=[1.0] * 6, whitened_10x=[0.001] * 6,
    ))
    assert reading["branch"] == "O-A" and reading["label"] == "CONDITIONING_CLOSES_IT"


def test_rule_o_b_when_whitening_mostly_closes_it():
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[0.3] * 6, raw_10x=[1.0] * 6, whitened_10x=[0.02] * 6,
    ))
    assert reading["branch"] == "O-B"
    assert reading["numbers"]["median_reduction_met"] is True


def test_rule_o_c_when_only_the_budget_closes_it():
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[1.9] * 6, raw_10x=[0.01] * 6, whitened_10x=[0.01] * 6,
    ))
    assert reading["branch"] == "O-C" and reading["label"] == "BUDGET_CLOSES_IT_NOT_CONDITIONING"


def test_rule_o_d_when_nothing_closes_it():
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[1.9] * 6, raw_10x=[0.5] * 6, whitened_10x=[0.4] * 6,
    ))
    assert reading["branch"] == "O-D" and reading["label"] == "NEITHER_CLOSES_IT"


def test_rule_o_e_on_a_mixed_picture():
    """Reduction met, whitened 10x still short, raw 10x closes: no branch covers that."""
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[0.3] * 6, raw_10x=[0.01] * 6, whitened_10x=[0.5] * 6,
    ))
    assert reading["branch"] == "O-E" and reading["label"] == "UNCLEAR"


def test_rule_is_evaluated_in_the_stated_order():
    """O-A precedes O-B: a run that satisfies both conditions is reported as O-A."""
    reading = OBJ.apply_reading_rule(_policies(
        raw_base=[2.0] * 6, whitened_base=[0.01] * 6, raw_10x=[1.0] * 6, whitened_10x=[0.001] * 6,
    ))
    assert reading["branch"] == "O-A"
    assert reading["numbers"]["median_reduction_met"] is True


def test_median_helper_is_the_even_length_average():
    assert OBJ._median([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert OBJ._median([5.0, 1.0, 3.0]) == 3.0
