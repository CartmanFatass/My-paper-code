"""Own-history B07 laws with the unchanged one-uniform flat-CDF decoder."""
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_index, categorical_probabilities
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import COMMANDS, MemoC, memo_key
from experiments.candidates.uav_fleet_adaptation.b06_count_development.policies import StudentPolicy, indexed_uniform
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import q_probabilities, score_tail_probabilities
from .contract import ARMS, DIRECT, NEURAL, ORDINARY
from .targets import build_targets


class Policy:
    def __init__(self, arm, actor, *, world, agent, sampling_root):
        if arm not in ARMS or ((actor is None) != (arm in ORDINARY)):
            raise ValueError("B07 arm/actor contract violated")
        if ((arm == "C") != (sampling_root is None)) or type(agent) is not int or not 0 <= agent < 5:
            raise ValueError("B07 sampling address contract violated")
        self.arm, self.actor = arm, actor
        self.world, self.agent, self.root = int(world), agent, sampling_root
        self.base = (StudentPolicy(actor, n=5, world=world, agent=agent, sampling_root=None,
                                   temperature=2. if arm == "Bstar0" else 1.)
                     if arm in NEURAL else MemoC(5))
        self.counters = self.base.counters
        self.counters.setdefault("sampled_draws", 0)
        self.counters.setdefault("neural_rows", 0)
        self.counters.update(law_evaluations=0, target_vectors=0, score_tail_evaluations=0)
        self.logit_cache = {}
        self.count = torch.tensor([5], dtype=torch.int64)

    def query(self, observation, tick, nav):
        result = self.base.query(observation, tick, nav)
        if self.arm in NEURAL:
            probabilities = result["probabilities"]
        else:
            result["c_index"] = int(result["action_index"])
            if self.arm in DIRECT:
                key = memo_key(observation, nav, 5)
                if key not in self.logit_cache:
                    with torch.inference_mode():
                        logits = self.actor(torch.from_numpy(result["features"]).reshape(1, 114), self.count)[0].numpy().copy()
                    if not np.isfinite(logits).all():
                        raise FloatingPointError("nonfinite direct P0 logits")
                    self.logit_cache[key] = logits
                    self.counters["neural_rows"] += 1
                    self.counters["cache_array_bytes"] += logits.nbytes
                result["logits"] = self.logit_cache[key].copy()
                parent = categorical_probabilities(result["logits"].astype(np.float64))
                t, h = build_targets(parent, result["scores"], result["c_index"])
                result["parent_probabilities"] = parent
                probabilities = t if self.arm == "Tdirect" else h
                self.counters["target_vectors"] += 2
            elif self.arm == "G":
                probabilities = score_tail_probabilities(result["scores"], result["c_index"])
                self.counters["score_tail_evaluations"] += 1
            else:
                probabilities = q_probabilities(result["c_index"], {"C": 0., "Q10": .1, "Q05": .05}[self.arm])
        uniform = -1.
        choice = result["action_index"]
        if self.arm != "C":
            uniform = indexed_uniform(self.root, self.world, tick, self.agent, 5)
            choice = categorical_index(probabilities, uniform)
            self.counters["sampled_draws"] += 1
        positive = probabilities > 0
        self.counters["law_evaluations"] += 1
        result.update(action_index=int(choice), command=COMMANDS[choice].copy(), probabilities=probabilities,
                      innovation=uniform, entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        return result
