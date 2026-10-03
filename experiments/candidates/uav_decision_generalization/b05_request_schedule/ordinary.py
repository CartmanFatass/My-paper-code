"""Corrected four-way G: public kinematics, exact known heads, future fluid."""
from dataclasses import dataclass

import numpy as np

from .contract import (CONTROL_PERIOD, G_HORIZON, HORIZON, LAST_ARRIVAL_TICK,
                       SERVICE_TICKS, TERMINAL_WEIGHT)
from .task import _array, candidate_slots, slot_positions


@dataclass(frozen=True)
class GPrediction:
    costs: np.ndarray
    counters: dict

    def __post_init__(self):
        object.__setattr__(self, "costs", _array(self.costs, np.float64, (4,), "G costs"))


def greedy_action(costs):
    """Canonical raw float64 cost then action-ID tie rule."""
    costs = _array(costs, np.float64, (4,), "G costs")
    return int(np.argmin(costs))


def g_values(state):
    if state.tick >= HORIZON:
        raise ValueError("no G action at the terminal accounting report")
    horizon = min(G_HORIZON, HORIZON - state.tick)
    candidates = candidate_slots(state)
    positions = np.tile(state.positions, (4, 1, 1))
    known = np.tile(state.counts, (4, 1))
    progress = np.tile(state.progress, (4, 1))
    future = np.zeros((4, 4), dtype=np.float64)
    costs = np.zeros(4, dtype=np.float64)
    all_targets = slot_positions(state.users)
    current = np.tile(state.active_slots, (4, 1))
    pair_ids = np.asarray(state.pairs, dtype=np.int64)
    rows = np.arange(4)[:, None]
    future_boundaries = 0
    for step in range(horizon):
        tick = state.tick + step
        slots = current if step < CONTROL_PERIOD else candidates
        targets = all_targets[slots]
        if tick > state.tick and tick <= LAST_ARRIVAL_TICK and tick % CONTROL_PERIOD == 0:
            future += state.probabilities
            future_boundaries += 1
        costs += (known + future).sum(axis=1)
        delta = targets - positions
        distance = np.linalg.norm(delta, axis=-1)
        positions += delta * (30.0 / np.maximum(30.0, distance))[:, :, None]
        close = np.linalg.norm(positions - targets, axis=-1) <= 1.0
        available = np.zeros((4, 4), dtype=bool)
        pair_close = close[:, pair_ids].all(axis=2)
        clusters = slots[:, pair_ids[:, 0]] // 2
        available[rows, clusters] = pair_close
        service_known = available & (known > 0)
        service_fluid = available & (known == 0)
        progress = np.where(service_known, progress + 1, 0)
        finished = service_known & (progress == SERVICE_TICKS)
        known -= finished
        progress[finished] = 0
        # The masks precede completion: no fluid drain on a known-head finish.
        future = np.where(service_fluid, np.maximum(0.0, future - 1.0 / SERVICE_TICKS), future)
    costs += TERMINAL_WEIGHT * (known + future).sum(axis=1)
    return GPrediction(costs, {
        "queries": 1, "candidate_values": 4, "horizon_ticks": horizon,
        "candidate_ticks": 4 * horizon, "cluster_recurrences": 16 * horizon,
        "kinematic_uav_steps": 24 * horizon,
        "future_arrival_boundaries": future_boundaries,
        "future_arrival_cluster_additions": 16 * future_boundaries,
        "radio_calls": 0,
    })
