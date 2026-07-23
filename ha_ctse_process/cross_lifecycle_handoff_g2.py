"""Deterministic information gate for anonymous cross-lifecycle handoff."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from itertools import product
from typing import Iterable


SOURCE_FAMILY = "CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2"
SCHEMA = "cross_lifecycle_commitment_handoff_g2_information_gate_v1"
PASS_RESULT = "PASS_HANDOFF_INFORMATION_GATE_G2"
FAIL_RESULT = "FAIL_HANDOFF_INFORMATION_GATE_G2"
INVALID_RESULT = "INVALID_HANDOFF_INFORMATION_GATE_G2"

BITS = (-1, 1)
PHYSICAL_SLOTS = (0, 1, 2)
CREATOR_DURATIONS = (1, 2)
SUCCESSOR_DURATIONS = (2, 4)


@dataclass(frozen=True, slots=True)
class HandoffCase:
    """One balanced creator-to-successor lifecycle handoff."""

    bit: int
    creator_slot: int
    successor_slot: int
    survivor_slot: int
    creator_duration: int
    successor_duration: int

    def successor_trace_key(self) -> tuple[tuple[int, int, int, int], ...]:
        """Return everything a fresh anonymous successor can observe.

        Neither a physical slot nor any pre-JOIN creator history is actor-visible.
        The trace length may expose the realized successor lifetime; sign mates
        remain exact even under that strongest allowed trace.
        """

        return tuple(
            (
                0,  # creator cue is absent
                0,  # cue-present flag
                int(age == 0),  # anonymous JOIN flag
                2,  # successor plus neutral survivor are active
            )
            for age in range(self.successor_duration)
        )


@dataclass(frozen=True, slots=True)
class MemberState:
    physical_slot: int
    lifecycle: int
    value: int


@dataclass(frozen=True, slots=True)
class HandoffState:
    """State after creator departure and anonymous successor JOIN."""

    members: tuple[MemberState, ...]
    team_recurrent_state: int
    held_mark: int
    held_owner_slot: None = None

    def successor_value(self, case: HandoffCase) -> int:
        matches = tuple(
            member.value
            for member in self.members
            if member.physical_slot == case.successor_slot and member.lifecycle == 1
        )
        if len(matches) != 1:
            raise RuntimeError("successor lifecycle state is not unique")
        return matches[0]

    def with_held_mark(self, held_mark: int) -> "HandoffState":
        if held_mark not in BITS:
            raise ValueError("held mark is outside {-1,+1}")
        return replace(self, held_mark=held_mark)


def _mapping_support() -> tuple[tuple[int, int, int], ...]:
    mappings: list[tuple[int, int, int]] = []
    for survivor_slot in PHYSICAL_SLOTS:
        non_survivors = tuple(
            slot for slot in PHYSICAL_SLOTS if slot != survivor_slot
        )
        for creator_slot in non_survivors:
            for successor_slot in non_survivors:
                mappings.append((creator_slot, successor_slot, survivor_slot))
    return tuple(mappings)


def build_cases() -> tuple[HandoffCase, ...]:
    """Enumerate the complete balanced, deterministic G2 gate."""

    return tuple(
        HandoffCase(
            bit=bit,
            creator_slot=creator_slot,
            successor_slot=successor_slot,
            survivor_slot=survivor_slot,
            creator_duration=creator_duration,
            successor_duration=successor_duration,
        )
        for (
            bit,
            (creator_slot, successor_slot, survivor_slot),
            creator_duration,
            successor_duration,
        ) in product(
            BITS,
            _mapping_support(),
            CREATOR_DURATIONS,
            SUCCESSOR_DURATIONS,
        )
    )


def simulate_handoff(
    case: HandoffCase, *, held_mark: int | None = None
) -> HandoffState:
    """Execute CREATE, terminal LEAVE, one gap, and anonymous successor JOIN."""

    mark = case.bit if held_mark is None else held_mark
    if mark not in BITS:
        raise ValueError("held mark is outside {-1,+1}")

    # CREATE: creator member recurrence, team recurrence and held state all see b.
    members = {
        (case.creator_slot, 0): case.bit,
        (case.survivor_slot, 0): 0,
    }
    team_recurrent_state = case.bit

    # Terminal LEAVE deletes the creator-owned recurrent state. The intervening
    # gap changes neither team recurrence nor the event-held object.
    del members[(case.creator_slot, 0)]

    # JOIN creates a distinct lifecycle even when its physical packing slot is
    # reused. It receives exact zero member-recurrent state.
    members[(case.successor_slot, 1)] = 0
    return HandoffState(
        members=tuple(
            MemberState(slot, lifecycle, value)
            for (slot, lifecycle), value in sorted(members.items())
        ),
        team_recurrent_state=team_recurrent_state,
        held_mark=mark,
    )


def validate_cases(cases: Iterable[HandoffCase]) -> dict[str, object]:
    """Fail closed on imbalance, identity leakage or incomplete support."""

    normalized = tuple(cases)
    if not normalized:
        raise ValueError("handoff cases cannot be empty")
    if any(type(case) is not HandoffCase for case in normalized):
        raise TypeError("every handoff case must be an exact HandoffCase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("handoff cases must be unique")

    for case in normalized:
        if case.bit not in BITS:
            raise ValueError("bit is outside {-1,+1}")
        if case.creator_duration not in CREATOR_DURATIONS:
            raise ValueError("creator duration is outside support")
        if case.successor_duration not in SUCCESSOR_DURATIONS:
            raise ValueError("successor duration is outside support")
        if case.survivor_slot in (case.creator_slot, case.successor_slot):
            raise ValueError("neutral survivor cannot own a handoff endpoint")
        if set((case.creator_slot, case.successor_slot, case.survivor_slot)) - set(
            PHYSICAL_SLOTS
        ):
            raise ValueError("physical slot is outside support")

    sign_groups: dict[tuple[int, int, int, int, int], set[int]] = defaultdict(set)
    for case in normalized:
        sign_groups[
            (
                case.creator_slot,
                case.successor_slot,
                case.survivor_slot,
                case.creator_duration,
                case.successor_duration,
            )
        ].add(case.bit)
    if any(bits != set(BITS) for bits in sign_groups.values()):
        raise ValueError("every handoff case must have an exact sign mate")

    expected = set(build_cases())
    if set(normalized) != expected:
        raise ValueError("handoff cases do not equal the frozen exhaustive support")

    mappings = {
        (case.creator_slot, case.successor_slot, case.survivor_slot)
        for case in normalized
    }
    same_slot = sum(case.creator_slot == case.successor_slot for case in normalized)
    cross_slot = len(normalized) - same_slot
    return {
        "bits": list(BITS),
        "creator_durations": list(CREATOR_DURATIONS),
        "successor_durations": list(SUCCESSOR_DURATIONS),
        "physical_slots": list(PHYSICAL_SLOTS),
        "mapping_count": len(mappings),
        "same_slot_handoffs": same_slot,
        "cross_slot_handoffs": cross_slot,
        "active_count_profile": [2, 1, 2],
    }


def _weighted_utility(cases: tuple[HandoffCase, ...], action_for_case) -> float:
    correct = 0
    total = 0
    for case in cases:
        action = int(action_for_case(case, simulate_handoff(case)))
        if action not in BITS:
            raise ValueError("constructive policy emitted an invalid action")
        correct += case.successor_duration * int(action == case.bit)
        total += case.successor_duration
    return correct / total


def _successor_bayes_bound(cases: tuple[HandoffCase, ...]) -> float:
    by_trace: dict[tuple[tuple[int, int, int, int], ...], Counter[int]] = defaultdict(
        Counter
    )
    for case in cases:
        by_trace[case.successor_trace_key()][case.bit] += case.successor_duration
    best_correct = sum(max(counts.values()) for counts in by_trace.values())
    total = sum(sum(counts.values()) for counts in by_trace.values())
    return best_correct / total


def _random_mark(case: HandoffCase) -> int:
    """Balanced outcome-independent mark; deliberately does not read bit."""

    parity = (
        case.creator_slot
        + case.successor_slot
        + case.survivor_slot
        + case.creator_duration
        + case.successor_duration
    ) % 2
    return 2 * parity - 1


def evaluate_information_gate(
    cases: Iterable[HandoffCase],
) -> dict[str, object]:
    """Evaluate exact controls and the held-mark intervention without learning."""

    normalized = tuple(cases)
    try:
        inventory = validate_cases(normalized)
    except (TypeError, ValueError) as error:
        return {
            "schema": SCHEMA,
            "source_family": SOURCE_FAMILY,
            "formal": False,
            "result": INVALID_RESULT,
            "operational_errors": [str(error)],
        }

    per_member = _weighted_utility(
        normalized,
        lambda case, state: state.successor_value(case) or 1,
    )
    dum = _weighted_utility(
        normalized,
        lambda case, state: state.successor_value(case) or 1,
    )
    team_rec = _weighted_utility(
        normalized, lambda _case, state: state.team_recurrent_state
    )
    ehc = _weighted_utility(normalized, lambda _case, state: state.held_mark)
    random_mark = _weighted_utility(
        normalized,
        lambda case, _state: simulate_handoff(
            case, held_mark=_random_mark(case)
        ).held_mark,
    )
    flipped_actions_changed = 0
    flipped_correct = 0
    flipped_total = 0
    for case in normalized:
        natural_state = simulate_handoff(case)
        flipped_state = natural_state.with_held_mark(-natural_state.held_mark)
        natural_action = natural_state.held_mark
        flipped_action = flipped_state.held_mark
        flipped_actions_changed += case.successor_duration * int(
            natural_action != flipped_action
        )
        flipped_correct += case.successor_duration * int(flipped_action == case.bit)
        flipped_total += case.successor_duration
    flipped = flipped_correct / flipped_total

    states = tuple((case, simulate_handoff(case)) for case in normalized)

    metrics = {
        "successor_per_member_bayes_bound": _successor_bayes_bound(normalized),
        "per_member_rec_utility": per_member,
        "dum_utility": dum,
        "team_rec_utility": team_rec,
        "ehc_utility": ehc,
        "random_mark_utility": random_mark,
        "ehc_flip_action_change": flipped_actions_changed / flipped_total,
        "ehc_flip_utility": flipped,
        "ehc_flip_utility_drop": ehc - flipped,
    }
    state_ownership = {
        "creator_member_state_deleted": all(
            not any(
                member.physical_slot == case.creator_slot and member.lifecycle == 0
                for member in state.members
            )
            for case, state in states
        ),
        "successor_member_state_zero_at_join": all(
            state.successor_value(case) == 0 for case, state in states
        ),
        "team_recurrent_state_survives": all(
            state.team_recurrent_state == case.bit for case, state in states
        ),
        "event_held_state_survives": all(
            state.held_mark == case.bit for case, state in states
        ),
        "fixed_slot_is_state_owner": any(
            state.held_owner_slot is not None for _case, state in states
        ),
    }
    expected_metrics = {
        "successor_per_member_bayes_bound": 0.5,
        "per_member_rec_utility": 0.5,
        "dum_utility": 0.5,
        "team_rec_utility": 1.0,
        "ehc_utility": 1.0,
        "random_mark_utility": 0.5,
        "ehc_flip_action_change": 1.0,
        "ehc_flip_utility": 0.0,
        "ehc_flip_utility_drop": 1.0,
    }
    result = (
        PASS_RESULT
        if metrics == expected_metrics
        and state_ownership
        == {
            "creator_member_state_deleted": True,
            "successor_member_state_zero_at_join": True,
            "team_recurrent_state_survives": True,
            "event_held_state_survives": True,
            "fixed_slot_is_state_owner": False,
        }
        else FAIL_RESULT
    )
    return {
        "schema": SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": False,
        "result": result,
        "case_count": len(normalized),
        "inventory": inventory,
        "metrics": metrics,
        "state_ownership": state_ownership,
        "operational_errors": [],
    }
