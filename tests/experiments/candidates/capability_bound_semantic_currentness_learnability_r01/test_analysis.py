import math

import pytest

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.analysis import (
    DELTA, reduce_finite_panel, select_branch,
)


def _panel(vector):
    return reduce_finite_panel([tuple(map(float, vector)) for _ in range(24)])


def test_exact_finite_descriptors_have_no_sampling_outputs() -> None:
    vectors = [(block / 100.0, -block / 200.0, (block - 12) / 50.0) for block in range(24)]
    decision = reduce_finite_panel(vectors)
    assert decision.block_count == 24
    assert decision.descriptors[0].minimum == 0
    assert decision.descriptors[0].maximum == pytest.approx(0.23)
    assert decision.descriptors[0].range == pytest.approx(0.23)
    assert decision.descriptors[0].mean == pytest.approx(0.115)


def test_finite_panel_rejects_missing_replaced_or_nonexact_input() -> None:
    with pytest.raises(ValueError, match="24 complete"):
        reduce_finite_panel([(0.0,) * 3] * 23)
    with pytest.raises(TypeError, match="float64"):
        reduce_finite_panel([(0, 0, 0)] * 24)


def test_exact_branch_precedence_and_literals() -> None:
    positive = _panel((DELTA + 0.01,) * 3)
    assert select_branch(positive, valid=False, raw_competent=False, no_resolvable_headroom=True,
                         structured_endpoint_gate=True) == "INVALID"
    assert select_branch(positive, valid=True, raw_competent=False, no_resolvable_headroom=True,
                         structured_endpoint_gate=True) == "RAW_INCOMPETENT"
    assert select_branch(positive, valid=True, raw_competent=True, no_resolvable_headroom=True,
                         structured_endpoint_gate=True) == "NO_RESOLVABLE_HEADROOM"
    assert select_branch(positive, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=True) == "VALID_NARROW_CBSC_INDUCTIVE_BIAS"
    generic = _panel((DELTA + 1, DELTA, DELTA + 1))
    assert select_branch(generic, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "GENERIC_FACTORIZATION_OR_CONDITIONING"
    no_specific = _panel((DELTA + 1, DELTA + 1, DELTA))
    assert select_branch(no_specific, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "NO_CAPABILITY_SPECIFIC_ATTRIBUTION"
    equivalent = _panel((DELTA, -DELTA, 0))
    assert select_branch(equivalent, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "PRACTICAL_EQUIVALENCE"
    superior = _panel((-DELTA - 1, 0, 0))
    assert select_branch(superior, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "RAW_OR_SHAM_MATERIALLY_SUPERIOR"


def test_strict_float64_decision_boundaries() -> None:
    at = _panel((DELTA, DELTA, DELTA))
    assert select_branch(at, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=True) == "PRACTICAL_EQUIVALENCE"
    above = math.nextafter(DELTA, math.inf)
    positive = _panel((above, above, above))
    assert select_branch(positive, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=True) == "VALID_NARROW_CBSC_INDUCTIVE_BIAS"
    edge = reduce_finite_panel([(-DELTA, DELTA, 0.0)] * 24)
    assert select_branch(edge, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "PRACTICAL_EQUIVALENCE"
    at_superior = _panel((-DELTA, 0.0, 0.0))
    assert select_branch(at_superior, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "PRACTICAL_EQUIVALENCE"
    strict = _panel((math.nextafter(-DELTA, -math.inf), 0.0, 0.0))
    assert select_branch(strict, valid=True, raw_competent=True, no_resolvable_headroom=False,
                         structured_endpoint_gate=False) == "RAW_OR_SHAM_MATERIALLY_SUPERIOR"
