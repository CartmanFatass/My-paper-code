from __future__ import annotations

import ast
import inspect
import json
import re
from collections import deque
from dataclasses import FrozenInstanceError
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from experiments.candidates.vsp_05 import semantic_veto_census as svc


ROOT = Path(__file__).parents[4]
SOURCE = ROOT / "experiments/candidates/vsp_05/semantic_veto_census.py"
INDEX = ROOT / "docs/research/candidates/vsp_05/CODE_SCIENCE_INDEX.md"


def test_registry_is_ex_ante_canonical_and_complete() -> None:
    signature = inspect.signature(svc.build_registry)
    source = inspect.getsource(svc.build_registry)
    assert not signature.parameters
    assert not ({"physical_label", "label", "outcome"} & {node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)})

    registry = svc.build_registry()
    dt = Fraction(1, 64)
    expected_grid = tuple(
        svc.Cell(a, s, d, r, o)
        for a, s, d, r, o in product(
            (0 * dt, 8 * dt, 32 * dt),
            (Fraction(1, 2), Fraction(1), Fraction(2)),
            (0 * dt, 2 * dt, 8 * dt),
            (1, 2, 4),
            (0, 2, 4),
        )
    )
    assert registry.grid == expected_grid
    assert len(registry.grid) == 243
    assert registry.schema == svc.FIELDS
    assert registry.lineage_registry == svc.FOLDS and len(set(svc.FOLDS)) == 6
    assert registry.x_star == tuple(product((False, True), repeat=6))
    assert len(registry.x_star) == len(set(registry.x_star)) == 64
    assert len(registry.tapes) == 243 * 6
    assert [(t.cell_key, t.fold) for t in registry.tapes] == [
        (cell.key, fold) for cell in expected_grid for fold in svc.FOLDS
    ]
    assert all(tape.xs == registry.x_star and len(set(tape.xs)) == 64 for tape in registry.tapes)


def test_event_and_physical_only_label_contract() -> None:
    event = svc.build_registry().event_registry[0]
    assert event.event_class == svc.EVENT_CLASS
    assert event.q[0] == 0
    assert sum(left == 0 and right == 1 for left, right in zip(event.q, event.q[1:])) == 1
    transition = next(i for i, (left, right) in enumerate(zip(event.q, event.q[1:])) if (left, right) == (0, 1))
    assert all(value == 1 for value in event.q[transition + 1 :])
    with pytest.raises(FrozenInstanceError):
        event.kappa = "changed"

    positive = (True, True, True, True, False, True)
    assert sum(svc.physical_label(x, transaction_match=True, owner_epoch_valid=True) for x in svc.X_STAR) == 1
    assert svc.physical_label(positive, transaction_match=True, owner_epoch_valid=True) == 1
    assert svc.physical_label(positive, transaction_match=False, owner_epoch_valid=True) == 0
    assert svc.physical_label(positive, transaction_match=True, owner_epoch_valid=False) == 0
    assert list(inspect.signature(svc.physical_label).parameters) == ["x", "transaction_match", "owner_epoch_valid"]
    assert len(positive) == len(svc.FIELDS) == 6


def test_exact_census_counts_support_and_contradictions() -> None:
    report = svc.census(svc.build_registry())
    counts = report.pop("_counts")
    assert report["opportunities"] == 243 * 6 * 64 == 93_312
    assert report["positive_labels"] == 243 * 6 == 1_458
    assert report["contradictions"] == []
    assert report["support_exits"] == []
    for x, (y0, y1) in counts.items():
        assert y0 + y1 == 243 * 6
        assert bool(y1) == (x == (True, True, True, True, False, True))
    assert set(report["folds"]) == set(svc.FOLDS)
    assert all(
        facts == {"count_per_tuple": 243, "full_support": True, "opportunities": 243 * 64, "tuple_count": 64}
        for facts in report["folds"].values()
    )


def test_primary_taint_graph_checks_every_forbidden_family_and_proxy() -> None:
    assert len(svc.FORBIDDEN_FAMILIES) == len(set(svc.FORBIDDEN_FAMILIES)) == 13
    assert set(svc.FORBIDDEN_PROXIES) == set(svc.FORBIDDEN_FAMILIES)
    assert len(set(svc.FORBIDDEN_PROXIES.values())) == 13
    report = svc.taint_report(svc.dependency_graph())
    assert report == {"clean": True, "checked_pairs": 26 * 5, "hits": []}


@pytest.mark.parametrize("source", svc.FORBIDDEN_FAMILIES + tuple(svc.FORBIDDEN_PROXIES.values()))
def test_direct_forbidden_dependency_injection_fails_closed(source: str) -> None:
    graph = svc.with_edge(svc.dependency_graph(), source, "tuple")
    report = svc.taint_report(graph)
    assert not report["clean"]
    assert any(hit["source"] == source and hit["target"] == "tuple" for hit in report["hits"])


