"""Synthetic C2 masks/codec/deadline fixtures; no environment or result data."""
from collections import Counter

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b07 import manager as m
from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records
from experiments.candidates.uav_user_waiting.b02.study import allocate_raw, record_round


def inputs():
    positions = np.array([[999.6, .4, 149.6], [100.3, 220.2, 50.2], [400.4, 700.1, 85.3],
                          [500.2, 600.2, 100.2], [800.4, 900.2, 120.1]])
    own = (positions-(0, 0, 50))/(1000, 1000, 100)
    actual = np.tile([1, -1, 1], (5, 1))
    proposals = np.array([[-1,1,-1], [1,0,1], [0,1,0], [-1,-1,1], [1,1,-1]])
    nav = np.arange(5, dtype=np.uint8)
    sites = np.column_stack((np.arange(50)*19+.4, np.arange(50)*17+.4))
    return own, actual, proposals, nav, m.p.encode_map(sites)


def make(*, horizon=256, clock=lambda:0.):
    own, actual, proposals, nav, packet = inputs()
    return m.Scheduler(packet, horizon=horizon, clock=clock, cpu_clock=lambda:0.), own, actual, proposals, nav


def mask_values(mask, rows):
    values = np.full((5, 50), -np.inf)
    values[m.p.mask_array(mask)] = -10.
    for member, ids in rows.items():
        assert mask & (1 << member)
        values[member, ids] = 3.
    return values


@pytest.fixture
def physics(monkeypatch):
    calls = dict(geometry=[], radio=[])
    def geometry(positions, sites):
        calls['geometry'].append((positions.copy(), sites.copy()))
        return np.broadcast_to(positions[:, 0, None], (5, 50)).copy()
    def radio(losses, *, transmitter_mask):
        mask = sum((1 << i) for i in np.flatnonzero(transmitter_mask))
        calls['radio'].append((mask, losses.copy()))
        return mask_values(mask, {i: np.arange(i*10, i*10+10) for i in np.flatnonzero(transmitter_mask)})
    monkeypatch.setattr(m, 'free_space_user_path_loss', geometry)
    monkeypatch.setattr(m, 'user_sinr_from_path_loss', radio)
    return calls


def numeric_tree(tree):
    for value in tree.values():
        if isinstance(value, dict):
            numeric_tree(value)
        else:
            assert value is not None and np.asarray(value).dtype.kind in 'biufUS'


