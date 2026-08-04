from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
from itertools import product
from typing import Iterable


GAMMA, CURRENT_VERSION, HORIZON = Fraction(1, 2), 9, 2
PRIMITIVE_TAPE, PARTNER_TAPE = ("hold", "advance"), ("silent", "ack")


class State(str, Enum):
    VACANT = "VACANT"
    OPEN_ACTIVE = "OPEN_ACTIVE"
    OPEN_NATURAL = "OPEN_NATURAL"
    OPEN_INTERRUPTED = "OPEN_INTERRUPTED"
    TERMINAL_READY = "TERMINAL_READY"
    HORIZON_READY = "HORIZON_READY"
    RELEASED = "RELEASED"
    INVALID = "INVALID"


class Event(str, Enum):
    CLAIM = "CLAIM"
    NATURAL = "NATURAL"
    INTERRUPT_NATURAL = "INTERRUPT_NATURAL"
    HORIZON = "HORIZON"
    TERMINAL_HORIZON = "TERMINAL_HORIZON"
    RELEASE = "RELEASE"
    STALE_VERSION = "STALE_VERSION"
    ILLEGAL = "ILLEGAL"


class World(str, Enum):
    POSITIVE = "W+"
    ZERO = "W0"


class Context(str, Enum):
    F = "F"
    P = "P"


