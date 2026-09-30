"""The inherited C/Q_I/S_I local decision barrier, before coordination."""

import operator
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import (
    COMMANDS, MemoC, initial_nav,
)
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import M, decode


def _integer(value, name, upper):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f'{name} must be an integer in 0..{upper}')
    try:
        value = operator.index(value)
    except TypeError as error:
        raise ValueError(f'{name} must be an integer in 0..{upper}') from error
    if not 0 <= value <= upper:
        raise ValueError(f'{name} must be an integer in 0..{upper}')
    return value


def _observations(observations):
    if np.iscomplexobj(observations):
        raise ValueError('local observations must be real')
    rows = np.asarray(observations, dtype=np.float32)
    if rows.shape != (5, 104) or not np.isfinite(rows).all():
        raise ValueError('expected five finite FP32 local observation rows of width104')
    return rows.copy()


def _array(value, shape, name, *, dtype=None):
    result = np.asarray(value)
    if (result.shape != shape or result.dtype.kind not in 'fiu'
            or not np.isfinite(result).all() or (dtype is not None and result.dtype != dtype)):
        raise ValueError(f'{name} must be a finite array of shape {shape}')
    return result.copy()


def _flag(value, name):
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError(f'{name} must be boolean')
    return bool(value)


def _diagnostic(pd, row, *, student):
    features = _array(pd['features'], (114,), 'features', dtype=np.float32)
    if not np.array_equal(features[:103], row[:103]):
        raise AssertionError('lawful feature provenance mismatch')
    result = dict(features=features, next_nav=_integer(pd['next_nav'], 'next_nav', 9),
                  action_index=_integer(pd['action_index'], 'action_index', 26),
                  fallback=_flag(pd['fallback'], 'fallback'),
                  memo_hit=_flag(pd['memo_hit'], 'memo_hit'),
                  n_current=_integer(pd['n_current'], 'n_current', 20),
                  n_peers=_integer(pd['n_peers'], 'n_peers', 4))
    if student:
        result['logits'] = _array(pd['logits'], (27,), 'logits', dtype=np.float32)
        if np.iscomplexobj(pd['probabilities']):
            raise ValueError('categorical probabilities must be real')
        p = np.asarray(pd['probabilities'], dtype=np.float64).copy()
        if (p.shape != (27,) or not np.isfinite(p).all() or (p < 0).any()
                or (p > 1).any() or abs(float(p.sum()) - 1) > 1e-12):
            raise ValueError('expected finite categorical probabilities[27]')
        result['probabilities'] = p
    else:
        # Keep the paid ranking arrays' original precision and byte payload.
        result['scores'] = _array(pd['scores'], (27,), 'scores')
        result['served'] = _array(pd['served'], (27,), 'served')
    return result


def _coins(coin_provider):
    supplied = coin_provider()
    result = {}
    for name in ('private_depart', 'private_tail'):
        values = np.asarray(supplied[name])
        if values.shape != (5,) or values.dtype != np.uint64 or (values >= M).any():
            raise ValueError(f'{name} must contain uint64[5] integers in [0,2**53)')
        result[name] = values.copy()
    return result


class LocalTeam:
    def __init__(self, family, observations, actor=None, *, policy_factory=None):
        if family not in ('C', 'Q_I', 'S_I'):
            raise ValueError('family must be C, Q_I or S_I')
        if (family == 'S_I') != (actor is not None):
            raise ValueError('S_I requires its actor; C and Q_I require actor=None')
        if policy_factory is not None and not callable(policy_factory):
            raise ValueError('policy_factory must be callable')
        rows = _observations(observations)
        self.family = family
        self.navs = np.asarray([_integer(initial_nav(row.copy()), 'initial_nav', 9)
                                for row in rows], dtype=np.int64)
        if policy_factory is not None:
            self.policies = [policy_factory(family, actor, agent) for agent in range(5)]
        elif family == 'S_I':
            self.policies = [StudentPolicy(actor, world=0, agent=0, sampled=False)
                             for _ in range(5)]
        else:
            self.policies = [MemoC() for _ in range(5)]

    def counts(self):
        totals = {}
        for policy in self.policies:
            for name, value in policy.counters.items():
                totals[name] = totals.get(name, 0) + int(value)
        return totals

    def decide(self, observations, tick, coin_provider=None):
        tick = _integer(tick, 'tick', 255)
        if tick % 4:
            raise ValueError('local decisions require the four-tick cadence')
        stochastic, student = self.family != 'C', self.family == 'S_I'
        if stochastic and not callable(coin_provider):
            raise ValueError('Q_I/S_I require a current private coin provider')
        rows = _observations(observations)
        pre = self.navs.copy()
        for nav in pre:
            _integer(nav, 'nav', 9)
        timing = {f'{part}_{clock}_seconds': 0.0
                  for part in ('decision_query', 'sampler') for clock in ('wall', 'cpu')}
        diagnostics, probabilities = [], []
        for agent, policy in enumerate(self.policies):
            wall, cpu = time.perf_counter(), time.process_time()
            pd = policy.query(rows[agent].copy(), tick, int(pre[agent]))
            timing['decision_query_wall_seconds'] += time.perf_counter() - wall
            timing['decision_query_cpu_seconds'] += time.process_time() - cpu
            pd = _diagnostic(pd, rows[agent], student=student)
            if student:
                p = pd['probabilities']
            else:
                p = np.full(27, .1 / 26 if stochastic else 0., dtype=np.float64)
                p[pd['action_index']] = .9 if stochastic else 1.
            diagnostics.append(pd)
            probabilities.append(p)
        # No current innovations are available until every local distribution is
        # built and its arrays have been copied out of policy-owned cache storage.
        coins = _coins(coin_provider) if stochastic else None
        sampled, choices = [], []
        for agent, (pd, p) in enumerate(zip(diagnostics, probabilities)):
            self.navs[agent] = pd['next_nav']
            if stochastic:
                wall, cpu = time.perf_counter(), time.process_time()
                result = decode(p, law='I', rank=agent, public=0,
                                private_depart=int(coins['private_depart'][agent]),
                                private_tail=int(coins['private_tail'][agent]))
                timing['sampler_wall_seconds'] += time.perf_counter() - wall
                timing['sampler_cpu_seconds'] += time.process_time() - cpu
                sampled.append(result)
                choices.append(result['action_index'])
            else:
                choices.append(pd['action_index'])
        record = dict(nav_pre=pre, nav_next=self.navs.copy(),
                      action_index=np.asarray(choices, dtype=np.int64),
                      modal_index=np.asarray([np.argmax(p) for p in probabilities], dtype=np.int64),
                      probabilities=np.stack(probabilities).copy())
        for key in ('fallback', 'memo_hit', 'features', 'n_current', 'n_peers'):
            record[key] = np.asarray([pd[key] for pd in diagnostics]).copy()
        if student:
            record['logits'] = np.stack([pd['logits'] for pd in diagnostics]).copy()
        else:
            record['policy_scores'] = np.stack([pd['scores'] for pd in diagnostics]).copy()
            record['policy_served'] = np.stack([pd['served'] for pd in diagnostics]).copy()
        if stochastic:
            for key in ('departure_threshold', 'tail_thresholds', 'effective_probabilities',
                        'departure_integer', 'requested_departure'):
                record[key] = np.asarray([result[key] for result in sampled]).copy()
            record['private_depart_integer'] = coins['private_depart'].copy()
            record['private_tail_integer'] = coins['private_tail'].copy()
        return dict(commands=COMMANDS[np.asarray(choices, dtype=np.int64)].copy(),
                    record=record, timing=timing, sampling_decisions=5 if stochastic else 0)
