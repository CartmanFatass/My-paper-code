"""Saved-state reconstruction of B03; no environment or optimizer replay.

World, radio, greedy association, BFS, information fields, motion, ordinary
programmes and the payment ledger are written separately from the worker.
Neural inference deliberately reuses the SHA-bound native model factory/core;
this checks its recorded inputs, recurrent history and outputs, not an
independent implementation of the transformer/GRU/PPO algorithms.
"""
from __future__ import annotations

from collections import deque
import hashlib
import itertools
import json
import math
from pathlib import Path
import resource
import time

import numpy as np

from . import contract as c


def same(actual, expected, label, atol=0.0, rtol=0.0):
    a, b = np.asarray(actual), np.asarray(expected)
    if a.shape != b.shape:
        raise AssertionError(f'{label}: shape {a.shape} != {b.shape}')
    if a.dtype.kind in 'fc' and not np.isfinite(a).all():
        raise AssertionError(f'{label}: nonfinite actual')
    if b.dtype.kind in 'fc' and not np.isfinite(b).all():
        raise AssertionError(f'{label}: nonfinite expected')
    ok = np.allclose(a, b, atol=atol, rtol=rtol) if atol or rtol else np.array_equal(a, b)
    error = float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.size else 0.0
    if not ok:
        raise AssertionError(f'{label}: maximum absolute error {error}')
    return error


def registry(world):
    """Pure reconstruction of the fixed addresses; no rejection or radio call."""
    random_state = np.random.RandomState(int(world))
    positions = np.asarray([[random_state.uniform(0, 5000), random_state.uniform(0, 5000),
                             random_state.uniform(50, 150)] for _ in range(6)])
    jitter = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world), 1])))
    far = np.asarray(((500, 500), (4500, 500), (4500, 4500), (500, 4500)), dtype=float)
    far += jitter.uniform(-50, 50, size=(4, 2))
    centers = np.concatenate((np.asarray([[2500., 2500.]]), far))
    disks = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world), 2])))
    users = []
    for center in centers:
        for _ in range(10):
            u, v = disks.uniform(0, 1, 2)
            angle = 2 * np.pi * v
            users.append(np.rint(center + 100 * np.sqrt(u) * np.asarray((np.cos(angle), np.sin(angle)))))
    users = np.asarray(users, dtype='<i4')
    order_rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world), 3])))
    order = order_rng.permutation(4).astype(np.uint8)
    packet = np.frombuffer(users.tobytes(order='C') + order.tobytes(), dtype=np.uint8).copy()
    return positions, users, order, packet


def routing(adjacency, bs_links):
    """Original ascending-ID BFS, including its three intermediate UAV limit."""
    paths = np.full((6, 7), -1, dtype=np.int16)
    lengths = np.zeros(6, dtype=np.int16)
    for start in range(6):
        queue, visited = deque([(start, [])]), {start}
        while queue:
            current, prefix = queue.popleft()
            if bs_links[current, 0]:
                path = prefix + [current, 6]
                paths[start, :len(path)] = path
                lengths[start] = len(path)
                break
            if len(prefix) >= 3:
                continue
            for other in range(6):
                if adjacency[current, other] and other not in visited:
                    visited.add(other)
                    queue.append((other, prefix + [current]))
    return paths, lengths


def physical_state(positions, users):
    """Free-space FDMA algebra, followed by the original greedy link order."""
    xyz = np.asarray(positions, dtype=np.float64)
    users = np.asarray(users, dtype=np.float64)
    user_delta = xyz[:, None, :2] - users[None]
    user_distance = np.sqrt(np.sum(user_delta ** 2, axis=-1) + xyz[:, None, 2] ** 2)
    peer_distance = np.sqrt(np.sum((xyz[:, None] - xyz[None]) ** 2, axis=-1))
    bs_distance = np.sqrt(np.sum((xyz - np.asarray((2500., 2500., 30.))) ** 2, axis=-1))[:, None]
    constant = 20 * np.log10(4 * np.pi / (3e8 / 2e9))
    def snr(distance):
        return 103. - (20 * np.log10(np.maximum(distance, 1e-6)) + constant)
    user_sinr, peer_sinr, bs_sinr = snr(user_distance), snr(peer_distance), snr(bs_distance)
    # Native vectorized peer path loss is set to zero on the diagonal.
    np.fill_diagonal(peer_sinr, 103.)
    connections = np.zeros((6, 50), dtype=bool)
    counts = np.zeros(6, dtype=int)
    assigned = np.zeros(50, dtype=bool)
    eligible = np.flatnonzero(user_sinr.reshape(-1) >= 3.)
    order = eligible[np.argsort(-user_sinr.reshape(-1)[eligible], kind='stable')]
    for flat in order:
        agent, user = divmod(int(flat), 50)
        if counts[agent] < 10 and not assigned[user]:
            counts[agent] += 1
            assigned[user] = True
            connections[agent, user] = True
    adjacency = (peer_sinr >= 3.) & (peer_sinr.T >= 3.)
    np.fill_diagonal(adjacency, False)
    bs_links = bs_sinr >= 3.
    paths, lengths = routing(adjacency, bs_links)
    return {'positions': xyz, 'connections': connections, 'user_sinr': user_sinr,
            'uav_sinr': peer_sinr, 'uav_connections': adjacency, 'bs_connections': bs_links,
            'routes': paths, 'route_lengths': lengths, 'transmitter_mask': np.ones(6, dtype=bool)}


