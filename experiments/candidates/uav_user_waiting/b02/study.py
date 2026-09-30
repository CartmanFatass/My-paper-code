"""Fixed temporal-continuity A/S/M/R comparison under the retained delayed native host."""

import json
import os
import platform
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.controller import LocalController
from .protocol import ALL_ON, HORIZON, N, U, encode_map, mask_array, DEADLINE_SECONDS
from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_service_age.b01.metrics import add_age_raw
from experiments.candidates.uav_user_waiting.b01 import study as previous_study
from .scheduler import Scheduler
from .predictor import controller_nav_index
from .storage import pack_records
from .metrics import episode_metrics, paired_reading

ROOT = Path(__file__).resolve().parents[4]
SEED, WORLDS = 29322000, 64
ARMS = ('A', 'S', 'M', 'R')
ARM_ORDERS = tuple(tuple(order[i:] + order[:i])
                   for order in (ARMS, tuple(reversed(ARMS))) for i in range(4))


def source_identities():
    existing = {row['path']: row for row in previous_study.source_identities()}
    for path in (ROOT / 'experiments/candidates/uav_user_waiting/b02').glob('*.py'):
        relative = str(path.relative_to(ROOT))
        existing[relative] = dict(file_identity(path), path=relative)
    return [existing[key] for key in sorted(existing)]


def frozen_config(launch_sha):
    return dict(object='UAV-USER-WAITING-B02', launch_sha=launch_sha,
                seeds=list(range(SEED, SEED + WORLDS)), arms=list(ARMS),
                arm_orders=[list(order) for order in ARM_ORDERS], horizon=HORIZON,
                planned_fits=0, planned_episodes=256, planned_steps=65536,
                delivery_ticks=2, hold_ticks=4, deadline_seconds=DEADLINE_SECONDS,
                report_bytes_per_uav=25, command_bytes=16, round_bytes=141,
                transmission_seconds=.564, nodes=N, users=U,
                primary='A-M: mean of50 individual maximum observed unserved gaps; lower favorable',
                actual_age='postmove service resets0; otherwise+1 from initial0',
                S='min sum of squared reconstructed per-user ages across the delivered4 ticks; native ties',
                A='two S finalists each followed by one modeled next S; min combined8-tick squared-age cost; horizon clipped; same deadline',
                M='retained minimum predicted cumulative-age selector between O and W plans, using W native tie keys',
                R='min max accumulated reconstructed age; then min total; then native ties',
                nav_contract='post-current-C index 0..9 in one common report byte; no other private state or future native C',
                continuation='virtual report at t+4 after first2 delivered transitions; resumed committed prefix reproduces t+4,t+5; next S delivered t+6..9; count Q8 each once',
                synthetic_observation='native-shaped104 float32; all top20 SINR-eligible users before capacity assignment and peers; quantized map and modeled positions',
                dtype='int64 age costs/burden; float64 radio/history/forecast',
                fallback='whole-round late or incomplete holds old commands/mask; no S rescue',
                unknown_prefix='no invented transitions; burden permanently censored if first lawful anchor>0',
                native_ties=['J','served','q==proposal_q','mask.bit_count()','-mask','-q'],
                seed_rng='native RandomState(world seed), exact inherited reset; no policy RNG',
                upper_work=dict(current_candidate_requests=2375680, future_candidate_requests=935424,
                                total_candidate_requests=3311104, candidate_state_reductions=13140480,
                                current_c_calls=81920, virtual_c_calls=40320),
                reader='all native/C/age/periodic/history/key/continuation arithmetic; selected plans and all evaluated pairs at0/60/124/248 checked physically',
                source_identities=source_identities())


