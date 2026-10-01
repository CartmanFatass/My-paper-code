"""Synthetic local/global recurrence and atomic settlement checks."""

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b06 import history as h
from experiments.candidates.uav_user_waiting.b02.scheduler import DeadlineExceeded


def values():
    result = np.full((5, 50), -10., np.float64)
    result[0, :15] = 3 + np.arange(15)
    result[1, 15:25] = 4.
    result[3, 25:] = 5.
    return result


def decode(grants):
    result = np.zeros((5, 50), bool)
    for member, row in enumerate(grants):
        valid = row[row >= 0]
        assert len(valid) == len(set(valid)) <= 10
        assert np.all(row[len(valid):] == -1)
        result[member, valid] = True
    return result


def reference(initial, tick, sinr):
    local, last, windows, burden = (initial.last_grant.copy(), initial.last.copy(),
                                    initial.windows.copy(), initial.burden.copy())
    expected = np.full((5, 10), -1, np.int8)
    for member in range(5):
        eligible = [u for u in range(50) if sinr[member, u] >= 3]
        ordered = sorted(eligible, key=lambda u: (int(local[member, u]), -float(sinr[member, u]), u))[:10]
        expected[member, :len(ordered)] = ordered
        local[member, ordered] = tick
    contacts = decode(expected).any(axis=0)
    last[contacts] = tick
    windows[tick // 64, contacts] = True
    burden += tick - last
    return expected, local, last, windows, burden


def assert_state(actual, before):
    assert actual.start_tick == before.start_tick
    for name in ('last', 'windows', 'burden', 'last_grant'):
        np.testing.assert_array_equal(getattr(actual, name), getattr(before, name))


def test_exact_lrs_priority_capacity_empty_rows_and_native_ties():
    initial = h.ServiceHistory()
    assert initial.last_grant.shape == (5, 50) and initial.last_grant.dtype == np.int64
    work = {key: 0 for key in h.WORK_KEYS}
    for tick in range(3):
        expected, local, last, windows, burden = reference(initial, tick, values())
        before = initial.copy()
        result, connections, native, grants = h.transition(initial, tick, values(), work=work)
        assert_state(initial, before)
        np.testing.assert_array_equal(grants, expected)
        np.testing.assert_array_equal(connections, decode(grants))
        for name, target in (('last_grant', local), ('last', last), ('windows', windows), ('burden', burden)):
            np.testing.assert_array_equal(getattr(result, name), target)
        assert np.all(grants[2] == -1) and np.all(grants[4] == -1)
        served = int(connections.sum())
        quality = sum(np.clip((values()[i, u]-3)/30, 0, 1) for i, u in zip(*np.nonzero(connections))) / served
        np.testing.assert_allclose(native, [.7*served/50+.3*quality, served, quality], atol=1e-12, rtol=0)
        initial = result
    assert work['lrs_row_selections'] == work['lrs_rows_completed'] == 15
    assert work['model_transitions_completed'] == 3


def test_global_recent_service_is_not_arriving_uav_local_recency():
    initial = h.ServiceHistory()
    initial.last[0], initial.last_grant[0, 0] = 9, 9
    initial.last[1:11], initial.last_grant[1, 1:11] = 5, 5
    initial.windows[0, :11] = True
    matrix = np.full((5, 50), -10.)
    matrix[1, :11] = np.arange(11) + 3.
    result, _, _, grants = h.transition(initial, 10, matrix)
    assert grants[1, 0] == 0  # globally youngest, locally unseen after handoff
    assert 1 not in grants[1]  # higher own recency tie loses on SINR
    assert result.last_grant[0, 0] == 9 and result.last_grant[1, 0] == 10
    assert initial.last_grant[1, 0] == -1


def test_copy_and_empty_grants_keep_state_private():
    original = h.ServiceHistory(start_tick=8)
    private = original.copy()
    private.last_grant[1, 7] = 8
    private.last[7] = 8
    assert original.last_grant[1, 7] == original.last[7] == -1
    result, connections, native, grants = h.transition(original, 8, np.full((5, 50), -10.))
    assert not connections.any() and np.all(grants == -1)
    np.testing.assert_array_equal(result.last_grant, original.last_grant)
    assert result.burden_unknown and np.all(result.burden == 9)
    np.testing.assert_array_equal(native, [0, 0, 0])


@pytest.mark.parametrize('invalid', [np.zeros((4, 50)), np.full((5, 50), np.nan), np.full((5, 50), np.inf), np.full((5, 50), 5.)])
def test_invalid_or_overlapping_modeled_eligibility_cannot_mutate_history(invalid):
    initial = h.ServiceHistory()
    before = initial.copy()
    with pytest.raises(ValueError):
        h.transition(initial, 0, invalid)
    assert_state(initial, before)


@pytest.fixture
def modeled(monkeypatch):
    monkeypatch.setattr(h, 'free_space_user_path_loss', lambda positions, sites: positions.copy())
    def sinr(losses, transmitter_mask):
        matrix = values()
        matrix[~transmitter_mask] = -np.inf
        return matrix
    monkeypatch.setattr(h, 'user_sinr_from_path_loss', sinr)


def execution(ticks=4):
    result = h.ExecutionHistory(np.zeros((50, 2)))
    for tick in range(ticks):
        result.append(tick, np.zeros((5, 3)), 31)
    result.anchor(0, np.tile([500, 500, 100], (5, 1)))
    return result


@pytest.mark.parametrize('exception', [RuntimeError, DeadlineExceeded])
def test_mid_row_exception_settlement_keeps_local_global_position_and_clock_atomic(exception, modeled, monkeypatch):
    actor = execution()
    before, position = actor.history.copy(), actor.position.copy()
    original = h.LeastRecentlyServed.grant
    calls = [0]
    def fail(self, ids, sinr, tick):
        calls[0] += 1
        if calls[0] == 3:
            raise exception('synthetic mid-row interruption')
        return original(self, ids, sinr, tick)
    with monkeypatch.context() as temporary:
        temporary.setattr(h.LeastRecentlyServed, 'grant', fail)
        with pytest.raises(exception):
            actor.settle(4)
    assert_state(actor.history, before)
    np.testing.assert_array_equal(actor.position, position)
    assert actor.next_unsettled == 0 and actor.predicted == actor.predicted_grants == {}
    partial = actor.settlement_partial
    assert partial['tick'] == 0 and partial['completed_rows'] == 2
    np.testing.assert_array_equal(partial['input_history']['last_grant'], before.last_grant)
    assert np.all(partial['grants'][2:] == -1)
    assert actor.work_counts['lrs_row_selections'] == 3 and actor.work_counts['lrs_rows_completed'] == 2
    assert actor.work_counts['model_transitions_completed'] == 0
    assert actor.settle(4) == (4, True)
    assert actor.next_unsettled == 4 and actor.settlement_partial == {}
    expected, *_ = reference(before, 0, values())
    np.testing.assert_array_equal(actor.predicted_grants[0], expected)
    assert actor.work_counts['model_fleet_ticks'] == 5
    assert actor.work_counts['lrs_row_selections'] == 23
    assert actor.work_counts['model_transitions_completed'] == 4


def test_deadline_after_full_transition_keeps_whole_committed_unit(modeled):
    actor = execution()
    checks = [0]
    def deadline():
        checks[0] += 1
        if checks[0] == 2:
            raise DeadlineExceeded
    with pytest.raises(DeadlineExceeded):
        actor.settle(4, deadline)
    assert actor.next_unsettled == 1 and actor.settlement_partial == {}
    contacts = decode(actor.predicted_grants[0]).any(axis=0)
    np.testing.assert_array_equal(actor.predicted[0], contacts)
    assert np.all(actor.history.last[contacts] == 0)
    assert np.all(actor.history.last_grant[decode(actor.predicted_grants[0])] == 0)
    assert np.all(actor.history.burden == np.where(contacts, 0, 1))


def test_unknown_start_and_anchor_quantization_preserve_censoring(modeled):
    actor = h.ExecutionHistory(np.zeros((50, 2)))
    for tick in range(12):
        actor.append(tick, np.tile([1, 0, 0], (5, 1)), 31)
    assert actor.settle(8) == (0, False)
    anchor = np.tile([995, 500, 100], (5, 1))
    actor.anchor(8, anchor)
    assert actor.start_tick == actor.next_unsettled == 8 and actor.history.burden_unknown
    assert actor.settle(12) == (4, True)
    assert set(actor.predicted) == set(actor.predicted_grants) == {8, 9, 10, 11}
    assert actor.history.burden_unknown
    assert np.all(actor.position[:, 0] == 1000)
    assert np.all(actor.history.last_grant[actor.history.last_grant >= 0] >= 8)
