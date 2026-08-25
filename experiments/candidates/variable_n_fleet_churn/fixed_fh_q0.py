"""Deterministic Q0 quotient/checker/cost certificate for VNFC-TEPR FIXED-FH.

This module deliberately contains no mission host, learned arm, coordinate,
panel, or full FIXED-FH solver.  It proves the finite quotient contract on a
registered reduced-horizon exact fixture and emits analytic full-query bounds.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence


F = Fraction
STAGE_ID = "VNFC-TEPR-FIXED-FH-QUOTIENT-AND-COST-CERTIFICATE-Q0"
SCIENCE_ID = "VNFC-TEPR-SCIENCE-20260815-04"
SCIENCE_SHA256 = "8e9e87f0bdc55a691a5232e58c7b022cbc637765c500845fd822bf2e3005f791"
ROOT = Path(__file__).resolve().parents[3]
STAGE_RECORD = (
    ROOT
    / "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_TEPR_FIXED_FH_QUOTIENT_AND_COST_CERTIFICATE_Q0.md"
)
TEST_SOURCE = (
    ROOT
    / "tests/experiments/candidates/variable_n_fleet_churn/"
    "test_fixed_fh_q0.py"
)
COMMAND_ID = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B "
    "experiments/candidates/variable_n_fleet_churn/fixed_fh_q0.py"
)
SUCCESSOR_LABELS = tuple(f"exo_{index:02d}" for index in range(16))


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, order=True)
class Command:
    """Exact complete-command identity; ``serialization`` owns every tie."""

    serialization: tuple[int, ...]
    label: str


@dataclass(frozen=True)
class Edge:
    label: str
    probability: Fraction
    target: str
    delivered_increment: int
    demand_increment: int


@dataclass(frozen=True)
class Action:
    command: Command
    bid_sources: tuple[str, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class CandidateMark:
    command: Command
    exact_expected_value: Fraction


@dataclass(frozen=True)
class State:
    name: str
    past_delivered: int
    d_past: int
    physical_tag: str
    history_tag: str
    irrelevant_note: str
    actions: tuple[Action, ...]
    x20: CandidateMark | None = None
    x40: CandidateMark | None = None

    @property
    def terminal_ratio(self) -> Fraction:
        if self.d_past <= 0:
            return F(0)
        return F(self.past_delivered, self.d_past)


@dataclass(frozen=True)
class Graph:
    states: tuple[State, ...]
    roots: tuple[str, ...]
    invalid_merge_pair: tuple[str, str]

    @property
    def by_name(self) -> Mapping[str, State]:
        return {state.name: state for state in self.states}


@dataclass(frozen=True)
class BellmanRow:
    action_values: tuple[tuple[Command, Fraction], ...]
    maximizing_commands: tuple[Command, ...]
    selected_command: Command | None
    value: Fraction


def _command(index: int, label: str) -> Command:
    # The twelve integers mirror the complete-command serializer's fixed width.
    return Command((index,) + (9,) * 11, label)


CMD_A = _command(1, "A")
CMD_B = _command(2, "B")
CMD_C = _command(3, "C")


def _probabilities() -> tuple[Fraction, ...]:
    # Complete sixteen-way law with unequal rational probabilities.
    return (F(1, 32),) * 15 + (F(17, 32),)


def _edges_to(targets: Sequence[str], increments: Mapping[str, tuple[int, int]]) -> tuple[Edge, ...]:
    if not targets:
        raise ValueError("targets must be nonempty")
    expanded = tuple(targets[index % len(targets)] for index in range(16))
    return tuple(
        Edge(label, probability, target, *increments[target])
        for label, probability, target in zip(SUCCESSOR_LABELS, _probabilities(), expanded)
    )


def _single_target_edges(target: str) -> tuple[Edge, ...]:
    return tuple(Edge(label, probability, target, 0, 0) for label, probability in zip(SUCCESSOR_LABELS, _probabilities()))


def build_fixture_graph() -> Graph:
    """Return the immutable finite Q0 agreement fixture.

    The graph is synthetic exact checker evidence only.  It is not a mission
    host, world, panel, treatment observation, or approximation to a result.
    """

    terminals = (
        State("terminal_low", 1, 4, "terminal", "none", "low", ()),
        State("terminal_mid_a", 2, 4, "terminal", "none", "first-copy", ()),
        State("terminal_mid_b", 2, 4, "terminal", "none", "second-copy", ()),
        State("terminal_high", 3, 4, "terminal", "none", "high", ()),
        State("terminal_unequal_den", 2, 5, "terminal", "none", "same-physical-different-Dpast", ()),
    )
    increments = {
        "terminal_low": (1, 4),
        "terminal_mid_a": (2, 4),
        "terminal_mid_b": (2, 4),
        "terminal_high": (3, 4),
        "terminal_unequal_den": (2, 5),
    }
    common_terminal_edges = _edges_to(
        ("terminal_low", "terminal_mid_a", "terminal_mid_b", "terminal_high"),
        increments,
    )
    denominator_edges = _edges_to(
        ("terminal_low", "terminal_unequal_den", "terminal_high"),
        increments,
    )

    tie_actions = (
        Action(CMD_A, ("weight_000", "weight_001"), common_terminal_edges),
        Action(CMD_B, ("weight_002",), common_terminal_edges),
    )
    leaf_tie = State(
        "leaf_tie", 0, 0, "leaf", "tie-history", "tie must select A", tie_actions,
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_B, F(1, 2)),
    )
    leaf_equiv_a = State(
        "leaf_equiv_a", 0, 0, "leaf", "equiv", "drop-note-a",
        (Action(CMD_A, ("weight_003", "weight_004"), common_terminal_edges),),
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_A, F(1, 2)),
    )
    leaf_equiv_b = State(
        "leaf_equiv_b", 0, 0, "leaf", "equiv", "drop-note-b",
        (Action(CMD_A, ("weight_003", "weight_004"), common_terminal_edges),),
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_A, F(1, 2)),
    )
    leaf_history_a = State(
        "leaf_history_a", 0, 0, "same-current-physics", "history-a", "must-not-merge",
        (Action(CMD_A, ("weight_005",), common_terminal_edges),),
        CandidateMark(CMD_A, F(3, 8)), CandidateMark(CMD_A, F(3, 8)),
    )
    leaf_history_b = State(
        "leaf_history_b", 0, 0, "same-current-physics", "history-b", "must-not-merge",
        (Action(CMD_C, ("weight_005",), denominator_edges),),
        CandidateMark(CMD_C, F(2, 5)), CandidateMark(CMD_C, F(2, 5)),
    )

    mid_equiv_a = State(
        "mid_equiv_a", 0, 0, "mid", "equiv", "mid-note-a",
        (Action(CMD_A, ("weight_006", "weight_007"), _single_target_edges("leaf_equiv_a")),),
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_A, F(1, 2)),
    )
    mid_equiv_b = State(
        "mid_equiv_b", 0, 0, "mid", "equiv", "mid-note-b",
        (Action(CMD_A, ("weight_006", "weight_007"), _single_target_edges("leaf_equiv_b")),),
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_A, F(1, 2)),
    )
    mid_history_a = State(
        "mid_history_a", 0, 0, "mid-history", "driver-a", "routes to history-a",
        (Action(CMD_A, ("weight_008",), _single_target_edges("leaf_history_a")),),
        CandidateMark(CMD_A, F(3, 8)), CandidateMark(CMD_A, F(3, 8)),
    )
    mid_history_b = State(
        "mid_history_b", 0, 0, "mid-history", "driver-b", "routes to history-b",
        (Action(CMD_A, ("weight_008",), _single_target_edges("leaf_history_b")),),
        CandidateMark(CMD_A, F(2, 5)), CandidateMark(CMD_A, F(2, 5)),
    )

    root_actions_a = (
        Action(CMD_A, ("weight_000", "weight_001"), _single_target_edges("mid_equiv_a")),
        Action(CMD_B, ("weight_002",), _single_target_edges("mid_history_a")),
    )
    root_actions_b = (
        Action(CMD_A, ("weight_000", "weight_001"), _single_target_edges("mid_equiv_b")),
        Action(CMD_B, ("weight_002",), _single_target_edges("mid_history_a")),
    )
    root_a = State(
        "root_a", 0, 0, "root", "root-history", "root-note-a", root_actions_a,
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_B, F(3, 8)),
    )
    root_b = State(
        "root_b", 0, 0, "root", "root-history", "root-note-b", root_actions_b,
        CandidateMark(CMD_A, F(1, 2)), CandidateMark(CMD_B, F(3, 8)),
    )

    states = terminals + (
        leaf_tie, leaf_equiv_a, leaf_equiv_b, leaf_history_a, leaf_history_b,
        mid_equiv_a, mid_equiv_b, mid_history_a, mid_history_b, root_a, root_b,
    )
    roots = (
        "root_a", "root_b", "mid_history_a", "mid_history_b", "leaf_tie",
        "leaf_equiv_a", "leaf_equiv_b", "terminal_unequal_den",
    )
    graph = Graph(states, roots, ("leaf_history_a", "leaf_history_b"))
    validate_graph(graph)
    return graph


def validate_graph(graph: Graph) -> None:
    by_name = graph.by_name
    if len(by_name) != len(graph.states):
        raise ValueError("duplicate state name")
    if any(root not in by_name for root in graph.roots):
        raise ValueError("unknown root")
    for state in graph.states:
        ordered = tuple(sorted((action.command for action in state.actions)))
        if tuple(action.command for action in state.actions) != ordered or len(set(ordered)) != len(ordered):
            raise ValueError(f"actions are not unique canonical commands in {state.name}")
        commands = set(ordered)
        for mark_name, mark in (("X20", state.x20), ("X40", state.x40)):
            if mark is not None and mark.command not in commands:
                raise ValueError(f"{mark_name} is absent from A_fix in {state.name}")
        for action in state.actions:
            if tuple(edge.label for edge in action.edges) != SUCCESSOR_LABELS:
                raise ValueError(f"incomplete or reordered sixteen-way law in {state.name}")
            if sum((edge.probability for edge in action.edges), F(0)) != 1:
                raise ValueError(f"transition probabilities do not sum to one in {state.name}")
            for edge in action.edges:
                if edge.probability < 0 or edge.target not in by_name:
                    raise ValueError(f"invalid transition in {state.name}")
                target = by_name[edge.target]
                if target.past_delivered != state.past_delivered + edge.delivered_increment:
                    raise ValueError(f"delivered increment mismatch in {state.name}->{edge.target}")
                if target.d_past != state.d_past + edge.demand_increment:
                    raise ValueError(f"demand increment mismatch in {state.name}->{edge.target}")


def _mark_signature(mark: CandidateMark | None) -> tuple[object, ...] | None:
    if mark is None:
        return None
    return mark.command.serialization, mark.command.label, mark.exact_expected_value


def _local_signature(state: State) -> tuple[object, ...]:
    return (
        state.past_delivered,
        state.d_past,
        state.terminal_ratio,
        tuple(
            (action.command.serialization, action.command.label, action.bid_sources)
            for action in state.actions
        ),
        _mark_signature(state.x20),
        _mark_signature(state.x40),
    )


def _transition_signature(state: State, partition: Mapping[str, int]) -> tuple[object, ...]:
    return tuple(
        (
            action.command.serialization,
            tuple(
                (
                    edge.label,
                    edge.probability,
                    edge.delivered_increment,
                    edge.demand_increment,
                    partition[edge.target],
                )
                for edge in action.edges
            ),
        )
        for action in state.actions
    )


def _canonical_partition(signatures: Mapping[str, object]) -> dict[str, int]:
    unique = sorted(set(signatures.values()), key=repr)
    ids = {signature: index for index, signature in enumerate(unique)}
    return {name: ids[signature] for name, signature in signatures.items()}


def build_partition(graph: Graph) -> dict[str, int]:
    """Construct the coarsest stable partition under the frozen signature."""

    partition = _canonical_partition({state.name: _local_signature(state) for state in graph.states})
    while True:
        signatures = {
            state.name: (_local_signature(state), _transition_signature(state, partition))
            for state in graph.states
        }
        refined = _canonical_partition(signatures)
        if all((partition[a] == partition[b]) == (refined[a] == refined[b]) for a in partition for b in partition):
            return refined
        partition = refined


def _first_counterexample(graph: Graph, partition: Mapping[str, int]) -> Mapping[str, object] | None:
    """Independently reject any class that violates the exact obligations."""

    by_class: dict[int, list[State]] = {}
    for state in graph.states:
        if state.name not in partition:
            return {"quantity": "missing_partition_key", "state": state.name}
        by_class.setdefault(partition[state.name], []).append(state)
    for class_id in sorted(by_class):
        states = sorted(by_class[class_id], key=lambda state: state.name)
        reference = states[0]
        for state in states[1:]:
            if _local_signature(reference) != _local_signature(state):
                return {
                    "class": class_id,
                    "quantity": "local_A_fix_X20_X40_Dpast_ratio_or_tie_signature",
                    "reference": reference.name,
                    "state": state.name,
                }
            if _transition_signature(reference, partition) != _transition_signature(state, partition):
                return {
                    "class": class_id,
                    "quantity": "labeled_rational_transition_distribution",
                    "reference": reference.name,
                    "state": state.name,
                }
    return None


def check_partition(graph: Graph, partition: Mapping[str, int]) -> None:
    counterexample = _first_counterexample(graph, partition)
    if counterexample is not None:
        raise ValueError(json.dumps(counterexample, sort_keys=True, separators=(",", ":")))


def _row_for_values(state: State, action_values: Sequence[tuple[Command, Fraction]]) -> BellmanRow:
    if not action_values:
        return BellmanRow((), (), None, state.terminal_ratio)
    best = max(value for _, value in action_values)
    maximizing = tuple(command for command, value in action_values if value == best)
    selected = min(maximizing)
    return BellmanRow(tuple(action_values), maximizing, selected, best)


def evaluate_reference(graph: Graph, state_name: str, horizon: int, memo: dict[tuple[str, int], BellmanRow] | None = None) -> BellmanRow:
    if horizon < 0:
        raise ValueError("negative horizon")
    if memo is None:
        memo = {}
    key = state_name, horizon
    if key in memo:
        return memo[key]
    state = graph.by_name[state_name]
    if horizon == 0 or not state.actions:
        row = _row_for_values(state, ())
    else:
        action_values = []
        for action in state.actions:
            value = sum(
                (edge.probability * evaluate_reference(graph, edge.target, horizon - 1, memo).value for edge in action.edges),
                F(0),
            )
            action_values.append((action.command, value))
        row = _row_for_values(state, action_values)
    memo[key] = row
    return row


def evaluate_quotient(
    graph: Graph,
    partition: Mapping[str, int],
    class_id: int,
    horizon: int,
    memo: dict[tuple[int, int], BellmanRow] | None = None,
) -> BellmanRow:
    if memo is None:
        memo = {}
    key = class_id, horizon
    if key in memo:
        return memo[key]
    representative = min((state for state in graph.states if partition[state.name] == class_id), key=lambda state: state.name)
    if horizon == 0 or not representative.actions:
        row = _row_for_values(representative, ())
    else:
        action_values = []
        for action in representative.actions:
            value = sum(
                (
                    edge.probability
                    * evaluate_quotient(graph, partition, partition[edge.target], horizon - 1, memo).value
                    for edge in action.edges
                ),
                F(0),
            )
            action_values.append((action.command, value))
        row = _row_for_values(representative, action_values)
    memo[key] = row
    return row


def reachable_states(graph: Graph, root: str, horizon: int) -> tuple[str, ...]:
    frontier = {root}
    reached = {root}
    for _ in range(horizon):
        next_frontier = {
            edge.target
            for name in frontier
            for action in graph.by_name[name].actions
            for edge in action.edges
        }
        reached.update(next_frontier)
        frontier = next_frontier
    return tuple(sorted(reached))


def exhaustive_agreement(graph: Graph, partition: Mapping[str, int]) -> Mapping[str, object]:
    check_partition(graph, partition)
    comparisons = 0
    reachable_pairs: set[tuple[str, int]] = set()
    tie_rows = 0
    for horizon in (1, 2, 3):
        for root in graph.roots:
            for state_name in reachable_states(graph, root, horizon):
                for remaining in range(horizon + 1):
                    reachable_pairs.add((state_name, remaining))
    ref_memo: dict[tuple[str, int], BellmanRow] = {}
    q_memo: dict[tuple[int, int], BellmanRow] = {}
    for state_name, horizon in sorted(reachable_pairs):
        reference = evaluate_reference(graph, state_name, horizon, ref_memo)
        quotient = evaluate_quotient(graph, partition, partition[state_name], horizon, q_memo)
        if reference != quotient:
            raise AssertionError(
                f"agreement counterexample state={state_name} horizon={horizon} "
                f"reference={reference} quotient={quotient}"
            )
        comparisons += 1
        tie_rows += len(reference.maximizing_commands) > 1

    invalid = dict(partition)
    left, right = graph.invalid_merge_pair
    invalid[right] = invalid[left]
    counterexample = _first_counterexample(graph, invalid)
    if counterexample is None:
        raise AssertionError("registered invalid merge was not rejected")
    return {
        "agreement_rows": comparisons,
        "horizons": [1, 2, 3],
        "invalid_merge_counterexample": counterexample,
        "reachable_state_horizon_rows": len(reachable_pairs),
        "tie_rows": tie_rows,
    }


def full_query_bounds(
    *,
    horizon: int = 6,
    actions: int = 129,
    successor_fanout: int = 16,
    legal_matchings: int = 1961,
    weight_vectors: int = 127,
    replicates: int = 20,
    worlds_per_replicate: int = 128,
    probability_bits: int = 12,
    increment_bits: int = 10,
    key_bytes: int = 2048,
    edge_bytes: int = 96,
    integer_object_overhead_bytes: int = 64,
) -> Mapping[str, object]:
    values = (
        horizon, actions, successor_fanout, legal_matchings, weight_vectors,
        replicates, worlds_per_replicate, probability_bits, increment_bits,
        key_bytes, edge_bytes, integer_object_overhead_bytes,
    )
    if any(value <= 0 for value in values):
        raise ValueError("full-query parameters must be positive")
    q_raw = sum(actions ** (depth + 1) * successor_fanout**depth for depth in range(horizon))
    e_raw = sum(
        actions ** (depth + 1) * successor_fanout ** (depth + 1)
        for depth in range(horizon - 1)
    )
    reachable_keys = sum((actions * successor_fanout) ** depth for depth in range(horizon))
    panel_worlds = replicates * worlds_per_replicate
    stochastic_depth = horizon - 1
    path_count = successor_fanout**stochastic_depth
    path_probability_bits = 1 + stochastic_depth * probability_bits
    terminal_increment_bits = increment_bits + math.ceil(math.log2(horizon + 1))
    weighted_term_denominator_bits = path_probability_bits + terminal_increment_bits
    # Safe for arbitrary reduced denominators: the denominator of a sum divides
    # their product.  This is intentionally conservative, not an allocation.
    bellman_denominator_bits = path_count * weighted_term_denominator_bits
    bellman_numerator_bits = bellman_denominator_bits + math.ceil(math.log2(path_count + 1))
    value_bytes = (
        math.ceil(bellman_denominator_bits / 8)
        + math.ceil(bellman_numerator_bits / 8)
        + 2 * integer_object_overhead_bytes
    )
    raw_memory_bytes = reachable_keys * key_bytes + e_raw * edge_bytes + q_raw * value_bytes
    candidate_generation = {
        "rda_calls_per_state": weight_vectors,
        "x20_matching_evaluations_per_state": legal_matchings,
        "x40_matching_pair_evaluations_per_state": legal_matchings * successor_fanout * legal_matchings,
    }
    return {
        "assumptions": {
            "A": actions,
            "B": successor_fanout,
            "F": legal_matchings,
            "H": horizon,
            "W": weight_vectors,
            "panel_worlds": panel_worlds,
        },
        "candidate_generation": candidate_generation,
        "quotient_parametric": {
            "action_evaluations": "sum_h(K_h*A_h)",
            "action_successor_edges": "sum_(h>1)(K_h*A_h*16)",
            "certificate_bytes": "sum_h(K_h*(key_bytes+value_bytes)+K_h*A_h*16*edge_bytes)",
            "reachable_key_counts": "K_1..K_6 are measured only by a later full graph; Q0 fabricates none",
        },
        "rational_bits": {
            "bellman_denominator_upper": bellman_denominator_bits,
            "bellman_numerator_upper": bellman_numerator_bits,
            "input_increment_bits": increment_bits,
            "input_probability_bits": probability_bits,
            "path_count": path_count,
            "path_probability_bits": path_probability_bits,
            "value_allocation_bytes_upper": value_bytes,
            "weighted_term_denominator_bits": weighted_term_denominator_bits,
        },
        "unquotiented": {
            "action_evaluations_one_root": q_raw,
            "action_evaluations_panel": q_raw * panel_worlds,
            "action_successor_edges_one_root": e_raw,
            "action_successor_edges_panel": e_raw * panel_worlds,
            "candidate_generation_work_one_root_upper": reachable_keys
            * (
                weight_vectors
                + legal_matchings
                + legal_matchings * successor_fanout * legal_matchings
            ),
            "peak_materialized_bytes_upper": raw_memory_bytes,
            "reachable_keys_one_root": reachable_keys,
            "reachable_keys_panel": reachable_keys * panel_worlds,
        },
        "work_ledger": [
            "canonical-key construction",
            "W RDA calls per reachable state",
            "X20 legal-matching enumeration",
            "X40 first-action by successor by X20 enumeration",
            "sixteen-way transition generation",
            "arbitrary-precision rational arithmetic",
            "partition refinement",
            "independent bisimulation checking",
            "backward induction",
            "certificate serialization",
            "panel multiplication",
        ],
    }


def _partition_inventory(graph: Graph, partition: Mapping[str, int]) -> Mapping[str, object]:
    classes: dict[int, list[str]] = {}
    for name, class_id in partition.items():
        classes.setdefault(class_id, []).append(name)
    normalized = [sorted(names) for _, names in sorted(classes.items())]
    return {
        "class_count": len(normalized),
        "classes": normalized,
        "merged_pairs": [names for names in normalized if len(names) > 1],
    }


def build_payload() -> Mapping[str, object]:
    graph = build_fixture_graph()
    partition = build_partition(graph)
    agreement = exhaustive_agreement(graph, partition)
    source_path = Path(__file__).resolve()
    return {
        "agreement": agreement,
        "bounds": full_query_bounds(),
        "bundle": {
            "command_identity": COMMAND_ID,
            "finite_completion": True,
            "manifest_complete": True,
            "science_card_sha256": SCIENCE_SHA256,
            "source_path": source_path.relative_to(ROOT).as_posix(),
            "source_sha256": _sha256(source_path),
            "stage_record_path": STAGE_RECORD.relative_to(ROOT).as_posix(),
            "stage_record_sha256": _sha256(STAGE_RECORD),
            "test_path": TEST_SOURCE.relative_to(ROOT).as_posix(),
            "test_sha256": _sha256(TEST_SOURCE),
        },
        "fixture": {
            "action_count": sum(len(state.actions) for state in graph.states),
            "edge_count": sum(len(action.edges) for state in graph.states for action in state.actions),
            "nonclaims": [
                "full FIXED-FH solver feasibility",
                "empirical host feasibility",
                "learned-arm value",
                "coordinate or panel result",
                "production lease readiness",
                "science-card modification",
            ],
            "root_count": len(graph.roots),
            "state_count": len(graph.states),
            "successor_labels": list(SUCCESSOR_LABELS),
        },
        "partition": _partition_inventory(graph, partition),
        "q0_cost": {
            "cpu_hours": [25, 800],
            "engineering_weeks": [5, 10],
            "peak_ram_gb": [4, 32],
            "retained_gb": [0.1, 5],
            "temporary_gb": [1, 50],
            "wall_weeks": [3, 8],
        },
        "science_id": SCIENCE_ID,
        "stage_id": STAGE_ID,
        "status": "Q0_COMPLETE",
    }


def build_result() -> Mapping[str, object]:
    payload = build_payload()
    return {
        "payload": payload,
        "payload_sha256": hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
    }


def main() -> None:
    sys.stdout.buffer.write(_canonical_bytes(build_result()) + b"\n")


if __name__ == "__main__":
    main()
