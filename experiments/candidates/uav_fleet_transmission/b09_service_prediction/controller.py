"""Lawful C/H/F programs: frozen C, common tracked-now H/F and bounded R search."""
from __future__ import annotations
from copy import deepcopy
import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    observed_bs_xy, observed_station_xy, search_ring, UnobservedRegime,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions
from experiments.candidates.uav_information_value.controllers import PointSetHeuristic
from experiments.candidates.uav_information_value.b02.controller import (
    StationPriorController, station_prior_bs_xy,
)
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import (
    MemoryController, AnonymousTracker, canonical_with_provenance,
)
from experiments.candidates.uav_radio_placement.b01.placement import (
    PARAMS, _lloyd, _layout, _travel, _better, _DIRECTIONS, PlacementController,
)
from experiments.candidates.uav_joint_transition.motion import legal_start
from .contract import MODEL_SEED, SAMPLES, equal
from .model import LawfulServiceModel
from .nominal import forecast
from .trace import CANDIDATE_DTYPE, empty_candidate, digest_bytes, install_forecast

# A single-process test invocation can report actual calls, including failed attempts.
# Episode summaries use each controller's own dictionary, not this cumulative diagnostic.
TOTALS = {}


class CostDict(dict):
    def __setitem__(self, key, value):
        difference = int(value) - int(self.get(key, 0))
        if difference > 0:
            TOTALS[key] = TOTALS.get(key, 0) + difference
        super().__setitem__(key, int(value))


def bump(counts, key, value=1):
    counts[key] = counts.get(key, 0) + value


class CController(MemoryController):
    """Only count the original C's work; inherited proposal bytes are unchanged."""
    def __init__(self):
        super().__init__("C")

    def reset(self):
        super().reset()
        self._counters = CostDict(self._counters)
        self._lloyd_solves = 0

    def propose(self, *args):
        replans = self.heuristic.replans_next()
        result = super().propose(*args)
        if replans and len(self.heuristic.last_plan["users"]):
            self._lloyd_solves += 1
            TOTALS["lloyd_solves"] = TOTALS.get("lloyd_solves", 0) + 1
        return result

    @property
    def counters(self):
        return super().counters | dict(current_projections=0, future_projections=0,
                                      lloyd_solves=self._lloyd_solves)

    def audit_arrays(self):
        return {"candidate_records": np.empty(0, dtype=CANDIDATE_DTYPE)}


def best_centers(users, k, counts):
    """R's exact eight starts and Lloyd implementation, with attempt counters."""
    points = np.asarray(users, dtype=np.float64)
    starts = [points[np.linspace(0, len(points) - 1, k, dtype=int)].copy()]
    for first in np.linspace(0, len(points) - 1, 7, dtype=int):
        indices = [int(first)]
        while len(indices) < k:
            distance = np.min(np.sum((points[:, None, :] - points[indices][None, :, :]) ** 2, axis=2), axis=1)
            distance[indices] = -np.inf
            indices.append(int(np.argmax(distance)))
        starts.append(points[indices].copy())
    results = []
    for initial in starts:
        bump(counts, "lloyd_solves")
        results.append(_lloyd(points, initial))
    best = min(range(len(results)), key=lambda index: results[index][2])
    centers, population, sse, _ = results[best]
    return centers, population, dict(kmeans_selected_start=int(best), kmeans_sse=sse,
                                     kmeans_start_sse=[row[2] for row in results])


