import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b02 import protocol as p
from experiments.candidates.uav_radio_activation.b02 import scheduler as s
from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)


def inputs():
    own = np.tile([.5, .5, .5], (5, 1)).astype(np.float32)
    actual = np.tile(COMMANDS[0], (5, 1))
    proposals = np.tile(COMMANDS[0], (5, 1))
    site_packet = p.encode_map(np.tile([500, 500], (50, 1)))
    return own, actual, proposals, site_packet


def test_version_two_codec_and_rejections():
    own, actual, proposals, _ = inputs()
    actual[0] = COMMANDS[3]
    proposals[0] = COMMANDS[7]
    packets = p.encode_reports(own, actual, proposals, 248)
    position, decoded_actual, decoded_proposals = p.decode_reports(packets, 248)
    assert len(packets) == 5 and all(len(packet) == 24 for packet in packets)
    np.testing.assert_array_equal(position, np.tile([500, 500, 100], (5, 1)))
    np.testing.assert_array_equal(decoded_actual, actual)
    np.testing.assert_array_equal(decoded_proposals, proposals)
    command = p.encode_command(19, 2, 7, 248)
    assert len(command) == 16 and p.decode_command(command, 248) == (19, 2, 7)
    assert p.SEED == 29306000 and p.WORLDS == 64
    assert p.DEADLINE_SECONDS == pytest.approx(3.456)
    assert 63 * (sum(map(len, packets)) + len(command)) == 8568
    with pytest.raises(ValueError):
        p.encode_reports(own, actual, proposals, 252)
    with pytest.raises(ValueError):
        p.decode_reports(packets, 244)
    with pytest.raises(ValueError):
        p.decode_reports(packets[::-1], 248)
    with pytest.raises(ValueError):
        p.decode_reports((bytes([1]) + packets[0][1:], *packets[1:]), 248)
    with pytest.raises(ValueError):
        p.decode_command(command, 244)
    with pytest.raises(ValueError):
        p.decode_command(bytes([1]) + command[1:], 248)
    with pytest.raises(ValueError):
        p.decode_command(command[:-1] + b'\xff', 248)
    with pytest.raises(ValueError):
        p.encode_command(19, 1, 7, 248)


def test_four_actual_ticks_then_candidate_and_clipping():
    positions = np.tile([500, 500, 100], (5, 1))
    actual = np.tile([1, 0, 0], (5, 1))
    proposals = np.zeros((5, 3))
    member = 0
    forecast = p.forecast_positions(positions, actual, proposals, 0, member)
    assert forecast.shape == (27, 4, 5, 3)
    zero_q = p.command_index([0, 0, 0])
    move_q = p.command_index([1, 0, 0])
    np.testing.assert_array_equal(forecast[zero_q, :, 0, 0], [620] * 4)
    np.testing.assert_array_equal(forecast[move_q, :, 0, 0], [650, 680, 710, 740])
    np.testing.assert_array_equal(forecast[move_q, :, 1, 0], [620] * 4)
    clipped = p.forecast_positions(np.tile([990, 5, 149], (5, 1)),
                                   np.tile([1, -1, 1], (5, 1)),
                                   np.tile([1, -1, 1], (5, 1)), 248, 2)
    np.testing.assert_array_equal(clipped[move_q, :, 0],
                                  np.tile([1000, 0, 150], (4, 1)))


def test_both_sequential_orders_and_exact_ties():
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
    assert s.rank(1, 1, (1., 20.), q0) > s.rank(2, 1, (1., 20.), q0)
    assert s.rank(q0, 1, (1., 21.), q1) > s.rank(q1, 1, (1., 20.), q1)
    assert s.rank(q1, 1, (1. + 1e-14, 20.), q0) > s.rank(q0, 1, (1., 20.), q0)


def test_silent_move_and_reactivate_joint_only_pattern():
    q0 = p.command_index([0, 0, 0])
    q1 = p.command_index([1, 0, 0])
    matrix = np.zeros((27, 32, 3))
    matrix[:, 2, 0] = .5  # A silent member's motion has no radio effect.
    matrix[q0, 1, 0] = .4
    matrix[q1, 1, 0] = 1.0
    assert s.sequential_search(lambda q, m: matrix[q, m], 2, q0) == (q0, 2)
    assert max(((q, m) for q in range(27) for m in range(1, 32)),
               key=lambda pair: s.rank(*pair, matrix[pair], q0)) == (q1, 1)


def fake_radio(monkeypatch):
    monkeypatch.setattr(s, 'free_space_user_path_loss', lambda positions, sites: positions)
    monkeypatch.setattr(s, 'user_sinr_from_path_loss',
                        lambda loss, transmitter_mask: (loss, transmitter_mask))
    monkeypatch.setattr(s, 'greedy_connection_assignment', lambda sinr: None)
    monkeypatch.setattr(s, 'service_metrics',
                        lambda sinr, connections: {'J': 1., 'served': 10., 'quality': .5})


