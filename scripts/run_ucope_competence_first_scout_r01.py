#!/usr/bin/env python3
"""Resource-gated runner for the UCOPE competence-first three-arm scout.

``assess-run`` is an A/RECON sizing operation.  It executes the reduced fresh
workload but publishes only activity and resource facts.  ``run-b1`` and
``resume-b1`` are result-bearing and therefore perform a fresh central 4 GiB
memory admission before creating or reopening scientific state.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import ctypes
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01 import (  # noqa: E402
    OBJECT_ID,
    RunBinding,
    ScoutConfig,
    run_workload,
    sanitize_assess_result,
    stage_checkpoint_inventory,
    validate_assess_artifact,
    validate_complete_tree,
    validate_scientific_artifact,
)
from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import load_checkpoint  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.artifact import (  # noqa: E402
    SCIENTIFIC_FORMAT,
    atomic_create_json,
    canonical_json_bytes,
    publish_complete,
)

PACKAGE_ROOT = PROJECT_ROOT / "experiments/candidates/ucope/competence_first_scout_r01"
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
RUNNER_PATH = Path(__file__).resolve()
ASSESS_FORMAT = "UCOPE_SCOUT_R01_A_RECON_RESOURCE_ASSESSMENT_V1"
B1_MANIFEST_FORMAT = "UCOPE_SCOUT_R01_B1_RUN_MANIFEST_V1"
RESOURCE_JOURNAL_FORMAT = "UCOPE_SCOUT_R01_RESOURCE_JOURNAL_ENTRY_V1"
RESOURCE_LEDGER_FORMAT = "UCOPE_SCOUT_R01_COMPLETE_RESOURCE_LEDGER_V1"
FAILURE_RECEIPT_FORMAT = "UCOPE_SCOUT_R01_ATTEMPT_FAILURE_V1"
TERMINAL_RECEIPT_FORMAT = "UCOPE_SCOUT_R01_COMPLETE_TERMINAL_RECEIPT_V1"
MINIMUM_MEMORY_BYTES = 4 * 1024**3
SAMPLE_SECONDS = 0.05
PUBLICATION_HEADROOM_BYTES = 1 * 1024**2
MAX_READY_WALL_SECONDS = 7_200
MAX_READY_RSS_BYTES = 2 * 1024**3
MAX_READY_STORAGE_BYTES = 2 * 1024**3
# Resource-only calibration from the quarantined, incomplete B1 attempt.  No
# checkpoint payload, evaluation, gate, or scientific outcome contributes to
# this engineering floor.  The observed full-load process-tree peak is guarded
# independently because reduced A/RECON cannot reproduce the retained three-
# seed populations plus the CPU allocator high-water across all three arms.
B1_RESOURCE_ONLY_RSS_CALIBRATION_ID = "ucope-scout-r01-b1-20260901-01"
B1_RESOURCE_ONLY_PEAK_RSS_BYTES = 455_176_192
RSS_HEADROOM_NUMERATOR = 5
RSS_HEADROOM_DENOMINATOR = 4
FORBIDDEN_MODULE_TOKENS = (
    "contextual_paid_acquisition_r01",
    "variable_k_paid_probe_r01_r03",
    "run_ucope_structural_competence_certificate",
)


class RunnerRefusal(RuntimeError):
    """Fail-closed engineering refusal."""


def _directory_size(root: Path, *, require_exists: bool = False) -> int:
    if not root.exists():
        if require_exists:
            raise RunnerRefusal(f"monitored resource root disappeared: {root}")
        return 0
    if root.is_symlink() or not root.is_dir():
        raise RunnerRefusal(f"resource root is not a plain directory: {root}")
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RunnerRefusal(f"resource root contains a symlink: {path}")
        if path.is_file():
            total += path.stat().st_size
    return total


def _filetime_value(value: Any) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


@dataclass(frozen=True)
class _ProcessSample:
    identity: tuple[int, int]
    rss_bytes: int
    cpu_seconds: float
    io_read_bytes: int
    io_write_bytes: int
    io_other_bytes: int
    threads: int


def _windows_process_tree() -> tuple[_ProcessSample, ...]:
    """Observe the current Windows process and all live descendants."""
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

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

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    kernel32.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(IO_COUNTERS)]
    kernel32.GetProcessIoCounters.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise RunnerRefusal("CreateToolhelp32Snapshot failed")
    entries: list[tuple[int, int, int]] = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while present:
            entries.append(
                (int(entry.th32ProcessID), int(entry.th32ParentProcessID), int(entry.cntThreads))
            )
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)

    root_pid = os.getpid()
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent, _threads in entries:
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    thread_by_pid = {pid: threads for pid, _parent, threads in entries}
    samples: list[_ProcessSample] = []
    for pid in sorted(descendants):
        handle = kernel32.GetCurrentProcess() if pid == root_pid else kernel32.OpenProcess(
            0x1000 | 0x0010, False, pid
        )
        if not handle:
            # A short-lived descendant may exit between enumeration and open.
            continue
        close = pid != root_pid
        try:
            memory = PROCESS_MEMORY_COUNTERS_EX()
            memory.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            io = IO_COUNTERS()
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise RunnerRefusal(f"GetProcessMemoryInfo failed for pid {pid}")
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
                raise RunnerRefusal(f"GetProcessIoCounters failed for pid {pid}")
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                raise RunnerRefusal(f"GetProcessTimes failed for pid {pid}")
            cpu_100ns = _filetime_value(kernel) + _filetime_value(user)
            samples.append(
                _ProcessSample(
                    (pid, _filetime_value(creation)),
                    int(memory.WorkingSetSize),
                    cpu_100ns / 10_000_000.0,
                    int(io.ReadTransferCount),
                    int(io.WriteTransferCount),
                    int(io.OtherTransferCount),
                    int(thread_by_pid.get(pid, 0)),
                )
            )
        finally:
            if close:
                kernel32.CloseHandle(handle)
    if not any(sample.identity[0] == root_pid for sample in samples):
        raise RunnerRefusal("current process was absent from process-tree observation")
    return tuple(samples)


def _portable_process_tree() -> tuple[_ProcessSample, ...]:
    """Single-process fallback for non-Windows developer tests."""
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss) * (1024 if sys.platform != "darwin" else 1)
    return (
        _ProcessSample(
            (os.getpid(), 0),
            rss,
            float(usage.ru_utime + usage.ru_stime),
            int(usage.ru_inblock) * 512,
            int(usage.ru_oublock) * 512,
            0,
            threading.active_count(),
        ),
    )


class ProcessTreeMonitor:
    """Sample process-tree and filesystem high-water facts without result fields."""

    def __init__(self, scratch_root: Path, durable_root: Path, sample_seconds: float = SAMPLE_SECONDS):
        self.scratch_root = scratch_root
        self.durable_root = durable_root
        self.sample_seconds = sample_seconds
        self.started_wall = time.perf_counter()
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._first: dict[tuple[int, int], _ProcessSample] = {}
        self._last: dict[tuple[int, int], _ProcessSample] = {}
        self.peak_rss_bytes = 0
        self.peak_processes = 0
        self.peak_threads = 0
        self.scratch_peak_bytes = 0
        self.durable_peak_bytes = 0
        self.samples = 0
        self._finished = False
        self._final_result: dict[str, Any] | None = None

    def _observe_locked(self) -> None:
        rows = _windows_process_tree() if os.name == "nt" else _portable_process_tree()
        self.samples += 1
        self.peak_rss_bytes = max(self.peak_rss_bytes, sum(row.rss_bytes for row in rows))
        self.peak_processes = max(self.peak_processes, len(rows))
        self.peak_threads = max(self.peak_threads, sum(row.threads for row in rows))
        self.scratch_peak_bytes = max(
            self.scratch_peak_bytes, _directory_size(self.scratch_root, require_exists=True)
        )
        self.durable_peak_bytes = max(
            self.durable_peak_bytes, _directory_size(self.durable_root, require_exists=True)
        )
        for row in rows:
            self._first.setdefault(row.identity, row)
            self._last[row.identity] = row

    def _observe(self) -> None:
        with self._lock:
            if self._finished:
                raise RunnerRefusal("resource monitor is already finished")
            self._observe_locked()

    def _loop(self) -> None:
        try:
            while not self._stop.wait(self.sample_seconds):
                self._observe()
        except BaseException as exc:  # recorded and re-raised by finish
            with self._lock:
                self._error = exc
            self._stop.set()

    def start(self) -> "ProcessTreeMonitor":
        with self._lock:
            if self._thread is not None or self._finished:
                raise RunnerRefusal("resource monitor may be started only once")
            self._observe_locked()
            self._thread = threading.Thread(target=self._loop, name="ucope-r01-resource-monitor", daemon=True)
            self._thread.start()
        return self

    def snapshot(self) -> dict[str, Any]:
        """Return a cumulative checkpoint observation without stopping the monitor."""
        with self._lock:
            if self._finished:
                return dict(self._final_result or {})
            if self._error is not None:
                raise RunnerRefusal(f"resource observation failed: {self._error}") from self._error
            self._observe_locked()
            cpu, read_bytes, write_bytes, other_bytes = self._cumulative_counters_locked()
            return {
                "sample_count": self.samples,
                "wall_seconds": time.perf_counter() - self.started_wall,
                "cpu_seconds": cpu,
                "peak_rss_bytes": self.peak_rss_bytes,
                "peak_process_count": self.peak_processes,
                "peak_thread_count": self.peak_threads,
                "scratch_peak_bytes": self.scratch_peak_bytes,
                "durable_peak_bytes": self.durable_peak_bytes,
                "io_read_bytes": read_bytes,
                "io_write_bytes": write_bytes,
                "io_other_bytes": other_bytes,
                "aggregate_io_bytes": read_bytes + write_bytes + other_bytes,
            }

    def rename_durable_root(self, source: Path, destination: Path) -> None:
        """Bind the final old sample, rename, retarget, and first new sample under one lock."""
        with self._lock:
            if self._finished or self._error is not None:
                raise RunnerRefusal("cannot retarget an inactive resource monitor")
            source = Path(source)
            destination = Path(destination)
            if (
                self.durable_root.resolve() != source.resolve()
                or source.parent.resolve() != destination.parent.resolve()
                or source.is_symlink()
                or not source.is_dir()
                or destination.exists()
            ):
                raise RunnerRefusal("durable monitor rename transaction has unsafe paths")
            # The monitor lock excludes the sampling thread from walking the old
            # tree while its name changes.  Both endpoint samples are real; a
            # missing/renamed root is never represented as zero bytes.
            self._observe_locked()
            os.replace(source, destination)
            self.durable_root = destination
            self._observe_locked()

    def _cumulative_counters_locked(self) -> tuple[float, int, int, int]:
        cpu = 0.0
        read_bytes = write_bytes = other_bytes = 0
        for identity, last in self._last.items():
            first = self._first[identity]
            cpu += max(0.0, last.cpu_seconds - first.cpu_seconds)
            read_bytes += max(0, last.io_read_bytes - first.io_read_bytes)
            write_bytes += max(0, last.io_write_bytes - first.io_write_bytes)
            other_bytes += max(0, last.io_other_bytes - first.io_other_bytes)
        return cpu, read_bytes, write_bytes, other_bytes

    def finish(self) -> dict[str, Any]:
        with self._lock:
            if self._finished:
                return dict(self._final_result or {})
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                raise RunnerRefusal("resource sampler did not terminate")
        with self._lock:
            self._observe_locked()
            if self._error is not None:
                raise RunnerRefusal(f"resource observation failed: {self._error}") from self._error
            wall = time.perf_counter() - self.started_wall
            cpu, read_bytes, write_bytes, other_bytes = self._cumulative_counters_locked()
            logical = max(1, os.cpu_count() or 1)
            result = {
            "measurement_complete": True,
            "measurement_source": "Windows process tree APIs" if os.name == "nt" else "getrusage single process",
            "sample_interval_seconds": self.sample_seconds,
            "sample_count": self.samples,
            "wall_seconds": wall,
            "cpu_seconds": cpu,
            "cpu_core_equivalents": 0.0 if wall <= 0 else cpu / wall,
            "host_cpu_occupancy": 0.0 if wall <= 0 else cpu / (wall * logical),
            "peak_rss_bytes": self.peak_rss_bytes,
            "peak_process_count": self.peak_processes,
            "peak_thread_count": self.peak_threads,
            "worker_count": 1,
            "accelerator": "NOT_APPLICABLE_CPU_ONLY",
            "peak_accelerator_memory_bytes": 0,
            "io_read_bytes": int(read_bytes),
            "io_write_bytes": int(write_bytes),
            "io_other_bytes": int(other_bytes),
            "aggregate_io_bytes": int(read_bytes + write_bytes + other_bytes),
            "scratch_peak_bytes": self.scratch_peak_bytes,
            "durable_peak_bytes": self.durable_peak_bytes,
            }
            self._finished = True
            self._final_result = dict(result)
            return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RunnerRefusal(f"bound file is absent or symlinked: {path}")
    try:
        locator = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RunnerRefusal(f"bound file is outside complete root: {path}") from exc
    return {"locator": locator, "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _control_root(manifest_path: Path, manifest: Mapping[str, Any]) -> Path:
    name = manifest["publication"]["control_namespace"]
    if type(name) is not str or not name.startswith(".ucope-scout-r01-control-") or "/" in name or "\\" in name:
        raise RunnerRefusal("manifest control namespace is unsafe")
    return manifest_path.parent / name


def _reject_journal_science(value: Any) -> None:
    forbidden = {
        "scores", "returns", "regret", "competence", "acquisition", "oracle", "root_actions",
        "tail_agreement", "gates", "polarity", "internal_result", "evaluations",
    }
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in forbidden:
                raise RunnerRefusal(f"scientific field is forbidden from resource journal: {key}")
            _reject_journal_science(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_journal_science(item)


def _validate_checkpoint_snapshot(value: Mapping[str, Any], previous: Mapping[str, Any] | None = None) -> None:
    required = {
        "sample_count", "wall_seconds", "cpu_seconds", "peak_rss_bytes", "peak_process_count",
        "peak_thread_count", "scratch_peak_bytes", "durable_peak_bytes", "io_read_bytes",
        "io_write_bytes", "io_other_bytes", "aggregate_io_bytes",
    }
    if not isinstance(value, Mapping) or set(value) != required or type(value["sample_count"]) is not int or value["sample_count"] <= 0:
        raise RunnerRefusal("checkpoint resource snapshot structure mismatch")
    if any(not isinstance(value[name], (int, float)) or isinstance(value[name], bool) or value[name] < 0 for name in required - {"sample_count"}):
        raise RunnerRefusal("checkpoint resource snapshot contains invalid counters")
    if value["aggregate_io_bytes"] != value["io_read_bytes"] + value["io_write_bytes"] + value["io_other_bytes"]:
        raise RunnerRefusal("checkpoint resource snapshot I/O does not reconcile")
    if previous is not None:
        monotone = required - {"cpu_seconds"}
        if any(value[name] < previous[name] for name in monotone) or value["cpu_seconds"] < previous["cpu_seconds"]:
            raise RunnerRefusal("checkpoint resource snapshots are not cumulative")


def _validate_terminal_resources(value: Mapping[str, Any]) -> None:
    required = {
        "measurement_complete", "measurement_source", "sample_interval_seconds", "sample_count",
        "wall_seconds", "cpu_seconds", "cpu_core_equivalents", "host_cpu_occupancy",
        "peak_rss_bytes", "peak_process_count", "peak_thread_count", "worker_count", "accelerator",
        "peak_accelerator_memory_bytes", "io_read_bytes", "io_write_bytes", "io_other_bytes",
        "aggregate_io_bytes", "scratch_peak_bytes", "durable_peak_bytes",
    }
    if not isinstance(value, Mapping) or set(value) != required or value["measurement_complete"] is not True or int(value["sample_count"]) < 1:
        raise RunnerRefusal("invocation terminal resource telemetry is incomplete")
    positive_integers = {"sample_count", "peak_process_count", "peak_thread_count", "worker_count"}
    nonnegative_numbers = required - positive_integers - {
        "measurement_complete", "measurement_source", "accelerator",
    }
    if (
        type(value["measurement_source"]) is not str
        or not value["measurement_source"]
        or value["accelerator"] != "NOT_APPLICABLE_CPU_ONLY"
        or any(type(value[name]) is not int or value[name] <= 0 for name in positive_integers)
        or any(
            not isinstance(value[name], (int, float))
            or isinstance(value[name], bool)
            or not math.isfinite(float(value[name]))
            or value[name] < 0
            for name in nonnegative_numbers
        )
        or float(value["sample_interval_seconds"]) <= 0
    ):
        raise RunnerRefusal("invocation terminal resource telemetry contains invalid counters")
    if int(value["aggregate_io_bytes"]) != int(value["io_read_bytes"]) + int(value["io_write_bytes"]) + int(value["io_other_bytes"]):
        raise RunnerRefusal("invocation terminal I/O does not reconcile")


def _validate_stage_events(value: Any) -> None:
    schemas = {
        "fresh_data": {"stage", "wall_seconds", "cpu_seconds"},
        "policy_start": {"stage", "arm_id", "seed_id", "fold_id", "resumed_root_updates"},
        "checkpoint": {"stage", "arm_id", "seed_id", "fold_id", "root_update"},
        "policy_end": {"stage", "arm_id", "seed_id", "fold_id", "root_updates", "tail_updates"},
        "policy": {
            "stage", "arm_id", "seed_id", "fold_id", "wall_seconds", "cpu_seconds",
            "root_updates", "tail_updates",
        },
    }
    if not isinstance(value, list):
        raise RunnerRefusal("invocation stage telemetry must be a list")
    for event in value:
        if not isinstance(event, Mapping) or event.get("stage") not in schemas or set(event) != schemas[event["stage"]]:
            raise RunnerRefusal("invocation stage telemetry structure mismatch")
        for name, item in event.items():
            if name in {"stage", "arm_id", "seed_id"}:
                if type(item) is not str or not item:
                    raise RunnerRefusal("invocation stage telemetry identity mismatch")
            elif name in {"wall_seconds", "cpu_seconds"}:
                if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)) or item < 0:
                    raise RunnerRefusal("invocation stage timing is invalid")
            elif type(item) is not int or item < 0:
                raise RunnerRefusal("invocation stage counter is invalid")


def _outcome_free_stage_event(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project an internal callback onto the result-blind timing/progress journal surface."""
    fields = {
        "fresh_data": ("stage", "wall_seconds", "cpu_seconds"),
        "policy_start": ("stage", "arm_id", "seed_id", "fold_id", "resumed_root_updates"),
        "checkpoint": ("stage", "arm_id", "seed_id", "fold_id", "root_update"),
        "policy_end": ("stage", "arm_id", "seed_id", "fold_id", "root_updates", "tail_updates"),
        "policy": (
            "stage", "arm_id", "seed_id", "fold_id", "wall_seconds", "cpu_seconds",
            "root_updates", "tail_updates",
        ),
    }
    stage = value.get("stage") if isinstance(value, Mapping) else None
    if stage not in fields or any(name not in value for name in fields[stage]):
        raise RunnerRefusal("internal stage callback cannot be projected onto the outcome-free schema")
    projected = {name: value[name] for name in fields[stage]}
    _validate_stage_events([projected])
    return projected


