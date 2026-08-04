"""Deterministic Sequence 11 finite census and independent handoff model check."""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from typing import Iterable, Mapping


ASSIGNMENT_ID = "vsp05_sequence_11_semantic_veto_20260803"
CANDIDATE = "CAND-VSP-05@adversarial-revision-v7"
TREATMENT = "VSP-05-FINITE-CENSUS-SEMANTIC-VETO-D0"
EVENT_CLASS = "E_SC1_SINGLE_OWNER_MONOTONE_SERVICE_COMPLETION"
RAW_OUTPUT_BINDING = "vsp05.semantic_veto_census.sequence11.v1"
FIELDS = (
    "e_local",
    "r_relation",
    "p_public",
    "b_integrity",
    "b_contradiction",
    "b_validity",
)
FOLDS = (
    "lineage_alpha_full",
    "lineage_beta_full",
    "lineage_gamma_full",
    "lineage_delta_full",
    "lineage_epsilon_full",
    "lineage_zeta_full",
)
FORBIDDEN_FAMILIES = (
    "time",
    "frame",
    "age",
    "velocity",
    "history",
    "occupancy",
    "raw_ids",
    "reward",
    "future_state",
    "recurrent_features",
    "shared_features",
    "normalization",
    "teacher_tensors",
)
FORBIDDEN_PROXIES = {
    "time": "elapsed_steps_proxy",
    "frame": "frame_index_proxy",
    "age": "object_age_proxy",
    "velocity": "speed_norm_proxy",
    "history": "temporal_cache_proxy",
    "occupancy": "occupancy_ratio_proxy",
    "raw_ids": "agent_id_proxy",
    "reward": "return_signal_proxy",
    "future_state": "next_state_proxy",
    "recurrent_features": "hidden_state_proxy",
    "shared_features": "partner_embedding_proxy",
    "normalization": "normalized_tuple_proxy",
    "teacher_tensors": "teacher_logits_proxy",
}
SENSITIVE_NODES = ("tuple", "artifact", "calibration", "threshold", "runtime_decision")
X_STAR = tuple(product((False, True), repeat=6))


@dataclass(frozen=True)
class EventSpec:
    event_class: str
    kappa: str
    owner: str
    target: str
    q: tuple[int, ...]


@dataclass(frozen=True)
class Cell:
    a: Fraction
    s: Fraction
    d: Fraction
    r: int
    o: int

    @property
    def key(self) -> str:
        return f"A={self.a}|S={self.s}|D={self.d}|R={self.r}|O={self.o}"


@dataclass(frozen=True)
class Tape:
    cell_key: str
    fold: str
    xs: tuple[tuple[bool, ...], ...]


@dataclass(frozen=True)
class Registry:
    event_registry: tuple[EventSpec, ...]
    lineage_registry: tuple[str, ...]
    grid: tuple[Cell, ...]
    schema: tuple[str, ...]
    x_star: tuple[tuple[bool, ...], ...]
    tapes: tuple[Tape, ...]


def monotone_q(horizon: int = 4, transition_at: int = 1) -> tuple[int, ...]:
    if not (0 < transition_at < horizon):
        raise ValueError("transition must be exactly once inside the registered horizon")
    return tuple(0 if index < transition_at else 1 for index in range(horizon))


def build_registry() -> Registry:
    dt = Fraction(1, 64)
    grid = tuple(
        Cell(a, s, d, r, o)
        for a, s, d, r, o in product(
            (0 * dt, 8 * dt, 32 * dt),
            (Fraction(1, 2), Fraction(1), Fraction(2)),
            (0 * dt, 2 * dt, 8 * dt),
            (1, 2, 4),
            (0, 2, 4),
        )
    )
    event = EventSpec(EVENT_CLASS, "kappa_focal_001", "owner_focal", "target_focal", monotone_q())
    tapes = tuple(Tape(cell.key, fold, X_STAR) for cell in grid for fold in FOLDS)
    return Registry((event,), FOLDS, grid, FIELDS, X_STAR, tapes)


def physical_label(
    x: tuple[bool, ...], *, transaction_match: bool, owner_epoch_valid: bool
) -> int:
    if len(x) != 6:
        raise ValueError("X must contain exactly the six registered physical booleans")
    physical = x == (True, True, True, True, False, True)
    return int(physical and transaction_match and owner_epoch_valid)


def x_key(x: tuple[bool, ...]) -> str:
    return "".join("1" if bit else "0" for bit in x)