def information(positions, users, order, tick, physical):
    """Rebuild the original float32 observation and count-state arithmetic."""
    task = np.zeros(21, dtype=np.float32)
    for window, cluster in enumerate(order):
        task[4 * window + int(cluster)] = 1
    if tick < 500:
        task[16 + int(order[tick // 125])] = 1
        task[20] = (125 - tick % 125) / 125
    xyz = np.asarray(positions, dtype=np.float64)
    users64 = np.asarray(users, dtype=np.float64)
    rows = np.zeros((6, 211), dtype=np.float32)
    for agent in range(6):
        own = xyz[agent]
        base = np.zeros(90, dtype=np.float64)
        base[:3] = own / 5000
        base[2] = (own[2] - 50) / 100
        eligible = np.flatnonzero(physical['user_sinr'][agent] >= 3.)
        ids = eligible[np.argsort(-physical['user_sinr'][agent, eligible], kind='stable')][:20]
        user_rows = base[3:63].reshape(20, 3)
        user_rows[:len(ids), :2] = (users64[ids] - own[:2]) / 5000
        user_rows[:len(ids), 2] = np.clip((physical['user_sinr'][agent, ids] + 10) / 50, 0, 1)
        eligible = np.flatnonzero(physical['uav_sinr'][agent] >= 3.)
        eligible = eligible[eligible != agent]
        ids = eligible[np.argsort(-physical['uav_sinr'][agent, eligible], kind='stable')][:6]
        peer_rows = base[63:87].reshape(6, 4)
        peer_rows[:len(ids), :2] = (xyz[ids, :2] - own[:2]) / 5000
        peer_rows[:len(ids), 2] = (xyz[ids, 2] - own[2]) / 100
        peer_rows[:len(ids), 3] = np.clip((physical['uav_sinr'][agent, ids] + 10) / 50, 0, 1)
        base[87] = tick / 500
        base[88] = physical['bs_connections'][agent, 0]
        length = int(physical['route_lengths'][agent])
        base[89] = min(length / 3, 1.) if length else 1.
        rows[agent, :90] = base
    rows[:, 90:190] = np.asarray(users, dtype=np.float32).reshape(100) / 5000
    rows[:, 190:] = task
    state = np.zeros(154, dtype=np.float32)
    # The native count adapter converts metres to float32 before normalization.
    position32 = xyz.astype(np.float32)
    padded = state[:24].reshape(8, 3)
    padded[:6, :2] = position32[:, :2] / 5000
    padded[:6, 2] = (position32[:, 2] - 50) / 100
    state[24:30] = 1
    state[32:132] = np.asarray(users, dtype=np.float32).reshape(100) / 5000
    state[132] = tick / 500
    state[133:] = task
    return rows, state


def clipped_actions(raw):
    """Preserve the sampled float32 / ordinary float64 host arithmetic."""
    actions = np.array(raw, copy=True)
    if actions.shape[-2:] != (6, 3) or not np.issubdtype(actions.dtype, np.floating):
        raise ValueError('six floating raw commands required')
    event_shape = actions.shape[:-2]
    flat = actions.reshape(-1, 3)
    events = np.zeros(len(flat), dtype=bool)
    for index, command in enumerate(flat):
        # The host copies each three-vector. A row view can have different
        # alignment and round its BLAS norm across the exact >1 branch.
        command = command.copy()
        norm = float(np.linalg.norm(command))
        if not np.isfinite(norm):
            raise ValueError('nonfinite raw action')
        if norm > 1:
            flat[index] = command / norm
            events[index] = norm > 1 + 1e-9
    return actions, events.reshape(*event_shape, 6).sum(axis=-1)


def motion(positions, raw):
    executed, events = clipped_actions(raw)
    # Native velocity multiplication occurs before adding to float64 positions.
    proposed = np.asarray(positions, dtype=np.float64) + (executed * 30) * 1.
    following = np.clip(proposed, (0, 0, 50), (5000, 5000, 150))
    return executed, following, events


def ledger(connections, lengths, order):
    """One payment update for each complete successor, never at reset."""
    con = np.asarray(connections)
    lengths = np.asarray(lengths)
    if con.shape != (500, 6, 50) or con.dtype != np.bool_ or lengths.shape != (500, 6):
        raise ValueError('full500 post-routing states required')
    routed = np.any(con & (lengths > 0)[:, :, None], axis=1)
    associated = np.any(con, axis=1)
    count = np.zeros(500, dtype=np.int16)
    runs = np.zeros(500, dtype=np.int16)
    paid = np.zeros((500, 4), dtype=bool)
    payment = np.zeros(500, dtype=np.float64)
    run, already = 0, np.zeros(4, dtype=bool)
    for tick in range(500):
        window = tick // 125
        if tick % 125 == 0:
            run = 0
        first = 10 + 10 * int(order[window])
        count[tick] = routed[tick, first:first + 10].sum()
        run = run + 1 if count[tick] >= 8 else 0
        runs[tick] = run
        if run >= 20 and not already[window]:
            payment[tick] = 1.
            already[window] = True
        paid[tick] = already
    return {'routed_user_mask': routed, 'associated_user_mask': associated,
            'window': np.arange(500, dtype=np.int16) // 125,
            'active_cluster': np.asarray(order)[np.arange(500) // 125],
            'active_count': count, 'run_length': runs, 'paid': paid,
            'payment': payment, 'external_scalar': payment / 6}


def dense_values(connections, lengths, user_sinr):
    routed = np.asarray(lengths) > 0
    coverage = np.sum(np.asarray(connections) & routed[:, None]) / 50
    capacity = 0.
    for agent in range(6):
        users = np.flatnonzero(connections[agent])
        if routed[agent] and len(users):
            capacity += 20e6 * np.log2(1 + 10 ** (float(np.min(user_sinr[agent, users])) / 10))
    throughput = capacity / (6 * 20e6 * math.log2(1001))
    return {'coverage_backhauled': float(coverage), 'throughput_term': float(throughput),
            'frontend_capacity_with_path_mbps': float(capacity / 1e6),
            'dense_reward': float(.5 * (coverage + throughput))}


def zero_runs(served):
    mask = np.asarray(served, dtype=bool)
    edges = np.diff(np.r_[True, mask, True].astype(np.int8))
    return [{'start': int(start), 'stop': int(stop), 'length': int(stop - start),
             'left_censored': bool(start == 0), 'right_censored': bool(stop == len(mask))}
            for start, stop in zip(np.flatnonzero(edges == -1), np.flatnonzero(edges == 1))]


def mission_metrics(raw, checked_ledger=None):
    facts = checked_ledger or ledger(raw['connections'][1:], raw['route_lengths'][1:], raw['schedule'])
    served = facts['routed_user_mask']
    user_rows = []
    for user in range(50):
        gaps = zero_runs(served[:, user])
        user_rows.append({'user': user, 'served_ticks': int(served[:, user].sum()),
                          'longest_gap': max((g['length'] for g in gaps), default=0),
                          'leading_gap': gaps[0]['length'] if gaps and gaps[0]['left_censored'] else 0,
                          'trailing_gap': gaps[-1]['length'] if gaps and gaps[-1]['right_censored'] else 0,
                          'gaps': gaps})
    longest = np.asarray([row['longest_gap'] for row in user_rows])
    individual_ticks = served.sum(axis=0)
    positions = raw['positions']
    delta = positions[1:] - positions[:-1]
    paths = np.linalg.norm(delta, axis=-1).sum(axis=0)
    team_counts = served.sum(axis=1)
    per_window = []
    for j in range(4):
        selection = slice(j * 125, (j + 1) * 125)
        hits = np.flatnonzero(facts['payment'][selection])
        per_window.append({'window': j, 'cluster': int(raw['schedule'][j]), 'completed': bool(len(hits)),
                           'completion_action': j * 125 + int(hits[0]) if len(hits) else None,
                           'completion_post_tick': j * 125 + int(hits[0]) + 1 if len(hits) else None,
                           'max_consecutive_qualified_ticks': int(facts['run_length'][selection].max()),
                           'qualified_ticks': int((facts['active_count'][selection] >= 8).sum()),
                           'max_active_users': int(facts['active_count'][selection].max()),
                           'active_user_ticks': int(facts['active_count'][selection].sum())})
    owners = np.where(raw['connections'].any(axis=1), raw['connections'].argmax(axis=1), -1)
    return {'W': int(facts['payment'].sum()), 'window_fraction': float(facts['payment'].sum() / 4),
            'J_dense': float(np.mean(raw['dense_reward'])),
            'coverage_backhauled': float(served.mean()), 'coverage_access': float(facts['associated_user_mask'].mean()),
            'frontend_capacity_with_path_mbps': float(np.mean(raw['frontend_capacity_with_path_mbps'])),
            'throughput_term': float(np.mean(raw['throughput_term'])),
            'team_zero_ticks': int((team_counts == 0).sum()),
            'longest_team_zero_run': max((x['length'] for x in zero_runs(team_counts > 0)), default=0),
            'first10_team_zero_ticks': int((team_counts[:10] == 0).sum()),
            'min_served_users': int(team_counts.min()), 'p10_served_users': float(np.quantile(team_counts, .1)),
            'never_served_users': int((individual_ticks == 0).sum()),
            'mean_user_longest_gap': float(longest.mean()), 'p90_user_longest_gap': float(np.quantile(longest, .9)),
            'max_user_longest_gap': int(longest.max()), 'min_user_served_ticks': int(individual_ticks.min()),
            'p10_user_served_ticks': float(np.quantile(individual_ticks, .1)),
            'mean_path_length_m': float(paths.mean()), 'total_path_length_m': float(paths.sum()),
            'xy_boundary_uav_ticks': int(np.any((positions[1:, :, :2] == 0) | (positions[1:, :, :2] == 5000), axis=-1).sum()),
            'altitude_boundary_uav_ticks': int(((positions[1:, :, 2] == 50) | (positions[1:, :, 2] == 150)).sum()),
            'zero_displacement_uav_ticks': int(np.all(delta == 0, axis=-1).sum()),
            'action_clip_events': int(np.sum(raw['action_clip_events'])),
            'user_association_changes': int(np.count_nonzero(owners[1:] != owners[:-1])),
            'route_changes': int(np.any(raw['routes'][1:] != raw['routes'][:-1], axis=-1).sum()),
            'window_details': per_window, 'user_details': user_rows, 'path_length_by_uav_m': paths.tolist()}


def _slots(users, clusters):
    points = []
    for cluster in clusters:
        center = np.mean(users[10 + 10 * int(cluster):20 + 10 * int(cluster)], axis=0)
        for ratio in (1 / 3, 2 / 3):
            xy = np.asarray((2500., 2500.)) + ratio * (center - np.asarray((2500., 2500.)))
            points.append((xy[0], xy[1], 100.))
    return np.asarray(points)


def decoded_pose(normalized):
    pose = np.asarray(normalized, dtype=np.float64).copy()
    pose[..., :2] *= 5000
    pose[..., 2] = 50 + 100 * pose[..., 2]
    return pose


def ordinary_commands(raw, programme, world):
    """Reconstruct every command on actual history; no counterfactual rollout."""
    positions, users, order = raw['positions'], raw['users'], raw['schedule']
    output = np.zeros((500, 6, 3), dtype=np.float64)
    details = {}
    current_pose = decoded_pose(raw['observations'][:500, :, :3])
    if programme == 'O':
        slots = _slots(users, order[:3])
        held_pose = decoded_pose(raw['states'][0, :18].reshape(6, 3))
        distance = np.linalg.norm(held_pose[:, None, :] - slots[None], axis=-1)
        arrival = np.ceil(distance / 30).astype(int)
        best = None
        for assignment in itertools.permutations(range(6)):
            times = np.asarray([arrival[assignment[j], j] for j in range(6)])
            pair_time = np.max(times.reshape(3, 2), axis=1)
            key = (*np.maximum(0, pair_time - np.asarray((105, 230, 355))).tolist(),
                   int(pair_time.max()), int(times.sum()), assignment)
            if best is None or key < best[0]:
                best = key, assignment
        assignment = best[1]
        targets = np.empty((6, 3), dtype=np.float64)
        targets[np.asarray(assignment)] = slots
        details.update(initial_assignment=list(assignment), initial_key=list(best[0][:-1]),
                       initial_slots=slots.tolist(), initial_arrival_steps=arrival[np.asarray(assignment), np.arange(6)].tolist(),
                       assignment_comparisons=722, distance_evaluations=40)
    elif programme == 'B':
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world), 4])))
        def draw():
            return np.asarray((rng.uniform(0, 5000), rng.uniform(0, 5000), rng.uniform(50, 150)))
        targets = np.asarray([draw() for _ in range(6)])
        details.update(replacements=0, uniform_draws=18)
    else:
        raise ValueError('only declared O/B programmes')
    for tick in range(500):
        if programme == 'O' and tick == 130:
            ids = assignment[:2]
            slots = _slots(users, order[3:4])
            held_pose = decoded_pose(raw['states'][tick, :18].reshape(6, 3))
            distance = np.linalg.norm(held_pose[np.asarray(ids), None, :] - slots[None], axis=-1)
            choices = []
            for perm in (ids, ids[::-1]):
                ds = np.asarray([distance[ids.index(perm[j]), j] for j in range(2)])
                choices.append(((int(np.ceil(ds / 30).max()), float(ds.sum()), perm), perm))
            chosen = min(choices)[1]
            targets[np.asarray(chosen)] = slots
            details['reassignment'] = list(chosen)
            details['fourth_slots'] = slots.tolist()
        if programme == 'B' and tick > 0 and tick % 10 == 0:
            for agent in range(6):
                details['uniform_draws'] += 1
                if rng.random() >= .9:
                    targets[agent] = draw()
                    details['uniform_draws'] += 3
                    details['replacements'] += 1
        delta = targets - current_pose[tick]
        output[tick] = delta / np.maximum(30., np.linalg.norm(delta, axis=-1))[:, None]
    if programme == 'O':
        # These are actual saved positions/routes, never predicted service scores.
        arrival_report = []
        for window in range(4):
            ids = assignment[2 * window:2 * window + 2] if window < 3 else tuple(details['reassignment'])
            targets = _slots(users, order[window:window + 1])
            start, stop = (0, 130) if window == 0 else (130, 501) if window == 3 else (0, 501)
            distances = np.linalg.norm(positions[start:stop, np.asarray(ids)] - targets[None], axis=-1)
            arrived = np.flatnonzero((distances <= 1e-3).all(axis=1))
            post = slice(window * 125 + 1, (window + 1) * 125 + 1)
            members = slice(10 + 10 * int(order[window]), 20 + 10 * int(order[window]))
            access = raw['connections'][post, :, members].sum(axis=(1, 2))
            service = (raw['connections'][post, :, members] & (raw['route_lengths'][post] > 0)[:, :, None]).sum(axis=(1, 2))
            arrival_report.append({'window': window, 'assigned_uavs': list(ids),
                                   'both_at_slots_first_state': start + int(arrived[0]) if len(arrived) else None,
                                   'slot_arrival_tolerance_m': .001,
                                   'minimum_max_pair_distance_m': float(distances.max(axis=1).min()),
                                   'window_access_count_max': int(access.max()), 'window_routed_count_max': int(service.max()),
                                   'qualified_routed_ticks': int((service >= 8).sum())})
        details['actual_arrival_association_route'] = arrival_report
    return output, details


