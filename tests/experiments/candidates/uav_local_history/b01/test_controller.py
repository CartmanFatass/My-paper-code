import math

import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController


def observation(own=(500.0, 500.0, 100.0), users=(), peers=()):
    row = np.zeros(104, dtype=np.float32)
    own = np.asarray(own, dtype=float)
    row[:3] = (own[0] / 1000, own[1] / 1000, (own[2] - 50) / 100)
    for i, (x, y, sinr) in enumerate(users):
        row[3 + 3*i:6 + 3*i] = ((x-own[0])/1000, (y-own[1])/1000, (sinr+10)/50)
    for i, (x, y, z) in enumerate(peers):
        row[63 + 4*i:67 + 4*i] = ((x-own[0])/1000, (y-own[1])/1000,
                                   (z-own[2])/100, 0.5)
    return row


def scalar_power(station, user):
    d = math.sqrt((station[0]-user[0])**2 + (station[1]-user[1])**2 + station[2]**2)
    loss = 20*math.log10(d) + 20*math.log10(4*math.pi/0.15)
    return 10**((23-loss)/10)


def scalar_score(own, user, command):
    position = np.asarray(own, dtype=float)
    scores = []
    served = []
    for _ in range(4):
        position = np.clip(position + 30*np.asarray(command), (0, 0, 50), (1000, 1000, 150))
        gamma = 10*math.log10(scalar_power(position, user) / 1e-8)
        yes = gamma >= 3
        served.append(int(yes))
        scores.append(0.7/50 + 0.3*min(max((gamma-3)/30, 0), 1) if yes else 0)
    return np.mean(scores), np.mean(served)


def scalar_greedy_score(own, peer, users, hidden, command):
    position = np.asarray(own, dtype=float)
    values = []
    counts = []
    for _ in range(4):
        position = np.clip(position + 30*np.asarray(command), (0, 0, 50), (1000, 1000, 150))
        pairs = []
        for j, user in enumerate(users):
            powers = (scalar_power(position, user), scalar_power(peer, user))
            for tx in (0, 1):
                gamma = 10*math.log10(powers[tx] / (powers[1-tx] + hidden + 1e-8))
                if gamma >= 3:
                    pairs.append((gamma, tx, j))
        pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
        used = set()
        tx_counts = [0, 0]
        qualities = []
        for gamma, tx, j in pairs:
            if j in used or tx_counts[tx] == 10:
                continue
            used.add(j)
            tx_counts[tx] += 1
            qualities.append(np.clip((gamma-3)/30, 0, 1))
        count = len(used)
        counts.append(count)
        values.append(0.7*count/50 + 0.3*(sum(qualities)/max(count, 1)))
    return np.mean(values), np.mean(counts)


def test_single_user_scalar_radio_and_counts():
    own = (500., 500., 100.)
    user = (850., 500.)
    gamma = 10*math.log10(scalar_power(own, user) / 1e-8)
    controller = LocalController(False)
    command, diag = controller.act(observation(own, [(user[0], user[1], gamma)]), 0)
    expected = np.array([scalar_score(own, user, action) for action in COMMANDS])
    np.testing.assert_allclose(diag['scores'], expected[:, 0], rtol=0, atol=1e-7)
    np.testing.assert_allclose(diag['served_candidates'], expected[:, 1], rtol=0, atol=1e-12)
    np.testing.assert_array_equal(command, COMMANDS[diag['selected_index']])
    assert controller.counters['trajectories'] == 27
    assert controller.counters['model_ticks'] == 108
    assert controller.counters['candidate_link_evaluations'] == 108
    assert controller.counters['objective_reductions'] == 108


def test_current_sinr_calibrates_unknown_interference():
    own = (500., 500., 100.)
    user = (850., 500.)
    hidden = 2e-8
    gamma = 10*math.log10(scalar_power(own, user) / (1e-8 + hidden))
    controller = LocalController(False)
    _, diag = controller.act(observation(own, [(user[0], user[1], gamma)]), 0)
    candidate = int(np.flatnonzero(np.all(COMMANDS == 0, axis=1))[0])
    future_gamma = 10*math.log10(scalar_power(own, user) / (1e-8 + hidden))
    expected = 0.7/50 + 0.3*np.clip((future_gamma-3)/30, 0, 1)
    assert diag['scores'][candidate] == pytest.approx(expected, abs=1e-7)


