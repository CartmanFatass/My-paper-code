"""Fixture-only efficiency review for the ONLGR TBVUUS r03 C++ host.

This harness deliberately exercises only explicit conformance fixtures.  It
does not materialize a run identity, invoke a runner, or expose any scientific
output.  The JSON it emits is a compact engineering review, rather than a
retained experiment artifact.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
import ctypes
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time
from typing import Any, Callable, Iterator, TypeVar


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (  # noqa: E402
    Arm,
    EncounterSpec,
    FixtureCase,
    FixtureTape,
    RouteClass,
    run_native_batch,
    run_reference_batch,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (  # noqa: E402
    native_backend as native,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.analysis import (  # noqa: E402
    ReplicateEndpoints,
    full_panel_inference,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.coordinates import (  # noqa: E402
    coordinate_row_count,
    coordinate_rows_sha256,
    iter_coordinate_rows,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.contracts import (  # noqa: E402
    ARMS,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.production import (  # noqa: E402
    EXPECTED_STORAGE_BYTES,
    MAX_RAM_BYTES,
    MAX_STORAGE_BYTES,
    PRODUCTION_BATCH_WIDTH,
    live_source_identity,
    run_fixture_benchmark,
)
from envs.native.production_backend import (  # noqa: E402
    ONLGR_TBVUUS_R03_FULL_HOST,
    require_cpp_batched_production,
)


SCHEMA = "ONLGR_TBVUUS_R03_EFFICIENCY_REVIEW_V1"
WIDTHS = (1, 8, 32)
FULL_PANEL_TICKS = 1_966_080
FULL_ROW_COUNT = 7_936_000
EXPECTED_ROW_SET_SHA256 = "bed53eed62ba7bb4afc3e789779861c9f565766fe6fde42d7a3a55793578e01a"
FIXTURE_COUNTER_PREFIX = b"ONLGR-TBVUUS-R03-FIXTURE-BENCHMARK\0"
FIXTURE_ROW_NAMESPACE = b"ONLGR-TBVUUS-R03-FIXTURE-BENCHMARK"
SYNTHETIC_SAMPLE_ROWS = 8_192
_FIXTURE_LAYOUT = (
    (RouteClass.SHORT, 1, 8),
    (RouteClass.SHORT, -1, -8),
    (RouteClass.SHORT, -1, 8),
    (RouteClass.SHORT, 1, -8),
)
T = TypeVar("T")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _process_snapshot() -> dict[str, int | bool | str | None]:
    """Return best-effort process memory and I/O counters without dependencies."""

    result: dict[str, int | bool | str | None] = {
        "available": True,
        "error": None,
        "rss_bytes": 0,
        "peak_rss_bytes": 0,
        "read_bytes": 0,
        "write_bytes": 0,
    }
    if os.name == "nt":
        try:
            from ctypes import wintypes

            class _ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("page_fault_count", wintypes.DWORD),
                    ("peak_working_set_size", ctypes.c_size_t),
                    ("working_set_size", ctypes.c_size_t),
                    ("quota_peak_paged_pool_usage", ctypes.c_size_t),
                    ("quota_paged_pool_usage", ctypes.c_size_t),
                    ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
                    ("quota_non_paged_pool_usage", ctypes.c_size_t),
                    ("pagefile_usage", ctypes.c_size_t),
                    ("peak_pagefile_usage", ctypes.c_size_t),
                ]

            class _IoCounters(ctypes.Structure):
                _fields_ = [
                    ("read_operation_count", ctypes.c_ulonglong),
                    ("write_operation_count", ctypes.c_ulonglong),
                    ("other_operation_count", ctypes.c_ulonglong),
                    ("read_transfer_count", ctypes.c_ulonglong),
                    ("write_transfer_count", ctypes.c_ulonglong),
                    ("other_transfer_count", ctypes.c_ulonglong),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(_ProcessMemoryCounters),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel32.GetProcessIoCounters.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(_IoCounters),
            ]
            kernel32.GetProcessIoCounters.restype = wintypes.BOOL
            handle = kernel32.GetCurrentProcess()
            memory = _ProcessMemoryCounters()
            memory.cb = ctypes.sizeof(memory)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
            result["rss_bytes"] = int(memory.working_set_size)
            result["peak_rss_bytes"] = int(memory.peak_working_set_size)
            if result["rss_bytes"] <= 0 or result["peak_rss_bytes"] <= 0:
                raise RuntimeError("GetProcessMemoryInfo returned a zero working-set counter")
            io = _IoCounters()
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
                raise OSError(ctypes.get_last_error(), "GetProcessIoCounters")
            result["read_bytes"] = int(io.read_transfer_count)
            result["write_bytes"] = int(io.write_transfer_count)
            return result
        except Exception as exc:
            result["available"] = False
            result["error"] = f"windows_telemetry_unavailable:{type(exc).__name__}:{exc}"
            return result
    try:
        import resource

        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result["peak_rss_bytes"] = peak * (1 if sys.platform == "darwin" else 1024)
        result["rss_bytes"] = result["peak_rss_bytes"]
    except Exception as exc:
        result["available"] = False
        result["error"] = f"posix_memory_telemetry_unavailable:{type(exc).__name__}:{exc}"
    try:
        values = {
            key: int(value.split()[0])
            for key, value in (line.split(":", 1) for line in Path("/proc/self/io").read_text().splitlines())
        }
        result["read_bytes"] = values.get("read_bytes", 0)
        result["write_bytes"] = values.get("write_bytes", 0)
    except Exception as exc:
        result["available"] = False
        result["error"] = f"posix_io_telemetry_unavailable:{type(exc).__name__}:{exc}"
    return result


def _measure(action: Callable[[], T]) -> tuple[T, dict[str, int | float | bool | str | None]]:
    before = _process_snapshot()
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    value = action()
    wall = time.perf_counter() - wall_start
    cpu = time.process_time() - cpu_start
    after = _process_snapshot()
    telemetry_available = bool(before["available"]) and bool(after["available"])
    errors = tuple(
        str(value)
        for value in (before["error"], after["error"])
        if isinstance(value, str) and value
    )
    return value, {
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "cpu_utilization_fraction": cpu / wall if wall else 0.0,
        "telemetry_available": telemetry_available,
        "telemetry_error": None if telemetry_available else "|".join(errors),
        "peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
        "io_read_bytes": max(0, int(after["read_bytes"]) - int(before["read_bytes"])),
        "io_write_bytes": max(0, int(after["write_bytes"]) - int(before["write_bytes"])),
    }


@contextmanager
def _isolated_native_cache(cache_root: Path) -> Iterator[None]:
    """Point the source-keyed loader at an owned cache and restore it exactly."""

    cache_root = Path(cache_root).resolve()
    original_path = native._artifact_path
    with native._LIBRARY_LOCK:
        original_libraries = dict(native._LOADED_LIBRARIES)
        native._LOADED_LIBRARIES.clear()

    def artifact_path(build_key: str) -> Path:
        return cache_root / build_key / "tbvuus_backend.dll"

    native._artifact_path = artifact_path
    try:
        yield
    finally:
        native._artifact_path = original_path
        with native._LIBRARY_LOCK:
            native._LOADED_LIBRARIES.clear()
            native._LOADED_LIBRARIES.update(original_libraries)


def _fixed_cases(width: int) -> tuple[FixtureCase, ...]:
    if width not in WIDTHS:
        raise ValueError("width must be one of 1, 8, 32")
    rows: list[FixtureCase] = []
    for index in range(width):
        route, direction, lateral = _FIXTURE_LAYOUT[index % len(_FIXTURE_LAYOUT)]
        spec = EncounterSpec(route, direction, lateral)
        tape = FixtureTape.constant(spec, normal=0.0, uniform=0.5)
        rows.append(FixtureCase(spec, tape, Arm(index % 4), f"fixture-{index:02d}"))
    return tuple(rows)


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
        return math.isclose(left, right, rel_tol=2e-14, abs_tol=2e-12)
    if isinstance(left, tuple) and isinstance(right, tuple):
        return len(left) == len(right) and all(_same_value(a, b) for a, b in zip(left, right))
    if is_dataclass(left) and is_dataclass(right) and type(left) is type(right):
        return all(_same_value(getattr(left, field.name), getattr(right, field.name)) for field in fields(left))
    return left == right


def _equivalent(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return len(left) == len(right) and all(_same_value(a, b) for a, b in zip(left, right))


def _run_width(width: int, repetitions: int) -> dict[str, object]:
    cases = _fixed_cases(width)
    oracle_times: list[dict[str, int | float]] = []
    native_times: list[dict[str, int | float]] = []
    exact = True
    terminal = True
    for _ in range(repetitions):
        expected, oracle_measurement = _measure(lambda: run_reference_batch(cases))
        observed, native_measurement = _measure(lambda: run_native_batch(cases))
        oracle_times.append(oracle_measurement)
        native_times.append(native_measurement)
        exact = exact and _equivalent(expected, observed)
        terminal = terminal and all(len(result.ticks) == result.spec.total_ticks for result in observed)
    native_wall = sum(float(item["wall_seconds"]) for item in native_times)
    ticks = sum(case.spec.total_ticks for case in cases) * repetitions
    return {
        "batch_width": width,
        "repetitions": repetitions,
        "ticks": ticks,
        "call_order": ["oracle", "native"],
        "oracle": oracle_times,
        "native": native_times,
        "ticks_per_second": ticks / native_wall if native_wall else 0.0,
        "exact_oracle_native_equality": exact,
        "full_reset_to_terminal": terminal,
    }


def _four_arm_order_check() -> bool:
    cases = _fixed_cases(8)
    grouped = tuple(sorted(cases, key=lambda case: (int(case.arm), case.logical_tag)))
    by_tag = {result.logical_tag: result for result in run_native_batch(cases)}
    grouped_by_tag = {result.logical_tag: result for result in run_native_batch(grouped)}
    return by_tag.keys() == grouped_by_tag.keys() and all(
        _same_value(by_tag[tag], grouped_by_tag[tag]) for tag in by_tag
    )


def _chunk_check() -> bool:
    cases = _fixed_cases(8)
    direct = run_native_batch(cases)
    chunked = tuple(item for start in range(0, len(cases), 4) for item in run_native_batch(cases[start : start + 4]))
    return _equivalent(direct, chunked)


def _analysis_timing() -> dict[str, int | float | bool | str | None]:
    fixed = tuple(ReplicateEndpoints(mean=0.5, tail=0.5) for _ in range(128))
    _, measurement = _measure(lambda: full_panel_inference({arm: fixed for arm in ARMS}))
    return {**measurement, "synthetic_pair_count": 128, "inference_completed": True}


def _atomic_write(path: Path, payload: bytes) -> tuple[int, int]:
    pending = path.with_name(f".{path.name}.pending")
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    scratch = pending.stat().st_size
    os.replace(pending, path)
    return path.stat().st_size, scratch


def _serialization_timing(root: Path) -> dict[str, object]:
    durable = root / "compact-cells"
    durable.mkdir(parents=True, exist_ok=False)
    scratch_peak = 0

    def commit() -> int:
        nonlocal scratch_peak
        total = 0
        for index in range(512):
            payload = _canonical({"complete": True, "fixture": "fixed", "item": index, "schema": "TBVUUS-COMPACT-CELL-V1"})
            retained, scratch = _atomic_write(durable / f"cell-{index:03d}.json", payload)
            total += retained
            scratch_peak = max(scratch_peak, scratch)
        return total

    durable_bytes, commit_measurement = _measure(commit)

    def scan() -> bool:
        rows = sorted(durable.glob("cell-*.json"))
        return len(rows) == 512 and all(json.loads(path.read_bytes()).get("complete") is True for path in rows)

    complete, scan_measurement = _measure(scan)
    return {
        "cell_count": 512,
        "atomic_commit": commit_measurement,
        "resume_scan": scan_measurement,
        "durable_bytes": durable_bytes,
        "scratch_bytes_peak": scratch_peak,
        "resume_scan_complete": complete,
    }


def _row_set_verification() -> dict[str, int | float | bool | str | None]:
    """Enumerate the independent row commitment exactly once in this process."""

    if coordinate_row_count() != FULL_ROW_COUNT:
        raise RuntimeError("row commitment count differs from the fixed complete domain")
    coordinate_rows_sha256.cache_clear()
    digest, measurement = _measure(coordinate_rows_sha256)
    if digest != EXPECTED_ROW_SET_SHA256:
        raise RuntimeError("row commitment digest differs from the fixed complete domain")
    return {
        **measurement,
        "row_count": FULL_ROW_COUNT,
        "sha256": digest,
        "matches_fixed_digest": True,
        "enumerated_once": True,
    }


def _fixture_counter_pair(row: bytes) -> tuple[float, float]:
    digest = hashlib.sha256(FIXTURE_COUNTER_PREFIX + row).digest()
    u1 = (int.from_bytes(digest[:8], "big") + 0.5) / float(1 << 64)
    u2 = (int.from_bytes(digest[8:16], "big") + 0.5) / float(1 << 64)
    radius = math.sqrt(-2.0 * math.log(u1))
    angle = 2.0 * math.pi * u2
    return radius * math.cos(angle), radius * math.sin(angle)


def _fixture_counter_materialization() -> dict[str, int | float | bool | str | None]:
    """Time a bounded SHA-256/Box--Muller fixture computation with no activity edge."""

    def fixture_row(source_row: bytes) -> bytes:
        try:
            _, remainder = source_row.split(b"|", 1)
        except ValueError as exc:
            raise RuntimeError("encoded fixture row lacks its first frame") from exc
        first = str(len(FIXTURE_ROW_NAMESPACE)).encode("ascii") + b":" + FIXTURE_ROW_NAMESPACE
        return first + b"|" + remainder

    sample_rows = tuple(
        fixture_row(row)
        for row in itertools.islice(iter_coordinate_rows(), SYNTHETIC_SAMPLE_ROWS)
    )
    if len(sample_rows) != SYNTHETIC_SAMPLE_ROWS:
        raise RuntimeError("fixture row sample is shorter than its fixed bound")
    row_lengths = tuple(len(row) for row in sample_rows)

    def materialize() -> str:
        proof = hashlib.sha256()
        for row in sample_rows:
            first, second = _fixture_counter_pair(row)
            proof.update(struct.pack(">dd", first, second))
        return proof.hexdigest()

    digest, measurement = _measure(materialize)
    return {
        **measurement,
        "sample_row_count": SYNTHETIC_SAMPLE_ROWS,
        "input_row_length_min_bytes": min(row_lengths),
        "input_row_length_max_bytes": max(row_lengths),
        "formula": "sha256_counter_box_muller_pair",
        "proof_sha256": digest,
        "full_row_count": FULL_ROW_COUNT,
        "projected_wall_seconds": float(measurement["wall_seconds"]) * FULL_ROW_COUNT / SYNTHETIC_SAMPLE_ROWS,
        "projected_cpu_seconds": float(measurement["cpu_seconds"]) * FULL_ROW_COUNT / SYNTHETIC_SAMPLE_ROWS,
    }


def _bytes_under(root: Path, relative: str) -> int:
    base = root / relative
    return sum(path.stat().st_size for path in base.rglob("*") if path.is_file()) if base.exists() else 0


def _fixture_runner_chain(root: Path) -> dict[str, object]:
    """Exercise the real fixture seam, retaining only engineering facts."""

    fixture_root = (Path(root) / "fixture-runner").resolve()
    artifact_root = (ROOT / "artifacts").resolve()
    try:
        fixture_root.relative_to(artifact_root)
    except ValueError:
        outside_artifacts = True
    else:
        outside_artifacts = False
    if not outside_artifacts:
        raise RuntimeError("fixture root escaped its temporary root")
    native_measurements: list[dict[str, int | float | bool | str | None]] = []

    def timed_native(cases: object) -> object:
        observed, measurement = _measure(lambda: run_native_batch(cases))
        native_measurements.append(measurement)
        return observed

    initial, initial_measurement = _measure(
        lambda: run_fixture_benchmark(fixture_root, native_runner=timed_native)
    )
    resumed, resume_measurement = _measure(lambda: run_fixture_benchmark(fixture_root))
    if not isinstance(initial, dict) or not isinstance(resumed, dict):
        raise RuntimeError("fixture runner emitted an invalid engineering record")
    if initial.get("native_calls") != 5 or initial.get("native_call_widths") != [32] * 5:
        raise RuntimeError("fixture runner did not retain five width-32 native calls")
    if resumed.get("resume_only") is not True or resumed.get("native_calls") != 0:
        raise RuntimeError("fixture runner resume changed its native-call boundary")
    if initial.get("committed_cells") != 4 or resumed.get("committed_cells") != 4:
        raise RuntimeError("fixture runner did not retain the exact compact cell set")
    if initial.get("complete_or_result_written") is not False or resumed.get("complete_or_result_written") is not False:
        raise RuntimeError("fixture runner crossed a result boundary")
    analysis_digest = initial.get("analysis_sha256")
    if not isinstance(analysis_digest, str) or len(analysis_digest) != 64:
        raise RuntimeError("fixture runner analysis digest is invalid")
    sidecar_bytes = _bytes_under(fixture_root, "private-sidecars")
    cell_bytes = _bytes_under(fixture_root, "private-cells")
    commit_bytes = _bytes_under(fixture_root, "private-commits")
    marker_bytes = (fixture_root / "FIXTURE_BENCHMARK.json").stat().st_size
    durable_bytes = sum(path.stat().st_size for path in fixture_root.rglob("*") if path.is_file())
    return {
        "fixture_root_outside_artifacts": outside_artifacts,
        "initial": initial_measurement,
        "resume": resume_measurement,
        "native_calls": len(native_measurements),
        "native_widths": [PRODUCTION_BATCH_WIDTH] * len(native_measurements),
        "native_measurements": native_measurements,
        "committed_cells": 4,
        "analysis_sha256": analysis_digest,
        "storage_bytes": {
            "sidecars": sidecar_bytes,
            "cells": cell_bytes,
            "commits": commit_bytes,
            "marker": marker_bytes,
            "durable_total": durable_bytes,
        },
        "resume_without_native_call": True,
    }


def _cold_probe(cache_root: Path) -> dict[str, int | float | bool | str | None]:
    with _isolated_native_cache(cache_root):
        _, measurement = _measure(native.require_cpp_batched_backend)
    return {**measurement, "isolated_cache": True}


def _run_cold_subprocess(cache_root: Path) -> dict[str, int | float | bool | str | None]:
    command = [sys.executable, str(Path(__file__).resolve()), "--cold-probe", "--cache-root", str(cache_root)]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError("isolated native cold probe did not complete")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict) or value.get("isolated_cache") is not True:
        raise RuntimeError("isolated native cold probe emitted an invalid record")
    return value


def _telemetry_available(measurement: object) -> bool:
    return isinstance(measurement, dict) and measurement.get("telemetry_available") is True


def _component_status(
    *,
    telemetry_complete: bool,
    equivalence_complete: bool,
    serialization_complete: bool,
    fixture_runner_complete: bool = True,
    row_set_complete: bool = True,
    materialization_complete: bool = True,
    thresholds_complete: bool = True,
) -> str:
    """Return an engineering status without changing any lease decision."""

    if all(
        (
            telemetry_complete,
            equivalence_complete,
            serialization_complete,
            fixture_runner_complete,
            row_set_complete,
            materialization_complete,
            thresholds_complete,
        )
    ):
        return "COMPLETE"
    return "REPAIR_REQUIRED"


def _write_output(path: Path, value: dict[str, object]) -> None:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value)
    pending = path.with_name(f".{path.name}.pending")
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


@contextmanager
def _retained_workspace(*, parent: Path | None) -> Iterator[Path]:
    """Keep an owned Windows loader cache until the interpreter exits.

    A loaded DLL cannot be removed on Windows.  Retaining this fresh directory
    below the caller-provided temporary root is therefore the honest atomic
    behavior; callers may remove it after the owning interpreter has ended.
    """

    yield Path(tempfile.mkdtemp(prefix="onlgr_tbvuus_efficiency_", dir=parent))


def run_benchmark(*, repetitions: int = 1, temp_root: Path | None = None) -> dict[str, object]:
    """Run the bounded, fixture-only engineering review.

    ``temp_root`` is caller-owned.  All temporary compile and serialization
    effects remain below it; no candidate artifact root is opened or written.
    """

    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer")
    parent = None if temp_root is None else Path(temp_root).resolve()
    if parent is not None:
        parent.mkdir(parents=True, exist_ok=True)
    with _retained_workspace(parent=parent) as workspace:
        cold = _run_cold_subprocess(workspace / "cold-cache")
        with _isolated_native_cache(workspace / "cold-cache"):
            _, warm_initial = _measure(native.require_cpp_batched_backend)
            _, warm_reuse = _measure(native.require_cpp_batched_backend)
            widths = [_run_width(width, repetitions) for width in WIDTHS]
            grouped_four_arm = _four_arm_order_check()
            worker_chunk = _chunk_check()
            shared_preflight = require_cpp_batched_production(
                ONLGR_TBVUUS_R03_FULL_HOST,
                backend="cpp",
                batch_width=PRODUCTION_BATCH_WIDTH,
            )
            component_identity = {
                "component": "onlgr_tbvuus_r03_cpp_backend",
                "candidate_source": live_source_identity(),
                "native_source_sha256": native.source_sha256(),
                "native_artifact": native.native_artifact_identity(),
                "abi": native.native_abi_identity(),
                "shared_component": {
                    "component": shared_preflight["component"],
                    "backend": shared_preflight["backend"],
                    "full_reset_step_cpp": shared_preflight["full_reset_step_cpp"],
                    "native": shared_preflight["native"],
                },
            }
        row_set = _row_set_verification()
        materialization = _fixture_counter_materialization()
        with _isolated_native_cache(workspace / "cold-cache"):
            fixture_runner = _fixture_runner_chain(workspace)
        analysis = _analysis_timing()
        serialization = _serialization_timing(workspace)
        selected = next(item for item in widths if item["batch_width"] == 32)
        selected_native = selected["native"]
        assert isinstance(selected_native, list)
        selected_wall = sum(float(item["wall_seconds"]) for item in selected_native)
        selected_cpu = sum(float(item["cpu_seconds"]) for item in selected_native)
        selected_ticks = int(selected["ticks"])
        wall_rate = selected_ticks / selected_wall if selected_wall else 0.0
        cpu_rate = selected_ticks / selected_cpu if selected_cpu else 0.0
        wall_projection = FULL_PANEL_TICKS / wall_rate if wall_rate else None
        cpu_projection = FULL_PANEL_TICKS / cpu_rate if cpu_rate else None
        bottlenecks = {
            "native_reset_to_terminal": sum(
                float(item["wall_seconds"])
                for row in widths
                for item in row["native"]
            ),
            "synthetic_analysis": float(analysis["wall_seconds"]),
            "compact_commit_and_scan": float(serialization["atomic_commit"]["wall_seconds"]) + float(serialization["resume_scan"]["wall_seconds"]),
        }
        dominant = max(bottlenecks, key=bottlenecks.get)
        measurements: list[object] = [
            cold,
            warm_initial,
            warm_reuse,
            row_set,
            materialization,
            analysis,
            serialization["atomic_commit"],
            serialization["resume_scan"],
            fixture_runner["initial"],
            fixture_runner["resume"],
        ]
        measurements.extend(item for row in widths for item in row["oracle"])
        measurements.extend(item for row in widths for item in row["native"])
        measurements.extend(fixture_runner["native_measurements"])
        telemetry_complete = (
            all(_telemetry_available(item) and int(item["peak_rss_bytes"]) > 0 for item in measurements)
            and int(serialization["atomic_commit"]["io_write_bytes"]) > 0
            and int(fixture_runner["initial"]["io_write_bytes"]) > 0
        )
        equivalence_complete = (
            all(bool(row["exact_oracle_native_equality"]) and bool(row["full_reset_to_terminal"]) for row in widths)
            and grouped_four_arm
            and worker_chunk
        )
        serialization_complete = bool(serialization["resume_scan_complete"])
        runner_storage = fixture_runner["storage_bytes"]
        fixture_runner_complete = (
            fixture_runner["fixture_root_outside_artifacts"] is True
            and fixture_runner["native_calls"] == 5
            and fixture_runner["native_widths"] == [32] * 5
            and fixture_runner["committed_cells"] == 4
            and fixture_runner["resume_without_native_call"] is True
            and int(runner_storage["sidecars"]) > 0
            and int(runner_storage["cells"]) > 0
            and int(runner_storage["commits"]) > 0
        )
        row_set_complete = (
            row_set["row_count"] == FULL_ROW_COUNT
            and row_set["sha256"] == EXPECTED_ROW_SET_SHA256
            and row_set["matches_fixed_digest"] is True
            and row_set["enumerated_once"] is True
        )
        materialization_complete = (
            materialization["sample_row_count"] == SYNTHETIC_SAMPLE_ROWS
            and materialization["full_row_count"] == FULL_ROW_COUNT
            and isinstance(materialization["proof_sha256"], str)
            and len(materialization["proof_sha256"]) == 64
        )
        fixture_scale = 128
        fixture_initial = fixture_runner["initial"]
        fixture_resume = fixture_runner["resume"]
        projected_runner_wall = float(fixture_initial["wall_seconds"]) * fixture_scale
        projected_runner_cpu = float(fixture_initial["cpu_seconds"]) * fixture_scale
        projected_resume_wall = float(fixture_resume["wall_seconds"]) * fixture_scale
        projected_resume_cpu = float(fixture_resume["cpu_seconds"]) * fixture_scale
        projected_storage = int(runner_storage["durable_total"]) * fixture_scale
        peak_rss = max(int(item["peak_rss_bytes"]) for item in measurements)
        full_chain_wall = (
            float(row_set["wall_seconds"])
            + float(materialization["projected_wall_seconds"])
            + projected_runner_wall
            + projected_resume_wall
        )
        full_chain_cpu = (
            float(row_set["cpu_seconds"])
            + float(materialization["projected_cpu_seconds"])
            + projected_runner_cpu
            + projected_resume_cpu
        )
        thresholds = {
            "cpu_under_10_hours": full_chain_cpu <= 10 * 60 * 60,
            "wall_under_2_hours": full_chain_wall <= 2 * 60 * 60,
            "rss_within_4_gib": peak_rss <= MAX_RAM_BYTES,
            "storage_within_4_gib": projected_storage <= MAX_STORAGE_BYTES,
        }
        thresholds_complete = all(thresholds.values())
        component_status = _component_status(
            telemetry_complete=telemetry_complete,
            equivalence_complete=equivalence_complete,
            serialization_complete=serialization_complete,
            fixture_runner_complete=fixture_runner_complete,
            row_set_complete=row_set_complete,
            materialization_complete=materialization_complete,
            thresholds_complete=thresholds_complete,
        )
        baseline = next(row for row in widths if row["batch_width"] == 1)
        hard_storage_bytes = MAX_STORAGE_BYTES
        expected_fixture_bytes = int(serialization["durable_bytes"])
        return {
            "schema": SCHEMA,
            "command": {
                "argv": [sys.executable, str(Path(__file__).resolve()), "--repetitions", str(repetitions)],
                "batch_widths": list(WIDTHS),
                "repetitions": repetitions,
                "fixture_only": True,
                "formal_activity": False,
            },
            "declared_work": {
                "forward_calls": 0,
                "backward_calls": 0,
                "training_steps": 0,
            },
            "compile_load": {
                "process_cold": cold,
                "warm_loader_initial": warm_initial,
                "warm_loader_reuse": warm_reuse,
            },
            "component_identity": component_identity,
            "batched_reset_to_terminal": widths,
            "grouped_four_arm_order_equivalent": grouped_four_arm,
            "row_set_verification": row_set,
            "fixture_counter_materialization": materialization,
            "fixture_runner_chain": fixture_runner,
            "fixed_synthetic_analysis": analysis,
            "compact_serialization": {
                **serialization,
                "evidence_class": "pre_runner_fixture",
                "actual_runner_storage_measured": False,
            },
            "chain_coverage": {
                "isolated_cold_compile_load": True,
                "warm_loader_reuse": True,
                "batched_fixture_oracle_native": equivalence_complete,
                "fixed_analysis": True,
                "pre_runner_fixture_atomic_commit_resume": serialization_complete,
                "row_set_verification": row_set_complete,
                "fixture_runner": fixture_runner_complete,
                "fixture_counter_materialization": materialization_complete,
                "telemetry_complete": telemetry_complete,
            },
            "baseline_optimized_summary": {
                "baseline_batch_width": 1,
                "baseline_ticks_per_second": baseline["ticks_per_second"],
                "selected_measured_batch_width": max(widths, key=lambda row: float(row["ticks_per_second"]))["batch_width"],
                "selected_measured_ticks_per_second": max(widths, key=lambda row: float(row["ticks_per_second"]))["ticks_per_second"],
                "selected_vs_baseline_ratio": (
                    float(max(widths, key=lambda row: float(row["ticks_per_second"]))["ticks_per_second"])
                    / float(baseline["ticks_per_second"])
                    if float(baseline["ticks_per_second"])
                    else None
                ),
                "fixed_group_contract": {"batch_width": 32, "native_calls_per_replicate": 5},
            },
            "full_panel_projection": {
                "ticks": FULL_PANEL_TICKS,
                "batch_width": 32,
                "wall_seconds": wall_projection,
                "cpu_seconds": cpu_projection,
            },
            "storage_comparison": {
                "evidence_class": "fixture_runner_pre_run",
                "actual_runner_storage_measured": True,
                "expected_fixture_durable_bytes": expected_fixture_bytes,
                "expected_full_chain_storage_bytes": EXPECTED_STORAGE_BYTES,
                "projected_fixture_runner_storage_bytes": projected_storage,
                "hard_storage_bytes": hard_storage_bytes,
                "expected_within_hard_limit": projected_storage <= hard_storage_bytes,
            },
            "full_chain_projection": {
                "replicates": 128,
                "cells": 512,
                "native_width32_calls": 640,
                "row_set_wall_seconds": row_set["wall_seconds"],
                "materialization_wall_seconds": materialization["projected_wall_seconds"],
                "fixture_runner_wall_seconds": projected_runner_wall,
                "fixture_resume_wall_seconds": projected_resume_wall,
                "wall_seconds": full_chain_wall,
                "cpu_seconds": full_chain_cpu,
                "peak_rss_bytes": peak_rss,
                "storage_bytes": projected_storage,
                "thresholds": thresholds,
            },
            "semantic_equivalence": {
                "all_widths_exact": all(bool(row["exact_oracle_native_equality"]) for row in widths),
                "all_widths_terminal": all(bool(row["full_reset_to_terminal"]) for row in widths),
                "grouped_four_arm_order_equivalent": grouped_four_arm,
                "worker_chunk_equivalent": worker_chunk,
            },
            "rollback_evidence": {
                "batch_width": {"exercised": True, "fallback_width": 1},
                "worker_chunk": {"exercised": worker_chunk, "fallback_chunk": 4},
                "loader_cache": {"exercised": True, "isolated": True},
                "io": {"exercised": bool(serialization["resume_scan_complete"]), "fallback": "resume_scan"},
                "python_fallback": False,
            },
            "efficiency_review": {
                "component_efficiency_review": component_status,
                "lease_readiness": "READY" if component_status == "COMPLETE" else "WITHHOLD",
                "lease_readiness_reason": (
                    "fixture_runner_chain_and_thresholds_complete"
                    if component_status == "COMPLETE"
                    else "fixture_runner_chain_or_threshold_requires_repair"
                ),
                "dominant_bottleneck": {"component": dominant, "wall_seconds": bottlenecks[dominant]},
                "all_checks_passed": component_status == "COMPLETE",
                "scientific_output_exposed": False,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cold-probe", action="store_true")
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    if args.cold_probe:
        if args.cache_root is None:
            parser.error("--cold-probe requires --cache-root")
        print(_canonical(_cold_probe(args.cache_root)).decode("utf-8"), end="")
        return 0
    value = run_benchmark(repetitions=args.repetitions, temp_root=args.temp_root)
    if args.output is not None:
        _write_output(args.output, value)
    print(_canonical(value).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
