from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_process import (
    ACTOR_CONTINUOUS_ZERO_BASED,
    ACTOR_UPDATE_ORDER,
    CRITIC_CONTINUOUS_ZERO_BASED,
    PathwiseReplayError,
    SourceSpecificMaskedWelford,
    replay_one_tick_from_ledger,
    run_two_owner_one_tick_pathwise_oracle,
)


def test_source_specific_masked_welford_uses_per_dimension_presence_and_roundtrips() -> None:
    state = SourceSpecificMaskedWelford.empty()
    actor = np.empty((1, 1, 4, 54), dtype=np.float64)
    for copy_index in range(4):
        actor[0, 0, copy_index] = 0.1 * (copy_index + 1)
    actor[0, 0, :, 11] = [1, 0, 1, 0]  # camera-present
    actor[0, 0, :, 25] = [1, 0, 0, 1]  # SOURCE-present
    actor[0, 0, :, 27] = [1, 0, 1, 0]  # delivered partner STATE-present
    actor[0, 0, :, 49] = [0, 1, 1, 0]  # accepted SNAPSHOT-present
    actor[0, 0, :, 51] = [1, 0, 0, 1]  # delivered READINESS-present

    before_actor = state.normalize_actor(actor)
    assert ACTOR_UPDATE_ORDER == ("lane", "tick", "physical_uav", "copy_I_then_S")
    assert before_actor[0, 0, :, 11].tolist() == [1.0, 0.0, 1.0, 0.0]
    assert before_actor[0, 0, :, 12].tolist() == [pytest_approx(0.1), 0.0, pytest_approx(0.3), 0.0]
    assert before_actor[0, 0, :, 26].tolist() == [pytest_approx(0.1), 0.0, 0.0, pytest_approx(0.4)]
    state.update_actor(actor)

    expected_actor_counts = np.zeros(54, dtype=np.int64)
    expected_actor_counts[list(ACTOR_CONTINUOUS_ZERO_BASED)] = 4
    for gated in ((12, 13), (26,), tuple(range(28, 36)), (50,), (52,)):
        expected_actor_counts[list(gated)] = 2
    assert np.array_equal(state.actor.count, expected_actor_counts)
    assert float(state.actor.mean[4]).hex() == "0x1.0000000000001p-2"
    assert state.actor.mean[12] == 0.2
    assert state.actor.mean[26] == 0.25
    assert state.actor.mean[28] == 0.2
    assert state.actor.mean[50] == 0.25
    assert state.actor.mean[52] == 0.25

    snapshot = np.stack((
        np.full(18, 0.1), np.full(18, 0.2), np.full(18, 0.3),
    ))
    accepted = np.asarray([True, False, True])
    before_snapshot = state.normalize_snapshot(snapshot, accepted)
    assert np.allclose(before_snapshot[0], 0.1 / np.sqrt(1.0 + 1e-8))
    assert np.array_equal(before_snapshot[1], np.zeros(18))
    assert np.allclose(before_snapshot[2], 0.3 / np.sqrt(1.0 + 1e-8))
    state.update_snapshot(snapshot, accepted)
    assert np.array_equal(state.snapshot.count, np.full(18, 2, dtype=np.int64))
    assert np.array_equal(state.snapshot.mean, np.full(18, 0.2))

    critic = np.stack((np.full(58, 0.1), np.full(58, 0.3))).reshape(1, 2, 58)
    critic[0, :, 11] = [1, 0]  # UAV0 camera-present
    critic[0, :, 29] = [0, 1]  # UAV1 camera-present
    critic[0, :, 18] = [1, 0]  # UAV0 SOURCE-present
    critic[0, :, 36] = [0, 1]  # UAV1 SOURCE-present
    critic[0, :, 40] = [1, 0]  # base-buffer present
    before_critic = state.normalize_critic(critic)
    assert before_critic[0, 1, 12] == 0.0
    assert before_critic[0, 0, 30] == 0.0
    assert before_critic[0, 1, 41] == 0.0
    state.update_critic(critic)
    expected_critic_counts = np.zeros(58, dtype=np.int64)
    expected_critic_counts[list(CRITIC_CONTINUOUS_ZERO_BASED)] = 2
    for gated in ((12, 13), (19, 20), (30, 31), (37, 38), tuple(range(41, 45))):
        expected_critic_counts[list(gated)] = 1
    assert np.array_equal(state.critic.count, expected_critic_counts)

    restored = SourceSpecificMaskedWelford.from_state_dict(state.state_dict())
    assert np.array_equal(restored.actor.count, state.actor.count)
    assert np.array_equal(restored.actor.mean, state.actor.mean)
    assert np.array_equal(restored.actor.m2, state.actor.m2)
    assert np.array_equal(restored.snapshot.count, state.snapshot.count)
    assert np.array_equal(restored.critic.count, state.critic.count)
    assert np.array_equal(restored.normalize_actor(actor), state.normalize_actor(actor))
    assert np.array_equal(restored.normalize_critic(critic), state.normalize_critic(critic))


def pytest_approx(value: float) -> float:
    """Literal helper keeps expected values independent of the normalizer state."""

    return value / np.sqrt(1.0 + 1e-8)


def test_source_specific_welford_rejects_non_boolean_presence_flags() -> None:
    state = SourceSpecificMaskedWelford.empty()
    actor = np.zeros((1, 1, 4, 54), dtype=np.float64)
    actor[0, 0, 0, 11] = 0.5
    with pytest.raises(ValueError, match=r"presence.*\{0,1\}"):
        state.normalize_actor(actor)

    critic = np.zeros((1, 1, 58), dtype=np.float64)
    critic[0, 0, 40] = -1.0
    with pytest.raises(ValueError, match=r"presence.*\{0,1\}"):
        state.update_critic(critic)


