"""Continuous result-process resource telemetry for SCDMP B01."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import errno as errno_module
import hashlib
import math
from pathlib import Path
import os
import sys
import stat
import threading
import time
from typing import Callable, Final, Mapping, Sequence


# Section 11 recast, 2026-09-02.  Evidence-spec §11.4 does not allow telemetry
# completeness to hold a B launch, and owner decision 7 in
# docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md resolves
# the clause §11.4 left open as *downgrade, not annul*: a run whose resource
# telemetry is missing stays valid and is marked `resources_unmeasured`.  These
# are the failure reasons that mean "the measurement is missing or failed".
# Everything else -- a measured cap exceedance, a nonzero result-process exit --
# still invalidates the attempt exactly as before.
UNMEASURED_TELEMETRY_REASONS: Final[frozenset[str]] = frozenset({
    "telemetry_missing",
    "telemetry_measurement_failed",
    "telemetry_zero_work",
})


def partition_failure_reasons(
    reasons: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split telemetry failure reasons into (unmeasured, invalidating)."""

    materialized = tuple(str(reason) for reason in reasons)
    unmeasured = tuple(
        reason for reason in materialized if reason in UNMEASURED_TELEMETRY_REASONS
    )
    invalidating = tuple(
        reason for reason in materialized if reason not in UNMEASURED_TELEMETRY_REASONS
    )
    return unmeasured, invalidating


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    peak_rss_bytes: int = 2 * 1024**3
    scratch_bytes: int = 256 * 1024**2
    durable_bytes: int = 256 * 1024**2
    wall_seconds: float = 1_800.0


@dataclass(frozen=True, slots=True)
class MeasurementIncident:
    severity: str
    disposition: str
    exception_class: str
    phase: str
    path_summary: str
    errno: int | None
    winerror: int | None


class _MeasurementFailure(RuntimeError):
    def __init__(self, primary: BaseException, incident: MeasurementIncident) -> None:
        super().__init__(str(primary))
        self.primary = primary
        self.incidents = [incident]

    @property
    def incident(self) -> MeasurementIncident:
        return self.incidents[0]


def _preserve_primary_with_cleanup(
    primary: BaseException | None, cleanup: "_MeasurementFailure",
) -> "_MeasurementFailure":
    if primary is None:
        return cleanup
    if isinstance(primary, _MeasurementFailure):
        primary.incidents.extend(cleanup.incidents)
        return primary
    wrapped = _measurement_failure(
        primary, disposition="WINDOWS_MEASUREMENT_BODY_FAILED",
        phase="windows_measurement_body", path_summary="process-tree",
    )
    wrapped.incidents.extend(cleanup.incidents)
    return wrapped


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
    foreground_io_read_bytes: int = 0
    foreground_io_write_bytes: int = 0
    process_tree_io_read_bytes: int = 0
    process_tree_io_write_bytes: int = 0
    torch_intraop_threads: int = 0
    torch_interop_threads: int = 0
    os_cpu_count: int = 0
    native_internal_worker_threads: int = 0
    measurement_incidents: tuple[MeasurementIncident, ...] = ()


def _tree_snapshot() -> dict[str, object]:
    if sys.platform == "win32":
        result = _windows_tree_snapshot()
    elif sys.platform.startswith("linux"):
        result = _linux_tree_snapshot()
    else:
        raise RuntimeError("process-tree telemetry is unsupported on this platform")
    result.update(foreground_io_snapshot())
    return result


def foreground_io_snapshot() -> dict[str, int]:
    if sys.platform == "win32":
        from ctypes import wintypes

        class IoCounters(ctypes.Structure):
            _fields_ = (
                ("read_operations", ctypes.c_ulonglong), ("write_operations", ctypes.c_ulonglong),
                ("other_operations", ctypes.c_ulonglong), ("read_bytes", ctypes.c_ulonglong),
                ("write_bytes", ctypes.c_ulonglong), ("other_bytes", ctypes.c_ulonglong),
            )
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessIoCounters.argtypes = (wintypes.HANDLE, ctypes.POINTER(IoCounters))
        kernel32.GetProcessIoCounters.restype = wintypes.BOOL
        value = IoCounters()
        if not kernel32.GetProcessIoCounters(kernel32.GetCurrentProcess(), ctypes.byref(value)):
            error = ctypes.WinError(ctypes.get_last_error())
            raise _measurement_failure(
                error, disposition="FOREGROUND_IO_FAILED", phase="windows_foreground_io",
                path_summary="process-root",
            ) from error
        return {"foreground_io_read_bytes": int(value.read_bytes),
                "foreground_io_write_bytes": int(value.write_bytes)}
    rows = {}
    for line in Path("/proc/self/io").read_text(encoding="ascii").splitlines():
        key, value = line.split(":", 1)
        rows[key] = int(value.strip())
    return {"foreground_io_read_bytes": rows["read_bytes"],
            "foreground_io_write_bytes": rows["write_bytes"]}


