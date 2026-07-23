from __future__ import annotations

from copy import deepcopy

import pytest

from ha_ctse_process.temporal_duty_g1 import (
    DURATION_SUPPORT,
    G1Observation,
    TemporalDutyG1Env,
    make_episode_spec,
)


SEEDS = {
    "task_seed": 168058,
    "membership_seed": 169058,
    "duty_seed": 170058,
    "opportunity_seed": 171058,
}


def _spec(
    profile: str = "train", *, base_id: int = 0, sign_mate: int = 1, **seeds: int
):
    return make_episode_spec(
        profile,
        base_id=base_id,
        sign_mate=sign_mate,
        **(SEEDS | seeds),
    )


def _state(env: TemporalDutyG1Env) -> dict[str, object]:
    return env.snapshot_state()


def _correct(env: TemporalDutyG1Env) -> dict[int, int]:
    return env.oracle_actions()


def _advance(env: TemporalDutyG1Env, target_time: int) -> None:
    while int(_state(env)["time"]) < target_time:
        env.step(_correct(env))


def test_counter_based_ledgers_are_deterministic_paired_and_independent() -> None:
    positive = _spec("heldout", base_id=17, sign_mate=1)
    repeated = _spec("heldout", base_id=17, sign_mate=1)
    negative = _spec("heldout", base_id=17, sign_mate=-1)
    assert positive == repeated
    assert positive.roster_size in (2, 3)
    assert negative.roster_size == positive.roster_size
    assert negative.membership_events == positive.membership_events
    assert negative.logical_to_physical == positive.logical_to_physical
    for plus, minus in zip(positive.lifecycle_ledgers, negative.lifecycle_ledgers, strict=True):
        assert minus.durations == plus.durations
        assert minus.opportunity_gaps == plus.opportunity_gaps
        assert minus.targets == tuple(-target for target in plus.targets)

    changed_membership = _spec("heldout", base_id=17, membership_seed=169059)
    assert [row.targets for row in changed_membership.lifecycle_ledgers] == [
        row.targets for row in positive.lifecycle_ledgers
    ]
    assert [row.durations for row in changed_membership.lifecycle_ledgers] == [
        row.durations for row in positive.lifecycle_ledgers
    ]
    assert [row.opportunity_gaps for row in changed_membership.lifecycle_ledgers] == [
        row.opportunity_gaps for row in positive.lifecycle_ledgers
    ]

    changed_opportunity = _spec("heldout", base_id=17, opportunity_seed=171059)
    assert changed_opportunity.membership_events == positive.membership_events
    assert [row.targets for row in changed_opportunity.lifecycle_ledgers] == [
        row.targets for row in positive.lifecycle_ledgers
    ]
    assert [row.durations for row in changed_opportunity.lifecycle_ledgers] == [
        row.durations for row in positive.lifecycle_ledgers
    ]


def test_rosters_duration_support_and_heldout_balanced_cycles() -> None:
    specs = [_spec("train", base_id=base_id) for base_id in range(64)]
    assert {spec.roster_size for spec in specs} == {2, 3}
    assert {duration for spec in specs for row in spec.lifecycle_ledgers for duration in row.durations} == set(DURATION_SUPPORT)
    assert {target for spec in specs for row in spec.lifecycle_ledgers for target in row.targets} == {-1, 1}

    heldout = _spec("heldout", base_id=9)
    for ledger in heldout.lifecycle_ledgers:
        assert set(ledger.durations[:4]) == set(DURATION_SUPPORT)
        assert ledger.durations[4:8] == ledger.durations[:4]


