"""Current-information controller ownership for UAV source-identifiability G0."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process.uav_episode_schema import (
    GROUND_USERS,
    PHYSICAL_UAVS,
    SERVICE_TARGET,
    Control,
    G0RealizationError,
    _readonly_array,
)
from ha_ctse_process.uav_g0_geometry import (
    FIXED_ALTITUDE_M,
    G0EpisodeSource,
    HOTSPOT_COUNT,
    SOURCE_ID,
    TARGET_LABELS,
    TargetKind,
    TargetLabel,
    USERS_PER_HOTSPOT,
    _finite_array,
)
from ha_ctse_process.uav_g0_statistics import weakest_hotspot_service_row


@dataclass(frozen=True)
class AnonymousLifecycleRow:
    """One current roster row; ``handle`` is opaque state ownership only."""

    handle: str
    position: np.ndarray
    velocity: np.ndarray
    active: bool
    service_available: bool

    def __post_init__(self) -> None:
        if not str(self.handle):
            raise G0RealizationError("lifecycle handle must be nonempty")
        position = _finite_array(self.position, (3,), label="lifecycle position")
        velocity = _finite_array(self.velocity, (3,), label="lifecycle velocity")
        if bool(self.active) != bool(self.service_available):
            raise G0RealizationError("active roster and service availability differ")
        object.__setattr__(self, "position", _readonly_array(position, dtype=np.float64))
        object.__setattr__(self, "velocity", _readonly_array(velocity, dtype=np.float64))

    @property
    def anonymous_tie_key(self) -> tuple[float, ...]:
        return tuple(float(value) for value in np.concatenate((self.position, self.velocity)))


@dataclass(frozen=True)
class G0CurrentInformation:
    """Exact current-only observation boundary shared by S and N controls."""

    rows: tuple[AnonymousLifecycleRow, ...]
    user_demand_mbps: np.ndarray
    user_delivered_rate_mbps: np.ndarray
    channel_association: np.ndarray
    base_xy: np.ndarray
    primary_xy: np.ndarray
    gate_xy: np.ndarray
    stage_xy: np.ndarray

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        _roster_by_handle(rows)
        arrays = (
            ("user_demand_mbps", self.user_demand_mbps, (GROUND_USERS,), np.float64),
            ("user_delivered_rate_mbps", self.user_delivered_rate_mbps, (GROUND_USERS,), np.float64),
            ("channel_association", self.channel_association, (PHYSICAL_UAVS, GROUND_USERS), np.bool_),
            ("base_xy", self.base_xy, (2,), np.float64),
            ("primary_xy", self.primary_xy, (6, 2), np.float64),
            ("gate_xy", self.gate_xy, (6, 2), np.float64),
            ("stage_xy", self.stage_xy, (2, 2), np.float64),
        )
        for name, value, shape, dtype in arrays:
            array = np.asarray(value, dtype=dtype)
            if array.shape != shape or (
                dtype is not np.bool_ and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"current-information {name} is malformed")
            if dtype is not np.bool_ and np.any(array < 0.0) and name in {
                "user_demand_mbps",
                "user_delivered_rate_mbps",
            }:
                raise G0RealizationError(f"current-information {name} is negative")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))
        object.__setattr__(self, "rows", rows)

    @property
    def weakest_hotspot_service(self) -> float:
        return weakest_hotspot_service_row(
            self.user_delivered_rate_mbps,
            np.repeat(np.arange(HOTSPOT_COUNT), USERS_PER_HOTSPOT),
        )


@dataclass(frozen=True)
class G0ControllerGeometry:
    """Static world geometry with no event, slot, user, or RNG authority."""

    base_xy: np.ndarray
    primary_xy: np.ndarray
    gate_xy: np.ndarray
    stage_xy: np.ndarray

    def __post_init__(self) -> None:
        for name, value, shape in (
            ("base_xy", self.base_xy, (2,)),
            ("primary_xy", self.primary_xy, (6, 2)),
            ("gate_xy", self.gate_xy, (6, 2)),
            ("stage_xy", self.stage_xy, (2, 2)),
        ):
            array = _finite_array(value, shape, label=f"controller {name}")
            object.__setattr__(self, name, _readonly_array(array, dtype=np.float64))

    @classmethod
    def from_source(cls, source: G0EpisodeSource) -> "G0ControllerGeometry":
        return cls(
            base_xy=source.geometry.base_xy,
            primary_xy=source.geometry.target_xy[:6],
            gate_xy=source.geometry.gate_xy,
            stage_xy=source.geometry.target_xy[6:],
        )

    def coordinate(self, label: TargetLabel | str) -> np.ndarray:
        parsed = label if isinstance(label, TargetLabel) else TargetLabel.parse(label)
        index = TARGET_LABELS.index(parsed)
        values = self.primary_xy if index < 6 else self.stage_xy
        return values[index if index < 6 else index - 6]

    def gate(self, label: TargetLabel | str) -> np.ndarray:
        parsed = label if isinstance(label, TargetLabel) else TargetLabel.parse(label)
        if parsed.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("only primary targets own holding gates")
        return self.gate_xy[TARGET_LABELS.index(parsed)]


def make_current_information(
    source: G0EpisodeSource,
    *,
    rows: Sequence[AnonymousLifecycleRow],
    user_demand_mbps: Sequence[float],
    user_delivered_rate_mbps: Sequence[float],
    channel_association: np.ndarray,
) -> G0CurrentInformation:
    return G0CurrentInformation(
        rows=tuple(rows),
        user_demand_mbps=np.asarray(user_demand_mbps, dtype=np.float64),
        user_delivered_rate_mbps=np.asarray(
            user_delivered_rate_mbps, dtype=np.float64
        ),
        channel_association=np.asarray(channel_association, dtype=np.bool_),
        base_xy=source.geometry.base_xy,
        primary_xy=source.geometry.target_xy[:6],
        gate_xy=source.geometry.gate_xy,
        stage_xy=source.geometry.target_xy[6:],
    )


def _current_roster(
    geometry: G0ControllerGeometry,
    information: G0CurrentInformation,
) -> dict[str, AnonymousLifecycleRow]:
    """Validate the complete frozen current-information envelope."""

    if not isinstance(information, G0CurrentInformation):
        raise G0RealizationError("controller requires the frozen current-information envelope")
    expected = (
        (information.base_xy, geometry.base_xy),
        (information.primary_xy, geometry.primary_xy),
        (information.gate_xy, geometry.gate_xy),
        (information.stage_xy, geometry.stage_xy),
    )
    if any(not np.array_equal(actual, frozen) for actual, frozen in expected):
        raise G0RealizationError("current-information geometry differs from the episode source")
    return _roster_by_handle(information.rows)


def initial_lifecycle_handles(source: G0EpisodeSource) -> tuple[str, ...]:
    """Create opaque handles without exposing target or physical-slot identity."""

    return tuple(
        hashlib.sha256(
            f"{SOURCE_ID}|{source.geometry.episode_id}|lifecycle|{rank}".encode("utf-8")
        ).hexdigest()[:24]
        for rank in range(PHYSICAL_UAVS)
    )


def replacement_lifecycle_handle(source: G0EpisodeSource, previous: str) -> str:
    return hashlib.sha256(
        f"{SOURCE_ID}|{source.geometry.episode_id}|rejoin|{previous}".encode("utf-8")
    ).hexdigest()[:24]


def _initial_ownership(
    source: G0EpisodeSource, handles: Sequence[str]
) -> dict[str, TargetLabel]:
    if len(handles) != PHYSICAL_UAVS or len(set(handles)) != PHYSICAL_UAVS:
        raise G0RealizationError("initial lifecycle handle inventory mismatch")
    return {
        str(handle): TargetLabel.parse(target)
        for handle, target in zip(handles, source.assignment.row_to_target)
    }


def _roster_by_handle(rows: Sequence[AnonymousLifecycleRow]) -> dict[str, AnonymousLifecycleRow]:
    values = {row.handle: row for row in rows}
    if len(values) != len(rows):
        raise G0RealizationError("current roster contains a duplicate opaque handle")
    if len(rows) != PHYSICAL_UAVS:
        raise G0RealizationError("physical roster must retain all eight storage rows")
    return values


class SameInformationController:
    """Frozen current-information reallocation state machine.

    The event ledger is intentionally absent from this interface.  LEAVE and
    REJOIN arrive as current boundary events; target choice uses only current
    anonymous physical content and registered geometry.
    """

    name = Control.SAME_INFORMATION.value
    uses_future_ledger = False
    trains = False

    def __init__(self, source: G0EpisodeSource, handles: Sequence[str]) -> None:
        self.geometry = G0ControllerGeometry.from_source(source)
        self.ownership = _initial_ownership(source, handles)
        self.original_ownership = dict(self.ownership)
        self._selected_reserve: str | None = None
        self._vacant_primary: TargetLabel | None = None
        self._selected_stage: TargetLabel | None = None
        self._absent_handle: str | None = None
        self._rejoined_handle: str | None = None
        self._rejoin_step: int | None = None
        self._complete_primary_steps = 0
        self._last_primary_step: int | None = None
        self._reserve_at_gate = False
        self._returned_to_stage = False

    def on_leave(
        self,
        absent_handle: str,
        rows: Sequence[AnonymousLifecycleRow],
    ) -> None:
        roster = _roster_by_handle(rows)
        if self._selected_reserve is not None:
            raise G0RealizationError("same-information controller observed a second leave")
        if absent_handle not in self.ownership or roster[absent_handle].active:
            raise G0RealizationError("leave boundary did not expose one inactive lifecycle")
        if sum(row.active for row in rows) != 7:
            raise G0RealizationError("first leave boundary does not have active count seven")
        vacant = self.ownership[absent_handle]
        if vacant.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("leave did not vacate exactly one primary")
        reserve_handles = [
            handle
            for handle, label in self.ownership.items()
            if label.kind is TargetKind.STAGE and roster[handle].active
        ]
        if len(reserve_handles) != 2:
            raise G0RealizationError("same-information leave does not expose two reserves")
        vacancy = self.geometry.coordinate(vacant)

        def rank(handle: str) -> tuple[float, ...]:
            row = roster[handle]
            stage = self.ownership[handle]
            stage_xy = self.geometry.coordinate(stage)
            distance = float(np.sum((row.position[:2] - vacancy) ** 2))
            return (
                distance,
                float(row.position[0]),
                float(row.position[1]),
                float(row.velocity[0]),
                float(row.velocity[1]),
                float(stage_xy[0]),
                float(stage_xy[1]),
            )

        selected = min(reserve_handles, key=rank)
        self._selected_reserve = selected
        self._selected_stage = self.ownership[selected]
        self._vacant_primary = vacant
        self._absent_handle = absent_handle
        self.ownership[selected] = vacant

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        if (
            self._selected_reserve is None
            or self._vacant_primary is None
            or previous_handle != self._absent_handle
            or previous_handle not in self.ownership
            or new_handle in self.ownership
        ):
            raise G0RealizationError("same-information rejoin ownership mismatch")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._vacant_primary
        self._rejoined_handle = new_handle
        self._rejoin_step = int(physical_step)
        if self._selected_stage is None:
            raise G0RealizationError("same-information selected stage is missing")
        self.ownership[self._selected_reserve] = self._selected_stage
        self._reserve_at_gate = True

    def target_map(
        self,
        information: G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        roster = _current_roster(self.geometry, information)
        weakest_hotspot_service = information.weakest_hotspot_service
        if not math.isfinite(float(weakest_hotspot_service)):
            raise G0RealizationError("same-information service input is nonfinite")
        if self._rejoined_handle is not None:
            if self._rejoin_step is None or self._vacant_primary is None:
                raise G0RealizationError("same-information rejoin state is incomplete")
            row = roster[self._rejoined_handle]
            owns_vacant_primary = bool(
                self.ownership.get(self._rejoined_handle) == self._vacant_primary
            )
            active_in_completed_previous_step = bool(
                self._last_primary_step == int(physical_step) - 1
            )
            if (
                int(physical_step) >= self._rejoin_step + 1
                and row.active
                and owns_vacant_primary
                and active_in_completed_previous_step
            ):
                self._complete_primary_steps += 1
            if row.active and owns_vacant_primary:
                self._last_primary_step = int(physical_step)
            ready = bool(
                int(physical_step) >= self._rejoin_step + 1
                and self._complete_primary_steps >= 1
                and float(weakest_hotspot_service) >= SERVICE_TARGET
            )
            if ready and not self._returned_to_stage:
                if self._selected_reserve is None or self._selected_stage is None:
                    raise G0RealizationError("same-information return state is incomplete")
                self._reserve_at_gate = False
                self._returned_to_stage = True
        result: dict[str, np.ndarray] = {}
        for handle, label in self.ownership.items():
            if handle not in roster:
                continue
            if handle == self._selected_reserve and self._reserve_at_gate:
                if self._vacant_primary is None:
                    raise G0RealizationError("same-information gate owner is missing")
                xy = self.geometry.gate(self._vacant_primary)
            else:
                xy = self.geometry.coordinate(label)
            result[handle] = np.concatenate((xy, np.asarray((FIXED_ALTITUDE_M,))))
        return result

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "future_event_field_read_count": 0,
            "future_channel_read_count": 0,
            "future_service_read_count": 0,
            "physical_slot_decision_read_count": 0,
            "epoch_decision_read_count": 0,
            "selected_reserve": self._selected_reserve,
            "vacant_primary": self._vacant_primary.key if self._vacant_primary else None,
            "reserve_at_gate": self._reserve_at_gate,
            "returned_to_stage": self._returned_to_stage,
        }


class NoReallocationController:
    """Same observation boundary with target ownership frozen through LEAVE."""

    name = Control.NO_REALLOCATION.value
    uses_future_ledger = False
    trains = False

    def __init__(self, source: G0EpisodeSource, handles: Sequence[str]) -> None:
        self.geometry = G0ControllerGeometry.from_source(source)
        self.ownership = _initial_ownership(source, handles)
        self._absent_handle: str | None = None
        self._vacant_primary: TargetLabel | None = None

    def on_leave(
        self, absent_handle: str, rows: Sequence[AnonymousLifecycleRow]
    ) -> None:
        roster = _roster_by_handle(rows)
        if sum(row.active for row in rows) != 7 or roster[absent_handle].active:
            raise G0RealizationError("no-reallocation leave boundary mismatch")
        vacant = self.ownership.get(absent_handle)
        if vacant is None or vacant.kind is not TargetKind.PRIMARY:
            raise G0RealizationError("no-reallocation did not observe a primary vacancy")
        self._absent_handle = absent_handle
        self._vacant_primary = vacant

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        del physical_step
        if previous_handle != self._absent_handle or new_handle in self.ownership:
            raise G0RealizationError("no-reallocation rejoin ownership mismatch")
        if self._vacant_primary is None:
            raise G0RealizationError("no-reallocation vacancy is missing")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._vacant_primary

    def target_map(
        self,
        information: G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        del physical_step
        roster = _current_roster(self.geometry, information)
        return {
            handle: np.concatenate(
                (self.geometry.coordinate(label), np.asarray((FIXED_ALTITUDE_M,)))
            )
            for handle, label in self.ownership.items()
            if handle in roster
        }

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "target_change_due_to_active_count": 0,
            "target_change_due_to_service_deficit": 0,
            "reserve_reallocation_count": 0,
            "survivor_reallocation_count": 0,
            "physical_slot_decision_read_count": 0,
            "future_event_field_read_count": 0,
        }


def target_map_to_dense(
    *,
    rows: Sequence[AnonymousLifecycleRow],
    target_map: Mapping[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Storage-only projection from opaque ownership to dense physical rows."""

    if len(rows) != PHYSICAL_UAVS:
        raise G0RealizationError("dense target projection requires eight rows")
    targets = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
    active = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
    for storage_row, row in enumerate(rows):
        if row.handle not in target_map:
            raise G0RealizationError("controller target map omitted a lifecycle")
        targets[storage_row] = _finite_array(
            target_map[row.handle], (3,), label="controller target"
        )
        active[storage_row] = bool(row.active)
    return targets, active
