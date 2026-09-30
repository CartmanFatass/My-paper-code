"""Independent saved-record recurrence and inherited bounded physical reader."""
import numpy as np
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.read import assert_close, radio
from experiments.candidates.uav_registered_service.b01.read import verify_periodic, compare_metrics
from experiments.candidates.uav_service_age.b01 import read as age_reader
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b02.metrics import episode_metrics
from experiments.candidates.uav_user_waiting.b02.read import (
    advance,check_history,native_key,two_orders,verify_post_c_nav,verify_stage as previous_verify_stage)
from .collector import value_diagnostics
from .features import pack_features


def reference_features(*,sites,positions,commands,mask,previous_nav,last,maximum,windows,tick):
    # A second numerical expression of the frozen basis; no history or scheduler API.
    age=np.zeros(50) if tick==0 else tick-1-np.asarray(last)
    a,b=age/256.,np.asarray(maximum)/256.
    slack=b-a
    active=np.array([bool(mask & (1<<i)) for i in range(5)])
    xy=np.asarray(sites)[:,:2,None]-np.asarray(positions)[active,:2].T[None,:,:]
    squared=(xy*xy).sum(axis=1)+np.asarray(positions)[active,2][None,:]**2
    d=np.sqrt(squared.min(axis=1))/np.sqrt(1000.**2+1000.**2+150.**2)
    nav=np.zeros((5,10));nav[np.arange(5),previous_nav.astype(int)]=1.
    member=np.zeros(5);member[(tick//4)%5]=1.
    relations=np.column_stack([d,d*d,slack,d*a,d*slack]).ravel()
    pooled=[a.mean(),(a*a).mean(),b.mean(),(b*b).mean(),slack.mean(),(slack*slack).mean(),d.mean(),(d*d).mean(),(d*a).mean(),(d*slack).mean()]
    return np.concatenate([np.asarray(sites)[:,:2].ravel()/1000.,
        ((positions-p.LOW)/(p.HIGH-p.LOW)).ravel(),np.asarray(commands).ravel(),active,
        nav.ravel(),a,b,np.asarray(windows).ravel(),np.asarray(last)<0,[1.,1.,1.],
        [tick/256.,(256-tick)/256.],member,relations,pooled]).astype(np.float32)


def verify_stage(stage,sites,*,value=None,arm,horizon,full_physics=False,extra_physics=()):
    # Frozen reader reconstructs physics, delivered4 costs and O/W/S keys. The G
    # search is checked below only after independently rebuilding its new keys.
    ordinary=dict(stage,searches={k:v for k,v in stage['searches'].items() if k!='G'})
    selected=list(extra_physics)+[s['selected_pair'] for s in stage['searches'].values() if s['completed']]
    checked=previous_verify_stage(ordinary,sites,full_physics=full_physics,extra_physics=selected)
    tick=stage['tick'];last=stage['input_history']['last'].copy()
    maximum=stage['input_maximum'].copy(); prefix_age=0
    for offset,contacts in enumerate(stage['prefix_contacts'][:stage['prefix_count']]):
        last[contacts]=tick+offset
        ages=tick+offset-last
        maximum=np.maximum(maximum,ages);prefix_age+=int(ages.sum())
    np.testing.assert_array_equal(stage['prefix_maximum'],maximum)
    assert stage['elapsed_prefix_age_cost']==prefix_age
    checked['keys']['G']={}; checked['zero_keys']={}
    for i,pair_array in enumerate(stage['evaluated_pairs']):
        pair=tuple(map(int,pair_array));q,mask=pair
        pl,pm=last.copy(),maximum.copy()
        windows=stage['prefix_history']['windows'].copy()
        midpoint=None
        for slot,contacts in enumerate(stage['contacts'][i]):
            k=tick+2+slot;pl[contacts]=k;windows[k//64]|=contacts
            pm=np.maximum(pm,k-pl)
            if slot==1: midpoint=(pl.copy(),pm.copy(),windows.copy())
        ml,mm,mw=midpoint
        np.testing.assert_array_equal(stage['midpoint_maximum'][i],mm)
        np.testing.assert_array_equal(stage['endpoint_maximum'][i],pm)
        inc=float((mm-stage['input_maximum']).mean())
        age=prefix_age+int(stage['age_sum'][i,:2].sum())
        assert stage['elapsed_increment'][i]==inc and stage['elapsed_age_cost'][i]==age
        ties=native_key(pair,stage['native'][i],p.command_index(stage['proposals'][stage['member']]))
        zero=(-inc,-age)+ties
        assert_close(stage['zero_key'][i],zero,0)
        checked['zero_keys'][pair]=zero
        if not stage['value_valid'][i]:
            assert np.isnan(stage['value_raw'][i]) and np.isnan(stage['keys']['G'][i]).all()
            continue
        commands=stage['proposals'].copy();commands[stage['member']]=COMMANDS[q]
        future=tick+4
        if future>=horizon or arm=='G0': raw=clipped=0.
        else:
            args=dict(sites=sites,positions=np.rint(stage['forecast'][q,1]),commands=commands,
                      mask=mask,previous_nav=stage['nav'],last=ml,maximum=mm,windows=mw,tick=future)
            x=reference_features(**args)
            np.testing.assert_array_equal(x,pack_features(**args,history_start=0,history_after=future))
            raw,clipped=value.evaluate(x,future)
        assert_close(stage['value_raw'][i],raw,0)
        assert_close(stage['value_clipped'][i],clipped,0)
        assert bool(stage['value_was_clipped'][i])==(raw!=clipped)
        assert stage['total_cost'][i]==inc+clipped
        key=(-inc-clipped,-age)+ties
        assert_close(stage['keys']['G'][i],key,0)
        assert_close(stage['zero_key'][i],zero,0)
        checked['keys']['G'][pair]=key;checked['zero_keys'][pair]=zero
    search=stage['searches'].get('G')
    if search and search['completed']:
        choice,motion,mask,requests=two_orders(checked['keys']['G'],stage['current_mask'],p.command_index(stage['proposals'][stage['member']]))
        for name,pair in (('selected_pair',choice),('motion_pair',motion),('mask_pair',mask)):
            np.testing.assert_array_equal(search[name],pair)
        begin,end=search['request_start'],search['request_end']
        np.testing.assert_array_equal(stage['request_pairs'][begin:end],requests)
        assert end-begin==116 and np.all(stage['request_orderings'][begin:end]=='G')
    return checked


def verify_decisions(row, raw, records, value_model=None):
    steps, arm = row['steps'], row['arm']
    sites = p.decode_map(raw['map_packet'].tobytes())
    anchors, last, windows = {}, np.full(50, -1, dtype=np.int64), np.zeros((4, 50), bool)
    burden = np.zeros(50, dtype=np.int64)
    maximum = np.zeros(50, dtype=np.int64)
    predicted, valid = np.zeros((steps, 50), bool), np.zeros(steps, bool)
    cursor, position, start, physics_pairs = 0, None, None, 0
    diagnostics, history_errors = [], []

    def settle(stop):
        nonlocal cursor, position
        while cursor < stop:
            origin = anchors.get(cursor, position)
            assert origin is not None
            position = np.clip(origin + 30 * raw['commands'][cursor], p.LOW, p.HIGH)
            _, connected, _ = radio(position, sites, int(raw['mask'][cursor]))
            served = connected.any(axis=0)
            predicted[cursor], valid[cursor] = served, True
            advance(last, windows, burden, cursor, served)
            np.maximum(maximum, cursor-last, out=maximum)
            cursor += 1
        if stop in anchors:
            position = anchors[stop].copy()

    assert len(records) == steps // 4
    for index, record in enumerate(records):
        tick = index * 4
        assert record['arm'] == arm and record['tick'] == tick and record['horizon'] == steps
        assert record['history_before'] == cursor
        sent = len(record['report_packets']) > 0
        if sent:
            packets = tuple(packet.tobytes() for packet in record['report_packets'])
            assert packets == p.encode_reports(raw['observations'][tick, :, :3], raw['commands'][tick],
                                                raw['proposals'][tick], tick, raw['post_c_nav'][index])
            np.testing.assert_array_equal(record['report_packets'], raw['report_packets'][index])
        else:
            assert not raw['report_packets'][index].any()
        if record['decoded_anchor']:
            assert sent
            decoded, committed, proposed, nav = p.decode_reports(packets, tick)
            for name, value in (('positions', decoded), ('actual', committed), ('proposals', proposed), ('nav', nav)):
                np.testing.assert_array_equal(record['decoded_' + name], value)
            anchors[tick] = decoded.copy()
            if start is None:
                start, cursor, position = tick, tick, decoded.copy()
        after = int(record['history_after'])
        assert cursor <= after <= tick
        assert record['counts']['history_reductions'] == after - cursor
        settle(after)
        assert record['history_start'] == (-1 if start is None else start)
        for name, value in (('last', last), ('windows', windows), ('burden', burden), ('maximum', maximum)):
            np.testing.assert_array_equal(record['history_' + name], value)
        assert record['burden_unknown'] == (start is not None and start > 0)
        if record['snapshot_valid']:
            assert after == tick and record['decoded_anchor']
            if start == 0:
                error = burden - raw['actual_ages'][:tick].sum(axis=0, dtype=np.int64)
                history_errors.append(dict(tick=tick, differing_users=int(np.count_nonzero(error)),
                                           max_absolute_error=int(np.abs(error).max())))
        current = record['current']
        checked = None
        if current:
            assert record['snapshot_valid']
            check_history(current['input_history'], start, last, windows, burden)
            for key in ('positions', 'actual', 'proposals', 'nav'):
                np.testing.assert_array_equal(current[key], record['decoded_' + key])
            assert current['tick'] == tick and current['length'] == min(4, steps - tick - 2)
            assert current['current_mask'] == raw['mask'][tick]
            np.testing.assert_array_equal(current['input_maximum'],maximum)
            checked = verify_stage(current, sites, value=value_model, arm=arm, horizon=steps,
                                   full_physics=tick in (0,60,124,248),
                                   extra_physics=[record['requested_pair']])
            physics_pairs += checked['candidate_physics_pairs']
        assert not record['branches'] and not record['continuation_used']
        if current and current['completed']:
            assert checked is not None
            if arm == 'S':
                requested = tuple(map(int,current['searches']['S']['selected_pair']))
                np.testing.assert_array_equal(record['s_pair'],requested)
                assert not record['value_eligible']
            else:
                finalists = [tuple(map(int,current['searches'][label]['selected_pair'])) for label in ('O','W')]
                requested = max(finalists,key=lambda pair:checked['keys']['W'][pair])
                np.testing.assert_array_equal(record['m_pair'],requested)
                if arm in ('G0','LR','LN'):
                    if start == 0:
                        assert record['value_eligible'] and not record['missing_maximum_m_fallback']
                        g = tuple(map(int,current['searches']['G']['selected_pair']))
                        requested = max((g,requested),key=lambda pair:checked['keys']['G'][pair])
                        queried = [tuple(map(int,pair)) for pair in current['evaluated_pairs']]
                        zero = max(queried,key=lambda pair:checked['zero_keys'][pair])
                        np.testing.assert_array_equal(record['visited_zero_pair'],zero)
                        assert tuple(current['request_pairs'][-1]) == tuple(record['m_pair'])
                        assert len(current['request_pairs']) == 349
                    else:
                        assert record['missing_maximum_m_fallback'] and not record['value_eligible']
                if record['perturbation_applied']:
                    assert arm == 'M' and tick == int(raw['perturbation_tick'])
                    requested = tuple(map(int,raw['perturbation_pair']))
            if np.all(record['requested_pair'] >= 0):
                assert tuple(record['requested_pair']) == requested
        if record['timely']:
            assert raw['timely'][index] and record['fallback_reason'] == ''
            q, mask = map(int, record['requested_pair'])
            assert q == raw['selected_q'][index] and mask == raw['selected_mask'][index]
            commands = record['decoded_proposals'].copy()
            commands[(tick // 4) % 5] = COMMANDS[q]
            assert p.decode_command(record['delivered_command_packet'].tobytes(), tick) == (mask, (tick // 4) % 5, q)
            assert record['wall_seconds'] <= p.DEADLINE_SECONDS
        else:
            assert not raw['timely'][index] and record['fallback_reason']
            commands, mask = raw['commands'][tick], int(raw['mask'][tick])
            assert raw['selected_q'][index] == raw['selected_mask'][index] == -1
            assert len(record['delivered_command_packet']) == 0
        np.testing.assert_array_equal(record['returned_commands'], commands)
        np.testing.assert_array_equal(raw['commitments'][index], commands)
        assert record['returned_mask'] == raw['applied_mask'][index] == mask
        length = raw['command_packet_lengths'][index]
        np.testing.assert_array_equal(raw['command_packets'][index, :length], record['delivered_command_packet'])
        assert not raw['command_packets'][index, length:].any()
        assert raw['round_bytes'][index] == (125 if sent else 0) + len(record['delivered_command_packet'])
        assert raw['scheduler_wall'][index] == record['wall_seconds']
        assert raw['scheduler_cpu'][index] == record['cpu_seconds']
        assert record['wall_seconds'] + 1e-12 >= raw['c_wall'][tick]
        assert record['cpu_seconds'] + 1e-12 >= raw['c_cpu'][tick]
        assert record['actual_timeout'] == (record['wall_seconds'] > p.DEADLINE_SECONDS)
        for unit in ('wall', 'cpu'):
            values = list(record['phase_' + unit].values())
            assert all(np.isfinite(value) and value >= 0 for value in values)
            assert sum(values) <= record[unit + '_seconds'] + 1e-9
        stages = ([current] if current else []) + [branch['continuation'] for branch in record['branches'].values() if branch['continuation']]
        counts = record['counts']
        assert counts['candidate_requests'] == sum(len(stage['request_pairs']) for stage in stages)
        assert counts['candidate_plans'] == sum(len(stage['evaluated_pairs']) for stage in stages)
        assert counts['state_reductions'] == sum(len(stage['evaluated_pairs']) * stage['length'] + len(stage['partial'].get('contacts', [])) for stage in stages)
        assert counts['geometry_snapshots'] == sum(int(stage['geometry_count_by_q'].sum()) for stage in stages)
        assert counts['prefix_ticks'] == sum(stage['prefix_count'] for stage in stages)
        assert counts['virtual_c_decisions'] == sum(branch['virtual_c_count'] for branch in record['branches'].values())
        assert counts['candidate_cache_hits'] + counts['candidate_uncached_requests'] == counts['candidate_requests']
        assert counts['interrupted_candidate_requests'] == counts['candidate_uncached_requests'] - counts['candidate_plans']
        for name in ('candidate_requests', 'candidate_plans', 'state_reductions', 'geometry_snapshots', 'prefix_ticks'):
            assert raw[name][index] == counts[name]
        assert not record['c_diagnostics_valid']
        assert counts['virtual_c_decisions'] == 0
        value_count = int(current['value_valid'].sum()) if current else 0
        expected_queries = value_count if arm in ('LR','LN') and tick+4<steps else 0
        assert counts['value_queries'] == counts['feature_rows'] == expected_queries
        assert counts['terminal_value_zeros'] == (value_count if tick+4==steps else 0)
    before = cursor
    if start is not None:
        settle(steps)
    assert raw['terminal_history_reductions'] == cursor - before
    assert raw['terminal_history_start'] == (-1 if start is None else start)
    assert bool(raw['terminal_history_complete']) == (start is not None and cursor == steps)
    assert bool(raw['terminal_burden_unknown']) == (start is not None and start > 0)
    for key, value in (('model_valid', valid), ('model_contacts', predicted), ('terminal_last', last),
                       ('terminal_windows', windows), ('terminal_burden', burden), ('terminal_maximum',maximum)):
        np.testing.assert_array_equal(raw[key], value)
    return dict(verified_model_transitions=int(valid.sum()), candidate_physics_pairs=physics_pairs,
                continuation_slots=diagnostics, settled_burden_errors=history_errors,
                terminal_model_minus_actual_burden=(burden - raw['actual_ages'].sum(axis=0, dtype=np.int64)).tolist() if start == 0 else None,
                physics_scope='all evaluated selected plans and search winners; all evaluated candidates at0/60/124/248; all completed cost/key arithmetic; perturbation native execution checked separately',
                kernel_scope='shared native radio; independent history/cost/ranking/trajectory reconstruction; frozen independent observation reader')


def verify_episode(row, raw, *, value=None, verify_observations=True):
    assert str(raw['program']) == row['arm'] and int(raw['world_seed']) == row['seed']
    records = unpack_records(raw)
    result = age_reader.verify_native(row, raw, verify_observations=verify_observations)
    verify_post_c_nav(raw)
    verify_periodic(row, raw)
    age_reader.verify_age(row, raw)
    result.update(verify_decisions(row, raw, records, value_model=value))
    users = raw['actual_ages'].sum(axis=0, dtype=np.int64) / row['steps']
    assert_close(row['F_user'], users.max(), 0)
    assert_close(row['per_user_mean_age'], users, 0)
    for key, value in episode_metrics(raw, row['steps'], row['arm'], records).items():
        compare_metrics(value, row[key])
    for key,item in value_diagnostics(records).items():
        compare_metrics(item,row[key])
    maximum=np.maximum.accumulate(raw['actual_ages'],axis=0)
    assert_close(float(maximum[-1].mean()),row['mean_user_max_unserved_gap'],0)
    increments=np.diff(np.vstack([np.zeros((1,50),np.int64),maximum]),axis=0)
    np.testing.assert_array_equal(increments.sum(axis=0),maximum[-1])
    result.update(arm=row['arm'], seed=row['seed'], value_replays=sum(r['counts']['value_queries'] for r in records))
    return result
