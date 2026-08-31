from dataclasses import asdict, replace

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import assert_projection_only_difference, initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG, RNGAddress
from experiments.candidates.finite_resource_relational_inductive_efficiency.runner import WorkReceipt, audit_pair_parity


def test_bit_identical_pair_initialization_and_projection_witness():
    phy, edge = initialize_paired_arms(AddressedRNG(b"p" * 32), "FRRIE-TEST-PAIR-BLOCK")
    assert phy.parameter_bytes() == edge.parameter_bytes()
    assert_projection_only_difference(phy, edge)


def test_rng_is_arm_and_cut_independent():
    rng = AddressedRNG(b"x" * 32)
    address = RNGAddress("FRRIE-FRESH-BLOCK-001", "EVALUATE", 6, 512, 0, 0, 0, 0, "EVALUATION")
    assert rng.block(address) == rng.block(address)
    with pytest.raises(ValueError, match="arm- and intervention-independent"):
        RNGAddress.from_mapping({**asdict(address), "arm": "PHY_TRUST"})


def test_pair_work_receipt_exact_parity():
    base = WorkReceipt(
        "PHY_TRUST", 1, 64, 64, 1, 1, 142052, 10, 1, 1, 8,
        "float32", 0, 0, {"schema": "DIRECT_TAPE_CONTRACT_V1", "coordinate": 1},
    )
    audit_pair_parity(base, replace(base, arm_id="EDGE_FLEX"))
    with pytest.raises(ValueError):
        audit_pair_parity(base, replace(base, arm_id="EDGE_FLEX", flops=11))