def paired(values):
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (32,):
        raise ValueError('exact32 conditional worlds required')
    mean, se = float(values.mean()), float(values.std(ddof=1) / np.sqrt(32))
    return {'mean': mean, 'standard_error': se, 't95_df31': [mean - 2.0395134463964077 * se, mean + 2.0395134463964077 * se],
            'min': float(values.min()), 'p10': float(np.quantile(values, .1)), 'median': float(np.median(values)),
            'p90': float(np.quantile(values, .9)), 'max': float(values.max()),
            'positive': int((values > 0).sum()), 'negative': int((values < 0).sum()), 'zero': int((values == 0).sum()),
            'world_values': values.tolist()}


def comparisons(rows):
    expected = {(programme, int(world)) for programme in c.PROGRAMMES for world in c.WORLDS}
    by_key = {(r['programme'], int(r['world'])): r for r in rows if r['phase'] == 'main'}
    if set(by_key) != expected or sum(r['phase'] == 'main' for r in rows) != 224:
        raise AssertionError('complete7x32 main panel required')
    fields = [key for key, value in next(iter(by_key.values()))['metrics'].items() if isinstance(value, (int, float))]
    arrays = {p: {key: np.asarray([by_key[p, w]['metrics'][key] for w in c.WORLDS], dtype=float) for key in fields}
              for p in c.PROGRAMMES}
    arrays['H-noD-initial'] = arrays['H-initial']
    all_pairs = {}
    ordered = (*c.PROGRAMMES, 'H-noD-initial')
    for i, right in enumerate(ordered):
        for left in ordered[i + 1:]:
            all_pairs[f'{left} minus {right}'] = {key: paired(arrays[left][key] - arrays[right][key]) for key in fields}
    primary = {f'H-final minus {right}': {key: paired(arrays['H-final'][key] - arrays[right][key]) for key in fields}
               for right in ('H-noD-final', 'SET-final')}
    gains = {p: {key: paired(arrays[p + '-final'][key] - arrays[p + '-initial'][key]) for key in fields}
             for p in ('H', 'H-noD', 'SET')}
    cases = {}
    for left, right in (('H-final', 'H-noD-final'), ('H-final', 'SET-final'), ('H-final', 'O'), ('SET-final', 'O')):
        d = arrays[left]['W'] - arrays[right]['W']
        ranked = sorted(range(32), key=lambda i: (d[i], int(c.WORLDS[i])))
        cases[f'{left} minus {right}'] = {'lowest_worlds': [int(c.WORLDS[i]) for i in ranked[:3]],
                                         'highest_worlds': [int(c.WORLDS[i]) for i in ranked[-3:]],
                                         'joint_zero_worlds': [int(c.WORLDS[i]) for i in range(32)
                                                               if arrays[left]['W'][i] == arrays[right]['W'][i] == 0]}
    return {'scope': 'One trained instance per recipe.32 fresh paired worlds conditional on those instances; no training replication.',
            'worlds': list(c.WORLDS), 'levels': {p: {key: paired(value) for key, value in a.items()} for p, a in arrays.items()},
            'primary': primary, 'initial_to_final': gains, 'all28_pairs': all_pairs, 'case_worlds': cases}