def test_capacity_and_native_quality_reduction():
    own = (500., 500., 100.)
    users = [(510. + 7*i, 500. + 2*i) for i in range(20)]
    rows = [(x, y, 10*math.log10(scalar_power(own, (x, y)) / 1e-8)) for x, y in users]
    controller = LocalController(False)
    _, diag = controller.act(observation(own, rows), 0)
    stationary = int(np.flatnonzero(np.all(COMMANDS == 0, axis=1))[0])
    qualities = sorted((min(max((gamma-3)/30, 0), 1) for _, _, gamma in rows), reverse=True)
    assert diag['served_candidates'][stationary] == 10
    assert diag['scores'][stationary] == pytest.approx(0.7*10/50 + 0.3*np.mean(qualities[:10]), abs=1e-7)


def test_visible_peer_scalar_greedy_and_link_accounting():
    own = (500., 500., 100.)
    peer = (800., 500., 100.)
    users = [(500. + 10*i, 500.) for i in range(12)]
    hidden = 1e-9
    observed = [(x, y, 10*math.log10(scalar_power(own, (x, y)) /
                                       (scalar_power(peer, (x, y)) + hidden + 1e-8)))
                for x, y in users]
    assert min(row[2] for row in observed) >= 3
    controller = LocalController(False)
    _, diag = controller.act(observation(own, observed, [peer]), 0)
    expected = np.array([scalar_greedy_score(own, peer, users, hidden, action)
                         for action in COMMANDS])
    np.testing.assert_allclose(diag['scores'], expected[:, 0], atol=1e-7)
    np.testing.assert_allclose(diag['served_candidates'], expected[:, 1], atol=1e-12)
    assert controller.counters['candidate_link_evaluations'] == 108*12
    assert controller.counters['setup_link_evaluations'] == 2*12
    assert controller.counters['grid_power_evaluations'] == 0
    assert controller.counters['link_evaluations'] == (108+2)*12


def test_cache_row_reordering_reset_and_per_agent_isolation():
    a, b = (400., 500.), (600., 500.)
    first = LocalController(True)
    other = LocalController(True)
    first.act(observation(users=[(*a, 8.), (*b, 5.)]), 0)
    first.act(observation(users=[(*b, 6.), (*a, 7.)]), 1)
    assert len(first.points) == 2
    assert first.counters['cache_matches'] == 2
    assert first.counters['cache_inserts'] == 2
    assert len(other.points) == 0
    copy = first.points
    copy[0] = -1
    assert np.all(first.points >= 0)
    first.reset()
    assert len(first.points) == 0
    assert first.counters['cache_matches'] == 0


def test_cache_eviction_uses_last_seen_then_insertion_order():
    controller = LocalController(True)
    for t in range(4):
        batch = [(20. + 10*i, 20. + 10*t, 6.) for i in range(20)]
        controller.act(observation(users=batch), t)
    assert len(controller.points) == 64
    assert controller.counters['cache_evicts'] == 16
    assert controller.counters['cache_inserts'] == 64
    assert not np.any(np.all(np.isclose(controller.points, (20., 20.)), axis=1))
    assert np.any(np.all(np.isclose(controller.points, (180., 20.)), axis=1))


def test_hold_ingests_each_step_and_shadow_is_read_only():
    controller = LocalController(True)
    empty = observation(own=(100., 100., 50.))
    command0, diag0 = controller.act(empty, 0)
    assert diag0['fallback'] and diag0['shadow_current_fallback']
    assert diag0['selected_index'] == diag0['shadow_current_index']
    first_index = controller._nav_index
    for t in (1, 2, 3):
        command, diag = controller.act(observation(own=(100.+30*t, 100., 50.),
                                                   users=[(500., 500., 5.)]), t)
        np.testing.assert_array_equal(command, command0)
        assert not diag['decision']
    assert controller._nav_index == first_index
    assert controller.counters['ingests'] == 4
    assert controller.counters['decisions'] == 1
    assert controller.counters['shadow_decisions'] == 1
    assert controller.counters['shadow_objective_reductions'] == 108


