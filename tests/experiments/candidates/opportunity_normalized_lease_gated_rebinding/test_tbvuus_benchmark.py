from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "tools" / "benchmarks" / "benchmark_onlgr_tbvuus_r03_cpp_backend.py"


def _load():
    spec = importlib.util.spec_from_file_location("tbvuus_benchmark", BENCHMARK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".cpp", ".h"}
    }


def test_fixture_only_efficiency_review_schema_and_no_sensitive_output(tmp_path: Path) -> None:
    benchmark = _load()
    before = _tree_hashes(ROOT / "experiments" / "candidates" / "opportunity_normalized_lease_gated_rebinding")
    result = benchmark.run_benchmark(repetitions=1, temp_root=tmp_path / "temporary")
    after = _tree_hashes(ROOT / "experiments" / "candidates" / "opportunity_normalized_lease_gated_rebinding")

    assert before == after
    assert result["schema"] == "ONLGR_TBVUUS_R03_EFFICIENCY_REVIEW_V1"
    assert result["command"]["batch_widths"] == [1, 8, 32]
    assert result["command"]["fixture_only"] is True
    assert result["command"]["formal_activity"] is False
    assert result["declared_work"] == {"forward_calls": 0, "backward_calls": 0, "training_steps": 0}
    assert [row["batch_width"] for row in result["batched_reset_to_terminal"]] == [1, 8, 32]
    assert all(row["exact_oracle_native_equality"] for row in result["batched_reset_to_terminal"])
    assert all(row["full_reset_to_terminal"] for row in result["batched_reset_to_terminal"])
    assert result["grouped_four_arm_order_equivalent"] is True
    assert result["semantic_equivalence"]["all_widths_exact"] is True
    assert result["semantic_equivalence"]["worker_chunk_equivalent"] is True
    assert result["fixed_synthetic_analysis"]["synthetic_pair_count"] == 128
    assert result["compact_serialization"]["cell_count"] == 512
    assert result["compact_serialization"]["resume_scan_complete"] is True
    assert result["compact_serialization"]["evidence_class"] == "pre_runner_fixture"
    assert result["compact_serialization"]["actual_runner_storage_measured"] is False
    assert result["full_panel_projection"]["ticks"] == 1_966_080
    assert result["full_panel_projection"]["wall_seconds"] is not None
    assert result["full_panel_projection"]["cpu_seconds"] is not None
    assert result["component_identity"]["component"] == "onlgr_tbvuus_r03_cpp_backend"
    assert len(result["component_identity"]["native_source_sha256"]) == 64
    assert result["component_identity"]["abi"]["abi_version"] == 1
    assert result["component_identity"]["shared_component"]["full_reset_step_cpp"] is True
    assert result["row_set_verification"]["row_count"] == 7_936_000
    assert result["row_set_verification"]["matches_fixed_digest"] is True
    assert result["row_set_verification"]["enumerated_once"] is True
    assert result["fixture_counter_materialization"]["full_row_count"] == 7_936_000
    assert result["fixture_counter_materialization"]["formula"] == "sha256_counter_box_muller_pair"
    assert result["fixture_counter_materialization"]["input_row_length_min_bytes"] > 33
    assert (
        result["fixture_counter_materialization"]["input_row_length_max_bytes"]
        >= result["fixture_counter_materialization"]["input_row_length_min_bytes"]
    )
    assert result["fixture_runner_chain"]["fixture_root_outside_artifacts"] is True
    assert result["fixture_runner_chain"]["native_calls"] == 5
    assert result["fixture_runner_chain"]["native_widths"] == [32] * 5
    assert result["fixture_runner_chain"]["resume_without_native_call"] is True
    assert result["fixture_runner_chain"]["storage_bytes"]["sidecars"] > 0
    assert result["fixture_runner_chain"]["storage_bytes"]["cells"] > 0
    assert result["fixture_runner_chain"]["storage_bytes"]["commits"] > 0
    assert result["storage_comparison"]["evidence_class"] == "fixture_runner_pre_run"
    assert result["storage_comparison"]["actual_runner_storage_measured"] is True
    assert result["storage_comparison"]["expected_within_hard_limit"] is True
    assert result["chain_coverage"]["batched_fixture_oracle_native"] is True
    assert result["chain_coverage"]["row_set_verification"] is True
    assert result["chain_coverage"]["fixture_runner"] is True
    assert result["chain_coverage"]["fixture_counter_materialization"] is True
    assert result["full_chain_projection"]["replicates"] == 128
    assert result["full_chain_projection"]["cells"] == 512
    assert result["full_chain_projection"]["native_width32_calls"] == 640
    assert all(result["full_chain_projection"]["thresholds"].values())
    assert result["rollback_evidence"]["python_fallback"] is False
    assert all(item["exercised"] for key, item in result["rollback_evidence"].items() if key != "python_fallback")
    assert result["efficiency_review"]["all_checks_passed"] is True
    assert result["efficiency_review"]["component_efficiency_review"] == "COMPLETE"
    assert result["efficiency_review"]["lease_readiness"] == "READY"
    assert result["efficiency_review"]["dominant_bottleneck"]["component"]
    assert result["efficiency_review"]["scientific_output_exposed"] is False

    encoded = json.dumps(result, sort_keys=True)
    for forbidden in ("namespace", "coordinate", "word", "endpoint", "mean_value", "tail_value", "result_map"):
        assert forbidden not in encoded.lower()


