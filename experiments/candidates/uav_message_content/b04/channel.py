"""Fixed RR channel with a dated three-coordinate forecast tail."""

import numpy as np

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import (
    Channel, COST, HORIZON, N, payloads,
)


class ForecastChannel(Channel):
    def __init__(self, seed, horizon=HORIZON):
        super().__init__(seed)
        self.horizon = horizon
        self.forecasts = np.zeros((N, N, 3), dtype=np.float32)

    def features_with_tail(self):
        return self.features(), self.forecasts.reshape(N, 15).copy()

    def resolve_payload(self, sender, packet):
        packet = np.asarray(packet, dtype=np.float32)
        if packet.shape != (10,) or not np.isfinite(packet).all():
            raise ValueError("B04 packet must have ten finite FP32 values")
        if self.pending[sender]:
            raise RuntimeError("fixed RR sender pending")
        self.attempts += 1
        due = self.t + (1 if self.good else 5)
        self.inflight.append((sender, self.t, due, packet.copy()))
        self.pending[sender] = True
        self.accepted += 1
        self.max_pending = max(self.max_pending, int(self.pending.sum()))
        return COST, due

    def deliver(self):
        self.delivered_events = []
        later = []
        for sender, sent, due, packet in self.inflight:
            if due <= self.t:
                peers = np.arange(N) != sender
                self.records[peers, sender, :7] = packet[:7]
                self.records[peers, sender, 7] = 1
                self.records[peers, sender, 8] = sent / HORIZON
                self.forecasts[peers, sender] = packet[7:]
                self.pending[sender] = False
                self.delivered += 1
                self.delivered_events.append((sender, sent, due))
            else:
                later.append((sender, sent, due, packet))
        self.inflight = later
        valid = self.records[..., 7] > 0
        self.records[..., 9] = np.where(valid, self.t / HORIZON - self.records[..., 8], 0)
        self.age_sum += float(self.records[..., 9].sum() * HORIZON)
        self.age_count += int(valid.sum())
        for sender in range(N):
            sent = np.rint(self.records[:, sender, 8] * HORIZON).astype(int)
            expired = valid[:, sender] & ((self.t - sent) >= np.minimum(10, self.horizon - sent))
            self.forecasts[expired, sender] = 0

    def begin_tick(self):
        self.deliver()

    def visible_records(self):
        return np.concatenate((self.records, self.forecasts), axis=-1)


def packet_for(raw, sender, forecast):
    old = payloads(raw)[sender].copy()
    if old.shape != (7,) or old[5] != 0:
        raise ValueError("geometry packet contract changed")
    return np.concatenate((old, np.asarray(forecast, dtype=np.float32))).astype(np.float32)
