"""Complete five-arm collection; retained planners unchanged, no worker CPU ceiling."""

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

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.protocol import (
    ALL_ON, HIGH, HORIZON, LOW, N, U, encode_map, mask_array,
)
from experiments.candidates.uav_radio_activation.b01.scheduler import Scheduler as RetainedScheduler
from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler as FrozenScheduler
from experiments.candidates.uav_radio_activation.b03.study import (
    allocate_raw as frozen_allocate, record_round as frozen_record, episode_metrics as frozen_metrics,
)
from .scheduler import Scheduler as HistoryScheduler
from .metrics import periodic_metrics, add_contact_raw, estimate_metrics

SEED, WORLDS = 29308000, 64
ARMS = ('R', 'S2', 'T2', 'O', 'P')
ARM_ORDERS = tuple(tuple(order[i:] + order[:i]) for order in (ARMS, tuple(reversed(ARMS))) for i in range(5))


def allocate_raw(horizon, arm, sites, map_packet):
    raw = frozen_allocate(horizon, arm, sites, map_packet)
    if arm in ('O', 'P'):
        rounds = horizon // HOLD
        raw.update(ordering_keys=np.full((rounds,27,32,U+7), np.nan), key_length=np.zeros(rounds,dtype=int),
                   candidate_contacts=np.zeros((rounds,27,32,HOLD,U),dtype=bool),
                   decoded_anchor=np.zeros(rounds,dtype=bool),
                   snapshot_last=np.full((rounds,U),-2), snapshot_windows=np.zeros((rounds,4,U),dtype=bool),
                   prefix_last=np.full((rounds,U),-2), prefix_windows=np.zeros((rounds,4,U),dtype=bool),
                   model_valid=np.zeros(horizon,dtype=bool), model_contacts=np.zeros((horizon,U),dtype=bool),
                   terminal_history_complete=np.array(False), terminal_history_reductions=np.array(0),
                   terminal_history_wall=np.array(0.), terminal_history_cpu=np.array(0.))
        for key in ('history_before','history_after','history_reductions','candidate_cache_hits','candidate_uncached_requests','interrupted_candidate_requests'):
            raw[key]=np.zeros(rounds,dtype=int)
        for key in ('history_wall','history_cpu','prefix_wall','prefix_cpu','candidate_wall','candidate_cpu'):
            raw[key]=np.zeros(rounds)
        raw['history_start']=np.full(rounds,-1)
        raw['window_valid']=np.zeros((rounds,4),dtype=bool)
        raw['unknown_age']=np.zeros((rounds,U),dtype=bool)
        raw['actual_timeout']=np.zeros(rounds,dtype=bool)
        raw['snapshot_valid']=np.zeros(rounds,dtype=bool)
        raw['prefix_valid']=np.zeros(rounds,dtype=bool)
        raw['fallback_reason']=np.full(rounds,'',dtype='<U32')
    return raw


def record_round(raw, arrival, tick, arm):
    index=int(raw['round_count'])
    frozen_record(raw, arrival, tick, arm)
    if arm in ('O','P'):
        for key in ('ordering_keys','key_length','decoded_anchor','history_before','history_after',
                    'snapshot_last','snapshot_windows','prefix_last','prefix_windows','history_reductions',
                    'history_wall','history_cpu','prefix_wall','prefix_cpu','candidate_wall','candidate_cpu',
                    'fallback_reason','history_start','window_valid','unknown_age','actual_timeout','snapshot_valid','prefix_valid','candidate_cache_hits','candidate_uncached_requests','interrupted_candidate_requests'):
            raw[key][index]=arrival[key]
        length=arrival['scored_length']
        raw['candidate_contacts'][index,:,:,:length]=arrival['candidate_contacts']


