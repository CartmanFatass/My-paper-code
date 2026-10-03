"""Public state, common geometric executor, wire payloads and FIFO ledger.

Actual request ages live only in QueueLedger. Reconstructed model heads have
unknown identity/arrival, never fabricated historical timestamps.
"""
from collections import deque
from dataclasses import dataclass
from itertools import permutations
import struct

import numpy as np

from .contract import (COMMAND_BYTES, CONTROL_PERIOD, HORIZON,
                       LAST_ARRIVAL_TICK, REPORT_BYTES, RESET_BYTES,
                       SERVICE_TICKS, TERMINAL_WEIGHT)


def _integer(value, name, low, high):
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer)) or not low <= value <= high):
        raise ValueError(f"invalid {name}")
    return int(value)


def _array(value, dtype, shape, name):
    original = np.asarray(value)
    if original.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")
    kind = np.dtype(dtype).kind
    if kind in "iu":
        limits = np.iinfo(dtype)
        if original.dtype.kind not in "iu" or np.any(original < limits.min) or np.any(original > limits.max):
            raise ValueError(f"{name} requires representable integers")
    elif kind == "b" and original.dtype.kind != "b":
        raise ValueError(f"{name} requires bool values")
    result = np.asarray(original, dtype=dtype)
    if kind == "f" and not np.all(np.isfinite(result)):
        raise ValueError(f"{name} requires finite values")
    # Immutable bytes backing prevents callers from re-enabling writeability.
    return np.frombuffer(result.tobytes(), dtype=dtype).reshape(shape)


def _rates(value):
    rates = _array(value, np.uint8, (4,), "rate_codes")
    if sorted(rates.tolist()) != [1, 2, 3, 6]:
        raise ValueError("rate_codes must permute [6,3,2,1]")
    return rates


def _pairs(value):
    pairs = _array(value, np.uint8, (3, 2), "pairs")
    if sorted(pairs.ravel().tolist()) != list(range(6)):
        raise ValueError("pairs must partition UAV IDs 0..5")
    return tuple(tuple(int(x) for x in row) for row in pairs)


