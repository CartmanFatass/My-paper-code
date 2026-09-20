"""Fixed crossing skills and a delayed TDMA channel for information-timing C01."""

from dataclasses import dataclass

import numpy as np


APPROACH, CROSSING, DONE = 0, 1, 2
PERIODS = (12, 16)
FRAME = 8
OBS_SIZE = 22
PACKET_BYTES = 7


@dataclass(frozen=True)
class Worlds:
    """Exogenous values are addressed by world/tick/agent, never action consumption."""

    advances: np.ndarray
    jobs: np.ndarray
    ids: tuple[int, ...]

    @classmethod
    def make(cls, master, phase, ids, horizon=96):
        if horizon <= 0 or horizon % 48:
            raise ValueError("horizon must end on both fixed skill clocks (multiple of 48)")
        ids = tuple(int(i) for i in ids)
        if not ids:
            raise ValueError("at least one world is required")
        advances, jobs = [], []
        for world in ids:
            move_rng = np.random.default_rng(np.random.SeedSequence([master, phase, world, 1]))
            job_rng = np.random.default_rng(np.random.SeedSequence([master, phase, world, 2]))
            advances.append(move_rng.random((horizon, 2)) < .75)
            jobs.append(job_rng.integers(1, 8, (horizon, 2), dtype=np.int16))
        return cls(np.stack(advances), np.stack(jobs), ids)


def project(payload, sent, t):
    """Project only transmitted contents; an expired commitment yields unknown."""
    age = np.maximum(t - sent, 0)
    valid = (sent >= 0) & (age < payload[..., 3])
    projected = payload.astype(np.int16, copy=True)
    approach = projected[..., 0] == APPROACH
    projected[..., 1] = np.where(approach,
        np.maximum(0, projected[..., 1] - np.floor(.75 * age).astype(np.int16)),
        projected[..., 1])
    crossing = projected[..., 0] == CROSSING
    projected[..., 2] = np.where(crossing, np.maximum(0, projected[..., 2] - age), 0)
    projected[..., 0] = np.where(crossing & (projected[..., 2] == 0), DONE, projected[..., 0])
    projected[..., 3] = np.maximum(0, projected[..., 3] - age)
    return projected, valid, age


def gate(own, peer, valid, identity):
    """Immutable feedback: known occupancy blocks; robot 1 also yields near the gate."""
    eligible = (own[..., 0] == APPROACH) & (own[..., 1] == 0) & (own[..., 3] >= 2)
    blocked = valid & (peer[..., 0] == CROSSING)
    yields = (identity == 1) & valid & (peer[..., 0] == APPROACH) & (peer[..., 1] <= 1)
    return eligible & ~blocked & ~yields


@dataclass(frozen=True)
class LocalView:
    """The only scheduler API. There is no reference to the current peer state."""

    t: int
    horizon: int
    sender: int
    own: np.ndarray
    last_sent: np.ndarray
    last_sent_time: np.ndarray
    peer: np.ndarray
    peer_valid: np.ndarray
    peer_age: np.ndarray
    available: np.ndarray

    @property
    def forced(self):
        return self.t % FRAME >= FRAME - 2

    @property
    def choice_mask(self):
        return self.available & ~np.full(len(self.available), self.forced)

    @property
    def own_age(self):
        return np.where(self.last_sent_time >= 0, self.t - self.last_sent_time, self.horizon)

    @property
    def peer_remaining(self):
        period = PERIODS[1 - self.sender]
        return period - self.t % period

    def features(self):
        n = len(self.available)
        own_onehot = np.eye(3, dtype=np.float32)[self.own[:, 0]]
        peer_onehot = np.eye(3, dtype=np.float32)[self.peer[:, 0]] * self.peer_valid[:, None]
        last_valid = self.last_sent_time >= 0
        scalars = np.column_stack((
            self.own[:, 1] / 7, self.own[:, 2] / 2, self.own[:, 3] / 16,
            np.full(n, self.peer_remaining / 16), last_valid,
            np.minimum(self.own_age, 16) / 16,
            (~last_valid) | (self.own[:, 0] != self.last_sent[:, 0]),
            np.where(last_valid, np.abs(self.own[:, 1] - self.last_sent[:, 1]) / 7, 1),
            self.peer_valid,
        ))
        tail = np.column_stack((
            np.where(self.peer_valid, self.peer[:, 1] / 7, 0),
            np.where(self.peer_valid, self.peer[:, 2] / 2, 0),
            np.minimum(self.peer_age, 16) / 16,
            np.full(n, self.sender), np.full(n, (self.horizon - self.t) / self.horizon),
            np.full(n, self.t % FRAME / FRAME), self.available,
        ))
        features = np.concatenate((own_onehot, scalars, peer_onehot, tail), axis=1).astype(np.float32)
        assert features.shape == (n, OBS_SIZE)
        return features


