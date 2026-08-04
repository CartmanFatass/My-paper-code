"""Deterministic Sequence 11 finite census and independent handoff model check."""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from typing import Callable, Iterable, Mapping


ASSIGNMENT_ID = "vsp05_sequence_11_semantic_veto_20260803"
CANDIDATE = "CAND-VSP-05@adversarial-revision-v7"
TREATMENT = "VSP-05-FINITE-CENSUS-SEMANTIC-VETO-D0"
EVENT_CLASS = "E_SC1_SINGLE_OWNER_MONOTONE_SERVICE_COMPLETION"
RAW_OUTPUT_BINDING = "vsp05.semantic_veto_census.sequence11.v4"
FIELDS = ("e_local", "r_relation", "p_public", "b_integrity", "b_contradiction", "b_validity")
POSITIVE_X = (True, True, True, True, False, True)
FOLDS = tuple(f"lineage_{name}_full" for name in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"))
FORBIDDEN_FAMILIES = ("time", "frame", "age", "velocity", "history", "occupancy", "raw_ids", "reward", "future_state", "recurrent_features", "shared_features", "normalization", "teacher_tensors")
_PROXIES = ("elapsed_steps_proxy", "frame_index_proxy", "object_age_proxy", "speed_norm_proxy", "temporal_cache_proxy", "occupancy_ratio_proxy", "agent_id_proxy", "return_signal_proxy", "next_state_proxy", "hidden_state_proxy", "partner_embedding_proxy", "normalized_tuple_proxy", "teacher_logits_proxy")
FORBIDDEN_PROXIES = dict(zip(FORBIDDEN_FAMILIES, _PROXIES))
X_STAR = tuple(product((False, True), repeat=6))
RAW_X_TAPE = tuple(product((False, True), repeat=6))
Q_KAPPA_TAPE = ((0, 0),) * 61 + ((0, 1),) + ((1, 1),) * 2
X_INDEX = {x: index for index, x in enumerate(X_STAR)}


@dataclass(frozen=True)
class EventSpec:
    event_class: str; kappa: str; owner: str; target: str


@dataclass(frozen=True)
class Cell:
    a: Fraction; s: Fraction; d: Fraction; r: int; o: int

    @property
    def key(self) -> str:
        return f"A={self.a}|S={self.s}|D={self.d}|R={self.r}|O={self.o}"


@dataclass(frozen=True)
class RawSources:
    e_local: bool; r_relation: bool; p_public: bool
    b_integrity: bool; b_contradiction: bool; b_validity: bool

    def as_x(self) -> tuple[bool, ...]:
        return tuple(getattr(self, name) for name in FIELDS)


@dataclass(frozen=True)
class PhysicalRecord:
    physical_time: Fraction; physical_index: int; q_kappa_state: tuple[int, int]
    transaction_identity: str; owner_epoch_valid: bool; cell: Cell; fold: str
    opportunity_identity: str; raw_sources: RawSources


@dataclass(frozen=True)
class Tape:
    cell_key: str; fold: str; records: tuple[PhysicalRecord, ...]
    xs: tuple[tuple[bool, ...], ...]; ys: tuple[int, ...]


@dataclass(frozen=True)
class Registry:
    event_registry: tuple[EventSpec, ...]; lineage_registry: tuple[str, ...]
    grid: tuple[Cell, ...]; schema: tuple[str, ...]
    x_star: tuple[tuple[bool, ...], ...]; records: tuple[PhysicalRecord, ...]
    raw_x_tape: tuple[tuple[bool, ...], ...]; q_kappa_tape: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class FrozenLookupArtifact:
    table: tuple[int, ...]
    dependencies: tuple[str, ...] = ("tuple",)

    def __post_init__(self) -> None:
        _require_dependencies(self.dependencies, ("tuple",), "artifact")
        if len(self.table) != len(X_STAR) or any(value not in (0, 1) for value in self.table):
            raise ValueError("artifact must be a frozen binary row for every registered X")


def _validate_registered_tapes(raw_x_tape: Iterable[tuple[bool, ...]]) -> tuple[tuple[bool, ...], ...]:
    raw, q = tuple(raw_x_tape), Q_KAPPA_TAPE
    if len(raw) != 64 or len(set(raw)) != 64 or set(raw) != set(X_STAR): raise ValueError("raw-X tape must be one frozen full-support permutation")
    if len(q) != 64 or sum(state == (0, 1) for state in q) != 1 or any(state not in ((0, 0), (0, 1), (1, 1)) for state in q) or any(left[1] != right[0] for left, right in zip(q, q[1:])): raise ValueError("Q_kappa tape must contain one connected monotone transition")
    return raw


def physical_records(grid: tuple[Cell, ...], event: EventSpec, raw_x_tape: Iterable[tuple[bool, ...]]) -> tuple[PhysicalRecord, ...]:
    raw_tape = _validate_registered_tapes(raw_x_tape); records = []
    for cell in grid:
        for fold in FOLDS:
            for index, (raw_x, q_state) in enumerate(zip(raw_tape, Q_KAPPA_TAPE)):
                identity = f"{cell.key}|{fold}|physical-opportunity-{index:02d}"
                records.append(PhysicalRecord(Fraction(index, 64), index, q_state, event.kappa, True, cell, fold, identity, RawSources(*raw_x)))
    return tuple(records)


def build_registry() -> Registry:
    dt = Fraction(1, 64)
    grid = tuple(Cell(a, s, d, r, o) for a, s, d, r, o in product((0 * dt, 8 * dt, 32 * dt), (Fraction(1, 2), Fraction(1), Fraction(2)), (0 * dt, 2 * dt, 8 * dt), (1, 2, 4), (0, 2, 4)))
    event = EventSpec(EVENT_CLASS, "kappa_focal_001", "owner_focal", "target_focal")
    records = list(physical_records(grid, event, RAW_X_TAPE))
    reference = records[0]
    records.extend((replace(reference, transaction_identity="other_kappa", opportunity_identity="audit-transaction-mismatch"), replace(reference, owner_epoch_valid=False, opportunity_identity="audit-invalid-owner-epoch")))
    return Registry((event,), FOLDS, grid, FIELDS, X_STAR, tuple(records), RAW_X_TAPE, Q_KAPPA_TAPE)


def _require_dependencies(actual: Iterable[str], expected: tuple[str, ...], surface: str) -> None:
    actual_tuple = tuple(actual)
    forbidden = set(FORBIDDEN_FAMILIES) | set(FORBIDDEN_PROXIES.values())
    if actual_tuple != expected or forbidden.intersection(actual_tuple):
        raise ValueError(f"{surface} dependencies must be exactly {expected}")


def raw_sources_from_input(values: Mapping[str, object]) -> RawSources:
    if tuple(values) != FIELDS or any(type(values[name]) is not bool for name in FIELDS): raise ValueError("raw record input must contain only the six registered Boolean sources")
    return RawSources(*(values[name] for name in FIELDS))


def extract_x(record: PhysicalRecord, *, dependencies: Iterable[str] = FIELDS) -> tuple[bool, ...]:
    _require_dependencies(dependencies, FIELDS, "extractor")
    if not isinstance(record, PhysicalRecord) or not isinstance(record.raw_sources, RawSources):
        raise TypeError("extractor accepts only a registered physical record")
    x = record.raw_sources.as_x()
    if any(type(value) is not bool for value in x):
        raise ValueError("extracted X must contain exactly six Booleans")
    return x


def physical_y(record: PhysicalRecord) -> int:
    return int(record.q_kappa_state[1] == 1 and record.transaction_identity == "kappa_focal_001" and record.owner_epoch_valid)


def _validate_q_binding(registry: Registry, records: Iterable[PhysicalRecord]) -> None:
    if registry.q_kappa_tape is not Q_KAPPA_TAPE: raise ValueError("registry Q_kappa tape must be the canonical Q_KAPPA_TAPE object")
    for record in records:
        if type(index := record.physical_index) is not int or not 0 <= index < len(Q_KAPPA_TAPE) or record.q_kappa_state != Q_KAPPA_TAPE[index]: raise ValueError("physical record Q_kappa state is not bound to canonical tape position")


def x_key(x: tuple[bool, ...]) -> str: return "".join("1" if bit else "0" for bit in x)


def admit_records(registry: Registry, records: Iterable[PhysicalRecord]) -> tuple[tuple[PhysicalRecord, ...], dict[str, int]]:
    event = registry.event_registry[0]
    allowed_cells = set(registry.grid)
    allowed_folds = set(registry.lineage_registry)
    admitted = []
    excluded = Counter()
    for record in records:
        if record.transaction_identity != event.kappa:
            excluded["transaction_mismatch"] += 1
        elif not record.owner_epoch_valid:
            excluded["invalid_owner_epoch"] += 1
        elif record.cell not in allowed_cells or record.fold not in allowed_folds:
            excluded["unregistered_cell_or_fold"] += 1
        else:
            admitted.append(record)
    return tuple(admitted), dict(sorted(excluded.items()))


def deduplicate_records(records: Iterable[PhysicalRecord]) -> tuple[tuple[PhysicalRecord, ...], int]:
    ordered = sorted(records, key=lambda item: (item.cell.key, item.fold, item.physical_time, item.physical_index, item.opportunity_identity))
    unique = {}
    for record in ordered:
        unique.setdefault(record.opportunity_identity, record)
    return tuple(unique.values()), len(ordered) - len(unique)


def materialize_tapes(registry: Registry, records: Iterable[PhysicalRecord]) -> tuple[Tape, ...]:
    records = tuple(records); _validate_q_binding(registry, records)
    groups: dict[tuple[str, str], list[PhysicalRecord]] = {}
    for record in records:
        groups.setdefault((record.cell.key, record.fold), []).append(record)
    tapes = []
    for (cell_key, fold), group in sorted(groups.items()):
        ordered = tuple(sorted(group, key=lambda item: (item.physical_time, item.physical_index)))
        xs = tuple(extract_x(item) for item in ordered)
        tapes.append(Tape(cell_key, fold, ordered, xs, tuple(physical_y(item) for item in ordered)))
    return tuple(tapes)


def _signature(tape: Tape) -> tuple[tuple[str, ...], str]: return tuple(x_key(x) for x in tape.xs), "".join(map(str, tape.ys))


def census(registry: Registry) -> dict[str, object]:
    admitted, exclusions = admit_records(registry, registry.records)
    unique, duplicate_count = deduplicate_records(admitted)
    tapes = materialize_tapes(registry, unique)
    counts = {x: [0, 0] for x in registry.x_star}
    fold_counts = {fold: Counter() for fold in registry.lineage_registry}
    support_exits = []
    for tape in tapes:
        for x, y in zip(tape.xs, tape.ys):
            if x not in counts:
                support_exits.append((tape.cell_key, tape.fold, x))
                continue
            counts[x][y] += 1
            fold_counts[tape.fold][x] += 1
    signatures = Counter(_signature(tape) for tape in tapes)
    contradictions = [x_key(x) for x, values in counts.items() if all(values)]
    fold_summary = {}
    for fold, counter in fold_counts.items():
        fold_summary[fold] = {"count_per_tuple": min(counter.values()), "full_support": set(counter) == set(registry.x_star) and len(set(counter.values())) == 1, "opportunities": sum(counter.values()), "tuple_count": len(counter)}
    return {
        "contradictions": contradictions,
        "admission": {"admitted": len(admitted), "exclusions_before_y": exclusions},
        "deduplication": {"duplicate_identity_count": duplicate_count, "unique_records": len(unique)},
        "folds": fold_summary,
        "opportunities": sum(sum(values) for values in counts.values()),
        "positive_labels": sum(values[1] for values in counts.values()),
        "support_exits": [str(item) for item in support_exits],
        "tape_signatures": [{"multiplicity": count, "x_keys": list(signature[0]), "y": signature[1]} for signature, count in sorted(signatures.items())],
        "unique_tape_signature_count": len(signatures),
        "x_by_y": {x_key(x): {"y0": values[0], "y1": values[1]} for x, values in counts.items()},
        "_counts": counts,
        "_tapes": tapes,
    }


def saturated_lookup() -> dict[tuple[bool, ...], int]:
    return {x: int(x == POSITIVE_X) for x in X_STAR}


def derive_pointwise_rule(counts: Mapping[tuple[bool, ...], tuple[int, int] | list[int]]) -> dict[tuple[bool, ...], int]:
    rule = {}
    for x in X_STAR:
        y0, y1 = counts[x]
        risk_if_zero = y1
        risk_if_one = y0
        rule[x] = int(risk_if_one < risk_if_zero)
    return rule


def freeze_lookup(rule: Mapping[tuple[bool, ...], int], dependencies: Iterable[str] = ("tuple",)) -> FrozenLookupArtifact:
    return FrozenLookupArtifact(tuple(rule[x] for x in X_STAR), tuple(dependencies))


def runtime_decision(x: tuple[bool, ...], artifact: FrozenLookupArtifact, *, dependencies: Iterable[str] = ("tuple", "artifact")) -> int:
    _require_dependencies(dependencies, ("tuple", "artifact"), "runtime")
    if x not in X_STAR:
        raise ValueError("runtime X is outside the frozen 64-row artifact")
    return artifact.table[X_INDEX[x]]


def sequential_fact(tape: Tape, rule: Mapping[tuple[bool, ...], int]) -> dict[str, object]:
    artifact = freeze_lookup(rule)
    decisions = tuple(runtime_decision(extract_x(record), artifact) for record in tape.records)
    surviving = 1
    false_alias = captures = missed = delay = 0
    first_index = first_label = first_positive = None
    for index, (action, label) in enumerate(zip(decisions, tape.ys)):
        if surviving and label and first_positive is None:
            first_positive = index
        false_alias += surviving * action * (1 - label)
        captures += surviving * action * label
        missed += surviving * (1 - action) * label
        if surviving and action and label:
            delay += index - (first_positive if first_positive is not None else index)
        if surviving and action:
            first_index, first_label = index, label
        surviving *= 1 - action
    return {
        "action_decisions": "".join(map(str, decisions)),
        "action_count": sum(rule.values()),
        "capture_delay": delay,
        "first_latch_index_zero_based": first_index,
        "first_latch_label": first_label,
        "first_latch_false_alias": false_alias,
        "missed_positives": missed,
        "positive_captures": captures,
    }


def derive_best_rule(tapes: tuple[Tape, ...]) -> tuple[dict[tuple[bool, ...], int], dict[str, object]]:
    signatures = {_signature(tape) for tape in tapes}
    if len(signatures) != 1:
        raise ValueError("registered analytic derivation requires the disclosed single physical tape signature")
    tape = tapes[0]
    if len(tape.xs) != len(set(tape.xs)) or set(tape.xs) != set(X_STAR):
        raise ValueError("registered analytic derivation requires unique full X support")
    positive_positions = [index for index, y in enumerate(tape.ys) if y]
    selected = tape.xs[positive_positions[0]] if positive_positions else None
    rule = {x: int(x == selected) for x in X_STAR}
    facts = sequential_fact(tape, rule)
    objective = {"constraints": ["binary_tuple_only", "one_shared_rule", "first_latch_absorbing", "single_unique_full_support_tape"], "derivation": "analytic earliest physical positive; all other actions deleted by final action-count tie-break", "lexicographic_order": ["false_alias", "missed_positive", "capture_delay", "action_count"], "selected_score": [facts["first_latch_false_alias"], facts["missed_positives"], facts["capture_delay"], facts["action_count"]]}
    return rule, objective


def registered_rules(tapes: tuple[Tape, ...]) -> tuple[dict[str, dict[tuple[bool, ...], int]], dict[str, object]]:
    best, objective = derive_best_rule(tapes)
    return {
        "NO_VETO": {x: 1 for x in X_STAR},
        "ALWAYS_VETO": {x: 0 for x in X_STAR},
        "SATURATED_ALLOWLIST_LOOKUP": saturated_lookup(),
        "BEST_DETERMINISTIC_TUPLE_ONLY_RULE": best,
    }, objective


def rule_summary(tapes: tuple[Tape, ...], rules: Mapping[str, Mapping[tuple[bool, ...], int]]) -> dict[str, object]:
    coverage = Counter(tape.cell_key for tape in tapes)
    summaries = {}
    for name, rule in rules.items():
        variants = Counter(json.dumps(sequential_fact(tape, rule), sort_keys=True, separators=(",", ":")) for tape in tapes)
        summaries[name] = {
            "unique_fact_variants": len(variants),
            "variants": [{"cell_fold_count": count, "facts": json.loads(facts)} for facts, count in sorted(variants.items())],
        }
    return {
        "cell_fold_coverage_counts": sorted(set(coverage.values())),
        "covered_cell_count": len(coverage),
        "rules": summaries,
        "tape_count": len(tapes),
    }


def clone_report(tape: Tape, rules: Mapping[str, Mapping[tuple[bool, ...], int]]) -> dict[str, object]:
    clones = tuple(product((Fraction(0), Fraction(1, 8), Fraction(1, 2)), (0, 2, 4), (1, 2, 4)))
    drifts = []
    comparisons = 0
    artifacts = {name: freeze_lookup(rule) for name, rule in rules.items()}
    for record in tape.records:
        for age, occupancy, frame_refinement in clones:
            clone = replace(record, cell=replace(record.cell, a=age, o=occupancy, r=frame_refinement), physical_time=Fraction(record.physical_index, 64 * frame_refinement))
            clone_x = extract_x(clone)
            for name, artifact in artifacts.items():
                comparisons += 1
                if clone_x != extract_x(record) or runtime_decision(clone_x, artifact) != runtime_decision(extract_x(record), artifact):
                    drifts.append((x_key(extract_x(record)), str(age), occupancy, frame_refinement, name))
    (selected_x,) = tuple(x for x, value in rules["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"].items() if value)
    positive = next(record for record in tape.records if extract_x(record) == selected_x)
    mutated = replace(positive, raw_sources=replace(positive.raw_sources, e_local=False))
    artifact = artifacts["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"]
    before_x, after_x = extract_x(positive), extract_x(mutated)
    before, after = runtime_decision(before_x, artifact), runtime_decision(after_x, artifact)
    return {
        "registered_clone_cases": len(clones),
        "physical_record_clones": len(tape.records) * len(clones),
        "comparisons": comparisons,
        "decision_drifts": drifts,
        "negative_allowlisted_source_mutation": {"detected": before_x != after_x and before != after, "source": "e_local", "x_before": x_key(before_x), "x_after": x_key(after_x), "decision_before": before, "decision_after": after},
    }


def _raises(call: Callable[[], object]) -> bool:
    try:
        call()
    except (TypeError, ValueError):
        return True
    return False


def firewall_report(record: PhysicalRecord, artifact: FrozenLookupArtifact) -> dict[str, object]:
    base = dict(zip(FIELDS, extract_x(record)))
    rejections = []
    forbidden = FORBIDDEN_FAMILIES + tuple(FORBIDDEN_PROXIES.values())
    for source in forbidden:
        injected = dict(base)
        injected[source] = False
        probes = {
            "record_input": lambda values=injected: raw_sources_from_input(values),
            "extractor_input": lambda name=source: extract_x(record, dependencies=FIELDS + (name,)),
            "artifact_dependencies": lambda name=source: freeze_lookup(saturated_lookup(), ("tuple", name)),
            "runtime_dependencies": lambda name=source: runtime_decision(extract_x(record), artifact, dependencies=("tuple", "artifact", name)),
        }
        for surface, probe in probes.items():
            if _raises(probe):
                rejections.append((source, surface))
    expected = len(forbidden) * 4
    return {"actual_path": "physical_record->X_extractor->frozen_lookup_artifact->tuple_only_runtime_decision", "clean": len(rejections) == expected, "injections_rejected": len(rejections), "injections_required": expected}


@dataclass(frozen=True)
class HandoffSpec:
    kappa: str = "kappa_focal_001"
    rho: str = "rho_receiver_001"
    epoch_sender: int = 7
    epoch_receiver: int = 11
    sender: str = "owner_focal"
    receiver: str = "receiver_focal"


@dataclass(frozen=True)
class SafeCertificate:
    sender: str
    receiver: str
    kappa: str
    observed_at_precommit: bool


@dataclass(frozen=True)
class ReadyAck:
    kappa: str
    rho: str
    epoch_sender: int
    epoch_receiver: int


@dataclass(frozen=True)
class HandoffState:
    semantic_latched: bool = False
    safe: bool = False
    ack_valid: bool = False
    revoked: bool = False
    public_commit: bool = False
    commit_count: int = 0
    sender_terminated: bool = False
    receiver_active: bool = False


HANDOFF_ACTIONS = (
    "SEMANTIC_LATCH",
    "SAFE_ON",
    "SAFE_OFF",
    "ACK_VALID",
    "ACK_INVALID",
    "ACK_MISMATCH",
    "REVOKE",
    "HANDOFF_COMMIT",
    "SENDER_TERMINATE",
    "RECEIVER_ACTIVATE",
)


def ack_matches(spec: HandoffSpec, ack: ReadyAck) -> bool:
    return ack == ReadyAck(spec.kappa, spec.rho, spec.epoch_sender, spec.epoch_receiver)


def safe_matches(spec: HandoffSpec, certificate: SafeCertificate) -> bool:
    expected = SafeCertificate(spec.sender, spec.receiver, spec.kappa, True)
    return certificate == expected


def observe_safe(state: HandoffState, spec: HandoffSpec, certificate: SafeCertificate) -> HandoffState:
    return replace(state, safe=safe_matches(spec, certificate))


def observe_ack(state: HandoffState, spec: HandoffSpec, ack: ReadyAck) -> HandoffState:
    return replace(state, ack_valid=ack_matches(spec, ack))


def handoff_transition(state: HandoffState, action: str, spec: HandoffSpec) -> HandoffState:
    if action == "SEMANTIC_LATCH":
        return replace(state, semantic_latched=True)
    if action == "SAFE_ON":
        return observe_safe(state, spec, SafeCertificate(spec.sender, spec.receiver, spec.kappa, True))
    if action == "SAFE_OFF":
        return observe_safe(state, spec, SafeCertificate(spec.sender, spec.receiver, spec.kappa, False))
    if action == "ACK_VALID":
        return observe_ack(state, spec, ReadyAck(spec.kappa, spec.rho, spec.epoch_sender, spec.epoch_receiver))
    if action == "ACK_INVALID":
        return observe_ack(state, spec, ReadyAck(spec.kappa, spec.rho, spec.epoch_sender, spec.epoch_receiver + 1))
    if action == "ACK_MISMATCH":
        return observe_ack(state, spec, ReadyAck("other_kappa", spec.rho, spec.epoch_sender, spec.epoch_receiver))
    if action == "REVOKE":
        return replace(state, revoked=True)
    if action == "HANDOFF_COMMIT":
        gates = state.semantic_latched and state.safe and state.ack_valid and not state.revoked
        if gates and not state.public_commit:
            return replace(state, public_commit=True, commit_count=state.commit_count + 1)
        return state
    if action == "SENDER_TERMINATE":
        return replace(state, sender_terminated=True) if state.public_commit else state
    if action == "RECEIVER_ACTIVATE":
        return replace(state, receiver_active=True) if state.public_commit else state
    raise ValueError(f"unknown handoff action: {action}")


def valid_handoff_trace(spec: HandoffSpec) -> tuple[HandoffState, tuple[str, ...]]:
    actions = (
        "SEMANTIC_LATCH",
        "SAFE_ON",
        "ACK_VALID",
        "HANDOFF_COMMIT",
        "SENDER_TERMINATE",
        "RECEIVER_ACTIVATE",
    )
    state = HandoffState()
    for action in actions:
        state = handoff_transition(state, action, spec)
    return state, actions


def handoff_model_check() -> dict[str, object]:
    spec = HandoffSpec()
    start = HandoffState()
    queue = deque([start])
    states = {start}
    transitions = []
    while queue:
        state = queue.popleft()
        for action in HANDOFF_ACTIONS:
            successor = handoff_transition(state, action, spec)
            transitions.append((state, action, successor))
            if successor not in states:
                states.add(successor)
                queue.append(successor)
    violations = []
    for state in states:
        if state.commit_count > 1:
            violations.append("commit_count_gt_one")
        if state.sender_terminated and not state.public_commit:
            violations.append("termination_without_public_commit")
        if state.receiver_active and not state.public_commit:
            violations.append("activation_without_public_commit")
        if state.public_commit != (state.commit_count == 1):
            violations.append("publication_count_not_atomic")
    for before, action, after in transitions:
        if action == "HANDOFF_COMMIT" and after.commit_count != before.commit_count:
            if not after.public_commit or after.commit_count != before.commit_count + 1:
                violations.append("non_atomic_commit_transition")
    valid_final, actions = valid_handoff_trace(spec)
    negative = _handoff_negative_checks(spec)
    terminal = not violations and all(negative.values()) and (
        valid_final.public_commit and valid_final.sender_terminated and valid_final.receiver_active
    )
    return {
        "actions": len(HANDOFF_ACTIONS),
        "exactly_once_handoff_safety": terminal,
        "invariant_violations": sorted(set(violations)),
        "negative_gate_checks": negative,
        "reachable_states": len(states),
        "transitions_checked": len(transitions),
        "valid_trace": {"actions": list(actions), "final": _state_dict(valid_final)},
    }


def _handoff_negative_checks(spec: HandoffSpec) -> dict[str, bool]:
    def apply(actions: Iterable[str]) -> HandoffState:
        state = HandoffState()
        for action in actions:
            state = handoff_transition(state, action, spec)
        return state

    valid_prefix = ("SEMANTIC_LATCH", "SAFE_ON", "ACK_VALID")
    committed = apply(valid_prefix + ("HANDOFF_COMMIT",))
    duplicate = handoff_transition(committed, "HANDOFF_COMMIT", spec)
    return {
        "absent_latch": not apply(("SAFE_ON", "ACK_VALID", "HANDOFF_COMMIT")).public_commit,
        "activation_before_commit": not apply(("RECEIVER_ACTIVATE",)).receiver_active,
        "duplicate_commit_idempotent": duplicate == committed and duplicate.commit_count == 1,
        "invalid_ack": not apply(("SEMANTIC_LATCH", "SAFE_ON", "ACK_INVALID", "HANDOFF_COMMIT")).public_commit,
        "mismatched_ack": not apply(("SEMANTIC_LATCH", "SAFE_ON", "ACK_MISMATCH", "HANDOFF_COMMIT")).public_commit,
        "missing_ack": not apply(("SEMANTIC_LATCH", "SAFE_ON", "HANDOFF_COMMIT")).public_commit,
        "revoked": not apply(valid_prefix + ("REVOKE", "HANDOFF_COMMIT")).public_commit,
        "semantic_latch_alone": not apply(("SEMANTIC_LATCH", "HANDOFF_COMMIT")).public_commit,
        "termination_before_commit": not apply(("SENDER_TERMINATE",)).sender_terminated,
        "unsafe": not apply(("SEMANTIC_LATCH", "ACK_VALID", "HANDOFF_COMMIT")).public_commit,
    }


def _state_dict(state: HandoffState) -> dict[str, object]:
    return {name: getattr(state, name) for name in state.__dataclass_fields__}


def build_report() -> dict[str, object]:
    registry = build_registry()
    count_report = census(registry)
    counts = count_report.pop("_counts")
    tapes = count_report.pop("_tapes")
    rules, objective = registered_rules(tapes)
    lookup = rules["SATURATED_ALLOWLIST_LOOKUP"]
    best = rules["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"]
    pointwise = derive_pointwise_rule(counts)
    firewall = firewall_report(tapes[0].records[0], freeze_lookup(best))
    clones = clone_report(tapes[0], rules)
    handoff = handoff_model_check()
    best_facts = sequential_fact(tapes[0], best)
    expected_ys = tuple(state[1] for state in registry.q_kappa_tape); label_binding_ok = all(tape.ys == expected_ys for tape in tapes)
    coverage_ok = len(tapes) == len(registry.grid) * len(FOLDS) and all(facts["full_support"] for facts in count_report["folds"].values()); admission_ok = count_report["admission"] == {"admitted": 93_312, "exclusions_before_y": {"invalid_owner_epoch": 1, "transaction_mismatch": 1}}
    dedup_ok = count_report["deduplication"]["duplicate_identity_count"] == 0
    sequential_ok = [best_facts[name] for name in ("first_latch_false_alias", "missed_positives", "capture_delay", "action_count")] == [0, 0, 0, 1] and best_facts["positive_captures"] == 1
    physical_terminal = all((not count_report["contradictions"], not count_report["support_exits"], coverage_ok, admission_ok, dedup_ok, label_binding_ok, count_report["positive_labels"] == 4_374, count_report["unique_tape_signature_count"] == 1, firewall["clean"], not clones["decision_drifts"], clones["negative_allowlisted_source_mutation"]["detected"], sequential_ok))
    q_transition = next(index for index, state in enumerate(registry.q_kappa_tape) if state == (0, 1))
    return {
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "census": count_report,
        "clone_invariance": clones,
        "conclusion": {"exactly_once_handoff_safety_holds_in_fixed_synthetic_instance": handoff["exactly_once_handoff_safety"], "finite_support_lookup_conformance_holds_in_fixed_synthetic_instance": physical_terminal},
        "event": _state_event(registry.event_registry[0], registry.q_kappa_tape),
        "grid": {"cell_count": len(registry.grid), "dt": "1/64", "fold_count": len(registry.lineage_registry), "o_max": 4},
        "executable_firewall": firewall,
        "handoff": handoff,
        "objective": objective,
        "physical_tape_registration": {"canonical_q_source": "Q_KAPPA_TAPE", "independent_tapes": True, "positive_physical_indices": [index for index, state in enumerate(registry.q_kappa_tape) if state[1]], "q_current_suffix": "".join(str(state[1]) for state in registry.q_kappa_tape[-3:]), "q_transition_index": q_transition, "raw_x_at_q_transition": x_key(registry.raw_x_tape[q_transition]), "rows": len(registry.raw_x_tape)},
        "pointwise_diagnostic": {"derived_best_equals_handcrafted_lookup": best == lookup, "handcrafted_64_row_lookup_equals_pointwise": lookup == pointwise},
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "rules": rule_summary(tapes, rules),
        "terminals": {"physical_census_tuple_only_first_latch": physical_terminal, "fixed_single_transaction_handoff": handoff["exactly_once_handoff_safety"]},
        "treatment": TREATMENT,
        "x_star": {"count": len(registry.x_star), "keys": [x_key(x) for x in registry.x_star]},
    }


def _state_event(event: EventSpec, q_kappa_tape: tuple[tuple[int, int], ...]) -> dict[str, object]:
    return {"event_class": event.event_class, "kappa": event.kappa, "owner": event.owner, "q_diagnostic": [q_kappa_tape[0][0], *(state[1] for state in q_kappa_tape[-3:])], "q_diagnostic_source": "Q_KAPPA_TAPE", "target": event.target}


def raw_json() -> str:
    return json.dumps(build_report(), sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    print(raw_json())
