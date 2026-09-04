"""Canonical CBSC-LR01 context addresses and 112-bit packing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Final, Mapping

from .contract import CELLS, FIELD_LAYOUT, INPUT_BITS, PROTOCOL_ID, SLOTS


class Purpose(str, Enum):
    MAIN = "MAIN"
    COMPETENCE = "COMPETENCE"


class Split(str, Enum):
    TRAIN = "TRAIN"
    EVAL = "EVAL"


FIELD_WIDTHS: Final = {name: width for name, _offset, width in FIELD_LAYOUT}


@dataclass(frozen=True, order=True)
class Address:
    purpose: Purpose
    block: int
    split: Split
    cell: int
    slot: int

    def __post_init__(self) -> None:
        limit = 24 if self.purpose is Purpose.MAIN else 4
        if type(self.block) is not int or not 0 <= self.block < limit:
            raise ValueError(f"{self.purpose.value} block must be in [0,{limit})")
        if type(self.cell) is not int or not 0 <= self.cell < CELLS:
            raise ValueError(f"cell must be in [0,{CELLS})")
        if type(self.slot) is not int or not 0 <= self.slot < SLOTS:
            raise ValueError(f"slot must be in [0,{SLOTS})")

    def components(self) -> tuple[str, str, int, str, int, int]:
        return (PROTOCOL_ID, self.purpose.value, self.block, self.split.value, self.cell, self.slot)

    def text(self) -> str:
        return json.dumps(
            list(self.components()), ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        )

    @property
    def carrier_nonce(self) -> int:
        return 64 + ((self.slot + self.block) % 16)

    @property
    def body_nonce(self) -> int:
        shift = {
            (Purpose.MAIN, Split.TRAIN): 3,
            (Purpose.MAIN, Split.EVAL): 11,
            (Purpose.COMPETENCE, Split.TRAIN): 5,
            (Purpose.COMPETENCE, Split.EVAL): 13,
        }[(self.purpose, self.split)]
        return 96 + ((self.slot + self.block + shift) % 16)


def panel_addresses(purpose: Purpose, block: int, split: Split) -> tuple[Address, ...]:
    """Return the exact 48-cell by 16-slot census in canonical cell/slot order."""

    return tuple(Address(purpose, block, split, cell, slot) for cell in range(CELLS) for slot in range(SLOTS))


def batch_addresses(purpose: Purpose, block: int, split: Split, batch_id: int) -> tuple[Address, ...]:
    """Return one 96-context batch: slots {2j,2j+1} in all cells."""

    if type(batch_id) is not int or not 0 <= batch_id < 8:
        raise ValueError("batch_id must be in [0,8)")
    slots = (2 * batch_id, 2 * batch_id + 1)
    return tuple(Address(purpose, block, split, cell, slot) for cell in range(CELLS) for slot in slots)


def _pack_bits(fields: Mapping[str, int]) -> tuple[int, ...]:
    expected = set(FIELD_WIDTHS)
    if set(fields) != expected:
        missing = sorted(expected - set(fields))
        extra = sorted(set(fields) - expected)
        raise ValueError(f"canonical field key mismatch: missing={missing}, extra={extra}")
    bits = [0] * INPUT_BITS
    for name, offset, width in FIELD_LAYOUT:
        value = fields[name]
        if type(value) is not int or not 0 <= value < 2**width:
            raise ValueError(f"{name} must be an integer in [0,{2**width})")
        for bit in range(width):
            bits[offset + bit] = (value >> bit) & 1
    return tuple(bits)


def validate_canonical_fields(fields: Mapping[str, int], address: Address) -> None:
    if not isinstance(address, Address):
        raise TypeError("canonical scientific packing requires an Address")
    expected = set(FIELD_WIDTHS)
    if set(fields) != expected:
        missing = sorted(expected - set(fields))
        extra = sorted(set(fields) - expected)
        raise ValueError(f"canonical field key mismatch: missing={missing}, extra={extra}")
    binary = {
        "focal_need_active", "access_binding_gated", "body_native_neutral",
        "body_content_bit", "focal_need_bit", "public_z0", "public_z1",
        "presentation_flip",
    }
    if any(type(fields[name]) is not int or fields[name] not in (0, 1) for name in binary):
        raise ValueError("canonical flags must be integer binary values")
    receiver = fields["physical_receiver"]
    if receiver not in (0, 1):
        raise ValueError("physical_receiver must be 0 or 1")
    owner_previous = fields["owner_predecessor"]
    if owner_previous not in (16, 18) or fields["owner_current"] not in (owner_previous, owner_previous + 1):
        raise ValueError("noncanonical OWNER code relation")
    body_epoch = fields["body_epoch"]
    if body_epoch not in (32, 34) or fields["current_epoch"] not in (body_epoch, body_epoch + 1):
        raise ValueError("noncanonical epoch code relation")
    if any(fields[name] not in (0, 1) for name in (
        "associated_carrier_issued_to", "execution_carrier_issued_to", "body_addressed_receiver",
    )):
        raise ValueError("noncanonical receiver token")
    if fields["body_addressed_receiver"] != fields["execution_carrier_issued_to"]:
        raise ValueError("body address must equal execution carrier receiver")
    gated = fields["access_binding_gated"]
    expected_execution = fields["associated_carrier_issued_to"] if gated else receiver
    if fields["execution_carrier_issued_to"] != expected_execution:
        raise ValueError("execution carrier violates OPEN/GATED law")
    source = fields["payload_source_receiver"]
    neutral = fields["body_native_neutral"]
    active = fields["focal_need_active"]
    if neutral != (source == 255) or active != (not neutral):
        raise ValueError("neutral/source/active sentinel law mismatch")
    if source not in (0, 1, 255) or (neutral and fields["body_content_bit"] != 0):
        raise ValueError("noncanonical payload source/content")
    if not 64 <= fields["carrier_nonce"] <= 79 or not 96 <= fields["body_nonce"] <= 111:
        raise ValueError("noncanonical nonce code")
    if fields["presentation_slot"] != 128 + (receiver ^ fields["presentation_flip"]):
        raise ValueError("noncanonical presentation slot")
    if fields["public_phase"] != 144 + ((fields["public_z0"] << 1) | fields["public_z1"]):
        raise ValueError("noncanonical public phase")
    q = address.slot
    r = q & 1
    presentation = (q >> 1) & 1
    old = ((q >> 2) & 1, (q >> 3) & 1)
    z = (((q >> 1) ^ (q >> 2)) & 1, ((q >> 1) ^ (q >> 3)) & 1)
    owner, remainder = divmod(address.cell, 24)
    semantic, remainder = divmod(remainder, 12)
    binding, remainder = divmod(remainder, 6)
    access, payload = divmod(remainder, 3)
    expected_owner_previous = 16 + 2 * ((q >> 2) & 1)
    expected_body_epoch = 32 + 2 * ((q >> 3) & 1)
    expected_associated = r if binding == 0 else 1 - r
    expected_execution = r if access == 0 else expected_associated
    expected_source = 255 if payload == 2 else expected_execution if payload == 0 else 1 - expected_execution
    expected_content = 0 if payload == 2 else old[expected_source] ^ z[expected_source]
    expected_need = (old[r] if semantic == 0 else 1 - old[r]) ^ z[r]
    expected = {
        "physical_receiver": r,
        "owner_predecessor": expected_owner_previous,
        "owner_current": expected_owner_previous if owner == 0 else expected_owner_previous + 1,
        "body_epoch": expected_body_epoch,
        "current_epoch": expected_body_epoch if semantic == 0 else expected_body_epoch + 1,
        "associated_carrier_issued_to": expected_associated,
        "execution_carrier_issued_to": expected_execution,
        "body_addressed_receiver": expected_execution,
        "payload_source_receiver": expected_source,
        "carrier_nonce": address.carrier_nonce,
        "body_nonce": address.body_nonce,
        "presentation_slot": 128 + (r ^ presentation),
        "public_phase": 144 + ((z[0] << 1) | z[1]),
        "focal_need_active": int(payload != 2),
        "access_binding_gated": access,
        "body_native_neutral": int(payload == 2),
        "body_content_bit": expected_content,
        "focal_need_bit": expected_need,
        "public_z0": z[0], "public_z1": z[1], "presentation_flip": presentation,
    }
    if dict(fields) != expected:
        mismatch = next(name for name in expected if fields[name] != expected[name])
        raise ValueError(f"field does not match canonical scientific address: {mismatch}")


def canonical_bits(fields: Mapping[str, int], address: Address) -> tuple[int, ...]:
    """Validate and pack the sole canonical scientific primitive layout."""

    validate_canonical_fields(fields, address)
    return _pack_bits(fields)


def unpack_bits(bits: tuple[int, ...]) -> dict[str, int]:
    if len(bits) != INPUT_BITS or any(type(bit) is not int or bit not in (0, 1) for bit in bits):
        raise ValueError(f"canonical input must be exactly {INPUT_BITS} integer binary bits")
    fields: dict[str, int] = {}
    for name, offset, width in FIELD_LAYOUT:
        fields[name] = sum(bits[offset + bit] << bit for bit in range(width))
    return fields


__all__ = [
    "Address", "FIELD_WIDTHS", "Purpose", "Split", "batch_addresses", "canonical_bits",
    "panel_addresses", "unpack_bits", "validate_canonical_fields",
]
