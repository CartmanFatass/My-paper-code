"""B08 lawful anonymous memory; the C arm executes frozen P_BS directly.

Track births are private episode-local counters, never native user identities. All
trace/state accessors return copies. No environment, central state or RNG is used.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TypedDict

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT,
    user_records,
)
from experiments.candidates.uav_information_value.b02.controller import (
    StationPriorController,
    station_prior_bs_xy,
)


TRACK_DTYPE = np.dtype([
    ("birth", np.int64), ("last_seen", np.int64),
    ("last_xy", np.float64, (2,)), ("v", np.float64, (2,)),
    ("current", np.bool_), ("unambiguous", np.bool_),
])
EVENT_NAMES = ("continued", "new", "ambiguous", "expired", "discarded", "cap_drop")


class CanonicalTrace(TypedDict):
    canonical_xy: np.ndarray
    kept_flat_indices: np.ndarray
    raw_to_canonical: np.ndarray


class MemoryTrace(CanonicalTrace):
    step: int
    tracks: np.ndarray
    events: dict[str, np.ndarray]
    event_counts: dict[str, int]
    replanned: bool
    plan_supplied_xy: np.ndarray | None


def canonical_with_provenance(
    observations, layout=S7S2_LAYOUT, tolerance_m=0.5,
) -> CanonicalTrace:
    """The frozen lexicographic greedy merge, recording its first rejecting kept point.

    Flat indices are observer-major raw user slots. Absent slots map to -1;
    merged slots map to the canonical index that rejected them. Decoding, sort,
    norm comparisons, short circuit and kept coordinate bytes match the original.
    """
    records = user_records(observations, layout)
    if records["present"].shape != (8, 30):
        raise ValueError("B08 requires the frozen eight-observer/thirty-slot layout")
    raw_indices = np.flatnonzero(records["present"].reshape(-1))
    points = records["xy_m"][records["present"]]
    order = np.lexsort((points[:, 1], points[:, 0]))
    kept, kept_indices = [], []
    mapping = np.full(240, -1, dtype=np.int64)
    for index in order:
        point = points[index]
        for canonical_index, other in enumerate(kept):
            if not np.linalg.norm(point - other) > tolerance_m:
                break
        else:
            canonical_index = len(kept)
            kept.append(point)
            kept_indices.append(raw_indices[index])
        mapping[raw_indices[index]] = canonical_index
    canonical = np.asarray(kept, dtype=np.float64).reshape(-1, 2)
    assert len(canonical) <= 30, "canonical current points exceed the public user cap"
    return {"canonical_xy": canonical,
            "kept_flat_indices": np.asarray(kept_indices, dtype=np.int64),
            "raw_to_canonical": mapping.reshape(8, 30)}


class AnonymousTracker:
    """Bounded mutually-unique association with expiration before matching."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._tracks = np.empty(0, dtype=TRACK_DTYPE)
        self._next_birth = 0
        self._step = -1
        self._events = {name: np.empty(0, dtype=np.int64) for name in EVENT_NAMES}
        self._counters = {"associations": 0, "projections": 0}

    @property
    def counters(self):
        return self._counters.copy()

    def snapshot(self):
        return {"tracks": self._tracks.copy(),
                "events": {name: births.copy() for name, births in self._events.items()},
                "event_counts": {name: len(births) for name, births in self._events.items()}}

    def update(self, current_xy, step):
        points = np.asarray(current_xy, dtype=np.float64).reshape(-1, 2)
        assert len(points) <= 30, "canonical current points exceed the public user cap"
        if int(step) != step or step <= self._step:
            raise ValueError("tracker steps must be increasing integer primitive times")
        step = int(step)
        self._counters["associations"] += 1
        events = {name: [] for name in EVENT_NAMES}
        expired = step - self._tracks["last_seen"] > 30
        events["expired"] = self._tracks["birth"][expired].tolist()
        old = self._tracks[~expired].copy()
        ages = step - old["last_seen"]
        distances = np.linalg.norm(old["last_xy"][:, None, :] - points[None, :, :], axis=2)
        feasible = distances <= 3.0 * ages[:, None] + 0.5
        old_degree, current_degree = feasible.sum(axis=1), feasible.sum(axis=0)
        unique = feasible & (old_degree[:, None] == 1) & (current_degree[None, :] == 1)
        old_continued = unique.any(axis=1)
        events["discarded"] = old["birth"][(old_degree > 0) & ~old_continued].tolist()
        current = np.zeros(len(points), dtype=TRACK_DTYPE)
        current["last_xy"] = points
        current["last_seen"] = step
        current["current"] = True
        for index, point in enumerate(points):
            matches = np.flatnonzero(unique[:, index])
            if len(matches):
                previous = old[matches[0]]
                birth = int(previous["birth"])
                events["continued"].append(birth)
                current["unambiguous"][index] = True
                if previous["unambiguous"] and previous["last_seen"] == step - 1:
                    velocity = point - previous["last_xy"]  # dt is exactly one second.
                    speed = np.linalg.norm(velocity)
                    if speed > 3.0:
                        velocity = velocity * (3.0 / speed)
                    current["v"][index] = velocity
            else:
                birth = self._next_birth
                self._next_birth += 1
                events["new"].append(birth)
                ambiguous = current_degree[index] > 0
                current["unambiguous"][index] = not ambiguous
                if ambiguous:
                    events["ambiguous"].append(birth)
            current["birth"][index] = birth
        remembered = old[old_degree == 0].copy()
        remembered["current"] = False
        order = np.lexsort((remembered["birth"], step - remembered["last_seen"]))
        remembered = remembered[order]
        room = 30 - len(current)
        events["cap_drop"] = remembered["birth"][room:].tolist()
        self._tracks = np.concatenate((current, remembered[:room]))
        self._events = {name: np.asarray(births, dtype=np.int64)
                        for name, births in events.items()}
        self._step = step
        return self.snapshot()

    def supplied_points(self, arm, step):
        if step != self._step:
            raise ValueError("supplied points require the latest ingested primitive time")
        if arm == "M":
            return self._tracks["last_xy"].copy()
        if arm != "V":
            raise ValueError("tracker supplies only M or V")
        self._counters["projections"] += 1
        ages = step - self._tracks["last_seen"]
        return np.clip(self._tracks["last_xy"] + (ages[:, None] + 15.0) * self._tracks["v"],
                       0.0, 8000.0)


