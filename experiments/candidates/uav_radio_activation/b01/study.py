"""Native closed-loop collection; truth is confined to provisioning and recording."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time
import traceback

import numpy as np
from scipy.stats import t as student_t

from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .protocol import ALL_ON, HORIZON, N, SEED, U, WORLDS, encode_map, mask_array
from .scheduler import Scheduler


ARMS = ('A', 'G', 'E')
ARM_ORDERS = (('A', 'G', 'E'), ('G', 'E', 'A'), ('E', 'A', 'G'),
              ('A', 'E', 'G'), ('E', 'G', 'A'), ('G', 'A', 'E'))
CPU_LIMIT_SECONDS = 3600.0


class ResourceLimit(Exception):
    pass


def check_cpu():
    if time.process_time() >= CPU_LIMIT_SECONDS:
        raise ResourceLimit('one CPU-hour batch ceiling reached')


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def file_identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=str(path.resolve()), bytes=path.stat().st_size, sha256=digest.hexdigest())


def factory(seed):
    def masked_base(**kwargs):
        return MultiUAVEnv(enable_transmitter_mask=True, **kwargs)
    return make_real(seed, base_class=masked_base)


def longest_true(values):
    longest = current = 0
    for value in values:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def episode_metrics(raw, steps):
    served = raw['served'][:steps]
    reward = raw['reward'][:steps]
    quality = raw['quality'][:steps]
    position = raw['positions'][:steps + 1]
    mask = raw['mask'][:steps]
    round_count = int(raw['round_count'])
    decision = np.arange(steps) % 4 == 0
    active = np.array([int(m).bit_count() for m in mask])
    timely = raw['timely'][:round_count]
    xy = position[1:, :, :2]
    return dict(
        J=float(reward.mean()), return_sum=float(reward.sum()),
        mean_served=float(served.mean()), mean_quality=float(quality.mean()),
        min_served=int(served.min()), zero_service_steps=int((served == 0).sum()),
        longest_zero_service=longest_true(served == 0),
        service_p10=float(np.quantile(served, .1)),
        mean_path_length_m=float(np.linalg.norm(np.diff(position, axis=0), axis=-1).sum(axis=0).mean()),
        xy_boundary_uav_steps=int(np.any((xy <= 1e-3) | (xy >= 1000 - 1e-3), axis=-1).sum()),
        lower_altitude_uav_steps=int((position[1:, :, 2] <= 50.001).sum()),
        fallback_decisions=int(raw['fallback'][:steps][decision].sum()),
        fallback_uav_steps=int(raw['fallback'][:steps].sum()),
        mean_visible_users=float(raw['n_current'][:steps].mean()),
        mean_visible_peers=float(raw['n_visible_peers'][:steps].mean()),
        empty_discovery_uav_steps=int((raw['n_current'][:steps] == 0).sum()),
        transmitter_on_ticks=int(active.sum()), mean_active_transmitters=float(active.mean()),
        all_on_steps=int((mask == ALL_ON).sum()),
        mask_flips=int(sum((int(a) ^ int(b)).bit_count() for a, b in zip(mask[:-1], mask[1:]))),
        report_rounds=round_count, deadline_misses=int((~timely).sum()),
        recurring_bytes=int(raw['round_bytes'][:round_count].sum()), preinstalled_map_bytes=400,
        candidate_plans=int(raw['candidate_plans'][:round_count].sum()),
        state_reductions=int(raw['state_reductions'][:round_count].sum()),
        geometry_snapshots=int(raw['geometry_snapshots'][:round_count].sum()),
        scheduler_wall_seconds=float(raw['scheduler_wall'][:round_count].sum()),
        scheduler_cpu_seconds=float(raw['scheduler_cpu'][:round_count].sum()),
        max_scheduler_wall_seconds=float(raw['scheduler_wall'][:round_count].max()) if round_count else 0.0,
    )


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON, scheduler_type=Scheduler):
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect N5 observation or non-all-on reset')
    # Registered sites are provisioned once; these truth copies never enter C or a round report.
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    scheduler = scheduler_type(arm, map_packet) if arm != 'A' else None
    controllers = [LocalController(history=False) for _ in range(N)]
    rounds = (horizon + 3) // 4
    raw = dict(
        true_sites=sites, map_packet=np.frombuffer(map_packet, dtype=np.uint8),
        observations=np.zeros((horizon + 1, N, 104), dtype=np.float32),
        positions=np.full((horizon + 1, N, 3), np.nan),
        commands=np.zeros((horizon, N, 3), dtype=np.float32),
        mask=np.zeros(horizon, dtype=np.uint8), reward=np.zeros(horizon),
        served=np.zeros(horizon, dtype=np.int16), quality=np.zeros(horizon),
        sinr=np.full((horizon, N, U), np.nan),
        connections=np.zeros((horizon, N, U), dtype=bool),
        fallback=np.zeros((horizon, N), dtype=bool),
        n_current=np.zeros((horizon, N), dtype=np.int16),
        n_visible_peers=np.zeros((horizon, N), dtype=np.int16),
        selected_index=np.zeros((horizon, N), dtype=np.int16),
        round_tick=np.full(rounds, -1), report_packets=np.zeros((rounds, N, 24), dtype=np.uint8),
        command_packets=np.zeros((rounds, 16), dtype=np.uint8),
        timely=np.zeros(rounds, dtype=bool), selected_mask=np.full(rounds, -1),
        applied_mask=np.full(rounds, -1), round_bytes=np.zeros(rounds, dtype=int),
        forecast=np.full((rounds, 4, N, 3), np.nan), forecast_lengths=np.zeros(rounds, dtype=int),
        candidate_scores=np.full((rounds, 32, 3), np.nan),
        candidate_states=np.full((rounds, 32, 4, 3), np.nan),
        candidate_order=np.full((rounds, 31), -1), candidate_plans=np.zeros(rounds, dtype=int),
        state_reductions=np.zeros(rounds, dtype=int), geometry_snapshots=np.zeros(rounds, dtype=int),
        scheduler_wall=np.zeros(rounds), scheduler_cpu=np.zeros(rounds),
        round_count=np.array(0), completed_steps=np.array(0),
    )
    raw['positions'][0] = np.array(reset_info['state_info']['uav_positions'], copy=True)
    raw['observations'][0] = obs
    current_mask = ALL_ON
    failure = None
    try:
        for tick in range(horizon):
            check_cpu()
            pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
            commands = np.array([pair[0] for pair in pairs], dtype=np.float32)
            raw['commands'][tick] = commands
            raw['mask'][tick] = current_mask
            for key in ('fallback', 'n_current', 'n_visible_peers', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            arrival = None
            if scheduler is not None and tick % 4 == 0:
                arrival = scheduler.decide(obs[:, :3].copy(), commands.copy(), tick, current_mask)
                index = int(raw['round_count'])
                raw['round_tick'][index] = tick
                raw['timely'][index] = arrival['timely']
                raw['selected_mask'][index] = -1 if arrival['selected_mask'] is None else arrival['selected_mask']
                raw['applied_mask'][index] = arrival['mask']
                for i, packet in enumerate(arrival['reports']):
                    raw['report_packets'][index, i] = np.frombuffer(packet, dtype=np.uint8)
                if arrival['command_packet']:
                    raw['command_packets'][index] = np.frombuffer(arrival['command_packet'], dtype=np.uint8)
                length = len(arrival['forecast'])
                raw['forecast_lengths'][index] = length
                raw['forecast'][index, :length] = arrival['forecast']
                raw['candidate_scores'][index] = arrival['scores']
                raw['candidate_states'][index] = arrival['per_state']
                raw['candidate_order'][index, :len(arrival['evaluated_masks'])] = arrival['evaluated_masks']
                for key in ('candidate_plans', 'state_reductions', 'geometry_snapshots'):
                    raw[key][index] = arrival[key]
                raw['scheduler_wall'][index] = arrival['wall_seconds']
                raw['scheduler_cpu'][index] = arrival['cpu_seconds']
                raw['round_bytes'][index] = arrival['recurring_bytes']
                raw['round_count'][...] = index + 1
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, next_info = env.step(commands)
            counts['team_steps'] += 1
            global_info = next_info['infos_dict']['uav_0']['global']
            # The environment updates SINR in place at arrival: preserve this transition first.
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            connections = np.array(global_info['connections'], dtype=bool, copy=True)
            served = int(connections.sum())
            quality = float(np.clip((sinr[connections] - 3.0) / 30.0, 0, 1).sum() / max(served, 1))
            reward = sum(float(x) for x in next_info['rewards_dict'].values())
            if not np.isclose(reward, .7 * served / U + .3 * quality, atol=1e-12, rtol=0):
                raise RuntimeError('native reward does not match preserved transition evidence')
            raw['sinr'][tick], raw['connections'][tick] = sinr, connections
            raw['served'][tick], raw['quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['positions'][tick + 1] = np.array(next_info['state_info']['uav_positions'], copy=True)
            raw['completed_steps'][...] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == horizon):
                raise RuntimeError('unexpected native terminal boundary')
            if arrival is not None:
                current_mask = arrival['mask']
                env.env.set_transmitter_mask(mask_array(current_mask))
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
            obs = next_obs
            raw['observations'][tick + 1] = obs
    except Exception as exc:
        failure = exc
    finally:
        path = Path(out) / 'raw' / f'{arm}_{seed}.npz'
        np.savez_compressed(path, **raw)
    if failure is not None:
        raise failure
    counts['complete_episodes'] += 1
    counter_keys = controllers[0].counters.keys()
    return dict(arm=arm, seed=seed, steps=horizon, **episode_metrics(raw, horizon),
                controller_counts={key: sum(c.counters[key] for c in controllers) for key in counter_keys},
                wall_seconds=time.perf_counter() - wall_start,
                cpu_seconds=time.process_time() - cpu_start, raw=file_identity(path))


def paired_reading(rows, seeds):
    by_key = {(row['arm'], row['seed']): row for row in rows}
    if len(by_key) != len(rows) or any((arm, seed) not in by_key for arm in ARMS for seed in seeds):
        raise ValueError('paired reading requires the complete three-arm panel')
    metrics = ('J', 'mean_served', 'mean_quality', 'min_served', 'zero_service_steps',
               'longest_zero_service', 'mean_path_length_m', 'xy_boundary_uav_steps',
               'fallback_decisions', 'mean_visible_users', 'mean_visible_peers',
               'transmitter_on_ticks', 'mask_flips', 'scheduler_cpu_seconds')
    comparisons = {}
    for first, second in (('G', 'A'), ('E', 'A'), ('E', 'G')):
        result = {}
        for key in metrics:
            delta = np.array([by_key[(first, seed)][key] - by_key[(second, seed)][key] for seed in seeds])
            mean = float(delta.mean())
            half = float(student_t.ppf(.975, len(seeds) - 1) * delta.std(ddof=1) / np.sqrt(len(seeds))) if len(seeds) > 1 else None
            result[key] = dict(mean=mean, differences=delta.tolist(),
                               descriptive_t95=[mean - half, mean + half] if half is not None else None,
                               positive=int((delta > 0).sum()), negative=int((delta < 0).sum()),
                               zero=int((delta == 0).sum()))
        comparisons[f'{first}-{second}'] = result
    return dict(seeds=list(seeds), comparisons=comparisons,
                unit='paired reset world, conditional on realized execution-platform deadlines; zero training inference')


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
                  arm_orders=[list(x) for x in ARM_ORDERS], order='world-index modulo six, paired and interleaved',
                  node='local_linux', compute_threads=1, cpu_limit_seconds=CPU_LIMIT_SECONDS,
                  planned_fits=0, planned_episodes=3 * len(seeds), planned_steps=3 * len(seeds) * horizon,
                  host='N5 U50 uniform static free_space no-shadowing non-FDMA 3dB cap10',
                  motion='retained LocalController(history=False), 27 commands, four-tick hold',
                  map_bytes=400, report_bytes=24, mask_command_bytes=16, link_bits_per_second=2000,
                  max_recurring_bytes_per_episode=8704, scheduler_deadline_seconds=.456,
                  score='horizon-average native J, service, active count, increasing mask integer',
                  cpu_scope='process lifetime including imports, initialization, native collection, search and output')
    summary = dict(object='UAV-RADIO-ACTIVATION-B01', status='INCOMPLETE', launch_sha=launch_sha,
                   config=config, counts=counts, rows=[], failure=None,
                   scientific_invocation=make_env is factory and tuple(seeds) == tuple(range(SEED, SEED + WORLDS)) and horizon == HORIZON)
    write_json(out / 'config.json', config)
    write_json(out / 'summary.json', summary)
    env = None
    try:
        check_cpu()
        env = make_env(seeds[0])
        counts['constructors'] += 1
        for index, seed in enumerate(seeds):
            for arm in ARM_ORDERS[index % len(ARM_ORDERS)]:
                row = collect_episode(env, arm, seed, out, counts, horizon=horizon)
                summary['rows'].append(row)
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
                                    peak_rss_kib=usage.ru_maxrss, rss_scope='runner process lifetime peak',
                                    thread_environment={name: os.environ.get(name) for name in
                                        ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})
        summary['artifacts'] = [file_identity(path) for path in sorted((out / 'raw').glob('*.npz'))]
        write_json(out / 'summary.json', summary)
    return summary
