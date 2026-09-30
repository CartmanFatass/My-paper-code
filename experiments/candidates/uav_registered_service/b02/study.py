"""Fixed three-arm collection with frozen O/S2 policies and private G history.

The local episode loop is needed because frozen B01 hard-codes five arms.
Storage and complete metrics reuse its helpers, with explicit G format dispatch.
"""

import itertools
import json
import os
import platform
from pathlib import Path
import resource
import time
import traceback

import numpy as np
from scipy.stats import t as student_t

from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_radio_activation.b01.protocol import ALL_ON, HORIZON, N, U, encode_map, mask_array
from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler as FrozenScheduler
from experiments.candidates.uav_registered_service.b01.scheduler import Scheduler as HistoryScheduler
from experiments.candidates.uav_registered_service.b01 import study as frozen
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from .scheduler import Scheduler as GatedScheduler
from .metrics import add_gate_raw, gate_metrics

SEED, WORLDS = 29309000, 64
ARMS = ('S2', 'O', 'G')
ARM_ORDERS = tuple(tuple(order[i:] + order[:i]) for order in (ARMS, tuple(reversed(ARMS))) for i in range(3))
GATE_FIELDS = ('gate_computed', 'gate_eligible', 'gate_released', 'gate_window', 'gate_wall', 'gate_cpu')
ROOT = Path(__file__).resolve().parents[4]


def source_identities():
    """Portable byte identities for B02 and its frozen policy/host dependencies."""
    directories = (
        'experiments/candidates/uav_registered_service/b02',
        'experiments/candidates/uav_registered_service/b01',
        'experiments/candidates/uav_radio_activation/b01',
        'experiments/candidates/uav_radio_activation/b02',
        'experiments/candidates/uav_radio_activation/b03',
    )
    paths = {p for directory in directories for p in (ROOT / directory).glob('*.py')}
    paths.update(ROOT / name for name in (
        'experiments/candidates/uav_local_history/b01/controller.py',
        'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py',
        'envs/pettingzoo/uav_env.py', 'envs/pettingzoo/uav_radio.py',
        'envs/pettingzoo/env_adapter.py', 'scripts/hmasd_admission.py',
        '.codex/hmasd-compute.toml',
    ))
    return [dict(file_identity(path), path=str(path.relative_to(ROOT))) for path in sorted(paths)]


def allocate_raw(horizon, arm, sites, map_packet):
    # G uses O's history storage contract; this is a local format choice only.
    raw = frozen.allocate_raw(horizon, 'O' if arm == 'G' else arm, sites, map_packet)
    if arm == 'G':
        rounds = horizon // HOLD
        for key in ('gate_computed', 'gate_eligible', 'gate_released'):
            raw[key] = np.zeros(rounds, dtype=bool)
        raw['gate_window'] = np.full(rounds, -1)
        raw['gate_wall'] = np.zeros(rounds)
        raw['gate_cpu'] = np.zeros(rounds)
    return raw


def record_round(raw, arrival, tick, arm):
    index = int(raw['round_count'])
    frozen.record_round(raw, arrival, tick, 'O' if arm == 'G' else arm)
    if arm == 'G':
        for key in GATE_FIELDS:
            raw[key][index] = arrival[key]


