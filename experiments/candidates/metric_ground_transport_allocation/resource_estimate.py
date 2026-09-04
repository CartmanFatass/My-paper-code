"""Non-scientific preactivity resource estimator for MGTAP R01.

This module deliberately does not import the registered MGTAP runner, trainer,
evaluation, analysis, RNG, or artifact modules.  It measures hand-written,
deterministic compute and storage fixtures, then scales those measurements by
the workload counts frozen in the current R01 authority.  It never takes an
optimizer step and never materializes a registered scientific address.
"""

from __future__ import annotations

_IMPORT_WALL_STARTED = __import__("time").perf_counter()
_IMPORT_CPU_STARTED = __import__("time").process_time()

import argparse
import ctypes
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import sys
import tempfile
import time
from typing import Callable


for _thread_variable in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "4"

import numpy as np
import torch


SCHEMA_VERSION = 1
ESTIMATOR_REVISION = "MGTAP-R01-PREACTIVITY-RESOURCE-ESTIMATOR-20260827"
AUTHORITY_REFS = {
    "direction": "docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md",
    "successor_authority":
        "docs/research/candidates/metric_ground_transport_allocation/"
        "MGTAP_MATCHED_UPDATE_SUPPORT_SUCCESSOR_SCIENCE_AUTHORITY_R01_20260827.md",
    "resource_handoff":
        "docs/research/candidates/metric_ground_transport_allocation/"
        "MGTAP_MATCHED_UPDATE_SUPPORT_IDENTIFIABILITY_RESOURCE_HANDOFF_20260825.md",
}
SOURCE_RELATIVE_PATH = (
    "experiments/candidates/metric_ground_transport_allocation/resource_estimate.py"
)
TEST_RELATIVE_PATH = (
    "tests/experiments/candidates/metric_ground_transport_allocation/"
    "test_resource_estimate.py"
)
OUTPUT_ROOT = Path(
    "temp/directions/metric_ground_transport_allocation/test"
)

WORKLOAD = {
    "gate_training_units": 24_576,
    "validation_panel_units": 192,
    "conditional_conclusion_training_units": 32_768,
    "conditional_base_plus_replay_units": 64,
    "conditional_packet_writes": 16,
}
WORKLOAD_FORMULAS = {
    "calibration_training_decisions": "4*6*4*256*48*2",
    "validation_decisions": "4*6*4*2*2*12*2*16*2",
    "conclusion_training_decisions": "4*16*512*48*2",
    "base_evaluation_decisions": "4*16*4*12*2*64*2",
    "replay_evaluation_decisions": "4*16*4*12*2*64*2",
}
SOURCE_CAPS = {
    "wall_seconds": 28_800,
    "process_cpu_seconds": 115_200,
    "peak_rss_bytes": 4 * 1024**3,
    "temporary_plus_final_bytes": 8 * 1024**3,
    "scheduling_wall_seconds": 7_200,
}
STATIC_PACKET_BYTES = 110_000_000
STATIC_SIXTEEN_PACKET_BYTES = 1_760_000_000
COMPUTE_UNCERTAINTY_FACTOR = 2.0
STORAGE_TIME_UNCERTAINTY_FACTOR = 1.5
RSS_UNCERTAINTY_FACTOR = 1.5
DISK_UNCERTAINTY_FACTOR = 1.25
SAFE_CAPACITY_FRACTION = 0.5


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_root() -> Path:
    root = Path.cwd().resolve()
    if not (root / "AGENTS.md").is_file():
        raise RuntimeError("run from the saved HMASD repository root")
    return root


def _validate_authority(root: Path) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for label, relative in AUTHORITY_REFS.items():
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"current authority is missing: {label}: {relative}")
        stat = path.stat()
        refs.append({
            "label": label,
            "path": relative,
            "modified_time_ns": str(stat.st_mtime_ns),
            "bytes": str(stat.st_size),
        })
    return refs


