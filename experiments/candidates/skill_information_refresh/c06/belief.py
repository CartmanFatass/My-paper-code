"""Lawful local observations and a finite physical belief for C06.

The filter is deliberately only an approximate physical belief: it propagates the
exact known CrossingHost physics and conditions on delivered packets and observed own
motion, but it does not use the likelihood of state-dependent peer send timing or
silence.  It is therefore neither an exact Bayesian posterior nor an optimality claim.
"""

from dataclasses import dataclass

import numpy as np

from experiments.candidates.skill_information_refresh.c01.host import (
    APPROACH,
    BYPASS,
    CROSSING,
    DONE,
    PERIODS,
    SHARED,
    choose_route,
    gate,
    project,
)


_STATE_TUPLES = tuple(
    [(APPROACH, distance, 0, route) for distance in range(8) for route in (SHARED, BYPASS)]
    + [(CROSSING, 0, 1, SHARED)]
    + [(CROSSING, 0, left, BYPASS) for left in range(1, 4)]
    + [(DONE, 0, 0, route) for route in (SHARED, BYPASS)]
)
STATE_SUPPORT = np.asarray(_STATE_TUPLES, dtype=np.int16)
STATE_SUPPORT.setflags(write=False)
_STATE_INDEX = {state: index for index, state in enumerate(_STATE_TUPLES)}


class BeliefContradiction(RuntimeError):
    """A lawful observation has zero probability under the current physical belief."""


def _immutable_array(value, shape, dtype, name):
    array = np.asarray(value)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    copy = np.array(array, dtype=dtype, copy=True)
    copy.setflags(write=False)
    return copy


@dataclass(frozen=True)
class LocalRecord:
    """Copied pre-action information available locally to one physical agent."""

    t: int
    horizon: int
    agent: int
    own: np.ndarray
    last_sent: np.ndarray
    last_sent_time: np.ndarray
    peer_packet: np.ndarray
    peer_packet_time: np.ndarray
    available: np.ndarray

    def __post_init__(self):
        t, horizon, agent = int(self.t), int(self.horizon), int(self.agent)
        if horizon <= 0 or not 0 <= t < horizon:
            raise ValueError("record time must be a nonterminal tick inside the horizon")
        if agent not in (0, 1):
            raise ValueError("agent must be 0 or 1")
        own = np.asarray(self.own)
        if own.ndim != 2 or own.shape[1] != 5:
            raise ValueError("own must have shape [B, 5]")
        batch = own.shape[0]
        object.__setattr__(self, "t", t)
        object.__setattr__(self, "horizon", horizon)
        object.__setattr__(self, "agent", agent)
        object.__setattr__(self, "own", _immutable_array(own, (batch, 5), np.int16, "own"))
        object.__setattr__(self, "last_sent",
            _immutable_array(self.last_sent, (batch, 5), np.int16, "last_sent"))
        object.__setattr__(self, "last_sent_time",
            _immutable_array(self.last_sent_time, (batch,), np.int64, "last_sent_time"))
        object.__setattr__(self, "peer_packet",
            _immutable_array(self.peer_packet, (batch, 5), np.int16, "peer_packet"))
        object.__setattr__(self, "peer_packet_time",
            _immutable_array(self.peer_packet_time, (batch,), np.int64, "peer_packet_time"))
        object.__setattr__(self, "available",
            _immutable_array(self.available, (batch,), bool, "available"))

    @property
    def batch(self):
        return self.own.shape[0]


def take_local(host, agent):
    """Copy the sole C06 observation boundary without reading peer physics or worlds."""
    agent = int(agent)
    if agent not in (0, 1):
        raise ValueError("agent must be 0 or 1")
    if host.t >= host.horizon:
        raise RuntimeError("no local observation after terminal time")
    batch = int(host.batch)
    remaining = PERIODS[agent] - host.t % PERIODS[agent]
    own = np.column_stack((
        host.stage[:, agent],
        host.distance[:, agent],
        host.cross_left[:, agent],
        np.full(batch, remaining, dtype=np.int16),
        host.route[:, agent],
    ))
    return LocalRecord(
        t=host.t,
        horizon=host.horizon,
        agent=agent,
        own=own,
        last_sent=host.last_sent[:, agent],
        last_sent_time=host.last_sent_time[:, agent],
        peer_packet=host.cache[:, agent],
        peer_packet_time=host.cache_time[:, agent],
        available=~host.spent[:, agent],
    )


def _payload(state, remaining):
    stage, distance, cross_left, route = state
    return np.asarray([[stage, distance, cross_left, remaining, route]], dtype=np.int16)


def _physical(payload):
    return (int(payload[0]), int(payload[1]), int(payload[2]), int(payload[4]))


