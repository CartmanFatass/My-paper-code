"""Fabricated local rows and actors only: no native transitions or retained assets."""
from copy import deepcopy
import math
import random

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import MemoC, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    StudentPolicy, categorical_index, categorical_probabilities, indexed_uniform,
)
from experiments.candidates.uav_fleet_transmission.b05_score_sampling import policies as p


@pytest.fixture(scope="session")
def query_counts():
    counts = dict(fixed_attempts=0, fixed_successes=0, memo_c=0, original_student=0)
    yield counts
    print("B05 synthetic query counts:", counts)


@pytest.fixture(autouse=True)
def count_queries(monkeypatch, query_counts):
    # Count actual calls, including independent reference queries; never infer
    # work from the number of parametrized cases.
    for cls, name in ((p.FixedPolicy, "fixed_attempts"), (MemoC, "memo_c"),
                      (StudentPolicy, "original_student")):
        original = cls.query

        def counted(self, *args, query=original, counter=name, **kwargs):
            query_counts[counter] += 1
            result = query(self, *args, **kwargs)
            if counter == "fixed_attempts":
                query_counts["fixed_successes"] += 1
            return result

        monkeypatch.setattr(cls, "query", counted)


def row(*, empty=False, waypoint=False):
    own = np.r_[WAYPOINTS[0], 50.] if waypoint else np.array([437., 623., 95.])
    observation = np.zeros(104, dtype=np.float32)
    observation[:3] = own / [1000., 1000., 100.] - [0., 0., .5]
    if not empty:
        observation[3:6] = [23. / 1000., -47. / 1000., (8. + 10.) / 50.]
        observation[63:67] = [120. / 1000., 170. / 1000., 20. / 100., 1.]
    return observation


class FixedActor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.register_buffer("values", torch.linspace(-3., 2., 27, dtype=torch.float32))

    def forward(self, features):
        assert features.shape == (1, 114) and features.dtype == torch.float32
        assert not torch.is_grad_enabled()
        self.calls.append(features.clone())
        return self.values.reshape(1, 27) + features[:, :1] * .125


def make_policy(arm, actor=None):
    return p.FixedPolicy(arm, actor, world=17, agent=2, sampling_root=71)


def assert_density(answer):
    probabilities = answer["probabilities"]
    assert probabilities.shape == (27,) and probabilities.dtype == np.float64
    assert np.isfinite(probabilities).all() and np.all(probabilities >= 0)
    assert probabilities.sum() == pytest.approx(1., rel=0., abs=4 * np.finfo(np.float64).eps)
    choice = answer["action_index"]
    assert answer["chosen_probability"] == probabilities[choice]
    assert answer["logp"] == np.log(probabilities[choice])
    expected_entropy = -math.fsum(float(v) * math.log(float(v)) for v in probabilities if v > 0)
    assert answer["entropy"] == pytest.approx(expected_entropy, abs=1e-15)
    assert answer["behavior_entropy"] == answer["entropy"]
    np.testing.assert_array_equal(answer["command"], p.COMMANDS[choice])
    assert not np.shares_memory(answer["command"], p.COMMANDS)


def test_exports_and_exact_all_score_ties():
    assert p.ARMS == ("C", "Q10", "Q05", "G", "S_L0", "S_L1", "Bstar_L0")
    assert p.ORDINARY_ARMS == p.ARMS[:4] and p.STUDENT_ARMS == p.ARMS[4:]
    assert p.TAU == .014
    for c_index in range(27):
        for score in (0., -7., 1e300):
            expected = np.full(27, .1 / 26., dtype=np.float64)
            expected[c_index] = .9
            np.testing.assert_array_equal(p.q_probabilities(c_index, .1), expected)
            actual = p.score_tail_probabilities(np.full(27, score), c_index)
            assert actual.tobytes() == expected.tobytes()


@pytest.mark.parametrize("c_index", [0, 13, 26])
def test_unequal_scores_scalar_reference_and_c_exclusion(c_index):
    scores = np.linspace(-.04, .075, 27, dtype=np.float64)
    scores[c_index] = 1e300  # C's score never enters tail normalization.
    alternatives = [i for i in range(27) if i != c_index]
    maximum = max(float(scores[i]) for i in alternatives)
    weights = [math.exp((float(scores[i]) - maximum) / .014) for i in alternatives]
    denominator = math.fsum(weights)
    expected = np.zeros(27, dtype=np.float64)
    expected[c_index] = .9
    for i, weight in zip(alternatives, weights):
        expected[i] = .1 * weight / denominator
    actual = p.score_tail_probabilities(scores, c_index)
    np.testing.assert_allclose(actual, expected, rtol=4e-16, atol=0.)
    assert actual[c_index] == .9
    assert actual[alternatives].sum() == pytest.approx(.1, abs=2e-17)
    assert np.all(np.diff(actual[alternatives]) > 0)


