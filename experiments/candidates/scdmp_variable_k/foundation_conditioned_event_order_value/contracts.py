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
MANIFEST_SCHEMA: Final[str] = "SCDMP_FCEOV_MANIFEST_V3"
TICK_SECONDS: Final[float] = 0.1
HORIZON_TICKS: Final[int] = 364
K_TARGET: Final[int] = 13
FOUNDATION_UPDATES: Final[int] = 160
CHECKPOINT_UPDATE: Final[int] = FOUNDATION_UPDATES
EPISODES_PER_UPDATE: Final[int] = 12
COMPETENCE_EPISODES: Final[int] = 120
TAPE_COUNT: Final[int] = 562
PANEL_WIDTH: Final[int] = 3_372
PANEL_FULL_SLICE_TAPES: Final[int] = 24
PANEL_FULL_SLICE_COUNT: Final[int] = 23
PANEL_FINAL_SLICE_TAPES: Final[int] = 10
PANEL_SLICE_COUNT: Final[int] = 24
PANEL_MAX_NATIVE_WIDTH: Final[int] = 144
PANEL_FINAL_NATIVE_WIDTH: Final[int] = 60
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
    "episodes_rollouts": 5_412,
    "primitive_slots": 1_969_968,
    "adamw_steps": 1_920,
    "checkpoints": 1,
    "forced_actions": 3_372,
    "foundation_queries": 148_164,
    "panel_slices": 24,
})

RESOURCE_ENVELOPE: Final[Mapping[str, int]] = MappingProxyType({
    "wall_seconds": 300,
    "peak_rss_bytes": 1_073_741_824,
    "scratch_bytes": 67_108_864,
    "durable_bytes": 67_108_864,
    "workers": 1,
    "native_threads": 1,
    "torch_threads": 1,
    "torch_interop_threads": 1,
    "minimum_available_memory_bytes": 4_294_967_296,
})

INFERENCE_ALPHA: Final[float] = 0.05
INFERENCE_MARGIN: Final[float] = 0.0
INFERENCE_CONTINUOUS_Q_STAR: Final[float] = 0.551580065745296
INFERENCE_DISCRETE_Q_FAIL: Final[float] = 0.551579365312785
INFERENCE_FIRST_GAP_RAW_SUM_PASS: Final[int] = 21_046
INFERENCE_COMMON_GAP_RAW_SUM_PASS: Final[int] = 42_091
INFERENCE_PLANNING_GAP: Final[float] = 0.1
INFERENCE_JOINT_POWER_LOWER_BOUND: Final[float] = 0.801021247429385
INFERENCE_N561_JOINT_POWER_LOWER_BOUND: Final[float] = 0.799048262648854


class Graph(str, Enum):
    HR = "HR"
    RH = "RH"


