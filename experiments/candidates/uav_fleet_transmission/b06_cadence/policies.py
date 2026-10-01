"""Frozen N5 B05 parent laws queried at actual, possibly off-grid, ticks.

Only scheduling validation changes: full C still scores four ticks and students
still use the original 114 features and one-row FP32 forward. Caches are private
to an episode/agent and exclude both clock and sampled action.
"""
from copy import deepcopy
from numbers import Integral

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as inherited
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    StudentPolicy as OriginalStudentPolicy,
    _cached_analysis,
    categorical_index,
    categorical_probabilities,
)
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import (
    ARMS, ORDINARY_ARMS, STUDENT_ARMS, TAU,
    q_probabilities, score_tail_probabilities,
)

COMMANDS = inherited.COMMANDS


def _address(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return int(value)


def _agent(value):
    value = _address(value, "agent")
    if value >= 5:
        raise ValueError("N5 agent must be in 0..4")
    return value


def indexed_uniform(root, world, tick, agent):
    """Extend the original SeedSequence law to every actual native tick."""
    address = [_address(root, "sampling_root"), _address(world, "world"),
               _address(tick, "tick"), _agent(agent)]
    return float(np.random.default_rng(np.random.SeedSequence(address)).random())


class _MemoC(inherited.MemoC):
    def _miss(self, row, tick, nav):
        controller = self._original
        controller._nav_index = nav
        own, xy, sinr, peers = inherited.original._parse(row)
        before = controller.counters.copy()
        controller.counters["ingests"] += 1
        _, _, _, observed_indices = controller._ingest(xy, tick)
        scores, served, _, _ = controller._decide(own, sinr, peers, observed_indices)
        for target, field in (("trajectories", "trajectories"), ("model_ticks", "model_ticks"),
                              ("candidate_links", "candidate_link_evaluations"),
                              ("setup_links", "setup_link_evaluations"),
                              ("objective_reductions", "objective_reductions")):
            self.counters[target] += controller.counters[field] - before[field]
        plan = controller._plan
        return {"action_index": int(plan["selected_index"]), "command": controller._command.copy(),
                "next_nav": int(controller._nav_index), "fallback": bool(plan["fallback"]),
                "scores": scores.copy(), "served": served.copy(),
                "n_current": len(xy), "n_peers": len(peers),
                "features": inherited._features(row, nav, plan["fallback"])}

    def query(self, row, tick, nav):
        row, tick, nav = inherited._row(row), _address(tick, "tick"), inherited._nav(nav)
        key = inherited.memo_key(row, nav)
        self.counters["requests"] += 1
        hit = key in self._cache
        if hit:
            self.counters["hits"] += 1
        else:
            self.counters["misses"] += 1
            self._cache[key] = deepcopy(self._miss(row, tick, nav))
            self.counters["cache_entries"] += 1
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += sum(
                value.nbytes for value in self._cache[key].values() if isinstance(value, np.ndarray))
        result = deepcopy(self._cache[key])
        result["memo_hit"] = hit
        return result


class _StudentPolicy(OriginalStudentPolicy):
    def query(self, row, tick, nav):
        _address(tick, "tick")
        key = inherited.memo_key(row, nav)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = inherited.analyze(row, nav)
            features = np.ascontiguousarray(result["features"], dtype=np.float32)
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
        result = deepcopy(self.cache[key])
        probabilities = categorical_probabilities(result["logits"])
        choice = int(np.argmax(result["logits"]))
        positive = probabilities > 0
        result.update(action_index=choice, command=COMMANDS[choice].copy(), memo_hit=hit,
                      probabilities=probabilities, innovation=-1.,
                      entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result


class FixedPolicy:
    """B05 diagnostics/counters, with a fresh addressed draw on every query."""
    def __init__(self, arm, actor, *, world, agent, sampling_root):
        if arm not in ARMS:
            raise ValueError("unknown B06 parent arm")
        self.arm = arm
        self.world = _address(world, "world")
        self.agent = _agent(agent)
        self.sampling_root = _address(sampling_root, "sampling_root")
        if arm in ORDINARY_ARMS:
            if actor is not None:
                raise ValueError("ordinary arms must not receive an actor")
            self.base = _MemoC()
        else:
            if actor is None:
                raise ValueError("student arms require an actor")
            self.base = _StudentPolicy(actor, world=self.world, agent=self.agent, sampled=False,
                                       sampling_root=self.sampling_root)
        self.counters = self.base.counters
        self.counters.setdefault("sampled_draws", 0)
        self.counters["score_tail_evaluations"] = 0

    def query(self, observation, tick, nav):
        answer = self.base.query(observation, tick, nav)
        if self.arm in ORDINARY_ARMS:
            answer["c_index"] = answer["action_index"]
            if self.arm == "G":
                probabilities = score_tail_probabilities(answer["scores"], answer["c_index"])
                self.counters["score_tail_evaluations"] += 1
            else:
                epsilon = {"C": 0., "Q10": .1, "Q05": .05}[self.arm]
                probabilities = q_probabilities(answer["c_index"], epsilon)
            choice = answer["c_index"]
        else:
            probabilities = answer["probabilities"]
            if self.arm == "Bstar_L0":
                probabilities = categorical_probabilities(answer["logits"].astype(np.float64) / 2.)
            choice = answer["action_index"]
        uniform = -1.
        if self.arm != "C":
            uniform = indexed_uniform(self.sampling_root, self.world, tick, self.agent)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        chosen_probability = float(probabilities[choice])
        if not np.isfinite(chosen_probability) or not 0 < chosen_probability <= 1:
            raise FloatingPointError("invalid chosen behavior probability")
        positive = probabilities > 0
        entropy = float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))
        answer.update(action_index=choice, command=COMMANDS[choice].copy(),
                      probabilities=probabilities, innovation=uniform, entropy=entropy,
                      behavior_entropy=entropy if self.arm != "C" else 0.,
                      chosen_probability=chosen_probability, logp=float(np.log(chosen_probability)))
        return answer
