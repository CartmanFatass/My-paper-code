from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "tools" / "benchmarks" / "benchmark_sgsp_rscf_update_audit.py"


def _module():
    spec = importlib.util.spec_from_file_location("sgsp_update154_benchmark", BENCHMARK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_update154_benchmark_is_result_blind_fp32_and_complete() -> None:
    module = _module()
    assert module.SCHEMA == "SGSP_RSCF_R01_UPDATE154_RESULT_BLIND_BENCHMARK_V1"
    assert module.WIDTH == 32
    assert module.OUTER_WORKERS == 1
    assert module.NATIVE_THREADS == 1
    assert module.UPDATE_INDEX_COUNT == 155
    source = BENCHMARK.read_text(encoding="utf-8")
    for required in (
        "require_cpp_batched_production(",
        "python_factual_trajectory",
        "native_factual_trajectory",
        "run_test_update(fixture_update_index=154",
        '"max_probability_abs_error"',
        '"projected_complete_wall_seconds"',
        '"peak_observed_rss_bytes"',
        '"dominant_bottleneck"',
    ):
        assert required in source
    for forbidden in (
        "retained_root",
        "master_record",
        "seed_rows",
        "quantity_vector",
        "result_branch",
        "inferential",
    ):
        assert forbidden not in source
