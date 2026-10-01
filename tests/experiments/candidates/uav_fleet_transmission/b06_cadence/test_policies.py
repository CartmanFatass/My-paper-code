"""Synthetic rows/actors only; no native environment or retained asset queries."""
from copy import deepcopy
import random

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as original_helpers
from experiments.candidates.uav_fleet_adaptation.b02 import policies as original_sampling
from experiments.candidates.uav_fleet_transmission.b05_score_sampling import policies as b05
from experiments.candidates.uav_fleet_transmission.b06_cadence import policies as p


def row(*, users=1, peers=1, waypoint=False, corner=False, weak=False):
    own = ([0., 0., 50.] if corner else
           [100., 100., 50.] if waypoint else [437., 623., 95.])
    observation = np.zeros(104, dtype=np.float32)
    observation[:3] = np.asarray(own) / [1000., 1000., 100.] - [0., 0., .5]
    slots = observation[3:63].reshape(20, 3)
    for i in range(users):
        slots[i] = [(23. + i * 7.) / 1000., (-47. + i * 3.) / 1000.,
                    ((-9. if weak else 8.) + 10.) / 50.]
    for i in range(peers):
        observation[63:103].reshape(10, 4)[i] = [.12 + .01 * i, .17, .2, 1.]
    return observation


class SyntheticActor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.register_buffer("weights", torch.arange(114 * 27, dtype=torch.float32)
                             .reshape(114, 27).remainder(19).sub(9).mul(.01))
        self.register_buffer("bias", torch.linspace(-2., 2., 27, dtype=torch.float32))

    def forward(self, features):
        assert features.shape == (1, 114) and features.dtype == torch.float32
        assert not torch.is_grad_enabled()
        self.calls.append(features.clone())
        return features @ self.weights + self.bias


def make_policy(arm, cls=p.FixedPolicy):
    actor = SyntheticActor() if arm in p.STUDENT_ARMS else None
    return cls(arm, actor, world=17, agent=2, sampling_root=71), actor


def assert_answer_equal(actual, expected):
    assert actual.keys() == expected.keys()
    for name in actual:
        np.testing.assert_array_equal(actual[name], expected[name], err_msg=name)


def assert_controller_equal(actual, expected):
    assert actual.history is expected.history is False
    assert actual.counters == expected.counters
    assert actual._nav_index == expected._nav_index
    for name in ("_points", "_last_seen", "_current_mask", "_command"):
        np.testing.assert_array_equal(getattr(actual, name), getattr(expected, name))
    assert_answer_equal(actual._plan, expected._plan)


def test_exports_reuse_frozen_laws_and_order():
    assert p.ARMS is b05.ARMS and p.ORDINARY_ARMS is b05.ORDINARY_ARMS
    assert p.STUDENT_ARMS is b05.STUDENT_ARMS and p.TAU == .014
    assert p.q_probabilities is b05.q_probabilities
    assert p.score_tail_probabilities is b05.score_tail_probabilities
    assert p.categorical_index is original_sampling.categorical_index
    assert p.categorical_probabilities is original_sampling.categorical_probabilities
    assert p.COMMANDS is original_helpers.COMMANDS


@pytest.mark.parametrize("arm", p.ARMS)
def test_old_grid_exact_b05_diagnostics_and_all_counters(arm):
    policy, actor = make_policy(arm)
    reference, reference_actor = make_policy(arm, b05.FixedPolicy)
    rows = [row(), row(users=0, peers=0, waypoint=True), row(users=20, peers=4),
            row(users=1, peers=0, weak=True), row(users=0, peers=0, corner=True)]
    for index, (observation, nav) in enumerate(
            [(value, nav) for value in rows for nav in (0, 3, 9)] * 2):
        tick = index * 4
        observation = observation.copy()
        observation[-1] = tick / 256.
        actual = policy.query(observation, tick, nav)
        expected = reference.query(observation, tick, nav)
        assert_answer_equal(actual, expected)
        assert policy.counters == reference.counters
        assert policy.counters is policy.base.counters
        if arm in p.ORDINARY_ARMS:
            assert_controller_equal(policy.base._original, reference.base._original)
    assert policy.counters["misses"] == policy.counters["hits"] == 15
    if actor is not None:
        assert len(actor.calls) == len(reference_actor.calls) == 15
        for actual, expected in zip(actor.calls, reference_actor.calls):
            assert torch.equal(actual, expected)


