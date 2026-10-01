"""Original N5 motion laws, retaining hidden features from the paid forward."""
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import (
    COMMANDS, COUNTER_NAMES, MemoC, _tick, memo_key,
)
from experiments.candidates.uav_fleet_adaptation.b02.model import Student
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    StudentPolicy, categorical_index, categorical_probabilities, indexed_uniform,
)
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.targets import build_targets
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import (
    q_probabilities, score_tail_probabilities,
)

PARENTS = ("P0", "Bstar0", "Hdirect", "G", "Q10", "C")


def _forward(actor, features):
    """Observe the second ReLU without changing the original forward sequence.

    The hook exists only during this synchronous call; it retains no shared
    state. Each caller owns the returned arrays and its episode-local cache.
    """
    hidden = []
    handle = actor.network[3].register_forward_hook(
        lambda module, inputs, output: hidden.append(output[0].cpu().numpy().copy()))
    try:
        with torch.inference_mode():
            logits = actor(torch.from_numpy(features).reshape(1, 114))[0].cpu().numpy().copy()
    finally:
        handle.remove()
    if (len(hidden) != 1 or hidden[0].shape != (128,) or hidden[0].dtype != np.float32
            or logits.shape != (27,) or logits.dtype != np.float32
            or not np.isfinite(hidden[0]).all() or not np.isfinite(logits).all()):
        raise FloatingPointError("finite original FP32 logits/second-ReLU features required")
    return logits, hidden[0]


class _HiddenStudentPolicy(StudentPolicy):
    def query(self, row, tick, nav):
        _tick(tick)
        key = memo_key(row, nav)
        # Delegate the helper/cache/law program unchanged. A local hook on the
        # actor captures the paid miss forward; no hook runs on a cache hit.
        hidden = []
        handle = None
        if key not in self.cache:
            handle = self.actor.network[3].register_forward_hook(
                lambda module, inputs, output: hidden.append(output[0].cpu().numpy().copy()))
        try:
            result = super().query(row, tick, nav)
        finally:
            if handle is not None:
                handle.remove()
        if not result["memo_hit"]:
            if (len(hidden) != 1 or hidden[0].shape != (128,) or hidden[0].dtype != np.float32
                    or not np.isfinite(hidden[0]).all()):
                raise FloatingPointError("finite original second-ReLU features required")
            self.cache[key]["hidden"] = hidden[0]
            self.counters["cache_array_bytes"] += hidden[0].nbytes
            result["hidden"] = hidden[0].copy()
        return result


class Policy:
    def __init__(self, parent, actor, *, world, agent, sampling_root):
        if parent not in PARENTS or ((actor is None) != (parent in ("G", "Q10", "C"))):
            raise ValueError("B08 parent/actor contract violated")
        if actor is not None and (not isinstance(actor, Student) or hasattr(actor, "count_weight")):
            raise ValueError("B08 requires the original Student without a count branch")
        if ((parent == "C") != (sampling_root is None)) or type(agent) is not int or not 0 <= agent < 5:
            raise ValueError("B08 sampling address contract violated")
        self.parent, self.actor = parent, actor
        self.world, self.agent, self.root = int(world), agent, sampling_root
        self.base = (_HiddenStudentPolicy(actor, world=world, agent=agent, sampled=False)
                     if parent in ("P0", "Bstar0") else MemoC())
        self.counters = self.base.counters
        for name in (*COUNTER_NAMES, "sampled_draws", "neural_rows"):
            self.counters.setdefault(name, 0)
        self.counters.update(law_evaluations=0, target_vectors=0, score_tail_evaluations=0)
        self.logit_cache = {}

    def query(self, old_row, tick, nav):
        result = self.base.query(old_row, tick, nav)
        if self.parent in ("P0", "Bstar0"):
            probabilities = result["probabilities"]
            if self.parent == "Bstar0":
                probabilities = categorical_probabilities(result["logits"].astype(np.float64) / 2.)
        else:
            result["c_index"] = int(result["action_index"])
            if self.parent == "Hdirect":
                key = memo_key(old_row, nav)
                if key not in self.logit_cache:
                    logits, hidden = _forward(self.actor, result["features"])
                    self.logit_cache[key] = (logits, hidden)
                    self.counters["neural_rows"] += 1
                    self.counters["cache_array_bytes"] += logits.nbytes + hidden.nbytes
                result["logits"], result["hidden"] = (v.copy() for v in self.logit_cache[key])
                parent = categorical_probabilities(result["logits"].astype(np.float64))
                _, probabilities = build_targets(parent, result["scores"], result["c_index"])
                result["parent_probabilities"] = parent
                self.counters["target_vectors"] += 2
            elif self.parent == "G":
                probabilities = score_tail_probabilities(result["scores"], result["c_index"])
                self.counters["score_tail_evaluations"] += 1
            else:
                probabilities = q_probabilities(result["c_index"], 0. if self.parent == "C" else .1)
        uniform = -1.
        choice = result["action_index"]
        if self.parent != "C":
            uniform = indexed_uniform(self.root, self.world, tick, self.agent)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        positive = probabilities > 0
        self.counters["law_evaluations"] += 1
        result.update(action_index=int(choice), command=COMMANDS[choice].copy(), probabilities=probabilities,
                      innovation=uniform, entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result
