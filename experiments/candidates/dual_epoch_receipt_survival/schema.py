"""Fixed nonlearned 192-bit token schema and arm information masks."""

from __future__ import annotations

from typing import Final, Iterable

import torch

from .domain import (
    GRU_DUAL, GRU_ORACLE, GRU_RAW, GRU_SNAPSHOT, GRU_UNBOUND,
    GRU_VALIDITY, Example, LeaseUpdate, OwnerUpdate, Receipt, Version,
)
from .verifier import verify_example


TOKEN_WIDTH: Final = 192
SEQUENCE_LENGTH: Final = 6
KIND_SLICE: Final = slice(0, 5)
SLOT_0_SLICE: Final = slice(5, 69)
SLOT_1_SLICE: Final = slice(69, 133)
EVENT_TIME_SLICE: Final = slice(133, 149)
VALID_FROM_SLICE: Final = slice(149, 165)
VALID_UNTIL_SLICE: Final = slice(165, 181)
PRESENCE_INDICES: Final = {
    "slot_0": 181, "slot_1": 182, "event_time": 183,
    "valid_from": 184, "valid_until": 185,
}
FLAG_INDICES: Final = {
    "displayed_content": 186, "tag_ok": 187, "issuer_allowed": 188,
    "live": 189, "bottom": 190,
}
PADDING_INDEX: Final = 191
KINDS: Final = {"MASK": 0, "RECEIPT": 1, "OWNER_UPDATE": 2, "LEASE_UPDATE": 3, "DECISION": 4}


TOKEN_SCHEMA = {
    "width": TOKEN_WIDTH,
    "sequence_length": SEQUENCE_LENGTH,
    "kind_one_hot": {key: value for key, value in KINDS.items()},
    "tuple_slots": {
        "slot_0": {"range": [5, 69], "layout": "handle:u32 then epoch:u32, MSB-first"},
        "slot_1": {"range": [69, 133], "layout": "handle:u32 then epoch:u32, MSB-first"},
    },
    "signed_time_fields": {
        "event_time": [133, 149], "valid_from": [149, 165], "valid_until": [165, 181],
        "encoding": "signed int16 two's-complement, MSB-first",
    },
    "presence_bits": dict(PRESENCE_INDICES),
    "flags": dict(FLAG_INDICES),
    "zero_padding": [PADDING_INDEX],
    "dtype": "float32 binary {0,1}",
}

MASK_CONTRACT = {
    GRU_DUAL: {
        "history": "five MASK tokens",
        "decision_extra": "live in live; displayed content only if live; bottom iff not live",
    },
    GRU_SNAPSHOT: {"history": "five MASK tokens", "decision_extra": "none"},
    GRU_UNBOUND: {
        "history": "five MASK tokens",
        "decision_extra": "A in tag_ok semantic channel; displayed content always",
    },
    GRU_VALIDITY: {"history": "five MASK tokens", "decision_extra": "live in live only"},
    GRU_ORACLE: {
        "history": "five MASK tokens",
        "decision_extra": "A,O,L in tag_ok/issuer_allowed/live semantic channels; displayed content always",
    },
    GRU_RAW: {
        "history": "receipt and four chronological raw updates",
        "decision_extra": "none; primitive tag_ok/issuer_allowed only; no O,L,live",
    },
    "common_decision": (
        "decision kind, final current owner tuple, final current lease tuple, "
        "decision time 0, final visible lease interval; all other final visible fields are constants"
    ),
    "label_absent": True,
}


def _unsigned_bits(value: int, width: int) -> list[float]:
    if not 0 <= int(value) < 2**width:
        raise ValueError(f"value outside u{width}: {value}")
    return [float((int(value) >> shift) & 1) for shift in reversed(range(width))]


def _signed_bits(value: int) -> list[float]:
    if not -(2**15) <= int(value) < 2**15:
        raise ValueError(f"value outside i16: {value}")
    return _unsigned_bits(int(value) & 0xFFFF, 16)


def _put_version(token: torch.Tensor, field: slice, value: Version) -> None:
    token[field] = torch.tensor(
        _unsigned_bits(value.handle, 32) + _unsigned_bits(value.epoch, 32),
        dtype=torch.float32,
    )


def _put_time(token: torch.Tensor, field: slice, value: int) -> None:
    token[field] = torch.tensor(_signed_bits(value), dtype=torch.float32)


def _token(kind: str) -> torch.Tensor:
    row = torch.zeros(TOKEN_WIDTH, dtype=torch.float32)
    row[KINDS[kind]] = 1.0
    return row