def test_train_iid_and_heldout_membership_patterns_and_packing() -> None:
    for profile in ("train", "iid"):
        spec = _spec(profile, base_id=12)
        events = {name: (time, target) for time, name, target in spec.membership_events}
        assert 10 <= events["TEMP_LEAVE"][0] <= 18
        assert 3 <= events["REJOIN"][0] - events["TEMP_LEAVE"][0] <= 7
        assert 28 <= events["JOIN"][0] <= 38
        assert events["JOIN"][0] > events["REJOIN"][0]
        assert 58 <= events["TERMINAL_LEAVE"][0] <= 70
        assert events["TEMP_LEAVE"][1] != events["TERMINAL_LEAVE"][1]
        assert spec.logical_to_physical == tuple(range(spec.roster_size))

    spec = _spec("heldout", base_id=12)
    events = {name: (time, target) for time, name, target in spec.membership_events}
    assert 8 <= events["JOIN"][0] <= 14
    assert 30 <= events["TEMP_LEAVE"][0] <= 38
    assert events["JOIN"][0] < events["TEMP_LEAVE"][0]
    assert 8 <= events["REJOIN"][0] - events["TEMP_LEAVE"][0] <= 12
    assert 62 <= events["TERMINAL_LEAVE"][0] <= 74
    assert spec.packing_mode == "REVERSED_ROTATED"
    assert sorted(spec.logical_to_physical) == list(range(spec.roster_size))


def test_actor_and_critic_views_are_exact_and_cue_expires_after_two_active_steps() -> None:
    env = TemporalDutyG1Env(_spec(base_id=2, sign_mate=-1))
    initial = env.observe()
    observation = initial[min(initial)]
    target = float(_state(env)["lifecycles"][min(initial)]["target"])
    assert isinstance(observation, G1Observation)
    assert len(observation.actor) == 6
    assert len(observation.critic) == 10
    assert observation.actor[:5] == (target, 1.0, 1.0, 1.0, 0.0)
    assert observation.critic[:6] == observation.actor
    assert observation.critic[6:] == (0.0, observation.critic[7], 0.0, 0.0)
    assert observation.opportunity_kind == "CREATE"
    assert set(vars(observation)) == {"actor", "critic", "opportunity_kind"}

    env.step(_correct(env))
    assert all(obs.actor[1] == 1.0 for obs in env.observe().values())
    env.step(_correct(env))
    assert all(obs.actor[:3] == (0.0, 0.0, 0.0) for obs in env.observe().values())


def test_opportunity_clock_has_create_then_one_or_two_active_step_gaps_and_freezes() -> None:
    env = TemporalDutyG1Env(_spec("train", base_id=5))
    temp_time, _, temp_target = next(
        event for event in env.spec.membership_events if event[1] == "TEMP_LEAVE"
    )
    rejoin_time, _, _ = next(
        event for event in env.spec.membership_events if event[1] == "REJOIN"
    )
    opportunity_times: dict[int, list[int]] = {slot: [] for slot in env.observe()}
    while int(_state(env)["time"]) < temp_time:
        time = int(_state(env)["time"])
        for slot, obs in env.observe().items():
            if obs.opportunity_kind is not None:
                opportunity_times.setdefault(slot, []).append(time)
        env.step(_correct(env))
    assert all(times[0] == 0 for times in opportunity_times.values())
    assert all(
        gap in (1, 2)
        for times in opportunity_times.values()
        for gap in (later - earlier for earlier, later in zip(times, times[1:]))
    )
    frozen = deepcopy(_state(env)["lifecycles"][temp_target])
    _advance(env, rejoin_time)
    restored = _state(env)["lifecycles"][temp_target]
    for field in (
        "target",
        "duration",
        "age",
        "remaining",
        "correct_count",
        "terminal_streak",
        "active_steps",
        "next_opportunity_active_step",
        "opportunity_index",
    ):
        assert restored[field] == frozen[field]
    assert env.observe()[temp_target].actor[4] == 1.0