@pytest.mark.parametrize("source", svc.FORBIDDEN_FAMILIES + tuple(svc.FORBIDDEN_PROXIES.values()))
def test_transitive_forbidden_dependency_injection_fails_closed(source: str) -> None:
    graph = svc.with_edge(svc.dependency_graph(), source, "injected_bridge")
    graph = svc.with_edge(graph, "injected_bridge", "artifact")
    report = svc.taint_report(graph)
    assert not report["clean"]
    assert any(hit["path"][:3] == [source, "injected_bridge", "artifact"] for hit in report["hits"])


def test_outcome_selection_recurrence_and_partner_adaptation_fail_closed() -> None:
    primary = svc.dependency_graph()
    assert svc.outcome_registry_report(primary)["clean"]
    direct = svc.with_edge(primary, "label", "registry")
    assert not svc.outcome_registry_report(direct)["clean"]
    transitive = svc.with_edge(primary, "outcome", "selector")
    transitive = svc.with_edge(transitive, "selector", "registry")
    assert not svc.outcome_registry_report(transitive)["clean"]
    for source in ("recurrent_features", "hidden_state_proxy", "shared_features", "partner_embedding_proxy"):
        assert not svc.taint_report(svc.with_edge(primary, source, "runtime_decision"))["clean"]


def test_canonical_lookup_and_independent_empirical_risk_rule() -> None:
    census = svc.census(svc.build_registry())
    counts = census["_counts"]
    lookup = svc.saturated_lookup()
    best = svc.derive_best_rule(counts)
    assert lookup == best
    assert sum(lookup.values()) == 1
    assert lookup[(True, True, True, True, False, True)] == 1
    tied = {x: [1, 1] for x in svc.X_STAR}
    assert set(svc.derive_best_rule(tied).values()) == {0}
    inverted = {x: [0, 3] for x in svc.X_STAR}
    assert set(svc.derive_best_rule(inverted).values()) == {1}


def test_rule_conventions_and_all_cell_fold_sequential_facts() -> None:
    registry = svc.build_registry()
    counts = svc.census(registry)["_counts"]
    rules = svc.registered_rules(counts)
    assert set(rules["NO_VETO"].values()) == {1}
    assert set(rules["ALWAYS_VETO"].values()) == {0}
    expected_lookup_decisions = "0" * 61 + "1" + "0" * 2
    expected = {
        "NO_VETO": ("1" * 64, 0, 0, 1, 1, 0),
        "ALWAYS_VETO": ("0" * 64, None, None, 0, 0, 1),
        "SATURATED_ALLOWLIST_LOOKUP": (expected_lookup_decisions, 61, 1, 0, 1, 0),
        "BEST_DETERMINISTIC_TUPLE_ONLY_RULE": (expected_lookup_decisions, 61, 1, 0, 1, 0),
    }
    seen_cells = set()
    seen_pairs = set()
    for tape in registry.tapes:
        seen_cells.add(tape.cell_key)
        seen_pairs.add((tape.cell_key, tape.fold))
        for name, rule in rules.items():
            fact = svc.sequential_fact(tape, rule)
            observed = (
                fact["action_decisions"],
                fact["first_latch_index_zero_based"],
                fact["first_latch_label"],
                fact["first_latch_false_alias"],
                fact["positive_captures"],
                fact["missed_positives"],
            )
            assert observed == expected[name]
    assert seen_cells == {cell.key for cell in registry.grid}
    assert len(seen_cells) == 243 and len(seen_pairs) == 243 * 6
    summary = svc.rule_summary(registry, rules)
    assert summary["cell_fold_coverage_counts"] == [6]
    assert summary["covered_cell_keys"] == sorted(seen_cells)
    assert summary["tape_count"] == 1_458
    assert all(item["unique_fact_variants"] == 1 for item in summary["rules"].values())
    assert all(item["variants"][0]["cell_fold_count"] == 1_458 for item in summary["rules"].values())


def test_age_occupancy_and_frame_refinement_clones_are_invariant() -> None:
    counts = svc.census(svc.build_registry())["_counts"]
    report = svc.clone_report(svc.registered_rules(counts))
    assert report == {"clone_count": 27, "comparisons": 64 * 27 * 4, "decision_drifts": []}


@pytest.mark.parametrize(
    "field,value",
    [("kappa", "other"), ("rho", "other"), ("epoch_sender", 8), ("epoch_receiver", 12)],
)
def test_ready_ack_requires_every_exact_binding(field: str, value: object) -> None:
    spec = svc.HandoffSpec()
    values = {
        "kappa": spec.kappa,
        "rho": spec.rho,
        "epoch_sender": spec.epoch_sender,
        "epoch_receiver": spec.epoch_receiver,
    }
    values[field] = value
    assert not svc.ack_matches(spec, svc.ReadyAck(**values))


