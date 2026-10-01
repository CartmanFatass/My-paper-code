"""Private local joint policy and ordinary compositions, with no critic access."""
import copy

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import (
    COMMANDS, COUNTER_NAMES, _setup, _sinr, memo_key, original,
)
from experiments.candidates.uav_fleet_adaptation.b02.policies import FeatureMemo, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.fit import capped_count, gate_features, predict
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.policies import Policy as OriginalPolicy, _forward
from .contract import DETERMINISTIC, JOINT, PROGRAMS
from .learning import categorical_index54, joint_probabilities


EXTRA_COUNTERS = ("joint_requests", "joint_neural_rows", "frozen_neural_rows", "gate_prediction_rows",
                  "off_setup_links", "off_score_evaluations", "off_logical_ticks", "off_sinr_slots",
                  "initial_fidelity_rows")
POLICY_COUNTERS = (*COUNTER_NAMES, "sampled_draws", "neural_rows", "law_evaluations", "target_vectors",
                   "score_tail_evaluations", *EXTRA_COUNTERS)
ZERO_INDEX = int(np.flatnonzero(np.all(COMMANDS == 0, axis=1))[0])


def off_score(row):
    """One owned, explicitly charged setup repeat; original C stays untouched."""
    own, users, observed, peers = original._parse(row)
    n, p = len(users), len(peers)
    if n:
        present, unknown = _setup(own, users, observed, peers)
        with np.errstate(divide="ignore"):
            sinr = _sinr(np.zeros((1, 1, n), dtype=np.float64), present, unknown)
    else:
        sinr = np.empty((1, 1, 1 + p, 0), dtype=np.float64)
    scores, served = original.LocalController._score(None, sinr, np.ones(n, dtype=bool))
    if not np.isfinite([scores[0], served[0]]).all():
        raise FloatingPointError("invalid OFF local score")
    return float(scores[0]), float(served[0]), (1 + p) * n


def select_cj(answer, score, served):
    """C's navigation was already updated before this choice."""
    anchor = int(answer["c_index"])
    if np.all(answer["served"] == 0.) and served == 0.:
        return anchor, capped_count(answer) == 0
    if served > 0. and score > float(np.max(answer["scores"])):
        return ZERO_INDEX, True
    return anchor, False


def _entropy(probabilities):
    positive = probabilities > 0
    return float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))


