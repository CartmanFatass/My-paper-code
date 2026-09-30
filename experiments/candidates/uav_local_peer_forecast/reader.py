"""Independent saved-data reconstruction. No actor/scorer/environment calls.

The local model intentionally uses C's sum-minus-own numerical law; the native
radio intentionally uses ascending-source sums and its dBm round trip. They are
different contracts. Comparisons use 2e-12 for FP64 score/radio arithmetic while
requiring exact observations, indices, commands, gates, and physical paths.
"""
from itertools import product
from pathlib import Path
import argparse
import os
import time

for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[_key] = '1'

import numpy as np

from .study import ARMS, SEEDS, ORDERS, HORIZON, identity, resources, write_json

COMMANDS = np.array(sorted(product((-1, 0, 1), repeat=3),
                           key=lambda a: (sum(x*x for x in a), a)), dtype=np.float32)
LOW, HIGH = np.array((0., 0., 50.)), np.array((1000., 1000., 150.))
WAYPOINTS = np.array(((100, 100), (900, 100), (900, 300), (100, 300),
                      (100, 500), (900, 500), (900, 700), (100, 700),
                      (100, 900), (900, 900)), dtype=np.float64)
SLICES = ('all', 'matched', 'moving_matched', 'moving_current_users',
          'moving_score_changed', 'moving_argmax_changed', 'moving_action_changed',
          'moving_physical_changed')


def new_progress():
    """Small mutable incurred-work record, also valid when reconstruction fails."""
    return dict(status='incomplete', episodes_started=0, episodes_completed=0,
                completed_episode_keys=[], current=None, counts={key: 0 for key in (
                    'score_requests_attempted', 'score_requests_completed',
                    'logical_model_ticks_attempted', 'logical_model_ticks_completed',
                    'controller_power_batches_attempted', 'controller_power_batches_completed',
                    'controller_power_values_attempted', 'controller_power_values_completed',
                    'native_reconstructions_attempted', 'native_reconstructions_completed',
                    'native_dense_power_slots_attempted', 'native_dense_power_slots_completed')})


def advance(progress, key, amount=1):
    if progress is not None:
        progress['counts'][key] += int(amount)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, name, *, exact=False):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape, f'{name}: shape {a.shape} != {b.shape}')
    require(np.array_equal(a, b) if exact else np.allclose(a, b, rtol=0, atol=2e-12),
            f'{name}: values differ')


def native_radio(positions, users, clock, *, progress=None):
    """Rebuild all-on free-space radio, stable greedy assignment and local rows."""
    xyz = np.asarray(positions, dtype=np.float64)
    users = np.asarray(users, dtype=np.float64)
    advance(progress, 'native_reconstructions_attempted')
    advance(progress, 'native_dense_power_slots_attempted', 275)
    d = xyz[:, None, :2] - users[None]
    distance = np.sqrt(d[..., 0]**2 + d[..., 1]**2 + xyz[:, None, 2]**2)
    loss = 20*np.log10(np.maximum(distance, 1e-6)) + 20*np.log10(4*np.pi/.15)
    pair = xyz[:, None] - xyz[None]
    pd = np.sqrt(pair[..., 0]**2 + pair[..., 1]**2 + pair[..., 2]**2)
    peer_loss = 20*np.log10(np.maximum(pd, 1e-6)) + 20*np.log10(4*np.pi/.15)
    np.fill_diagonal(peer_loss, 0.)

    def sinr_matrix(path_loss, peer=False):
        rx = 23. - path_loss
        linear = 10.**(rx/10.)
        if peer:
            np.fill_diagonal(linear, 0.)
        interference = np.zeros_like(linear)
        for tx in range(5):
            for other in range(5):
                if other != tx:
                    interference[tx] += linear[other]
        positive = interference > 0
        db = 10*np.log10(np.where(positive, interference, 1.))
        denominator = np.where(positive, 10*np.log10(1e-8 + 10.**(db/10.)), -80.)
        return rx-denominator

    sinr, peer_sinr = sinr_matrix(loss), sinr_matrix(peer_loss, True)
    advance(progress, 'native_dense_power_slots_completed', 275)
    connections = np.zeros((5, 50), dtype=bool)
    occupancy = np.zeros(5, dtype=np.int64)
    used = set()
    # Python's stable sort retains native row-major ties independently of numpy argsort.
    eligible = [(i, j) for i in range(5) for j in range(50) if sinr[i, j] >= 3.]
    for i, j in sorted(eligible, key=lambda ij: -sinr[ij]):
        if j not in used and occupancy[i] < 10:
            used.add(j)
            connections[i, j] = True
            occupancy[i] += 1
    served = int(connections.sum())
    quality_sum = 0.
    for i in range(5):
        for j in range(50):
            if connections[i, j]:
                quality_sum += float(np.clip((sinr[i, j]-3.)/30., 0., 1.))
    quality = quality_sum/max(served, 1)
    obs = np.zeros((5, 104), dtype=np.float32)
    user_ids, peer_ids = [], []
    for i in range(5):
        u = sorted((j for j in range(50) if sinr[i, j] >= 3.), key=lambda j: -sinr[i, j])[:20]
        p = sorted((j for j in range(5) if j != i and peer_sinr[i, j] >= 3.),
                   key=lambda j: -peer_sinr[i, j])
        obs[i, :3] = (xyz[i, 0]/1000, xyz[i, 1]/1000, (xyz[i, 2]-50)/100)
        for k, j in enumerate(u):
            obs[i, 3+3*k:6+3*k] = (*((users[j]-xyz[i, :2])/1000),
                                       np.clip((sinr[i, j]+10)/50, 0, 1))
        for k, j in enumerate(p):
            obs[i, 63+4*k:67+4*k] = (*((xyz[j]-xyz[i])/(1000, 1000, 100)),
                                         np.clip((peer_sinr[i, j]+10)/50, 0, 1))
        obs[i, 103] = clock/256
        user_ids.append(u)
        peer_ids.append(p)
    advance(progress, 'native_reconstructions_completed')
    return dict(obs=obs, user_ids=user_ids, peer_ids=peer_ids, sinr=sinr,
                connections=connections, served=served, quality=quality,
                J=.7*served/50 + .3*quality)