def _advance_pair(own_state, peer_state, own_gate, peer_gate, own_advance, peer_advance):
    """Apply the C01 post-gate physics to one own/peer state pair."""
    stages = [own_state[0], peer_state[0]]
    distances = [own_state[1], peer_state[1]]
    cross_left = [own_state[2], peer_state[2]]
    routes = [own_state[3], peer_state[3]]
    advances = (own_advance, peer_advance)
    decisions = (own_gate, peer_gate)

    for index in range(2):
        if stages[index] == APPROACH and distances[index] > 0 and advances[index]:
            distances[index] -= 1
    for index in range(2):
        if decisions[index]:
            stages[index] = CROSSING
            cross_left[index] = 4 if routes[index] == BYPASS else 2

    if (stages[0] == CROSSING and routes[0] == SHARED
            and stages[1] == CROSSING and routes[1] == SHARED):
        stages[:] = [DONE, DONE]
        cross_left[:] = [0, 0]

    for index in range(2):
        if stages[index] == CROSSING:
            cross_left[index] -= 1
            if cross_left[index] == 0:
                stages[index] = DONE
        if stages[index] == DONE:
            distances[index] = 0
    return (
        (stages[0], distances[0], cross_left[0], routes[0]),
        (stages[1], distances[1], cross_left[1], routes[1]),
    )


