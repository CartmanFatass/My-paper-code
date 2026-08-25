"""TEST-only Gate A benchmark for the SGSP RSCF C++17 suffix host.

The benchmark deliberately compares a materialized fixture oracle with the
source-keyed native host.  It is an engineering check, not a runner and not an
activity surface.  It writes a canonical JSON report only to an explicitly
requested path.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any, Callable

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.semantic_graphon_shared_policy_rscf_gate_a import (
    ABI_TAG,
    CONCURRENCY_LEVELS,
    NATIVE_THREADS,
    SUPPORTED_WIDTHS,
    make_fixture_batch,
    python_suffix_batch,
    validate_fixture_batch,
)


SCHEMA = "SGSP_RSCF_GATE_A_NATIVE_HOST_BENCHMARK_V1"
TEST_CLASS = "TEST_ONLY_GATE_A"
MINIMUM_PAIRS = 5
DEFAULT_WARMUP_PAIRS = 3
REQUIRED_SPEEDUP = 2.0


def _native_functions() -> tuple[Callable[[], Any], Callable[[dict[str, np.ndarray]], dict[str, np.ndarray]], Callable[[], dict[str, Any]]]:
    """Import the native boundary only when a benchmark actually runs."""
    from experiments.candidates.semantic_graphon_shared_policy_rscf_gate_a.native_loader import (
        load_native_host,
        native_identity,
        native_suffix_batch,
    )

    return load_native_host, native_suffix_batch, native_identity


def _canonical_output(value: dict[str, np.ndarray]) -> tuple[tuple[str, str, tuple[int, ...], bytes], ...]:
    if not isinstance(value, dict):
        raise TypeError("suffix output must be a dict")
    rows: list[tuple[str, str, tuple[int, ...], bytes]] = []
    for name in sorted(value):
        array = value[name]
        if not isinstance(array, np.ndarray):
            raise TypeError(f"suffix output {name} is not an ndarray")
        contiguous = np.ascontiguousarray(array)
        rows.append((name, contiguous.dtype.str, tuple(contiguous.shape), contiguous.tobytes()))
    return tuple(rows)


def exact_outputs(left: dict[str, np.ndarray], right: dict[str, np.ndarray]) -> bool:
    """Require the complete output key/dtype/shape/value identity."""
    return _canonical_output(left) == _canonical_output(right)


def _rss_bytes() -> int | None:
    """Return this process's working set when the host exposes it."""
    if sys.platform.startswith("win"):
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            ok = psapi.GetProcessMemoryInfo(
                kernel32.GetCurrentProcess(),
                ctypes.byref(counters),
                counters.cb,
            )
        except (AttributeError, OSError):
            return None
        return int(counters.WorkingSetSize) if ok else None
    try:
        import resource  # type: ignore
    except ImportError:
        return None
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _tree_bytes(root: Path | None) -> int | None:
    if root is None or not root.exists():
        return None
    if root.is_file():
        return root.stat().st_size
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _identity_path(identity: dict[str, Any], *names: str) -> Path | None:
    for name in names:
        value = identity.get(name)
        if isinstance(value, str) and value:
            path = Path(value)
            if path.exists():
                return path
    return None


def _source_identity() -> dict[str, Any]:
    relative_paths = (
        "experiments/candidates/semantic_graphon_shared_policy_rscf_gate_a/contract.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_gate_a/fixture_oracle.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_gate_a/native_loader.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_gate_a/native/rscf_gate_a_host.cpp",
        "tools/benchmarks/benchmark_sgsp_rscf_gate_a.py",
    )
    files: dict[str, str] = {}
    digest = hashlib.sha256()
    for relative in relative_paths:
        path = REPOSITORY_ROOT / relative
        if not path.exists():
            raise RuntimeError(f"Gate A source is missing: {relative}")
        payload = path.read_bytes()
        files[relative] = hashlib.sha256(payload).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(payload)
    return {"combined_sha256": digest.hexdigest(), "files": files}


def _time_call(callable_: Callable[[], dict[str, np.ndarray]]) -> tuple[dict[str, np.ndarray], float, float]:
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    result = callable_()
    return result, time.perf_counter() - wall_started, time.process_time() - cpu_started


