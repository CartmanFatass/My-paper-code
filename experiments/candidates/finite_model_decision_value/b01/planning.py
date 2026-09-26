"""B01 paired planner adapted from C06 at 3ca4cb1f83ea869e1efca852a099db31c52b0e2c.

Both estimators retain the same NEAR rule and ACTIVE_FIRST continuation. The
sampled or posterior-mean movement law persists through each synthetic future;
these rollouts never read the evaluation world's future.
"""

from dataclasses import replace

import numpy as np

from .host import APPROACH, SHARED, CrossingHost, DONE, FRAME, PERIODS, Worlds


def select_record(record, indices):
    """Keep the observation type without retaining a reference to the host."""
    return replace(record, **{name: getattr(record, name)[indices].copy() for name in (
        "own", "last_sent", "last_sent_time", "peer_packet", "peer_packet_time", "available")})


def independent_model_worlds(record, ids, seed, phase, particles):
    """Address state, law, process and jobs separately from administrative IDs."""
    if particles < 2 or len(ids) != len(record.available):
        raise ValueError("need >=2 particles and one administrative ID per observation")
    if len(set(int(i) for i in ids)) != len(ids):
        raise ValueError("planner IDs must be unique within a batch")
    state_uniforms, theta_uniforms, processes, jobs = [], [], [], []
    for world_id in ids:
        address = (int(seed), int(phase), int(world_id), int(record.t))
        def generator(kind):
            return np.random.default_rng(np.random.SeedSequence([*address, kind]))
        state_uniforms.append(generator(1).random(particles))
        theta_uniforms.append(generator(2).random(particles))
        # Full arrays give each future tick, agent and particle a fixed slot.
        # Branch length and other categories never consume this stream.
        processes.append(generator(3).random((particles, record.horizon, 2)))
        jobs.append(generator(4).integers(
            1, 8, (particles, record.horizon, 2), dtype=np.int16))
    return (np.stack(state_uniforms), np.stack(theta_uniforms),
            np.concatenate(processes), np.concatenate(jobs))


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