def test_complete_search_matrix_shadow_and_work(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    result = s.Scheduler('T', site_packet, lambda: 0.0,
                         lambda: 0.0).decide(own, actual, proposals, 0, 31)
    assert result['timely'] and result['selected_q'] == 0 and result['mask'] == 31
    assert result['selected_mask'] == 31
    assert result['sequential_pair'] == (0, 31)
    np.testing.assert_array_equal(result['sequential_score'], [1., 10., .5])
    assert result['scores'].shape == (27, 32, 3)
    assert len(result['evaluated_pairs']) == result['candidate_plans'] == 837
    assert result['candidate_requests'] == 837
    assert result['state_reductions'] == 3348
    assert result['geometry_snapshots'] == 108 and result['prefix_ticks'] == 4
    assert result['recurring_bytes'] == 136
    sequential = s.Scheduler('S', site_packet, lambda: 0.0,
                             lambda: 0.0).decide(own, actual, proposals, 0, 31)
    assert sequential['timely'] and sequential['candidate_requests'] == 116
    assert sequential['candidate_requests'] > sequential['candidate_plans']
    assert sequential['sequential_pair'] == (sequential['selected_q'], sequential['selected_mask'])
    np.testing.assert_array_equal(sequential['sequential_score'],
                                  sequential['scores'][sequential['sequential_pair']])
    assert sequential['geometry_snapshots'] <= 108
    assert sequential['state_reductions'] == 4 * sequential['candidate_plans']


def test_real_radio_score_uses_four_candidate_positions():
    own, actual, proposals, site_packet = inputs()
    result = s.Scheduler('S', site_packet, lambda: 0.0,
                         lambda: 0.0).decide(own, actual, proposals, 0, 31)
    q, mask = result['evaluated_pairs'][0]
    sites = p.decode_map(site_packet)
    values = []
    for positions in result['forecast'][q]:
        loss = free_space_user_path_loss(positions, sites)
        sinr = user_sinr_from_path_loss(loss, transmitter_mask=p.mask_array(mask))
        metrics = service_metrics(sinr, greedy_connection_assignment(sinr))
        values.append([metrics['J'], metrics['served'], metrics['quality']])
    np.testing.assert_allclose(result['scores'][q, mask], np.mean(values, axis=0), rtol=0, atol=1e-14)


def test_atomic_late_before_reports_and_after_decode(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    actual[0] = COMMANDS[1]
    proposals[0] = COMMANDS[2]
    late = s.Scheduler('S', site_packet, lambda: 4.0,
                       lambda: 0.0).decide(own, actual, proposals, 0, 7,
                                            started=0.0, cpu_started=0.0)
    assert not late['timely'] and late['reports'] == () and late['recurring_bytes'] == 0
    assert late['selected_q'] is None and late['selected_mask'] is None
    assert late['command_packet'] == b'' and late['mask'] == 7
    np.testing.assert_array_equal(late['commands'], actual)
    now = [0.0]
    real_decode = s.decode_command

    def decode_late(*args):
        result = real_decode(*args)
        now[0] = 4.0
        return result

    monkeypatch.setattr(s, 'decode_command', decode_late)
    late = s.Scheduler('S', site_packet, lambda: now[0],
                       lambda: 0.0).decide(own, actual, proposals, 0, 7)
    assert not late['timely'] and late['selected_q'] is None
    assert late['candidate_plans'] > 0 and late['state_reductions'] > 0
    assert late['reports'] and late['command_packet'] == b''
    assert late['recurring_bytes'] == 120 and late['mask'] == 7
    np.testing.assert_array_equal(late['commands'], actual)


def test_partial_reduction_miss_preserves_work_and_actual_team(monkeypatch):
    fake_radio(monkeypatch)
    own, actual, proposals, site_packet = inputs()
    actual[0] = COMMANDS[1]
    proposals[0] = COMMANDS[2]
    now = [0.0]

    def late_metric(sinr, connections):
        now[0] = 4.0
        return {'J': 1., 'served': 10., 'quality': .5}

    monkeypatch.setattr(s, 'service_metrics', late_metric)
    result = s.Scheduler('S', site_packet, lambda: now[0],
                         lambda: 0.0).decide(own, actual, proposals, 0, 3)
    assert not result['timely'] and result['candidate_plans'] == 0
    assert result['candidate_requests'] == 1 and result['state_reductions'] == 1
    assert result['geometry_snapshots'] == 4 and result['prefix_ticks'] == 4
    assert result['command_packet'] == b'' and result['mask'] == 3
    np.testing.assert_array_equal(result['commands'], actual)