def predecision_slot(t, sender):
    start = t // FRAME * FRAME
    slots = np.arange(start + sender, start + FRAME, 2)
    peer_period = PERIODS[1 - sender]
    next_boundary = (start // peer_period + 1) * peer_period
    before = slots[slots + 1 <= next_boundary]
    if next_boundary <= start + FRAME and before.size:
        return int(before[-1])
    return int(slots[-1])


def simple_requests(view, arm, distance_delta=2, age_limit=None):
    if arm == "POLL":
        return np.full(len(view.available), view.t % FRAME == view.sender)
    if arm == "PRE_DECISION":
        return np.full(len(view.available), view.t == predecision_slot(view.t, view.sender))
    if arm != "AGE_CHANGE":
        raise ValueError(f"unknown fixed scheduler {arm}")
    previous = view.last_sent_time >= 0
    changed = (~previous) | (view.own[:, 0] != view.last_sent[:, 0]) | (
        np.abs(view.own[:, 1] - view.last_sent[:, 1]) >= distance_delta)
    own_near = (view.own[:, 0] == CROSSING) | (
        (view.own[:, 0] == APPROACH) & (view.own[:, 1] <= 2))
    peer_near = (~view.peer_valid) | (view.peer[:, 0] == CROSSING) | (
        (view.peer[:, 0] == APPROACH) & (view.peer[:, 1] <= 2))
    too_old = np.zeros(len(previous), dtype=bool) if age_limit is None else (
        (~previous) | (view.own_age >= age_limit))
    return (changed & (own_near | peer_near)) | too_old | (
        view.t == predecision_slot(view.t, view.sender))


class CrossingHost:
    """Vectorized independent worlds; no learned component changes these dynamics."""

    def __init__(self, worlds):
        self.worlds = worlds
        self.batch, self.horizon, _ = worlds.advances.shape
        self.t = 0
        self.stage = np.full((self.batch, 2), DONE, dtype=np.int16)
        self.distance = np.zeros((self.batch, 2), dtype=np.int16)
        self.cross_left = np.zeros((self.batch, 2), dtype=np.int16)
        self.cache = np.zeros((self.batch, 2, 4), dtype=np.int16)
        self.cache_time = np.full((self.batch, 2), -1, dtype=np.int16)
        self.last_sent = np.zeros_like(self.cache)
        self.last_sent_time = np.full_like(self.cache_time, -1)
        self.pending = np.zeros((self.batch, 2), dtype=bool)
        self.pending_payload = np.zeros_like(self.cache)
        self.pending_time = np.full_like(self.cache_time, -1)
        self.spent = np.zeros((self.batch, 2), dtype=bool)
        metric_names = ("jobs_started", "completed_jobs", "conflicts", "wait_ticks", "gate_opportunities",
            "gate_disagreement", "unknown_gate", "packets", "delivered", "choice_opportunities",
            "forced_packets", "message_age_sum", "message_age_count", "send_peer_actionable",
            "send_before_peer_decision", "send_changed", "send_own_age_sum")
        self.metrics = {name: np.zeros(self.batch, dtype=np.int64) for name in metric_names}
        self.send_phase = np.zeros((self.batch, FRAME), dtype=np.int64)
        self.send_peer_remaining = np.zeros((self.batch, max(PERIODS)), dtype=np.int64)
        self.send_clock_phase = np.zeros((self.batch, 48), dtype=np.int64)
        self._prepare_tick()

    def _prepare_tick(self):
        if self.t >= self.horizon:
            return
        for receiver in range(2):
            delivery = self.pending[:, receiver]
            self.cache[delivery, receiver] = self.pending_payload[delivery, receiver]
            self.cache_time[delivery, receiver] = self.pending_time[delivery, receiver]
            self.metrics["delivered"] += delivery
        self.pending.fill(False)
        if self.t % FRAME == 0:
            self.spent.fill(False)
        for agent, period in enumerate(PERIODS):
            if self.t % period == 0:
                self.stage[:, agent] = APPROACH
                self.distance[:, agent] = self.worlds.jobs[:, self.t, agent]
                self.cross_left[:, agent] = 0
                self.metrics["jobs_started"] += 1

    def payloads(self):
        remaining = np.broadcast_to(np.asarray(PERIODS) - self.t % np.asarray(PERIODS),
                                    (self.batch, 2))
        return np.stack((self.stage, self.distance, self.cross_left, remaining), axis=-1)

    def view(self):
        if self.t >= self.horizon:
            raise RuntimeError("no scheduler observation after terminal time")
        sender = self.t % 2
        peer, valid, age = project(self.cache[:, sender], self.cache_time[:, sender], self.t)
        return LocalView(self.t, self.horizon, sender, self.payloads()[:, sender].copy(),
            self.last_sent[:, sender].copy(), self.last_sent_time[:, sender].copy(),
            peer, valid, age, (~self.spent[:, sender]).copy())

    def step(self, requested):
        view = self.view()
        requested = np.asarray(requested, dtype=bool)
        if requested.shape != (self.batch,):
            raise ValueError("one Boolean request per independent world is required")
        sender, receiver = view.sender, 1 - view.sender
        sent = view.available & (requested | view.forced)
        self.metrics["choice_opportunities"] += view.choice_mask
        self.metrics["packets"] += sent
        self.metrics["forced_packets"] += sent & view.forced
        self.spent[sent, sender] = True
        self.last_sent[sent, sender] = view.own[sent]
        self.last_sent_time[sent, sender] = self.t
        self.pending[sent, receiver] = True
        self.pending_payload[sent, receiver] = view.own[sent]
        self.pending_time[sent, receiver] = self.t
        self.send_phase[:, self.t % FRAME] += sent
        self.send_peer_remaining[:, view.peer_remaining - 1] += sent
        self.send_clock_phase[:, self.t % 48] += sent
        self.metrics["send_before_peer_decision"] += sent & (view.peer_remaining == 1)
        changed = (view.last_sent_time < 0) | (view.own[:, 0] != view.last_sent[:, 0]) | (
            view.own[:, 1] != view.last_sent[:, 1])
        self.metrics["send_changed"] += sent & changed
        self.metrics["send_own_age_sum"] += np.where(sent, view.own_age, 0)

        own = self.payloads()
        peer, valid, age = project(self.cache, self.cache_time, self.t)
        decisions = gate(own, peer, valid, np.arange(2))
        gate_opportunity = (own[..., 0] == APPROACH) & (own[..., 1] == 0) & (own[..., 3] >= 2)
        # Factual current-snapshot comparison at the encountered state, diagnostic only.
        oracle_decisions = gate(own, own[:, ::-1], np.ones_like(valid), np.arange(2))
        self.metrics["gate_opportunities"] += gate_opportunity.sum(1)
        self.metrics["gate_disagreement"] += (gate_opportunity & (decisions != oracle_decisions)).sum(1)
        self.metrics["unknown_gate"] += (gate_opportunity & ~valid).sum(1)
        self.metrics["wait_ticks"] += (gate_opportunity & ~decisions).sum(1)
        self.metrics["message_age_sum"] += np.where(valid, age, 0).sum(1)
        self.metrics["message_age_count"] += valid.sum(1)
        actionable_peer = (own[:, receiver, 0] == CROSSING) | (
            (own[:, receiver, 0] == APPROACH) & (own[:, receiver, 1] <= 1))
        self.metrics["send_peer_actionable"] += sent & actionable_peer

        approaching = (self.stage == APPROACH) & (self.distance > 0)
        moves = approaching & self.worlds.advances[:, self.t]
        self.distance[moves] -= 1
        self.stage[decisions] = CROSSING
        self.cross_left[decisions] = 2
        occupying = self.stage == CROSSING
        conflicts = occupying.sum(1) == 2
        self.metrics["conflicts"] += conflicts
        self.stage[conflicts] = DONE
        self.cross_left[conflicts] = 0
        crossing = self.stage == CROSSING
        self.cross_left[crossing] -= 1
        completed = crossing & (self.cross_left == 0)
        self.stage[completed] = DONE
        self.distance[self.stage == DONE] = 0
        reward = completed.sum(1).astype(np.float32)
        self.metrics["completed_jobs"] += completed.sum(1)
        self.t += 1
        self._prepare_tick()
        return reward

    def rows(self):
        rows = []
        for i, world_id in enumerate(self.worlds.ids):
            row = {key: int(value[i]) for key, value in self.metrics.items()}
            row.update(world_id=world_id, steps=self.t,
                service=row["completed_jobs"] / row["jobs_started"],
                bytes=row["packets"] * PACKET_BYTES, timing_slot_bits=self.t,
                pending_at_end=int(self.pending[i].sum()),
                send_phase=self.send_phase[i].tolist(),
                send_peer_remaining=self.send_peer_remaining[i].tolist(),
                send_clock_phase=self.send_clock_phase[i].tolist())
            rows.append(row)
        return rows
