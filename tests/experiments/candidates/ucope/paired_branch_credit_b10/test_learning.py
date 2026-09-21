from __future__ import annotations

import pytest
import torch

from experiments.candidates.ucope.frozen_mean_gate_b08.engine import Gate as RichGate
from experiments.candidates.ucope.normalized_distance_gate_b09.gate import Gate
from experiments.candidates.ucope.paired_branch_credit_b10.collection import FocalCase
from experiments.candidates.ucope.paired_branch_credit_b10.learning import update_pairs


class RecordingOptimizer:
    """Capture step calls/gradients without changing any weights or optimizer state."""

    def __init__(self, parameter):
        self.parameter = parameter
        self.gradients = []

    def zero_grad(self, set_to_none):
        assert set_to_none
        self.parameter.grad = None

    def step(self):
        self.gradients.append(self.parameter.grad.item())


def _pair(active, keep_return=0.21, end_return=0.20):
    return dict(
        mode="paired", case=FocalCase(1, 0), eligible=active,
        sampled_keep=torch.tensor([True, False] if active else [False, False]),
        suffix_returns=torch.tensor([keep_return, end_return], dtype=torch.float64),
        context=torch.zeros(5, 175), old_logits=torch.zeros(5),
    )


def test_four_updates_use_fp64_difference_and_full_schedule_denominator_without_a_fit():
    gate = Gate("scalar", seed=7, median=0.0, scale=1.0)
    optimizer = RecordingOptimizer(gate.b0)
    counts = {}
    metrics = update_pairs(
        gate, optimizer, [_pair(True), _pair(False, 0.2, 0.2)], horizon=2,
        check=lambda: None, counts=counts,
    )
    assert counts == {"gate_optimizer_steps": 4} and len(metrics) == 4
    # Maximize 5 * p(1-p) * .01 / 2; the optimizer sees the loss's minus sign.
    assert optimizer.gradients == pytest.approx([-0.00625] * 4)
    assert gate.b0.item() == 0.0  # Mock calls did not perform an actual optimizer update.


def test_update_rejects_fake_pairs_before_any_optimizer_step():
    gate = Gate("scalar", seed=7, median=0.0, scale=1.0)
    optimizer = RecordingOptimizer(gate.b0)
    pair = _pair(True)
    pair["sampled_keep"] = torch.tensor([True, True])
    with pytest.raises(ValueError, match="branch identities"):
        update_pairs(gate, optimizer, [pair], horizon=2, check=lambda: None, counts={})
    assert optimizer.gradients == []


def test_subtraction_precedes_fp32_conversion_even_when_each_return_rounds_the_same():
    gate = Gate("scalar", seed=7, median=0.0, scale=1.0)
    optimizer = RecordingOptimizer(gate.b0)
    active = _pair(True, 0.2 + 1e-10, 0.2)
    returns = active["suffix_returns"]
    assert returns.float()[0] == returns.float()[1]
    delta = float(returns[0] - returns[1])
    update_pairs(gate, optimizer, [active, _pair(False, 0.2, 0.2)], horizon=2,
                 check=lambda: None, counts={})
    assert all(gradient < 0 for gradient in optimizer.gradients)
    assert optimizer.gradients == pytest.approx([-5 * 0.25 * delta / 2] * 4,
                                                rel=1e-6, abs=1e-16)
    assert gate.b0.item() == 0.0


def test_rich_gate_routes_credit_to_each_pairs_actual_focal_agent_without_a_fit():
    gate = RichGate("contextual", seed=17)
    pairs = [_pair(True, 0.201, 0.2), _pair(True, 0.198, 0.2)]
    pairs[0]["case"] = FocalCase(1, 3)
    pairs[1]["case"] = FocalCase(1, 1)
    pairs[0]["context"] = torch.linspace(-0.2, 0.3, 5 * 175).reshape(5, 175)
    pairs[1]["context"] = torch.linspace(0.3, -0.4, 5 * 175).reshape(5, 175)
    before = {name: value.clone() for name, value in gate.state_dict().items()}
    parameters = list(gate.parameters())
    logits = gate(torch.stack([pair["context"] for pair in pairs]))
    deltas = [(pair["suffix_returns"][0] - pair["suffix_returns"][1]).float()
              for pair in pairs]
    # Independent first-update derivative: p=.5, so d/dlogit is delta / 4.
    linearized_loss = -5 * 0.25 * (deltas[0] * logits[0, 3] + deltas[1] * logits[1, 1]) / 2
    expected = torch.autograd.grad(linearized_loss, parameters)
    assert torch.linalg.vector_norm(torch.cat([value.flatten() for value in expected])) < 0.5
    assert any(bool(value.abs().sum()) for value in expected[2:])

    class RecordAll:
        def __init__(self):
            self.calls = []

        def zero_grad(self, set_to_none):
            assert set_to_none
            for parameter in parameters:
                parameter.grad = None

        def step(self):
            self.calls.append(tuple(parameter.grad.clone() for parameter in parameters))

    optimizer = RecordAll()
    update_pairs(gate, optimizer, pairs, horizon=2, check=lambda: None, counts={})
    assert len(optimizer.calls) == 4
    for gradients in optimizer.calls:
        for actual, wanted in zip(gradients, expected):
            torch.testing.assert_close(actual, wanted, rtol=2e-6, atol=1e-9)
    for name, value in gate.state_dict().items():
        assert torch.equal(value, before[name])
