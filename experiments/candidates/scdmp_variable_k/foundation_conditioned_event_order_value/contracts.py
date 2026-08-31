"""Typed, result-blind contracts for the SCDMP FCEOV gate.

The module contains only direct values and equality checks.  In particular it
does not manufacture run identity or authorize work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
import math
import struct
from types import MappingProxyType
from typing import Final, Mapping, Sequence

from ..target_bound_competent_controller_order_value.config import (
    ACTIONS as _REGISTERED_ACTIONS,
)


class ContractError(ValueError):
    """A value differs from the frozen FCEOV observable."""


HOST: Final[str] = "QUAD-UAV-PALLET-GANTRY-24P5M-v1"
MANIFEST_SCHEMA: Final[str] = "SCDMP_FCEOV_MANIFEST_V2"
TICK_SECONDS: Final[float] = 0.1
HORIZON_TICKS: Final[int] = 364
K_TARGET: Final[int] = 13
FOUNDATION_UPDATES: Final[int] = 160
CHECKPOINT_UPDATE: Final[int] = FOUNDATION_UPDATES
EPISODES_PER_UPDATE: Final[int] = 12
COMPETENCE_EPISODES: Final[int] = 120
TAPE_COUNT: Final[int] = 24
PANEL_WIDTH: Final[int] = 144
FAILURE_LABELS: Final[tuple[str, ...]] = (
    "cable_overload",
    "gantry_contact",
    "attitude_loss",
    "formation_loss",
)

# The old host stores rows as (a,r1,r2,r3,r4).  The FCEOV API exposes the
# science-card shape (a,(r1,r2,r3,r4)) while preserving catalogue order.
ACTIONS: Final[tuple[tuple[int, tuple[int, int, int, int]], ...]] = tuple(
    (row[0], (row[1], row[2], row[3], row[4])) for row in _REGISTERED_ACTIONS
)
COMMON_INDEX: Final[int] = 0
A_HR_INDEX: Final[int] = 10
A_RH_INDEX: Final[int] = 12
CANDIDATE_ACTIONS: Final[Mapping[str, int]] = MappingProxyType({
    "COMMON": COMMON_INDEX,
    "A_HR": A_HR_INDEX,
    "A_RH": A_RH_INDEX,
})
GRAPHS: Final[tuple[str, str]] = ("HR", "RH")
GRAPH_Q: Final[Mapping[str, int]] = MappingProxyType({"HR": 1, "RH": 0})
GRAPH_ASSIGNMENT: Final[Mapping[str, tuple[int, int, int, int]]] = MappingProxyType({
    "HR": (4, 2, 1, 3),
    "RH": (1, 4, 2, 3),
})
GRAPH_EVENTS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "HR": ("HOOK_HANDOFF", "FORMATION_ROTATE"),
    "RH": ("FORMATION_ROTATE", "HOOK_HANDOFF"),
})

RESOURCE_MAXIMA: Final[Mapping[str, int]] = MappingProxyType({
    "episodes_rollouts": 2_184,
    "primitive_slots": 794_976,
    "adamw_steps": 1_920,
    "checkpoints": 1,
    "forced_actions": 144,
    "foundation_queries": 61_008,
})


class Graph(str, Enum):
    HR = "HR"
    RH = "RH"


class Disposition(str, Enum):
    ESTABLISHED = "TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED"
    CLOSED = "TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED"
    FOUNDATION_NONPASS = "FOUNDATION_COMPETENCE_NOT_ESTABLISHED"


@dataclass(frozen=True, slots=True)
class PublicClaimState:
    """The implementation's explicit reachable public Dirac-state assumption."""

    x: float = 0.0
    v: float = 0.015
    y: float = 0.0
    w: float = 0.0
    phi: float = 0.0
    omega: float = 0.0
    z: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    formation: float = 0.0
    prior_a: int = 1
    prior_load_share: tuple[int, int, int, int] = (0, 0, 0, 0)
    tick: int = 0
    k: int = K_TARGET

    def observation(self) -> tuple[float, ...]:
        return (
            self.x / 24.5,
            self.v / 1.6,
            self.y / 0.40,
            self.w / 0.25,
            self.phi / 0.35,
            self.omega / 0.40,
            *(item / 0.25 for item in self.z),
            self.formation / 0.40,
            self.prior_a / 2.0,
            *self.prior_load_share,
            self.k / 13.0,
            self.tick / 364.0,
        )

    def observation_bytes(self) -> bytes:
        return struct.pack("<18d", *self.observation())


def fixed_claim_state() -> PublicClaimState:
    """Return the manifest-bound reachable public claim state."""

    return PublicClaimState()