@pytest.mark.parametrize('tick', [0, 4, 252])
def test_complete_menu_wire_prefix_forecast_counts_and_proposal_only_command(tick, physics):
    actor, own, actual, proposals, nav = make()
    result = actor.decide(own, actual, proposals, tick, 31, nav)
    record, counts = result['record'], result['counts']
    length = min(4, 256-tick-2)
    expected_menu = [1,2,3,4,5,6,8,9,10,12,16,17,18,20,24]
    assert list(m.MASK_MENU) == expected_menu
    assert len(expected_menu) == 15 and all(1 <= mask.bit_count() <= 2 for mask in expected_menu)
    np.testing.assert_array_equal(record['mask_menu'], expected_menu)
    np.testing.assert_array_equal(record['request_masks'], expected_menu)
    assert counts['candidate_requests'] == counts['candidate_plans'] == 15
    assert counts['radio_calls_attempted'] == counts['radio_calls_completed'] == counts['state_reductions'] == 15*length
    assert counts['sinr_link_entries'] == 250*15*length
    assert counts['geometry_attempts'] == counts['geometry_snapshots'] == counts['forecast_ticks'] == length
    assert counts['geometry_link_entries'] == 250*length
    assert counts['prefix_attempts'] == counts['prefix_ticks'] == 2
    assert len(physics['geometry']) == length and len(physics['radio']) == 15*length
    position = record['decoded_positions'].copy()
    for slot in range(2):
        position = np.clip(position+actual*30, m.p.LOW, m.p.HIGH)
        np.testing.assert_array_equal(record['prefix_positions'][slot], position)
    for slot in range(length):
        position = np.clip(position+proposals*30, m.p.LOW, m.p.HIGH)
        np.testing.assert_array_equal(record['forecast'][slot], position)
        np.testing.assert_array_equal(physics['geometry'][slot][0], position)
        np.testing.assert_array_equal(physics['geometry'][slot][1], actor.sites)
    for i, mask in enumerate(expected_menu):
        counts_by_uav = np.where(m.p.mask_array(mask), 10, 0)
        np.testing.assert_array_equal(record['eligible_counts'][i], np.tile(counts_by_uav,(length,1)))
        assert record['completed_slots'][i] == length and record['candidate_completed'][i]
        expected = [10*mask.bit_count()*length, 10*mask.bit_count(), -(mask^31).bit_count(), -mask]
        np.testing.assert_array_equal(record['keys'][i], expected)
    assert result['mask'] == 3 and result['timely'] and record['completed_calculation']
    np.testing.assert_array_equal(result['commands'], proposals)
    member = (tick//4)%5
    q = m.p.command_index(proposals[member])
    assert result['selected_q'] == record['requested_q'] == q
    assert m.p.decode_command(result['command_packet'], tick) == (3, member, q)
    assert len(result['reports']) == 5 and all(len(packet) == 25 for packet in result['reports'])
    assert len(result['command_packet']) == 16 and result['recurring_bytes'] == 141
    assert result['scheduler_wall'] == result['wall_seconds'] == record['wall_seconds']
    assert result['scheduler_cpu'] == result['cpu_seconds'] == record['cpu_seconds']
    assert not hasattr(actor, 'execution') and not hasattr(actor, 'history')
    numeric_tree(record)
    restored = unpack_records(pack_records([record]))[0]
    np.testing.assert_array_equal(restored['keys'], record['keys'])
    raw = allocate_raw(256, 'C2', actor.sites, inputs()[-1])
    record_round(raw, result, tick)
    assert int(raw['round_count']) == 1 and raw['applied_mask'][0] == 3


def test_rounded_reports_map_and_deterministic_stateless_output(physics):
    actor, own, actual, proposals, nav = make(horizon=8)
    first = actor.decide(own, actual, proposals, 0, 31, nav)
    changed = own.copy()
    changed[:,0] += .00001
    second = actor.decide(changed, actual, proposals, 0, 31, nav)
    assert first['reports'] == second['reports'] and first['command_packet'] == second['command_packet']
    for field in ('decoded_positions','forecast','prefix_positions','eligible_counts','keys','distinct_users'):
        np.testing.assert_array_equal(first['record'][field], second['record'][field])
    np.testing.assert_array_equal(actor.sites, np.rint(np.column_stack((np.arange(50)*19+.4,np.arange(50)*17+.4))))
    assert first['record']['decoded_positions'][0,0] == 1000
    assert first['record']['decoded_positions'][0,0] != own[0,0]*1000


@pytest.mark.parametrize('rule', ['capacity_primary','distinct_secondary','churn_tertiary','integer_final'])
def test_exact_tie_hierarchy_no_quality_or_age(rule, physics, monkeypatch):
    actor, own, actual, proposals, nav = make(horizon=8)
    entering, expected = 31, 3
    calls = Counter()
    def radio(losses, *, transmitter_mask):
        mask = sum(1 << i for i in np.flatnonzero(transmitter_mask))
        slot = calls[mask]
        calls[mask] += 1
        rows = {}
        if rule == 'capacity_primary':
            if mask == 1: rows = {0:np.arange(15)}
            if mask == 3: rows = {0:np.arange(9),1:np.arange(20,29)}
        elif rule == 'distinct_secondary':
            if mask == 1: rows = {0:np.arange(10)}
            if mask == 3: rows = {0:np.arange(slot*10,slot*10+10)}
        elif mask in (3,5):
            rows = {0:np.arange(10)}
        values = mask_values(mask, rows)
        if rule == 'integer_final' and mask == 5:
            values[values >= 3.] = 33.  # Higher quality cannot enter the declared four-part key.
        return values
    if rule == 'distinct_secondary': entering = 1
    if rule == 'churn_tertiary': entering, expected = 5, 5
    monkeypatch.setattr(m, 'user_sinr_from_path_loss', radio)
    result = actor.decide(own, actual, proposals, 0, entering, nav)
    assert result['mask'] == expected
    record = result['record']
    independent = [tuple(key) for key in record['keys']]
    assert record['selected_index'] == max(range(15), key=independent.__getitem__)
    if rule == 'capacity_primary':
        one, pair = m.MASK_MENU.index(1), m.MASK_MENU.index(3)
        assert record['keys'][one,0] == 40 and record['keys'][pair,0] == 72
    if rule == 'distinct_secondary':
        one, pair = m.MASK_MENU.index(1), m.MASK_MENU.index(3)
        assert record['keys'][one,0] == record['keys'][pair,0] == 40
        assert record['keys'][one,1] == 10 and record['keys'][pair,1] == 40


def test_zero_eligibility_still_uses_complete_cap_two_menu_and_current_proposals(physics, monkeypatch):
    actor, own, actual, proposals, nav = make(horizon=8)
    def empty(losses, *, transmitter_mask):
        mask = sum(1 << i for i in np.flatnonzero(transmitter_mask))
        return mask_values(mask, {})
    monkeypatch.setattr(m, 'user_sinr_from_path_loss', empty)
    result = actor.decide(own, actual, proposals, 0, 31, nav)
    assert result['timely'] and result['mask'] == 3
    np.testing.assert_array_equal(result['commands'], proposals)
    assert result['record']['counts']['candidate_plans'] == 15
    assert np.all(result['record']['keys'][:,:2] == 0)
    assert not result['record']['distinct_users'].any()


def test_deadline_after_last_radio_reduction_cannot_deliver_unfinished_menu_choice(physics, monkeypatch):
    now, calls = [0.], [0]
    actor, own, actual, proposals, nav = make(horizon=8, clock=lambda:now[0])
    function = m.user_sinr_from_path_loss
    def late(*args, **kwargs):
        result = function(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 60:
            now[0] = 2.
        return result
    monkeypatch.setattr(m, 'user_sinr_from_path_loss', late)
    result = actor.decide(own, actual, proposals, 0, 31, nav)
    record = result['record']
    assert not result['timely'] and not record['completed_calculation']
    assert record['counts']['radio_calls_completed'] == record['counts']['state_reductions'] == 60
    assert record['counts']['candidate_requests'] == 15 and record['counts']['candidate_plans'] == 14
    assert record['completed_slots'][-1] == 4 and not record['candidate_completed'][-1]
    assert np.all(record['keys'][-1] == m.KEY_SENTINEL)
    assert record['partial'] == dict(phase='candidate', mask_index=14, mask=24, slot=4)
    assert result['mask'] == 31 and result['command_packet'] == b''
    np.testing.assert_array_equal(result['commands'], actual)


@pytest.mark.parametrize('where', ['before', 'report', 'prefix', 'geometry', 'radio', 'command', 'finish'])
def test_deadline_at_every_phase_holds_both_outputs_and_paid_prefix(where, physics, monkeypatch):
    now = [0.]
    actor, own, actual, proposals, nav = make(horizon=8, clock=lambda:now[0])
    if where == 'before':
        now[0] = 2.
    elif where in ('report', 'command'):
        name = 'encode_reports' if where == 'report' else 'encode_command'
        function = getattr(m.p, name)
        def late(*args, **kwargs):
            result = function(*args, **kwargs)
            now[0] = 2.
            return result
        monkeypatch.setattr(m.p, name, late)
    elif where == 'prefix':
        function = m.np.clip
        def late(*args, **kwargs):
            result = function(*args, **kwargs)
            now[0] = 2.
            return result
        monkeypatch.setattr(m.np, 'clip', late)
    elif where in ('geometry','radio'):
        name = 'free_space_user_path_loss' if where == 'geometry' else 'user_sinr_from_path_loss'
        function = getattr(m,name)
        def late(*args, **kwargs):
            result = function(*args, **kwargs)
            now[0] = 2.
            return result
        monkeypatch.setattr(m,name,late)
    else:
        function = actor._finish_record
        def late(record):
            function(record)
            now[0] = 2.
        monkeypatch.setattr(actor, '_finish_record', late)
    result = actor.decide(own, actual, proposals, 0, 31, nav, started=0., cpu_started=0.)
    record, counts = result['record'], result['counts']
    assert not result['timely'] and record['actual_timeout']
    assert result['mask'] == record['returned_mask'] == 31
    np.testing.assert_array_equal(result['commands'], actual)
    assert result['selected_q'] is result['selected_mask'] is None
    assert result['command_packet'] == b'' and not len(record['delivered_command_packet'])
    assert result['recurring_bytes'] == (0 if where == 'before' else 125)
    if where == 'prefix':
        assert counts['prefix_attempts'] == counts['prefix_ticks'] == 1
    if where == 'geometry':
        assert counts['geometry_attempts'] == counts['geometry_snapshots'] == 1 and counts['candidate_requests'] == 0
    if where == 'radio':
        assert counts['radio_calls_attempted'] == counts['radio_calls_completed'] == counts['state_reductions'] == 1
        assert counts['candidate_requests'] == 1 and counts['candidate_plans'] == 0
        assert record['completed_slots'][0] == 1
    if where in ('command','finish'):
        assert record['completed_calculation'] and record['requested_mask'] == 3
        assert len(record['command_packet']) == 16
        assert counts['candidate_plans'] == 15
    numeric_tree(record)


@pytest.mark.parametrize('where', ['report','decode','geometry','invalid_geometry','radio','invalid_sinr','overlap','command'])
def test_numerical_or_input_failure_propagates_with_partial_counters(where, physics, monkeypatch):
    actor, own, actual, proposals, nav = make(horizon=8)
    def error(*args, **kwargs):
        raise ArithmeticError('synthetic call failed')
    if where in ('report','decode','command'):
        name = {'report':'encode_reports','decode':'decode_reports','command':'encode_command'}[where]
        monkeypatch.setattr(m.p, name, error)
    elif where == 'geometry':
        monkeypatch.setattr(m, 'free_space_user_path_loss', error)
    elif where == 'invalid_geometry':
        monkeypatch.setattr(m, 'free_space_user_path_loss', lambda *args: np.full((5,50),np.nan))
    elif where == 'radio':
        monkeypatch.setattr(m, 'user_sinr_from_path_loss', error)
    elif where == 'invalid_sinr':
        monkeypatch.setattr(m, 'user_sinr_from_path_loss', lambda *args,**kwargs: np.full((5,50),np.nan))
    else:
        function = m.user_sinr_from_path_loss
        def overlap(*args, **kwargs):
            mask = kwargs['transmitter_mask']
            result = function(*args, **kwargs)
            if mask.sum() == 2:
                result[np.flatnonzero(mask),0] = 3.
            return result
        monkeypatch.setattr(m, 'user_sinr_from_path_loss', overlap)
    with pytest.raises((ArithmeticError,ValueError)):
        actor.decide(own,actual,proposals,0,31,nav)
    record, counts = actor.last_record, actor.last_record['counts']
    assert record['fallback_reason'] == 'exception' and not record['timely']
    assert not len(record['delivered_command_packet'])
    if where == 'geometry':
        assert counts['geometry_attempts'] == 1 and counts['geometry_snapshots'] == 0
    if where == 'invalid_geometry':
        assert counts['geometry_attempts'] == counts['geometry_snapshots'] == 1
    if where == 'radio':
        assert counts['radio_calls_attempted'] == 1 and counts['radio_calls_completed'] == counts['state_reductions'] == 0
    if where == 'invalid_sinr':
        assert counts['radio_calls_attempted'] == counts['radio_calls_completed'] == 1 and counts['state_reductions'] == 0
    if where == 'overlap':
        assert counts['candidate_requests'] == 3 and counts['candidate_plans'] == 2
        assert counts['radio_calls_attempted'] == counts['radio_calls_completed'] == 9
        assert counts['state_reductions'] == 8
        assert record['partial']['radio_returned'] and record['partial']['multiplicity'][0] == 2
        assert record['completed_slots'][2] == 0
    numeric_tree(record)


@pytest.mark.parametrize('invalid', ['own','actual','proposals','nav','mask','tick','horizon','map'])
def test_invalid_inputs_are_never_hidden_by_expired_deadline(invalid, physics):
    actor, own, actual, proposals, nav = make(horizon=8, clock=lambda:2.)
    if invalid == 'own': own[0,0] = np.nan
    if invalid == 'actual': actual[0,0] = 2
    if invalid == 'proposals': proposals[0,0] = 2
    if invalid == 'nav': nav[0] = 10
    mask, tick = (0 if invalid == 'mask' else 31), (1 if invalid == 'tick' else 0)
    with pytest.raises(ValueError):
        if invalid == 'horizon': m.Scheduler(inputs()[-1], horizon=9)
        elif invalid == 'map': m.Scheduler(b'bad map')
        else: actor.decide(own,actual,proposals,tick,mask,nav,started=0.)
