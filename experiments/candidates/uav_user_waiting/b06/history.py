"""Joint local/global modeled history; native grants never enter this module."""

from dataclasses import dataclass, field

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss, service_metrics, user_sinr_from_path_loss
from experiments.candidates.uav_user_waiting.b01.history import (
    ServiceHistory as BurdenHistory, ExecutionHistory as FrozenExecutionHistory,
)
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.scheduler import history_record as global_history_record
from experiments.candidates.uav_user_waiting.b05.allocation import LeastRecentlyServed

WORK_KEYS = ('model_fleet_ticks', 'model_transitions_completed', 'lrs_row_selections',
             'lrs_rows_completed', 'sinr_link_entries', 'model_geometry_snapshots')


def history_record(history):
    return dict(global_history_record(history), last_grant=history.last_grant.copy())


@dataclass
class ServiceHistory(BurdenHistory):
    last_grant: np.ndarray = field(default_factory=lambda: np.full((p.N, p.U), -1, np.int64))

    def copy(self):
        return ServiceHistory(self.start_tick, self.last.copy(), self.windows.copy(),
                              self.burden.copy(), self.last_grant.copy())


def _add(work, key, amount=1):
    if work is not None:
        work[key] = work.get(key, 0) + amount


def transition(history, tick, sinr, *, work=None, partial=None):
    """Return a complete new history or throw; never mutate the input history."""
    values = np.asarray(sinr)
    if values.shape != (p.N, p.U) or not np.all(np.isfinite(values) | np.isneginf(values)):
        raise ValueError('invalid modeled SINR')
    eligible = values >= 3.
    if np.any(eligible.sum(axis=0) > 1):
        raise ValueError('modeled eligible user sets must be disjoint')
    new = history.copy()
    connections = np.zeros((p.N, p.U), bool)
    grants = np.full((p.N, 10), -1, np.int8)
    if partial is not None:
        partial.update(input_history=history_record(history), grants=grants.copy(), completed_rows=0)
    for member in range(p.N):
        ids = np.flatnonzero(eligible[member])
        actor = LeastRecentlyServed()
        actor.last_grant = new.last_grant[member]
        _add(work, 'lrs_row_selections')
        selected = actor.grant(ids, values[member, ids], int(tick))
        connections[member, selected] = True
        grants[member, :len(selected)] = selected
        _add(work, 'lrs_rows_completed')
        if partial is not None:
            partial.update(grants=grants.copy(), completed_rows=member + 1)
    metrics = service_metrics(values, connections)
    new.update(tick, connections.any(axis=0))
    native = np.array([metrics['J'], metrics['served'], metrics['quality']], np.float64)
    _add(work, 'model_transitions_completed')
    return new, connections, native, grants


def advance(history, tick, losses, mask, *, work=None, partial=None):
    _add(work, 'model_fleet_ticks')
    _add(work, 'sinr_link_entries', p.N * p.U)
    sinr = user_sinr_from_path_loss(losses, transmitter_mask=p.mask_array(mask))
    return transition(history, tick, sinr, work=work, partial=partial)


def model(positions, sites, mask, history, tick, *, work=None, partial=None):
    _add(work, 'model_geometry_snapshots')
    losses = free_space_user_path_loss(positions, sites)
    return advance(history, tick, losses, mask, work=work, partial=partial)


class ExecutionHistory(FrozenExecutionHistory):
    def __init__(self, sites):
        super().__init__(sites)
        self.history = ServiceHistory()
        self.predicted_grants = {}
        self.settlement_partial = {}
        self.work_counts = {key: 0 for key in WORK_KEYS}

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
            position = np.clip(origin + commands * 30., p.LOW, p.HIGH)
            self.settlement_partial = dict(tick=tick, mask=int(mask), positions=position.copy(),
                input_history=history_record(self.history), grants=np.full((p.N, 10), -1, np.int8), completed_rows=0)
            history, connections, _, grants = evaluate(position, self.sites, mask, self.history, tick,
                work=self.work_counts, partial=self.settlement_partial)
            contacts, grant_copy = connections.any(axis=0), grants.copy()
            # All potentially failing numerical work preceded this joint commit.
            self.position, self.history = position, history
            self.predicted[tick] = contacts
            self.predicted_grants[tick] = grant_copy
            self.next_unsettled += 1
            self.settlement_partial = {}
            completed += 1
            check()
        if stop in self.anchors:
            self.position = self.anchors[stop].copy()
        return completed, True