def _public_bytes(value: PublicClaimState | bytes | Sequence[float]) -> bytes:
    if isinstance(value, PublicClaimState):
        return value.observation_bytes()
    if isinstance(value, bytes):
        if len(value) != 18 * 8:
            raise ContractError("public observation bytes must encode exactly 18 float64 values")
        return value
    raw = tuple(value)
    if len(raw) != 18 or any(
        isinstance(item, bool) or not isinstance(item, (int, float)) for item in raw
    ):
        raise ContractError("public observation must contain 18 real values")
    row = tuple(float(item) for item in raw)
    if any(not math.isfinite(item) for item in row):
        raise ContractError("public observation must contain 18 finite values")
    return struct.pack("<18d", *row)


def validate_state_alias(
    hr: PublicClaimState | bytes | Sequence[float],
    rh: PublicClaimState | bytes | Sequence[float],
) -> bool:
    """Require byte-identical public first-renewal observations."""

    if _public_bytes(hr) != _public_bytes(rh):
        raise ContractError("HR/RH public first-renewal observations are not byte-identical")
    return True


@dataclass(frozen=True, slots=True)
class Manifest:
    schema: str = MANIFEST_SCHEMA
    host: str = HOST
    tick_seconds: float = TICK_SECONDS
    horizon_ticks: int = HORIZON_TICKS
    external_k: int = K_TARGET
    foundation_updates: int = FOUNDATION_UPDATES
    checkpoint_update: int = CHECKPOINT_UPDATE
    result_phase: str = "FOUNDATION_AND_2X3"
    production_status: str = "SCIENTIFIC_INFERENCE_HOLD"
    master_contract: tuple[str, ...] = (
        "one OS-cryptographic 32-byte master after preflight and fresh-root creation",
        "create-only raw persistence; reload unchanged; no seed selection, redraw, or retry",
        "checkpoint V2 binds the same raw master at completed update 160",
    )
    episodes_per_update: int = EPISODES_PER_UPDATE
    competence_episodes: int = COMPETENCE_EPISODES
    tapes: int = TAPE_COUNT
    panel_width: int = PANEL_WIDTH
    actions: tuple[int, int, int] = (COMMON_INDEX, A_HR_INDEX, A_RH_INDEX)
    candidate_actions: tuple[tuple[str, int, tuple[int, tuple[int, int, int, int]]], ...] = (
        ("COMMON", COMMON_INDEX, (1, (0, 0, 0, 0))),
        ("A_HR", A_HR_INDEX, (2, (1, -1, 0, 0))),
        ("A_RH", A_RH_INDEX, (2, (0, 0, 1, -1))),
    )
    product_initialization: tuple[str, ...] = (
        "Uv,Uy,Uphi iid Uniform[0,1)", "v=0.03*Uv", "y=0.02*Uy-0.01",
        "phi=0.02*Uphi-0.01", "x=w=omega=z_1:4=f=0",
        "prior_action=1", "prior_load_share_1:4=0", "n=0",
    )
    claim_state: tuple[tuple[str, object], ...] = (
        ("x", 0.0), ("v", 0.015), ("y", 0.0), ("w", 0.0), ("phi", 0.0),
        ("omega", 0.0), ("z", (0.0, 0.0, 0.0, 0.0)), ("formation", 0.0),
        ("prior_a", 1), ("prior_load_share", (0, 0, 0, 0)), ("tick", 0), ("k", 13),
    )
    graph_contract: tuple[tuple[str, tuple[str, str], tuple[int, int, int, int], int], ...] = (
        ("HR", ("HOOK_HANDOFF", "FORMATION_ROTATE"), (4, 2, 1, 3), 1),
        ("RH", ("FORMATION_ROTATE", "HOOK_HANDOFF"), (1, 4, 2, 3), 0),
    )
    competence_contract: tuple[tuple[str, object], ...] = (
        ("family_size", 7), ("alpha", 0.05 / 7.0),
        ("graph_lower_strict", 0.72), ("pooled_lower_strict", 0.84),
        ("failure_upper_strict", 0.10),
    )
    contrast_contract: tuple[str, ...] = (
        "d_0m=mu_RH_A_RH-mu_RH_A_HR", "d_1m=mu_HR_A_HR-mu_HR_A_RH",
        "d_0c=mu_RH_A_RH-mu_RH_COMMON", "d_1c=mu_HR_A_HR-mu_HR_COMMON",
        "I=0.5*(d_0m+d_1m)",
        "V_A=min(0.5*d_0m,0.5*d_1m,0.5*(d_0c+d_1c))",
    )
    inference_contract: tuple[tuple[str, object], ...] = (
        ("blocks", 24), ("family_size", 4), ("family_alpha", 0.05),
        ("one_sided_alpha", 0.05 / 4.0), ("df", 23),
        ("reduction", "float64_fsum"), ("zero_variance", "lower_equals_mean"),
        ("branch", "all_four_adjusted_lower_bounds_strictly_positive"),
    )
    rng_contract: tuple[str, ...] = (
        "foundation-initialization:uniform24:(tensor_name,flat_index)",
        "foundation-training-initial-state:uniform53:(update,pair,component)",
        "foundation-training-disturbance:fair-bit:(update,pair,tick,component)",
        "foundation-training-categorical:uniform24:(update,episode,renewal)",
        "foundation-minibatch:epoch-keyed:(update,epoch)",
        "foundation-competence-initialization:uniform53:(graph,graph_mission,component)",
        "foundation-competence-disturbance:fair-bit:(graph,graph_mission,tick,component)",
        "assay-disturbance:fair-bit:(tape,tick,component)",
    )
    endpoint: str = "U=1[safe_dock]*(1-dock_tick/364); failure_or_timeout=0"
    resource_maxima: tuple[tuple[str, int], ...] = tuple(RESOURCE_MAXIMA.items())
    source_modules: tuple[str, ...] = (
        "__init__", "__main__", "contracts", "rng", "foundation", "training", "host_bridge", "panel",
        "clock_controls", "analysis", "lifecycle", "artifacts", "source_manifest", "runner",
    )
    allowed_dependencies: tuple[str, ...] = (
        "target_bound_competent_controller_order_value.config:ACTIONS,FORMATION_ROTATE,HOOK_HANDOFF",
        "target_bound_competent_controller_order_value.host_types:HostOutput,RenewalLane,ResetLane",
        "target_bound_competent_controller_order_value.native_backend:NativeBatch,test_only_primitive,test_only_setup_composition",
    )
    forbidden_dependencies: tuple[str, ...] = (
        "target_bound_competent_controller_order_value.opportunity",
        "target_bound_competent_controller_order_value.production",
        "target_bound_competent_controller_order_value.lifecycle",
        "target_bound_competent_controller_order_value.rng",
        "target_bound_competent_controller_order_value.result",
        "target_bound_competent_controller_order_value.production_services",
        "target_bound_competent_controller_order_value.lease",
        "target_bound_competent_controller_order_value.empirical_contract",
        "target_bound_competent_controller_order_value.evaluation",
        "target_bound_competent_controller_order_value.inference",
        "target_bound_competent_controller_order_value.runner",
        "target_bound_competent_controller_order_value.artifacts",
        "target_bound_competent_controller_order_value.source_manifest",
    )

    def validate(self) -> None:
        if self != Manifest():
            raise ContractError("manifest differs from the frozen FCEOV contract")

    def to_dict(self) -> dict[str, object]:
        value = json.loads(json.dumps(asdict(self), allow_nan=False))
        value["resource_maxima"] = dict(self.resource_maxima)
        return value