def test_extreme_finite_scores_underflow_and_finite_grid_tiny_bins():
    scores = np.full(27, -1e308)
    scores[26] = 1e308
    with np.errstate(all="raise"):
        probabilities = p.score_tail_probabilities(scores, 13)
    assert probabilities[13] == .9 and probabilities[26] == .1
    assert np.count_nonzero(probabilities) == 2
    assert categorical_index(probabilities, 0.) == 13
    assert categorical_index(probabilities, np.nextafter(1., 0.)) == 26
    scores = np.full(27, -1.)
    scores[26] = 0.
    probabilities = p.score_tail_probabilities(scores, 13)
    assert 0 < probabilities[0] < 2. ** -53
    assert categorical_index(probabilities, 0.) == 0
    assert categorical_index(probabilities, 2. ** -53) == 13
    assert categorical_index(probabilities, .9) == 26


@pytest.mark.parametrize("arm,epsilon", [("C", 0.), ("Q10", .1), ("Q05", .05), ("G", .1)])
@pytest.mark.parametrize("empty", [False, True])
def test_ordinary_source_law_fallback_and_indexed_replay(arm, epsilon, empty):
    observation = row(empty=empty, waypoint=empty)
    reference = MemoC().query(observation, 0, 0)
    policy = make_policy(arm)
    assert policy.counters is policy.base.counters
    answer = policy.query(observation, 0, 0)
    assert answer["c_index"] == reference["action_index"]
    for key in ("features", "scores", "served", "next_nav", "fallback", "n_current", "n_peers", "memo_hit"):
        np.testing.assert_array_equal(answer[key], reference[key])
    if empty:
        assert answer["fallback"] and answer["next_nav"] == 1
        assert np.all(answer["scores"] == answer["scores"][0])
    if arm == "G":
        expected = p.score_tail_probabilities(reference["scores"], reference["action_index"])
    else:
        expected = np.full(27, epsilon / 26., dtype=np.float64)
        expected[reference["action_index"]] = 1. - epsilon
    np.testing.assert_array_equal(answer["probabilities"], expected)
    uniform = -1. if arm == "C" else indexed_uniform(71, 17, 0, 2)
    choice = reference["action_index"] if arm == "C" else categorical_index(expected, uniform)
    assert answer["innovation"] == uniform and answer["action_index"] == choice
    assert policy.counters["sampled_draws"] == (arm != "C")
    assert policy.counters["score_tail_evaluations"] == (arm == "G")
    assert_density(answer)


@pytest.mark.parametrize("arm", p.ARMS)
def test_one_draw_each_cache_query_navigation_and_copy_isolation(arm, monkeypatch):
    actor = FixedActor() if arm in p.STUDENT_ARMS else None
    policy = make_policy(arm, actor)
    observation = row(empty=True, waypoint=True)
    addresses = []

    def draw(root, world, tick, agent):
        addresses.append((root, world, tick, agent))
        return 0. if tick == 0 else np.nextafter(1., 0.)

    monkeypatch.setattr(p, "indexed_uniform", draw)
    first = policy.query(observation, 0, 0)
    saved = deepcopy(first)
    for value in first.values():
        if isinstance(value, np.ndarray):
            value.fill(-99)
    observation[-1] = 4. / 256.
    second = policy.query(observation, 4, 0)
    assert second["memo_hit"] and policy.counters["requests"] == 2
    assert policy.counters["misses"] == policy.counters["hits"] == 1
    assert second["next_nav"] == saved["next_nav"] == 1
    for key in ("features", "scores", "served", "logits"):
        if key in saved:
            np.testing.assert_array_equal(second[key], saved[key])
    assert_density(second)
    if arm == "C":
        assert addresses == [] and second["innovation"] == -1.
    else:
        assert addresses == [(71, 17, 0, 2), (71, 17, 4, 2)]
        assert saved["action_index"] == 0 and second["action_index"] == 26
        assert policy.counters["sampled_draws"] == 2
    assert policy.counters["score_tail_evaluations"] == (2 if arm == "G" else 0)
    cache = policy.base.cache if actor is not None else policy.base._cache
    assert all("innovation" not in entry and "probabilities" not in entry for entry in cache.values())
    if actor is not None:
        assert len(actor.calls) == 1 and policy.counters["neural_rows"] == 1


