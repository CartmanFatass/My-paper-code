"""A fixed two-decision receiver with one charged context and one refresh packet."""

from dataclasses import dataclass
from itertools import product

import numpy as np


HORIZON = 6
RULES = ("VOI", "PRE_FIRST", "PRE_LAST", "AGE_CHANGE", "INVERSE_CHANGE")
RESTRICTED = ("PRE_FIRST", "PRE_LAST", "AGE_CHANGE", "INVERSE_CHANGE")


@dataclass(frozen=True)
class Worlds:
    ids: np.ndarray
    condition: np.ndarray
    weight: np.ndarray
    risk_tenths: np.ndarray
    flip_draw: np.ndarray

    def __post_init__(self):
        n = len(self.ids)
        for name in ("condition", "weight", "risk_tenths", "flip_draw"):
            value = getattr(self, name)
            if value.shape != (n,) or not np.issubdtype(value.dtype, np.integer):
                raise ValueError(f"invalid world field {name}")
        if (not np.isin(self.condition, (0, 1)).all()
                or not np.isin(self.weight, (1, 2, 3)).all()
                or not np.isin(self.risk_tenths, (0, 1, 5, 9)).all()
                or not ((self.flip_draw >= 0) & (self.flip_draw < 10)).all()):
            raise ValueError("world outside fixed C05 support")

    @classmethod
    def make(cls, seed, phase, count):
        rng = np.random.default_rng(np.random.SeedSequence([seed, phase]))
        return cls(np.arange(count), rng.integers(0, 2, count),
            rng.integers(1, 4, count), rng.choice([1, 5, 9], count), rng.integers(0, 10, count))

    @classmethod
    def exact(cls, zero_risk=False):
        cases = np.asarray(list(product((0, 1), (1, 2, 3),
            (0,) if zero_risk else (1, 5, 9), range(10))), dtype=np.int64)
        return cls(np.arange(len(cases)), *(cases[:, i] for i in range(4)))

    def take(self, start, stop):
        return Worlds(*(getattr(self, name)[start:stop] for name in
            ("ids", "condition", "weight", "risk_tenths", "flip_draw")))


@dataclass(frozen=True)
class SenderView:
    """Only current local sensing and a context packet already delivered at tick 1."""

    condition: np.ndarray
    received_weight: np.ndarray
    risk_tenths: np.ndarray

    def features(self):
        return np.stack((self.condition, self.received_weight / 3., self.risk_tenths / 10.),
            axis=1).astype(np.float32)

    def delta_tenths(self):
        return 10 * self.received_weight * self.condition - 4 * self.risk_tenths


def rule(name, view):
    if name == "VOI":
        return view.delta_tenths() > 0
    if name == "PRE_FIRST":
        return np.ones(len(view.condition), dtype=bool)
    if name == "PRE_LAST":
        return np.zeros(len(view.condition), dtype=bool)
    if name == "AGE_CHANGE":
        return view.condition != 0
    if name == "INVERSE_CHANGE":
        return view.condition == 0
    raise ValueError(f"unknown rule: {name}")


class FixedHost:
    """No trainable controller, early stopping, access contention or free request channel.

    prepare() executes tick 0 and delivers its context at tick 1. rollout() consumes
    the sole timing decision, then executes the remaining fixed ticks. The future flip
    draw is private environment state; it is never a member of SenderView.
    """

    def __init__(self, worlds):
        self.worlds = worlds
        self.prepared = False
        self.finished = False

    def prepare(self):
        if self.prepared:
            raise RuntimeError("context may only be sent once")
        self.prepared = True
        n = len(self.worlds.ids)
        # [w, late_weight, action_tick_1, action_tick_2, timestamp_lo, hi, sender_R]
        self.context_packet = np.tile(np.array([0, 4, 2, 4, 0, 0, 0], dtype=np.uint8), (n, 1))
        self.context_packet[:, 0] = self.worlds.weight
        self.context_arrival = np.ones(n, dtype=np.int64)
        self.view = SenderView(self.worlds.condition.copy(),
            self.context_packet[:, 0].astype(np.int64), self.worlds.risk_tenths.copy())
        return self.view

    def rollout(self, early):
        if not self.prepared or self.finished:
            raise RuntimeError("rollout requires one delivered context and cannot resume")
        early = np.asarray(early)
        n = len(self.worlds.ids)
        if early.shape != (n,) or early.dtype != np.bool_:
            raise ValueError("one boolean send decision is required per cycle")
        self.finished = True
        w = self.worlds
        future = np.bitwise_xor(w.condition, w.flip_draw < w.risk_tenths)
        send_tick = np.where(early, 1, 3)
        data_packet = np.empty((n, 4), dtype=np.uint8)
        data_packet[:, 0] = np.where(early, w.condition, future)
        data_packet[:, 1] = send_tick
        data_packet[:, 2] = 0
        data_packet[:, 3] = 1  # sender S
        arrival_tick = data_packet[:, 1].astype(np.int64) + 1
        cache = np.zeros(n, dtype=np.int64)
        cache_stamp = np.full(n, -1, dtype=np.int64)
        cache_trace, stamp_trace = [], []
        actions = np.empty((n, 2), dtype=np.int64)
        sent = np.zeros((n, HORIZON, 2), dtype=bool)
        delivered = np.zeros_like(sent)
        sent[:, 0, 0] = True
        delivered[:, 1, 0] = True
        sent[np.arange(n), send_tick, 1] = True
        delivered[np.arange(n), arrival_tick, 1] = True
        for tick in range(HORIZON):
            arrived = arrival_tick == tick
            cache[arrived] = data_packet[arrived, 0]
            cache_stamp[arrived] = data_packet[arrived, 1]
            cache_trace.append(cache.copy())
            stamp_trace.append(cache_stamp.copy())
            if tick in (2, 4):
                actions[:, int(tick == 4)] = cache
        correct = np.stack((actions[:, 0] == w.condition, actions[:, 1] == future), axis=1)
        # Both branch weights are decoded from the same fixed receiver context.
        weights = self.context_packet[:, :2].astype(np.int64)
        utility = (correct * weights).sum(axis=1)
        trace = dict(world_ids=w.ids.copy(), legal_features=self.view.features(),
            initial_condition=w.condition.copy(), future_condition=future,
            weight=w.weight.copy(), risk_tenths=w.risk_tenths.copy(), flip_draw=w.flip_draw.copy(),
            early=early.copy(), context_packet=self.context_packet.copy(), data_packet=data_packet,
            context_arrival=self.context_arrival.copy(), data_arrival=arrival_tick,
            sent=sent, delivered=delivered, receiver_cache=np.stack(cache_trace, axis=1),
            cache_timestamp=np.stack(stamp_trace, axis=1), receiver_actions=actions,
            receiver_commitment=np.tile(np.array([0, 0, 0, 1, 1, 1]), (n, 1)),
            correct=correct, utility=utility, packets=sent.sum(axis=(1, 2)),
            bytes=sent[:, :, 0].sum(axis=1) * 7 + sent[:, :, 1].sum(axis=1) * 4,
            timing_slots=np.full(n, 2), timing_choices=np.ones(n, dtype=np.int64))
        return utility, trace