def episode_metrics(raw, steps, arm):
    result = frozen.episode_metrics(raw, steps, 'O' if arm == 'G' else arm)
    if arm == 'G':
        result.update(gate_metrics(raw, steps))
    return result


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    scheduler_type=None,
                    controller_type=LocalController):
    if arm not in ARMS or not 8 <= horizon <= HORIZON or horizon % 4:
        raise ValueError('three arms require complete four-tick blocks from8 to256')
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect observation or non-all-on reset')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    chosen_type = scheduler_type or {'O': HistoryScheduler, 'G': GatedScheduler, 'S2': FrozenScheduler}[arm]
    scheduler = chosen_type(arm, map_packet, horizon=horizon)
    controllers = [controller_type(history=False) for _ in range(N)]
    raw = allocate_raw(horizon, arm, sites, map_packet)
    raw['positions'][0] = np.array(reset_info['state_info']['uav_positions'], copy=True)
    raw['observations'][0] = obs
    actual = np.zeros((N, 3), dtype=np.float32)
    proposals = actual.copy()
    current_mask, pending, pairs = ALL_ON, None, None
    pending_at = None
    failure = None
    try:
        for tick in range(horizon):
            reporting = tick % HOLD == 0
            c_start, c_cpu = time.perf_counter(), time.process_time()
            if reporting:
                pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
                proposals = np.array([pair[0] for pair in pairs], dtype=np.float32)
                raw['c_called'][tick] = True
                raw['c_decision'][tick] = tick % 4 == 0
                raw['c_wall'][tick], raw['c_cpu'][tick] = time.perf_counter() - c_start, time.process_time() - c_cpu
            if tick == 0:
                actual = proposals.copy()
            raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, current_mask
            for key in ('fallback', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            raw['n_current'][tick] = (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1)
            raw['n_visible_peers'][tick] = (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1)
            if reporting:
                pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                           current_mask, started=c_start, cpu_started=c_cpu)
                pending_at = tick + DELIVERY
                record_round(raw, pending, tick, arm)
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            if arm in ('O', 'G'):
                scheduler.executed(tick, actual.copy(), int(current_mask))
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
            arrival_due = tick + 1 == pending_at
            if pending is not None and arrival_due:
                current_mask = pending['mask']
                actual = np.array(pending['commands'], dtype=np.float32, copy=True)
                env.env.set_transmitter_mask(mask_array(current_mask))
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                pending = None
                pending_at = None
            obs = next_obs
            raw['observations'][tick + 1] = obs
    except Exception as exc:
        failure = exc
    finally:
        if arm in ('O', 'G'):
            support_wall, support_cpu = time.perf_counter(), time.process_time()
            before = scheduler.execution.next_unsettled
            ready = False
            try:
                _, ready = scheduler.execution.settle(int(raw['completed_steps']))
            except Exception as support_failure:
                raw['terminal_support_failure_type'] = np.array(type(support_failure).__name__)
                raw['terminal_support_failure_message'] = np.array(str(support_failure))
                if failure is None:
                    failure = support_failure
            settled = scheduler.execution.next_unsettled
            start_tick = scheduler.execution.start_tick
            raw['terminal_history_start'] = np.array(-1 if start_tick is None else start_tick)
            if start_tick is not None:
                raw['model_valid'][start_tick:settled] = True
            for tick, served in scheduler.execution.predicted.items():
                raw['model_contacts'][tick] = served
            raw['terminal_history_complete'][...] = ready
            raw['terminal_history_reductions'][...] = settled - before
            raw['terminal_history_wall'][...] = time.perf_counter() - support_wall
            raw['terminal_history_cpu'][...] = time.process_time() - support_cpu
            raw['terminal_last'] = scheduler.execution.history.last.copy()
            raw['terminal_windows'] = scheduler.execution.history.windows.copy()
        raw['episode_failure_type'] = np.array('' if failure is None else type(failure).__name__)
        raw['episode_failure_message'] = np.array('' if failure is None else str(failure))
        add_contact_raw(raw, int(raw['completed_steps']))
        if arm == 'G':
            add_gate_raw(raw, int(raw['completed_steps']))
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
    by_key = {(row['arm'],row['seed']):row for row in rows}
    if not seeds or len(by_key)!=len(rows) or len(rows)!=len(ARMS)*len(seeds) or any((arm,seed) not in by_key for arm in ARMS for seed in seeds):
        raise ValueError('paired reading requires all three complete arms')
    metrics=('F','J','mean_served','mean_quality','service_p10','min_served','zero_service_steps',
             'longest_zero_service','mean_path_length_m','xy_boundary_uav_steps','lower_altitude_uav_steps',
             'fallback_decisions','proposal_command_edits','executed_block_edits','transmitter_on_ticks',
             'mask_flips','scheduler_cpu_seconds','scheduler_wall_seconds','cpu_seconds','wall_seconds',
             'recurring_bytes','deadline_misses','ever_served','never_served','max_unserved_gap',
             'mean_user_max_unserved_gap','candidate_requests','candidate_plans','state_reductions','geometry_snapshots')
    # These are existing frozen readings, flattened only for world-paired contrasts.
    def readings(row):
        values = {name: row[name] for name in metrics}
        for name in ('unserved_gaps', 'closed_unserved_gaps'):
            values.update({f'{name}.{stat}': row[name][stat] for stat in ('count', 'mean', 'maximum')})
        for name in ('per_window_coverage', 'satisfied_window_histogram'):
            values.update({f'{name}.{index}': value for index, value in enumerate(row[name])})
        for name in ('left_censored_gaps', 'right_censored_gaps', 'c_cpu_seconds', 'c_wall_seconds'):
            values[name] = row[name]
        return values
    flat = {key: readings(row) for key, row in by_key.items()}
    comparisons={}
    for second,first in itertools.combinations(ARMS,2):
        result={}
        for key in flat[first, seeds[0]]:
            differences = [None if flat[first, seed][key] is None or flat[second, seed][key] is None
                           else flat[first, seed][key] - flat[second, seed][key] for seed in seeds]
            delta = np.array([value for value in differences if value is not None], dtype=float)
            mean = float(delta.mean()) if len(delta) else None
            half = float(student_t.ppf(.975, len(delta) - 1) * delta.std(ddof=1) / np.sqrt(len(delta))) if len(delta) > 1 else None
            result[key] = dict(mean=mean, differences=differences,
                               descriptive_t95=[mean-half, mean+half] if half is not None else None,
                               worlds_with_both_readings=len(delta), missing_worlds=len(seeds)-len(delta),
                               positive=int((delta>0).sum()), negative=int((delta<0).sum()), zero=int((delta==0).sum()))
        comparisons[f'{first}-{second}']=result
    return dict(primary='G-O',seeds=list(seeds),comparisons=comparisons,
                unit='paired reset world conditional on realized node/load/deadlines; zero training inference',
                absent_gap_scope='undefined gap means/maxima stay null; contrasts and intervals use only worlds with both readings, with explicit missing counts')


