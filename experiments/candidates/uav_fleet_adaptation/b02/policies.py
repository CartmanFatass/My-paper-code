"""Private episode caches and independently addressed categorical decisions."""
from __future__ import annotations

import copy

import numpy as np
import torch

from .controllers import COMMANDS, analyze, memo_key


def _cached_analysis(result):
    # Power/geometry debug arrays remain available from analyze() for numerical
    # tests; a deployed cache needs only the declared sufficient state/features.
    return {name: copy.deepcopy(result[name]) for name in
            ("features", "next_nav", "fallback", "n_current", "n_peers")}


def indexed_uniform(root: int, world: int, tick: int, agent: int) -> float:
    if tick < 0 or tick % 4 or not 0 <= agent < 5:
        raise ValueError("sampling address must name a decision tick and agent")
    return float(np.random.default_rng(np.random.SeedSequence(
        [int(root), int(world), int(tick), int(agent)])).random())


def categorical_probabilities(logits):
    values = np.asarray(logits, dtype=np.float64)
    if values.shape != (27,) or not np.isfinite(values).all():
        raise ValueError("finite 27-logit vector required")
    values = np.exp(values - np.max(values))  # Fixed temperature one; no floor.
    probabilities = values / values.sum(dtype=np.float64)
    if not np.isfinite(probabilities).all() or probabilities.sum() <= 0:
        raise FloatingPointError("invalid categorical distribution")
    return probabilities


def categorical_index(probabilities, uniform):
    p = np.asarray(probabilities, dtype=np.float64)
    if p.shape != (27,) or np.any(p < 0) or not np.isfinite(p).all():
        raise ValueError("invalid categorical probabilities")
    if not np.isclose(p.sum(), 1.0, rtol=0, atol=1e-12) or not 0 <= uniform < 1:
        raise ValueError("invalid categorical mass/innovation")
    cdf = np.cumsum(p, dtype=np.float64)
    cdf[-1] = 1.0
    return int(np.searchsorted(cdf, uniform, side="right"))


class FeatureMemo:
    """Analytic features for expert roll-in; separate from paid C labels."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.cache = {}
        self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                             helper_setup_links=0, helper_extreme_links=0,
                             cache_entries=0, cache_key_bytes=0, cache_array_bytes=0)

    def query(self, row, tick, nav):
        if tick < 0 or tick % 4:
            raise ValueError("feature queries only at decision ticks")
        key = memo_key(row, nav)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = analyze(row, nav)
            self.cache[key] = _cached_analysis(result)
            self.counters["misses"] += 1
            for name, value in result["counters"].items():
                self.counters[name] = self.counters.get(name, 0) + int(value)
            self.counters["cache_entries"] = len(self.cache)
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += result["features"].nbytes
        result = copy.deepcopy(self.cache[key])
        result["memo_hit"] = hit
        return result


class StudentPolicy:
    """A single agent; a cache hit never reuses a sampled command or innovation."""
    def __init__(self, actor, *, world, agent, sampled=False, sampling_root=29342003):
        self.actor = actor
        self.world, self.agent = int(world), int(agent)
        self.sampled, self.sampling_root = bool(sampled), int(sampling_root)
        self.reset()

    def reset(self):
        self.cache = {}
        self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                             helper_setup_links=0, helper_extreme_links=0,
                             neural_rows=0, sampled_draws=0, cache_entries=0,
                             cache_key_bytes=0, cache_array_bytes=0)

    def query(self, row, tick, nav):
        if tick < 0 or tick % 4:
            raise ValueError("policy queries only at four-tick decisions")
        self.counters["requests"] += 1
        key = memo_key(row, nav)
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = analyze(row, nav)
            features = np.ascontiguousarray(result["features"], dtype=np.float32)
            # A fixed one-row forward keeps actor arithmetic a function of this
            # agent's information, independent of other agents' cache misses.
            with torch.inference_mode():
                logits = self.actor(torch.from_numpy(features).reshape(1, 114))[0].cpu().numpy().copy()
            if not np.isfinite(logits).all():
                raise FloatingPointError("nonfinite deployed logits")
            self.cache[key] = {**_cached_analysis(result), "features": features.copy(), "logits": logits}
            self.counters["misses"] += 1
            self.counters["neural_rows"] += 1
            for name, value in result["counters"].items():
                self.counters[name] = self.counters.get(name, 0) + int(value)
            self.counters["cache_entries"] = len(self.cache)
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += features.nbytes + logits.nbytes
        result = copy.deepcopy(self.cache[key])
        probabilities = categorical_probabilities(result["logits"])
        uniform = -1.0
        if self.sampled:
            uniform = indexed_uniform(self.sampling_root, self.world, tick, self.agent)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        else:
            choice = int(np.argmax(result["logits"]))
        positive = probabilities > 0
        result.update(action_index=choice, command=COMMANDS[choice].copy(), memo_hit=hit,
                      probabilities=probabilities, innovation=uniform,
                      entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result