def episode_metrics(raw, steps, arm):
    result=frozen_metrics(raw,steps,arm)
    result.update(periodic_metrics(raw['connections'][:steps].any(axis=1)))
    result['candidate_request_completion_residual']=int(result['candidate_requests']-raw['candidate_plans'].sum())
    if arm not in ('O','P'):
        result['candidate_residual_scope']='legacy requests minus completed plans; not literal cache hits after interruption'
    if arm in ('O','P'):
        result.update(estimate_metrics(raw,steps))
        for key in ('candidate_cache_hits','candidate_uncached_requests','interrupted_candidate_requests'):
            result[key]=int(raw[key].sum())
        for key in ('history_reductions','history_wall','history_cpu','prefix_wall','prefix_cpu','candidate_wall','candidate_cpu'):
            result[key]=float(raw[key].sum()) if key.endswith(('wall','cpu')) else int(raw[key].sum())
        for key in ('terminal_history_complete','terminal_history_reductions','terminal_history_wall','terminal_history_cpu'):
            result[key]=raw[key].item()
        result['actual_timeout_rounds']=int(raw['actual_timeout'].sum())
        result['model_start_tick']=int(raw['terminal_history_start'])
        result['model_unknown_prefix_transitions']=int(raw['terminal_history_start']) if int(raw['terminal_history_start'])>=0 else steps
        result['selected_forecast_service_false_positive']=0
        result['selected_forecast_service_false_negative']=0
        result['selected_forecast_transitions']=0
        for index in range(int(raw['round_count'])):
            if not raw['timely'][index]:
                continue
            tick=int(raw['round_tick'][index])+DELIVERY
            length=min(HOLD,steps-tick)
            q,mask=int(raw['selected_q'][index]),int(raw['selected_mask'][index])
            prediction=raw['candidate_contacts'][index,q,mask,:length]
            actual=raw['connections'][tick:tick+length].any(axis=1)
            result['selected_forecast_service_false_positive']+=int((prediction & ~actual).sum())
            result['selected_forecast_service_false_negative']+=int((~prediction & actual).sum())
            result['selected_forecast_transitions']+=length
        result['history_unavailable_rounds']=int((raw['history_start']<0).sum())
        result['history_unavailable_fallbacks']=int((raw['fallback_reason']=='history_unavailable').sum())
    return result


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    scheduler_type=None, retained_type=RetainedScheduler,
                    controller_type=LocalController):
    if arm not in ARMS or not 8 <= horizon <= HORIZON or horizon % 4:
        raise ValueError('five arms require complete four-tick blocks from8 to256')
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect observation or non-all-on reset')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    chosen_type = scheduler_type or (HistoryScheduler if arm in ('O', 'P') else FrozenScheduler)
    scheduler = retained_type('E', map_packet) if arm == 'R' else chosen_type(arm, map_packet, horizon=horizon)
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
                pending_at = tick + (1 if arm == 'R' else DELIVERY)
                record_round(raw, pending, tick, arm)
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            if arm in ('O', 'P'):
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
                if arm != 'R':
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
        if arm in ('O', 'P'):
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
    if len(by_key)!=len(rows) or len(rows)!=len(ARMS)*len(seeds) or any((arm,seed) not in by_key for arm in ARMS for seed in seeds):
        raise ValueError('paired reading requires all five complete arms')
    metrics=('F','J','mean_served','mean_quality','service_p10','min_served','zero_service_steps',
             'longest_zero_service','mean_path_length_m','xy_boundary_uav_steps','lower_altitude_uav_steps',
             'fallback_decisions','proposal_command_edits','executed_block_edits','transmitter_on_ticks',
             'mask_flips','scheduler_cpu_seconds','scheduler_wall_seconds','cpu_seconds','wall_seconds',
             'recurring_bytes','deadline_misses','ever_served','never_served','max_unserved_gap',
             'mean_user_max_unserved_gap','candidate_requests','candidate_plans','state_reductions','geometry_snapshots')
    comparisons={}
    for second,first in itertools.combinations(ARMS,2):
        result={}
        for key in metrics:
            delta=np.array([by_key[first,seed][key]-by_key[second,seed][key] for seed in seeds])
            mean=float(delta.mean())
            half=float(student_t.ppf(.975,len(seeds)-1)*delta.std(ddof=1)/np.sqrt(len(seeds))) if len(seeds)>1 else None
            result[key]=dict(mean=mean,differences=delta.tolist(),descriptive_t95=[mean-half,mean+half] if half is not None else None,
                             positive=int((delta>0).sum()),negative=int((delta<0).sum()),zero=int((delta==0).sum()))
        comparisons[f'{first}-{second}']=result
    return dict(primary='P-O',seeds=list(seeds),comparisons=comparisons,
                unit='paired reset world conditional on realized node/load/deadlines; zero training inference')


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
                arm_orders=[list(x) for x in ARM_ORDERS],order='world index modulo10 cyclic/reversed cyclic',
                planned_fits=0,planned_episodes=5*len(seeds),planned_steps=5*len(seeds)*horizon,
                learning='fixed deterministic policies; no parameters, gradients or optimizer',
                terminal_history_completeness='all reconstructable post-anchor transitions; unknown prefix excluded from model validity only',
                compute_threads=1,cpu_limit_seconds=None,
                preferred_node='wsl_4070',actual_host=platform.node(),actual_platform=platform.platform(),
                actual_python=os.path.realpath(os.sys.executable),admission_identity=admission,
                host='N5 U50 static uniform free_space no-shadowing non-FDMA 3dB cap10',
                delivery_ticks={'R':1,'S2':2,'T2':2,'O':2,'P':2},hold_ticks=4,
                map_bytes=400,report_bytes=24,command_bytes=16,link_bits_per_second=2000,
                deadline_seconds={'R':.456,'S2':1.456,'T2':1.456,'O':1.456,'P':1.456},
                score='P: new pairs; O/P: lexicographic older-age distinct users; native J,served,preserve Cq,more active,lower mask,lower q',
                truth_history='evaluation only; no service ACK',terminal_history_scope='separately timed evaluator support outside online deadline; included in worker resources; never actor action',
                source_identities=[file_identity(path) for path in sorted(Path(__file__).parent.glob('*.py'))],
                frozen_radio_source='2bff85091f85f6d52fc0344d0329b4fc39fa6d5c')
    summary=dict(object='UAV-REGISTERED-SERVICE-B01',status='INCOMPLETE',launch_sha=launch_sha,
                 config=config,counts=counts,rows=[],failure=None,scientific_invocation=scientific)
    write_json(out/'config.json',config)
    write_json(out/'summary.json',summary)
    env=None
    try:
        env=make_env(seeds[0])
        counts['constructors']+=1
        for index,seed in enumerate(seeds):
            for arm in ARM_ORDERS[index%10]:
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
