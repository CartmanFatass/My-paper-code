"""Reader reconstruction from original B02 primitives and frozen law formulas.

No collector or B08 policy implementation supplies this reader's answers.
Both direct target vectors are reconstructed on each law call, so the
two-vector counter also measures the reference's actual replay work.
"""
from contextlib import contextmanager
from numbers import Integral

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import (
    COMMANDS, COUNTER_NAMES, MemoC, _tick, memo_key,
)
from experiments.candidates.uav_fleet_adaptation.b02.model import Student
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy


@contextmanager
def _capture_second_relu(actor):
    captured = []
    def capture(module, inputs, output):
        captured.append(output[0].cpu().numpy().copy())
    handle = actor.network[3].register_forward_hook(capture)
    try:
        yield captured
    finally:
        handle.remove()


def _hidden(captured):
    if (len(captured) != 1 or captured[0].shape != (128,) or captured[0].dtype != np.float32
            or not np.isfinite(captured[0]).all()):
        raise FloatingPointError("reference requires finite paid original second-ReLU128")
    return captured[0]


def _softmax(logits, temperature=1.):
    values = np.asarray(logits, dtype=np.float64) / temperature
    if values.shape != (27,) or not np.isfinite(values).all():
        raise ValueError("reference requires finite logits27")
    weights = np.exp(values - np.max(values))
    return weights / weights.sum(dtype=np.float64)


def _ordinary_law(parent, scores, c_index):
    probabilities = np.full(27, (0. if parent == "C" else .1) / 26., dtype=np.float64)
    probabilities[c_index] = 1. if parent == "C" else .9
    if parent == "G" and not np.all(scores == scores[0]):
        alternatives = np.arange(27) != c_index
        tail = scores[alternatives]
        with np.errstate(over="ignore", under="ignore"):
            weights = np.exp((tail - np.max(tail)) / .014)
        probabilities[alternatives] = .1 * (weights / weights.sum(dtype=np.float64))
    return probabilities


def _direct_targets(parent, scores, c_index):
    """Independently reconstruct original B07 T/H, including unused T work."""
    for value in (parent, scores):
        if (not isinstance(value, np.ndarray) or value.shape != (27,)
                or value.dtype != np.float64 or not np.isfinite(value).all()):
            raise ValueError("reference direct targets require finite FP64 vectors27")
    if (np.any(parent < 0.) or abs(float(parent.sum(dtype=np.float64)) - 1.) > 5e-14
            or np.any(scores < -1e-14) or np.any(scores > 1. + 1e-14)
            or isinstance(c_index, (bool, np.bool_)) or not isinstance(c_index, Integral)
            or not 0 <= c_index < 27):
        raise ValueError("invalid reference direct parent/scores/C index")
    flat = bool(np.all(scores == scores[0]))
    if flat:
        target_t = parent.copy()
    else:
        weighted = parent * np.exp((scores - np.max(scores)) / .014)
        mass = float(weighted.sum(dtype=np.float64))
        if not np.isfinite(mass) or mass <= 0.:
            raise FloatingPointError("reference tilted parent has invalid mass")
        target_t = (1. - .1) * parent + .1 * (weighted / mass)
    target_h = (1. - .1) * parent
    target_h[int(c_index)] += .1
    for target in (target_t, target_h):
        if (not np.isfinite(target).all() or np.any(target < 0.)
                or abs(float(target.sum(dtype=np.float64)) - 1.) > 5e-14):
            raise FloatingPointError("reference direct target has invalid mass")
    if (np.any(target_t[parent == 0.] != 0.)
            or (flat and target_t.tobytes() != parent.tobytes())):
        raise AssertionError("reference T support/flat-copy contract changed")
    return target_t, target_h


