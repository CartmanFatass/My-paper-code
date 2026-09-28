"""Lawful reset-frozen station prior for the B02 P_BS controller."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy
from experiments.candidates.energy_relay_benchmark.b01.observation import station_records
from experiments.candidates.uav_information_value.controllers import (
    SourceController,
    canonical_legal_users,
)


def station_prior_bs_xy(observations, layout) -> np.ndarray | None:
    """Decode the first valid legal record for each station ID at reset."""
    records = station_records(observations, layout)
    positions = []
    for station_id in (0, 1):
        observers = np.flatnonzero(records["valid"][:, station_id])
        if not len(observers):
            return None
        xy = records["xyz_m"][observers[0], station_id, :2]
        if not np.isfinite(xy).all():
            return None
        positions.append(xy)
    return np.clip((positions[0] - 0.3 * positions[1]) / 0.7, 0.0, 8000.0)


class StationPriorController(SourceController):
    """H_BS with a frozen station prior only until a genuine legal BS sighting."""

    def __init__(self):
        super().__init__("H_BS")

    def reset(self) -> None:
        super().reset()
        self._prior_initialized = False
        self._prior_bs_xy: np.ndarray | None = None

    @property
    def prior_bs_xy(self) -> np.ndarray | None:
        return None if self._prior_bs_xy is None else self._prior_bs_xy.copy()

    def propose(self, observations, state, step, previous_done, modes):
        if not self._prior_initialized:
            self._prior_bs_xy = station_prior_bs_xy(observations, self.heuristic.layout)
            self._prior_initialized = True

        current_bs = observed_bs_xy(observations, self.heuristic.layout)
        if current_bs is not None:
            self._seen_bs_xy = current_bs.copy()
        replans = self.heuristic.replans_next()
        inputs = None
        if replans:
            params = self.heuristic.params
            users = canonical_legal_users(observations, self.heuristic.layout,
                                          params.dedup_tolerance_m)
            if current_bs is not None:
                bs_xy, bs_input_source = current_bs, "observed-current"
            elif self._seen_bs_xy is not None:
                bs_xy, bs_input_source = self._seen_bs_xy.copy(), "observed-memory"
            elif self._prior_bs_xy is not None:
                bs_xy, bs_input_source = self._prior_bs_xy.copy(), "inferred"
            else:
                bs_xy, bs_input_source = None, "absent"
            inputs = {"users_xy": users, "bs_xy": bs_xy}
        actions = self.heuristic.act(observations, modes, inputs)
        if replans:
            plan = self.heuristic.last_plan
            self.diagnostics.append({
                "call": plan["call"], "supplied_user_count": len(inputs["users_xy"]),
                "current_bs_present": current_bs is not None,
                "seen_bs_so_far": self._seen_bs_xy is not None,
                "memory_used": bs_input_source == "observed-memory",
                "prior_used": bs_input_source == "inferred",
                "bs_input_source": bs_input_source,
                "search": plan["search"],
                "user_source": "legal", "bs_source": "station-prior" if bs_input_source == "inferred"
                else "legal-memory",
            })
            if plan["search"]:
                self.search_replan_steps.append(int(step))
        return actions
