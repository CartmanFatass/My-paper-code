"""Descriptive recovery-opportunity readings for the fixed B08 comparison."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..b04.evaluation import TRACE_FIELDS


WINDOW_STEPS = 250


def _zero_service_intervals(values: np.ndarray) -> list[dict[str, Any]]:
    zero = np.asarray(values, dtype=np.float64) <= 0.0
    padded = np.concatenate(([False], zero, [False])).astype(np.int8)
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    stops = np.flatnonzero(changes == -1)
    return [
        {
            "start_offset": int(start),
            "stop_offset": int(stop),
            "actual_steps": int(stop - start),
            "right_censored": bool(stop == len(zero)),
        }
        for start, stop in zip(starts, stops, strict=True)
    ]


def recovery_opportunity_summary(
    diagnostics: dict[str, np.ndarray],
    metrics: np.ndarray,
    *,
    time_step_seconds: float,
    window_steps: int = WINDOW_STEPS,
) -> dict[str, Any]:
    """Return the prospectively fixed first qualifying F-exit description.

    An interval begins on an entry decision and ends on the transition whose
    decision exits F.  An interval still active at the native ending is retained
    as right-censored.  Qualification requires charger input and positive signed
    physical stored-energy gain from the first input through the exit, inclusive.
    """

    mode_before = np.asarray(diagnostics["mode_before"], dtype=bool)
    mode = np.asarray(diagnostics["mode"], dtype=bool)
    entered = np.asarray(diagnostics["entry"], dtype=bool)
    exited = np.asarray(diagnostics["exit"], dtype=bool)
    charger_input = np.asarray(diagnostics["charger_input_wh"], dtype=np.float64)
    stored_delta = np.asarray(
        diagnostics["signed_stored_energy_delta_wh"], dtype=np.float64
    )
    metric_array = np.asarray(metrics, dtype=np.float64)
    if mode.ndim != 2 or mode_before.shape != mode.shape:
        raise ValueError("feedback mode arrays must be [time, member]")
    expected = mode.shape
    for name, value in {
        "entry": entered,
        "exit": exited,
        "charger_input_wh": charger_input,
        "signed_stored_energy_delta_wh": stored_delta,
    }.items():
        if value.shape != expected:
            raise ValueError(f"{name} must have shape {expected}")
    if metric_array.shape != (expected[0], len(TRACE_FIELDS)):
        raise ValueError("metrics do not match the fixed B08 trace schema")
    if not np.isfinite(metric_array).all() or not np.isfinite(charger_input).all():
        raise ValueError("opportunity inputs must be finite")
    if (
        not np.isfinite(stored_delta).all()
        or not np.isfinite(time_step_seconds)
        or time_step_seconds <= 0.0
    ):
        raise ValueError("physical energy and timestep inputs must be finite and positive")
    if int(window_steps) <= 0:
        raise ValueError("window_steps must be positive")

    horizon, members = expected
    intervals: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for member in range(members):
        active_start: int | None = None
        active_left_censored = False
        for step in range(horizon):
            if mode_before[step, member] and active_start is None:
                active_start = step
                active_left_censored = True
            if entered[step, member]:
                if active_start is not None and not active_left_censored:
                    raise RuntimeError("feedback interval re-entered before exit")
                active_start = step
                active_left_censored = False
            if mode[step, member] and active_start is None:
                # A trace may begin in F only when a caller slices a live episode.
                active_start = step
            if not exited[step, member]:
                continue
            if not mode_before[step, member] or mode[step, member]:
                raise RuntimeError("exit row is inconsistent with feedback modes")
            if active_start is None:
                raise RuntimeError("feedback exit has no active interval")
            interval_slice = slice(active_start, step + 1)
            input_rows = np.flatnonzero(charger_input[interval_slice, member] > 0.0)
            first_input = (
                active_start + int(input_rows[0]) if input_rows.size else None
            )
            gain = (
                float(stored_delta[first_input : step + 1, member].sum())
                if first_input is not None
                else None
            )
            row = {
                "member": member,
                "start_step": active_start,
                "left_censored": active_left_censored,
                "exit_step": step,
                "right_censored": False,
                "actual_interval_steps": step - active_start + 1,
                "first_input_step": first_input,
                "interval_charger_input_wh": float(
                    charger_input[interval_slice, member].sum()
                ),
                "input_through_exit_wh": (
                    float(charger_input[first_input : step + 1, member].sum())
                    if first_input is not None
                    else 0.0
                ),
                "signed_stored_gain_from_first_input_through_exit_wh": gain,
                "qualifying_positive_gain_exit": bool(
                    first_input is not None and gain is not None and gain > 0.0
                ),
            }
            intervals.append(row)
            if row["qualifying_positive_gain_exit"]:
                candidates.append(row)
            active_start = None
            active_left_censored = False
        if active_start is not None:
            interval_slice = slice(active_start, horizon)
            input_rows = np.flatnonzero(charger_input[interval_slice, member] > 0.0)
            first_input = (
                active_start + int(input_rows[0]) if input_rows.size else None
            )
            intervals.append(
                {
                    "member": member,
                    "start_step": active_start,
                    "left_censored": active_left_censored,
                    "exit_step": None,
                    "right_censored": True,
                    "actual_interval_steps": horizon - active_start,
                    "first_input_step": first_input,
                    "interval_charger_input_wh": float(
                        charger_input[interval_slice, member].sum()
                    ),
                    "input_through_exit_wh": None,
                    "signed_stored_gain_from_first_input_through_exit_wh": None,
                    "qualifying_positive_gain_exit": False,
                }
            )

    candidates.sort(key=lambda row: (row["exit_step"], row["member"]))
    anchor = None
    if candidates:
        selected = candidates[0]
        start = int(selected["exit_step"])
        stop = min(horizon, start + int(window_steps))
        qos = metric_array[:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
        throughput = metric_array[
            :, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")
        ]
        window_qos = qos[start:stop]
        window_throughput = throughput[start:stop]
        positive = np.flatnonzero(window_qos > 0.0)
        later_positive = np.flatnonzero(qos[start + 1 : stop] > 0.0)
        selected_member = int(selected["member"])
        reentries = np.flatnonzero(entered[start + 1 : stop, selected_member])
        anchor = {
            **selected,
            "anchor_step": start,
            "time_remaining_steps": horizon - start,
            "actual_window_steps": stop - start,
            "window_stop_exclusive": stop,
            "window_cumulative_qos": float(window_qos.sum()),
            "window_delivered_megabits": float(
                window_throughput.sum() * float(time_step_seconds)
            ),
            "window_delivered_megabytes": float(
                window_throughput.sum() * float(time_step_seconds) / 8.0
            ),
            "window_positive_service_steps": int(positive.size),
            "window_zero_service_intervals": _zero_service_intervals(window_qos),
            "service_immediately_before_exit": (
                None if start == 0 else bool(qos[start - 1] > 0.0)
            ),
            "positive_service_on_exit_transition": bool(qos[start] > 0.0),
            "new_positive_service_after_exit": bool(later_positive.size),
            "first_positive_service_after_exit_offset": (
                int(later_positive[0]) + 1 if later_positive.size else None
            ),
            "feedback_reentry_in_window": bool(reentries.size),
            "first_feedback_reentry": (
                {
                    "offset": int(reentries[0]) + 1,
                    "member": selected_member,
                }
                if reentries.size
                else None
            ),
        }

    with_input = [row for row in intervals if row["first_input_step"] is not None]
    completed_with_input = [
        row for row in with_input if not row["right_censored"]
    ]
    anchor_steps = int(anchor["actual_window_steps"]) if anchor is not None else 0
    anchor_positive = int(anchor["window_positive_service_steps"]) if anchor is not None else 0
    return {
        "first_qualifying_exit_anchor": anchor,
        "intervals": intervals,
        "denominators": {
            "feedback_activation_intervals": len(intervals),
            "feedback_mode_uav_steps": int(mode.sum()),
            "intervals_with_charger_input": len(with_input),
            "qualifying_positive_gain_exits": len(candidates),
            "intervals_without_charger_input": sum(
                row["first_input_step"] is None for row in intervals
            ),
            "input_intervals_without_qualifying_exit": sum(
                not row["qualifying_positive_gain_exit"] for row in with_input
            ),
            "completed_input_intervals_without_positive_gain": sum(
                not row["qualifying_positive_gain_exit"]
                for row in completed_with_input
            ),
            "right_censored_intervals": sum(
                row["right_censored"] for row in intervals
            ),
            "qualifying_anchors_with_insufficient_residual_window": int(
                anchor is not None
                and int(anchor["actual_window_steps"]) < int(window_steps)
            ),
            "selected_anchor_actual_window_steps": anchor_steps,
            "selected_anchor_planned_window_steps": int(window_steps) if anchor is not None else 0,
            "selected_anchor_positive_service_steps": anchor_positive,
            "selected_anchor_zero_service_steps": anchor_steps - anchor_positive,
            "selected_anchor_with_feedback_reentry": int(
                anchor is not None and anchor["feedback_reentry_in_window"]
            ),
        },
    }


def aggregate_opportunity_summaries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = (
        "feedback_activation_intervals",
        "feedback_mode_uav_steps",
        "intervals_with_charger_input",
        "qualifying_positive_gain_exits",
        "intervals_without_charger_input",
        "input_intervals_without_qualifying_exit",
        "completed_input_intervals_without_positive_gain",
        "right_censored_intervals",
        "qualifying_anchors_with_insufficient_residual_window",
        "selected_anchor_actual_window_steps",
        "selected_anchor_planned_window_steps",
        "selected_anchor_positive_service_steps",
        "selected_anchor_zero_service_steps",
        "selected_anchor_with_feedback_reentry",
    )
    return {
        "worlds": len(rows),
        "worlds_with_feedback_activation": sum(
            row["denominators"]["feedback_activation_intervals"] > 0 for row in rows
        ),
        "worlds_with_qualifying_anchor": sum(
            row["first_qualifying_exit_anchor"] is not None for row in rows
        ),
        **{
            key: int(sum(row["denominators"][key] for row in rows))
            for key in keys
        },
    }
