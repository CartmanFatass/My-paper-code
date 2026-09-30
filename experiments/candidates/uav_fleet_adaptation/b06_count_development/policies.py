"""Private indexed stochastic deployment and greedy acquisition at public N."""
from copy import deepcopy

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_probabilities, categorical_index
from .controllers import COMMANDS, MemoC, analyze, cached_analysis, fleet_count, memo_key, inherited


def indexed_uniform(root, world, tick, agent, n):
    n = fleet_count(n)
    inherited._tick(tick)
    if type(agent) is not int or not 0 <= agent < n:
        raise ValueError("invalid within-fleet sampling address")
    return float(np.random.default_rng(np.random.SeedSequence(
        [int(root), int(world), int(tick), agent])).random())


class StudentPolicy:
    def __init__(self, actor, *, n, world, agent, sampling_root=None, temperature=1.):
        self.n = fleet_count(n)
        self.actor, self.world, self.agent = actor, int(world), int(agent)
        if not 0 <= self.agent < self.n or temperature not in (1., 2.):
            raise ValueError("invalid deployment interface")
        self.sampling_root, self.temperature = sampling_root, float(temperature)
        self.cache = {}
        self.count_tensor = torch.tensor([self.n], dtype=torch.int64)
        self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                             helper_setup_links=0, helper_extreme_links=0, neural_rows=0,
                             sampled_draws=0, cache_entries=0, cache_key_bytes=0, cache_array_bytes=0)

    def query(self, row, tick, nav):
        inherited._tick(tick)
        key = memo_key(row, nav, self.n)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = analyze(row, nav, self.n)
            features = np.ascontiguousarray(result["features"], dtype=np.float32)
            with torch.inference_mode():
                logits = self.actor(torch.from_numpy(features).reshape(1, 114), self.count_tensor)[0].cpu().numpy().copy()
            if not np.isfinite(logits).all():
                raise FloatingPointError("nonfinite deployed logits")
            self.cache[key] = dict(cached_analysis(result), logits=logits)
            self.counters["misses"] += 1
            self.counters["neural_rows"] += 1
            for name, value in result["counters"].items():
                self.counters[name] += int(value)
            self.counters["cache_entries"] += 1
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += features.nbytes + logits.nbytes
        result = deepcopy(self.cache[key])
        probabilities = categorical_probabilities(result["logits"].astype(np.float64) / self.temperature)
        uniform = -1.
        if self.sampling_root is None:
            choice = int(np.argmax(result["logits"]))
        else:
            uniform = indexed_uniform(self.sampling_root, self.world, tick, self.agent, self.n)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        positive = probabilities > 0
        result.update(action_index=choice, command=COMMANDS[choice].copy(), memo_hit=hit,
                      probabilities=probabilities, innovation=uniform,
                      entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result


class OrdinaryPolicy(MemoC):
    def __init__(self, *, n, world, agent, sampling_root=None):
        super().__init__(n)
        self.world, self.agent, self.sampling_root = int(world), int(agent), sampling_root
        self.counters["sampled_draws"] = 0

    def query(self, row, tick, nav):
        result = super().query(row, tick, nav)
        mode = result["action_index"]
        p = np.zeros(27, dtype=np.float64)
        p[mode] = 1.
        uniform = -1.
        if self.sampling_root is not None:
            p.fill(.1 / 26.)
            p[mode] = .9
            uniform = indexed_uniform(self.sampling_root, self.world, tick, self.agent, self.n)
            result["action_index"] = categorical_index(p, uniform)
            result["command"] = COMMANDS[result["action_index"]].copy()
            self.counters["sampled_draws"] += 1
        result.update(mode_index=mode, probabilities=p, innovation=uniform)
        return result
