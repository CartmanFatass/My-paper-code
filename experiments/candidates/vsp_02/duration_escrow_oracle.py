from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
from itertools import product
from types import MappingProxyType
from typing import Callable, Iterable, Mapping


GAMMA, CURRENT_VERSION, HORIZON = Fraction(1, 2), 9, 2; PRIMITIVE_TAPE, PARTNER_TAPE = ("hold", "advance"), ("silent", "ack")


class State(str, Enum):
    VACANT = "VACANT"; OPEN_ACTIVE = "OPEN_ACTIVE"; OPEN_NATURAL = "OPEN_NATURAL"
    OPEN_INTERRUPTED = "OPEN_INTERRUPTED"; TERMINAL_READY = "TERMINAL_READY"
    HORIZON_READY = "HORIZON_READY"; RELEASED = "RELEASED"; INVALID = "INVALID"


class Event(str, Enum):
    CLAIM = "CLAIM"; NATURAL = "NATURAL"; INTERRUPT_NATURAL = "INTERRUPT_NATURAL"
    HORIZON = "HORIZON"; TERMINAL_HORIZON = "TERMINAL_HORIZON"; RELEASE = "RELEASE"
    STALE_VERSION = "STALE_VERSION"; ILLEGAL = "ILLEGAL"


class World(str, Enum):
    POSITIVE = "W+"; ZERO = "W0"


class Context(str, Enum):
    F = "F"; P = "P"


class Action(str, Enum):
    SHORT = "SHORT"; LONG = "LONG"


class CloseMode(str, Enum):
    NATURAL = "NATURAL"; SIMULTANEOUS_INTERRUPT_NATURAL = "SIMULTANEOUS_INTERRUPT_NATURAL"


class Cutoff(str, Enum):
    HORIZON = "HORIZON"; SIMULTANEOUS_TERMINAL_HORIZON = "SIMULTANEOUS_TERMINAL_HORIZON"


@dataclass(frozen=True)
class FutureBranch:
    world: World; close_mode: CloseMode; cutoff: Cutoff
    owner_departure: bool; weight: Fraction

    def key(self) -> tuple[World, CloseMode, Cutoff, bool]:
        return self.world, self.close_mode, self.cutoff, self.owner_departure


Z0_FULL_FIELDS = ("context", "tau", "public_history_at_tau", "focal_execution_phase", "public_partner_phase", "legal_duration_mask", "behavior_version")
CANDIDATE_Z0_USED_FIELDS = COMPARATOR_Z0_USED_FIELDS = ("context",)
CANDIDATE_IGNORED_LEGAL_FIELDS = COMPARATOR_IGNORED_LEGAL_FIELDS = (
    "tau", "public_history_at_tau", "focal_execution_phase", "public_partner_phase", "legal_duration_mask", "behavior_version",
)
BRANCH_FIELDS = ("world", "close_mode", "cutoff", "owner_departure")
SELECTOR_TAPE = tuple(Fraction(index, 8) for index in range(8))
REGISTERED_SELECTOR_TAPE = (
    Fraction(0), Fraction(1, 8), Fraction(1, 4), Fraction(3, 8), Fraction(1, 2), Fraction(5, 8), Fraction(3, 4), Fraction(7, 8),
)
COMPARATOR_PROBABILITIES: Mapping[Context, Fraction] = MappingProxyType({
    Context.F: Fraction(1, 4), Context.P: Fraction(3, 4),
})
BRANCH_LAW = tuple(
    FutureBranch(world, close, cutoff, departure, Fraction(1, 16))
    for world, close, cutoff, departure in product(
        World, CloseMode, Cutoff, (False, True)
    )
)


EXPECTED_DELTAS = {
    (World.POSITIVE, Context.F): -GAMMA / 2,
    (World.POSITIVE, Context.P): GAMMA / 4,
    (World.ZERO, Context.F): Fraction(0),
    (World.ZERO, Context.P): Fraction(0),
}


