"""Original channel timing with an explicit seven-float payload slot."""

from collections import deque

import numpy as np

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import (
    Channel, COST, N, payloads,
)


class ContentChannel(Channel):
    def resolve_payload(self, sender, payload):
        packet = np.asarray(payload, dtype=np.float32)
        if packet.shape != (7,) or not np.isfinite(packet).all():
            raise ValueError("packet must contain seven finite float32 values")
        requested = np.zeros(N, dtype=bool)
        requested[sender] = True
        attempts = requested & ~self.pending
        number = int(attempts.sum())
        self.attempts += number
        if number != 1:
            raise RuntimeError("fixed RR sender was pending")
        due = self.t + (1 if self.good else 5)
        self.inflight.append((sender, self.t, due, packet.copy()))
        self.pending[sender] = True
        self.accepted += 1
        self.max_pending = max(self.max_pending, int(self.pending.sum()))
        return COST, due


class Sightings:
    """Per-sender five-observation moments, with no user identity."""

    def __init__(self):
        self.history = [deque(maxlen=5) for _ in range(N)]

    def observe(self, raw):
        raw = np.asarray(raw, dtype=np.float32)
        users = raw[:, 3:63].reshape(N, 20, 3)
        visible = users[..., 2] > 0
        absolute = users[..., :2] + raw[:, None, :2]
        for i in range(N):
            xy = absolute[i, visible[i]]
            self.history[i].append((len(xy), xy.sum(0, dtype=np.float64),
                                    np.square(xy.astype(np.float64)).sum()))

    def payload(self, raw, sender):
        history = self.history[sender]
        count = sum(item[0] for item in history)
        center = sum((item[1] for item in history), np.zeros(2, dtype=np.float64)) / max(count, 1)
        square = sum(item[2] for item in history) / max(count, 1)
        radius = np.sqrt(max(square - float(center @ center), 0) / 2) if count else 0
        if not count:
            center[:] = 0
        return np.concatenate((raw[sender, :3], center,
                               [radius, count / (20 * len(history))])).astype(np.float32)


def hand_payload(arm, raw, sender, sightings):
    if arm == "C":
        return payloads(raw)[sender]
    if arm == "H":
        return sightings.payload(raw, sender)
    raise ValueError(arm)