def validate_resource_request(observed: Mapping[str, int]) -> None:
    if set(observed) != set(RESOURCE_MAXIMA):
        raise ContractError("resource inventory fields differ")
    for name, maximum in RESOURCE_MAXIMA.items():
        value = observed[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
            raise ContractError(f"resource ceiling exceeded or invalid: {name}")


@dataclass(frozen=True, slots=True)
class FoundationGate:
    complete: bool
    passed: bool
    graph_lower_bounds: tuple[tuple[str, float], ...]
    pooled_lower_bound: float
    failure_upper_bounds: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class PanelCell:
    tape: int
    graph: str
    action_name: str
    action_index: int
    terminal: bool
    safe_dock: bool
    dock_tick: int | None
    failures: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TerminalFact:
    schema: str
    disposition: str
    foundation_gate: FoundationGate
    panel_complete: bool
    adjusted_lower_bounds: tuple[tuple[str, float], ...] = ()


if ACTIONS[COMMON_INDEX] != (1, (0, 0, 0, 0)):
    raise RuntimeError("registered COMMON catalogue action drifted")
if ACTIONS[A_HR_INDEX] != (2, (1, -1, 0, 0)):
    raise RuntimeError("registered A_HR catalogue action drifted")
if ACTIONS[A_RH_INDEX] != (2, (0, 0, 1, -1)):
    raise RuntimeError("registered A_RH catalogue action drifted")
if PANEL_WIDTH != TAPE_COUNT * len(GRAPHS) * len(CANDIDATE_ACTIONS):
    raise RuntimeError("FCEOV native panel width drifted")


__all__ = [
    "ACTIONS", "A_HR_INDEX", "A_RH_INDEX", "CANDIDATE_ACTIONS", "CHECKPOINT_UPDATE", "COMMON_INDEX",
    "COMPETENCE_EPISODES", "ContractError", "Disposition", "EPISODES_PER_UPDATE",
    "FAILURE_LABELS", "FOUNDATION_UPDATES", "FoundationGate", "GRAPH_ASSIGNMENT",
    "GRAPH_EVENTS", "GRAPH_Q", "GRAPHS", "Graph", "HORIZON_TICKS", "HOST",
    "K_TARGET", "MANIFEST_SCHEMA", "Manifest", "PANEL_WIDTH", "PanelCell", "PublicClaimState",
    "RESOURCE_MAXIMA", "TAPE_COUNT", "TICK_SECONDS",
    "TerminalFact", "fixed_claim_state", "validate_resource_request", "validate_state_alias",
]
