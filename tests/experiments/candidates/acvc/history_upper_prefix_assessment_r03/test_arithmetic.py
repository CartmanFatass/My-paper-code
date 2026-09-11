from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

from experiments.candidates.acvc.history_upper_prefix_assessment_r03.arithmetic import (
    prefix_bound, rational, structural_counts, synthetic_inputs,
)


def test_independent_hand_enumeration():
    # One frame, two truths. Before truth is revealed the weighted action tie
    # gives 3/2; after either truth the best joint-mass score is 9/8.
    atoms = ((F(3, 4), F(1, 4)), (F(1, 4), F(3, 4)))
    contexts = ((F(1),), (F(1),))
    scores = (((F(3), F(0)),), ((F(0), F(3)),))
    result = prefix_bound(atoms, contexts, scores, (F(2),), (F(1, 5),), horizon=3, prefix=2)
    assert result == F(6, 5) + F(3, 2) + 2 * F(9, 8) + F(3)


def test_prior_horizon_and_context_factors():
    atoms = ((F(1, 3), F(2, 3)), (F(3, 5), F(2, 5)))
    contexts = ((F(1, 4), F(3, 4)), (F(2, 3), F(1, 3)))
    scores = (((F(-2), F(1)), (F(4), F(2))), ((F(3), F(0)), (F(-1), F(2))))
    prior = (F(2, 7), F(5, 7))
    # Independent Cartesian product calculation, explicitly rebuild each mass.
    expected = 5 * F(3, 11) * F(2, 9)
    for depth in range(3):
        for history in product(range(2), repeat=depth):
            joint = []
            for regime in range(2):
                mass = prior[regime]
                for atom in history:
                    mass *= atoms[regime][atom]
                joint.append(mass)
            for context in range(2):
                expected += max(sum(joint[r] * contexts[r][context] * scores[r][context][a]
                                    for r in range(2)) for a in range(2))
    expected += 2 * sum(prior[r] * contexts[r][c] * max(scores[r][c])
                        for r in range(2) for c in range(2))
    assert prefix_bound(atoms, contexts, scores, (F(3, 11),), (F(2, 9),),
                        prior=prior, horizon=5, prefix=3) == expected


def test_synthetic_normalization_and_static_envelope():
    atoms, contexts, scores, multipliers, budgets = synthetic_inputs()
    assert len(atoms) == len(contexts) == len(scores) == 2
    assert all(len(row) == 24 for row in atoms)
    assert all(len(row) == 12 for row in contexts)
    assert all(len(row) == 12 and all(len(cell) == 3 for cell in row) for row in scores)
    assert len(multipliers) == len(budgets) == 2
    assert all(sum(row) == 1 and all(x > 0 for x in row) for row in atoms + contexts)
    assert all(x > 0 for x in multipliers + budgets)
    assert all(contexts[r][c] == atoms[r][2*c] + atoms[r][2*c+1]
               for r in range(2) for c in range(12))
    exact_width = [x for row in atoms for x in row] + [x for row in scores for cell in row for x in cell]
    exact_width += list(multipliers + budgets)
    all_inputs = exact_width + [x for row in contexts for x in row] + [F(1, 2), F(1, 2)]
    assert all(abs(x.numerator).bit_length() <= 512 and x.denominator.bit_length() <= 512
               for x in all_inputs)
    assert all(x.denominator.bit_length() == 512 for x in exact_width)
    assert rational("a") == rational("a") != rational("b")
    assert structural_counts() == {"histories": 14425, "action_scores": 519300,
                                   "terms_per_score": 2, "tail_scores": 72,
                                   "history_expansions": 14424}


def test_resource_callback_stops_arithmetic():
    import pytest
    calls = []
    def stop():
        calls.append(1)
        raise TimeoutError
    with pytest.raises(TimeoutError):
        prefix_bound(((F(1),),) * 2, ((F(1),),) * 2,
                     (((F(1),),),) * 2, (), (), check=stop)
    assert len(calls) == 1


def test_one_small_publication_smoke(tmp_path):
    root = Path(__file__).resolve().parents[5]
    result = subprocess.run([sys.executable, str(root / "scripts/run_acvc_history_upper_prefix_cost_r03.py"),
                             "--smoke", "--out", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert set(summary) == {"status", "wall_seconds", "peak_rss_bytes", "static_counts"}
    assert summary["status"] == "complete"
    assert summary["wall_seconds"] > 0 and summary["peak_rss_bytes"] > 0
    assert summary["static_counts"]["histories"] == 3
