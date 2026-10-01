"""Saved-data law reconstruction independent of B09 Member/head/tracker code."""
from copy import deepcopy

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav, memo_key
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reference import (
    ReferencePolicy, _capture_second_relu, _hidden, _softmax,
)
from experiments.candidates.uav_local_peer_forecast.reader import decode, match_frames, prepare_score, ranking
from .policies import ALL_COUNTS


def history_empty():
    return dict(descriptor=np.zeros(16, dtype=np.float32), matches=np.full(4, -1, dtype=np.int64),
                delta=np.zeros((4, 3), dtype=np.float64), gate_counts=np.zeros(4, dtype=np.int64), n_peers=0)


def focal_context(features, hidden, tick, history=None):
    context = np.zeros(259, dtype=np.float32)
    context[:114], context[114:242], context[242] = features, hidden, tick / 256.
    if history is not None:
        context[243:] = history
    return context


def focal_logits(context, base_logits, state):
    # Reconstruct the selected single-row arithmetic directly, not via ResponseHead.
    x = torch.from_numpy(np.asarray(context, dtype=np.float32)).clone(memory_format=torch.contiguous_format)
    base = torch.from_numpy(np.asarray(base_logits, dtype=np.float32)).clone(memory_format=torch.contiguous_format)
    with torch.inference_mode():
        logits = base + .5 * torch.tanh(torch.mv(state["W"], x) + state["b"])
    if logits.shape != (27,) or logits.dtype != torch.float32 or not torch.isfinite(logits).all():
        raise FloatingPointError("invalid reconstructed focal logits")
    return logits.numpy().copy()


def decode_law(probabilities, uniform):
    cdf = np.cumsum(probabilities, dtype=np.float64)
    cdf[-1] = 1.
    return int(np.searchsorted(cdf, uniform, side="right"))


