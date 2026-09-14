"""The selected finite communication task; all payloads use local observations."""

import numpy as np

N, HORIZON, COST = 5, 256, .001
EXTRA_SIZE = 63


def payloads(raw):
    raw = np.asarray(raw, dtype=np.float32)
    users = raw[:, 3:63].reshape(N, 20, 3)
    visible = users[..., 2] > 0
    count = visible.sum(1)
    xy = (users[..., :2] * visible[..., None]).sum(1) / np.maximum(count[:, None], 1)
    centroid = np.zeros((N, 3), dtype=np.float32)
    centroid[:, :2] = np.where(count[:, None] > 0, xy + raw[:, :2], 0)
    return np.concatenate((raw[:, :3], centroid, count[:, None] / 20), axis=1).astype(np.float32)


class Channel:
    """One episode owns the RNG, in-flight packets and receiver records."""

    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.good = bool(self.rng.integers(2))
        self.t = 0
        self.pending = np.zeros(N, dtype=bool)
        self.inflight = []
        # Receiver, physical sender, [payload7, validity, send time, age].
        self.records = np.zeros((N, N, 10), dtype=np.float32)
        self.attempts = self.collisions = self.accepted = self.delivered = 0
        self.max_pending = 0
        self.age_sum = self.age_count = 0

    def begin_tick(self):
        later = []
        for sender, sent, due, payload in self.inflight:
            if due <= self.t:
                peers = np.arange(N) != sender
                self.records[peers, sender, :7] = payload
                self.records[peers, sender, 7] = 1
                self.records[peers, sender, 8] = sent / HORIZON
                self.pending[sender] = False
                self.delivered += 1
            else:
                later.append((sender, sent, due, payload))
        self.inflight = later
        valid = self.records[..., 7] > 0
        self.records[..., 9] = np.where(valid, self.t / HORIZON - self.records[..., 8], 0)
        self.age_sum += float(self.records[..., 9].sum() * HORIZON)
        self.age_count += int(valid.sum())

    def features(self):
        channel = np.tile(np.eye(2, dtype=np.float32)[int(self.good)], (N, 1))
        clock = np.tile(np.eye(N, dtype=np.float32)[self.t % N], (N, 1))
        return np.concatenate((channel, np.eye(N, dtype=np.float32), clock,
                               self.pending[:, None], self.records.reshape(N, 50)), axis=1)

    def resolve(self, requested, raw):
        attempts = np.asarray(requested, dtype=bool) & ~self.pending
        senders = np.flatnonzero(attempts)
        number = int(senders.size)
        self.attempts += number
        if number == 1:
            sender = int(senders[0])
            self.inflight.append((sender, self.t, self.t + (1 if self.good else 5),
                                  payloads(raw)[sender].copy()))
            self.pending[sender] = True
            self.accepted += 1
            self.max_pending = max(self.max_pending, int(self.pending.sum()))
        elif number > 1:
            self.collisions += number
        return COST * number

    def advance(self):
        self.t += 1
        if self.rng.random() >= .95:
            self.good = not self.good

    def facts(self):
        return dict(attempts=self.attempts, collided_attempts=self.collisions,
                    accepted_packets=self.accepted, delivered_packets=self.delivered,
                    pending_at_end=int(self.pending.sum()), max_pending=self.max_pending,
                    mean_observed_message_age=(self.age_sum / self.age_count if self.age_count else None))
