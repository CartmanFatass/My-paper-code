"""Mocked radio/S semantics; no native environment or scientific rollout."""

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b06 import scheduler as s, history as h
from experiments.candidates.uav_user_waiting.b02 import scheduler as frozen
from experiments.candidates.uav_registered_service.b01 import history as global_history
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded


def inputs():
    positions = np.array([[100, 100, 80], [300, 200, 100], [600, 400, 120],
                          [800, 700, 90], [400, 800, 110]], float)
    own = (positions - (0, 0, 50)) / (1000, 1000, 100)
    sites = np.column_stack((np.arange(50)*19, np.arange(50)*17))
    return own, np.zeros((5, 3)), np.zeros((5, 3)), np.arange(5), s.p.encode_map(sites)


def make(*, horizon=12, clock=lambda: 0.):
    own, actual, proposals, nav, packet = inputs()
    return s.Scheduler('S', packet, clock, lambda: 0., horizon=horizon), own, actual, proposals, nav


@pytest.fixture
def modeled(monkeypatch):
    def loss(positions, sites):
        return positions.copy()
    def sinr(positions, transmitter_mask):
        values = np.full((5, 50), -10.)
        for member in np.flatnonzero(transmitter_mask):
            # Saturated own disjoint ID ranges; member0 has15 eligible identities.
            start, size = (0, 15) if member == 0 else (15 + (member-1)*8, 8)
            values[member, start:start+size] = 3 + np.arange(size) + positions[member, 0]/1000
        values[~transmitter_mask] = -np.inf
        return values
    monkeypatch.setattr(h, 'free_space_user_path_loss', loss)
    monkeypatch.setattr(s, 'free_space_user_path_loss', loss)
    monkeypatch.setattr(h, 'user_sinr_from_path_loss', sinr)
    return loss, sinr


def unpack(grants):
    bits = np.zeros((5, 50), bool)
    for member, ids in enumerate(grants):
        chosen = ids[ids >= 0]
        assert len(chosen) == len(set(chosen)) <= 10 and np.all(ids[len(chosen):] == -1)
        bits[member, chosen] = True
    assert np.all(bits.sum(axis=0) <= 1)
    return bits


