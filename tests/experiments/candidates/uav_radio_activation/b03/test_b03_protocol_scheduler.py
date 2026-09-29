import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_radio_activation.b03 import scheduler as s


def inputs():
    own = np.tile([.5, .5, .5], (5, 1)).astype(np.float32)
    actual = np.tile(COMMANDS[0], (5, 1))
    proposals = np.tile(COMMANDS[0], (5, 1))
    site_packet = p.encode_map(np.tile([500, 500], (50, 1)))
    return own, actual, proposals, site_packet


def fake_radio(monkeypatch):
    monkeypatch.setattr(s, 'free_space_user_path_loss', lambda positions, sites: positions)
    monkeypatch.setattr(s, 'user_sinr_from_path_loss',
                        lambda loss, transmitter_mask: (loss, transmitter_mask))
    monkeypatch.setattr(s, 'greedy_connection_assignment', lambda sinr: None)
    monkeypatch.setattr(s, 'service_metrics',
                        lambda sinr, connections: {'J': 1., 'served': 10., 'quality': .5})


def test_version_three_delivery_hold_and_terminal_report():
    own, actual, proposals, _ = inputs()
    actual[0] = COMMANDS[3]
    proposals[0] = COMMANDS[7]
    packets = p.encode_reports(own, actual, proposals, 252)
    positions, actual_wire, proposals_wire = p.decode_reports(packets, 252)
    np.testing.assert_array_equal(positions, np.tile([500, 500, 100], (5, 1)))
    np.testing.assert_array_equal(actual_wire, actual)
    np.testing.assert_array_equal(proposals_wire, proposals)
    assert len(packets) == 5 and all(len(packet) == 24 for packet in packets)
    assert p.REPORT.unpack(packets[0])[:6] == (3, 0, 4, 2, 63, 252)
    command = p.encode_command(19, 3, 7, 252)
    assert len(command) == 16 and p.decode_command(command, 252) == (19, 3, 7)
    assert p.COMMAND.unpack(command) == (3, 19, 4, 3, 63, 254, 7)
    assert p.SEED == 29307000 and p.WORLDS == 64
    assert p.DEADLINE_SECONDS == pytest.approx(1.456)
    assert 64 * (sum(map(len, packets)) + len(command)) == 8704
    assert tuple(p.REPORT_TICKS) == tuple(range(0, 256, 4))
    with pytest.raises(ValueError):
        p.encode_reports(own, actual, proposals, 256)
    with pytest.raises(ValueError):
        p.decode_reports(packets, 248)
    with pytest.raises(ValueError):
        p.decode_reports(packets[::-1], 252)
    with pytest.raises(ValueError):
        p.decode_reports((bytes([2]) + packets[0][1:], *packets[1:]), 252)
    with pytest.raises(ValueError):
        p.decode_reports((packets[0][:3] + b'\x04' + packets[0][4:], *packets[1:]), 252)
    with pytest.raises(ValueError):
        p.decode_command(command, 248)
    with pytest.raises(ValueError):
        p.decode_command(bytes([2]) + command[1:], 252)
    with pytest.raises(ValueError):
        p.decode_command(p.COMMAND.pack(3, 19, 4, 3, 63, 256, 7), 252)