def _load_resource_journal(control_root: Path, *, config: ScoutConfig, run_binding: RunBinding, live_attempt_id: str | None = None) -> list[dict[str, Any]]:
    journal_root = control_root / "resource-journal"
    if not journal_root.exists():
        return []
    if journal_root.is_symlink() or not journal_root.is_dir():
        raise RunnerRefusal("resource journal root is unsafe")
    paths = sorted(journal_root.glob("entry-*.json"))
    values = [_load_json(path) for path in paths]
    required = {"format", "schema_version", "sequence", "kind", "attempt_id", "config", "run_binding", "payload"}
    attempts: dict[str, list[str]] = {}
    checkpoint_identities = set()
    last_snapshot: dict[str, Mapping[str, Any]] = {}
    for sequence, (path, value) in enumerate(zip(paths, values)):
        if path.name != f"entry-{sequence:06d}.json" or set(value) != required:
            raise RunnerRefusal("resource journal sequence or field inventory mismatch")
        if value["format"] != RESOURCE_JOURNAL_FORMAT or value["schema_version"] != 1 or value["sequence"] != sequence:
            raise RunnerRefusal("resource journal identity mismatch")
        if value["config"] != config.to_dict() or value["run_binding"] != run_binding.to_dict():
            raise RunnerRefusal("resource journal config/run binding mismatch")
        if type(value["attempt_id"]) is not str or not value["attempt_id"]:
            raise RunnerRefusal("resource journal attempt identity is invalid")
        kind = value["kind"]
        if kind not in {"ADMISSION", "CHECKPOINT", "CORE_TERMINAL", "PUBLICATION_TERMINAL"} or not isinstance(value["payload"], Mapping):
            raise RunnerRefusal("resource journal kind/payload mismatch")
        prior = attempts.setdefault(value["attempt_id"], [])
        if kind == "ADMISSION":
            if prior or set(value["payload"]) != {"passed", "receipt", "error"} or type(value["payload"]["passed"]) is not bool:
                raise RunnerRefusal("resource journal admission ordering mismatch")
        elif kind == "CHECKPOINT":
            if not prior or prior[0] != "ADMISSION" or "CORE_TERMINAL" in prior:
                raise RunnerRefusal("checkpoint journal entry is outside an admitted live invocation")
            if set(value["payload"]) != {"identity", "resources"}:
                raise RunnerRefusal("checkpoint journal payload mismatch")
            identity = value["payload"]["identity"]
            if not isinstance(identity, Mapping) or set(identity) != {"arm_id", "seed_id", "fold_id", "root_update"}:
                raise RunnerRefusal("checkpoint journal identity mismatch")
            key = (identity["arm_id"], identity["seed_id"], identity["fold_id"], identity["root_update"])
            if key in checkpoint_identities:
                raise RunnerRefusal("checkpoint journal identity was duplicated across attempts")
            checkpoint_identities.add(key)
            _validate_checkpoint_snapshot(value["payload"]["resources"], last_snapshot.get(value["attempt_id"]))
            last_snapshot[value["attempt_id"]] = value["payload"]["resources"]
        elif kind == "CORE_TERMINAL":
            if not prior or prior[0] != "ADMISSION" or "CORE_TERMINAL" in prior or set(value["payload"]) != {"status", "phase", "resources", "stage_events", "error"}:
                raise RunnerRefusal("core terminal journal ordering/payload mismatch")
            if value["payload"]["status"] not in {"COMPLETE", "FAILED"}:
                raise RunnerRefusal("core terminal status mismatch")
            if value["payload"]["resources"] is not None:
                _validate_terminal_resources(value["payload"]["resources"])
            _validate_stage_events(value["payload"]["stage_events"])
        else:
            if not prior or "CORE_TERMINAL" not in prior or "PUBLICATION_TERMINAL" in prior or set(value["payload"]) != {"status", "phase", "resources", "error"}:
                raise RunnerRefusal("publication terminal journal ordering/payload mismatch")
            core_row = next(row for row in values[:sequence] if row["attempt_id"] == value["attempt_id"] and row["kind"] == "CORE_TERMINAL")
            if core_row["payload"]["status"] != "COMPLETE" or value["payload"]["status"] not in {"COMPLETE", "FAILED"}:
                raise RunnerRefusal("publication terminal requires a complete core invocation")
            if value["payload"]["resources"] is not None:
                _validate_terminal_resources(value["payload"]["resources"])
        _reject_journal_science(value["payload"])
        prior.append(kind)
    live = [
        attempt for attempt, kinds in attempts.items()
        if "CORE_TERMINAL" not in kinds
        or (kinds[-1] == "CORE_TERMINAL" and next(row for row in reversed(values) if row["attempt_id"] == attempt and row["kind"] == "CORE_TERMINAL")["payload"]["status"] == "COMPLETE")
    ]
    expected_live = live if live_attempt_id == "*" and len(live) <= 1 else ([] if live_attempt_id is None else [live_attempt_id])
    if live != expected_live:
        raise RunnerRefusal("resource journal contains an unterminated prior invocation")
    checkpoint_sequence = [dict(row["payload"]["identity"]) for row in values if row["kind"] == "CHECKPOINT"]
    expected_prefix = _expected_checkpoint_sequence(config)[: len(checkpoint_sequence)]
    if checkpoint_sequence != expected_prefix:
        raise RunnerRefusal("resource journal checkpoints are not the canonical prefix")
    return values


