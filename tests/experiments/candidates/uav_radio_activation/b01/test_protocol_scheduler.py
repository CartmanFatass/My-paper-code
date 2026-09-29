import numpy as np
import pytest

from experiments.candidates.uav_radio_activation.b01 import protocol as p
from experiments.candidates.uav_radio_activation.b01 import scheduler as s


def inputs():
    rng = np.random.RandomState(711)
    xyz = rng.uniform((0, 0, 50), (1000, 1000, 150), (5, 3))
    own = ((xyz - (0, 0, 50)) / (1000, 1000, 100)).astype(np.float32)
    commands = rng.randint(-1, 2, (5, 3)).astype(np.float32)
    sites = rng.uniform(0, 1000, (50, 2))
    return own, commands, p.encode_map(sites)


def test_codec_lengths_colliding_sites_and_rounding():
    own, commands, site_packet = inputs()
    sites = np.zeros((50, 2))
    sites[:2] = [[10.2, 20.1], [10.3, 20.4]]
    encoded = p.encode_map(sites)
    decoded = p.decode_map(encoded)
    assert len(encoded) == 400 and decoded.shape == (50, 2)
    np.testing.assert_array_equal(decoded[0], decoded[1])
    packets = p.encode_reports(own, commands, 252)
    positions, actual = p.decode_reports(packets, 252)
    expected = own.astype(float) * (1000, 1000, 100) + (0, 0, 50)
    assert max(map(len, packets)) == 24
    assert np.max(np.abs(positions - expected)) <= .5
    np.testing.assert_array_equal(actual, commands)
    command = p.encode_command(19, 252)
    assert len(command) == 16 and p.decode_command(command, 252) == 19
    assert 64 * (sum(map(len, packets)) + len(command)) == 8704
    assert p.DEADLINE_SECONDS == pytest.approx(.456)
    with pytest.raises(ValueError):
        p.decode_reports(packets, 248)
    with pytest.raises(ValueError):
        p.decode_reports(packets[::-1], 252)
    with pytest.raises(ValueError):
        p.encode_reports(np.zeros((5, 104)), commands, 0)
    with pytest.raises(ValueError):
        p.decode_command(command, 248)


def test_post_movement_offsets_and_final_truncation():
    xyz = np.tile([500, 500, 100], (5, 1))
    velocity = np.tile([1, 0, 0], (5, 1))
    path, offsets = p.forecast_positions(xyz, velocity, 0)
    assert offsets == (2, 3, 4, 5)
    np.testing.assert_array_equal(path[:, 0, 0], [560, 590, 620, 650])
    final, offsets = p.forecast_positions(xyz, velocity, 252)
    assert offsets == (2, 3, 4)
    np.testing.assert_array_equal(final[:, 0, 0], [560, 590, 620])
    clipped, _ = p.forecast_positions(np.tile([990, 5, 149], (5, 1)),
                                      np.tile([1, -1, 1], (5, 1)), 0)
    np.testing.assert_array_equal(clipped, np.tile([1000, 0, 150], (4, 5, 1)))


def test_search_matches_full_score_and_greedy_path():
    own, commands, packet = inputs()
    # A frozen clock makes this a correctness check, not a scheduler timing pilot.
    exact = s.Scheduler('E', packet, clock=lambda: 0.0).decide(own, commands, 0, 31)
    greedy = s.Scheduler('G', packet, clock=lambda: 0.0).decide(own, commands, 0, 31)
    assert exact['candidate_plans'] == 31 and exact['state_reductions'] == 124
    assert exact['geometry_snapshots'] == 4
    assert exact['mask'] == max(range(1, 32), key=lambda m: s.rank(m, exact['scores'][m]))
    current = 31
    sequence = [31]
    while current.bit_count() > 1:
        removals = sorted(current ^ (1 << i) for i in range(5) if current & (1 << i))
        sequence.extend(removals)
        best = max(removals, key=lambda m: s.rank(m, exact['scores'][m]))
        if s.rank(best, exact['scores'][best]) <= s.rank(current, exact['scores'][current]):
            break
        current = best
    assert greedy['mask'] == current
    assert greedy['evaluated_masks'] == sequence
    assert greedy['candidate_plans'] <= 15
    assert s.rank(31, (0., 0.)) > s.rank(30, (0., 0.))
    assert s.rank(1, (0., 0.)) > s.rank(2, (0., 0.))
    final = s.Scheduler('E', packet, clock=lambda: 0.0).decide(own, commands, 252, 31)
    assert final['state_reductions'] == 93 and final['geometry_snapshots'] == 3


def test_deadline_discards_partial_search_and_late_command(monkeypatch):
    own, commands, packet = inputs()
    now = [0.0]
    actual_metric = s.service_metrics

    def overdue_metric(*args, **kwargs):
        value = actual_metric(*args, **kwargs)
        now[0] = 1.0
        return value

    monkeypatch.setattr(s, 'service_metrics', overdue_metric)
    result = s.Scheduler('E', packet, clock=lambda: now[0]).decide(own, commands, 0, 7)
    assert not result['timely'] and result['mask'] == 7 and result['selected_mask'] is None
    assert result['candidate_plans'] == 0 and result['state_reductions'] == 1
    assert result['command_packet'] == b'' and result['recurring_bytes'] == 120
    monkeypatch.setattr(s, 'service_metrics', actual_metric)
    actual_decode = s.decode_command

    def late_decode(*args):
        value = actual_decode(*args)
        now[0] = 1.0
        return value

    now[0] = 0.0
    monkeypatch.setattr(s, 'decode_command', late_decode)
    result = s.Scheduler('E', packet, clock=lambda: now[0]).decide(own, commands, 0, 7)
    assert result['candidate_plans'] == 31
    assert not result['timely'] and result['mask'] == 7 and result['command_packet'] == b''
