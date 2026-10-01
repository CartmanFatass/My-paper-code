"""Delayed C2 collection; no modeled history settlement or real grant feedback."""

from collections import Counter
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_user_waiting.b02.protocol import ALL_ON, encode_map, mask_array
from experiments.candidates.uav_user_waiting.b02.predictor import controller_nav_index
from experiments.candidates.uav_user_waiting.b02.study import allocate_raw as previous_raw, record_round
from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_service_age.b01.metrics import add_age_raw
from experiments.candidates.uav_user_waiting.b06.collect import (
    PairCheckedEnvironment, _ControllerMeter, _add_c_raw, accounting_error, error_details, atomic_npz,
)
from . import protocol as p
from .manager import Scheduler
from .metrics import episode_metrics

BASELINE_FIELDS = ('positions', 'true_sites', 'map_packet', 'observations', 'commands', 'mask')


def allocate_raw(horizon, sites, packet):
    raw = previous_raw(horizon, p.PROGRAM, sites, packet)
    # This program has no modeled execution history. Do not serialize dummy history.
    for name in ('model_valid', 'model_contacts', 'terminal_history_complete',
                 'terminal_history_reductions', 'terminal_history_wall', 'terminal_history_cpu'):
        del raw[name]
    return raw


def collect_episode(env, seed, out, counts, baseline_identity, *, accounting=None,
                    horizon=p.HORIZON, scheduler_type=Scheduler, controller_type=LocalController):
    accounting = {} if accounting is None else accounting
    p.require(8 <= horizon <= p.HORIZON and horizon % 4 == 0, 'complete four-tick horizon required')
    started, cpu_started = time.perf_counter(), time.process_time()
    baseline = p.load_raw(baseline_identity, BASELINE_FIELDS)
    counts['baseline_raw_files_loaded'] += 1
    counts['baseline_raw_bytes_hashed'] += baseline_identity['bytes']
    counts['baseline_array_bytes_loaded'] += sum(array.nbytes for array in baseline.values())
    paired = PairCheckedEnvironment(env, baseline, counts)
    obs, reset_info = paired.reset(seed=seed)
    counts['explicit_resets'] += 1
    p.require(obs.shape == (p.N, 104) and env.env.transmitter_mask.all(), 'incorrect reset contract')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    packet = encode_map(sites)
    raw = allocate_raw(horizon, sites, packet)
    raw.update(world_seed=np.array(seed), training_episode=np.array(False), grant_feedback_used=np.array(False),
        baseline_sf_sha256=np.array(baseline_identity['sha256']), baseline_sf_bytes=np.array(baseline_identity['bytes'], np.int64),
        collector_program=np.array(p.PROGRAM))
    attempted, completed = np.zeros((horizon, p.N), bool), np.zeros((horizon, p.N), bool)
    raw['current_c_attempted'], raw['current_c_completed'] = attempted, completed
    controllers = [_ControllerMeter(controller_type(history=False), i, attempted, completed, counts) for i in range(p.N)]
    scheduler = scheduler_type(packet, horizon=horizon)
    records, failure = [], None
    raw['positions'][0] = reset_info['state_info']['uav_positions']
    raw['observations'][0] = obs
    actual = np.zeros((p.N, 3), np.float32)
    proposals = actual.copy()
    current_mask, pending, pending_at, pairs = ALL_ON, None, None, None
    try:
        for tick in range(horizon):
            reporting = tick % 4 == 0
            c_start, c_cpu = time.perf_counter(), time.process_time()
            if reporting:
                try:
                    pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
                finally:
                    raw['c_wall'][tick], raw['c_cpu'][tick] = time.perf_counter()-c_start, time.process_time()-c_cpu
                proposals = np.asarray([pair[0] for pair in pairs], np.float32)
                raw['c_called'][tick] = raw['c_decision'][tick] = True
            if tick == 0:
                actual = proposals.copy()
            raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, current_mask
            for key in ('fallback', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            raw['n_current'][tick] = (obs[:, 3:63].reshape(p.N,20,3)[:,:,2] > 0).sum(axis=1)
            raw['n_visible_peers'][tick] = (obs[:,63:103].reshape(p.N,10,4)[:,:,3] > 0).sum(axis=1)
            if reporting:
                nav = np.asarray([controller_nav_index(c) for c in controllers], np.uint8)
                raw['post_c_nav'][tick//4] = nav
                result = None
                try:
                    result = scheduler.decide(obs[:,:3].copy(), actual.copy(), proposals.copy(), tick,
                                              current_mask, nav, started=c_start, cpu_started=c_cpu)
                finally:
                    record = result['record'] if result is not None else getattr(scheduler, 'last_record', None)
                    if record:
                        records.append(record)
                pending, pending_at = result, tick+2
                record_round(raw, pending, tick)
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            global_info = info['infos_dict']['uav_0']['global']
            # Save postmove service before arrival refresh mutates native radio arrays.
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            connected = np.array(global_info['connections'], dtype=bool, copy=True)
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected]-3.)/30.,0.,1.).sum()/max(served,1))
            reward = sum(float(value) for value in info['rewards_dict'].values())
            p.require(np.isclose(reward, .7*served/p.U+.3*quality, atol=1e-12, rtol=0), 'native reward differs')
            raw['sinr'][tick], raw['connections'][tick] = sinr, connected
            raw['served'][tick], raw['quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['positions'][tick+1] = info['state_info']['uav_positions']
            raw['completed_steps'][...] = tick+1
            p.require(bool(terminated or truncated) == (tick+1 == horizon), 'unexpected native terminal boundary')
            if pending is not None and tick+1 == pending_at:
                current_mask = int(pending['mask'])
                actual = np.array(pending['commands'], dtype=np.float32, copy=True)
                counts['mask_refresh_attempts'] += 1
                env.env.set_transmitter_mask(mask_array(current_mask))
                counts['mask_refreshes'] += 1
                next_obs = env._dict_to_array({agent:env.env._get_observation(agent) for agent in env.agents})
                pending, pending_at = None, None
            obs = next_obs
            raw['observations'][tick+1] = obs
    except Exception as exc:
        failure = exc
    finally:
        def support(phase, function):
            nonlocal failure
            try:
                return function()
            except Exception as exc:
                accounting_error(accounting, phase, exc)
                if failure is None:
                    failure = exc
                return None
        steps = int(raw['completed_steps'])
        support('contact_arrays', lambda:add_contact_raw(raw, steps))
        support('age_arrays', lambda:add_age_raw(raw, steps))
        support('current_c_raw', lambda:_add_c_raw(raw, attempted, completed, controllers))
        keys = tuple(controllers[0].counters)
        raw['controller_counter_keys'] = np.asarray(keys)
        raw['controller_counts'] = np.asarray([sum(c.counters[key] for c in controllers) for key in keys])
        packed = support('decision_records', lambda:pack_records(records))
        if packed is not None:
            raw.update(packed)
        accounting.update(current_c_attempted=int(attempted.sum()), current_c_completed=int(completed.sum()),
                          current_c_failed=int((attempted & ~completed).sum()),
                          current_c_source_counts=dict(zip(keys,raw['controller_counts'].tolist())))
        model_counts = Counter()
        for record in records:
            model_counts.update({key:int(value) for key,value in record['counts'].items()})
        accounting['model_work'] = dict(model_counts)
        for name,value in accounting['current_c_source_counts'].items():
            counts['worker_current_c_source_'+name] += value
        raw['episode_failure_type'] = np.array('' if failure is None else type(failure).__name__)
        raw['episode_failure_message'] = np.array('' if failure is None else error_details(failure)['message'])
        if failure is not None:
            support('failed_raw', lambda:atomic_npz(Path(out)/'raw'/f'{p.PROGRAM}_{seed}.npz',raw))
    if failure is not None:
        raise failure
    counts['complete_episodes'] += 1
    try:
        row = dict(arm=p.PROGRAM,seed=seed,steps=horizon,**episode_metrics(raw,horizon,records),
            controller_counts=dict(zip(keys,raw['controller_counts'].tolist())),
            wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started)
    except Exception as exc:
        raw['episode_failure_type'] = np.array(type(exc).__name__)
        raw['episode_failure_message'] = np.array(error_details(exc)['message'])
        try:
            atomic_npz(Path(out)/'raw'/f'{p.PROGRAM}_{seed}.npz',raw)
        except Exception as support_failure:
            accounting_error(accounting,'failed_reducer_raw',support_failure)
        raise
    return row,raw,baseline