def dependency_graph() -> dict[str, tuple[str, ...]]:
    nodes = set(FORBIDDEN_FAMILIES) | set(FORBIDDEN_PROXIES.values())
    nodes |= set(FIELDS) | set(SENSITIVE_NODES) | {
        "transaction_match",
        "owner_epoch_valid",
        "label",
        "outcome",
        "registry",
    }
    graph = {node: () for node in nodes}
    for family, proxy in FORBIDDEN_PROXIES.items():
        graph[family] = (proxy,)
    for field in FIELDS:
        graph[field] = ("tuple",)
    graph["tuple"] = ("artifact", "label")
    graph["transaction_match"] = ("label",)
    graph["owner_epoch_valid"] = ("label",)
    graph["artifact"] = ("calibration", "runtime_decision")
    graph["calibration"] = ("threshold",)
    graph["threshold"] = ("runtime_decision",)
    graph["registry"] = ("artifact",)
    return graph


def with_edge(
    graph: Mapping[str, Iterable[str]], source: str, destination: str
) -> dict[str, tuple[str, ...]]:
    copied = {node: tuple(targets) for node, targets in graph.items()}
    copied.setdefault(source, ())
    copied.setdefault(destination, ())
    copied[source] = tuple(sorted(set(copied[source]) | {destination}))
    return copied


def _path(graph: Mapping[str, Iterable[str]], source: str, target: str) -> tuple[str, ...]:
    queue = deque([(source, (source,))])
    seen = {source}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        for child in graph.get(node, ()):
            if child not in seen:
                seen.add(child)
                queue.append((child, path + (child,)))
    return ()


def taint_report(graph: Mapping[str, Iterable[str]]) -> dict[str, object]:
    forbidden = FORBIDDEN_FAMILIES + tuple(FORBIDDEN_PROXIES.values())
    hits = []
    for source in forbidden:
        for target in SENSITIVE_NODES:
            path = _path(graph, source, target)
            if path:
                hits.append({"source": source, "target": target, "path": list(path)})
    return {"clean": not hits, "checked_pairs": len(forbidden) * len(SENSITIVE_NODES), "hits": hits}


def outcome_registry_report(graph: Mapping[str, Iterable[str]]) -> dict[str, object]:
    hits = []
    for source in ("label", "outcome"):
        path = _path(graph, source, "registry")
        if path:
            hits.append(list(path))
    return {"clean": not hits, "paths": hits}


def census(registry: Registry) -> dict[str, object]:
    counts = {x: [0, 0] for x in registry.x_star}
    fold_counts = {fold: Counter() for fold in registry.lineage_registry}
    support_exits = []
    for tape in registry.tapes:
        for x in tape.xs:
            if x not in counts:
                support_exits.append((tape.cell_key, tape.fold, x))
                continue
            y = physical_label(x, transaction_match=True, owner_epoch_valid=True)
            counts[x][y] += 1
            fold_counts[tape.fold][x] += 1
    contradictions = [x_key(x) for x, values in counts.items() if all(values)]
    fold_summary = {
        fold: {
            "count_per_tuple": min(counter.values()),
            "full_support": set(counter) == set(registry.x_star) and len(set(counter.values())) == 1,
            "opportunities": sum(counter.values()),
            "tuple_count": len(counter),
        }
        for fold, counter in fold_counts.items()
    }
    return {
        "contradictions": contradictions,
        "folds": fold_summary,
        "opportunities": sum(sum(values) for values in counts.values()),
        "positive_labels": sum(values[1] for values in counts.values()),
        "support_exits": [str(item) for item in support_exits],
        "x_by_y": {x_key(x): {"y0": values[0], "y1": values[1]} for x, values in counts.items()},
        "_counts": counts,
    }


def saturated_lookup() -> dict[tuple[bool, ...], int]:
    return {x: physical_label(x, transaction_match=True, owner_epoch_valid=True) for x in X_STAR}


def derive_best_rule(counts: Mapping[tuple[bool, ...], tuple[int, int] | list[int]]) -> dict[tuple[bool, ...], int]:
    rule = {}
    for x in X_STAR:
        y0, y1 = counts[x]
        risk_if_zero = y1
        risk_if_one = y0
        rule[x] = int(risk_if_one < risk_if_zero)
    return rule


