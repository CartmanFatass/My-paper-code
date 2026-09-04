"""Exact pigeonhole certificate for the frozen VQFP-to-FRRIE action seam."""

from __future__ import annotations

from dataclasses import dataclass

from .contract import (
    COMMON_ROSTERS,
    FROZEN_COUNTEREXAMPLE_ROSTER,
    FRRIE_ROSTERS,
    OneStepCodecContract,
    VQFP_REGISTERED_ROSTERS,
    allocation_count,
    legal_joint_action_count,
)


CERTIFICATE_SCHEMA = "VQFP_FRRIE_ONE_STEP_ACTION_CODEC_IMPOSSIBILITY_V1"
CONCLUSION = "NO_TOTAL_INJECTIVE_ONE_STEP_ACTION_CODEC"
FAILED_REQUIREMENT = "decode(encode(allocation)) == allocation for every admissible allocation"
ENDPOINT_STATUS = "UNREACHABLE_AFTER_ROUNDTRIP_CARDINALITY_CONTRADICTION"


@dataclass(frozen=True, slots=True)
class ImpossibilityCertificate:
    schema: str
    contract: OneStepCodecContract
    allocation_count: int
    legal_joint_action_count: int
    pigeonhole_gap: int
    minimum_collision_fiber_size: int
    minimum_native_steps_for_capacity: int
    common_rosters: tuple[int, ...]
    vqfp_rosters_without_native_target: tuple[int, ...]
    roundtrip_implies_injective: bool
    one_step_injection_possible: bool
    conclusion: str
    failed_requirement: str
    endpoint_equality_status: str


def minimum_native_steps_for_capacity(domain_count: int, one_step_count: int) -> int:
    """Return the minimum symbol steps needed by an abstract rank/unrank channel."""

    if type(domain_count) is not int or domain_count <= 0:
        raise ValueError("domain_count must be a positive literal integer")
    if type(one_step_count) is not int or one_step_count <= 1:
        raise ValueError("one_step_count must be a literal integer greater than one")
    steps = 1
    capacity = one_step_count
    while capacity < domain_count:
        capacity *= one_step_count
        steps += 1
    return steps


def build_impossibility_certificate(
    roster: int = FROZEN_COUNTEREXAMPLE_ROSTER,
    *,
    roles: tuple[str, ...] | None = None,
) -> ImpossibilityCertificate:
    """Construct the finite witness before attempting any codec implementation."""

    if roster not in COMMON_ROSTERS:
        raise ValueError("requested roster has no roster-preserving VQFP/FRRIE cell")
    contract = (
        OneStepCodecContract.for_roster(roster)
        if roles is None
        else OneStepCodecContract.for_roles(roles)
    ).validate()
    if contract.roster != roster:
        raise ValueError("certificate roster and actual role tuple differ")
    domain = allocation_count(roster, quanta=contract.quantum_count)
    codomain = legal_joint_action_count(contract.roles)
    if domain <= codomain:
        raise ValueError("the requested roster does not furnish a pigeonhole contradiction")
    return ImpossibilityCertificate(
        schema=CERTIFICATE_SCHEMA,
        contract=contract,
        allocation_count=domain,
        legal_joint_action_count=codomain,
        pigeonhole_gap=domain - codomain,
        minimum_collision_fiber_size=(domain + codomain - 1) // codomain,
        minimum_native_steps_for_capacity=minimum_native_steps_for_capacity(
            domain, codomain
        ),
        common_rosters=COMMON_ROSTERS,
        vqfp_rosters_without_native_target=tuple(
            roster for roster in VQFP_REGISTERED_ROSTERS if roster not in FRRIE_ROSTERS
        ),
        roundtrip_implies_injective=True,
        one_step_injection_possible=False,
        conclusion=CONCLUSION,
        failed_requirement=FAILED_REQUIREMENT,
        endpoint_equality_status=ENDPOINT_STATUS,
    )


def validate_impossibility_certificate(
    certificate: ImpossibilityCertificate,
) -> ImpossibilityCertificate:
    """Recompute every fact; no stored count or conclusion is trusted."""

    if not isinstance(certificate, ImpossibilityCertificate):
        raise TypeError("an ImpossibilityCertificate is required")
    contract = certificate.contract.validate()
    expected = build_impossibility_certificate(contract.roster, roles=contract.roles)
    if certificate != expected:
        raise ValueError("impossibility certificate differs from exact recomputation")
    return certificate