def decode(row):
    row = np.asarray(row, dtype=np.float32)
    own = np.array((float(row[0])*1000, float(row[1])*1000, 50+float(row[2])*100))
    users, peers = row[3:63].reshape(20, 3), row[63:103].reshape(10, 4)
    u, p = users[users[:, 2] > 0], peers[peers[:, 3] > 0]
    return own, own[:2]+u[:, :2].astype(float)*1000, u[:, 2].astype(float)*50-10, (
        own+p[:, :3].astype(float)*(1000, 1000, 100))


def match_frames(current, previous):
    matches = np.full(len(current), -1, dtype=np.int64)
    gates = np.zeros((len(current), len(previous)), dtype=bool)
    # Separate scalar gate construction avoids using live association as proof.
    for i, point in enumerate(current):
        for j, old in enumerate(previous):
            gates[i, j] = all(abs(float(point[k]-old[k])) <= 30.001 for k in range(3))
    for i in range(len(current)):
        possible = np.flatnonzero(gates[i])
        if len(possible) == 1 and int(gates[:, possible[0]].sum()) == 1:
            matches[i] = possible[0]
    delta = np.zeros_like(current)
    for i, j in enumerate(matches):
        if j >= 0:
            for axis in range(3):
                value = current[i, axis]-previous[j, axis]
                delta[i, axis] = 0. if abs(value) < .001 else min(30., max(-30., value))
    return matches, delta, gates.sum(axis=1)


def local_power(stations, users, *, progress=None):
    # C's squared-distance summation, unlike the native per-axis expression.
    values = int(np.prod(stations.shape[:-1]))*len(users)
    advance(progress, 'controller_power_batches_attempted')
    advance(progress, 'controller_power_values_attempted', values)
    d = stations[..., None, :2]-users[..., :2]
    squared = np.sum(d*d, axis=-1) + stations[..., None, 2]**2
    loss = 20*np.log10(np.sqrt(np.maximum(squared, 1e-12))) + 20*np.log10(4*np.pi/.15)
    powers = 10.**((23.-loss)/10.)
    advance(progress, 'controller_power_batches_completed')
    advance(progress, 'controller_power_values_completed', values)
    return powers


def prepare_score(own, users, observed_sinr, peers, *, progress=None):
    xyz = np.broadcast_to(own, (27, 3)).copy()
    trajectories = np.empty((27, 4, 3))
    for lead in range(4):
        xyz = np.minimum(HIGH, np.maximum(LOW, xyz+30*COMMANDS))
        trajectories[:, lead] = xyz
    present = local_power(np.concatenate((own[None], peers)), users, progress=progress)
    unknown = np.zeros(len(users))
    if len(peers) < 4:
        unknown = np.maximum(present[0]/(10.**(observed_sinr/10.))
                             - np.sum(present[1:], axis=0)-1e-8, 0.)
    return dict(trajectories=trajectories, present=present, unknown=unknown,
                own_power=local_power(trajectories, users, progress=progress), own=own, users=users, peers=peers)