def _validated_output(root: Path, output: Path) -> Path:
    if not output.is_absolute():
        raise ValueError("--output must be absolute")
    resolved = output.resolve(strict=False)
    allowed = (root / OUTPUT_ROOT).resolve()
    if allowed not in resolved.parents or resolved.suffix != ".json":
        raise ValueError(f"--output must be a JSON file below {allowed}")
    if resolved.exists():
        raise FileExistsError(resolved)
    temporary = resolved.with_suffix(resolved.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError(temporary)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


class _WindowsProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class _WindowsMemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _process_memory_bytes() -> tuple[int, int]:
    """Return current RSS and process-lifetime peak RSS in bytes."""
    if sys.platform == "win32":
        counters = _WindowsProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(_WindowsProcessMemoryCounters),
            ctypes.c_ulong,
        )
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)

    current = 0
    proc_statm = Path("/proc/self/statm")
    if proc_statm.is_file():
        resident_pages = int(proc_statm.read_text(encoding="ascii").split()[1])
        current = resident_pages * int(os.sysconf("SC_PAGE_SIZE"))
    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    return current or peak, peak


def _physical_memory_bytes() -> tuple[int, int]:
    """Return total and currently available physical memory in bytes."""
    if sys.platform == "win32":
        status = _WindowsMemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed")
        return int(status.ullTotalPhys), int(status.ullAvailPhys)

    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        values: dict[str, int] = {}
        for line in meminfo.read_text(encoding="ascii").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
        return values["MemTotal"], values.get("MemAvailable", values["MemFree"])
    pages = int(os.sysconf("SC_PHYS_PAGES"))
    available_pages = int(os.sysconf("SC_AVPHYS_PAGES"))
    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    return pages * page_size, available_pages * page_size


def _time_samples(
    function: Callable[[], None],
    *,
    warmups: int,
    repetitions: int,
    units_per_sample: int,
) -> dict[str, object]:
    for _ in range(warmups):
        for _ in range(units_per_sample):
            function()
    wall_samples: list[float] = []
    cpu_samples: list[float] = []
    for _ in range(repetitions):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        for _ in range(units_per_sample):
            function()
        wall_samples.append((time.perf_counter() - wall_started) / units_per_sample)
        cpu_samples.append((time.process_time() - cpu_started) / units_per_sample)
    return {
        "warmup_repetitions": warmups * units_per_sample,
        "measured_repetitions": repetitions * units_per_sample,
        "timing_samples": repetitions,
        "units_per_sample": units_per_sample,
        "central_wall_seconds_per_unit": statistics.median(wall_samples),
        "observed_max_wall_seconds_per_unit": max(wall_samples),
        "central_cpu_seconds_per_unit": statistics.median(cpu_samples),
        "observed_max_cpu_seconds_per_unit": max(cpu_samples),
    }


def _training_fixture() -> None:
    weights = torch.linspace(-0.025, 0.025, steps=48, dtype=torch.float64).reshape(8, 6)
    idle_weights = torch.linspace(-0.02, 0.02, steps=12, dtype=torch.float64).reshape(2, 6)
    weights.requires_grad_(True)
    idle_weights.requires_grad_(True)
    edge = torch.eye(8, dtype=torch.float64) + 0.01
    total = torch.zeros((), dtype=torch.float64)
    for roster_size in (4, 8):
        features = torch.arange(48 * 6, dtype=torch.float64).reshape(48, 6)
        features = (features.remainder(17.0) - 8.0) / 17.0
        mapped = (features @ weights.T) @ edge.T
        idle = features @ idle_weights.T
        expanded = mapped[:, None, :4].expand(48, roster_size, 4)
        idle_column = idle[:, None, :1].expand(48, roster_size, 1)
        logits = torch.cat((expanded, idle_column), dim=2)
        coefficients = torch.arange(logits.numel(), dtype=torch.float64).reshape(logits.shape)
        coefficients = coefficients.remainder(11.0) / 11.0
        probabilities = torch.softmax(logits, dim=2)
        total = total + (probabilities * coefficients).sum() / float(logits.shape[0])
        total = total + torch.logsumexp(logits, dim=2).mean()
    total.backward()
    torch.nn.utils.clip_grad_norm_((weights, idle_weights), 5.0)


def _softmax_numpy(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials, axis=1, keepdims=True)


