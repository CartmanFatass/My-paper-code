from __future__ import annotations

import hashlib
import json

import pytest

from ha_ctse_process.collectors import (
    DEFAULT_SUBPROC_TRANSPORT,
    SHARED_MEMORY_TRANSPORT,
)
from tools.benchmarks import benchmark_collectors as benchmark


def test_source_fingerprint_covers_runtime_harness_and_default_declaration():
    fingerprint = benchmark._source_fingerprint()
    expected_files = {
        path.as_posix(): hashlib.sha256(
            (benchmark.REPOSITORY_ROOT / path).read_bytes()
        ).hexdigest()
        for path in benchmark.SOURCE_PATHS
    }
    assert fingerprint["files"] == expected_files
    declaration = fingerprint["production_default_declaration"]
    assert declaration["symbol"].endswith("DEFAULT_SUBPROC_TRANSPORT")
    assert declaration["value"] == DEFAULT_SUBPROC_TRANSPORT
    declaration_without_digest = {
        "symbol": declaration["symbol"],
        "value": declaration["value"],
    }
    assert declaration["sha256"] == benchmark._canonical_sha256(
        declaration_without_digest
    )
    assert fingerprint["aggregate_sha256"] == benchmark._canonical_sha256(
        {
            "files": expected_files,
            "production_default_declaration": declaration,
        }
    )


def test_configuration_workload_fingerprint_is_complete_and_stable():
    configuration, workload, fingerprint = benchmark._evidence_context(
        repeats=31,
        iterations=200,
        num_envs=4,
        width=64,
        seed=20260815,
    )
    assert configuration["production_default_under_test"] == SHARED_MEMORY_TRANSPORT
    assert configuration["reference_transport"] == "pipe_pickle"
    assert configuration["optimized_transport"] == "shared_memory_v1"
    assert configuration["warmup_steps"] == 5
    assert configuration["shared_memory_bytes_per_worker"] == 1 << 20
    assert workload == {
        "seed": 20260815,
        "repeats": 31,
        "iterations_per_sample": 200,
        "num_envs": 4,
        "observation_shape_per_env": [8, 64],
        "state_shape_per_env": [128],
        "action_shape_per_env": [8],
        "measured_collector_steps_per_transport": 6200,
    }
    assert fingerprint == benchmark._canonical_sha256(
        {"configuration": configuration, "workload": workload}
    )


@pytest.mark.parametrize("repeats", [1, 30, 32])
def test_benchmark_rejects_small_or_even_sample_counts_before_launch(repeats):
    with pytest.raises(ValueError, match="odd sample count"):
        benchmark.run_benchmark(repeats=repeats)


@pytest.mark.parametrize(
    "semantic,positive,message",
    [
        (False, False, "semantic/RNG equivalence failed"),
        (True, False, "median is non-positive"),
    ],
)
def test_acceptance_is_unconditionally_fail_closed(semantic, positive, message):
    result = {
        "semantic_rng_equivalence": semantic,
        "shared_memory_positive_median": positive,
    }
    with pytest.raises(RuntimeError, match=message):
        benchmark._enforce_acceptance(result)


def test_production_default_is_the_optimized_transport_under_test():
    assert DEFAULT_SUBPROC_TRANSPORT == SHARED_MEMORY_TRANSPORT


def test_retained_result_is_bound_to_current_source_and_authoritative_workload():
    result_path = (
        benchmark.REPOSITORY_ROOT
        / "docs/benchmarks/shared_infrastructure_audit_20260815/collectors.json"
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["source_fingerprint"] == benchmark._source_fingerprint()
    assert result["production_default_under_test"] == DEFAULT_SUBPROC_TRANSPORT
    assert result["configuration"]["production_default_under_test"] == (
        DEFAULT_SUBPROC_TRANSPORT
    )
    assert result["workload"] == {
        "seed": 20260815,
        "repeats": 31,
        "iterations_per_sample": 200,
        "num_envs": 4,
        "observation_shape_per_env": [8, 64],
        "state_shape_per_env": [128],
        "action_shape_per_env": [8],
        "measured_collector_steps_per_transport": 6200,
    }
    assert result["configuration_workload_sha256"] == benchmark._canonical_sha256(
        {
            "configuration": result["configuration"],
            "workload": result["workload"],
        }
    )
    assert result["semantic_rng_equivalence"] is True
    assert result["shared_memory_positive_median"] is True
    assert result["shared_memory_v1_median_seconds"] < (
        result["pipe_pickle_median_seconds"]
    )