def allocate_raw(horizon, arm, sites, map_packet):
    rounds = horizon // HOLD
    return dict(program=np.array(arm), true_sites=sites,
        map_packet=np.frombuffer(map_packet, dtype=np.uint8),
        observations=np.zeros((horizon + 1,N,104),dtype=np.float32),
        positions=np.full((horizon + 1,N,3),np.nan),
        commands=np.zeros((horizon,N,3),dtype=np.float32),
        proposals=np.zeros((horizon,N,3),dtype=np.float32),
        commitments=np.zeros((rounds,N,3),dtype=np.float32),
        c_called=np.zeros(horizon,dtype=bool),c_decision=np.zeros(horizon,dtype=bool),
        c_wall=np.zeros(horizon),c_cpu=np.zeros(horizon),
        post_c_nav=np.zeros((rounds,N),dtype=np.uint8),
        mask=np.zeros(horizon,dtype=np.uint8),reward=np.zeros(horizon),
        served=np.zeros(horizon,dtype=np.int16),quality=np.zeros(horizon),
        sinr=np.full((horizon,N,U),np.nan),connections=np.zeros((horizon,N,U),dtype=bool),
        fallback=np.zeros((horizon,N),dtype=bool),
        n_current=np.zeros((horizon,N),dtype=np.int16),
        n_visible_peers=np.zeros((horizon,N),dtype=np.int16),
        selected_index=np.full((horizon,N),-1,dtype=np.int16),
        round_tick=np.full(rounds,-1),report_packets=np.zeros((rounds,N,25),dtype=np.uint8),
        command_packets=np.zeros((rounds,16),dtype=np.uint8),
        command_packet_lengths=np.zeros(rounds,dtype=np.uint8),
        timely=np.zeros(rounds,dtype=bool),selected_mask=np.full(rounds,-1),
        selected_q=np.full(rounds,-1),applied_mask=np.full(rounds,-1),
        round_bytes=np.zeros(rounds,dtype=int),candidate_plans=np.zeros(rounds,dtype=int),
        candidate_requests=np.zeros(rounds,dtype=int),state_reductions=np.zeros(rounds,dtype=int),
        geometry_snapshots=np.zeros(rounds,dtype=int),prefix_ticks=np.zeros(rounds,dtype=int),
        scheduler_wall=np.zeros(rounds),scheduler_cpu=np.zeros(rounds),
        model_valid=np.zeros(horizon,dtype=bool),model_contacts=np.zeros((horizon,U),dtype=bool),
        terminal_history_complete=np.array(False),terminal_history_reductions=np.array(0),
        terminal_history_wall=np.array(0.),terminal_history_cpu=np.array(0.),
        round_count=np.array(0),completed_steps=np.array(0))