def arithmetic(history, grants_rows, first_tick):
    local = history['last_grant'].copy()
    last, windows, burden = (history[name].copy() for name in ('last', 'windows', 'burden'))
    ages, squares, contacts = [], [], []
    for slot, grants in enumerate(grants_rows):
        tick = first_tick + slot
        assigned = unpack(grants)
        local[assigned] = tick
        contact = assigned.any(axis=0)
        last[contact] = tick
        windows[tick // 64, contact] = True
        age = tick - last
        burden += age
        ages.append(int(age.sum()))
        squares.append(int(np.square(age).sum()))
        contacts.append(contact)
    return dict(last_grant=local, last=last, windows=windows, burden=burden), np.array(contacts), ages, squares


def replay_search(stage):
    keys = {tuple(pair): tuple(key) for pair, key in zip(stage['evaluated_pairs'], stage['keys']['S'])}
    first = [(q, stage['current_mask']) for q in range(27)]
    q, _ = max(first, key=keys.__getitem__)
    second = [(q, mask) for mask in range(1, 32)]
    motion = max(second, key=keys.__getitem__)
    proposal = s.p.command_index(stage['proposals'][stage['member']])
    third = [(proposal, mask) for mask in range(1, 32)]
    _, mask = max(third, key=keys.__getitem__)
    fourth = [(q, mask) for q in range(27)]
    mask_pair = max(fourth, key=keys.__getitem__)
    chosen = max((motion, mask_pair), key=keys.__getitem__)
    record = stage['searches']['S']
    np.testing.assert_array_equal(stage['request_pairs'], first+second+third+fourth)
    np.testing.assert_array_equal(record['motion_pair'], motion)
    np.testing.assert_array_equal(record['mask_pair'], mask_pair)
    np.testing.assert_array_equal(record['selected_pair'], chosen)
    assert record['completed'] and record['request_end'] == 116
    return chosen


def numeric_tree(tree):
    for value in tree.values():
        if isinstance(value, dict):
            numeric_tree(value)
        else:
            assert value is not None and np.asarray(value).dtype.kind in 'biufUS'


@pytest.mark.parametrize('tick', [0, 4, 8])
def test_s_exact_request_paths_wire_terminal_and_all_local_global_arithmetic(tick, modeled):
    actor, own, actual, proposals, nav = make()
    # Establish a causal start at0 without any environment or truth values.
    actor.execution.anchor(0, np.rint(own*(1000, 1000, 100)+(0, 0, 50)))
    for t in range(tick):
        actor.executed(t, actual, 31)
    result = actor.decide(own, actual, proposals, tick, 31, nav)
    record, stage = result['record'], result['record']['current']
    assert result['timely'] and result['candidate_requests'] == 116
    assert record['branches'] == {} and not record['continuation_used']
    assert all(len(packet) == 25 for packet in result['reports']) and len(result['command_packet']) == 16
    assert result['recurring_bytes'] == 141
    length = min(4, 12-tick-2)
    assert stage['length'] == length and stage['candidate_grants'].shape[1:] == (length, 5, 10)
    prefix, contact, _, _ = arithmetic(stage['input_history'], stage['prefix_grants'], tick)
    np.testing.assert_array_equal(stage['prefix_contacts'], contact)
    for key, value in prefix.items():
        np.testing.assert_array_equal(stage['prefix_history'][key], value)
    proposal_q = s.p.command_index(stage['proposals'][stage['member']])
    for index, (q, mask) in enumerate(stage['evaluated_pairs']):
        endpoint, contact, sums, squares = arithmetic(stage['prefix_history'], stage['candidate_grants'][index], tick+2)
        np.testing.assert_array_equal(stage['contacts'][index], contact)
        np.testing.assert_array_equal(stage['endpoint_last'][index], endpoint['last'])
        np.testing.assert_array_equal(stage['endpoint_burden'][index], endpoint['burden'])
        np.testing.assert_array_equal(stage['age_sum'][index], sums)
        np.testing.assert_array_equal(stage['age_square_sum'][index], squares)
        native = stage['native'][index]
        expected = (-sum(squares), native[0], native[1], int(q == proposal_q), int(mask).bit_count(), -int(mask), -int(q))
        np.testing.assert_array_equal(stage['keys']['S'][index], expected)
    selected = replay_search(stage)
    assert (result['selected_q'], result['selected_mask']) == selected
    np.testing.assert_array_equal(record['requested_pair'], selected)
    assert actor.execution.next_unsettled == tick
    np.testing.assert_array_equal(actor.execution.history.last_grant, stage['input_history']['last_grant'])
    counts = result['counts']
    assert counts['history_reductions'] == tick
    expected_ticks = tick+2+counts['state_reductions']
    assert counts['model_fleet_ticks'] == counts['model_transitions_completed'] == expected_ticks
    assert counts['lrs_row_selections'] == counts['lrs_rows_completed'] == 5*expected_ticks
    assert counts['sinr_link_entries'] == 250*expected_ticks
    assert counts['history_lrs_row_selections'] == 5*tick
    assert counts['candidate_cache_hits'] == 116-counts['candidate_plans']
    numeric_tree(record)


def test_private_candidate_state_and_branch_evaluation_order_isolated(modeled):
    actor, own, actual, proposals, nav = make()
    decoded = s.p.decode_reports(s.p.encode_reports(own, actual, proposals, 0, nav), 0)
    initial = h.ServiceHistory()
    def stage():
        counts = {key: 0 for key in ('candidate_requests','candidate_cache_hits','candidate_uncached_requests',
            'candidate_plans','state_reductions','geometry_snapshots','prefix_ticks','current_prefix_ticks')+h.WORK_KEYS}
        result = s.Stage(actor, {}, *decoded, 0, 31, initial, lambda:None, counts)
        result.prepare()
        return result
    first, reverse = stage(), stage()
    prefix_before = first.prefix.copy()
    a, b = (13, 31), (0, 1)
    first.score(*a)
    first.score(*b)
    reverse.score(*b)
    reverse.score(*a)
    for pair in (a, b):
        left = first.data[first.cache[pair]]
        right = reverse.data[reverse.cache[pair]]
        np.testing.assert_array_equal(left['grants'], right['grants'])
        assert left['keys'] == right['keys']
    for name in ('last_grant','last','windows','burden'):
        np.testing.assert_array_equal(getattr(first.prefix,name),getattr(prefix_before,name))
        np.testing.assert_array_equal(getattr(initial,name),getattr(h.ServiceHistory(),name))
    assert actor.execution.predicted == actor.execution.predicted_grants == {}
    count = first.counts['lrs_row_selections']
    first.score(*a)
    assert first.counts['lrs_row_selections'] == count  # cache hit never advances clocks


def test_no_capacity_choice_preserves_frozen_s_contacts_keys_commands_paths(modeled, monkeypatch):
    loss, original_sinr = modeled
    def nonsaturated(positions, transmitter_mask):
        values = original_sinr(positions, transmitter_mask)
        values[0, 10:15] = -10. if transmitter_mask[0] else -np.inf
        return values
    monkeypatch.setattr(h, 'user_sinr_from_path_loss', nonsaturated)
    monkeypatch.setattr(frozen, 'free_space_user_path_loss', loss)
    monkeypatch.setattr(frozen, 'user_sinr_from_path_loss', nonsaturated)
    monkeypatch.setattr(global_history, 'free_space_user_path_loss', loss)
    monkeypatch.setattr(global_history, 'user_sinr_from_path_loss', nonsaturated)
    actor, own, actual, proposals, nav = make()
    baseline = frozen.Scheduler('S', inputs()[4], lambda:0., lambda:0., horizon=12)
    for tick in (0,4,8):
        if tick:
            for t in range(tick-4,tick):
                actor.executed(t, actual, 31)
                baseline.executed(t,actual,31)
        result = actor.decide(own,actual,proposals,tick,31,nav)
        original = baseline.decide(own,actual,proposals,tick,31,nav)
        assert (result['selected_q'],result['selected_mask']) == (original['selected_q'],original['selected_mask'])
        np.testing.assert_array_equal(result['commands'],original['commands'])
        assert result['command_packet'] == original['command_packet']
        for key in ('request_pairs','evaluated_pairs','contacts','native'):
            np.testing.assert_array_equal(result['record']['current'][key],original['record']['current'][key])
        np.testing.assert_array_equal(result['record']['current']['keys']['S'],original['record']['current']['keys']['S'])


@pytest.mark.parametrize('failure', ['deadline','exception'])
def test_partial_candidate_keeps_private_joint_state_and_error_evidence(failure, modeled, monkeypatch):
    time = [0.]
    actor, own, actual, proposals, nav = make(clock=lambda:time[0])
    grant = h.LeastRecentlyServed.grant
    calls = [0]
    def interrupt(self, ids, values, tick):
        calls[0] += 1
        # Two prefix ticks (10rows), then one complete candidate tick(5rows).
        if calls[0] == 18:
            if failure == 'exception':
                raise RuntimeError('synthetic candidate row failure')
            time[0] = 2.
            raise DeadlineExceeded
        return grant(self, ids, values, tick)
    monkeypatch.setattr(h.LeastRecentlyServed,'grant',interrupt)
    if failure == 'exception':
        with pytest.raises(RuntimeError):
            actor.decide(own,actual,proposals,0,31,nav)
        record = actor.last_record
        assert record['decision_failure_type'] == 'RuntimeError'
    else:
        result = actor.decide(own,actual,proposals,0,31,nav)
        record = result['record']
        assert not result['timely'] and result['mask'] == 31 and result['command_packet'] == b''
        np.testing.assert_array_equal(result['commands'],actual)
    partial = record['current']['partial']
    assert partial['grants'].shape == (1,5,10) and partial['contacts'].shape == (1,50)
    assert partial['row_partial']['completed_rows'] == 2
    assert record['counts']['lrs_row_selections'] == 18 and record['counts']['lrs_rows_completed'] == 17
    assert record['counts']['state_reductions'] == 1 and record['counts']['interrupted_candidate_requests'] == 1
    np.testing.assert_array_equal(actor.execution.history.last_grant,np.full((5,50),-1))
    assert actor.execution.next_unsettled == 0
    numeric_tree(record)


@pytest.mark.parametrize('where', ['pre_c','encode','command','finish'])
def test_whole_deadline_retains_old_action_including_record_finalization(where, modeled, monkeypatch):
    time = [0.]
    actor, own, actual, proposals, nav = make(clock=lambda:time[0])
    if where == 'pre_c':
        time[0] = 2.
    elif where in ('encode','command'):
        name = 'encode_reports' if where == 'encode' else 'encode_command'
        function = getattr(s.p,name)
        def late(*args,**kwargs):
            value = function(*args,**kwargs)
            time[0] = 2.
            return value
        monkeypatch.setattr(s.p,name,late)
    else:
        finish = s.Stage.finish_record
        def late(self):
            finish(self)
            time[0] = 2.
        monkeypatch.setattr(s.Stage,'finish_record',late)
    result = actor.decide(own,actual,proposals,0,31,nav,started=0.,cpu_started=0.)
    assert not result['timely'] and result['record']['actual_timeout']
    np.testing.assert_array_equal(result['commands'],actual)
    assert result['mask'] == 31 and result['command_packet'] == b''
    if where in ('command','finish'):
        assert result['record']['current']['completed'] and np.all(result['record']['requested_pair'] >= 0)
    if where == 'encode':
        assert not result['record']['decoded_anchor'] and actor.execution.start_tick is None


@pytest.mark.parametrize('failure', ['deadline', 'exception'])
def test_interrupted_prefix_retains_only_completed_private_transition(failure, modeled, monkeypatch):
    actor, own, actual, proposals, nav = make()
    grant = h.LeastRecentlyServed.grant
    calls = [0]

    def interrupt(self, ids, values, tick):
        calls[0] += 1
        if calls[0] == 8:
            if failure == 'deadline':
                raise DeadlineExceeded
            raise RuntimeError('synthetic prefix row failure')
        return grant(self, ids, values, tick)

    monkeypatch.setattr(h.LeastRecentlyServed, 'grant', interrupt)
    if failure == 'exception':
        with pytest.raises(RuntimeError):
            actor.decide(own, actual, proposals, 0, 31, nav)
        record = actor.last_record
    else:
        result = actor.decide(own, actual, proposals, 0, 31, nav)
        record = result['record']
        assert not result['timely'] and result['mask'] == 31
        np.testing.assert_array_equal(result['commands'], actual)
    stage = record['current']
    assert stage['prefix_count'] == 1 and not stage['prefix_valid']
    assert stage['prefix_partial']['completed_rows'] == 2
    expected, contacts, _, _ = arithmetic(stage['input_history'], stage['prefix_grants'][:1], 0)
    for key, value in expected.items():
        np.testing.assert_array_equal(stage['prefix_history'][key], value)
        np.testing.assert_array_equal(stage['prefix_partial']['input_history'][key], value)
    np.testing.assert_array_equal(stage['prefix_contacts'][:1], contacts)
    np.testing.assert_array_equal(actor.execution.history.last_grant, np.full((5, 50), -1))
    assert record['counts']['lrs_row_selections'] == 8
    assert record['counts']['lrs_rows_completed'] == 7
    assert record['counts']['model_transitions_completed'] == 1
    assert record['counts']['candidate_requests'] == 0
    numeric_tree(record)


def test_terminal_settlement_covers_four_final_executed_ticks_and_grant_state(modeled):
    actor, own, actual, proposals, nav = make(horizon=8)
    actor.decide(own,actual,proposals,0,31,nav)
    for t in range(4): actor.executed(t,actual,31)
    result = actor.decide(own,actual,proposals,4,31,nav)
    assert result['record']['current']['length'] == 2
    for t in range(4,8): actor.executed(t,actual,31)
    assert actor.execution.settle(8) == (4,True)
    assert set(actor.execution.predicted_grants) == set(range(8))
    assert actor.execution.next_unsettled == 8
    assert actor.execution.work_counts['model_transitions_completed'] == 8
    assert not actor.execution.history.burden_unknown


def test_missing_history_and_arm_validation(modeled, monkeypatch):
    actor, own, actual, proposals, nav = make()
    monkeypatch.setattr(actor.execution,'settle',lambda tick,check:(0,False))
    result = actor.decide(own,actual,proposals,0,31,nav)
    assert not result['timely'] and result['record']['fallback_reason'] == 'history_unavailable'
    assert result['record']['current'] == {} and result['candidate_requests'] == 0
    with pytest.raises(ValueError):
        s.Scheduler('S_F',inputs()[4])
