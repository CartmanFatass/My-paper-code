"""Deterministic information gate for anonymous cross-lifecycle handoff."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import blake2b
from itertools import product
from typing import Any, Iterable, Mapping


SOURCE_FAMILY = "CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2"
SCHEMA = "cross_lifecycle_commitment_handoff_g2_information_gate_v1"
PASS_RESULT = "PASS_HANDOFF_INFORMATION_GATE_G2"
FAIL_RESULT = "FAIL_HANDOFF_INFORMATION_GATE_G2"
INVALID_RESULT = "INVALID_HANDOFF_INFORMATION_GATE_G2"

BITS = (-1, 1)
PHYSICAL_SLOTS = (0, 1, 2)
CREATOR_DURATIONS = (1, 2)
SUCCESSOR_DURATIONS = (2, 4)

ACTION_VALUES = (-1, 1)
ACTOR_WIDTH = 6
CRITIC_WIDTH = 10
MAXIMUM_CAPACITY = 3
TRAIN_GAPS = (1, 2, 3)
HELDOUT_GAPS = (8, 12)
TRAIN_DUTY_DURATIONS = (4, 6)
HELDOUT_DUTY_DURATIONS = (8, 10)


@dataclass(frozen=True, slots=True)
class G2EpisodeSpec:
    profile: str
    base_id: int
    sign_mate: int
    bit: int
    creator_slot: int
    successor_slot: int
    survivor_slot: int
    creator_duration: int
    gap: int
    successor_duration: int
    nuisance: tuple[int, ...]

    @property
    def successor_join_time(self) -> int:
        return self.creator_duration + self.gap

    @property
    def horizon(self) -> int:
        return self.successor_join_time + self.successor_duration


@dataclass(frozen=True, slots=True)
class G2Observation:
    actor: tuple[float, float, float, float, float, float]
    critic: tuple[
        float, float, float, float, float, float, float, float, float, float
    ]
    lifecycle: int
    opportunity_kind: str | None


def _checked_nonnegative_int(name: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _counter_index(seed: int, domain: str, base_id: int, modulo: int) -> int:
    _checked_nonnegative_int("seed", seed)
    _checked_nonnegative_int("base_id", base_id)
    if type(modulo) is not int or modulo <= 0:
        raise ValueError("modulo must be a positive integer")
    digest = blake2b(
        f"{seed}:{domain}:{base_id}".encode("ascii"), digest_size=8
    ).digest()
    return int.from_bytes(digest, "little") % modulo


def make_episode_spec(
    profile: str,
    *,
    base_id: int,
    sign_mate: int,
    task_seed: int = 273101,
    membership_seed: int = 273201,
    nuisance_seed: int = 273301,
) -> G2EpisodeSpec:
    """Create one paired counter-based train/IID/held-out episode ledger."""

    if profile not in ("train", "iid", "heldout"):
        raise ValueError("profile must be train, iid, or heldout")
    base_id = _checked_nonnegative_int("base_id", base_id)
    if sign_mate not in BITS:
        raise ValueError("sign_mate must be -1 or +1")
    for name, seed in (
        ("task_seed", task_seed),
        ("membership_seed", membership_seed),
        ("nuisance_seed", nuisance_seed),
    ):
        _checked_nonnegative_int(name, seed)

    root_bit = BITS[_counter_index(task_seed, "bit", base_id, len(BITS))]
    bit = sign_mate * root_bit
    creator_duration = CREATOR_DURATIONS[
        _counter_index(task_seed, "creator_duration", base_id, 2)
    ]
    if profile == "heldout":
        gaps = HELDOUT_GAPS
        duties = HELDOUT_DUTY_DURATIONS
    else:
        gaps = TRAIN_GAPS
        duties = TRAIN_DUTY_DURATIONS
    gap = gaps[_counter_index(task_seed, f"{profile}:gap", base_id, len(gaps))]
    successor_duration = duties[
        _counter_index(task_seed, f"{profile}:duty", base_id, len(duties))
    ]
    mapping = _mapping_support()[
        _counter_index(membership_seed, f"{profile}:mapping", base_id, 12)
    ]
    horizon = creator_duration + gap + successor_duration
    nuisance = tuple(
        BITS[_counter_index(nuisance_seed, f"{profile}:nuisance:{time}", base_id, 2)]
        for time in range(horizon)
    )
    return G2EpisodeSpec(
        profile=profile,
        base_id=base_id,
        sign_mate=sign_mate,
        bit=bit,
        creator_slot=mapping[0],
        successor_slot=mapping[1],
        survivor_slot=mapping[2],
        creator_duration=creator_duration,
        gap=gap,
        successor_duration=successor_duration,
        nuisance=nuisance,
    )


class CrossLifecycleHandoffG2Env:
    """Anonymous trainable creator-to-successor handoff source."""

    def __init__(self, spec: G2EpisodeSpec) -> None:
        if type(spec) is not G2EpisodeSpec:
            raise TypeError("spec must be an exact G2EpisodeSpec")
        self.spec = spec
        self._time = 0
        self._successor_correct = 0
        self._successor_rows = 0
        self._successor_actions: list[int] = []

    @property
    def done(self) -> bool:
        return self._time >= self.spec.horizon

    @property
    def time(self) -> int:
        return self._time

    def _active_slots(self) -> tuple[int, ...]:
        if self.done:
            return ()
        if self._time < self.spec.creator_duration:
            return tuple(sorted((self.spec.creator_slot, self.spec.survivor_slot)))
        if self._time < self.spec.successor_join_time:
            return (self.spec.survivor_slot,)
        return tuple(sorted((self.spec.successor_slot, self.spec.survivor_slot)))

    def observe(self) -> dict[int, G2Observation]:
        if self.done:
            return {}
        active_slots = self._active_slots()
        active_count = len(active_slots)
        if self._time < self.spec.creator_duration:
            phase = 0.0
            remaining_gap = float(self.spec.gap)
            remaining_duty = float(self.spec.successor_duration)
        elif self._time < self.spec.successor_join_time:
            phase = 0.5
            remaining_gap = float(self.spec.successor_join_time - self._time)
            remaining_duty = float(self.spec.successor_duration)
        else:
            phase = 1.0
            remaining_gap = 0.0
            remaining_duty = float(self.spec.horizon - self._time)

        result: dict[int, G2Observation] = {}
        for slot in active_slots:
            is_creator = (
                slot == self.spec.creator_slot
                and self._time < self.spec.creator_duration
            )
            is_successor = (
                slot == self.spec.successor_slot
                and self._time >= self.spec.successor_join_time
            )
            cue_present = is_creator and self._time == 0
            join_flag = self._time == 0 or (
                is_successor and self._time == self.spec.successor_join_time
            )
            if is_successor:
                lifecycle = 1
                age = self._time - self.spec.successor_join_time
            else:
                lifecycle = 0
                age = self._time
            actor = (
                float(self.spec.bit if cue_present else 0),
                float(cue_present),
                float(join_flag),
                float(min(age, 12) / 12),
                float(active_count / MAXIMUM_CAPACITY),
                float(self.spec.nuisance[self._time]),
            )
            critic = actor + (
                float(self.spec.bit),
                phase,
                float(remaining_duty / 10),
                float(remaining_gap / 12),
            )
            result[slot] = G2Observation(
                actor=actor,
                critic=critic,
                lifecycle=lifecycle,
                opportunity_kind="CREATE" if cue_present else None,
            )
        return result

    def oracle_actions(self) -> dict[int, int]:
        return {
            slot: (
                self.spec.bit
                if self._time >= self.spec.successor_join_time
                and slot == self.spec.successor_slot
                else 1
            )
            for slot in self._active_slots()
        }

    def reactive_actions(self) -> dict[int, int]:
        return {slot: 1 for slot in self._active_slots()}

    def step(self, actions: Mapping[int, int]) -> dict[str, object]:
        if self.done:
            raise RuntimeError("cannot step a completed handoff episode")
        if not isinstance(actions, Mapping):
            raise TypeError("actions must be a mapping")
        active_slots = set(self._active_slots())
        if set(actions) != active_slots:
            raise ValueError(f"actions must contain exactly active slots {sorted(active_slots)}")
        normalized: dict[int, int] = {}
        for slot, action in actions.items():
            if type(action) is not int or action not in ACTION_VALUES:
                raise ValueError("every action must be the integer -1 or +1")
            normalized[slot] = action

        successor_active = self._time >= self.spec.successor_join_time
        reward = 0.0
        successor_action: int | None = None
        if successor_active:
            successor_action = normalized[self.spec.successor_slot]
            reward = float(successor_action == self.spec.bit)
            self._successor_correct += int(reward)
            self._successor_rows += 1
            self._successor_actions.append(successor_action)

        self._time += 1
        done = self.done
        utility = (
            self._successor_correct / self._successor_rows
            if done and self._successor_rows
            else None
        )
        return {
            "reward": reward,
            "done": done,
            "successor_action": successor_action,
            "utility": utility,
        }

    def snapshot_state(self) -> dict[str, Any]:
        return deepcopy(
            {
                "schema": "cross_lifecycle_handoff_g2_env_state_v1",
                "spec": self.spec,
                "time": self._time,
                "successor_correct": self._successor_correct,
                "successor_rows": self._successor_rows,
                "successor_actions": tuple(self._successor_actions),
            }
        )

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "CrossLifecycleHandoffG2Env":
        copied = deepcopy(dict(snapshot))
        if copied.pop("schema", None) != "cross_lifecycle_handoff_g2_env_state_v1":
            raise ValueError("snapshot schema mismatch")
        environment = cls(copied.pop("spec"))
        environment._time = copied.pop("time")
        environment._successor_correct = copied.pop("successor_correct")
        environment._successor_rows = copied.pop("successor_rows")
        environment._successor_actions = list(copied.pop("successor_actions"))
        if copied or not 0 <= environment._time <= environment.spec.horizon:
            raise ValueError("snapshot contents are invalid")
        return environment


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