class Policy:
    """One physical agent's episode-local caches, never shared across updates."""
    def __init__(self, program, parent, gate, *, actor=None, world, agent, sampling_root,
                 initial=False):
        if program not in PROGRAMS or ((program in JOINT) != (actor is not None)):
            raise ValueError("declared program/joint actor required")
        if ((program in DETERMINISTIC) != (sampling_root is None)) or type(agent) is not int or not 0 <= agent < 5:
            raise ValueError("private program sampling address invalid")
        self.program, self.parent, self.gate, self.actor = program, parent, gate, actor
        self.world, self.agent, self.root, self.initial = int(world), agent, sampling_root, bool(initial)
        if program in JOINT:
            self.base = FeatureMemo()
        else:
            family = "C" if program == "CJ" else program.split("_", 1)[0]
            original_actor = parent if family in ("P0", "Bstar0", "Hdirect") else None
            self.base = OriginalPolicy(family, original_actor, world=world, agent=agent, sampling_root=sampling_root)
        self.counters = self.base.counters
        for key in POLICY_COUNTERS:
            self.counters.setdefault(key, 0)
        self.joint_cache, self.prior_cache = {}, {}

    def _prior(self, key, answer):
        if key not in self.prior_cache:
            logits, hidden = _forward(self.parent, answer["features"])
            self.prior_cache[key] = (logits, hidden)
            self.counters["frozen_neural_rows"] += 1
            self.counters["cache_array_bytes"] += logits.nbytes + hidden.nbytes
        logits, hidden = (value.copy() for value in self.prior_cache[key])
        prediction = float(predict(self.gate, gate_features(dict(features=answer["features"], hidden=hidden), "HIDDEN")))
        self.counters["gate_prediction_rows"] += 1
        return logits, hidden, prediction

    def query(self, row, tick, nav):
        eligible = self.agent == (tick // 4) % 5
        answer = self.base.query(row, tick, nav)
        count = capped_count(answer)
        prediction, preferred, requested_off = 0., False, False
        prior = np.ones(2, dtype=np.float64)
        answer.update(eligible=bool(eligible), off_score=0., off_service=0., off_evaluated=False,
                      init_logit_max_abs=0., init_probability_max_abs=0., init_tv=0., initial_fidelity=False)
        if self.program in JOINT:
            self.counters["joint_requests"] += 1
            key = memo_key(row, nav)
            if key not in self.joint_cache:
                with torch.inference_mode():
                    logits = self.actor(torch.from_numpy(answer["features"]).reshape(1, 114))[0].cpu().numpy().copy()
                if logits.shape != (54,) or logits.dtype != np.float32 or not np.isfinite(logits).all():
                    raise FloatingPointError("finite joint54 FP32 logits required")
                self.joint_cache[key] = logits
                self.counters["joint_neural_rows"] += 1
                self.counters["cache_array_bytes"] += logits.nbytes
            logits = self.joint_cache[key].copy()
            prior_logits, prior_hidden = np.zeros(27, dtype=np.float32), np.zeros(128, dtype=np.float32)
            if eligible:
                prior_logits, prior_hidden, prediction = self._prior(key, answer)
                preferred = prediction > 0.
                prior = np.array([.1, .9] if preferred else [.9, .1], dtype=np.float64)
            probabilities = joint_probabilities(logits, prior, eligible)
            uniform = indexed_uniform(self.root, self.world, tick, self.agent)
            choice = categorical_index54(probabilities, uniform)
            requested_off = choice >= 27
            self.counters["sampled_draws"] += 1
            self.counters["law_evaluations"] += 1
            answer.update(logits=logits, prior=prior, prior_logits=prior_logits, prior_hidden=prior_hidden,
                          probabilities=probabilities, innovation=uniform, action_index=choice,
                          command=COMMANDS[choice % 27].copy(), entropy=_entropy(probabilities))
            if eligible and self.initial:
                p = np.exp(prior_logits.astype(np.float64) - np.max(prior_logits.astype(np.float64)))
                p /= p.sum(dtype=np.float64)
                product = np.r_[p * prior[0], p * prior[1]]
                answer.update(initial_fidelity=True,
                              init_logit_max_abs=float(np.max(np.abs(logits.astype(np.float64) - np.tile(prior_logits, 2)))),
                              init_probability_max_abs=float(np.max(np.abs(probabilities - product))),
                              init_tv=float(.5 * np.abs(probabilities - product).sum()))
                self.counters["initial_fidelity_rows"] += 1
        elif self.program == "CJ":
            if eligible:
                score, served, links = off_score(row)
                choice, requested_off = select_cj(answer, score, served)
                self.counters["off_setup_links"] += links
                self.counters["off_score_evaluations"] += 1
                self.counters["off_logical_ticks"] += 4
                self.counters["off_sinr_slots"] += links
                probabilities = np.zeros(27, dtype=np.float64)
                probabilities[choice] = 1.
                answer.update(action_index=choice, command=COMMANDS[choice].copy(), probabilities=probabilities,
                              entropy=0., off_score=score, off_service=served, off_evaluated=True)
        elif eligible:
            gate_kind = self.program.split("_", 1)[1]
            if gate_kind == "HIDDEN":
                prediction = float(predict(self.gate, gate_features(answer, "HIDDEN")))
                self.counters["gate_prediction_rows"] += 1
                preferred = prediction > 0.
                requested_off = preferred
            elif gate_kind == "ZERO":
                requested_off = count == 0
            elif gate_kind != "A":
                raise ValueError("undeclared ordinary gate")
        if requested_off and not eligible:
            raise AssertionError("noneligible transmitter requested OFF")
        probabilities = answer["probabilities"]
        motion = probabilities[:27] + probabilities[27:] if self.program in JOINT else probabilities
        off_probability = float(probabilities[27:].sum()) if self.program in JOINT else float(requested_off)
        choice = int(answer["action_index"])
        answer.update(motion_index=choice % 27, gate_count=count, gate_prediction=prediction,
                      hidden_preferred_off=bool(preferred), requested_off=bool(requested_off),
                      off_probability=off_probability, motion_entropy=_entropy(motion),
                      gate_entropy=_entropy(np.array([1. - off_probability, off_probability])),
                      logp=float(np.log(probabilities[choice])))
        return answer
