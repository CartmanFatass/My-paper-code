"""Local causal rule fixtures only; no production trace reads."""

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b05.allocation import RoundRobin, LeastRecentlyServed


@pytest.mark.parametrize('cls', [RoundRobin, LeastRecentlyServed])
def test_empty_capacity_and_registered_ids_only(cls):
    actor = cls()
    np.testing.assert_array_equal(actor.grant(np.empty(0, int), np.empty(0), 0), [])
    ids = np.arange(15)
    selected = actor.grant(ids, np.full(15, 3.), 1)
    assert len(selected) == 10 and len(set(selected)) == 10 and set(selected) <= set(ids)
    assert set(actor.grant(np.array([3, 18]), np.array([6., 9.]), 2)) == {3, 18}
    if cls is RoundRobin:
        assert actor.cursor == 4  # cursor10 scans18, wraps, then grants3
    else:
        assert actor.last_grant[18] == actor.last_grant[3] == 2


def test_rr_cursor_zero_empty_unchanged_wrap_and_current_eligibility():
    actor = RoundRobin()
    ids = np.arange(50)
    np.testing.assert_array_equal(actor.grant(ids[::-1], np.ones(50)*4, 0), np.arange(10))
    assert actor.cursor == 10
    actor.grant(np.empty(0, int), np.empty(0), 1)
    assert actor.cursor == 10
    np.testing.assert_array_equal(actor.grant(np.array([48, 49, 0, 1]), np.ones(4)*4, 2), [48, 49, 0, 1])
    assert actor.cursor == 2
    # It scans only current eligible IDs; previous misses confer no new information.
    np.testing.assert_array_equal(actor.grant(np.array([0, 3, 47]), np.array([30., 3., 9.]), 3), [3, 47, 0])
    assert actor.cursor == 1


def test_lrs_own_recency_then_descending_current_sinr_then_id():
    actor = LeastRecentlyServed()
    ids = np.arange(12)
    np.testing.assert_array_equal(actor.grant(ids[::-1], np.full(12, 5.), 0), np.arange(10))
    sinr = np.arange(12, dtype=float) + 3
    np.testing.assert_array_equal(actor.grant(ids, sinr, 1), [11, 10, 9, 8, 7, 6, 5, 4, 3, 2])
    assert actor.last_grant[0] == actor.last_grant[1] == 0
    assert np.all(actor.last_grant[2:12] == 1)


def test_handoff_does_not_transfer_other_uav_recency_and_mission_reset():
    first, arriving = LeastRecentlyServed(), LeastRecentlyServed()
    first.grant(np.arange(10), np.full(10, 8.), 0)
    ids = np.arange(11)
    sinr = np.full(11, 5.)
    np.testing.assert_array_equal(arriving.grant(ids, sinr, 1), np.arange(10))
    assert arriving.last_grant[10] == -1 and first.last_grant[10] == -1
    # New mission instances have no reset/refresh grant initialization.
    reset = LeastRecentlyServed()
    assert np.all(reset.last_grant == -1)
    rr = RoundRobin()
    assert rr.cursor == 0


@pytest.mark.parametrize('cls', [RoundRobin, LeastRecentlyServed])
@pytest.mark.parametrize('ids,sinr,tick', [
    ([1, 1], [3., 4.], 0), ([50], [3.], 0), ([-1], [3.], 0),
    ([1.], [3.], 0), ([1], [np.nan], 0), ([1], [], 0), ([1], [3.], -1),
])
def test_malformed_local_interface(cls, ids, sinr, tick):
    with pytest.raises(ValueError):
        cls().grant(np.asarray(ids), np.asarray(sinr), tick)


def test_rules_do_not_consume_future_or_global_state_and_numpy_rng_is_unchanged():
    state = np.random.get_state()
    for cls in (RoundRobin, LeastRecentlyServed):
        a, b = cls(), cls()
        for tick, ids in enumerate((np.arange(15), np.arange(2, 20), np.array([0, 49]))):
            sinr = np.full(len(ids), 5.)
            np.testing.assert_array_equal(a.grant(ids, sinr, tick), b.grant(ids.copy(), sinr.copy(), tick))
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])
