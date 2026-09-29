import hashlib

import numpy as np
import pytest

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel
from experiments.candidates.uav_message_content.read_b02 import (
    behavior_from_observations, packet_from_observations, read_trace,
)


def test_boundary_distance_does_not_round_threshold_to_float32():
    observations = np.full((1, 6, 171), .5, dtype=np.float32)
    coordinates = [1 - 2**-23, 1 - 2**-24, 0, 2e-7, np.float32(1e-7),
                   np.nextafter(np.float32(1e-7), np.float32(np.inf))]
    observations[0, :, 0] = coordinates
    observations[0, :, 2] = coordinates
    result = behavior_from_observations(observations)
    assert result["boundary_fraction"] == .5
    assert result["height_floor_fraction"] == 2 / 6
    assert result["height_ceiling_fraction"] == 1 / 6


def test_independent_packet_reconstruction_preserves_current_fields_and_history_spread():
    observations = np.zeros((7, 5, 171), dtype=np.float32)
    observations[:, 0, :3] = (.5, .5, .3)
    observations[0, 0, 3:9] = (-.2, 0, .4, .2, 0, .4)
    observations[1, 0, 3:9] = (-.4, 0, .4, .4, 0, .4)
    current = packet_from_observations(observations, 1, 0, "B")
    ordinary = packet_from_observations(observations, 1, 0, "O")
    np.testing.assert_allclose(current, [.5, .5, .3, .5, .5, 0, .1])
    np.testing.assert_array_equal(ordinary[[0, 1, 2, 3, 4, 6]], current[[0, 1, 2, 3, 4, 6]])
    assert ordinary[5] == pytest.approx(np.sqrt(.2))
    # Current count/centroid become empty even while private history still has spread.
    after_empty = packet_from_observations(observations, 2, 0, "O")
    np.testing.assert_array_equal(after_empty[[3, 4, 6]], [0, 0, 0])
    assert after_empty[5] > 0
    expired = packet_from_observations(observations, 6, 0, "O")
    np.testing.assert_array_equal(expired[3:], [0, 0, 0, 0])


@pytest.mark.parametrize("arm", ["B", "O", "L"])
def test_complete_trace_reader_and_corrupted_preserved_field(tmp_path, arm):
    # A protocol fixture, with explicit synthetic outcomes and no simulator or policy.
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = .5
    raw[:, 3:9] = (-.2, 0, .4, .2, 0, .4)
    scalar = {"B": 0., "O": np.sqrt(.08), "L": .7}[arm]
    pre_content = np.array([np.arctanh(2 * scalar - 1) if arm == "L" else 0], dtype=np.float32)
    packet = np.array([.5, .5, .5, .5, .5, scalar, .1], dtype=np.float32)
    channel = Channel(771)
    trace = {name: [] for name in (
        "actor_input", "critic_input", "packet", "pre_tanh_content", "due", "good",
        "sender", "deliveries", "content_credit_mask", "records", "pending_after_send",
        "action", "pre_tanh_motion", "reward_physical", "reward_net", "served_users",
        "Q", "scalar_response_rms", "scalar_response_max")}
    for t in range(256):
        before = channel.delivered
        channel.begin_tick()
        extras = channel.features()
        actor_input = np.concatenate((raw, np.zeros((5, 4), dtype=np.float32), extras), axis=1)
        critic_input = np.r_[np.zeros(136, dtype=np.float32), extras.ravel()]
        good = int(channel.good)
        sender = t % 5
        assert not channel.pending[sender]
        due = t + (1 if good else 5)
        channel.inflight.append((sender, t, due, packet.copy()))
        channel.pending[sender] = True
        values = (actor_input, critic_input, packet.copy(), pre_content.copy(), due, good,
                  t % 5, channel.delivered - before, arm == "L" and due < 256,
                  channel.records.copy(), channel.pending.copy(),
                  np.zeros((5, 3), dtype=np.float32), np.zeros((5, 3), dtype=np.float32),
                  .13, .129, 5, .2, 0., 0.)
        for key, value in zip(trace, values):
            trace[key].append(value)
        channel.advance()
    arrays = {key: np.asarray(value) for key, value in trace.items()}
    path = tmp_path / "fixture.npz"
    np.savez_compressed(path, **arrays)
    row = dict(raw=str(path), raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               phase="initial_eval", J_net=.129, J_physical=.13,
               served_users_per_tick=5, Q=.2, charge_per_tick=.001,
               delivered_packets=channel.delivered, pending_at_end=int(channel.pending.sum()),
               channel_sequence_sha256=hashlib.sha256(bytes(arrays["good"].tolist())).hexdigest(),
               action_sequence_sha256=hashlib.sha256(arrays["action"].tobytes()).hexdigest(),
               scalar_response_rms=0., scalar_response_max=0., boundary_fraction=0.,
               height_floor_fraction=0., height_ceiling_fraction=0., mean_height_m=100.)
    checked = read_trace(row, arm)
    assert checked["delivered"] + checked["censored"] == 256
    assert checked["content_credit_rows"] == (channel.delivered if arm == "L" else 0)
    arrays["packet"][-1, 6] += .05
    np.savez_compressed(path, **arrays)
    row["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(AssertionError):
        read_trace(row, arm)
