"""Literal public primitive-token codec for CBSC-OMRC-B01.

Only the seventeen public bytes enter this module. Evaluator truth, reward,
oracle values, future facts, arm labels, and result identity have no codec
surface.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from typing import Iterable

import numpy as np

from .contract import PREACTION_KINDS, EventKind, OpportunityPosition, PrimitiveKind


ABSENT_BYTE = 255
NEUTRAL_PAYLOAD_SOURCE = 254
BYTE_COUNT = 16
FLAG_COUNT = 8
PACKED_BYTE_COUNT = 17
CHANNEL_COUNT = 136


class TokenValidationError(ValueError):
    """Raised when a public token contradicts the literal schema."""


class ByteField(str, Enum):
    EVENT_KIND = "event_kind"
    SUBJECT_RECEIVER = "subject_receiver"
    TARGET_RECEIVER = "target_receiver"
    SLOT = "slot"
    CARRIER = "carrier"
    OWNER_OLD = "owner_old"
    OWNER_NEW = "owner_new"
    EPOCH_OLD = "epoch_old"
    EPOCH_NEW = "epoch_new"
    BODY_OWNER = "body_owner"
    BODY_EPOCH = "body_epoch"
    BODY_ADDRESSED_RECEIVER = "body_addressed_receiver"
    PAYLOAD_SOURCE_RECEIVER = "payload_source_receiver"
    CAPABILITY_RECEIVER = "capability_receiver"
    OPPORTUNITY_INDEX = "opportunity_index"
    EVENT_ORDER_POSITION = "event_order_position"


class FlagField(str, Enum):
    OLD_NEED = "old_need"
    NEW_NEED = "new_need"
    BODY_CONTENT = "body_content"
    BODY_NATIVE_NEUTRAL = "body_native_neutral"
    ACCESS_GATED = "access_gated"
    REQUEST_ACTIVE = "request_active"
    REQUEST_NEED = "request_need"
    RESERVED_ZERO = "reserved_zero"


BYTE_FIELD_ORDER = tuple(ByteField)
FLAG_FIELD_ORDER = tuple(FlagField)
_NON_KIND_BYTE_FIELDS = frozenset(BYTE_FIELD_ORDER[1:])


def _validate_plain_byte(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise TokenValidationError(f"{name} must be an integer byte")


@dataclass(frozen=True)
class EventKindLayout:
    """One codebook entry and its exact public byte/flag surface.

    ``PrimitiveKind`` remains accepted for pre-clarification semantic-core
    fixtures. Production adapters require the literal ``EventKind`` entries.
    """

    kind: PrimitiveKind | EventKind
    code: int
    required_byte_fields: frozenset[ByteField] = frozenset()
    optional_byte_fields: frozenset[ByteField] = frozenset()
    allowed_flag_fields: frozenset[FlagField] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, (PrimitiveKind, EventKind)):
            raise TokenValidationError("layout kind must be PrimitiveKind or EventKind")
        _validate_plain_byte("layout code", self.code)
        if self.code in (NEUTRAL_PAYLOAD_SOURCE, ABSENT_BYTE):
            raise TokenValidationError("event-kind code cannot use a reserved sentinel")
        if isinstance(self.kind, EventKind) and self.code != int(self.kind):
            raise TokenValidationError("literal EventKind code must equal its fixed numeric value")
        byte_fields = self.required_byte_fields | self.optional_byte_fields
        if not all(isinstance(item, ByteField) for item in byte_fields):
            raise TokenValidationError("layout byte fields must be ByteField values")
        if ByteField.EVENT_KIND in byte_fields:
            raise TokenValidationError("event_kind is implicit and cannot be a layout field")
        if not byte_fields <= _NON_KIND_BYTE_FIELDS:
            raise TokenValidationError("layout contains an unknown byte field")
        if self.required_byte_fields & self.optional_byte_fields:
            raise TokenValidationError("required and optional byte fields must be disjoint")
        if not all(isinstance(item, FlagField) for item in self.allowed_flag_fields):
            raise TokenValidationError("layout flag fields must be FlagField values")
        if FlagField.RESERVED_ZERO in self.allowed_flag_fields:
            raise TokenValidationError("reserved_zero can never be enabled by a layout")

    @property
    def bmask(self) -> int:
        """Mask over bytes 0..15; byte zero is always the event kind."""

        selected = {ByteField.EVENT_KIND} | set(self.required_byte_fields) | set(
            self.optional_byte_fields
        )
        return sum(1 << BYTE_FIELD_ORDER.index(field) for field in selected)

    @property
    def fmask(self) -> int:
        """Mask over the eight packed flags."""

        return sum(1 << FLAG_FIELD_ORDER.index(field) for field in self.allowed_flag_fields)


@dataclass(frozen=True)
class PrimitiveToken:
    event_kind: int
    subject_receiver: int = ABSENT_BYTE
    target_receiver: int = ABSENT_BYTE
    slot: int = ABSENT_BYTE
    carrier: int = ABSENT_BYTE
    owner_old: int = ABSENT_BYTE
    owner_new: int = ABSENT_BYTE
    epoch_old: int = ABSENT_BYTE
    epoch_new: int = ABSENT_BYTE
    body_owner: int = ABSENT_BYTE
    body_epoch: int = ABSENT_BYTE
    body_addressed_receiver: int = ABSENT_BYTE
    payload_source_receiver: int = ABSENT_BYTE
    capability_receiver: int = ABSENT_BYTE
    opportunity_index: int = ABSENT_BYTE
    event_order_position: int = ABSENT_BYTE
    old_need: bool = False
    new_need: bool = False
    body_content: bool = False
    body_native_neutral: bool = False
    access_gated: bool = False
    request_active: bool = False
    request_need: bool = False
    reserved_zero: bool = False

    def __post_init__(self) -> None:
        for field in fields(self)[:BYTE_COUNT]:
            _validate_plain_byte(field.name, getattr(self, field.name))
        for field in fields(self)[BYTE_COUNT:]:
            if type(getattr(self, field.name)) is not bool:
                raise TokenValidationError(f"{field.name} must be bool")
        if self.reserved_zero:
            raise TokenValidationError("reserved_zero must be false")
        _validate_known_field_domains(self)

    def byte_values(self) -> tuple[int, ...]:
        return tuple(int(getattr(self, field.value)) for field in BYTE_FIELD_ORDER)

    def flag_values(self) -> tuple[bool, ...]:
        return tuple(getattr(self, field.value) for field in FLAG_FIELD_ORDER)


@dataclass(frozen=True)
class LearnerProjection:
    """Immutable public bytes only; evaluator and result fields cannot enter."""

    packed: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.packed, bytes) or len(self.packed) != PACKED_BYTE_COUNT:
            raise TokenValidationError("learner projection must hold exactly 17 bytes")

    def float32_channels(self) -> np.ndarray:
        return bytes_to_lsb_float32(self.packed, expected_bytes=PACKED_BYTE_COUNT)


class CanonicalTokenCodec:
    """Strict codec; omission of ``layouts`` selects the frozen literal codebook."""

    def __init__(self, layouts: Iterable[EventKindLayout] | None = None) -> None:
        entries = tuple(LITERAL_EVENT_LAYOUTS if layouts is None else layouts)
        if not entries:
            raise TokenValidationError("at least one event-kind layout is required")
        if len({entry.code for entry in entries}) != len(entries):
            raise TokenValidationError("event-kind codes must be unique")
        if len({entry.kind for entry in entries}) != len(entries):
            raise TokenValidationError("event kinds must be unique")
        self._by_code = {entry.code: entry for entry in entries}
        self._by_kind = {entry.kind: entry for entry in entries}

    def code_for(self, kind: PrimitiveKind | EventKind) -> int:
        try:
            return self._by_kind[kind].code
        except (KeyError, TypeError) as error:
            raise TokenValidationError(f"no code is registered for {kind!r}") from error

    def kind_for(self, code: int) -> PrimitiveKind | EventKind:
        try:
            return self._by_code[code].kind
        except (KeyError, TypeError) as error:
            raise TokenValidationError(f"unknown event-kind code {code!r}") from error

    def layout_for(self, code: int | EventKind) -> EventKindLayout:
        try:
            return self._by_code[int(code)]
        except (KeyError, TypeError, ValueError) as error:
            raise TokenValidationError(f"unknown event-kind code {code!r}") from error

    def validate(self, token: PrimitiveToken) -> EventKindLayout:
        if not isinstance(token, PrimitiveToken):
            raise TokenValidationError("token must be PrimitiveToken")
        try:
            layout = self._by_code[token.event_kind]
        except KeyError as error:
            raise TokenValidationError(
                f"event_kind {token.event_kind} is absent from the external codebook"
            ) from error
        present = frozenset(
            field for field in _NON_KIND_BYTE_FIELDS if getattr(token, field.value) != ABSENT_BYTE
        )
        allowed = layout.required_byte_fields | layout.optional_byte_fields
        missing = layout.required_byte_fields - present
        illegal = present - allowed
        if missing:
            raise TokenValidationError(
                "required fields are absent: " + ", ".join(sorted(item.value for item in missing))
            )
        if illegal:
            raise TokenValidationError(
                "fields are illegal for event kind: "
                + ", ".join(sorted(item.value for item in illegal))
            )
        enabled_flags = frozenset(
            field for field in FLAG_FIELD_ORDER if getattr(token, field.value)
        )
        illegal_flags = enabled_flags - layout.allowed_flag_fields
        if illegal_flags:
            raise TokenValidationError(
                "flags are illegal for event kind: "
                + ", ".join(sorted(item.value for item in illegal_flags))
            )
        _validate_kind_clock(layout.kind, token)
        return layout

    def pack(self, token: PrimitiveToken) -> bytes:
        self.validate(token)
        flag_byte = sum(int(value) << bit for bit, value in enumerate(token.flag_values()))
        return bytes((*token.byte_values(), flag_byte))

    def unpack(self, packed: bytes) -> PrimitiveToken:
        if not isinstance(packed, bytes) or len(packed) != PACKED_BYTE_COUNT:
            raise TokenValidationError("packed token must be exactly 17 bytes")
        flag_byte = packed[-1]
        values = dict(zip((field.value for field in BYTE_FIELD_ORDER), packed[:BYTE_COUNT]))
        values.update(
            {
                field.value: bool((flag_byte >> bit) & 1)
                for bit, field in enumerate(FLAG_FIELD_ORDER)
            }
        )
        token = PrimitiveToken(**values)
        self.validate(token)
        return token

    def project_for_learner(self, token: PrimitiveToken) -> LearnerProjection:
        return LearnerProjection(self.pack(token))

    def encode_float32(self, token: PrimitiveToken) -> np.ndarray:
        return self.project_for_learner(token).float32_channels()


def _fields(*values: ByteField) -> frozenset[ByteField]:
    return frozenset(values)


def _flags(*values: FlagField) -> frozenset[FlagField]:
    return frozenset(values)


LITERAL_EVENT_LAYOUTS = (
    EventKindLayout(EventKind.INIT_OWNER, EventKind.INIT_OWNER, _fields(
        ByteField.SUBJECT_RECEIVER, ByteField.OWNER_NEW, ByteField.EVENT_ORDER_POSITION)),
    EventKindLayout(EventKind.INIT_SEMANTIC, EventKind.INIT_SEMANTIC, _fields(
        ByteField.SUBJECT_RECEIVER, ByteField.EPOCH_NEW, ByteField.EVENT_ORDER_POSITION),
        allowed_flag_fields=_flags(FlagField.NEW_NEED)),
    EventKindLayout(EventKind.INIT_CAPABILITY, EventKind.INIT_CAPABILITY, _fields(
        ByteField.CARRIER, ByteField.CAPABILITY_RECEIVER, ByteField.EVENT_ORDER_POSITION)),
    EventKindLayout(EventKind.INIT_BODY, EventKind.INIT_BODY, _fields(
        ByteField.SLOT, ByteField.CARRIER, ByteField.BODY_OWNER, ByteField.BODY_EPOCH,
        ByteField.BODY_ADDRESSED_RECEIVER, ByteField.PAYLOAD_SOURCE_RECEIVER,
        ByteField.EVENT_ORDER_POSITION),
        allowed_flag_fields=_flags(FlagField.BODY_CONTENT, FlagField.BODY_NATIVE_NEUTRAL)),
    EventKindLayout(EventKind.OWNER, EventKind.OWNER, _fields(
        ByteField.SUBJECT_RECEIVER, ByteField.OWNER_OLD, ByteField.OWNER_NEW,
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION)),
    EventKindLayout(EventKind.SEMANTIC, EventKind.SEMANTIC, _fields(
        ByteField.SUBJECT_RECEIVER, ByteField.EPOCH_OLD, ByteField.EPOCH_NEW,
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION),
        allowed_flag_fields=_flags(FlagField.OLD_NEED, FlagField.NEW_NEED)),
    EventKindLayout(EventKind.CAPABILITY, EventKind.CAPABILITY, _fields(
        ByteField.CARRIER, ByteField.CAPABILITY_RECEIVER, ByteField.OPPORTUNITY_INDEX,
        ByteField.EVENT_ORDER_POSITION)),
    EventKindLayout(EventKind.BODY, EventKind.BODY, _fields(
        ByteField.SLOT, ByteField.CARRIER, ByteField.BODY_OWNER, ByteField.BODY_EPOCH,
        ByteField.BODY_ADDRESSED_RECEIVER, ByteField.PAYLOAD_SOURCE_RECEIVER,
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION),
        allowed_flag_fields=_flags(FlagField.BODY_CONTENT, FlagField.BODY_NATIVE_NEUTRAL)),
    *(EventKindLayout(kind, kind, _fields(
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION)) for kind in (
            EventKind.NOOP_OWNER, EventKind.NOOP_SEMANTIC,
            EventKind.NOOP_CAPABILITY, EventKind.NOOP_BODY)),
    EventKindLayout(EventKind.DECISION, EventKind.DECISION, _fields(
        ByteField.TARGET_RECEIVER, ByteField.SLOT, ByteField.CARRIER,
        ByteField.BODY_OWNER, ByteField.BODY_EPOCH, ByteField.BODY_ADDRESSED_RECEIVER,
        ByteField.PAYLOAD_SOURCE_RECEIVER, ByteField.CAPABILITY_RECEIVER,
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION),
        allowed_flag_fields=_flags(
            FlagField.BODY_CONTENT, FlagField.BODY_NATIVE_NEUTRAL,
            FlagField.ACCESS_GATED, FlagField.REQUEST_ACTIVE, FlagField.REQUEST_NEED)),
    EventKindLayout(EventKind.SETTLEMENT, EventKind.SETTLEMENT, _fields(
        ByteField.OPPORTUNITY_INDEX, ByteField.EVENT_ORDER_POSITION)),
)

LITERAL_TOKEN_CODEC = CanonicalTokenCodec(LITERAL_EVENT_LAYOUTS)

_EXPECTED_MASKS = {
    EventKind.INIT_OWNER: (0x8043, 0x00), EventKind.INIT_SEMANTIC: (0x8103, 0x02),
    EventKind.INIT_CAPABILITY: (0xA011, 0x00), EventKind.INIT_BODY: (0x9E19, 0x0C),
    EventKind.OWNER: (0xC063, 0x00), EventKind.SEMANTIC: (0xC183, 0x03),
    EventKind.CAPABILITY: (0xE011, 0x00), EventKind.BODY: (0xDE19, 0x0C),
    EventKind.NOOP_OWNER: (0xC001, 0x00), EventKind.NOOP_SEMANTIC: (0xC001, 0x00),
    EventKind.NOOP_CAPABILITY: (0xC001, 0x00), EventKind.NOOP_BODY: (0xC001, 0x00),
    EventKind.DECISION: (0xFE1D, 0x7C), EventKind.SETTLEMENT: (0xC001, 0x00),
}
assert {layout.kind: (layout.bmask, layout.fmask) for layout in LITERAL_EVENT_LAYOUTS} == _EXPECTED_MASKS


def bytes_to_lsb_float32(packed: bytes, *, expected_bytes: int) -> np.ndarray:
    """Expand bytes in byte order and then least-significant-bit first."""

    if not isinstance(packed, bytes) or len(packed) != expected_bytes:
        raise TokenValidationError(f"projection requires exactly {expected_bytes} bytes")
    raw = np.frombuffer(packed, dtype=np.uint8)
    channels = ((raw[:, None] >> np.arange(8, dtype=np.uint8)) & 1).reshape(-1)
    result = channels.astype(np.float32, copy=False)
    if result.shape != (expected_bytes * 8,) or result.dtype != np.float32:
        raise AssertionError("LSB projection must be a one-dimensional FP32 vector")
    return result.copy()


def _validate_optional_domain(name: str, value: int, allowed: range | tuple[int, ...]) -> None:
    if value != ABSENT_BYTE and value not in allowed:
        raise TokenValidationError(f"{name} has an invalid present value")


def _validate_kind_clock(kind: PrimitiveKind | EventKind, token: PrimitiveToken) -> None:
    position = token.event_order_position
    opportunity = token.opportunity_index
    if isinstance(kind, EventKind):
        if kind is EventKind.INIT_OWNER:
            valid = opportunity == ABSENT_BYTE and position == token.subject_receiver
        elif kind is EventKind.INIT_SEMANTIC:
            valid = opportunity == ABSENT_BYTE and position == 2 + token.subject_receiver
        elif kind is EventKind.INIT_CAPABILITY:
            valid = opportunity == ABSENT_BYTE and position == 4 + token.carrier
        elif kind is EventKind.INIT_BODY:
            valid = opportunity == ABSENT_BYTE and position == 6 + token.slot
        elif kind in {
            EventKind.OWNER, EventKind.SEMANTIC, EventKind.CAPABILITY, EventKind.BODY,
            EventKind.NOOP_OWNER, EventKind.NOOP_SEMANTIC,
            EventKind.NOOP_CAPABILITY, EventKind.NOOP_BODY,
        }:
            valid = opportunity != ABSENT_BYTE and 0 <= position < 4
        elif kind is EventKind.DECISION:
            valid = opportunity != ABSENT_BYTE and position == int(OpportunityPosition.DECISION)
        else:
            valid = opportunity != ABSENT_BYTE and position == int(OpportunityPosition.SETTLEMENT)
    else:
        if position == ABSENT_BYTE:
            return
        if kind is PrimitiveKind.PREAMBLE:
            valid = 0 <= position < 8
        elif kind in PREACTION_KINDS:
            valid = 0 <= position < int(OpportunityPosition.DECISION)
        elif kind is PrimitiveKind.DECISION:
            valid = position == int(OpportunityPosition.DECISION)
        elif kind is PrimitiveKind.SETTLEMENT:
            valid = position == int(OpportunityPosition.SETTLEMENT)
        else:
            valid = False
    if not valid:
        label = kind.name if isinstance(kind, EventKind) else kind.value
        raise TokenValidationError(
            f"opportunity/position is illegal for {label}: {opportunity}/{position}"
        )


def _validate_known_field_domains(token: PrimitiveToken) -> None:
    if token.event_kind in (NEUTRAL_PAYLOAD_SOURCE, ABSENT_BYTE):
        raise TokenValidationError("event_kind cannot use a reserved sentinel")
    for name in ("subject_receiver", "target_receiver", "body_addressed_receiver", "capability_receiver"):
        _validate_optional_domain(name, getattr(token, name), (0, 1))
    for name in ("slot", "carrier"):
        _validate_optional_domain(name, getattr(token, name), (0, 1))
    for name in ("owner_old", "owner_new", "epoch_old", "epoch_new", "body_owner", "body_epoch"):
        _validate_optional_domain(name, getattr(token, name), range(16, 64))
    _validate_optional_domain(
        "payload_source_receiver", token.payload_source_receiver, (0, 1, NEUTRAL_PAYLOAD_SOURCE))
    _validate_optional_domain("opportunity_index", token.opportunity_index, range(24))
    _validate_optional_domain("event_order_position", token.event_order_position, range(8))
    if token.body_native_neutral:
        if token.payload_source_receiver != NEUTRAL_PAYLOAD_SOURCE or token.body_content:
            raise TokenValidationError(
                "body_native_neutral requires neutral source 254 and content zero")
    elif token.payload_source_receiver == NEUTRAL_PAYLOAD_SOURCE:
        raise TokenValidationError("neutral source 254 requires body_native_neutral")