def _append_resource_journal(
    control_root: Path,
    *,
    config: ScoutConfig,
    run_binding: RunBinding,
    attempt_id: str,
    kind: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _load_resource_journal(
        control_root, config=config, run_binding=run_binding,
        live_attempt_id=attempt_id if kind != "ADMISSION" else None,
    )
    value = {
        "format": RESOURCE_JOURNAL_FORMAT,
        "schema_version": 1,
        "sequence": len(existing),
        "kind": kind,
        "attempt_id": attempt_id,
        "config": config.to_dict(),
        "run_binding": run_binding.to_dict(),
        "payload": dict(payload),
    }
    _reject_journal_science(value["payload"])
    journal_root = control_root / "resource-journal"
    journal_root.mkdir(parents=True, exist_ok=True)
    atomic_create_json(journal_root / f"entry-{len(existing):06d}.json", value)
    # Re-read immediately so create-once bytes, ordering and all prior attempts are checked.
    if kind == "CORE_TERMINAL" and payload.get("status") == "FAILED":
        expected_live = None
    elif kind == "PUBLICATION_TERMINAL":
        expected_live = None
    else:
        expected_live = attempt_id
    return _load_resource_journal(
        control_root, config=config, run_binding=run_binding,
        live_attempt_id=expected_live,
    )[-1]


def _journal_aggregate(entries: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(canonical_json_bytes(list(entries))).hexdigest()


def _validate_resumable_prior_journal(entries: Sequence[Mapping[str, Any]]) -> None:
    """Refuse a RunBinding whose prior process lost terminal resource observation."""
    core_terminals = {row["attempt_id"]: row for row in entries if row["kind"] == "CORE_TERMINAL"}
    publication_terminals = {row["attempt_id"]: row for row in entries if row["kind"] == "PUBLICATION_TERMINAL"}
    for admission in (row for row in entries if row["kind"] == "ADMISSION"):
        core = core_terminals.get(admission["attempt_id"])
        if core is None:
            raise RunnerRefusal(
                "prior invocation has no core terminal resource witness; this RunBinding is incomplete and cannot resume"
            )
        if admission["payload"]["passed"] is True and core["payload"]["resources"] is None:
            raise RunnerRefusal(
                "prior admitted invocation lost resource telemetry; this RunBinding is incomplete and cannot resume"
            )
        if core["payload"]["status"] == "COMPLETE":
            publication = publication_terminals.get(admission["attempt_id"])
            if publication is None or publication["payload"]["resources"] is None:
                raise RunnerRefusal(
                    "prior complete core invocation lacks publication terminal telemetry; this RunBinding is incomplete and cannot resume"
                )


def _expected_checkpoint_sequence(config: ScoutConfig) -> list[dict[str, Any]]:
    return [
        {"arm_id": arm, "seed_id": seed, "fold_id": fold, "root_update": update}
        for arm in config.arms
        for seed in config.seed_ids
        for fold in (0, 1)
        for update in config.evaluation_root_updates
    ]


def _work_checkpoint_sequence(work: Path, *, config: ScoutConfig, run_binding: RunBinding) -> list[dict[str, Any]]:
    checkpoint_root = work / "scientific_checkpoints"
    if not checkpoint_root.exists():
        return []
    paths = sorted(checkpoint_root.rglob("root-*.pt"))
    identities = []
    for path in paths:
        payload = load_checkpoint(path)
        if payload["config"] != config.to_dict() or payload["run_binding"] != run_binding.to_dict():
            raise RunnerRefusal("transient checkpoint config/run binding mismatch")
        identities.append({
            "arm_id": payload["arm_id"], "seed_id": payload["seed_id"],
            "fold_id": payload["fold_id"], "root_update": payload["root_updates"],
        })
    order = {tuple(row.values()): index for index, row in enumerate(_expected_checkpoint_sequence(config))}
    try:
        return sorted(identities, key=lambda row: order[tuple(row.values())])
    except KeyError as exc:
        raise RunnerRefusal("transient checkpoint identity is outside the frozen inventory") from exc


def _source_paths() -> tuple[Path, ...]:
    paths = tuple(sorted(PACKAGE_ROOT.glob("*.py"))) + (RUNNER_PATH,)
    if not paths or any(not path.is_file() or path.is_symlink() for path in paths):
        raise RunnerRefusal("source fence inventory is incomplete or unsafe")
    return paths


def _source_fence() -> dict[str, Any]:
    files = [
        {"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": _sha256_file(path)}
        for path in _source_paths()
    ]
    aggregate = hashlib.sha256(canonical_json_bytes(files)).hexdigest()
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--", *(row["path"] for row in files)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RunnerRefusal(f"Git source fence unavailable: {exc}") from exc
    return {
        "git_head": head,
        "relevant_status": status,
        "files": files,
        "aggregate_sha256": aggregate,
    }


def _runtime_fence() -> dict[str, Any]:
    import torch

    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "torch_version": str(torch.__version__),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_intraop_threads": int(torch.get_num_threads()),
        "torch_interop_threads": int(torch.get_num_interop_threads()),
        "logical_processors": int(os.cpu_count() or 1),
    }


def _validate_import_firewall() -> None:
    imported = [name for name in sys.modules if any(token in name.lower() for token in FORBIDDEN_MODULE_TOKENS)]
    if imported:
        raise RunnerRefusal(f"consumed UCOPE module entered runtime: {sorted(imported)}")
    for path in _source_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(any(token in name.lower() for token in FORBIDDEN_MODULE_TOKENS) for name in names):
                raise RunnerRefusal(f"consumed UCOPE import found in {path}")


def _run_memory_admission(receipt: Path) -> dict[str, Any]:
    receipt.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(RESOURCE_PREFLIGHT), "admit-memory", "--out", str(receipt)]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if completed.returncode != 0 or not receipt.is_file():
        raise RunnerRefusal(
            f"central 4 GiB memory admission failed rc={completed.returncode}: {completed.stderr.strip()}"
        )
    value = json.loads(receipt.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("passed") is not True
        or value.get("physical_floor_pass") is not True
        or value.get("effective_floor_pass") is not True
        or int(value.get("available_physical_bytes", 0)) < MINIMUM_MEMORY_BYTES
        or int(value.get("effective_available_bytes", 0)) < MINIMUM_MEMORY_BYTES
    ):
        raise RunnerRefusal("central admission receipt does not establish both 4 GiB floors")
    return value


def _round_up(value: float, quantum: int) -> int:
    return int(math.ceil(max(1.0, value) / quantum) * quantum)


