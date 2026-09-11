"""Unit checks for DISH-RENEWAL-BOUNDARY-A02-CORRECTION; no native library required."""

import ast
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.renewal_boundary_a01 import (
    HARD_EVENTS,
)
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.renewal_boundary_a02 import (
    OBJECT, ROW_KEYS, make_row, reduce_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    NativeBatch, _ResetInput, _State, _StepOutput, empty_step_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_contract import (
    TRAIN_LANES,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, NativePersistentTrainingFlow, RecurrentRolloutState,
    TICKS_PER_UPDATE_PER_LANE,
)


REPO = Path(__file__).resolve().parents[5]


def _fake_batch(countdowns, raw_renew=None, ticks=None):
    width = len(countdowns)
    batch = NativeBatch.__new__(NativeBatch)
    batch.width = width
    batch.library = "no-native"
    batch._states = (_State * width)()
    batch._outputs = (_StepOutput * width)()
    if raw_renew is None:
        raw_renew = [0] * width
    if ticks is None:
        ticks = [0] * width
    for index, countdown in enumerate(countdowns):
        batch._states[index].countdown = int(countdown)
        batch._states[index].tick = int(ticks[index])
        batch._outputs[index].renew = int(raw_renew[index])
        batch._outputs[index].tick = int(ticks[index])
    return batch


def _reset_row(phase):
    names = [name for name, _ in _ResetInput._fields_ if name != "master"]
    row = {name: 0 for name in names}
    row["master"] = bytes(32)
    row["phase"] = int(phase)
    row["k_initial"] = 8
    row["k_new"] = 8
    row["reflection"] = 1
    return row


class _StubResetLibrary:
    def dish_rbhr_r06_prod_reset_selected_batch(self, reset_array, selected, width, states, outputs):
        width = int(width)
        for index in range(width):
            if selected[index]:
                states[index].countdown = reset_array[index].phase
                states[index].tick = 0
                outputs[index].renew = 0
                outputs[index].tick = 0
        return 0


class _StubStepLibrary:
    def dish_rbhr_r06_prod_step_batch(self, states, pointer, width, outputs):
        del pointer
        width = int(width)
        for index in range(width):
            outputs[index].renew = int(states[index].countdown == 0)
            if states[index].countdown == 0:
                states[index].countdown = 7
            else:
                states[index].countdown -= 1
            states[index].tick += 1
            outputs[index].tick = states[index].tick
        return 0


def _observation(**overrides):
    value = {
        "terminal": np.array([0]), "owner": np.array([0]), "renew": np.array([0]),
        "renew_completed": np.array([0]), "tick": np.array([0]), "service": np.array([0]),
        "cas_applied": np.array([0]),
        **{name: np.array([0]) for name in HARD_EVENTS},
    }
    value.update(overrides)
    return value


def _state(**overrides):
    row = np.zeros(1, dtype=np.dtype(_State))
    for name, value in overrides.items():
        row[name] = value
    return row


def test_ordinary_observe_reports_current_countdown_permission():
    batch = _fake_batch(countdowns=[0, 3, 0], raw_renew=[0, 1, 1])
    observation = batch.observe()
    np.testing.assert_array_equal(observation["renew"], np.array([1, 0, 1], dtype=observation["renew"].dtype))
    np.testing.assert_array_equal(
        observation["renew_completed"], np.array([0, 1, 1], dtype=observation["renew_completed"].dtype),
    )
    batch.library = _StubStepLibrary()
    after = batch.step(empty_step_rows(3))
    np.testing.assert_array_equal(after["renew_completed"], np.array([1, 0, 1], dtype=after["renew_completed"].dtype))
    np.testing.assert_array_equal(after["renew"], np.array([0, 0, 0], dtype=after["renew"].dtype))


def test_reset_phase_zero_exposes_renew_one_phase_four_exposes_zero():
    batch = _fake_batch(countdowns=[4], raw_renew=[1])
    batch.library = _StubResetLibrary()
    zero = batch.reset_selected(np.array([1], dtype=np.int32), (_reset_row(0),))
    np.testing.assert_array_equal(zero["renew"], np.array([1], dtype=zero["renew"].dtype))
    np.testing.assert_array_equal(zero["renew_completed"], np.array([0], dtype=zero["renew_completed"].dtype))
    four = batch.reset_selected(np.array([1], dtype=np.int32), (_reset_row(4),))
    np.testing.assert_array_equal(four["renew"], np.array([0], dtype=four["renew"].dtype))
    np.testing.assert_array_equal(four["renew_completed"], np.array([0], dtype=four["renew_completed"].dtype))


def test_repeated_observe_does_not_advance_tick_or_countdown():
    batch = _fake_batch(countdowns=[0, 3, 0], raw_renew=[1, 0, 1], ticks=[5, 5, 5])
    first = batch.observe()
    second = batch.observe()
    np.testing.assert_array_equal(first["renew"], second["renew"])
    np.testing.assert_array_equal(first["renew_completed"], second["renew_completed"])
    np.testing.assert_array_equal(first["tick"], second["tick"])
    assert [int(batch._states[index].countdown) for index in range(3)] == [0, 3, 0]
    assert [int(batch._states[index].tick) for index in range(3)] == [5, 5, 5]


def test_collector_fragment_fields_follow_corrected_renew():
    # 0 backward. One BatchedRecurrentPolicy construction (checkpoint_bytes=None),
    # matching test_package.py::test_genuine_policy_link.
    torch.set_num_threads(1)
    corrected = np.zeros((TICKS_PER_UPDATE_PER_LANE, TRAIN_LANES), dtype=np.int32)
    corrected[0, 0] = 1
    corrected[0, 1] = 0
    corrected[1, 0] = 0
    corrected[1, 1] = 1
    actor = np.zeros((TRAIN_LANES, 4, 54), dtype=np.float32)
    hidden = np.zeros((TRAIN_LANES, 4, 128), dtype=np.float32)
    observation_ticks = []
    outcome_ticks = []
    action_ticks = []
    label_ticks = []
    normalized_actor_ticks = []
    hidden_before_ticks = []
    reset_ticks = []
    behavior_log_prob_ticks = []
    for tick in range(TICKS_PER_UPDATE_PER_LANE):
        observation_ticks.append({
            "actor": actor,
            "owner": np.zeros(TRAIN_LANES, dtype=np.int64),
            "renew": corrected[tick],
            "snapshot_payload": np.zeros((TRAIN_LANES, 18), dtype=np.float32),
            "snapshot_delivery_mask": np.zeros(TRAIN_LANES, dtype=bool),
        })
        outcome_ticks.append({
            "critic": np.zeros((TRAIN_LANES, 58), dtype=np.float32),
            "cas_applied": np.zeros(TRAIN_LANES, dtype=np.int32),
            "service": np.zeros(TRAIN_LANES, dtype=np.float32),
            "terminal": np.zeros(TRAIN_LANES, dtype=bool),
        })
        action_ticks.append(empty_step_rows(TRAIN_LANES))
        label_ticks.append({
            "target": np.zeros((TRAIN_LANES, 4), dtype=np.float32),
            "links": np.zeros((TRAIN_LANES, 4, 2), dtype=np.float32),
            "missing": np.zeros((TRAIN_LANES, 4), dtype=np.float32),
            "q_labels": np.zeros((TRAIN_LANES, 20), dtype=np.float32),
            "q_mask": np.ones(TRAIN_LANES, dtype=bool),
            "next_mask": np.ones(TRAIN_LANES, dtype=bool),
            "q_copy_index": np.zeros(TRAIN_LANES, dtype=np.int64),
        })
        normalized_actor_ticks.append(actor)
        hidden_before_ticks.append(hidden)
        reset_ticks.append(np.zeros(TRAIN_LANES, dtype=bool))
        behavior_log_prob_ticks.append(np.zeros(TRAIN_LANES, dtype=np.float32))
    fragments = NativePersistentTrainingFlow._fragments(
        None, observation_ticks, outcome_ticks, action_ticks, label_ticks,
        normalized_actor_ticks, hidden_before_ticks, reset_ticks,
        behavior_log_prob_ticks,
    )
    expected_two_tick = np.array([[True, False], [False, True]])
    renew_tick_lane = fragments["renew"].numpy().reshape(
        TRAIN_LANES, TICKS_PER_UPDATE_PER_LANE,
    ).T
    np.testing.assert_array_equal(renew_tick_lane[:2, :2], expected_two_tick)
    np.testing.assert_array_equal(fragments["renew"].numpy(), fragments["prepare_mask"].numpy())
    np.testing.assert_array_equal(fragments["renew"].numpy(), fragments["commit_mask"].numpy())

    observation = {
        "actor": np.full((2, 4, 54), 0.02, np.float32),
        "owner": np.array([0, 1]), "renew": np.array([1, 0], dtype=np.int32),
        "snapshot_payload": np.zeros((2, 18), np.float32),
        "snapshot_delivery_mask": np.zeros(2, dtype=bool),
    }
    state = RecurrentRolloutState.fresh("STRUCTURED", width=2)
    policy = BatchedRecurrentPolicy(
        arm="STRUCTURED", checkpoint_bytes=None, state=state, forecast_package=True,
    )
    first = policy.step_rows(observation, sampler=None, global_tick=0, deterministic=True)
    held = float(np.float32(0.02))
    np.testing.assert_allclose(first["raw_action"][1], [held, held, held, held], rtol=0, atol=0)
    assert not np.allclose(first["raw_action"][0], first["raw_action"][1])
    observation["renew"] = np.array([0, 1], dtype=np.int32)
    second = policy.step_rows(observation, sampler=None, global_tick=1, deterministic=True)
    np.testing.assert_allclose(second["raw_action"][0], [held, held, held, held], rtol=0, atol=0)


def test_reduce_rows_four_tick_handwritten_counts():
    held = [0.0, 0.0, 0.0, 0.0]
    projected_one = [1.0, 0.0, 0.0, 0.0]
    rows = [
        {
            "window": 1, "t": 0, "policy_renew": False, "native_admission": False,
            "renew_completed": False,
            "held_changed": False, "incorporated_as_projected": False,
            "value_equal_to_held": True, "held_before": held, "held_after": held,
            "emitted": held, "projected_expected": held,
        },
        {
            "window": 1, "t": 1, "policy_renew": True, "native_admission": True,
            "renew_completed": True,
            "held_changed": True, "incorporated_as_projected": True,
            "value_equal_to_held": False, "held_before": held,
            "held_after": projected_one, "emitted": projected_one,
            "projected_expected": projected_one,
        },
        {
            "window": 1, "t": 2, "policy_renew": True, "native_admission": False,
            "renew_completed": False,
            "held_changed": False, "incorporated_as_projected": False,
            "value_equal_to_held": False, "held_before": projected_one,
            "held_after": projected_one, "emitted": [2.0, 0.0, 0.0, 0.0],
            "projected_expected": [2.0, 0.0, 0.0, 0.0],
        },
        {
            "window": 1, "t": 3, "policy_renew": False, "native_admission": True,
            "renew_completed": True,
            "held_changed": True, "incorporated_as_projected": False,
            "value_equal_to_held": True, "held_before": projected_one,
            "held_after": [0.5, 0.0, 0.0, 0.0], "emitted": projected_one,
            "projected_expected": projected_one,
        },
    ]
    result = reduce_rows(rows)
    overall = result["overall"]
    assert overall["matched_renewals"] == 1
    assert overall["matched_non_renewals"] == 1
    assert overall["native_true_policy_false"] == 1
    assert overall["policy_true_native_false"] == 1
    assert overall["native_out_renew_equals_policy_renew"] == 2
    assert overall["native_out_true_policy_false"] == 1
    assert overall["policy_true_native_out_false"] == 1
    assert overall["admissions"] == 2
    assert overall["admissions_held_equals_projected"] == 1
    assert overall["admissions_emitted_equals_held"] == 1
    assert overall["held_changed_ticks"] == 2
    assert overall["live_ticks"] == 4
    assert result["per_window"]["1"]["live_ticks"] == 4
    pre = _state(tick=0, countdown=0, owner=0, a=(0.0, 0.0, 0.0, 0.0), total_energy=1.0)
    post = _state(tick=1, countdown=7, owner=0, a=(1.0, 0.0, 0.0, 0.0), total_energy=2.0)
    step = empty_step_rows(1)
    step["raw_action"][0] = (1.0, 0.0, 0.0, 0.0)
    row = make_row(
        window=1, t=1,
        observation=_observation(renew=np.array([1]), tick=np.array([0])),
        pre=pre, step_rows=step, post=post,
        observation_after=_observation(
            renew=np.array([0]), renew_completed=np.array([1]),
            tick=np.array([1]), service=np.array([1]),
        ),
    )
    for key in ROW_KEYS:
        assert key in row
    assert "hard_events" in row and "hard_event_increments" in row
    assert set(row["hard_events"]) == set(HARD_EVENTS)
    assert set(row["hard_event_increments"]) == set(HARD_EVENTS)
    assert row["policy_renew"] is True
    assert row["renew_completed"] is True
    assert row["native_admission"] is True
    assert row["incorporated_as_projected"] is True
    assert row["value_equal_to_held"] is False
    assert OBJECT == "DISH-RENEWAL-BOUNDARY-A02-CORRECTION"


def test_source_parses():
    paths = (
        REPO / "experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a02.py",
        REPO / "scripts/run_dish_renewal_boundary_a02.py",
        REPO / "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py",
    )
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