def run_batch(out, launch_sha, *, make_env=factory, seeds=tuple(range(SEED,SEED+WORLDS)), horizon=HORIZON, entry_start=None, admission=None):
    wall_start=time.perf_counter() if entry_start is None else entry_start
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    if (out/'summary.json').exists() or (out/'raw').exists():
        raise FileExistsError('refusing to replace scientific evidence')
    (out/'raw').mkdir()
    counts=dict(constructors=0,explicit_resets=0,native_step_calls=0,team_steps=0,complete_episodes=0,fit_started=0,optimizer_steps=0)
    scientific=make_env is factory and tuple(seeds)==tuple(range(SEED,SEED+WORLDS)) and horizon==HORIZON
    config=dict(launch_sha=launch_sha,arms=list(ARMS),seeds=list(seeds),horizon=horizon,
                arm_orders=[list(x) for x in ARM_ORDERS],order='world index modulo6 cyclic/reversed cyclic',
                planned_fits=0,planned_episodes=3*len(seeds),planned_steps=3*len(seeds)*horizon,
                learning='fixed deterministic policies; no parameters, gradients or optimizer',
                terminal_history_completeness='all reconstructable post-anchor transitions; unknown prefix excluded from model validity only',
                compute_threads=1,cpu_limit_seconds=None,
                preferred_node='wsl_4070',actual_host=platform.node(),actual_platform=platform.platform(),
                actual_python=os.path.realpath(os.sys.executable),admission_identity=admission,
                host='N5 U50 static uniform free_space no-shadowing non-FDMA 3dB cap10',
                delivery_ticks={arm:2 for arm in ARMS},hold_ticks=4,
                map_bytes=400,report_bytes=24,command_bytes=16,link_bits_per_second=2000,
                deadline_seconds={arm:1.456 for arm in ARMS},
                score='S2 native; O age-group/native; G fixed coverage gate selects native iff complete lawful same-window prefix, otherwise O',
                gate='all50 model prefix bits; one64transition window with start>=lawful anchor; computed once before both orders',
                evaluator_completion_scope='actual report contacts through t-1; committed-prefix contacts through t+1; whole window at episode end',
                truth_history='evaluation only; no service ACK',terminal_history_scope='separately timed evaluator support outside online deadline; included in worker resources; never actor action',
                source_identities=source_identities(),
                library_versions=dict(numpy=np.__version__, scipy=__import__('scipy').__version__),
                frozen_radio_source='2bff85091f85f6d52fc0344d0329b4fc39fa6d5c')
    summary=dict(object='UAV-REGISTERED-SERVICE-B02',status='INCOMPLETE',launch_sha=launch_sha,
                 config=config,counts=counts,rows=[],failure=None,scientific_invocation=scientific)
    write_json(out/'config.json',config)
    write_json(out/'summary.json',summary)
    env=None
    try:
        env=make_env(seeds[0])
        counts['constructors']+=1
        for index,seed in enumerate(seeds):
            for arm in ARM_ORDERS[index%6]:
                summary['rows'].append(collect_episode(env,arm,seed,out,counts,horizon=horizon))
                write_json(out/'summary.json',summary)
                print(json.dumps(dict(arm=arm,seed=seed,complete_episodes=counts['complete_episodes'],team_steps=counts['team_steps'])),flush=True)
        summary['fixed_policy_evaluation_counts']=dict(episodes=counts['complete_episodes'],transitions=counts['team_steps'],optimizer_updates=0,parameter_updates=0)
        summary['paired']=paired_reading(summary['rows'],seeds)
        summary['status']='COMPLETE'
    except Exception as exc:
        summary['status']='INCOMPLETE_TECHNICAL_FAILURE'
        summary['failure']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    finally:
        if env is not None:
            env.close()
        usage=resource.getrusage(resource.RUSAGE_SELF)
        summary['resources']=dict(wall_seconds=time.perf_counter()-wall_start,user_cpu_seconds=usage.ru_utime,
                                  system_cpu_seconds=usage.ru_stime,process_cpu_seconds=usage.ru_utime+usage.ru_stime,
                                  peak_rss_kib=usage.ru_maxrss,rss_scope='worker lifetime peak; Linux KiB',
                                  thread_environment={name:os.environ.get(name) for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
        summary['artifacts']=[file_identity(path) for path in sorted((out/'raw').glob('*.npz'))]
        write_json(out/'summary.json',summary)
    return summary
