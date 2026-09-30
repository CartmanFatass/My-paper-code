"""One lawful t40 choice, followed by the unchanged native commitment/C program."""
from copy import deepcopy
import time

import numpy as np

from experiments.candidates.uav_fleet_transmission.b02.controller import Program
from experiments.candidates.uav_fleet_transmission.b03.controller import continuation_rank
from experiments.candidates.uav_fleet_transmission.b03.option import (
    _plan, branch_id, enumerate_champions, physical_identity, stationary_rank,
)
from experiments.candidates.uav_fleet_transmission.b03.surrogate import (
    simulate_continuation as simulate_reference,
)
from experiments.candidates.uav_fleet_transmission.control import decode_public_state

from .learning import choose_plan

ARMS = ("R", "T_E", "K2_E", "L")


class AmortizedProgram:
    def __init__(self, arm, artifact=None, *, reference=False):
        if arm not in ARMS or (arm == "L") != (artifact is not None):
            raise ValueError("fixed B06 arm/artifact contract differs")
        self.arm, self.artifact, self.reference = arm, artifact, reference
        self.base = Program("C", horizon=500)
        self.selection = None
        self.selection_timing = None
        self.pending = None

    @property
    def controller(self):
        return self.base.controller

    @property
    def plan(self):
        return self.base.plan

    def _decide(self, state, old_mask):
        wall, cpu = time.perf_counter(), time.process_time()
        positions, users = decode_public_state(state, 8)
        bc, bw = time.process_time(), time.perf_counter()
        bank = enumerate_champions(positions, users, old_mask)
        detail_timing = {"bank_cpu_seconds": time.process_time()-bc, "bank_wall_seconds": time.perf_counter()-bw,
                         "feature_cpu_seconds": 0., "feature_wall_seconds": 0.,
                         "inference_cpu_seconds": 0., "inference_wall_seconds": 0.}
        original = bank["original_R"]
        chosen, learner, branches, pending = None, None, [], []
        if self.arm == "R":
            chosen = original if original["initiated"] else None
        elif self.arm == "L":
            chosen, learner = choose_plan(self.artifact, bank, state, old_mask, timing=detail_timing)
        else:
            if self.reference:
                simulator = simulate_reference
            else:
                from .cycle import simulate_continuation
                simulator = simulate_continuation
            champions = bank["champions"]
            if self.arm == "K2_E":
                champions = sorted(champions, key=lambda p: stationary_rank(p["selected"]), reverse=True)[:2]
            candidates = [None, *champions]
            for candidate in candidates:
                result = simulator(self.controller, state, old_mask, candidate, horizon=500)
                record = {"id": branch_id(candidate), "physical_identity": physical_identity(candidate),
                          "stationary_candidate": None if candidate is None else candidate["selected"],
                          "summary": result["summary"]}
                branches.append(record)
                pending.append((record["id"], result))
            best = max(range(len(candidates)), key=lambda k: continuation_rank(
                branches[k]["summary"], candidates[k]))
            if branches[best]["summary"]["total_J"] > branches[0]["summary"]["total_J"]:
                chosen = candidates[best]
        if self.arm == "R":
            display_plan = deepcopy(original)
        elif chosen is None:
            display_plan = _plan(None, positions, original["stay_score"], original["candidate_digest"],
                                 original["counts"], original["candidate_count"])
        else:
            display_plan = deepcopy(chosen)
        self.base.plan, self.base.option_old_mask = display_plan, int(old_mask)
        self.selection = {
            "arm": self.arm, "candidate_digest": original["candidate_digest"],
            "candidate_count": original["candidate_count"], "bank_counts": original["counts"],
            "champion_ids": [branch_id(p) for p in bank["champions"]],
            "champion_candidates": [p["selected"] for p in bank["champions"]],
            "original_R_physical_identity": physical_identity(original),
            "original_R_branch": branch_id(original), "original_R_initiated": original["initiated"],
            "selected_physical_identity": physical_identity(chosen), "selected_branch": branch_id(chosen),
            "initiated": chosen is not None, "branches": branches, "learner": learner,
        }
        self.pending = {"candidate_rows": bank["candidate_rows"], "branches": pending}
        self.selection_timing = {"cpu_seconds": time.process_time() - cpu,
                                 "wall_seconds": time.perf_counter() - wall, **detail_timing}

    def select(self, t, state, old_mask):
        if t == 40:
            if self.selection is not None or self.controller.next_t != 40:
                raise ValueError("the sole B06 choice was repeated or reached out of order")
            self._decide(state, old_mask)
        command, mask, decision = self.base.select(t, state, old_mask)
        if t == 40:
            decision["option"] = deepcopy(self.plan)
            decision["selection"] = deepcopy(self.selection)
        return command, mask, decision

    def take_artifacts(self):
        pending, self.pending = self.pending, None
        return pending