class Action(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


class CloseMode(str, Enum):
    NATURAL = "NATURAL"
    SIMULTANEOUS_INTERRUPT_NATURAL = "SIMULTANEOUS_INTERRUPT_NATURAL"


class Cutoff(str, Enum):
    HORIZON = "HORIZON"
    SIMULTANEOUS_TERMINAL_HORIZON = "SIMULTANEOUS_TERMINAL_HORIZON"


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
    if state is State.INVALID:
        return State.INVALID
    return _LEGAL_TRANSITIONS.get((state, event), State.INVALID)


def resolve_close(*, natural: bool, interrupt: bool) -> Event:
    if interrupt:
        return Event.INTERRUPT_NATURAL
    if natural:
        return Event.NATURAL
    raise ValueError("ambiguous close: neither natural nor interrupt")


def resolve_cutoff(*, horizon: bool, terminal: bool) -> Event:
    if terminal:
        return Event.TERMINAL_HORIZON
    if horizon:
        return Event.HORIZON
    raise ValueError("ambiguous cutoff: neither horizon nor terminal")


@dataclass(frozen=True)
class DecisionIdentity:
    episode_id: str
    source_owner_epoch: int
    own_boundary_index: int
    behavior_version: int


@dataclass(frozen=True)
class CaseSpec:
    world: World
    context: Context
    action: Action
    close_mode: CloseMode
    cutoff: Cutoff
    owner_departure: bool
    behavior_version: int
    base_index: int


@dataclass(frozen=True)
class PhysicalTrace:
    tau: int
    horizon: int
    terminal_time: int
    rewards: tuple[Fraction, ...]
    vbar: Fraction
    close_outcome: str
    cutoff_outcome: str
    final_owner_epoch: int
    primitive_tape: tuple[str, ...]
    partner_tape: tuple[str, ...]
    timing: tuple[int, int, int, int]


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    identity: DecisionIdentity
    slot_index: int
    event: Event
    before: State
    after: State
    policy_clock: int
    environment_clock: int


@dataclass(frozen=True)
class ScoreRecord:
    identity: DecisionIdentity
    target: Fraction
    score: Fraction
    action: Action


@dataclass(frozen=True)
class TombstoneRecord:
    identity: DecisionIdentity
    final_state: State
    target: Fraction | None
    reason: str


@dataclass(frozen=True)
class ReleaseRecord:
    identity: DecisionIdentity
    target: Fraction
    release_clock: int


@dataclass(frozen=True)
class VersionRecord:
    behavior_version: int
    record_count: int
    released_count: int
    invalid_count: int
    can_advance: bool


@dataclass(frozen=True)
class PolicyParameter:
    name: str


@dataclass(frozen=True)
class FrozenBootstrap:
    name: str
    value: Fraction
    trainable: bool = False


@dataclass(frozen=True)
class CaseResult:
    spec: CaseSpec
    identity: DecisionIdentity
    slot_index: int
    valid: bool
    final_state: State
    physical: PhysicalTrace | None
    target: Fraction | None
    target_recomputed: Fraction | None
    events: tuple[EventRecord, ...]
    scores: tuple[ScoreRecord, ...]
    tombstones: tuple[TombstoneRecord, ...]
    releases: tuple[ReleaseRecord, ...]


@dataclass(frozen=True)
class OracleAudit:
    cases: tuple[CaseResult, ...]
    report: dict[str, object]


def _probability(context: Context) -> Fraction:
    return Fraction(1, 4) if context is Context.F else Fraction(3, 4)


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


class EscrowRegistry:
    def __init__(self) -> None:
        self._slots: dict[DecisionIdentity, int] = {}
        self._released: set[DecisionIdentity] = set()

    def claim(self, identity: DecisionIdentity, slot_index: int) -> None:
        if identity in self._slots:
            raise ValueError("decision identity already claimed; slot cannot alias")
        self._slots[identity] = slot_index

    def release(self, identity: DecisionIdentity) -> None:
        if identity not in self._slots or identity in self._released:
            raise ValueError("missing or duplicate release")
        self._released.add(identity)


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


def _predecision_key(spec: CaseSpec) -> tuple[str, str, str, str, bool]:
    return (
        spec.world.value, spec.context.value, spec.close_mode.value,
        spec.cutoff.value, spec.owner_departure,
    )


def _candidate_mapping(cases: Iterable[CaseResult]) -> dict[tuple[object, ...], Fraction]:
    return {
        _predecision_key(case.spec) + (case.spec.action.value,): case.target
        for case in cases if case.valid and case.target is not None
    }


def horizon_flush_tabular_duration_null() -> dict[tuple[object, ...], Fraction]:
    mapping: dict[tuple[object, ...], Fraction] = {}
    for world, context, close, cutoff, departure, action in product(
        World, Context, CloseMode, Cutoff, (False, True), Action
    ):
        value = Fraction(1 if context is Context.F else 2)
        value += Fraction(1, 16) if close is CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL else 0
        value += Fraction(1, 8) if cutoff is Cutoff.SIMULTANEOUS_TERMINAL_HORIZON else 0
        value += Fraction(1, 32) if departure else 0
        if world is World.POSITIVE and action is Action.LONG:
            value += -GAMMA / 2 if context is Context.F else GAMMA / 4
        key = (world.value, context.value, close.value, cutoff.value, departure, action.value)
        mapping[key] = value
    return mapping


def _version_record(cases: tuple[CaseResult, ...], version: int) -> VersionRecord:
    selected = tuple(case for case in cases if case.spec.behavior_version == version)
    released = sum(len(case.releases) for case in selected)
    invalid = sum(case.final_state is State.INVALID for case in selected)
    can_advance = bool(selected) and released == len(selected) and invalid == 0
    return VersionRecord(version, len(selected), released, invalid, can_advance)


def _q(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def run_oracle() -> OracleAudit:
    validate_parameter_separation(PolicyParameter("theta"), FrozenBootstrap("Vbar", Fraction(1, 2)))
    cases = tuple(execute_case(spec) for spec in all_specs())
    for case in cases:
        verify_case(case)
    valid = tuple(case for case in cases if case.valid)
    stale = tuple(case for case in cases if not case.valid)
    candidate = _candidate_mapping(valid)
    null = horizon_flush_tabular_duration_null()
    raw_scores: dict[tuple[World, Context], set[Fraction]] = {
        (world, context): set() for world in World for context in Context
    }
    raw_settings: Counter[tuple[World, Context]] = Counter()
    raw_matches, w0_matches = [], []
    deltas: dict[tuple[World, Context], set[Fraction]] = {
        (world, context): set() for world in World for context in Context
    }
    for key in sorted({_predecision_key(case.spec) for case in valid}):
        pair = [case for case in valid if _predecision_key(case.spec) == key]
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
        if short.spec.world is World.ZERO:
            w0_matches.append(short.physical == long.physical)
    exact_deltas = {
        (world, context): next(iter(values))
        for (world, context), values in deltas.items() if len(values) == 1
    }
    psi = exact_deltas[(World.POSITIVE, Context.P)] - exact_deltas[(World.POSITIVE, Context.F)]
    current = _version_record(cases, CURRENT_VERSION)
    stale_version = _version_record(cases, CURRENT_VERSION - 1)
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
        "valid_score_release_tombstone_exactly_once": all(len(c.scores) == len(c.releases) == len(c.tombstones) == 1 and len(c.events) == 4 for c in valid),
        "stale_has_no_score_or_release": all(c.final_state is State.INVALID and len(c.events) == len(c.tombstones) == 1 and not c.scores and not c.releases for c in stale),
        "raw_expected_score_matches_analytic": all(raw_matches),
        "frozen_deltas_exact": exact_deltas == EXPECTED_DELTAS and psi == 3 * GAMMA / 4,
        "w0_paired_physical_equality_zero_gradient": all(w0_matches) and exact_deltas[(World.ZERO, Context.F)] == exact_deltas[(World.ZERO, Context.P)] == 0,
        "tabular_null_exact_reproduction": candidate == null and set(candidate).issubset(null),
    }
    if not all(invariants.values()):
        raise ValueError("aggregate invariant failure: " + ",".join(key for key, value in invariants.items() if not value))
    schemas = {
        cls.__name__: [field.name for field in fields(cls)]
        for cls in (DecisionIdentity, EventRecord, TombstoneRecord, ReleaseRecord, VersionRecord)
    }
    report: dict[str, object] = {
        "candidate": "CAND-VSP-02@adversarial-revision-v8",
        "coverage": {
            "total": len(cases), "valid": len(valid), "stale": len(stale),
            "per_world_valid": 32, "per_world_stale": 32,
            "axes": ["world", "context", "action", "close", "cutoff", "owner_departure", "version"],
            "shape": [2, 2, 2, 2, 2, 2, 2],
        },
        "deltas": {
            "W+|F": _q(exact_deltas[(World.POSITIVE, Context.F)]),
            "W+|P": _q(exact_deltas[(World.POSITIVE, Context.P)]),
            "W0|F": _q(exact_deltas[(World.ZERO, Context.F)]),
            "W0|P": _q(exact_deltas[(World.ZERO, Context.P)]),
            "psi": _q(psi),
        },
        "invariants": invariants,
        "timing_tensor": {
            "axes": ["world", "context", "action", "close", "cutoff", "owner_departure"],
            "shape": [2, 2, 2, 2, 2, 2], "entries": len(valid),
            "tau_values": sorted({case.physical.tau for case in valid if case.physical}),
            "frozen": invariants["frozen_stop_gradient_vbar"],
        },
        "null": {
            "name": "HORIZON_FLUSH_TABULAR_DURATION_NULL",
            "same_information": True, "full_horizon": True,
            "finite_predecision_keys": len(null) // 2,
            "action_entries": len(null), "candidate_entries": len(candidate),
            "candidate_nested": set(candidate).issubset(null),
            "exact_reproduction": candidate == null,
        },
        "raw_expected_scores": {
            f"{world.value}|{context.value}": {
                "value": _q(next(iter(raw_scores[(world, context)]))),
                "settings": raw_settings[(world, context)],
            }
            for world in World for context in Context
            if len(raw_scores[(world, context)]) == 1
        },
        "schemas": schemas,
        "versions": {
            "current": current.__dict__, "stale": stale_version.__dict__,
        },
        "terminal": "ADAPTIVE_DURATION_RETIRED",
        "disposition": "BOOKKEEPING_TRANSPORT_CONFORMANCE_ONLY",
    }
    return OracleAudit(cases, report)


def audit_json() -> str:
    return json.dumps(run_oracle().report, sort_keys=True, separators=(",", ":"), default=str)


if __name__ == "__main__":
    print(audit_json())