def validate_shapes(raw, full):
    for key, value in raw.items():
        if value.dtype == object or value.dtype.kind in 'fc' and not np.isfinite(value).all():
            raise AssertionError('nonfinite/object raw field: ' + key)
    subset = ('positions', 'connections', 'routes', 'route_lengths', 'transmitter_mask')
    for key in c.STATE_FIELDS if full else subset:
        tail, dtype = c.STATE_FIELDS[key]
        if raw[key].shape != (501, *tail) or raw[key].dtype != np.dtype(dtype):
            raise AssertionError('raw state shape/dtype: ' + key)
    for key, (tail, dtype) in c.LEDGER_FIELDS.items():
        if raw[key].shape != (500, *tail) or raw[key].dtype != np.dtype(dtype):
            raise AssertionError('raw ledger shape/dtype: ' + key)
    if raw['raw_actions'].shape != (500, 6, 3) or raw['executed_actions'].shape != (500, 6, 3):
        raise AssertionError('complete sampled/executed command shape')
    if raw['raw_actions'].dtype not in (np.dtype('float32'), np.dtype('float64')) or raw['raw_actions'].dtype != raw['executed_actions'].dtype:
        raise AssertionError('preserved sampled/executed dtype')
    if full:
        for key, shape in (('observations', (501, 6, 211)), ('states', (501, 154))):
            if raw[key].shape != shape or raw[key].dtype != np.float32:
                raise AssertionError('actual complete information shape/dtype: ' + key)


