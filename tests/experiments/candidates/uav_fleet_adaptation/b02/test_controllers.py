"""Synthetic numerical and causal cache checks; no native study trajectories."""
from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as c
from experiments.candidates.uav_local_history.b01 import controller as source


def row(own=(500., 500., 100.), users=(), sinr=(), peers=(), time=0.):
    result = np.zeros(104, dtype=np.float32)
    own, users, peers = np.asarray(own), np.asarray(users).reshape(-1, 2), np.asarray(peers).reshape(-1, 3)
    result[:3] = own / (1000., 1000., 100.) - (0., 0., .5)
    for slot, (user, db) in enumerate(zip(users, sinr)):
        result[3 + 3 * slot:6 + 3 * slot] = [*(user - own[:2]) / 1000., (db + 10.) / 50.]
    for slot, peer in enumerate(peers):
        result[63 + 4 * slot:67 + 4 * slot] = [*(peer - own) / (1000., 1000., 100.), 1.]
    result[-1] = time
    return result


def reference(observation, t, nav):
    teacher = source.LocalController(history=False)
    teacher._nav_index = nav
    command, diagnostic = teacher.act(observation, t)
    return command, diagnostic, teacher._nav_index


def assert_helper(observation, nav):
    result = c.analyze(observation, nav)
    command, diag, next_nav = reference(observation, 0, nav)
    assert result["fallback"] == diag["fallback"]
    assert result["next_nav"] == next_nav
    assert result["features"].dtype == np.float32 and result["features"].shape == (114,)
    np.testing.assert_array_equal(result["features"][:103], observation[:103])
    np.testing.assert_array_equal(result["features"][103:113], np.eye(10, dtype=np.float32)[nav])
    assert result["features"][-1] == diag["fallback"]
    n, p = result["n_current"], result["n_peers"]
    assert result["counters"]["helper_calls"] == 1
    assert result["counters"]["helper_setup_links"] == (1 + p) * n
    assert result["counters"]["helper_extreme_links"] == 2 * n
    assert set(result["counters"]) == {"helper_calls", "helper_setup_links", "helper_extreme_links"}
    if n:
        own, users, observed, peers = source._parse(observation)
        trajectory = source.LocalController._trajectories(own)
        exhaustive = source._power(trajectory, users)
        np.testing.assert_array_equal(result["extreme_power"][0], exhaustive.max(axis=(0, 1)))
        np.testing.assert_array_equal(result["extreme_power"][1], exhaustive.min(axis=(0, 1)))
    return result


def test_source_binding_and_empty_user_waypoint_clipping_rules():
    assert c.verify_source() == c.SOURCE_SHA256
    np.testing.assert_array_equal(c.C7_INDICES, np.arange(7))
    for waypoint in range(10):
        own = (*source.WAYPOINTS[waypoint], 50.)
        observation = row(own)
        assert c.initial_nav(observation) == waypoint
        result = assert_helper(observation, waypoint)
        assert result["fallback"] and result["next_nav"] == (waypoint + 1) % 10
    # Original <=60 arrival test and nextafter boundaries in observed FP32 input.
    for x in (40., np.nextafter(np.float32(.04), np.float32(0.)) * 1000.,
              np.nextafter(np.float32(.04), np.float32(1.)) * 1000., 160., 161.):
        assert_helper(row((x, 100., 150.)), 0)
    for own in ((0., 0., 50.), (1000., 1000., 150.), (0., 1000., 150.), (1000., 0., 50.)):
        observation = row(own, [(500., 500.)], [3.])
        assert_helper(observation, 9)


def test_randomized_physical_local_rows_helper_and_c7_exact_scores():
    rng = np.random.RandomState(71)
    for case in range(180):
        n, p = case % 21, case % 5
        own = rng.uniform([0., 0., 50.], [1000., 1000., 150.])
        users = rng.uniform(0., 1000., (n, 2))
        peers = rng.uniform([0., 0., 50.], [1000., 1000., 150.], (p, 3))
        observation = row(own, users, rng.uniform(-9., 45., n), peers)
        nav = case % 10
        result = assert_helper(observation, nav)
        command, diag, next_nav = reference(observation, 12, nav)
        small = c.MemoC7().query(observation, 12, nav)
        np.testing.assert_array_equal(small["scores"], diag["scores"][c.C7_INDICES])
        np.testing.assert_array_equal(small["served"], diag["served_candidates"][c.C7_INDICES])
        assert small["fallback"] == diag["fallback"] and small["next_nav"] == next_nav
        np.testing.assert_array_equal(small["features"], result["features"])
        if not small["fallback"]:
            assert small["action_index"] == c.C7_INDICES[np.argmax(diag["scores"][c.C7_INDICES])]
        else:
            own_decoded = source._parse(observation)[0]
            endpoints = source.LocalController._trajectories(own_decoded)[c.C7_INDICES, -1]
            target = np.r_[source.WAYPOINTS[next_nav], 50.]
            expected = c.C7_INDICES[np.argmin(np.sum((endpoints - target) ** 2, axis=1))]
            assert small["action_index"] == expected