def _filetime_seconds(value: object) -> float:
    high = int(getattr(value, "dwHighDateTime"))
    low = int(getattr(value, "dwLowDateTime"))
    return ((high << 32) | low) / 10_000_000.0


def _classify_open_process_failure(
    *, pid: int, root_pid: int, error: OSError,
) -> MeasurementIncident | None:
    code = getattr(error, "winerror", None)
    if pid != root_pid and code in {87, 1168}:
        return _incident(
            error, severity="TOLERATED",
            disposition="CHILD_EXITED_BEFORE_OPEN_PROCESS",
            phase="windows_open_process", path_summary="process-child",
        )
    return None


def _classify_process_sampling_failure(
    *, phase: str, pid: int, root_pid: int, error: OSError,
) -> MeasurementIncident | None:
    code = getattr(error, "winerror", None)
    if pid != root_pid and code in {6, 87, 1168}:
        return _incident(
            error, severity="TOLERATED",
            disposition="CHILD_EXITED_DURING_PROCESS_SAMPLING",
            phase=phase, path_summary="process-child",
        )
    return None


def _windows_tree_snapshot() -> dict[str, object]:
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

    class IoCounters(ctypes.Structure):
        _fields_ = (
            ("read_operations", ctypes.c_ulonglong), ("write_operations", ctypes.c_ulonglong),
            ("other_operations", ctypes.c_ulonglong), ("read_bytes", ctypes.c_ulonglong),
            ("write_bytes", ctypes.c_ulonglong), ("other_bytes", ctypes.c_ulonglong),
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
    kernel32.GetProcessIoCounters.argtypes = (wintypes.HANDLE, ctypes.POINTER(IoCounters))
    kernel32.GetProcessIoCounters.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
    )
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        error = ctypes.WinError(ctypes.get_last_error())
        raise _measurement_failure(
            error, disposition="PROCESS_SNAPSHOT_FAILED", phase="windows_process_snapshot",
            path_summary="process-tree",
        ) from error
    entries: dict[int, tuple[int, int]] = {}
    incidents: list[MeasurementIncident] = []
    snapshot_primary: BaseException | None = None
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        ctypes.set_last_error(0)
        available = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        if not available:
            error = ctypes.WinError(ctypes.get_last_error())
            raise _measurement_failure(
                error, disposition="PROCESS_ENUMERATION_FAILED",
                phase="windows_process_enumeration", path_summary="process-tree",
            ) from error
        while available:
            entries[int(entry.th32ProcessID)] = (
                int(entry.th32ParentProcessID), int(entry.cntThreads)
            )
            ctypes.set_last_error(0)
            available = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
            if not available:
                code = int(ctypes.get_last_error())
                if code not in {0, 18}:  # ERROR_NO_MORE_FILES is the only normal terminator.
                    error = ctypes.WinError(code)
                    raise _measurement_failure(
                        error, disposition="PROCESS_ENUMERATION_FAILED",
                        phase="windows_process_enumeration", path_summary="process-tree",
                    ) from error
    except BaseException as error:
        snapshot_primary = error
        raise
    finally:
        if not kernel32.CloseHandle(snapshot):
            error = ctypes.WinError(ctypes.get_last_error())
            cleanup = _measurement_failure(
                error, disposition="PROCESS_SNAPSHOT_CLOSE_FAILED",
                phase="windows_process_snapshot_close", path_summary="process-tree",
            )
            merged = _preserve_primary_with_cleanup(snapshot_primary, cleanup)
            if merged is not snapshot_primary:
                raise merged from (snapshot_primary or error)
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
    process_records = []
    for pid in sorted(selected):
        handle = kernel32.OpenProcess(0x00001000 | 0x00000400, False, pid)
        if not handle:
            code = int(ctypes.get_last_error())
            error = ctypes.WinError(code)
            tolerated = _classify_open_process_failure(
                pid=pid, root_pid=os.getpid(), error=error,
            )
            if tolerated is not None:
                incidents.append(tolerated)
                continue
            raise _measurement_failure(
                error, disposition="PROCESS_OPEN_FAILED", phase="windows_open_process",
                path_summary="process-root" if pid == os.getpid() else "process-child",
            ) from error
        process_primary: BaseException | None = None
        try:
            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            created = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            io = IoCounters()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                error = ctypes.WinError(ctypes.get_last_error())
                tolerated = _classify_process_sampling_failure(
                    phase="windows_process_memory", pid=pid, root_pid=os.getpid(), error=error,
                )
                if tolerated is not None:
                    incidents.append(tolerated)
                    continue
                raise _measurement_failure(
                    error, disposition="PROCESS_MEMORY_FAILED", phase="windows_process_memory",
                    path_summary="process-root" if pid == os.getpid() else "process-child",
                ) from error
            if not kernel32.GetProcessTimes(
                handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)
            ):
                error = ctypes.WinError(ctypes.get_last_error())
                tolerated = _classify_process_sampling_failure(
                    phase="windows_process_times", pid=pid, root_pid=os.getpid(), error=error,
                )
                if tolerated is not None:
                    incidents.append(tolerated)
                    continue
                raise _measurement_failure(
                    error, disposition="PROCESS_TIMES_FAILED", phase="windows_process_times",
                    path_summary="process-root" if pid == os.getpid() else "process-child",
                ) from error
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
                error = ctypes.WinError(ctypes.get_last_error())
                tolerated = _classify_process_sampling_failure(
                    phase="windows_process_io", pid=pid, root_pid=os.getpid(), error=error,
                )
                if tolerated is not None:
                    incidents.append(tolerated)
                    continue
                raise _measurement_failure(
                    error, disposition="PROCESS_IO_FAILED", phase="windows_process_io",
                    path_summary="process-root" if pid == os.getpid() else "process-child",
                ) from error
            rss += int(counters.WorkingSetSize)
            cpu += _filetime_seconds(kernel) + _filetime_seconds(user)
            threads += entries.get(pid, (0, 0))[1]
            observed += 1
            creation_ticks = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            process_records.append({
                "identity": f"{pid}:{creation_ticks}", "pid": pid,
                "cpu_seconds": _filetime_seconds(kernel) + _filetime_seconds(user),
                "io_read_bytes": int(io.read_bytes), "io_write_bytes": int(io.write_bytes),
            })
        except BaseException as error:
            process_primary = error
            raise
        finally:
            if not kernel32.CloseHandle(handle):
                error = ctypes.WinError(ctypes.get_last_error())
                cleanup = _measurement_failure(
                    error, disposition="PROCESS_HANDLE_CLOSE_FAILED",
                    phase="windows_process_handle_close",
                    path_summary="process-root" if pid == os.getpid() else "process-child",
                )
                merged = _preserve_primary_with_cleanup(process_primary, cleanup)
                if merged is not process_primary:
                    raise merged from (process_primary or error)
    memory = MemoryStatus()
    memory.length = ctypes.sizeof(memory)
    if observed < 1:
        raise RuntimeError("result process tree cannot be observed")
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        error = ctypes.WinError(ctypes.get_last_error())
        raise _measurement_failure(
            error, disposition="SYSTEM_MEMORY_FAILED", phase="windows_global_memory",
            path_summary="system-memory",
        ) from error
    return {
        "process_tree_rss_bytes": rss,
        "cpu_seconds": cpu,
        "process_count": observed,
        "thread_count": threads,
        "available_memory_bytes": int(memory.available_physical),
        "process_records": process_records,
        "measurement_incidents": incidents,
    }