@pytest.mark.parametrize(
    "field,value",
    [("sender", "other"), ("receiver", "other"), ("kappa", "other"), ("observed_at_precommit", False)],
)
def test_safe_certificate_requires_exact_parties_transaction_and_precommit_time(field: str, value: object) -> None:
    spec = svc.HandoffSpec()
    values = {
        "sender": spec.sender,
        "receiver": spec.receiver,
        "kappa": spec.kappa,
        "observed_at_precommit": True,
    }
    values[field] = value
    assert not svc.safe_matches(spec, svc.SafeCertificate(**values))


def test_handoff_model_exhaustively_checks_reachable_graph() -> None:
    spec = svc.HandoffSpec()
    start = svc.HandoffState()
    queue = deque([start])
    states = {start}
    transitions = 0
    while queue:
        state = queue.popleft()
        for action in svc.HANDOFF_ACTIONS:
            successor = svc.handoff_transition(state, action, spec)
            transitions += 1
            assert successor.commit_count <= 1
            assert not successor.sender_terminated or successor.public_commit
            assert not successor.receiver_active or successor.public_commit
            assert successor.public_commit == (successor.commit_count == 1)
            if successor not in states:
                states.add(successor)
                queue.append(successor)
    report = svc.handoff_model_check()
    assert report["reachable_states"] == len(states) == 48
    assert report["transitions_checked"] == transitions == 480
    assert report["invariant_violations"] == []
    assert report["exactly_once_handoff_safety"]
    assert all(report["negative_gate_checks"].values())


def test_handoff_negative_gates_valid_trace_and_duplicate_commit() -> None:
    spec = svc.HandoffSpec()

    def apply(actions: tuple[str, ...]) -> svc.HandoffState:
        state = svc.HandoffState()
        for action in actions:
            state = svc.handoff_transition(state, action, spec)
        return state

    assert not apply(("SEMANTIC_LATCH", "HANDOFF_COMMIT")).public_commit
    assert not apply(("SEMANTIC_LATCH", "ACK_VALID", "HANDOFF_COMMIT")).public_commit
    assert not apply(("SEMANTIC_LATCH", "SAFE_ON", "HANDOFF_COMMIT")).public_commit
    assert not apply(("SAFE_ON", "ACK_VALID", "HANDOFF_COMMIT")).public_commit
    assert not apply(("SEMANTIC_LATCH", "SAFE_ON", "ACK_VALID", "REVOKE", "HANDOFF_COMMIT")).public_commit
    assert not apply(("SENDER_TERMINATE",)).sender_terminated
    assert not apply(("RECEIVER_ACTIVATE",)).receiver_active
    committed, actions = svc.valid_handoff_trace(spec)
    assert actions[-3:] == ("HANDOFF_COMMIT", "SENDER_TERMINATE", "RECEIVER_ACTIVATE")
    assert committed.public_commit and committed.commit_count == 1
    assert committed.sender_terminated and committed.receiver_active
    assert svc.handoff_transition(committed, "HANDOFF_COMMIT", spec) == committed


def test_deterministic_compact_sorted_json_and_separate_terminals() -> None:
    first = svc.raw_json()
    second = svc.raw_json()
    assert first == second
    assert ": " not in first and ", " not in first
    report = json.loads(first)
    assert first == json.dumps(report, sort_keys=True, separators=(",", ":"))
    assert report["raw_output_binding"] == svc.RAW_OUTPUT_BINDING
    assert report["conclusion"] == {
        "exactly_once_handoff_safety_holds_in_fixed_synthetic_instance": True,
        "finite_support_lookup_conformance_holds_in_fixed_synthetic_instance": True,
    }
    assert report["census"]["opportunities"] == 93_312
    assert report["grid"]["cell_count"] == 243
    assert len(report["grid"]["cell_keys"]) == 243


def test_source_scope_active_line_limit_and_no_forbidden_runtime_interfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    active = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert len(active) <= 500
    tree = ast.parse(text)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imports <= {"__future__", "json", "collections", "dataclasses", "fractions", "itertools", "typing"}
    registry_source = inspect.getsource(svc.build_registry)
    assert all(term not in registry_source for term in ("reward", "future", "recurrent", "partner", "label", "outcome"))
    assert "torch" not in text and "tensorflow" not in text and "production" not in text.lower()


def test_code_science_index_contains_one_full_exact_raw_output_block() -> None:
    text = INDEX.read_text(encoding="utf-8")
    begin = "<!-- FULL_RAW_JSON_BEGIN -->"
    end = "<!-- FULL_RAW_JSON_END -->"
    assert text.count(begin) == text.count(end) == 1
    pattern = re.compile(
        re.escape(begin) + r"\n```json\n([^\n]+)\n```\n" + re.escape(end)
    )
    matches = pattern.findall(text)
    assert len(matches) == 1
    assert matches[0] == svc.raw_json()
    assert svc.RAW_OUTPUT_BINDING in text
    assert "experiments/candidates/vsp_05/semantic_veto_census.py" in text
    assert "tests/experiments/candidates/vsp_05/test_semantic_veto_census.py" in text
    assert "MLP was not run" in text
