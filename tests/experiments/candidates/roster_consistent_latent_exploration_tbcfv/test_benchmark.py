from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.benchmarks import benchmark_rcle_tbcfv_r04_native as benchmark


def _walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return {str(key).casefold() for key in value} | set().union(
            *(_walk_keys(child) for child in value.values())
        )
    if isinstance(value, list):
        return set().union(*(_walk_keys(child) for child in value)) if value else set()
    return set()


@pytest.fixture(scope="module")
def record(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, object], Path]:
    root = tmp_path_factory.mktemp("fixture_benchmark")
    return benchmark.run_benchmark(repetitions=1, temp_root=root), root


def test_benchmark_emits_canonical_fixture_only_schema(record: tuple[dict[str, object], Path]) -> None:
    value, root = record
    assert value["schema"] == benchmark.SCHEMA
    assert value["fixture_only"] is True
    assert value["formal_activity"] is False
    assert value["scientific_output_exposed"] is False
    assert value["empirical_runner_measured"] is False
    assert value["python_oracle_only"] is True
    assert value["python_fallback"] is False
    assert value["efficiency_review"] in {"COMPLETE", "REPAIR_REQUIRED"}
    assert value["lease_readiness"] == "WITHHOLD"
    destination = root / "canonical.json"
    benchmark._write_output(destination, value)
    assert destination.read_bytes() == benchmark._canonical(value)
    assert json.loads(destination.read_text(encoding="utf-8")) == value


def test_benchmark_covers_widths_equivalence_and_required_chain(record: tuple[dict[str, object], Path]) -> None:
    value, _ = record
    widths = value["batched_reset_to_terminal"]
    assert [row["batch_width"] for row in widths] == [1, 8, 32]
    assert all(row["exact_oracle_native_equality"] for row in widths)
    assert all(row["full_reset_to_terminal"] for row in widths)
    expected_selected = max(
        widths,
        key=lambda row: (row["ticks_per_second"], -row["batch_width"]),
    )
    summary = value["baseline_optimized_summary"]
    assert summary["selected_batch_width"] == expected_selected["batch_width"]
    assert summary["selected_ticks_per_second"] == expected_selected["ticks_per_second"]
    assert summary["selection_rule"] == "maximum measured ticks_per_second; exact ties choose lower batch width"
    equivalence = value["semantic_equivalence"]
    assert equivalence == {
        "all_widths_exact": True,
        "all_widths_terminal": True,
        "scalar_order_exact": True,
        "chunk_order_exact": True,
        "abi2_event_lifecycle_exact": True,
    }
    coverage = value["chain_coverage"]
    for name in ("environment", "abi2_event_lifecycle", "loader", "batch", "forward_backward", "rollout", "evaluation", "io", "resume"):
        assert coverage[name] is True
    assert value["component_identity"]["abi"]["abi_version"] == 2
    assert value["component_identity"]["contract"]["event_time_newcomer_position_input"] is True
    assert value["component_identity"]["contract"]["transport_keys_actor_model_visible"] is False
    assert value["abi2_event_lifecycle"] == {
        "pre_event_observed": True,
        "apply_event_batch_observed": True,
        "stable_transport_alignment": True,
        "model_public_inputs_exclude_transport_keys": True,
    }
    assert value["model_forward_backward"]["stopped_normal_score_path"] is True
    assert value["model_forward_backward"]["flex_path"] is True
    assert value["model_forward_backward"]["episodes"] == 64
    assert value["model_forward_backward"]["agent_decisions"] == 8_192
    assert value["model_forward_backward"]["candidate_scores_per_decision"] == 6
    assert value["model_forward_backward"]["fixed_norm_update_completed"] is True
    assert value["learned_heldout_forward"]["agent_decisions"] == 8_192
    assert value["learned_heldout_forward"]["forward_completed"] is True
    assert value["scripted_consumers"]["outcome_values_exposed"] is False
    assert value["scripted_consumers"]["fixture_repetitions"] == 128
    assert value["scripted_consumers"]["consumer_calls"] == 6_144
    assert value["synthetic_72_tail_analyzer"]["synthetic_tail_count"] == 72
    assert value["synthetic_72_tail_analyzer"]["analyzer_invocations"] == 64
    assert value["synthetic_72_tail_analyzer"]["schema_identity_verified"] is True
    assert value["synthetic_72_tail_analyzer"]["construction_guards_verified"] is True
    assert value["synthetic_72_tail_analyzer"]["interpretation_value_exposed"] is False


