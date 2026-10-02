"""H_T: frozen H_A scores, with literal shortest-travel choice above base.

The plan-boundary callback adapts selection; a narrow completed-prefix wrapper
defers the frozen query boundary until provisional flags are reconstructed.
Candidate physics, solver provenance and the inherited single act remain B10.
The retained arm is H_A so tracker/reset/map semantics stay frozen; policy_arm
identifies the B11 selection rule to external capture/runner code.
"""
from __future__ import annotations
from itertools import combinations
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as b10
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.controller import (
    ROLE_SERVICE, current_velocities, bump, LawfulServiceModel, legal_start,
    MODEL_SEED, SAMPLES, equal,
)

TOTALS = b10.TOTALS
CANDIDATE_DTYPE = b10.CANDIDATE_DTYPE
ReplayBoundary = b10.ReplayBoundary


def select_travel_tie(records):
    """Return old H/final local indices and exact top/minimum-travel masks.

    Base wins if it has the literal maximum score, regardless of travel. Above
    base, only exact maxima enter the literal float64 travel/index comparison.
    No candidate is rescored and provisional accepted flags are untouched.
    """
    scores = np.asarray(records["score"], dtype=np.float64)
    travel = np.asarray(records["forecast_travel"], dtype=np.float64)
    if scores.ndim != 1 or len(scores) == 0 or travel.shape != scores.shape:
        raise ValueError("tie selection requires a nonempty candidate vector")
    if not np.isfinite(scores).all() or not np.isfinite(travel).all():
        raise FloatingPointError("non-finite score or forecast travel")
    top = scores == float(np.max(scores))
    h_selected = int(np.flatnonzero(top)[0])
    minimum = top & (travel == float(np.min(travel[top])))
    selected = 0 if top[0] else int(np.flatnonzero(minimum)[0])
    return h_selected, selected, top, minimum


class TravelTieController(b10.ServiceController):
    policy_arm = "H_T"

    def __init__(self):
        super().__init__("H_A")

    def _query(self, *args, **kwargs):
        """Reuse one frozen query; defer only its completed-table boundary.

        B10 stops inside its last completed query if no final selected record
        exists. The caller has not yet reconstructed that row's provisional
        accepted flag. Let the loop do that bookkeeping, then stop before any
        final selection; incomplete nominal/RF/scalar boundaries still propagate.
        """
        before = len(self.candidates)
        try:
            return super()._query(*args, **kwargs)
        except ReplayBoundary as error:
            if (str(error) != "recorded prefix ends before search selection" or
                    self.replay_prefix is None or len(self.candidates) != before + 1 or
                    not self.candidates[-1]["completed"]):
                raise
            return before

    def _on_plan(self, observations, modes, plan):
        step = self.heuristic.calls
        ordinary = self.heuristic.targets_xy.copy()
        roles = self.heuristic.assignment_role.copy()
        eligible = (~modes & (roles == ROLE_SERVICE) & np.isfinite(ordinary).all(axis=1))
        if eligible.sum() > 6:
            raise ValueError("ordinary C assigned more than six service members")
        users = plan["users"]
        self._last_trace["plan_supplied_xy"] = users.copy()
        fallback = 2 if plan["bs_xy"] is None else 1 if eligible.sum() < 2 else 0
        future = np.empty((3, 0, 2), dtype=np.float64)
        velocities = np.empty((0, 2), dtype=np.float64)
        if self.tracker is not None:
            equal(users, self._last_trace["canonical_xy"], "C/current-map")
            velocities = current_velocities(users, self._last_trace)
            if fallback == 0 and self.arm == "F_A":
                future = np.asarray([np.clip(users + tau * velocities, 0.0, 8000.0) for tau in SAMPLES])
                bump(self._counts, "future_projections", len(SAMPLES))
            elif fallback == 0:
                future = np.repeat(users[None, :, :], len(SAMPLES), axis=0)
        first, selected, pair = len(self.candidates), -1, (-1, -1)
        self.last_decision = dict(step=int(step), candidate_first=first,
            candidate_count=0, selected=selected, fallback=fallback,
            future_xy=future.copy(), ordinary_targets=ordinary,
            assignment_role=roles, assignment_column=self.heuristic.assignment_column.copy(),
            assignment_call=self.heuristic.assignment_call.copy(), eligible=eligible,
            selected_pair=np.asarray(pair, dtype=np.int8), current_velocities=velocities, h_selected=-1, tie_changed=False,
            top_score_mask=np.empty(0, dtype=bool), min_travel_mask=np.empty(0, dtype=bool))

        if self.tracker is not None and fallback == 0:
            start = legal_start(observations)
            if self.model is None:
                self.model = LawfulServiceModel(self._counts, seed=MODEL_SEED)
            pairs = [(-1, -1)] + list(combinations(np.flatnonzero(eligible).tolist(), 2))
            best = None
            for index, candidate_pair in enumerate(pairs):
                targets = ordinary.copy()
                left, right = candidate_pair
                if left >= 0:
                    targets[[left, right]] = targets[[right, left]]
                layout = np.column_stack((targets, np.full(8, 100.0)))
                alias = bool(left >= 0 and np.array_equal(targets, ordinary, equal_nan=True))
                global_index = self._query(step, index, candidate_pair, layout, start,
                    modes, future, plan["bs_xy"], alias_base=alias)
                row = self.candidates[global_index]
                if best is None or float(row["score"]) > float(self.candidates[best]["score"]):
                    best = global_index
                    row["accepted"] = True
                self.last_decision["h_selected"] = best - first
            records = self.audit_arrays()["candidate_records"][first:]
            h_selected, selected, top, min_travel = select_travel_tie(records)
            if h_selected != best - first:
                raise AssertionError("literal H incumbent differs from exact maximum")
            if self.replay_prefix is not None:
                saved_step = self.replay_prefix[self.replay_prefix["step"] == step]
                if not np.any(saved_step["selected"]):
                    raise ReplayBoundary("recorded prefix ends before search selection")
            self.last_decision.update(h_selected=h_selected, tie_changed=selected != h_selected,
                top_score_mask=top, min_travel_mask=min_travel)
            best = first + selected
            self.candidates[best]["selected"] = True
            selected = best - first
            pair = pairs[selected]
            if self.replay_prefix is not None:
                saved = self.replay_prefix[first:len(self.candidates)]
                actual = self.audit_arrays()["candidate_records"][first:]
                for name in ("accepted", "selected"):
                    equal(actual[name], saved[name], "candidate/ranking/" + name)
            # Commit to the actual original C state before its one action.
            self.heuristic.targets_xy = self.candidates[best]["targets"][:, :2].copy()
            plan["targets"] = self.heuristic.targets_xy.copy()
        self.last_decision.update(candidate_count=len(self.candidates)-first,
            selected=selected, selected_pair=np.asarray(pair, dtype=np.int8))


def make_controller(arm):
    if arm == "H_T":
        return TravelTieController()
    if arm == "H_A":
        return b10.make_controller(arm)
    raise ValueError("B11 factory supports H_T and frozen H_A only")