class PhysicalBelief:
    """Finite approximate belief over one hidden peer's physical state."""

    states = STATE_SUPPORT

    def __init__(self, record):
        if not isinstance(record, LocalRecord):
            raise TypeError("record must be a LocalRecord")
        if record.t != 0:
            raise ValueError("the first local record must be taken at t=0")
        self.record = record
        self.weights = np.zeros((record.batch, len(self.states)), dtype=np.float64)
        for distance in range(1, 8):
            self.weights[:, _STATE_INDEX[(APPROACH, distance, 0, SHARED)]] = 1 / 7
        self._stats = {"observations": 1, "packet_updates": 0, "contradictions": 0}
        self._validate_clock(record)

    @property
    def stats(self):
        return {name: int(value) for name, value in self._stats.items()}

    @property
    def counts(self):
        return self.stats

    def _contradiction(self, rows, message):
        self._stats["contradictions"] += int(rows)
        raise BeliefContradiction(message)

    def _validate_clock(self, record):
        expected = PERIODS[record.agent] - record.t % PERIODS[record.agent]
        bad = np.count_nonzero(record.own[:, 3] != expected)
        if bad:
            self._contradiction(bad, "own remaining commitment disagrees with the public clock")

    def _condition_packet(self, weights, new_record):
        previous = self.record
        changed = new_record.peer_packet_time != previous.peer_packet_time
        unchanged_content = np.all(new_record.peer_packet == previous.peer_packet, axis=1)
        bad_static = (~changed) & ~unchanged_content
        if bad_static.any():
            self._contradiction(bad_static.sum(), "peer packet changed without a new timestamp")
        bad_time = changed & (new_record.peer_packet_time != previous.t)
        if bad_time.any():
            self._contradiction(bad_time.sum(), "a new peer packet must have timestamp t-1")

        peer = 1 - previous.agent
        expected_remaining = PERIODS[peer] - previous.t % PERIODS[peer]
        for row in np.flatnonzero(changed):
            packet = new_record.peer_packet[row]
            state = _physical(packet)
            index = _STATE_INDEX.get(state)
            if packet[3] != expected_remaining or index is None or weights[row, index] <= 0:
                self._contradiction(1,
                    f"delivered peer packet has zero compatible support in row {row}")
            weights[row].fill(0)
            weights[row, index] = 1
        return int(changed.sum())

    def _validate_own_send_history(self, new_record):
        previous = self.record
        changed = new_record.last_sent_time != previous.last_sent_time
        same_payload = np.all(new_record.last_sent == previous.last_sent, axis=1)
        bad_static = (~changed) & ~same_payload
        bad_new = changed & ((new_record.last_sent_time != previous.t)
            | ~np.all(new_record.last_sent == previous.own, axis=1))
        bad = bad_static | bad_new
        if bad.any():
            self._contradiction(bad.sum(), "own sent history is inconsistent with the last pre-action record")

    def update(self, new_record):
        """Assimilate one next-tick local record and propagate exact C01 physics."""
        if not isinstance(new_record, LocalRecord):
            raise TypeError("new_record must be a LocalRecord")
        previous = self.record
        if (new_record.agent != previous.agent or new_record.horizon != previous.horizon
                or new_record.batch != previous.batch):
            raise ValueError("record identity, horizon and batch must remain fixed")
        if new_record.t != previous.t + 1:
            raise ValueError("PhysicalBelief requires a record for every consecutive tick")
        self._validate_clock(new_record)
        self._validate_own_send_history(new_record)

        conditioned = self.weights.copy()
        packet_updates = self._condition_packet(conditioned, new_record)
        predicted = np.zeros_like(conditioned)
        tprev = previous.t
        agent = previous.agent
        peer = 1 - agent
        own_boundary = new_record.t % PERIODS[agent] == 0
        peer_boundary = new_record.t % PERIODS[peer] == 0
        outcome_values = ((False, .25), (True, .75))

        for row in range(previous.batch):
            own_state = _physical(previous.own[row])
            own_packet = previous.own[row:row + 1]
            peer_cache, peer_valid, _ = project(
                previous.peer_packet[row:row + 1],
                previous.peer_packet_time[row:row + 1], tprev)
            own_gate = bool(gate(own_packet, peer_cache, peer_valid,
                np.asarray([agent]))[0])

            receiver_cache, receiver_valid, _ = project(
                previous.last_sent[row:row + 1],
                previous.last_sent_time[row:row + 1], tprev)
            if peer_boundary:
                reset_cache, reset_valid, _ = project(
                    new_record.last_sent[row:row + 1],
                    new_record.last_sent_time[row:row + 1], new_record.t)
                distances = np.arange(1, 8, dtype=np.int16)
                reset_routes = choose_route(distances, PERIODS[peer], reset_cache, reset_valid)
                reset_indices = [
                    _STATE_INDEX[(APPROACH, int(distance), 0, int(route))]
                    for distance, route in zip(distances, reset_routes)
                ]

            for index, prior_mass in enumerate(conditioned[row]):
                if prior_mass <= 0:
                    continue
                peer_state = _STATE_TUPLES[index]
                peer_packet = _payload(peer_state, PERIODS[peer] - tprev % PERIODS[peer])
                peer_gate = bool(gate(peer_packet, receiver_cache, receiver_valid,
                    np.asarray([peer]))[0])
                for own_advance, own_probability in outcome_values:
                    for peer_advance, peer_probability in outcome_values:
                        next_own, next_peer = _advance_pair(
                            own_state, peer_state, own_gate, peer_gate,
                            own_advance, peer_advance)
                        mass = prior_mass * own_probability * peer_probability
                        if not own_boundary and next_own != _physical(new_record.own[row]):
                            continue
                        if peer_boundary:
                            for reset_index in reset_indices:
                                predicted[row, reset_index] += mass / 7
                        else:
                            predicted[row, _STATE_INDEX[next_peer]] += mass

        totals = predicted.sum(axis=1)
        zero = totals <= 0
        if zero.any():
            self._contradiction(zero.sum(), "new own observation has zero physical likelihood")
        predicted /= totals[:, None]
        self.weights = predicted
        self.record = new_record
        self._stats["observations"] += 1
        self._stats["packet_updates"] += packet_updates
        return self

    def sample_payloads(self, uniforms):
        """Sample peer payloads from caller-supplied U[0,1) values of shape [B,P]."""
        uniforms = np.asarray(uniforms, dtype=np.float64)
        if uniforms.ndim != 2 or uniforms.shape[0] != self.record.batch:
            raise ValueError("uniforms must have shape [B, P]")
        if not np.isfinite(uniforms).all() or (uniforms < 0).any() or (uniforms >= 1).any():
            raise ValueError("uniforms must be finite values in [0, 1)")
        cdf = np.cumsum(self.weights, axis=1)
        cdf[:, -1] = 1
        indices = (uniforms[:, :, None] >= cdf[:, None, :]).sum(axis=2)
        sampled = self.states[indices]
        payloads = np.empty((*indices.shape, 5), dtype=np.int16)
        payloads[..., 0:3] = sampled[..., 0:3]
        peer = 1 - self.record.agent
        payloads[..., 3] = PERIODS[peer] - self.record.t % PERIODS[peer]
        payloads[..., 4] = sampled[..., 3]
        return payloads

    def sample(self, source, particles=None):
        """Return sampled payloads and [B,K] counts from an RNG or uniform array."""
        if hasattr(source, "random"):
            if particles is None or int(particles) <= 0:
                raise ValueError("a positive particle count is required with an RNG")
            uniforms = source.random((self.record.batch, int(particles)))
        else:
            if particles is not None:
                raise ValueError("particles is only used with an RNG")
            uniforms = np.asarray(source, dtype=np.float64)
        payloads = self.sample_payloads(uniforms)
        sampled_states = payloads[..., (0, 1, 2, 4)]
        indices = np.empty(sampled_states.shape[:2], dtype=np.int64)
        for row in range(indices.shape[0]):
            for particle in range(indices.shape[1]):
                indices[row, particle] = _STATE_INDEX[tuple(
                    int(value) for value in sampled_states[row, particle])]
        counts = np.zeros_like(self.weights, dtype=np.int64)
        rows = np.repeat(np.arange(self.record.batch), indices.shape[1])
        np.add.at(counts, (rows, indices.ravel()), 1)
        return payloads, counts