class MemoryController(StationPriorController):
    """C/M/V adapter retaining the frozen P_BS planner, clock and BS precedence."""

    def __init__(self, arm):
        if arm not in ("C", "M", "V"):
            raise ValueError("B08 arm must be C, M or V")
        super().__init__()
        self.arm = arm

    def reset(self):
        super().reset()
        self.tracker = AnonymousTracker()
        self._last_trace: MemoryTrace | dict | None = None
        self._counters = {"proposals": 0, "plans": 0, "canonicalizations": 0}

    @property
    def counters(self):
        return self._counters | self.tracker.counters

    @property
    def last_trace(self):
        return deepcopy(self._last_trace)

    def propose(self, observations, state, step, previous_done, modes):
        self._counters["proposals"] += 1
        replans = self.heuristic.replans_next()
        if self.arm == "C":
            actions = super().propose(observations, state, step, previous_done, modes)
            if replans:
                self._counters["canonicalizations"] += 1
                self._counters["plans"] += 1
            self._last_trace = {"step": int(step), "replanned": replans,
                                "plan_supplied_xy": self.heuristic.last_plan["users"].copy()
                                if replans else None}
            return actions

        self._counters["canonicalizations"] += 1
        provenance = canonical_with_provenance(
            observations, self.heuristic.layout, self.heuristic.params.dedup_tolerance_m)
        tracking = self.tracker.update(provenance["canonical_xy"], step)
        self._last_trace = {"step": int(step), **provenance, **tracking,
                            "replanned": replans, "plan_supplied_xy": None}
        if not self._prior_initialized:
            self._prior_bs_xy = station_prior_bs_xy(observations, self.heuristic.layout)
            self._prior_initialized = True
        current_bs = observed_bs_xy(observations, self.heuristic.layout)
        if current_bs is not None:
            self._seen_bs_xy = current_bs.copy()
        inputs = None
        if replans:
            users = self.tracker.supplied_points(self.arm, step)
            if current_bs is not None:
                bs_xy, bs_input_source = current_bs, "observed-current"
            elif self._seen_bs_xy is not None:
                bs_xy, bs_input_source = self._seen_bs_xy.copy(), "observed-memory"
            elif self._prior_bs_xy is not None:
                bs_xy, bs_input_source = self._prior_bs_xy.copy(), "inferred"
            else:
                bs_xy, bs_input_source = None, "absent"
            inputs = {"users_xy": users, "bs_xy": bs_xy}
            self._last_trace["plan_supplied_xy"] = users.copy()
            self._counters["plans"] += 1
        actions = self.heuristic.act(observations, modes, inputs)
        if replans:
            plan = self.heuristic.last_plan
            self.diagnostics.append({
                "call": plan["call"], "supplied_user_count": len(inputs["users_xy"]),
                "current_bs_present": current_bs is not None,
                "seen_bs_so_far": self._seen_bs_xy is not None,
                "memory_used": bs_input_source == "observed-memory",
                "prior_used": bs_input_source == "inferred", "bs_input_source": bs_input_source,
                "search": plan["search"], "user_source": "legal",
                "bs_source": "station-prior" if bs_input_source == "inferred" else "legal-memory",
            })
            if plan["search"]:
                self.search_replan_steps.append(int(step))
        return actions
