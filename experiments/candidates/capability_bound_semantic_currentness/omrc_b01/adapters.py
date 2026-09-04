"""Literal four-byte public-history adapters for CBSC-OMRC-B01."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .contract import EventKind
from .token import (
    ABSENT_BYTE,
    LITERAL_TOKEN_CODEC,
    EventKindLayout,
    PrimitiveToken,
    TokenValidationError,
    bytes_to_lsb_float32,
)


ADAPTER_BYTE_COUNT = 4
ADAPTER_CHANNEL_COUNT = 32


class AdapterStateError(ValueError):
    """Raised when a valid token violates episode-local adapter chronology."""


@dataclass(frozen=True)
class AdapterWorkReceipt:
    """Result-blind logical work performed for one token."""

    byte_reads: int = 0
    byte_writes: int = 0
    uint8_xors: int = 0
    appended_bytes: int = 0
    age_increments: int = 0

    def __add__(self, other: object) -> "AdapterWorkReceipt":
        if not isinstance(other, AdapterWorkReceipt):
            return NotImplemented
        return AdapterWorkReceipt(
            self.byte_reads + other.byte_reads,
            self.byte_writes + other.byte_writes,
            self.uint8_xors + other.uint8_xors,
            self.appended_bytes + other.appended_bytes,
            self.age_increments + other.age_increments,
        )


@dataclass(frozen=True)
class AdapterEmission:
    """Four post-update bytes and the logical work used to obtain them."""

    packed: bytes
    work: AdapterWorkReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.packed, bytes) or len(self.packed) != ADAPTER_BYTE_COUNT:
            raise AdapterStateError("adapter emission must contain exactly four bytes")
        if not isinstance(self.work, AdapterWorkReceipt):
            raise AdapterStateError("adapter emission requires an AdapterWorkReceipt")

    def float32_channels(self) -> np.ndarray:
        channels = bytes_to_lsb_float32(self.packed, expected_bytes=ADAPTER_BYTE_COUNT)
        if channels.shape != (ADAPTER_CHANNEL_COUNT,):
            raise AssertionError("adapter projection must contain 32 channels")
        return channels


class _BaseAdapter:
    def __init__(self) -> None:
        self._total_work = AdapterWorkReceipt()

    @property
    def state(self) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @property
    def total_work(self) -> AdapterWorkReceipt:
        return self._total_work

    def process(self, token: PrimitiveToken) -> AdapterEmission:
        layout = _literal_layout(token)
        boundary_work = self._apply_opportunity_boundary(token)
        update_work = self._update(layout.kind, token)
        packed, emission_work = self._emit(layout.kind, token)
        work = boundary_work + update_work + emission_work
        self._total_work = self._total_work + work
        return AdapterEmission(packed, work)

    def replay(self, tokens: Iterable[PrimitiveToken]) -> tuple[AdapterEmission, ...]:
        return tuple(self.process(token) for token in tokens)

    def _apply_opportunity_boundary(self, token: PrimitiveToken) -> AdapterWorkReceipt:
        return AdapterWorkReceipt()

    def _update(self, kind: EventKind, token: PrimitiveToken) -> AdapterWorkReceipt:
        raise NotImplementedError

    def _emit(
        self, kind: EventKind, token: PrimitiveToken
    ) -> tuple[bytes, AdapterWorkReceipt]:
        raise NotImplementedError


class RawHistoryAdapter(_BaseAdapter):
    """Generic four-byte FIFO over mask-selected public token bytes."""

    def __init__(self) -> None:
        super().__init__()
        self._registers = [ABSENT_BYTE] * ADAPTER_BYTE_COUNT

    @property
    def state(self) -> tuple[int, int, int, int]:
        return tuple(self._registers)

    def process(self, token: PrimitiveToken) -> AdapterEmission:
        layout = _literal_layout(token)
        packed_token = LITERAL_TOKEN_CODEC.pack(token)
        appended = [
            packed_token[index]
            for index in range(16)
            if layout.bmask & (1 << index)
        ]
        if layout.fmask != 0:
            appended.append(packed_token[16])
        for value in appended:
            self._registers[:] = (*self._registers[1:], value)
        work = AdapterWorkReceipt(appended_bytes=len(appended))
        self._total_work = self._total_work + work
        return AdapterEmission(bytes(self._registers), work)

    def _update(self, kind: EventKind, token: PrimitiveToken) -> AdapterWorkReceipt:
        raise AssertionError("RAW uses its literal positional append path")

    def _emit(
        self, kind: EventKind, token: PrimitiveToken
    ) -> tuple[bytes, AdapterWorkReceipt]:
        raise AssertionError("RAW emits from its literal positional append path")


class StructCurrentnessAdapter(_BaseAdapter):
    """Relation-aligned OWNER/epoch register adapter."""

    def __init__(self) -> None:
        super().__init__()
        self._registers = [ABSENT_BYTE] * ADAPTER_BYTE_COUNT

    @property
    def state(self) -> tuple[int, int, int, int]:
        return tuple(self._registers)

    def _update(self, kind: EventKind, token: PrimitiveToken) -> AdapterWorkReceipt:
        if kind in (EventKind.INIT_OWNER, EventKind.OWNER):
            self._registers[token.subject_receiver] = token.owner_new
            return AdapterWorkReceipt(byte_writes=1)
        if kind in (EventKind.INIT_SEMANTIC, EventKind.SEMANTIC):
            self._registers[2 + token.subject_receiver] = token.epoch_new
            return AdapterWorkReceipt(byte_writes=1)
        return AdapterWorkReceipt()

    def _emit(
        self, kind: EventKind, token: PrimitiveToken
    ) -> tuple[bytes, AdapterWorkReceipt]:
        if kind is EventKind.DECISION:
            receiver = token.target_receiver
            owner = self._registers[receiver]
            epoch = self._registers[2 + receiver]
            owner_for_xor = self._registers[receiver]
            epoch_for_xor = self._registers[2 + receiver]
            return (
                bytes(
                    (
                        owner,
                        epoch,
                        owner_for_xor ^ token.body_owner,
                        epoch_for_xor ^ token.body_epoch,
                    )
                ),
                AdapterWorkReceipt(byte_reads=4, uint8_xors=2),
            )
        return bytes(self._registers), AdapterWorkReceipt(byte_reads=4)


class PredictiveIndexAdapter(_BaseAdapter):
    """Latest addressed content and opportunity-age adapter."""

    def __init__(self) -> None:
        super().__init__()
        self._registers = [ABSENT_BYTE] * ADAPTER_BYTE_COUNT
        self._current_opportunity: int | None = None

    @property
    def state(self) -> tuple[int, int, int, int]:
        return tuple(self._registers)

    def _apply_opportunity_boundary(self, token: PrimitiveToken) -> AdapterWorkReceipt:
        if token.opportunity_index == ABSENT_BYTE:
            return AdapterWorkReceipt()
        opportunity = token.opportunity_index
        if token.event_order_position == 0:
            expected = 0 if self._current_opportunity is None else self._current_opportunity + 1
            if opportunity != expected:
                raise AdapterStateError(
                    f"PI expected opportunity {expected} boundary, got {opportunity}"
                )
            increments = 0
            for content_lane, age_lane in ((0, 1), (2, 3)):
                if self._registers[content_lane] == ABSENT_BYTE:
                    self._registers[age_lane] = ABSENT_BYTE
                else:
                    self._registers[age_lane] = min(255, self._registers[age_lane] + 1)
                    increments += 1
            self._current_opportunity = opportunity
            return AdapterWorkReceipt(byte_reads=2, byte_writes=2, age_increments=increments)
        if self._current_opportunity != opportunity:
            raise AdapterStateError(
                "PI received an ordinary token before that opportunity's position-zero boundary"
            )
        return AdapterWorkReceipt()

    def _update(self, kind: EventKind, token: PrimitiveToken) -> AdapterWorkReceipt:
        if kind in (EventKind.INIT_BODY, EventKind.BODY):
            receiver = token.body_addressed_receiver
            self._registers[2 * receiver] = int(token.body_content)
            self._registers[2 * receiver + 1] = 0
            return AdapterWorkReceipt(byte_writes=2)
        return AdapterWorkReceipt()

    def _emit(
        self, kind: EventKind, token: PrimitiveToken
    ) -> tuple[bytes, AdapterWorkReceipt]:
        return bytes(self._registers), AdapterWorkReceipt(byte_reads=4)


class DerangedCurrentnessAdapter(_BaseAdapter):
    """Equal-work fixed no-fixed-point routing control."""

    def __init__(self) -> None:
        super().__init__()
        self._registers = [ABSENT_BYTE] * ADAPTER_BYTE_COUNT

    @property
    def state(self) -> tuple[int, int, int, int]:
        return tuple(self._registers)

    def _update(self, kind: EventKind, token: PrimitiveToken) -> AdapterWorkReceipt:
        if kind in (EventKind.INIT_OWNER, EventKind.OWNER):
            lane = 3 if token.subject_receiver == 0 else 2
            self._registers[lane] = token.owner_new
            return AdapterWorkReceipt(byte_writes=1)
        if kind in (EventKind.INIT_SEMANTIC, EventKind.SEMANTIC):
            lane = 1 if token.subject_receiver == 0 else 0
            self._registers[lane] = token.epoch_new
            return AdapterWorkReceipt(byte_writes=1)
        return AdapterWorkReceipt()

    def _emit(
        self, kind: EventKind, token: PrimitiveToken
    ) -> tuple[bytes, AdapterWorkReceipt]:
        if kind is EventKind.DECISION:
            receiver = token.target_receiver
            owner = self._registers[receiver]
            epoch = self._registers[2 + receiver]
            owner_for_xor = self._registers[receiver]
            epoch_for_xor = self._registers[2 + receiver]
            return (
                bytes(
                    (
                        owner,
                        epoch,
                        owner_for_xor ^ token.body_owner,
                        epoch_for_xor ^ token.body_epoch,
                    )
                ),
                AdapterWorkReceipt(byte_reads=4, uint8_xors=2),
            )
        return bytes(self._registers), AdapterWorkReceipt(byte_reads=4)


def _literal_layout(token: PrimitiveToken) -> EventKindLayout:
    layout = LITERAL_TOKEN_CODEC.validate(token)
    if not isinstance(layout.kind, EventKind):
        raise TokenValidationError("production adapters require the literal EventKind codebook")
    return layout
