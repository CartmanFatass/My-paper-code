from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest

from experiments.candidates.variable_n_fleet_churn import fixed_fh_q0 as q0


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "experiments/candidates/variable_n_fleet_churn/fixed_fh_q0.py"
STAGE_RECORD = (
    ROOT
    / "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_TEPR_FIXED_FH_QUOTIENT_AND_COST_CERTIFICATE_Q0.md"
)
CERTIFICATE = (
    ROOT
    / "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_TEPR_FIXED_FH_Q0_CERTIFICATE.json"
)


def _run_cli() -> bytes:
    return subprocess.run(
        [q0.sys.executable, "-B", str(SOURCE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def test_stage_record_precedes_source_and_is_hash_bound() -> None:
    assert STAGE_RECORD.is_file()
    assert STAGE_RECORD.stat().st_mtime_ns <= SOURCE.stat().st_mtime_ns
    assert q0._sha256(STAGE_RECORD) == "4175838faf0bf3745dac9208806e69f4a579a7042ba67d1f638a2d23bf50be46"
    assert q0.SCIENCE_SHA256 == "8e9e87f0bdc55a691a5232e58c7b022cbc637765c500845fd822bf2e3005f791"


def test_fixture_is_exact_complete_and_contains_required_cases() -> None:
    graph = q0.build_fixture_graph()
    assert len(graph.states) == 16
    assert len(graph.roots) == 8
    for state in graph.states:
        for action in state.actions:
            assert tuple(edge.label for edge in action.edges) == q0.SUCCESSOR_LABELS
            assert sum((edge.probability for edge in action.edges), F(0)) == 1
            assert all(isinstance(edge.probability, F) for edge in action.edges)
    assert any(len(action.bid_sources) > 1 for state in graph.states for action in state.actions)
    assert any(state.x20 and state.x40 and state.x20.command != state.x40.command for state in graph.states)
    assert any(state.x20 and state.x40 and state.x20.command == state.x40.command for state in graph.states)
    assert graph.by_name["terminal_mid_a"].physical_tag == graph.by_name["terminal_unequal_den"].physical_tag
    assert graph.by_name["terminal_mid_a"].d_past != graph.by_name["terminal_unequal_den"].d_past


def test_builder_merges_only_exact_bisimilar_fixture_states() -> None:
    graph = q0.build_fixture_graph()
    partition = q0.build_partition(graph)
    q0.check_partition(graph, partition)
    assert partition["terminal_mid_a"] == partition["terminal_mid_b"]
    assert partition["leaf_equiv_a"] == partition["leaf_equiv_b"]
    assert partition["mid_equiv_a"] == partition["mid_equiv_b"]
    assert partition["root_a"] == partition["root_b"]
    assert partition["leaf_history_a"] != partition["leaf_history_b"]
    assert partition["terminal_mid_a"] != partition["terminal_unequal_den"]


def test_independent_checker_rejects_registered_invalid_merge() -> None:
    graph = q0.build_fixture_graph()
    partition = q0.build_partition(graph)
    left, right = graph.invalid_merge_pair
    invalid = dict(partition)
    invalid[right] = invalid[left]
    with pytest.raises(ValueError, match="local_A_fix_X20_X40_Dpast_ratio_or_tie_signature"):
        q0.check_partition(graph, invalid)


def test_checker_rejects_transition_change_under_existing_partition() -> None:
    graph = q0.build_fixture_graph()
    partition = q0.build_partition(graph)
    states = list(graph.states)
    index = next(i for i, state in enumerate(states) if state.name == "leaf_equiv_b")
    state = states[index]
    action = state.actions[0]
    edges = list(action.edges)
    edges[0] = replace(edges[0], target="terminal_high", delivered_increment=3, demand_increment=4)
    states[index] = replace(state, actions=(replace(action, edges=tuple(edges)),))
    changed = replace(graph, states=tuple(states))
    q0.validate_graph(changed)
    with pytest.raises(ValueError, match="labeled_rational_transition_distribution"):
        q0.check_partition(changed, partition)


def test_reference_and_quotient_agree_exhaustively_h1_h2_h3() -> None:
    graph = q0.build_fixture_graph()
    partition = q0.build_partition(graph)
    result = q0.exhaustive_agreement(graph, partition)
    assert result["horizons"] == [1, 2, 3]
    assert result["agreement_rows"] == result["reachable_state_horizon_rows"]
    assert result["agreement_rows"] > 40
    assert result["tie_rows"] > 0
    assert result["invalid_merge_counterexample"]["quantity"] == "local_A_fix_X20_X40_Dpast_ratio_or_tie_signature"


def test_expectation_of_ratios_and_complete_tie_set_are_preserved() -> None:
    graph = q0.build_fixture_graph()
    partition = q0.build_partition(graph)
    reference = q0.evaluate_reference(graph, "leaf_tie", 1)
    quotient = q0.evaluate_quotient(graph, partition, partition["leaf_tie"], 1)
    assert reference == quotient
    assert reference.maximizing_commands == (q0.CMD_A, q0.CMD_B)
    assert reference.selected_command == q0.CMD_A
    assert reference.value != F(2, 4)  # mixed denominators make ratio-of-sums unsafe


def test_full_query_raw_and_parametric_bounds_are_exact() -> None:
    bounds = q0.full_query_bounds()
    raw = bounds["unquotiented"]
    expected_q = sum(129 ** (depth + 1) * 16**depth for depth in range(6))
    expected_e = sum(129 ** (depth + 1) * 16 ** (depth + 1) for depth in range(5))
    expected_keys = sum((129 * 16) ** depth for depth in range(6))
    assert raw["action_evaluations_one_root"] == expected_q
    assert raw["action_successor_edges_one_root"] == expected_e
    assert raw["reachable_keys_one_root"] == expected_keys
    assert raw["action_evaluations_panel"] == expected_q * 20 * 128
    assert bounds["candidate_generation"] == {
        "rda_calls_per_state": 127,
        "x20_matching_evaluations_per_state": 1961,
        "x40_matching_pair_evaluations_per_state": 1961 * 16 * 1961,
    }
    assert bounds["quotient_parametric"]["reachable_key_counts"].startswith("K_1..K_6")
    assert bounds["rational_bits"]["bellman_denominator_upper"] > 1_000_000
    assert bounds["rational_bits"]["value_allocation_bytes_upper"] > 1_000_000


def test_full_query_bounds_reject_nonpositive_parameters() -> None:
    with pytest.raises(ValueError, match="positive"):
        q0.full_query_bounds(horizon=0)
    with pytest.raises(ValueError, match="positive"):
        q0.full_query_bounds(actions=-1)


def test_cli_is_byte_stable_hash_bound_and_narrow() -> None:
    first = _run_cli()
    second = _run_cli()
    assert first == second
    result = json.loads(first)
    payload = result["payload"]
    assert result["payload_sha256"] == hashlib.sha256(q0._canonical_bytes(payload)).hexdigest()
    assert first == (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert payload["status"] == "Q0_COMPLETE"
    assert payload["bundle"]["finite_completion"] is True
    assert payload["bundle"]["manifest_complete"] is True
    assert payload["bundle"]["science_card_sha256"] == q0.SCIENCE_SHA256
    assert payload["bundle"]["test_sha256"] == q0._sha256(Path(q0.__file__).resolve().parents[3] / payload["bundle"]["test_path"])
    assert payload["fixture"]["nonclaims"] == [
        "full FIXED-FH solver feasibility",
        "empirical host feasibility",
        "learned-arm value",
        "coordinate or panel result",
        "production lease readiness",
        "science-card modification",
    ]
    assert payload["q0_cost"]["engineering_weeks"] == [5, 10]


def test_durable_certificate_is_exact_cli_output() -> None:
    assert CERTIFICATE.read_bytes() == _run_cli()
