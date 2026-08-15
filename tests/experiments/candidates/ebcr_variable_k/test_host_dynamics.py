from __future__ import annotations

import numpy as np

from experiments.candidates.ebcr_variable_k.host import (
    ExogenousEpisode, balance_report, generate_episode, run_episode,
)
from experiments.candidates.ebcr_variable_k.config import CONCLUSION_CELLS


class ConstantActor:
    def __init__(self, probability: float) -> None:
        self.probability = probability
        self.calls = 0

    def probabilities(self, features: np.ndarray) -> np.ndarray:
        self.calls += int(features.shape[0])
        return np.full(features.shape[0], self.probability, dtype=np.float64)


def _boundary_episode() -> ExogenousEpisode:
    latent = np.asarray([[0, 0]] * 4 + [[1, 1]] * 2, dtype=np.int8)
    observations = latent.copy()
    observations[2:4] = 1
    boundary = np.asarray([0, 0, 0, 0, 1, 0], dtype=np.int8)
    changed = np.zeros((6, 2), dtype=np.int8)
    changed[4] = 1
    return ExogenousEpisode(
        seed=1, episode=0, namespace="manual", cell="ORDER_ON",
        joint_mismatch=True, durations=(4,), noise=0.0, latent=latent,
        observations=observations, readiness=np.ones((6, 2), dtype=np.int8),
        boundary=boundary, changed=changed,
        preroll=np.zeros((3, 2), dtype=np.int8),
    )


def test_within_tick_change_observation_renewal_instantiation_then_packet_order():
    row = run_episode(_boundary_episode(), arm="FIXED-4", actor=ConstantActor(0.5))
    assert row.renewal_times == ((4,), (4,))
    assert row.boundary_delays == (0, 0)
    # Ticks 0..3 succeed, renewal tick 4 cannot, and the skill instantiated
    # from the current three-observation window succeeds on tick 5.
    assert row.packet_successes == 5
    assert row.simultaneous_renewal_ticks == 1


def test_current_readiness_can_execute_request_and_pending_expires_after_two_ticks():
    exogenous = generate_episode(
        seed=17, episode=3, namespace="pending", cell="ID_OFF",
        durations=(128,), noise=0.0, joint_mismatch=False, horizon=12,
    )
    unready = ExogenousEpisode(**{
        **exogenous.__dict__, "readiness": np.zeros((12, 2), dtype=np.int8)
    })
    row = run_episode(unready, arm="LOCAL", actor=ConstantActor(1.0))
    assert row.ordinary_times[0][0] == 6
    assert row.ordinary_times[1][0] == 6
    assert row.pending_delays[:2] == (2, 2)
    assert row.unsafe_normal_renewal_cost == 0.20


def test_counter_keyed_generation_is_replayable_and_action_independent():
    kwargs = dict(
        seed=31, episode=9, namespace="paired", cell="SHORT_OFF",
        durations=(6, 8, 10), noise=0.10, joint_mismatch=False, horizon=128,
    )
    first = generate_episode(**kwargs)
    second = generate_episode(**kwargs)
    for name in ("latent", "observations", "readiness", "boundary", "changed", "preroll"):
        assert np.array_equal(getattr(first, name), getattr(second, name))
    fixed = run_episode(first, arm="FIXED-8", actor=ConstantActor(0.5))
    local = run_episode(first, arm="LOCAL", actor=ConstantActor(0.5))
    assert fixed.physics_ticks == local.physics_ticks == 128
    assert fixed.transmitted_bits == local.transmitted_bits == 512


def test_registered_conclusion_cells_have_deterministic_balance_certificates():
    for tempo, (durations, noise) in CONCLUSION_CELLS.items():
        for joint in (False, True):
            episodes = [
                generate_episode(
                    seed=17, episode=index, namespace="balance", cell=tempo,
                    durations=durations, noise=noise, joint_mismatch=joint,
                ) for index in range(64)
            ]
            report = balance_report(episodes)
            assert report["balanced"], (tempo, joint, report)
            assert set(report["initial_latent_pair_counts"].values()) == {16}
            assert set(report["readiness_namespace_slot_counts"].values()) == {16}
            assert set(report["noise_namespace_slot_counts"].values()) == {16}
            assert abs(report["actual_changed_agent_counts"][0] - report["actual_changed_agent_counts"][1]) <= 1
