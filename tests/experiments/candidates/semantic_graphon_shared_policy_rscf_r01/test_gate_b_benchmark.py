from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_PATH = ROOT / "tools" / "benchmarks" / "benchmark_sgsp_rscf_gate_b.py"


@pytest.fixture(scope="module")
def benchmark_module():
    spec = importlib.util.spec_from_file_location("sgsp_rscf_gate_b_benchmark", BENCHMARK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(width: int, cpu: float, rss: int | None, conformant: bool = True) -> dict[str, object]:
    return {
        "width": width,
        "exact_conformance_digest_equality": conformant,
        "projected_complete_panel_cpu_seconds": cpu,
        "peak_observed_rss_bytes": rss,
    }


def test_benchmark_declares_complete_test_only_matrix_and_abi(benchmark_module) -> None:
    assert benchmark_module.SCHEMA == "SGSP_RSCF_GATE_B_FULL_CHAIN_BENCHMARK_V1"
    assert benchmark_module.SUPPORTED_WIDTHS == (32, 64, 128, 256)
    assert benchmark_module.CONCURRENCY_LEVELS == (1, 2, 4)
    assert benchmark_module.NATIVE_THREADS == 1
    assert benchmark_module.MINIMUM_PAIRS == 3
    source = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert "TEST_ONLY_GATE_B_FULL_CHAIN" in source
    assert "ABI_VERSION" in source
    assert "RSCFGateBRunner" in source


def test_result_blind_selection_minimizes_cpu_then_rss_then_width(benchmark_module) -> None:
    rows = [_row(32, 10.0, 900), _row(64, 8.0, 1100), _row(128, 8.0, 800), _row(256, 8.0, 800)]
    selected = benchmark_module.choose_result_blind_width(rows)
    assert selected["selected_width"] == 128
    assert selected["numeric_target_or_analyzer_values_inspected"] is False
    assert "result_blind" in selected["selection_policy"]


def test_selection_excludes_nonconformant_width_and_requires_candidate(benchmark_module) -> None:
    selected = benchmark_module.choose_result_blind_width([_row(32, 1.0, 1, False), _row(64, 2.0, 2, True)])
    assert selected["selected_width"] == 64
    with pytest.raises(RuntimeError, match="no structurally conformant"):
        benchmark_module.choose_result_blind_width([_row(32, 1.0, 1, False)])


def test_composed_cost_inventory_uses_disjoint_environment_and_update_categories(benchmark_module) -> None:
    measurements = {
        "base_factual_trace_cpu_seconds_per_slot": 0.0,
        "alternative_native_suffix_cpu_seconds_per_slot": 0.0,
        "torch_factual_graph_backward_cpu_seconds_per_update": 0.0,
        "evaluation_trace_cpu_seconds_per_seed": 0.0,
        "frontier_checkpoint_io_cpu_seconds_per_seed": 0.0,
        "analyzer_cpu_seconds_once_per_panel": 0.0,
    }
    inventory = benchmark_module.compose_cost_projection(measurements)["logical_work_inventory"]
    assert inventory["base_rollout_environment_slots"] == 18_874_368
    assert inventory["alternative_suffix_environment_slots"] == 71_565_312
    assert inventory["backward_update_calls"] == 24_576


def test_composed_cost_model_keeps_fixed_terms_outside_environment_multiplier(benchmark_module) -> None:
    measurements = {
        "base_factual_trace_cpu_seconds_per_slot": 1.0,
        "alternative_native_suffix_cpu_seconds_per_slot": 2.0,
        "torch_factual_graph_backward_cpu_seconds_per_update": 3.0,
        "evaluation_trace_cpu_seconds_per_seed": 4.0,
        "frontier_checkpoint_io_cpu_seconds_per_seed": 5.0,
        "analyzer_cpu_seconds_once_per_panel": 6.0,
    }
    projection = benchmark_module.compose_cost_projection(measurements)
    inventory = projection["logical_work_inventory"]
    components = projection["component_cpu_seconds"]
    assert inventory["base_rollout_environment_slots"] == 18_874_368
    assert inventory["alternative_suffix_environment_slots"] == 71_565_312
    assert inventory["frontier_checkpoint_io_seed_count"] == 24
    assert components["frontier_checkpoint_io_per_seed"] == 24 * 5.0
    assert components["evaluation_trace_per_seed"] == 24 * 4.0
    assert components["analyzer_once_per_panel"] == 6.0
    assert projection["total_cpu_seconds"] == pytest.approx(sum(components.values()))
    assert "analyzer_once_per_panel" in projection["fixed_terms_not_multiplied_by_environment_slots"]
    assert all("future" not in name for name in components)


def test_wall_projection_uses_observed_throughput_not_ideal_worker_division(benchmark_module) -> None:
    projected = benchmark_module.project_wall_from_observed_throughput(
        100.0,
        {
            1: {"aggregate_cpu_seconds": 10.0, "aggregate_wall_seconds": 10.0},
            2: {"aggregate_cpu_seconds": 15.0, "aggregate_wall_seconds": 10.0},
            4: {"aggregate_cpu_seconds": 20.0, "aggregate_wall_seconds": 10.0},
        },
    )
    assert projected["ideal_division_used"] is False
    rows = projected["wall_by_observed_worker_throughput"]
    assert rows["1"]["projected_wall_seconds_before_headroom"] == pytest.approx(100.0)
    assert rows["2"]["projected_wall_seconds_before_headroom"] == pytest.approx(100.0 / 1.5)
    assert rows["4"]["projected_wall_seconds_with_headroom"] == pytest.approx(100.0 / 2.0 * 1.25)


def test_source_identity_binds_28_family_clarification_and_benchmark(benchmark_module) -> None:
    identity = benchmark_module._source_identity()
    assert identity["clarification_sha256"] == benchmark_module.SUPPORT_SLACK_CLARIFICATION_SHA256
    assert "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py" in identity["files"]
    assert len(identity["combined_sha256"]) == 64


def test_rollback_nodes_and_schema_cover_lifecycle_resources_and_analyzer(benchmark_module) -> None:
    nodes = benchmark_module._rollback_nodes()
    assert {node["node"] for node in nodes} >= {"test_identity", "native_abi_v3", "atomic_frontier_resume"}
    source = BENCHMARK_PATH.read_text(encoding="utf-8")
    for required in ("run_gate_a_self_check", "frontier", "checkpoint", "evaluation_consumer", "28_family_analyzer", "peak_continuously_sampled_rss_bytes", "retained_source_bytes", "compose_cost_projection"):
        assert required in source
    assert "FAMILY_SIZE" in source and "QUANTITY_NAMES" in source


def test_full_chain_contract_requires_final_64_inventory_durable_resume_and_generated_consumers(benchmark_module) -> None:
    source = BENCHMARK_PATH.read_text(encoding="utf-8")
    for required in (
        "episodes_per_roster=32",
        "len(update.native_targets) == 64",
        "len(update.shared_snapshot_digests) == 192",
        "save_test_checkpoint",
        "restore_test_checkpoint",
        "generate_test_evaluation_panel",
        "all_widths_exact_64_episode_inventory",
        "all_widths_durable_frontier_resume",
        "all_widths_generated_evaluation_consumers",
    ):
        assert required in source


def test_recompute_parent_rejects_tamper_and_source_identity_mismatch(benchmark_module, tmp_path) -> None:
    parent = {"schema": benchmark_module.SCHEMA, "formal_activity": False, "acceptance": {}}
    path = tmp_path / "parent.json"
    path.write_bytes(benchmark_module._canonical_json(parent))
    with pytest.raises(ValueError, match="acceptance"):
        benchmark_module._load_verified_parent_report(path)
    current = {"files": {"runner.py": "a", "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py": "b" * 64}}
    parent_source = {"files": {"runner.py": "tampered", "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py": "b" * 64}}
    with pytest.raises(ValueError, match="source/runner identity mismatch"):
        benchmark_module._verify_parent_source_files(parent_source, current)


def test_v3_cost_categories_are_cpu_provenanced_mutually_exclusive_and_three_sampled(benchmark_module) -> None:
    source = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert benchmark_module.SELECTION_RATE_SAMPLES == 3
    assert "cpu_clock = time.process_time" in source
    assert "wall_started = time.perf_counter" in source
    assert "torch_factual_graph_backward_cpu_seconds_per_update" in source
    assert "gate_a_v3_self_check" in source
    with pytest.raises(ValueError, match="cost measurement schema mismatch"):
        benchmark_module.compose_cost_projection({
            "base_factual_trace_cpu_seconds_per_slot": 0.0,
            "alternative_native_suffix_cpu_seconds_per_slot": 0.0,
            "torch_factual_graph_backward_cpu_seconds_per_update": 0.0,
            "evaluation_trace_cpu_seconds_per_seed": 0.0,
            "frontier_checkpoint_io_cpu_seconds_per_seed": 0.0,
            "analyzer_cpu_seconds_once_per_panel": 0.0,
            "future_learned_seconds_per_decision": 0.0,
        })


def test_v3_self_check_rejects_field_mismatch_and_error_over_tolerance(benchmark_module) -> None:
    native = SimpleNamespace(source_sha256="a", build_key_sha256="b", artifact_sha256="c", artifact_path="d")
    record = {
        "categorical_terminal_digest_exact": True, "three_origins_same_factual_episode": True,
        "factual_suffix_identity": True, "all_nonfactual_legal_actions": True,
        "common_tape_across_actions_and_modes": True, "reverse_order_independence": True,
        "suffix_paired_warm_speedup": 2.0, "factual_trace_paired_warm_speedup": 2.0,
        "intact_float_max_abs_error": 2e-12, "full_rotated_float_max_abs_error": 0.0,
        "shadow_float_max_abs_error": 0.0,
    }
    payload = {"abi_version": benchmark_module.ABI_VERSION, "native_threads": 1,
               "identity": {"source_sha256": "a", "build_key_sha256": "b", "artifact_sha256": "c", "artifact_path": "d"},
               "widths": {str(width): dict(record) for width in benchmark_module.SUPPORTED_WIDTHS},
               "concurrency": {str(worker): {} for worker in benchmark_module.CONCURRENCY_LEVELS}}
    assert benchmark_module._verify_gate_a_self_check(payload, native)["widths"]["32"]["suffix_paired_warm_speedup"] == 2.0
    payload["widths"]["32"]["reverse_order_independence"] = False
    with pytest.raises(RuntimeError, match="categorical/origin"):
        benchmark_module._verify_gate_a_self_check(payload, native)
    payload["widths"]["32"]["reverse_order_independence"] = True
    payload["widths"]["32"]["shadow_float_max_abs_error"] = 2.0001e-12
    with pytest.raises(RuntimeError, match="numerical tolerance"):
        benchmark_module._verify_gate_a_self_check(payload, native)


def test_v3_trace_cache_contract_and_shared_snapshot_digest_inventory_rule(benchmark_module) -> None:
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.runner import RSCFGateBRunner

    benchmark_source = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert "_evaluation_probability_cache" not in benchmark_source
    runner_source = Path(RSCFGateBRunner.__module__.replace(".", "/") + ".py")
    assert "_evaluation_trace_cache" in (ROOT / runner_source).read_text(encoding="utf-8")
    assert "len(set(update.shared_snapshot_digests))" not in benchmark_source
    assert "_selector_origin_identity_keys" in benchmark_source
    assert "len(target.origin_snapshot_sha256) == 3" in benchmark_source
    assert "full_chain_conformance_calls\": 1" in benchmark_source
    assert "selected_width = int(selection[\"selected_width\"])" in benchmark_source
    assert "for workers in CONCURRENCY_LEVELS" in benchmark_source


def test_selector_origin_keys_are_unique_without_unique_world_snapshot_digests(benchmark_module) -> None:
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import TestIdentity
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.selector import generate_test_selector_schedule

    identity = TestIdentity("CASEKEYS")
    schedules = tuple(generate_test_selector_schedule(identity, fixture_update_index=0, roster_size=n) for n in (9, 15))
    keys = benchmark_module._selector_origin_identity_keys(schedules)
    assert len(keys) == 192
    assert len(set(keys)) == 192


def test_measurement_frontier_write_resume_and_identity_tamper_rejection(benchmark_module, tmp_path) -> None:
    identity = {"schema": benchmark_module.SCHEMA, "width": 32, "native": "V3"}
    row = {"width": 32, "exact_conformance_digest_equality": True}
    observed, resumed, path = benchmark_module._frontier_row(tmp_path, "width-32", identity, row)
    assert observed == row and not resumed and path
    reused, resumed, _ = benchmark_module._frontier_row(tmp_path, "width-32", identity, {})
    assert reused == row and resumed
    with pytest.raises(RuntimeError, match="drift/tamper"):
        benchmark_module._frontier_row(tmp_path, "width-32", {**identity, "width": 64}, {})
