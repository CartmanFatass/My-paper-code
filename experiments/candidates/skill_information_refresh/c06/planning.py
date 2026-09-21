"""Paired rollouts constructed only from one sender's lawful physical belief.

The known physical model and ACTIVE_FIRST continuation are common resources for
both planning horizons. These rollouts are not the evaluation world's future.
"""

from dataclasses import replace

import numpy as np

from ..c01.host import CrossingHost, DONE, FRAME, PERIODS, Worlds


def select_record(record, indices):
    """Keep the observation type without retaining a reference to the host."""
    return replace(record, **{name: getattr(record, name)[indices].copy() for name in (
        "own", "last_sent", "last_sent_time", "peer_packet", "peer_packet_time", "available")})


def commitment_end(t, receiver, horizon):
    """End of the receiver commitment containing delivery at t+1.

    Delivery on a boundary belongs to the new commitment. A delivery just before
    that boundary belongs to the old one; this is deliberately a short target.
    """
    return min(((t + 1) // PERIODS[receiver] + 1) * PERIODS[receiver], horizon)


def independent_model_worlds(record, ids, seed, phase, particles):
    """World IDs address planner RNG only; no actual environment array is read."""
    if particles < 2 or len(ids) != len(record.available):
        raise ValueError("need >=2 particles and one administrative ID per observation")
    uniforms, advances, jobs = [], [], []
    for world_id in ids:
        rng = np.random.default_rng(np.random.SeedSequence(
            [int(seed), int(phase), int(world_id), int(record.t), 606]))
        uniforms.append(rng.random(particles))
        advances.append(rng.random((particles, record.horizon, 2)) < .75)
        jobs.append(rng.integers(1, 8, (particles, record.horizon, 2), dtype=np.int16))
    return np.stack(uniforms), np.concatenate(advances), np.concatenate(jobs)


def model_host(record, peer_payloads, advances, jobs):
    """Create both root branches with paired latent states and future noise."""
    batch, particles, width = peer_payloads.shape
    if width != 5 or batch != len(record.available):
        raise ValueError("peer samples must be B x particles x 5")
    if advances.shape != (batch * particles, record.horizon, 2) or jobs.shape != advances.shape:
        raise ValueError("synthetic future arrays have the wrong shape")
    if np.any(record.last_sent_time >= record.t) or np.any(record.peer_packet_time >= record.t):
        raise ValueError("pre-step caches cannot contain a current/future send")
    n = batch * particles
    worlds = Worlds(np.concatenate((advances, advances)), np.concatenate((jobs, jobs)), tuple(range(2 * n)))
    host = CrossingHost(worlds)
    host.t = record.t  # record is already after delivery, quota reset and boundary selection
    own = np.repeat(record.own, particles, axis=0)
    peer = peer_payloads.reshape(n, 5)
    pair = np.empty((n, 2, 5), dtype=np.int16)
    pair[:, record.agent] = own
    pair[:, 1 - record.agent] = peer
    pair = np.concatenate((pair, pair))
    host.stage[:] = pair[..., 0]
    host.distance[:] = pair[..., 1]
    host.cross_left[:] = pair[..., 2]
    host.route[:] = pair[..., 4]

    def copies(value):
        expanded = np.repeat(value, particles, axis=0)
        return np.concatenate((expanded, expanded))

    a, b = record.agent, 1 - record.agent
    host.cache[:, a] = copies(record.peer_packet)
    host.cache_time[:, a] = copies(record.peer_packet_time)
    host.cache[:, b] = copies(record.last_sent)
    host.cache_time[:, b] = copies(record.last_sent_time)
    host.last_sent[:, a] = copies(record.last_sent)
    host.last_sent_time[:, a] = copies(record.last_sent_time)
    host.last_sent[:, b] = copies(record.peer_packet)
    host.last_sent_time[:, b] = copies(record.peer_packet_time)
    host.spent[:, a] = copies(~record.available)
    # Every previous send has arrived before this pre-step record. Quota
    # accounting is exact even though physical filtering ignores silence's
    # state-dependent likelihood.
    host.spent[:, b] = copies(record.peer_packet_time >= (record.t // FRAME) * FRAME)
    host.pending.fill(False)
    host.pending_time.fill(-1)
    for values in host.metrics.values():
        values.fill(0)
    return host


def paired_values(record, weights, states, ids, *, seed, phase, particles, mode, counters=None):
    """Return native completion differences, with fixed future continuation.

    All root observations must be available and unforced. The only varying root
    intervention is HOLD versus SEND; future policies, model and RNG agree.
    """
    if mode not in ("SHORT", "LONG"):
        raise ValueError("unknown value horizon")
    if record.agent != record.t % 2 or not np.all(record.available) or record.t % FRAME >= FRAME - 2:
        raise ValueError("rollout requested outside an optional sender opportunity")
    weights = np.asarray(weights, dtype=np.float64)
    states = np.asarray(states, dtype=np.int16)
    if weights.shape != (len(ids), len(states)) or np.any(weights < 0) or not np.isfinite(weights).all():
        raise ValueError("invalid physical belief")
    np.testing.assert_allclose(weights.sum(axis=1), 1., rtol=0, atol=1e-12)
    uniforms, advances, jobs = independent_model_worlds(record, ids, seed, phase, particles)
    counters = {} if counters is None else counters
    def count(key, amount):
        counters[key] = counters.get(key, 0) + int(amount)
    count("model_root_decisions", len(ids))
    count("synthetic_advance_draws", len(ids) * particles * record.horizon * 2)
    count("synthetic_job_draws", len(ids) * particles * record.horizon * 2)
    cumulative = weights.cumsum(axis=1)
    cumulative[:, -1] = 1.
    indices = (uniforms[..., None] >= cumulative[:, None, :]).sum(axis=-1)
    selected = states[indices]
    peer_payloads = np.empty((*selected.shape[:-1], 5), dtype=np.int16)
    peer_payloads[..., :3] = selected[..., :3]
    peer_payloads[..., 3] = PERIODS[1 - record.agent] - record.t % PERIODS[1 - record.agent]
    peer_payloads[..., 4] = selected[..., 3]
    host = model_host(record, peer_payloads, advances, jobs)
    count("model_initialization_worlds", 2 * len(ids) * particles)
    end = min(record.t + 32, record.horizon) if mode == "LONG" else commitment_end(
        record.t, 1 - record.agent, record.horizon)
    n = len(ids) * particles
    total = np.zeros(2 * n, dtype=np.float64)
    for tick in range(record.t, end):
        if tick == record.t:
            requested = np.concatenate((np.zeros(n, dtype=bool), np.ones(n, dtype=bool)))
        else:
            requested = host.view().own[:, 0] != DONE
        total += host.step(requested)
        count("model_branch_transitions", 2 * n)
    hold, send = total[:n].reshape(-1, particles), total[n:].reshape(-1, particles)
    difference = send - hold
    return dict(hold=hold.mean(axis=1), send=send.mean(axis=1),
        delta=difference.mean(axis=1), se=difference.std(axis=1, ddof=1) / np.sqrt(particles),
        particles=particles, model_branch_transitions=2 * n * (end - record.t),
        model_initialization_worlds=2 * n, synthetic_advance_draws=n * record.horizon * 2,
        synthetic_job_draws=n * record.horizon * 2, end=end)