def test_output_is_canonical_and_only_caller_roots_are_mutated(tmp_path: Path) -> None:
    benchmark = _load()
    temp_root = tmp_path / "temporary"
    output = tmp_path / "output" / "review.json"
    temp_root.mkdir()
    result = {
        "schema": "ONLGR_TBVUUS_R03_EFFICIENCY_REVIEW_V1",
        "command": {"fixture_only": True, "formal_activity": False},
        "efficiency_review": {"scientific_output_exposed": False},
    }
    benchmark._write_output(output, result)
    payload = output.read_bytes()
    assert payload == benchmark._canonical(result)
    assert json.loads(payload) == result
    assert not list(temp_root.rglob("*.pending"))
    assert set(path.parts[len(tmp_path.parts)] for path in tmp_path.rglob("*") if path.is_file()) <= {"temporary", "output"}


def test_telemetry_is_nonzero_or_explicitly_unavailable(tmp_path: Path) -> None:
    benchmark = _load()
    telemetry = benchmark._serialization_timing(tmp_path / "fixture-io")
    commit = telemetry["atomic_commit"]
    assert isinstance(commit, dict)
    if commit["telemetry_available"] is True:
        assert int(commit["peak_rss_bytes"]) > 0
        assert int(commit["io_write_bytes"]) > 0
        assert commit["telemetry_error"] is None
    else:
        assert isinstance(commit["telemetry_error"], str)
        assert commit["telemetry_error"]
        assert benchmark._component_status(
            telemetry_complete=False,
            equivalence_complete=True,
            serialization_complete=True,
        ) == "REPAIR_REQUIRED"
    if os.name == "nt":
        assert commit["telemetry_available"] is True or isinstance(commit["telemetry_error"], str)


def test_component_status_requires_telemetry_and_equivalence() -> None:
    benchmark = _load()
    assert benchmark._component_status(
        telemetry_complete=True,
        equivalence_complete=True,
        serialization_complete=True,
    ) == "COMPLETE"
    assert benchmark._component_status(
        telemetry_complete=False,
        equivalence_complete=True,
        serialization_complete=True,
    ) == "REPAIR_REQUIRED"
    assert benchmark._component_status(
        telemetry_complete=True,
        equivalence_complete=False,
        serialization_complete=True,
    ) == "REPAIR_REQUIRED"
    assert benchmark._component_status(
        telemetry_complete=True,
        equivalence_complete=True,
        serialization_complete=True,
        fixture_runner_complete=False,
    ) == "REPAIR_REQUIRED"
    assert benchmark._component_status(
        telemetry_complete=True,
        equivalence_complete=True,
        serialization_complete=True,
        thresholds_complete=False,
    ) == "REPAIR_REQUIRED"