def test_source_specific_welford_uses_exact_serial_collection_order() -> None:
    state = SourceSpecificMaskedWelford.empty()
    actor = np.zeros((1, 2, 4, 54), dtype=np.float64)
    actor[..., 4] = np.asarray(
        [1e16, 1.0, -1e16, 3.0, 7.0, -5.0, 1e-12, -1e-12],
        dtype=np.float64,
    ).reshape(1, 2, 4)

    state.update_actor(actor)

    assert state.actor.count[4] == 8
    assert float(state.actor.mean[4]).hex() == "0x1.4000000000000p-1"
    assert float(state.actor.m2[4]).hex() == "0x1.3b8b5b5056e16p+107"
    # A batch-mean/dot merge yields 0x1.8p-1 and ...e17; it is not the
    # registered lane/tick/physical/copy serial recurrence.
    assert float(state.actor.mean[4]).hex() != "0x1.8000000000000p-1"


def test_two_owner_live_replay_native_pathwise_oracle_is_fieldwise_and_result_blind() -> None:
    oracle = run_two_owner_one_tick_pathwise_oracle()

    assert oracle.schema == "DISH_PSF_R01_TWO_OWNER_ONE_TICK_ORACLE_V1"
    assert oracle.question_relevant_output is False
    assert oracle.initial_owner.tolist() == [0, 1]
    assert oracle.owner_history.tolist() == [[0, 1], [0, 1]]
    assert oracle.pre_application_promotion_count == 0
    assert oracle.snapshot_recipient.tolist() == [1, 0]
    assert oracle.phase_trace == (
        "BEGIN_TICK_ARRIVALS",
        "SNAPSHOT_ASSIMILATION",
        "IMMUTABLE_POST_ARRIVAL_PRE_CAS_CUT",
        "BRANCH_TRANSACTION",
        "BRANCH_OBSERVATION",
        "SINGLE_POLICY_FORWARD",
    )

    assert oracle.native_actor.shape == oracle.causal_oracle_actor.shape == (3, 2, 4, 54)
    assert oracle.native_critic.shape == oracle.causal_oracle_critic.shape == (3, 2, 58)
    assert np.array_equal(oracle.native_actor, oracle.causal_oracle_actor)
    assert np.array_equal(oracle.native_critic, oracle.causal_oracle_critic)
    assert oracle.actor_fields_compared == 3 * 2 * 4 * 54
    assert oracle.critic_fields_compared == 3 * 2 * 58
    assert oracle.delivered_partner_state_used is True
    assert oracle.absent_partner_state_zeroed is True
    assert oracle.distinct_d_g1_g5_preserved is True
    assert oracle.causal_oracle_critic[0, 0, 42] == 5.0  # nonzero base position error
    assert oracle.causal_oracle_critic[0, 1, 42] == 1e6  # absent base sentinel
    expected_header_version_match = np.asarray(
        (
            ((1, 1, 0, 0), (0, 0, 1, 1)),
            ((0, 0, 0, 1), (0, 0, 0, 0)),
            ((0, 0, 0, 1), (0, 0, 0, 0)),
        ),
        dtype=np.float64,
    )
    assert np.array_equal(oracle.native_actor[..., 53], expected_header_version_match)
    assert np.array_equal(oracle.causal_oracle_actor[..., 53], expected_header_version_match)

    assert oracle.role_indices == (
        {"owner": 0, "owner_motion": 0, "standby_motion": 3, "prepare": 0, "commit": 3},
        {"owner": 1, "owner_motion": 2, "standby_motion": 1, "prepare": 2, "commit": 1},
    )
    assert np.array_equal(oracle.live_hidden, oracle.replay_hidden)
    assert np.array_equal(oracle.live_logits, oracle.replay_logits)
    assert np.array_equal(oracle.old_log_probability, oracle.replay_log_probability)
    assert np.array_equal(oracle.behavior_policy_ratio, np.ones(2, dtype=np.float64))
    assert np.array_equal(oracle.live_normalized_actor, oracle.replay_normalized_actor)
    assert oracle.masked_welford_applied is True
    assert oracle.actor_welford_post_equal is True
    assert oracle.welford_pre_state_immutable is True
    assert oracle.current_tstar_excluded_from_welford_pre_state is True
    assert np.any(oracle.replay_ledger.source_specific_welford_state["actor"]["count"] > 0)
    assert oracle.replay_owner_history_consumed is True
    assert oracle.forward_count_before.tolist() == [0, 0]
    assert oracle.forward_count_after.tolist() == [1, 1]
    assert oracle.tstar_observation_consumption_count.tolist() == [1, 1]
    assert oracle.snapshot_assimilation_before_cas is True
    assert oracle.branch_observation_before_forward is True


def test_pathwise_replay_rejects_owner_history_drift_and_detects_fragment_tamper() -> None:
    oracle = run_two_owner_one_tick_pathwise_oracle()
    owner_history = oracle.replay_ledger.owner_history.copy()
    owner_history[1, 0] = 1
    with pytest.raises(PathwiseReplayError, match="owner history"):
        replay_one_tick_from_ledger(replace(oracle.replay_ledger, owner_history=owner_history))

    fragment = oracle.replay_ledger.fragment_initial_hidden.copy()
    fragment[0, 0, 0] += 0.125
    tampered = replay_one_tick_from_ledger(
        replace(oracle.replay_ledger, fragment_initial_hidden=fragment)
    )
    assert not np.array_equal(tampered.hidden, oracle.live_hidden)
    assert not np.array_equal(tampered.log_probability, oracle.old_log_probability)