@pytest.mark.parametrize("arm,temperature", [("S_L0", 1.), ("S_L1", 1.), ("Bstar_L0", 2.)])
def test_original_student_one_row_features_logits_and_temperature(arm, temperature):
    actor, reference_actor = FixedActor(), FixedActor()
    policy = make_policy(arm, actor)
    reference = StudentPolicy(reference_actor, world=17, agent=2, sampled=False, sampling_root=71)
    for tick in (0, 4):
        observation = row()
        observation[-1] = tick / 256.
        source = reference.query(observation, tick, 3)
        answer = policy.query(observation, tick, 3)
        for key in ("features", "logits", "next_nav", "fallback", "n_current", "n_peers", "memo_hit"):
            np.testing.assert_array_equal(answer[key], source[key])
        expected = categorical_probabilities(source["logits"].astype(np.float64) / temperature)
        np.testing.assert_array_equal(answer["probabilities"], expected)
        uniform = indexed_uniform(71, 17, tick, 2)
        assert answer["innovation"] == uniform
        assert answer["action_index"] == categorical_index(expected, uniform)
        assert_density(answer)
    assert len(actor.calls) == len(reference_actor.calls) == 1
    assert policy.base.sampled is False and policy.counters["sampled_draws"] == 2
    assert "c_index" not in answer and "scores" not in answer and "served" not in answer


def test_all_27_categories_survive_clipped_physical_aliases(monkeypatch):
    observation = np.zeros(104, dtype=np.float32)  # Fabricated corner (0,0,50).
    source = MemoC().query(observation, 0, 0)
    probabilities = p.q_probabilities(source["action_index"], .1)
    cdf = np.cumsum(probabilities)
    uniforms = iter((np.r_[0., cdf[:-1]] + cdf) / 2.)
    monkeypatch.setattr(p, "indexed_uniform", lambda *address: float(next(uniforms)))
    policy = make_policy("G")
    commands = []
    for index in range(27):
        answer = policy.query(observation, index * 4, 0)
        assert answer["action_index"] == index
        assert answer["next_nav"] == source["next_nav"]
        assert answer["memo_hit"] == (index > 0)
        np.testing.assert_array_equal(answer["probabilities"], probabilities)
        commands.append(answer["command"])
    np.testing.assert_array_equal(commands, p.COMMANDS)
    positions = np.tile([0., 0., 50.], (27, 1))
    for _ in range(4):
        positions = np.clip(positions + np.asarray(commands, dtype=np.float64) * 30.,
                            [0., 0., 50.], [1000., 1000., 150.])
    assert len(np.unique(positions, axis=0)) < 27
    assert np.count_nonzero(probabilities) == 27
    assert policy.counters["sampled_draws"] == policy.counters["score_tail_evaluations"] == 27
    assert policy.counters["misses"] == 1 and policy.counters["hits"] == 26


@pytest.mark.parametrize("arm", p.ARMS)
def test_global_rng_noninterference_and_address_replay(arm):
    actor = FixedActor() if arm in p.STUDENT_ARMS else None
    policy, replay = make_policy(arm, actor), make_policy(arm, actor)
    numpy_state, torch_state, python_state = np.random.get_state(), torch.get_rng_state().clone(), random.getstate()
    for tick in (0, 4):
        answer = policy.query(row(), tick, 2)
        repeated = replay.query(row(), tick, 2)
        assert answer["innovation"] == repeated["innovation"]
        assert answer["action_index"] == repeated["action_index"]
        np.testing.assert_array_equal(answer["probabilities"], repeated["probabilities"])
    after = np.random.get_state()
    assert after[0] == numpy_state[0] and after[2:] == numpy_state[2:]
    np.testing.assert_array_equal(after[1], numpy_state[1])
    assert torch.equal(torch_state, torch.get_rng_state()) and random.getstate() == python_state


@pytest.mark.parametrize("bad", [-1, 27, True, np.bool_(False), 2., "2", None])
def test_invalid_c_index(bad):
    with pytest.raises(ValueError):
        p.q_probabilities(bad, .1)
    with pytest.raises(ValueError):
        p.score_tail_probabilities(np.zeros(27), bad)


@pytest.mark.parametrize("bad", [np.zeros(26), np.zeros((27, 1)), np.full(27, np.nan),
                               np.full(27, np.inf), np.zeros(27, dtype=np.complex128)])
def test_invalid_scores(bad):
    with pytest.raises(ValueError):
        p.score_tail_probabilities(bad, 0)


@pytest.mark.parametrize("bad", [-.1, 1.1, np.nan, np.inf, True, "0.1", None])
def test_invalid_epsilon(bad):
    with pytest.raises(ValueError):
        p.q_probabilities(0, bad)


@pytest.mark.parametrize("arm", p.ARMS)
def test_actor_boundary(arm):
    with pytest.raises(ValueError):
        make_policy(arm, FixedActor() if arm in p.ORDINARY_ARMS else None)


def test_unknown_arm():
    with pytest.raises(ValueError):
        make_policy("unknown")


@pytest.mark.parametrize("arm", ["C", "G", "S_L0"])
@pytest.mark.parametrize("tick,nav", [(-4, 0), (1, 0), (0, -1), (0, 10), (0, True)])
def test_invalid_query_boundaries(arm, tick, nav):
    policy = make_policy(arm, FixedActor() if arm in p.STUDENT_ARMS else None)
    with pytest.raises(ValueError):
        policy.query(row(), tick, nav)
    assert policy.counters["sampled_draws"] == policy.counters["score_tail_evaluations"] == 0