_LEGAL_TRANSITIONS = {
    (State.VACANT, Event.CLAIM): State.OPEN_ACTIVE,
    (State.OPEN_ACTIVE, Event.NATURAL): State.OPEN_NATURAL,
    (State.OPEN_ACTIVE, Event.INTERRUPT_NATURAL): State.OPEN_INTERRUPTED,
    (State.OPEN_NATURAL, Event.HORIZON): State.HORIZON_READY,
    (State.OPEN_INTERRUPTED, Event.HORIZON): State.HORIZON_READY,
    (State.OPEN_NATURAL, Event.TERMINAL_HORIZON): State.TERMINAL_READY,
    (State.OPEN_INTERRUPTED, Event.TERMINAL_HORIZON): State.TERMINAL_READY,
    (State.TERMINAL_READY, Event.RELEASE): State.RELEASED,
    (State.HORIZON_READY, Event.RELEASE): State.RELEASED,
}


def transition(state: State, event: Event) -> State:
    if state is State.INVALID: return State.INVALID
    return _LEGAL_TRANSITIONS.get((state, event), State.INVALID)


def resolve_close(*, natural: bool, interrupt: bool) -> Event:
    if interrupt: return Event.INTERRUPT_NATURAL
    if natural: return Event.NATURAL
    raise ValueError("ambiguous close: neither natural nor interrupt")


def resolve_cutoff(*, horizon: bool, terminal: bool) -> Event:
    if terminal: return Event.TERMINAL_HORIZON
    if horizon: return Event.HORIZON
    raise ValueError("ambiguous cutoff: neither horizon nor terminal")


@dataclass(frozen=True)
class DecisionIdentity:
    episode_id: str; source_owner_epoch: int; own_boundary_index: int; behavior_version: int


@dataclass(frozen=True)
class CaseSpec:
    world: World; context: Context; action: Action; close_mode: CloseMode
    cutoff: Cutoff; owner_departure: bool; behavior_version: int; base_index: int


@dataclass(frozen=True)
class PhysicalTrace:
    tau: int; horizon: int; terminal_time: int; rewards: tuple[Fraction, ...]
    vbar: Fraction; close_outcome: str; cutoff_outcome: str; final_owner_epoch: int
    primitive_tape: tuple[str, ...]; partner_tape: tuple[str, ...]
    timing: tuple[int, int, int, int]


@dataclass(frozen=True)
class EventRecord:
    event_id: str; identity: DecisionIdentity; slot_index: int; event: Event
    before: State; after: State; policy_clock: int; environment_clock: int


@dataclass(frozen=True)
class ScoreRecord:
    identity: DecisionIdentity; target: Fraction; score: Fraction; action: Action


@dataclass(frozen=True)
class TombstoneRecord:
    identity: DecisionIdentity; final_state: State; target: Fraction | None; reason: str


@dataclass(frozen=True)
class ReleaseRecord:
    identity: DecisionIdentity; target: Fraction; release_clock: int


@dataclass(frozen=True)
class PolicyParameter:
    name: str


@dataclass(frozen=True)
class FrozenBootstrap:
    name: str; value: Fraction; trainable: bool = False


@dataclass(frozen=True)
class CaseResult:
    spec: CaseSpec; identity: DecisionIdentity; slot_index: int; valid: bool
    final_state: State; physical: PhysicalTrace | None; target: Fraction | None
    target_recomputed: Fraction | None; events: tuple[EventRecord, ...]
    scores: tuple[ScoreRecord, ...]; tombstones: tuple[TombstoneRecord, ...]
    releases: tuple[ReleaseRecord, ...]


@dataclass(frozen=True)
class OracleAudit:
    cases: tuple[CaseResult, ...]; report: dict[str, object]


def _probability(context: Context) -> Fraction:
    return Fraction(1, 4) if context is Context.F else Fraction(3, 4)


