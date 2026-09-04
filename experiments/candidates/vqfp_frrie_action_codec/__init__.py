"""Finite contract and impossibility certificate for the VQFP/FRRIE action seam.

The package deliberately exports an interface but no codec implementation.  Under
the frozen one-native-decision semantics, the exact VQFP allocation domain is
larger than the FRRIE legal joint-action codomain already at the common roster
``N=6``.
"""

from .certificate import (
    CERTIFICATE_SCHEMA,
    ImpossibilityCertificate,
    build_impossibility_certificate,
    minimum_native_steps_for_capacity,
    validate_impossibility_certificate,
)
from .contract import (
    COMMON_ROSTERS,
    FROZEN_COUNTEREXAMPLE_ROSTER,
    FRRIE_ROSTERS,
    LEGAL_ACTIONS_BY_ROLE,
    PUBLIC_ROLES,
    QUANTUM_COUNT,
    VQFP_REGISTERED_ROSTERS,
    ActionCodec,
    CodecContractError,
    OneStepCodecContract,
    allocation_count,
    legal_joint_action_count,
    physical_command,
    validate_allocation,
    validate_native_joint_action,
    validate_role_layout,
    witness_role_layout,
)

__all__ = [
    "CERTIFICATE_SCHEMA",
    "COMMON_ROSTERS",
    "FROZEN_COUNTEREXAMPLE_ROSTER",
    "FRRIE_ROSTERS",
    "LEGAL_ACTIONS_BY_ROLE",
    "PUBLIC_ROLES",
    "QUANTUM_COUNT",
    "VQFP_REGISTERED_ROSTERS",
    "ActionCodec",
    "CodecContractError",
    "ImpossibilityCertificate",
    "OneStepCodecContract",
    "allocation_count",
    "build_impossibility_certificate",
    "legal_joint_action_count",
    "physical_command",
    "minimum_native_steps_for_capacity",
    "validate_allocation",
    "validate_impossibility_certificate",
    "validate_native_joint_action",
    "validate_role_layout",
    "witness_role_layout",
]