def _linux_tree_snapshot() -> dict[str, object]:
    process_rows: dict[int, tuple[int, int, int, float, int, int, int]] = {}
    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    ticks = int(os.sysconf("SC_CLK_TCK"))
    for stat_path in Path("/proc").glob("[0-9]*/stat"):
        try:
            raw = stat_path.read_text(encoding="ascii")
            fields = raw[raw.rfind(")") + 2:].split()
            pid = int(stat_path.parent.name)
            io_values = {"read_bytes": 0, "write_bytes": 0}
            try:
                for line in (stat_path.parent / "io").read_text(encoding="ascii").splitlines():
                    key, value = line.split(":", 1)
                    if key in io_values:
                        io_values[key] = int(value.strip())
            except (OSError, ValueError):
                pass
            process_rows[pid] = (
                int(fields[1]), int(fields[17]), int(fields[21]) * page_size,
                (int(fields[11]) + int(fields[12])) / ticks,
                int(fields[19]), io_values["read_bytes"], io_values["write_bytes"],
            )
        except (OSError, ValueError, IndexError):
            continue
    selected = {os.getpid()}
    changed = True
    while changed:
        before = len(selected)
        selected.update(
            pid for pid, (parent, _threads, _rss, _cpu, _start, _read, _write)
            in process_rows.items() if parent in selected
        )
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
        "process_records": [
            {
                "identity": f"{pid}:{process_rows[pid][4]}", "pid": pid,
                "cpu_seconds": process_rows[pid][3],
                "io_read_bytes": process_rows[pid][5],
                "io_write_bytes": process_rows[pid][6],
            }
            for pid in selected if pid in process_rows
        ],
    }


