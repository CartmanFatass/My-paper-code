from __future__ import annotations

import itertools
import math

import pytest
import torch

from experiments.candidates.ucope.paired_branch_credit_b10.credit import (
    factual_surrogate,
    paired_surrogate,
)


@pytest.mark.parametrize("p", [0.1, 0.5, 0.8])
def test_paired_gradient_is_the_expectation_of_two_factual_rollouts(p):
    old = torch.tensor([math.log(p / (1 - p))], dtype=torch.float64, requires_grad=True)
    keep_return, end_return, baseline = 0.43, 0.11, 0.07
    delta = torch.tensor([keep_return - end_return], dtype=torch.float64, requires_grad=True)
    active = torch.tensor([True])
    new = old.detach().clone().requires_grad_()
    objective = paired_surrogate(new, old, delta, active)
    paired_gradient = torch.autograd.grad(objective, new)[0].item()
    expected = p * (1 - p) * (keep_return - end_return)
    assert paired_gradient == pytest.approx(expected, abs=1e-14)
    assert old.grad is None and delta.grad is None
    mean = variance = 0.0
    for first, second in itertools.product((False, True), repeat=2):
        weight = (p if first else 1 - p) * (p if second else 1 - p)
        new = old.detach().clone().requires_grad_()
        objective = factual_surrogate(
            new, old, torch.tensor([[first, second]]),
            torch.tensor([[keep_return if first else end_return,
                           keep_return if second else end_return]], dtype=torch.float64),
            torch.tensor([baseline], dtype=torch.float64), active,
        )
        gradient = torch.autograd.grad(objective, new)[0].item()
        mean += weight * gradient
        variance += weight * (gradient - paired_gradient) ** 2
    assert mean == pytest.approx(paired_gradient, abs=1e-14)
    assert variance > 0


def test_pairing_is_not_a_universal_strict_variance_improvement():
    # For a binary p=.5 decision with exact midpoint baseline and deterministic
    # potential returns, even one factual score is already noise-free.
    old = torch.zeros(1, dtype=torch.float64)
    for keep in (False, True):
        new = old.clone().requires_grad_()
        objective = factual_surrogate(
            new, old, torch.tensor([[keep, keep]]),
            torch.full((1, 2), 0.4 if keep else 0.2, dtype=torch.float64),
            torch.tensor([0.3], dtype=torch.float64), torch.tensor([True]),
        )
        assert torch.autograd.grad(objective, new)[0].item() == pytest.approx(0.05)


def test_inactive_rows_stay_in_denominator_and_last_tick_is_not_special():
    new = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    delta = torch.tensor([0.4, 900.0, -0.2], dtype=torch.float64)
    objective = paired_surrogate(
        new, new.detach(), delta, torch.tensor([True, False, True]), multiplier=15.0,
    )
    gradient = torch.autograd.grad(objective, new)[0]
    torch.testing.assert_close(gradient, torch.tensor([0.5, 0.0, -0.25], dtype=torch.float64))
    # Zero actual branch difference produces zero gradient regardless of state.
    fresh = torch.tensor([0.7], dtype=torch.float64, requires_grad=True)
    zero = paired_surrogate(fresh, fresh.detach(), torch.zeros_like(fresh), torch.tensor([True]))
    assert torch.autograd.grad(zero, fresh)[0].item() == 0.0


def test_clipped_pair_objective_matches_independent_probability_calculation():
    old_p = [0.25, 0.7, 0.5]
    new_p = [0.8, 0.1, 0.9]
    delta = [0.4, -0.7, 0.3]
    logit = lambda probabilities: torch.tensor(
        [math.log(p / (1 - p)) for p in probabilities], dtype=torch.float64
    )
    actual = paired_surrogate(
        logit(new_p), logit(old_p), torch.tensor(delta, dtype=torch.float64),
        torch.ones(3, dtype=torch.bool),
    )
    expected = 0.0
    for before, after, difference in zip(old_p, new_p, delta):
        for mass, ratio, advantage in (
            (before, after / before, (1 - before) * difference),
            (1 - before, (1 - after) / (1 - before), -before * difference),
        ):
            expected += mass * min(ratio * advantage, min(1.2, max(0.8, ratio)) * advantage)
    assert actual.item() == pytest.approx(expected / 3, abs=1e-14)


def test_targets_cannot_backpropagate_and_invalid_probabilities_fail_closed():
    new = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    old = new.detach().clone().requires_grad_()
    returns = torch.tensor([[0.2, 0.4]], dtype=torch.float64, requires_grad=True)
    baseline = torch.tensor([0.1], dtype=torch.float64, requires_grad=True)
    factual_surrogate(new, old, torch.tensor([[False, True]]), returns, baseline,
                      torch.tensor([True])).backward()
    assert old.grad is None and returns.grad is None and baseline.grad is None
    with pytest.raises(ValueError, match="support"):
        paired_surrogate(new, torch.tensor([1000.0], dtype=torch.float64),
                         torch.zeros_like(new), torch.tensor([True]))
    with pytest.raises(ValueError, match="finite"):
        paired_surrogate(new, old, torch.tensor([float("nan")], dtype=torch.float64),
                         torch.tensor([True]))
