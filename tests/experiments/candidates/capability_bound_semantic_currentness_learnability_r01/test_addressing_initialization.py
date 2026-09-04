from __future__ import annotations

import hashlib
import json

import torch

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.addressing import (
    address_digest,
    addressed_u64,
    block_id,
    canonical_address_bytes,
    ordered_batch_ids,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.initialization import (
    initialized_learner,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.support import Purpose


def test_ascii_canonical_json_address_and_u64() -> None:
    parts = ["CBSC-LR01-ORDER", "MAIN", "CBSC-LR01-MAIN-B00", 2, 7]
    expected = json.dumps(parts, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    assert canonical_address_bytes(parts) == expected
    assert address_digest(parts) == hashlib.sha256(expected).digest()
    assert addressed_u64(parts) == int.from_bytes(hashlib.sha256(expected).digest()[:8], "big")


def test_block_ids_and_arm_excluded_batch_order() -> None:
    identity = block_id(Purpose.MAIN, 3)
    assert identity == "CBSC-LR01-MAIN-B03"
    order = ordered_batch_ids("MAIN", identity, 5)
    assert sorted(order) == list(range(8))
    assert order == ordered_batch_ids("MAIN", identity, 5)


def test_addressed_initialization_is_identical_and_preserves_ambient_rng() -> None:
    torch.manual_seed(9127)
    before = torch.random.get_rng_state().clone()
    left = initialized_learner(Purpose.MAIN, 0)
    after = torch.random.get_rng_state()
    right = initialized_learner(Purpose.MAIN, 0)
    assert torch.equal(before, after)
    assert all(torch.equal(a, b) for a, b in zip(left.parameters(), right.parameters()))
    assert torch.count_nonzero(left.layers[-1].weight).item() == 0
    assert torch.count_nonzero(left.layers[-1].bias).item() == 0
    assert all(torch.count_nonzero(layer.bias).item() == 0 for layer in left.layers[:-1])


def test_addressed_initialization_changes_by_block() -> None:
    left = initialized_learner(Purpose.COMPETENCE, 0)
    right = initialized_learner(Purpose.COMPETENCE, 1)
    assert not torch.equal(left.layers[0].weight, right.layers[0].weight)
    assert torch.equal(left.layers[-1].weight, right.layers[-1].weight)