def test_telemetry_is_measured_or_explicitly_unavailable(record: tuple[dict[str, object], Path]) -> None:
    value, _ = record
    measurements = [
        value["compile_load"]["process_cold"],
        value["compile_load"]["warm_loader_initial"],
        value["compile_load"]["warm_loader_reuse"],
        value["model_forward_backward"]["measurement"],
        value["learned_heldout_forward"]["measurement"],
        value["atomic_write_resume"]["atomic_write"],
        value["atomic_write_resume"]["resume_scan_restore"],
    ]
    for measurement in measurements:
        assert measurement["wall_seconds"] >= 0.0
        assert measurement["cpu_seconds"] >= 0.0
        if measurement["telemetry_available"]:
            assert measurement["peak_rss_bytes"] > 0
        else:
            assert measurement["telemetry_error"]


def test_result_blind_record_has_no_question_relevant_endpoint_keys(record: tuple[dict[str, object], Path]) -> None:
    value, _ = record
    keys = _walk_keys(value)
    forbidden = {"tau", "u", "f", "y", "return", "returns", "branch", "scientific_branch", "endpoint"}
    assert keys.isdisjoint(forbidden)
    assert value["atomic_write_resume"]["empirical_runner_measured"] is False
    summary = value["baseline_optimized_summary"]
    projection = value["projected_full_panel_cost"]
    assert projection["basis"] and projection["uncertainty"]
    assert projection["frozen_component_counts"] == {
        "learned_arm_run_block_updates": 80_000,
        "learned_heldout_agent_decisions": 262_144_000,
        "scripted_claim_clock_consumer_calls": 15_728_640,
        "native_host_ticks": 495_452_160,
        "analyzer_invocations": 1,
        "atomic_run_blocks": 20,
        "cold_loads_per_worker": 1,
    }
    components = projection["components"]
    assert {component["name"] for component in components} == {
        "cold_load_per_worker",
        f"native_host_width_{summary['selected_batch_width']}",
        "learned_update_forward_backward",
        "learned_heldout_forward",
        "scripted_claim_clock_consumers",
        "synthetic_72_tail_analyzer",
        "atomic_publish_resume",
    }
    assert projection["wall_seconds"]["one_worker"] == pytest.approx(
        sum(component["projected_wall_seconds"] for component in components)
    )
    assert projection["wall_seconds"]["up_to_four_equivalence_supported"]["lower"] <= projection["wall_seconds"]["one_worker"]
    assert value["dominant_projected_component"]["name"] in {component["name"] for component in components}
    assert value["atomic_write_resume"]["run_blocks"] == 20
    assert value["rollback_nodes"]["batch_width"]["selected"] == summary["selected_batch_width"]
    assert value["rollback_nodes"]["batch_width"]["fallback"] == 1
    for component in components:
        if component["multiplier"] > 1.0:
            assert component["cpu_basis_seconds"] > 0.0
            assert component["cpu_basis_kind"] in {"measured", "timer_resolution_upper_bound"}
    scripted_component = next(component for component in components if component["name"] == "scripted_claim_clock_consumers")
    assert scripted_component["cpu_basis_kind"] == "measured"
    assert set(value["rollback_nodes"]) == {"native_backend", "batch_width", "loader_cache", "consumer", "io"}


def test_fixture_writes_stay_under_caller_root(record: tuple[dict[str, object], Path]) -> None:
    _, root = record
    children = tuple(root.iterdir())
    assert children
    assert all(child.resolve().is_relative_to(root.resolve()) for child in children)


def test_repetitions_are_bounded() -> None:
    with pytest.raises(ValueError, match="1..7"):
        benchmark.run_benchmark(repetitions=0)
    with pytest.raises(ValueError, match="1..7"):
        benchmark.run_benchmark(repetitions=8)
