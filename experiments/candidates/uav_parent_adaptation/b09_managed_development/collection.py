"""Actual S2 trajectories with immutable pre-proposal learning records."""
import copy
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_radio_activation.b01 import protocol as ep
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.collection import (
    COORD_COUNTERS, allocate_raw, record_round, _observation, _mask,
)
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.reading import episode_metrics
from .contract import arm_parts, base_arm
from .learning import critic_features
from .policies import ManagedTeam


def collect_episode(env, *, arm, world, tape, bundle, out, protocol, counts, actor,
                    policy_sha, inflight, check, head=None, critic=None,
                    team_type=ManagedTeam, coordinator_factory=None,
                    clock=time.perf_counter, cpu_clock=time.process_time):
    program, coordinator = arm_parts(arm)
    family = program if program in ('C', 'Q_I') else 'S_I'
    training = critic is not None
    if training and (program not in ('CAL', 'CONT') or head is None or tape != 0):
        raise ValueError('training requires selected new head and one I tape')
    if (family == 'C') != (tape == -1) or (family != 'C' and (tape not in protocol.tapes or bundle is None)):
        raise ValueError('program/tape mismatch')
    path = Path(out) / 'raw' / f'{arm}_w{world}_t{tape}.npz'
    if path.exists():
        raise FileExistsError('existing episode evidence: no repeat')
    start_wall, start_cpu = clock(), cpu_clock()
    inflight.clear()
    inflight.update(arm=arm, world=int(world), tape=int(tape), phase='reset', completed_steps=0)
    check()
    counts['explicit_reset_calls'] += 1
    obs, info = env.reset(seed=int(world))
    counts['explicit_resets'] += 1
    obs = _observation(obs)
    _mask(env, ep.ALL_ON)
    state = np.asarray(info['state'], dtype=np.float32).copy() if training else None
    users = np.asarray(info['state_info']['user_positions'], dtype=np.float64).copy()
    raw = allocate_raw(protocol.horizon, coordinator)
    raw['positions'][0] = np.asarray(info['state_info']['uav_positions'], dtype=np.float64)
    raw['initial_users'] = users
    map_packet = ep.encode_map(users)
    raw['map_packet'] = np.frombuffer(map_packet, np.uint8).copy()
    if training:
        d = protocol.horizon // 4
        raw.update(critic_states=np.full((d, 116), np.nan, np.float32),
                   critic_features=np.full((d, 186), np.nan, np.float32),
                   critic_actual=np.full((d, 5, 3), np.nan, np.float32),
                   critic_mask=np.zeros((d, 5), bool),
                   critic_nav=np.full((d, 5), -1, np.int64),
                   values=np.full(d, np.nan, np.float32))
    team, records = None, []
    times = {f'{part}_{clock_name}_seconds': 0. for part in
             ('decision_query', 'sampler', 'local_block', 'native_step', 'mask_refresh', 'raw_write', 'critic')
             for clock_name in ('wall', 'cpu')}
    current_mask, pending, pending_at = ep.ALL_ON, None, None
    actual = np.zeros((5, 3), np.float32)
    completed = False
    try:
        team = team_type(family, obs.copy(), actor=actor if family == 'S_I' else None,
                         head=head, temperature=2. if program == 'Bstar' else 1.)
        scheduler = (coordinator_factory(coordinator, map_packet, protocol.horizon)
                     if coordinator_factory is not None else Scheduler(
                         coordinator, map_packet, clock=clock, cpu_clock=cpu_clock, horizon=protocol.horizon))
        for tick in range(protocol.horizon):
            check()
            raw['observations'][tick] = obs
            if tick % 4 == 0:
                if pending is not None:
                    raise AssertionError('pending control at report boundary')
                j = tick // 4
                # This baseline is captured before queries, nav advance, current
                # innovations and the special startup actual=proposals assignment.
                if training:
                    inflight.update(phase='critic', tick=tick)
                    wall, cpu = clock(), cpu_clock()
                    raw['critic_states'][j] = state
                    raw['critic_actual'][j] = actual
                    raw['critic_mask'][j] = _mask(env, current_mask)
                    raw['critic_nav'][j] = team.navs.copy()
                    cf = critic_features(state, actual, raw['critic_mask'][j], team.navs.copy(),
                                         tick=tick, horizon=protocol.horizon)
                    raw['critic_features'][j] = cf
                    counts['collected_critic_attempts'] = counts.get('collected_critic_attempts', 0) + 1
                    with torch.inference_mode():
                        value = critic(torch.from_numpy(cf))
                    if value.numel() != 1 or not bool(torch.isfinite(value).all()):
                        raise FloatingPointError('nonfinite pre-action critic')
                    raw['values'][j] = float(value)
                    counts['collected_critic_rows'] += 1
                    times['critic_wall_seconds'] += clock() - wall
                    times['critic_cpu_seconds'] += cpu_clock() - cpu
                local_wall, local_cpu = clock(), cpu_clock()
                inflight.update(phase='local_decision', tick=tick)

                def coins():
                    counts['private_integer_reads'] += 10
                    return {key: bundle[key][j].copy() for key in ('private_depart', 'private_tail')}

                counts['policy_block_calls'] += 1
                decision = team.decide(obs.copy(), tick, coin_provider=coins if family != 'C' else None)
                counts['policy_blocks'] += 1
                counts['sampling_decisions'] += int(decision['sampling_decisions'])
                for key, value in decision['timing'].items():
                    times[key] += value
                times['local_block_wall_seconds'] += clock() - local_wall
                times['local_block_cpu_seconds'] += cpu_clock() - local_cpu
                records.append(copy.deepcopy(decision['record']))
                proposals = np.asarray(decision['commands'], dtype=np.float32).copy()
                raw['proposals'][j] = proposals
                raw['completed_decisions'][...] = j + 1
                if tick == 0:
                    actual = proposals.copy()
                raw['coord_started'][j] = True
                raw['coord_due'][j] = tick + 2
                raw['coord_actual'][j] = actual
                raw['coord_mask_before'][j] = current_mask
                inflight['phase'] = 'coordinator_call'
                counts['coordinator_round_calls'] += 1
                pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                           current_mask, started=local_wall, cpu_started=local_cpu)
                counts['coordinator_round_returns'] += 1
                pending_at = tick + 2
                record_round(raw, pending, j, coordinator)
            raw['commands'][tick] = actual
            raw['transmitter_mask'][tick] = _mask(env, current_mask)
            inflight['phase'] = 'native_step'
            check()
            wall, cpu = clock(), cpu_clock()
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['native_steps'] += 1
            times['native_step_wall_seconds'] += clock() - wall
            times['native_step_cpu_seconds'] += cpu_clock() - cpu
            global_info = info['infos_dict']['uav_0']['global']
            sinr = np.asarray(global_info['sinr_matrix'], dtype=np.float64).copy()
            connected = np.asarray(global_info['connections'], dtype=bool).copy()
            active = raw['transmitter_mask'][tick]
            if (sinr.shape != (5, 50) or connected.shape != (5, 50)
                    or not np.isfinite(sinr[active]).all() or not np.isneginf(sinr[~active]).all()):
                raise AssertionError('invalid native endpoint SINR')
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected] - 3.) / 30., 0., 1.).sum() / max(served, 1))
            reward = sum(float(x) for x in info['rewards_dict'].values())
            if not np.isclose(reward, .7 * served / 50. + .3 * quality, rtol=0., atol=1e-12):
                raise AssertionError('native reward mismatch')
            after = np.asarray(info['state_info']['uav_positions'], dtype=np.float64).copy()
            expected = np.clip(raw['positions'][tick] + actual.astype(np.float64) * 30., ep.LOW, ep.HIGH)
            if not np.array_equal(after, expected):
                raise AssertionError('native motion law changed')
            raw['positions'][tick + 1] = after
            raw['sinr'][tick], raw['connections'][tick] = sinr, connected
            raw['served'][tick], raw['sinr_quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['completed_steps'][...] = tick + 1
            inflight['completed_steps'] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
                raise AssertionError('unexpected episode boundary')
            if training:
                state = np.asarray(info['next_state'], dtype=np.float32).copy()
            if pending is not None and tick + 1 == pending_at:
                inflight['phase'] = 'mask_arrival'
                wall, cpu = clock(), cpu_clock()
                actual = np.asarray(pending['commands'], dtype=np.float32).copy()
                current_mask = int(pending['mask'])
                counts['mask_setter_calls'] += 1
                env.env.set_transmitter_mask(ep.mask_array(current_mask))
                counts['mask_setter_returns'] += 1
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                times['mask_refresh_wall_seconds'] += clock() - wall
                times['mask_refresh_cpu_seconds'] += cpu_clock() - cpu
                pending, pending_at = None, None
            obs = _observation(next_obs)
        check()
        if pending is not None:
            raise AssertionError('terminal pending delivery')
        if training:
            raw['macro_rewards'] = raw['reward'].reshape(-1, 4).sum(axis=1, dtype=np.float64)
        completed = True
    finally:
        raw['terminal_observation'] = obs.copy()
        raw['terminal_mask'] = ep.mask_array(current_mask)
        if records:
            for key in records[0]:
                raw[key] = np.asarray([record[key] for record in records])
        raw['episode_complete'] = np.array(completed)
        wall, cpu = clock(), cpu_clock()
        np.savez_compressed(path, **raw)
        identity = file_identity(path)
        identity['path'] = str(path.relative_to(out))
        times['raw_write_wall_seconds'] += clock() - wall
        times['raw_write_cpu_seconds'] += cpu_clock() - cpu
        inflight.update(raw=identity, policy_counts={} if team is None else team.counts(), times=times.copy(),
                        partial_coordinator_work_may_be_unknown=inflight['phase'] == 'coordinator_call',
                        partial_local_work_may_be_unknown=inflight['phase'] == 'local_decision')
    row = dict(arm=arm, world=int(world), tape=int(tape), policy_sha256=policy_sha,
               **episode_metrics(raw, base_arm(arm)), mean_height_m=float(raw['positions'][1:, :, 2].mean()),
               **times, policy_counts=team.counts(),
               coordinator_counts={key: int(raw['coord_' + key].sum()) for key in COORD_COUNTERS},
               scheduler_wall_seconds=float(raw['coord_wall_seconds'].sum()),
               scheduler_cpu_seconds=float(raw['coord_cpu_seconds'].sum()), raw=identity,
               initial_state_sha256=array_digest(raw['positions'][0], users),
               bundle_sha256=array_digest(bundle['public'], bundle['private_depart'], bundle['private_tail'])
               if family != 'C' else None, cpu_seconds=cpu_clock() - start_cpu, wall_seconds=clock() - start_wall)
    counts['complete_episodes'] += 1
    inflight.clear()
    return row, raw if training else None
