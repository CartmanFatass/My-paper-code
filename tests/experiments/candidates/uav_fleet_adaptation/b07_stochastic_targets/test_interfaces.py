"""Synthetic cache/RNG/direct-law integration; no canonical input is opened."""
import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import policies
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.contract import ARMS, FROZEN


class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward(self, x, n):
        assert x.dtype == torch.float32 and x.shape == (1, 114)
        assert n.tolist() == [5]
        self.calls += 1
        return torch.arange(27, dtype=torch.float32).reshape(1, 27) / 11


def observation():
    row = np.zeros(104, dtype=np.float32)
    row[:3] = [.37, .62, .45]
    return row


@pytest.mark.parametrize("arm", ["P0", "Bstar0", "Tdirect", "Hdirect"])
def test_cache_hit_keeps_fresh_uniform_and_own_nav(arm):
    actor = Actor()
    policy = policies.Policy(arm, actor, world=103, agent=2, sampling_root=105)
    obs = observation()
    before = torch.random.get_rng_state().clone()
    first = policy.query(obs, 0, 0)
    obs[-1] = 4 / 256
    second = policy.query(obs, 4, 0)
    assert actor.calls == 1
    assert not first["memo_hit"] and second["memo_hit"]
    assert first["innovation"] != second["innovation"]
    for tick, answer in ((0, first), (4, second)):
        expected = np.random.default_rng(np.random.SeedSequence([105, 103, tick, 2])).random()
        assert answer["innovation"] == expected
        cumulative = np.cumsum(answer["probabilities"]); cumulative[-1] = 1
        assert answer["action_index"] == np.searchsorted(cumulative, expected, side="right")
        np.testing.assert_array_equal(answer["command"], policies.COMMANDS[answer["action_index"]])
    np.testing.assert_array_equal(first["logits"], second["logits"])
    assert policy.counters["sampled_draws"] == 2
    policy.query(obs, 8, 1)
    assert actor.calls == 2 and policy.counters["misses"] == 2
    assert torch.equal(before, torch.random.get_rng_state())


def test_direct_reuses_c_features_and_flat_t_is_exact(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("direct programs must not instantiate StudentPolicy/helper")
    monkeypatch.setattr(policies, "StudentPolicy", forbidden)
    actor = Actor()
    policy = policies.Policy("Tdirect", actor, world=1001, agent=0, sampling_root=7)
    result = policy.query(observation(), 0, 3)
    assert result["fallback"] and np.all(result["scores"] == 0)
    assert result["probabilities"].tobytes() == result["parent_probabilities"].tobytes()
    assert policy.counters["helper_calls"] == 0
    assert policy.counters["neural_rows"] == 1 and policy.counters["target_vectors"] == 2


def test_direct_h_includes_c_fallback_choice():
    policy = policies.Policy("Hdirect", Actor(), world=1001, agent=0, sampling_root=7)
    result = policy.query(observation(), 0, 3)
    expected = .9 * result["parent_probabilities"]
    expected[result["c_index"]] += .1
    np.testing.assert_array_equal(result["probabilities"], expected)


@pytest.mark.parametrize("arm,epsilon", [("C", 0), ("Q10", .1), ("Q05", .05), ("G", .1)])
def test_ordinary_zero_support_laws(arm, epsilon):
    policy = policies.Policy(arm, None, world=1003, agent=1, sampling_root=None if arm == "C" else 9)
    result = policy.query(observation(), 0, 1)
    p = np.full(27, epsilon / 26.)
    p[result["c_index"]] = 1 - epsilon
    np.testing.assert_array_equal(result["probabilities"], p)
    assert policy.counters["neural_rows"] == 0
    assert policy.counters["sampled_draws"] == int(arm != "C")


def test_arm_rights_and_complete_cyclic_pairing():
    with pytest.raises(ValueError):
        policies.Policy("C", Actor(), world=1, agent=0, sampling_root=None)
    with pytest.raises(ValueError):
        policies.Policy("P0", None, world=1, agent=0, sampling_root=4)
    with pytest.raises(ValueError):
        policies.Policy("C", None, world=1, agent=0, sampling_root=4)
    base = FROZEN.episode_order(0)
    assert len(base) == 21 and base[0] == ("C", None)
    assert {a for a, _ in base} == set(ARMS)
    for wi in range(32):
        order = FROZEN.episode_order(wi)
        assert set(order) == set(base)
        assert order == base[wi % 21:] + base[:wi % 21]


def test_frozen_protocol_rejects_changed_seed():
    from dataclasses import replace
    with pytest.raises(ValueError):
        replace(FROZEN, layout_root=9).validate()
