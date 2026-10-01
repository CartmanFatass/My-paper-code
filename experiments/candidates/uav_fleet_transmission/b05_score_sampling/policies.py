"""Fixed B05 laws over the frozen local C scores and one-row student logits."""
from numbers import Integral, Real

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, MemoC
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    StudentPolicy as OriginalStudentPolicy,
    categorical_index,
    categorical_probabilities,
    indexed_uniform,
)

ARMS = ("C", "Q10", "Q05", "G", "S_L0", "S_L1", "Bstar_L0")
ORDINARY_ARMS = ARMS[:4]
STUDENT_ARMS = ARMS[4:]
TAU = 0.014


def _c_index(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or not 0 <= value < 27:
        raise ValueError("C index must be an integer in 0..26")
    return int(value)


def q_probabilities(c_index, epsilon):
    """Keep the original ordered FP64 Q law, including its rounding."""
    c_index = _c_index(c_index)
    if (isinstance(epsilon, (bool, np.bool_)) or not isinstance(epsilon, Real)
            or not np.isfinite(epsilon) or not 0 <= epsilon <= 1):
        raise ValueError("epsilon must be finite and in 0..1")
    probabilities = np.full(27, epsilon / 26., dtype=np.float64)
    probabilities[c_index] = 1. - epsilon
    return probabilities


def score_tail_probabilities(scores, c_index):
    """Give C .9 mass and distribute .1 over its 26 score-weighted alternatives."""
    c_index = _c_index(c_index)
    if np.iscomplexobj(scores):
        raise ValueError("finite real 27-score vector required")
    scores = np.asarray(scores, dtype=np.float64)
    if scores.shape != (27,) or not np.isfinite(scores).all():
        raise ValueError("finite real 27-score vector required")
    if np.all(scores == scores[0]):
        return q_probabilities(c_index, .1)
    alternatives = np.arange(27) != c_index
    tail = scores[alternatives]
    # Extreme finite inputs may yield -inf differences, whose exp is exactly
    # zero. The maximum alternative always retains weight one; no floor is used.
    with np.errstate(over="ignore", under="ignore"):
        weights = np.exp((tail - np.max(tail)) / TAU)
    probabilities = np.empty(27, dtype=np.float64)
    probabilities[alternatives] = .1 * (weights / weights.sum(dtype=np.float64))
    probabilities[c_index] = .9
    return probabilities


class FixedPolicy:
    """Episode-private frozen cache; draw once on every stochastic query."""
    def __init__(self, arm, actor, *, world, agent, sampling_root):
        if arm not in ARMS:
            raise ValueError("unknown B05 arm")
        self.arm = arm
        self.world, self.agent, self.sampling_root = int(world), int(agent), int(sampling_root)
        if arm in ORDINARY_ARMS:
            if actor is not None:
                raise ValueError("ordinary arms must not receive an actor")
            self.base = MemoC()
        else:
            if actor is None:
                raise ValueError("student arms require an actor")
            self.base = OriginalStudentPolicy(actor, world=world, agent=agent, sampled=False,
                                              sampling_root=sampling_root)
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