def test_threshold_roundoff_calibration_and_iterated_clipping():
    # For one user/no peers, place the maximal candidate SINR near3dB,
    # then traverse representable observation values across that threshold.
    cases = (((500., 500., 100.), (850., 780.)),
             ((0., 0., 50.), (130., 130.)),
             ((1000., 1000., 150.), (750., 870.)),
             ((30., 970., 149.99999), (850., 60.)))
    observed_outcomes = set()
    for own, user in cases:
        observation = row(own, [user], [3.])
        decoded, users, _, _ = source._parse(observation)
        present = source._power(decoded[None], users)[0, 0]
        maximum = source._power(source.LocalController._trajectories(decoded), users).max()
        gamma = source.SINR_LINEAR * present / maximum
        center = np.float32((10. * np.log10(gamma) + 10.) / 50.)
        values = [center]
        below = above = center
        for _ in range(32):
            below = np.nextafter(below, np.float32(0.))
            above = np.nextafter(above, np.float32(1.))
            values.extend((below, above))
        for value in values:
            observation[5] = value
            result = assert_helper(observation, 3)
            observed_outcomes.add(result["fallback"])
    assert observed_outcomes == {False, True}
    # p=4 bypasses residual calibration; peer eligibility must also match C.
    own = (500., 500., 100.)
    user = (700., 500.)
    for altitude in (50., 50.00001, 100., 149.99999, 150.):
        peers = ((700., 500., altitude), (0., 0., 150.), (0., 1000., 150.), (1000., 0., 150.))
        assert_helper(row(own, [user], [3.], peers), 0)


def test_c7_full_support_nonfallback_even_when_subset_has_no_service():
    own, user = (500., 500., 150.), (800., 800.)
    observation = row(own, [user], [-2.])
    decoded, users, _, _ = source._parse(observation)
    powers = source._power(source.LocalController._trajectories(decoded), users)[..., 0]
    base = source._power(decoded[None], users)[0, 0]
    full, axes = powers.max(), powers[c.C7_INDICES].max()
    # A threshold between the best diagonal and best axis leaves C7 allzero.
    gamma = source.SINR_LINEAR * base / ((full + axes) * .5)
    observation[5] = (10. * np.log10(gamma) + 10.) / 50.
    controller = c.MemoC7()
    result = controller.query(observation, 0, 4)
    assert not result["fallback"] and result["next_nav"] == 4
    assert not result["served"].any() and result["action_index"] == 0
    assert not result["command"].any()


def test_peer_threshold_extreme_and_total_minus_station_rounding():
    # Keep own/all other peer links below3dB, and move one peer's encoded
    # coordinate through its exact best-candidate threshold. This exercises the
    # decreasing-in-own-power branch, including p=4 with no residual calibration.
    for p in range(1, 5):
        own, user = (0., 0., 100.), (900., 900.)

        def observed_at(x):
            return row(own, [user], [45.], [(x, x, 100.)] + [(0., 0., 150.)] * (p - 1))

        lower, upper = 0., 900.
        for _ in range(40):
            mid = (lower + upper) * .5
            analysis = c.analyze(observed_at(mid), 0)
            if analysis["extreme_sinr"][1, 1, 0] >= source.THRESHOLD:
                upper = mid
            else:
                lower = mid
        center = observed_at((lower + upper) * .5)
        values, below, above = [center[63]], center[63], center[63]
        for _ in range(32):
            below = np.nextafter(below, np.float32(0.))
            above = np.nextafter(above, np.float32(1.))
            values.extend((below, above))
        outcomes = set()
        for value in values:
            observation = center.copy()
            observation[63] = value
            analysis = assert_helper(observation, 0)
            assert analysis["unknown_power"][0] == 0.
            assert analysis["extreme_sinr"][0, 0, 0] < source.THRESHOLD
            own_decoded, users, _, _ = source._parse(observation)
            moving = source._power(source.LocalController._trajectories(own_decoded), users)
            full_power = np.concatenate((moving[:, :, None, :],
                                         np.broadcast_to(analysis["present_power"][None, None, 1:], (27, 4, p, 1))), axis=2)
            denominator = np.sum(full_power, axis=2, keepdims=True) - full_power + analysis["unknown_power"] + source.NOISE
            full_sinr = 10. * np.log10(full_power / denominator)
            assert analysis["extreme_sinr"][1, 1, 0] == full_sinr[:, :, 1, 0].max()
            outcomes.add(analysis["fallback"])
        assert outcomes == {False, True}