@pytest.mark.parametrize("tick", [1, 2, 3, 5, 255, 256])
def test_full_c_off_grid_decides_current_row_at_actual_tick(tick):
    policy, _ = make_policy("C")
    previous = policy.query(row(users=0, peers=0, waypoint=True), 0, 0)
    observation = row(users=20, peers=4)
    actual = policy.query(observation, tick, 3)
    # The original old-grid law provides an independent full-C arithmetic oracle.
    expected = b05.FixedPolicy("C", None, world=17, agent=2, sampling_root=71).query(
        observation, 0, 3)
    assert_answer_equal(actual, expected)
    assert actual["c_index"] != previous["c_index"]
    assert not actual["fallback"] and actual["n_current"] == 20
    controller = policy.base._original
    np.testing.assert_array_equal(controller.last_seen, np.full(20, tick))
    np.testing.assert_array_equal(controller.current_mask, np.ones(20, dtype=bool))
    assert len(controller.cache_points) == 0
    assert controller.counters["ingests"] == controller.counters["decisions"] == 2
    assert policy.counters["trajectories"] == 54
    assert policy.counters["model_ticks"] == policy.counters["objective_reductions"] == 216
    assert policy.counters["candidate_links"] == 108 * 20
    assert policy.counters["setup_links"] == 5 * 20


@pytest.mark.parametrize("arm", p.ARMS)
@pytest.mark.parametrize("tick", [1, 2, 255])
def test_fresh_off_grid_query_equals_parent_except_actual_draw(arm, tick):
    policy, actor = make_policy(arm)
    reference, reference_actor = make_policy(arm, b05.FixedPolicy)
    observation = row(users=20, peers=4)
    observation[-1] = tick / 256.
    expected = reference.query(observation, 0, 9)
    if arm != "C":
        uniform = float(np.random.default_rng(np.random.SeedSequence([71, 17, tick, 2])).random())
        choice = original_sampling.categorical_index(expected["probabilities"], uniform)
        chosen_probability = float(expected["probabilities"][choice])
        expected.update(innovation=uniform, action_index=choice,
                        command=original_helpers.COMMANDS[choice].copy(),
                        chosen_probability=chosen_probability, logp=float(np.log(chosen_probability)))
    assert_answer_equal(policy.query(observation, tick, 9), expected)
    assert policy.counters == reference.counters
    if actor is not None:
        assert len(actor.calls) == len(reference_actor.calls) == 1
        assert torch.equal(actor.calls[0], reference_actor.calls[0])
        assert policy.base.sampled is False


@pytest.mark.parametrize("arm", p.ARMS)
def test_off_grid_fallback_navigation_once_per_query(arm):
    policy, _ = make_policy(arm)
    observation = row(users=0, peers=0, waypoint=True)
    nav = 0
    for tick in (1, 2, 3, 4):
        reference, _ = make_policy(arm, b05.FixedPolicy)
        expected = reference.query(observation, 0, nav)
        actual = policy.query(observation, tick, nav)
        for field in ("features", "next_nav", "fallback", "n_current", "n_peers"):
            np.testing.assert_array_equal(actual[field], expected[field])
        assert actual["fallback"] and actual["next_nav"] == 1
        # Caller adopts the returned nav; proximity to waypoint0 cannot advance it again.
        nav = actual["next_nav"]
    assert policy.counters["misses"] == policy.counters["hits"] == 2
    if arm in p.ORDINARY_ARMS:
        assert policy.base._original.counters["fallback_decisions"] == 2


@pytest.mark.parametrize("arm", p.ARMS)
def test_clock_independent_private_cache_actual_draw_and_copy_isolation(arm, monkeypatch):
    policy, actor = make_policy(arm)
    addresses = []

    def draw(root, world, tick, agent):
        addresses.append((root, world, tick, agent))
        return 0. if tick == 1 else np.nextafter(1., 0.)

    monkeypatch.setattr(p, "indexed_uniform", draw)
    observation = row(users=0, peers=0, waypoint=True)
    first = policy.query(observation, 1, 0)
    saved = deepcopy(first)
    for value in first.values():
        if isinstance(value, np.ndarray):
            value.fill(-99)
    observation[-1] = np.nan  # Clock is deliberately outside the 103-value contract/key.
    second = policy.query(observation, 2, 0)
    assert second["memo_hit"] and second["next_nav"] == saved["next_nav"] == 1
    for name in ("features", "scores", "served", "logits", "probabilities"):
        if name in saved:
            np.testing.assert_array_equal(second[name], saved[name])
    assert policy.counters["misses"] == policy.counters["hits"] == 1
    assert policy.counters["cache_key_bytes"] == 103 * 4 + 1
    if arm == "C":
        assert addresses == [] and second["innovation"] == -1.
    else:
        assert addresses == [(71, 17, 1, 2), (71, 17, 2, 2)]
        assert saved["action_index"] == 0 and second["action_index"] == 26
        assert policy.counters["sampled_draws"] == 2
    assert policy.counters["score_tail_evaluations"] == (2 if arm == "G" else 0)
    cache = policy.base.cache if actor is not None else policy.base._cache
    assert len(cache) == 1
    assert all("innovation" not in entry and "probabilities" not in entry for entry in cache.values())
    if actor is not None:
        assert len(actor.calls) == policy.counters["neural_rows"] == 1
        assert all("action_index" not in entry for entry in cache.values())
    other, _ = make_policy(arm)
    assert not other.query(observation, 2, 0)["memo_hit"]
    assert other.counters["cache_entries"] == 1
    policy.query(observation, 3, 1)
    observation[0] = np.nextafter(observation[0], np.float32(1.))
    policy.query(observation, 3, 1)
    assert policy.counters["cache_entries"] == 3


