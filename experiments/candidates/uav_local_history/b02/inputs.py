"""Actor-owned observation history; no environment or evaluator dependencies."""

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import LocalController, _parse


class ObservationHistory:
    def __init__(self):
        self.cache = LocalController(history=True)
        self.row = None
        self.own = None
        self.now = -1
        self.current_sinr = np.zeros(64, dtype=np.float32)
        self.ingests = 0
        self.association_distance_evaluations = 0

    def ingest(self, row, clock):
        self.row = np.array(row, dtype=np.float32, copy=True)
        own, xy, sinr, _peers = _parse(self.row)
        size = len(self.cache.points)
        _, _, _, indices = self.cache._ingest(xy, clock)
        for index in indices:
            self.association_distance_evaluations += size
            if index >= size:
                size += 1
        self.current_sinr[:] = 0
        self.current_sinr[indices] = (sinr + 10) / 50
        self.own, self.now = own, clock
        self.ingests += 1

    def features(self, last_command):
        if self.row is None:
            raise RuntimeError("ingest before requesting features")
        last_command = np.asarray(last_command, dtype=np.float32)
        if last_command.shape != (3,):
            raise ValueError("one agent's last command required")
        points = self.cache.points
        size = len(points)
        packed = np.zeros((64, 7), dtype=np.float32)
        packed[:size, :2] = points / 1000
        packed[:size, 2:4] = (points - self.own[:2]) / 1000
        packed[:size, 4] = (self.now - self.cache.last_seen) / 256
        packed[:size, 5] = self.cache.current_mask
        packed[:size, 6] = self.current_sinr[:size]
        valid = np.arange(64) < size
        context = np.concatenate((self.row, last_command))
        return context, packed, valid


def current_only(points, valid):
    """Nonmutating matched-input diagnostic, not an executed control policy."""
    present = np.asarray(valid, dtype=bool) & (np.asarray(points)[..., 5] != 0)
    return np.where(present[..., None], points, 0), present
