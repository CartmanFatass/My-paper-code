"""Continuous result-process resource telemetry for SCDMP B01."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import math
from pathlib import Path
import os
import sys
import threading
import time
from typing import Callable, Mapping


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    peak_rss_bytes: int = 2 * 1024**3
    scratch_bytes: int = 256 * 1024**2
    durable_bytes: int = 256 * 1024**2
    wall_seconds: float = 1_800.0


@dataclass(frozen=True, slots=True)
class ResourceTelemetry:
    passed: bool
    failure_reasons: tuple[str, ...]
    sample_count: int
    process_tree_peak_rss_bytes: int
    scratch_high_water_bytes: int
    durable_high_water_bytes: int
    wall_seconds: float
    cpu_seconds: float
    cpu_utilization_fraction: float
    max_process_count: int
    max_thread_count: int
    start_available_memory_bytes: int | None
    end_available_memory_bytes: int | None
    exit_status: int


def _tree_snapshot() -> dict[str, int | float]:
    if sys.platform == "win32":
        return _windows_tree_snapshot()
    if sys.platform.startswith("linux"):
        return _linux_tree_snapshot()
    raise RuntimeError("process-tree telemetry is unsupported on this platform")


def _filetime_seconds(value: object) -> float:
    high = int(getattr(value, "dwHighDateTime"))
    low = int(getattr(value, "dwLowDateTime"))
    return ((high << 32) | low) / 10_000_000.0


def _windows_tree_snapshot() -> dict[str, int | float]:
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = (
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        )

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = (
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        )

    class MemoryStatus(ctypes.Structure):
        _fields_ = (
            ("length", wintypes.DWORD), ("memory_load", wintypes.DWORD),
            ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        )

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry))
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry))
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
    )
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
    )
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise OSError("CreateToolhelp32Snapshot failed")
    entries: dict[int, tuple[int, int]] = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        available = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while available:
            entries[int(entry.th32ProcessID)] = (
                int(entry.th32ParentProcessID), int(entry.cntThreads)
            )
            available = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    selected = {os.getpid()}
    changed = True
    while changed:
        before = len(selected)
        selected.update(pid for pid, (parent, _threads) in entries.items() if parent in selected)
        changed = len(selected) != before
    rss = 0
    cpu = 0.0
    threads = 0
    observed = 0
    for pid in sorted(selected):
        handle = kernel32.OpenProcess(0x00001000 | 0x00000400, False, pid)
        if not handle:
            continue
        try:
            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            created = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                continue
            if not kernel32.GetProcessTimes(
                handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)
            ):
                continue
            rss += int(counters.WorkingSetSize)
            cpu += _filetime_seconds(kernel) + _filetime_seconds(user)
            threads += entries.get(pid, (0, 0))[1]
            observed += 1
        finally:
            kernel32.CloseHandle(handle)
    memory = MemoryStatus()
    memory.length = ctypes.sizeof(memory)
    if observed < 1 or not kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise RuntimeError("result process tree cannot be observed")
    return {
        "process_tree_rss_bytes": rss,
        "cpu_seconds": cpu,
        "process_count": observed,
        "thread_count": threads,
        "available_memory_bytes": int(memory.available_physical),
    }


def _linux_tree_snapshot() -> dict[str, int | float]:
    process_rows: dict[int, tuple[int, int, int, float]] = {}
    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    ticks = int(os.sysconf("SC_CLK_TCK"))
    for stat_path in Path("/proc").glob("[0-9]*/stat"):
        try:
            raw = stat_path.read_text(encoding="ascii")
            fields = raw[raw.rfind(")") + 2:].split()
            pid = int(stat_path.parent.name)
            process_rows[pid] = (
                int(fields[1]), int(fields[17]), int(fields[21]) * page_size,
                (int(fields[11]) + int(fields[12])) / ticks,
            )
        except (OSError, ValueError, IndexError):
            continue
    selected = {os.getpid()}
    changed = True
    while changed:
        before = len(selected)
        selected.update(pid for pid, (parent, _threads, _rss, _cpu) in process_rows.items() if parent in selected)
        changed = len(selected) != before
    rows = tuple(process_rows[pid] for pid in selected if pid in process_rows)
    if not rows:
        raise RuntimeError("result process tree cannot be observed")
    meminfo = {}
    for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
        key, value = line.split(":", 1)
        meminfo[key] = int(value.strip().split()[0]) * 1024
    return {
        "process_tree_rss_bytes": sum(row[2] for row in rows),
        "cpu_seconds": sum(row[3] for row in rows),
        "process_count": len(rows),
        "thread_count": sum(row[1] for row in rows),
        "available_memory_bytes": meminfo["MemAvailable"],
    }


def _tree_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


class ContinuousResourceMonitor:
    """Sample the complete foreground process tree and artifact high waters."""

    def __init__(
        self,
        *,
        scratch_root: str | Path,
        durable_root: str | Path,
        snapshot_source: Callable[[], Mapping[str, object]] = _tree_snapshot,
        size_source: Callable[[Path, Path], tuple[int, int]] | None = None,
        clock: Callable[[], float] = time.perf_counter,
        limits: ResourceLimits = ResourceLimits(),
        interval_seconds: float = 0.05,
        autostart: bool = True,
    ) -> None:
        self.scratch_root = Path(scratch_root)
        self.durable_root = Path(durable_root)
        self.snapshot_source = snapshot_source
        self.size_source = size_source or (lambda scratch, durable: (_tree_bytes(scratch), _tree_bytes(durable)))
        self.clock = clock
        self.limits = limits
        self.interval_seconds = interval_seconds
        self._started_at = float(clock())
        if not math.isfinite(self._started_at):
            raise ValueError("resource telemetry clock must be finite")
        self._last_at = self._started_at
        self._samples: list[tuple[dict[str, object], int, int]] = []
        self._direct_scratch_peak = 0
        self._errors: list[str] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        if autostart:
            self.start()

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("resource telemetry is already running")
        self._thread = threading.Thread(target=self._run, name="scdmp-b01-resource-monitor", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.sample_now()
            self._stop.wait(self.interval_seconds)

    def sample_now(self) -> None:
        try:
            snapshot = dict(self.snapshot_source())
            required = {
                "process_tree_rss_bytes", "cpu_seconds", "process_count", "thread_count",
                "available_memory_bytes",
            }
            if not required <= set(snapshot):
                raise ValueError("resource snapshot fields are missing")
            rss = snapshot["process_tree_rss_bytes"]
            cpu = snapshot["cpu_seconds"]
            processes = snapshot["process_count"]
            threads = snapshot["thread_count"]
            available_memory = snapshot["available_memory_bytes"]
            if (
                isinstance(rss, bool) or not isinstance(rss, int) or rss < 0
                or isinstance(cpu, bool) or not isinstance(cpu, (int, float))
                or not math.isfinite(float(cpu)) or cpu < 0
                or isinstance(processes, bool) or not isinstance(processes, int) or processes < 1
                or isinstance(threads, bool) or not isinstance(threads, int) or threads < 1
                or isinstance(available_memory, bool) or not isinstance(available_memory, int)
                or available_memory < 0
            ):
                raise ValueError("resource snapshot fields are invalid")
            scratch, durable = self.size_source(self.scratch_root, self.durable_root)
            if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (scratch, durable)):
                raise ValueError("artifact high-water observation is invalid")
            self._samples.append((snapshot, scratch, durable))
            observed_at = float(self.clock())
            if not math.isfinite(observed_at) or observed_at < self._last_at:
                raise ValueError("resource telemetry clock must be finite and monotonic")
            self._last_at = observed_at
        except Exception as error:  # measurement failure must survive to final fail-closed fact
            self._errors.append(type(error).__name__)
            self._stop.set()

    def observe_scratch_path(self, path: str | Path) -> None:
        """Observe an atomic temporary before unlink so polling cannot miss it."""

        try:
            size = _tree_bytes(Path(path))
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise ValueError("atomic scratch size is invalid")
            self._direct_scratch_peak = max(self._direct_scratch_peak, size)
        except Exception as error:
            self._errors.append(type(error).__name__)
            self._stop.set()
            raise RuntimeError("atomic scratch observation failed") from error

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=max(1.0, self.interval_seconds * 4))
        if self._thread.is_alive():
            self._errors.append("monitor_thread_did_not_stop")
        self._thread = None

    def finalize(self, *, exit_status: int) -> ResourceTelemetry:
        was_running = self._thread is not None
        self.stop()
        # Capture the terminal process/artifact state after the workload, so a
        # short run cannot end between polling ticks without entering RSS/CPU/
        # durable accounting. Manual injected tests already call sample_now.
        if was_running:
            self.sample_now()
        if not self._samples:
            return ResourceTelemetry(
                False, ("telemetry_missing",), 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0,
                None, None, int(exit_status),
            )
        rss_peak = max(int(row[0]["process_tree_rss_bytes"]) for row in self._samples)
        scratch_peak = max(self._direct_scratch_peak, *(row[1] for row in self._samples))
        durable_peak = max(row[2] for row in self._samples)
        wall = max(0.0, self._last_at - self._started_at)
        cpu_values = tuple(float(row[0]["cpu_seconds"]) for row in self._samples)
        # Descendants may exit before the terminal sample, so retain the
        # observed aggregate high-water rather than subtracting only endpoints.
        cpu = max(0.0, max(cpu_values) - min(cpu_values))
        reasons = []
        if self._errors:
            reasons.append("telemetry_measurement_failed")
        if rss_peak > self.limits.peak_rss_bytes:
            reasons.append("process_tree_peak_rss_exceeded")
        if scratch_peak > self.limits.scratch_bytes:
            reasons.append("scratch_high_water_exceeded")
        if durable_peak > self.limits.durable_bytes:
            reasons.append("durable_output_exceeded")
        if wall > self.limits.wall_seconds:
            reasons.append("wall_time_exceeded")
        if wall <= 0.0 or cpu <= 0.0:
            reasons.append("telemetry_zero_work")
        if int(exit_status) != 0:
            reasons.append("result_process_nonzero_exit")
        start_memory = self._samples[0][0].get("available_memory_bytes")
        end_memory = self._samples[-1][0].get("available_memory_bytes")
        return ResourceTelemetry(
            not reasons, tuple(reasons), len(self._samples), rss_peak, scratch_peak, durable_peak,
            wall, cpu, cpu / wall if wall > 0.0 else 0.0,
            max(int(row[0]["process_count"]) for row in self._samples),
            max(int(row[0]["thread_count"]) for row in self._samples),
            int(start_memory) if isinstance(start_memory, int) else None,
            int(end_memory) if isinstance(end_memory, int) else None,
            int(exit_status),
        )

    def __enter__(self) -> "ContinuousResourceMonitor":
        if self._thread is None:
            self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.stop()


__all__ = ["ContinuousResourceMonitor", "ResourceLimits", "ResourceTelemetry"]