def candidate_selector(context: Context, tape: Fraction) -> Action:
    return Action.LONG if tape < _probability(context) else Action.SHORT


def comparator_selector(
    context: Context, tape: Fraction,
    probabilities: Mapping[Context, Fraction] = COMPARATOR_PROBABILITIES,
) -> Action:
    return Action.LONG if tape < probabilities[context] else Action.SHORT


def _occupancy(context: Context) -> Fraction:
    return Fraction(2, 5) if context is Context.F else Fraction(3, 5)


def physical_kernel(spec: CaseSpec) -> PhysicalTrace:
    r0 = Fraction(1, 2) if spec.context is Context.F else Fraction(3, 2)
    r1 = Fraction(1)
    if spec.close_mode is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL:
        r0, r1 = r0 + Fraction(1, 32), r1 + Fraction(1, 16)
    if spec.owner_departure:
        r0, r1 = r0 + Fraction(1, 64), r1 + Fraction(1, 32)
    terminal = spec.cutoff is Cutoff.SIMULTANEOUS_TERMINAL_HORIZON
    if terminal:
        r0, r1 = r0 + Fraction(1, 16), r1 + Fraction(1, 8)
    else:
        r0 -= Fraction(1, 8)
    if spec.world is World.POSITIVE and spec.action is Action.LONG:
        if spec.context is Context.F:
            r0, r1 = r0 - Fraction(1, 8), r1 - Fraction(1, 4)
        else:
            r0, r1 = r0 + Fraction(1, 16), r1 + Fraction(1, 8)
    tau = 100 + 4 * int(spec.owner_departure)
    terminal_time = tau + HORIZON if terminal else tau + HORIZON + 1
    close_outcome = (
        "INTERRUPTED"
        if spec.close_mode is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL
        else "NATURAL"
    )
    cutoff_outcome = "TERMINAL" if terminal else "HORIZON"
    owner_epoch = 8 if spec.owner_departure else 7
    return PhysicalTrace(
        tau,
        HORIZON,
        terminal_time,
        (r0, r1),
        Fraction(1, 2),
        close_outcome,
        cutoff_outcome,
        owner_epoch,
        PRIMITIVE_TAPE,
        PARTNER_TAPE,
        (tau, tau + 1, tau + HORIZON, tau + HORIZON),
    )


def absolute_target(trace: PhysicalTrace, *, bootstrap_on_terminal: bool = False) -> Fraction:
    kappa = min(trace.terminal_time, trace.tau + trace.horizon)
    terminal = trace.terminal_time <= trace.tau + trace.horizon
    if terminal and bootstrap_on_terminal:
        raise ValueError("terminal branch forbids bootstrap")
    count = kappa - trace.tau
    if count < 0 or count > len(trace.rewards):
        raise ValueError("illegal absolute-time reward support")
    target = sum(
        (GAMMA**offset) * trace.rewards[offset]
        for offset in range(count)
    )
    if trace.terminal_time > trace.tau + trace.horizon:
        target += GAMMA**trace.horizon * trace.vbar
    return target


def validate_parameter_separation(policy: object, bootstrap: object) -> None:
    if policy is bootstrap:
        raise ValueError("shared policy/bootstrap parameter")
    if getattr(bootstrap, "trainable", True):
        raise ValueError("Vbar must be frozen/stop-gradient")


def _append_event(
    records: list[EventRecord], identity: DecisionIdentity, slot: int,
    event: Event, policy_clock: int, environment_clock: int,
) -> State:
    before = records[-1].after if records else State.VACANT
    after = transition(before, event)
    records.append(EventRecord(
        f"{identity.episode_id}:{identity.own_boundary_index}:{len(records)}",
        identity, slot, event, before, after, policy_clock, environment_clock,
    ))
    return after