def record_round(raw, arrival, tick):
    index = int(raw['round_count'])
    record = arrival['record']
    raw['round_tick'][index] = tick
    if len(record['report_packets']):
        raw['report_packets'][index] = record['report_packets']
    packet = np.asarray(record['delivered_command_packet'], dtype=np.uint8)
    raw['command_packet_lengths'][index] = len(packet)
    raw['command_packets'][index,:len(packet)] = packet
    for key in ('timely','selected_mask','selected_q','candidate_plans','candidate_requests',
                'state_reductions','geometry_snapshots','prefix_ticks','scheduler_wall','scheduler_cpu'):
        raw[key][index] = -1 if arrival[key] is None else arrival[key]
    raw['round_bytes'][index] = arrival['recurring_bytes']
    raw['applied_mask'][index] = arrival['mask']
    raw['commitments'][index] = arrival['commands']
    raw['round_count'][...] = index + 1


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    scheduler_type=None, controller_type=LocalController):
    """Frozen delayed control loop; evaluator truth never enters the scheduler."""
    if arm not in ARMS or not 8 <= horizon <= HORIZON or horizon % 4:
        raise ValueError('complete four-tick episode horizon required')
    started, cpu_started = time.perf_counter(), time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect native observation or reset mask')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    scheduler = (scheduler_type or Scheduler)(arm, map_packet, horizon=horizon)
    controllers = [controller_type(history=False) for _ in range(N)]
    raw = allocate_raw(horizon, arm, sites, map_packet)
    raw['world_seed'] = np.array(seed)
    raw['training_episode'] = np.array(False)
    records = []
    raw['positions'][0] = np.array(reset_info['state_info']['uav_positions'], copy=True)
    raw['observations'][0] = obs
    actual = np.zeros((N, 3), dtype=np.float32)
    proposals = actual.copy()
    current_mask, pending, pending_at, pairs = ALL_ON, None, None, None
    failure = None
    try:
        for tick in range(horizon):
            reporting = tick % HOLD == 0
            c_start, c_cpu = time.perf_counter(), time.process_time()
            if reporting:
                pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
                proposals = np.array([pair[0] for pair in pairs], dtype=np.float32)
                raw['c_called'][tick] = raw['c_decision'][tick] = True
                raw['c_wall'][tick], raw['c_cpu'][tick] = time.perf_counter() - c_start, time.process_time() - c_cpu
            if tick == 0:
                actual = proposals.copy()
            raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, current_mask
            for key in ('fallback', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            raw['n_current'][tick] = (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1)
            raw['n_visible_peers'][tick] = (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1)
            if reporting:
                nav_indices = np.array([controller_nav_index(c) for c in controllers], dtype=np.uint8)
                raw['post_c_nav'][tick // HOLD] = nav_indices
                pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                           current_mask, nav_indices, started=c_start, cpu_started=c_cpu)
                pending_at = tick + DELIVERY
                record_round(raw, pending, tick)
                records.append(pending['record'])
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            scheduler.executed(tick, actual.copy(), int(current_mask))
            global_info = info['infos_dict']['uav_0']['global']
            # Arriving masks mutate radio arrays. Preserve actual postmove service first.
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            connected = np.array(global_info['connections'], dtype=bool, copy=True)
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected] - 3) / 30, 0, 1).sum() / max(served, 1))
            reward = sum(float(value) for value in info['rewards_dict'].values())
            if not np.isclose(reward, .7 * served / U + .3 * quality, atol=1e-12, rtol=0):
                raise RuntimeError('preserved actual transition disagrees with native reward')
            raw['sinr'][tick], raw['connections'][tick] = sinr, connected
            raw['served'][tick], raw['quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['positions'][tick + 1] = np.array(info['state_info']['uav_positions'], copy=True)
            raw['completed_steps'][...] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == horizon):
                raise RuntimeError('unexpected native terminal boundary')
            if pending is not None and tick + 1 == pending_at:
                current_mask = pending['mask']
                actual = np.array(pending['commands'], dtype=np.float32, copy=True)
                env.env.set_transmitter_mask(mask_array(current_mask))
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                pending, pending_at = None, None
            obs = next_obs
            raw['observations'][tick + 1] = obs
    except Exception as exc:
        failure = exc
    finally:
        wall, cpu = time.perf_counter(), time.process_time()
        before = scheduler.execution.next_unsettled
        ready = False
        try:
            _, ready = scheduler.execution.settle(int(raw['completed_steps']))
        except Exception as support_failure:
            raw['terminal_support_failure_type'] = np.array(type(support_failure).__name__)
            raw['terminal_support_failure_message'] = np.array(str(support_failure))
            if failure is None:
                failure = support_failure
        settled, start_tick = scheduler.execution.next_unsettled, scheduler.execution.start_tick
        raw['terminal_history_start'] = np.array(-1 if start_tick is None else start_tick)
        if start_tick is not None:
            raw['model_valid'][start_tick:settled] = True
        for tick, served in scheduler.execution.predicted.items():
            raw['model_contacts'][tick] = served
        raw['terminal_history_complete'][...] = ready
        raw['terminal_history_reductions'][...] = settled - before
        raw['terminal_history_wall'][...] = time.perf_counter() - wall
        raw['terminal_history_cpu'][...] = time.process_time() - cpu
        raw['terminal_last'] = scheduler.execution.history.last.copy()
        raw['terminal_windows'] = scheduler.execution.history.windows.copy()
        raw['terminal_burden'] = scheduler.execution.history.burden.copy()
        raw['terminal_burden_unknown'] = np.array(start_tick is not None and start_tick > 0)
        raw['episode_failure_type'] = np.array('' if failure is None else type(failure).__name__)
        raw['episode_failure_message'] = np.array('' if failure is None else str(failure))
        steps = int(raw['completed_steps'])
        add_contact_raw(raw, steps)
        add_age_raw(raw, steps)
        keys = tuple(controllers[0].counters)
        raw['controller_counter_keys'] = np.array(keys)
        raw['controller_counts'] = np.array([sum(c.counters[key] for c in controllers) for key in keys])
        raw.update(pack_records(records))
        if failure is not None:
            np.savez_compressed(Path(out) / 'raw' / f'{arm}_{seed}.npz', **raw)
    if failure is not None:
        raise failure
    counts['complete_episodes'] += 1
    row = dict(arm=arm, seed=seed, steps=horizon, **episode_metrics(raw, horizon, arm, records),
               controller_counts=dict(zip(keys, raw['controller_counts'].tolist())),
               wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started)
    return row, raw


