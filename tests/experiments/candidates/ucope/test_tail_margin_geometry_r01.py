"""Tests for the outcome-free margin geometry of ``UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01``.

The geometry is exact algebra on a linear score, so these tests check the algebra rather than a
tolerance: the basis reproduces the oracle's tail values, the flip radius is the stated ratio,
the top-two gap is exactly linear in the coefficients (so the directional derivative is not an
approximation), and the tail geometry cannot depend on the probe cost.
"""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    CONTEXTS,
    K_EVAL,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import tail_basis  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    expected_tail,
    optimal_tail,
)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = _load("ucope_tail_margin_geometry_r01", "run_ucope_tail_margin_geometry_r01.py")


@pytest.fixture(scope="module")
def truth():
    return GEOMETRY.truth_geometry()


def test_the_object_is_outcome_free_and_declared_a_recon():
    assert GEOMETRY.OBJECT_ID == "UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01"
    assert GEOMETRY.EVIDENCE_CLASS == "A/RECON"
    assert GEOMETRY.BETA_STAR == (0.31, 0.60, 1.35, -1.08, -0.891)
    assert GEOMETRY.TARGET_CONTEXT_ID == "LINKED-p17_20-c9_100"
    assert GEOMETRY.AGREEMENT_GATE == Fraction(19, 20)
    source = (PROJECT_ROOT / "scripts/run_ucope_tail_margin_geometry_r01.py").read_text(
        encoding="utf-8")
    for forbidden in ("optimizer_for", "train_stage", "_step", "execute_policy_episode",
                      "evaluate_policy"):
        assert forbidden not in source, forbidden


def test_the_grid_is_every_context_and_forced_probe_belief():
    cells = list(GEOMETRY.belief_grid())
    assert len(cells) == len(CONTEXTS) * 7 == 56
    assert {cell for cell, *_ in cells} == {context_id(context) for context in CONTEXTS}
    masses = {}
    for cell, _context, _count, _belief, mass in cells:
        masses[cell] = masses.get(cell, Fraction(0)) + mass
    for total in masses.values():
        assert total == Fraction(1), "the belief masses of one context must sum to one"


def test_the_frozen_basis_reproduces_the_oracle_tail_values_exactly(truth):
    worst = max(
        row["basis_score_vs_expected_tail_max_abs"]
        for context in truth["contexts"].values() for row in context["cells"].values())
    assert worst < 1e-12
    assert all(context["basis_exact_everywhere"] for context in truth["contexts"].values())


def test_the_basis_argmax_is_the_oracle_period_at_every_cell(truth):
    for context in truth["contexts"].values():
        for row in context["cells"].values():
            assert row["basis_argmax_period"] == row["oracle_period"]
            assert row["oracle_period"] in K_EVAL
            assert optimal_tail(K_EVAL, Fraction(row["belief"]).limit_denominator(10 ** 9))[0] \
                in K_EVAL


def test_the_flip_radius_is_the_stated_ratio():
    belief = Fraction(3, 100000)
    geometry = GEOMETRY.cell_geometry(belief, GEOMETRY.BETA_STAR)
    top = geometry["argmax_period"]
    binding = geometry["flip_binding_period"]
    z_top = numpy.asarray(tail_basis(belief=float(belief), period=top))
    z_bind = numpy.asarray(tail_basis(belief=float(belief), period=binding))
    scores = geometry["scores"]
    expected = (scores[str(top)] - scores[str(binding)]) / numpy.linalg.norm(z_top - z_bind)
    assert geometry["flip_radius_l2"] == pytest.approx(expected, rel=1e-12)
    assert geometry["top_two_gap"] > 0.0


def test_the_top_two_gap_is_exactly_linear_in_the_coefficients():
    """So the directional derivative is exact algebra, not a first-order approximation."""
    belief = Fraction(3, 100000)
    star = numpy.asarray(GEOMETRY.BETA_STAR)
    base = GEOMETRY.cell_geometry(belief, star)
    top, competitor = base["argmax_period"], base["flip_binding_period"]
    rng = numpy.random.default_rng(20260903)
    for _ in range(8):
        error = rng.normal(size=5) * 0.05
        norm = float(numpy.linalg.norm(error))
        derivative = GEOMETRY.directional_derivative(belief, top, competitor, error / norm)
        moved = GEOMETRY.cell_geometry(belief, star + error)
        actual_gap = moved["scores"][str(top)] - moved["scores"][str(competitor)]
        assert actual_gap == pytest.approx(
            base["top_two_gap"] + derivative * norm, rel=1e-9, abs=1e-15)