def execute_case(spec: CaseSpec) -> CaseResult:
    identity = DecisionIdentity(
        f"{spec.world.value}-episode", 7, spec.base_index, spec.behavior_version
    )
    slot = spec.base_index % 4
    if spec.behavior_version != CURRENT_VERSION:
        record = EventRecord(
            f"{identity.episode_id}:{identity.own_boundary_index}:stale",
            identity, slot, Event.STALE_VERSION, State.VACANT, State.INVALID,
            spec.base_index, 100,
        )
        tombstone = TombstoneRecord(identity, State.INVALID, None, "STALE_VERSION")
        return CaseResult(
            spec, identity, slot, False, State.INVALID, None, None, None,
            (record,), (), (tombstone,), (),
        )
    trace = physical_kernel(spec)
    target = absolute_target(trace)
    recomputed = absolute_target(trace)
    events: list[EventRecord] = []
    policy_clock = spec.base_index
    _append_event(events, identity, slot, Event.CLAIM, policy_clock, trace.tau)
    close = resolve_close(
        natural=True,
        interrupt=spec.close_mode is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL,
    )
    _append_event(events, identity, slot, close, policy_clock, trace.tau + 1)
    cutoff = resolve_cutoff(
        horizon=True,
        terminal=spec.cutoff is Cutoff.SIMULTANEOUS_TERMINAL_HORIZON,
    )
    _append_event(events, identity, slot, cutoff, policy_clock, trace.tau + HORIZON)
    final_state = _append_event(
        events, identity, slot, Event.RELEASE, policy_clock, trace.tau + HORIZON
    )
    if any(record.after is State.INVALID for record in events):
        raise ValueError("illegal transition in valid path")
    p = _probability(spec.context)
    action_code = 1 if spec.action is Action.LONG else 0
    score = ScoreRecord(identity, target, (action_code - p) * target, spec.action)
    tombstone = TombstoneRecord(identity, final_state, target, "RELEASED")
    release = ReleaseRecord(identity, target, trace.tau + HORIZON)
    return CaseResult(
        spec, identity, slot, True, final_state, trace, target, recomputed,
        tuple(events), (score,), (tombstone,), (release,),
    )


def verify_case(case: CaseResult) -> None:
    if case != execute_case(case.spec):
        raise ValueError("case record differs from canonical spec realization")
    if not case.valid:
        record, tombstone = case.events[0], case.tombstones[0]
        if not (
            case.spec.behavior_version != CURRENT_VERSION
            and record.event is Event.STALE_VERSION
            and record.before is State.VACANT and record.after is State.INVALID
            and tombstone.reason == "STALE_VERSION" and tombstone.target is None
            and not case.scores and not case.releases
        ):
            raise ValueError("stale record semantics violation")
        return
    if case.physical is None or case.target != absolute_target(case.physical):
        raise ValueError("target/physical recomputation mismatch")
    current = State.VACANT
    for record in case.events:
        if (
            record.before is not current
            or transition(current, record.event) is not record.after
            or record.after is State.INVALID
        ):
            raise ValueError("ambiguous or illegal transition trace")
        current = record.after
    close = Event.INTERRUPT_NATURAL if case.spec.close_mode is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL else Event.NATURAL
    cutoff = Event.TERMINAL_HORIZON if case.spec.cutoff is Cutoff.SIMULTANEOUS_TERMINAL_HORIZON else Event.HORIZON
    if case.events[1].event is not close or case.events[2].event is not cutoff:
        raise ValueError("simultaneous-event priority violation")


def all_specs() -> tuple[CaseSpec, ...]:
    specs: list[CaseSpec] = []
    for world in World:
        base_index = 0
        for context, action, close, cutoff, departure in product(
            Context, Action, CloseMode, Cutoff, (False, True)
        ):
            for version in (CURRENT_VERSION, CURRENT_VERSION - 1):
                specs.append(CaseSpec(
                    world, context, action, close, cutoff, departure, version, base_index
                ))
            base_index += 1
    return tuple(specs)


