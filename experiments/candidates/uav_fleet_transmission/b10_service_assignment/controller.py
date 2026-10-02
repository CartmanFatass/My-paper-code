"""Ordinary C destinations, with current-only H_A/F_A service assignment scores.

The inherited StationPriorController observes BS and invokes one original act.
The local planner records its one actual solver result, then a boundary hook
commits selected targets before that act emits an action. No native input enters.
"""
from __future__ import annotations
from copy import deepcopy
from itertools import combinations
import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import _assign, observed_station_xy
from experiments.candidates.uav_information_value.controllers import PointSetHeuristic
from experiments.candidates.uav_information_value.b02.controller import StationPriorController
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import (
    AnonymousTracker, canonical_with_provenance,
)
from experiments.candidates.uav_fleet_transmission.b09_service_prediction.model import LawfulServiceModel
from experiments.candidates.uav_joint_transition.motion import legal_start
from .contract import MODEL_SEED, SAMPLES, equal
from .nominal import forecast
from .trace import CANDIDATE_DTYPE, empty_candidate, digest_bytes, install_forecast

ROLE_MISSING, ROLE_RELAY, ROLE_SERVICE, ROLE_RING = 0, 1, 2, 3
CALL_MISSING, CALL_PRIMARY, CALL_RING = 0, 1, 2
TOTALS = {}


class CostDict(dict):
    def __setitem__(self, key, value):
        difference = int(value) - int(self.get(key, 0))
        if difference > 0:
            TOTALS[key] = TOTALS.get(key, 0) + difference
        super().__setitem__(key, int(value))


def bump(counts, key, value=1):
    counts[key] = counts.get(key, 0) + value


class ReplayBoundary(RuntimeError):
    """No completed query beyond the saved prefix may be reconstructed."""


def validate_candidate_record(recorded):
    ticks, started = int(recorded["ticks"]), int(recorded["ticks_started"])
    rf, rf_started = int(recorded["rf_completed"]), int(recorded["rf_started"])
    if not (0 <= ticks <= started <= min(30, ticks+1) and
            0 <= rf <= rf_started <= min(3, rf+1)):
        raise ValueError("corrupt candidate work prefix")
    if (rf_started and ticks != 30) or (recorded["completed"] and
            (ticks != 30 or rf != 3 or not np.isfinite(recorded["score"]))):
        raise ValueError("corrupt candidate completion")
    if (recorded["selected"] or recorded["accepted"]) and not recorded["completed"]:
        raise ValueError("ranked incomplete candidate")
    if np.isfinite(recorded["score"]) and (ticks != 30 or rf != 3):
        raise ValueError("corrupt scalar completion")


class ProvenanceHeuristic(PointSetHeuristic):
    """Original assignment arithmetic, recording actual solver columns in-place."""
    def __init__(self, params, on_plan, counts):
        self.on_plan, self.counts = on_plan, counts
        super().__init__(params)

    def plan(self, observations, modes, plan_inputs=None):
        self.assignment_role = np.zeros(8, dtype=np.int8)
        self.assignment_column = np.full(8, -1, dtype=np.int16)
        self.assignment_call = np.zeros(8, dtype=np.int8)
        self._assignment_call = 0
        self._n_relay = (self.params.n_relay if
            len(plan_inputs["users_xy"]) and plan_inputs["bs_xy"] is not None else 0)
        bump(self.counts, "plans")
        # The original planner rejects an absent BS/station before any Lloyd
        # call. Count a solve attempt only when it reaches that computation.
        if len(plan_inputs["users_xy"]) and (plan_inputs["bs_xy"] is not None or
                observed_station_xy(observations, self.layout) is not None):
            bump(self.counts, "lloyd_solves")
        plan = super().plan(observations, modes, plan_inputs)
        self.on_plan(observations, np.asarray(modes, dtype=bool), plan)
        return plan

    def _assign_targets(self, own_xy, uavs, points, targets):
        self._assignment_call += 1
        call = CALL_PRIMARY if self._assignment_call == 1 else CALL_RING
        bump(self.counts, "assignment_calls")
        params = self.params
        if len(uavs) == 0 or len(points) == 0:
            return set()
        cost = np.linalg.norm(own_xy[uavs][:, None, :] - points[None, :, :], axis=2)
        for row, uav in enumerate(uavs):
            previous = self.targets_xy[uav]
            if np.all(np.isfinite(previous)):
                continuing = int(np.argmin(np.linalg.norm(points - previous, axis=1)))
                cost[row, continuing] -= params.switch_margin_m
        bump(self.counts, "assignment_solves")
        assigned = set()
        for row, col in _assign(cost):
            targets[uavs[row]] = points[col]
            assigned.add(int(uavs[row]))
            self.assignment_column[uavs[row]] = col
            self.assignment_call[uavs[row]] = call
            self.assignment_role[uavs[row]] = (ROLE_RING if call == CALL_RING else
                ROLE_RELAY if col < self._n_relay else ROLE_SERVICE)
        return assigned