def test_join_resets_lifecycle_and_terminal_and_horizon_censor_open_segments() -> None:
    env = TemporalDutyG1Env(_spec("heldout", base_id=4))
    join_time, _, join_target = next(
        event for event in env.spec.membership_events if event[1] == "JOIN"
    )
    terminal_time, _, terminal_target = next(
        event for event in env.spec.membership_events if event[1] == "TERMINAL_LEAVE"
    )
    _advance(env, join_time)
    joined = _state(env)["lifecycles"][join_target]
    assert joined["age"] == joined["correct_count"] == joined["terminal_streak"] == 0
    assert joined["remaining"] == joined["duration"]
    assert env.observe()[join_target].actor[2:5] == (1.0, 1.0, 0.0)
    assert env.observe()[join_target].opportunity_kind == "CREATE"

    _advance(env, terminal_time)
    terminal = _state(env)["lifecycles"][terminal_target]
    assert terminal["terminal"] and not terminal["active"]
    completed_before = int(_state(env)["completed_segments"])
    while int(_state(env)["time"]) < env.spec.horizon:
        env.step(_correct(env))
    final = _state(env)
    assert int(final["completed_segments"]) >= completed_before
    assert int(final["started_segments"]) == env.spec.started_segment_denominator
    assert int(final["completed_segments"]) < int(final["started_segments"])


@pytest.mark.parametrize(
    ("actions", "successful"),
    [
        ((1, 1, 1, 1, 1, 1), True),
        ((1, 1, 1, 1, 0, 0), False),
        ((0, 0, 1, 1, 1, 1), False),
    ],
)
def test_segment_success_requires_three_quarters_and_last_two(
    actions: tuple[int, ...], successful: bool
) -> None:
    spec = next(
        spec
        for base_id in range(128)
        if (spec := _spec("heldout", base_id=base_id)).lifecycle_ledgers[0].durations[0]
        == 6
    )
    env = TemporalDutyG1Env(spec)
    slot = min(env.observe())
    target = _state(env)["lifecycles"][slot]["target"]
    for is_correct in actions:
        step_actions = env.oracle_actions()
        step_actions[slot] = int(target) if is_correct else -int(target)
        env.step(step_actions)
    record = next(
        row
        for row in _state(env)["segment_records"]
        if row["slot"] == slot and row["segment_index"] == 0
    )
    assert record["status"] == "COMPLETED"
    assert record["success"] is successful


def test_reward_increments_sum_exactly_to_registered_utility() -> None:
    env = TemporalDutyG1Env(_spec("iid", base_id=31))
    rewards: list[float] = []
    while int(_state(env)["time"]) < env.spec.horizon:
        transition = env.step(env.history_free_actions(seed=777))
        rewards.append(float(transition["reward"]))
    outcome = env.outcome()
    expected = 0.75 * outcome["action_accuracy"] + 0.25 * outcome["segment_success_rate"]
    assert outcome["action_opportunities"] == outcome["action_denominator"]
    assert outcome["started_segments"] == outcome["eligible_segments"]
    assert outcome["utility"] == pytest.approx(expected)
    assert outcome["reward_sum"] == pytest.approx(expected, abs=1e-15)
    assert sum(rewards) == pytest.approx(expected, abs=1e-15)


def test_snapshot_restore_exact_and_controls_are_deterministic_history_free() -> None:
    env = TemporalDutyG1Env(_spec("heldout", base_id=23))
    _advance(env, 37)
    snapshot = env.snapshot_state()
    restored = TemporalDutyG1Env.from_snapshot_state(snapshot)
    assert restored.snapshot_state() == snapshot
    assert restored.observe() == env.observe()
    assert restored.oracle_actions() == env.oracle_actions()
    assert restored.history_free_actions(seed=991) == env.history_free_actions(seed=991)

    mutated = deepcopy(snapshot)
    mutated["lifecycles"][next(iter(mutated["lifecycles"]))]["age"] += 1
    assert restored.snapshot_state() == snapshot
    for _ in range(11):
        actions = env.history_free_actions(seed=991)
        assert restored.step(actions) == env.step(actions)


def test_input_domains_fail_closed() -> None:
    with pytest.raises(ValueError, match="profile"):
        _spec("fitting")
    with pytest.raises(ValueError, match="sign_mate"):
        _spec(sign_mate=0)
    with pytest.raises(ValueError, match="base_id"):
        _spec(base_id=-1)
    env = TemporalDutyG1Env(_spec())
    with pytest.raises(ValueError, match="active slots"):
        env.step({})
    bad = env.oracle_actions()
    bad[min(bad)] = 2
    with pytest.raises(ValueError, match="action"):
        env.step(bad)