def validate_slots(slots, pairs):
    slots = _array(slots, np.uint8, (6,), "slots")
    if np.any(slots > 7):
        raise ValueError("slot ID outside 0..7")
    clusters = []
    for pair in _pairs(pairs):
        ids = slots[list(pair)]
        if ids[0] // 2 != ids[1] // 2 or set((ids % 2).tolist()) != {0, 1}:
            raise ValueError("each pair must occupy one cluster's inner/outer slots")
        clusters.append(int(ids[0] // 2))
    if len(set(clusters)) != 3:
        raise ValueError("pair targets must have distinct clusters")
    return slots


@dataclass(frozen=True, eq=False)
class PublicState:
    world: int
    tick: int
    users: np.ndarray
    rate_codes: np.ndarray
    positions: np.ndarray
    ack: np.ndarray
    counts: np.ndarray
    progress: np.ndarray
    active_slots: np.ndarray
    pairs: tuple

    def __post_init__(self):
        object.__setattr__(self, "world", _integer(self.world, "world", 0, 2**63 - 1))
        object.__setattr__(self, "tick", _integer(self.tick, "tick", 0, HORIZON))
        specifications = (("users", np.int32, (50, 2)),
                          ("positions", np.float64, (6, 3)),
                          ("ack", np.bool_, (50,)), ("counts", np.int64, (4,)),
                          ("progress", np.int64, (4,)))
        for name, dtype, shape in specifications:
            object.__setattr__(self, name, _array(getattr(self, name), dtype, shape, name))
        object.__setattr__(self, "rate_codes", _rates(self.rate_codes))
        object.__setattr__(self, "pairs", _pairs(self.pairs))
        object.__setattr__(self, "active_slots", validate_slots(self.active_slots, self.pairs))
        _queue_state(self.counts, self.progress)

    @property
    def probabilities(self):
        return self.rate_codes.astype(np.float64) / 10.0


def _queue_state(counts, progress):
    if (np.any(counts < 0) or np.any(counts > 48) or np.any(progress < 0)
            or np.any(progress >= SERVICE_TICKS) or np.any((counts == 0) & (progress != 0))):
        raise ValueError("invalid queue counts/head progress")


def slot_positions(users, slots=None):
    users = _array(users, np.int32, (50, 2), "users")
    means = users[10:].reshape(4, 10, 2).astype(np.float64).mean(axis=1)
    xy = 2500.0 + (means[:, None, :] - 2500.0) * np.array([1/3, 2/3])[None, :, None]
    targets = np.concatenate((xy, np.full((4, 2, 1), 100.0)), axis=2).reshape(8, 3)
    if slots is None:
        return targets
    ids = np.asarray(slots)
    if ids.dtype.kind not in "iu" or np.any(ids < 0) or np.any(ids > 7):
        raise ValueError("invalid slot IDs")
    return targets[ids]


def initial_assignment(users, rate_codes, positions):
    rates = _rates(rate_codes)
    positions = _array(positions, np.float64, (6, 3), "positions")
    clusters = sorted(sorted(range(4), key=lambda c: (-int(rates[c]), c))[:3])
    slots = np.array([2*c + side for c in clusters for side in range(2)], dtype=np.uint8)
    targets = slot_positions(users, slots)
    distances = np.linalg.norm(positions[:, None, :] - targets[None, :, :], axis=-1)
    def key(order):
        d = distances[np.asarray(order), np.arange(6)]
        return int(np.ceil(d / 30.0).sum()), float(d.sum()), order
    order = min(permutations(range(6)), key=key)
    active = np.empty(6, dtype=np.uint8)
    active[list(order)] = slots
    return active, tuple(tuple(order[i:i+2]) for i in range(0, 6, 2))


def candidate_slots(state):
    """KEEP and one moved pair each, mapped from current reported positions."""
    current = state.active_slots
    occupied = {int(current[pair[0]] // 2) for pair in state.pairs}
    missing = next(iter(set(range(4)) - occupied))
    destination = slot_positions(state.users, np.array([2*missing, 2*missing+1]))
    candidates = np.tile(current, (4, 1))
    for action, pair in enumerate(state.pairs, start=1):
        def key(order):
            d = np.linalg.norm(state.positions[list(order)] - destination, axis=1)
            return int(np.ceil(d / 30.0).max()), float(d.sum()), order
        order = min(permutations(pair), key=key)
        candidates[action, list(order)] = [2*missing, 2*missing+1]
    return candidates


def steer(positions, targets):
    """Original ordinary.steer arithmetic; native actions remain float64."""
    delta = np.asarray(targets, dtype=np.float64) - np.asarray(positions, dtype=np.float64)
    return delta / np.maximum(30.0, np.linalg.norm(delta, axis=-1))[:, None]


def pack_reset(users, rate_codes):
    payload = _array(users, np.int32, (50, 2), "users").astype("<i4").tobytes() + _rates(rate_codes).tobytes()
    assert len(payload) == RESET_BYTES
    return payload


def unpack_reset(payload):
    if len(payload) != RESET_BYTES:
        raise ValueError("reset payload must be 404 bytes")
    return (_array(np.frombuffer(payload[:400], "<i4").reshape(50, 2), np.int32, (50, 2), "users"),
            _rates(np.frombuffer(payload[400:], np.uint8)))


def pack_report(state):
    bits = np.packbits(state.ack, bitorder="little")
    payload = (state.positions.astype("<f8").tobytes() + bits.tobytes()
               + state.counts.astype("<u2").tobytes() + state.progress.astype(np.uint8).tobytes()
               + state.active_slots.tobytes() + struct.pack("<H", state.tick))
    assert len(payload) == REPORT_BYTES
    return payload


def unpack_report(payload, *, world, users, rate_codes, pairs):
    if len(payload) != REPORT_BYTES or payload[150] & 0b11111100:
        raise ValueError("invalid report length or nonzero ACK padding")
    return PublicState(world, struct.unpack("<H", payload[169:171])[0], users, rate_codes,
                       np.frombuffer(payload[:144], "<f8").reshape(6, 3),
                       np.unpackbits(np.frombuffer(payload[144:151], np.uint8), bitorder="little")[:50].astype(bool),
                       np.frombuffer(payload[151:159], "<u2"),
                       np.frombuffer(payload[159:163], np.uint8),
                       np.frombuffer(payload[163:169], np.uint8), pairs)


def pack_command(slots, pairs):
    payload = validate_slots(slots, pairs).tobytes()
    assert len(payload) == COMMAND_BYTES
    return payload


def unpack_command(payload, pairs):
    if len(payload) != COMMAND_BYTES:
        raise ValueError("command must be six bytes")
    return validate_slots(np.frombuffer(payload, np.uint8), pairs)


@dataclass(frozen=True)
class Request:
    request_id: int | None
    cluster: int
    arrival_tick: int | None


@dataclass(frozen=True)
class Completion:
    request: Request
    completion_tick: int


class QueueLedger:
    """Sequential start/finish API prevents double charging or overrun."""
    def __init__(self):
        self._queues = [deque() for _ in range(4)]
        self._progress = np.zeros(4, dtype=np.int64)
        self._tick = 0
        self._started = False
        self._terminal = False
        self._next_id = 0
        self._arrivals = []
        self._completions = []
        self.residence_cost = 0
        self._terminal_charge = 0

    @classmethod
    def from_public(cls, counts, progress, tick):
        """Reconstruct heads only; costs begin at this tick, ages remain unknown."""
        counts = _array(counts, np.int64, (4,), "counts")
        progress = _array(progress, np.int64, (4,), "progress")
        _queue_state(counts, progress)
        result = cls()
        result._tick = _integer(tick, "tick", 0, HORIZON)
        result._queues = [deque(Request(None, c, None) for _ in range(int(n)))
                          for c, n in enumerate(counts)]
        result._progress = progress.copy()
        return result

    @property
    def tick(self):
        return self._tick

    @property
    def area_cost(self):
        return self.residence_cost

    @property
    def terminal_charge(self):
        return self._terminal_charge

    @property
    def total_cost(self):
        return self.residence_cost + self._terminal_charge

    @property
    def counts(self):
        return np.array([len(queue) for queue in self._queues], dtype=np.int64)

    @property
    def progress(self):
        return self._progress.copy()

    @property
    def arrivals(self):
        return tuple(self._arrivals)

    @property
    def completions(self):
        return tuple(self._completions)

    @property
    def unfinished(self):
        return tuple(tuple(queue) for queue in self._queues)

    def start_tick(self, tick, arrivals):
        tick = _integer(tick, "tick", 0, HORIZON - 1)
        bits = _array(arrivals, np.bool_, (4,), "arrivals")
        if tick != self._tick or self._started or self._terminal:
            raise ValueError("tick must start exactly once in sequential order")
        if (tick % CONTROL_PERIOD or tick > LAST_ARRIVAL_TICK) and np.any(bits):
            raise ValueError("arrival outside fixed grid")
        if np.any(self.counts + bits > 48):
            raise ValueError("queue exceeds fixed arrival bound")
        for cluster in np.flatnonzero(bits):
            request = Request(self._next_id, int(cluster), tick)
            self._next_id += 1
            self._queues[cluster].append(request)
            self._arrivals.append(request)
        self._started = True
        cost = int(self.counts.sum())
        self.residence_cost += cost
        return cost

    def finish_tick(self, tick, ack_or_qualified):
        tick = _integer(tick, "tick", 0, HORIZON - 1)
        ack = np.asarray(ack_or_qualified)
        if ack.shape == (50,):
            ack = _array(ack, np.bool_, (50,), "ACK")
            qualified = ack[10:].reshape(4, 10).sum(axis=1) >= 8
        else:
            qualified = _array(ack, np.bool_, (4,), "qualification")
        if tick != self._tick or not self._started:
            raise ValueError("finish requires one started tick")
        completed = []
        for c, queue in enumerate(self._queues):
            if queue and qualified[c]:
                self._progress[c] += 1
                if self._progress[c] == SERVICE_TICKS:
                    completion = Completion(queue.popleft(), tick + 1)
                    self._completions.append(completion)
                    completed.append(completion)
                    self._progress[c] = 0
            else:
                self._progress[c] = 0
        self._started = False
        self._tick += 1
        return tuple(completed)

    def terminal_cost(self):
        if self._tick != HORIZON or self._started or self._terminal:
            raise ValueError("terminal charge requires completed horizon exactly once")
        self._terminal = True
        self._terminal_charge = TERMINAL_WEIGHT * int(self.counts.sum())
        return self._terminal_charge
