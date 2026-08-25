"""Result-blind TEST-only VQFP r05 numeric/ANALYTIC measurement."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import statistics
import tempfile
import time
from typing import Any, Callable, Iterable, Sequence, TypeVar

from .contracts import (
    ANALYTIC_KINDS,
    ANALYTIC_STATE_COUNT,
    NUMERIC_FUNCTIONS,
    TEST_NAMESPACE,
    WIDTH_LABELS,
    WIDTH_SWEEP,
    WORKER_SWEEP,
)
from .fixtures import (
    analytic_states,
    numeric_batch,
    state_records,
    states_from_records,
    synthetic_chain_fixtures,
)
from .lifecycle import publish_frontier, restore_frontier
from .native_backend import (
    AnalyticResult,
    AnalyticState,
    analytic_result_record,
    artifact_identity,
    numeric_result_record,
    run_numeric_batch,
    solve_analytic_batch,
)


T = TypeVar("T")
FULL_ANALYTIC_SOLVES = 1_572_864
FULL_NUMERIC_CALLS_STATIC_LOWER_BOUND = 1_960_000_000_000


class _ProcessMemoryCountersEx(ctypes.Structure):
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


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


def _process_handle() -> wintypes.HANDLE:
    function = ctypes.windll.kernel32.GetCurrentProcess
    function.restype = wintypes.HANDLE
    return function()


def _rss_bytes() -> int:
    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    function = ctypes.windll.psapi.GetProcessMemoryInfo
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_ProcessMemoryCountersEx),
        wintypes.DWORD,
    )
    function.restype = wintypes.BOOL
    if not function(_process_handle(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def _io() -> tuple[int, int]:
    counters = _IoCounters()
    function = ctypes.windll.kernel32.GetProcessIoCounters
    function.argtypes = (wintypes.HANDLE, ctypes.POINTER(_IoCounters))
    function.restype = wintypes.BOOL
    if not function(_process_handle(), ctypes.byref(counters)):
        raise OSError("GetProcessIoCounters failed")
    return int(counters.ReadTransferCount), int(counters.WriteTransferCount)


def _measure(call: Callable[[], T]) -> tuple[T, dict[str, int | float | bool]]:
    read_before, write_before = _io()
    cpu_before = time.process_time()
    wall_before = time.perf_counter()
    value = call()
    wall = time.perf_counter() - wall_before
    cpu = time.process_time() - cpu_before
    read_after, write_after = _io()
    return value, {
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "peak_rss_bytes": _rss_bytes(),
        "io_read_bytes": max(0, read_after - read_before),
        "io_write_bytes": max(0, write_after - write_before),
        "telemetry_available": True,
    }


def _records_digest(records: Iterable[tuple[object, ...]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        payload = json.dumps(record, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _solve_rows(rows: Sequence[AnalyticState], width: int) -> tuple[tuple[object, ...], ...]:
    output: list[tuple[object, ...]] = []
    for start in range(0, len(rows), width):
        chunk = list(rows[start : start + width])
        valid = len(chunk)
        if valid < width:
            chunk.extend(rows[: width - valid])
        results = solve_analytic_batch(chunk)
        output.extend(analytic_result_record(result) for result in results[:valid])
    return tuple(output)


def _worker_solve(indexed_records: Sequence[tuple[int, tuple[int, ...]]]) -> dict[str, object]:
    rows = states_from_records(record for _, record in indexed_records)
    values, measurement = _measure(lambda: _solve_rows(rows, 128))
    indexed = tuple((index, value) for (index, _), value in zip(indexed_records, values))
    return {"indexed": indexed, "measurement": measurement}


def _run_workers(records: tuple[tuple[int, ...], ...], workers: int) -> dict[str, object]:
    partitions: list[list[tuple[int, tuple[int, ...]]]] = [[] for _ in range(workers)]
    for index, record in enumerate(records):
        partitions[index % workers].append((index, record))
    context = multiprocessing.get_context("spawn")
    started = time.perf_counter()
    if workers == 1:
        returns = [_worker_solve(partitions[0])]
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            returns = list(pool.map(_worker_solve, partitions))
    wall = time.perf_counter() - started
    combined: list[tuple[int, tuple[object, ...]]] = []
    for item in returns:
        combined.extend(item["indexed"])  # type: ignore[arg-type]
    combined.sort(key=lambda item: item[0])
    values = tuple(value for _, value in combined)
    child = [item["measurement"] for item in returns]
    return {
        "workers": workers,
        "wall_seconds": wall,
        "digest": _records_digest(values),
        "rows": len(values),
        "aggregate_child_cpu_seconds": sum(float(row["cpu_seconds"]) for row in child),
        "maximum_child_rss_bytes": max(int(row["peak_rss_bytes"]) for row in child),
        "aggregate_child_io_read_bytes": sum(int(row["io_read_bytes"]) for row in child),
        "aggregate_child_io_write_bytes": sum(int(row["io_write_bytes"]) for row in child),
        "telemetry_available": all(row["telemetry_available"] is True for row in child),
    }


def _quantile(values: Sequence[int], probability: float) -> int:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(probability * len(ordered)) - 1))
    return int(ordered[index])


def _lifecycle_measurement(temp_root: Path) -> dict[str, object]:
    root = temp_root / "TEST_ONLY_FRONTIER"
    payload0 = {
        "namespace": TEST_NAMESPACE,
        "generation": 0,
        "completed_fixture_rows": 2048,
        "scientific_output": False,
        "production_compatible": False,
    }
    payload1 = {
        "namespace": TEST_NAMESPACE,
        "generation": 1,
        "completed_fixture_rows": 4096,
        "scientific_output": False,
        "production_compatible": False,
    }
    commit0, measure0 = _measure(lambda: publish_frontier(root, 0, payload0))
    commit1, measure1 = _measure(lambda: publish_frontier(root, 1, payload1))
    restored, restore_measurement = _measure(lambda: restore_frontier(root))
    if restored["payload"] != payload1:
        raise RuntimeError("TEST-only resume did not restore the exact latest frontier")
    durable = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return {
        "commits": [commit0, commit1],
        "commit_measurements": [measure0, measure1],
        "restore_measurement": restore_measurement,
        "latest_generation": 1,
        "exact_resume": True,
        "durable_bytes": durable,
        "test_only": True,
        "scientific_output": False,
    }


def run_measurement(*, temp_root: Path | None = None) -> dict[str, object]:
    """Execute the one authorized TEST-only measurement object."""

    rows = analytic_states()
    if len(rows) != ANALYTIC_STATE_COUNT:
        raise RuntimeError("analytic fixture cardinality drift")
    chain = synthetic_chain_fixtures()
    if len(chain) != 32 or any(row.namespace != TEST_NAMESPACE for row in chain):
        raise RuntimeError("synthetic chain fixture identity drift")

    native_identity = artifact_identity()

    numeric_widths: list[dict[str, object]] = []
    for width in WIDTH_SWEEP:
        fixtures = numeric_batch(width)
        values, measurement = _measure(lambda fixtures=fixtures: run_numeric_batch(fixtures))
        records = tuple(numeric_result_record(value) for value in values)
        numeric_widths.append(
            {
                "width": WIDTH_LABELS[width],
                "physical_width": width,
                "fixture_rows": width,
                "all_exact": all(record[1] == 1 and record[2] == 1 for record in records),
                "digest": _records_digest(records),
                "certificate_bytes": sum(record[3] for record in records),
                "measurement": measurement,
                "calls_per_wall_second": width / float(measurement["wall_seconds"]),
                "calls_per_cpu_second": (
                    None
                    if float(measurement["cpu_seconds"]) <= 0
                    else width / float(measurement["cpu_seconds"])
                ),
            }
        )

    analytic_widths: list[dict[str, object]] = []
    baseline_records: tuple[tuple[object, ...], ...] | None = None
    for width in WIDTH_SWEEP:
        values, measurement = _measure(lambda width=width: _solve_rows(rows, width))
        if baseline_records is None:
            baseline_records = values
        digest = _records_digest(values)
        analytic_widths.append(
            {
                "width": WIDTH_LABELS[width],
                "physical_width": width,
                "state_rows": len(values),
                "digest": digest,
                "exact_width1_equivalence": values == baseline_records,
                "measurement": measurement,
                "solves_per_wall_second": len(values) / float(measurement["wall_seconds"]),
                "solves_per_cpu_second": (
                    None
                    if float(measurement["cpu_seconds"]) <= 0
                    else len(values) / float(measurement["cpu_seconds"])
                ),
            }
        )
    assert baseline_records is not None
    baseline_digest = _records_digest(baseline_records)

    records = state_records(rows)
    worker_rows = [_run_workers(records, workers) for workers in WORKER_SWEEP]
    for row in worker_rows:
        row["exact_width1_equivalence"] = row["digest"] == baseline_digest

    nodes = [int(record[2]) for record in baseline_records]
    certificate_bytes = [int(record[3]) for record in baseline_records]
    strata: dict[str, dict[str, object]] = {}
    for kind, name in enumerate(ANALYTIC_KINDS):
        selected = [
            baseline_records[index]
            for index, state in enumerate(rows)
            if int(state.kind) == kind
        ]
        strata[name] = {
            "rows": len(selected),
            "node_p50": _quantile([int(value[2]) for value in selected], 0.50),
            "node_p95": _quantile([int(value[2]) for value in selected], 0.95),
            "node_max": max(int(value[2]) for value in selected),
            "certificate_bytes_max": max(int(value[3]) for value in selected),
        }

    numeric_fastest = max(numeric_widths, key=lambda row: float(row["calls_per_wall_second"]))
    analytic_fastest = max(analytic_widths, key=lambda row: float(row["solves_per_wall_second"]))
    analytic_rate = float(analytic_fastest["solves_per_wall_second"])
    numeric_rate = float(numeric_fastest["calls_per_wall_second"])

    parent = Path(tempfile.mkdtemp(prefix="vqfp_r05_test_measurement_", dir=temp_root))
    lifecycle = _lifecycle_measurement(parent)

    all_numeric_exact = all(row["all_exact"] is True for row in numeric_widths)
    all_widths_exact = all(row["exact_width1_equivalence"] is True for row in analytic_widths)
    all_workers_exact = all(row["exact_width1_equivalence"] is True for row in worker_rows)
    fixed_fixture_equivalence = all_numeric_exact and all_widths_exact and all_workers_exact

    report: dict[str, object] = {
        "schema": "VQFP_FERL_R05_TEST_ONLY_NUMERIC_ANALYTIC_MEASUREMENT_V1",
        "namespace": TEST_NAMESPACE,
        "stage": "VQFP-FERL-R05-TEST-ONLY-NUMERIC-ANALYTIC-CERTIFICATE-MEASUREMENT",
        "science_revision": "VQFP-FERL-SCIENCE-20260821-05",
        "test_only": True,
        "result_blind": True,
        "scientific_output": False,
        "production_namespace": False,
        "native_identity": native_identity,
        "fixture_inventory": {
            "numeric_function_families": list(NUMERIC_FUNCTIONS),
            "numeric_base_rows": 21,
            "analytic_states": ANALYTIC_STATE_COUNT,
            "analytic_strata": list(ANALYTIC_KINDS),
            "registered_n": [4, 6, 8, 12],
            "synthetic_chain_rows": len(chain),
            "analyzer_branch_fixture_coverage": sorted({row.analyzer_branch_fixture for row in chain}),
            "widths": [WIDTH_LABELS[width] for width in WIDTH_SWEEP],
            "workers": list(WORKER_SWEEP),
        },
        "numeric_certificate_measurement": {
            "widths": numeric_widths,
            "all_fixed_fixtures_exact": all_numeric_exact,
            "fixed_directed_bracket_checker": True,
            "general_all_input_correct_rounding_proof": False,
            "difficult_case_adaptive_precision_measured": False,
        },
        "analytic_measurement": {
            "widths": analytic_widths,
            "workers": worker_rows,
            "all_widths_exact": all_widths_exact,
            "all_workers_exact": all_workers_exact,
            "node_distribution": {
                "p50": _quantile(nodes, 0.50),
                "p95": _quantile(nodes, 0.95),
                "p99": _quantile(nodes, 0.99),
                "max": max(nodes),
            },
            "certificate_bytes_distribution": {
                "p50": _quantile(certificate_bytes, 0.50),
                "p95": _quantile(certificate_bytes, 0.95),
                "p99": _quantile(certificate_bytes, 0.99),
                "max": max(certificate_bytes),
                "total": sum(certificate_bytes),
            },
            "strata": strata,
            "literal_fixture_solver_checker": True,
            "generic_interval_branch_and_bound_implemented": False,
            "generic_nonconvex_tail_contained": False,
        },
        "synthetic_chain": {
            "rows": [asdict(row) for row in chain],
            "metadata_boundary_complete": True,
            "exact_actor_critic_update_kernel_exercised": False,
            "full_host_reset_to_terminal_exercised": False,
            "complete_180_row_numeric_analyzer_exercised": False,
        },
        "atomic_lifecycle": lifecycle,
        "literal_equivalence": fixed_fixture_equivalence,
        "full_panel_projection": {
            "analytic_solve_count": FULL_ANALYTIC_SOLVES,
            "fixed_archetype_rate_based_wall_seconds": FULL_ANALYTIC_SOLVES / analytic_rate,
            "numeric_call_static_lower_bound": FULL_NUMERIC_CALLS_STATIC_LOWER_BOUND,
            "fixed_table_rate_based_wall_seconds": FULL_NUMERIC_CALLS_STATIC_LOWER_BOUND / numeric_rate,
            "admissible_for_full_r05": False,
            "reason": "fixed proof archetypes and table-bound numeric witnesses do not contain difficult-rounding or generic nonconvex certificate tails",
        },
        "resource_summary": {
            "peak_parent_rss_bytes": _rss_bytes(),
            "maximum_child_rss_bytes": max(int(row["maximum_child_rss_bytes"]) for row in worker_rows),
            "fixture_frontier_durable_bytes": int(lifecycle["durable_bytes"]),
            "numeric_certificate_bytes_max_width": max(int(row["certificate_bytes"]) for row in numeric_widths),
            "analytic_certificate_bytes_total": sum(certificate_bytes),
        },
        "technical_disposition": "UNCONTAINED_NUMERIC_AND_ANALYTIC_GENERALITY_TAIL",
        "technical_reason": (
            "fixed TEST fixtures are literally equal across all required widths/workers, "
            "but the package does not establish an all-input correctly-rounded proof, "
            "generic nonconvex branch-and-bound tail, exact r05 actor/trainer, full host, "
            "or complete binary256 analyzer; rate extrapolation is therefore inadmissible"
        ),
        "science_bearing_ambiguity": "none",
        "question_relevant_output": "none",
        "full_r05_construction_ready": False,
        "local_fence": (
            "TEST-only numeric/analytic fixtures and measurement only; no production "
            "namespace/master/seed/coordinate/model/checkpoint/training/evaluation/result/lease"
        ),
    }
    return report


__all__ = ["run_measurement"]
