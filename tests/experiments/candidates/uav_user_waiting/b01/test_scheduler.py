"""Bounded correctness fixtures; no scientific episode or result panel."""

import inspect

import numpy as np
import pytest

from envs.pettingzoo import uav_radio as radio
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_registered_service.b01 import study as retained
from experiments.candidates.uav_user_waiting.b01 import history as h, scheduler as s


def inputs():
    own = np.tile([.5, .5, .5], (p.N, 1)).astype(np.float32)
    actual = np.zeros((p.N, 3))
    proposed = np.tile([1, 0, 0], (p.N, 1))
    packet = p.encode_map(np.tile([500, 500], (p.U, 1)))
    return own, actual, proposed, packet


def make(*, clock=lambda: 0., horizon=8):
    own, actual, proposed, packet = inputs()
    return s.Scheduler('R', packet, clock, lambda: 0., horizon=horizon), own, actual, proposed


def recurrence(last, burden, contacts, first_tick):
    """Scalar oracle independent of the direction history implementation."""
    last, burden = list(map(int, last)), list(map(int, burden))
    for offset, served in enumerate(contacts):
        tick = first_tick + offset
        for user in range(p.U):
            if served[user]:
                last[user] = tick
            burden[user] += tick - last[user]
    return np.array(last, dtype=np.int64), np.array(burden, dtype=np.int64)


def oracle_key(q, mask, native, burden, proposal_q):
    return (-max(map(int, burden)), -sum(map(int, burden)),
            float(native[0]), float(native[1]), int(q == proposal_q),
            int(mask).bit_count(), -int(mask), -int(q))


def replay_paths(keys, current_mask, proposal_q):
    """Four explicit reductions, independent of sequential_search."""
    requests = [(q, current_mask) for q in range(27)]
    first_q, _ = max(requests, key=lambda pair: keys[pair])
    motion_masks = [(first_q, mask) for mask in range(1, 32)]
    motion = max(motion_masks, key=lambda pair: keys[pair])
    proposal_masks = [(proposal_q, mask) for mask in range(1, 32)]
    _, first_mask = max(proposal_masks, key=lambda pair: keys[pair])
    mask_qs = [(q, first_mask) for q in range(27)]
    mask = max(mask_qs, key=lambda pair: keys[pair])
    return max((motion, mask), key=lambda pair: keys[pair]), requests + motion_masks + proposal_masks + mask_qs


def assert_fallback(result, actual, mask):
    assert not result['timely'] and result['actual_timeout']
    assert result['selected_q'] is None and result['selected_mask'] is None
    assert result['sequential_pair'] is None and result['sequential_score'] is None
    assert result['command_packet'] == b'' and result['mask'] == mask
    assert result['fallback_reason'] == 'deadline'
    np.testing.assert_array_equal(result['commands'], actual)
    assert result['request_count'] == result['candidate_requests']
    assert result['candidate_requests'] == result['candidate_cache_hits'] + result['candidate_uncached_requests']
    assert result['interrupted_candidate_requests'] == result['candidate_uncached_requests'] - result['candidate_plans']


def test_integer_recurrence_copy_and_permanent_censoring():
    contacts = np.zeros((6, p.U), bool)
    contacts[0, 0] = contacts[2, 1] = contacts[4, 0] = True
    history = h.ServiceHistory()
    for tick, served in enumerate(contacts):
        history.update(tick, served)
    last, burden = recurrence(np.full(p.U, -1), np.zeros(p.U), contacts, 0)
    np.testing.assert_array_equal(history.last, last)
    np.testing.assert_array_equal(history.burden, burden)
    assert history.burden[:3].tolist() == [7, 9, 21]
    assert history.burden.dtype == np.int64 and not history.burden_unknown
    clone = history.copy()
    clone.update(6, np.ones(p.U, bool))
    np.testing.assert_array_equal(history.burden, burden)
    assert not np.shares_memory(clone.burden, history.burden)
    assert not np.shares_memory(clone.last, history.last)
    assert not np.shares_memory(clone.windows, history.windows)
    late = h.ServiceHistory(start_tick=4)
    late.burden[:] = 2**31
    late.update(4, np.zeros(p.U, bool))
    late.update(5, np.ones(p.U, bool))
    assert (late.burden == 2**31 + 5).all()
    assert late.burden_unknown and late.copy().burden_unknown
    assert (late.last == 5).all()  # Age uncertainty cleared; burden remains censored.


