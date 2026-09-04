from __future__ import annotations

import itertools

import pytest

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.codecs import (
    CODEC_SCHEDULES,
    CodecArm,
    decode_bits,
    encode_bits,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.contract import (
    ACTIVE_PARAMETERS,
    FIELD_LAYOUT,
    SHEAR_OPERATIONS,
    describe,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.host import context
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.support import (
    Address,
    Purpose,
    Split,
    batch_addresses,
    canonical_bits,
    panel_addresses,
    unpack_bits,
)


def _fields() -> dict[str, int]:
    return context(_address()).fields


def _address() -> Address:
    return Address(Purpose.MAIN, 0, Split.TRAIN, 0, 7)


def test_result_blind_contract_and_parameter_count() -> None:
    payload = describe()
    widths = payload["network"]["widths"]
    counted = sum((left + 1) * right for left, right in itertools.pairwise(widths))
    assert counted == ACTIVE_PARAMETERS == 43_395
    assert payload["mode"] == "RESULT_BLIND_DESCRIBE"
    assert payload["result_activity"] == "ZERO"
    assert payload["result_fields"] == []
    assert set(payload["representation"]["ordered_schedules"]) == {
        "STRUCTURED_CBSC", "STRUCTURED_SHAM", "RAW_FLEX",
    }
    assert all(len(schedule) == 49 for schedule in payload["representation"]["ordered_schedules"].values())
    assert payload["dependency_firewall"] == {
        "old_exact_runner": False,
        "old_exact_enumerator": False,
        "old_exact_artifact": False,
    }


def test_canonical_112_bit_lsb_first_round_trip() -> None:
    fields = _fields()
    bits = canonical_bits(fields, _address())
    assert len(bits) == 112
    assert bits[:8] == tuple((fields["physical_receiver"] >> bit) & 1 for bit in range(8))
    assert unpack_bits(bits) == fields


@pytest.mark.parametrize("arm", list(CodecArm))
def test_each_codec_has_exact_schedule_and_is_lossless(arm: CodecArm) -> None:
    bits = canonical_bits(_fields(), _address())
    assert len(CODEC_SCHEDULES[arm]) == SHEAR_OPERATIONS == 49
    encoded = encode_bits(bits, arm)
    assert decode_bits(encoded, arm) == bits


def test_literal_codec_schedules() -> None:
    assert CODEC_SCHEDULES[CodecArm.STRUCT][:7] == (
        (16, 8), (32, 24), (40, 0), (48, 0), (56, 0), (64, 0),
        (17, 9),
    )
    assert CODEC_SCHEDULES[CodecArm.STRUCT][-1] == (107, 108)
    assert CODEC_SCHEDULES[CodecArm.SHAM][-1] == (107, 109)
    assert CODEC_SCHEDULES[CodecArm.RAW][:5] == ((1, 0), (3, 2), (5, 4), (7, 6), (9, 8))
    assert CODEC_SCHEDULES[CodecArm.RAW][-1] == (97, 96)


def test_exact_address_support_nonce_pairing_and_batches() -> None:
    train = panel_addresses(Purpose.MAIN, 3, Split.TRAIN)
    evaluation = panel_addresses(Purpose.MAIN, 3, Split.EVAL)
    assert len(train) == len(evaluation) == 48 * 16
    assert train[0].components() == ("CBSC-LR01", "MAIN", 3, "TRAIN", 0, 0)
    assert train[-1].components() == ("CBSC-LR01", "MAIN", 3, "TRAIN", 47, 15)
    assert {(row.carrier_nonce, row.body_nonce) for row in train} == {
        (64 + ((slot + 3) % 16), 96 + ((slot + 6) % 16)) for slot in range(16)
    }
    assert {(row.carrier_nonce, row.body_nonce) for row in evaluation} == {
        (64 + ((slot + 3) % 16), 96 + ((slot + 14) % 16)) for slot in range(16)
    }
    assert {
        (row.cell, row.carrier_nonce, row.body_nonce) for row in train
    }.isdisjoint({(row.cell, row.carrier_nonce, row.body_nonce) for row in evaluation})
    batch = batch_addresses(Purpose.MAIN, 3, Split.TRAIN, 5)
    assert len(batch) == 96
    assert [row.slot for row in batch[:4]] == [10, 11, 10, 11]
    assert {row.cell for row in batch} == set(range(48))


def test_address_and_bit_validation_fail_closed() -> None:
    with pytest.raises(ValueError):
        Address(Purpose.MAIN, 0, Split.TRAIN, 48, 0)
    fields = _fields()
    fields.pop("public_z1")
    with pytest.raises(ValueError, match="field key mismatch"):
        canonical_bits(fields, _address())
    with pytest.raises(ValueError, match="exactly 112"):
        encode_bits([0] * 111, CodecArm.RAW)
    with pytest.raises(ValueError, match="MAIN block"):
        Address(Purpose.MAIN, 24, Split.TRAIN, 0, 0)
    with pytest.raises(ValueError, match="COMPETENCE block"):
        Address(Purpose.COMPETENCE, 4, Split.TRAIN, 0, 0)


def test_address_text_is_canonical_ascii_json() -> None:
    address = Address(Purpose.MAIN, 2, Split.EVAL, 7, 9)
    assert address.text() == '["CBSC-LR01","MAIN",2,"EVAL",7,9]'


def test_public_packer_rejects_width_valid_but_scientifically_noncanonical_fields() -> None:
    fields = _fields()
    fields["owner_current"] = 255
    with pytest.raises(ValueError, match="OWNER code"):
        canonical_bits(fields, _address())
    fields = _fields()
    fields["presentation_slot"] = 130
    with pytest.raises(ValueError, match="presentation slot"):
        canonical_bits(fields, _address())