def check_routes(raw):
    """Training has no extra radio replay, but retains complete native routes."""
    same(raw['transmitter_mask'], np.ones((501, 6), dtype=bool), 'all original transmitters remain on')
    lengths, paths = raw['route_lengths'], raw['routes']
    if np.any((lengths != 0) & ((lengths < 2) | (lengths > 5))):
        raise AssertionError('native BFS path length including endpoints')
    for time_index, agent in zip(*np.nonzero(lengths)):
        path = paths[time_index, agent, :lengths[time_index, agent]]
        if path[0] != agent or path[-1] != 6 or len(set(path[:-1].tolist())) != len(path) - 1 or np.any((path[:-1] < 0) | (path[:-1] > 5)):
            raise AssertionError('native route endpoint/node/cycle')
    for position in range(7):
        if np.any(paths[:, :, position][lengths <= position] != -1):
            raise AssertionError('route padding')
    if np.any(raw['connections'].sum(axis=1) > 1) or np.any(raw['connections'].sum(axis=2) > 10):
        raise AssertionError('exclusive user and per-UAV capacity')


def check_episode(raw, world, full, meter):
    validate_shapes(raw, full)
    positions0, users, order, packet = registry(world)
    same(raw['positions'][0], positions0, 'native initial uniform draw')
    same(raw['users'], users, 'registered users and order')
    same(raw['schedule'], order, 'complete fixed window schedule')
    same(raw['packet'], packet, '404-byte registered payload')
    check_routes(raw)
    command, following, events = motion(raw['positions'][:-1], raw['raw_actions'])
    same(raw['executed_actions'], command, 'dtype-preserving unit-ball clip')
    same(raw['positions'][1:], following, 'native normalized motion and boundary clipping')
    same(raw['action_clip_events'], events, 'native1e-9 clip-event convention')
    same(raw['terminated'], np.arange(500) == 499, 'complete terminal successor')
    same(raw['truncated'], np.zeros(500, dtype=bool), 'no truncation')
    facts = ledger(raw['connections'][1:], raw['route_lengths'][1:], order)
    for key, value in facts.items():
        same(raw[key], value, 'post-routing ledger ' + key)
    same(raw['coverage_backhauled'], facts['routed_user_mask'].mean(axis=1), 'all50 native coverage')
    same(raw['dense_reward'], .5 * (raw['coverage_backhauled'] + raw['throughput_term']), 'secondary dense diagnostic', atol=2e-15)
    meter.add('reader_ledger_updates', 500)
    meter.add('reader_user_indicator_reads', 25000)
    meter.add('reader_movement_uav_ticks', 3000)
    errors = {'user_sinr': 0., 'uav_sinr': 0., 'observations': 0., 'states': 0.}
    if full:
        same(raw['bs_positions'], [[2500., 2500., 30.]], 'fixed known BS')
        rebuilt_obs, rebuilt_states = np.empty_like(raw['observations']), np.empty_like(raw['states'])
        for tick in range(501):
            physical = physical_state(raw['positions'][tick], users)
            meter.add('reader_physical_states')
            meter.add('reader_distance_relations', 321)
            for key, expected in physical.items():
                tolerance = 2e-11 if key in ('user_sinr', 'uav_sinr') else 0.
                error = same(raw[key][tick], expected, f'physics {tick}/{key}', atol=tolerance)
                if key in errors:
                    errors[key] = max(errors[key], error)
            # Use the independent physical calculation for information replay.
            obs, state = information(raw['positions'][tick], users, order, tick, physical)
            rebuilt_obs[tick], rebuilt_states[tick] = obs, state
            errors['observations'] = max(errors['observations'], same(raw['observations'][tick], obs, 'complete legal observation', atol=1.2e-7))
            errors['states'] = max(errors['states'], same(raw['states'][tick], state, 'complete count/task state'))
            if tick:
                dense = dense_values(physical['connections'], physical['route_lengths'], physical['user_sinr'])
                for key, value in dense.items():
                    same(raw[key][tick - 1], value, 'independent native dense diagnostic ' + key, atol=2e-10)
        # Inputs are independently reconstructed, not copied from the recorded actor inputs.
        replay = dict(raw)
        replay['observations'], replay['states'] = rebuilt_obs, rebuilt_states
    else:
        replay = None
    return {'world': int(world), 'metrics': mission_metrics(raw, facts), 'max_errors': errors}, replay


def checked_file(root, identity):
    root = Path(root).resolve()
    path = Path(identity['path'])
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise AssertionError('evidence path is missing or outside canonical worker root')
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    if path.stat().st_size != int(identity['bytes']) or h.hexdigest() != identity['sha256']:
        raise AssertionError('canonical evidence identity changed: ' + str(path))
    return path


def load_arrays(root, identity):
    with np.load(checked_file(root, identity), allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.partial')
    partial.write_text(json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':')) + '\n')
    partial.replace(path)