def test_frozen_atomic_settlement_anchors_and_no_forecast_commit():
    execution = h.ExecutionHistory(np.zeros((p.U, 2)))
    commands = np.zeros((p.N, 3))
    initial, later = np.tile([100, 100, 100], (p.N, 1)), np.tile([700, 700, 100], (p.N, 1))
    execution.anchor(0, initial)
    execution.anchor(4, later)
    for tick in range(8):
        execution.append(tick, commands, 31)
    contacts = np.zeros((8, p.U), bool)
    contacts[np.arange(8), np.arange(8)] = True
    positions = []

    def evaluate(position, sites, mask):
        positions.append(position.copy())
        return contacts[len(positions) - 1], np.zeros(3)

    def check():
        if len(positions) == 2:
            raise s.DeadlineExceeded

    with pytest.raises(s.DeadlineExceeded):
        execution.settle(4, check, evaluate)
    assert execution.next_unsettled == 2 and sorted(execution.predicted) == [0, 1]
    _, burden = recurrence(np.full(p.U, -1), np.zeros(p.U), contacts[:2], 0)
    np.testing.assert_array_equal(execution.history.burden, burden)
    assert execution.settle(8, evaluate=evaluate) == (6, True)
    last, burden = recurrence(np.full(p.U, -1), np.zeros(p.U), contacts, 0)
    np.testing.assert_array_equal(execution.history.last, last)
    np.testing.assert_array_equal(execution.history.burden, burden)
    np.testing.assert_array_equal(positions[:4], np.tile(initial, (4, 1, 1)))
    np.testing.assert_array_equal(positions[4:], np.tile(later, (4, 1, 1)))


def test_burden_key_controls_all_inner_orders_final_and_native_ties():
    burdens = np.full((27, 32, p.U), 100, np.int64)
    native = np.zeros((27, 32, 3))
    native[2, 1, 0] = 1000  # Native preference cannot override better burden.
    for pair, value in [((1, 1), 80), ((1, 2), 50), ((0, 3), 75), ((4, 3), 60)]:
        burdens[pair] = value
    calls = []

    def score(q, mask):
        calls.append((q, mask))
        return native[q, mask]

    key = lambda q, m: s.ordering_r(q, m, native[q, m], burdens[q, m], 0)
    assert s.sequential_search(score, key, 1, 0) == (1, 2)
    oracle_keys = {(q, m): oracle_key(q, m, native[q, m], burdens[q, m], 0)
                   for q in range(27) for m in range(1, 32)}
    selected, expected = replay_paths(oracle_keys, 1, 0)
    assert selected == (1, 2) and calls == expected and len(calls) == 116
    assert calls[:27] == [(q, 1) for q in range(27)]
    assert calls[27:58] == [(1, m) for m in range(1, 32)]
    assert calls[58:89] == [(0, m) for m in range(1, 32)]
    assert calls[89:] == [(q, 3) for q in range(27)]
    # Equal maximum resolves by sum, followed by the complete native/tie tuple.
    a, b = np.zeros(p.U, np.int64), np.zeros(p.U, np.int64)
    a[0] = b[0] = 10
    b[1] = 5
    assert s.ordering_r(0, 1, [0, 0, 0], a, 0) > s.ordering_r(0, 1, [999, 50, 1], b, 0)
    for q in range(27):
        for mask in (1, 3, 7, 31):
            assert s.ordering_r(q, mask, [1.5, 10, 99], a, 13) == oracle_key(q, mask, [1.5, 10, -99], a, 13)


def test_settled_memory_changes_ranking_against_incremental_burden():
    snapshot = np.zeros(p.U, dtype=np.int64)
    snapshot[0] = 100
    first, second = snapshot.copy(), snapshot.copy()
    first[1] += 10
    second[0] += 5
    native = [0., 0., 0.]
    full_first = s.ordering_r(0, 1, native, first, 13)
    full_second = s.ordering_r(1, 1, native, second, 13)
    incremental_first = s.ordering_r(0, 1, native, first - snapshot, 13)
    incremental_second = s.ordering_r(1, 1, native, second - snapshot, 13)
    assert full_first > full_second
    assert incremental_first < incremental_second
    assert full_first == oracle_key(0, 1, native, first, 13)
    assert full_second == oracle_key(1, 1, native, second, 13)


