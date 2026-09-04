"""Typed one-decision ActionCodec contract shared by the finite certificate.

This is a semantics contract, not a compression API.  A conforming codec would
map one VQFP allocation to one legal FRRIE joint action at the same host step.
Its signatures intentionally expose no observation, history, tape, RNG, work,
or side-channel input.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Mapping, Protocol, runtime_checkable


QUANTUM_COUNT: Final[int] = 120
VQFP_REGISTERED_ROSTERS: Final[tuple[int, ...]] = (4, 6, 8, 12)
FRRIE_ROSTERS: Final[tuple[int, ...]] = (6, 9, 15, 21)
COMMON_ROSTERS: Final[tuple[int, ...]] = tuple(
    roster for roster in VQFP_REGISTERED_ROSTERS if roster in FRRIE_ROSTERS
)
FROZEN_COUNTEREXAMPLE_ROSTER: Final[int] = 6
PUBLIC_ROLES: Final[tuple[str, ...]] = (
    "WEST_SURVEYOR",
    "EAST_SURVEYOR",
    "RIDGE_RELAY",
)
LEGAL_ACTIONS_BY_ROLE: Final[Mapping[str, tuple[int, ...]]] = MappingProxyType(
    {
        "WEST_SURVEYOR": (0, 1, 5),
        "EAST_SURVEYOR": (0, 1, 5),
        "RIDGE_RELAY": (2, 3, 4, 5),
    }
)


class CodecContractError(ValueError):
    """A value violates the frozen one-native-decision seam."""


def witness_role_layout(roster: int) -> tuple[str, ...]:
    """Return one valid balanced layout used by the finite witness.

    FRRIE accepts any stable entity-order permutation with equal role counts.
    The legal-joint-action count depends only on those counts, so this block
    layout is a witness rather than a claim that production order is unique.
    """

    if type(roster) is not int or roster not in FRRIE_ROSTERS or roster % 3:
        raise CodecContractError("roster must be one registered FRRIE multiple of three")
    per_role = roster // 3
    return tuple(role for role in PUBLIC_ROLES for _ in range(per_role))


def validate_role_layout(
    roles: tuple[str, ...], *, roster: int
) -> tuple[str, ...]:
    """Validate the actual stable balanced role tuple in literal entity order."""

    if not isinstance(roles, tuple) or len(roles) != roster:
        raise CodecContractError("roles must be one tuple aligned with the fixed roster")
    if roster not in FRRIE_ROSTERS or roster % 3:
        raise CodecContractError("roster must be one registered FRRIE multiple of three")
    if any(role not in LEGAL_ACTIONS_BY_ROLE for role in roles):
        raise CodecContractError("role layout contains an unregistered public role")
    per_role = roster // 3
    if any(roles.count(role) != per_role for role in PUBLIC_ROLES):
        raise CodecContractError("role layout must contain equal counts of all public roles")
    return roles


def validate_allocation(
    allocation: tuple[int, ...], *, roster: int
) -> tuple[int, ...]:
    """Validate one literal weak composition of 120 in entity order."""

    if roster not in COMMON_ROSTERS:
        raise CodecContractError("allocation roster has no roster-preserving VQFP/FRRIE cell")
    if not isinstance(allocation, tuple) or len(allocation) != roster:
        raise CodecContractError("allocation must be one tuple with length equal to roster")
    if any(type(value) is not int or value < 0 for value in allocation):
        raise CodecContractError("allocation entries must be nonnegative literal integers")
    if sum(allocation) != QUANTUM_COUNT:
        raise CodecContractError("allocation must sum exactly to Q=120")
    return allocation


def validate_native_joint_action(
    native_action: tuple[int, ...], *, roles: tuple[str, ...]
) -> tuple[int, ...]:
    """Validate one legal categorical joint action in the same entity order."""

    if not isinstance(native_action, tuple) or len(native_action) != len(roles):
        raise CodecContractError("native action must be one tuple aligned with roles")
    validate_role_layout(roles, roster=len(roles))
    for entity, (action, role) in enumerate(zip(native_action, roles)):
        if type(action) is not int or action not in LEGAL_ACTIONS_BY_ROLE[role]:
            raise CodecContractError(
                f"native action at entity {entity} is illegal for role {role}"
            )
    return native_action


def physical_command(
    allocation: tuple[int, ...], *, roster: int
) -> tuple[Fraction, ...]:
    """Materialize the simultaneous VQFP command ``a_i=n_i/600`` exactly."""

    checked = validate_allocation(allocation, roster=roster)
    return tuple(Fraction(value, 600) for value in checked)


def allocation_count(roster: int, *, quanta: int = QUANTUM_COUNT) -> int:
    """Count all nonnegative length-``roster`` vectors summing to ``quanta``."""

    if type(roster) is not int or roster <= 0:
        raise CodecContractError("allocation roster must be a positive literal integer")
    if type(quanta) is not int or quanta < 0:
        raise CodecContractError("quanta must be a nonnegative literal integer")
    return math.comb(quanta + roster - 1, roster - 1)


def legal_joint_action_count(roles: tuple[str, ...]) -> int:
    """Count the exact fixed-role legal joint categorical actions at one step."""

    if not isinstance(roles, tuple) or not roles:
        raise CodecContractError("roles must be a nonempty literal tuple")
    validate_role_layout(roles, roster=len(roles))
    return math.prod(len(LEGAL_ACTIONS_BY_ROLE[role]) for role in roles)


@dataclass(frozen=True, slots=True)
class OneStepCodecContract:
    """Complete preservation contract for a hypothetical codec implementation."""

    roster: int
    roles: tuple[str, ...]
    quantum_count: int = QUANTUM_COUNT
    native_decision_steps: int = 1
    extra_host_steps: int = 0
    consumes_observation: bool = False
    consumes_history: bool = False
    consumes_tape: bool = False
    consumes_rng: bool = False
    reorders_entities: bool = False
    changes_roles: bool = False
    changes_logical_work: bool = False
    physical_command_denominator: int = 600
    allocation_applied_simultaneously: bool = True
    native_action_semantics_preserved: bool = True
    roundtrip_required: bool = True
    pathwise_endpoint_equality_required: bool = True

    @classmethod
    def for_roster(cls, roster: int) -> "OneStepCodecContract":
        return cls(roster=roster, roles=witness_role_layout(roster))

    @classmethod
    def for_roles(cls, roles: tuple[str, ...]) -> "OneStepCodecContract":
        return cls(roster=len(roles), roles=validate_role_layout(roles, roster=len(roles)))

    def validate(self) -> "OneStepCodecContract":
        validate_role_layout(self.roles, roster=self.roster)
        if self.roster not in COMMON_ROSTERS:
            raise CodecContractError("codec roster has no roster-preserving VQFP/FRRIE cell")
        if self.quantum_count != QUANTUM_COUNT:
            raise CodecContractError("codec quantum count must equal Q=120")
        if self.native_decision_steps != 1 or self.extra_host_steps != 0:
            raise CodecContractError("codec must occupy exactly one native decision and add no step")
        forbidden = (
            self.consumes_observation,
            self.consumes_history,
            self.consumes_tape,
            self.consumes_rng,
            self.reorders_entities,
            self.changes_roles,
            self.changes_logical_work,
        )
        if any(forbidden):
            raise CodecContractError("codec uses a forbidden input or changes preserved semantics")
        if self.physical_command_denominator != 600:
            raise CodecContractError("VQFP physical commands must remain a_i=n_i/600")
        required = (
            self.allocation_applied_simultaneously,
            self.native_action_semantics_preserved,
            self.roundtrip_required,
            self.pathwise_endpoint_equality_required,
        )
        if not all(required):
            raise CodecContractError(
                "codec must preserve simultaneity, categorical meaning, round trip, and endpoint"
            )
        return self


@runtime_checkable
class ActionCodec(Protocol):
    """Exact interface a future FRRIE consumer would require.

    The contract binds roster and role layout.  Encoding and decoding therefore
    have no second input through which scientific state could leak.
    """

    @property
    def contract(self) -> OneStepCodecContract: ...

    def encode(self, allocation: tuple[int, ...], /) -> tuple[int, ...]: ...

    def decode(self, native_action: tuple[int, ...], /) -> tuple[int, ...]: ...
