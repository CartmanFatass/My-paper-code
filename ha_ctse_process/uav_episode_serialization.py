"""Canonical wire codec for frozen UAV episode evidence."""

from __future__ import annotations

from dataclasses import fields
from typing import Any, Mapping

import numpy as np

from ha_ctse_process import uav_episode_schema as schema


_NATIVE_ARRAY_KEYS = frozenset({"dtype", "shape", "data_hex"})
_EPISODE_RUN_KEYS = frozenset(item.name for item in fields(schema.EpisodeRunEvidence))
_METRIC_KEYS = frozenset(
    {
        "episode_id",
        "control",
        "cell",
        "onset",
        "duration",
        "J_event",
        "Q_ordinary",
        "M_event",
        "A_control",
        "B_access",
        "C_cat",
    }
)


def _require_exact_keys(value: Any, keys: frozenset[str], *, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"G0 {label} schema mismatch")


def _native_array(value: Any) -> dict[str, Any]:
    array = np.ascontiguousarray(np.asarray(value))
    if array.dtype.hasobject or not array.dtype.isnative:
        raise ValueError("G0 native array must have a non-object native dtype")
    return {
        "dtype": array.dtype.name,
        "shape": [int(item) for item in array.shape],
        "data_hex": array.tobytes(order="C").hex(),
    }


def _array_from_native(value: Any, *, label: str) -> np.ndarray:
    _require_exact_keys(value, _NATIVE_ARRAY_KEYS, label=label)
    try:
        dtype = np.dtype(value["dtype"])
        shape = tuple(int(item) for item in value["shape"])
        raw = bytes.fromhex(value["data_hex"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"G0 {label} native array schema mismatch") from error
    if dtype.hasobject or not dtype.isnative or any(item < 0 for item in shape):
        raise ValueError(f"G0 {label} native array dtype/shape is invalid")
    expected = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
    if len(raw) != expected or value["data_hex"] != raw.hex():
        raise ValueError(f"G0 {label} native array byte count mismatch")
    return np.frombuffer(raw, dtype=dtype).reshape(shape).copy()


def episode_run_to_primitive(run: schema.EpisodeRunEvidence) -> dict[str, Any]:
    value = {
        "episode_id": run.episode_id,
        "control": run.control.value,
        "cell": run.cell.value,
        "metrics": run.metrics.to_primitive(),
        "source_sha256": run.source_sha256,
        **{
            name: _native_array(getattr(run, name))
            for name in schema.EPISODE_RUN_ARRAY_SPECS
        },
        "controller_evidence": dict(run.controller_evidence),
        "target_trace_sha256": run.target_trace_sha256,
        "raw_action_trace_sha256": run.raw_action_trace_sha256,
        "executed_velocity_trace_sha256": run.executed_velocity_trace_sha256,
        "executed_position_trace_sha256": run.executed_position_trace_sha256,
        "service_trace_sha256": run.service_trace_sha256,
        "controller_state_sha256": run.controller_state_sha256,
        "lifecycle_events": [item.to_primitive() for item in run.lifecycle_events],
        "tracker_failures": run.tracker_failures,
        "action_support_violations": run.action_support_violations,
        "ownership_violations": run.ownership_violations,
        "backhaul_guard_blocked_actions": run.backhaul_guard_blocked_actions,
        "oracle_qualification_failures": run.oracle_qualification_failures,
    }
    _require_exact_keys(value, _EPISODE_RUN_KEYS, label="formal episode run")
    return value


def _metrics_from_primitive(value: Any) -> schema.EpisodeMetrics:
    _require_exact_keys(value, _METRIC_KEYS, label="episode metrics")
    return schema.EpisodeMetrics(
        episode_id=int(value["episode_id"]),
        control=value["control"],
        cell=value["cell"],
        onset=int(value["onset"]),
        duration=int(value["duration"]),
        j_event=float(value["J_event"]),
        q_ordinary=float(value["Q_ordinary"]),
        m_event=float(value["M_event"]),
        a_control=float(value["A_control"]),
        b_access=int(value["B_access"]),
        c_cat=int(value["C_cat"]),
    )


def episode_run_from_primitive(value: Any) -> schema.EpisodeRunEvidence:
    _require_exact_keys(value, _EPISODE_RUN_KEYS, label="formal episode run")
    arrays = {
        name: _array_from_native(value[name], label=name)
        for name in schema.EPISODE_RUN_ARRAY_SPECS
    }
    for name, (
        expected_shape,
        expected_dtype,
    ) in schema.EPISODE_RUN_ARRAY_SPECS.items():
        if arrays[name].shape != expected_shape or arrays[name].dtype != expected_dtype:
            raise ValueError(f"G0 {name} registered dtype/shape mismatch")
    return schema.EpisodeRunEvidence(
        episode_id=int(value["episode_id"]),
        control=value["control"],
        cell=value["cell"],
        metrics=_metrics_from_primitive(value["metrics"]),
        source_sha256=value["source_sha256"],
        controller_evidence=value["controller_evidence"],
        lifecycle_events=tuple(
            schema.LifecycleBoundaryEvent(**item) for item in value["lifecycle_events"]
        ),
        target_trace_sha256=value["target_trace_sha256"],
        raw_action_trace_sha256=value["raw_action_trace_sha256"],
        executed_velocity_trace_sha256=value["executed_velocity_trace_sha256"],
        executed_position_trace_sha256=value["executed_position_trace_sha256"],
        service_trace_sha256=value["service_trace_sha256"],
        controller_state_sha256=value["controller_state_sha256"],
        tracker_failures=int(value["tracker_failures"]),
        action_support_violations=int(value["action_support_violations"]),
        ownership_violations=int(value["ownership_violations"]),
        backhaul_guard_blocked_actions=int(value["backhaul_guard_blocked_actions"]),
        oracle_qualification_failures=int(value["oracle_qualification_failures"]),
        **arrays,
    )
