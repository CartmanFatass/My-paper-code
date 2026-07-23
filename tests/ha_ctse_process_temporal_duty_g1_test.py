from __future__ import annotations

from copy import deepcopy

import pytest

from ha_ctse_process.temporal_duty_g1 import (
    G1Observation,
    TemporalDutyG1Env,
    make_episode_spec,
)


def _time(environment: TemporalDutyG1Env) -> int:
    return int(environment.snapshot_state()["time"])


def _correct_actions(environment: TemporalDutyG1Env) -> dict[int, int]:
    state = environment.snapshot_state()
    return {
        int(slot): int(lifecycle["g"])
        for slot, lifecycle in state["lifecycles"].items()
        if lifecycle["active"]
    }


def _zero_actions(environment: TemporalDutyG1Env) -> dict[int, int]:
    return {slot: 0 for slot in environment.observe()}


def _advance_to(environment: TemporalDutyG1Env, target: int) -> None:
    while _time(environment) < target:
        environment.step(_correct_actions(environment))


def test_two_step_cue_and_actor_observation_hides_lifecycle_state() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 6, -1, 0))

    first = environment.observe()
    assert set(first) == {0, 1}
    assert all(isinstance(observation, G1Observation) for observation in first.values())
    assert all(len(observation.actor) == 6 for observation in first.values())
    assert first[0].actor == (-1.0, 1.0, 1.0, 0.0, 0.0, 0.5)
    assert not hasattr(first[0], "g")
    assert not hasattr(first[0], "age")
    assert not hasattr(first[0], "remaining")
    assert not hasattr(first[0], "correct_count")
    assert not hasattr(first[0], "terminal_streak")

    environment.step(_correct_actions(environment))
    assert environment.observe()[0].actor[:3] == (-1.0, 1.0, 0.0)
    environment.step(_correct_actions(environment))
    assert environment.observe()[0].actor[:3] == (0.0, 0.0, 0.0)


def test_split_support_and_exact_logical_to_physical_schedule_mapping() -> None:
    fitting = make_episode_spec("fitting", 3, 14, 1, 1)
    assert fitting.logical_to_physical == (1, 2, 0)
    assert fitting.membership_events == (
        (12, "TEMP_LEAVE", 2),
        (16, "REJOIN", 2),
        (28, "JOIN", 3),
        (68, "TERMINAL_LEAVE", 1),
    )

    heldout = make_episode_spec("heldout", 3, 18, -1, 1)
    assert heldout.logical_to_physical == (2, 0, 1)
    assert heldout.membership_events == (
        (13, "TEMP_LEAVE", 0),
        (17, "REJOIN", 0),
        (29, "JOIN", 3),
        (69, "TERMINAL_LEAVE", 2),
    )

    for duration in (6, 14):
        assert make_episode_spec("fitting", 2, duration, 1, 0).duration == duration
    for duration in (10, 18):
        assert make_episode_spec("heldout", 2, duration, 1, 0).duration == duration
    with pytest.raises(ValueError, match="duration"):
        make_episode_spec("fitting", 2, 10, 1, 0)
    with pytest.raises(ValueError, match="duration"):
        make_episode_spec("heldout", 2, 14, 1, 0)


def test_heldout_timing_and_permutation_change_membership_not_denominators() -> None:
    fitting = make_episode_spec("fitting", 2, 6, 1, 0)
    heldout = make_episode_spec("heldout", 2, 10, 1, 0)
    assert fitting.logical_to_physical == (0, 1)
    assert heldout.logical_to_physical == (1, 0)
    assert tuple(event[0] for event in fitting.membership_events) == (12, 16, 28, 68)
    assert tuple(event[0] for event in heldout.membership_events) == (13, 17, 29, 69)
    assert fitting.action_denominator == heldout.action_denominator == 196


def test_temp_leave_freezes_and_rejoin_restores_the_same_lifecycle() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 3, 14, 1, 0))
    temp_target = environment.snapshot_state()["spec"]["temp_target"]
    _advance_to(environment, 12)
    left = environment.snapshot_state()["lifecycles"][temp_target]
    assert not left["active"]
    frozen = tuple(
        left[field]
        for field in ("g", "age", "remaining", "correct_count", "terminal_streak", "opportunities")
    )
    assert temp_target not in environment.observe()

    _advance_to(environment, 16)
    restored = environment.snapshot_state()["lifecycles"][temp_target]
    assert restored["active"]
    assert tuple(
        restored[field]
        for field in ("g", "age", "remaining", "correct_count", "terminal_streak", "opportunities")
    ) == frozen
    assert environment.observe()[temp_target].actor[4] == 1.0