def _physical_key(spec: CaseSpec) -> tuple[str, str, str, str, bool]:
    return (
        spec.world.value, spec.context.value, spec.close_mode.value,
        spec.cutoff.value, spec.owner_departure,
    )


def candidate_integrated_values(
    cases: Iterable[CaseResult], law: tuple[FutureBranch, ...] = BRANCH_LAW,
) -> dict[tuple[Context, Action], Fraction]:
    weights = {branch.key(): branch.weight for branch in law}
    grouped: dict[tuple[Context, Action], dict[tuple[World, CloseMode, Cutoff, bool], Fraction]] = {}
    for case in cases:
        if not case.valid or case.target is None:
            continue
        key = (case.spec.context, case.spec.action)
        branch = (case.spec.world, case.spec.close_mode, case.spec.cutoff, case.spec.owner_departure)
        if branch in grouped.setdefault(key, {}): raise ValueError("duplicate future branch in candidate group")
        grouped[key][branch] = case.target
    if set(grouped) != set(product(Context, Action)): raise ValueError("candidate Z0/action domain mismatch")
    if any(set(realized) != set(weights) for realized in grouped.values()): raise ValueError("candidate future branch support mismatch")
    return {
        key: sum(weights[branch] * target for branch, target in realized.items())
        for key, realized in grouped.items()
    }


def comparator_integrated_values(
    law: tuple[FutureBranch, ...] = BRANCH_LAW,
) -> dict[tuple[Context, Action], Fraction]:
    values: dict[tuple[Context, Action], Fraction] = {}
    for context, action in product(Context, Action):
        values[(context, action)] = sum(branch.weight * absolute_target(physical_kernel(
            CaseSpec(branch.world, context, action, branch.close_mode, branch.cutoff,
                     branch.owner_departure, CURRENT_VERSION, 0))) for branch in law)
    return values


