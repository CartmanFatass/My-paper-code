"""Lawful model history: executed actions and decoded position anchors only."""

from dataclasses import dataclass, field

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment, service_metrics,
    user_sinr_from_path_loss,
)
from experiments.candidates.uav_radio_activation.b03.protocol import LOW, HIGH, N, U, mask_array


def model(positions, sites, mask):
    loss = free_space_user_path_loss(positions, sites)
    sinr = user_sinr_from_path_loss(loss, transmitter_mask=mask_array(mask))
    connections = greedy_connection_assignment(sinr)
    metrics = service_metrics(sinr, connections)
    return connections.any(axis=0), np.array([metrics['J'], metrics['served'], metrics['quality']])


@dataclass
class ServiceHistory:
    start_tick: int = 0
    last: np.ndarray = field(default_factory=lambda: np.full(U, -1, dtype=int))
    windows: np.ndarray = field(default_factory=lambda: np.zeros((4, U), dtype=bool))

    def copy(self):
        return ServiceHistory(self.start_tick, self.last.copy(), self.windows.copy())

    def update(self, tick, served):
        served = np.asarray(served, dtype=bool)
        if served.shape != (U,) or not 0 <= tick < 256:
            raise ValueError('invalid model service transition')
        window = tick // 64
        new_pairs = int((served & ~self.windows[window]).sum()) if window * 64 >= self.start_tick else 0
        self.windows[window] |= served
        self.last[served] = tick
        return new_pairs


def age_groups(history):
    # -1 is unseen within-task at a0, or a censored oldest group when a>0.
    # Censored users have unknown individual true ages; no row priority is imposed.
    return tuple(history.last == value for value in np.unique(history.last))


class ExecutionHistory:
    """Atomic settlement; decoded anchors survive an interrupted later settlement."""

    def __init__(self, sites):
        self.sites = np.array(sites, copy=True)
        self.actions = []
        self.anchors = {}
        self.next_unsettled = 0
        self.position = None
        self.start_tick = None
        self.history = ServiceHistory()
        self.predicted = {}

    def append(self, tick, commands, mask):
        if tick != len(self.actions):
            raise ValueError('execution log must append each transition exactly once')
        commands = np.asarray(commands)
        if commands.shape != (N, 3) or not np.isin(commands, (-1, 0, 1)).all():
            raise ValueError('invalid executed commands')
        mask_array(mask)
        self.actions.append((commands.copy(), int(mask)))

    def anchor(self, tick, decoded_position):
        value = np.asarray(decoded_position, dtype=float)
        if tick < self.next_unsettled or value.shape != (N, 3) or not np.isfinite(value).all():
            raise ValueError('invalid decoded anchor')
        if tick in self.anchors and not np.array_equal(value, self.anchors[tick]):
            raise ValueError('conflicting decoded anchor')
        self.anchors[tick] = value.copy()
        if self.start_tick is None:
            # Initial missing reports censor only the unreconstructable prefix.
            # Its actions remain in the log; none becomes a settled/no-service transition.
            self.start_tick = tick
            self.next_unsettled = tick
            self.position = value.copy()
            self.history.start_tick = tick

    def settle(self, stop, check=lambda: None, evaluate=model):
        if not self.next_unsettled <= stop <= len(self.actions):
            raise ValueError('settlement outside executed log')
        completed = 0
        while self.next_unsettled < stop:
            check()
            tick = self.next_unsettled
            origin = self.anchors.get(tick, self.position)
            if origin is None:
                return completed, False
            commands, mask = self.actions[tick]
            position = np.clip(origin + commands * 30., LOW, HIGH)
            served, _ = evaluate(position, self.sites, mask)
            # A completed transition commits as one unit before the next deadline check.
            history = self.history.copy()
            history.update(tick, served)
            self.position, self.history = position, history
            self.predicted[tick] = np.asarray(served, dtype=bool).copy()
            self.next_unsettled += 1
            completed += 1
            check()
        if stop in self.anchors:
            self.position = self.anchors[stop].copy()
        return completed, True
