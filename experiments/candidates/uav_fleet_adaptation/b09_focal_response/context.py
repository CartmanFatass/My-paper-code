"""Lawful single-agent, consecutive-frame peer features for B09."""
from numbers import Integral

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import _parse
from experiments.candidates.uav_local_peer_forecast.controller import associate


def _tick(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or not 0 <= value < 256:
        raise ValueError("tick must be an original native integer in [0,256)")
    return int(value)


def _fp32(value, shape, name):
    if not isinstance(value, np.ndarray) or value.dtype != np.float32 or value.shape != shape:
        raise ValueError(f"{name} requires FP32 shape {shape}")
    if not np.isfinite(value).all():
        raise FloatingPointError(f"nonfinite {name}")
    return value


class PeerHistory:
    """No planner, identities, commands, user history or invisible-peer memory."""
    def __init__(self):
        self.reset()

    def reset(self):
        self._previous_peers = np.empty((0, 3), dtype=np.float64)
        self._clock = -1
        self.matches = np.full(4, -1, dtype=np.int64)
        self.delta = np.zeros((4, 3), dtype=np.float64)
        self.gate_counts = np.zeros(4, dtype=np.int64)
        self.counters = dict(ingests=0, adjacent_updates=0, pair_gates=0,
                             matched_rows=0, moving_rows=0)

    def ingest(self, row, t):
        t = _tick(t)
        row = _fp32(row, (104,), "local row")
        if t != self._clock + 1 or float(row[103]) != t / 256:
            raise ValueError("expected consecutive native clock and exact row clock")
        _, _, _, peers = _parse(row)
        if len(peers) > 4:
            raise ValueError("original N5 row has at most four visible peers")
        matches, delta, gates = associate(peers, self._previous_peers)
        descriptor = np.zeros((4, 4), dtype=np.float32)
        n = len(peers)
        descriptor[:n, :3] = delta / 30.
        descriptor[:n, 3] = matches >= 0
        self.matches.fill(-1)
        self.delta.fill(0)
        self.gate_counts.fill(0)
        self.matches[:n], self.delta[:n], self.gate_counts[:n] = matches, delta, gates
        self.counters["ingests"] += 1
        if t:
            self.counters["adjacent_updates"] += 1
            self.counters["pair_gates"] += n * len(self._previous_peers)
        self.counters["matched_rows"] += int((matches >= 0).sum())
        self.counters["moving_rows"] += int(np.any(delta != 0, axis=1).sum())
        self._previous_peers = peers.copy()
        self._clock = t
        return dict(descriptor=descriptor.reshape(16).copy(), matches=self.matches.copy(),
                    delta=self.delta.copy(), gate_counts=self.gate_counts.copy(),
                    n_peers=n, counters=self.counters.copy())


def pack_context(features, hidden, tick, history_descriptor=None):
    """Copy inherited coordinates verbatim, followed by clock and current ranks."""
    features = _fp32(features, (114,), "features")
    hidden = _fp32(hidden, (128,), "hidden")
    tick = _tick(tick)
    descriptor = (np.zeros(16, dtype=np.float32) if history_descriptor is None else
                  _fp32(history_descriptor, (16,), "history descriptor"))
    return np.concatenate((features, hidden, np.array([tick / 256], dtype=np.float32), descriptor))