def _path_summary(root: Path, path: Path) -> str:
    """Return a content-blind stable coordinate summary."""

    if path == root:
        return "measurement-root"
    try:
        relative = path.relative_to(root).as_posix().encode("utf-8", errors="surrogatepass")
    except ValueError:
        relative = b"outside-root"
    return f"descendant-sha256:{hashlib.sha256(relative).hexdigest()[:16]}"


def _incident(
    error: BaseException, *, severity: str, disposition: str, phase: str,
    path_summary: str,
) -> MeasurementIncident:
    return MeasurementIncident(
        severity, disposition, type(error).__name__, phase, path_summary,
        getattr(error, "errno", None), getattr(error, "winerror", None),
    )


def _measurement_failure(
    error: BaseException, *, disposition: str, phase: str, path_summary: str,
) -> _MeasurementFailure:
    return _MeasurementFailure(error, _incident(
        error, severity="FATAL", disposition=disposition, phase=phase,
        path_summary=path_summary,
    ))


def _is_reparse(stat_result: object) -> bool:
    return bool(int(getattr(stat_result, "st_file_attributes", 0) or 0) & 0x400)


def _stat_identity(stat_result: object) -> tuple[int, int] | None:
    device = getattr(stat_result, "st_dev", None)
    inode = getattr(stat_result, "st_ino", None)
    if (
        isinstance(device, int) and not isinstance(device, bool)
        and isinstance(inode, int) and not isinstance(inode, bool) and inode != 0
    ):
        return device, inode
    return None


