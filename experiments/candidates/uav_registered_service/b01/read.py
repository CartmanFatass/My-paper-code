#!/usr/bin/env python3
"""Saved-data causal reconstruction, no environment steps or new search panel."""

import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import numpy as np
from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.read import assert_close, observed_rows, radio
from experiments.candidates.uav_radio_activation.b01.protocol import ALL_ON, HORIZON, N, U, encode_map
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_radio_activation.b03.read import verify_episode as verify_frozen
from experiments.candidates.uav_radio_activation.b03.study import block_positions
from experiments.candidates.uav_registered_service.b01.study import ARMS, ARM_ORDERS, SEED, WORLDS, episode_metrics, file_identity, paired_reading, write_json
from experiments.candidates.uav_registered_service.b01.metrics import periodic_metrics, contact_gaps, window_bits


def compare_metrics(actual, expected):
    if isinstance(actual,dict):
        if set(actual)!=set(expected):
            raise AssertionError('different metric keys')
        for key in actual:
            compare_metrics(actual[key],expected[key])
    elif isinstance(actual,str):
        if actual!=expected:
            raise AssertionError('different metric scope')
    elif actual is None:
        if expected is not None:
            raise AssertionError('different absent metric')
    else:
        assert_close(actual,expected,1e-12)


def selection(keys, key_length, current_mask, proposal_q):
    requested=[]
    def key(pair):
        value=keys[pair][:key_length]
        if not np.isfinite(value).all():
            raise AssertionError('inner choice used uncompleted history key')
        return tuple(value)
    def choose(pairs):
        pairs=list(pairs)
        requested.extend(pairs)
        return sorted(pairs,key=key)[-1]
    q,_=choose((q,current_mask) for q in range(27))
    first=choose((q,mask) for mask in range(1,32))
    _,mask=choose((proposal_q,mask) for mask in range(1,32))
    second=choose((q,mask) for q in range(27))
    return max((first,second),key=key),list(dict.fromkeys(requested))