def ranking(prepared, delta, sign, nav, *, progress=None):
    """Pure ranking; actual and C shadow share prepared powers, never state mutation."""
    peers, users = prepared['peers'], prepared['users']
    advance(progress, 'score_requests_attempted')
    advance(progress, 'logical_model_ticks_attempted', 108)
    p, n = len(peers), len(users)
    moving = np.any(delta != 0, axis=1) if sign else np.zeros(p, dtype=bool)
    future = np.broadcast_to(prepared['present'][None, 1:], (4, p, n)).copy()
    positions = peers[moving].copy()
    for lead in range(4):
        if n and moving.any():
            positions = np.minimum(HIGH, np.maximum(LOW, positions+sign*delta[moving]))
            future[lead, moving] = local_power(positions, users, progress=progress)
    if n:
        powers = np.concatenate((prepared['own_power'][:, :, None],
                                 np.broadcast_to(future, (27, 4, p, n))), axis=2)
        sinr = 10*np.log10(powers/(powers.sum(axis=2, keepdims=True)-powers
                                  + prepared['unknown']+1e-8))
        selected = np.zeros(sinr.shape, dtype=bool)
        # Sort and select independently per transmitter; no cross-user truth.
        for tx in range(1+p):
            order = np.argsort(-sinr[:, :, tx], axis=-1, kind='stable')[:, :, :10]
            eligible = sinr[:, :, tx] >= 3.
            np.put_along_axis(selected[:, :, tx], order,
                              np.take_along_axis(eligible, order, axis=-1), axis=-1)
        counts = selected.sum(axis=(-1, -2))
        quality = np.where(selected, np.clip((sinr-3)/30, 0, 1), 0).sum(
            axis=(-1, -2))/np.maximum(counts, 1)
        scores = (.7*counts/50 + .3*quality).mean(axis=1)
        served = counts.mean(axis=1)
    else:
        scores, served = np.zeros(27), np.zeros(27)
    fallback = bool(np.all(served == 0))
    entering = nav
    if nav == -1:
        nav = int(np.argmin(((WAYPOINTS-prepared['own'][:2])**2).sum(axis=1)))
    initialized_nav = nav
    if fallback:
        if np.linalg.norm(WAYPOINTS[nav]-prepared['own'][:2]) <= 60.:
            nav = (nav+1) % 10
        target = np.r_[WAYPOINTS[nav], 50.]
        selected_index = int(np.argmin(((prepared['trajectories'][:, -1]-target)**2).sum(axis=1)))
    else:
        selected_index = int(np.argmax(scores))
    advance(progress, 'score_requests_completed')
    advance(progress, 'logical_model_ticks_completed', 108)
    return dict(scores=scores, served=served, choice=selected_index,
                argmax=int(np.argmax(scores)), fallback=fallback, nav=nav,
                initialized_nav=initialized_nav, entering_nav=entering,
                moving_powers=4*int(moving.sum())*n)


def initial_geometry(seed):
    rng = np.random.RandomState(seed)
    xyz = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                    for _ in range(5)])
    users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
    return xyz, users


def longest_zero_run(served):
    longest = current = 0
    for value in served:
        current = current+1 if value == 0 else 0
        longest = max(longest, current)
    return longest


def endpoint(data):
    positions, served = data['positions'], data['served']
    post = positions[1:]
    boundary = ((post[..., :2] <= .001) | (post[..., :2] >= 999.999)).any(axis=-1)
    return dict(J=float(data['reward'].mean()), return_sum=float(data['reward'].sum()),
                mean_served=float(served.mean()), mean_quality=float(data['quality'].mean()),
                min_served=int(served.min()), service_p10=float(np.quantile(served, .1)),
                zero_service_ticks=int((served == 0).sum()), longest_zero_run=longest_zero_run(served),
                per_uav_path_length_m=np.linalg.norm(np.diff(positions, axis=0), axis=-1).sum(axis=0).tolist(),
                mean_path_length_m=float(np.linalg.norm(np.diff(positions, axis=0), axis=-1).sum(axis=0).mean()),
                xy_boundary_uav_ticks=int(boundary.sum()),
                lower_altitude_uav_ticks=int((post[..., 2] <= 50.001).sum()),
                upper_altitude_uav_ticks=int((post[..., 2] >= 149.999).sum()),
                mean_altitude_m=float(post[..., 2].mean()),
                fallback_decisions=int(data['fallback'][::4].sum()))


