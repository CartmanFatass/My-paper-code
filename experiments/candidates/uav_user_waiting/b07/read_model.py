"""Independent full-menu geometry, capacity key and wire/delivery verification."""

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss
from experiments.candidates.uav_user_waiting.b02 import protocol as wire
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records

MENU = tuple(mask for mask in range(1,32) if sum((mask>>i)&1 for i in range(5)) in (1,2))
SENTINEL = np.iinfo(np.int64).min


def full_menu(position, actual, proposals, sites, entering_mask, length, paid):
    prefixes, points, losses = [], [], []
    point = position.copy()
    for _ in range(2):
        point = np.maximum(wire.LOW, np.minimum(wire.HIGH, point+30.*actual))
        prefixes.append(point.copy())
        paid['reader_prefix_kinematic_ticks'] += 1
    for _ in range(length):
        point = np.maximum(wire.LOW, np.minimum(wire.HIGH, point+30.*proposals))
        points.append(point.copy())
        paid['modeled_geometry_attempts'] += 1
        paid['modeled_geometry_link_entries'] += 250
        losses.append(free_space_user_path_loss(point, sites))
        paid['modeled_geometry_completed'] += 1
    eligible = np.zeros((15,length,5,50), bool)
    keys = []
    for index, mask in enumerate(MENU):
        for slot in range(length):
            paid['modeled_physics_attempts'] += 1
            paid['modeled_sinr_link_entries'] += 250
            values = user_sinr_from_path_loss(losses[slot], transmitter_mask=wire.mask_array(mask))
            paid['modeled_physics_completed'] += 1
            assert np.isfinite(values[wire.mask_array(mask)]).all()
            assert np.isneginf(values[~wire.mask_array(mask)]).all()
            eligible[index,slot] = values >= 3.
            assert np.all(eligible[index,slot].sum(axis=0)<=1), 'LRS cardinality equivalence requires disjoint eligibility'
        capacity = sum(min(10,int(eligible[index,slot,member].sum())) for slot in range(length) for member in range(5))
        distinct = sum(bool(eligible[index,:,:,user].any()) for user in range(50))
        flips = sum(((mask^entering_mask)>>i)&1 for i in range(5))
        keys.append((capacity,distinct,-flips,-mask))
    return np.asarray(prefixes),np.asarray(points),eligible,keys