def verify_periodic(row,raw):
    contacts=raw['connections'].any(axis=1)
    np.testing.assert_array_equal(raw['actual_contacts'],contacts)
    # Independent scalar periodic accumulation and continuous gaps.
    bits=np.zeros(((len(contacts)+63)//64,50),dtype=bool)
    events,gaps=[],[]
    for user in range(50):
        start=None
        for tick in range(len(contacts)+1):
            contact=tick<len(contacts) and bool(contacts[tick,user])
            if contact:
                bits[tick//64,user]=True
                events.append((user,tick))
            if tick<len(contacts) and not contact and start is None:
                start=tick
            if (contact or tick==len(contacts)) and start is not None:
                gaps.append((user,start,tick,tick-start,int(start==0),int(tick==len(contacts))))
                start=None
    np.testing.assert_array_equal(raw['actual_window_bits'],bits)
    np.testing.assert_array_equal(raw['contact_events'],np.array(events,dtype=int).reshape(-1,2))
    np.testing.assert_array_equal(raw['unserved_gap_rows'],np.array(gaps,dtype=int).reshape(-1,6))
    if row['F']!=int(bits.sum()) or row['per_window_coverage']!=bits.sum(axis=1).tolist():
        raise AssertionError('periodic endpoint mismatch')


def verify_history_episode(row, raw, *, verify_observations=True):
    arm, steps = row['arm'], int(raw['completed_steps'])
    if steps != row['steps'] or steps != raw['commands'].shape[0]:
        raise AssertionError('incomplete raw cannot support a complete endpoint')
    expected_c = np.ones(steps, dtype=bool) if arm == 'R' else np.arange(steps) % p.HOLD == 0
    np.testing.assert_array_equal(raw['c_called'], expected_c)
    np.testing.assert_array_equal(raw['c_decision'], expected_c & (np.arange(steps) % 4 == 0))
    if verify_observations:
        terminal_obs = observed_rows(raw['positions'][-1], raw['true_sites'], int(raw['mask'][-1]), steps)
        terminal_obs[:, -1] = 1.0
        assert_close(raw['observations'][-1], terminal_obs, 1e-6)
    if raw['map_packet'].tobytes() != encode_map(raw['true_sites']):
        raise AssertionError('map binding mismatch')
    rng = np.random.RandomState(row['seed'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)] for _ in range(N)])
    sites = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
    np.testing.assert_array_equal(initial, raw['positions'][0])
    np.testing.assert_array_equal(sites, raw['true_sites'])
    assert_close(raw['positions'][1:], np.clip(raw['positions'][:-1] + raw['commands'] * 30, p.LOW, p.HIGH), 0)
    controllers = [LocalController(history=False) for _ in range(N)]
    proposals = np.zeros((N, 3))
    pairs = None
    max_j_error = max_sinr_error = max_obs_error = 0.0
    current_mask = ALL_ON
    actual = None
    report_age = []
    origin = 0
    has_delivered_plan = False
    startup_hold_ticks = 0
    rounds = int(raw['round_count'])
    if rounds != steps // p.HOLD:
        raise AssertionError('incorrect proposal exposure')
    for tick in range(steps):
        if int(raw['mask'][tick]) != current_mask:
            raise AssertionError('mask arrived early or was held incorrectly')
        if tick >= p.DELIVERY:
            report_age.append(tick - origin)
            startup_hold_ticks += int(not has_delivered_plan)
        if verify_observations:
            expected_obs = observed_rows(raw['positions'][tick], sites, current_mask, tick)
            expected_obs[:, -1] = tick / steps
            assert_close(raw['observations'][tick], expected_obs, 1e-6)
            max_obs_error = max(max_obs_error, float(np.max(np.abs(raw['observations'][tick] - expected_obs))))
        if expected_c[tick]:
            pairs = [controller.act(raw['observations'][tick, i], tick) for i, controller in enumerate(controllers)]
            proposals = np.array([pair[0] for pair in pairs])
        np.testing.assert_array_equal(proposals, raw['proposals'][tick])
        for key in ('fallback', 'selected_index'):
            np.testing.assert_array_equal([pair[1][key] for pair in pairs], raw[key][tick])
        obs = raw['observations'][tick]
        np.testing.assert_array_equal(raw['n_current'][tick], (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1))
        np.testing.assert_array_equal(raw['n_visible_peers'][tick], (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1))
        if tick == 0:
            actual = proposals.copy()
        np.testing.assert_array_equal(actual, raw['commands'][tick])
        sinr, connected, metrics = radio(raw['positions'][tick + 1], sites, current_mask)
        assert_close(raw['sinr'][tick], sinr)
        np.testing.assert_array_equal(raw['connections'][tick], connected)
        assert_close([raw['reward'][tick], raw['served'][tick], raw['quality'][tick]],
                     [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        max_j_error = max(max_j_error, abs(float(raw['reward'][tick]) - metrics['J']))
        finite = np.isfinite(sinr)
        max_sinr_error = max(max_sinr_error, float(np.max(np.abs(raw['sinr'][tick][finite] - sinr[finite]))))
        if tick + 1 >= p.DELIVERY and (tick + 1 - p.DELIVERY) % p.HOLD == 0:
            index = (tick + 1 - p.DELIVERY) // p.HOLD
            current_mask = int(raw['applied_mask'][index])
            actual = raw['commitments'][index]
            if raw['timely'][index]:
                origin = int(raw['round_tick'][index])
                has_delivered_plan = True
    for key, value in row['controller_counts'].items():
        if sum(c.counters[key] for c in controllers) != value:
            raise AssertionError(f'C counter mismatch: {key}')
    np.testing.assert_array_equal(raw['controller_counts'], [row['controller_counts'][str(k)] for k in raw['controller_counter_keys']])

    # Separate causal replay: neither actor History nor its update/ordering methods are used.
    sites=p.decode_map(raw['map_packet'].tobytes())
    anchors={}
    last=np.full(U,-1,dtype=int)
    windows=np.zeros((4,U),dtype=bool)
    next_unsettled=0
    position=None
    predicted=np.zeros((steps,U),dtype=bool)
    valid=np.zeros(steps,dtype=bool)
    physics_pairs=0
    model_start=None

    def settle(stop):
        nonlocal position,next_unsettled
        while next_unsettled<stop:
            tick=next_unsettled
            origin=anchors.get(tick,position)
            if origin is None:
                raise AssertionError('settled transition without lawful prior anchor')
            position=np.clip(origin+30*raw['commands'][tick],p.LOW,p.HIGH)
            _,connected,_=radio(position,sites,int(raw['mask'][tick]))
            served=connected.any(axis=0)
            predicted[tick]=served
            valid[tick]=True
            last[served]=tick
            windows[tick//64]|=served
            next_unsettled+=1
        if stop in anchors:
            position=anchors[stop].copy()

    for index in range(rounds):
        tick=4*index
        length=min(4,steps-tick-2)
        member=index%N
        proposal_q=p.command_index(raw['proposals'][tick,member])
        current_mask=int(raw['mask'][tick])
        if int(raw['history_before'][index])!=next_unsettled or raw['round_tick'][index]!=tick:
            raise AssertionError('history/report cursor identity mismatch')
        report_sent=bool(raw['report_packets'][index].any())
        if report_sent:
            packets=tuple(x.tobytes() for x in raw['report_packets'][index])
            if packets!=p.encode_reports(raw['observations'][tick,:,:3],raw['commands'][tick],raw['proposals'][tick],tick):
                raise AssertionError('illegal report inputs')
            decoded,actual_wire,proposal_wire=p.decode_reports(packets,tick)
        if raw['decoded_anchor'][index]:
            if not report_sent:
                raise AssertionError('hidden unsent anchor')
            anchors[tick]=decoded.copy()
            if model_start is None:
                model_start=tick
                next_unsettled=tick
                position=decoded.copy()
        after=int(raw['history_after'][index])
        if not next_unsettled<=after<=tick:
            raise AssertionError('settlement skipped or included unexecuted transitions')
        expected_start=-1 if model_start is None else model_start
        if raw['history_start'][index]!=expected_start:
            raise AssertionError('model start/censored prefix identity mismatch')
        np.testing.assert_array_equal(raw['window_valid'][index],np.arange(4)*64 >= (256 if model_start is None else model_start))
        if int(raw['history_reductions'][index])!=after-next_unsettled:
            raise AssertionError('history work mismatch')
        settle(after)
        np.testing.assert_array_equal(raw['unknown_age'][index],(last==-1) & (model_start is not None and model_start>0))
        if raw['snapshot_valid'][index]:
            if after!=tick or not raw['decoded_anchor'][index]:
                raise AssertionError('planning snapshot used unsettled history')
            np.testing.assert_array_equal(raw['snapshot_last'][index],last)
            np.testing.assert_array_equal(raw['snapshot_windows'][index],windows)
        key_length=int(raw['key_length'][index])
        scores=raw['candidate_scores'][index]
        plans=int(raw['candidate_plans'][index])
        order=[tuple(map(int,pair)) for pair in raw['candidate_order'][index,:plans]]
        if int(raw['candidate_requests'][index])!=int(raw['candidate_cache_hits'][index]+raw['candidate_uncached_requests'][index]):
            raise AssertionError('explicit candidate request accounting mismatch')
        if int(raw['interrupted_candidate_requests'][index])!=int(raw['candidate_uncached_requests'][index])-plans:
            raise AssertionError('abandoned candidate accounting mismatch')
        if len(set(order))!=plans or np.count_nonzero(np.isfinite(scores[:,:,0]))!=plans:
            raise AssertionError('candidate score/count mismatch')
        if raw['forecast_lengths'][index]!=length or not np.isnan(raw['forecast'][index,:,length:]).all():
            raise AssertionError('terminal forecast extent mismatch')
        if key_length and not raw['prefix_valid'][index]:
            raise AssertionError('keys without complete private prefix')
        if key_length:
            prefix_last,prefix_windows=last.copy(),windows.copy()
            prefix_position=decoded.copy()
            for offset in range(2):
                prefix_position=np.clip(prefix_position+actual_wire*30,p.LOW,p.HIGH)
                _,connected,_=radio(prefix_position,sites,current_mask)
                served=connected.any(axis=0)
                prefix_last[served]=tick+offset
                prefix_windows[(tick+offset)//64]|=served
            np.testing.assert_array_equal(raw['prefix_last'][index],prefix_last)
            np.testing.assert_array_equal(raw['prefix_windows'][index],prefix_windows)
            age_values=sorted(set(prefix_last.tolist()))
            expected_length=len(age_values)+6+int(arm=='P')
            if key_length!=expected_length:
                raise AssertionError('age ordering omitted a group')
            forecast=np.array([block_positions(prefix_position,np.array([
                COMMANDS[q] if i==member else proposal_wire[i] for i in range(N)]),length) for q in range(27)])
            assert_close(raw['forecast'][index,:,:length],forecast,0)
            for q,mask in order:
                contacts=raw['candidate_contacts'][index,q,mask,:length]
                if raw['candidate_contacts'][index,q,mask,length:].any():
                    raise AssertionError('fictional terminal contacts')
                candidate_windows=prefix_windows.copy()
                new_pairs=0
                for slot,served in enumerate(contacts):
                    window=(tick+2+slot)//64
                    if window*64>=model_start:
                        new_pairs+=int((served & ~candidate_windows[window]).sum())
                    candidate_windows[window]|=served
                distinct=contacts.any(axis=0)
                counts=[int(distinct[prefix_last==age].sum()) for age in age_values]
                assert_close(scores[q,mask,1],float(contacts.sum(axis=1).mean()),1e-12)
                assert_close(scores[q,mask,0],.7*scores[q,mask,1]/50+.3*scores[q,mask,2],1e-12)
                expected=((new_pairs,) if arm=='P' else ())+tuple(counts)+(
                    float(scores[q,mask,0]),float(scores[q,mask,1]),int(q==proposal_q),
                    mask.bit_count(),-mask,-q)
                assert_close(raw['ordering_keys'][index,q,mask,:key_length],expected,0)
                if not np.isnan(raw['ordering_keys'][index,q,mask,key_length:]).all():
                    raise AssertionError('ordering padding not empty')
            subset=set(order) if tick in (0,60,124,252) else set()
            selected_q=int(raw['selected_q'][index])
            selected_mask=int(raw['selected_mask'][index])
            if raw['timely'][index]:
                subset.add((selected_q,selected_mask))
            for q,mask in sorted(subset):
                values=[]
                for slot,point in enumerate(forecast[q]):
                    _,connected,metrics=radio(point,sites,mask)
                    np.testing.assert_array_equal(raw['candidate_contacts'][index,q,mask,slot],connected.any(axis=0))
                    values.append((metrics['J'],metrics['served'],metrics['quality']))
                assert_close(scores[q,mask],np.mean(values,axis=0),1e-12)
                physics_pairs+=1
        if raw['scheduler_wall'][index]+1e-12<raw['c_wall'][tick] or raw['scheduler_cpu'][index]+1e-12<raw['c_cpu'][tick]:
            raise AssertionError('O/P deadline omitted C proposal')
        if raw['timely'][index]:
            selected,expected_order=selection(raw['ordering_keys'][index],key_length,current_mask,proposal_q)
            if not key_length or order!=expected_order or selected!=(selected_q,selected_mask):
                raise AssertionError('history sequential selection mismatch')
            mask,received_member,q=p.decode_command(raw['command_packets'][index].tobytes(),tick)
            if (q,mask)!=selected or received_member!=member:
                raise AssertionError('history command/selection mismatch')
            commands=proposal_wire.copy()
            commands[member]=COMMANDS[q]
            np.testing.assert_array_equal(raw['commitments'][index],commands)
            np.testing.assert_array_equal(raw['sequential_pair'][index],selected)
            assert_close(raw['sequential_score'][index],scores[selected],0)
            if raw['applied_mask'][index]!=mask or raw['round_bytes'][index]!=136 or raw['scheduler_wall'][index]>p.DEADLINE_SECONDS:
                raise AssertionError('incorrect timely arrival')
            if raw['candidate_requests'][index]!=116 or raw['state_reductions'][index]!=length*plans or raw['geometry_snapshots'][index]!=27*length:
                raise AssertionError('completed O/P search work mismatch')
            if raw['fallback_reason'][index]!='':
                raise AssertionError('timely result has fallback reason')
        else:
            if raw['selected_q'][index]!=-1 or raw['selected_mask'][index]!=-1 or raw['command_packets'][index].any():
                raise AssertionError('timeout retained partial plan')
            np.testing.assert_array_equal(raw['commitments'][index],raw['commands'][tick])
            if raw['applied_mask'][index]!=current_mask or raw['round_bytes'][index]!=(120 if report_sent else 0):
                raise AssertionError('timeout changed team/mask or traffic')
    terminal_before=next_unsettled
    if position is not None or 0 in anchors:
        settle(steps)
    if int(raw['terminal_history_reductions'])!=next_unsettled-terminal_before:
        raise AssertionError('terminal support work mismatch')
    if int(raw['terminal_history_start'])!=(-1 if model_start is None else model_start):
        raise AssertionError('terminal censored origin mismatch')
    if bool(raw['terminal_history_complete'])!=(model_start is not None and next_unsettled==steps):
        raise AssertionError('terminal support completeness mismatch')
    np.testing.assert_array_equal(raw['model_contacts'],predicted)
    np.testing.assert_array_equal(raw['model_valid'],valid)
    np.testing.assert_array_equal(raw['terminal_last'],last)
    np.testing.assert_array_equal(raw['terminal_windows'],windows)
    for key,value in episode_metrics(raw,steps,arm).items():
        compare_metrics(value,row[key])
    verify_periodic(row,raw)
    return dict(arm=arm,seed=row['seed'],verified_steps=steps,
                verified_model_transitions=int(valid.sum()),candidate_physics_pairs=physics_pairs,
                candidate_physics_scope='all selected pairs; all evaluated pairs at reports0,60,124,252; all stored ordering keys',
                kernel_scope='shared native radio kernels; causal loop and key arithmetic independently reconstructed',
                max_native_J_error=max_j_error,max_native_sinr_error=max_sinr_error,max_observation_error=max_obs_error)


def verify_episode(row,raw,**kwargs):
    if row['arm'] in ('R','S2','T2'):
        if row['arm']=='R' and row['steps']!=256 and kwargs.get('verify_observations',True):
            for tick in range(row['steps']+1):
                mask=int(raw['mask'][min(tick,row['steps']-1)])
                observation=observed_rows(raw['positions'][tick],raw['true_sites'],mask,tick)
                observation[:,-1]=tick/row['steps']
                assert_close(raw['observations'][tick],observation,1e-6)
            kwargs=dict(kwargs,verify_observations=False)
        result=verify_frozen(row,raw,**kwargs)
        verify_periodic(row,raw)
        for key,value in episode_metrics(raw,row['steps'],row['arm']).items():
            compare_metrics(value,row[key])
        return result
    return verify_history_episode(row,raw,**kwargs)


def read_result(out):
    started,cpu_started=time.perf_counter(),time.process_time()
    out=Path(out)
    summary=json.loads((out/'summary.json').read_text())
    if summary['status']!='COMPLETE' or not summary['scientific_invocation']:
        raise ValueError('no complete fixed scientific panel to interpret')
    seeds=list(range(SEED,SEED+WORLDS))
    if summary['config']['seeds']!=seeds or summary['config']['horizon']!=HORIZON or summary['config']['arms']!=list(ARMS):
        raise AssertionError('changed panel')
    if summary['launch_sha']!=summary['config']['launch_sha']:
        raise AssertionError('source identity mismatch')
    expected=dict(constructors=1,explicit_resets=320,native_step_calls=81920,team_steps=81920,complete_episodes=320,fit_started=0,optimizer_steps=0)
    if summary['fixed_policy_evaluation_counts']!=dict(episodes=320,transitions=81920,optimizer_updates=0,parameter_updates=0):
        raise AssertionError('wrong fixed-policy evaluation exposure')
    if summary['counts']!=expected:
        raise AssertionError('wrong scientific exposure')
    if json.loads((out/'config.json').read_text())!=summary['config']:
        raise AssertionError('config differs from summary')
    if sorted(summary['artifacts'],key=lambda x:x['path'])!=sorted([row['raw'] for row in summary['rows']],key=lambda x:x['path']):
        raise AssertionError('raw manifest differs from rows')
    if [(row['arm'],row['seed']) for row in summary['rows']]!=[(arm,seed) for i,seed in enumerate(seeds) for arm in ARM_ORDERS[i%10]]:
        raise AssertionError('wrong fixed interleaving')
    if json.loads((out/'process-exit.json').read_text())['exit_code']!=0:
        raise AssertionError('worker did not exit successfully')
    rows,worlds=[],{}
    total_bytes=0
    for row in summary['rows']:
        path=Path(row['raw']['path'])
        identity=file_identity(path)
        if identity!=row['raw']:
            raise AssertionError('raw identity mismatch')
        total_bytes+=identity['bytes']
        with np.load(path,allow_pickle=False) as raw:
            world=(raw['true_sites'],raw['positions'][0])
            if row['seed'] in worlds:
                for left,right in zip(world,worlds[row['seed']]):
                    np.testing.assert_array_equal(left,right)
            else:
                worlds[row['seed']]=tuple(x.copy() for x in world)
            rows.append(verify_episode(row,raw))
        print(json.dumps(dict(verified=len(rows),arm=row['arm'],seed=row['seed'])),flush=True)
    paired=paired_reading(summary['rows'],seeds)
    if paired!=summary['paired']:
        raise AssertionError('paired reading differs from summary')
    result=dict(status='VERIFIED_COMPLETE',launch_sha=summary['launch_sha'],summary_sha256=file_identity(out/'summary.json')['sha256'],
                verified_raw_files=len(rows),verified_raw_bytes=total_bytes,rows=rows,paired=paired,
                scope='all native/C/actual periodic endpoints; all O/P executed histories and keys; declared candidate subset; no environment steps or fits',
                wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,rss_scope='reader lifetime peak; Linux KiB')
    write_json(out/'reading.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    read_result(parser.parse_args().out)
