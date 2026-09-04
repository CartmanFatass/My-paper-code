import ast
from dataclasses import replace
from fractions import Fraction
import inspect
from pathlib import Path

import pytest

from experiments.candidates.vqfp_frrie_action_codec import (
    ActionCodec,
    CodecContractError,
    OneStepCodecContract,
    legal_joint_action_count,
    physical_command,
    validate_allocation,
    validate_native_joint_action,
    validate_role_layout,
    witness_role_layout,
)


def test_frozen_n6_role_layout_and_legal_actions_are_entity_ordered():
    roles = witness_role_layout(6)
    assert roles == (
        "WEST_SURVEYOR",
        "WEST_SURVEYOR",
        "EAST_SURVEYOR",
        "EAST_SURVEYOR",
        "RIDGE_RELAY",
        "RIDGE_RELAY",
    )
    assert validate_native_joint_action((0, 1, 5, 0, 2, 4), roles=roles) == (
        0, 1, 5, 0, 2, 4
    )
    with pytest.raises(CodecContractError, match="illegal"):
        validate_native_joint_action((2, 1, 5, 0, 2, 4), roles=roles)
    with pytest.raises(CodecContractError, match="illegal"):
        validate_native_joint_action((0, 1, 5, 0, 0, 4), roles=roles)


def test_allocation_contract_is_every_literal_weak_composition_of_120():
    assert validate_allocation((120, 0, 0, 0, 0, 0), roster=6) == (
        120, 0, 0, 0, 0, 0
    )
    assert validate_allocation((20, 20, 20, 20, 20, 20), roster=6)
    assert physical_command((20, 20, 20, 20, 20, 20), roster=6) == (
        Fraction(1, 30),
    ) * 6
    for invalid in (
        (119, 0, 0, 0, 0, 0),
        (121, -1, 0, 0, 0, 0),
        (True, 119, 0, 0, 0, 0),
        (120, 0, 0, 0, 0),
    ):
        with pytest.raises(CodecContractError):
            validate_allocation(invalid, roster=6)
    with pytest.raises(CodecContractError, match="no roster-preserving"):
        validate_allocation((30, 30, 30, 30), roster=4)


def test_codec_contract_forbids_extra_steps_and_side_channels():
    contract = OneStepCodecContract.for_roster(6).validate()
    assert contract.native_decision_steps == 1
    assert contract.extra_host_steps == 0
    for changed in (
        replace(contract, native_decision_steps=2, extra_host_steps=1),
        replace(contract, consumes_observation=True),
        replace(contract, consumes_history=True),
        replace(contract, consumes_tape=True),
        replace(contract, consumes_rng=True),
        replace(contract, reorders_entities=True),
        replace(contract, changes_roles=True),
        replace(contract, changes_logical_work=True),
        replace(contract, physical_command_denominator=1),
        replace(contract, allocation_applied_simultaneously=False),
        replace(contract, native_action_semantics_preserved=False),
        replace(contract, roundtrip_required=False),
        replace(contract, pathwise_endpoint_equality_required=False),
    ):
        with pytest.raises(CodecContractError):
            changed.validate()


def test_actual_balanced_role_permutations_are_accepted_without_reordering():
    interleaved = (
        "RIDGE_RELAY",
        "WEST_SURVEYOR",
        "EAST_SURVEYOR",
        "WEST_SURVEYOR",
        "RIDGE_RELAY",
        "EAST_SURVEYOR",
    )
    assert validate_role_layout(interleaved, roster=6) is interleaved
    contract = OneStepCodecContract.for_roles(interleaved).validate()
    assert contract.roles == interleaved
    assert contract.physical_command_denominator == 600
    assert contract.allocation_applied_simultaneously is True
    assert contract.native_action_semantics_preserved is True
    assert contract.roundtrip_required is True
    assert contract.pathwise_endpoint_equality_required is True
    assert legal_joint_action_count(interleaved) == legal_joint_action_count(
        witness_role_layout(6)
    ) == 1_296
    with pytest.raises(CodecContractError, match="equal counts"):
        validate_role_layout(("WEST_SURVEYOR",) * 6, roster=6)


def test_exported_codec_interface_has_no_auxiliary_input_channel():
    assert tuple(inspect.signature(ActionCodec.encode).parameters) == (
        "self", "allocation"
    )
    assert tuple(inspect.signature(ActionCodec.decode).parameters) == (
        "self", "native_action"
    )


def test_certificate_package_has_no_historical_runtime_or_external_effect_dependency():
    package = (
        Path(__file__).parents[4]
        / "experiments"
        / "candidates"
        / "vqfp_frrie_action_codec"
    )
    forbidden = {
        "experiments.candidates.finite_resource_relational_inductive_efficiency",
        "experiments.candidates.vqfp_vnpa_r03",
        "experiments.candidates.semantic_graphon_shared_policy_rscf_r01",
        "hashlib",
        "hmac",
        "subprocess",
        "socket",
    }
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        assert not forbidden.intersection(imported), path