def test_two_actual_prefix_ticks_candidate_offsets_and_terminal_bound():
    positions = np.tile([500, 500, 100], (5, 1))
    actual = np.tile([1, 0, 0], (5, 1))
    proposals = np.zeros((5, 3))
    zero_q = p.command_index([0, 0, 0])
    move_q = p.command_index([1, 0, 0])
    forecast = p.forecast_positions(positions, actual, proposals, 0, 0)
    assert forecast.shape == (27, 4, 5, 3)
    np.testing.assert_array_equal(forecast[zero_q, :, 0, 0], [560] * 4)
    np.testing.assert_array_equal(forecast[move_q, :, 0, 0], [590, 620, 650, 680])
    np.testing.assert_array_equal(forecast[move_q, :, 1, 0], [560] * 4)
    terminal = p.forecast_positions(positions, actual, proposals, 252, 3)
    assert terminal.shape == (27, 2, 5, 3)
    np.testing.assert_array_equal(terminal[move_q, :, 3, 0], [590, 620])
    for horizon in (8, 12, 16):
        last = horizon - 4
        member = (last // 4) % 5
        assert p.forecast_positions(positions, actual, proposals, last, member,
                                    horizon=horizon).shape == (27, 2, 5, 3)
    with pytest.raises(ValueError):
        p.forecast_positions(positions, actual, proposals, 8, 2, horizon=8)


def test_nonpanel_fixture_positions_roundtrip():
    for seed in (29306999, 29307064):
        rng = np.random.default_rng(seed)
        xyz = np.column_stack((rng.integers(0, 1001, 5),
                               rng.integers(0, 1001, 5),
                               rng.integers(50, 151, 5)))
        own = (xyz - [0, 0, 50]) / [1000, 1000, 100]
        actual = COMMANDS[rng.integers(0, len(COMMANDS), 5)]
        proposals = COMMANDS[rng.integers(0, len(COMMANDS), 5)]
        decoded, actual_wire, proposals_wire = p.decode_reports(
            p.encode_reports(own, actual, proposals, 4), 4)
        np.testing.assert_array_equal(decoded, xyz)
        np.testing.assert_array_equal(actual_wire, actual)
        np.testing.assert_array_equal(proposals_wire, proposals)


def test_both_sequential_orders_and_joint_tie_order():
    q0 = p.command_index([0, 0, 0])
    q1 = p.command_index([1, 0, 0])
    matrix = np.zeros((27, 32, 3))
    matrix[q0, 1, 0] = .5
    matrix[q1, 1, 0] = .6
    matrix[q1, 2, 0] = .7
    matrix[q0, 2, 0] = .8
    assert s.sequential_search(lambda q, m: matrix[q, m], 1, q0) == (q0, 2)
    matrix[q1, 2, 0] = .9
    assert s.sequential_search(lambda q, m: matrix[q, m], 1, q0) == (q1, 2)
    assert s.rank(q0, 3, (1., 20.), q0) > s.rank(q1, 31, (1., 20.), q0)
    assert s.rank(q1, 31, (1., 20.), q0) > s.rank(q1, 1, (1., 20.), q0)
    assert s.rank(q1, 1, (1., 20.), q0) > s.rank(q1, 2, (1., 20.), q0)


def test_complete_search_cache_work_and_terminal_scoring(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    exhaustive = s.Scheduler('T2', site_packet, lambda: 0.0,
                             lambda: 0.0).decide(own, actual, proposals, 252, 31)
    assert exhaustive['timely'] and exhaustive['selected_q'] == 0
    assert exhaustive['selected_mask'] == exhaustive['mask'] == 31
    assert exhaustive['sequential_pair'] == (0, 31)
    np.testing.assert_array_equal(exhaustive['sequential_score'], [1., 10., .5])
    assert exhaustive['forecast'].shape == (27, 2, 5, 3)
    assert exhaustive['scored_length'] == exhaustive['prefix_ticks'] == 2
    assert exhaustive['scores'].shape == (27, 32, 3)
    assert len(exhaustive['evaluated_pairs']) == exhaustive['candidate_plans'] == 837
    assert exhaustive['candidate_requests'] == 837
    assert exhaustive['state_reductions'] == 1674
    assert exhaustive['geometry_snapshots'] == 54
    assert exhaustive['recurring_bytes'] == 136
    sequential = s.Scheduler('S2', site_packet, lambda: 0.0,
                             lambda: 0.0, horizon=8).decide(
                                 own, actual, proposals, 4, 31)
    assert sequential['timely'] and sequential['candidate_requests'] == 116
    assert sequential['candidate_requests'] > sequential['candidate_plans']
    assert sequential['sequential_pair'] == (
        sequential['selected_q'], sequential['selected_mask'])
    assert sequential['state_reductions'] == 2 * sequential['candidate_plans']
    assert sequential['geometry_snapshots'] <= 54
    assert sequential['forecast'].shape == (27, 2, 5, 3)


def test_real_radio_score_uses_only_scored_states():
    from envs.pettingzoo.uav_radio import (
        free_space_user_path_loss, greedy_connection_assignment,
        service_metrics, user_sinr_from_path_loss,
    )
    own, actual, proposals, site_packet = inputs()
    result = s.Scheduler('S2', site_packet, lambda: 0.0,
                         lambda: 0.0, horizon=8).decide(
                             own, actual, proposals, 4, 31)
    q, mask = result['evaluated_pairs'][0]
    sites = p.decode_map(site_packet)
    values = []
    for positions in result['forecast'][q]:
        loss = free_space_user_path_loss(positions, sites)
        sinr = user_sinr_from_path_loss(loss, transmitter_mask=p.mask_array(mask))
        metrics = service_metrics(sinr, greedy_connection_assignment(sinr))
        values.append([metrics['J'], metrics['served'], metrics['quality']])
    assert len(values) == 2
    np.testing.assert_allclose(result['scores'][q, mask], np.mean(values, axis=0),
                               rtol=0, atol=1e-14)


def test_full_deadline_and_atomic_miss_at_encode_decode(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    actual[0] = COMMANDS[1]
    proposals[0] = COMMANDS[2]
    scheduler = s.Scheduler('S2', site_packet, lambda: 1.457, lambda: 0.0)
    late = scheduler.decide(own, actual, proposals, 0, 7, started=0.0, cpu_started=0.0)
    assert not late['timely'] and late['reports'] == () and late['recurring_bytes'] == 0
    assert late['command_packet'] == b'' and late['mask'] == 7
    np.testing.assert_array_equal(late['commands'], actual)

    now = [0.0]
    real_encode = s.encode_reports

    def encode_late(*args):
        packets = real_encode(*args)
        now[0] = 1.457
        return packets

    monkeypatch.setattr(s, 'encode_reports', encode_late)
    late = s.Scheduler('S2', site_packet, lambda: now[0],
                       lambda: 0.0).decide(own, actual, proposals, 0, 7)
    assert not late['timely'] and late['reports'] and late['recurring_bytes'] == 120
    assert late['candidate_requests'] == 0 and late['command_packet'] == b''
    np.testing.assert_array_equal(late['commands'], actual)
    monkeypatch.setattr(s, 'encode_reports', real_encode)

    real_decode = s.decode_command

    def decode_late(*args):
        result = real_decode(*args)
        now[0] = 1.457
        return result

    now[0] = 0.0
    monkeypatch.setattr(s, 'decode_command', decode_late)
    late = s.Scheduler('S2', site_packet, lambda: now[0],
                       lambda: 0.0).decide(own, actual, proposals, 0, 7)
    assert not late['timely'] and late['candidate_plans'] > 0
    assert late['reports'] and late['recurring_bytes'] == 120
    assert late['command_packet'] == b'' and late['mask'] == 7
    np.testing.assert_array_equal(late['commands'], actual)


def test_repeated_misses_keep_actual_whole_team_beyond_hold(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    actual[0] = COMMANDS[1]
    proposals[0] = COMMANDS[2]
    scheduler = s.Scheduler('S2', site_packet, lambda: 2.0, lambda: 0.0,
                            horizon=16)
    commands, mask = actual, 7
    for tick in (0, 4, 8, 12):
        result = scheduler.decide(own, commands, proposals, tick, mask,
                                  started=0.0, cpu_started=0.0)
        assert not result['timely'] and result['selected_q'] is None
        assert result['selected_mask'] is None and result['command_packet'] == b''
        np.testing.assert_array_equal(result['commands'], actual)
        assert result['mask'] == 7
        commands, mask = result['commands'], result['mask']


def test_partial_reduction_miss_preserves_work(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    now = [0.0]

    def late_metric(sinr, connections):
        now[0] = 1.457
        return {'J': 1., 'served': 10., 'quality': .5}

    monkeypatch.setattr(s, 'service_metrics', late_metric)
    result = s.Scheduler('S2', site_packet, lambda: now[0],
                         lambda: 0.0).decide(own, actual, proposals, 0, 3)
    assert not result['timely'] and result['candidate_plans'] == 0
    assert result['candidate_requests'] == 1 and result['state_reductions'] == 1
    assert result['geometry_snapshots'] == 4 and result['prefix_ticks'] == 2
    assert result['command_packet'] == b'' and result['mask'] == 3
    np.testing.assert_array_equal(result['commands'], actual)
