"""Allocate exactly two exact continuations with the frozen B06 ordering."""
from copy import deepcopy
import time

from experiments.candidates.uav_fleet_transmission.b03.controller import continuation_rank
from experiments.candidates.uav_fleet_transmission.b03.option import (
    _plan, branch_id, enumerate_champions, physical_identity, stationary_rank,
)
from experiments.candidates.uav_fleet_transmission.b03.surrogate import (
    simulate_continuation as simulate_reference,
)
from experiments.candidates.uav_fleet_transmission.control import decode_public_state

from ..b06_continuation_amortization.controller import AmortizedProgram
from ..b06_continuation_amortization.cycle import simulate_continuation
from ..b06_continuation_amortization.learning import choose_plan


ARMS = ("R", "T_E", "K2_E", "L2_E")


class ShortlistProgram(AmortizedProgram):
    """Change only the sole t40 menu; inherit commitment and artifact delivery."""

    def __init__(self, fitted, *, reference=False):
        super().__init__("L", fitted, reference=reference)
        self.arm = "L2_E"

    def _decide(self, state, old_mask):
        wall, cpu = time.perf_counter(), time.process_time()
        positions, users = decode_public_state(state, 8)
        bc, bw = time.process_time(), time.perf_counter()
        bank = enumerate_champions(positions, users, old_mask)
        detail_timing = {
            "bank_cpu_seconds": time.process_time() - bc,
            "bank_wall_seconds": time.perf_counter() - bw,
            "feature_cpu_seconds": 0., "feature_wall_seconds": 0.,
            "inference_cpu_seconds": 0., "inference_wall_seconds": 0.,
        }
        original, champions = bank["original_R"], bank["champions"]
        # The direct L positivity decision is a diagnostic, never a menu filter.
        _, learner = choose_plan(self.artifact, bank, state, old_mask, timing=detail_timing)
        sc, sw = time.process_time(), time.perf_counter()
        if learner["zero_beta_fallback"]:
            # Exact stationary values retain K2_E ties even when subtraction and
            # /500 would collapse distinct FP64 values to the same advantage.
            ordered = sorted(range(len(champions)),
                             key=lambda i: stationary_rank(champions[i]["selected"]), reverse=True)
        else:
            def rank(i):
                c = champions[i]["selected"]
                return (learner["predicted_advantages"][i], c["predicted_total_served"],
                        -c["path"], -c["duration"], -c["member"], -c["site"])
            ordered = sorted(range(len(champions)), key=rank, reverse=True)
        shortlist = ordered[:2]
        detail_timing.update(shortlist_cpu_seconds=time.process_time() - sc,
                             shortlist_wall_seconds=time.perf_counter() - sw)
        candidates = [None, *(champions[i] for i in shortlist)]
        simulator = simulate_reference if self.reference else simulate_continuation
        branches, pending = [], []
        for candidate in candidates:
            result = simulator(self.controller, state, old_mask, candidate, horizon=500)
            record = {
                "id": branch_id(candidate), "physical_identity": physical_identity(candidate),
                "stationary_candidate": None if candidate is None else candidate["selected"],
                "summary": result["summary"],
            }
            branches.append(record)
            pending.append((record["id"], result))
        best = max(range(len(candidates)), key=lambda k: continuation_rank(
            branches[k]["summary"], candidates[k]))
        chosen = (candidates[best] if branches[best]["summary"]["total_J"]
                  > branches[0]["summary"]["total_J"] else None)
        display_plan = (deepcopy(chosen) if chosen is not None else _plan(
            None, positions, original["stay_score"], original["candidate_digest"],
            original["counts"], original["candidate_count"]))
        self.base.plan, self.base.option_old_mask = display_plan, int(old_mask)
        self.selection = {
            "arm": self.arm, "candidate_digest": original["candidate_digest"],
            "candidate_count": original["candidate_count"], "bank_counts": original["counts"],
            "champion_ids": [branch_id(p) for p in champions],
            "champion_candidates": [p["selected"] for p in champions],
            "original_R_physical_identity": physical_identity(original),
            "original_R_branch": branch_id(original), "original_R_initiated": original["initiated"],
            "selected_physical_identity": physical_identity(chosen), "selected_branch": branch_id(chosen),
            "initiated": chosen is not None, "branches": branches, "learner": learner,
            "ordered_champion_indices": ordered,
            "ordered_champion_ids": [branch_id(champions[i]) for i in ordered],
            "shortlist_indices": shortlist,
            "shortlist_ids": [branch_id(champions[i]) for i in shortlist],
        }
        self.pending = {"candidate_rows": bank["candidate_rows"], "branches": pending}
        self.selection_timing = {"cpu_seconds": time.process_time() - cpu,
                                 "wall_seconds": time.perf_counter() - wall, **detail_timing}


def make_program(arm, fitted=None, reference=False):
    """Return original baseline objects and the matching L2_E interface."""
    if arm not in ARMS:
        raise ValueError("unknown fixed B07 arm")
    if arm == "L2_E":
        return ShortlistProgram(fitted, reference=reference)
    return AmortizedProgram(arm, fitted, reference=reference)
