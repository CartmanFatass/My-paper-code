from __future__ import annotations

import pytest

from ha_ctse_process.cross_lifecycle_handoff_g2 import (
    CrossLifecycleHandoffG2Env,
    HELDOUT_DUTY_DURATIONS,
    HELDOUT_GAPS,
    PASS_RESULT,
    TRAIN_DUTY_DURATIONS,
    TRAIN_GAPS,
    build_cases,
    evaluate_information_gate,
    make_episode_spec,
    simulate_handoff,
    validate_cases,
)


def test_exhaustive_cases_are_balanced_anonymous_and_cover_handoffs() -> None:
    cases = build_cases()
    inventory = validate_cases(cases)

    assert len(cases) == 96
    assert inventory == {
        "bits": [-1, 1],
        "creator_durations": [1, 2],
        "successor_durations": [2, 4],
        "physical_slots": [0, 1, 2],
        "mapping_count": 12,
        "same_slot_handoffs": 48,
        "cross_slot_handoffs": 48,
        "active_count_profile": [2, 1, 2],
    }

    first = cases[0]
    with pytest.raises(ValueError, match="sign mate"):
        validate_cases(tuple(case for case in cases if case != first))


def test_information_bound_and_constructive_controls_are_exact() -> None:
    result = evaluate_information_gate(build_cases())

    assert result["result"] == PASS_RESULT
    assert result["formal"] is False
    assert result["metrics"] == {
        "successor_per_member_bayes_bound": 0.5,
        "per_member_rec_utility": 0.5,
        "dum_utility": 0.5,
        "team_rec_utility": 1.0,
        "ehc_utility": 1.0,
        "random_mark_utility": 0.5,
        "ehc_flip_action_change": 1.0,
        "ehc_flip_utility": 0.0,
        "ehc_flip_utility_drop": 1.0,
    }
    assert result["state_ownership"] == {
        "creator_member_state_deleted": True,
        "successor_member_state_zero_at_join": True,
        "team_recurrent_state_survives": True,
        "event_held_state_survives": True,
        "fixed_slot_is_state_owner": False,
    }


def test_successor_trace_has_no_bit_or_identity_leakage() -> None:
    cases = build_cases()
    grouped: dict[tuple[object, ...], set[int]] = {}
    for case in cases:
        grouped.setdefault(case.successor_trace_key(), set()).add(case.bit)

    assert len(grouped) == 2
    assert all(bits == {-1, 1} for bits in grouped.values())
    assert {len(trace) for trace in grouped} == {2, 4}

    same_slot = next(case for case in cases if case.creator_slot == case.successor_slot)
    cross_slot = next(case for case in cases if case.creator_slot != case.successor_slot)
    for case in (same_slot, cross_slot):
        state = simulate_handoff(case)
        assert state.successor_value(case) == 0
        assert state.team_recurrent_state == case.bit
        assert state.held_mark == case.bit
        assert state.held_owner_slot is None
        assert not any(
            member.physical_slot == case.creator_slot and member.lifecycle == 0
            for member in state.members
        )
        assert state.with_held_mark(-case.bit).held_mark == -case.bit


def test_train_iid_heldout_ledgers_are_paired_independent_and_cover_support() -> None:
    for profile in ("train", "iid", "heldout"):
        plus = make_episode_spec(profile, base_id=11, sign_mate=1)
        minus = make_episode_spec(profile, base_id=11, sign_mate=-1)
        assert minus.bit == -plus.bit
        assert minus.creator_slot == plus.creator_slot
        assert minus.successor_slot == plus.successor_slot
        assert minus.survivor_slot == plus.survivor_slot
        assert minus.creator_duration == plus.creator_duration
        assert minus.gap == plus.gap
        assert minus.successor_duration == plus.successor_duration
        assert minus.nuisance == plus.nuisance

    train = [make_episode_spec("train", base_id=index, sign_mate=1) for index in range(96)]
    heldout = [
        make_episode_spec("heldout", base_id=index, sign_mate=1) for index in range(96)
    ]
    assert {spec.gap for spec in train} == set(TRAIN_GAPS)
    assert {spec.successor_duration for spec in train} == set(TRAIN_DUTY_DURATIONS)
    assert {spec.gap for spec in heldout} == set(HELDOUT_GAPS)
    assert {spec.successor_duration for spec in heldout} == set(
        HELDOUT_DUTY_DURATIONS
    )
    assert {
        (spec.creator_slot, spec.successor_slot, spec.survivor_slot)
        for spec in train + heldout
    } == {
        (case.creator_slot, case.successor_slot, case.survivor_slot)
        for case in build_cases()
    }


def test_trainable_environment_has_no_actor_leak_and_exact_reward_snapshot() -> None:
    plus_spec = make_episode_spec("heldout", base_id=7, sign_mate=1)
    minus_spec = make_episode_spec("heldout", base_id=7, sign_mate=-1)
    plus = CrossLifecycleHandoffG2Env(plus_spec)
    minus = CrossLifecycleHandoffG2Env(minus_spec)

    assert plus.observe()[plus_spec.creator_slot].actor[0] == plus_spec.bit
    assert minus.observe()[minus_spec.creator_slot].actor[0] == minus_spec.bit
    while plus.time < plus_spec.successor_join_time:
        plus.step(plus.oracle_actions())
        minus.step(minus.oracle_actions())

    plus_successor = plus.observe()[plus_spec.successor_slot]
    minus_successor = minus.observe()[minus_spec.successor_slot]
    assert plus_successor.lifecycle == minus_successor.lifecycle == 1
    assert plus_successor.actor == minus_successor.actor
    assert plus_successor.critic != minus_successor.critic
    assert plus_successor.actor[0:2] == (0.0, 0.0)
    assert plus_successor.actor[2] == 1.0

    snapshot = plus.snapshot_state()
    restored = CrossLifecycleHandoffG2Env.from_snapshot(snapshot)
    assert restored.snapshot_state() == snapshot
    while not plus.done:
        plus_result = plus.step(plus.oracle_actions())
        restored_result = restored.step(restored.oracle_actions())
        assert plus_result == restored_result
    assert plus_result["utility"] == 1.0
    assert plus_result["reward"] == 1.0

    reactive = CrossLifecycleHandoffG2Env(minus_spec)
    reward_sum = 0.0
    while not reactive.done:
        actions = reactive.reactive_actions()
        if reactive.time >= minus_spec.successor_join_time:
            actions[minus_spec.successor_slot] = -minus_spec.bit
        result = reactive.step(actions)
        reward_sum += float(result["reward"])
    assert result["utility"] == 0.0
    assert reward_sum == 0.0