def replay_model(agent, payload, raw, metadata, meter):
    """Same pinned neural implementation, independently reconstructed legal inputs."""
    import torch
    from . import evidence as e
    world = int(metadata['world'])
    agent.reset_env_state(0)
    e.seed_rng(world + 51)
    if e.rng_state() != metadata['pre_world_rng']:
        raise AssertionError('deployment RNG does not equal the fixed per-world seed state')
    e.restore_rng(metadata['pre_world_rng'])
    before = e.digest_agent(agent)
    if before != payload['state_digest']:
        raise AssertionError('complete loaded model/normalizer identity')
    maximum = {'raw_actions': 0., 'step_values': 0., 'hidden_inputs': 0.}
    with e.instrument_agent(agent, meter) as optimizers, torch.no_grad():
        for tick in range(500):
            actions, _, data = agent.step(raw['states'][tick][None], raw['observations'][tick][None],
                                          np.asarray([tick]), np.asarray([False]), deterministic=False,
                                          return_step_data=True, build_infos=False)
            meter.add('reader_model_team_steps')
            meter.add('reader_actor_agent_rows', 6)
            meter.add('reader_critic_agent_rows', 6)
            maximum['raw_actions'] = max(maximum['raw_actions'], same(actions[0], raw['raw_actions'][tick], 'sampled policy action replay', atol=2e-5, rtol=1e-6))
            for key in c.STEP_FIELDS:
                saved = 'step__' + key
                if (key in data) != (saved in raw):
                    raise AssertionError('complete per-step policy metadata: ' + key)
                if key in data:
                    value = np.asarray(data[key])[0]
                    error = same(raw[saved][tick], value, 'policy metadata ' + key,
                                 atol=2e-5 if value.dtype.kind == 'f' else 0., rtol=1e-6 if value.dtype.kind == 'f' else 0.)
                    maximum['step_values'] = max(maximum['step_values'], error)
            log = data['log_probs'][0]
            for key in ('team_log_prob', 'agent_log_probs', 'state_value', 'agent_values'):
                value = np.asarray(log.get(key, 0. if key in ('team_log_prob', 'state_value') else [0.] * 6), dtype=np.float32)
                same(raw['coord__' + key][tick], value, 'coordinator metadata ' + key, atol=2e-5, rtol=1e-6)
            for key, value in (('actor_hidden_input', agent.get_prev_actor_hidden_np(0, n_agents=6)),
                               ('critic_hidden_input', agent.get_prev_critic_hidden_np(0, n_agents=6))):
                maximum['hidden_inputs'] = max(maximum['hidden_inputs'], same(raw[key][tick], value, 'recurrent input ' + key, atol=2e-5, rtol=1e-6))
                if tick == 0:
                    same(value, np.zeros_like(value), 'first-step recurrent reset mask')
            if agent.use_central_snapshot:
                held_tick = tick // 10 * 10
                same(raw['held_states'][tick], raw['states'][held_tick], 'recorded SET held state')
                same(raw['held_observations'][tick], raw['observations'][held_tick], 'recorded SET held joint rows', atol=1.2e-7)
                same(agent._central_snapshot_states[0], raw['states'][held_tick], 'replayed SET snapshot clock')
                same(agent._central_snapshot_obs[0], raw['observations'][held_tick], 'replayed SET held rows')
            if agent.d2_enabled:
                expected = tick % 10 == 0
                same(data['d2_sample_Z'][0], expected, 'fixed10 team skill clock')
                same(data['d2_sampled_mask'][0], np.full(6, expected), 'all6 synchronized skill assignments')
                meter.add('reader_H_skill_decisions' if expected else 'reader_H_nondecision_ticks')
                # Native D2 evaluates the previous held skill even before a new
                # boundary choice; only the first tick lacks that evaluation.
                if tick:
                    meter.add('reader_H_held_team_rows')
        if any(optimizers.values()):
            raise AssertionError('reader replay performed optimization')
    if e.digest_agent(agent) != before:
        raise AssertionError('reader replay modified model or normalizer state')
    return {'max_errors': maximum, 'frozen_state_digest': before, 'optimizer_calls': optimizers,
            'neural_replay_scope': 'pinned factory/native inference reused; physics/information/ordinary/ledger independently reconstructed'}


def check_training_rewards(raw, arm):
    expected_env = np.broadcast_to(raw['external_scalar'][:, None], (500, 6)).astype(np.float32)
    same(raw['reward_env'], expected_env, 'low-level external per-agent R/6')
    same(raw['reward_process'], np.zeros_like(raw['reward_process']), 'no process bonus')
    if arm != 'H':
        same(raw['reward_team_disc'], np.zeros_like(raw['reward_team_disc']), 'disabled discriminator reward')
        same(raw['reward_ind_disc'], np.zeros_like(raw['reward_ind_disc']), 'disabled individual reward')
    mixed = raw['reward_env'] + raw['reward_team_disc'] + raw['reward_ind_disc'] + raw['reward_process']
    same(raw['mixed_low_reward'], mixed, 'actual low-level mixed reward components', atol=1.2e-7, rtol=1e-6)
    return {'external_agent_reward_sum': float(np.sum(raw['reward_env'], dtype=np.float64)),
            'team_discriminator_component_sum': float(np.sum(raw['reward_team_disc'], dtype=np.float64)),
            'individual_discriminator_component_sum': float(np.sum(raw['reward_ind_disc'], dtype=np.float64)),
            'component_scope': 'native stored weighted reward components; no extra discriminator inference'}


def check_d2(table, raw):
    """Validate segment units at their original start slots, not a toy return."""
    valid = np.arange(500) % 10 == 0
    same(table['d2_team_valid'], valid, 'd2 every10 team segment starts')
    same(table['d2_agent_valid'], np.broadcast_to(valid[:, None], (500, 6)), 'd2 all-agent segment starts')
    rewards = np.asarray(raw['external_scalar'])
    expected = np.asarray([sum(.99 ** u * float(rewards[t + u]) for u in range(10)) for t in range(0, 500, 10)], dtype=np.float32)
    same(table['d2_team_reward'][valid], expected, 'discounted external-only high-level team reward')
    same(table['d2_agent_reward'][valid], np.broadcast_to(expected[:, None], (50, 6)), 'discounted external-only high-level individual reward')
    for level in ('team', 'agent'):
        same(table[f'd2_{level}_elapsed'][valid], np.full_like(table[f'd2_{level}_elapsed'][valid], 10), 'd2 elapsed10')
        terminals = np.zeros_like(table[f'd2_{level}_terminal'][valid])
        terminals[-1] = True
        same(table[f'd2_{level}_terminal'][valid], terminals, 'd2 terminal segment only at final native step')
    return {'team_segments': 50, 'individual_segments': 300, 'within_segment_discount': .99,
            'across_segment_discount': .99 ** 10, 'terminal_bootstrap': 0., 'reward_units': 'per-agent external R/6'}


def compare_worker_metrics(ours, theirs):
    fields = ('W', 'window_fraction', 'J_dense', 'team_zero_ticks', 'longest_team_zero_run',
              'mean_path_length_m', 'zero_displacement_uav_ticks', 'coverage_backhauled', 'throughput_term')
    for key in fields:
        same(ours[key], theirs[key], 'independent/worker mission reduction ' + key, atol=1e-10)
    same(ours['action_clip_events'], theirs['clip_events'], 'worker clipping count')
    service = theirs['all_user_service']
    for key in ('never_served_users', 'mean_user_longest_gap', 'p90_user_longest_gap', 'max_user_longest_gap'):
        same(ours[key], service[key], 'all50-user reduction ' + key)
    for own, old in zip(ours['user_details'], service['users']):
        for key in ('user', 'served_ticks', 'longest_gap', 'leading_gap', 'trailing_gap'):
            same(own[key], old[key], 'per-user full mission ' + key)
        if own['gaps'] != old['zero_runs']:
            raise AssertionError('per-user start/end-censored gap history')