def geometric_seed(observations, modes, users, bs, previous_xy, counts):
    """R best-of-eight extended by the original local H1 sparse-ring rule."""
    h = PointSetHeuristic(PARAMS)
    h.targets_xy = previous_xy.copy()
    centers, population, info = best_centers(users, min(6, len(users)), counts)
    relays = np.asarray([bs + (index + 1) / 3.0 * (centers.mean(axis=0) - bs)
                         for index in range(2)], dtype=np.float64)
    priority = np.concatenate((relays, centers[np.argsort(-population, kind="stable")]), axis=0)
    own_xy = own_positions(observations, h.layout)[:, :2]
    movable = np.flatnonzero(~modes)
    targets = np.full((8, 2), np.nan)
    assigned = h._assign_targets(own_xy, movable, priority[:len(movable)], targets)
    leftover = np.asarray([uav for uav in movable if uav not in assigned], dtype=np.int64)
    if len(leftover):
        station = observed_station_xy(observations, h.layout)
        if station is None:
            raise UnobservedRegime("geometric spare ring requires lawful station1")
        h._assign_targets(own_xy, leftover, search_ring(station, h.params.search_radius_m, 8), targets)
    return targets, info


class ReplayBoundary(RuntimeError):
    """Stop before work absent from an incomplete recorded candidate prefix."""


