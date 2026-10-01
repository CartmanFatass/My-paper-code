"""Independent saved-row laws; no B10 collector/policy answer is reused."""
import numpy as np
import torch
from torch.nn import functional as F

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, COUNTER_NAMES, memo_key, original
from experiments.candidates.uav_fleet_adaptation.b02.policies import FeatureMemo
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reference import ReferencePolicy, _capture_second_relu, _hidden
from .contract import DETERMINISTIC, JOINT, PROGRAMS


EXTRA = ("joint_requests", "joint_neural_rows", "frozen_neural_rows", "gate_prediction_rows",
         "off_setup_links", "off_score_evaluations", "off_logical_ticks", "off_sinr_slots", "initial_fidelity_rows")


def hidden_vector(features, hidden):
    count = min(sum(float(features[3 + 3 * slot + 2]) > 0 for slot in range(20)), 10)
    return np.concatenate((features.astype(np.float64), np.eye(11, dtype=np.float64)[count],
                           hidden.astype(np.float64))), count


def density(logits, prior, eligible):
    """Separate reconstruction of the declared finite normalization."""
    z = np.asarray(logits, dtype=np.float64).copy()
    if z.shape != (54,) or not np.isfinite(z).all():
        raise ValueError("reference requires finite logits54")
    if eligible:
        z += np.repeat(np.log(np.asarray(prior, dtype=np.float64)), 27)
        weights = np.exp(z - np.max(z))
    else:
        weights = np.zeros(54, dtype=np.float64)
        weights[:27] = np.exp(z[:27] - np.max(z[:27]))
    return weights / weights.sum(dtype=np.float64)


def draw(probabilities, uniform):
    cumulative = np.minimum(np.cumsum(probabilities, dtype=np.float64), 1.)
    support = np.flatnonzero(probabilities > 0.)
    if not len(support):
        raise ValueError("empty reference support")
    cumulative[support[-1]:] = 1.
    selected = int(np.searchsorted(cumulative, uniform, side="right"))
    if selected >= len(probabilities) or probabilities[selected] <= 0.:
        raise AssertionError("reference selected unavailable category")
    return selected


def joint_forward(actor, features):
    """Rebuild the three original affine/ReLU stages from saved tensors."""
    state = actor.state_dict()
    x = torch.from_numpy(np.asarray(features, dtype=np.float32)).reshape(1, 114).clone(memory_format=torch.contiguous_format)
    with torch.inference_mode():
        x = F.relu(F.linear(x, state["network.0.weight"], state["network.0.bias"]))
        x = F.relu(F.linear(x, state["network.2.weight"], state["network.2.bias"]))
        x = F.linear(x, state["network.4.weight"], state["network.4.bias"])
    return x[0].numpy().copy()


def _off(row):
    own, users, observed, peers = original._parse(row)
    n, p = len(users), len(peers)
    if n:
        present = original._power(np.concatenate((own[None, :], peers), axis=0), users)
        residual = np.zeros(n, dtype=np.float64)
        if p < 4:
            residual = np.maximum(present[0] / (10. ** (observed / 10.)) - present[1:].sum(axis=0) - original.NOISE, 0.)
        power = present.copy()
        power[0] = 0.
        denominator = power.sum(axis=0, keepdims=True) - power + residual + original.NOISE
        with np.errstate(divide="ignore"):
            sinr = 10. * np.log10(power / denominator)
        chosen = np.zeros_like(sinr, dtype=bool)
        for station in range(1 + p):
            order = np.argsort(-sinr[station], kind="stable")[:10]
            chosen[station, order] = sinr[station, order] >= original.THRESHOLD
        served = float(chosen.sum())
        quality = float(np.where(chosen, np.clip((sinr - 3.) / 30., 0., 1.), 0.).sum() / max(served, 1.))
        score = .7 * served / 50. + .3 * quality
    else:
        served = score = 0.
    return score, served, (1 + p) * n


def _entropy(p):
    positive = p > 0.
    return float(-np.sum(p[positive] * np.log(p[positive])))


