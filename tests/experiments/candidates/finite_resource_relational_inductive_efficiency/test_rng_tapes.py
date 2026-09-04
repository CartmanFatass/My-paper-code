from copy import deepcopy
from dataclasses import asdict, replace
import inspect

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import (
    AddressedRNG,
    FP32_UNIFORM_DENOMINATOR,
    SemanticRNGAddress,
    float32_uniform_mapping_contract,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    FP32_PROBABILITY_TOLERANCE,
    IMPLEMENTATION_CONTRACT,
    ContractError,
    validate_manifest,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.tapes import (
    PUBLIC_ROLES,
    complete_test_only_witness,
    episode_tape_contract,
    generate_episode_tape,
    generate_training_origin_schedule,
    inverse_cdf_action,
    origin_schedule_contract,
    training_origin_addresses,
)


def _action_address(**changes):
    base = SemanticRNGAddress(
        seed_block="FRRIE-TEST-SEMANTIC-BLOCK",
        purpose="TEST_ONLY",
        roster=9,
        update=0,
        episode=3,
        basin=None,
        event_ordinal=None,
        slot=4,
        public_role=1,
        role_local_index=2,
        sender=5,
        receiver=None,
        kind="action_uniform",
        draw=0,
    )
    return replace(base, **changes).validate()


@pytest.mark.parametrize(
    "label", ["arm", "arm_id", "cut", "intervention", "branch", "branch_id"],
)
def test_semantic_addresses_reject_arm_cut_intervention_and_branch_labels(label):
    with pytest.raises(ValueError, match="branch-independent"):
        SemanticRNGAddress.from_mapping({**asdict(_action_address()), label: "FORBIDDEN"})


def test_semantic_coordinates_are_stable_and_each_perturbation_changes_the_word():
    rng = AddressedRNG(b"a" * 32)
    address = _action_address()
    assert rng.block(address) == rng.block(address)
    alternatives = (
        replace(address, seed_block="FRRIE-TEST-SEMANTIC-BLOCK-2"),
        replace(address, episode=4),
        replace(address, slot=5),
        replace(address, draw=1),
        replace(address, kind="base_uniform"),
    )
    assert len({rng.block(item) for item in (address, *alternatives)}) == 1 + len(alternatives)


def test_complete_test_witness_is_repeatable_common_and_value_free_receipted():
    first = complete_test_only_witness(9, 7)
    second = complete_test_only_witness(9, 7)
    for field in (
        "event_times", "detection_uniform", "uplink_uniform",
        "base_uniform", "action_uniform",
    ):
        assert np.array_equal(getattr(first, field), getattr(second, field))
    parameters = inspect.signature(generate_episode_tape).parameters
    assert not ({"arm", "cut", "intervention", "branch"} & set(parameters))
    receipt = first.receipt().as_mapping()
    assert "root" not in receipt
    assert set(receipt) == {
        "schema", "seed_block", "purpose", "roster", "update", "episode",
        "shapes", "dtypes", "coordinate_counts", "uniform_mapping",
        "complete", "stateless",
    }
    assert receipt == first.receipt().as_mapping()


@pytest.mark.parametrize("roster", [6, 9, 15, 21])
def test_episode_tape_shapes_are_complete_immutable_and_events_do_not_repeat(roster):
    tape = complete_test_only_witness(roster)
    per_role = roster // 3
    assert tape.event_times.shape == (2, 3)
    assert tape.detection_uniform.shape == (12, 2, per_role)
    assert tape.uplink_uniform.shape == (12, roster, roster)
    assert tape.base_uniform.shape == (12, roster)
    assert tape.action_uniform.shape == (12, roster)
    for row in tape.event_times:
        assert len(set(row.tolist())) == 3
        assert np.all((0 <= row) & (row <= 7))
    for _, shape in tape.shapes:
        assert all(dimension > 0 for dimension in shape)
    for field, _ in tape.shapes:
        assert getattr(tape, field).flags.c_contiguous
        assert not getattr(tape, field).flags.writeable
    for field in (
        "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform",
    ):
        values = getattr(tape, field)
        assert np.all(values < 1.0)
        assert np.all(values * FP32_UNIFORM_DENOMINATOR == np.floor(
            values * FP32_UNIFORM_DENOMINATOR
        ))
    with pytest.raises(ValueError):
        tape.action_uniform[0, 0] = 0.5
    with pytest.raises(ValueError):
        tape.action_uniform.setflags(write=True)
    native = tape.native_environment_payload()
    assert native.event_times.shape == (2, 3)
    assert native.event_times.dtype == np.dtype(np.int32)
    assert native.detection_uniforms.shape == (12, 21)
    assert native.uplink_uniforms.shape == (12, 21, 21)
    assert native.base_uniforms.shape == (12, 21)
    assert np.array_equal(
        native.detection_uniforms[:, : 2 * per_role].reshape(12, 2, per_role),
        tape.detection_uniform,
    )
    assert np.array_equal(native.uplink_uniforms[:, :roster, :roster], tape.uplink_uniform)
    assert np.array_equal(native.base_uniforms[:, :roster], tape.base_uniform)
    assert np.all(native.detection_uniforms[:, roster:] == 0.0)
    assert np.all(native.uplink_uniforms[:, roster:, :] == 0.0)
    assert np.all(native.uplink_uniforms[:, :, roster:] == 0.0)
    assert np.all(native.base_uniforms[:, roster:] == 0.0)
    assert all(
        not getattr(native, field).flags.writeable
        for field in ("event_times", "detection_uniforms", "uplink_uniforms", "base_uniforms")
    )
    assert not hasattr(native, "action_uniform") and not hasattr(native, "action_uniforms")


def test_roster_is_an_independent_semantic_coordinate():
    rng = AddressedRNG(b"r" * 32)
    left = generate_episode_tape(
        rng, seed_block="FRRIE-TEST-ROSTER-BLOCK", purpose="TEST_ONLY",
        roster=6, update=0, episode=0,
    )
    right = generate_episode_tape(
        rng, seed_block="FRRIE-TEST-ROSTER-BLOCK", purpose="TEST_ONLY",
        roster=9, update=0, episode=0,
    )
    assert left.action_uniform[0, 0] != right.action_uniform[0, 0]
    assert not np.array_equal(left.event_times, right.event_times)


@pytest.mark.parametrize("roster", [9, 15])
def test_rscf_selector_is_exactly_antithetic_with_one_origin_per_episode_role(roster):
    schedule = generate_training_origin_schedule(
        AddressedRNG(b"s" * 32), seed_block="FRRIE-TEST-SELECTOR-BLOCK",
        roster=roster, update=1,
    )
    assert len(schedule.selections) == 32 * 3
    assert {
        (item.episode, item.public_role) for item in schedule.selections
    } == {(episode, role) for episode in range(32) for role in PUBLIC_ROLES}
    for pair in range(16):
        for role in PUBLIC_ROLES:
            sides = {
                item.side: item for item in schedule.selections
                if item.pair == pair and item.public_role == role
            }
            assert sides[0].base_slot == sides[1].base_slot
            assert sides[0].selected_slot == sides[0].base_slot
            assert sides[1].selected_slot == 11 - sides[0].base_slot
            assert 0 <= sides[0].role_local_index < roster // 3
            assert 0 <= sides[1].role_local_index < roster // 3
    assert schedule.receipt()["origins"] == 96


def test_origin_local_index_address_is_side_specific_while_base_address_omits_side():
    common = {
        "seed_block": "FRRIE-TEST-SIDE-SPECIFIC-ORIGIN",
        "purpose": "TRAIN",
        "roster": 15,
        "update": 512,
        "pair": 15,
        "public_role": 2,
    }
    base0, local0 = training_origin_addresses(**common, side=0)
    base1, local1 = training_origin_addresses(**common, side=1)
    assert base0 == base1
    assert base0.episode == base1.episode == 30
    assert local0.episode == 30 and local1.episode == 31
    assert local0.canonical_bytes() != local1.canonical_bytes()
    rng = AddressedRNG(b"i" * 32)
    assert rng.block(local0) != rng.block(local1)

    law = origin_schedule_contract()
    assert law == IMPLEMENTATION_CONTRACT["rscf"]["origin_schedule"]
    assert law["base_slot_address_includes_side"] is False
    assert law["base_slot_shared_across_pair_sides"] is True
    assert law["side0_slot"] == "BASE_SLOT"
    assert law["side1_slot"] == "11_MINUS_BASE_SLOT"
    assert law["role_local_index_address_includes_side"] is True
    assert law["role_local_entity_shared_across_pair_sides"] is False
    assert law["role_local_entity_draws_independent_across_pair_sides"] is True
    assert law["role_local_index_support"] == "0..N/3-1"
    assert law["matching_episode_coordinate_shared_across_arms"] is True


def test_manifest_rejects_false_shared_pair_side_entity_claim(manifest_factory):
    manifest = manifest_factory()
    false_contract = deepcopy(manifest["implementation_contract"])
    false_contract["rscf"]["origin_schedule"][
        "role_local_entity_shared_across_pair_sides"
    ] = True
    manifest["implementation_contract"] = false_contract
    with pytest.raises(ContractError, match="implementation_contract"):
        validate_manifest(manifest)


def test_direct_contract_does_not_consume_a_root_and_inverse_cdf_uses_tape_uniform():
    contract = episode_tape_contract(
        seed_block="FRRIE-TEST-CONTRACT-BLOCK", purpose="EVALUATE",
        roster=21, update=512, episode=255,
    )
    assert contract["shapes"]["uplink_uniform"] == [12, 21, 21]
    assert "root" not in contract
    assert contract["uniform_mapping"] == float32_uniform_mapping_contract()
    assert inverse_cdf_action([0.2, 0.3, 0.5], 0.0) == 0
    assert inverse_cdf_action([0.2, 0.3, 0.5], 0.2) == 1
    assert inverse_cdf_action([0.2, 0.3, 0.5], 0.999) == 2


def test_inverse_cdf_accepts_fp32_row_error_and_rejects_out_of_tolerance_sum():
    valid_fp32_row = np.asarray([0.1, 0.2, 0.3, 0.4000001], dtype=np.float32)
    error = abs(float(valid_fp32_row.astype(np.float64).sum()) - 1.0)
    assert 1.0e-12 < error <= FP32_PROBABILITY_TOLERANCE
    assert inverse_cdf_action(valid_fp32_row, 0.75) == 3

    with pytest.raises(ValueError, match="sum to one"):
        inverse_cdf_action([0.5, 0.5 + 2.0 * FP32_PROBABILITY_TOLERANCE], 0.25)


def test_float32_uniform_exact_maximum_word_mapping():
    class MaximumWordRNG(AddressedRNG):
        def block(self, address, block_index=0):
            address.validate()
            assert block_index == 0
            return b"\xff" * 32

    value = MaximumWordRNG(b"m" * 32).uniform_float32(_action_address())
    assert value == 1.0 - 1.0 / FP32_UNIFORM_DENOMINATOR
    assert np.float32(value) == value
    assert value < 1.0
    contract = float32_uniform_mapping_contract()
    assert contract["numerator_max"] == FP32_UNIFORM_DENOMINATOR - 1
    assert contract["upper_endpoint_excluded"] is True
    assert "root" not in contract


def test_float32_uniform_streams_over_full_block_update_boundary_without_allocation():
    rng = AddressedRNG(b"z" * 32)
    maximum = 0.0
    count = 0
    for block in range(24):
        for update in range(1, 513):
            address = replace(
                _action_address(),
                seed_block=f"FRRIE-TEST-PANEL-BLOCK-{block:02d}",
                purpose="EVALUATE",
                roster=21,
                update=update,
                episode=255,
                slot=11,
                public_role=2,
                role_local_index=6,
                sender=20,
            ).validate()
            value = rng.uniform_float32(address)
            assert 0.0 <= value < 1.0
            assert (value * FP32_UNIFORM_DENOMINATOR).is_integer()
            maximum = max(maximum, value)
            count += 1
    assert count == 24 * 512
    assert maximum < 1.0
