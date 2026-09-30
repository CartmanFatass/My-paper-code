"""Synthetic source/algebra fixtures only; no native environments or steps."""

import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.read import observed_rows
from experiments.candidates.uav_service_age.b01.scheduler import Scheduler as FrozenM
from experiments.candidates.uav_user_waiting.b01.scheduler import Scheduler as FrozenR
from experiments.candidates.uav_user_waiting.b02 import predictor, protocol as p, scheduler as s


def inputs():
    positions = np.array([[100, 100, 80], [300, 200, 100], [600, 400, 120],
                          [800, 700, 90], [400, 800, 110]], float)
    sites = np.array([[50 + 100 * x, 100 + 180 * y] for x in range(10) for y in range(5)])
    own = (positions - (0, 0, 50)) / (1000, 1000, 100)
    actual = np.zeros((5, 3))
    proposals = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, -1]])
    return own, actual, proposals, np.arange(5), p.encode_map(sites)


def make(arm='A', *, horizon=12, clock=lambda: 0.):
    own, actual, proposed, nav, packet = inputs()
    return s.Scheduler(arm, packet, clock, lambda: 0., horizon=horizon), own, actual, proposed, nav


def update(last, windows, burden, rows, first_tick):
    last, windows, burden = last.copy(), windows.copy(), burden.copy()
    sums, squares = [], []
    for offset, row in enumerate(rows):
        tick = first_tick + offset
        total = square = 0
        for user in range(p.U):
            if row[user]:
                last[user] = tick
                windows[tick // 64, user] = True
            age = tick - int(last[user])
            burden[user] += age
            total += age
            square += age * age
        sums.append(total)
        squares.append(square)
    return last, windows, burden, np.array(sums, np.int64), np.array(squares, np.int64)


def replay_search(stage, label):
    keys = {tuple(pair): tuple(key) for pair, key in zip(stage['evaluated_pairs'], stage['keys'][label])}
    member = stage['member']
    proposal = p.command_index(stage['proposals'][member])
    first = [(q, stage['current_mask']) for q in range(27)]
    q, _ = max(first, key=lambda pair: keys[pair])
    second = [(q, mask) for mask in range(1, 32)]
    motion = max(second, key=lambda pair: keys[pair])
    third = [(proposal, mask) for mask in range(1, 32)]
    _, mask = max(third, key=lambda pair: keys[pair])
    fourth = [(q, mask) for q in range(27)]
    mask_pair = max(fourth, key=lambda pair: keys[pair])
    search = stage['searches'][label]
    np.testing.assert_array_equal(search['motion_pair'], motion)
    np.testing.assert_array_equal(search['mask_pair'], mask_pair)
    np.testing.assert_array_equal(search['selected_pair'], max((motion, mask_pair), key=lambda pair: keys[pair]))
    path = stage['request_pairs'][search['request_start']:search['request_end']]
    np.testing.assert_array_equal(path, first + second + third + fourth)
    assert len(path) == 116 and search['completed']


def verify_stage(stage):
    initial = stage['input_history']
    last, windows, burden, _, _ = update(initial['last'], initial['windows'], initial['burden'],
                                          stage['prefix_contacts'], stage['tick'])
    prefix = stage['prefix_history']
    for key, expected in (('last', last), ('windows', windows), ('burden', burden)):
        np.testing.assert_array_equal(prefix[key], expected)
    groups = [last == value for value in np.unique(last)]
    proposal_q = p.command_index(stage['proposals'][stage['member']])
    for index, (q, mask) in enumerate(stage['evaluated_pairs']):
        endpoint, _, total, sums, squares = update(last, windows, burden, stage['contacts'][index], stage['tick'] + 2)
        np.testing.assert_array_equal(stage['endpoint_last'][index], endpoint)
        np.testing.assert_array_equal(stage['endpoint_burden'][index], total)
        np.testing.assert_array_equal(stage['age_sum'][index], sums)
        np.testing.assert_array_equal(stage['age_square_sum'][index], squares)
        assert stage['age_cost'][index] == sum(map(int, sums))
        assert stage['q2_cost'][index] == sum(map(int, squares))
        native = stage['native'][index]
        ties = (native[0], native[1], int(q == proposal_q), int(mask).bit_count(), -int(mask), -int(q))
        distinct = stage['contacts'][index].any(axis=0)
        keys = dict(O=tuple(int((distinct & group).sum()) for group in groups) + ties,
                    W=(-int(sums.sum()),) + ties, S=(-int(squares.sum()),) + ties,
                    R=(-int(total.max()), -sum(map(int, total))) + ties)
        for label, key in keys.items():
            np.testing.assert_array_equal(stage['keys'][label][index], key)
    for label in stage['searches']:
        replay_search(stage, label)
    for pair, index in zip(stage['request_pairs'], stage['request_candidate_index']):
        assert index >= 0
        np.testing.assert_array_equal(pair, stage['evaluated_pairs'][index])


def numeric_tree(tree):
    for value in tree.values():
        if isinstance(value, dict):
            numeric_tree(value)
        else:
            assert value is not None
            assert np.asarray(value).dtype.kind in 'biufUS'


def test_codec_state_boundaries_versions_and_shared_deadline():
    own, actual, proposed, nav, _ = inputs()
    packets = p.encode_reports(own, actual, proposed, 0, nav)
    assert all(len(packet) == 25 for packet in packets)
    assert p.REPORT.size == 25 and p.COMMAND.size == 16
    assert p.DEADLINE_SECONDS == pytest.approx(1.436)
    positions, wire_actual, wire_proposed, wire_nav = p.decode_reports(packets, 0)
    np.testing.assert_array_equal(positions, np.rint(own * (1000, 1000, 100) + (0, 0, 50)))
    np.testing.assert_array_equal(wire_actual, actual)
    np.testing.assert_array_equal(wire_proposed, proposed)
    np.testing.assert_array_equal(wire_nav, nav)
    packet = p.encode_command(7, 0, 13, 0)
    assert p.decode_command(packet, 0) == (7, 0, 13)
    for invalid in ([-1, 0, 0, 0, 0], [10, 0, 0, 0, 0], [0.] * 5, [True] * 5, [0] * 4):
        with pytest.raises(ValueError):
            p.encode_reports(own, actual, proposed, 0, invalid)
    for version in (3, 5):
        wrong = bytes([version]) + packets[0][1:]
        with pytest.raises(ValueError):
            p.decode_reports((wrong,) + packets[1:], 0)
    wrong_nav = packets[0][:-1] + bytes([10])
    with pytest.raises(ValueError):
        p.decode_reports((wrong_nav,) + packets[1:], 0)
    with pytest.raises(ValueError):
        p.decode_command(bytes([3]) + packet[1:], 0)


@pytest.mark.parametrize('mask', [1, 3, 7, 31])
def test_synthetic_observation_is_source_equivalent_and_uses_eligible_top20(mask):
    positions = np.tile([500, 500, 100], (5, 1)).astype(float)
    sites = np.array([[450 + index, 500] for index in range(50)])
    rows, work = predictor.synthetic_observations(positions, sites, mask, 4, horizon=12)
    expected = observed_rows(positions, sites, mask, 4)
    expected[:, -1] = 4 / 12
    np.testing.assert_array_equal(rows, expected)
    assert rows.dtype == np.float32 and rows.shape == (5, 104)
    assert work['observation_user_links'] == 250
    if mask == 1:
        visible = rows[0, 3:63].reshape(20, 3)
        assert (visible[:, 2] > 0).sum() == 20
        assert not rows[1:, 3:103].any()
        # Assignment capacity is10 while the observation retains20 eligible rows.
        loss = s.free_space_user_path_loss(positions, sites)
        sinr = s.user_sinr_from_path_loss(loss, transmitter_mask=p.mask_array(mask))
        assert s.greedy_connection_assignment(sinr).sum() == 10


def test_cloned_c_uses_only_decoded_post_call_navigation_and_is_private():
    own, _, _, _, packet = inputs()
    positions = np.rint(own * (1000, 1000, 100) + (0, 0, 50))
    rows, _ = predictor.synthetic_observations(positions, p.decode_map(packet), 7, 0, horizon=12)
    real = LocalController(history=False)
    for tick in range(4):
        real.act(rows[0], tick)
    nav = predictor.controller_nav_index(real)
    clone = predictor.clone_controller(nav)
    another = predictor.clone_controller(nav)
    assert clone._points.shape == (0, 2) and clone.counters['decisions'] == 0
    later, _ = predictor.synthetic_observations(positions, p.decode_map(packet), 7, 4, horizon=12)
    command, diagnostics = clone.act(later[0], 4)
    expected, expected_diag = real.act(later[0], 4)
    np.testing.assert_array_equal(command, expected)
    np.testing.assert_array_equal(diagnostics['scores'], expected_diag['scores'])
    assert clone._nav_index == real._nav_index
    assert another._nav_index == nav and another.counters['decisions'] == 0
    clone._points[:] = -123
    assert not np.array_equal(clone._points, real._points)
    with pytest.raises(ValueError):
        predictor.controller_nav_index(LocalController(history=False))


def test_reset_zero_squared_age_algebra_and_integer_gap_costs():
    ages = np.arange(50, dtype=np.int64)
    served = np.arange(50) % 3 == 0
    after = np.where(served, 0, ages + 1)
    assert np.square(after).sum() - np.square(ages).sum() == (2 * ages + 1).sum() - np.square(ages[served] + 1).sum()
    for gap in (1, 5, 20, 255):
        assert sum(tick * tick for tick in range(1, gap + 1)) == gap * (gap + 1) * (2 * gap + 1) // 6


@pytest.mark.parametrize('arm,frozen_type', [('R', FrozenR), ('M', FrozenM)])
def test_r_and_m_preserve_frozen_source_rankings_and_request_paths(arm, frozen_type):
    actor, own, actual, proposed, nav = make(arm)
    frozen = frozen_type(arm, inputs()[4], lambda: 0., lambda: 0., horizon=12)
    for tick in (0, 4, 8):
        if tick:
            for executed_tick in range(tick - 4, tick):
                actor.executed(executed_tick, actual, 7)
                frozen.executed(executed_tick, actual, 7)
        result = actor.decide(own, actual, proposed, tick, 7, nav)
        baseline = frozen.decide(own, actual, proposed, tick, 7)
        assert result['timely'] and baseline['timely']
        assert (result['selected_q'], result['selected_mask']) == (baseline['selected_q'], baseline['selected_mask'])
        np.testing.assert_array_equal(result['commands'], baseline['commands'])
        assert result['candidate_requests'] == (232 if arm == 'M' else 116)
        current = result['record']['current']
        verify_stage(current)
        key_name = 'R' if arm == 'R' else 'W'
        for index, (q, mask) in enumerate(current['evaluated_pairs']):
            np.testing.assert_array_equal(current['native'][index], baseline['scores'][q, mask])
            np.testing.assert_array_equal(current['contacts'][index], baseline['candidate_contacts'][q, mask])
            expected = baseline['ordering_keys'][q, mask, :8] if arm == 'R' else baseline['w_ordering_keys'][q, mask]
            np.testing.assert_array_equal(current['keys'][key_name][index], expected)
        assert actor.execution.next_unsettled == tick
        np.testing.assert_array_equal(actor.execution.history.burden, current['input_history']['burden'])
        numeric_tree(result['record'])


@pytest.mark.parametrize('tick', [0, 248, 252])
def test_a_shared_trajectory_q8_truncation_and_only_first_action_delivery(tick):
    actor, own, actual, proposed, nav = make(horizon=256)
    for executed_tick in range(tick):
        actor.executed(executed_tick, actual, 31)
    # Synthetic late-start anchor avoids creating any native history fixture.
    if tick:
        actor.execution.anchor(tick, np.rint(own * (1000, 1000, 100) + (0, 0, 50)))
    baseline, _, _, _, _ = make('S', horizon=256)
    for executed_tick in range(tick):
        baseline.executed(executed_tick, actual, 31)
    if tick:
        baseline.execution.anchor(tick, actor.execution.position)
    result = actor.decide(own, actual, proposed, tick, 31, nav)
    short = baseline.decide(own, actual, proposed, tick, 31, nav)
    record, current = result['record'], result['record']['current']
    assert result['timely'] and short['timely']
    np.testing.assert_array_equal(record['s_pair'], [short['selected_q'], short['selected_mask']])
    np.testing.assert_array_equal(current['request_pairs'], short['record']['current']['request_pairs'])
    verify_stage(current)
    assert any(np.array_equal(pair, record['s_pair']) for pair in record['first_finalists'])
    if tick == 252:
        assert not record['continuation_used'] and record['branches'] == {}
        assert result['candidate_requests'] == 116 and current['length'] == 2
        assert (result['selected_q'], result['selected_mask']) == (short['selected_q'], short['selected_mask'])
    elif len(record['first_finalists']) == 2:
        assert record['continuation_used'] and result['candidate_requests'] == 348
        assert result['counts']['virtual_c_decisions'] == 10
        assert result['counts']['continuation_prefix_ticks'] == 4
        for branch in record['branches'].values():
            assert branch['completed'] and branch['prefix_matches']
            pair = tuple(branch['first_pair'])
            index = next(index for index, value in enumerate(current['evaluated_pairs']) if tuple(value) == pair)
            prefix = current['prefix_history']
            last, windows, burden, _, _ = update(prefix['last'], prefix['windows'], prefix['burden'], current['contacts'][index, :2], tick + 2)
            np.testing.assert_array_equal(branch['input_history']['last'], last)
            np.testing.assert_array_equal(branch['input_history']['windows'], windows)
            np.testing.assert_array_equal(branch['input_history']['burden'], burden)
            np.testing.assert_array_equal(branch['model_positions'], current['forecast'][pair[0], 1])
            np.testing.assert_array_equal(branch['decoded_positions'], branch['model_positions'])
            next_stage = branch['continuation']
            verify_stage(next_stage)
            np.testing.assert_array_equal(next_stage['prefix_positions'], current['forecast'][pair[0], 2:4])
            np.testing.assert_array_equal(next_stage['prefix_contacts'], current['contacts'][index, 2:4])
            assert next_stage['tick'] == tick + 4 and next_stage['length'] == (2 if tick == 248 else 4)
            assert branch['q8'] == branch['current_q2'] + branch['continuation_q2']
            next_pair = tuple(next_stage['searches']['S']['selected_pair'])
            next_index = next(i for i, value in enumerate(next_stage['evaluated_pairs']) if tuple(value) == next_pair)
            delivered = list(map(int, current['age_square_sum'][index])) + list(map(int, next_stage['age_square_sum'][next_index]))
            assert len(delivered) == (6 if tick == 248 else 8)
            assert sum(delivered) == branch['q8']
        assert record['c_diagnostics_valid']
        candidate_index = {tuple(pair): index for index, pair in enumerate(current['evaluated_pairs'])}
        independent_winner = max(range(2), key=lambda number: (
            -record['branches']['branch_' + str(number)]['q8'],
            *current['keys']['S'][candidate_index[tuple(record['first_finalists'][number])]],
        ))
        assert record['selected_branch'] == independent_winner
        np.testing.assert_array_equal(record['requested_pair'], record['first_finalists'][independent_winner])
        assert record['c0_q8'] == record['c0_current_q2'] + record['c0_continuation_q2']
        assert record['c1_q8'] == record['c1_current_q2'] + record['c1_continuation_q2']
        np.testing.assert_array_equal(record['c0_pair'], record['s_pair'])
        assert record['c1_q8'] <= record['c0_q8']
    else:
        assert result['candidate_requests'] == 116 and not record['continuation_used']
    assert result['recurring_bytes'] == 141
    assert actor.execution.predicted == {} and actor.execution.next_unsettled == tick
    commands = proposed.copy()
    commands[(tick // 4) % 5] = COMMANDS[result['selected_q']]
    np.testing.assert_array_equal(result['commands'], commands)
    assert result['mask'] == result['selected_mask']
    numeric_tree(record)


def test_a_single_finalist_skips_virtual_c(monkeypatch):
    original = s._Stage.search

    def single(stage, label):
        selected, _ = original(stage, label)
        return selected, (selected, selected)

    monkeypatch.setattr(s._Stage, 'search', single)
    actor, own, actual, proposed, nav = make()
    result = actor.decide(own, actual, proposed, 0, 31, nav)
    assert result['timely'] and result['candidate_requests'] == 116
    assert result['record']['first_finalists'].shape == (1, 2)
    assert result['record']['branches'] == {} and result['counts']['virtual_c_decisions'] == 0


@pytest.mark.parametrize('phase', ['current_c', 'encode', 'prefix', 'candidate', 'current_search',
                                  'observation', 'virtual_c', 'synthetic_encode',
                                  'continuation_prefix', 'continuation_search', 'command', 'serialization'])
def test_one_deadline_holds_old_entire_team_in_every_phase(monkeypatch, phase):
    now = [0.]
    actor, own, actual, proposed, nav = make(clock=lambda: now[0])
    if phase == 'current_c':
        now[0] = 2.
    elif phase in ('encode', 'synthetic_encode', 'command'):
        name = 'encode_command' if phase == 'command' else 'encode_reports'
        original = getattr(p, name)

        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            if phase != 'synthetic_encode' or args[3] == 4:
                now[0] = 2.
            return value

        monkeypatch.setattr(p, name, late)
    elif phase in ('prefix', 'candidate', 'continuation_prefix'):
        original = s._Stage.prepare if phase != 'candidate' else s._Stage.score

        def late(stage, *args):
            if phase == 'candidate':
                # Interrupt one candidate after its first completed radio reduction.
                native_metrics = s.service_metrics

                def metrics(*values):
                    result = native_metrics(*values)
                    now[0] = 2.
                    return result

                monkeypatch.setattr(s, 'service_metrics', metrics)
            value = original(stage, *args)
            if phase != 'continuation_prefix' or stage.continuation:
                now[0] = 2.
            return value

        monkeypatch.setattr(s._Stage, 'score' if phase == 'candidate' else 'prepare', late)
    elif phase in ('current_search', 'continuation_search'):
        original = s._Stage.search

        def late(stage, label):
            value = original(stage, label)
            if (phase == 'continuation_search') == stage.continuation:
                now[0] = 2.
            return value

        monkeypatch.setattr(s._Stage, 'search', late)
    elif phase == 'observation':
        original = s.synthetic_observations

        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            now[0] = 2.
            return value

        monkeypatch.setattr(s, 'synthetic_observations', late)
    elif phase == 'virtual_c':
        original = LocalController.act

        def late(controller, *args):
            value = original(controller, *args)
            now[0] = 2.
            return value

        monkeypatch.setattr(LocalController, 'act', late)
    else:
        original = s._Stage.finish_record

        def late(stage):
            value = original(stage)
            now[0] = 2.
            return value

        monkeypatch.setattr(s._Stage, 'finish_record', late)
    result = actor.decide(own, actual, proposed, 0, 31, nav, started=0., cpu_started=0.)
    assert not result['timely'] and result['record']['actual_timeout']
    assert result['selected_q'] is None and result['selected_mask'] is None
    np.testing.assert_array_equal(result['commands'], actual)
    assert result['mask'] == 31 and result['command_packet'] == b''
    assert not actor.execution.history.burden.any() and not actor.execution.history.windows.any()
    assert result['counts']['candidate_uncached_requests'] == result['candidate_plans'] + result['counts']['interrupted_candidate_requests']
    if phase in ('current_c', 'encode'):
        assert actor.execution.anchors == {} and not result['record']['decoded_anchor']
    if phase == 'candidate':
        stage = result['record']['current']
        assert stage['evaluated_pairs'].shape == (0, 2)
        assert stage['partial']['contacts'].shape == (1, 50)
        assert stage['request_candidate_index'].tolist() == [-1]
    if phase == 'virtual_c':
        assert result['counts']['virtual_c_decisions'] == 1
        assert result['record']['branches']['branch_0']['virtual_c_count'] == 1
    numeric_tree(result['record'])