def encode_event(event: Receipt | OwnerUpdate | LeaseUpdate) -> torch.Tensor:
    if isinstance(event, Receipt):
        row = _token("RECEIPT")
        _put_version(row, SLOT_0_SLICE, event.owner_anchor)
        _put_version(row, SLOT_1_SLICE, event.lease_anchor)
        _put_time(row, EVENT_TIME_SLICE, event.event_time)
        _put_time(row, VALID_FROM_SLICE, event.valid_from)
        _put_time(row, VALID_UNTIL_SLICE, event.valid_until)
        row[list(PRESENCE_INDICES.values())] = 1.0
        row[FLAG_INDICES["displayed_content"]] = float(event.displayed_bit)
        row[FLAG_INDICES["tag_ok"]] = float(event.tag_ok)
        row[FLAG_INDICES["issuer_allowed"]] = float(event.issuer_allowed)
        return row
    if isinstance(event, OwnerUpdate):
        row = _token("OWNER_UPDATE")
        _put_version(row, SLOT_0_SLICE, event.from_version)
        _put_version(row, SLOT_1_SLICE, event.to_version)
        _put_time(row, EVENT_TIME_SLICE, event.event_time)
        row[PRESENCE_INDICES["slot_0"]] = 1.0
        row[PRESENCE_INDICES["slot_1"]] = 1.0
        row[PRESENCE_INDICES["event_time"]] = 1.0
        return row
    if isinstance(event, LeaseUpdate):
        row = _token("LEASE_UPDATE")
        _put_version(row, SLOT_0_SLICE, event.from_version)
        _put_version(row, SLOT_1_SLICE, event.to_version)
        _put_time(row, EVENT_TIME_SLICE, event.event_time)
        _put_time(row, VALID_FROM_SLICE, event.valid_from)
        _put_time(row, VALID_UNTIL_SLICE, event.valid_until)
        row[list(PRESENCE_INDICES.values())] = 1.0
        return row
    raise TypeError("unsupported event type")


def _decision(example: Example) -> torch.Tensor:
    row = _token("DECISION")
    _put_version(row, SLOT_0_SLICE, example.final_owner)
    _put_version(row, SLOT_1_SLICE, example.final_lease)
    _put_time(row, EVENT_TIME_SLICE, 0)
    _put_time(row, VALID_FROM_SLICE, example.final_valid_from)
    _put_time(row, VALID_UNTIL_SLICE, example.final_valid_until)
    row[list(PRESENCE_INDICES.values())] = 1.0
    return row


def encode_example(example: Example, arm: str) -> torch.Tensor:
    decision = _decision(example)
    if arm == GRU_RAW:
        history = [encode_event(event) for event in example.events]
    else:
        history = [_token("MASK") for _ in range(5)]
        verification = verify_example(example)
        if arm == GRU_DUAL:
            decision[FLAG_INDICES["live"]] = float(verification.live)
            decision[FLAG_INDICES["bottom"]] = float(not verification.live)
            if verification.live:
                decision[FLAG_INDICES["displayed_content"]] = float(verification.content)
        elif arm == GRU_SNAPSHOT:
            pass
        elif arm == GRU_UNBOUND:
            decision[FLAG_INDICES["tag_ok"]] = float(example.authentication)
            decision[FLAG_INDICES["displayed_content"]] = float(example.displayed_bit)
        elif arm == GRU_VALIDITY:
            decision[FLAG_INDICES["live"]] = float(example.live)
        elif arm == GRU_ORACLE:
            decision[FLAG_INDICES["tag_ok"]] = float(example.authentication)
            decision[FLAG_INDICES["issuer_allowed"]] = float(example.owner_survives)
            decision[FLAG_INDICES["live"]] = float(example.lease_survives)
            decision[FLAG_INDICES["displayed_content"]] = float(example.displayed_bit)
        else:
            raise ValueError(f"unknown arm {arm!r}")
    result = torch.stack((*history, decision))
    if tuple(result.shape) != (SEQUENCE_LENGTH, TOKEN_WIDTH):
        raise AssertionError("token shape drift")
    if result[PADDING_INDEX].any() if result.ndim == 1 else result[:, PADDING_INDEX].any():
        raise AssertionError("padding must remain zero")
    return result


def encode_panel(examples: Iterable[Example], arm: str) -> tuple[torch.Tensor, torch.Tensor]:
    rows = list(examples)
    inputs = torch.stack([encode_example(row, arm) for row in rows])
    labels = torch.tensor([int(row.correct_action) for row in rows], dtype=torch.long)
    return inputs, labels


def audit_information_partitions(examples: Iterable[Example]) -> dict[str, object]:
    """Prove the matched observational equivalence classes in every superblock."""
    rows = list(examples)
    blocks: dict[int, list[Example]] = {}
    for row in rows:
        blocks.setdefault(row.superblock, []).append(row)
    expected_unique = {
        GRU_SNAPSHOT: 1, GRU_UNBOUND: 4, GRU_VALIDITY: 2,
        GRU_DUAL: 3, GRU_ORACLE: 16,
    }
    worst_shared_label_count = {arm: 1 for arm in expected_unique}
    for block in blocks.values():
        if len(block) != 16 or {row.core_index for row in block} != set(range(16)):
            raise ValueError("incomplete matched superblock")
        for arm, expected in expected_unique.items():
            observations: dict[bytes, set[int]] = {}
            for row in block:
                encoded = encode_example(row, arm).numpy().tobytes()
                observations.setdefault(encoded, set()).add(int(row.correct_action))
            if len(observations) != expected:
                raise ValueError(f"{arm} information partition drift")
            worst_shared_label_count[arm] = max(
                worst_shared_label_count[arm], max(len(labels) for labels in observations.values())
            )
    structural_ceilings = {
        arm: 1.0 / label_count for arm, label_count in worst_shared_label_count.items()
    }
    if structural_ceilings[GRU_SNAPSHOT] != 1 / 3:
        raise ValueError("snapshot structural ceiling drift")
    if structural_ceilings[GRU_UNBOUND] != 1 / 2 or structural_ceilings[GRU_VALIDITY] != 1 / 2:
        raise ValueError("unbound/validity structural ceiling drift")
    return {
        "superblocks_checked": len(blocks),
        "variants_per_superblock": 16,
        "unique_observations_per_superblock": expected_unique,
        "maximum_correct_labels_sharing_one_observation": worst_shared_label_count,
        "structural_maximin_ceilings": structural_ceilings,
    }
