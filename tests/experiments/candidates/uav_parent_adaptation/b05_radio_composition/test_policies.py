"""Outcome-blind local-barrier fixtures: no production forwards or rankings."""

import copy

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import (
    M, decode, partition,
)
from experiments.candidates.uav_parent_adaptation.b05_radio_composition import policies as module


class ForbiddenActor:
    def __call__(self, *args, **kwargs):
        raise AssertionError('the synthetic checks must not forward an actor')


class StubPolicy:
    def __init__(self, family, agent, events, *, advance=False):
        self.family, self.agent, self.events, self.advance = family, agent, events, advance
        self.counters = dict(requests=0, hits=0, misses=0, neural_rows=0)
        self.cache, self.calls = {}, []
        self.transform = None
        self.failure = None

    def query(self, row, tick, nav):
        self.counters['requests'] += 1  # Include attempted queries when a stub fails.
        self.events.append(('query', self.agent, tick))
        self.calls.append((row.copy(), tick, nav))
        if self.failure:
            raise self.failure
        key = (row[:103].tobytes(), nav)
        hit = key in self.cache
        self.counters['hits' if hit else 'misses'] += 1
        if not hit:
            features = np.concatenate((row[:103], np.eye(10, dtype=np.float32)[nav],
                                       np.ones(1, dtype=np.float32)))
            result = dict(features=features, next_nav=(nav + 1) % 10 if self.advance else nav,
                          fallback=True, memo_hit=False, n_current=0, n_peers=0,
                          action_index=6 + self.agent)
            if self.family == 'S_I':
                self.counters['neural_rows'] += 1
                # Deliberately not re-derived from these sentinel logits: the
                # adapter must use the supplied frozen marginal, not a new softmax.
                p = np.zeros(27, dtype=np.float64)
                p[13 + self.agent], p[0] = .7, .3
                result.update(logits=np.linspace(-2, 2, 27, dtype=np.float32), probabilities=p)
            else:
                result.update(scores=np.arange(27, dtype=np.float64) / 7,
                              served=np.arange(27, dtype=np.float64) / 3)
            self.cache[key] = result
        result = self.cache[key]
        result['memo_hit'] = hit
        if self.transform:
            self.transform(result)
        return result


@pytest.fixture
def observations():
    rows = np.zeros((5, 104), dtype=np.float32)
    rows[:, 0] = np.arange(5, dtype=np.float32) / 10
    rows[:, 1] = np.arange(5, dtype=np.float32) / 20
    rows[:, 2] = .5
    return rows


@pytest.fixture(autouse=True)
def synthetic_initial_nav(monkeypatch):
    # Do not call even the production geometry parser in these adapter fixtures.
    monkeypatch.setattr(module, 'initial_nav', lambda row: int(round(float(row[0]) * 10)))


def make_team(family, observations, *, advance=False):
    events, created = [], []
    actor = ForbiddenActor() if family == 'S_I' else None

    def factory(received_family, received_actor, agent):
        assert received_family == family and received_actor is actor
        policy = StubPolicy(family, agent, events, advance=advance)
        created.append(policy)
        return policy

    team = module.LocalTeam(family, observations, actor, policy_factory=factory)
    return team, events, created


def fixed_coins(depart, tail):
    return {'private_depart': np.asarray(depart, dtype=np.uint64),
            'private_tail': np.asarray(tail, dtype=np.uint64)}


