from dataclasses import replace

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency import host
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import (
    vqfp_controls,
)
from experiments.candidates.vqfp_frrie_action_codec import (
    COMMON_ROSTERS,
    LEGAL_ACTIONS_BY_ROLE,
    PUBLIC_ROLES,
    QUANTUM_COUNT,
    VQFP_REGISTERED_ROSTERS,
    allocation_count,
    build_impossibility_certificate,
    legal_joint_action_count,
    validate_impossibility_certificate,
    witness_role_layout,
)


def test_bridge_literals_match_current_frrie_and_vqfp_source_contracts():
    assert QUANTUM_COUNT == vqfp_controls.Q == 120
    assert PUBLIC_ROLES == host.PUBLIC_ROLES
    assert dict(LEGAL_ACTIONS_BY_ROLE) == host.LEGAL_ACTIONS_BY_ROLE
    assert witness_role_layout(6) == tuple(
        role for role in host.PUBLIC_ROLES for _ in range(2)
    )


def test_n6_pigeonhole_counts_are_exact_and_dispositive():
    roles = witness_role_layout(6)
    assert allocation_count(6) == 234_531_275  # C(125, 5)
    assert legal_joint_action_count(roles) == 1_296  # 3^4 * 4^2
    certificate = build_impossibility_certificate()
    assert certificate.allocation_count == 234_531_275
    assert certificate.legal_joint_action_count == 1_296
    assert certificate.pigeonhole_gap == 234_529_979
    assert certificate.minimum_collision_fiber_size == 180_966
    assert certificate.minimum_native_steps_for_capacity == 3
    assert COMMON_ROSTERS == certificate.common_rosters == (6,)
    assert VQFP_REGISTERED_ROSTERS == (4, 6, 8, 12)
    assert certificate.vqfp_rosters_without_native_target == (4, 8, 12)
    assert certificate.roundtrip_implies_injective is True
    assert certificate.one_step_injection_possible is False
    assert certificate.conclusion == "NO_TOTAL_INJECTIVE_ONE_STEP_ACTION_CODEC"
    assert certificate.endpoint_equality_status == (
        "UNREACHABLE_AFTER_ROUNDTRIP_CARDINALITY_CONTRADICTION"
    )
    assert validate_impossibility_certificate(certificate) is certificate


def test_three_symbol_steps_have_capacity_but_are_semantically_inadmissible():
    certificate = build_impossibility_certificate()
    codomain = certificate.legal_joint_action_count
    assert codomain**2 < certificate.allocation_count <= codomain**3
    assert certificate.contract.native_decision_steps == 1
    assert certificate.contract.extra_host_steps == 0


def test_certificate_count_is_invariant_to_actual_balanced_entity_order():
    interleaved = (
        "RIDGE_RELAY",
        "WEST_SURVEYOR",
        "EAST_SURVEYOR",
        "WEST_SURVEYOR",
        "RIDGE_RELAY",
        "EAST_SURVEYOR",
    )
    certificate = build_impossibility_certificate(6, roles=interleaved)
    assert certificate.contract.roles == interleaved
    assert certificate.legal_joint_action_count == 1_296
    assert certificate.minimum_collision_fiber_size == 180_966
    assert validate_impossibility_certificate(certificate) is certificate


def test_certificate_rejects_any_tampered_count_or_conclusion():
    certificate = build_impossibility_certificate()
    for changed in (
        replace(certificate, allocation_count=certificate.allocation_count - 1),
        replace(certificate, legal_joint_action_count=certificate.legal_joint_action_count + 1),
        replace(certificate, pigeonhole_gap=0),
        replace(certificate, minimum_collision_fiber_size=1),
        replace(certificate, minimum_native_steps_for_capacity=2),
        replace(certificate, roundtrip_implies_injective=False),
        replace(certificate, one_step_injection_possible=True),
        replace(certificate, conclusion="CODEC_EXISTS"),
    ):
        with pytest.raises(ValueError, match="differs"):
            validate_impossibility_certificate(changed)


def test_certificate_refuses_noncommon_rosters_instead_of_broadening_claim():
    for roster in (4, 8, 12, 9, 15, 21):
        with pytest.raises(ValueError, match="no roster-preserving"):
            build_impossibility_certificate(roster)
