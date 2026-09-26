"""Independent known-array checks for the fixed B08 recovery description."""

from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
from experiments.candidates.uav_service_auxiliary.b08.metrics import (
    aggregate_opportunity_summaries,
    recovery_opportunity_summary,
)


def _fixture():
    horizon, members = 8, 3
    mode_before = np.zeros((horizon, members), dtype=bool)
    mode = np.zeros_like(mode_before)
    entry = np.zeros_like(mode_before)
    exit_ = np.zeros_like(mode_before)
    charger = np.zeros((horizon, members), dtype=np.float64)
    stored = np.zeros_like(charger)

    for member in (0, 1):
        entry[0, member] = True
        mode[0:2, member] = True
        mode_before[1:3, member] = True
        exit_[2, member] = True
        charger[1, member] = 2.0 + member
        stored[1, member] = 2.0 + member
        stored[2, member] = -0.5
    # A later re-entry by member 0 is censored and has no input.
    entry[4, 0] = True
    mode[4:, 0] = True
    mode_before[5:, 0] = True
    # Member 2 activates later, receives input, and is right-censored.
    entry[4, 2] = True
    mode[4:, 2] = True
    mode_before[5:, 2] = True
    charger[5, 2] = 1.0
    stored[5, 2] = 0.5

    metrics = np.zeros((horizon, len(TRACE_FIELDS)), dtype=np.float64)
    qos = np.asarray((0.0, 0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 3.0))
    throughput = np.asarray((0.0, 0.0, 8.0, 0.0, 16.0, 0.0, 0.0, 24.0))
    metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")] = qos
    metrics[:, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")] = throughput
    diagnostics = {
        "mode_before": mode_before,
        "mode": mode,
        "entry": entry,
        "exit": exit_,
        "charger_input_wh": charger,
        "signed_stored_energy_delta_wh": stored,
    }
    return diagnostics, metrics


def test_first_positive_gain_exit_uses_time_then_member_and_real_window_units():
    diagnostics, metrics = _fixture()
    result = recovery_opportunity_summary(
        diagnostics, metrics, time_step_seconds=2.0, window_steps=4
    )
    anchor = result["first_qualifying_exit_anchor"]
    assert anchor["anchor_step"] == 2
    assert anchor["member"] == 0  # simultaneous member-1 exit loses the fixed tie
    assert anchor["actual_window_steps"] == 4
    assert anchor["time_remaining_steps"] == 6
    assert anchor["input_through_exit_wh"] == 2.0
    assert anchor["signed_stored_gain_from_first_input_through_exit_wh"] == 1.5
    assert anchor["window_cumulative_qos"] == 3.0
    assert anchor["window_delivered_megabits"] == 48.0
    assert anchor["window_delivered_megabytes"] == 6.0
    assert anchor["window_positive_service_steps"] == 2
    assert anchor["service_immediately_before_exit"] is False
    assert anchor["positive_service_on_exit_transition"] is True
    assert anchor["new_positive_service_after_exit"] is True
    assert anchor["first_positive_service_after_exit_offset"] == 2
    assert anchor["feedback_reentry_in_window"] is True
    assert anchor["first_feedback_reentry"] == {"offset": 2, "member": 0}
    assert anchor["window_zero_service_intervals"] == [
        {"start_offset": 1, "stop_offset": 2, "actual_steps": 1, "right_censored": False},
        {"start_offset": 3, "stop_offset": 4, "actual_steps": 1, "right_censored": True},
    ]


def test_opportunity_denominators_retain_no_input_and_censored_intervals():
    diagnostics, metrics = _fixture()
    result = recovery_opportunity_summary(
        diagnostics, metrics, time_step_seconds=1.0, window_steps=7
    )
    assert result["denominators"] == {
        "feedback_activation_intervals": 4,
        "feedback_mode_uav_steps": 12,
        "intervals_with_charger_input": 3,
        "qualifying_positive_gain_exits": 2,
        "intervals_without_charger_input": 1,
        "input_intervals_without_qualifying_exit": 1,
        "completed_input_intervals_without_positive_gain": 0,
        "right_censored_intervals": 2,
        "qualifying_anchors_with_insufficient_residual_window": 1,
        "selected_anchor_actual_window_steps": 6,
        "selected_anchor_planned_window_steps": 7,
        "selected_anchor_positive_service_steps": 3,
        "selected_anchor_zero_service_steps": 3,
        "selected_anchor_with_feedback_reentry": 1,
    }
    censored = [row for row in result["intervals"] if row["right_censored"]]
    assert {(row["member"], row["start_step"]) for row in censored} == {(0, 4), (2, 4)}
    aggregate = aggregate_opportunity_summaries([result, result])
    assert aggregate["worlds"] == 2
    assert aggregate["worlds_with_qualifying_anchor"] == 2
    assert aggregate["right_censored_intervals"] == 4


def test_anchor_reentry_ignores_other_members_first_activation():
    diagnostics, metrics = _fixture()
    diagnostics["entry"][4, 0] = False
    diagnostics["mode"][4:, 0] = False
    diagnostics["mode_before"][5:, 0] = False
    result = recovery_opportunity_summary(
        diagnostics, metrics, time_step_seconds=1.0, window_steps=4
    )
    anchor = result["first_qualifying_exit_anchor"]
    assert diagnostics["entry"][4, 2]
    assert anchor["member"] == 0
    assert anchor["feedback_reentry_in_window"] is False
    assert anchor["first_feedback_reentry"] is None
    assert result["denominators"]["selected_anchor_with_feedback_reentry"] == 0


def test_nonfinite_time_step_is_rejected():
    diagnostics, metrics = _fixture()
    with pytest.raises(ValueError, match="timestep inputs"):
        recovery_opportunity_summary(
            diagnostics, metrics, time_step_seconds=np.nan, window_steps=4
        )


def test_step_zero_anchor_marks_pre_exit_service_unknown_and_caps_real_end():
    horizon, members = 2, 1
    diagnostics = {
        "mode_before": np.asarray(((True,), (False,))),
        "mode": np.zeros((horizon, members), dtype=bool),
        "entry": np.zeros((horizon, members), dtype=bool),
        "exit": np.asarray(((True,), (False,))),
        "charger_input_wh": np.asarray(((1.0,), (0.0,))),
        "signed_stored_energy_delta_wh": np.asarray(((0.25,), (0.0,))),
    }
    metrics = np.zeros((horizon, len(TRACE_FIELDS)), dtype=np.float64)
    result = recovery_opportunity_summary(
        diagnostics, metrics, time_step_seconds=1.0, window_steps=250
    )
    anchor = result["first_qualifying_exit_anchor"]
    assert anchor["anchor_step"] == 0
    assert anchor["service_immediately_before_exit"] is None
    assert anchor["actual_window_steps"] == 2
    assert result["denominators"]["qualifying_anchors_with_insufficient_residual_window"] == 1