def _warm_row(
    *,
    width: int,
    measured_pairs: int,
    warmup_pairs: int,
    native_suffix_batch: Callable[[dict[str, np.ndarray]], dict[str, np.ndarray]],
) -> dict[str, Any]:
    batch = make_fixture_batch(width)
    validate_fixture_batch(batch, width)
    reference = python_suffix_batch(batch)
    accelerated = native_suffix_batch(batch)
    if not exact_outputs(reference, accelerated):
        raise RuntimeError(f"native output differs at width {width}")

    for _ in range(warmup_pairs):
        warm_python = python_suffix_batch(batch)
        warm_native = native_suffix_batch(batch)
        if not exact_outputs(warm_python, warm_native):
            raise RuntimeError(f"native warmup differs at width {width}")

    timings: dict[str, list[float]] = {"python": [], "native": []}
    cpu_timings: dict[str, list[float]] = {"python": [], "native": []}
    for pair_index in range(measured_pairs):
        order = (("python", python_suffix_batch), ("native", native_suffix_batch))
        if pair_index % 2:
            order = tuple(reversed(order))
        outputs: dict[str, dict[str, np.ndarray]] = {}
        for name, implementation in order:
            output, wall_seconds, cpu_seconds = _time_call(lambda: implementation(batch))
            outputs[name] = output
            timings[name].append(wall_seconds)
            cpu_timings[name].append(cpu_seconds)
        if not exact_outputs(outputs["python"], outputs["native"]):
            raise RuntimeError(f"native measured output differs at width {width}, pair {pair_index}")

    python_median = float(statistics.median(timings["python"]))
    native_median = float(statistics.median(timings["native"]))
    if native_median <= 0.0:
        raise RuntimeError("native warm median must be positive")
    speedup = python_median / native_median
    return {
        "width": width,
        "fixture_case_offset": 0,
        "warmup_pairs": warmup_pairs,
        "measured_pairs": measured_pairs,
        "alternating_order": True,
        "exact_output_identity": True,
        "python_wall_seconds_per_pair": timings["python"],
        "native_wall_seconds_per_pair": timings["native"],
        "python_cpu_seconds_per_pair": cpu_timings["python"],
        "native_cpu_seconds_per_pair": cpu_timings["native"],
        "python_warm_median_seconds": python_median,
        "native_warm_median_seconds": native_median,
        "paired_warm_speedup": speedup,
        "required_speedup": REQUIRED_SPEEDUP,
        "accepted": speedup >= REQUIRED_SPEEDUP,
    }


def _concurrency_row(
    *,
    width: int,
    concurrency: int,
    native_suffix_batch: Callable[[dict[str, np.ndarray]], dict[str, np.ndarray]],
) -> dict[str, Any]:
    batches = [make_fixture_batch(width, case_offset=(concurrency * 100_000) + worker * width) for worker in range(concurrency)]
    expected = [python_suffix_batch(batch) for batch in batches]
    rss_before = _rss_bytes()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="sgsp-rscf-gate-a") as executor:
        observed = list(executor.map(native_suffix_batch, batches))
    wall_seconds = time.perf_counter() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    exact = all(exact_outputs(reference, native) for reference, native in zip(expected, observed))
    if not exact:
        raise RuntimeError(f"native concurrent output differs at width {width}, concurrency {concurrency}")
    rss_after = _rss_bytes()
    rss_values = [value for value in (rss_before, rss_after) if value is not None]
    return {
        "width": width,
        "concurrency": concurrency,
        "native_threads_per_worker": NATIVE_THREADS,
        "fixture_case_offsets": [(concurrency * 100_000) + worker * width for worker in range(concurrency)],
        "exact_output_identity": True,
        "aggregate_wall_seconds": wall_seconds,
        "aggregate_cpu_seconds": cpu_seconds,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "peak_observed_rss_bytes": max(rss_values) if rss_values else None,
    }


def _rollback_nodes(*, identity: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "node": "fixture_validation",
            "fence": "reject noncanonical input before host entry",
            "exercised": True,
        },
        {
            "node": "abi_source_key",
            "fence": "loader identity carries ABI tag and source key",
            "exercised": bool(identity),
        },
        {
            "node": "exact_oracle",
            "fence": "all output keys/dtypes/shapes/values must match",
            "exercised": True,
        },
        {
            "node": "host_removal",
            "fence": "remove the TEST-only component and its source-keyed build directory; no caller substitution is permitted",
            "exercised": True,
        },
    ]


