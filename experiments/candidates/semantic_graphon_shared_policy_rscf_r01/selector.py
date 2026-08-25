"""Arm-independent antithetic origin selector for deterministic Gate-B tests.

The address types make forbidden dependencies structurally unavailable: the
base-slot address has no side field, the local-index address has one side
field, and neither has an arm, state, action, buffer, branch, or outcome field.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Final

from .contracts import (
    HORIZON,
    PAIRS_PER_TRAIN_ROSTER,
    PUBLIC_ROLES,
    ROLE_COUNT,
    SELECTOR_SCHEMA,
    TestIdentity,
    canonical_digest,
    require_test_identity,
    validate_roster_size,
)


_UINT64_SPACE: Final = 1 << 64


@dataclass(frozen=True)
class BaseSlotAddress:
    test_namespace: str
    phase: str
    fixture_update_index: int
    roster_size: int
    pair_index: int
    role_index: int
    selector_kind: str = "base_slot"

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": SELECTOR_SCHEMA,
            "test_namespace": self.test_namespace,
            "phase": self.phase,
            "fixture_update_index": self.fixture_update_index,
            "roster_size": self.roster_size,
            "pair_index": self.pair_index,
            "role_index": self.role_index,
            "selector_kind": self.selector_kind,
        }


@dataclass(frozen=True)
class LocalIndexAddress:
    test_namespace: str
    phase: str
    fixture_update_index: int
    roster_size: int
    pair_index: int
    side: int
    role_index: int
    selector_kind: str = "local_index"

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": SELECTOR_SCHEMA,
            "test_namespace": self.test_namespace,
            "phase": self.phase,
            "fixture_update_index": self.fixture_update_index,
            "roster_size": self.roster_size,
            "pair_index": self.pair_index,
            "side": self.side,
            "role_index": self.role_index,
            "selector_kind": self.selector_kind,
        }


@dataclass(frozen=True)
class OriginSelection:
    pair_index: int
    side: int
    role_index: int
    role_name: str
    base_slot: int
    selected_slot: int
    role_local_index: int
    roster_agent_index: int
    base_address_digest: str
    local_address_digest: str

    @property
    def q_entry_count(self) -> int:
        return 3 if self.role_index in (0, 1) else 4

    @property
    def alternative_count(self) -> int:
        return self.q_entry_count - 1

    def canonical_payload(self) -> dict[str, object]:
        return {
            "pair_index": self.pair_index,
            "side": self.side,
            "role_index": self.role_index,
            "role_name": self.role_name,
            "base_slot": self.base_slot,
            "selected_slot": self.selected_slot,
            "role_local_index": self.role_local_index,
            "roster_agent_index": self.roster_agent_index,
            "base_address_digest": self.base_address_digest,
            "local_address_digest": self.local_address_digest,
            "q_entry_count": self.q_entry_count,
            "alternative_count": self.alternative_count,
        }


@dataclass(frozen=True)
class SelectorCounts:
    factual_test_episodes: int
    selected_origins: int
    q_entries: int
    factual_reuses: int
    alternative_continuations: int

    def canonical_payload(self) -> dict[str, int]:
        return {
            "factual_test_episodes": self.factual_test_episodes,
            "selected_origins": self.selected_origins,
            "q_entries": self.q_entries,
            "factual_reuses": self.factual_reuses,
            "alternative_continuations": self.alternative_continuations,
        }


@dataclass(frozen=True)
class SelectorSchedule:
    test_namespace: str
    fixture_update_index: int
    roster_size: int
    selections: tuple[OriginSelection, ...]
    counts: SelectorCounts
    provenance_digest: str

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": SELECTOR_SCHEMA,
            "test_namespace": self.test_namespace,
            "fixture_update_index": self.fixture_update_index,
            "roster_size": self.roster_size,
            "selections": [selection.canonical_payload() for selection in self.selections],
            "counts": self.counts.canonical_payload(),
        }


def _validate_fixture_update_index(value: int) -> int:
    if type(value) is not int or not 0 <= value < 512:
        raise ValueError("fixture_update_index must be an integer in [0, 511]")
    return value


def _uniform_below(address: BaseSlotAddress | LocalIndexAddress, upper: int) -> tuple[int, str]:
    """Exact finite-support rejection sampler driven by a TEST-only digest."""
    if type(upper) is not int or upper <= 0:
        raise ValueError("uniform upper bound must be positive")
    address_digest = canonical_digest(address)
    rejection_limit = _UINT64_SPACE - (_UINT64_SPACE % upper)
    counter = 0
    while True:
        material = f"{address_digest}|draw|{counter}".encode("ascii")
        word = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
        if word < rejection_limit:
            return word % upper, address_digest
        counter += 1


def select_test_pair(
    identity: TestIdentity,
    *,
    fixture_update_index: int,
    roster_size: int,
    pair_index: int,
) -> tuple[OriginSelection, ...]:
    """Select exactly one origin per role on both sides of one TEST pair."""
    identity = require_test_identity(identity)
    fixture_update_index = _validate_fixture_update_index(fixture_update_index)
    roster_size = validate_roster_size(roster_size, training_only=True)
    if type(pair_index) is not int or not 0 <= pair_index < PAIRS_PER_TRAIN_ROSTER:
        raise ValueError("pair_index must be an integer in [0, 15]")
    multiplicity = roster_size // ROLE_COUNT
    selections: list[OriginSelection] = []
    for role_index, role_name in enumerate(PUBLIC_ROLES):
        base_address = BaseSlotAddress(
            test_namespace=identity.namespace,
            phase="TEST_TRAINING",
            fixture_update_index=fixture_update_index,
            roster_size=roster_size,
            pair_index=pair_index,
            role_index=role_index,
        )
        base_slot, base_digest = _uniform_below(base_address, HORIZON)
        for side in (0, 1):
            local_address = LocalIndexAddress(
                test_namespace=identity.namespace,
                phase="TEST_TRAINING",
                fixture_update_index=fixture_update_index,
                roster_size=roster_size,
                pair_index=pair_index,
                side=side,
                role_index=role_index,
            )
            local_index, local_digest = _uniform_below(local_address, multiplicity)
            selections.append(
                OriginSelection(
                    pair_index=pair_index,
                    side=side,
                    role_index=role_index,
                    role_name=role_name,
                    base_slot=base_slot,
                    selected_slot=base_slot if side == 0 else HORIZON - 1 - base_slot,
                    role_local_index=local_index,
                    roster_agent_index=role_index * multiplicity + local_index,
                    base_address_digest=base_digest,
                    local_address_digest=local_digest,
                )
            )
    return tuple(selections)


def generate_test_selector_schedule(
    identity: TestIdentity,
    *,
    fixture_update_index: int,
    roster_size: int,
) -> SelectorSchedule:
    """Create the full 32-episode selector schedule for one TEST roster block."""
    identity = require_test_identity(identity)
    fixture_update_index = _validate_fixture_update_index(fixture_update_index)
    roster_size = validate_roster_size(roster_size, training_only=True)
    selections = tuple(
        selection
        for pair_index in range(PAIRS_PER_TRAIN_ROSTER)
        for selection in select_test_pair(
            identity,
            fixture_update_index=fixture_update_index,
            roster_size=roster_size,
            pair_index=pair_index,
        )
    )
    counts = SelectorCounts(
        factual_test_episodes=2 * PAIRS_PER_TRAIN_ROSTER,
        selected_origins=len(selections),
        q_entries=sum(selection.q_entry_count for selection in selections),
        factual_reuses=len(selections),
        alternative_continuations=sum(selection.alternative_count for selection in selections),
    )
    schedule_without_digest = {
        "schema": SELECTOR_SCHEMA,
        "test_namespace": identity.namespace,
        "fixture_update_index": fixture_update_index,
        "roster_size": roster_size,
        "selections": [selection.canonical_payload() for selection in selections],
        "counts": counts.canonical_payload(),
    }
    schedule = SelectorSchedule(
        test_namespace=identity.namespace,
        fixture_update_index=fixture_update_index,
        roster_size=roster_size,
        selections=selections,
        counts=counts,
        provenance_digest=canonical_digest(schedule_without_digest),
    )
    validate_selector_schedule(schedule)
    return schedule


def validate_selector_schedule(schedule: SelectorSchedule) -> None:
    if not isinstance(schedule, SelectorSchedule):
        raise ValueError("selector schedule has wrong type")
    validate_roster_size(schedule.roster_size, training_only=True)
    if not schedule.test_namespace.startswith("TEST_ONLY|"):
        raise ValueError("selector schedule is not TEST-only")
    expected_keys = {
        (pair, side, role)
        for pair in range(PAIRS_PER_TRAIN_ROSTER)
        for side in (0, 1)
        for role in range(ROLE_COUNT)
    }
    actual_keys = {(item.pair_index, item.side, item.role_index) for item in schedule.selections}
    if actual_keys != expected_keys or len(actual_keys) != len(schedule.selections):
        raise ValueError("selector schedule must contain exactly one origin per role and TEST episode")
    by_pair_role: dict[tuple[int, int], dict[int, OriginSelection]] = {}
    for item in schedule.selections:
        by_pair_role.setdefault((item.pair_index, item.role_index), {})[item.side] = item
    for sides in by_pair_role.values():
        if sides[0].base_slot != sides[1].base_slot:
            raise ValueError("base-slot address must be side-free")
        if sides[0].base_address_digest != sides[1].base_address_digest:
            raise ValueError("base-slot provenance differs by side")
        if sides[0].selected_slot + sides[1].selected_slot != HORIZON - 1:
            raise ValueError("episode sides are not antithetic complements")
        if sides[0].local_address_digest == sides[1].local_address_digest:
            raise ValueError("local-index provenance must be side-specific")
    expected_counts = SelectorCounts(32, 96, 320, 96, 224)
    if schedule.counts != expected_counts:
        raise ValueError("selector schedule counts differ from the frozen per-roster block")
    payload = schedule.canonical_payload()
    if canonical_digest(payload) != schedule.provenance_digest:
        raise ValueError("selector provenance digest mismatch")