def verify_decisions(raw, paid):
    records = unpack_records(raw)
    steps = len(raw['commands'])
    assert len(records) == steps//4
    sites = wire.decode_map(raw['map_packet'].tobytes())
    total = {}
    for index,record in enumerate(records):
        tick, length = index*4,min(4,steps-index*4-2)
        assert record['tick']==tick and record['horizon']==steps and record['length']==length
        assert record['member']==index%5 and record['current_mask']==int(raw['mask'][tick])
        packets = wire.encode_reports(raw['observations'][tick,:,:3],raw['commands'][tick],
                                      raw['proposals'][tick],tick,raw['post_c_nav'][index])
        reports = np.asarray([np.frombuffer(packet,np.uint8) for packet in packets])
        position,actual,proposals,nav = wire.decode_reports(packets,tick)
        if len(record['report_packets']):
            np.testing.assert_array_equal(record['report_packets'],reports)
            np.testing.assert_array_equal(raw['report_packets'][index],reports)
        else:
            assert not record['decoded'] and not raw['report_packets'][index].any()
        if record['decoded']:
            for name,value in (('positions',position),('actual',actual),('proposals',proposals),('nav',nav)):
                np.testing.assert_array_equal(record['decoded_'+name],value)
            assert record['requested_q']==wire.command_index(proposals[index%5])
        prefix,forecast,eligibility,keys = full_menu(position,actual,proposals,sites,int(raw['mask'][tick]),length,paid)
        assert 0<=record['prefix_count']<=2 and 0<=record['forecast_count']<=length
        n_prefix,n_forecast=int(record['prefix_count']),int(record['forecast_count'])
        np.testing.assert_array_equal(record['prefix_positions'][:n_prefix],prefix[:n_prefix])
        assert np.isnan(record['prefix_positions'][n_prefix:]).all()
        np.testing.assert_array_equal(record['forecast'][:n_forecast],forecast[:n_forecast])
        assert np.isnan(record['forecast'][n_forecast:]).all()
        if n_forecast:
            assert n_prefix==2 and record['decoded']
        np.testing.assert_array_equal(record['mask_menu'],MENU)
        counts=record['counts']
        assert 0<=counts['candidate_requests']<=15
        np.testing.assert_array_equal(record['request_masks'],MENU[:counts['candidate_requests']])
        slots=record['completed_slots']
        assert slots.shape==(15,) and np.all((slots>=0)&(slots<=length))
        completed=record['candidate_completed']
        assert completed.dtype==bool and completed.shape==(15,)
        assert counts['candidate_plans']==int(completed.sum())
        assert counts['state_reductions']==int(slots.sum())
        assert counts['candidate_plans']<=counts['candidate_requests']
        np.testing.assert_array_equal(completed,np.arange(15)<int(completed.sum()))
        for candidate in range(15):
            n=int(slots[candidate])
            if n:
                assert candidate<counts['candidate_requests'] and n_forecast==length
                if candidate:
                    assert completed[candidate-1]
            np.testing.assert_array_equal(record['eligible_counts'][candidate,:n],eligibility[candidate,:n].sum(axis=2))
            assert np.all(record['eligible_counts'][candidate,n:]==-1)
            np.testing.assert_array_equal(record['distinct_users'][candidate],eligibility[candidate,:n].any(axis=(0,1)))
            if completed[candidate]:
                assert n==length
                np.testing.assert_array_equal(record['keys'][candidate],keys[candidate])
            else:
                assert np.all(record['keys'][candidate]==SENTINEL)
        expected_counts=dict(candidate_requests=counts['candidate_requests'],candidate_plans=int(completed.sum()),
            state_reductions=int(slots.sum()),geometry_attempts=n_forecast,geometry_snapshots=n_forecast,
            geometry_link_entries=n_forecast*250,radio_calls_attempted=int(slots.sum()),
            radio_calls_completed=int(slots.sum()),sinr_link_entries=int(slots.sum())*250,
            prefix_attempts=n_prefix,prefix_ticks=n_prefix,forecast_ticks=n_forecast)
        assert counts==expected_counts, (counts,expected_counts)
        for name,value in expected_counts.items():
            total[name]=total.get(name,0)+value
        chosen=max(range(15),key=lambda i:keys[i])
        if record['completed_calculation']:
            assert completed.all()
            assert record['selected_index']==chosen and record['selected_mask']==MENU[chosen]
            assert record['requested_mask']==MENU[chosen]
        else:
            assert record['selected_index']==record['selected_mask']==record['requested_mask']==-1
        assert np.isfinite(record['wall_seconds']) and record['wall_seconds']>=0
        assert np.isfinite(record['cpu_seconds']) and record['cpu_seconds']>=0
        assert record['actual_timeout']==(record['wall_seconds']>wire.DEADLINE_SECONDS)
        for timings in (record['phase_wall'],record['phase_cpu']):
            assert all(np.isfinite(value) and value>=0 for value in timings.values())
        timely=bool(record['timely'])
        assert bool(raw['timely'][index])==timely
        if timely:
            assert record['completed_calculation'] and not record['actual_timeout'] and record['fallback_reason']==''
            expected_packet=wire.encode_command(MENU[chosen],index%5,wire.command_index(proposals[index%5]),tick)
            expected_cmd,expected_mask=proposals,MENU[chosen]
            assert raw['selected_mask'][index]==expected_mask and raw['selected_q'][index]==wire.command_index(proposals[index%5])
        else:
            assert record['actual_timeout'] and record['fallback_reason']=='deadline'
            expected_packet=b''
            expected_cmd,expected_mask=actual,int(raw['mask'][tick])
            assert raw['selected_mask'][index]==raw['selected_q'][index]==-1
        if len(record['command_packet']):
            assert record['completed_calculation']
            assert record['command_packet'].tobytes()==wire.encode_command(MENU[chosen],index%5,wire.command_index(proposals[index%5]),tick)
        assert record['delivered_command_packet'].tobytes()==expected_packet
        assert raw['command_packet_lengths'][index]==len(expected_packet)
        assert raw['command_packets'][index,:len(expected_packet)].tobytes()==expected_packet
        assert not raw['command_packets'][index,len(expected_packet):].any()
        assert raw['round_bytes'][index]==len(record['report_packets'])*25+len(expected_packet)
        np.testing.assert_array_equal(record['returned_commands'],expected_cmd)
        np.testing.assert_array_equal(raw['commitments'][index],expected_cmd)
        assert record['returned_mask']==raw['applied_mask'][index]==expected_mask
        for name in ('candidate_requests','candidate_plans','state_reductions','geometry_snapshots','prefix_ticks'):
            assert raw[name][index]==counts[name]
        assert raw['scheduler_wall'][index]==record['wall_seconds']
        assert raw['scheduler_cpu'][index]==record['cpu_seconds']
        assert record['wall_seconds']>=raw['c_wall'][tick]
        if timely:
            np.testing.assert_array_equal(raw['commands'][tick+2:min(tick+6,steps)],np.repeat(expected_cmd[None],length,axis=0))
            assert np.all(raw['mask'][tick+2:min(tick+6,steps)]==expected_mask)
    return dict(verified_decision_rounds=len(records),model_work=total,
                independent_candidate_checks=len(records)*15,
                full_candidate_physics_scope='every mask and all forecast slots, including worker deadline-unfinished candidates')
