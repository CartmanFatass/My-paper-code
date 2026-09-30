import inspect

import numpy as np
import pytest

from experiments.candidates.uav_registered_service.b01 import history as h, scheduler as old
from experiments.candidates.uav_registered_service.b02 import scheduler as s
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_local_history.b01.controller import COMMANDS


def inputs():
    own = np.tile([.5, .5, .5], (5, 1)).astype(np.float32)
    actual = np.zeros((5, 3))
    proposed = np.tile([1, 0, 0], (5, 1))
    packet = p.encode_map(np.tile([500, 500], (50, 1)))
    return own, actual, proposed, packet


@pytest.mark.parametrize('tick,anchor,bits,expected', [
    (0, 0, 49, (0, True, False)), (0, 0, 50, (0, True, True)),
    (60, 0, 50, (0, False, False)), (124, 0, 50, (1, False, False)),
    (188, 0, 50, (2, False, False)),
    (64, 0, 49, (1, True, False)), (64, 0, 50, (1, True, True)),
    (4, 4, 50, (0, False, False)), (64, 4, 50, (1, True, True)),
    (252, 0, 50, (3, True, True)),
])
def test_exact_gate_edges(tick, anchor, bits, expected):
    history = h.ServiceHistory(start_tick=anchor)
    history.windows[(tick + 2) // 64, :bits] = True
    assert s.coverage_gate(history, tick, 256) == expected
    if tick == 64:
        history.windows[0] = True
        history.windows[1] = False
        assert s.coverage_gate(history, tick, 256) == (1, True, False)


def test_truth_free_api_and_private_prefix_no_persistence(monkeypatch):
    own, actual, proposed, packet = inputs()
    monkeypatch.setattr(s, 'model', lambda *args: (np.ones(50, bool), np.zeros(3)))
    actor = s.Scheduler('G', packet, lambda: 0., lambda: 0., horizon=8)
    result = actor.decide(own, actual, proposed, 0, 31)
    assert result['gate_computed'] and result['gate_eligible'] and result['gate_released']
    assert result['timely'] and result['key_length'] == 6
    assert result['prefix_windows'][0].all()
    assert actor.execution.next_unsettled == 0 and actor.execution.predicted == {}
    assert actor.execution.history.last.tolist() == [-1] * 50
    assert not actor.execution.history.windows.any()
    assert set(inspect.signature(actor.executed).parameters) == {'tick', 'commands', 'mask'}
    assert set(inspect.signature(actor.decide).parameters) == {
        'own_observation', 'actual_commands', 'proposals', 'tick', 'current_mask', 'started', 'cpu_started'}
    assert result['candidate_requests'] == 116
    assert result['state_reductions'] == 4 * result['candidate_plans']
    proposal_q = p.command_index(proposed[0])
    for q, mask in result['evaluated_pairs']:
        assert tuple(result['ordering_keys'][q, mask, :6]) == s.native_rank(q, mask, result['scores'][q, mask], proposal_q)


@pytest.mark.parametrize('released,expected', [(False, (1, 2)), (True, (2, 1))])
def test_both_inner_orders_and_final_choice_use_fixed_gate(released, expected):
    scores = np.zeros((27, 32, 3))
    scores[2, 1, 0] = 100
    age = np.zeros((27, 32))
    age[1, 1], age[1, 2], age[0, 3], age[4, 3] = 2, 3, 2.5, 2.8
    calls = []
    def score(q, mask):
        calls.append((q, mask))
        return scores[q, mask]
    # Noninteger synthetic counts only encode ranks; real actor counts are integer.
    key = lambda q, mask: (() if released else (age[q, mask],)) + s.native_rank(q, mask, scores[q, mask], 0)
    assert s.sequential_search(score, key, 1, 0) == expected
    assert len(calls) == 116
    assert calls[:27] == [(q, 1) for q in range(27)]
    assert calls[27:58] == [(expected[0], mask) for mask in range(1, 32)]
    assert calls[58:89] == [(0, mask) for mask in range(1, 32)]
    assert calls[89:] == [(q, 31 if released else 3) for q in range(27)]
    native = [1., 50., .3]
    assert s.ordering(released, 2, 1, native, [2, 4], 0) == (
        (() if released else (2, 4)) + s.native_rank(2, 1, native, 0))


def test_gate_is_called_once_before_any_candidate_and_candidate_cannot_release(monkeypatch):
    own, actual, proposed, packet = inputs()
    monkeypatch.setattr(s, 'model', lambda *args: (np.zeros(50, bool), np.zeros(3)))
    original_gate, original_search = s.coverage_gate, s.sequential_search
    calls = []
    def gate(*args):
        calls.append('gate')
        return original_gate(*args)
    def search(score, key, *args):
        assert calls == ['gate']
        def scored(q, mask):
            calls.append('candidate')
            return score(q, mask)
        return original_search(scored, key, *args)
    monkeypatch.setattr(s, 'coverage_gate', gate)
    monkeypatch.setattr(s, 'sequential_search', search)
    actor = s.Scheduler('G', packet, lambda: 0., lambda: 0., horizon=8)
    result = actor.decide(own, actual, proposed, 0, 31)
    assert result['timely'] and not result['gate_released'] and calls.count('gate') == 1
    assert result['key_length'] == 7 and not actor.execution.history.windows.any()


def test_before_release_g_matches_o_all_scientific_arrays_exactly():
    own, actual, proposed, packet = inputs()
    g = s.Scheduler('G', packet, lambda: 0., lambda: 0., horizon=12)
    o = old.Scheduler('O', packet, lambda: 0., lambda: 0., horizon=12)
    for tick in range(12):
        if tick % 4 == 0:
            gr = g.decide(own, actual, proposed, tick, 1)
            original = o.decide(own, actual, proposed, tick, 1)
            assert not gr['gate_released']
            for key in original:
                if key in ('reports', 'command_packet', 'sequential_pair', 'evaluated_pairs'):
                    assert gr[key] == original[key]
                else:
                    np.testing.assert_array_equal(gr[key], original[key])
        g.executed(tick, actual, 1)
        o.executed(tick, actual, 1)


def test_censored_anchor_crossing_terminal_and_history_continues(monkeypatch):
    own, actual, proposed, packet = inputs()
    actor = s.Scheduler('G', packet, lambda: 2., lambda: 0.)
    missing = actor.decide(own, actual, proposed, 0, 1, started=0.)
    assert not missing['decoded_anchor'] and not missing['gate_computed']
    for tick in range(4):
        actor.executed(tick, actual, 1)
    actor.clock = lambda: 0.
    monkeypatch.setattr(s, 'model', lambda *args: (np.ones(50, bool), np.zeros(3)))
    result = actor.decide(own, actual, proposed, 4, 1)
    assert result['prefix_windows'][0].all() and not result['gate_eligible']
    assert result['history_start'] == 4 and actor.execution.predicted == {}
    for tick in range(4, 60):
        actor.executed(tick, actual, 1)
    crossing = actor.decide(own, actual, proposed, 60, 1)
    assert crossing['timely'] and not crossing['gate_eligible'] and not crossing['gate_released']
    assert crossing['scored_length'] == 4 and crossing['history_reductions'] == 56
    for tick in range(60, 64):
        actor.executed(tick, actual, 1)
    released = actor.decide(own, actual, proposed, 64, 1)
    assert released['gate_released'] and released['history_after'] == 64
    assert not actor.execution.history.windows[1].any()
    for tick in range(64, 252):
        actor.executed(tick, actual, 1)
    terminal = actor.decide(own, actual, proposed, 252, 1)
    assert terminal['gate_released'] and terminal['scored_length'] == 2
    assert terminal['forecast'].shape == (27, 2, 5, 3)
    assert max(actor.execution.predicted) == 251
    assert len(actor.execution.predicted) == 248 and actor.execution.start_tick == 4


@pytest.mark.parametrize('phase', ['gate', 'decode'])
def test_charged_gate_and_final_decode_timeout_fallback_entire_team(monkeypatch, phase):
    own, actual, proposed, packet = inputs()
    now = [0.]
    monkeypatch.setattr(s, 'model', lambda *args: (np.ones(50, bool), np.zeros(3)))
    original = s.coverage_gate if phase == 'gate' else s.decode_command
    def overrun(*args):
        result = original(*args)
        now[0] = 2.
        return result
    monkeypatch.setattr(s, 'coverage_gate' if phase == 'gate' else 'decode_command', overrun)
    actor = s.Scheduler('G', packet, lambda: now[0], lambda: now[0], horizon=8)
    result = actor.decide(own, actual, proposed, 0, 7, started=0., cpu_started=0.)
    assert result['gate_computed'] and result['gate_released'] and not result['timely']
    assert result['actual_timeout'] and result['command_packet'] == b'' and result['mask'] == 7
    np.testing.assert_array_equal(result['commands'], actual)
    assert result['recurring_bytes'] == 120 and not actor.execution.history.windows.any()
    if phase == 'gate':
        assert result['gate_wall'] == result['prefix_wall'] == 2.
        assert result['candidate_requests'] == 0
    else:
        assert result['candidate_requests'] == 116


def test_atomic_backlog_replays_saved_anchors_without_recensoring():
    execution = h.ExecutionHistory(np.zeros((50, 2)))
    zero = np.zeros((5, 3))
    for tick in range(12):
        execution.append(tick, zero, 31)
    first, next_position = np.tile([100, 100, 100], (5, 1)), np.tile([600, 600, 100], (5, 1))
    execution.anchor(4, first)
    seen = []
    def evaluate(position, *args):
        seen.append(position.copy())
        return np.ones(50, bool), np.zeros(3)
    def check():
        if len(seen) == 2:
            raise s.DeadlineExceeded
    with pytest.raises(s.DeadlineExceeded):
        execution.settle(8, check, evaluate)
    assert execution.next_unsettled == 6 and sorted(execution.predicted) == [4, 5]
    execution.anchor(8, next_position)
    assert execution.settle(12, evaluate=evaluate) == (6, True)
    assert execution.start_tick == 4 and sorted(execution.predicted) == list(range(4, 12))
    np.testing.assert_array_equal(seen[:4], np.broadcast_to(first, (4, 5, 3)))
    np.testing.assert_array_equal(seen[4:], np.broadcast_to(next_position, (4, 5, 3)))