class ServiceController(StationPriorController):
    """Private model is created once after reset; observations are the sole live input."""
    def __init__(self, arm):
        if arm not in ("H", "F"):
            raise ValueError("service arm must be H or F")
        super().__init__()
        self.arm = arm
        self.replay_prefix = None

    def reset(self):
        previous = getattr(self, "model", None)
        if previous is not None:
            previous.close()
        super().reset()
        self.tracker = AnonymousTracker()
        self._counts = CostDict()
        self.model = None
        self.targets_xyz = np.full((8, 3), np.nan)
        self._previous_F = np.zeros(8, dtype=bool)
        self._fallback = False
        self._last_trace = None
        self.last_decision = None
        self.candidates = []
        self.replay_prefix = None

    @property
    def counters(self):
        return dict(self._counts)

    @property
    def last_trace(self):
        return deepcopy(self._last_trace)

    @property
    def targets_xy(self):
        return self.targets_xyz[:, :2].copy()

    def audit_arrays(self):
        return {"candidate_records": np.asarray(self.candidates, dtype=CANDIDATE_DTYPE)}

    def _query(self, step, index, kind, layout, start, modes, future, bs, **meta):
        global_index = len(self.candidates)
        recorded = None
        if self.replay_prefix is not None:
            if global_index >= len(self.replay_prefix):
                raise ReplayBoundary("recorded candidate prefix exhausted")
            recorded = self.replay_prefix[global_index]
        row = empty_candidate(step, index, kind, layout, len(future[0]), **meta)
        if recorded is not None:
            for name in ("step", "index", "kind", "sweep", "member", "axis", "sign", "q", "targets"):
                equal(row[name], recorded[name], "candidate/input/" + name)
        self.candidates.append(row)  # Preserve the attempted candidate before effects.
        bump(self._counts, "candidate_forecasts")

        def tick(tick_number, digest):
            row["ticks"] = tick_number
            row["tick_digest"] = digest_bytes(digest)
            if recorded is not None and not recorded["completed"] and tick_number >= recorded["ticks"] < 30:
                raise ReplayBoundary("recorded nominal prefix exhausted")

        if recorded is not None and not recorded["completed"] and int(recorded["ticks"]) == 0:
            raise ReplayBoundary("no completed nominal tick recorded")
        prediction, tick_digest = forecast(start, layout, np.zeros(8, dtype=np.int64),
                                           modes, self.model.raw, counters=self._counts, on_tick=tick)
        install_forecast(row, prediction)
        row["tick_digest"] = digest_bytes(tick_digest)
        for sample in range(3):
            if recorded is not None and not recorded["completed"] and sample >= recorded["rf_completed"]:
                raise ReplayBoundary("recorded RF prefix exhausted")
            row["rf_started"] += 1
            result = self.model.score(prediction.xyz[sample], prediction.battery[sample], future[sample], bs)
            row["rf_completed"] += 1
            row["qos"][sample] = result["qos"]
            row["rf_digest"][sample] = digest_bytes(result["digest"])
            row["return_cost"][sample] = min(1.0, max(0.0, -float(np.min(prediction.margin[sample]))) / 0.05)
        partial = recorded is not None and not recorded["completed"]
        if partial and not np.isfinite(recorded["score"]):
            raise ReplayBoundary("recorded RF calls end before score/ranking completion")
        row["score"] = float(10.0 * np.sum(row["qos"] - 2.0 * row["return_cost"]))
        if partial and not np.isfinite(recorded["target_travel"]):
            raise ReplayBoundary("recorded scalar score ends before travel tie-break")
        row["target_travel"] = _travel(layout, start["xyz"])
        if not np.isfinite(row["score"]):
            raise FloatingPointError("non-finite candidate score")
        if partial:
            raise ReplayBoundary("recorded scalar work ends before candidate completion")
        row["completed"] = True
        if (recorded is not None and global_index == len(self.replay_prefix) - 1
                and not np.any(self.replay_prefix["selected"][self.replay_prefix["step"] == step])):
            raise ReplayBoundary("recorded prefix ends before observable search selection")
        return global_index

    def _search(self, observations, modes, users, future, bs, step):
        own = own_positions(observations, self.heuristic.layout)
        start = legal_start(observations)
        previous = self.targets_xyz.copy()
        h = PointSetHeuristic(PARAMS)
        h.targets_xy = previous[:, :2].copy()
        bump(self._counts, "lloyd_solves")
        h.plan(observations, modes, {"users_xy": users, "bs_xy": bs})
        g, geometry = geometric_seed(observations, modes, users, bs, previous[:, :2], self._counts)
        carried = np.where(np.isfinite(previous), previous, own)
        carried[self._previous_F] = own[self._previous_F]
        initial = (_layout(h.targets_xy, own, modes), _layout(g, own, modes), carried, own.copy())
        first, best = len(self.candidates), None
        for kind, raw in enumerate(initial):
            layout = raw.copy()
            layout[modes] = own[modes]
            index = self._query(step, len(self.candidates) - first, kind, layout, start, modes, future, bs)
            row = self.candidates[index]
            if best is None or _better(float(row["score"]), float(row["target_travel"]),
                                       float(self.candidates[best]["score"]), float(self.candidates[best]["target_travel"])):
                best = index
                row["accepted"] = True
        low, high = np.asarray((0.0, 0.0, 50.0)), np.asarray((8000.0, 8000.0, 200.0))
        for sweep, (horizontal, vertical) in enumerate(((500.0, 50.0), (125.0, 25.0))):
            for offset in range(8):
                member = (step // 30 + offset) % 8
                if modes[member]:
                    continue
                incumbent = self.candidates[best]["targets"].copy()
                winner = best
                for axis, sign in _DIRECTIONS:
                    target = incumbent.copy()
                    target[member, axis] += sign * (vertical if axis == 2 else horizontal)
                    target[member] = np.clip(target[member], low, high)
                    index = self._query(step, len(self.candidates) - first, 4, target, start, modes, future, bs,
                                        sweep=sweep, member=member, axis=axis, sign=sign)
                    row, leader = self.candidates[index], self.candidates[winner]
                    if _better(float(row["score"]), float(row["target_travel"]),
                               float(leader["score"]), float(leader["target_travel"])):
                        winner = index
                if winner != best:
                    best = winner
                    self.candidates[best]["accepted"] = True
        self.candidates[best]["selected"] = True
        self.targets_xyz = self.candidates[best]["targets"].copy()
        self.heuristic.targets_xy = self.targets_xyz[:, :2].copy()
        self.heuristic.last_plan = dict(h.last_plan, targets=self.heuristic.targets_xy.copy())
        self._previous_F = modes.copy()
        assert len(self.candidates) - first == 4 + 12 * int((~modes).sum())
        return first, len(self.candidates) - first, best - first, geometry

    def propose(self, observations, state, step, previous_done, modes):
        if int(step) != self.heuristic.calls:
            raise ValueError("service controller requires sequential primitive calls")
        bump(self._counts, "proposals")
        if self.model is None:
            self.model = LawfulServiceModel(self._counts, seed=MODEL_SEED)
        modes = np.asarray(modes, dtype=bool)
        if modes.shape != (8,):
            raise ValueError("F mask shape differs")
        replans = self.heuristic.replans_next()
        bump(self._counts, "canonicalizations")
        provenance = canonical_with_provenance(observations, self.heuristic.layout,
                                               self.heuristic.params.dedup_tolerance_m)
        bump(self._counts, "associations")
        tracking = self.tracker.update(provenance["canonical_xy"], step)
        self._last_trace = {"step": int(step), **provenance, **tracking,
                            "replanned": replans, "plan_supplied_xy": None}
        if not self._prior_initialized:
            self._prior_bs_xy = station_prior_bs_xy(observations, self.heuristic.layout)
            self._prior_initialized = True
        current_bs = observed_bs_xy(observations, self.heuristic.layout)
        if current_bs is not None:
            self._seen_bs_xy = current_bs.copy()
        if replans:
            bump(self._counts, "plans")
            tracks = tracking["tracks"]
            ages = int(step) - tracks["last_seen"]
            bump(self._counts, "current_projections")
            users = np.clip(tracks["last_xy"] + ages[:, None] * tracks["v"], 0.0, 8000.0)
            if self.arm == "F":
                future = []
                for tau in SAMPLES:
                    bump(self._counts, "future_projections")
                    future.append(np.clip(tracks["last_xy"] + (ages[:, None] + tau) * tracks["v"], 0.0, 8000.0))
                future = np.asarray(future)
            else:
                future = np.repeat(users[None, :, :], 3, axis=0)
            if current_bs is not None:
                bs, bs_source = current_bs, "observed-current"
            elif self._seen_bs_xy is not None:
                bs, bs_source = self._seen_bs_xy.copy(), "observed-memory"
            elif self._prior_bs_xy is not None:
                bs, bs_source = self._prior_bs_xy.copy(), "inferred"
            else:
                bs, bs_source = None, "absent"
            self._last_trace["plan_supplied_xy"] = users.copy()
            self._fallback = len(users) == 0 or bs is None
            if self._fallback:
                if len(users):
                    bump(self._counts, "lloyd_solves")
                action = self.heuristic.act(observations, modes, {"users_xy": users, "bs_xy": bs})
                self.targets_xyz = np.column_stack((self.heuristic.targets_xy, np.full(8, 100.0)))
                self._previous_F = modes.copy()
                first, count, selected, geometry = len(self.candidates), 0, -1, {}
            else:
                first, count, selected, geometry = self._search(observations, modes, users, future, bs, step)
                self.heuristic.calls += 1
                action = PlacementController._actions(self, observations)
            self.last_decision = dict(step=int(step), candidate_first=first, candidate_count=count,
                                      selected=selected, fallback=(1 if not len(users) else 2) if self._fallback else 0,
                                      future_xy=future.copy(), **geometry)
            self.diagnostics.append(dict(call=int(step), supplied_user_count=len(users),
                current_bs_present=current_bs is not None, seen_bs_so_far=self._seen_bs_xy is not None,
                memory_used=bs_source == "observed-memory", prior_used=bs_source == "inferred",
                bs_input_source=bs_source, search=bool(self.heuristic.last_plan["search"]),
                user_source="legal", bs_source="station-prior" if bs_source == "inferred" else "legal-memory"))
            if self.heuristic.last_plan["search"]:
                self.search_replan_steps.append(int(step))
        elif self._fallback:
            action = self.heuristic.act(observations, modes)
        else:
            self.heuristic.calls += 1
            action = PlacementController._actions(self, observations)
        return action

    def close(self):
        if self.model is not None:
            self.model.close()


def make_controller(arm):
    if arm == "REFERENCE":
        return StationPriorController()
    if arm == "C":
        return CController()
    return ServiceController(arm)
