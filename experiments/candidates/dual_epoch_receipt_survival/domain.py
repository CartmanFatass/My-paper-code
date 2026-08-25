"""Typed host records and frozen DEARS-B1 constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final


class Action(IntEnum):
    USE_0 = 0
    USE_1 = 1
    RESET = 2


ACTIONS: Final = tuple(Action)
GRU_DUAL: Final = "GRU-DUAL"
GRU_SNAPSHOT: Final = "GRU-SNAPSHOT"
GRU_UNBOUND: Final = "GRU-UNBOUND"
GRU_VALIDITY: Final = "GRU-VALIDITY"
GRU_ORACLE: Final = "GRU-ORACLE"
GRU_RAW: Final = "GRU-RAW"
RULE_DUAL: Final = "RULE-DUAL"
LEARNED_ARMS: Final = (
    GRU_DUAL, GRU_SNAPSHOT, GRU_UNBOUND, GRU_VALIDITY, GRU_ORACLE, GRU_RAW,
)
BASE_SEEDS: Final = (13, 29, 43, 59, 73, 89, 103, 127, 149, 181)

INTERLEAVINGS: Final = (
    ("O1", "O2", "L1", "L2"),
    ("O1", "L1", "O2", "L2"),
    ("O1", "L1", "L2", "O2"),
    ("L1", "L2", "O1", "O2"),
    ("L1", "O1", "L2", "O2"),
    ("L1", "O1", "O2", "L2"),
)
OFFSETS: Final = {
    "train": (-12, -8, -4),
    "validation": (-10, -6),
    "test": (-11, -9, -7, -5, -3, -1),
}
SUPERBLOCK_COUNTS: Final = {"train": 576, "validation": 192, "test": 576}
EXAMPLE_COUNTS: Final = {key: value * 16 for key, value in SUPERBLOCK_COUNTS.items()}


@dataclass(frozen=True, order=True)
class Version:
    handle: int
    epoch: int

    def __post_init__(self) -> None:
        if not (0 < int(self.handle) < 2**32 and 0 < int(self.epoch) < 2**32):
            raise ValueError("opaque versions require nonzero u32 components")


@dataclass(frozen=True)
class Receipt:
    displayed_bit: int
    owner_anchor: Version
    lease_anchor: Version
    event_time: int
    valid_from: int
    valid_until: int
    tag_ok: bool
    issuer_allowed: bool
    nonce: int


@dataclass(frozen=True)
class OwnerUpdate:
    edge: int
    from_version: Version
    to_version: Version
    event_time: int


@dataclass(frozen=True)
class LeaseUpdate:
    edge: int
    from_version: Version
    to_version: Version
    event_time: int
    valid_from: int
    valid_until: int


Event = Receipt | OwnerUpdate | LeaseUpdate


@dataclass(frozen=True)
class Example:
    seed: int
    split: str
    superblock: int
    core_index: int
    events: tuple[Event, ...]
    final_owner: Version
    final_lease: Version
    final_valid_from: int
    final_valid_until: int
    authentication: bool
    owner_survives: bool
    lease_survives: bool
    displayed_bit: int
    authentication_detail: str
    owner_detail: str
    lease_detail: str
    handoff_offset: int
    order: tuple[str, ...]
    correct_action: Action

    @property
    def refined_cell(self) -> str:
        return "|".join((
            self.authentication_detail,
            self.owner_detail,
            self.lease_detail,
            str(self.displayed_bit),
        ))

    @property
    def live(self) -> bool:
        return self.authentication and self.owner_survives and self.lease_survives

    @property
    def matched_id(self) -> tuple[int, str, int]:
        return (self.seed, self.split, self.superblock)


def correct_action(live: bool, bit: int) -> Action:
    if not live:
        return Action.RESET
    return Action.USE_1 if int(bit) else Action.USE_0