def _projection(core: Mapping[str, Any], resources: Mapping[str, Any]) -> dict[str, Any]:
    stages = core["stage_times"]
    data_wall = sum(float(row["wall_seconds"]) for row in stages if row["stage"] == "fresh_data")
    policy_wall = sum(float(row["wall_seconds"]) for row in stages if row["stage"] == "policy")
    data_cpu = sum(float(row["cpu_seconds"]) for row in stages if row["stage"] == "fresh_data")
    policy_cpu = sum(float(row["cpu_seconds"]) for row in stages if row["stage"] == "policy")
    # B1/ASSESS exact scaling: fresh population 48x; aggregate policy/update work <=60x.
    central_wall = data_wall * 48 + policy_wall * 60
    central_cpu = data_cpu * 48 + policy_cpu * 60
    guarded_wall = central_wall * 1.5 + 60.0
    assess_guarded_rss = (
        int(resources["peak_rss_bytes"]) * RSS_HEADROOM_NUMERATOR
        + RSS_HEADROOM_DENOMINATOR - 1
    ) // RSS_HEADROOM_DENOMINATOR
    calibrated_b1_guarded_rss = (
        B1_RESOURCE_ONLY_PEAK_RSS_BYTES * RSS_HEADROOM_NUMERATOR
        + RSS_HEADROOM_DENOMINATOR - 1
    ) // RSS_HEADROOM_DENOMINATOR
    guarded_rss = max(assess_guarded_rss, calibrated_b1_guarded_rss)
    # Frozen-target checkpoints dominate storage: 16x rows, 2x checkpoints, 3x seeds.
    storage_scale = 96
    guarded_scratch = int(math.ceil(int(resources["scratch_peak_bytes"]) * storage_scale * 1.5))
    guarded_durable = int(
        math.ceil((int(resources["durable_peak_bytes"]) + PUBLICATION_HEADROOM_BYTES) * storage_scale * 1.5)
    )
    ready = (
        guarded_wall <= MAX_READY_WALL_SECONDS
        and guarded_rss <= MAX_READY_RSS_BYTES
        and guarded_scratch <= MAX_READY_STORAGE_BYTES
        and guarded_durable <= MAX_READY_STORAGE_BYTES
    )
    python_adequate = guarded_wall <= 3_600
    core_runtime = core.get("runtime_refs", {})
    observed_processes = int(resources["peak_process_count"])
    observed_threads = int(resources["peak_thread_count"])
    torch_intraop = int(core_runtime.get("torch_intraop_threads", 0))
    torch_interop = int(core_runtime.get("torch_interop_threads", 0))
    if torch_intraop <= 0 or torch_interop <= 0:
        raise RunnerRefusal("sizing receipt lacks positive frozen Torch thread counts")
    return {
        "basis": "measured reduced three-arm A/RECON plus outcome-blind full-load RSS calibration; exact work scaling with 50% wall/storage and 5/4 RSS guards",
        "data_scale": 48,
        "policy_work_scale": 60,
        "storage_scale": storage_scale,
        "central_projected_wall_seconds": central_wall,
        "guarded_projected_wall_seconds": guarded_wall,
        "central_projected_cpu_seconds": central_cpu,
        "assess_guarded_peak_rss_bytes": assess_guarded_rss,
        "resource_only_b1_rss_calibration": {
            "attempt_id": B1_RESOURCE_ONLY_RSS_CALIBRATION_ID,
            "complete": False,
            "scientific_object_consumed": False,
            "observed_peak_rss_bytes": B1_RESOURCE_ONLY_PEAK_RSS_BYTES,
            "headroom_numerator": RSS_HEADROOM_NUMERATOR,
            "headroom_denominator": RSS_HEADROOM_DENOMINATOR,
            "guarded_peak_rss_bytes": calibrated_b1_guarded_rss,
        },
        "guarded_projected_peak_rss_bytes": guarded_rss,
        "guarded_projected_scratch_bytes": guarded_scratch,
        "guarded_projected_durable_bytes": guarded_durable,
        "resource_cap": {
            "wall_seconds": _round_up(guarded_wall, 300),
            "peak_rss_bytes": _round_up(guarded_rss, 64 * 1024**2),
            "scratch_bytes": _round_up(guarded_scratch, 64 * 1024**2),
            "durable_bytes": _round_up(guarded_durable, 64 * 1024**2),
            "workers": 1,
            "processes": max(1, observed_processes),
            "threads": _round_up(math.ceil(observed_threads * 1.25), 8),
            "torch_intraop_threads": torch_intraop,
            "torch_interop_threads": torch_interop,
        },
        "python_batching_adequate": python_adequate,
        "native_backend_required": False if python_adequate else "PROFILE_BEFORE_DECISION",
        "performance_disposition": "PERFORMANCE_READY" if ready else "REPAIR_REQUIRED",
    }


def _assessment_document(core: Mapping[str, Any], admission: Mapping[str, Any], resources: Mapping[str, Any]) -> dict[str, Any]:
    projection = _projection(core, resources)
    return {
        "format": ASSESS_FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "mode": "A/RECON",
        "claim_ceiling": "RESOURCE_AND_ENGINEERING_FACTS_ONLY_NO_ALGORITHM_EFFECT",
        "source_fence": _source_fence(),
        "runtime_fence": _runtime_fence(),
        "central_memory_admission": dict(admission),
        "core_assessment": dict(core),
        "resources": dict(resources),
        "projection": projection,
    }