def test_join_creates_a_fresh_lifecycle_and_resets_actor_state() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 14, -1, 1))
    _advance_to(environment, 28)
    joined = environment.snapshot_state()["lifecycles"][2]
    assert {
        key: joined[key]
        for key in ("g", "age", "remaining", "correct_count", "terminal_streak", "opportunities")
    } == {
        "g": -1,
        "age": 0,
        "remaining": 14,
        "correct_count": 0,
        "terminal_streak": 0,
        "opportunities": 0,
    }
    assert environment.observe()[2].actor == (-1.0, 1.0, 1.0, 1.0, 0.0, 0.75)


def test_terminal_leave_censors_without_completion_credit() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 14, 1, 0))
    terminal_target = environment.snapshot_state()["spec"]["terminal_target"]
    _advance_to(environment, 67)
    successes_before = environment.snapshot_state()["successful_segments"]
    environment.step(_correct_actions(environment))
    state = environment.snapshot_state()
    assert state["time"] == 68
    assert state["lifecycles"][terminal_target]["terminal"]
    assert not state["lifecycles"][terminal_target]["active"]
    assert state["successful_segments"] == successes_before
    assert terminal_target not in environment.observe()


def test_every_active_transition_is_one_opportunity_and_inactive_clock_freezes() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 6, 1, 0))
    temp_target = environment.snapshot_state()["spec"]["temp_target"]
    _advance_to(environment, 12)
    at_leave = environment.snapshot_state()
    assert at_leave["lifecycles"][temp_target]["opportunities"] == 12
    assert at_leave["action_opportunities"] == sum(
        lifecycle["opportunities"] for lifecycle in at_leave["lifecycles"].values()
    )
    _advance_to(environment, 16)
    at_rejoin = environment.snapshot_state()
    assert at_rejoin["lifecycles"][temp_target]["opportunities"] == 12
    environment.step(_correct_actions(environment))
    assert environment.snapshot_state()["lifecycles"][temp_target]["opportunities"] == 13


def test_active_count_is_always_normalized_by_four() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 6, 1, 0))
    assert {observation.actor[5] for observation in environment.observe().values()} == {0.5}
    _advance_to(environment, 12)
    assert {observation.actor[5] for observation in environment.observe().values()} == {0.25}
    _advance_to(environment, 16)
    assert {observation.actor[5] for observation in environment.observe().values()} == {0.5}
    _advance_to(environment, 28)
    assert {observation.actor[5] for observation in environment.observe().values()} == {0.75}


def test_snapshot_round_trip_is_exact_and_continuations_are_independent() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("heldout", 3, 18, -1, 1))
    _advance_to(environment, 17)
    snapshot = environment.snapshot_state()
    restored = TemporalDutyG1Env.from_snapshot_state(snapshot)
    assert restored.snapshot_state() == snapshot
    assert restored.observe() == environment.observe()

    mutated = deepcopy(snapshot)
    mutated["lifecycles"][0]["age"] += 1
    assert restored.snapshot_state() == snapshot

    for _ in range(9):
        assert restored.step(_correct_actions(restored)) == environment.step(
            _correct_actions(environment)
        )
    assert restored.snapshot_state() == environment.snapshot_state()


def test_action_domain_and_exact_active_key_set_are_enforced() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 2, 6, 1, 0))
    with pytest.raises(ValueError, match="action"):
        environment.step({0: 2, 1: 0})
    with pytest.raises(ValueError, match="active"):
        environment.step({0: 0})
    with pytest.raises(ValueError, match="action"):
        environment.step({0: True, 1: 0})


def test_horizon_censors_unfinished_segments_and_utility_reward_identity() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("fitting", 3, 14, 1, 0))
    rewards: list[float] = []
    while _time(environment) < 80:
        transition = environment.step(_correct_actions(environment))
        rewards.append(float(transition["reward"]))
    outcome = environment.outcome()

    assert transition["done"] is True
    assert outcome["action_opportunities"] == 276.0
    assert outcome["eligible_segments"] == 21.0
    assert outcome["successful_segments"] == 17.0
    assert outcome["action_accuracy"] == 1.0
    assert outcome["segment_success_rate"] == pytest.approx(17.0 / 21.0)
    assert outcome["utility"] == pytest.approx(0.75 + 0.25 * 17.0 / 21.0)
    assert outcome["reward_sum"] == pytest.approx(outcome["utility"])
    assert sum(rewards) == pytest.approx(outcome["utility"])
    assert 0.0 <= outcome["utility"] <= 1.0


def test_incorrect_actions_keep_utility_in_range_and_reward_sum_exact() -> None:
    environment = TemporalDutyG1Env(make_episode_spec("heldout", 3, 10, -1, 0))
    rewards = []
    while _time(environment) < 80:
        transition = environment.step(_zero_actions(environment))
        rewards.append(float(transition["reward"]))
    outcome = environment.outcome()
    assert outcome["utility"] == 0.0
    assert outcome["reward_sum"] == 0.0
    assert sum(rewards) == 0.0
    assert 0.0 <= outcome["utility"] <= 1.0
