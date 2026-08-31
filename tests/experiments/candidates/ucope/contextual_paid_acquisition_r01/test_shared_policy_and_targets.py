from fractions import Fraction

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract
from experiments.candidates.ucope.contextual_paid_acquisition_r01.model import (
    build_shared_model,
    displayed_belief,
    feature_vector,
    validate_shared_model,
)
from experiments.candidates.ucope.contextual_paid_acquisition_r01.oracle import posterior_short
from experiments.candidates.ucope.contextual_paid_acquisition_r01.training import _root_target


torch = pytest.importorskip("torch")


def _context(link="LINKED", reliability=Fraction(17, 20), cost=Fraction(9, 100)):
    return {"link": link, "reliability": reliability, "total_cost": cost}


def test_feature_shape_order_and_context_effects_are_exact():
    assert contract.FEATURE_NAMES == (
        "linked_indicator", "reliability_p", "probe_time_signed", "probe_energy_signed",
        "belief_short", "belief_long", "action_is_probe", "period_over_9", "period_over_9_squared",
    )
    linked = feature_vector(_context(), belief_short=Fraction(3, 4), action_is_probe=False, period=6)
    assert linked == (1.0, 0.85, -0.03, -0.06, 0.75, 0.25, 0.0, 2 / 3, 4 / 9)
    severed = feature_vector(_context("SEVERED", Fraction(13, 20), Fraction(14, 100)), action_is_probe=True, period=0)
    assert severed == (0.0, 0.65, -0.03, -0.11, 0.5, 0.5, 1.0, 0.0, 0.0)
    assert len(linked) == 9


def test_displayed_belief_uses_count_only_when_linked():
    for count in range(7):
        assert displayed_belief("LINKED", Fraction(17, 20), count) == posterior_short(Fraction(17, 20), count)
        assert displayed_belief("SEVERED", Fraction(17, 20), count) == Fraction(1, 2)
    for bad in (-1, 7, True, 1.5):
        with pytest.raises(ValueError):
            displayed_belief("LINKED", Fraction(17, 20), bad)


def test_root_and_tail_architectures_are_shared_fp32_and_exact():
    model = build_shared_model(contract.SEED_SLOTS[0])
    validate_shared_model(model)
    assert set(model._modules) == {"root", "tail"}
    for scorer in (model.root, model.tail):
        linear = [module for module in scorer.modules() if isinstance(module, torch.nn.Linear)]
        assert [(layer.in_features, layer.out_features) for layer in linear] == [(9, 64), (64, 64), (64, 1)]
    assert all(parameter.dtype == torch.float32 for parameter in model.parameters())
    assert all(name.startswith(("root.", "tail.")) for name, _ in model.named_parameters())


def test_fixed_glorot_is_seed_deterministic_and_seed_distinct():
    first = build_shared_model(contract.SEED_SLOTS[0])
    second = build_shared_model(contract.SEED_SLOTS[0])
    other = build_shared_model(contract.SEED_SLOTS[1])
    assert all(torch.equal(first.state_dict()[name], second.state_dict()[name]) for name in first.state_dict())
    assert any(not torch.equal(first.state_dict()[name], other.state_dict()[name]) for name in first.state_dict() if name.endswith("weight"))
    assert all(torch.count_nonzero(value) == 0 for name, value in first.state_dict().items() if name.endswith("bias"))


class _FixedTailModel:
    def score_tail(self, features):
        assert features.dtype == torch.float32
        return torch.tensor([0.1, 0.7, 0.2, 0.4, 0.3], dtype=torch.float32)


def test_fixed_targets_use_unshaped_tail_and_primitive_probe_ledger_only():
    immediate = {"root_action": "IMMEDIATE", "tail_return": 0.375, "unshaped_return": 999.0}
    assert _root_target(_FixedTailModel(), immediate, _context()) == 0.375
    probe = {
        "root_action": "PROBE", "link": "LINKED", "reliability": "17/20",
        "displayed_short_count": 4, "tail_return": -999.0, "unshaped_return": 888.0,
        "primitive_ledger": {"probe_service": 0.04, "probe_time": -0.03, "probe_energy": -0.06},
    }
    expected = 0.04 - 0.03 - 0.06 + float(torch.tensor(0.7, dtype=torch.float32))
    assert _root_target(_FixedTailModel(), probe, _context()) == pytest.approx(expected, abs=0.0)


def test_feature_and_model_validation_fail_closed():
    with pytest.raises(ValueError):
        feature_vector(_context(), action_is_probe=True, period=1)
    with pytest.raises(ValueError):
        feature_vector(_context(), belief_short=1.01, action_is_probe=False, period=1)
    with pytest.raises(ValueError):
        feature_vector(_context(), action_is_probe=False, period=10)

    class Leaky(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.root = torch.nn.Linear(9, 1)
            self.tail = torch.nn.Linear(9, 1)
            self.context_replica = torch.nn.Linear(9, 1)

    with pytest.raises(ValueError):
        validate_shared_model(Leaky())
