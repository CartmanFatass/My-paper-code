"""Typed materialized inputs and public outputs for the TBCC native host.

These values contain no RNG, empirical identity, model, checkpoint, or result.
They are only the deterministic inputs/outputs of one candidate-local host.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from .config import (
    ACTION_COUNT,
    ALLOWED_K,
    FORMATION_ROTATE,
    HOOK_HANDOFF,
    MAX_HOLD_TICKS,
    TARGET_SWITCH_TICKS,
)


@dataclass(frozen=True, slots=True)
class ResetLane:
    """One materialized, treatment-independent reset lane."""

    middle_events: tuple[int, int]
    k_initial: int
    initial_v: float
    initial_y: float
    initial_phi: float
    k_after: int | None = None
    switch_tick: int | None = None
    active: bool = True

    def validate(self) -> None:
        if self.middle_events not in (
            (HOOK_HANDOFF, FORMATION_ROTATE),
            (FORMATION_ROTATE, HOOK_HANDOFF),
        ):
            raise ValueError("middle_events must be the exact H/R permutation")
        if isinstance(self.k_initial, bool) or self.k_initial not in ALLOWED_K:
            raise ValueError("k_initial must be one of 5, 7, 11, 13")
        after = self.k_initial if self.k_after is None else self.k_after
        if isinstance(after, bool) or after not in ALLOWED_K:
            raise ValueError("k_after must be one of 5, 7, 11, 13")
        if self.switch_tick is None:
            if after != self.k_initial:
                raise ValueError("fixed-k reset must preserve k")
        else:
            if self.switch_tick not in TARGET_SWITCH_TICKS:
                raise ValueError("switch_tick must be 91 or 273")
            if (self.k_initial, after) not in ((7, 13), (13, 7)):
                raise ValueError("switch schedules must be 7->13 or 13->7")
            if self.switch_tick % self.k_initial != 0:
                raise ValueError("switch_tick must be an outgoing-k renewal boundary")
        values = (self.initial_v, self.initial_y, self.initial_phi)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise TypeError("initial public draws must be real scalars")
        if not all(isfinite(float(value)) for value in values):
            raise ValueError("initial public draws must be finite")
        if not 0.0 <= float(self.initial_v) <= 0.03:
            raise ValueError("initial_v is outside the frozen initialization law")
        if not -0.01 <= float(self.initial_y) <= 0.01:
            raise ValueError("initial_y is outside the frozen initialization law")
        if not -0.01 <= float(self.initial_phi) <= 0.01:
            raise ValueError("initial_phi is outside the frozen initialization law")
        if not isinstance(self.active, bool):
            raise TypeError("active must be bool")

    @property
    def resolved_k_after(self) -> int:
        return self.k_initial if self.k_after is None else self.k_after

    @property
    def resolved_switch_tick(self) -> int:
        return 0 if self.switch_tick is None else self.switch_tick


@dataclass(frozen=True, slots=True)
class RenewalLane:
    """One action and a fixed 13-tick disturbance envelope for one lane."""

    action: int
    eta_v: tuple[float, ...]
    eta_y: tuple[float, ...]
    eta_omega: tuple[float, ...]
    active: bool = True

    def validate(self) -> None:
        if isinstance(self.action, bool) or not isinstance(self.action, int):
            raise TypeError("action must be an integer catalogue index")
        if not 0 <= self.action < ACTION_COUNT:
            raise ValueError(f"action must be in [0, {ACTION_COUNT - 1}]")
        for name, values, magnitude in (
            ("eta_v", self.eta_v, 0.003),
            ("eta_y", self.eta_y, 0.002),
            ("eta_omega", self.eta_omega, 0.004),
        ):
            if not isinstance(values, tuple) or len(values) != MAX_HOLD_TICKS:
                raise ValueError(f"{name} must be an exact {MAX_HOLD_TICKS}-tuple")
            if any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in values):
                raise TypeError(f"{name} must contain real scalars")
            if any(not isfinite(float(value)) or abs(float(value)) != magnitude for value in values):
                raise ValueError(f"{name} must contain only the frozen +/-{magnitude} values")
        if not isinstance(self.active, bool):
            raise TypeError("active must be bool")


@dataclass(frozen=True, slots=True)
class HostOutput:
    """One lane snapshot after reset, masking, or one complete external hold."""

    advanced: bool
    active: bool
    terminal: bool
    ticks_advanced: int
    tick: int
    hold_k: int
    next_k: int
    observation: tuple[float, ...]
    safe_dock: bool
    timeout: bool
    cable_overload: bool
    gantry_contact: bool
    attitude_loss: bool
    formation_loss: bool
    cumulative_reward: float
    cumulative_energy: float
    energy_ticks: int
    dock_tick: int | None
    last_hold_reward_count: int = 0
    last_hold_rewards: tuple[float, ...] = (0.0,) * MAX_HOLD_TICKS

    def __post_init__(self) -> None:
        if not 0 <= self.last_hold_reward_count <= MAX_HOLD_TICKS:
            raise ValueError("last_hold_reward_count is outside the native trace capacity")
        if len(self.last_hold_rewards) != MAX_HOLD_TICKS:
            raise ValueError("last_hold_rewards must retain the fixed native trace width")
        if any(not isfinite(value) for value in self.last_hold_rewards):
            raise ValueError("last_hold_rewards must be finite")
        if any(value != 0.0 for value in self.last_hold_rewards[self.last_hold_reward_count :]):
            raise ValueError("inactive native reward-trace tail must be canonical zero")

    @property
    def completion_value(self) -> float:
        if not self.safe_dock or self.dock_tick is None:
            return 0.0
        return 1.0 - self.dock_tick / 364.0

    @property
    def completion_time_seconds(self) -> float:
        return 0.1 * self.dock_tick if self.safe_dock and self.dock_tick is not None else 36.4

    @property
    def mean_active_energy(self) -> float:
        return self.cumulative_energy / self.energy_ticks if self.energy_ticks else 0.0


def constant_disturbance_lane(
    action: int,
    *,
    eta_v: float = 0.003,
    eta_y: float = 0.002,
    eta_omega: float = 0.004,
    active: bool = True,
) -> RenewalLane:
    """Create one deterministic conformance lane, not a stochastic tape."""

    return RenewalLane(
        action=action,
        eta_v=(eta_v,) * MAX_HOLD_TICKS,
        eta_y=(eta_y,) * MAX_HOLD_TICKS,
        eta_omega=(eta_omega,) * MAX_HOLD_TICKS,
        active=active,
    )


def materialize_rows(rows: Iterable[RenewalLane]) -> tuple[RenewalLane, ...]:
    materialized = tuple(rows)
    for row in materialized:
        if not isinstance(row, RenewalLane):
            raise TypeError("renewal rows must be RenewalLane values")
        row.validate()
    return materialized
