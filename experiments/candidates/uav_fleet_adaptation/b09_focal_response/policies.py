"""Episode-private programs; only immutable Student weights may be shared."""
from copy import deepcopy

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, COUNTER_NAMES, _features, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_index, categorical_probabilities, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.policies import Policy, _HiddenStudentPolicy
from experiments.candidates.uav_local_peer_forecast.controller import MotionController
from .context import PeerHistory, pack_context


EXTRA_COUNTS = ("neural_rows", "sampled_draws", "law_evaluations", "target_vectors", "score_tail_evaluations",
                "head_rows", "tracker_ingests", "adjacent_updates", "pair_gates", "matched_rows", "moving_rows",
                "moving_peer_ticks", "moving_link_evaluations", "calibration_discrepancy_rows", "fallback_decisions")
ALL_COUNTS = tuple(dict.fromkeys((*COUNTER_NAMES, *EXTRA_COUNTS)))


def empty_history():
    return dict(descriptor=np.zeros(16, dtype=np.float32), matches=np.full(4, -1, dtype=np.int64),
                delta=np.zeros((4, 3), dtype=np.float64), gate_counts=np.zeros(4, dtype=np.int64), n_peers=0)


def complete_answer(answer):
    """Storage sentinels are never used as policy inputs or extra queries."""
    result = deepcopy(answer)
    result.setdefault("logits", np.zeros(27, dtype=np.float32))
    result.setdefault("hidden", np.zeros(128, dtype=np.float32))
    result.setdefault("scores", np.zeros(27, dtype=np.float64))
    result.setdefault("served", np.zeros(27, dtype=np.float64))
    result.setdefault("c_index", -1)
    result.setdefault("parent_probabilities", np.zeros(27, dtype=np.float64))
    result.setdefault("context", np.zeros(259, dtype=np.float32))
    result.setdefault("base_logits", np.zeros(27, dtype=np.float32))
    chosen = float(result["probabilities"][result["action_index"]])
    if not np.isfinite(chosen) or chosen <= 0:
        raise FloatingPointError("selected law has zero/nonfinite mass")
    result["logp"] = float(np.log(chosen))
    return result


class Member:
    """One physical member's law, cache, tracker and private navigation state."""
    def __init__(self, law, actors, *, world, agent, root, head=None):
        self.law, self.world, self.agent, self.root = law, int(world), int(agent), int(root)
        self.head, self.history, self.last = head, empty_history(), None
        self.tick, self.requests = -1, 0
        self.tracker = PeerHistory() if law == "H" else None
        self.motion = MotionController(law) if law in ("V", "R") else None
        if law in ("F", "H"):
            if agent != 0 or head is None:
                raise ValueError("one focal head required only on physical slot0")
            self.base = _HiddenStudentPolicy(actors["P0"], world=world, agent=agent, sampled=False)
        elif law not in ("V", "R"):
            if head is not None:
                raise ValueError("fixed member cannot receive a trainable head")
            parent = "P0" if law == "P1" else law
            actor = actors["P1"] if law == "P1" else actors["P0"] if law in ("P0", "Bstar0", "Hdirect") else None
            self.base = Policy(parent, actor, world=world, agent=agent, sampling_root=None if law == "C" else root)

    @property
    def counters(self):
        result = dict.fromkeys(ALL_COUNTS, 0)
        if self.motion is not None:
            values = self.motion.counters
            mapping = dict(requests="decisions", misses="decisions", trajectories="trajectories",
                           model_ticks="model_ticks", candidate_links="candidate_link_evaluations",
                           setup_links="setup_link_evaluations", objective_reductions="objective_reductions",
                           tracker_ingests="ingests", adjacent_updates="adjacent_updates", pair_gates="pair_gates",
                           matched_rows="matched_rows", moving_rows="moving_rows", moving_peer_ticks="moving_peer_ticks",
                           moving_link_evaluations="moving_link_evaluations", fallback_decisions="fallback_decisions",
                           calibration_discrepancy_rows="calibration_discrepancy_rows")
            result.update({key: int(values[field]) for key, field in mapping.items()})
            result["law_evaluations"] = self.requests
        else:
            result.update(self.base.counters)
            if self.law in ("F", "H"):
                result.update(head_rows=self.requests, law_evaluations=self.requests, sampled_draws=self.requests)
            if self.tracker is not None:
                result.update({("tracker_ingests" if key == "ingests" else key): int(value)
                               for key, value in self.tracker.counters.items()})
        return result

    def ingest(self, row, tick):
        """Only H/V/R process primitive rows; no unused planner runs for H."""
        if self.tracker is not None:
            self.history = self.tracker.ingest(row, tick)
            self.tick = int(tick)
        elif self.motion is not None:
            if tick == 0:
                self.motion._nav_index = initial_nav(row)
            before = int(self.motion._nav_index)
            command, diag = self.motion.act(row.copy(), tick)
            count = int(diag["n_visible_peers"])
            history = empty_history()
            history.update(n_peers=count)
            history["matches"][:count] = diag["matches"]
            history["delta"][:count] = diag["delta"]
            history["gate_counts"][:count] = diag["gate_counts"]
            descriptor = history["descriptor"].reshape(4, 4)
            descriptor[:count, :3] = (diag["delta"] / 30.).astype(np.float32)
            descriptor[:count, 3] = (diag["matches"] >= 0).astype(np.float32)
            self.history = history
            if tick % 4 == 0:
                choice = int(diag["selected_index"])
                probabilities = np.zeros(27, dtype=np.float64)
                probabilities[choice] = 1.
                self.last = dict(features=_features(row, before, diag["fallback"]), action_index=choice,
                                 command=command.copy(), next_nav=int(self.motion._nav_index),
                                 fallback=bool(diag["fallback"]), scores=diag["scores"].copy(),
                                 served=diag["served_candidates"].copy(), c_index=choice, memo_hit=False,
                                 n_current=int(diag["n_current"]), n_peers=count,
                                 probabilities=probabilities, innovation=-1., entropy=0., nav_pre=before)
            self.tick = int(tick)
        return deepcopy(self.history)

    def query(self, row, tick, nav):
        if tick % 4:
            raise ValueError("decision calls only at four-tick boundaries")
        if self.motion is not None:
            if self.tick != tick or self.last is None or self.last["nav_pre"] != nav:
                raise ValueError("V/R requires this member's consecutive primitive ingests and private nav")
            answer = deepcopy(self.last)
        elif self.law in ("F", "H"):
            answer = self.base.query(row.copy(), tick, nav)
            answer["base_logits"] = answer["logits"].copy()
            descriptor = self.history["descriptor"] if self.law == "H" else None
            if self.law == "H" and self.tick != tick:
                raise ValueError("H requires the current consecutive tracker ingest")
            answer["context"] = pack_context(answer["features"], answer["hidden"], tick, descriptor)
            with torch.inference_mode():
                logits = self.head(torch.from_numpy(answer["context"]), torch.from_numpy(answer["base_logits"]))
            answer["logits"] = logits.cpu().numpy().copy()
            probabilities = categorical_probabilities(answer["logits"].astype(np.float64))
            uniform = indexed_uniform(self.root, self.world, tick, self.agent)
            choice = categorical_index(probabilities, uniform)
            positive = probabilities > 0
            answer.update(probabilities=probabilities, innovation=uniform, action_index=choice,
                          command=COMMANDS[choice].copy(), entropy=float(-np.sum(probabilities[positive] * np.log(probabilities[positive]))))
        else:
            answer = self.base.query(row.copy(), tick, nav)
        self.requests += 1
        return complete_answer(answer)