class Reference:
    def __init__(self, program, parent, gate, *, actor=None, world, agent, sampling_root, initial=False):
        if program not in PROGRAMS or ((program in JOINT) != (actor is not None)):
            raise ValueError("reference program binding differs")
        if (program in DETERMINISTIC) != (sampling_root is None):
            raise ValueError("reference randomness domain differs")
        self.program, self.parent, self.gate, self.actor = program, parent, gate, actor
        self.world, self.agent, self.root, self.initial = int(world), int(agent), sampling_root, bool(initial)
        if program in JOINT:
            self.base = FeatureMemo()
        else:
            family = "C" if program == "CJ" else program.split("_", 1)[0]
            self.base = ReferencePolicy(family, parent if family in ("P0", "Bstar0", "Hdirect") else None,
                                        world=world, agent=agent, sampling_root=sampling_root)
        self.counters = self.base.counters
        for key in (*COUNTER_NAMES, "sampled_draws", "neural_rows", "law_evaluations", "target_vectors", "score_tail_evaluations", *EXTRA):
            self.counters.setdefault(key, 0)
        self.outputs, self.frozen = {}, {}

    def query(self, row, tick, nav):
        answer = self.base.query(row, tick, nav)
        eligible = self.agent == (tick // 4) % 5
        count = min(sum(float(answer["features"][3 + 3 * slot + 2]) > 0 for slot in range(20)), 10)
        prediction, preferred, off = 0., False, False
        answer.update(eligible=eligible, off_score=0., off_service=0., off_evaluated=False,
                      initial_fidelity=False, init_logit_max_abs=0., init_probability_max_abs=0., init_tv=0.)
        if self.program in JOINT:
            self.counters["joint_requests"] += 1
            key = memo_key(row, nav)
            if key not in self.outputs:
                self.outputs[key] = joint_forward(self.actor, answer["features"])
                self.counters["joint_neural_rows"] += 1
                self.counters["cache_array_bytes"] += self.outputs[key].nbytes
            logits = self.outputs[key].copy()
            prior = np.ones(2, dtype=np.float64)
            prior_logits, hidden = np.zeros(27, dtype=np.float32), np.zeros(128, dtype=np.float32)
            if eligible:
                if key not in self.frozen:
                    with _capture_second_relu(self.parent) as captured, torch.inference_mode():
                        original_logits = self.parent(torch.from_numpy(answer["features"]).reshape(1, 114))[0].numpy().copy()
                    original_hidden = _hidden(captured)
                    self.frozen[key] = (original_logits, original_hidden)
                    self.counters["frozen_neural_rows"] += 1
                    self.counters["cache_array_bytes"] += original_logits.nbytes + original_hidden.nbytes
                prior_logits, hidden = (x.copy() for x in self.frozen[key])
                vector, _ = hidden_vector(answer["features"], hidden)
                prediction = float(((vector - self.gate["mean"]) / self.gate["scale"]) @ self.gate["coefficients"] + self.gate["intercept"])
                preferred = prediction > 0.
                prior = np.array([.1, .9] if preferred else [.9, .1], dtype=np.float64)
                self.counters["gate_prediction_rows"] += 1
            p = density(logits, prior, eligible)
            uniform = float(np.random.default_rng(np.random.SeedSequence([self.root, self.world, tick, self.agent])).random())
            selected = draw(p, uniform)
            off = selected >= 27
            answer.update(logits=logits, prior=prior, prior_logits=prior_logits, prior_hidden=hidden,
                          probabilities=p, innovation=uniform, action_index=selected,
                          command=COMMANDS[selected % 27].copy(), entropy=_entropy(p))
            self.counters["sampled_draws"] += 1
            self.counters["law_evaluations"] += 1
            if eligible and self.initial:
                parent_p = np.exp(prior_logits.astype(np.float64) - np.max(prior_logits.astype(np.float64)))
                parent_p /= parent_p.sum(dtype=np.float64)
                product = np.concatenate((parent_p * prior[0], parent_p * prior[1]))
                answer.update(initial_fidelity=True,
                              init_logit_max_abs=float(np.abs(logits.astype(np.float64) - np.tile(prior_logits, 2)).max()),
                              init_probability_max_abs=float(np.abs(p - product).max()),
                              init_tv=float(.5 * np.abs(p - product).sum()))
                self.counters["initial_fidelity_rows"] += 1
        elif self.program == "CJ" and eligible:
            score, served, links = _off(row)
            selected = int(answer["c_index"])
            if np.all(answer["served"] == 0.) and served == 0.:
                off = count == 0
            elif served > 0. and score > float(np.max(answer["scores"])):
                off = True
                selected = next(i for i, cmd in enumerate(COMMANDS) if not np.any(cmd))
            p = np.zeros(27, dtype=np.float64)
            p[selected] = 1.
            answer.update(action_index=selected, command=COMMANDS[selected].copy(), probabilities=p,
                          entropy=0., off_score=score, off_service=served, off_evaluated=True)
            self.counters["off_setup_links"] += links
            self.counters["off_score_evaluations"] += 1
            self.counters["off_logical_ticks"] += 4
            self.counters["off_sinr_slots"] += links
        elif self.program != "CJ" and eligible:
            kind = self.program.split("_", 1)[1]
            if kind == "HIDDEN":
                vector, _ = hidden_vector(answer["features"], answer["hidden"])
                prediction = float(((vector - self.gate["mean"]) / self.gate["scale"]) @ self.gate["coefficients"] + self.gate["intercept"])
                preferred = prediction > 0.
                off = preferred
                self.counters["gate_prediction_rows"] += 1
            elif kind == "ZERO":
                off = count == 0
            elif kind != "A":
                raise AssertionError("unknown reference gate")
        p, selected = answer["probabilities"], int(answer["action_index"])
        off_mass = float(p[27:].sum()) if self.program in JOINT else float(off)
        motion = p[:27] + p[27:] if self.program in JOINT else p
        answer.update(motion_index=selected % 27, gate_count=count, gate_prediction=prediction,
                      hidden_preferred_off=preferred, requested_off=off, off_probability=off_mass,
                      motion_entropy=_entropy(motion), gate_entropy=_entropy(np.array([1. - off_mass, off_mass])),
                      logp=float(np.log(p[selected])))
        return answer