class ReferencePolicy:
    def __init__(self, parent, actor, *, world, agent, sampling_root):
        if (parent not in ("P0", "Bstar0", "Hdirect", "G", "Q10", "C")
                or ((actor is None) != (parent in ("G", "Q10", "C")))):
            raise ValueError("reference parent/actor contract violated")
        if actor is not None and (not isinstance(actor, Student) or hasattr(actor, "count_weight")):
            raise ValueError("reference requires original Student without count branch")
        if ((parent == "C") != (sampling_root is None)) or type(agent) is not int or not 0 <= agent < 5:
            raise ValueError("reference sampling address contract violated")
        self.parent, self.actor = parent, actor
        self.world, self.agent, self.root = int(world), agent, sampling_root
        self.base = (StudentPolicy(actor, world=world, agent=agent, sampled=False)
                     if parent in ("P0", "Bstar0") else MemoC())
        self.counters = self.base.counters
        for name in (*COUNTER_NAMES, "neural_rows", "sampled_draws"):
            self.counters.setdefault(name, 0)
        self.counters.update(law_evaluations=0, target_vectors=0, score_tail_evaluations=0)
        self.hidden_cache = {}
        self.neural_cache = {}

    def query(self, old_row, tick, nav):
        _tick(tick)
        key = memo_key(old_row, nav)
        if self.parent in ("P0", "Bstar0"):
            if key not in self.hidden_cache:
                with _capture_second_relu(self.actor) as captured:
                    result = self.base.query(old_row, tick, nav)
                self.hidden_cache[key] = _hidden(captured)
                self.counters["cache_array_bytes"] += self.hidden_cache[key].nbytes
            else:
                result = self.base.query(old_row, tick, nav)
            result["hidden"] = self.hidden_cache[key].copy()
            probabilities = _softmax(result["logits"], 2. if self.parent == "Bstar0" else 1.)
        else:
            result = self.base.query(old_row, tick, nav)
            c_index = int(result["action_index"])
            result["c_index"] = c_index
            if self.parent == "Hdirect":
                if key not in self.neural_cache:
                    with _capture_second_relu(self.actor) as captured, torch.inference_mode():
                        logits = self.actor(torch.from_numpy(result["features"]).reshape(1, 114))[0].cpu().numpy().copy()
                    if logits.shape != (27,) or logits.dtype != np.float32 or not np.isfinite(logits).all():
                        raise FloatingPointError("reference requires finite original FP32 logits27")
                    hidden = _hidden(captured)
                    self.neural_cache[key] = (logits, hidden)
                    self.counters["neural_rows"] += 1
                    self.counters["cache_array_bytes"] += logits.nbytes + hidden.nbytes
                result["logits"], result["hidden"] = (array.copy() for array in self.neural_cache[key])
                result["parent_probabilities"] = _softmax(result["logits"])
                # Both formulas are paid on every query, even on cache hits.
                _, probabilities = _direct_targets(result["parent_probabilities"], result["scores"], c_index)
                self.counters["target_vectors"] += 2
            else:
                probabilities = _ordinary_law(self.parent, result["scores"], c_index)
                if self.parent == "G":
                    self.counters["score_tail_evaluations"] += 1
        if (not np.isfinite(probabilities).all() or np.any(probabilities < 0.)
                or abs(float(probabilities.sum(dtype=np.float64)) - 1.) > 5e-14):
            raise FloatingPointError("invalid reference law")
        innovation = -1.
        choice = int(result["action_index"])
        if self.parent != "C":
            innovation = float(np.random.default_rng(np.random.SeedSequence(
                [int(self.root), self.world, int(tick), self.agent])).random())
            cdf = np.cumsum(probabilities, dtype=np.float64)
            cdf[-1] = 1.
            choice = int(np.searchsorted(cdf, innovation, side="right"))
            self.counters["sampled_draws"] += 1
        positive = probabilities > 0
        self.counters["law_evaluations"] += 1
        result.update(action_index=choice, command=COMMANDS[choice].copy(), probabilities=probabilities,
                      innovation=innovation, entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result
