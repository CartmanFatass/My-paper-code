"""Complete native R/S/T collection with distinct suggestions and actual actions."""

import json
import os
from pathlib import Path
import resource
import time
import traceback

import numpy as np
from scipy.stats import t as student_t

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.protocol import (
    ALL_ON, HIGH, HORIZON, LOW, N, U, encode_map, mask_array,
)
from experiments.candidates.uav_radio_activation.b01.scheduler import Scheduler as RetainedScheduler
from experiments.candidates.uav_radio_activation.b01.study import (
    episode_metrics as old_metrics, factory, file_identity, write_json,
)
from .scheduler import Scheduler


SEED, WORLDS = 29306000, 64
ARMS = ('R', 'S', 'T')
ARM_ORDERS = (('R', 'S', 'T'), ('S', 'T', 'R'), ('T', 'R', 'S'),
              ('R', 'T', 'S'), ('T', 'S', 'R'), ('S', 'R', 'T'))
CPU_LIMIT_SECONDS = 10800.0


class ResourceLimit(Exception):
    pass


def check_cpu():
    if time.process_time() >= CPU_LIMIT_SECONDS:
        raise ResourceLimit('three CPU-hour native-worker ceiling reached')


def block_positions(position, commands):
    position = np.array(position, dtype=np.float64, copy=True)
    states = []
    for _ in range(4):
        position = np.clip(position + commands * 30.0, LOW, HIGH)
        states.append(position.copy())
    return np.array(states)


