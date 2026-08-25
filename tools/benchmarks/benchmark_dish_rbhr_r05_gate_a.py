"""Result-blind TEST-only Gate-A benchmark for DISH RBHR r05."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.contracts import fixture_family
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.native_backend import (
    artifact_identity,
    generator_scan_native,
    run_native_batch,
)


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _rss() -> int:
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
    return int(counters.PeakWorkingSetSize)


def _measure(call):
    rss_before = _rss()
    cpu_before = time.process_time()
    wall_before = time.perf_counter()
    value = call()
    wall = time.perf_counter() - wall_before
    cpu = time.process_time() - cpu_before
    rss = max(rss_before, _rss())
    return value, {"wall_seconds": wall, "cpu_seconds": cpu, "peak_observed_rss_bytes": rss}


def _cold_identity() -> dict[str, object]:
    root = Path(tempfile.mkdtemp(prefix="dish-rbhr-r05-gate-a-cold-"))
    script = (
        "import json; "
        "from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.native_backend "
        "import artifact_identity; print(json.dumps(artifact_identity(), sort_keys=True))"
    )
    environment = dict(os.environ)
    environment["TEMP"] = str(root)
    environment["TMP"] = str(root)
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[2],
        env=environment, capture_output=True, text=True, check=True,
    )
    wall = time.perf_counter() - started
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    return {"subprocess_wall_seconds": wall, "identity": payload, "isolated_temp_root": str(root)}


def _width_record(width: int, repetitions: int) -> dict[str, object]:
    fixtures = fixture_family(width)
    runs: list[dict[str, object]] = []
    digests: list[str] = []
    for _ in range(repetitions):
        results, measurement = _measure(lambda: run_native_batch(fixtures))
        digest = hashlib.sha256(repr(results).encode("utf-8")).hexdigest()
        digests.append(digest)
        runs.append(measurement)
    best = min(runs, key=lambda row: row["wall_seconds"])
    return {
        "width": width,
        "ticks": width * 1200,
        "runs": runs,
        "all_result_digests_equal": len(set(digests)) == 1,
        "best_ticks_per_second": width * 1200 / float(best["wall_seconds"]),
    }


def _generator_worker_record(workers: int) -> dict[str, object]:
    requests = [
        (0xD15A900000000000 + index, 0, 256, index % 3)
        for index in range(256)
    ]
    def execute():
        chunks = [requests[index::workers] for index in range(workers)]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(generator_scan_native, chunks))
        merged = [item for part in parts for item in part]
        return sorted(merged, key=lambda item: (-1 if item[0] is None else item[0], item[1]))
    results, measurement = _measure(execute)
    return {
        "workers": workers,
        "requests": len(requests),
        "measurement": measurement,
        "result_digest": hashlib.sha256(repr(results).encode("utf-8")).hexdigest(),
        "requests_per_second": len(requests) / float(measurement["wall_seconds"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    if args.repetitions <= 0:
        raise SystemExit("repetitions must be positive")
    cold = _cold_identity()
    warm, warm_measurement = _measure(artifact_identity)
    widths = [_width_record(width, args.repetitions) for width in (1, 32, 48, 50, 96, 240)]
    workers = [_generator_worker_record(count) for count in (1, 2, 4, 8)]
    # Thread completion order may differ; semantic equivalence is checked by a
    # separate ordered generator test.  Here we require stable request counts
    # and record throughput/resource behavior only.
    payload = {
        "schema": "DISH_RBHR_R05_GATE_A_RESULT_BLIND_BENCHMARK_V1",
        "test_only": True,
        "scientific_activity": False,
        "question_relevant_output": False,
        "cold_load": cold,
        "warm_load": {"identity": warm, "measurement": warm_measurement},
        "native_widths": widths,
        "generator_workers": workers,
        "python_fallback": False,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(json.dumps({
        "schema": payload["schema"],
        "output": None if args.output is None else str(args.output),
        "width_ticks_per_second": {str(row["width"]): row["best_ticks_per_second"] for row in widths},
        "worker_requests_per_second": {str(row["workers"]): row["requests_per_second"] for row in workers},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
