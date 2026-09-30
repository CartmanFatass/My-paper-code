"""Unchanged local information, with one cached frozen forward and bounded head."""
import copy
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, analyze, memo_key
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    _cached_analysis, categorical_index, categorical_probabilities, indexed_uniform,
)
from experiments.candidates.uav_fleet_adaptation.b04_native_development.policies import LocalPolicy as OrdinaryPolicy, entropy
from .contract import HEADS


def frozen_forward(actor, features):
    """Exactly the original one-row layer order, exposing the existing hidden row."""
    x = torch.from_numpy(np.ascontiguousarray(features, dtype=np.float32)).reshape(1, 114)
    with torch.inference_mode():
        x = actor.network[0](x)
        x = actor.network[1](x)
        x = actor.network[2](x)
        h = actor.network[3](x)
        z = actor.network[4](h)
    return h[0].numpy().copy(), z[0].numpy().copy()


class LocalPolicy:
    def __init__(self, arm, actor, *, lineage, head=None, world, agent, sampling_root):
        if arm not in ("C", "Q", "S", "Bstar", *HEADS) or (arm in HEADS) != (head is not None):
            raise ValueError("policy/head mismatch")
        if head is not None and head.kind != arm:
            raise ValueError("wrong head kind for deployed arm")
        if (arm not in ("C", "Q")) != (actor is not None):
            raise ValueError("only student programs receive an actor")
        self.arm, self.actor, self.head = arm, actor, head
        self.world, self.agent, self.root = int(world), int(agent), int(sampling_root)
        self.temperature = 2. if arm == "Bstar" and lineage == 0 else 1.
        self.ordinary = None
        if arm in ("C", "Q"):
            self.ordinary = OrdinaryPolicy("C_0" if arm == "C" else "C_.10", None,
                                           world=world, agent=agent, sampling_root=sampling_root)
            self.counters = self.ordinary.counters
        else:
            self.cache = {}
            self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                                 helper_setup_links=0, helper_extreme_links=0, neural_rows=0,
                                 head_rows=0, sampled_draws=0, cache_entries=0, cache_key_bytes=0,
                                 cache_array_bytes=0)

    def query(self, row, tick, nav):
        if self.ordinary is not None:
            return self.ordinary.query(row, tick, nav)
        if tick < 0 or tick % 4:
            raise ValueError("policy only queries at four-tick clocks")
        key = memo_key(row, nav)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = analyze(row, nav)
            features = np.ascontiguousarray(result["features"], dtype=np.float32)
            hidden, original = frozen_forward(self.actor, features)
            self.counters["neural_rows"] += 1
            if not np.isfinite(hidden).all() or not np.isfinite(original).all():
                raise FloatingPointError("nonfinite frozen student output")
            value = {**_cached_analysis(result), "hidden": hidden, "base_logits": original}
            if self.head is not None:
                with torch.inference_mode():
                    value["logits"] = self.head(torch.from_numpy(hidden), torch.from_numpy(original)).numpy().copy()
                self.counters["head_rows"] += 1
                if not np.isfinite(value["logits"]).all():
                    raise FloatingPointError("nonfinite deployed head output")
            self.cache[key] = value
            self.counters["misses"] += 1
            for name, count in result["counters"].items():
                self.counters[name] = self.counters.get(name, 0) + int(count)
            self.counters["cache_entries"] = len(self.cache)
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += features.nbytes + hidden.nbytes + original.nbytes
            if self.head is not None:
                self.counters["cache_array_bytes"] += value["logits"].nbytes
        result = copy.deepcopy(self.cache[key])
        logits = result.get("logits", result["base_logits"])
        p = categorical_probabilities(logits.astype(np.float64) / self.temperature)
        u = indexed_uniform(self.root, self.world, tick, self.agent)
        choice = categorical_index(p, u)
        self.counters["sampled_draws"] += 1
        chosen = float(p[choice])
        if not 0 < chosen <= 1:
            raise FloatingPointError("invalid sampled probability")
        result.update(logits=logits, probabilities=p, innovation=u, action_index=choice,
                      command=COMMANDS[choice].copy(), chosen_probability=chosen, logp=float(np.log(chosen)),
                      memo_hit=hit, entropy=entropy(p), behavior_entropy=entropy(p))
        return result


def shadow_from_answers(answers, positions, counts):
    """Same-history S uses already-paid original logits; motion is separately paid."""
    logits = np.stack([a["base_logits"] for a in answers])
    p = np.stack([categorical_probabilities(z) for z in logits])
    actions = np.array([categorical_index(q, a["innovation"]) for q, a in zip(p, answers)], dtype=np.int64)
    counts["shadow_decisions"] += 5
    position, path = np.array(positions, copy=True), []
    for _ in range(4):
        position = np.clip(position + COMMANDS[actions].astype(np.float64) * 30.,
                           [0., 0., 50.], [1000., 1000., 150.])
        counts["shadow_motion_ticks"] += 5
        path.append(position.copy())
    return dict(probabilities=p, action_index=actions, positions=np.asarray(path, dtype=np.float64))