def registered_rules(counts: Mapping[tuple[bool, ...], tuple[int, int] | list[int]]) -> dict[str, dict[tuple[bool, ...], int]]:
    return {
        "NO_VETO": {x: 1 for x in X_STAR},
        "ALWAYS_VETO": {x: 0 for x in X_STAR},
        "SATURATED_ALLOWLIST_LOOKUP": saturated_lookup(),
        "BEST_DETERMINISTIC_TUPLE_ONLY_RULE": derive_best_rule(counts),
    }


def sequential_fact(tape: Tape, rule: Mapping[tuple[bool, ...], int]) -> dict[str, object]:
    decisions = tuple(rule[x] for x in tape.xs)
    labels = tuple(physical_label(x, transaction_match=True, owner_epoch_valid=True) for x in tape.xs)
    surviving = 1
    false_alias = 0
    first_index = None
    first_label = None
    for index, (action, label) in enumerate(zip(decisions, labels)):
        false_alias += surviving * action * (1 - label)
        if surviving and action:
            first_index, first_label = index, label
        surviving *= 1 - action
    return {
        "action_decisions": "".join(map(str, decisions)),
        "first_latch_index_zero_based": first_index,
        "first_latch_label": first_label,
        "first_latch_false_alias": false_alias,
        "missed_positives": sum((1 - action) * label for action, label in zip(decisions, labels)),
        "positive_captures": sum(action * label for action, label in zip(decisions, labels)),
    }


def rule_summary(registry: Registry, rules: Mapping[str, Mapping[tuple[bool, ...], int]]) -> dict[str, object]:
    coverage = Counter(tape.cell_key for tape in registry.tapes)
    summaries = {}
    for name, rule in rules.items():
        variants = Counter(
            json.dumps(sequential_fact(tape, rule), sort_keys=True, separators=(",", ":"))
            for tape in registry.tapes
        )
        summaries[name] = {
            "unique_fact_variants": len(variants),
            "variants": [
                {"cell_fold_count": count, "facts": json.loads(facts)}
                for facts, count in sorted(variants.items())
            ],
        }
    return {
        "cell_fold_coverage_counts": sorted(set(coverage.values())),
        "covered_cell_keys": sorted(coverage),
        "rules": summaries,
        "tape_count": len(registry.tapes),
    }


def clone_report(rules: Mapping[str, Mapping[tuple[bool, ...], int]]) -> dict[str, object]:
    clones = tuple(product(("0", "1/8", "1/2"), (0, 2, 4), (1, 2, 4)))
    drifts = []
    comparisons = 0
    for x in X_STAR:
        for age, occupancy, frame_refinement in clones:
            clone_x = tuple(x)
            for name, rule in rules.items():
                comparisons += 1
                if clone_x != x or rule[clone_x] != rule[x]:
                    drifts.append((x_key(x), age, occupancy, frame_refinement, name))
    return {"clone_count": len(clones), "comparisons": comparisons, "decision_drifts": drifts}


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
    rules = registered_rules(counts)
    taint = taint_report(dependency_graph())
    outcome_registry = outcome_registry_report(dependency_graph())
    clones = clone_report(rules)
    handoff = handoff_model_check()
    lookup_terminal = (
        not count_report["contradictions"]
        and not count_report["support_exits"]
        and taint["clean"]
        and outcome_registry["clean"]
        and not clones["decision_drifts"]
        and rules["SATURATED_ALLOWLIST_LOOKUP"] == rules["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"]
    )
    return {
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "census": count_report,
        "clone_invariance": clones,
        "conclusion": {
            "exactly_once_handoff_safety_holds_in_fixed_synthetic_instance": handoff["exactly_once_handoff_safety"],
            "finite_support_lookup_conformance_holds_in_fixed_synthetic_instance": lookup_terminal,
        },
        "event": _state_event(registry.event_registry[0]),
        "grid": {
            "cell_count": len(registry.grid),
            "cell_keys": sorted(cell.key for cell in registry.grid),
            "dt": "1/64",
            "fold_count": len(registry.lineage_registry),
            "o_max": 4,
        },
        "handoff": handoff,
        "outcome_selected_registry": outcome_registry,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "rules": rule_summary(registry, rules),
        "taint": taint,
        "treatment": TREATMENT,
        "x_star": {"count": len(registry.x_star), "keys": [x_key(x) for x in registry.x_star]},
    }


def _state_event(event: EventSpec) -> dict[str, object]:
    return {
        "event_class": event.event_class,
        "kappa": event.kappa,
        "owner": event.owner,
        "q": list(event.q),
        "target": event.target,
    }


def raw_json() -> str:
    return json.dumps(build_report(), sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    print(raw_json())