def test_native_fixture_private_candidates_common_record_and_saved_replay(tmp_path):
    actor, own, actual, proposed = make()
    packet = inputs()[3]
    raw = retained.allocate_raw(8, 'O', actor.sites, packet)
    for tick in (0, 4):
        if tick:
            for executed_tick in range(4):
                actor.executed(executed_tick, actual, 7)
        result = actor.decide(own, actual, proposed, tick, 7)
        assert result['timely'] and result['key_length'] == 8
        assert result['request_count'] == 116
        assert result['scored_length'] == (4 if tick == 0 else 2)
        assert result['state_reductions'] == result['candidate_plans'] * result['scored_length']
        assert result['geometry_snapshots'] == 27 * result['scored_length']
        assert result['candidate_cache_hits'] == 116 - result['candidate_plans']
        np.testing.assert_array_equal(actor.execution.history.burden, result['snapshot_burden'])
        assert actor.execution.next_unsettled == tick
        assert len(actor.execution.predicted) == tick
        assert np.isnan(result['ordering_keys'][:, :, 8:]).all()
        retained.record_round(raw, result, tick, 'O')
        # Store the stable direction fields using the collector's prefix contract.
        for field in result['extra_record_fields']:
            value = np.asarray(result[field])
            assert value.dtype != object
            key = 'burden_' + field
            if key not in raw:
                raw[key] = np.zeros((2,) + value.shape, dtype=value.dtype)
            raw[key][tick // 4] = value
        prefix_last, prefix_burden = recurrence(result['snapshot_last'], result['snapshot_burden'], result['prefix_contacts'], tick)
        np.testing.assert_array_equal(prefix_last, result['prefix_last'])
        np.testing.assert_array_equal(prefix_burden, result['prefix_burden'])
        for q, mask in result['evaluated_pairs']:
            contacts, values = [], []
            for position in result['forecast'][q]:
                losses = radio.free_space_user_path_loss(position, actor.sites)
                sinr = radio.user_sinr_from_path_loss(losses, transmitter_mask=p.mask_array(mask))
                connections = radio.greedy_connection_assignment(sinr)
                metrics = radio.service_metrics(sinr, connections)
                contacts.append(connections.any(axis=0))
                values.append([metrics['J'], metrics['served'], metrics['quality']])
            np.testing.assert_array_equal(contacts, result['candidate_contacts'][q, mask])
            np.testing.assert_array_equal(np.mean(values, axis=0), result['scores'][q, mask])
            last, burden = recurrence(prefix_last, prefix_burden, contacts, tick + p.DELIVERY)
            np.testing.assert_array_equal(last, result['candidate_endpoint_last'][q, mask])
            np.testing.assert_array_equal(burden, result['candidate_endpoint_burden'][q, mask])
        assert result['recurring_bytes'] == 136
        commands = proposed.copy()
        commands[(tick // 4) % p.N] = COMMANDS[result['selected_q']]
        np.testing.assert_array_equal(result['commands'], commands)
    path = tmp_path / 'saved.npz'
    np.savez(path, **raw)
    with np.load(path, allow_pickle=False) as saved:
        for index, tick in enumerate((0, 4)):
            proposal_q = p.command_index(saved['burden_decoded_proposals'][index, (tick // 4) % p.N])
            keys = {}
            for q, mask in saved['burden_request_pairs'][index]:
                burden = saved['burden_candidate_endpoint_burden'][index, q, mask]
                native = saved['candidate_scores'][index, q, mask]
                key = oracle_key(q, mask, native, burden, proposal_q)
                np.testing.assert_array_equal(key, saved['ordering_keys'][index, q, mask, :8])
                keys[q, mask] = key
            selected, requests = replay_paths(keys, 7, proposal_q)
            assert selected == (saved['selected_q'][index], saved['selected_mask'][index])
            np.testing.assert_array_equal(requests, saved['burden_request_pairs'][index])
    assert set(inspect.signature(actor.executed).parameters) == {'tick', 'commands', 'mask'}
    assert set(inspect.signature(actor.decide).parameters) == {
        'own_observation', 'actual_commands', 'proposals', 'tick', 'current_mask', 'started', 'cpu_started'}


def test_late_anchor_censors_only_missing_prefix_and_burden_stays_unknown():
    actor, own, actual, proposed = make(clock=lambda: 2., horizon=12)
    first = actor.decide(own, actual, proposed, 0, 7, started=0.)
    assert_fallback(first, actual, 7)
    assert not first['decoded_anchor'] and actor.execution.anchors == {}
    for tick in range(4):
        actor.executed(tick, actual, 7)
    actor.clock = lambda: 0.
    late = actor.decide(own, actual, proposed, 4, 7)
    assert late['timely'] and late['burden_unknown']
    assert late['history_start'] == 4 and late['history_reductions'] == 0
    assert actor.execution.predicted == {} and actor.execution.next_unsettled == 4
    assert (late['snapshot_burden'] == 0).all() and late['unknown_age'].all()
    for tick in range(4, 8):
        actor.executed(tick, actual, 7)
    actor.execution.settle(8, evaluate=lambda *args: (np.ones(p.U, bool), np.zeros(3)))
    final = actor.decide(own, actual, proposed, 8, 7)
    assert final['timely'] and not final['unknown_age'].any()
    assert final['burden_unknown'] and actor.execution.history.burden_unknown
    assert sorted(actor.execution.predicted) == list(range(4, 8))


@pytest.mark.parametrize('phase', ['entry', 'encode', 'prefix', 'geometry', 'reduction', 'command_encode', 'command_decode', 'final_return'])
def test_deadline_each_phase_retains_whole_team_and_completed_evidence(monkeypatch, phase):
    now = [0.]
    actor, own, actual, proposed = make(clock=lambda: now[0])
    if phase == 'entry':
        now[0] = 2.
    elif phase in ('encode', 'command_encode', 'command_decode'):
        name = {'encode': 'encode_reports', 'command_encode': 'encode_command', 'command_decode': 'decode_command'}[phase]
        original = getattr(s, name)

        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            now[0] = 2.
            return value

        monkeypatch.setattr(s, name, late)
    elif phase == 'prefix':
        original = s.model

        def late(*args):
            value = original(*args)
            now[0] = 2.
            return value

        monkeypatch.setattr(s, 'model', late)
    elif phase in ('geometry', 'reduction'):
        name = 'free_space_user_path_loss' if phase == 'geometry' else 'service_metrics'
        original = getattr(radio, name)
        def late(*args, **kwargs):
            value = original(*args, **kwargs)
            # Frozen model binds its own imports; only candidate calls see this.
            now[0] = 2.
            return value

        monkeypatch.setattr(radio, name, late)
    else:
        original = s.decode_command
        decoded = [False]
        clock_calls = [0]

        def decode(*args):
            value = original(*args)
            decoded[0] = True
            return value

        def clock():
            if decoded[0]:
                clock_calls[0] += 1
            return 2. if clock_calls[0] >= 3 else 0.

        actor.clock = clock
        monkeypatch.setattr(s, 'decode_command', decode)
    result = actor.decide(own, actual, proposed, 0, 7, started=0.)
    assert_fallback(result, actual, 7)
    assert not actor.execution.history.burden.any()
    assert not actor.execution.history.windows.any()
    assert actor.execution.next_unsettled == 0
    if phase in ('entry', 'encode'):
        assert not result['decoded_anchor'] and actor.execution.anchors == {}
        assert not result['snapshot_valid'] and result['request_count'] == 0
    elif phase == 'prefix':
        assert result['snapshot_valid'] and not result['prefix_valid']
        assert result['prefix_ticks'] == 1 and result['request_count'] == 0
    elif phase in ('geometry', 'reduction'):
        assert result['prefix_valid'] and result['request_count'] == 1
        assert result['candidate_plans'] == 0 and result['interrupted_candidate_requests'] == 1
        assert np.isnan(result['scores']).all()
        assert (result['candidate_endpoint_burden'] == -2).all()
        assert (result['request_pairs'][1:] == -1).all()
        assert result['state_reductions'] == int(phase == 'reduction')
    else:
        assert result['candidate_plans'] > 0 and result['request_count'] == 116
        for q, mask in result['evaluated_pairs']:
            assert np.isfinite(result['ordering_keys'][q, mask, :8]).all()


def test_scheduler_history_deadline_commits_atomic_burden_then_resumes(monkeypatch):
    now = [0.]
    actor, own, actual, proposed = make(clock=lambda: now[0], horizon=12)
    actor.execution.anchor(0, np.tile([500, 500, 100], (p.N, 1)))
    for tick in range(4):
        actor.executed(tick, actual, 7)
    original = actor.execution.settle
    calls = [0]

    def evaluate(*args):
        calls[0] += 1
        if calls[0] == 2:
            now[0] = 2.
        return np.zeros(p.U, bool), np.zeros(3)

    monkeypatch.setattr(actor.execution, 'settle', lambda stop, check: original(stop, check, evaluate))
    interrupted = actor.decide(own, actual, proposed, 4, 7)
    assert_fallback(interrupted, actual, 7)
    assert interrupted['history_before'] == 0 and interrupted['history_after'] == 2
    assert interrupted['history_reductions'] == 2 and not interrupted['snapshot_valid']
    assert set(actor.execution.anchors) == {0, 4}
    assert (actor.execution.history.burden == 3).all()
    now[0] = 0.
    resumed = actor.decide(own, actual, proposed, 4, 7)
    assert resumed['timely'] and resumed['history_reductions'] == 2
    assert (resumed['snapshot_burden'] == 10).all()
    assert (actor.execution.history.burden == 10).all()


@pytest.mark.parametrize('arm,horizon', [('O', 8), ('R', 4), ('R', 10), ('R', 260)])
def test_invalid_arm_or_horizon(arm, horizon):
    with pytest.raises(ValueError):
        s.Scheduler(arm, inputs()[3], horizon=horizon)