def episode_metrics(raw, steps, arm):
    result = old_metrics(raw, steps)
    rounds = int(raw['round_count'])
    result['fallback_decisions'] = int(raw['fallback'][:steps][raw['c_decision'][:steps]].sum())
    result.update(c_wall_seconds=float(raw['c_wall'].sum()),
                  c_cpu_seconds=float(raw['c_cpu'].sum()),
                  candidate_requests=int(raw['candidate_requests'][:rounds].sum()),
                  prefix_ticks=int(raw['prefix_ticks'][:rounds].sum()),
                  proposal_command_edits=0, executed_block_edits=0, clipped_alias_edits=0,
                  selected_silent_to_active=0)
    if arm != 'R':
        for index in range(rounds):
            tick = int(raw['round_tick'][index])
            if not raw['timely'][index] or tick + 8 > steps:
                continue
            member = (tick // 4) % N
            proposal = raw['proposals'][tick]
            committed = raw['commitments'][index]
            edited = bool(np.any(proposal[member] != committed[member]))
            expected_c = block_positions(raw['positions'][tick + 4], proposal)
            actual = raw['positions'][tick + 5:tick + 9]
            displacement_edit = bool(np.any(actual[:, member] != expected_c[:, member]))
            result['proposal_command_edits'] += int(edited)
            result['executed_block_edits'] += int(displacement_edit)
            result['clipped_alias_edits'] += int(edited and not displacement_edit)
            result['selected_silent_to_active'] += int(
                not (int(raw['mask'][tick]) & (1 << member))
                and bool(int(raw['applied_mask'][index]) & (1 << member)))
    return result


def allocate_raw(horizon, arm, sites, map_packet):
    rounds = horizon // 4 - (arm != 'R')
    raw = dict(
        true_sites=sites, map_packet=np.frombuffer(map_packet, dtype=np.uint8),
        observations=np.zeros((horizon + 1, N, 104), dtype=np.float32),
        positions=np.full((horizon + 1, N, 3), np.nan),
        commands=np.zeros((horizon, N, 3), dtype=np.float32),
        proposals=np.zeros((horizon, N, 3), dtype=np.float32),
        commitments=np.zeros((rounds, N, 3), dtype=np.float32),
        c_called=np.zeros(horizon, dtype=bool), c_decision=np.zeros(horizon, dtype=bool),
        c_wall=np.zeros(horizon), c_cpu=np.zeros(horizon),
        mask=np.zeros(horizon, dtype=np.uint8), reward=np.zeros(horizon),
        served=np.zeros(horizon, dtype=np.int16), quality=np.zeros(horizon),
        sinr=np.full((horizon, N, U), np.nan), connections=np.zeros((horizon, N, U), dtype=bool),
        fallback=np.zeros((horizon, N), dtype=bool),
        n_current=np.zeros((horizon, N), dtype=np.int16),
        n_visible_peers=np.zeros((horizon, N), dtype=np.int16),
        selected_index=np.full((horizon, N), -1, dtype=np.int16),
        round_tick=np.full(rounds, -1), report_packets=np.zeros((rounds, N, 24), dtype=np.uint8),
        command_packets=np.zeros((rounds, 16), dtype=np.uint8),
        timely=np.zeros(rounds, dtype=bool), selected_mask=np.full(rounds, -1),
        selected_q=np.full(rounds, -1), applied_mask=np.full(rounds, -1),
        round_bytes=np.zeros(rounds, dtype=int), candidate_plans=np.zeros(rounds, dtype=int),
        candidate_requests=np.zeros(rounds, dtype=int), state_reductions=np.zeros(rounds, dtype=int),
        geometry_snapshots=np.zeros(rounds, dtype=int), prefix_ticks=np.zeros(rounds, dtype=int),
        scheduler_wall=np.zeros(rounds), scheduler_cpu=np.zeros(rounds),
        round_count=np.array(0), completed_steps=np.array(0),
    )
    if arm == 'R':
        raw.update(forecast=np.full((rounds, 4, N, 3), np.nan),
                   forecast_lengths=np.zeros(rounds, dtype=int),
                   candidate_scores=np.full((rounds, 32, 3), np.nan),
                   candidate_states=np.full((rounds, 32, 4, 3), np.nan),
                   candidate_order=np.full((rounds, 31), -1))
    else:
        raw.update(forecast=np.full((rounds, 27, 4, N, 3), np.nan),
                   candidate_scores=np.full((rounds, 27, 32, 3), np.nan),
                   candidate_order=np.full((rounds, 837, 2), -1),
                   sequential_pair=np.full((rounds, 2), -1),
                   sequential_score=np.full((rounds, 3), np.nan))
    return raw


def record_round(raw, arrival, tick, arm):
    index = int(raw['round_count'])
    raw['round_tick'][index] = tick
    raw['timely'][index] = arrival['timely']
    raw['selected_mask'][index] = -1 if arrival['selected_mask'] is None else arrival['selected_mask']
    raw['applied_mask'][index] = arrival['mask']
    for i, packet in enumerate(arrival['reports']):
        raw['report_packets'][index, i] = np.frombuffer(packet, dtype=np.uint8)
    if arrival['command_packet']:
        raw['command_packets'][index] = np.frombuffer(arrival['command_packet'], dtype=np.uint8)
    raw['candidate_scores'][index] = arrival['scores']
    for key in ('candidate_plans', 'state_reductions', 'geometry_snapshots'):
        raw[key][index] = arrival[key]
    raw['candidate_requests'][index] = arrival.get('candidate_requests', arrival['candidate_plans'])
    raw['scheduler_wall'][index], raw['scheduler_cpu'][index] = arrival['wall_seconds'], arrival['cpu_seconds']
    raw['round_bytes'][index] = arrival['recurring_bytes']
    if arm == 'R':
        length = len(arrival['forecast'])
        raw['forecast_lengths'][index] = length
        raw['forecast'][index, :length] = arrival['forecast']
        raw['candidate_states'][index] = arrival['per_state']
        raw['candidate_order'][index, :len(arrival['evaluated_masks'])] = arrival['evaluated_masks']
        raw['commitments'][index] = raw['commands'][tick]
    else:
        raw['commitments'][index] = arrival['commands']
        raw['selected_q'][index] = -1 if arrival['selected_q'] is None else arrival['selected_q']
        raw['forecast'][index] = arrival['forecast']
        raw['prefix_ticks'][index] = arrival['prefix_ticks']
        order = arrival['evaluated_pairs']
        if order:
            raw['candidate_order'][index, :len(order)] = order
        if arrival.get('sequential_pair') is not None:
            raw['sequential_pair'][index] = arrival['sequential_pair']
            raw['sequential_score'][index] = arrival['sequential_score']
    raw['round_count'][...] = index + 1


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    scheduler_type=Scheduler, retained_type=RetainedScheduler,
                    controller_type=LocalController):
    if arm not in ARMS or horizon < 8 or horizon % 4:
        raise ValueError('R/S/T require complete four-tick blocks and at least eight ticks')
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect observation or non-all-on reset')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    scheduler = retained_type('E', map_packet) if arm == 'R' else scheduler_type(arm, map_packet)
    controllers = [controller_type(history=False) for _ in range(N)]
    raw = allocate_raw(horizon, arm, sites, map_packet)
    raw['positions'][0] = np.array(reset_info['state_info']['uav_positions'], copy=True)
    raw['observations'][0] = obs
    actual = np.zeros((N, 3), dtype=np.float32)
    proposals = actual.copy()
    current_mask, pending, pairs = ALL_ON, None, None
    failure = None
    try:
        for tick in range(horizon):
            check_cpu()
            reporting = tick % 4 == 0 and (arm == 'R' or tick + 4 < horizon)
            c_start, c_cpu = time.perf_counter(), time.process_time()
            if arm == 'R' or reporting:
                pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
                proposals = np.array([pair[0] for pair in pairs], dtype=np.float32)
                raw['c_called'][tick] = True
                raw['c_decision'][tick] = tick % 4 == 0
                raw['c_wall'][tick], raw['c_cpu'][tick] = time.perf_counter() - c_start, time.process_time() - c_cpu
            if arm == 'R' or tick == 0:
                actual = proposals.copy()
            raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, current_mask
            for key in ('fallback', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            raw['n_current'][tick] = (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1)
            raw['n_visible_peers'][tick] = (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1)
            if reporting:
                if arm == 'R':
                    pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), tick, current_mask)
                else:
                    pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                               current_mask, started=c_start, cpu_started=c_cpu)
                record_round(raw, pending, tick, arm)
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            global_info = info['infos_dict']['uav_0']['global']
            # Arrival mutates radio arrays in place: first preserve the completed transition.
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            connected = np.array(global_info['connections'], dtype=bool, copy=True)
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected] - 3) / 30, 0, 1).sum() / max(served, 1))
            reward = sum(float(x) for x in info['rewards_dict'].values())
            if not np.isclose(reward, .7 * served / U + .3 * quality, atol=1e-12, rtol=0):
                raise RuntimeError('native reward disagrees with preserved transition')
            raw['sinr'][tick], raw['connections'][tick] = sinr, connected
            raw['served'][tick], raw['quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['positions'][tick + 1] = np.array(info['state_info']['uav_positions'], copy=True)
            raw['completed_steps'][...] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == horizon):
                raise RuntimeError('unexpected native terminal boundary')
            arrival_due = (arm == 'R' and reporting) or (arm != 'R' and (tick + 1) % 4 == 0)
            if pending is not None and arrival_due:
                current_mask = pending['mask']
                if arm != 'R':
                    actual = np.array(pending['commands'], dtype=np.float32, copy=True)
                env.env.set_transmitter_mask(mask_array(current_mask))
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                pending = None
            obs = next_obs
            raw['observations'][tick + 1] = obs
    except Exception as exc:
        failure = exc
    finally:
        counter_keys = tuple(controllers[0].counters)
        raw['controller_counter_keys'] = np.array(counter_keys)
        raw['controller_counts'] = np.array([sum(c.counters[key] for c in controllers) for key in counter_keys])
        path = Path(out) / 'raw' / f'{arm}_{seed}.npz'
        np.savez_compressed(path, **raw)
    if failure is not None:
        raise failure
    counts['complete_episodes'] += 1
    return dict(arm=arm, seed=seed, steps=horizon, **episode_metrics(raw, horizon, arm),
                controller_counts=dict(zip(counter_keys, raw['controller_counts'].tolist())),
                wall_seconds=time.perf_counter() - wall_start, cpu_seconds=time.process_time() - cpu_start,
                raw=file_identity(path))