def save_episode(out, row, raw):
    path = Path(out) / 'raw' / f"{row['arm']}_{row['seed']}.npz"
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **raw)
    row['raw'] = file_identity(path)
    row['storage_wall_seconds'] = time.perf_counter() - wall
    row['storage_cpu_seconds'] = time.process_time() - cpu



def run_batch(out, launch_sha, *, entry_start=None, admission=None):
    out = Path(out).resolve()
    if (out / 'config.json').exists() or (out / 'summary.json').exists():
        raise FileExistsError('result output already has scientific records; no implicit resume')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'raw').mkdir(exist_ok=True)
    started = time.perf_counter() if entry_start is None else entry_start
    cpu_started = time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = frozen_config(launch_sha)
    write_json(out / 'config.json', config)
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, optimizer_steps=0)
    summary = dict(object='UAV-USER-WAITING-B02', status='RUNNING', launch_sha=launch_sha,
                   scientific_invocation=True, config=config, counts=counts, rows=[],
                   admission=admission,
                   runtime=dict(python=platform.python_version(), numpy=np.__version__,
                                torch=torch.__version__, host=platform.node(), platform=platform.platform()))
    env = None
    try:
        env = factory(SEED)
        counts['constructors'] += 1
        env.env.max_steps = HORIZON
        for index, seed in enumerate(config['seeds']):
            for arm in ARM_ORDERS[index % len(ARM_ORDERS)]:
                row, raw = collect_episode(env, arm, seed, out, counts)
                save_episode(out, row, raw)
                summary['rows'].append(row)
                write_json(out / 'summary.json', summary)
                print(json.dumps(dict(arm=arm, seed=seed, completed=counts['complete_episodes'],
                                      steps=counts['team_steps'], gap=row['mean_user_max_unserved_gap'], A=row['A'], misses=row['deadline_misses'])), flush=True)
        summary['paired'] = paired_reading(summary['rows'], config['seeds'], ARMS)
        summary['status'] = 'COMPLETE'
        summary['fixed_policy_evaluation_counts'] = dict(episodes=256, transitions=65536,
                                                        optimizer_updates=0, parameter_updates=0)
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        if env is not None:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary['resources'] = dict(wall_seconds=time.perf_counter() - started,
                                    measured_cpu_seconds=time.process_time() - cpu_started,
                                    process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
                                    peak_rss_kib=usage.ru_maxrss, rss_scope='worker lifetime peak; Linux KiB',
                                    scope='entry wall includes imports; measured_cpu starts after study import; process CPU includes import/init',
                                    torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                                    thread_environment={key: os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
        summary['artifacts'] = [file_identity(path) for path in sorted((out / 'raw').iterdir()) if path.is_file()]
        write_json(out / 'summary.json', summary)
    return summary