def empty_errors():
    return {s: dict(pairs=0, lead_sums=np.zeros((3, 4))) for s in SLICES}


def error_reading(errors):
    result = {}
    for name, item in errors.items():
        count = item['pairs']
        lead = item['lead_sums']/count if count else None
        result[name] = dict(pairs=count, per_lead_mean_m=(
            {arm: lead[i].tolist() for i, arm in enumerate(ARMS)} if count else None),
            four_lead_then_pair_mean_m=(
                {arm: float(lead[i].mean()) for i, arm in enumerate(ARMS)} if count else None))
    return result


def read_episode(data, *, horizon=HORIZON, verify_seed=True, progress=None):
    arm, seed = str(data['arm']), int(data['seed'])
    if progress is None:
        progress = new_progress()
    progress['episodes_started'] += 1
    progress['current'] = dict(arm=arm, seed=seed, tick=None, actor=None, stage='input_checks')
    require(arm in ARMS, 'unknown arm')
    shapes = dict(observations=(horizon+1, 5, 104), positions=(horizon+1, 5, 3),
                  users=(50, 2), commands=(horizon, 5, 3), reward=(horizon,),
                  served=(horizon,), quality=(horizon,), agent_rewards=(horizon, 5),
                  connections=(horizon, 5, 50), native_sinr=(horizon, 5, 50),
                  selected_index=(horizon, 5), fallback=(horizon, 5),
                  nav_before=(horizon, 5), nav_after=(horizon, 5),
                  n=(horizon, 5), p=(horizon, 5), m=(horizon, 5),
                  matches=(horizon, 5, 4), delta=(horizon, 5, 4, 3), gate_counts=(horizon, 5, 4),
                  scores=(horizon//4, 5, 27), candidate_service=(horizon//4, 5, 27))
    require(horizon > 0 and horizon % 4 == 0, 'reader requires complete command blocks')
    for name, shape in shapes.items():
        require(name in data and data[name].shape == shape, f'incomplete/invalid {name}')
        require(np.isfinite(data[name]).all(), f'nonfinite {name}')
    require(np.isin(data['commands'], (-1, 0, 1)).all(), 'nonprimitive command')
    if verify_seed:
        xyz, users = initial_geometry(seed)
        close(data['positions'][0], xyz, 'seed initial UAVs', exact=True)
        close(data['users'], users, 'seed static users', exact=True)
    previous = [np.empty((0, 3)) for _ in range(5)]
    previous_ids = [[] for _ in range(5)]
    nav = [-1]*5
    hold = np.zeros((5, 3), dtype=np.float32)
    plan_choice, plan_fallback = np.full(5, -1), np.zeros(5, dtype=bool)
    errors = empty_errors()
    counts = dict(ingests=0, decisions=0, score_requests=0, logical_model_ticks=0,
                  own_power_values=0, setup_power_values=0, moving_power_values=0,
                  own_trajectory_assemblies=0, logical_trajectory_requests=0,
                  logical_sinr_values=0, logical_list_sorts=0, moving_peer_ticks=0,
                  forecast_lead_pair_comparisons=0, decision_current_users=0,
                  decision_visible_peers=0, decision_matched_peers=0, decision_moving_peers=0,
                  native_dense_power_slots=0,
                  pair_gates=0, adjacent_updates=0, visible_rows=0, previous_visible_rows=0, matched_rows=0,
                  moving_rows=0, missing_rows=0, ambiguous_rows=0, new_or_unreachable_rows=0,
                  accepted_association_errors=0, decoded_peer_max_error_m=0.,
                  decoded_user_max_error_m=0., scored_moving_events=0,
                  score_changed_events=0, argmax_changed_events=0, action_changed_events=0,
                  physical_changed_events=0, command_alias_events=0,
                  max_score_perturbation=0., score_l1_perturbation_sum=0.,
                  next_persistent_rows=0, next_stopped_rows=0, next_reversed_rows=0,
                  next_other_rows=0, fallback_decisions=0)
    worker = {k: np.zeros(5, dtype=np.int64) for k in (
        'ingests', 'decisions', 'trajectories', 'model_ticks', 'candidate_link_evaluations',
        'setup_link_evaluations', 'objective_reductions', 'fallback_decisions',
        'calibration_discrepancy_rows', 'adjacent_updates', 'pair_gates', 'matched_rows',
        'moving_rows', 'moving_peer_ticks', 'moving_link_evaluations')}
    for t in range(horizon+1):
        progress['current'].update(tick=t, actor=None, stage='native_reconstruction')
        radio = native_radio(data['positions'][t], data['users'], t, progress=progress)
        counts['native_dense_power_slots'] += 275
        close(data['observations'][t], radio['obs'], f'local observation t={t}', exact=True)
        if t:
            close(data['positions'][t], np.clip(data['positions'][t-1]+30*data['commands'][t-1], LOW, HIGH),
                  f'native movement t={t}', exact=True)
            close(data['connections'][t-1], radio['connections'], 'native association', exact=True)
            close(data['native_sinr'][t-1], radio['sinr'], 'native user radio')
            close(data['served'][t-1], radio['served'], 'native served', exact=True)
            close(data['quality'][t-1], radio['quality'], 'native Q')
            close(data['reward'][t-1], radio['J'], 'native J')
            close(data['agent_rewards'][t-1], np.full(5, radio['J']/5), 'per-agent native reward')
        if t == horizon:
            break
        for i in range(5):
            progress['current'].update(actor=i, stage='actor_checks')
            own, users, sinr, peers = decode(data['observations'][t, i])
            n, p = len(users), len(peers)
            matches, delta, gates = match_frames(peers, previous[i])
            moving = np.any(delta != 0, axis=1)
            m = int(moving.sum())
            counts['ingests'] += 1
            counts['pair_gates'] += p*len(previous[i])
            counts['adjacent_updates'] += int(t > 0)
            counts['visible_rows'] += p
            counts['previous_visible_rows'] += len(previous[i])
            counts['matched_rows'] += int((matches >= 0).sum())
            counts['moving_rows'] += m
            counts['missing_rows'] += max(0, len(previous[i])-len(set(matches[matches >= 0])))
            counts['ambiguous_rows'] += int(((matches < 0) & (gates > 0)).sum())
            counts['new_or_unreachable_rows'] += int((gates == 0).sum())
            ids = radio['peer_ids'][i]
            if p:
                counts['decoded_peer_max_error_m'] = max(counts['decoded_peer_max_error_m'],
                    float(np.linalg.norm(peers-data['positions'][t, ids], axis=1).max()))
            if n:
                counts['decoded_user_max_error_m'] = max(counts['decoded_user_max_error_m'],
                    float(np.linalg.norm(users-data['users'][radio['user_ids'][i]], axis=1).max()))
            for k, old in enumerate(matches):
                if old >= 0:
                    counts['accepted_association_errors'] += int(ids[k] != previous_ids[i][old])
            close(data['n'][t, i], n, 'n', exact=True)
            close(data['p'][t, i], p, 'p', exact=True)
            padded_matches, padded_delta, padded_gates = np.full(4, -1), np.zeros((4, 3)), np.zeros(4, int)
            if arm != 'C':
                padded_matches[:p], padded_delta[:p], padded_gates[:p] = matches, delta, gates
            close(data['m'][t, i], m if arm != 'C' else 0, 'm', exact=True)
            close(data['matches'][t, i], padded_matches, 'matches', exact=True)
            close(data['delta'][t, i], padded_delta, 'delta', exact=True)
            close(data['gate_counts'][t, i], padded_gates, 'gates', exact=True)
            close(data['nav_before'][t, i], nav[i], 'entering navigation', exact=True)
            worker['ingests'][i] += 1
            if arm != 'C':
                worker['adjacent_updates'][i] += int(t > 0)
                worker['pair_gates'][i] += p*len(previous[i])
                worker['matched_rows'][i] += int((matches >= 0).sum())
                worker['moving_rows'][i] += m
            if t % 4 == 0:
                progress['current']['stage'] = 'score_setup'
                prepared = prepare_score(own, users, sinr, peers, progress=progress)
                progress['current']['stage'] = 'actual_ranking'
                actual = ranking(prepared, delta, {'C': 0, 'V': 1, 'R': -1}[arm], nav[i], progress=progress)
                if arm != 'C':
                    progress['current']['stage'] = 'stationary_shadow'
                    shadow = ranking(prepared, delta, 0, nav[i], progress=progress)
                else:
                    shadow = actual
                counts['decisions'] += 1
                counts['score_requests'] += 1+(arm != 'C')
                counts['logical_model_ticks'] += 108*(1+(arm != 'C'))
                counts['own_trajectory_assemblies'] += 27
                counts['logical_trajectory_requests'] += 27*(1+(arm != 'C'))
                counts['logical_sinr_values'] += 108*(1+p)*n*(1+(arm != 'C'))
                counts['logical_list_sorts'] += 108*(1+p)*(1+(arm != 'C'))
                counts['moving_peer_ticks'] += 4*m if arm != 'C' and n else 0
                counts['forecast_lead_pair_comparisons'] += 12*p
                counts['decision_current_users'] += n
                counts['decision_visible_peers'] += p
                counts['decision_matched_peers'] += int((matches >= 0).sum())
                counts['decision_moving_peers'] += m
                counts['own_power_values'] += 108*n
                counts['setup_power_values'] += (1+p)*n
                counts['moving_power_values'] += actual['moving_powers']
                counts['fallback_decisions'] += int(actual['fallback'])
                counts['scored_moving_events'] += int(n > 0 and m > 0)
                perturb = actual['scores']-shadow['scores']
                score_changed = bool(np.any(perturb != 0))
                argmax_changed = actual['argmax'] != shadow['argmax']
                action_changed = actual['choice'] != shadow['choice']
                # Physical aliases use evaluator-only exact native own coordinates.
                physical = np.broadcast_to(data['positions'][t, i], (2, 3)).copy()
                physical_paths = []
                alternatives = COMMANDS[[actual['choice'], shadow['choice']]]
                for _ in range(4):
                    physical = np.clip(physical+30*alternatives, LOW, HIGH)
                    physical_paths.append(physical.copy())
                physical_paths = np.asarray(physical_paths)
                physical_changed = not np.array_equal(physical_paths[:, 0], physical_paths[:, 1])
                for name, value in dict(score_changed_events=score_changed,
                        argmax_changed_events=argmax_changed, action_changed_events=action_changed,
                        physical_changed_events=physical_changed,
                        command_alias_events=action_changed and not physical_changed).items():
                    counts[name] += int(value)
                counts['max_score_perturbation'] = max(counts['max_score_perturbation'], float(np.abs(perturb).max()))
                counts['score_l1_perturbation_sum'] += float(np.abs(perturb).sum())
                progress['current']['stage'] = 'saved_score_checks'
                close(data['scores'][t//4, i], actual['scores'], 'actual 27 scores')
                close(data['candidate_service'][t//4, i], actual['served'], 'actual 27 service')
                hold[i] = COMMANDS[actual['choice']]
                nav[i], plan_choice[i], plan_fallback[i] = actual['nav'], actual['choice'], actual['fallback']
                worker['decisions'][i] += 1
                worker['trajectories'][i] += 27
                worker['model_ticks'][i] += 108
                worker['objective_reductions'][i] += 108
                worker['candidate_link_evaluations'][i] += 108*n
                worker['setup_link_evaluations'][i] += (1+p)*n
                worker['fallback_decisions'][i] += int(actual['fallback'])
                if n:
                    current_db = 10*np.log10(prepared['present'][0]/(
                        prepared['present'][1:].sum(axis=0)+prepared['unknown']+1e-8))
                    worker['calibration_discrepancy_rows'][i] += int((np.abs(current_db-sinr) > 1e-4).sum())
                if arm != 'C' and n:
                    worker['moving_peer_ticks'][i] += 4*m
                    worker['moving_link_evaluations'][i] += 4*m*n
                # All forecast errors are on this recorded path, associated by evaluator IDs.
                forecast = np.broadcast_to(peers, (3, 4, p, 3)).copy()
                for branch, sign in ((1, 1), (2, -1)):
                    loc = peers[moving].copy()
                    for lead in range(4):
                        loc = np.clip(loc+sign*delta[moving], LOW, HIGH)
                        forecast[branch, lead, moving] = loc
                for k, peer_id in enumerate(ids):
                    truth = data['positions'][t+1:t+5, peer_id]
                    e = np.linalg.norm(forecast[:, :, k]-truth[None], axis=-1)
                    flags = (True, matches[k] >= 0, moving[k], moving[k] and n > 0,
                             moving[k] and n > 0 and score_changed,
                             moving[k] and n > 0 and argmax_changed,
                             moving[k] and n > 0 and action_changed,
                             moving[k] and n > 0 and physical_changed)
                    for slice_name, enabled in zip(SLICES, flags):
                        if enabled:
                            errors[slice_name]['pairs'] += 1
                            errors[slice_name]['lead_sums'] += e
                    if matches[k] >= 0 and moving[k] and t:
                        old_command = data['commands'][t-1, peer_id]
                        new_command = data['commands'][t, peer_id]
                        category = ('persistent' if np.array_equal(old_command, new_command) else
                                    'stopped' if not new_command.any() else
                                    'reversed' if np.array_equal(new_command, -old_command) else 'other')
                        counts[f'next_{category}_rows'] += 1
            elif nav[i] == -1:
                raise ValueError('navigation not initialized at first decision')
            close(data['commands'][t, i], hold[i], 'selected/held command', exact=True)
            close(data['selected_index'][t, i], plan_choice[i], 'selected index', exact=True)
            close(data['fallback'][t, i], plan_fallback[i], 'fallback', exact=True)
            close(data['nav_after'][t, i], nav[i], 'navigation evolution', exact=True)
            previous[i], previous_ids[i] = peers, ids
    # Core C has extra history-only counters fixed at zero, all are checked as well.
    progress['current'].update(actor=None, stage='counter_audit')
    keys = data['counter_keys'].tolist()
    require(len(keys) == len(set(keys)) and data['counters'].shape == (5, len(keys)), 'counter inventory')
    worker['link_evaluations'] = (worker['candidate_link_evaluations'] + worker['setup_link_evaluations']
                                  + worker['moving_link_evaluations'])
    for key in keys:
        expected = worker.get(key, np.zeros(5, dtype=np.int64))
        close(data['counters'][:, keys.index(key)], expected, f'worker counter {key}', exact=True)
    require(set(worker)-{'adjacent_updates', 'pair_gates', 'matched_rows', 'moving_rows',
                        'moving_peer_ticks', 'moving_link_evaluations'} <= set(keys), 'missing core counts')
    if arm != 'C':
        require(set(worker) <= set(keys), 'missing motion counts')
    association_rates = dict(
        default_velocity_per_visible_row=(counts['visible_rows']-counts['matched_rows'])/max(counts['visible_rows'], 1),
        ambiguous_per_visible_row=counts['ambiguous_rows']/max(counts['visible_rows'], 1),
        missing_per_previous_row=counts['missing_rows']/max(counts['previous_visible_rows'], 1),
        accepted_error_per_matched_row=counts['accepted_association_errors']/max(counts['matched_rows'], 1))
    result = dict(arm=arm, seed=seed, endpoint=endpoint(data), counts=counts,
                association_rates=association_rates,
                worker_counts={k: int(data['counters'][:, j].sum()) for j, k in enumerate(keys)},
                forecast_errors=error_reading(errors))
    progress['episodes_completed'] += 1
    progress['completed_episode_keys'].append(dict(arm=arm, seed=seed))
    progress['current']['stage'] = 'episode_complete'
    return result, errors


def paired(rows):
    by_key = {(r['arm'], r['seed']): r for r in rows}
    require(len(by_key) == 96 and len(rows) == 96, 'requires complete 96-row inventory')
    require(set(by_key) == {(a, s) for a in ARMS for s in SEEDS}, 'fixed panel differs')
    result = {}
    for candidate, baseline in (('R', 'C'), ('V', 'C'), ('R', 'V')):
        metrics = {}
        for name in rows[0]['endpoint']:
            if name == 'per_uav_path_length_m':
                continue
            values = np.array([by_key[candidate, s]['endpoint'][name]-
                               by_key[baseline, s]['endpoint'][name] for s in SEEDS])
            mean = float(values.mean())
            item = dict(signed_world_differences=values.tolist(), mean=mean,
                        median=float(np.median(values)), minimum=float(values.min()), maximum=float(values.max()),
                        positive=int((values > 0).sum()), negative=int((values < 0).sum()),
                        exactly_equal=int((values == 0).sum()))
            if name in ('J', 'mean_served'):
                half_width = 2.0395134463964077*float(values.std(ddof=1))/np.sqrt(32)
                item.update(descriptive_t95_df31=[mean-half_width, mean+half_width])
            metrics[name] = item
        result[f'{candidate}-{baseline}'] = metrics
    return result


def read_panel(out, config, episodes, *, progress=None):
    wall, cpu = time.perf_counter(), time.process_time()
    if progress is None:
        progress = new_progress()
    require(config['seeds'] == list(SEEDS) and config['horizon'] == HORIZON
            and config['arms'] == list(ARMS) and config['orders'] == [list(o) for o in ORDERS], 'fixed config')
    require(config['started_fits'] == config['optimizer_calls'] == config['training_labels'] == 0,
            'fixed programs require zero fits, optimizer calls and labels')
    expected_order = [(a, s) for j, s in enumerate(SEEDS) for a in ORDERS[j % 6]]
    require([(r['arm'], r['seed']) for r in episodes] == expected_order, 'collection order/inventory differs')
    all_errors = {a: empty_errors() for a in ARMS}
    rows, geometries = [], {}
    for episode in episodes:
        progress['current'] = dict(arm=episode['arm'], seed=episode['seed'], tick=None,
                                   actor=None, stage='raw_hash_and_load')
        name = f"{episode['arm']}_{episode['seed']}.npz"
        path = Path(out)/'raw'/name
        actual_identity = identity(path)
        for field in ('sha256', 'bytes'):
            require(actual_identity[field] == episode['raw'][field], f'raw identity differs {name}')
        with np.load(path, allow_pickle=False) as saved:
            data = {k: saved[k] for k in saved.files}
        close(data['seed'], episode['seed'], 'seed locator', exact=True)
        require(str(data['arm']) == episode['arm'], 'arm locator')
        row, errors = read_episode(data, progress=progress)
        progress['current']['stage'] = 'panel_pairing_checks'
        require(row['worker_counts'] == episode['controller_counts'], 'episode/worker counts differ')
        geometry = (data['positions'][0].tobytes(), data['users'].tobytes())
        seed = episode['seed']
        if seed in geometries:
            require(geometry == geometries[seed], 'unpaired initial geometry')
        else:
            require(geometry not in geometries.values(), 'duplicate world geometry')
            geometries[seed] = geometry
        row['raw'] = actual_identity
        rows.append(row)
        for key in SLICES:
            all_errors[row['arm']][key]['pairs'] += errors[key]['pairs']
            all_errors[row['arm']][key]['lead_sums'] += errors[key]['lead_sums']
    totals = {}
    for key in rows[0]['counts']:
        totals[key] = (max(r['counts'][key] for r in rows) if key.startswith(('max_', 'decoded_'))
                       else sum(r['counts'][key] for r in rows))
    require(totals['ingests'] == 122880 and totals['decisions'] == 30720
            and totals['score_requests'] == 51200 and totals['logical_model_ticks'] == 5529600,
            'complete reader work counts differ')
    power_total = sum(totals[k] for k in ('own_power_values', 'setup_power_values',
                                        'moving_power_values', 'native_dense_power_slots'))
    require(power_total <= 82663200, 'reader declared power ceiling exceeded')
    progress['current'] = dict(arm=None, seed=None, tick=None, actor=None, stage='panel_aggregate_checks')
    incurred = progress['counts']
    require(progress['episodes_completed'] == len(rows)
            and incurred['score_requests_completed'] == incurred['score_requests_attempted'] == totals['score_requests']
            and incurred['logical_model_ticks_completed'] == incurred['logical_model_ticks_attempted'] == totals['logical_model_ticks']
            and incurred['native_dense_power_slots_completed'] == totals['native_dense_power_slots']
            and incurred['controller_power_values_completed'] == (
                totals['own_power_values']+totals['setup_power_values']+totals['moving_power_values']),
            'complete progress/work counts differ')
    contrasts = paired(rows)
    progress['status'] = 'complete'
    return dict(status='complete', primary='R-C full-episode mean native J', rows=rows,
                contrasts=contrasts, counts=totals, power_slots=power_total, progress=progress,
                forecast_errors={a: error_reading(e) for a, e in all_errors.items()},
                telemetry=resources(wall, cpu),
                reuse_scope='own trajectories, own powers, present powers and calibration within each decision',
                deployment_savings_claimed=False,
                association_scope='errors counted, never used to filter actor actions or native endpoints')


def main():
    parser = argparse.ArgumentParser(description='Independently verify one complete saved C/V/R panel')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    import json
    wall, cpu = time.perf_counter(), time.process_time()
    progress = new_progress()
    try:
        config = json.loads((args.out/'config.json').read_text())
        status = json.loads((args.out/'worker-status.json').read_text())
        require(status['status'] == 'complete', 'worker is incomplete')
        reading = read_panel(args.out, config, status['episodes'], progress=progress)
        write_json(args.out/'reading.json', reading)
        write_json(args.out/'reader-status.json', dict(status='complete', progress=progress,
                   reading=identity(args.out/'reading.json'), telemetry=resources(wall, cpu)))
    except BaseException as exc:
        progress['status'] = 'incomplete'
        write_json(args.out/'reader-status.json', dict(status='failed', progress=progress,
                   error=f'{type(exc).__name__}: {exc}', telemetry=resources(wall, cpu)))
        raise


if __name__ == '__main__':
    main()