def paired_reading(rows, seeds):
    by_key = {(row['arm'], row['seed']): row for row in rows}
    if len(by_key) != len(rows) or any((arm, seed) not in by_key for arm in ARMS for seed in seeds):
        raise ValueError('paired reading requires every complete R/S/T world')
    metrics = ('J', 'mean_served', 'mean_quality', 'service_p10', 'min_served', 'zero_service_steps',
               'longest_zero_service', 'mean_path_length_m', 'xy_boundary_uav_steps', 'fallback_decisions',
               'mean_visible_users', 'mean_visible_peers', 'transmitter_on_ticks', 'mask_flips',
               'scheduler_cpu_seconds', 'cpu_seconds', 'recurring_bytes', 'deadline_misses')
    comparisons = {}
    for first, second in (('S', 'R'), ('T', 'R'), ('T', 'S')):
        result = {}
        for key in metrics:
            delta = np.array([by_key[first, seed][key] - by_key[second, seed][key] for seed in seeds])
            mean = float(delta.mean())
            half = (float(student_t.ppf(.975, len(seeds) - 1) * delta.std(ddof=1) / np.sqrt(len(seeds)))
                    if len(seeds) > 1 else None)
            result[key] = dict(mean=mean, differences=delta.tolist(),
                               descriptive_t95=[mean - half, mean + half] if half is not None else None,
                               positive=int((delta > 0).sum()), negative=int((delta < 0).sum()),
                               zero=int((delta == 0).sum()))
        comparisons[f'{first}-{second}'] = result
    return dict(seeds=list(seeds), comparisons=comparisons,
                unit='paired reset world conditional on realized host/load/deadlines; zero training inference')


