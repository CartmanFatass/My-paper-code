"""Retained B02 native loop with B03 scheduler and maximum-history evidence."""
from pathlib import Path
import time
import numpy as np
from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_user_waiting.b02.protocol import N,U,HORIZON,HOLD,DELIVERY,ALL_ON,encode_map,mask_array
from experiments.candidates.uav_user_waiting.b02.study import allocate_raw, record_round, save_episode
from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from experiments.candidates.uav_user_waiting.b02.predictor import controller_nav_index
from experiments.candidates.uav_user_waiting.b02.metrics import episode_metrics
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_service_age.b01.metrics import add_age_raw
from .scheduler import Scheduler

ARMS = ('M','S','G0','LR','LN')


def value_diagnostics(records):
    eligible = [r for r in records if r['value_eligible']]
    executed = [r for r in eligible if r['timely']]
    stages = [r['current'] for r in records if r['current']]
    values = np.concatenate([s['value_clipped'][s['value_valid']] for s in stages]) if stages else np.empty(0)
    return dict(value_eligible_rounds=len(eligible), value_executed_rounds=len(executed),
        value_pair_changes_from_m=sum(not np.array_equal(r['requested_pair'],r['m_pair']) for r in executed),
        value_pair_changes_from_visited_zero=sum(not np.array_equal(r['requested_pair'],r['visited_zero_pair']) for r in executed),
        missing_maximum_m_fallbacks=sum(r['missing_maximum_m_fallback'] for r in records),
        perturbations_computed=sum(r['perturbation_applied'] for r in records),
        perturbations_executed=sum(r['perturbation_applied'] and r['timely'] for r in records),
        value_queries=sum(r['counts']['value_queries'] for r in records),
        value_clipped_count=sum(int(s['value_was_clipped'].sum()) for s in stages),
        value_range=[float(values.min()),float(values.max())] if len(values) else None)


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    scheduler_type=None, controller_type=LocalController, value=None, perturbation=None, training=False):
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
    scheduler = (scheduler_type or Scheduler)(arm, map_packet, horizon=horizon, value=value, perturbation=perturbation)
    controllers = [controller_type(history=False) for _ in range(N)]
    raw = allocate_raw(horizon, arm, sites, map_packet)
    raw['world_seed'] = np.array(seed)
    raw['training_episode'] = np.array(training)
    raw['perturbation_tick'] = np.array(-1 if perturbation is None else perturbation[0])
    raw['perturbation_pair'] = np.array([-1,-1] if perturbation is None else perturbation[1], np.int64)
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
        raw['terminal_maximum'] = scheduler.execution.history.maximum.copy()
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
    row.update(value_diagnostics(records))
    return row, raw