def validate_assessment(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "mode", "claim_ceiling",
        "source_fence", "runtime_fence", "central_memory_admission", "core_assessment",
        "resources", "projection",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise RunnerRefusal("assessment field inventory mismatch")
    if (
        value["format"] != ASSESS_FORMAT
        or value["schema_version"] != 1
        or value["object_id"] != OBJECT_ID
        or value["mode"] != "A/RECON"
        or value["claim_ceiling"] != "RESOURCE_AND_ENGINEERING_FACTS_ONLY_NO_ALGORITHM_EFFECT"
    ):
        raise RunnerRefusal("assessment identity/claim ceiling mismatch")
    validate_assess_artifact(value["core_assessment"])
    observed_source = value["source_fence"]
    current_source = _source_fence()
    if (
        not isinstance(observed_source, Mapping)
        or observed_source.get("files") != current_source["files"]
        or observed_source.get("aggregate_sha256") != current_source["aggregate_sha256"]
    ):
        raise RunnerRefusal("assessment source fence does not match current source bytes")
    assess_binding = RunBinding.from_value(
        value["core_assessment"]["run_binding"], "ASSESS"
    )
    if assess_binding.source_aggregate != observed_source.get("aggregate_sha256"):
        raise RunnerRefusal("assessment core run binding differs from the source fence")
    if not isinstance(value["runtime_fence"], Mapping) or value["runtime_fence"] != _runtime_fence():
        raise RunnerRefusal("assessment runtime fence does not match current runtime")
    admission = value["central_memory_admission"]
    if not isinstance(admission, Mapping) or admission.get("passed") is not True:
        raise RunnerRefusal("assessment lacks passing central admission")
    resources = value["resources"]
    required_resource = {
        "measurement_complete", "measurement_source", "sample_interval_seconds", "sample_count",
        "wall_seconds", "cpu_seconds", "cpu_core_equivalents", "host_cpu_occupancy",
        "peak_rss_bytes", "peak_process_count", "peak_thread_count", "worker_count",
        "accelerator", "peak_accelerator_memory_bytes", "io_read_bytes", "io_write_bytes",
        "io_other_bytes", "aggregate_io_bytes", "scratch_peak_bytes", "durable_peak_bytes",
    }
    if not isinstance(resources, Mapping) or set(resources) != required_resource:
        raise RunnerRefusal("assessment resource inventory mismatch")
    if resources["measurement_complete"] is not True or int(resources["sample_count"]) < 2:
        raise RunnerRefusal("assessment process-tree observation is incomplete")
    if any(int(resources[name]) < 0 for name in required_resource if name.endswith("_bytes")):
        raise RunnerRefusal("assessment contains negative byte telemetry")
    if value["projection"] != _projection(value["core_assessment"], resources):
        raise RunnerRefusal("assessment projection does not recompute")
    canonical_json_bytes(value)
    return dict(value)


def _safe_scratch_for(output_root: Path) -> Path:
    resolved = output_root.resolve()
    parent = resolved.parent
    parent.mkdir(parents=True, exist_ok=True)
    return parent / f".{resolved.name}.scratch-{uuid.uuid4().hex}"


def assess_run(output_root: str | Path) -> Path:
    output = Path(output_root).resolve()
    if output.exists():
        raise RunnerRefusal(f"assessment output root is create-once: {output}")
    output.mkdir(parents=True)
    admission_path = output / "admit-memory.json"
    admission = _run_memory_admission(admission_path)
    scratch = _safe_scratch_for(output)
    scratch.mkdir(parents=True)
    monitor = ProcessTreeMonitor(scratch, output).start()
    resources: dict[str, Any] | None = None
    try:
        _validate_import_firewall()
        assessment_binding = RunBinding.assess(_source_fence()["aggregate_sha256"])
        result = run_workload(
            ScoutConfig.assess(), scratch, run_binding=assessment_binding
        )
        core = sanitize_assess_result(result)
        resources = monitor.finish()
        monitor = None  # type: ignore[assignment]
        document = _assessment_document(core, admission, resources)
        # Account prospectively for the create-once receipt itself without exposing internal state.
        for _ in range(4):
            resources["durable_peak_bytes"] = max(
                int(resources["durable_peak_bytes"]),
                _directory_size(output) + len(canonical_json_bytes(document)),
            )
            document = _assessment_document(core, admission, resources)
        validated = validate_assessment(document)
        receipt = output / "assessment-receipt.json"
        atomic_create_json(receipt, validated)
        return receipt
    except BaseException as exc:
        if monitor is not None:
            with contextlib.suppress(BaseException):
                resources = monitor.finish()
        stop = {
            "format": "UCOPE_SCOUT_R01_A_RECON_STOP_V1",
            "schema_version": 1,
            "mode": "A/RECON",
            "complete": False,
            "reason_type": type(exc).__name__,
            "reason": str(exc),
            "resources": resources,
        }
        with contextlib.suppress(FileExistsError):
            atomic_create_json(output / "assessment-stop.json", stop)
        raise
    finally:
        if scratch.exists():
            resolved = scratch.resolve()
            if resolved.parent != output.parent.resolve() or not resolved.name.startswith(f".{output.name}.scratch-"):
                raise RunnerRefusal("refusing to remove an unexpected assessment scratch root")
            shutil.rmtree(resolved)


def _load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RunnerRefusal(f"JSON document must be an object: {path}")
    return value


def create_b1_manifest(assessment_path: str | Path, manifest_path: str | Path) -> Path:
    assessment = validate_assessment(_load_json(assessment_path))
    if assessment["projection"]["performance_disposition"] != "PERFORMANCE_READY":
        raise RunnerRefusal("B1 manifest requires a PERFORMANCE_READY sizing assessment")
    source = _source_fence()
    if source["relevant_status"]:
        raise RunnerRefusal("B1 manifest requires committed clean relevant sources")
    manifest_destination = Path(manifest_path).resolve()
    control_name = f".ucope-scout-r01-control-{hashlib.sha256(str(manifest_destination).encode('utf-8')).hexdigest()[:16]}"
    value = {
        "format": B1_MANIFEST_FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "config": ScoutConfig.b1().to_dict(),
        "source_fence": source,
        "runtime_fence": _runtime_fence(),
        "assessment_path": str(Path(assessment_path).resolve()),
        "assessment_sha256": _sha256_file(Path(assessment_path).resolve()),
        "resource_cap": dict(assessment["projection"]["resource_cap"]),
        "publication": {
            "control_namespace": control_name,
            "complete_namespace": "complete",
            "complete_result": "complete/result.json",
            "terminal_receipt": "complete/terminal-receipt.json",
            "resource_ledger": "complete/resource-ledger.json",
        },
    }
    manifest_basis_digest = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    value["run_binding"] = RunBinding.b1(
        manifest_digest=manifest_basis_digest,
        source_aggregate=str(source["aggregate_sha256"]),
        assessment_digest=str(value["assessment_sha256"]),
    ).to_dict()
    return atomic_create_json(manifest_destination, value)


def _validate_b1_manifest(value: Mapping[str, Any], manifest_path: Path) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "config", "source_fence", "runtime_fence",
        "assessment_path", "assessment_sha256", "resource_cap", "publication", "run_binding",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise RunnerRefusal("B1 manifest field inventory mismatch")
    if value["format"] != B1_MANIFEST_FORMAT or value["schema_version"] != 1 or value["object_id"] != OBJECT_ID:
        raise RunnerRefusal("B1 manifest identity mismatch")
    if ScoutConfig.from_dict(value["config"]) != ScoutConfig.b1():
        raise RunnerRefusal("B1 manifest configuration drift")
    current_source = _source_fence()
    if current_source["relevant_status"] or current_source != value["source_fence"]:
        raise RunnerRefusal("B1 source fence drift or dirty relevant source")
    if _runtime_fence() != value["runtime_fence"]:
        raise RunnerRefusal("B1 runtime fence drift")
    assessment = Path(str(value["assessment_path"]))
    if not assessment.is_file() or _sha256_file(assessment) != value["assessment_sha256"]:
        raise RunnerRefusal("B1 sizing assessment binding drift")
    assessment_value = validate_assessment(_load_json(assessment))
    expected_cap = assessment_value["projection"]["resource_cap"]
    if value["resource_cap"] != expected_cap:
        raise RunnerRefusal("B1 resource cap differs from the bound sizing assessment")
    required_cap = {
        "wall_seconds", "peak_rss_bytes", "scratch_bytes", "durable_bytes", "workers",
        "processes", "threads", "torch_intraop_threads", "torch_interop_threads",
    }
    if (
        not isinstance(value["resource_cap"], Mapping)
        or set(value["resource_cap"]) != required_cap
        or any(type(value["resource_cap"][name]) is not int or value["resource_cap"][name] <= 0 for name in required_cap)
    ):
        raise RunnerRefusal("B1 resource cap field/value structure is invalid")
    expected_control = f".ucope-scout-r01-control-{hashlib.sha256(str(manifest_path.resolve()).encode('utf-8')).hexdigest()[:16]}"
    if value["publication"] != {
        "control_namespace": expected_control,
        "complete_namespace": "complete",
        "complete_result": "complete/result.json",
        "terminal_receipt": "complete/terminal-receipt.json",
        "resource_ledger": "complete/resource-ledger.json",
    }:
        raise RunnerRefusal("B1 publication namespace drift")
    manifest_basis = dict(value)
    observed_binding = RunBinding.from_value(manifest_basis.pop("run_binding"), "B1")
    expected_manifest_digest = hashlib.sha256(canonical_json_bytes(manifest_basis)).hexdigest()
    expected_binding = RunBinding.b1(
        manifest_digest=expected_manifest_digest,
        source_aggregate=str(value["source_fence"]["aggregate_sha256"]),
        assessment_digest=str(value["assessment_sha256"]),
    )
    if observed_binding != expected_binding:
        raise RunnerRefusal("B1 prospective run binding does not match the manifest basis")
    if manifest_path.resolve() == assessment.resolve():
        raise RunnerRefusal("B1 manifest and assessment may not alias")
    return dict(value)


def _scientific_document(
    result: Any,
    resource: Mapping[str, Any],
    checkpoint_inventory: Sequence[Mapping[str, Any]],
    *,
    artifact_root: Path,
    stage_times: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    value = {
        "format": SCIENTIFIC_FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "complete": True,
        "config": result.config.to_dict(),
        "run_binding": result.run_binding.to_dict(),
        "work": dict(result.work),
        "activity": dict(result.activity),
        "stage_times": [dict(row) for row in (result.stage_times if stage_times is None else stage_times)],
        "source_refs": list(result.source_refs),
        "runtime_refs": {**dict(result.runtime_refs), "resource": dict(resource)},
        "checkpoints": [dict(record) for record in checkpoint_inventory],
        "internal_result": dict(result.internal_result),
    }
    return validate_scientific_artifact(value, artifact_root=artifact_root)


def _journal_summary(entries: Sequence[Mapping[str, Any]], config: ScoutConfig) -> dict[str, Any]:
    admissions = [dict(row) for row in entries if row["kind"] == "ADMISSION"]
    terminals = [dict(row) for row in entries if row["kind"] == "CORE_TERMINAL"]
    checkpoints = [dict(row["payload"]["identity"]) for row in entries if row["kind"] == "CHECKPOINT"]
    if checkpoints != _expected_checkpoint_sequence(config):
        raise RunnerRefusal(f"resource journal checkpoint sequence is incomplete: {len(checkpoints)}")
    if not admissions or len(admissions) != len(terminals):
        raise RunnerRefusal("resource journal attempt admission/terminal inventory mismatch")
    terminal_by_attempt = {row["attempt_id"]: row for row in terminals}
    checkpoint_attempts = {row["attempt_id"] for row in entries if row["kind"] == "CHECKPOINT"}
    passing_admissions = 0
    for admission in admissions:
        payload = admission["payload"]
        receipt = payload["receipt"]
        terminal = terminal_by_attempt[admission["attempt_id"]]["payload"]
        if payload["passed"] is not True:
            if admission["attempt_id"] in checkpoint_attempts or terminal["status"] != "FAILED" or terminal["phase"] != "CENTRAL_MEMORY_ADMISSION" or terminal["resources"] is not None:
                raise RunnerRefusal("refused admission is not an outcome-free control-only attempt")
            continue
        if terminal["resources"] is None:
            raise RunnerRefusal("passing admitted attempt lacks complete terminal resource telemetry")
        passing_admissions += 1
        if not isinstance(receipt, Mapping):
            raise RunnerRefusal("passing journal admission lacks its receipt")
        if (
            receipt.get("passed") is not True
            or receipt.get("physical_floor_pass") is not True
            or receipt.get("effective_floor_pass") is not True
            or int(receipt.get("minimum_available_bytes", 0)) != MINIMUM_MEMORY_BYTES
            or int(receipt.get("available_physical_bytes", 0)) < MINIMUM_MEMORY_BYTES
            or int(receipt.get("effective_available_bytes", 0)) < MINIMUM_MEMORY_BYTES
        ):
            raise RunnerRefusal("journal admission does not establish both 4 GiB floors")
    if passing_admissions == 0:
        raise RunnerRefusal("complete B1 journal has no passing launch admission")
    if terminals[-1]["payload"]["status"] != "COMPLETE":
        raise RunnerRefusal("resource journal does not end in a complete invocation")
    resources = [row["payload"]["resources"] for row in terminals if isinstance(row["payload"]["resources"], Mapping)]
    if not resources:
        raise RunnerRefusal("resource journal lacks invocation telemetry")
    aggregate = {
        "attempt_count": len(terminals),
        "wall_seconds": sum(float(row["wall_seconds"]) for row in resources),
        "cpu_seconds": sum(float(row["cpu_seconds"]) for row in resources),
        "peak_rss_bytes": max(int(row["peak_rss_bytes"]) for row in resources),
        "peak_process_count": max(int(row["peak_process_count"]) for row in resources),
        "peak_thread_count": max(int(row["peak_thread_count"]) for row in resources),
        "worker_count": max(int(row["worker_count"]) for row in resources),
        "io_read_bytes": sum(int(row["io_read_bytes"]) for row in resources),
        "io_write_bytes": sum(int(row["io_write_bytes"]) for row in resources),
        "io_other_bytes": sum(int(row["io_other_bytes"]) for row in resources),
        "aggregate_io_bytes": sum(int(row["aggregate_io_bytes"]) for row in resources),
        "scratch_peak_bytes": max(int(row["scratch_peak_bytes"]) for row in resources),
        "durable_peak_bytes": max(int(row["durable_peak_bytes"]) for row in resources),
    }
    stage_events = [dict(event) for row in terminals for event in row["payload"]["stage_events"]]
    return {
        "admissions": admissions,
        "attempts": terminals,
        "checkpoint_sequence": checkpoints,
        "aggregate_resources": aggregate,
        "stage_events": stage_events,
    }


def _validate_embedded_journal(entries: Sequence[Mapping[str, Any]], *, config: ScoutConfig, run_binding: RunBinding) -> None:
    required = {"format", "schema_version", "sequence", "kind", "attempt_id", "config", "run_binding", "payload"}
    last_snapshot: dict[str, Mapping[str, Any]] = {}
    for sequence, row in enumerate(entries):
        if not isinstance(row, Mapping) or set(row) != required or row["format"] != RESOURCE_JOURNAL_FORMAT or row["schema_version"] != 1 or row["sequence"] != sequence:
            raise RunnerRefusal("embedded resource journal structure/sequence mismatch")
        if row["config"] != config.to_dict() or row["run_binding"] != run_binding.to_dict():
            raise RunnerRefusal("embedded resource journal binding mismatch")
        _reject_journal_science(row["payload"])
        if row["kind"] == "CHECKPOINT":
            if set(row["payload"]) != {"identity", "resources"}:
                raise RunnerRefusal("embedded checkpoint journal payload mismatch")
            _validate_checkpoint_snapshot(row["payload"]["resources"], last_snapshot.get(row["attempt_id"]))
            last_snapshot[row["attempt_id"]] = row["payload"]["resources"]
        elif row["kind"] == "ADMISSION":
            if set(row["payload"]) != {"passed", "receipt", "error"}:
                raise RunnerRefusal("embedded admission journal payload mismatch")
        elif row["kind"] == "CORE_TERMINAL":
            if set(row["payload"]) != {"status", "phase", "resources", "stage_events", "error"}:
                raise RunnerRefusal("embedded terminal journal payload mismatch")
            if row["payload"]["resources"] is not None:
                _validate_terminal_resources(row["payload"]["resources"])
        elif row["kind"] == "PUBLICATION_TERMINAL":
            if set(row["payload"]) != {"status", "phase", "resources", "error"}:
                raise RunnerRefusal("embedded publication terminal journal payload mismatch")
            if row["payload"]["resources"] is not None:
                _validate_terminal_resources(row["payload"]["resources"])
        else:
            raise RunnerRefusal("embedded resource journal kind mismatch")


def _validate_resource_cap(resources: Mapping[str, Any], cap: Mapping[str, Any]) -> None:
    if (
        float(resources["wall_seconds"]) > cap["wall_seconds"]
        or int(resources["peak_rss_bytes"]) > cap["peak_rss_bytes"]
        or int(resources["scratch_peak_bytes"]) > cap["scratch_bytes"]
        or int(resources["durable_peak_bytes"]) > cap["durable_bytes"]
        or int(resources["worker_count"]) > cap["workers"]
        or int(resources["peak_process_count"]) > cap["processes"]
        or int(resources["peak_thread_count"]) > cap["threads"]
    ):
        raise RunnerRefusal("B1 aggregate resource cap exceeded")


def _resource_ledger(
    *,
    config: ScoutConfig,
    run_binding: RunBinding,
    cap: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
    checkpoint_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    _validate_embedded_journal(entries, config=config, run_binding=run_binding)
    summary = _journal_summary(entries, config)
    _validate_resource_cap(summary["aggregate_resources"], cap)
    return {
        "format": RESOURCE_LEDGER_FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "config": config.to_dict(),
        "run_binding": run_binding.to_dict(),
        "resource_cap": dict(cap),
        "journal_entries": [dict(row) for row in entries],
        "journal_aggregate_sha256": _journal_aggregate(entries),
        "admissions": summary["admissions"],
        "attempts": summary["attempts"],
        "checkpoint_sequence": summary["checkpoint_sequence"],
        "checkpoint_inventory_aggregate_sha256": hashlib.sha256(canonical_json_bytes(list(checkpoint_inventory))).hexdigest(),
        "aggregate_resources": summary["aggregate_resources"],
        "stage_events": summary["stage_events"],
    }


def _aggregate_publication_resources(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    terminals = [row for row in entries if row["kind"] == "PUBLICATION_TERMINAL"]
    if not terminals or any(not isinstance(row["payload"]["resources"], Mapping) for row in terminals):
        raise RunnerRefusal("publication attempts lack complete terminal resources")
    rows = [row["payload"]["resources"] for row in terminals]
    for row in rows:
        _validate_terminal_resources(row)
    wall = sum(float(row["wall_seconds"]) for row in rows)
    cpu = sum(float(row["cpu_seconds"]) for row in rows)
    logical = max(1, os.cpu_count() or 1)
    return {
        "measurement_complete": True,
        "measurement_source": "AGGREGATED_PUBLICATION_ATTEMPTS",
        "sample_interval_seconds": max(float(row["sample_interval_seconds"]) for row in rows),
        "sample_count": sum(int(row["sample_count"]) for row in rows),
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "cpu_core_equivalents": 0.0 if wall <= 0 else cpu / wall,
        "host_cpu_occupancy": 0.0 if wall <= 0 else cpu / (wall * logical),
        "peak_rss_bytes": max(int(row["peak_rss_bytes"]) for row in rows),
        "peak_process_count": max(int(row["peak_process_count"]) for row in rows),
        "peak_thread_count": max(int(row["peak_thread_count"]) for row in rows),
        "worker_count": max(int(row["worker_count"]) for row in rows),
        "accelerator": "NOT_APPLICABLE_CPU_ONLY",
        "peak_accelerator_memory_bytes": max(int(row["peak_accelerator_memory_bytes"]) for row in rows),
        "io_read_bytes": sum(int(row["io_read_bytes"]) for row in rows),
        "io_write_bytes": sum(int(row["io_write_bytes"]) for row in rows),
        "io_other_bytes": sum(int(row["io_other_bytes"]) for row in rows),
        "aggregate_io_bytes": sum(int(row["aggregate_io_bytes"]) for row in rows),
        "scratch_peak_bytes": max(int(row["scratch_peak_bytes"]) for row in rows),
        "durable_peak_bytes": max(int(row["durable_peak_bytes"]) for row in rows),
    }


def _combine_core_publication_resources(
    core: Mapping[str, Any], publication: Mapping[str, Any], terminal_bytes: int,
    journal_reservation: Mapping[str, int],
) -> dict[str, Any]:
    if type(terminal_bytes) is not int or terminal_bytes <= 0:
        raise RunnerRefusal("terminal receipt reservation must be a positive exact byte count")
    return {
        "core_attempt_count": int(core["attempt_count"]),
        "wall_seconds": float(core["wall_seconds"]) + float(publication["wall_seconds"]),
        "cpu_seconds": float(core["cpu_seconds"]) + float(publication["cpu_seconds"]),
        "peak_rss_bytes": max(int(core["peak_rss_bytes"]), int(publication["peak_rss_bytes"])),
        "peak_process_count": max(int(core["peak_process_count"]), int(publication["peak_process_count"])),
        "peak_thread_count": max(int(core["peak_thread_count"]), int(publication["peak_thread_count"])),
        "worker_count": max(int(core["worker_count"]), int(publication["worker_count"])),
        "publication_attempt_count": int(publication["publication_attempt_count"]),
        "io_read_bytes": int(core["io_read_bytes"]) + int(publication["io_read_bytes"]) + terminal_bytes + journal_reservation["io_read_bytes"],
        "io_write_bytes": int(core["io_write_bytes"]) + int(publication["io_write_bytes"]) + terminal_bytes + journal_reservation["io_write_bytes"],
        "io_other_bytes": int(core["io_other_bytes"]) + int(publication["io_other_bytes"]),
        "aggregate_io_bytes": int(core["aggregate_io_bytes"]) + int(publication["aggregate_io_bytes"]) + 2 * terminal_bytes + journal_reservation["aggregate_io_bytes"],
        "scratch_peak_bytes": max(int(core["scratch_peak_bytes"]), int(publication["scratch_peak_bytes"])),
        "durable_peak_bytes": max(int(core["durable_peak_bytes"]), int(publication["durable_peak_bytes"])) + terminal_bytes + journal_reservation["durable_bytes"],
        "terminal_receipt_size_bytes": terminal_bytes,
    }


def _terminal_receipt_from_preterminal(
    *,
    preterminal: Mapping[str, Any],
    publication_terminal_entry: Mapping[str, Any],
    cap: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes]:
    full_entries = [*preterminal["resource_ledger"]["journal_entries"], dict(publication_terminal_entry)]
    _validate_embedded_journal(full_entries, config=ScoutConfig.from_dict(preterminal["config"]), run_binding=RunBinding.from_value(preterminal["run_binding"], "B1"))
    publication_resources = _aggregate_publication_resources(full_entries)
    publication_resources = {**publication_resources, "publication_attempt_count": sum(row["kind"] == "PUBLICATION_TERMINAL" for row in full_entries)}
    prior_journal_bytes = sum(len(canonical_json_bytes(row)) for row in preterminal["resource_ledger"]["journal_entries"])
    full_journal_bytes = sum(len(canonical_json_bytes(row)) for row in full_entries)
    publication_entry_bytes = len(canonical_json_bytes(publication_terminal_entry))
    journal_reservation = {
        "io_read_bytes": prior_journal_bytes + full_journal_bytes,
        "io_write_bytes": publication_entry_bytes,
        "aggregate_io_bytes": prior_journal_bytes + full_journal_bytes + publication_entry_bytes,
        "durable_bytes": full_journal_bytes,
        "basis": "CREATE_ONCE_PUBLICATION_TERMINAL_PLUS_PRE_AND_POST_APPEND_FULL_JOURNAL_READBACK",
    }
    terminal_bytes = 1
    for _ in range(16):
        reservation = {
            "size_bytes": terminal_bytes,
            "io_read_bytes": terminal_bytes,
            "io_write_bytes": terminal_bytes,
            "aggregate_io_bytes": 2 * terminal_bytes,
            "durable_bytes": terminal_bytes,
            "basis": "EXACT_CANONICAL_TERMINAL_BYTES_PLUS_ONE_LIGHTWEIGHT_READBACK",
        }
        combined = _combine_core_publication_resources(
            preterminal["resource_ledger"]["aggregate_resources"], publication_resources,
            terminal_bytes, journal_reservation,
        )
        _validate_resource_cap(combined, cap)
        value = {
            "format": TERMINAL_RECEIPT_FORMAT,
            "schema_version": 1,
            "object_id": OBJECT_ID,
            "complete": True,
            "config": preterminal["config"],
            "run_binding": preterminal["run_binding"],
            "result": preterminal["result_record"],
            "resource_ledger": preterminal["resource_ledger_record"],
            "checkpoint_count": preterminal["checkpoint_count"],
            "checkpoint_inventory_aggregate_sha256": preterminal["checkpoint_inventory_aggregate_sha256"],
            "journal_aggregate_sha256": preterminal["journal_aggregate_sha256"],
            "full_journal_aggregate_sha256": _journal_aggregate(full_entries),
            "manifest": preterminal["manifest_record"],
            "publication_terminal_entry": dict(publication_terminal_entry),
            "publication_resources": dict(publication_resources),
            "post_monitor_journal_reservation": journal_reservation,
            "terminal_receipt_reservation": reservation,
            "combined_resources": combined,
            "combined_cap": dict(cap),
            "combined_cap_pass": True,
        }
        encoded = canonical_json_bytes(value)
        if len(encoded) == terminal_bytes:
            return value, encoded
        terminal_bytes = len(encoded)
    raise RunnerRefusal("terminal receipt byte reservation did not converge")


def validate_failure_receipt(value: Mapping[str, Any], *, config: ScoutConfig, run_binding: RunBinding) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "complete", "attempt_id", "phase", "config",
        "run_binding", "admission", "resources", "error_type", "error",
    }
    if not isinstance(value, Mapping) or set(value) != required or value["format"] != FAILURE_RECEIPT_FORMAT or value["schema_version"] != 1 or value["object_id"] != OBJECT_ID or value["complete"] is not False:
        raise RunnerRefusal("failure receipt structure mismatch")
    if value["config"] != config.to_dict() or value["run_binding"] != run_binding.to_dict() or type(value["attempt_id"]) is not str or type(value["phase"]) is not str:
        raise RunnerRefusal("failure receipt identity/binding mismatch")
    if value["admission"] is not None and not isinstance(value["admission"], Mapping):
        raise RunnerRefusal("failure receipt admission must be object or null")
    if value["resources"] is not None:
        _validate_terminal_resources(value["resources"])
    _reject_journal_science({"admission": value["admission"], "resources": value["resources"]})
    return dict(value)


def validate_b1_preterminal_tree(
    complete_root: str | Path,
    manifest_path: str | Path,
    *,
    allow_terminal: bool = False,
) -> dict[str, Any]:
    root = Path(complete_root)
    manifest_file = Path(manifest_path)
    manifest = _validate_b1_manifest(_load_json(manifest_file), manifest_file)
    config = ScoutConfig.from_dict(manifest["config"])
    run_binding = RunBinding.from_value(manifest["run_binding"], "B1")
    result = _load_json(root / "result.json")
    ledger = _load_json(root / "resource-ledger.json")
    validate_complete_tree(result, complete_root=root, run_manifest=manifest)
    required_ledger = {
        "format", "schema_version", "object_id", "config", "run_binding", "resource_cap",
        "journal_entries", "journal_aggregate_sha256", "admissions", "attempts",
        "checkpoint_sequence", "checkpoint_inventory_aggregate_sha256", "aggregate_resources", "stage_events",
    }
    if set(ledger) != required_ledger or ledger["format"] != RESOURCE_LEDGER_FORMAT or ledger["schema_version"] != 1 or ledger["object_id"] != OBJECT_ID:
        raise RunnerRefusal("complete resource ledger structure mismatch")
    if ledger["config"] != config.to_dict() or ledger["run_binding"] != run_binding.to_dict() or ledger["resource_cap"] != manifest["resource_cap"]:
        raise RunnerRefusal("complete resource ledger binding mismatch")
    rebuilt = _resource_ledger(
        config=config, run_binding=run_binding, cap=manifest["resource_cap"],
        entries=ledger["journal_entries"], checkpoint_inventory=result["checkpoints"],
    )
    if ledger != rebuilt:
        raise RunnerRefusal("complete resource ledger does not recompute")
    resource_ref = result["runtime_refs"].get("resource")
    if not isinstance(resource_ref, Mapping) or set(resource_ref) != {"resource_ledger", "terminal_receipt_locator", "journal_aggregate_sha256", "manifest_sha256"} or resource_ref.get("resource_ledger") != _file_record(root / "resource-ledger.json", root) or resource_ref.get("terminal_receipt_locator") != "terminal-receipt.json" or resource_ref.get("journal_aggregate_sha256") != ledger["journal_aggregate_sha256"] or resource_ref.get("manifest_sha256") != _sha256_file(manifest_file):
        raise RunnerRefusal("scientific result resource/terminal reference mismatch")
    expected_files = {"result.json", "resource-ledger.json"} | {record["locator"] for record in result["checkpoints"]}
    if allow_terminal:
        expected_files.add("terminal-receipt.json")
    observed_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if observed_files != expected_files:
        raise RunnerRefusal("preterminal tree file inventory mismatch")
    return {
        "config": config.to_dict(),
        "run_binding": run_binding.to_dict(),
        "result": result,
        "resource_ledger": ledger,
        "result_record": _file_record(root / "result.json", root),
        "resource_ledger_record": _file_record(root / "resource-ledger.json", root),
        "checkpoint_count": len(result["checkpoints"]),
        "checkpoint_inventory_aggregate_sha256": ledger["checkpoint_inventory_aggregate_sha256"],
        "journal_aggregate_sha256": ledger["journal_aggregate_sha256"],
        "manifest_record": {
            "name": manifest_file.name,
            "size_bytes": manifest_file.stat().st_size,
            "sha256": _sha256_file(manifest_file),
        },
    }


def validate_b1_complete_tree(complete_root: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    root = Path(complete_root)
    manifest_file = Path(manifest_path)
    preterminal = validate_b1_preterminal_tree(root, manifest_file, allow_terminal=True)
    terminal = _load_json(root / "terminal-receipt.json")
    required_terminal = {
        "format", "schema_version", "object_id", "complete", "config", "run_binding", "result",
        "resource_ledger", "checkpoint_count", "checkpoint_inventory_aggregate_sha256",
        "journal_aggregate_sha256", "manifest", "publication_resources", "terminal_receipt_reservation",
        "combined_resources", "combined_cap", "combined_cap_pass", "publication_terminal_entry",
        "full_journal_aggregate_sha256", "post_monitor_journal_reservation",
    }
    if set(terminal) != required_terminal or terminal["format"] != TERMINAL_RECEIPT_FORMAT or terminal["complete"] is not True:
        raise RunnerRefusal("terminal receipt structure mismatch")
    expected_terminal, encoded = _terminal_receipt_from_preterminal(
        preterminal=preterminal,
        publication_terminal_entry=terminal["publication_terminal_entry"],
        cap=preterminal["resource_ledger"]["resource_cap"],
    )
    if terminal != expected_terminal or (root / "terminal-receipt.json").read_bytes() != encoded:
        raise RunnerRefusal("terminal receipt/result/ledger/checkpoint/manifest binding mismatch")
    manifest = _validate_b1_manifest(_load_json(manifest_file), manifest_file)
    config = ScoutConfig.from_dict(manifest["config"])
    run_binding = RunBinding.from_value(manifest["run_binding"], "B1")
    observed_journal = _load_resource_journal(
        _control_root(manifest_file, manifest), config=config, run_binding=run_binding,
    )
    expected_journal = [
        *preterminal["resource_ledger"]["journal_entries"], terminal["publication_terminal_entry"],
    ]
    if observed_journal != expected_journal:
        raise RunnerRefusal("terminal receipt does not bind the persistent full resource journal")
    if _directory_size(root) > terminal["combined_cap"]["durable_bytes"]:
        raise RunnerRefusal("final complete directory exceeds the combined durable cap")
    return {"result": preterminal["result"], "resource_ledger": preterminal["resource_ledger"], "terminal_receipt": terminal}


def _publication_residues(output: Path) -> list[Path]:
    if not output.exists():
        return []
    if output.is_symlink() or not output.is_dir():
        raise RunnerRefusal("B1 output root is not a plain directory")
    prefixes = (".complete-staging-", ".complete-postvalidated-", ".publication-scratch-")
    residues = sorted(
        (path for path in output.iterdir() if path.name.startswith(prefixes)),
        key=lambda path: path.name,
    )
    if any(path.is_symlink() for path in residues):
        raise RunnerRefusal("B1 publication residue contains a symlink")
    return residues


def _recover_pending_publication(
    *,
    output: Path,
    complete: Path,
    manifest_path: Path,
    entries: Sequence[Mapping[str, Any]],
) -> Path | None:
    """Refuse cross-invocation publication residues without external effects.

    Recovery would itself be a result-bearing resume requiring a new admission,
    process-tree observation, and terminal binding. This schema intentionally
    has no second commit transaction, so an interrupted hidden publication
    permanently closes this RunBinding and requires a fresh manifest/output.
    """
    residues = _publication_residues(output)
    if complete.exists():
        if residues:
            raise RunnerRefusal("immutable complete tree coexists with unbound publication residue")
        return None
    final = entries[-1] if entries else None
    recoverable = (
        isinstance(final, Mapping)
        and final.get("kind") == "PUBLICATION_TERMINAL"
        and final.get("payload", {}).get("status") == "COMPLETE"
    )
    if not recoverable:
        if residues:
            raise RunnerRefusal(
                "unbound publication residue is quarantined; this RunBinding cannot resume"
            )
        return None
    raise RunnerRefusal(
        "publication was interrupted before the visible atomic commit; this RunBinding cannot resume"
    )


def run_b1(manifest_path: str | Path, output_root: str | Path, *, resume: bool) -> Path:
    manifest_file = Path(manifest_path).resolve()
    output = Path(output_root).resolve()
    attempt_id = uuid.uuid4().hex
    config = ScoutConfig.b1()
    phase = "LOAD_MANIFEST"
    manifest: dict[str, Any] | None = None
    run_binding: RunBinding | None = None
    control: Path | None = None
    admission: dict[str, Any] | None = None
    resources: dict[str, Any] | None = None
    monitor: ProcessTreeMonitor | None = None
    publication_monitor: ProcessTreeMonitor | None = None
    publication_resources: dict[str, Any] | None = None
    staging: Path | None = None
    postvalidated: Path | None = None
    publication_scratch: Path | None = None
    complete = output / "complete"
    stage_events: list[dict[str, Any]] = []
    admission_journaled = False
    try:
        manifest = _validate_b1_manifest(_load_json(manifest_file), manifest_file)
        run_binding = RunBinding.from_value(manifest["run_binding"], "B1")
        control = _control_root(manifest_file, manifest)
        control.mkdir(parents=True, exist_ok=True)
        prior_entries = _load_resource_journal(control, config=config, run_binding=run_binding, live_attempt_id="*")
        recovered = _recover_pending_publication(
            output=output, complete=complete, manifest_path=manifest_file, entries=prior_entries,
        )
        if recovered is not None:
            return recovered
        _validate_resumable_prior_journal(prior_entries)
        if complete.exists():
            raise RunnerRefusal("complete B1 namespace already exists")

        phase = "CENTRAL_MEMORY_ADMISSION"
        admission_path = control / "admissions" / f"attempt-{attempt_id}.json"
        try:
            admission = _run_memory_admission(admission_path)
            admission_payload = {"passed": True, "receipt": admission, "error": None}
        except BaseException as admission_error:
            if admission_path.is_file():
                with contextlib.suppress(BaseException):
                    admission = _load_json(admission_path)
            admission_payload = {"passed": False, "receipt": admission, "error": f"{type(admission_error).__name__}: {admission_error}"}
            _append_resource_journal(control, config=config, run_binding=run_binding, attempt_id=attempt_id, kind="ADMISSION", payload=admission_payload)
            admission_journaled = True
            raise
        _append_resource_journal(control, config=config, run_binding=run_binding, attempt_id=attempt_id, kind="ADMISSION", payload=admission_payload)
        admission_journaled = True

        phase = "IMPORT_FIREWALL"
        _validate_import_firewall()
        phase = "OUTPUT_PREPARE"
        work = output / "work"
        if resume:
            if not work.is_dir():
                raise RunnerRefusal("resume requires the existing transient work namespace")
        else:
            if output.exists():
                raise RunnerRefusal("fresh B1 output root is create-once")
            work.mkdir(parents=True)
        live_entries = _load_resource_journal(control, config=config, run_binding=run_binding, live_attempt_id=attempt_id)
        journal_checkpoints = [dict(row["payload"]["identity"]) for row in live_entries if row["kind"] == "CHECKPOINT"]
        if _work_checkpoint_sequence(work, config=config, run_binding=run_binding) != journal_checkpoints:
            raise RunnerRefusal("transient checkpoint tree and persistent resource journal diverge")
        staging = output / f".complete-staging-{attempt_id}"
        staging.mkdir(parents=True)
        phase = "MONITOR_START"
        monitor = ProcessTreeMonitor(work, staging).start()

        import torch
        cap = manifest["resource_cap"]
        if int(torch.get_num_threads()) != cap["torch_intraop_threads"] or int(torch.get_num_interop_threads()) != cap["torch_interop_threads"]:
            raise RunnerRefusal("B1 torch thread runtime differs from the frozen cap")

        def observe_stage(event: Mapping[str, Any]) -> None:
            nonlocal phase
            projected = _outcome_free_stage_event(event)
            stage_events.append(projected)
            if projected["stage"] == "checkpoint":
                phase = "CHECKPOINT"
                identity = {name: projected[name] for name in ("arm_id", "seed_id", "fold_id", "root_update")}
                _append_resource_journal(
                    control, config=config, run_binding=run_binding, attempt_id=attempt_id,
                    kind="CHECKPOINT", payload={"identity": identity, "resources": monitor.snapshot()},
                )
                phase = "CORE_WORKLOAD"

        phase = "CORE_WORKLOAD"
        result = run_workload(config, work, stage_callback=observe_stage, run_binding=run_binding)
        phase = "CHECKPOINT_STAGING"
        inventory = stage_checkpoint_inventory(config, result.checkpoints, staging_root=staging, run_binding=run_binding)
        phase = "MONITOR_FINISH"
        resources = monitor.finish()
        monitor = None
        publication_scratch = output / f".publication-scratch-{attempt_id}"
        publication_scratch.mkdir()
        phase = "PUBLICATION_MONITOR_START"
        publication_monitor = ProcessTreeMonitor(publication_scratch, staging).start()
        phase = "CORE_TERMINAL"
        _append_resource_journal(
            control, config=config, run_binding=run_binding, attempt_id=attempt_id,
            kind="CORE_TERMINAL",
            payload={"status": "COMPLETE", "phase": phase, "resources": resources, "stage_events": stage_events, "error": None},
        )
        entries = _load_resource_journal(
            control, config=config, run_binding=run_binding, live_attempt_id=attempt_id,
        )
        ledger = _resource_ledger(config=config, run_binding=run_binding, cap=cap, entries=entries, checkpoint_inventory=inventory)
        phase = "RESOURCE_LEDGER_PUBLICATION"
        atomic_create_json(staging / "resource-ledger.json", ledger)
        resource_reference = {
            "resource_ledger": _file_record(staging / "resource-ledger.json", staging),
            "terminal_receipt_locator": "terminal-receipt.json",
            "journal_aggregate_sha256": ledger["journal_aggregate_sha256"],
            "manifest_sha256": _sha256_file(manifest_file),
        }
        merged_stage_times = [
            event for event in ledger["stage_events"]
            if event.get("stage") in {"fresh_data", "policy"} and "wall_seconds" in event and "cpu_seconds" in event
        ]
        phase = "RESULT_PUBLICATION"
        document = _scientific_document(result, resource_reference, inventory, artifact_root=staging, stage_times=merged_stage_times)
        publish_complete(staging / "result.json", document, artifact_root=staging)
        phase = "STAGING_PRETERMINAL_VALIDATION"
        staging_preterminal = validate_b1_preterminal_tree(staging, manifest_file)
        postvalidated = output / f".complete-postvalidated-{attempt_id}"
        if postvalidated.exists():
            raise RunnerRefusal("hidden post-validation namespace already exists")
        phase = "ATOMIC_HIDDEN_POSTVALIDATION_RENAME"
        publication_monitor.rename_durable_root(staging, postvalidated)
        staging = None
        phase = "HIDDEN_POSTVALIDATION_PRETERMINAL_VALIDATION"
        complete_preterminal = validate_b1_preterminal_tree(postvalidated, manifest_file)
        if {
            key: staging_preterminal[key]
            for key in ("config", "run_binding", "result_record", "resource_ledger_record", "checkpoint_count", "checkpoint_inventory_aggregate_sha256", "journal_aggregate_sha256", "manifest_record")
        } != {
            key: complete_preterminal[key]
            for key in ("config", "run_binding", "result_record", "resource_ledger_record", "checkpoint_count", "checkpoint_inventory_aggregate_sha256", "journal_aggregate_sha256", "manifest_record")
        }:
            raise RunnerRefusal("staging/hidden-postvalidation bindings differ after rename")
        phase = "PUBLICATION_MONITOR_FINISH"
        publication_resources = publication_monitor.finish()
        publication_monitor = None
        if publication_scratch.exists():
            publication_scratch.rmdir()
        publication_scratch = None

        # Build against the exact prospective create-once journal row first.  A
        # cap/schema failure therefore records PUBLICATION_TERMINAL/FAILED rather
        # than prematurely claiming that publication completed.
        publication_terminal_entry = {
            "format": RESOURCE_JOURNAL_FORMAT,
            "schema_version": 1,
            "sequence": len(entries),
            "kind": "PUBLICATION_TERMINAL",
            "attempt_id": attempt_id,
            "config": config.to_dict(),
            "run_binding": run_binding.to_dict(),
            "payload": {
                "status": "COMPLETE",
                "phase": phase,
                "resources": publication_resources,
                "error": None,
            },
        }
        phase = "TERMINAL_RECEIPT_RESERVATION"
        terminal, terminal_bytes = _terminal_receipt_from_preterminal(
            preterminal=complete_preterminal,
            publication_terminal_entry=publication_terminal_entry,
            cap=cap,
        )
        phase = "TERMINAL_RECEIPT_PUBLICATION"
        terminal_path = postvalidated / "terminal-receipt.json"
        atomic_create_json(terminal_path, terminal)
        if terminal_path.read_bytes() != terminal_bytes:
            raise RunnerRefusal("terminal receipt create-once bytes differ from the reserved bytes")
        expected_files = {"result.json", "resource-ledger.json", "terminal-receipt.json"} | {
            record["locator"] for record in complete_preterminal["result"]["checkpoints"]
        }
        observed_files = {path.relative_to(postvalidated).as_posix() for path in postvalidated.rglob("*") if path.is_file()}
        if observed_files != expected_files:
            raise RunnerRefusal("final lightweight complete file inventory mismatch")
        if _directory_size(postvalidated) > terminal["combined_cap"]["durable_bytes"]:
            raise RunnerRefusal("final complete directory exceeds the combined durable cap")
        phase = "PUBLICATION_TERMINAL"
        written_publication_terminal = _append_resource_journal(
            control, config=config, run_binding=run_binding, attempt_id=attempt_id,
            kind="PUBLICATION_TERMINAL", payload=publication_terminal_entry["payload"],
        )
        if written_publication_terminal != publication_terminal_entry:
            raise RunnerRefusal("publication terminal journal bytes differ from the reserved entry")
        phase = "ATOMIC_VISIBLE_COMPLETE_RENAME"
        os.replace(postvalidated, complete)
        postvalidated = None
        if work.exists():
            with contextlib.suppress(OSError):
                shutil.rmtree(work)
        return complete / "result.json"
    except BaseException as exc:
        if publication_monitor is not None:
            with contextlib.suppress(BaseException):
                publication_resources = publication_monitor.finish()
        if monitor is not None:
            with contextlib.suppress(BaseException):
                resources = monitor.finish()
        if control is not None and run_binding is not None and admission_journaled:
            with contextlib.suppress(BaseException):
                observed = _load_resource_journal(
                    control, config=config, run_binding=run_binding, live_attempt_id="*",
                )
                attempt_rows = [row for row in observed if row["attempt_id"] == attempt_id]
                core_rows = [row for row in attempt_rows if row["kind"] == "CORE_TERMINAL"]
                publication_rows = [row for row in attempt_rows if row["kind"] == "PUBLICATION_TERMINAL"]
                if not core_rows:
                    _append_resource_journal(
                        control, config=config, run_binding=run_binding, attempt_id=attempt_id,
                        kind="CORE_TERMINAL",
                        payload={"status": "FAILED", "phase": phase, "resources": resources, "stage_events": stage_events, "error": f"{type(exc).__name__}: {exc}"},
                    )
                elif (
                    core_rows[-1]["payload"]["status"] == "COMPLETE"
                    and not publication_rows
                    and not (postvalidated is not None and (postvalidated / "terminal-receipt.json").is_file())
                ):
                    _append_resource_journal(
                        control, config=config, run_binding=run_binding, attempt_id=attempt_id,
                        kind="PUBLICATION_TERMINAL",
                        payload={"status": "FAILED", "phase": phase, "resources": publication_resources, "error": f"{type(exc).__name__}: {exc}"},
                    )
        if control is not None and run_binding is not None:
            failure = {
                "format": FAILURE_RECEIPT_FORMAT, "schema_version": 1, "object_id": OBJECT_ID,
                "complete": False, "attempt_id": attempt_id, "phase": phase,
                "config": config.to_dict(), "run_binding": run_binding.to_dict(),
                "admission": admission, "resources": publication_resources or resources,
                "error_type": type(exc).__name__, "error": str(exc),
            }
            with contextlib.suppress(FileExistsError):
                atomic_create_json(
                    control / "failure-receipts" / f"attempt-{attempt_id}.json",
                    validate_failure_receipt(failure, config=config, run_binding=run_binding),
                )
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        preserve_postvalidated = False
        if postvalidated is not None and postvalidated.exists() and control is not None and run_binding is not None:
            preserve_postvalidated = (postvalidated / "terminal-receipt.json").is_file()
            with contextlib.suppress(BaseException):
                observed = _load_resource_journal(
                    control, config=config, run_binding=run_binding, live_attempt_id="*",
                )
                attempt_rows = [row for row in observed if row["attempt_id"] == attempt_id]
                preserve_postvalidated = preserve_postvalidated or any(
                    row["kind"] == "PUBLICATION_TERMINAL" and row["payload"]["status"] == "COMPLETE"
                    for row in attempt_rows
                )
        if postvalidated is not None and postvalidated.exists() and not preserve_postvalidated:
            shutil.rmtree(postvalidated)
        if publication_scratch is not None and publication_scratch.exists():
            shutil.rmtree(publication_scratch)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("describe", allow_abbrev=False)
    assess = commands.add_parser("assess-run", allow_abbrev=False)
    assess.add_argument("--output-root", required=True)
    create = commands.add_parser("create-b1-manifest", allow_abbrev=False)
    create.add_argument("--assessment", required=True)
    create.add_argument("--manifest", required=True)
    run = commands.add_parser("run-b1", allow_abbrev=False)
    run.add_argument("--manifest", required=True)
    run.add_argument("--output-root", required=True)
    resume = commands.add_parser("resume-b1", allow_abbrev=False)
    resume.add_argument("--manifest", required=True)
    resume.add_argument("--output-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "describe":
            print(json.dumps({
                "object_id": OBJECT_ID,
                "commands": ["describe", "assess-run", "create-b1-manifest", "run-b1", "resume-b1"],
                "b1": ScoutConfig.b1().to_dict(),
                "assess": ScoutConfig.assess().to_dict(),
            }, sort_keys=True))
            return 0
        if args.command == "assess-run":
            path = assess_run(args.output_root)
        elif args.command == "create-b1-manifest":
            path = create_b1_manifest(args.assessment, args.manifest)
        elif args.command == "run-b1":
            path = run_b1(args.manifest, args.output_root, resume=False)
        elif args.command == "resume-b1":
            path = run_b1(args.manifest, args.output_root, resume=True)
        else:  # pragma: no cover
            raise AssertionError("unreachable command")
        print(json.dumps({"complete": True, "path": str(path)}, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, RunnerRefusal) as exc:
        print(f"UCOPE scout runner refused: {exc}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
