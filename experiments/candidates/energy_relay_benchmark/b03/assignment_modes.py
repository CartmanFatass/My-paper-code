"""Stage 2-0 assignment modes of H_central's target step (zero-fit stake sizing).

``AssignmentModeHeuristic`` is B01's ``LayoutHeuristic`` with ``_assign_targets`` replaced by one
of three rules on the same inputs (``plan`` passes ``uavs = available`` in ascending index and
``points = priority[:len(available)]``: relays first, then centroids by descending user count):

- ``hungarian``: the base method unchanged (distance cost, previous-target hysteresis,
  ``_assign`` = Hungarian); the recorded H_central.
- ``identity``: the j-th available UAV takes priority slot j (``uavs[j] -> points[j]``); no cost
  is computed.  With all eight UAVs available this is UAV i -> slot i.
- ``independent_nearest``: the base cost matrix (hysteresis included, built exactly as the base
  does), then every UAV takes its own row-wise cheapest point; duplicates allowed, unclaimed
  points unserved.

Everything else (planning, movement, information, shield) is H_central's.
"""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    HeuristicParams,
    LayoutHeuristic,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT,
    ObservationLayout,
)

ASSIGNMENT_MODES = ("hungarian", "identity", "independent_nearest")


class AssignmentModeHeuristic(LayoutHeuristic):
    """``LayoutHeuristic`` whose target step uses one of ``ASSIGNMENT_MODES``."""

    def __init__(self, params: HeuristicParams, mode: str,
                 layout: ObservationLayout = S7S2_LAYOUT):
        if mode not in ASSIGNMENT_MODES:
            raise ValueError(f"assignment mode must be one of {ASSIGNMENT_MODES}")
        self.mode = mode
        super().__init__(params, layout)

    def _assign_targets(self, own_xy, uavs, points, targets) -> set[int]:
        if self.mode == "hungarian":
            return super()._assign_targets(own_xy, uavs, points, targets)
        if self.mode == "identity":
            assigned = set()
            for j, uav in enumerate(uavs):
                if j < len(points):
                    targets[uav] = points[j]
                    assigned.add(int(uav))
            return assigned
        # independent_nearest: the base cost matrix (verbatim), then a row-wise argmin.
        params = self.params
        if len(uavs) == 0 or len(points) == 0:
            return set()
        cost = np.linalg.norm(own_xy[uavs][:, None, :] - points[None, :, :], axis=2)
        # Hysteresis: the target continuing a UAV's previous target is cheaper by the margin,
        # so the UAV switches only if another target is closer by more than switch_margin_m.
        for row, uav in enumerate(uavs):
            previous = self.targets_xy[uav]
            if np.all(np.isfinite(previous)):
                continuing = int(np.argmin(np.linalg.norm(points - previous, axis=1)))
                cost[row, continuing] -= params.switch_margin_m
        assigned = set()
        for row, uav in enumerate(uavs):
            col = int(np.argmin(cost[row]))
            targets[uav] = points[col]
            assigned.add(int(uav))
        return assigned


class AssignmentModeController(HeuristicController):
    """``HeuristicController`` driving an ``AssignmentModeHeuristic`` (central plan inputs)."""

    def __init__(self, params: HeuristicParams, env, mode: str):
        super().__init__(params, env)
        self.heuristic = AssignmentModeHeuristic(params, mode)
        self.mode = mode
