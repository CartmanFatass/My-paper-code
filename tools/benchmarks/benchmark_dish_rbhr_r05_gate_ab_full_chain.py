"""Result-blind full Gate-A/Gate-B construction benchmark for DISH r05."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.contracts import fixture_family
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.gate_b import run_gate_b_fixture
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.native_backend import artifact_identity, run_native_batch


class _Counters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _peak_rss() -> int:
    counters = _Counters(); counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
    return int(counters.PeakWorkingSetSize)


def _measure(call):
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    result = call()
    return result, {
        "wall_seconds": time.perf_counter()-wall0,
        "cpu_seconds": time.process_time()-cpu0,
        "peak_rss_bytes": _peak_rss(),
    }


def _worker_unit(index: int) -> dict[str, object]:
    root = Path(tempfile.mkdtemp(prefix=f"dish-rbhr-r05-worker-{index}-"))
    fixtures = fixture_family(32)
    host, host_measurement = _measure(lambda: run_native_batch(fixtures))
    gate, gate_measurement = _measure(lambda: run_gate_b_fixture(root, resamples=512))
    return {
        "index": index,
        "host_digest": hashlib.sha256(repr(host).encode("utf-8")).hexdigest(),
        "gate_branch_count": gate["branch_case_count"],
        "host_measurement": host_measurement,
        "gate_measurement": gate_measurement,
        "resume_bytes": Path(gate["resume_path"]).stat().st_size,
    }


def _worker_sweep(workers: int) -> dict[str, object]:
    wall0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(_worker_unit, range(workers)))
    wall = time.perf_counter()-wall0
    return {
        "workers": workers,
        "wall_seconds": wall,
        "aggregate_child_cpu_seconds": sum(row["host_measurement"]["cpu_seconds"] + row["gate_measurement"]["cpu_seconds"] for row in rows),
        "aggregate_peak_rss_bytes_upper": sum(row["gate_measurement"]["peak_rss_bytes"] for row in rows),
        "all_host_digests_equal": len({row["host_digest"] for row in rows}) == 1,
        "all_branch_counts_complete": all(row["gate_branch_count"] == 15 for row in rows),
        "resume_bytes": sum(row["resume_bytes"] for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="dish-rbhr-r05-gate-b-exact-"))
    identity, loader = _measure(artifact_identity)
    fixtures = fixture_family(32)
    host, host_measurement = _measure(lambda: run_native_batch(fixtures))
    gate_b, gate_b_measurement = _measure(lambda: run_gate_b_fixture(root, resamples=99_999))
    sweeps = [_worker_sweep(workers) for workers in (1, 2, 4, 8)]
    one_wall = sweeps[0]["wall_seconds"]
    for row in sweeps:
        row["effective_speedup_vs_one"] = one_wall / row["wall_seconds"] * row["workers"]
        row["parallel_efficiency"] = row["effective_speedup_vs_one"] / row["workers"]
    selected = max(sweeps, key=lambda row: row["effective_speedup_vs_one"])
    host_tps = 32 * 1200 / host_measurement["wall_seconds"]
    update_wall = float(gate_b["synthetic_update"]["wall_seconds"])
    update_cpu = min(update_wall, gate_b_measurement["cpu_seconds"])
    update_units = 120 * 1024
    tick_equivalents = {"low": 7.86e9, "central": 10.72e9, "high": 26.08e9}
    projection = {}
    speedup = max(1.0, float(selected["effective_speedup_vs_one"]))
    for name, ticks in tick_equivalents.items():
        native_hours = ticks / host_tps / 3600.0
        training_hours = update_wall * update_units / 3600.0
        cpu_hours = update_cpu * update_units / 3600.0 + native_hours
        projection[name] = {
            "native_host_hours_at_measured_width32": native_hours,
            "synthetic_update_scaled_hours": training_hours,
            "cpu_core_hours_before_io_headroom": cpu_hours,
            "wall_hours_at_selected_measured_worker_speedup": (native_hours+training_hours)/speedup,
        }
    resume_bytes = Path(gate_b["resume_path"]).stat().st_size
    checkpoint_generations_at_16_update_cadence = 120 * 64
    projected_resume_write_bytes = resume_bytes * checkpoint_generations_at_16_update_cadence
    payload = {
        "schema": "DISH_RBHR_R05_GATE_AB_FULL_CHAIN_RESULT_BLIND_BENCHMARK_V1",
        "test_only": True,
        "scientific_activity_boundary_fixture_only": True,
        "scientific_master": False,
        "scientific_model_or_checkpoint": False,
        "question_relevant_output": False,
        "native_identity": identity,
        "loader_measurement": loader,
        "native_width32": {
            "measurement": host_measurement,
            "ticks": 32*1200,
            "ticks_per_second": host_tps,
            "result_digest": hashlib.sha256(repr(host).encode("utf-8")).hexdigest(),
        },
        "gate_b_exact": gate_b,
        "gate_b_measurement": gate_b_measurement,
        "worker_sweep": sweeps,
        "selected_worker_count": selected["workers"],
        "selected_effective_speedup": selected["effective_speedup_vs_one"],
        "projection": projection,
        "resume_scenario": {
            "cadence_updates": 16,
            "generations": checkpoint_generations_at_16_update_cadence,
            "single_synthetic_record_bytes": resume_bytes,
            "projected_write_bytes": projected_resume_write_bytes,
            "engineering_scenario_not_frozen_science": True,
        },
        "gpu_measurement": "NOT_AVAILABLE_CPU_HOST",
        "python_environment_fallback": False,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(json.dumps({
        "schema": payload["schema"],
        "output": str(args.output),
        "gate_b_wall_seconds": gate_b_measurement["wall_seconds"],
        "host_ticks_per_second": host_tps,
        "selected_worker_count": payload["selected_worker_count"],
        "selected_effective_speedup": payload["selected_effective_speedup"],
        "central_projection": projection["central"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
