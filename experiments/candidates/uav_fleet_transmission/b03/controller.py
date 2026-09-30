"""T: select among complete C continuations of the fixed R shortlist."""
from copy import deepcopy
import hashlib

import numpy as np

from ..control import decode_public_state
from ..b02.controller import Program
from .option import branch_id, enumerate_champions, physical_identity
from .surrogate import simulate_continuation


def continuation_rank(summary, plan):
    if plan is None:
        return (summary["total_J"], summary["total_served"], 0., 0, 0, 0)
    return (summary["total_J"], summary["total_served"], -plan["selected"]["path"],
            -plan["duration"], -plan["member"], -plan["site"])


def modeled_execution_identity(arrays):
    digest = hashlib.sha256()
    for key, dtype in (("positions", "<f8"), ("actions", "<f4"), ("masks", "<i8")):
        value = np.asarray(arrays[key], dtype=dtype)
        digest.update(np.asarray(value.shape, dtype="<i8").tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


class ContinuationProgram:
    """Only the public report, entering mask and private command history enter.

    Sinks own serialization; their return values cannot affect the decision.
    No environment, world identity or future native data enters this object.
    """
    def __init__(self, horizon=500, branch_sink=None, candidate_sink=None):
        if horizon != 500:
            raise ValueError("T is fixed at H500")
        self.base = Program("C", horizon)
        self.horizon = horizon
        self.branch_sink, self.candidate_sink = branch_sink, candidate_sink
        self.continuation = None

    @property
    def plan(self):
        return self.base.plan

    @property
    def controller(self):
        return self.base.controller

    def select(self, t, state, old_mask):
        shortlist = None
        if t == 40:
            if self.continuation is not None or self.controller.next_t != 40:
                raise ValueError("T selection repeated or reached with wrong clock")
            positions, users = decode_public_state(state, 8)
            shortlist = enumerate_champions(positions, users, old_mask)
            if self.candidate_sink is not None:
                self.candidate_sink(shortlist["candidate_rows"])
            plans = [None, *shortlist["champions"]]
            branches = []
            for plan in plans:
                result = simulate_continuation(self.controller, state, old_mask, plan, self.horizon)
                identifier = branch_id(plan)
                branches.append({"id": identifier, "physical_identity": physical_identity(plan),
                    "modeled_execution_identity": modeled_execution_identity(result["arrays"]),
                    "plan": deepcopy(plan), "summary": result["summary"]})
                if self.branch_sink is not None:
                    self.branch_sink(identifier, result)
            best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
            # Full-score ties always decline, regardless of a service tie-break.
            if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
                best = 0
            selected = deepcopy(plans[best])
            if selected is None:
                selected = deepcopy(shortlist["original_R"])
                selected.update(initiated=False, member=None, site=None, offsets=None, commands=[],
                    duration=0, arrival_t=None, predicted_destination=positions.tolist(), predicted_mask=None,
                    predicted_total_J=selected["stay_total_J"], predicted_total_served=selected["stay_total_served"])
            self.base.plan, self.base.option_old_mask = selected, int(old_mask)
            original_id = branch_id(shortlist["original_R"])
            if original_id not in {b["id"] for b in branches}:
                raise ValueError("original R complete program missing from retained branches")
            original = next(b for b in branches if b["id"] == original_id)
            if branches[best]["summary"]["total_J"] < original["summary"]["total_J"]:
                raise ValueError("selected model value below represented original R")
            global_physical = shortlist["original_R"]["selected"]
            self.continuation = {"original_R": shortlist["original_R"], "branches": branches,
                "selected_branch": branches[best]["id"], "original_R_branch": original_id,
                "best_stationary_physical_branch": None if global_physical is None else
                    f"m{global_physical['member']}_s{global_physical['site']}",
                "selected_physical_identity": branches[best]["physical_identity"],
                "original_R_physical_identity": physical_identity(shortlist["original_R"]),
                "strict_model_improvement_over_stay": best != 0,
                "model_J_gain_over_R": branches[best]["summary"]["total_J"] - original["summary"]["total_J"]}
        command, new_mask, decision = self.base.select(t, state, old_mask)
        if shortlist is not None:
            decision["option"] = deepcopy(self.base.plan)
            decision["continuation"] = self.continuation
        return command, new_mask, decision
