"""Original RR channel timing with a single replaceable packet coordinate."""

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
    """Per-sender five-observation anonymous visible-user moments."""

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

    def spread(self, sender):
        history = self.history[sender]
        count = sum(item[0] for item in history)
        if not count:
            return 0.0
        center = sum((item[1] for item in history), np.zeros(2, dtype=np.float64)) / count
        square = sum(item[2] for item in history) / count
        return float(np.clip(np.sqrt(2 * max(square - float(center @ center), 0)), 0, 1))


def hand_payload(arm, raw, sender, sightings, scalar=None):
    packet = payloads(raw)[sender].copy()
    if arm == "B":
        pass
    elif arm == "O":
        packet[5] = sightings.spread(sender)
    elif arm == "L":
        if scalar is None or not 0 <= float(scalar) <= 1:
            raise ValueError("L needs one unit-interval scalar")
        packet[5] = scalar
    else:
        raise ValueError(arm)
    return packet
