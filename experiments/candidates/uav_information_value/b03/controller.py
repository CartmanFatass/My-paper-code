"""Reset-frozen legal station-0 anchor under the unchanged P_BS decision rule."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import station_records
from experiments.candidates.uav_information_value.b02.controller import StationPriorController
from experiments.candidates.uav_information_value.controllers import make_controller as make_reference


def station_zero_xy(observations, layout):
    records = station_records(observations, layout)
    observers = np.flatnonzero(records["valid"][:, 0])
    if not len(observers):
        return None
    xy = records["xyz_m"][observers[0], 0, :2]
    return xy.copy() if np.isfinite(xy).all() else None


class StationZeroController(StationPriorController):
    """Use station 0 until the first real BS sighting, then permanent truth memory."""

    def propose(self, observations, state, step, previous_done, modes):
        if not self._prior_initialized:
            self._prior_bs_xy = station_zero_xy(observations, self.heuristic.layout)
            self._prior_initialized = True
        return super().propose(observations, state, step, previous_done, modes)


def make_controller(arm):
    if arm == "H_BS":
        return make_reference("H_BS")
    if arm == "P_BS":
        return StationPriorController()
    if arm == "S0_BS":
        return StationZeroController()
    raise ValueError(f"unknown B03 arm {arm!r}")