def tree_bytes(
    path: Path,
    *,
    incident_sink: Callable[[MeasurementIncident], None] | None = None,
) -> int:
    root = Path(path)
    root_stat = root.stat(follow_symlinks=False)  # missing root is fatal
    root_identity = _stat_identity(root_stat)
    if root_identity is None:
        raise OSError("artifact measurement root has no stable filesystem identity")
    if stat.S_ISLNK(root_stat.st_mode) or _is_reparse(root_stat):
        raise OSError("artifact measurement root is a symlink or reparse point")
    if stat.S_ISREG(root_stat.st_mode):
        terminal = root.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(terminal.st_mode) or _is_reparse(terminal)
            or _stat_identity(terminal) is None
            or root_identity != _stat_identity(terminal)
        ):
            raise OSError("artifact measurement file identity changed during traversal")
        return int(root_stat.st_size)
    if not stat.S_ISDIR(root_stat.st_mode):
        raise OSError("artifact measurement root is not a regular file or directory")

    def scan_directory(directory: Path, initial: object) -> int:
        identity = _stat_identity(initial)
        if identity is None:
            raise OSError("artifact directory has no stable filesystem identity")
        if not stat.S_ISDIR(initial.st_mode) or _is_reparse(initial):
            raise OSError("artifact directory type changed before traversal")
        total = 0
        # scandir/open/iteration errors are intentionally not caught.  Only a
        # DirEntry that was successfully enumerated and then vanished at its
        # own stat boundary is an admissible atomic-publication race.
        with os.scandir(directory) as entries:
            for entry in entries:
                item = directory / entry.name
                try:
                    observed = entry.stat(follow_symlinks=False)
                except FileNotFoundError as error:
                    if error.errno != errno_module.ENOENT:
                        raise
                    if incident_sink is not None:
                        incident_sink(_incident(
                            error, severity="TOLERATED",
                            disposition="EPHEMERAL_DESCENDANT_DISAPPEARED",
                            phase="tree_descendant_stat",
                            path_summary=_path_summary(root, item),
                        ))
                    continue
                if stat.S_ISLNK(observed.st_mode) or _is_reparse(observed):
                    raise OSError("artifact tree contains a symlink or reparse point")
                if stat.S_ISREG(observed.st_mode):
                    total += int(observed.st_size)
                elif stat.S_ISDIR(observed.st_mode):
                    # Windows CPython may expose st_ino=0 through DirEntry.stat
                    # even when Path.stat has the stable NTFS file identity.
                    # This second stat is no longer the admissible enumerated
                    # entry boundary: any error here is fatal.
                    directory_initial = item.stat(follow_symlinks=False)
                    if (
                        not stat.S_ISDIR(directory_initial.st_mode)
                        or _is_reparse(directory_initial)
                    ):
                        raise OSError("artifact directory changed after entry enumeration")
                    entry_identity = _stat_identity(observed)
                    path_identity = _stat_identity(directory_initial)
                    if path_identity is None or (
                        entry_identity is not None and entry_identity != path_identity
                    ):
                        raise OSError("artifact directory entry identity differs")
                    total += scan_directory(item, directory_initial)
                else:
                    raise OSError("artifact tree contains a non-regular entry")
        terminal = directory.stat(follow_symlinks=False)
        terminal_identity = _stat_identity(terminal)
        if (
            terminal_identity is None or terminal_identity != identity
            or not stat.S_ISDIR(terminal.st_mode) or _is_reparse(terminal)
        ):
            raise OSError("artifact directory identity changed during traversal")
        return total

    return scan_directory(root, root_stat)


# Private compatibility for focused tests and existing internal imports.
_tree_bytes = tree_bytes


