from __future__ import annotations

from dataclasses import replace
import math

import pytest

from experiments.candidates.acvc import analyze
from experiments.candidates.acvc.host import (
    Binding, FRAME_SIZE, PREDICATE, Action, CanonicalState, Feedback,
    SceneBlueprint, encode_frame, frame_signals, iter_scenes, manifest_balance,
    parse_frames, run_scene,
)
from experiments.candidates.acvc.policies import (
    AUTH_PROBE, DET_BOUND, IGNORE, LEARN_CORRECT, LEARN_PERM,
    TabularQLearner, counter_uniform, epsilon_for_episode, evaluation_tie_rank,
    fixed_action,
)
from experiments.candidates.acvc.run import BASE_SEEDS, CAPS, DECLARED_COUNTS


def _first_event(split="test"):
    return next(scene for scene in iter_scenes(11, split) if scene.event)


def test_frame_is_exactly_64_bytes_and_parser_precedence_is_fail_closed():
    binding = Binding(11, 12, 13)
    first = encode_frame(
        sender_id=0, verdict_bit=1, confidence_u8=242, binding=binding,
        sequence=7, auth_tag=b"a" * 16,
    )
    duplicate = encode_frame(
        sender_id=0, verdict_bit=0, confidence_u8=242, binding=binding,
        sequence=7, auth_tag=b"b" * 16,
    )
    unapproved = encode_frame(
        sender_id=2, verdict_bit=0, confidence_u8=242, binding=binding,
        sequence=8, auth_tag=b"c" * 16,
    )
    wrong_version = bytes([2]) + first[1:]
    assert len(first) == FRAME_SIZE == 64
    result = parse_frames(
        [first[:-1], wrong_version, unapproved, first, duplicate],
        authenticated_bytes=frozenset({wrong_version, unapproved, first, duplicate}),
    )
    assert result.rejected == (
        "wrong_length", "wrong_version", "unapproved_sender", "duplicate_sequence"
    )
    assert len(result.accepted) == 1 and result.accepted[0].binding == binding
    failed_auth = parse_frames([first], authenticated_bytes=frozenset())
    assert failed_auth.rejected == ("failed_authentication",)


def test_matching_requires_all_binding_fields_and_inclusive_window_then_epoch_invalidates():
    binding = Binding(11, 12, 13)
    raw = encode_frame(
        sender_id=0, verdict_bit=1, confidence_u8=242, binding=binding,
        sequence=7, auth_tag=b"x" * 16,
    )
    parsed = parse_frames([raw], authenticated_bytes=frozenset({raw})).accepted
    target = replace(_first_event().targets[0], event_id=11, epoch=12, target_id=13)
    assert frame_signals(parsed, target=target, current_epoch=12, tick=1) == (True, True)
    assert frame_signals(parsed, target=target, current_epoch=12, tick=12) == (True, True)
    assert frame_signals(parsed, target=target, current_epoch=13, tick=2) == (True, False)
    assert frame_signals(parsed, target=target, current_epoch=12, tick=13) == (True, False)
    wrong_predicate = replace(parsed[0], binding=replace(binding, predicate=PREDICATE + 1))
    assert frame_signals([wrong_predicate], target=target, current_epoch=12, tick=2) == (True, False)