def _validation_panel_fixture() -> None:
    transform = np.arange(30, dtype=np.float64).reshape(6, 5) / 31.0
    checksum = 0.0
    for roster_size in (4, 8):
        decisions = 12 * 2 * 16 * 2
        features = np.arange(decisions * 6, dtype=np.float64).reshape(decisions, 6)
        features = (np.remainder(features, 23.0) - 11.0) / 23.0
        logits = features @ transform
        expanded = np.repeat(logits, roster_size, axis=0)
        probabilities = _softmax_numpy(expanded)
        checksum += float(np.sum(probabilities[:, 0]))
    if not math.isfinite(checksum):
        raise RuntimeError("nonfinite validation fixture checksum")


def _base_plus_replay_fixture() -> None:
    transform = np.arange(30, dtype=np.float64).reshape(6, 5) / 29.0
    checksum = 0.0
    for roster_size in (4, 6, 8, 12):
        decisions = 12 * 2 * 64 * 2
        features = np.arange(decisions * 6, dtype=np.float64).reshape(decisions, 6)
        features = (np.remainder(features, 31.0) - 15.0) / 31.0
        logits = np.repeat(features @ transform, roster_size, axis=0)
        base = _softmax_numpy(logits)
        replay = _softmax_numpy(logits[::-1])
        checksum += float(np.sum(base[:, 0]) + np.sum(replay[:, 0]))
    if not math.isfinite(checksum):
        raise RuntimeError("nonfinite base-plus-replay fixture checksum")


def _four_fit_concatenation() -> dict[str, int]:
    rows_per_fit = 12_288
    columns = 128
    parts = []
    for index in range(4):
        part = np.arange(rows_per_fit * columns, dtype=np.float64).reshape(
            rows_per_fit, columns
        )
        part += float(index)
        parts.append(part)
    before_current, before_peak = _process_memory_bytes()
    combined = np.concatenate(parts, axis=0)
    after_current, after_peak = _process_memory_bytes()
    result = {
        "measured_repetitions": 1,
        "rows_per_fit": rows_per_fit,
        "fit_count": 4,
        "columns": columns,
        "part_bytes": int(sum(part.nbytes for part in parts)),
        "combined_bytes": int(combined.nbytes),
        "rss_before_bytes": before_current,
        "rss_after_bytes": after_current,
        "process_peak_before_bytes": before_peak,
        "process_peak_after_bytes": after_peak,
    }
    del combined, parts
    gc.collect()
    return result


def _packet_arrays(rows: int = 49_152) -> dict[str, np.ndarray]:
    int8_values = np.arange(rows * 256, dtype=np.int8).reshape(rows, 256)
    int8_values *= np.int8(73)
    int16_values = np.arange(rows * 256, dtype=np.int16).reshape(rows, 256)
    int16_values *= np.int16(251)
    int32_values = np.arange(rows * 128, dtype=np.int32).reshape(rows, 128)
    int32_values *= np.int32(65_537)
    float_values = np.arange(rows * 120, dtype=np.float64).reshape(rows, 120)
    np.sin(float_values * 0.6180339887498948, out=float_values)
    return {
        "fixture_i8": int8_values,
        "fixture_i16": int16_values,
        "fixture_i32": int32_values,
        "fixture_f64": float_values,
    }