def current_velocities(points, tracking):
    """Tracker current rows are emitted first, in canonical input order."""
    rows = tracking["tracks"][tracking["tracks"]["current"]]
    if len(rows) != len(points) or not np.array_equal(rows["last_xy"], points):
        raise ValueError("tracker current rows differ from the current canonical map")
    return rows["v"].copy()


class AssignmentController(StationPriorController):
    def __init__(self, arm):
        if arm not in ("C", "H_A", "F_A"):
            raise ValueError("B10 arm must be C, H_A or F_A")
        super().__init__()
        self.arm = arm
        self.heuristic = ProvenanceHeuristic(self.heuristic.params, self._on_plan, self._counts)
        self.reset()

    def reset(self):
        previous = getattr(self, "model", None)
        if previous is not None:
            previous.close()
        super().reset()
        self._counts = CostDict(proposals=0, plans=0, canonicalizations=0, associations=0,
                                current_projections=0, future_projections=0)
        if isinstance(self.heuristic, ProvenanceHeuristic):
            self.heuristic.counts = self._counts
        self.tracker = AnonymousTracker() if self.arm in ("H_A", "F_A") else None
        self.model = None
        self.candidates = []
        self.replay_prefix = None
        self._last_trace = None
        self.last_decision = None

    @property
    def counters(self):
        return dict(self._counts)

    @property
    def last_trace(self):
        return deepcopy(self._last_trace)

    def audit_arrays(self):
        return {"candidate_records": np.asarray(self.candidates, dtype=CANDIDATE_DTYPE)}

    def propose(self, observations, state, step, previous_done, modes):
        if int(step) != self.heuristic.calls:
            raise ValueError("B10 requires sequential primitive calls")
        modes = np.asarray(modes, dtype=bool)
        if modes.shape != (8,):
            raise ValueError("F mask shape differs")
        bump(self._counts, "proposals")
        replans = self.heuristic.replans_next()
        self._last_trace = dict(step=int(step), replanned=replans, plan_supplied_xy=None)
        if self.tracker is not None:
            bump(self._counts, "canonicalizations")
            provenance = canonical_with_provenance(observations, self.heuristic.layout,
                self.heuristic.params.dedup_tolerance_m)
            bump(self._counts, "associations")
            tracking = self.tracker.update(provenance["canonical_xy"], step)
            self._last_trace.update(provenance | tracking)
        if replans:
            # The inherited StationPriorController also canonicalizes for C.
            bump(self._counts, "canonicalizations")
        return super().propose(observations, state, step, previous_done, modes)

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
            selected_pair=np.asarray(pair, dtype=np.int8), current_velocities=velocities)

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

    def _query(self, step, index, pair, layout, start, modes, future, bs, *, alias_base=False):
        global_index = len(self.candidates)
        recorded = None
        if self.replay_prefix is not None:
            if self.replay_prefix.dtype != CANDIDATE_DTYPE or self.replay_prefix.ndim != 1:
                raise ValueError("invalid candidate prefix schema")
            if global_index >= len(self.replay_prefix):
                raise ReplayBoundary("recorded candidate prefix exhausted")
            recorded = self.replay_prefix[global_index]
            validate_candidate_record(recorded)
        row = empty_candidate(step, index, pair, layout, len(future[0]), alias_base=alias_base)
        if recorded is not None:
            for name in ("step", "index", "pair_left", "pair_right", "alias_base", "q", "targets", "hold_xy"):
                equal(row[name], recorded[name], "candidate/input/" + name)
        self.candidates.append(row)
        if self.last_decision is not None and self.last_decision["step"] == step:
            self.last_decision["candidate_count"] = len(self.candidates) - self.last_decision["candidate_first"]
        bump(self._counts, "candidate_forecasts")

        def tick_started(number):
            row["ticks_started"] = number

        def tick(number, digest):
            row["ticks"] = number
            row["tick_digest"] = digest_bytes(digest)
            if recorded is not None and number == int(recorded["ticks"]):
                equal(row["tick_digest"], recorded["tick_digest"], "candidate/tick-digest")
                if number < 30:
                    raise ReplayBoundary("recorded nominal prefix exhausted")

        if recorded is not None and int(recorded["ticks"]) == 0:
            raise ReplayBoundary("no completed nominal tick recorded")
        prediction, tick_digest = forecast(start, layout, np.zeros(8, dtype=np.int64),
            modes, self.model.raw, counters=self._counts, on_tick=tick,
            on_tick_started=tick_started, hold_xy=row["hold_xy"])
        install_forecast(row, prediction)
        row["tick_digest"] = digest_bytes(tick_digest)
        if recorded is not None:
            for name in ("xyz", "battery", "margin", "F", "waits", "cancelled", "crossed_F",
                         "crossed_reserve", "crossed_cutoff", "forecast_travel", "tick_digest"):
                equal(row[name], recorded[name], "candidate/forecast/" + name)
        for sample in range(len(SAMPLES)):
            if recorded is not None and sample >= int(recorded["rf_completed"]):
                raise ReplayBoundary("recorded RF prefix exhausted")
            row["rf_started"] += 1
            rf_before = self._counts.get("model_rf_calls", 0)
            result = self.model.score(prediction.xyz[sample], prediction.battery[sample], future[sample], bs)
            row["rf_completed"] += 1
            bump(self._counts, "model_score_calls_completed")
            if self._counts.get("model_rf_calls", 0) > rf_before:
                bump(self._counts, "model_rf_calls_completed")
            row["qos"][sample] = result["qos"]
            row["rf_digest"][sample] = digest_bytes(result["digest"])
            row["return_cost"][sample] = min(1.0, max(0.0, -float(np.min(prediction.margin[sample]))) / 0.05)
            if recorded is not None:
                for name in ("qos", "rf_digest", "return_cost"):
                    equal(row[name][sample], recorded[name][sample], "candidate/rf/" + name)
        if recorded is not None and not recorded["completed"] and not np.isfinite(recorded["score"]):
            raise ReplayBoundary("recorded RF prefix ends before scalar completion")
        row["score"] = float(10.0 * np.sum(row["qos"] - 2.0 * row["return_cost"]))
        if not np.isfinite(row["score"]):
            raise FloatingPointError("non-finite candidate score")
        if recorded is not None:
            equal(row["score"], recorded["score"], "candidate/score")
            if not recorded["completed"]:
                raise ReplayBoundary("recorded scalar ends before candidate completion")
        row["completed"] = True
        bump(self._counts, "candidate_forecasts_completed")
        if (recorded is not None and global_index == len(self.replay_prefix)-1 and
                not np.any(self.replay_prefix["selected"][self.replay_prefix["step"] == step])):
            raise ReplayBoundary("recorded prefix ends before search selection")
        return global_index

    def close(self):
        if self.model is not None:
            self.model.close()
            self.model = None


class CController(AssignmentController):
    def __init__(self):
        super().__init__("C")


class ServiceController(AssignmentController):
    def __init__(self, arm):
        if arm not in ("H_A", "F_A"):
            raise ValueError("service arm must be H_A or F_A")
        super().__init__(arm)


def make_controller(arm):
    if arm == "REFERENCE":
        return StationPriorController()
    if arm == "C":
        return CController()
    return ServiceController(arm)
