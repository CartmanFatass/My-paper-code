"""Bounded heads with unchanged B05 five-query/two-private-integer barrier."""
import copy

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import analyze, memo_key
from experiments.candidates.uav_fleet_adaptation.b02.policies import _cached_analysis, categorical_probabilities
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.policies import frozen_forward
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.policies import LocalTeam


class ProposalPolicy:
    def __init__(self, actor, *, head=None, temperature=1.):
        self.actor, self.head, self.temperature = actor, head, float(temperature)
        if self.temperature not in (1., 2.) or (head is not None and self.temperature != 1.):
            raise ValueError('fixed head or paid temperature2 required')
        self.cache, self.latest = {}, None
        self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                             helper_setup_links=0, helper_extreme_links=0, neural_rows=0,
                             head_rows=0, sampled_draws=0, cache_entries=0,
                             cache_key_bytes=0, cache_array_bytes=0)

    def query(self, row, tick, nav):
        if tick < 0 or tick % 4:
            raise ValueError('four-tick decision required')
        key = memo_key(row, nav)
        self.counters['requests'] += 1
        hit = key in self.cache
        if hit:
            self.counters['hits'] += 1
        else:
            result = analyze(row, nav)
            features = np.ascontiguousarray(result['features'], dtype=np.float32)
            hidden, original = frozen_forward(self.actor, features)
            self.counters['neural_rows'] += 1
            if not np.isfinite(hidden).all() or not np.isfinite(original).all():
                raise FloatingPointError('nonfinite frozen student output')
            value = {**_cached_analysis(result), 'hidden': hidden, 'base_logits': original}
            if self.head is not None:
                with torch.inference_mode():
                    value['logits'] = self.head(torch.from_numpy(hidden), torch.from_numpy(original)).numpy().copy()
                self.counters['head_rows'] += 1
                if not np.isfinite(value['logits']).all():
                    raise FloatingPointError('nonfinite head output')
            self.cache[key] = value
            self.counters['misses'] += 1
            for name, count in result['counters'].items():
                self.counters[name] = self.counters.get(name, 0) + int(count)
            self.counters['cache_entries'] = len(self.cache)
            self.counters['cache_key_bytes'] += len(key)
            self.counters['cache_array_bytes'] += features.nbytes + hidden.nbytes + original.nbytes
            if self.head is not None:
                self.counters['cache_array_bytes'] += value['logits'].nbytes
        value = copy.deepcopy(self.cache[key])
        logits = value.get('logits', value['base_logits']).copy()
        p = categorical_probabilities(logits.astype(np.float64) / self.temperature)
        if not (p > 0).all():
            raise FloatingPointError('nominal proposal probabilities must be strictly positive')
        value.update(logits=logits, probabilities=p, action_index=int(np.argmax(p)), memo_hit=hit)
        self.latest = copy.deepcopy(value)
        return value


class ManagedTeam(LocalTeam):
    def __init__(self, family, observations, actor=None, *, head=None, temperature=1.):
        factory = None
        if family == 'S_I':
            factory = lambda _family, model, _agent: ProposalPolicy(model, head=head, temperature=temperature)
        elif head is not None or temperature != 1.:
            raise ValueError('ordinary programs cannot receive learned context')
        super().__init__(family, observations, actor, policy_factory=factory)

    def decide(self, observations, tick, coin_provider=None):
        context = {}
        supplied_coins = coin_provider
        if self.family == 'S_I':
            if not callable(coin_provider):
                raise ValueError('S_I requires a current private coin provider')

            def supplied_coins():
                # The base team has built and copied all five distributions.
                # Bind their immutable learning context before exposing coins.
                for key in ('hidden', 'base_logits'):
                    context[key] = np.stack([p.latest[key] for p in self.policies]).copy()
                return coin_provider()

        decision = super().decide(observations, tick, supplied_coins)
        if self.family == 'S_I':
            record = decision['record']
            for key in ('hidden', 'base_logits'):
                record[key] = context[key]
            chosen = record['probabilities'][np.arange(5), record['action_index']]
            if not ((chosen > 0) & (chosen <= 1)).all():
                raise FloatingPointError('invalid nominal sampled probability')
            record['logp'] = np.log(chosen)
        return decision
