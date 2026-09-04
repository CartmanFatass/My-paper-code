from __future__ import annotations

import inspect

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import TEST_SEED_LABELS
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import B01ContractError
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import (
    create_production_seed_packet, create_test_seed_packet, read_test_seed_packet,
)


def test_five_root_test_double_is_create_once_canonical_and_atomic(tmp_path):
    target = (tmp_path / "test-five-root-packet.json").resolve()
    roots = tuple(bytes([index]) * 32 for index in range(1, 6))
    create_test_seed_packet(target, roots=roots)
    packet = read_test_seed_packet(target)
    assert packet["labels"] == list(TEST_SEED_LABELS)
    assert packet["roots_hex"] == [root.hex() for root in roots]
    assert len(set(bytes.fromhex(root) for root in packet["roots_hex"])) == 5
    assert not target.with_name(target.name + ".creating").exists()
    with pytest.raises(B01ContractError, match="not fresh"):
        create_test_seed_packet(target, roots=roots)


def test_production_creator_has_no_injectable_rng_or_root_parameter_and_is_not_called():
    signature = inspect.signature(create_production_seed_packet)
    assert tuple(signature.parameters) == ("path",)
