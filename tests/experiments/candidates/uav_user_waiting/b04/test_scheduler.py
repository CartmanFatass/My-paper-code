"""Mock/analytical union checks; no native environment steps or training."""

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import scheduler as frozen
from experiments.candidates.uav_user_waiting.b04 import scheduler as s


@pytest.fixture
def radio(monkeypatch):
    """Deterministic assignment fixture exercises the real frozen stage/search."""
    def loss(position, sites):
        return position.copy()

    def sinr(position, transmitter_mask):
        return position, transmitter_mask

    def assignment(payload):
        position, mask = payload
        result = np.zeros((5, 50), bool)
        for member in np.flatnonzero(mask):
            first = (int(position[member, 0] + 2 * position[member, 1] + position[member, 2]) // 30) % 50
            count = 2 + (int(position[member, 2]) // 30) % 5
            result[member, (first + np.arange(count)) % 50] = True
        return result

    def metrics(payload, connections):
        position, mask = payload
        return dict(J=float(position[mask].sum()) / 10000, served=int(connections.any(axis=0).sum()), quality=1.)

    monkeypatch.setattr(frozen, 'free_space_user_path_loss', loss)
    monkeypatch.setattr(frozen, 'user_sinr_from_path_loss', sinr)
    monkeypatch.setattr(frozen, 'greedy_connection_assignment', assignment)
    monkeypatch.setattr(frozen, 'service_metrics', metrics)


def inputs():
    positions = np.array([[100, 100, 80], [300, 200, 100], [600, 400, 120],
                          [800, 700, 90], [400, 800, 110]], float)
    own = (positions - (0, 0, 50)) / (1000, 1000, 100)
    sites = np.column_stack((np.arange(50) * 19, np.arange(50) * 17))
    actual = np.zeros((5, 3))
    proposals = np.zeros((5, 3))
    return own, actual, proposals, np.arange(5), s.p.encode_map(sites)


def make(arm, *, horizon=12, clock=lambda: 0.):
    own, actual, proposed, nav, packet = inputs()
    return s.Scheduler(arm, packet, clock, lambda: 0., horizon=horizon), own, actual, proposed, nav


def replay(stage, label):
    keys = {tuple(pair): tuple(key) for pair, key in zip(stage['evaluated_pairs'], stage['keys'][label])}
    first = [(q, stage['current_mask']) for q in range(27)]
    q, _ = max(first, key=keys.__getitem__)
    second = [(q, mask) for mask in range(1, 32)]
    motion = max(second, key=keys.__getitem__)
    proposed = s.p.command_index(stage['proposals'][stage['member']])
    third = [(proposed, mask) for mask in range(1, 32)]
    _, mask = max(third, key=keys.__getitem__)
    fourth = [(q, mask) for q in range(27)]
    mask_pair = max(fourth, key=keys.__getitem__)
    record = stage['searches'][label]
    np.testing.assert_array_equal(stage['request_pairs'][record['request_start']:record['request_end']],
                                  first + second + third + fourth)
    chosen = max((motion, mask_pair), key=keys.__getitem__)
    np.testing.assert_array_equal(record['selected_pair'], chosen)
    assert record['completed']
    return chosen


def same_tree(left, right):
    assert left.keys() == right.keys()
    for name in left:
        if isinstance(left[name], dict):
            same_tree(left[name], right[name])
        else:
            np.testing.assert_array_equal(left[name], right[name])


def numeric_tree(tree):
    for value in tree.values():
        if isinstance(value, dict):
            numeric_tree(value)
        else:
            assert value is not None and np.asarray(value).dtype.kind in 'biufUS'


@pytest.mark.parametrize('arm', ['M', 'S'])
def test_baselines_delegate_exactly_without_wrapper_timing_or_fields(arm, radio):
    actor, own, actual, proposed, nav = make(arm)
    baseline = frozen.Scheduler(arm, inputs()[4], lambda: 0., lambda: 0., horizon=12)
    for tick in (0, 4, 8):
        if tick:
            for executed_tick in range(tick - 4, tick):
                actor.executed(executed_tick, actual, 7)
                baseline.executed(executed_tick, actual, 7)
        result = actor.decide(own, actual, proposed, tick, 7, nav, started=0., cpu_started=0.)
        expected = baseline.decide(own, actual, proposed, tick, 7, nav, started=0., cpu_started=0.)
        same_tree(result, expected)
        assert 'union' not in result['record']


def test_union_pool_generator_paths_counts_and_global_filter_arithmetic(radio):
    records = []
    for arm in ('U', 'K'):
        actor, own, actual, proposed, nav = make(arm)
        result = actor.decide(own, actual, proposed, 0, 7, nav)
        assert result['timely'] and result['candidate_requests'] == 348
        record, stage = result['record'], result['record']['current']
        union = record['union']
        assert union['completed'] and stage['completed']
        assert record['branches'] == {} and not record['continuation_used']
        assert tuple(stage['searches']) == ('O', 'W', 'S')
        o_pair, w_pair, s_pair = (replay(stage, label) for label in ('O', 'W', 'S'))
        keys = {tuple(pair): tuple(key) for pair, key in zip(stage['evaluated_pairs'], stage['keys']['W'])}
        m_pair = max((o_pair, w_pair), key=keys.__getitem__)
        np.testing.assert_array_equal(union['m_pair'], m_pair)
        np.testing.assert_array_equal(union['s_pair'], s_pair)
        pairs = list(dict.fromkeys(map(tuple, stage['request_pairs'])))
        np.testing.assert_array_equal(union['pool_pairs'], pairs)
        np.testing.assert_array_equal(union['pool_pairs'], stage['evaluated_pairs'])
        totals = stage['contacts'].sum(axis=(1, 2), dtype=np.int64)
        np.testing.assert_array_equal(union['service_totals'], totals)
        floor = totals[pairs.index(m_pair)]
        assert union['service_floor_total'] == floor
        feasible = totals >= floor
        np.testing.assert_array_equal(union['feasible'], feasible)
        assert feasible[pairs.index(m_pair)]
        s_keys = {tuple(pair): tuple(key) for pair, key in zip(stage['evaluated_pairs'], stage['keys']['S'])}
        u_pair = max(pairs, key=s_keys.__getitem__)
        k_pair = max((pair for pair, ok in zip(pairs, feasible) if ok), key=s_keys.__getitem__)
        np.testing.assert_array_equal(union['u_pair'], u_pair)
        np.testing.assert_array_equal(union['k_pair'], k_pair)
        selected = u_pair if arm == 'U' else k_pair
        assert (result['selected_q'], result['selected_mask']) == selected
        np.testing.assert_array_equal(record['requested_pair'], selected)
        assert result['counts']['candidate_plans'] == len(pairs)
        assert result['counts']['state_reductions'] == 4 * len(pairs)
        assert result['counts']['candidate_cache_hits'] == 348 - len(pairs)
        assert result['counts']['virtual_c_decisions'] == 0
        assert result['recurring_bytes'] == 141
        numeric_tree(record)
        records.append(record)
    same_tree(records[0]['current'], records[1]['current'])
    same_tree(records[0]['union'], records[1]['union'])


class AdversarialStage(frozen._Stage):
    """Analytical comparator fixture with competing excluded/feasible candidates."""
    def score(self, q, mask):
        index = super().score(q, mask)
        row = self.data[index]
        pair = q, mask
        tie = (0., 0., int(q == self.proposal_q), int(mask).bit_count(), -mask, -q)
        # O's winner has the best W value, while S/U prefer a below-floor candidate.
        o = 10 if pair == (0, 1) else (5 if pair == (0, 7) else 0)
        w = 10 if pair == (0, 1) else (9 if pair == (3, 7) else (8 if pair == (self.proposal_q, 7) else 0))
        square = -1 if pair == (2, 1) else (-2 if pair == (3, 7) else (-3 if pair == (self.proposal_q, 1) else -100))
        row['keys'].update(O=(o,) + (0,) * (len(self.groups) - 1) + tie,
                           W=(w,) + tie, S=(square,) + tie)
        contacts = np.zeros((self.length, 50), bool)
        count = 10 if pair == (0, 1) else (12 if pair == (3, 7) else 5)
        contacts[:, :count] = True
        row['contacts'] = contacts
        return index


@pytest.mark.parametrize('arm,selected', [('U', (2, 1)), ('K', (3, 7))])
def test_service_floor_only_after_generation_and_excludes_better_s_candidate(arm, selected, radio, monkeypatch):
    monkeypatch.setattr(s, '_Stage', AdversarialStage)
    actor, own, actual, proposed, nav = make(arm)
    result = actor.decide(own, actual, proposed, 0, 7, nav)
    union, stage = result['record']['union'], result['record']['current']
    assert result['candidate_requests'] == 348 and result['timely']
    assert (result['selected_q'], result['selected_mask']) == selected
    np.testing.assert_array_equal(union['m_pair'], (0, 1))
    np.testing.assert_array_equal(union['s_pair'], (2, 1))
    np.testing.assert_array_equal(union['u_pair'], (2, 1))
    np.testing.assert_array_equal(union['k_pair'], (3, 7))
    pairs = list(map(tuple, union['pool_pairs']))
    assert union['service_floor_total'] == 40
    assert not union['feasible'][pairs.index((2, 1))]
    assert union['feasible'][pairs.index((0, 1))]
    for label in ('O', 'W', 'S'):
        replay(stage, label)


def test_exact_full_key_ties_preserve_first_visited_pair(radio, monkeypatch):
    class TieStage(frozen._Stage):
        def score(self, q, mask):
            index = super().score(q, mask)
            self.data[index]['keys'] = dict(O=(0,) * (len(self.groups) + 6), W=(0,) * 7, S=(0,) * 7, R=(0,) * 8)
            self.data[index]['contacts'] = np.zeros((self.length, 50), bool)
            return index
    monkeypatch.setattr(s, '_Stage', TieStage)
    actor, own, actual, proposed, nav = make('K')
    result = actor.decide(own, actual, proposed, 0, 7, nav)
    assert result['timely']
    assert (result['selected_q'], result['selected_mask']) == (0, 7)
    assert result['record']['union']['feasible'].all()


@pytest.mark.parametrize('arm', ['U', 'K'])
def test_terminal_block_has_two_delivered_transitions_and_exact_integer_mean_floor(arm, radio):
    actor, own, actual, proposed, nav = make(arm, horizon=8)
    for tick in range(4):
        actor.executed(tick, actual, 7)
    result = actor.decide(own, actual, proposed, 4, 7, nav)
    assert result['timely']
    stage, union = result['record']['current'], result['record']['union']
    assert stage['length'] == 2 and stage['contacts'].shape[1] == 2
    assert stage['forecast'].shape[1] == 2
    totals = stage['contacts'].sum(axis=(1, 2), dtype=np.int64)
    np.testing.assert_array_equal(union['service_totals'], totals)
    np.testing.assert_array_equal(union['feasible'], totals / 2 >= union['service_floor_total'] / 2)
    assert result['counts']['state_reductions'] == 2 * len(totals)
    assert result['counts']['prefix_ticks'] == 2


@pytest.mark.parametrize('arm', ['U', 'K'])
def test_partial_union_after_complete_m_holds_old_action_without_rescue(arm, radio, monkeypatch):
    class InterruptedStage(frozen._Stage):
        def score(self, q, mask):
            index = super().score(q, mask)
            if self.label == 'S':
                raise frozen.DeadlineExceeded
            return index
    monkeypatch.setattr(s, '_Stage', InterruptedStage)
    actor, own, actual, proposed, nav = make(arm)
    result = actor.decide(own, actual, proposed, 0, 7, nav)
    union, stage = result['record']['union'], result['record']['current']
    assert not result['timely'] and not union['completed']
    assert result['selected_q'] is None and result['mask'] == 7 and result['command_packet'] == b''
    np.testing.assert_array_equal(result['commands'], actual)
    assert union['service_floor_total'] >= 0 and np.all(union['m_pair'] >= 0)
    assert stage['searches']['O']['completed'] and stage['searches']['W']['completed']
    assert not stage['searches']['S']['completed']
    assert result['candidate_requests'] == 233
    np.testing.assert_array_equal(union['pool_pairs'], stage['evaluated_pairs'])
    assert len(union['service_totals']) == len(union['pool_pairs']) > 0
    np.testing.assert_array_equal(result['record']['requested_pair'], [-1, -1])
    numeric_tree(result['record'])


@pytest.mark.parametrize('boundary', ['pre_c', 'reports', 'ranking', 'command', 'finish'])
def test_whole_round_late_work_holds_old_action_and_records_calculation(boundary, radio, monkeypatch):
    time = [0.]
    actor, own, actual, proposed, nav = make('K', clock=lambda: time[0])
    if boundary == 'pre_c':
        time[0] = 2.
    elif boundary == 'reports':
        original = s.p.encode_reports
        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            time[0] = 2.
            return value
        monkeypatch.setattr(s.p, 'encode_reports', late)
    elif boundary == 'command':
        original = s.p.encode_command
        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            time[0] = 2.
            return value
        monkeypatch.setattr(s.p, 'encode_command', late)
    else:
        class LateStage(frozen._Stage):
            def key(self, pair, label):
                value = super().key(pair, label)
                if boundary == 'ranking' and self.record['completed']:
                    time[0] = 2.
                return value
            def finish_record(self):
                super().finish_record()
                if boundary == 'finish':
                    time[0] = 2.
        monkeypatch.setattr(s, '_Stage', LateStage)
    result = actor.decide(own, actual, proposed, 0, 7, nav, started=0., cpu_started=0.)
    assert not result['timely'] and result['record']['actual_timeout']
    np.testing.assert_array_equal(result['commands'], actual)
    assert result['mask'] == 7 and result['command_packet'] == b''
    assert len(result['record']['delivered_command_packet']) == 0
    if boundary in ('command', 'finish'):
        assert result['record']['union']['completed']
        assert np.all(result['record']['requested_pair'] >= 0)
        assert len(result['record']['command_packet']) == 16
    else:
        assert not result['record']['union']['completed']
    if boundary == 'reports':
        assert not result['record']['decoded_anchor']


def test_missing_history_retains_empty_incomplete_union(radio, monkeypatch):
    actor, own, actual, proposed, nav = make('U')
    monkeypatch.setattr(actor.execution, 'settle', lambda tick, check: (0, False))
    result = actor.decide(own, actual, proposed, 0, 7, nav)
    assert not result['timely'] and result['record']['fallback_reason'] == 'history_unavailable'
    assert not result['record']['union']['completed']
    assert result['record']['union']['pool_pairs'].shape == (0, 2)
    assert result['candidate_requests'] == 0
    numeric_tree(result['record'])


def test_arm_validation():
    for arm in ('A', 'R', 'unknown'):
        with pytest.raises(ValueError):
            s.Scheduler(arm, inputs()[4])


def test_mid_candidate_deadline_preserves_partial_physics_without_union_winner(radio, monkeypatch):
    time = [0.]
    original = frozen.service_metrics
    def interrupt(*args, **kwargs):
        value = original(*args, **kwargs)
        time[0] = 2.
        return value
    monkeypatch.setattr(frozen, 'service_metrics', interrupt)
    actor, own, actual, proposed, nav = make('U', clock=lambda: time[0])
    result = actor.decide(own, actual, proposed, 0, 7, nav, started=0.)
    stage, union = result['record']['current'], result['record']['union']
    assert not result['timely'] and not union['completed']
    assert result['candidate_requests'] == 1 and result['counts']['candidate_plans'] == 0
    assert result['counts']['interrupted_candidate_requests'] == 1
    assert result['counts']['state_reductions'] == 1
    assert stage['partial']['contacts'].shape == (1, 50)
    assert stage['partial']['age_square_sum'].shape == (1,)
    assert stage['request_candidate_index'][0] == -1
    assert union['pool_pairs'].shape == (0, 2)
    assert stage['evaluated_pairs'].shape == (0, 2)
    np.testing.assert_array_equal(result['commands'], actual)
    numeric_tree(result['record'])


def test_deadline_is_inclusive_and_uses_supplied_current_c_start(radio):
    own, actual, proposed, nav, packet = inputs()
    actor = s.Scheduler('K', packet, lambda: s.p.DEADLINE_SECONDS, lambda: 5., horizon=8)
    result = actor.decide(own, actual, proposed, 0, 7, nav, started=0., cpu_started=2.)
    assert result['timely'] and not result['record']['actual_timeout']
    assert result['wall_seconds'] == s.p.DEADLINE_SECONDS
    assert result['cpu_seconds'] == 3.