@pytest.mark.parametrize("split", ["train", "validation", "test"])
def test_registered_scene_manifests_have_exact_counts_cells_orders_and_permutations(split):
    rows = list(iter_scenes(11, split))
    report = manifest_balance(rows)
    expected = {
        "train": (7680, 3840, 20),
        "validation": (768, 384, 2),
        "test": (3840, 1920, 10),
    }[split]
    total, event, repeats = expected
    assert report["scenes"] == total
    assert report["event"] == event
    assert report["all_clean"] == total - event
    assert set(report["event_cell_counts"]) == {repeats}
    assert set(report["service_order_counts"]["event"]) == {event // 24}
    assert set(report["service_order_counts"]["all_clean"]) == {(total - event) // 24}
    assert set(report["permutation_counts"]["event"]) == {event // 24}
    assert set(report["permutation_counts"]["all_clean"]) == {(total - event) // 24}


def test_correct_and_permuted_frames_preserve_multisets_but_change_only_payload_association():
    scene = next(
        row for row in iter_scenes(11, "test")
        if row.event and row.binding_permutation != tuple(range(4))
    )
    correct_raw = scene.frame_bytes(LEARN_CORRECT)
    perm_raw = scene.frame_bytes(LEARN_PERM)
    correct = parse_frames(correct_raw, authenticated_bytes=frozenset(correct_raw)).accepted
    perm = parse_frames(perm_raw, authenticated_bytes=frozenset(perm_raw)).accepted
    bindings = lambda frames: sorted(
        (f.binding.event_id, f.binding.subject_epoch, f.binding.target_id,
         f.binding.predicate, f.binding.valid_from, f.binding.valid_until)
        for f in frames
    )
    payloads = lambda frames: sorted((f.verdict_bit, f.confidence_u8) for f in frames)
    assert bindings(correct) == bindings(perm)
    assert payloads(correct) == payloads(perm) == [(0, 242), (0, 242), (0, 242), (1, 242)]
    true = scene.targets[scene.true_target]
    correct_negative = next(f for f in correct if f.verdict_bit)
    assert correct_negative.binding.target_id == true.target_id
    perm_negative = next(f for f in perm if f.verdict_bit)
    assert perm_negative.binding.target_id == scene.targets[scene.binding_permutation[scene.true_target]].target_id


def test_scene_learning_rewards_include_communication_once_and_activity_rows_include_outcomes():
    scene = _first_event()
    observed = []
    result = run_scene(
        scene, arm=LEARN_CORRECT,
        selector=lambda _state: Action.COMPLETE,
        transition_observer=lambda state, action, reward, next_state, done: observed.append(
            (state, action, reward, next_state, done)
        ),
        retain_rows=True,
    )
    assert math.isclose(sum(row[2] for row in observed), result["scene_reward"], abs_tol=1e-12)
    assert sum(math.isclose(row[2] - result["target_action_outcome_rows"][index]["reward"], -0.04, abs_tol=1e-12)
               for index, row in enumerate(observed)) == 1
    assert all("post_action_invalid" in row for row in result["target_action_outcome_rows"])
    assert observed[-1][4] is True and all(row[4] is False for row in observed[:-1])


def test_q_learning_bootstraps_across_target_boundary_and_zeros_only_at_scene_end():
    learner = TabularQLearner(300011)
    first = CanonicalState(0, 0, Feedback.NONE.value, True, False, False)
    next_target = CanonicalState(1, 0, Feedback.NONE.value, True, False, False)
    learner.values(next_target)[0] = 4.0
    learner.update(first, Action.COMPLETE, 1.0, next_target, False)
    assert learner.values(first)[0] == pytest.approx(0.15 * 5.0)
    final = CanonicalState(3, 0, Feedback.NONE.value, True, False, False)
    learner.update(final, Action.COMPLETE, 1.0, None, True)
    assert learner.values(final)[0] == pytest.approx(0.15)


def test_q_schedule_counter_pairing_fixed_evaluation_rank_and_checkpoint_round_trip():
    assert epsilon_for_episode(1) == pytest.approx(0.30)
    assert epsilon_for_episode(7000) == pytest.approx(0.02)
    assert epsilon_for_episode(7680) == pytest.approx(0.02)
    assert counter_uniform(300011, 8, 2, 1, "epsilon_coin") == counter_uniform(300011, 8, 2, 1, "epsilon_coin")
    assert evaluation_tie_rank(11) == evaluation_tie_rank(11)
    assert set(evaluation_tie_rank(11)) == set(Action)
    learner = TabularQLearner(300011)
    state = CanonicalState(0, 0, Feedback.NONE.value, False, False, False)
    learner.update(state, Action.COMPLETE, 1.0, None, True)
    restored = TabularQLearner.from_json(learner.to_json())
    assert restored.to_json() == learner.to_json()


def test_fixed_policy_analytic_references_on_one_exact_balanced_test_manifest():
    accumulators = {arm: analyze.ArmAccumulator() for arm in (DET_BOUND, AUTH_PROBE, IGNORE)}
    for scene in iter_scenes(11, "test"):
        for arm, accumulator in accumulators.items():
            accumulator.add(run_scene(scene, arm=arm, selector=lambda state, arm=arm: fixed_action(arm, state)))
    summaries = {arm: accumulator.summary() for arm, accumulator in accumulators.items()}
    assert summaries[DET_BOUND]["mean_event_reward"] == pytest.approx(3.46, abs=1e-12)
    assert summaries[DET_BOUND]["d_joint_rate"] == 1.0
    # Service-order/event-target relative alignment is independently shuffled,
    # so a finite registered manifest approaches rather than exactly crosses
    # the analytic AUTH-PROBE reference.
    assert summaries[AUTH_PROBE]["mean_event_reward"] == pytest.approx(2.935, abs=0.01)
    assert summaries[AUTH_PROBE]["d_joint_rate"] == pytest.approx(0.125, abs=0.02)
    assert summaries[IGNORE]["mean_event_reward"] == pytest.approx(-7.04, abs=1e-12)


def test_registered_envelope_has_only_full_budget_and_caps():
    assert BASE_SEEDS == (11, 23, 37, 53, 71, 89, 107, 127, 149, 173)
    assert DECLARED_COUNTS == {
        "learned_arm_scenes": 245760,
        "fixed_policy_test_scenes": 115200,
        "maximum_decision_transitions": 4331520,
        "learned_checkpoints": 20,
        "base_seeds": 10,
    }
    assert CAPS == {
        "cpu_workers": 1,
        "decision_transitions": 5000000,
        "wall_seconds": 1080,
        "peak_rss_bytes": 1610612736,
    }


def test_t_intervals_use_ten_seed_level_values_and_prespecified_criteria():
    arms = {
        LEARN_CORRECT: {"mean_event_reward": 3.46, "invalid_false_complete_rate": 0.0,
                        "clean_harm_all_clean_scenes": 0.0, "clean_harm_event_clean_targets": 0.0,
                        "d_joint_rate": 1.0},
        LEARN_PERM: {"mean_event_reward": 2.46, "d_joint_rate": 0.0},
        DET_BOUND: {"mean_event_reward": 3.46, "d_joint_rate": 1.0},
        AUTH_PROBE: {"mean_event_reward": 2.935, "d_joint_rate": 0.125},
    }
    result = analyze.analyze_registered([{"arms": arms} for _ in range(10)])
    assert result["tau_neg"]["student_t_95"] == {
        "mean": 1.0, "lower": 1.0, "upper": 1.0, "standard_error": 0.0,
    }
    assert result["all_prespecified_criteria_hold"] is True