def registered_z0_conformance(
    cases: Iterable[CaseResult], law: tuple[FutureBranch, ...] = BRANCH_LAW,
    probabilities: Mapping[Context, Fraction] = COMPARATOR_PROBABILITIES,
    candidate_select: Callable[[Context, Fraction], Action] = candidate_selector,
    comparator_select: Callable[[Context, Fraction], Action] = comparator_selector,
) -> dict[str, object]:
    cases = tuple(cases); signatures = tuple(branch.key() for branch in law)
    law_frozen = (
        isinstance(law, tuple) and len(law) == 16 and len(set(signatures)) == 16
        and all(isinstance(branch, FutureBranch) and isinstance(branch.weight, Fraction)
                and branch.weight == Fraction(1, 16) for branch in law)
        and sum((branch.weight for branch in law), Fraction(0)) == 1
        and tuple(field.name for field in fields(FutureBranch)) == BRANCH_FIELDS + ("weight",)
    )
    candidate_choices = {(context, tape): candidate_select(context, tape)
                         for context, tape in product(Context, SELECTOR_TAPE)}
    comparator_choices = {(context, tape): comparator_select(context, tape, probabilities)
                          for context, tape in product(Context, SELECTOR_TAPE)}
    candidate_values = candidate_integrated_values(cases, law)
    comparator_values = comparator_integrated_values(law)
    expected_selector_domain = set(product(Context, REGISTERED_SELECTOR_TAPE)); expected_value_domain = set(product(Context, Action))
    tape_ordered_exact = SELECTOR_TAPE == REGISTERED_SELECTOR_TAPE; tape_length_exact = len(SELECTOR_TAPE) == 8
    tape_unique_exact = len(set(SELECTOR_TAPE)) == 8; registered_selector_keys_exact = len(expected_selector_domain) == 16
    candidate_selector_domain_exact = set(candidate_choices) == expected_selector_domain; comparator_selector_domain_exact = set(comparator_choices) == expected_selector_domain
    candidate_value_domain_exact = set(candidate_values) == expected_value_domain; comparator_value_domain_exact = set(comparator_values) == expected_value_domain
    selector_nested = set(candidate_choices).issubset(comparator_choices); selector_equal_keys = set(candidate_choices) == set(comparator_choices)
    value_nested = set(candidate_values).issubset(comparator_values); value_equal_keys = set(candidate_values) == set(comparator_values)
    branch_only_in_law = all(set(BRANCH_FIELDS).isdisjoint(fields_) for fields_ in (CANDIDATE_Z0_USED_FIELDS, COMPARATOR_Z0_USED_FIELDS))
    used_is_strict_subset = all(set(fields_) < set(Z0_FULL_FIELDS) for fields_ in (CANDIDATE_Z0_USED_FIELDS, COMPARATOR_Z0_USED_FIELDS))
    same_used_selector_information = (
        CANDIDATE_Z0_USED_FIELDS == COMPARATOR_Z0_USED_FIELDS == ("context",)
        and CANDIDATE_IGNORED_LEGAL_FIELDS == COMPARATOR_IGNORED_LEGAL_FIELDS == ("tau", "public_history_at_tau", "focal_execution_phase", "public_partner_phase", "legal_duration_mask", "behavior_version")
        and set(CANDIDATE_Z0_USED_FIELDS + CANDIDATE_IGNORED_LEGAL_FIELDS) == set(Z0_FULL_FIELDS)
        and used_is_strict_subset and branch_only_in_law
    )
    probability_table_registered = dict(probabilities) == {Context.F: Fraction(1, 4), Context.P: Fraction(3, 4)}
    selector_exact = candidate_choices == comparator_choices; value_exact = candidate_values == comparator_values
    terminal_gate = all((
        same_used_selector_information, probability_table_registered, law_frozen,
        tape_ordered_exact, tape_length_exact, tape_unique_exact,
        registered_selector_keys_exact, candidate_selector_domain_exact, comparator_selector_domain_exact,
        candidate_value_domain_exact, comparator_value_domain_exact,
        selector_nested, selector_equal_keys, selector_exact,
        value_nested, value_equal_keys, value_exact,
    ))
    return {
        "name": "REGISTERED_Z0_FINITE_COMPARATOR", "same_used_selector_information": same_used_selector_information,
        "z0_full_fields": list(Z0_FULL_FIELDS), "candidate_z0_used_fields": list(CANDIDATE_Z0_USED_FIELDS),
        "comparator_z0_used_fields": list(COMPARATOR_Z0_USED_FIELDS), "candidate_ignored_legal_fields": list(CANDIDATE_IGNORED_LEGAL_FIELDS),
        "comparator_ignored_legal_fields": list(COMPARATOR_IGNORED_LEGAL_FIELDS), "used_is_strict_subset_of_full": used_is_strict_subset,
        "branch_variables_marginalized_only": branch_only_in_law,
        "branch_law": {
            "fields": list(BRANCH_FIELDS), "branches_per_z0_action": len(law),
            "uniform_weight": _q(Fraction(1, 16)), "normalized_full_support": law_frozen,
        },
        "probabilities": {context.value: _q(probabilities[context]) for context in Context},
        "selector": {
            "runtime_tape_cells": len(SELECTOR_TAPE), "registered_tape_cells": len(REGISTERED_SELECTOR_TAPE),
            "runtime_tape_ordered_exact": tape_ordered_exact, "runtime_tape_length_exact": tape_length_exact,
            "runtime_tape_unique_exact": tape_unique_exact, "registered_entries": len(expected_selector_domain),
            "registered_domain_exact": registered_selector_keys_exact, "threshold": "LONG iff tape < p",
            "candidate_entries": len(candidate_choices), "comparator_entries": len(comparator_choices),
            "candidate_domain_exact": candidate_selector_domain_exact,
            "comparator_domain_exact": comparator_selector_domain_exact,
            "candidate_nested": selector_nested, "equal_keys": selector_equal_keys,
            "exact_reproduction": selector_exact,
        },
        "values": {
            "scope": "REGISTERED_16_BRANCH_SYNTHETIC_MIXTURE", "conditions_on_full_z0": False,
            "marginalized_fields": ["world", "close_mode", "cutoff", "owner_departure", "associated_tau"], "marginalized_owner_departure_tau_values": sorted({case.physical.tau for case in cases if case.valid and case.physical}),
            "key_fields": ["context", "action"], "candidate_entries": len(candidate_values),
            "comparator_entries": len(comparator_values),
            "candidate_domain_exact": candidate_value_domain_exact,
            "comparator_domain_exact": comparator_value_domain_exact,
            "candidate_nested": value_nested, "equal_keys": value_equal_keys,
            "exact_reproduction": value_exact,
            "candidate": {f"{context.value}|{action.value}": _q(candidate_values[(context, action)])
                          for context, action in product(Context, Action)},
            "comparator": {f"{context.value}|{action.value}": _q(comparator_values[(context, action)])
                           for context, action in product(Context, Action)},
        },
        "terminal_gate": terminal_gate,
    }