@pytest.mark.parametrize('family', ['C', 'Q_I', 'S_I'])
def test_five_queries_before_once_per_block_coins_and_frozen_decoder(family, observations):
    team, events, created = make_team(family, observations)
    coins = fixed_coins([0, M - 1, 0, M - 1, 0], [0, M - 1, M - 1, 0, M // 2])

    def provider():
        assert events == [('query', i, 0) for i in range(5)]
        events.append(('coins',))
        return coins

    result = team.decide(observations, 0, provider)
    assert events == [('query', i, 0) for i in range(5)] + ([('coins',)] if family != 'C' else [])
    record = result['record']
    assert result['sampling_decisions'] == (0 if family == 'C' else 5)
    assert result['commands'].shape == (5, 3) and result['commands'].dtype == np.float32
    assert record['features'].shape == (5, 114) and record['features'].dtype == np.float32
    assert np.array_equal(record['features'][:, :103], observations[:, :103])
    assert np.array_equal(record['nav_pre'], np.arange(5))
    assert np.array_equal(record['nav_next'], np.arange(5))
    assert record['fallback'].dtype == np.bool_ and record['fallback'].all()
    for agent in range(5):
        row, tick, nav = created[agent].calls[0]
        assert np.array_equal(row, observations[agent]) and tick == 0 and nav == agent
        assert not np.shares_memory(row, observations)
        if family == 'S_I':
            p = next(iter(created[agent].cache.values()))['probabilities']
            assert np.array_equal(record['logits'][agent], np.linspace(-2, 2, 27, dtype=np.float32))
            assert 'policy_scores' not in record and 'policy_served' not in record
        else:
            p = np.full(27, .1 / 26 if family == 'Q_I' else 0., dtype=np.float64)
            p[6 + agent] = .9 if family == 'Q_I' else 1.
            assert record['policy_scores'].dtype == np.float64
            assert record['policy_served'].dtype == np.float64
            assert np.array_equal(record['policy_scores'][agent], np.arange(27) / 7)
            assert np.array_equal(record['policy_served'][agent], np.arange(27) / 3)
            assert 'logits' not in record
        assert np.array_equal(record['probabilities'][agent], p)
        assert record['modal_index'][agent] == p.argmax()
        if family != 'C':
            expected = decode(p, law='I', rank=agent, public=0,
                              private_depart=int(coins['private_depart'][agent]),
                              private_tail=int(coins['private_tail'][agent]))
            for key in ('departure_threshold', 'tail_thresholds', 'effective_probabilities',
                        'departure_integer', 'requested_departure', 'action_index'):
                assert np.array_equal(record[key][agent], expected[key])
            assert record['private_depart_integer'][agent] == coins['private_depart'][agent]
            assert record['private_tail_integer'][agent] == coins['private_tail'][agent]
        else:
            assert record['action_index'][agent] == 6 + agent
            assert 'departure_integer' not in record
        assert np.array_equal(result['commands'][agent], module.COMMANDS[record['action_index'][agent]])
    assert team.counts() == dict(requests=5, hits=0, misses=5, neural_rows=5 if family == 'S_I' else 0)
    assert set(result['timing']) == {'decision_query_wall_seconds', 'decision_query_cpu_seconds',
                                     'sampler_wall_seconds', 'sampler_cpu_seconds'}
    assert all(np.isfinite(value) and value >= 0 for value in result['timing'].values())
    if family == 'C':
        assert result['timing']['sampler_wall_seconds'] == result['timing']['sampler_cpu_seconds'] == 0


@pytest.mark.parametrize('family', ['Q_I', 'S_I'])
def test_exact_cache_hits_still_use_new_private_draws_with_empty_fallback_rows(family, observations):
    team, events, created = make_team(family, observations)
    calls = []

    def provider():
        calls.append(len(events))
        return fixed_coins([0 if len(calls) == 1 else M - 1] * 5, [0] * 5)

    first = team.decide(observations, 0, provider)
    saved = copy.deepcopy(first)
    second_rows = observations.copy()
    second_rows[:, 103] = 4 / 256  # Clock field is excluded from the inherited exact key.
    second = team.decide(second_rows, 4, provider)
    assert calls == [5, 10]
    assert not first['record']['memo_hit'].any() and second['record']['memo_hit'].all()
    assert first['record']['requested_departure'].all()
    assert not second['record']['requested_departure'].any()
    assert np.all(first['record']['action_index'] != second['record']['action_index'])
    assert np.array_equal(second['record']['action_index'], second['record']['modal_index'])
    assert team.counts() == dict(requests=10, hits=5, misses=5, neural_rows=5 if family == 'S_I' else 0)
    assert len(created) == 5 and all(len(policy.cache) == 1 for policy in created)
    assert first['record']['fallback'].all() and second['record']['fallback'].all()
    assert not first['record']['n_current'].any() and not first['record']['n_peers'].any()
    for key, value in saved['record'].items():
        assert np.array_equal(first['record'][key], value)


@pytest.mark.parametrize('family', ['C', 'Q_I', 'S_I'])
def test_navigation_own_state_and_every_saved_array_are_independent_copies(family, observations):
    team, _, policies = make_team(family, observations, advance=True)
    coins = fixed_coins([M - 1] * 5, [0] * 5)
    result = team.decide(observations, 0, lambda: coins)
    snapshot = copy.deepcopy(result['record'])
    for policy in policies:
        for diagnostic in policy.cache.values():
            for value in diagnostic.values():
                if isinstance(value, np.ndarray):
                    value.fill(77)
    coins['private_depart'].fill(13)
    coins['private_tail'].fill(17)
    observations.fill(-2)
    team.navs.fill(9)
    for key, value in snapshot.items():
        assert np.array_equal(result['record'][key], value)
    # A coordinator can override actual commands without feeding them or its mask
    # into the local navigation update. The next query gets the helper's next_nav.
    rows = np.zeros((5, 104), dtype=np.float32)
    rows[:, 0] = np.arange(5) / 10
    rows[:, 1] = np.arange(5) / 20
    rows[:, 2] = .5
    team.navs[:] = snapshot['nav_next']
    result['record']['nav_next'].fill(8)
    result['commands'].fill(0)  # Simulated downstream override.
    followup = team.decide(rows, 4, lambda: fixed_coins([M - 1] * 5, [0] * 5))
    assert np.array_equal(followup['record']['nav_pre'], np.arange(1, 6))
    assert [policy.calls[-1][2] for policy in policies] == list(range(1, 6))
    assert np.array_equal(team.navs, np.arange(2, 7))
    assert not np.shares_memory(followup['record']['nav_next'], team.navs)


def test_snapshots_before_callback_and_query_argument_isolation(observations):
    team, events, policies = make_team('S_I', observations)
    expected = observations.copy()
    for policy in policies:
        original_query = policy.query

        def mutating_query(row, tick, nav, query=original_query):
            pd = query(row, tick, nav)
            row.fill(-99)
            return pd

        policy.query = mutating_query

    def provider():
        assert len(events) == 5
        for policy in policies:
            for diagnostic in policy.cache.values():
                diagnostic['features'].fill(-8)
                diagnostic['logits'].fill(-8)
                diagnostic['probabilities'].fill(-8)
        observations.fill(-9)
        return fixed_coins([M - 1] * 5, [0] * 5)

    result = team.decide(observations, 0, provider)
    assert np.array_equal(result['record']['features'][:, :103], expected[:, :103])
    assert np.array_equal(result['record']['logits'], np.tile(np.linspace(-2, 2, 27, dtype=np.float32), (5, 1)))
    assert np.array_equal(result['record']['action_index'], np.arange(13, 18))


def test_each_episode_constructs_fresh_policies_and_default_classes_keep_disabled_sampling(monkeypatch, observations):
    constructed = []

    def c_constructor():
        constructed.append(('C',))
        return StubPolicy('C', 0, [])

    def student_constructor(actor, *, world, agent, sampled):
        constructed.append(('S', actor, world, agent, sampled))
        return StubPolicy('S_I', 0, [])

    monkeypatch.setattr(module, 'MemoC', c_constructor)
    monkeypatch.setattr(module, 'StudentPolicy', student_constructor)
    c = module.LocalTeam('C', observations)
    q = module.LocalTeam('Q_I', observations)
    actor = ForbiddenActor()
    student = module.LocalTeam('S_I', observations, actor)
    again = module.LocalTeam('S_I', observations, actor)
    assert constructed == [('C',)] * 10 + [('S', actor, 0, 0, False)] * 10
    all_policies = c.policies + q.policies + student.policies + again.policies
    assert len({id(policy) for policy in all_policies}) == 20
    assert len({id(policy.cache) for policy in all_policies}) == 20
    assert np.array_equal(student.navs, again.navs)
    student.navs.fill(9)
    assert np.array_equal(again.navs, np.arange(5))


@pytest.mark.parametrize('family', ['Q_I', 'S_I'])
def test_departure_boundary_and_last_private_tail_match_exact_I(family, observations):
    team, _, _ = make_team(family, observations)
    p = np.full(27, .1 / 26) if family == 'Q_I' else np.zeros(27)
    if family == 'Q_I':
        p[6] = .9
    else:
        p[13], p[0] = .7, .3
    b = partition(p)['departure_threshold']
    result = team.decide(observations, 0, lambda: fixed_coins([b - 1, b, b - 1, b, 0], [M - 1] * 5))
    assert result['record']['requested_departure'].tolist() == [True, False, True, False, True]
    assert result['record']['action_index'][0] == (26 if family == 'Q_I' else 0)


@pytest.mark.parametrize('family,actor', [('other', None), ('S_I', None),
                                       ('C', ForbiddenActor()), ('Q_I', ForbiddenActor())])
def test_invalid_family_actor_boundary(family, actor, observations):
    with pytest.raises(ValueError):
        module.LocalTeam(family, observations, actor)


@pytest.mark.parametrize('tick', [-4, 1, 2, 255, 256, .0, True])
def test_bad_cadence_fails_before_any_query(tick, observations):
    team, events, _ = make_team('C', observations)
    with pytest.raises(ValueError):
        team.decide(observations, tick)
    assert events == [] and team.counts()['requests'] == 0


@pytest.mark.parametrize('bad', [np.zeros((4, 104)), np.zeros((5, 103)),
                               np.full((5, 104), np.nan), np.full((5, 104), np.inf),
                               np.zeros((5, 104), dtype=np.complex128)])
def test_bad_observation_shape_or_finiteness(bad, observations):
    with pytest.raises(ValueError):
        module.LocalTeam('C', bad)
    team, events, _ = make_team('C', observations)
    with pytest.raises(ValueError):
        team.decide(bad, 0)
    assert not events


@pytest.mark.parametrize('field,bad', [('features', np.zeros(113, dtype=np.float32)),
                                    ('features', np.full(114, np.nan, dtype=np.float32)),
                                    ('logits', np.zeros(26, dtype=np.float32)),
                                    ('logits', np.full(27, np.inf, dtype=np.float32)),
                                    ('probabilities', np.zeros(27)),
                                    ('probabilities', np.full(27, np.nan)),
                                    ('probabilities', np.full(27, 1 / 27 + 0j)),
                                    ('next_nav', 10), ('n_peers', 5)])
def test_bad_diagnostics_fail_before_coins_and_preserve_attempted_counts(field, bad, observations):
    team, events, policies = make_team('S_I', observations)
    policies[2].transform = lambda pd: pd.update({field: bad})

    def forbidden_coins():
        raise AssertionError('no coins should be read for invalid distributions')

    with pytest.raises(ValueError):
        team.decide(observations, 0, forbidden_coins)
    assert events == [('query', i, 0) for i in range(3)]
    assert team.counts()['requests'] == 3


def test_feature_provenance_failure_and_query_exception_are_visible(observations):
    team, _, policies = make_team('C', observations)
    policies[1].transform = lambda pd: pd['features'].__setitem__(0, .99)
    with pytest.raises(AssertionError, match='provenance'):
        team.decide(observations, 0)
    assert team.counts()['requests'] == 2
    team, _, policies = make_team('C', observations)
    policies[3].failure = RuntimeError('synthetic query failure')
    with pytest.raises(RuntimeError, match='synthetic query'):
        team.decide(observations, 0)
    assert team.counts()['requests'] == 4


@pytest.mark.parametrize('bad', [dict(private_depart=np.zeros(4, dtype=np.uint64),
                                   private_tail=np.zeros(5, dtype=np.uint64)),
                               dict(private_depart=np.zeros(5, dtype=np.int64),
                                    private_tail=np.zeros(5, dtype=np.uint64)),
                               dict(private_depart=np.zeros(5, dtype=np.uint64),
                                    private_tail=np.full(5, M, dtype=np.uint64))])
def test_invalid_coin_shapes_dtypes_ranges_fail_without_navigation_repair(bad, observations):
    team, events, _ = make_team('Q_I', observations, advance=True)
    before = team.navs.copy()
    with pytest.raises(ValueError):
        team.decide(observations, 0, lambda: bad)
    assert len(events) == 5 and team.counts()['requests'] == 5
    assert np.array_equal(team.navs, before)


def test_stochastic_provider_is_required_but_C_never_uses_it(observations):
    team, events, _ = make_team('Q_I', observations)
    with pytest.raises(ValueError, match='provider'):
        team.decide(observations, 0)
    assert events == []
    c, _, _ = make_team('C', observations)

    def forbidden():
        raise AssertionError('C must not consume any coin')

    assert c.decide(observations, 0, forbidden)['sampling_decisions'] == 0