def paired_values(record, weights, theta_values, states, ids, *, seed, phase,
                  particles=32, mode, counters=None):
    """Return native completion differences, with fixed future continuation.

    All root observations must be available and unforced. The only varying root
    intervention is HOLD versus SEND; future policies, model and RNG agree.
    """
    if mode not in ("POSTERIOR_MEAN", "JOINT"):
        raise ValueError("unknown model mode")
    if record.agent != record.t % 2 or not np.all(record.available) or record.t % FRAME >= FRAME - 2:
        raise ValueError("rollout requested outside an optional sender opportunity")
    weights = np.asarray(weights, dtype=np.float64)
    states = np.asarray(states, dtype=np.int16)
    theta_values = np.asarray(theta_values, dtype=np.float64)
    if theta_values.ndim == 1:
        theta_values = np.broadcast_to(theta_values, (len(ids), len(theta_values)))
    if (states.shape != (22, 4) or weights.ndim != 3 or
            weights.shape != (len(ids), theta_values.shape[1], len(states)) or
            theta_values.shape[0] != len(ids) or np.any(weights < 0) or
            not np.isfinite(weights).all() or not np.isfinite(theta_values).all() or
            np.any((theta_values < 0) | (theta_values > 1))):
        raise ValueError("invalid joint physical belief")
    np.testing.assert_allclose(weights.sum(axis=(1, 2)), 1., rtol=0, atol=1e-12)
    state_uniforms, theta_uniforms, process, jobs = independent_model_worlds(
        record, ids, seed, phase, particles)
    counters = {} if counters is None else counters
    def count(key, amount):
        counters[key] = counters.get(key, 0) + int(amount)
    count("model_root_decisions", len(ids))
    count("synthetic_advance_draws", len(ids) * particles * record.horizon * 2)
    count("synthetic_job_draws", len(ids) * particles * record.horizon * 2)
    marginal = weights.sum(axis=1)
    cumulative = marginal.cumsum(axis=1)
    cumulative[:, -1] = 1.
    indices = (state_uniforms[..., None] >= cumulative[:, None, :]).sum(axis=-1)
    conditional = np.take_along_axis(weights, indices[:, None, :], axis=2).transpose(0, 2, 1)
    conditional /= np.take_along_axis(marginal, indices, axis=1)[:, :, None]
    conditional_cdf = conditional.cumsum(axis=2)
    conditional_cdf[:, :, -1] = 1.
    theta_indices = (theta_uniforms[..., None] >= conditional_cdf).sum(axis=2)
    selected_theta = np.take_along_axis(theta_values, theta_indices, axis=1)
    mean_theta = (weights.sum(axis=2) * theta_values).sum(axis=1)
    root_theta = selected_theta if mode == "JOINT" else np.broadcast_to(
        mean_theta[:, None], selected_theta.shape)
    advances = process < root_theta.reshape(len(ids) * particles, 1, 1)
    selected = states[indices]
    peer_payloads = np.empty((*selected.shape[:-1], 5), dtype=np.int16)
    peer_payloads[..., :3] = selected[..., :3]
    peer_payloads[..., 3] = PERIODS[1 - record.agent] - record.t % PERIODS[1 - record.agent]
    peer_payloads[..., 4] = selected[..., 3]
    host = model_host(record, peer_payloads, advances, jobs)
    count("model_initialization_worlds", 2 * len(ids) * particles)
    n = len(ids) * particles
    receiver = 1 - record.agent
    receiver_period = PERIODS[receiver]
    long_end = min(record.t + 32, record.horizon)
    opportunity_tick = np.full(n, -1, dtype=np.int16)
    opportunity_kind = np.zeros(n, dtype=np.int8)
    near_end = np.full(n, record.horizon, dtype=np.int16)
    unresolved = np.ones(n, dtype=bool)
    rewards = []

    for tick in range(record.t, long_end):
        physical = host.payloads()
        if tick >= record.t + 1 and unresolved.any():
            # _prepare_tick has already selected a boundary route at this pre-step
            # phase, so a boundary must be recognized before physical equality.
            at_boundary = unresolved & (tick % receiver_period == 0)
            if at_boundary.any():
                opportunity_tick[at_boundary] = tick
                opportunity_kind[at_boundary] = 1
                near_end[at_boundary] = min(
                    receiver_period * (tick // receiver_period + 1), record.horizon)
                unresolved[at_boundary] = False

            comparable = unresolved.copy()
            if comparable.any():
                hold_physical = physical[:n]
                send_physical = physical[n:]
                equal = np.all(hold_physical == send_physical, axis=(1, 2))
                if np.any(comparable & ~equal):
                    first = int(np.flatnonzero(comparable & ~equal)[0])
                    raise RuntimeError(
                        f"paired physical prefixes diverged before opportunity for sample {first}")
                receiver_state = hold_physical[:, receiver]
                at_gate = comparable & (
                    (receiver_state[:, 0] == APPROACH)
                    & (receiver_state[:, 1] == 0)
                    & (receiver_state[:, 4] == SHARED)
                    & (receiver_state[:, 3] >= 2)
                )
                if at_gate.any():
                    opportunity_tick[at_gate] = tick
                    opportunity_kind[at_gate] = 2
                    ends = receiver_period * (tick // receiver_period + 1)
                    near_end[at_gate] = np.minimum(ends, record.horizon)
                    unresolved[at_gate] = False

        if not unresolved.any() and tick >= int(near_end.max()):
            break

        view = host.view()
        if tick == record.t:
            requested = np.concatenate((np.zeros(n, dtype=bool), np.ones(n, dtype=bool)))
        else:
            requested = view.own[:, 0] != DONE
        reward = host.step(requested)
        rewards.append(reward)
        count("model_branch_transitions", 2 * n)

    if unresolved.any() and long_end < record.horizon:
        raise RuntimeError("no receiver opportunity found within the lawful 32-tick bound")
    if np.any(near_end > long_end):
        raise RuntimeError("receiver opportunity commitment extends beyond LONG32")
    reward_steps = np.stack(rewards, axis=1)
    simulated_steps = reward_steps.shape[1]
    hold_steps = reward_steps[:n].reshape(len(ids), particles, simulated_steps)
    send_steps = reward_steps[n:].reshape(len(ids), particles, simulated_steps)
    absolute_ticks = record.t + np.arange(simulated_steps)
    near_mask = absolute_ticks[None, None, :] < near_end.reshape(len(ids), particles, 1)
    near_hold = (hold_steps * near_mask).sum(axis=2)
    near_send = (send_steps * near_mask).sum(axis=2)
    hold_samples = near_hold
    send_samples = near_send
    end = int(near_end.max())
    difference = send_samples - hold_samples
    result = dict(
        hold=hold_samples.mean(axis=1),
        send=send_samples.mean(axis=1),
        delta=difference.mean(axis=1),
        mc_se=difference.std(axis=1, ddof=1) / np.sqrt(particles),
        se=difference.std(axis=1, ddof=1) / np.sqrt(particles),
        sample_delta=difference,
        root_state_index=indices,
        root_theta=root_theta,
        near_hold_samples=near_hold,
        near_send_samples=near_send,
        near_end=near_end.reshape(len(ids), particles),
        opportunity_tick=opportunity_tick.reshape(len(ids), particles),
        opportunity_kind=opportunity_kind.reshape(len(ids), particles),
        particles=particles,
        model_branch_transitions=2 * n * simulated_steps,
        model_initialization_worlds=2 * n,
        synthetic_advance_draws=n * record.horizon * 2,
        synthetic_job_draws=n * record.horizon * 2, end=end)
    return result
