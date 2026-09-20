"""Independent exact-enumeration and Gaussian-moment checks; no native runs."""
from fractions import Fraction as F
from itertools import product
import math

import pytest
import torch

from tools.analysis.temporal_alignment_identification import (
    GateCell, ar1_delayed_reward_gradient, canonical_examples, decision_values,
)


@pytest.mark.parametrize("name, total, fresh, retained", [
    ("new_observation", F(1, 2), F(1, 2), F(0)),
    ("previous_command", F(1, 2), F(0), F(1, 2)),
    ("mixed", F(1, 2), F(1, 4), F(1, 4)),
    ("cancellation", F(0), F(1, 4), F(-1, 4)),
])
def test_known_exact_components_with_identical_end_rates(name, total, fresh, retained):
    values = decision_values(canonical_examples()[name])
    assert values["end_rate"] == F(1, 2)
    assert values["total_gap"] == total
    assert values["new_observation_component"] == fresh
    assert values["retained_component"] == retained
    assert total == fresh + retained


@pytest.mark.parametrize("name", list(canonical_examples()))
def test_direct_pair_and_branch_enumeration_matches_calendar_gap(name):
    cells = canonical_examples()[name]
    gap, probability = F(0), F(0)
    for left, right in product(cells, repeat=2):
        for b_left, b_right in product((0, 1), repeat=2):
            p_left = left.end_probability if b_left else 1 - left.end_probability
            p_right = right.end_probability if b_right else 1 - right.end_probability
            weight = left.probability * right.probability * p_left * p_right
            own_returns = b_left * left.advantage + b_right * right.advantage
            exchanged_returns = b_right * left.advantage + b_left * right.advantage
            gap += weight * (own_returns - exchanged_returns) / 2
            probability += weight
    assert probability == 1
    assert gap == decision_values(cells)["total_gap"]


def test_unequal_context_masses_require_conditional_weighting():
    cells = (
        GateCell(0, 0, F(1, 2), F(0), F(-1)),
        GateCell(0, 1, F(1, 4), F(1), F(2)),
        GateCell(1, 0, F(1, 4), F(1, 2), F(1)),
    )
    values = decision_values(cells)
    assert values["end_rate"] == F(3, 8)
    assert values["online"] == F(5, 8)
    assert values["independent_calendar"] == F(3, 32)
    assert values["retained_only"] == F(1, 8)
    assert values["new_observation_component"] == F(1, 2)
    assert values["retained_component"] == F(1, 32)
    assert values["total_gap"] == F(17, 32)


def test_covariance_identity_does_not_need_independence_of_old_and_new_information():
    cells = (
        GateCell(0, 0, F(1, 2), F(1, 5), F(-2)),
        GateCell(0, 1, F(1, 4), F(4, 5), F(3)),
        GateCell(1, 0, F(1, 4), F(2, 3), F(1)),
    )
    expected_p = sum(c.probability * c.end_probability for c in cells)
    expected_a = sum(c.probability * c.advantage for c in cells)
    expected_product = sum(c.probability * c.end_probability * c.advantage for c in cells)
    values = decision_values(cells)
    assert values["total_gap"] == expected_product - expected_p * expected_a
    assert values["total_gap"] == values["new_observation_component"] + values["retained_component"]


@pytest.mark.parametrize("cells", [
    (), (GateCell(0, 0, F(1, 2), F(1, 2), F(1)),),
    (GateCell(0, 0, F(1), F(2), F(1)),),
    (GateCell(0, 0, F(1), F(-1), F(1)),),
    (GateCell(0, 0, F(0), F(0), F(0)), GateCell(1, 0, F(1), F(0), F(0))),
])
def test_invalid_populations_are_rejected(cells):
    with pytest.raises(ValueError):
        decision_values(cells)


def test_float_inputs_do_not_silently_become_exact_rationals():
    with pytest.raises(TypeError):
        decision_values([GateCell(0, 0, 1.0, F(1, 2), F(1))])


@pytest.mark.parametrize("rho", [F(0), F(3, 5), F(-3, 5)])
def test_conditional_gaussian_autograd_matches_exact_moments(rho):
    # Two-node Gaussian quadrature in each independent standard normal is exact
    # for these degree-two reward-times-score expectations. These four nodes
    # are integration points, not a replacement discrete behavior density.
    r, innovation_std = float(rho), math.sqrt(1 - float(rho) ** 2)
    actions = torch.tensor([(e0, r * e0 + innovation_std * e1)
                            for e0, e1 in product((-1., 1.), repeat=2)], dtype=torch.float64)
    means = torch.zeros(2, dtype=torch.float64, requires_grad=True)
    first = torch.distributions.Normal(means[0], 1.).log_prob(actions[:, 0])
    conditional_mean = means[1] + r * (actions[:, 0] - means[0])
    second = torch.distributions.Normal(conditional_mean, innovation_std).log_prob(actions[:, 1])
    correct_gradient = torch.autograd.grad((actions[:, 0] * (first + second)).mean(), means)[0]
    marginal_logp = torch.distributions.Normal(means, torch.ones_like(means)).log_prob(actions).sum(-1)
    wrong_gradient = torch.autograd.grad((actions[:, 0] * marginal_logp).mean(), means)[0]
    exact = ar1_delayed_reward_gradient(rho)
    torch.testing.assert_close(correct_gradient, torch.tensor([float(x) for x in exact["correct"]],
                                                             dtype=torch.float64), rtol=0, atol=1e-12)
    torch.testing.assert_close(wrong_gradient, torch.tensor([float(x) for x in exact["independent_marginal"]],
                                                           dtype=torch.float64), rtol=0, atol=1e-12)
    assert exact["correct"] == (F(1), F(0))
    assert exact["independent_marginal"] == (F(1), rho)


@pytest.mark.parametrize("rho", [F(-1), F(1), F(2)])
def test_singular_or_nonstationary_noise_is_rejected(rho):
    with pytest.raises(ValueError):
        ar1_delayed_reward_gradient(rho)