@pytest.mark.parametrize("kind", [c.MemoC, c.MemoC7])
def test_actual_history_key_time_omission_reset_and_return_copy_isolation(kind, monkeypatch):
    observation = row((100., 100., 75.))
    controller, other = kind(), kind()
    seen = []
    original_act = source.LocalController.act

    def act(self, observed, t):
        seen.append((observed.copy(), t, self._nav_index))
        return original_act(self, observed, t)

    monkeypatch.setattr(source.LocalController, "act", act)
    first = controller.query(observation, 8, 0)
    assert first["next_nav"] == 1 and not first["memo_hit"]
    after_miss = deepcopy(controller.counters)
    changed_time = observation.copy()
    changed_time[103] = .9
    hit = controller.query(changed_time, 100, 0)
    assert hit["memo_hit"] and hit["next_nav"] == 1
    assert c.memo_key(changed_time, 0) == c.memo_key(observation, 0)
    for counter in c.COUNTER_NAMES:
        if counter not in ("requests", "hits"):
            assert controller.counters[counter] == after_miss[counter]
    assert controller.counters["cache_key_bytes"] == 413
    assert controller.counters["cache_array_bytes"] == (900 if kind is c.MemoC else 580)
    for field in ("command", "scores", "served", "features"):
        hit[field][...] = 999.
    again = controller.query(observation, 104, 0)
    for field in ("command", "scores", "served", "features"):
        np.testing.assert_array_equal(again[field], first[field])
    changed_nav = controller.query(observation, 108, 7)
    assert not changed_nav["memo_hit"] and changed_nav["next_nav"] == 7
    changed_observation = observation.copy()
    changed_observation[0] = np.nextafter(changed_observation[0], np.float32(1.))
    assert not controller.query(changed_observation, 112, 7)["memo_hit"]
    assert not other.query(observation, 116, 0)["memo_hit"]
    if kind is c.MemoC:
        assert controller.counters["helper_calls"] == 0
        assert [(t, nav) for _, t, nav in seen[:3]] == [(8, 0), (108, 7), (112, 7)]
        np.testing.assert_array_equal(seen[0][0], observation)
        assert controller.counters["model_ticks"] == 3 * 108
    else:
        assert not seen
        assert controller.counters["helper_calls"] == 3
        assert controller.counters["model_ticks"] == 3 * 28
    controller.reset()
    assert not any(controller.counters.values())
    assert not controller.query(observation, 0, 0)["memo_hit"]


def test_full_c_paid_query_matches_source_and_actual_link_counters():
    observation = row((410., 510., 93.), [(610., 530.), (220., 290.)], [5., 4.], [(700., 540., 100.)])
    controller = c.MemoC()
    for t, nav in ((0, 1), (16, 5), (28, 3)):
        expected_command, diag, post = reference(observation, t, nav)
        result = controller.query(observation, t, nav)
        np.testing.assert_array_equal(result["command"], expected_command)
        np.testing.assert_array_equal(result["scores"], diag["scores"])
        np.testing.assert_array_equal(result["served"], diag["served_candidates"])
        assert (result["next_nav"], result["fallback"], result["action_index"]) == (
            post, diag["fallback"], diag["selected_index"])
    assert controller.counters["candidate_links"] == 3 * 108 * 2
    assert controller.counters["setup_links"] == 3 * 2 * 2
    assert controller.counters["helper_calls"] == 0
    small = c.MemoC7()
    small.query(observation, 0, 1)
    assert small.counters["candidate_links"] == 28 * 2
    assert small.counters["helper_setup_links"] == 2 * 2 and small.counters["setup_links"] == 0
    assert small.counters["helper_extreme_links"] == 4
    for t in (1, -4, 2.5, True):
        with pytest.raises(ValueError):
            controller.query(observation, t, 0)
    for nav in (-1, 10, .5, True):
        with pytest.raises(ValueError):
            c.analyze(observation, nav)


def test_n5_visible_peer_contract_rejects_outside_support():
    observation = row(peers=[(600., 500., 100.)] * 5)
    for operation in (lambda: c.analyze(observation, 0), lambda: c.memo_key(observation, 0),
                      lambda: c.initial_nav(observation), lambda: c.MemoC().query(observation, 0, 0),
                      lambda: c.MemoC7().query(observation, 0, 0)):
        with pytest.raises(ValueError, match="at most four visible peers"):
            operation()