def test_absent_point_censoring_and_shadow_current_subset():
    own = (500., 500., 50.)
    point = (500., 500.)
    controller = LocalController(True)
    controller.act(observation(own, [(*point, 15.)]), 0)
    for t in (1, 2, 3):
        controller.act(observation(own), t)
    _, diag = controller.act(observation(own), 4)
    assert diag['n_absent'] == 1
    assert diag['n_current'] == 0
    assert diag['shadow_current_fallback']
    assert diag['fallback']
    assert np.max(diag['served_candidates']) == 0
    assert controller.counters['setup_link_evaluations'] >= 64
    assert controller.counters['candidate_link_evaluations'] == 216


def test_shadow_current_scores_reuse_identical_current_model():
    own = (500., 500., 100.)
    first = (650., 500., 8.)
    second = (350., 500., 7.)
    hist = LocalController(True)
    current = LocalController(False)
    for t, rows in ((0, [first]), (1, []), (2, []), (3, []), (4, [second])):
        obs = observation(own, rows)
        _, hdiag = hist.act(obs, t)
        _, cdiag = current.act(obs, t)
    np.testing.assert_allclose(hdiag['shadow_scores'], cdiag['scores'], atol=1e-12)
    np.testing.assert_allclose(hdiag['shadow_served_candidates'], cdiag['served_candidates'], atol=1e-12)
    assert hdiag['shadow_current_index'] == cdiag['selected_index']
    assert hdiag['n_absent'] == 1


def test_four_visible_peers_do_not_invent_hidden_interference():
    own = (500., 500., 50.)
    far_peers = [(0., 0., 100.), (0., 1000., 100.), (1000., 0., 100.), (1000., 1000., 100.)]
    controller = LocalController(True)
    controller.act(observation(own, [(500., 500., 3.5)], far_peers), 0)
    assert controller.counters['calibration_discrepancy_rows'] == 1
    for t in (1, 2, 3):
        controller.act(observation(own, peers=far_peers), t)
    controller.act(observation(own, peers=far_peers), 4)
    assert controller.counters['grid_power_evaluations'] == 0
    assert controller.counters['censor_discrepancy_rows'] >= 1


def test_top_twenty_censor_uses_weakest_row_not_three_db():
    own = (500., 500., 50.)
    peers = [(0., 0., 100.), (0., 1000., 100.), (1000., 0., 100.)]
    def decide_with_rows(count):
        controller = LocalController(True)
        controller.act(observation(own, [(500., 500., 15.)], peers), 0)
        for t in (1, 2, 3):
            controller.act(observation(own, peers=peers), t)
        rows = [(300.+i, 300., 3.1) for i in range(count)]
        return controller.act(observation(own, rows, peers), 4)[1]

    nineteen = decide_with_rows(19)
    twenty = decide_with_rows(20)
    assert nineteen['n_absent'] == 1
    assert twenty['n_absent'] == 1
    assert nineteen['max_absent_current_sinr_db'] < 3
    assert twenty['max_absent_current_sinr_db'] > 3
    assert twenty['max_absent_current_sinr_db'] < 3.1


def test_current_arm_discards_absent_points_and_sweep_clips():
    controller = LocalController(False)
    controller.act(observation(users=[(600., 500., 5.)]), 0)
    controller.act(observation(), 1)
    assert len(controller.points) == 0
    assert len(controller.cache_points) == 0
    _, diag = controller.act(observation(own=(0., 0., 50.)), 4)
    assert diag['fallback']
    assert diag['n_cached'] == 0
    assert diag['predicted_J'] == 0


def test_real_reset_row_reconstructs_lawful_user_coordinates():
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real

    env = make_real(seed=17)
    rows, _ = env.reset()
    controller = LocalController(True)
    controller.act(rows[0], 0)
    truth = env.env.user_positions
    for point in controller.current_points:
        assert np.min(np.linalg.norm(truth - point, axis=1)) < 0.01
    env.close()