def test_the_tail_geometry_cannot_depend_on_the_probe_cost(truth):
    """The frozen tail basis is (1, b, k, b*k, k^2): no cost term, so cost twins must tie."""
    by_stratum: dict[tuple[str, str], list[str]] = {}
    for context in CONTEXTS:
        link, p, _cost = context
        by_stratum.setdefault((link, str(p)), []).append(context_id(context))
    assert len(by_stratum) == 4
    for cells in by_stratum.values():
        assert len(cells) == 2
        first, second = (truth["contexts"][cell] for cell in cells)
        assert first["minimum_flip_radius_l2"] == second["minimum_flip_radius_l2"]
        assert first["minimum_top_two_gap"] == second["minimum_top_two_gap"]


def test_the_target_context_stratum_is_the_most_fragile(truth):
    ranking = truth["fragility_ranking"]
    assert ranking[0] == GEOMETRY.TARGET_CONTEXT_ID
    assert truth["target_context_rank"] == 1
    # It ties with its cost twin, and the pair is strictly tighter than every other stratum.
    tight = truth["contexts"][GEOMETRY.TARGET_CONTEXT_ID]["minimum_flip_radius_l2"]
    others = [truth["contexts"][cell]["minimum_flip_radius_l2"] for cell in ranking[2:]]
    assert truth["contexts"]["LINKED-p17_20-c7_50"]["minimum_flip_radius_l2"] == tight
    assert min(others) > tight


def test_the_published_reference_is_validated(tmp_path):
    with pytest.raises(GEOMETRY.RefusedComputation, match="record missing"):
        GEOMETRY.published_coefficients(tmp_path / "absent.json")
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"object_id": "OTHER", "policies": []}), encoding="utf-8")
    with pytest.raises(GEOMETRY.RefusedComputation, match="not the competence run record"):
        GEOMETRY.published_coefficients(wrong)


def _reference(path: Path, beta) -> Path:
    path.write_text(json.dumps({
        "object_id": "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01",
        "policies": [{
            "seed_id": "seed", "fold_id": 0,
            "beta_tail_star": list(GEOMETRY.BETA_STAR),
            "arms": {"WHITENED-10X": {
                "beta_tail": list(beta),
                "d_learned_tail": 0.0,
                "competence": {"minimum_tail_agreement": 1.0},
            }},
        }],
    }), encoding="utf-8")
    return path


def test_a_vector_equal_to_beta_star_flips_nothing(tmp_path):
    path = GEOMETRY.run_geometry(tmp_path / "run",
                                 _reference(tmp_path / "ref.json", GEOMETRY.BETA_STAR))
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    assert record["evidence_class"] == "A/RECON"
    assert record["admission"]["passed"] is True
    vector = record["policies"][0]["vectors"]["WHITENED-10X"]
    assert vector["coefficient_error_l2"] == 0.0
    assert vector["total_flipped_cells"] == 0
    assert vector["minimum_agreement"] == 1.0
    assert vector["contexts_below_gate"] == 0
    assert len(record["truth_geometry"]["contexts"]) == 8


def test_an_error_past_the_tight_cells_flip_radius_costs_the_agreement_gate(tmp_path):
    """A perturbation along the binding direction at the tightest cell must break the gate."""
    truth = GEOMETRY.truth_geometry()
    cell = truth["contexts"][GEOMETRY.TARGET_CONTEXT_ID]["cells"]["0"]
    direction = numpy.asarray(GEOMETRY.cell_geometry(
        Fraction(3, 100000), GEOMETRY.BETA_STAR)["flip_direction_unit"])
    beta = numpy.asarray(GEOMETRY.BETA_STAR) + direction * (cell["flip_radius_l2"] * 1.5)
    path = GEOMETRY.run_geometry(tmp_path / "run", _reference(tmp_path / "ref.json", beta))
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    vector = record["policies"][0]["vectors"]["WHITENED-10X"]
    assert vector["total_flipped_cells"] > 0
    assert vector["minimum_agreement"] < 1.0
    assert vector["contexts_below_gate"] >= 1


def test_the_output_root_is_create_once(tmp_path):
    (tmp_path / "taken").mkdir()
    with pytest.raises(GEOMETRY.RefusedComputation, match="create-once"):
        GEOMETRY.run_geometry(tmp_path / "taken")


def test_every_held_out_decision_direction_has_a_training_support_witness():
    """z(b, j) - z(b, j+2) == (z(b, j-1) - z(b, j+3)) / 2, exactly, at every belief."""
    identity = GEOMETRY.held_out_direction_identity()
    assert identity["witness_pairs"] == [[1, 5], [3, 7], [5, 9]]
    assert identity["maximum_identity_error"] < 1e-15
    assert len(identity["cells"]) == 8 * 7 * (len(K_EVAL) - 1)
    for row in identity["cells"]:
        assert set(row["training_witness_pair"]) <= {1, 3, 5, 7, 9}
        assert set(row["held_out_pair"]) <= set(K_EVAL)
        assert row["training_direction_norm"] == pytest.approx(
            2.0 * row["held_out_direction_norm"], rel=1e-12)
