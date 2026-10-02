import copy
import hashlib

import numpy as np
import pytest
import torch

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss, greedy_connection_assignment, service_metrics
from experiments.candidates.uav_message_content.b07.collect import collect_episode
from experiments.candidates.uav_message_content.b07.contract import artifact
from experiments.candidates.uav_message_content.b07.reader import individual_service, independent_source, read_episode
from experiments.candidates.uav_message_content.b07.receiver import Receiver, BaseActor
from experiments.candidates.uav_message_content.b07.transport import ByteCodec
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import payloads


class SyntheticWorld:
    """Explicit synthetic geometry/service fixture, never MultiUAVEnv or make_real."""
    def __init__(self):
        self.env = self

    def state(self):
        return np.r_[self.uav_positions.ravel(), self.user_positions.ravel(), self.t / 256].astype(np.float32)

    def obs(self):
        raw = np.zeros((5, 104), dtype=np.float32)
        raw[:, :2] = self.uav_positions[:, :2] / 1000
        raw[:, 2] = (self.uav_positions[:, 2] - 50) / 100
        raw[:, -1] = self.t / 256
        sinr = user_sinr_from_path_loss(free_space_user_path_loss(self.uav_positions, self.user_positions))
        for sender in range(5):
            ids = np.flatnonzero(sinr[sender] >= 3)
            ids = ids[np.argsort(-sinr[sender, ids], kind="stable")][:20]
            block = raw[sender, 3:63].reshape(20, 3)
            block[:len(ids), :2] = (self.user_positions[ids] - self.uav_positions[sender, :2]) / 1000
            block[:len(ids), 2] = np.clip((sinr[sender, ids] + 10) / 50, 0, 1)
        return raw

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.uav_positions = np.column_stack((rng.uniform(0, 1000, (5, 2)), rng.uniform(50, 150, 5)))
        self.user_positions = rng.uniform(0, 1000, (50, 2))
        self.t = 0
        return self.obs(), {"state": self.state()}

    def step(self, action):
        self.uav_positions += action * np.float32(30)
        self.uav_positions[:, :2] = self.uav_positions[:, :2].clip(0, 1000)
        self.uav_positions[:, 2] = self.uav_positions[:, 2].clip(50, 150)
        self.t += 1
        sinr = user_sinr_from_path_loss(free_space_user_path_loss(self.uav_positions, self.user_positions))
        connections = greedy_connection_assignment(sinr)
        outcome = service_metrics(sinr, connections)
        names = [f"uav_{i}" for i in range(5)]
        info = dict(next_state=self.state(), rewards_dict={n: outcome["J"] / 5 for n in names},
                    infos_dict={n: {"global": {"served_users": outcome["served"], "connections": connections,
                                              "sinr_matrix": sinr}} for n in names})
        return self.obs(), 0., self.t == 256, False, info


@pytest.mark.parametrize("kind,compressed", [("D", False), ("B", False), ("D", True)])
def test_complete_synthetic_native_reader(tmp_path, kind, compressed):
    with torch.random.fork_rng():
        torch.manual_seed(17)
        actor = (Receiver() if kind == "D" else BaseActor()).requires_grad_(False)
    book = torch.rand(256, 6, generator=torch.Generator().manual_seed(18)) if compressed else None
    scales = torch.ones(6) if compressed else None
    collector_counts, reader_counts = {}, {}
    row = collect_episode(SyntheticWorld(), actor, kind, ByteCodec(book, scales, collector_counts), 0,
                          tmp_path / "trace.npz", collector_counts)
    reading = read_episode(row, actor, kind, book, scales, reader_counts)
    assert collector_counts["native_steps"] == collector_counts["native_step_calls"] == 256
    assert collector_counts["native_actor_rows"] == collector_counts["motion_vectors"] == 1280
    assert reader_counts["reader_actor_rows"] == 1280 and reader_counts["reader_physical_states"] == 256
    assert row["delivered"] + row["censored"] == 256
    assert reading["packet_bytes"] == 256 * (3 if compressed else 26)
    assert len(reading["individual_service"]["served_ticks"]) == 50
    if compressed:
        assert collector_counts["nearest_center_comparisons"] == reader_counts["nearest_center_comparisons"] == 65536
    # Rehashed corruption must still fail the independent private/history binding.
    with np.load(row["raw"]["path"]) as archive:
        corrupted = {key: archive[key].copy() for key in archive.files}
    corrupted["actor_input"][0, 0, 121] = 1.
    np.savez_compressed(tmp_path / "corrupted.npz", **corrupted)
    bad_row = copy.deepcopy(row)
    bad_row["raw"] = artifact(tmp_path / "corrupted.npz")
    with pytest.raises(AssertionError):
        read_episode(bad_row, actor, kind, book, scales, {})


def test_censored_individual_gap_age_conventions():
    bits = np.array([[0, 1, 0], [0, 1, 1], [0, 1, 0], [0, 1, 0]], dtype=np.uint8)
    result = individual_service(bits)
    assert result["served_ticks"] == [0, 4, 1]
    assert result["longest_gap"] == [4, 0, 2]
    assert result["mean_waiting_age"] == [2.5, 0., 1.]
    assert result["never_served"] == 1
    assert result["longest_gap_cases"] == [dict(user=0, start=0, end_exclusive=4, gap=4,
                                               prefix_censored=True, suffix_censored=True)]


def test_independent_centroid_matches_mixed_dtype_sender_exactly():
    raw = SyntheticWorld()
    observations, _ = raw.reset(1981002000)
    for t in range(11):
        for sender in range(5):
            np.testing.assert_array_equal(independent_source(observations[sender]),
                                          payloads(observations)[sender, [0, 1, 2, 3, 4, 6]])
        observations = raw.step(np.full((5, 3), .123, dtype=np.float32))[0]


def test_native_failure_partial_trace_and_effect_frontier(tmp_path):
    class Fails(SyntheticWorld):
        def step(self, action):
            if self.t == 1:
                raise RuntimeError("synthetic failure")
            return super().step(action)
    actor = BaseActor().requires_grad_(False)
    counts = {}
    with pytest.raises(RuntimeError, match="synthetic failure"):
        collect_episode(Fails(), actor, "B", ByteCodec(counts=counts), 0, tmp_path / "trace.npz", counts)
    assert counts["native_step_calls"] == 2 and counts["native_steps"] == 1
    assert not (tmp_path / "trace.npz").exists()
    with np.load(tmp_path / "trace.partial.npz") as partial:
        assert partial["action"].shape == (1, 5, 3)
