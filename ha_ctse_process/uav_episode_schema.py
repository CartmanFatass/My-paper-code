"""Shared frozen schema for UAV G0 episode evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Mapping

import numpy as np


PHYSICAL_HORIZON = 500
PHYSICAL_UAVS = 8
GROUND_USERS = 30
ACTION_DIM = 4
SERVICE_TARGET = 0.90


class G0RealizationError(ValueError):
    """A fail-closed violation of the frozen source realization."""


class Cell(str, Enum):
    EVENT = "UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE"
    NO_EVENT = "NO_EVENT"


class Control(str, Enum):
    ORACLE = "MECHANICALLY_QUALIFIED_ORACLE"
    SAME_INFORMATION = "SAME_INFORMATION_CONSTRUCTIVE"
    NO_REALLOCATION = "NO_REALLOCATION"


def _readonly_array(value: Any, *, dtype: np.dtype[Any] | type | None = None) -> np.ndarray:
    result = np.asarray(value, dtype=dtype).copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class LifecycleBoundaryEvent:
    kind: str
    physical_step: int
    previous_handle: str
    current_handle: str | None
    owner_target: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "physical_step": int(self.physical_step),
            "previous_handle": self.previous_handle,
            "current_handle": self.current_handle,
            "owner_target": self.owner_target,
        }


@dataclass(frozen=True)
class EpisodeMetrics:
    episode_id: int
    control: Control
    cell: Cell
    onset: int
    duration: int
    j_event: float
    q_ordinary: float
    m_event: float
    a_control: float
    b_access: int
    c_cat: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", Control(self.control))
        object.__setattr__(self, "cell", Cell(self.cell))
        values = (
            self.j_event,
            self.q_ordinary,
            self.m_event,
            self.a_control,
        )
        if not all(math.isfinite(float(value)) for value in values):
            raise G0RealizationError("episode metric contains a nonfinite value")
        if self.b_access not in (0, 1) or self.c_cat not in (0, 1):
            raise G0RealizationError("binary episode metric is outside {0,1}")
        if not all(0.0 <= float(value) <= 1.0 for value in values[:3]):
            raise G0RealizationError("J/Q/M metric is outside [0,1]")
        expected_a = (
            min(float(self.j_event) / SERVICE_TARGET, float(self.q_ordinary) / SERVICE_TARGET)
            if self.cell is Cell.EVENT
            else float(self.q_ordinary) / SERVICE_TARGET
        )
        expected_b = int(expected_a >= 1.0)
        if float(self.a_control) != expected_a or int(self.b_access) != expected_b:
            raise G0RealizationError("A/B metrics do not reconstruct from J/Q")
        if self.cell is Cell.NO_EVENT and (
            float(self.j_event) != 1.0 or int(self.c_cat) != 0
        ):
            raise G0RealizationError("NO_EVENT J/C metric law drifted")

    def to_primitive(self) -> dict[str, Any]:
        return {
            "episode_id": int(self.episode_id),
            "control": self.control.value,
            "cell": self.cell.value,
            "onset": int(self.onset),
            "duration": int(self.duration),
            "J_event": float(self.j_event),
            "Q_ordinary": float(self.q_ordinary),
            "M_event": float(self.m_event),
            "A_control": float(self.a_control),
            "B_access": int(self.b_access),
            "C_cat": int(self.c_cat),
        }


EPISODE_RUN_ARRAY_SPECS = {
    "user_demand_input_mbps": (
        (PHYSICAL_HORIZON, GROUND_USERS),
        np.dtype(np.float64),
    ),
    "user_delivered_input_mbps": (
        (PHYSICAL_HORIZON, GROUND_USERS),
        np.dtype(np.float64),
    ),
    "channel_association_input": (
        (PHYSICAL_HORIZON, PHYSICAL_UAVS, GROUND_USERS),
        np.dtype(np.bool_),
    ),
    "delivered_user_rates_mbps": (
        (PHYSICAL_HORIZON, GROUND_USERS),
        np.dtype(np.float64),
    ),
    "target_trace": (
        (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3),
        np.dtype(np.float64),
    ),
    "raw_action_trace": (
        (PHYSICAL_HORIZON, PHYSICAL_UAVS, ACTION_DIM),
        np.dtype(np.float32),
    ),
    "executed_velocity_trace": (
        (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3),
        np.dtype(np.float64),
    ),
    "position_trace": (
        (PHYSICAL_HORIZON + 1, PHYSICAL_UAVS, 3),
        np.dtype(np.float64),
    ),
    "active_mask_trace": (
        (PHYSICAL_HORIZON, PHYSICAL_UAVS),
        np.dtype(np.bool_),
    ),
    "weakest_service": ((PHYSICAL_HORIZON,), np.dtype(np.float64)),
}


@dataclass(frozen=True)
class EpisodeRunEvidence:
    episode_id: int
    control: Control
    cell: Cell
    metrics: EpisodeMetrics
    source_sha256: str
    user_demand_input_mbps: np.ndarray
    user_delivered_input_mbps: np.ndarray
    channel_association_input: np.ndarray
    delivered_user_rates_mbps: np.ndarray
    target_trace: np.ndarray
    raw_action_trace: np.ndarray
    executed_velocity_trace: np.ndarray
    position_trace: np.ndarray
    active_mask_trace: np.ndarray
    controller_evidence: Mapping[str, Any]
    target_trace_sha256: str
    raw_action_trace_sha256: str
    executed_velocity_trace_sha256: str
    executed_position_trace_sha256: str
    service_trace_sha256: str
    controller_state_sha256: str
    lifecycle_events: tuple[LifecycleBoundaryEvent, ...]
    tracker_failures: int
    action_support_violations: int
    ownership_violations: int
    backhaul_guard_blocked_actions: int
    oracle_qualification_failures: int
    weakest_service: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", Control(self.control))
        object.__setattr__(self, "cell", Cell(self.cell))
        for name, (shape, dtype) in EPISODE_RUN_ARRAY_SPECS.items():
            array = np.asarray(getattr(self, name), dtype=dtype)
            if array.shape != shape or (
                dtype != np.dtype(np.bool_) and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"episode run {name} evidence is malformed")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))
        if not isinstance(self.controller_evidence, Mapping):
            raise G0RealizationError("controller evidence is not a mapping")
        object.__setattr__(self, "controller_evidence", dict(self.controller_evidence))
