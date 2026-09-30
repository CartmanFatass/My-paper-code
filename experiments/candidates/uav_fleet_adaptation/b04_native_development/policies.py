"""Original lawful local kernels, with the eight predeclared deployment choices."""
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, MemoC
from experiments.candidates.uav_fleet_adaptation.b02.policies import (
    StudentPolicy as OriginalStudentPolicy, categorical_index, categorical_probabilities, indexed_uniform,
)
from .contract import candidate_spec


def entropy(probabilities):
    positive = probabilities > 0
    return float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))


class LocalPolicy:
    """One actual agent/history; cached values never include a sampled category."""
    def __init__(self, candidate, actor, *, world, agent, sampling_root):
        self.spec = candidate_spec(candidate)
        self.world, self.agent, self.sampling_root = int(world), int(agent), int(sampling_root)
        if self.spec["family"] == "S":
            if actor is None:
                raise ValueError("Student candidate requires its bound actor")
            # The frozen kernel computes one-row logits, features, original T=1
            # probabilities and greedy action. No private draw is hidden here.
            self.base = OriginalStudentPolicy(actor, world=world, agent=agent, sampled=False,
                                              sampling_root=sampling_root)
        else:
            if actor is not None:
                raise ValueError("ordinary C must not receive an actor")
            self.base = MemoC()
            self.base.counters["sampled_draws"] = 0
        self.counters = self.base.counters

    def query(self, observation, tick, nav):
        answer = self.base.query(observation, tick, nav)
        if self.spec["family"] == "C":
            answer["c_index"] = answer["action_index"]
            epsilon = self.spec["epsilon"]
            probabilities = np.full(27, epsilon / 26., dtype=np.float64)
            probabilities[answer["c_index"]] = 1. - epsilon
            sampled = epsilon > 0
            choice = answer["c_index"]
        else:
            temperature = self.spec["temperature"]
            probabilities = answer["probabilities"]
            if temperature not in (None, 1.):
                probabilities = categorical_probabilities(answer["logits"].astype(np.float64) / temperature)
            sampled = temperature is not None
            choice = int(np.argmax(answer["logits"]))
        uniform = -1.
        if sampled:
            uniform = indexed_uniform(self.sampling_root, self.world, tick, self.agent)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        chosen_probability = float(probabilities[choice]) if sampled else 1.
        if not 0 < chosen_probability <= 1 or not np.isfinite(chosen_probability):
            raise FloatingPointError("invalid chosen behavior probability")
        answer.update(action_index=choice, command=COMMANDS[choice].copy(), probabilities=probabilities,
                      innovation=uniform, entropy=entropy(probabilities),
                      behavior_entropy=entropy(probabilities) if sampled else 0.,
                      chosen_probability=chosen_probability, logp=float(np.log(chosen_probability)))
        return answer


def shadow_on_features(actor, features, uniforms, positions, counts):
    """Frozen S on R's saved local histories; no analytic helper or radio call."""
    logits, probabilities, choices = [], [], []
    for feature, uniform in zip(features, uniforms):
        with torch.inference_mode():
            z = actor(torch.from_numpy(np.ascontiguousarray(feature, dtype=np.float32)).reshape(1, 114))[0].cpu().numpy().copy()
        counts["shadow_actor_rows"] += 1
        p = categorical_probabilities(z)
        logits.append(z); probabilities.append(p); choices.append(categorical_index(p, float(uniform)))
    choices = np.asarray(choices, dtype=np.int64)
    position = np.array(positions, dtype=np.float64, copy=True)
    path = []
    for _ in range(4):
        position = np.clip(position + COMMANDS[choices].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        counts["shadow_motion_ticks"] += 5
        path.append(position.copy())
    return {"logits": np.asarray(logits, dtype=np.float32), "probabilities": np.asarray(probabilities, dtype=np.float64),
            "action_index": choices, "positions": np.asarray(path, dtype=np.float64)}
