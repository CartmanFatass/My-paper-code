"""Zero-training information gate for asynchronous commitment rosters."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import permutations
import math
import re
from typing import Any, Iterable


SOURCE_FAMILY = "ASYNC_COMMITMENT_ROSTER_G3"
SCHEMA = "async_commitment_roster_g3_information_gate_v1"
PASS_RESULT = "PASS_ASYNC_ROSTER_INFORMATION_GATE_G3"
FAIL_RESULT = "FAIL_ASYNC_ROSTER_INFORMATION_GATE_G3"
INVALID_RESULT = "INVALID_ASYNC_ROSTER_INFORMATION_GATE_G3"

LABELS = (0, 1, 2, 3)
PHYSICAL_SLOTS = (0, 1, 2, 3, 4)
ACTIVE_COUNTS = (2, 3, 4)
CASE_VARIANTS = (
    "RENEW",
    "JOIN",
    "REJOIN",
    "REPLACE_SAME_SLOT",
    "REPLACE_CROSS_SLOT",
)
EXPECTED_CASE_COUNTS = {2: 400, 3: 3_600, 4: 14_400}
EXPECTED_CASE_COUNT = sum(EXPECTED_CASE_COUNTS.values())


def _checked_int(name: str, value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _checked_label(value: object) -> int:
    if type(value) is not int or value not in LABELS:
        raise ValueError("commitment label is outside the registered support")
    return value


def _checked_slot(value: object) -> int:
    if type(value) is not int or value not in PHYSICAL_SLOTS:
        raise ValueError("physical slot is outside the registered support")
    return value


@dataclass(frozen=True, slots=True)
class CommitmentRecord:
    lifecycle_id: int
    physical_slot: int
    commitment: int | None
    active: bool


@dataclass(frozen=True, slots=True)
class RosterEvent:
    kind: str
    lifecycle_id: int
    physical_slot: int
    commitment: int | None


@dataclass(frozen=True, slots=True)
class RosterState:
    """Lifecycle-owned records; physical slots are packing coordinates only."""

    records: tuple[CommitmentRecord, ...]
    history: tuple[RosterEvent, ...]

    @classmethod
    def empty(cls) -> "RosterState":
        return cls(records=(), history=())

    def contains(self, lifecycle_id: int) -> bool:
        return any(record.lifecycle_id == lifecycle_id for record in self.records)

    def record(self, lifecycle_id: int) -> CommitmentRecord:
        matches = [
            record for record in self.records if record.lifecycle_id == lifecycle_id
        ]
        if len(matches) != 1:
            raise KeyError(f"lifecycle {lifecycle_id} is not present exactly once")
        return matches[0]

    def _replace_record(self, updated: CommitmentRecord) -> "RosterState":
        records = tuple(
            updated if record.lifecycle_id == updated.lifecycle_id else record
            for record in self.records
        )
        return replace(self, records=records)

    def _append_event(
        self,
        kind: str,
        lifecycle_id: int,
        physical_slot: int,
        commitment: int | None,
    ) -> "RosterState":
        event = RosterEvent(kind, lifecycle_id, physical_slot, commitment)
        return replace(self, history=self.history + (event,))

    def _assert_slot_available(
        self, physical_slot: int, *, except_lifecycle: int | None = None
    ) -> None:
        for record in self.records:
            if (
                record.active
                and record.physical_slot == physical_slot
                and record.lifecycle_id != except_lifecycle
            ):
                raise ValueError("two active lifecycles cannot occupy one physical slot")

    def join(self, lifecycle_id: int, physical_slot: int) -> "RosterState":
        lifecycle_id = _checked_int("lifecycle_id", lifecycle_id)
        physical_slot = _checked_slot(physical_slot)
        if self.contains(lifecycle_id):
            raise ValueError("JOIN cannot reuse a live lifecycle identifier")
        self._assert_slot_available(physical_slot)
        state = replace(
            self,
            records=self.records
            + (CommitmentRecord(lifecycle_id, physical_slot, None, True),),
        )
        return state._append_event("JOIN", lifecycle_id, physical_slot, None)

    def commit(self, lifecycle_id: int, commitment: int) -> "RosterState":
        commitment = _checked_label(commitment)
        record = self.record(lifecycle_id)
        if not record.active or record.commitment is not None:
            raise ValueError("COMMIT requires an active uncommitted lifecycle")
        state = self._replace_record(replace(record, commitment=commitment))
        return state._append_event(
            "COMMIT", lifecycle_id, record.physical_slot, commitment
        )

    def renew(self, lifecycle_id: int) -> "RosterState":
        record = self.record(lifecycle_id)
        if not record.active or record.commitment is None:
            raise ValueError("RENEW requires an active committed lifecycle")
        state = self._replace_record(replace(record, commitment=None))
        return state._append_event(
            "RENEW", lifecycle_id, record.physical_slot, record.commitment
        )

    def temporary_leave(self, lifecycle_id: int) -> "RosterState":
        record = self.record(lifecycle_id)
        if not record.active or record.commitment is None:
            raise ValueError("temporary LEAVE requires an active commitment")
        state = self._replace_record(replace(record, active=False))
        return state._append_event(
            "TEMP_LEAVE", lifecycle_id, record.physical_slot, record.commitment
        )

    def rejoin(self, lifecycle_id: int, physical_slot: int) -> "RosterState":
        physical_slot = _checked_slot(physical_slot)
        record = self.record(lifecycle_id)
        if record.active or record.commitment is None:
            raise ValueError("REJOIN requires an absent lifecycle with held state")
        self._assert_slot_available(physical_slot, except_lifecycle=lifecycle_id)
        state = self._replace_record(
            replace(record, physical_slot=physical_slot, active=True)
        )
        return state._append_event(
            "REJOIN", lifecycle_id, physical_slot, record.commitment
        )

    def terminal_leave(self, lifecycle_id: int) -> "RosterState":
        record = self.record(lifecycle_id)
        records = tuple(
            candidate
            for candidate in self.records
            if candidate.lifecycle_id != lifecycle_id
        )
        state = replace(self, records=records)
        return state._append_event(
            "TERMINAL_LEAVE",
            lifecycle_id,
            record.physical_slot,
            record.commitment,
        )

    def intervene_commitment(
        self, lifecycle_id: int, commitment: int
    ) -> "RosterState":
        """Change only one retained record from an exact pre-edit snapshot."""

        commitment = _checked_label(commitment)
        record = self.record(lifecycle_id)
        if not record.active or record.commitment is None:
            raise ValueError("intervention target must be active and committed")
        if commitment == record.commitment:
            raise ValueError("intervention must change the retained commitment")
        return self._replace_record(replace(record, commitment=commitment))

    def standing_records(
        self, *, editor_lifecycle: int
    ) -> tuple[CommitmentRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self.records
                    if record.active
                    and record.lifecycle_id != editor_lifecycle
                    and record.commitment is not None
                ),
                key=lambda record: record.lifecycle_id,
            )
        )


@dataclass(frozen=True, slots=True)
class GateCase:
    case_id: int
    active_count: int
    variant: str
    editor_lifecycle: int
    state: RosterState
    editor_context: tuple[float, float, float]

    @property
    def standing_records(self) -> tuple[CommitmentRecord, ...]:
        return self.state.standing_records(editor_lifecycle=self.editor_lifecycle)

    @property
    def standing_commitments(self) -> tuple[int, ...]:
        return tuple(
            int(record.commitment) for record in self.standing_records
        )


def _event_code(variant: str) -> float:
    if variant == "RENEW":
        return 0.0
    if variant == "JOIN":
        return 0.25
    if variant == "REJOIN":
        return 0.5
    if variant.startswith("REPLACE_"):
        return 0.75
    raise ValueError("unknown case variant")


def _build_case(
    *,
    case_id: int,
    active_count: int,
    variant: str,
    editor_slot: int,
    standing_slots: tuple[int, ...],
    standing_labels: tuple[int, ...],
) -> GateCase:
    if variant not in CASE_VARIANTS:
        raise ValueError("unknown case variant")
    if len(standing_slots) != active_count - 1 or len(standing_labels) != active_count - 1:
        raise ValueError("standing roster width does not match active count")
    if len(set(standing_slots)) != len(standing_slots) or editor_slot in standing_slots:
        raise ValueError("physical packing collides")
    if len(set(standing_labels)) != len(standing_labels):
        raise ValueError("standing commitments must be unique")

    state = RosterState.empty()
    standing_lifecycles: list[int] = []
    for index, (slot, label) in enumerate(zip(standing_slots, standing_labels)):
        lifecycle_id = 100 + index
        standing_lifecycles.append(lifecycle_id)
        state = state.join(lifecycle_id, slot).commit(lifecycle_id, label)

    editor_lifecycle = 900
    old_label = (standing_labels[0] + 1) % len(LABELS)
    if variant == "RENEW":
        state = state.join(editor_lifecycle, editor_slot)
        state = state.commit(editor_lifecycle, old_label)
        state = state.renew(editor_lifecycle)
    elif variant == "JOIN":
        state = state.join(editor_lifecycle, editor_slot)
    elif variant == "REJOIN":
        restored_lifecycle = standing_lifecycles[0]
        restored_slot = state.record(restored_lifecycle).physical_slot
        state = state.temporary_leave(restored_lifecycle)
        state = state.rejoin(restored_lifecycle, restored_slot)
        state = state.join(editor_lifecycle, editor_slot)
        state = state.commit(editor_lifecycle, old_label)
        state = state.renew(editor_lifecycle)
    else:
        unused_slots = sorted(
            set(PHYSICAL_SLOTS) - {editor_slot, *standing_slots}
        )
        departure_slot = (
            editor_slot
            if variant == "REPLACE_SAME_SLOT"
            else unused_slots[0]
        )
        departing_lifecycle = 800
        state = state.join(departing_lifecycle, departure_slot)
        state = state.commit(departing_lifecycle, old_label)
        state = state.terminal_leave(departing_lifecycle)
        state = state.join(editor_lifecycle, editor_slot)

    if len([record for record in state.records if record.active]) != active_count:
        raise AssertionError("case construction produced the wrong active count")
    if state.record(editor_lifecycle).commitment is not None:
        raise AssertionError("editor must begin the decision uncommitted")

    editor_context = (
        _event_code(variant),
        float(active_count / max(ACTIVE_COUNTS)),
        float(variant in ("JOIN", "REPLACE_SAME_SLOT", "REPLACE_CROSS_SLOT")),
    )
    return GateCase(
        case_id=case_id,
        active_count=active_count,
        variant=variant,
        editor_lifecycle=editor_lifecycle,
        state=state,
        editor_context=editor_context,
    )


def enumerate_cases() -> Iterable[GateCase]:
    case_id = 0
    for active_count in ACTIVE_COUNTS:
        width = active_count - 1
        for standing_labels in permutations(LABELS, width):
            for editor_slot in PHYSICAL_SLOTS:
                available = tuple(
                    slot for slot in PHYSICAL_SLOTS if slot != editor_slot
                )
                for standing_slots in permutations(available, width):
                    for variant in CASE_VARIANTS:
                        yield _build_case(
                            case_id=case_id,
                            active_count=active_count,
                            variant=variant,
                            editor_slot=editor_slot,
                            standing_slots=standing_slots,
                            standing_labels=standing_labels,
                        )
                        case_id += 1


def _smallest_missing(commitments: Iterable[int]) -> int:
    present = set(commitments)
    for label in LABELS:
        if label not in present:
            return label
    raise ValueError("no legal missing commitment remains")


def _utility(commitments: Iterable[int], editor_choice: int) -> Fraction:
    values = tuple(commitments) + (_checked_label(editor_choice),)
    return Fraction(len(set(values)), len(values))


def _reconstruct_standing_from_history(
    history: tuple[RosterEvent, ...], *, editor_lifecycle: int
) -> tuple[int, ...]:
    records: dict[int, CommitmentRecord] = {}
    for event in history:
        if event.kind == "JOIN":
            records[event.lifecycle_id] = CommitmentRecord(
                event.lifecycle_id, event.physical_slot, None, True
            )
        elif event.kind == "COMMIT":
            record = records[event.lifecycle_id]
            records[event.lifecycle_id] = replace(
                record, commitment=_checked_label(event.commitment)
            )
        elif event.kind == "RENEW":
            record = records[event.lifecycle_id]
            records[event.lifecycle_id] = replace(record, commitment=None)
        elif event.kind == "TEMP_LEAVE":
            record = records[event.lifecycle_id]
            records[event.lifecycle_id] = replace(record, active=False)
        elif event.kind == "REJOIN":
            record = records[event.lifecycle_id]
            records[event.lifecycle_id] = replace(
                record, physical_slot=event.physical_slot, active=True
            )
        elif event.kind == "TERMINAL_LEAVE":
            records.pop(event.lifecycle_id)
        else:
            raise ValueError("history contains an unknown event")
    return tuple(
        sorted(
            int(record.commitment)
            for lifecycle_id, record in records.items()
            if lifecycle_id != editor_lifecycle
            and record.active
            and record.commitment is not None
        )
    )


def _ownership_audit() -> dict[str, bool]:
    state = RosterState.empty().join(1, 0).commit(1, 2)
    absent = state.temporary_leave(1)
    restored = absent.rejoin(1, 4)
    terminal = restored.terminal_leave(1)
    fresh = terminal.join(2, 4)
    return {
        "temporary_leave_freezes_commitment": absent.record(1).commitment == 2,
        "rejoin_restores_commitment": restored.record(1).commitment == 2,
        "commitment_not_physical_slot_owned": (
            restored.record(1).physical_slot == 4
            and restored.record(1).commitment == 2
        ),
        "terminal_leave_deletes_commitment": not terminal.contains(1),
        "fresh_join_is_uncommitted": fresh.record(2).commitment is None,
    }


def _fraction_means(
    sums: dict[int, Fraction], counts: Counter[int]
) -> dict[str, float]:
    return {
        str(active_count): float(sums[active_count] / counts[active_count])
        for active_count in ACTIVE_COUNTS
    }


def _expected_independent(active_count: int) -> Fraction:
    missing_count = len(LABELS) - (active_count - 1)
    duplicate_count = active_count - 1
    return (
        Fraction(missing_count, len(LABELS))
        + Fraction(duplicate_count, len(LABELS))
        * Fraction(active_count - 1, active_count)
    )


def evaluate_information_gate(
    *, source_commit: str = "UNBOUND_NONFORMAL"
) -> dict[str, Any]:
    counts: Counter[int] = Counter()
    variant_counts: Counter[str] = Counter()
    roster_sum: dict[int, Fraction] = defaultdict(Fraction)
    team_sum: dict[int, Fraction] = defaultdict(Fraction)
    independent_sum: dict[int, Fraction] = defaultdict(Fraction)
    shuffled_sum: dict[int, Fraction] = defaultdict(Fraction)
    choice_change_sum: dict[int, Fraction] = defaultdict(Fraction)
    adapted_sum: dict[int, Fraction] = defaultdict(Fraction)
    replay_sum: dict[int, Fraction] = defaultdict(Fraction)
    gain_sum: dict[int, Fraction] = defaultdict(Fraction)

    slot_invariance: dict[
        tuple[int, str, tuple[int, ...]],
        tuple[int, int, Fraction, Fraction, int, Fraction, Fraction],
    ] = {}
    context_invariance: dict[tuple[int, str], tuple[float, float, float]] = {}

    for case in enumerate_cases():
        active_count = case.active_count
        counts[active_count] += 1
        variant_counts[case.variant] += 1
        standing = case.standing_commitments
        if len(standing) != active_count - 1 or len(set(standing)) != len(standing):
            raise AssertionError("case standing roster is not the exhaustive unique support")

        roster_choice = _smallest_missing(standing)
        roster_utility = _utility(standing, roster_choice)
        team_standing = _reconstruct_standing_from_history(
            case.state.history, editor_lifecycle=case.editor_lifecycle
        )
        if tuple(sorted(standing)) != team_standing:
            raise AssertionError("TEAM_REC oracle history does not reconstruct the roster")
        team_choice = _smallest_missing(team_standing)
        team_utility = _utility(standing, team_choice)

        independent_utility = sum(
            (_utility(standing, choice) for choice in LABELS), Fraction()
        ) / len(LABELS)
        shuffled = tuple((label + 1) % len(LABELS) for label in standing)
        shuffled_choice = _smallest_missing(shuffled)
        shuffled_utility = _utility(standing, shuffled_choice)

        target = min(
            case.standing_records,
            key=lambda record: (int(record.commitment), record.lifecycle_id),
        )
        intervened = case.state.intervene_commitment(
            target.lifecycle_id, roster_choice
        )
        intervened_standing = tuple(
            int(record.commitment)
            for record in intervened.standing_records(
                editor_lifecycle=case.editor_lifecycle
            )
        )
        adapted_choice = _smallest_missing(intervened_standing)
        adapted_utility = _utility(intervened_standing, adapted_choice)
        replay_utility = _utility(intervened_standing, roster_choice)
        choice_change = Fraction(int(adapted_choice != roster_choice), 1)
        utility_gain = adapted_utility - replay_utility

        unchanged_records = {
            record.lifecycle_id: record
            for record in case.state.records
            if record.lifecycle_id != target.lifecycle_id
        }
        intervened_unchanged = {
            record.lifecycle_id: record
            for record in intervened.records
            if record.lifecycle_id != target.lifecycle_id
        }
        if unchanged_records != intervened_unchanged or intervened.history != case.state.history:
            raise AssertionError("roster intervention changed more than one held record")

        roster_sum[active_count] += roster_utility
        team_sum[active_count] += team_utility
        independent_sum[active_count] += independent_utility
        shuffled_sum[active_count] += shuffled_utility
        choice_change_sum[active_count] += choice_change
        adapted_sum[active_count] += adapted_utility
        replay_sum[active_count] += replay_utility
        gain_sum[active_count] += utility_gain

        invariant_key = (
            active_count,
            case.variant,
            tuple(sorted(standing)),
        )
        invariant_value = (
            roster_choice,
            team_choice,
            independent_utility,
            shuffled_utility,
            adapted_choice,
            adapted_utility,
            replay_utility,
        )
        prior = slot_invariance.setdefault(invariant_key, invariant_value)
        if prior != invariant_value:
            raise AssertionError("a physical-slot permutation changed gate behavior")

        context_key = (active_count, case.variant)
        prior_context = context_invariance.setdefault(context_key, case.editor_context)
        if prior_context != case.editor_context:
            raise AssertionError("editor context contains packing or lifecycle identity")

    case_count = sum(counts.values())
    roster_by_active = _fraction_means(roster_sum, counts)
    team_by_active = _fraction_means(team_sum, counts)
    independent_by_active = _fraction_means(independent_sum, counts)
    shuffled_by_active = _fraction_means(shuffled_sum, counts)
    choice_change_by_active = _fraction_means(choice_change_sum, counts)
    adapted_by_active = _fraction_means(adapted_sum, counts)
    replay_by_active = _fraction_means(replay_sum, counts)
    gain_by_active = _fraction_means(gain_sum, counts)

    checks = {
        "editor_context_anonymous": all(
            len(context) == 3 and all(type(value) is float for value in context)
            for context in context_invariance.values()
        ),
        "event_variant_balanced": len(set(variant_counts.values())) == 1,
        "physical_slot_permutation_invariant": True,
        "standing_roster_permutation_complete": (
            counts == Counter(EXPECTED_CASE_COUNTS)
        ),
    }
    ownership = _ownership_audit()
    metrics = {
        "roster_editor_utility": float(
            sum(roster_sum.values(), Fraction()) / case_count
        ),
        "team_rec_oracle_utility": float(
            sum(team_sum.values(), Fraction()) / case_count
        ),
        "roster_editor_utility_by_active": roster_by_active,
        "team_rec_oracle_utility_by_active": team_by_active,
        "independent_editor_utility_by_active": independent_by_active,
        "shuffled_roster_utility_by_active": shuffled_by_active,
        "intervention_choice_change": float(
            sum(choice_change_sum.values(), Fraction()) / case_count
        ),
        "intervention_adapted_utility": float(
            sum(adapted_sum.values(), Fraction()) / case_count
        ),
        "intervention_choice_change_by_active": choice_change_by_active,
        "intervention_adapted_utility_by_active": adapted_by_active,
        "intervention_replayed_utility_by_active": replay_by_active,
        "intervention_utility_gain_by_active": gain_by_active,
    }

    structural_valid = (
        case_count == EXPECTED_CASE_COUNT
        and counts == Counter(EXPECTED_CASE_COUNTS)
        and all(checks.values())
        and all(ownership.values())
        and all(
            math.isfinite(value)
            for value in (
                metrics["roster_editor_utility"],
                metrics["team_rec_oracle_utility"],
                metrics["intervention_choice_change"],
                metrics["intervention_adapted_utility"],
            )
        )
    )
    pass_metrics = (
        metrics["roster_editor_utility"] == 1.0
        and metrics["team_rec_oracle_utility"] == 1.0
        and all(value == 1.0 for value in roster_by_active.values())
        and all(value == 1.0 for value in team_by_active.values())
        and all(
            independent_by_active[str(active_count)]
            == float(_expected_independent(active_count))
            for active_count in ACTIVE_COUNTS
        )
        and all(value < 1.0 for value in shuffled_by_active.values())
        and metrics["intervention_choice_change"] == 1.0
        and metrics["intervention_adapted_utility"] == 1.0
        and all(
            gain_by_active[str(active_count)] == float(Fraction(1, active_count))
            for active_count in ACTIVE_COUNTS
        )
    )
    result = (
        INVALID_RESULT
        if not structural_valid
        else PASS_RESULT
        if pass_metrics
        else FAIL_RESULT
    )
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": False,
        "status": "COMPLETE",
        "result": result,
        "case_count": case_count,
        "case_counts_by_active": {
            str(active_count): counts[active_count]
            for active_count in ACTIVE_COUNTS
        },
        "case_counts_by_variant": {
            variant: variant_counts[variant] for variant in CASE_VARIANTS
        },
        "checks": checks,
        "state_ownership": ownership,
        "metrics": metrics,
    }
    return payload


def _require_exact_dict(name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{name} must be an exact object")
    return value


def validate_information_gate_result(payload: object) -> None:
    data = _require_exact_dict("payload", payload)
    if data.get("schema") != SCHEMA or data.get("source_family") != SOURCE_FAMILY:
        raise ValueError("information-gate schema/source mismatch")
    if data.get("formal") is not False:
        raise ValueError("information gate must retain formal=false")
    if data.get("status") != "COMPLETE":
        raise ValueError("information gate is not complete")
    source_commit = data.get("source_commit")
    if source_commit != "UNBOUND_NONFORMAL" and (
        type(source_commit) is not str
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
    ):
        raise ValueError("source_commit is not an exact lowercase Git identity")
    if data.get("case_count") != EXPECTED_CASE_COUNT:
        raise ValueError("case_count does not close the exhaustive inventory")
    if data.get("case_counts_by_active") != {
        str(key): value for key, value in EXPECTED_CASE_COUNTS.items()
    }:
        raise ValueError("active-count inventory mismatch")
    variant_counts = _require_exact_dict(
        "case_counts_by_variant", data.get("case_counts_by_variant")
    )
    expected_variant_count = EXPECTED_CASE_COUNT // len(CASE_VARIANTS)
    if variant_counts != {
        variant: expected_variant_count for variant in CASE_VARIANTS
    }:
        raise ValueError("event-variant inventory mismatch")
    checks = _require_exact_dict("checks", data.get("checks"))
    ownership = _require_exact_dict("state_ownership", data.get("state_ownership"))
    if not checks or not ownership or not all(value is True for value in checks.values()):
        expected = INVALID_RESULT
    elif not all(value is True for value in ownership.values()):
        expected = INVALID_RESULT
    else:
        metrics = _require_exact_dict("metrics", data.get("metrics"))
        independent = _require_exact_dict(
            "independent_editor_utility_by_active",
            metrics.get("independent_editor_utility_by_active"),
        )
        shuffled = _require_exact_dict(
            "shuffled_roster_utility_by_active",
            metrics.get("shuffled_roster_utility_by_active"),
        )
        gains = _require_exact_dict(
            "intervention_utility_gain_by_active",
            metrics.get("intervention_utility_gain_by_active"),
        )
        registered_numbers = [
            metrics.get("roster_editor_utility"),
            metrics.get("team_rec_oracle_utility"),
            metrics.get("intervention_choice_change"),
            metrics.get("intervention_adapted_utility"),
            *independent.values(),
            *shuffled.values(),
            *gains.values(),
        ]
        if any(
            type(value) not in (int, float)
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            for value in registered_numbers
        ):
            expected = INVALID_RESULT
        else:
            passes = (
                metrics.get("roster_editor_utility") == 1.0
                and metrics.get("team_rec_oracle_utility") == 1.0
                and metrics.get("intervention_choice_change") == 1.0
                and metrics.get("intervention_adapted_utility") == 1.0
                and independent
                == {
                    str(active_count): float(_expected_independent(active_count))
                    for active_count in ACTIVE_COUNTS
                }
                and set(shuffled) == {str(value) for value in ACTIVE_COUNTS}
                and all(float(value) < 1.0 for value in shuffled.values())
                and gains
                == {
                    str(active_count): float(Fraction(1, active_count))
                    for active_count in ACTIVE_COUNTS
                }
            )
            expected = PASS_RESULT if passes else FAIL_RESULT
    if data.get("result") != expected:
        raise ValueError("registered result does not follow the frozen selector")