def _q(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def run_oracle() -> OracleAudit:
    validate_parameter_separation(PolicyParameter("theta"), FrozenBootstrap("Vbar", Fraction(1, 2)))
    cases = tuple(execute_case(spec) for spec in all_specs())
    for case in cases:
        verify_case(case)
    valid = tuple(case for case in cases if case.valid)
    stale = tuple(case for case in cases if not case.valid)
    comparator = registered_z0_conformance(valid)
    raw_scores = {(world, context): set() for world in World for context in Context}
    raw_settings: Counter[tuple[World, Context]] = Counter()
    raw_matches, w0_matches = [], []
    deltas = {(world, context): set() for world in World for context in Context}
    for key in sorted({_physical_key(case.spec) for case in valid}):
        pair = [case for case in valid if _physical_key(case.spec) == key]
        short = next(case for case in pair if case.spec.action is Action.SHORT)
        long = next(case for case in pair if case.spec.action is Action.LONG)
        context = short.spec.context
        p = _probability(context)
        mu = _occupancy(context)
        raw = mu * ((1 - p) * short.scores[0].score + p * long.scores[0].score)
        delta = long.target - short.target
        analytic = mu * p * (1 - p) * delta
        raw_matches.append(raw == analytic)
        raw_scores[(short.spec.world, context)].add(raw)
        raw_settings[(short.spec.world, context)] += 1
        deltas[(short.spec.world, context)].add(delta)
        if short.spec.world is World.ZERO: w0_matches.append(short.physical == long.physical)
    exact_deltas = {(world, context): next(iter(values))
                    for (world, context), values in deltas.items() if len(values) == 1}
    psi = exact_deltas[(World.POSITIVE, Context.P)] - exact_deltas[(World.POSITIVE, Context.F)]
    identity_fields = tuple(field.name for field in fields(DecisionIdentity))
    invariants = {
        "absolute_target_conserved_before_gradient": all(c.target == c.target_recomputed == absolute_target(c.physical) for c in valid),
        "explicit_nonzero_second_reward_kernel": all(c.physical.rewards[1] != 0 for c in valid),
        "frozen_stop_gradient_vbar": all(c.physical.vbar == Fraction(1, 2) and c.physical.primitive_tape is PRIMITIVE_TAPE and c.physical.partner_tape is PARTNER_TAPE for c in valid),
        "interrupt_over_natural": all(c.events[1].event is (Event.INTERRUPT_NATURAL if c.spec.close_mode is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL else Event.NATURAL) for c in valid),
        "terminal_over_horizon": all(c.events[2].event is (Event.TERMINAL_HORIZON if c.spec.cutoff is Cutoff.SIMULTANEOUS_TERMINAL_HORIZON else Event.HORIZON) for c in valid),
        "separate_policy_environment_clocks": all(e.policy_clock == c.spec.base_index and e.environment_clock in c.physical.timing for c in valid for e in c.events),
        "slot_excluded_from_identity": identity_fields == ("episode_id", "source_owner_epoch", "own_boundary_index", "behavior_version"),
        "owner_departure_identity_escrow": all(c.identity.source_owner_epoch == 7 and c.physical.final_owner_epoch == (8 if c.spec.owner_departure else 7) for c in valid),
        "one_score_release_tombstone_per_realization": all(len(c.scores) == len(c.releases) == len(c.tombstones) == 1 and len(c.events) == 4 for c in valid),
        "stale_has_no_score_or_release": all(c.final_state is State.INVALID and len(c.events) == len(c.tombstones) == 1 and not c.scores and not c.releases for c in stale),
        "raw_expected_score_matches_analytic": all(raw_matches),
        "frozen_deltas_exact": exact_deltas == EXPECTED_DELTAS and psi == 3 * GAMMA / 4,
        "w0_paired_physical_equality_zero_gradient": all(w0_matches) and exact_deltas[(World.ZERO, Context.F)] == exact_deltas[(World.ZERO, Context.P)] == 0,
        "registered_z0_selector_value_conformance": bool(comparator["terminal_gate"]),
    }
    if not all(invariants.values()):
        raise ValueError("aggregate invariant failure: " + ",".join(key for key, value in invariants.items() if not value))
    schemas = {cls.__name__: [field.name for field in fields(cls)]
               for cls in (DecisionIdentity, EventRecord, TombstoneRecord, ReleaseRecord)}
    report: dict[str, object] = {
        "candidate": "CAND-VSP-02@adversarial-revision-v8",
        "coverage": {
            "total": len(cases), "valid": len(valid), "stale": len(stale),
            "per_world_valid": 32, "per_world_stale": 32,
            "axes": ["world", "context", "action", "close", "cutoff", "owner_departure", "version"],
            "shape": [2, 2, 2, 2, 2, 2, 2],
        },
        "deltas": {"W+|F": _q(exact_deltas[(World.POSITIVE, Context.F)]),
                   "W+|P": _q(exact_deltas[(World.POSITIVE, Context.P)]),
                   "W0|F": _q(exact_deltas[(World.ZERO, Context.F)]),
                   "W0|P": _q(exact_deltas[(World.ZERO, Context.P)]), "psi": _q(psi)},
        "invariants": invariants,
        "timing_tensor": {
            "axes": ["world", "context", "action", "close", "cutoff", "owner_departure"],
            "shape": [2, 2, 2, 2, 2, 2], "entries": len(valid),
            "tau_values": sorted({case.physical.tau for case in valid if case.physical}),
            "frozen": invariants["frozen_stop_gradient_vbar"],
        },
        "comparator": comparator,
        "raw_expected_scores": {
            f"{world.value}|{context.value}": {
                "value": _q(next(iter(raw_scores[(world, context)]))), "settings": raw_settings[(world, context)]}
            for world in World for context in Context
            if len(raw_scores[(world, context)]) == 1
        },
        "schemas": schemas,
        "bookkeeping": {
            "scope": "PER_REALIZATION_RECORD_SHAPE_ONLY",
            "valid_record_counts": {"events": 4, "scores": 1, "releases": 1, "tombstones": 1},
            "stale_record_counts": {"events": 1, "scores": 0, "releases": 0, "tombstones": 1},
        },
        "terminal": "REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE",
        "disposition": "NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR",
    }
    return OracleAudit(cases, report)


def audit_json() -> str:
    return json.dumps(run_oracle().report, sort_keys=True, separators=(",", ":"), default=str)


if __name__ == "__main__":
    print(audit_json())