def _measure_tree_bytes(
    path: Path, *, phase: str, incident_sink: Callable[[MeasurementIncident], None],
) -> int:
    try:
        return tree_bytes(path, incident_sink=incident_sink)
    except _MeasurementFailure:
        raise
    except Exception as error:
        raise _measurement_failure(
            error, disposition="TREE_MEASUREMENT_FAILED", phase=phase,
            path_summary="measurement-root",
        ) from error


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
        self._incidents: list[MeasurementIncident] = []
        self.size_source = size_source or (
            lambda scratch, durable: (
                _measure_tree_bytes(
                    scratch, phase="scratch_tree_measurement",
                    incident_sink=self._incidents.append,
                ),
                _measure_tree_bytes(
                    durable, phase="durable_tree_measurement",
                    incident_sink=self._incidents.append,
                ),
            )
        )
        self._process_extrema: dict[str, list[float | int]] = {}
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
            snapshot.setdefault("foreground_io_read_bytes", 0)
            snapshot.setdefault("foreground_io_write_bytes", 0)
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
            io_read = snapshot["foreground_io_read_bytes"]
            io_write = snapshot["foreground_io_write_bytes"]
            process_records = snapshot.get("process_records")
            raw_incidents = snapshot.get("measurement_incidents", ())
            if not isinstance(raw_incidents, (tuple, list)):
                raise ValueError("measurement incident inventory differs")
            snapshot_reported_fatal = False
            for incident in raw_incidents:
                if isinstance(incident, MeasurementIncident):
                    typed = incident
                elif isinstance(incident, dict):
                    if set(incident) != {
                        "severity", "disposition", "exception_class", "phase",
                        "path_summary", "errno", "winerror",
                    }:
                        raise ValueError("measurement incident fields differ")
                    typed = MeasurementIncident(**incident)
                else:
                    raise ValueError("measurement incident type differs")
                if (
                    typed.severity not in {"TOLERATED", "FATAL"}
                    or not all(isinstance(value, str) and value for value in (
                        typed.disposition, typed.exception_class, typed.phase, typed.path_summary,
                    ))
                    or any(value is not None and (isinstance(value, bool) or not isinstance(value, int))
                           for value in (typed.errno, typed.winerror))
                ):
                    raise ValueError("measurement incident value differs")
                self._incidents.append(typed)
                if typed.severity == "FATAL":
                    snapshot_reported_fatal = True
            if snapshot_reported_fatal:
                self._errors.append("snapshot_reported_fatal_incident")
                self._stop.set()
                return
            if (
                isinstance(rss, bool) or not isinstance(rss, int) or rss < 0
                or isinstance(cpu, bool) or not isinstance(cpu, (int, float))
                or not math.isfinite(float(cpu)) or cpu < 0
                or isinstance(processes, bool) or not isinstance(processes, int) or processes < 1
                or isinstance(threads, bool) or not isinstance(threads, int) or threads < 1
                or isinstance(available_memory, bool) or not isinstance(available_memory, int)
                or available_memory < 0
                or isinstance(io_read, bool) or not isinstance(io_read, int) or io_read < 0
                or isinstance(io_write, bool) or not isinstance(io_write, int) or io_write < 0
            ):
                raise ValueError("resource snapshot fields are invalid")
            if process_records is not None:
                if not isinstance(process_records, list):
                    raise ValueError("process-tree identity records are invalid")
                for record in process_records:
                    if not isinstance(record, dict):
                        raise ValueError("process-tree identity record differs")
                    identity = record.get("identity")
                    pid = record.get("pid")
                    record_cpu = record.get("cpu_seconds")
                    record_read = record.get("io_read_bytes")
                    record_write = record.get("io_write_bytes")
                    if (
                        not isinstance(identity, str) or not identity
                        or isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0
                        or isinstance(record_cpu, bool) or not isinstance(record_cpu, (int, float))
                        or not math.isfinite(float(record_cpu)) or record_cpu < 0
                        or isinstance(record_read, bool) or not isinstance(record_read, int) or record_read < 0
                        or isinstance(record_write, bool) or not isinstance(record_write, int) or record_write < 0
                    ):
                        raise ValueError("process-tree identity record fields differ")
                    if identity not in self._process_extrema:
                        # The foreground process predates monitoring, while a
                        # descendant's counters start at process creation and
                        # must be retained even if it exits before final sample.
                        base_cpu = float(record_cpu) if pid == os.getpid() else 0.0
                        base_read = record_read if pid == os.getpid() else 0
                        base_write = record_write if pid == os.getpid() else 0
                        self._process_extrema[identity] = [
                            base_cpu, float(record_cpu), base_read, record_read,
                            base_write, record_write,
                        ]
                    extrema = self._process_extrema[identity]
                    extrema[1] = max(float(extrema[1]), float(record_cpu))
                    extrema[3] = max(int(extrema[3]), record_read)
                    extrema[5] = max(int(extrema[5]), record_write)
            scratch, durable = self.size_source(self.scratch_root, self.durable_root)
            if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (scratch, durable)):
                raise ValueError("artifact high-water observation is invalid")
            self._samples.append((snapshot, scratch, durable))
            observed_at = float(self.clock())
            if not math.isfinite(observed_at) or observed_at < self._last_at:
                raise ValueError("resource telemetry clock must be finite and monotonic")
            self._last_at = observed_at
        except Exception as error:  # measurement failure must survive to final fail-closed fact
            if isinstance(error, _MeasurementFailure):
                self._errors.append(type(error.primary).__name__)
                self._incidents.extend(error.incidents)
            else:
                self._errors.append(type(error).__name__)
                self._incidents.append(_incident(
                    error, severity="FATAL", disposition="MEASUREMENT_ABORTED",
                    phase="sample_now", path_summary="measurement-root",
                ))
            self._stop.set()

    def require_valid_initial_observation(self) -> None:
        """Fail closed unless at least one complete, incident-free sample is recorded."""

        if not self._samples or self._errors or any(
            incident.severity == "FATAL" for incident in self._incidents
        ):
            raise RuntimeError("live resource telemetry lacks a valid initial observation")

    def observe_scratch_path(self, path: str | Path) -> None:
        """Observe an atomic temporary before unlink so polling cannot miss it."""

        try:
            size = tree_bytes(Path(path))
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise ValueError("atomic scratch size is invalid")
            self._direct_scratch_peak = max(self._direct_scratch_peak, size)
        except Exception as error:
            self._errors.append(type(error).__name__)
            self._incidents.append(_incident(
                error, severity="FATAL", disposition="MEASUREMENT_ABORTED",
                phase="observe_scratch_path", path_summary="measurement-root",
            ))
            self._stop.set()
            raise RuntimeError("atomic scratch observation failed") from error

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=max(1.0, self.interval_seconds * 4))
        if self._thread.is_alive():
            self._errors.append("monitor_thread_did_not_stop")
            self._incidents.append(MeasurementIncident(
                "FATAL", "MONITOR_THREAD_DID_NOT_STOP", "RuntimeError", "monitor_stop",
                "measurement-root", None, None,
            ))
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
            missing_reasons = ("telemetry_missing",) + (
                ("telemetry_measurement_failed",) if self._errors else ()
            )
            return ResourceTelemetry(
                False, missing_reasons, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0,
                None, None, int(exit_status),
                measurement_incidents=tuple(self._incidents),
            )
        rss_peak = max(int(row[0]["process_tree_rss_bytes"]) for row in self._samples)
        scratch_peak = max(self._direct_scratch_peak, *(row[1] for row in self._samples))
        durable_peak = max(row[2] for row in self._samples)
        wall = max(0.0, self._last_at - self._started_at)
        cpu_values = tuple(float(row[0]["cpu_seconds"]) for row in self._samples)
        # Descendants may exit before the terminal sample, so retain the
        # observed aggregate high-water rather than subtracting only endpoints.
        aggregate_cpu = max(0.0, max(cpu_values) - min(cpu_values))
        io_read_values = tuple(int(row[0]["foreground_io_read_bytes"]) for row in self._samples)
        io_write_values = tuple(int(row[0]["foreground_io_write_bytes"]) for row in self._samples)
        foreground_io_read = max(0, max(io_read_values) - min(io_read_values))
        foreground_io_write = max(0, max(io_write_values) - min(io_write_values))
        if self._process_extrema:
            cpu = sum(max(0.0, float(row[1]) - float(row[0])) for row in self._process_extrema.values())
            tree_io_read = sum(max(0, int(row[3]) - int(row[2])) for row in self._process_extrema.values())
            tree_io_write = sum(max(0, int(row[5]) - int(row[4])) for row in self._process_extrema.values())
        else:
            cpu = aggregate_cpu
            tree_io_read = foreground_io_read
            tree_io_write = foreground_io_write
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
        try:
            import torch
            torch_intraop = int(torch.get_num_threads())
            torch_interop = int(torch.get_num_interop_threads())
        except Exception:
            torch_intraop = 0
            torch_interop = 0
        return ResourceTelemetry(
            not reasons, tuple(reasons), len(self._samples), rss_peak, scratch_peak, durable_peak,
            wall, cpu, cpu / wall if wall > 0.0 else 0.0,
            max(int(row[0]["process_count"]) for row in self._samples),
            max(int(row[0]["thread_count"]) for row in self._samples),
            int(start_memory) if isinstance(start_memory, int) else None,
            int(end_memory) if isinstance(end_memory, int) else None,
            int(exit_status),
            foreground_io_read, foreground_io_write,
            tree_io_read, tree_io_write,
            torch_intraop, torch_interop, int(os.cpu_count() or 0), 0,
            tuple(self._incidents),
        )

    def __enter__(self) -> "ContinuousResourceMonitor":
        if self._thread is None:
            self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.stop()


__all__ = [
    "ContinuousResourceMonitor", "ResourceLimits", "ResourceTelemetry",
    "MeasurementIncident", "foreground_io_snapshot", "tree_bytes",
]