@pytest.mark.parametrize("arm", p.ARMS)
def test_actual_address_replay_rng_invariance_and_private_draws(arm):
    policy, _ = make_policy(arm)
    replay, _ = make_policy(arm)
    private_rng = np.random.default_rng(345)
    private_state = deepcopy(private_rng.bit_generator.state)
    numpy_state, torch_state, python_state = np.random.get_state(), torch.get_rng_state().clone(), random.getstate()
    for tick in (0, 1, 2, 3, 4, 255):
        observation = row()
        observation[-1] = tick / 256.
        actual = policy.query(observation, tick, 2)
        assert_answer_equal(actual, replay.query(observation, tick, 2))
        expected_draw = float(np.random.default_rng(np.random.SeedSequence([71, 17, tick, 2])).random())
        assert actual["innovation"] == (-1. if arm == "C" else expected_draw)
        if arm != "C":
            assert actual["action_index"] == original_sampling.categorical_index(
                actual["probabilities"], expected_draw)
    after = np.random.get_state()
    assert after[0] == numpy_state[0] and after[2:] == numpy_state[2:]
    np.testing.assert_array_equal(after[1], numpy_state[1])
    assert torch.equal(torch_state, torch.get_rng_state()) and random.getstate() == python_state
    assert private_rng.bit_generator.state == private_state
    assert policy.counters["sampled_draws"] == (0 if arm == "C" else 6)
    assert policy.counters["misses"] == 1 and policy.counters["hits"] == 5


def test_old_grid_uniform_exact_and_all_27_categories_off_grid(monkeypatch):
    for tick in (0, 4, 252):
        for agent in range(5):
            assert p.indexed_uniform(71, 17, tick, agent) == original_sampling.indexed_uniform(71, 17, tick, agent)
    observation = row(users=0, peers=0, corner=True)
    reference, _ = make_policy("G", b05.FixedPolicy)
    probabilities = reference.query(observation, 0, 0)["probabilities"]
    cdf = np.cumsum(probabilities)
    uniforms = iter((np.r_[0., cdf[:-1]] + cdf) / 2.)
    monkeypatch.setattr(p, "indexed_uniform", lambda *args: float(next(uniforms)))
    policy, _ = make_policy("G")
    for index in range(27):
        result = policy.query(observation, index + 1, 0)
        assert result["action_index"] == index
        np.testing.assert_array_equal(result["command"], p.COMMANDS[index])
        assert not np.shares_memory(result["command"], p.COMMANDS)
    assert policy.counters["misses"] == 1 and policy.counters["hits"] == 26
    assert policy.counters["sampled_draws"] == policy.counters["score_tail_evaluations"] == 27


@pytest.mark.parametrize("name", ["root", "world", "tick", "agent"])
@pytest.mark.parametrize("bad", [-1, True, np.bool_(False), 1.5, 1., "1", None])
def test_integer_draw_addresses(name, bad):
    values = dict(root=71, world=17, tick=1, agent=2)
    values[name] = bad
    with pytest.raises(ValueError):
        p.indexed_uniform(**values)


def test_n5_agent_boundaries_and_numpy_integers():
    for agent in range(5):
        assert p.indexed_uniform(np.int64(71), np.int64(17), np.int64(1), np.int64(agent)) == p.indexed_uniform(71, 17, 1, agent)
    for agent in (5, 10):
        with pytest.raises(ValueError):
            p.indexed_uniform(71, 17, 1, agent)
        with pytest.raises(ValueError):
            p.FixedPolicy("C", None, world=17, agent=agent, sampling_root=71)


@pytest.mark.parametrize("arm", ["C", "G", "S_L0"])
def test_invalid_query_rows_navigation_ticks_and_constructor(arm):
    policy, _ = make_policy(arm)
    for bad in (-1, True, 1., "1", None):
        with pytest.raises(ValueError):
            policy.query(row(), bad, 0)
    for bad in (-1, 10, True, 1., "1", None):
        with pytest.raises(ValueError):
            policy.query(row(), 1, bad)
    invalid = row()
    invalid[1] = np.nan
    for observation in (invalid, np.zeros(103), row(peers=5)):
        with pytest.raises(ValueError):
            policy.query(observation, 1, 0)
    assert all(value == 0 for value in policy.counters.values())
    for name in ("world", "agent", "sampling_root"):
        kwargs = dict(world=17, agent=2, sampling_root=71)
        kwargs[name] = 1.5
        with pytest.raises(ValueError):
            p.FixedPolicy(arm, SyntheticActor() if arm in p.STUDENT_ARMS else None, **kwargs)


@pytest.mark.parametrize("arm", p.ARMS)
def test_actor_contract(arm):
    with pytest.raises(ValueError):
        p.FixedPolicy(arm, SyntheticActor() if arm in p.ORDINARY_ARMS else None,
                      world=17, agent=2, sampling_root=71)
    with pytest.raises(ValueError):
        p.FixedPolicy("unknown", None, world=17, agent=2, sampling_root=71)
