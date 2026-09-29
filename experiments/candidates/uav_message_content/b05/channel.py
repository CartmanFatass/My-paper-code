"""The B04 dated endpoint channel, common to all three B05 arms."""

import numpy as np

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import (
    Channel, COST, HORIZON, N, payloads,
)


class ForecastChannel(Channel):
    def __init__(self, seed, horizon=HORIZON):
        super().__init__(seed)
        self.horizon = horizon
        self.forecasts = np.zeros((N, N, 3), dtype=np.float32)

    def resolve_payload(self, sender, packet):
        packet = np.asarray(packet, dtype=np.float32)
        if packet.shape != (10,) or not np.isfinite(packet).all():
            raise ValueError("B05 packet must have ten finite FP32 values")
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
        sent = np.rint(self.records[..., 8] * HORIZON).astype(np.int32)
        expired = valid & ((self.t - sent) >= np.minimum(10, self.horizon - sent))
        self.forecasts[expired] = 0

    def begin_tick(self):
        self.deliver()

    def visible_records(self):
        return np.concatenate((self.records, self.forecasts), axis=-1)


def packet_for(raw, sender, forecast):
    old = payloads(raw)[sender].copy()
    if old.shape != (7,) or old[5] != 0:
        raise ValueError("retained geometry packet contract changed")
    return np.concatenate((old, np.asarray(forecast, dtype=np.float32))).astype(np.float32)


def cache_timing(records, t, horizon):
    valid = records[..., 7] > 0
    sent = np.rint(records[..., 8] * HORIZON).astype(np.int32)
    age = np.where(valid, t - sent, -1).astype(np.int16)
    lead = np.where(valid, np.maximum(np.minimum(10, horizon - sent) - age, 0), 0)
    return age, lead.astype(np.int16)


def endpoints(position, sampled, central, horizon):
    if not 1 <= horizon <= 10:
        raise ValueError("forecast horizon")
    speed = np.array((.03, .03, .30), dtype=np.float32)
    first = np.clip(np.asarray(position, dtype=np.float32) + speed * sampled, 0, 1)
    ordinary = np.clip(first + (horizon - 1) * speed * central, 0, 1)
    sampled_cv = np.clip(first + (horizon - 1) * speed * sampled, 0, 1)
    return ordinary, sampled_cv