class ReferenceMember:
    def __init__(self, law, actors, *, world, agent, root, head_state=None):
        self.law, self.world, self.agent, self.root = law, int(world), int(agent), int(root)
        self.head_state = head_state
        self.history, self.previous, self.clock = history_empty(), np.empty((0, 3)), -1
        self.own_counts = dict.fromkeys(ALL_COUNTS, 0)
        self.last, self.nav = None, None
        if law in ("F", "H"):
            if agent != 0 or head_state is None:
                raise ValueError("reference requires one ego head state")
            self.base = StudentPolicy(actors["P0"], world=world, agent=agent, sampled=False)
        elif law not in ("V", "R"):
            parent = "P0" if law == "P1" else law
            actor = actors["P1"] if law == "P1" else actors["P0"] if law in ("P0", "Bstar0", "Hdirect") else None
            self.base = ReferencePolicy(parent, actor, world=world, agent=agent, sampling_root=None if law == "C" else root)

    @property
    def counters(self):
        result = dict.fromkeys(ALL_COUNTS, 0)
        if self.law not in ("V", "R"):
            result.update(self.base.counters)
        for key, value in self.own_counts.items():
            result[key] += value
        return result

    def ingest(self, row, tick):
        if self.law not in ("H", "V", "R"):
            return deepcopy(self.history)
        if tick != self.clock + 1 or float(row[-1]) != tick / 256.:
            raise ValueError("reference consecutive original clock required")
        own, users, sinr, peers = decode(row)
        matches, delta, gates = match_frames(peers, self.previous)
        n, p = len(users), len(peers)
        result = history_empty()
        result.update(n_peers=p)
        result["matches"][:p], result["delta"][:p], result["gate_counts"][:p] = matches, delta, gates
        descriptor = result["descriptor"].reshape(4, 4)
        for i in range(p):
            descriptor[i, :3] = delta[i] / 30.
            descriptor[i, 3] = float(matches[i] >= 0)
        c = self.own_counts
        c["tracker_ingests"] += 1
        c["adjacent_updates"] += int(tick > 0)
        c["pair_gates"] += len(peers) * len(self.previous)
        c["matched_rows"] += int((matches >= 0).sum())
        m = int(np.any(delta != 0, axis=1).sum())
        c["moving_rows"] += m
        self.previous, self.history, self.clock = peers.copy(), result, int(tick)
        if self.law in ("V", "R") and tick % 4 == 0:
            if self.nav is None:
                self.nav = initial_nav(row)
            before = self.nav
            prepared = prepare_score(own, users, sinr, peers)
            actual = ranking(prepared, delta, 1 if self.law == "V" else -1, before)
            choice = int(actual["choice"])
            features = np.zeros(114, dtype=np.float32)
            features[:103], features[103 + before], features[-1] = row[:103], 1., actual["fallback"]
            probabilities = np.zeros(27, dtype=np.float64)
            probabilities[choice] = 1.
            self.nav = int(actual["nav"])
            self.last = dict(features=features, action_index=choice, next_nav=self.nav, fallback=bool(actual["fallback"]),
                             scores=actual["scores"], served=actual["served"], c_index=choice, n_current=n, n_peers=p,
                             probabilities=probabilities, innovation=-1., entropy=0., memo_hit=False, nav_pre=before)
            for key, amount in (("requests", 1), ("misses", 1), ("trajectories", 27), ("model_ticks", 108),
                                ("objective_reductions", 108), ("candidate_links", 108 * n), ("setup_links", (1 + p) * n),
                                ("fallback_decisions", int(actual["fallback"])),
                                ("moving_peer_ticks", 4 * m if n else 0), ("moving_link_evaluations", 4 * m * n)):
                c[key] += amount
            if n:
                modeled = 10. * np.log10(prepared["present"][0] / (
                    prepared["present"][1:].sum(axis=0) + prepared["unknown"] + 1e-8))
                c["calibration_discrepancy_rows"] += int(np.count_nonzero(np.abs(modeled - sinr) > 1e-4))
        return deepcopy(self.history)

    def query(self, row, tick, nav):
        if self.law in ("V", "R"):
            if self.clock != tick or self.last["nav_pre"] != nav:
                raise AssertionError("reference private V/R navigation changed")
            answer = deepcopy(self.last)
            self.own_counts["law_evaluations"] += 1
        elif self.law in ("F", "H"):
            key = memo_key(row, nav)
            if key not in self.base.cache:
                with _capture_second_relu(self.base.actor) as captured:
                    answer = self.base.query(row.copy(), tick, nav)
                hidden = _hidden(captured)
                self.base.cache[key]["hidden"] = hidden
                self.base.counters["cache_array_bytes"] += hidden.nbytes
                answer["hidden"] = hidden.copy()
            else:
                answer = self.base.query(row.copy(), tick, nav)
            descriptor = self.history["descriptor"] if self.law == "H" else None
            if self.law == "H" and self.clock != tick:
                raise AssertionError("reference history missing current native row")
            context = focal_context(answer["features"], answer["hidden"], tick, descriptor)
            answer["base_logits"] = answer["logits"].copy()
            answer["context"] = context
            answer["logits"] = focal_logits(context, answer["base_logits"], self.head_state)
            probabilities = _softmax(answer["logits"])
            uniform = float(np.random.default_rng(np.random.SeedSequence([self.root, self.world, int(tick), self.agent])).random())
            choice = decode_law(probabilities, uniform)
            positive = probabilities > 0
            answer.update(probabilities=probabilities, innovation=uniform, action_index=choice,
                          entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
            for key in ("head_rows", "sampled_draws", "law_evaluations"):
                self.own_counts[key] += 1
        else:
            answer = self.base.query(row.copy(), tick, nav)
        answer["command"] = COMMANDS[answer["action_index"]].copy()
        # Independently named neutral storage values for programs that do not compute a field.
        for name, shape, dtype in (("logits", (27,), np.float32), ("hidden", (128,), np.float32),
                                   ("scores", (27,), np.float64), ("served", (27,), np.float64),
                                   ("parent_probabilities", (27,), np.float64)):
            answer.setdefault(name, np.zeros(shape, dtype=dtype))
        answer.setdefault("c_index", -1)
        answer["logp"] = float(np.log(answer["probabilities"][answer["action_index"]]))
        return answer