def run(root, out, args, context):
    """One declared reader operation over the complete canonical worker output."""
    import gc
    from . import evidence as e
    worker_root, out = Path(context['worker_root']), Path(out)
    manifest, worker = context['manifest'], context['worker_summary']
    meter = context['meter']
    if worker['status'] != 'COMPLETE' or worker['new_native_steps'] != 1196000 or worker['new_fits'] != 3 or worker['optimizer_steps'] != 615600:
        raise AssertionError('one complete fixed worker required')
    expected_frozen = {(p, int(w), 'main') for p in c.PROGRAMMES for w in c.WORLDS}
    expected_frozen |= {(p, c.AUDIT_WORLD, 'audit') for p in c.AUDITS}
    actual_frozen = {(r['programme'], int(r['world']), r['phase']) for r in manifest['frozen']}
    expected_training = {(arm, rollout) for arm in c.ARMS for rollout in range(1, 46)}
    if len(manifest['frozen']) != 232 or actual_frozen != expected_frozen or len(manifest['training']) != 135 or {(r['arm'], r['rollout']) for r in manifest['training']} != expected_training:
        raise AssertionError('complete fixed endpoint and training roster')
    if worker.get('launch_sha') != context['worker_config']['launch_sha']:
        raise AssertionError('worker configuration/source identity')
    alias = json.loads(checked_file(worker_root, manifest['initial_alias']).read_bytes())
    if alias['only_difference'] != 'disable_discriminator_rewards' or alias['alias_main'] != 'H-initial':
        raise AssertionError('full initial inference alias proof')
    changed = {key for key in alias['H'] if alias['H'][key] != alias['H-noD'][key]}
    if changed != {'disable_discriminator_rewards'} or alias['H']['disable_discriminator_training'] or alias['H-noD']['disable_discriminator_training']:
        raise AssertionError('noD retains original classifier training and initial inference')
    same(alias['aliased_worlds'], c.WORLDS, 'initial alias full32-world scope')
    if alias['source_sha256'] != context['worker_config']['source_sha256']:
        raise AssertionError('initial alias scientific source identity')
    results, training = [], []
    prefix = context.get('reader_prefix')
    progress = {'schema': 1, 'status': 'STARTED', 'new_native_steps': 0, 'new_fits': 0, 'optimizer_steps': 0,
                'worker_manifest': context['manifest_identity'], 'frozen_checked': 0, 'training_rollouts_checked': 0}
    def publish():
        progress['cost'] = meter.report()
        _write(out / 'summary.json', progress)
    publish()
    try:
        meter.phase = 'reader/training'
        for row in sorted(manifest['training'], key=lambda r: (c.ARMS.index(r['arm']), r['rollout'])):
            arm, rollout = row['arm'], int(row['rollout'])
            if prefix:
                from .reader_prefix import reuse_training
                training.append(reuse_training(prefix, row, worker_root, meter))
                progress['training_rollouts_checked'] += 1
                continue
            progress['inflight'] = {'kind': 'training', 'arm': arm, 'rollout': rollout}
            publish()
            metadata = json.loads(checked_file(worker_root, row['metadata']).read_bytes())
            raw = load_arrays(worker_root, row['raw'])
            worlds = [c.training_world(lane, rollout - 1) for lane in range(16)]
            same(metadata['worlds'], worlds, 'shared complete training-world address')
            same(row['worlds'], worlds, 'training manifest world address')
            if metadata['arm'] != arm or metadata['rollout'] != rollout or metadata['launch_sha'] != worker['launch_sha']:
                raise AssertionError('training row lineage')
            expected_total = {key: total // 45 * rollout for key, total in c.OPTIMIZER_TOTALS[arm].items()}
            expected_delta = {key: total // 45 for key, total in c.OPTIMIZER_TOTALS[arm].items()}
            if metadata['optimizer_total'] != expected_total or metadata['optimizer_delta'] != expected_delta:
                raise AssertionError('all native update/retained-classifier counts')
            terminal = metadata['terminal_facts']
            if not terminal['low_level_dones_last_step_all_true'] or terminal['low_level_dones_before_last_any']:
                raise AssertionError('saved native terminal masks')
            lanes = []
            for lane, world in enumerate(worlds):
                one = {key: value[lane] for key, value in raw.items()}
                result, _ = check_episode(one, world, False, meter)
                compare_worker_metrics(result['metrics'], metadata['metrics'][lane])
                result['rewards'] = check_training_rewards(one, arm)
                if arm != 'SET':
                    result['d2'] = check_d2(one, one)
                # Raw masks retain every user tick; compact training checks retain
                # per-user totals/gaps without repeating every interval in JSON.
                for person in result['metrics']['user_details']:
                    person.pop('gaps')
                lanes.append(result)
            checked = {'arm': arm, 'rollout': rollout, 'worlds': worlds, 'lanes': lanes,
                       'losses': metadata['losses'], 'parameter_motion': metadata['parameter_motion'],
                       'optimizer_total': metadata['optimizer_total'], 'raw': row['raw'], 'metadata': row['metadata']}
            _write(out / 'checks' / 'training' / f'{arm}_{rollout:02}.json', checked)
            scalar_keys = [key for key, value in lanes[0]['metrics'].items() if isinstance(value, (int, float))]
            training.append({'arm': arm, 'rollout': rollout,
                             'means': {key: float(np.mean([x['metrics'][key] for x in lanes])) for key in scalar_keys},
                             'W_by_lane': [x['metrics']['W'] for x in lanes], 'losses': metadata['losses'],
                             'parameter_motion': metadata['parameter_motion'], 'optimizer_total': expected_total})
            progress['training_rollouts_checked'] += 1
            del raw
            publish()
        agent, payload, current_checkpoint = None, None, None
        for row in manifest['frozen']:
            programme, world = row['programme'], int(row['world'])
            if prefix and (programme, world) in prefix['frozen']:
                from .reader_prefix import reuse_frozen
                results.append(reuse_frozen(prefix, row, worker_root, meter))
                progress['frozen_checked'] += 1
                continue
            progress['inflight'] = {'kind': 'frozen', 'programme': programme, 'world': world, 'phase': row['phase']}
            meter.phase = 'reader/' + programme
            publish()
            raw = load_arrays(worker_root, row['raw'])
            metadata = json.loads(checked_file(worker_root, row['metadata']).read_bytes())
            for key in ('world', 'programme', 'phase'):
                if metadata[key] != row[key]:
                    raise AssertionError('frozen metadata lineage: ' + key)
            if metadata['source_sha256'] != context['worker_config']['source_sha256'] or metadata['worker_config_sha256'] != context['worker_config_identity']['sha256']:
                raise AssertionError('frozen source/input identities')
            result, replay = check_episode(raw, world, True, meter)
            result.update(programme=programme, phase=row['phase'], raw=row['raw'], metadata=row['metadata'])
            compare_worker_metrics(result['metrics'], metadata['metrics'])
            if programme in ('O', 'B'):
                commands, details = ordinary_commands(replay, programme, world)
                same(raw['raw_actions'], commands, 'complete lawful ordinary command reconstruction', atol=1e-13)
                meter.add('reader_ordinary_' + programme + '_commands', 3000)
                if programme == 'O':
                    meter.add('reader_O_permutation_comparisons', 722)
                    meter.add('reader_O_matching_distances', 40)
                    same(metadata['ordinary']['assignment'], details['initial_assignment'], 'ordinary initial complete matching')
                    same(metadata['ordinary']['reassignment'], details['reassignment'], 'ordinary fourth-cluster matching')
                else:
                    same(metadata['ordinary']['draws'], details['uniform_draws'], 'sticky random draws including replacements')
                    same(metadata['ordinary']['replacements'], details['replacements'], 'sticky replacement decisions')
                result['ordinary'] = details
            else:
                arm, endpoint = programme.rsplit('-', 1)
                identity = manifest['checkpoints'][arm][endpoint]
                if metadata['checkpoint'] != identity:
                    raise AssertionError('mission checkpoint matches exact programme')
                address = (arm, endpoint, identity['sha256'])
                if address != current_checkpoint:
                    if agent is not None:
                        del agent
                        gc.collect()
                    checkpoint = checked_file(worker_root, identity)
                    agent, config, payload = e.load_agent(checkpoint, arm, 1, out / 'logs' / programme, meter)
                    current_checkpoint = address
                    if payload['launch_sha'] != worker['launch_sha'] or payload['endpoint'] != endpoint:
                        raise AssertionError('checkpoint launch/endpoint binding')
                    if endpoint == 'initial' and arm in ('H', 'H-noD') and payload['state_digest'] != alias['state_digest']:
                        raise AssertionError('initial full H/noD module-normalizer alias')
                result['policy'] = replay_model(agent, payload, replay, metadata, meter)
            _write(out / 'checks' / 'frozen' / f'{programme}_{world}.json', result)
            results.append(result)
            progress['frozen_checked'] += 1
            del raw, replay
            publish()
        if agent is not None:
            del agent
            gc.collect()
        # The audit is a wiring witness in addition to the whole-initial-state proof.
        audits = {r['programme']: r for r in manifest['frozen'] if r['phase'] == 'audit'}
        h = load_arrays(worker_root, audits['H-initial']['raw'])
        n = load_arrays(worker_root, audits['H-noD-initial']['raw'])
        if set(h) != set(n):
            raise AssertionError('full initial audit fields')
        for key in h:
            same(h[key], n[key], 'complete initial audit identity ' + key)
        del h, n
        expected = {'reader_ledger_updates': 1196000, 'reader_user_indicator_reads': 59800000,
                    'reader_movement_uav_ticks': 7176000, 'reader_physical_states': 116232,
                    'reader_distance_relations': 37310472, 'reader_model_team_steps': 83000,
                    'reader_actor_agent_rows': 498000, 'reader_critic_agent_rows': 498000,
                    'reader_H_skill_decisions': 5000, 'reader_H_nondecision_ticks': 45000,
                    'reader_H_held_team_rows': 49900, 'reader_ordinary_O_commands': 99000,
                    'reader_ordinary_B_commands': 99000, 'reader_O_permutation_comparisons': 23826,
                    'reader_O_matching_distances': 1320}
        reused_counts = prefix['counts'] if prefix else {}
        for key, value in expected.items():
            same(meter.counts.get(key, 0) + reused_counts.get(key, 0), value,
                 'complete reader exposure including bound prefix ' + key)
        if prefix:
            same(meter.counts.get('reader_prefix_movement_recheck_uav_ticks'), 6981000,
                 'all reused movement rechecked under host-copy semantics')
            if meter.counts.get('model_constructions', 0) or meter.counts.get('reader_model_team_steps', 0):
                raise AssertionError('prefix completion must not repeat neural queries')
        if any(meter.counts.get('optimizer_' + key, 0) for key in e.OPTIMIZERS):
            raise AssertionError('reader must not perform an optimizer step')
        reading = {'schema': 1, 'object': c.OBJECT, 'worker_manifest': context['manifest_identity'],
                   'worker_summary': context['worker_summary_identity'], 'worker_config': context['worker_config_identity'],
                   'source_sha256': context['source_sha256'], 'comparisons': comparisons(results),
                   'training': training, 'cost': meter.report(),
                   'frozen_results': [{key: value for key, value in r.items() if key not in ('policy', 'max_errors')}
                                      for r in results],
                   'scope': 'All232 frozen and2160 training missions read; no environment/controller counterfactual rollout or optimizer replay.'}
        if prefix:
            reading['reused_prefix'] = prefix['identity']
            reading['coverage_counts'] = expected
            reading['reused_counts'] = reused_counts
        # Full per-user interval histories live once in checks/frozen, whose paths
        # and original masks remain available; the published reading stays compact.
        for result in reading['frozen_results']:
            result['metrics'] = dict(result['metrics'])
            result['metrics'].pop('user_details')
        _write(out / 'reading.json', reading)
        progress.update(status='COMPLETE', inflight=None, reading=e.identity(out / 'reading.json', out),
                        declared_reader_counts=expected, native_worker_steps=1196000, worker_fits=3,
                        worker_optimizer_steps=615600)
        if prefix:
            progress.update(reused_prefix=prefix['identity'], reused_counts=reused_counts,
                            new_frozen_checked=65, reused_frozen_checked=167,
                            reused_training_rollouts_checked=135)
        publish()
        return progress
    except BaseException as exc:
        progress.update(status='FAILED', error=type(exc).__name__ + ': ' + str(exc))
        publish()
        raise
