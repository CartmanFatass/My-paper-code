from __future__ import annotations

import hashlib

import pytest

from experiments.candidates.variable_n_fleet_churn_r02.contract import ContractViolation
from experiments.candidates.variable_n_fleet_churn_r02.rng import (
    ActionAddress,
    a0_master,
    a0_opaque_ranks,
    a0_presentations,
    action_word,
    lp,
    record_message,
    unbiased_index,
)


def _primitive_address() -> ActionAddress:
    return ActionAddress(
        phase="A0",
        replicate_role="A0-RECON-00",
        policy_stream="A0-COMMON",
        roster_size=3,
        failed_zone=1,
        update_or_panel_row="PRIMITIVE/DUPLICATE_TIE",
        episode_row=0,
        physical_time=0,
        token_role="EXEC_FAILED",
    )


def test_lp_master_record_and_action_word_golden_vectors() -> None:
    assert lp("A") == b"\x00\x00\x00\x01A"
    assert lp(2026090191) == b"\x00\x00\x00\x0a2026090191"
    assert a0_master().hex() == "cc5a53342321fe6d0d73fa7f5d0ea7253441be84dbd323db9d2aaacb3e491f7d"

    message = record_message(_primitive_address().fields())
    assert hashlib.sha256(message).hexdigest() == "f5a61c95a71c674391efe7608bb27d6295a982239ae19fbdd53126cb87761362"
    assert action_word(a0_master(), _primitive_address()) == 0x74488D49EE7D7DEF


def test_action_address_excludes_presentation_and_physical_keys() -> None:
    names = tuple(name for name, _ in _primitive_address().fields())
    forbidden = {
        "presentation",
        "external_row",
        "canonical_index",
        "opaque_rank",
        "physical_rank",
        "memory_address",
        "batch_lane",
    }
    assert forbidden.isdisjoint(names)
    with pytest.raises(TypeError):
        ActionAddress(**(_primitive_address().__dict__ | {"presentation": "reverse"}))
    with pytest.raises(ContractViolation):
        ActionAddress(**(_primitive_address().__dict__ | {"draw": 1}))


def test_unbiased_256_bit_rejection_uses_a_fresh_incremented_block() -> None:
    messages: list[bytes] = []
    values = iter(((1 << 256) - 1, 5))

    def digest(_master: bytes, message: bytes) -> bytes:
        messages.append(message)
        return next(values).to_bytes(32, "big")

    result = unbiased_index(b"m", (("domain", "unit"),), 3, hmac_digest=digest)
    assert result == 2
    assert messages[0].endswith(lp("block") + lp(0))
    assert messages[1].endswith(lp("block") + lp(1))
    assert messages[0] != messages[1]


def test_a0_opaque_and_presentation_golden_vectors() -> None:
    assert a0_opaque_ranks((1, 2, 3, 4), 3, 1) == {3: 1, 1: 2, 4: 3, 2: 4}
    assert a0_presentations((1, 2, 3), 3, 1) == {
        "canonical": (1, 2, 3),
        "reverse": (3, 2, 1),
        "cyclic": (2, 3, 1),
        "seed_fixed_random": (2, 1, 3),
    }


@pytest.mark.parametrize("bad", [-1, True, 1.5])
def test_unsigned_record_values_fail_closed(bad: object) -> None:
    with pytest.raises(ContractViolation):
        lp(bad)  # type: ignore[arg-type]
