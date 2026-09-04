from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_PATH = ROOT / "tools" / "benchmarks" / "benchmark_sgsp_rscf_gate_a.py"


def _benchmark():
    spec = importlib.util.spec_from_file_location("sgsp_rscf_gate_a_benchmark", BENCHMARK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _api():
    from experiments.candidates.semantic_graphon_shared_policy_rscf_gate_a import (
        ABI_TAG,
        CONCURRENCY_LEVELS,
        NATIVE_THREADS,
        SUPPORTED_WIDTHS,
        make_fixture_batch,
        python_suffix_batch,
        validate_fixture_batch,
    )
    return ABI_TAG, CONCURRENCY_LEVELS, NATIVE_THREADS, SUPPORTED_WIDTHS, make_fixture_batch, python_suffix_batch, validate_fixture_batch


def test_public_contract_is_fixed_test_only_surface() -> None:
    abi_tag, concurrencies, native_threads, widths, make_batch, _, validate = _api()
    assert abi_tag == "SGSP_RSCF_NATIVE_ABI_V1"
    assert widths == (32, 64, 128, 256)
    assert concurrencies == (1, 2, 4)
    assert native_threads == 1
    batch = make_batch(32)
    validate(batch, 32)


@pytest.mark.parametrize("width", (32, 64, 128, 256))
def test_fixture_oracle_is_deterministic_at_every_width(width: int) -> None:
    _, _, _, _, make_batch, oracle, validate = _api()
    first = make_batch(width, case_offset=17)
    second = make_batch(width, case_offset=17)
    validate(first, width)
    assert all(np.array_equal(first[name], second[name]) for name in sorted(first))
    first_result = oracle(first)
    second_result = oracle(second)
    assert all(np.array_equal(first_result[name], second_result[name]) for name in sorted(first_result))


def test_fixture_contract_fails_closed_for_malformed_arrays() -> None:
    _, _, _, _, make_batch, _, validate = _api()
    batch = make_batch(32)
    malformed = {name: value.copy() for name, value in batch.items()}
    malformed["n_agents"] = malformed["n_agents"].astype(np.int64)
    with pytest.raises(ValueError, match="dtype"):
        validate(malformed)
    malformed = {name: value.copy() for name, value in batch.items()}
    malformed["roles"] = np.asfortranarray(malformed["roles"])
    with pytest.raises(ValueError, match="C-contiguous"):
        validate(malformed)
    malformed = {name: value.copy() for name, value in batch.items()}
    malformed["forced_action"][0] = 4
    with pytest.raises(ValueError, match="illegal"):
        validate(malformed)


@pytest.mark.parametrize("width", (32, 64, 128, 256))
def test_native_exactly_matches_oracle_at_every_width(width: int) -> None:
    _, _, _, _, make_batch, oracle, _ = _api()
    from experiments.candidates.semantic_graphon_shared_policy_rscf_gate_a.native_loader import (
        load_native_host,
        native_suffix_batch,
    )
    benchmark = _benchmark()
    load_native_host()
    batch = make_batch(width, case_offset=width)
    assert benchmark.exact_outputs(oracle(batch), native_suffix_batch(batch))


def test_native_identity_is_source_keyed_and_thread_fenced() -> None:
    abi_tag, _, native_threads, _, _, _, _ = _api()
    from experiments.candidates.semantic_graphon_shared_policy_rscf_gate_a.native_loader import (
        load_native_host,
        native_identity,
    )
    load_native_host()
    identity = native_identity()
    assert identity["abi_tag"] == abi_tag
    assert identity["native_threads"] == native_threads
    assert identity.get("source_sha256") or identity.get("source_key")


def test_benchmark_schema_and_exact_matrix(tmp_path: Path) -> None:
    benchmark = _benchmark()
    report = benchmark.run_benchmark(measured_pairs=5, warmup_pairs=1)
    assert report["schema"] == benchmark.SCHEMA
    assert report["test_class"] == benchmark.TEST_CLASS
    assert report["formal_activity"] is False
    assert report["supported_widths"] == [32, 64, 128, 256]
    assert report["concurrency_levels"] == [1, 2, 4]
    assert [row["width"] for row in report["warm_width_matrix"]] == [32, 64, 128, 256]
    assert {(row["width"], row["concurrency"]) for row in report["concurrency_matrix"]} == {
        (width, concurrency) for width in (32, 64, 128, 256) for concurrency in (1, 2, 4)
    }
    assert all(row["exact_output_identity"] for row in report["warm_width_matrix"])
    assert all(row["exact_output_identity"] for row in report["concurrency_matrix"])
    assert report["resources"]["telemetry_available"] is True
    assert isinstance(report["resources"]["peak_rss_bytes"], int)
    assert report["resources"]["peak_rss_bytes"] > 0
    assert report["acceptance"]["resource_telemetry_available"] is True
    output = tmp_path / "report.json"
    benchmark.write_report(output, report)
    assert output.read_bytes() == benchmark._canonical_json(report)
    assert json.loads(output.read_bytes()) == report


def test_benchmark_rejects_insufficient_pairs() -> None:
    benchmark = _benchmark()
    with pytest.raises(ValueError, match=">= 5"):
        benchmark.run_benchmark(measured_pairs=4)


def test_acceptance_requires_every_width_to_hit_threshold() -> None:
    benchmark = _benchmark()
    rows = [
        {"exact_output_identity": True, "accepted": True},
        {"exact_output_identity": True, "accepted": False},
    ]
    concurrency = [{"exact_output_identity": True}]
    assert benchmark.acceptance_from_rows(rows, concurrency)["accepted"] is False
    assert benchmark.acceptance_from_rows([rows[0]], [{"exact_output_identity": False}])["accepted"] is False
    assert benchmark.REQUIRED_SPEEDUP == 2.0


def test_report_is_structural_only_and_exposes_rollback_nodes() -> None:
    benchmark = _benchmark()
    report = benchmark.run_benchmark(measured_pairs=5, warmup_pairs=1)
    encoded = json.dumps(report, sort_keys=True).lower()
    for forbidden in ("coordinate", "checkpoint", "endpoint", "rollout", "inference", "r03", "cca", "production"):
        assert forbidden not in encoded
    assert all(node["exercised"] for node in report["rollback_nodes"])
    assert report["acceptance"]["exact_equivalence_all_widths"] is True