def _measure_common_storage(work: Path) -> dict[str, object]:
    table_path = work / "tables_fixture.npz"
    manifest_path = work / "manifest_fixture.json"
    summary_path = work / "summary_fixture.json"
    table = np.arange(312_064, dtype=np.uint8)
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    np.savez_compressed(table_path, deterministic_table=table)
    common_document = {
        "fixture_kind": "non_scientific_common_tree",
        "revision": ESTIMATOR_REVISION,
        "complete": True,
    }
    manifest_path.write_text(
        json.dumps(common_document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps({"fixture_kind": "resource_only"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    wall_seconds = time.perf_counter() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    files = [table_path, manifest_path, summary_path]
    current, peak = _process_memory_bytes()
    return {
        "measured_repetitions": 1,
        "table_uncompressed_bytes": int(table.nbytes),
        "table_compressed_bytes": table_path.stat().st_size,
        "json_bytes": manifest_path.stat().st_size + summary_path.stat().st_size,
        "complete_common_tree_bytes": sum(path.stat().st_size for path in files),
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "rss_after_bytes": current,
        "process_peak_after_bytes": peak,
    }


def _measure_packet_storage(work: Path) -> dict[str, object]:
    packet_path = work / "packet_fixture.npz"
    arrays = _packet_arrays()
    uncompressed_bytes = int(sum(array.nbytes for array in arrays.values()))
    before_current, before_peak = _process_memory_bytes()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    np.savez_compressed(packet_path, **arrays)
    write_wall = time.perf_counter() - wall_started
    write_cpu = time.process_time() - cpu_started
    after_write_current, after_write_peak = _process_memory_bytes()
    del arrays
    gc.collect()

    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    accessed_bytes = 0
    with np.load(packet_path, allow_pickle=False) as packet:
        for name in packet.files:
            array = packet[name]
            accessed_bytes += int(array.nbytes)
            if array.size:
                _ = array.reshape(-1)[0]
            del array
    read_wall = time.perf_counter() - wall_started
    read_cpu = time.process_time() - cpu_started
    after_read_current, after_read_peak = _process_memory_bytes()
    return {
        "measured_repetitions": 1,
        "row_count": 49_152,
        "typed_array_count": 4,
        "uncompressed_bytes": uncompressed_bytes,
        "authority_static_packet_bytes": STATIC_PACKET_BYTES,
        "compressed_bytes": packet_path.stat().st_size,
        "write_wall_seconds": write_wall,
        "write_cpu_seconds": write_cpu,
        "read_access_wall_seconds": read_wall,
        "read_access_cpu_seconds": read_cpu,
        "read_accessed_bytes": accessed_bytes,
        "rss_before_bytes": before_current,
        "process_peak_before_bytes": before_peak,
        "rss_after_write_bytes": after_write_current,
        "process_peak_after_write_bytes": after_write_peak,
        "rss_after_read_bytes": after_read_current,
        "process_peak_after_read_bytes": after_read_peak,
    }


def _upper_per_unit(measurement: dict[str, object], resource: str) -> float:
    return float(measurement[f"observed_max_{resource}_seconds_per_unit"]) * COMPUTE_UNCERTAINTY_FACTOR


def _central_per_unit(measurement: dict[str, object], resource: str) -> float:
    return float(measurement[f"central_{resource}_seconds_per_unit"])


def _project(
    import_wall: float,
    import_cpu: float,
    training: dict[str, object],
    validation: dict[str, object],
    evaluation: dict[str, object],
    common: dict[str, object],
    packet: dict[str, object],
    gate_peak: int,
    all_pass_peak: int,
) -> dict[str, object]:
    gate_central_wall = (
        import_wall
        + WORKLOAD["gate_training_units"] * _central_per_unit(training, "wall")
        + WORKLOAD["validation_panel_units"] * _central_per_unit(validation, "wall")
        + float(common["wall_seconds"])
    )
    gate_upper_wall = (
        import_wall * COMPUTE_UNCERTAINTY_FACTOR
        + WORKLOAD["gate_training_units"] * _upper_per_unit(training, "wall")
        + WORKLOAD["validation_panel_units"] * _upper_per_unit(validation, "wall")
        + float(common["wall_seconds"]) * STORAGE_TIME_UNCERTAINTY_FACTOR
    )
    gate_central_cpu = (
        import_cpu
        + WORKLOAD["gate_training_units"] * _central_per_unit(training, "cpu")
        + WORKLOAD["validation_panel_units"] * _central_per_unit(validation, "cpu")
        + float(common["cpu_seconds"])
    )
    gate_upper_cpu = (
        import_cpu * COMPUTE_UNCERTAINTY_FACTOR
        + WORKLOAD["gate_training_units"] * _upper_per_unit(training, "cpu")
        + WORKLOAD["validation_panel_units"] * _upper_per_unit(validation, "cpu")
        + float(common["cpu_seconds"]) * STORAGE_TIME_UNCERTAINTY_FACTOR
    )

    packet_central_wall = float(packet["write_wall_seconds"]) + float(
        packet["read_access_wall_seconds"]
    )
    packet_upper_wall = packet_central_wall * STORAGE_TIME_UNCERTAINTY_FACTOR
    packet_central_cpu = float(packet["write_cpu_seconds"]) + float(
        packet["read_access_cpu_seconds"]
    )
    packet_upper_cpu = packet_central_cpu * STORAGE_TIME_UNCERTAINTY_FACTOR
    all_central_wall = (
        gate_central_wall
        + WORKLOAD["conditional_conclusion_training_units"]
        * _central_per_unit(training, "wall")
        + WORKLOAD["conditional_base_plus_replay_units"]
        * _central_per_unit(evaluation, "wall")
        + WORKLOAD["conditional_packet_writes"] * packet_central_wall
    )
    all_upper_wall = (
        gate_upper_wall
        + WORKLOAD["conditional_conclusion_training_units"]
        * _upper_per_unit(training, "wall")
        + WORKLOAD["conditional_base_plus_replay_units"]
        * _upper_per_unit(evaluation, "wall")
        + WORKLOAD["conditional_packet_writes"] * packet_upper_wall
    )
    all_central_cpu = (
        gate_central_cpu
        + WORKLOAD["conditional_conclusion_training_units"]
        * _central_per_unit(training, "cpu")
        + WORKLOAD["conditional_base_plus_replay_units"]
        * _central_per_unit(evaluation, "cpu")
        + WORKLOAD["conditional_packet_writes"] * packet_central_cpu
    )
    all_upper_cpu = (
        gate_upper_cpu
        + WORKLOAD["conditional_conclusion_training_units"]
        * _upper_per_unit(training, "cpu")
        + WORKLOAD["conditional_base_plus_replay_units"]
        * _upper_per_unit(evaluation, "cpu")
        + WORKLOAD["conditional_packet_writes"] * packet_upper_cpu
    )

    common_bytes = int(common["complete_common_tree_bytes"])
    packet_bytes = int(packet["compressed_bytes"])
    gate_retained_upper = math.ceil(common_bytes * DISK_UNCERTAINTY_FACTOR)
    all_retained_central = common_bytes + 16 * packet_bytes
    all_retained_upper = max(
        math.ceil(all_retained_central * DISK_UNCERTAINTY_FACTOR),
        math.ceil((STATIC_SIXTEEN_PACKET_BYTES + common_bytes) * 1.05),
    )
    gate_temporary_upper = gate_retained_upper + common_bytes
    all_temporary_upper = all_retained_upper + math.ceil(
        packet_bytes * DISK_UNCERTAINTY_FACTOR
    )
    return {
        "gate_only": {
            "central_wall_seconds": gate_central_wall,
            "conservative_upper_wall_seconds": gate_upper_wall,
            "central_cpu_seconds": gate_central_cpu,
            "conservative_upper_cpu_seconds": gate_upper_cpu,
            "central_peak_rss_bytes": gate_peak,
            "conservative_upper_peak_rss_bytes": math.ceil(
                gate_peak * RSS_UNCERTAINTY_FACTOR
            ),
            "central_temporary_bytes": common_bytes,
            "conservative_upper_temporary_bytes": gate_temporary_upper,
            "central_retained_bytes": common_bytes,
            "conservative_upper_retained_bytes": gate_retained_upper,
            "process_count": 1,
            "numerical_thread_limit": 4,
            "torch_interop_thread_count": 1,
            "accelerator_count": 0,
        },
        "all_pass": {
            "central_wall_seconds": all_central_wall,
            "conservative_upper_wall_seconds": all_upper_wall,
            "central_cpu_seconds": all_central_cpu,
            "conservative_upper_cpu_seconds": all_upper_cpu,
            "central_peak_rss_bytes": all_pass_peak,
            "conservative_upper_peak_rss_bytes": math.ceil(
                all_pass_peak * RSS_UNCERTAINTY_FACTOR
            ),
            "central_temporary_bytes": all_retained_central,
            "conservative_upper_temporary_bytes": all_temporary_upper,
            "central_retained_bytes": all_retained_central,
            "conservative_upper_retained_bytes": all_retained_upper,
            "process_count": 1,
            "numerical_thread_limit": 4,
            "torch_interop_thread_count": 1,
            "accelerator_count": 0,
        },
    }


def _capacity_comparisons(
    output: Path, projections: dict[str, object]
) -> dict[str, object]:
    total_memory, available_memory = _physical_memory_bytes()
    disk = shutil.disk_usage(output.parent)
    safe_memory = math.floor(available_memory * SAFE_CAPACITY_FRACTION)
    safe_disk = math.floor(disk.free * SAFE_CAPACITY_FRACTION)
    all_pass = projections["all_pass"]
    peak_upper = int(all_pass["conservative_upper_peak_rss_bytes"])
    temporary_upper = int(all_pass["conservative_upper_temporary_bytes"])
    memory_safe = peak_upper <= safe_memory and peak_upper <= SOURCE_CAPS["peak_rss_bytes"]
    disk_safe = (
        temporary_upper <= safe_disk
        and temporary_upper <= SOURCE_CAPS["temporary_plus_final_bytes"]
    )
    return {
        "physical_memory_total_bytes": total_memory,
        "physical_memory_available_bytes": available_memory,
        "safe_memory_capacity_bytes": safe_memory,
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "safe_disk_capacity_bytes": safe_disk,
        "safe_capacity_fraction": SAFE_CAPACITY_FRACTION,
        "all_pass_upper_peak_within_safe_memory": memory_safe,
        "all_pass_upper_peak_within_4_gib_source_cap": peak_upper
        <= SOURCE_CAPS["peak_rss_bytes"],
        "all_pass_upper_temporary_within_safe_disk": disk_safe,
        "all_pass_upper_temporary_within_8_gib_source_cap": temporary_upper
        <= SOURCE_CAPS["temporary_plus_final_bytes"],
        "required_memory_disposition": "SAFE" if memory_safe else "REDUCE_BATCH_OR_SHARD",
        "required_disk_disposition": "SAFE" if disk_safe else "REDUCE_BATCH_OR_SHARD",
    }


def _atomic_json_write(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def build_estimate(output: Path) -> dict[str, object]:
    root = _repo_root()
    output = _validated_output(root, output)
    authority_refs = _validate_authority(root)

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    if torch.cuda.is_available():
        raise RuntimeError("estimator requires a CPU-only runtime")

    import_wall = time.perf_counter() - _IMPORT_WALL_STARTED
    import_cpu = time.process_time() - _IMPORT_CPU_STARTED
    cold_current, cold_peak = _process_memory_bytes()
    training = _time_samples(
        _training_fixture, warmups=1, repetitions=5, units_per_sample=64
    )
    training_current, training_peak = _process_memory_bytes()
    validation = _time_samples(
        _validation_panel_fixture, warmups=1, repetitions=5, units_per_sample=8
    )
    validation_current, validation_peak = _process_memory_bytes()

    work = Path(tempfile.mkdtemp(prefix=".mgtap-estimator-", dir=output.parent)).resolve()
    try:
        if output.parent.resolve() not in work.parents:
            raise RuntimeError("temporary work directory escaped assigned output parent")
        common = _measure_common_storage(work)
        gate_peak = max(
            cold_peak,
            training_peak,
            validation_peak,
            int(common["process_peak_after_bytes"]),
        )
        evaluation = _time_samples(
            _base_plus_replay_fixture,
            warmups=1,
            repetitions=3,
            units_per_sample=2,
        )
        evaluation_current, evaluation_peak = _process_memory_bytes()
        concatenation = _four_fit_concatenation()
        packet = _measure_packet_storage(work)
        all_pass_peak = max(
            gate_peak,
            evaluation_peak,
            int(concatenation["process_peak_after_bytes"]),
            int(packet["process_peak_after_write_bytes"]),
            int(packet["process_peak_after_read_bytes"]),
        )

        projections = _project(
            import_wall,
            import_cpu,
            training,
            validation,
            evaluation,
            common,
            packet,
            gate_peak,
            all_pass_peak,
        )
        capacity = _capacity_comparisons(output, projections)
        all_upper_wall = float(
            projections["all_pass"]["conservative_upper_wall_seconds"]
        )
        classification = (
            "<=7200"
            if all_upper_wall <= SOURCE_CAPS["scheduling_wall_seconds"]
            else ">7200"
        )
        implementation_refs = []
        for relative in (SOURCE_RELATIVE_PATH, TEST_RELATIVE_PATH):
            implementation_refs.append(
                {"path": relative, "sha256": _sha256(root / relative)}
            )
        estimate: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "estimator_revision": ESTIMATOR_REVISION,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "classification": classification,
            "authority_refs": authority_refs,
            "implementation_refs": implementation_refs,
            "runtime": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "numpy": np.__version__,
                "torch": torch.__version__,
                "cpu_count": os.cpu_count(),
                "process_count": 1,
                "numerical_thread_limit": torch.get_num_threads(),
                "torch_interop_thread_count": torch.get_num_interop_threads(),
                "accelerator_count": 0,
            },
            "workload": WORKLOAD,
            "workload_formulas": WORKLOAD_FORMULAS,
            "source_caps": SOURCE_CAPS,
            "uncertainty": {
                "compute_time_factor": COMPUTE_UNCERTAINTY_FACTOR,
                "storage_time_factor": STORAGE_TIME_UNCERTAINTY_FACTOR,
                "rss_factor": RSS_UNCERTAINTY_FACTOR,
                "disk_factor": DISK_UNCERTAINTY_FACTOR,
            },
            "measured_primitives": {
                "cold_imported_process": {
                    "import_wall_seconds": import_wall,
                    "import_cpu_seconds": import_cpu,
                    "current_rss_bytes": cold_current,
                    "process_peak_rss_bytes": cold_peak,
                },
                "training_forward_backward_clip_unit": {
                    **training,
                    "decisions_per_unit": 96,
                    "roster_agent_steps_per_unit": 576,
                    "optimizer_steps": 0,
                    "rss_after_bytes": training_current,
                    "process_peak_after_bytes": training_peak,
                },
                "validation_panel_unit": {
                    **validation,
                    "decisions_per_unit": 1_536,
                    "roster_agent_steps_per_unit": 9_216,
                    "rss_after_bytes": validation_current,
                    "process_peak_after_bytes": validation_peak,
                },
                "base_plus_replay_unit": {
                    **evaluation,
                    "base_decisions_per_unit": 12_288,
                    "replay_decisions_per_unit": 12_288,
                    "roster_agent_steps_per_unit": 184_320,
                    "rss_after_bytes": evaluation_current,
                    "process_peak_after_bytes": evaluation_peak,
                },
                "four_fit_concatenation": concatenation,
                "common_tree_storage": common,
                "packet_storage": packet,
            },
            "projections": projections,
            "capacity_comparisons": capacity,
            "scheduling": {
                "classification": classification,
                "performance_reasonableness_review_required": classification == ">7200",
                "explicit_user_approval_required_before_later_result_command": classification
                == ">7200",
                "unsafe_memory_or_disk_requires_reduction": not (
                    capacity["all_pass_upper_peak_within_safe_memory"]
                    and capacity["all_pass_upper_temporary_within_safe_disk"]
                ),
            },
            "unmeasured_primitives": [],
            "non_scientific_attestation": {
                "scientific_activity_started": False,
                "registered_stochastic_materialization": False,
                "optimizer_step_called": False,
                "activity_marker_created": False,
                "scientific_result_tree_created_or_inspected": False,
                "production_or_registered_fit_called": False,
                "result_analysis_called": False,
                "scientific_values_or_registered_addresses_created_or_inspected": False,
            },
        }
        _atomic_json_write(output, estimate)
        return estimate
    finally:
        resolved_parent = output.parent.resolve()
        if work.exists() and resolved_parent in work.parents:
            shutil.rmtree(work)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure deterministic, non-scientific MGTAP R01 resource fixtures "
            "and write one current-authority estimate JSON."
        )
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    estimate = build_estimate(args.output)
    print(
        json.dumps(
            {
                "classification": estimate["classification"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
