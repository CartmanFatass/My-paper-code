"""Synthetic checks of truthful counts and the one-extra original-block rule."""
import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b06_cadence.gate import Cadence, own_count, remaining_motion_changed


def row(number):
    obs = np.zeros(104, dtype=np.float32)
    obs[3:63].reshape(20, 3)[:min(20, number), 2] = .26
    return obs


def test_radio_uniqueness_and_capacity_with_truncated_observation():
    # Positive-noise SINR threshold >1 admits at most one station per user.
    power = np.random.default_rng(1529).lognormal(0., 4., (5, 50))
    gamma = power / (power.sum(axis=0)[None] - power + .001)
    eligible = gamma >= 10 ** .3
    assert np.all(eligible.sum(axis=0) <= 1)
    for n in range(51):
        assert own_count(row(n)) == min(10, n)
    # At r>1, two eligible powers would imply p_i>p_j and p_j>p_i.
    r = 10 ** .3
    assert r > 1 and .001 > 0


def test_consecutive_gain_then_loss_and_spent_allowance():
    gate = Cadence("E")
    counts = [0, 2, 1, 0, 2, 1, 3, 2, 0]
    states = [gate.step(row(n), t) for t, n in enumerate(counts)]
    assert [t for t, s in enumerate(states) if s["query"]] == [0, 2, 4, 5, 8]
    assert states[2]["extra"] and states[2]["used"]
    assert states[3]["loss"] and not states[3]["available"]
    assert states[7]["loss"] and not states[7]["query"]
    # Loss at boundary is one mandatory query and resets allowance.
    assert states[8]["loss"] and states[8]["kind"] == 0 and not states[8]["used"]


def test_tick_and_reset_contract():
    for mode, expected in (("H4", [0, 4]), ("H1", list(range(8)))):
        gate = Cadence(mode)
        assert [t for t in range(8) if gate.step(row(0), t)["query"]] == expected
    gate = Cadence("E")
    with pytest.raises(ValueError):
        gate.step(row(0), 1)
    gate.step(row(1), 0)
    with pytest.raises(ValueError):
        gate.step(row(1), 0)
    with pytest.raises(ValueError):
        Cadence("E").step(row(0), False)


def test_alias_spends_allowance_and_original_remaining_geometry():
    gate = Cadence("E")
    assert gate.step(row(3), 0)["query"]
    assert gate.step(row(2), 1)["extra"]
    assert not remaining_motion_changed([0., 0., 50.], [-1., -1., -1.], [0., 0., 0.], 1)
    assert not gate.step(row(1), 2)["query"]  # No retry after an alias or same category.
    assert remaining_motion_changed([500., 500., 100.], [1., 0., 0.], [-1., 0., 0.], 3)


@pytest.mark.parametrize("bad", [np.zeros(103, np.float32), np.zeros(104, np.float64), np.full(104, np.nan, np.float32)])
def test_gate_rejects_bad_observations(bad):
    with pytest.raises(ValueError):
        own_count(bad)