class Disposition(str, Enum):
    ESTABLISHED = "TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED"
    CLOSED = "TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION"
    FOUNDATION_NONPASS = "FOUNDATION_COMPETENCE_NOT_ESTABLISHED"
    INVALID = "INVALID_EVIDENCE"


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
    production_status: str = "READY_GUARDED_RESUMABLE_RESULT"
    master_contract: tuple[str, ...] = (
        "one OS-cryptographic 32-byte master after fresh preflight and resource admission",
        "create-only raw persistence; every resume reloads the same master",
        "no redraw, replacement, seed selection, threshold change, or tape-count change",
        "checkpoint V3 binds the same raw master at completed update 160",
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
        ("tapes", 562),
        ("component_names", ("g_A_RH", "g_A_HR", "g_COMMON")),
        ("g_A_RH", "0.5*d_1m"),
        ("g_A_HR", "0.5*d_0m"),
        ("g_COMMON", "0.5*(d_0c+d_1c)"),
        ("method", "bounded_Bernoulli_KL_Chernoff"),
        ("component_alpha", 0.05),
        ("joint_p_value", "max_component_p_value_IUT"),
        ("error_control", "all_or_none_strong_FWER"),
        ("margin", 0.0),
        ("branch", "single_joint_claim_only"),
        ("integer_first_pass_A_RH", 21_046),
        ("integer_first_pass_A_HR", 21_046),
        ("integer_first_pass_COMMON", 42_091),
        ("continuous_q_star", 0.551580065745296),
        ("discrete_q_fail", 0.551579365312785),
        ("planning_normalized_support_range_gap_minimum", 0.1),
        ("joint_power_lower_bound", 0.801021247429385),
        ("n561_joint_power_lower_bound", 0.799048262648854),
        ("forbidden_reporting", "independent_component_claims_or_simultaneous_confidence_intervals"),
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
    resource_envelope: tuple[tuple[str, int], ...] = tuple(RESOURCE_ENVELOPE.items())
    panel_slice_contract: tuple[tuple[str, object], ...] = (
        ("slice_count", 24),
        ("full_slice_count", 23),
        ("full_slice_tapes", 24),
        ("full_slice_width", 144),
        ("final_slice_tapes", 10),
        ("final_slice_width", 60),
        ("ordering", "global_tape_then_HR_RH_then_COMMON_A_HR_A_RH"),
        ("publication", "all_3372_cells_then_one_atomic_global_recomputation"),
        ("stopping", "no_early_stop_no_supplement_no_replacement"),
    )
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
        value["resource_envelope"] = dict(self.resource_envelope)
        return value


def validate_resource_request(observed: Mapping[str, int]) -> None:
    if set(observed) != set(RESOURCE_MAXIMA):
        raise ContractError("resource inventory fields differ")
    for name, maximum in RESOURCE_MAXIMA.items():
        value = observed[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
            raise ContractError(f"resource ceiling exceeded or invalid: {name}")


def validate_resource_envelope(observed: Mapping[str, int]) -> None:
    if not isinstance(observed, Mapping) or dict(observed) != dict(RESOURCE_ENVELOPE):
        raise ContractError("resource envelope differs from the frozen V3 contract")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in observed.values()):
        raise ContractError("resource envelope values must be positive integers")


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
    gap_integer_sums: tuple[tuple[str, int], ...] = ()
    component_p_values: tuple[tuple[str, float], ...] = ()
    joint_p_value: float | None = None
    joint_effect_lower_bound: float | None = None


if ACTIONS[COMMON_INDEX] != (1, (0, 0, 0, 0)):
    raise RuntimeError("registered COMMON catalogue action drifted")
if ACTIONS[A_HR_INDEX] != (2, (1, -1, 0, 0)):
    raise RuntimeError("registered A_HR catalogue action drifted")
if ACTIONS[A_RH_INDEX] != (2, (0, 0, 1, -1)):
    raise RuntimeError("registered A_RH catalogue action drifted")
if PANEL_WIDTH != TAPE_COUNT * len(GRAPHS) * len(CANDIDATE_ACTIONS):
    raise RuntimeError("FCEOV native panel width drifted")
if (
    PANEL_FULL_SLICE_COUNT * PANEL_FULL_SLICE_TAPES + PANEL_FINAL_SLICE_TAPES
    != TAPE_COUNT
    or PANEL_FULL_SLICE_TAPES * len(GRAPHS) * len(CANDIDATE_ACTIONS)
    != PANEL_MAX_NATIVE_WIDTH
    or PANEL_FINAL_SLICE_TAPES * len(GRAPHS) * len(CANDIDATE_ACTIONS)
    != PANEL_FINAL_NATIVE_WIDTH
):
    raise RuntimeError("FCEOV panel-slice decomposition drifted")


__all__ = [
    "ACTIONS", "A_HR_INDEX", "A_RH_INDEX", "CANDIDATE_ACTIONS", "CHECKPOINT_UPDATE", "COMMON_INDEX",
    "COMPETENCE_EPISODES", "ContractError", "Disposition", "EPISODES_PER_UPDATE",
    "FAILURE_LABELS", "FOUNDATION_UPDATES", "FoundationGate", "GRAPH_ASSIGNMENT",
    "GRAPH_EVENTS", "GRAPH_Q", "GRAPHS", "Graph", "HORIZON_TICKS", "HOST",
    "INFERENCE_ALPHA", "INFERENCE_COMMON_GAP_RAW_SUM_PASS", "INFERENCE_CONTINUOUS_Q_STAR",
    "INFERENCE_DISCRETE_Q_FAIL", "INFERENCE_FIRST_GAP_RAW_SUM_PASS",
    "INFERENCE_JOINT_POWER_LOWER_BOUND", "INFERENCE_MARGIN",
    "INFERENCE_N561_JOINT_POWER_LOWER_BOUND", "INFERENCE_PLANNING_GAP",
    "K_TARGET", "MANIFEST_SCHEMA", "Manifest", "PANEL_FINAL_NATIVE_WIDTH",
    "PANEL_FINAL_SLICE_TAPES", "PANEL_FULL_SLICE_COUNT", "PANEL_FULL_SLICE_TAPES",
    "PANEL_MAX_NATIVE_WIDTH", "PANEL_SLICE_COUNT", "PANEL_WIDTH", "PanelCell", "PublicClaimState",
    "RESOURCE_ENVELOPE", "RESOURCE_MAXIMA", "TAPE_COUNT", "TICK_SECONDS",
    "TerminalFact", "fixed_claim_state", "validate_resource_envelope", "validate_resource_request",
    "validate_state_alias",
]
