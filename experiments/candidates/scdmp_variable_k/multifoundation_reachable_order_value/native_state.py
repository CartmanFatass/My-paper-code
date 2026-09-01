"""Typed, result-blind state boundary for MF-RS-MK native rollouts.

The byte payloads are complete native POD snapshots.  They contain plant,
controller-memory, latent assignment, terminal, counter, and cumulative-cost
state, but no RNG or empirical/result identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Callable, Final, Protocol

MAX_BATCH_WIDTH: Final[int] = 144
MAX_HOLD_TICKS: Final[int] = 13
OBSERVATION_WIDTH: Final[int] = 18
HORIZON_TICKS: Final[int] = 364
ACTION_COUNT: Final[int] = 18
ALLOWED_K: Final[frozenset[int]] = frozenset((7, 13))
TARGET_TICKS: Final[frozenset[int]] = frozenset((64, 160, 256))

HR_ASSIGNMENT: Final[tuple[int, int, int, int]] = (4, 2, 1, 3)
RH_ASSIGNMENT: Final[tuple[int, int, int, int]] = (1, 4, 2, 3)


class TapeNamespace(str, Enum):
    SOURCE = "SOURCE"
    DEVELOPMENT = "DEVELOPMENT"
    HELDOUT = "HELDOUT"


@dataclass(frozen=True, slots=True)
class TapeAddress:
    """Address coordinate; namespaces, not byte inequality, define separation."""

    namespace: TapeNamespace
    seed: int
    tape_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, TapeNamespace):
            raise TypeError("tape namespace must be a TapeNamespace")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("tape seed must be an integer coordinate")
        if not isinstance(self.tape_id, str) or not self.tape_id:
            raise ValueError("tape_id must be a nonempty string")


@dataclass(frozen=True, slots=True)
class DisturbanceHold:
    """One pre-materialized, treatment-common 13-tick disturbance row."""

    eta_v: tuple[float, ...]
    eta_y: tuple[float, ...]
    eta_omega: tuple[float, ...]

    def validate(self) -> None:
        for name, values, magnitude in (
            ("eta_v", self.eta_v, 0.003),
            ("eta_y", self.eta_y, 0.002),
            ("eta_omega", self.eta_omega, 0.004),
        ):
            if not isinstance(values, tuple) or len(values) != MAX_HOLD_TICKS:
                raise ValueError(f"{name} must be an exact {MAX_HOLD_TICKS}-tuple")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
                raise TypeError(f"{name} must contain real scalars")
            if any(not isfinite(float(value)) or abs(float(value)) != magnitude for value in values):
                raise ValueError(f"{name} must contain only +/-{magnitude}")


@dataclass(frozen=True, slots=True)
class HostOutput:
    """Public host observation plus endpoint, cost, and count facts."""

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
    last_hold_rewards: tuple[float, ...]

    @property
    def failure(self) -> bool:
        return self.cable_overload or self.gantry_contact or self.attitude_loss or self.formation_loss

    @property
    def completion_value(self) -> float:
        if not self.safe_dock or self.dock_tick is None:
            return 0.0
        return 1.0 - self.dock_tick / HORIZON_TICKS


@dataclass(frozen=True, slots=True)
class NativeState:
    """One validated complete native state and its materialized public view."""

    state_bytes: bytes
    output: HostOutput
    event_phase: str
    event_order: str | None
    latent_assignment: tuple[int, int, int, int]
    latent_q: int


class BatchedPolicy(Protocol):
    """Immutable policy call seam; one action is returned per visible row."""

    def __call__(self, observations: tuple[tuple[float, ...], ...]) -> tuple[int, ...]: ...


@dataclass(frozen=True, slots=True)
class ReachableTwins:
    """One treatment-common reachable source and its HR/RH native clones."""

    state_id: str
    k: int
    target_tick: int
    boundary_tick: int
    source_seed: int
    source_address: TapeAddress
    pre_event_p: tuple[int, int, int, int]
    pre_event_q: int
    source_tape: tuple[DisturbanceHold, ...]
    source_snapshot_bytes: bytes
    hr: NativeState
    rh: NativeState
    hr_public_bytes: bytes
    rh_public_bytes: bytes
    hr_assignment: tuple[int, int, int, int]
    rh_assignment: tuple[int, int, int, int]
    eligible: bool
    selected_tape_index: int
    source_renewal_index: int
    source_scan_receipts: tuple["SourceScanReceipt", ...]
    persistent_twin_bytes_equal: bool
    transitions: int
    policy_queries: int


@dataclass(frozen=True, slots=True)
class BranchEvaluation:
    """Complete native twin-branch execution accounting."""

    outputs: tuple[HostOutput, ...]
    raw_returns: tuple[float, ...]
    costs: tuple[float, ...]
    terminal_counts: dict[str, int]
    width: int
    forced_holds: int
    policy_queries: int
    policy_batch_calls: int
    renewal_steps: int
    transitions: int


@dataclass(frozen=True, slots=True)
class SourceScanReceipt:
    candidate_index: int
    eligible: bool
    renewal_steps: int
    transitions: int
    policy_queries: int
    terminal: bool


def validate_actions(actions: tuple[int, ...], width: int) -> None:
    if len(actions) != width:
        raise ValueError("policy action width differs from active observation width")
    if any(isinstance(action, bool) or not isinstance(action, int) or not 0 <= action < ACTION_COUNT
           for action in actions):
        raise ValueError(f"action must be an integer in [0, {ACTION_COUNT - 1}]")


__all__ = [
    "ACTION_COUNT", "ALLOWED_K", "BatchedPolicy", "BranchEvaluation", "DisturbanceHold",
    "HORIZON_TICKS", "HR_ASSIGNMENT", "HostOutput", "MAX_BATCH_WIDTH", "MAX_HOLD_TICKS",
    "NativeState", "OBSERVATION_WIDTH", "RH_ASSIGNMENT", "ReachableTwins", "SourceScanReceipt", "TARGET_TICKS",
    "TapeAddress", "TapeNamespace", "validate_actions",
]
