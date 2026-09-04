"""Typed, exact-value schema for the CBSC finite factorial.

The module deliberately contains no sampler.  All probability-like quantities are
``Fraction`` values and every scientific coordinate is an explicit enum member.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Mapping


class _Name(str, Enum):
    def __str__(self) -> str:
        return self.value


class OwnerState(_Name):
    LIVE = "LIVE"
    BROKEN = "BROKEN"


class SemanticState(_Name):
    PERSIST = "PERSIST"
    REFRESH = "REFRESH"


class BindingState(_Name):
    AUTHENTIC = "AUTHENTIC"
    WHOLE_CARRIER_REASSOCIATED = "WHOLE_CARRIER_REASSOCIATED"


class AccessState(_Name):
    OPEN = "OPEN"
    BINDING_GATED = "BINDING_GATED"


class PayloadState(_Name):
    RECEIVER_CORRECT = "RECEIVER_CORRECT"
    SWAPPED = "SWAPPED"
    NATIVE_NEUTRAL = "NATIVE_NEUTRAL"


class PolicyArm(_Name):
    CBSC_RULE = "CBSC_RULE"
    RAW_EXACT_OPTIMUM = "RAW_EXACT_OPTIMUM"
    OWNER_BLIND_OPTIMUM = "OWNER_BLIND_OPTIMUM"
    PREDICTIVE_INDEX_CAPABILITY_NULL = "PREDICTIVE_INDEX_CAPABILITY_NULL"
    RESET_EXACT = "RESET_EXACT"
    HARD_OPEN = "HARD_OPEN"


class Action(_Name):
    SERVE = "SERVE"
    REFRESH = "REFRESH"
    SAFE_FALLBACK = "SAFE_FALLBACK"


@dataclass(frozen=True, order=True)
class NuisanceCoordinate:
    physical_receiver: int
    old_bit: int
    current_bit: int
    donor_bit: int
    z0: int
    z1: int
    presentation_permutation: int

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value not in (0, 1):
                raise ValueError(f"{field.name} must be the integer 0 or 1")

    def address(self) -> tuple[int, ...]:
        return tuple(getattr(self, field.name) for field in fields(self))


@dataclass(frozen=True, order=True)
class Body:
    body_id: str
    addressed_receiver: int
    payload_source_receiver: int | None
    content_bit: int | None
    native_neutral: bool
    epoch: int
    public_phase: int


@dataclass(frozen=True, order=True)
class Carrier:
    carrier_id: str
    issued_to_receiver: int
    body: Body


@dataclass(frozen=True)
class World:
    world_id: str
    nuisance_id: str
    owner: OwnerState
    semantic: SemanticState
    binding: BindingState
    access: AccessState
    payload: PayloadState
    nuisance: NuisanceCoordinate
    focal_need_active: bool
    issued_inventory: tuple[Carrier, ...]
    issued_carriers: tuple[Carrier, Carrier]
    carriers_by_physical_receiver: tuple[Carrier, Carrier]
    presented_carriers: tuple[Carrier, Carrier]

    @property
    def physical_receiver(self) -> int:
        return self.nuisance.physical_receiver

    @property
    def focal_carrier(self) -> Carrier:
        return self.carriers_by_physical_receiver[self.physical_receiver]

    @property
    def routed_carrier(self) -> Carrier:
        """Receiver-addressed lookup used when ACCESS is OPEN."""

        return self.issued_carriers[self.physical_receiver]

    @property
    def execution_carrier(self) -> Carrier:
        return self.routed_carrier if self.access is AccessState.OPEN else self.focal_carrier

    @property
    def owner_continuity(self) -> bool:
        return self.owner is OwnerState.LIVE

    @property
    def epoch_match(self) -> bool:
        return self.semantic is SemanticState.PERSIST

    @property
    def association_authentic(self) -> bool:
        return self.focal_carrier.issued_to_receiver == self.physical_receiver

    @property
    def body_address_match(self) -> bool:
        return self.execution_carrier.body.addressed_receiver == self.physical_receiver

    @property
    def payload_source_match(self) -> bool:
        return self.execution_carrier.body.payload_source_receiver == self.physical_receiver

    @property
    def native_neutral(self) -> bool:
        return self.execution_carrier.body.native_neutral

    @property
    def current_content_bit(self) -> int:
        base = self.nuisance.old_bit if self.epoch_match else self.nuisance.current_bit
        phase = self.nuisance.z0 if self.physical_receiver == 0 else self.nuisance.z1
        return base ^ phase

    @property
    def focal_need_value(self) -> int:
        return self.current_content_bit

    @property
    def direct_content_current(self) -> bool:
        body = self.execution_carrier.body
        return (
            self.epoch_match
            and not body.native_neutral
            and self.payload_source_match
            and body.content_bit == self.current_content_bit
        )


@dataclass(frozen=True, order=True)
class ObservationKey:
    """Hashable controller observation made only from pre-action primitives."""

    primitives: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, order=True)
class LedgerEntry:
    name: str
    clock: int
    amount: Fraction


@dataclass(frozen=True)
class ActionLedger:
    action: Action
    terminal_clock: int
    entries: tuple[LedgerEntry, ...]
    net_return: Fraction

    def __post_init__(self) -> None:
        if sum((entry.amount for entry in self.entries), Fraction(0)) != self.net_return:
            raise ValueError("ledger entries do not reconcile to net_return")


@dataclass(frozen=True)
class ActionVector:
    serve: Fraction
    refresh: Fraction
    safe_fallback: Fraction

    def for_action(self, action: Action) -> Fraction:
        return {
            Action.SERVE: self.serve,
            Action.REFRESH: self.refresh,
            Action.SAFE_FALLBACK: self.safe_fallback,
        }[action]


@dataclass(frozen=True)
class PolicyDecision:
    observation: ObservationKey
    action_values: ActionVector
    action: Action
    unique: bool
    margin: Fraction


@dataclass(frozen=True)
class ExactPolicy:
    policy: PolicyArm
    decisions: tuple[PolicyDecision, ...]

    def action_for(self, observation: ObservationKey) -> Action:
        for decision in self.decisions:
            if decision.observation == observation:
                return decision.action
        raise KeyError("observation is outside this exact policy's support")


@dataclass(frozen=True)
class RegisteredSpec:
    schema: str
    direction_id: str
    protocol_id: str
    nuisance_version: str
    owner_levels: tuple[OwnerState, ...]
    semantic_levels: tuple[SemanticState, ...]
    binding_levels: tuple[BindingState, ...]
    access_levels: tuple[AccessState, ...]
    payload_levels: tuple[PayloadState, ...]
    policies: tuple[PolicyArm, ...]
    actions: tuple[Action, ...]
    nuisance_fields: tuple[str, ...]
    costs: tuple[tuple[str, Fraction], ...]
    material_margin: Fraction
    protocol_order: tuple[str, ...]
    all_payload_issuance_law: str
    phase_currentness_law: str
    reassociation_law: str
    authorization_information_law: str
    action_clock_law: tuple[tuple[str, int], ...]
    determinism_law: tuple[str, ...]
    publication_law: tuple[str, ...]
    branch_order: tuple[str, ...]
    cbsc_fixed_rule: tuple[tuple[str, str], ...]
    owner_blind_law: tuple[str, ...]
    reset_law: tuple[str, ...]
    hard_open_law: tuple[str, ...]
    policy_capability_law: tuple[tuple[str, str], ...]
    action_ledger_incidence: tuple[tuple[str, tuple[str, ...]], ...]
    contrast_laws: tuple[tuple[str, str], ...]
    delta_comparator: str
    branch_witness_law: str
    interpretation_boundary: str

    def cost(self, name: str) -> Fraction:
        return dict(self.costs)[name]

    @property
    def scientific_cell_count(self) -> int:
        return (
            len(self.owner_levels)
            * len(self.semantic_levels)
            * len(self.binding_levels)
            * len(self.access_levels)
            * len(self.payload_levels)
        )

    @property
    def nuisance_count(self) -> int:
        return 2 ** len(self.nuisance_fields)

    @property
    def world_count(self) -> int:
        return self.scientific_cell_count * self.nuisance_count


@dataclass(frozen=True)
class SpecAudit:
    valid: bool
    scientific_cell_count: int
    nuisance_count_per_cell: int
    world_count_per_arm: int
    checks: tuple[tuple[str, bool], ...]
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultRow:
    world_id: str
    nuisance_id: str
    policy: PolicyArm
    observation: ObservationKey
    action_values: ActionVector
    decision: Action
    ledger: ActionLedger


@dataclass(frozen=True)
class CompleteResult:
    schema: str
    complete: bool
    identity: Mapping[str, Any]
    manifests: Mapping[str, Any]
    support: Mapping[str, Any]
    pairing: Mapping[str, Any]
    rows: tuple[ResultRow, ...]
    contrasts: Mapping[str, Any]
    audits: Mapping[str, Any]
    interpretation_boundary: str
    branch: str
    first_failing_witness: str | None = None


def rational_json(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def from_rational_json(value: object) -> Fraction:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(type(part) is not int for part in value)
        or value[1] == 0
    ):
        raise ValueError("JSON rational must be [integer numerator, nonzero integer denominator]")
    result = Fraction(value[0], value[1])
    if [result.numerator, result.denominator] != value:
        raise ValueError("JSON rational must be in canonical reduced form with positive denominator")
    return result


def to_jsonable(value: Any) -> Any:
    """Convert CBSC values to the sole canonical JSON data model."""

    if isinstance(value, Fraction):
        return rational_json(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple) or isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported CBSC serialization value: {type(value).__name__}")


__all__ = [
    "AccessState", "Action", "ActionLedger", "ActionVector", "BindingState", "Body",
    "Carrier", "CompleteResult", "ExactPolicy", "LedgerEntry", "NuisanceCoordinate",
    "ObservationKey", "OwnerState", "PayloadState", "PolicyArm", "PolicyDecision",
    "RegisteredSpec", "ResultRow", "SemanticState", "SpecAudit", "World",
    "from_rational_json", "rational_json", "to_jsonable",
]
