from __future__ import annotations

import pytest
import torch

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