def acceptance_from_rows(
    warm_rows: list[dict[str, Any]], concurrency_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compute the Gate A gate from complete width and concurrency evidence."""
    all_exact = all(row["exact_output_identity"] for row in warm_rows) and all(
        row["exact_output_identity"] for row in concurrency_rows
    )
    all_fast = all(bool(row["accepted"]) for row in warm_rows)
    return {
        "exact_equivalence_all_widths": all_exact,
        "warm_speedup_requirement": REQUIRED_SPEEDUP,
        "warm_speedup_all_widths": all_fast,
        "accepted": all_exact and all_fast,
    }


def run_benchmark(*, measured_pairs: int = MINIMUM_PAIRS, warmup_pairs: int = DEFAULT_WARMUP_PAIRS) -> dict[str, Any]:
    """Execute the full Gate A width/concurrency matrix and fail closed."""
    if not isinstance(measured_pairs, int) or isinstance(measured_pairs, bool) or measured_pairs < MINIMUM_PAIRS:
        raise ValueError(f"measured_pairs must be an integer >= {MINIMUM_PAIRS}")
    if not isinstance(warmup_pairs, int) or isinstance(warmup_pairs, bool) or warmup_pairs < 1:
        raise ValueError("warmup_pairs must be an integer >= 1")

    load_native_host, native_suffix_batch, native_identity = _native_functions()
    cold_wall_started = time.perf_counter()
    cold_cpu_started = time.process_time()
    load_native_host()
    cold_load_wall = time.perf_counter() - cold_wall_started
    cold_load_cpu = time.process_time() - cold_cpu_started
    identity = dict(native_identity())
    if identity.get("abi_tag") != ABI_TAG:
        raise RuntimeError("native identity ABI tag differs from the fixture contract")
    if identity.get("native_threads") != NATIVE_THREADS:
        raise RuntimeError("native identity does not declare exactly one native thread")

    warm_rows = [
        _warm_row(
            width=width,
            measured_pairs=measured_pairs,
            warmup_pairs=warmup_pairs,
            native_suffix_batch=native_suffix_batch,
        )
        for width in SUPPORTED_WIDTHS
    ]
    concurrency_rows = [
        _concurrency_row(width=width, concurrency=concurrency, native_suffix_batch=native_suffix_batch)
        for width in SUPPORTED_WIDTHS
        for concurrency in CONCURRENCY_LEVELS
    ]
    acceptance = acceptance_from_rows(warm_rows, concurrency_rows)
    resource_telemetry_available = all(
        row["peak_observed_rss_bytes"] is not None for row in concurrency_rows
    )
    acceptance["resource_telemetry_available"] = resource_telemetry_available
    acceptance["accepted"] = bool(acceptance["accepted"] and resource_telemetry_available)
    cache_path = _identity_path(identity, "build_directory", "cache_directory", "build_root", "artifact_path", "artifact")
    source_bytes = _tree_bytes(REPOSITORY_ROOT / "experiments" / "candidates" / "semantic_graphon_shared_policy_rscf_gate_a")
    build_bytes = _tree_bytes(cache_path)
    report_estimate = 0  # Filled after the report has a stable structure.
    report = {
        "schema": SCHEMA,
        "test_class": TEST_CLASS,
        "formal_activity": False,
        "native_threads_per_worker": NATIVE_THREADS,
        "supported_widths": list(SUPPORTED_WIDTHS),
        "concurrency_levels": list(CONCURRENCY_LEVELS),
        "process_cold_load": {
            "wall_seconds": cold_load_wall,
            "cpu_seconds": cold_load_cpu,
            "excluded_from_warm_timings": True,
        },
        "source_identity": _source_identity(),
        "native_identity": identity,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "warm_width_matrix": warm_rows,
        "concurrency_matrix": concurrency_rows,
        "resources": {
            "telemetry_available": resource_telemetry_available,
            "scratch_bytes": build_bytes,
            "retained_source_bytes": source_bytes,
            "retained_build_bytes": build_bytes,
            "retained_report_bytes": report_estimate,
            "peak_rss_bytes": max(
                (row["peak_observed_rss_bytes"] for row in concurrency_rows if row["peak_observed_rss_bytes"] is not None),
                default=_rss_bytes(),
            ),
        },
        "engineering_elapsed_estimate": {
            "observed_cold_load_seconds": cold_load_wall,
            "observed_full_matrix_warm_calls": len(SUPPORTED_WIDTHS) * measured_pairs * 2,
            "observed_concurrency_calls": sum(CONCURRENCY_LEVELS) * len(SUPPORTED_WIDTHS),
            "basis": "measured TEST-only suffix calls; no activity estimate",
        },
        "rollback_nodes": _rollback_nodes(identity=identity),
        "acceptance": acceptance,
    }
    # The byte-count field participates in the canonical payload, so converge
    # it before callers write the report.
    while True:
        encoded = _canonical_json(report)
        encoded_bytes = len(encoded)
        if report["resources"]["retained_report_bytes"] == encoded_bytes:
            break
        report["resources"]["retained_report_bytes"] = encoded_bytes
    return report


def _canonical_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    """Atomically write canonical JSON only to the explicit caller path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(_canonical_json(report))
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--measured-pairs", type=int, default=MINIMUM_PAIRS)
    parser.add_argument("--warmup-pairs", type=int, default=DEFAULT_WARMUP_PAIRS)
    args = parser.parse_args()
    report = run_benchmark(measured_pairs=args.measured_pairs, warmup_pairs=args.warmup_pairs)
    write_report(args.output, report)
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0 if report["acceptance"]["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
