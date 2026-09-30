"""Fixed M/S/U/K service/continuity panel on the unchanged B02 collection loop."""

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
from experiments.candidates.uav_user_waiting.b02.protocol import (
    ALL_ON, HORIZON, N, U, encode_map, mask_array, DEADLINE_SECONDS,
)
from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_service_age.b01.metrics import add_age_raw
from experiments.candidates.uav_user_waiting.b02 import study as previous_study
from experiments.candidates.uav_user_waiting.b02.study import allocate_raw, record_round
from experiments.candidates.uav_user_waiting.b02.predictor import controller_nav_index
from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from .scheduler import Scheduler
from .metrics import episode_metrics, paired_reading, BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES

ROOT = Path(__file__).resolve().parents[4]
SEED, WORLDS, FIXTURE_SEED = 29426000, 64, 29426999
ARMS = ('M', 'S', 'U', 'K')
ARM_ORDERS = tuple(tuple(order[index:] + order[:index])
                   for order in (ARMS, tuple(reversed(ARMS))) for index in range(4))


def source_identities():
    existing = {row['path']: row for row in previous_study.source_identities()}
    for path in (ROOT / 'experiments/candidates/uav_user_waiting/b04').glob('*.py'):
        relative = str(path.relative_to(ROOT))
        existing[relative] = dict(file_identity(path), path=relative)
    return [existing[key] for key in sorted(existing)]


def frozen_config(launch_sha):
    return dict(object='UAV-USER-WAITING-B04', launch_sha=launch_sha,
        seeds=list(range(SEED, SEED + WORLDS)), arms=list(ARMS),
        arm_orders=[list(order) for order in ARM_ORDERS], horizon=HORIZON,
        planned_fits=0, planned_optimizer_updates=0, planned_episodes=256, planned_steps=65536,
        fixture=dict(seed=FIXTURE_SEED, horizon=8, episodes=4, native_steps=32),
        delivery_ticks=2, hold_ticks=4, deadline_seconds=DEADLINE_SECONDS,
        report_bytes_per_uav=25, command_bytes=16, round_bytes=141,
        map_bytes=400, transmission_seconds=.564, nodes=N, users=U,
        M='unchanged B02 O and W two-order searches; choose their winners by W key',
        S='unchanged B02 S two-order search; negative delivered age-square sum then native ties',
        U='same-state O/W/S unmodified searches; choose maximum S key over every distinct visited pair',
        K='same completed U pool; admit integer delivered assigned-user-tick total>=same-state M total; then same S key',
        union_order='first visit in sequential O/W/S requests with shared cache; floor never changes generation',
        terminal='delivered length=min(4,H-t-2); last report252 scores254/255 only; prefix excluded',
        native_ties=['J','served','q==proposal_q','mask.bit_count()','-mask','-q'],
        actual_age='postmove service resets0; otherwise+1 from initial0; native gaps keep boundary censoring',
        nav_contract='post-current-C index in common report byte; no future C, ACK, truth, extra actor information or learned value',
        fallback='any whole-round late, incomplete union or missing history holds old commands and mask; no M rescue',
        unknown_prefix='no invented transitions; burden permanently censored if first lawful anchor>0',
        dtype='int64 age costs and assigned-user-tick floor; float64 radio/history/forecast',
        seed_rng='native RandomState(world seed), inherited reset; no policy RNG',
        primary='K-M native mean service>=0, episode maximum gap<0, worst-user mean age<0; exploratory joint signs',
        secondary='K-U local floor; U-S expanded ordinary search; preserve all six contrasts',
        bootstrap=dict(seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES),
        upper_work=dict(candidate_requests=4276224, delivered_state_reductions=16971264,
                        prefix_transitions=32768, current_c_calls=81920, future_c_calls=0),
        reader='all native/C/age/periodic/history/contact-cost-key/path/pool/floor arithmetic; selected programs and search winners every round; all visited at0/60/124/248; same native radio kernel',
        reader_current_c_calls=163840,
        source_identities=source_identities())


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
    summary = dict(object='UAV-USER-WAITING-B04', status='RUNNING', launch_sha=launch_sha,
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
                                      steps=counts['team_steps'], maximum_gap=row['max_unserved_gap'], worst_age=row['F_user'], served=row['mean_served'], misses=row['deadline_misses'])), flush=True)
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