def run_batch(out, launch_sha, *, make_env=factory, seeds=tuple(range(SEED, SEED + WORLDS)),
              horizon=HORIZON, entry_start=None):
    wall_start = time.perf_counter() if entry_start is None else entry_start
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'summary.json').exists() or (out / 'raw').exists():
        raise FileExistsError('refusing to replace scientific evidence')
    (out / 'raw').mkdir()
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, optimizer_steps=0)
    config = dict(launch_sha=launch_sha, arms=list(ARMS), seeds=list(seeds), horizon=horizon,
                  arm_orders=[list(x) for x in ARM_ORDERS], order='world index modulo six; balanced interleaved',
                  node='local_linux', compute_threads=1, cpu_limit_seconds=CPU_LIMIT_SECONDS,
                  planned_fits=0, planned_episodes=3 * len(seeds), planned_steps=3 * len(seeds) * horizon,
                  host='N5 U50 static uniform free_space no-shadowing non-FDMA 3dB cap10',
                  motion='retained C(history=False); R B01 clock, S/T four-step delayed commitments',
                  map_bytes=400, report_bytes=24, command_bytes=16, link_bits_per_second=2000,
                  max_recurring_bytes={'R': 8704, 'S': 8568, 'T': 8568},
                  deadline_seconds={'R': .456, 'S': 3.456, 'T': 3.456},
                  score='S/T: J,service,preserve Cq,more active,increasing mask,increasing COMMANDS index',
                  R_score='unchanged B01 J,service,more active,increasing mask',
                  cpu_scope='native worker process lifetime including imports/init/search/collection/output')
    summary = dict(object='UAV-RADIO-ACTIVATION-B02', status='INCOMPLETE', launch_sha=launch_sha,
                   config=config, counts=counts, rows=[], failure=None,
                   scientific_invocation=make_env is factory and tuple(seeds) == tuple(range(SEED, SEED + WORLDS))
                   and horizon == HORIZON)
    write_json(out / 'config.json', config)
    write_json(out / 'summary.json', summary)
    env = None
    try:
        check_cpu()
        env = make_env(seeds[0])
        counts['constructors'] += 1
        for index, seed in enumerate(seeds):
            for arm in ARM_ORDERS[index % 6]:
                summary['rows'].append(collect_episode(env, arm, seed, out, counts, horizon=horizon))
                write_json(out / 'summary.json', summary)
                print(json.dumps(dict(arm=arm, seed=seed, complete_episodes=counts['complete_episodes'],
                                      team_steps=counts['team_steps'], cpu_seconds=time.process_time())), flush=True)
        check_cpu()
        summary['paired'] = paired_reading(summary['rows'], seeds)
        summary['status'] = 'COMPLETE'
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_RESOURCE_LIMIT' if isinstance(exc, ResourceLimit) else 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['failure'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        if env is not None:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary['resources'] = dict(wall_seconds=time.perf_counter() - wall_start,
                                    user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime,
                                    process_cpu_seconds=usage.ru_utime + usage.ru_stime,
                                    peak_rss_kib=usage.ru_maxrss, rss_scope='native-worker process lifetime peak',
                                    thread_environment={name: os.environ.get(name) for name in
                                        ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})
        summary['artifacts'] = [file_identity(path) for path in sorted((out / 'raw').glob('*.npz'))]
        write_json(out / 'summary.json', summary)
    return summary
