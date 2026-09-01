"""Outcome-blind Windows process-tree telemetry for VNFC B/EXPLORE.

The monitor observes the current process and its descendants.  Scientific work
counters and the primary/shadow host-call ledger remain caller-owned and are
bound only when the terminal payload is formed.
"""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import json
import math
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Mapping, Sequence


TELEMETRY_SCHEMA = "VNFC_BPCR_BEXP_R01_EXTERNAL_TELEMETRY_V1"
MINIMUM_AVAILABLE_BYTES = 4 * 1024**3
PREFLIGHT_FRESH_SECONDS = 300.0
FROZEN_SAMPLE_INTERVAL_SECONDS = 0.05
IMPLEMENTATION_READY = True
IMPLEMENTATION_BLOCKER = (
    "R01 exact storage contract is absent or incomplete; sampled directory values are lower bounds"
)
STAGES = ("source_binding", "training", "evaluation", "serialization")
ARMS = ("MAPR", "DIRECT")
TELEMETRY_TERMINAL_NAME = "TELEMETRY_TERMINAL.json"
VALID_CLAIM_NAME = "VALID_CLAIM.json"
INCOMPLETE_CLAIM_NAME = "INCOMPLETE_CLAIM.json"
TELEMETRY_FIELDS = frozenset(
    {
        "telemetry_schema",
        "telemetry_terminal",
        "stage_wall_seconds",
        "end_to_end_wall_seconds",
        "stage_cpu_seconds",
        "end_to_end_cpu_seconds",
        "process_tree_peak_rss_bytes",
        "available_physical_bytes",
        "effective_available_bytes",
        "native_integrated_ticks",
        "scientific_work_transitions_per_second",
        "worker_count",
        "threads_per_worker",
        "scratch_peak_bytes",
        "durable_peak_bytes",
        "io_read_bytes",
        "io_write_bytes",
        "parameter_count_by_arm",
        "forward_calls_by_arm",
        "backward_calls_by_arm",
        "flop_exposure_by_arm",
        "primary_host_calls",
        "shadow_host_calls",
    }
)


class ProcessTelemetryError(RuntimeError):
    """Fail-closed process telemetry refusal."""


@dataclass(frozen=True)
class ProcessSample:
    """One live process observation, keyed against PID reuse."""

    pid: int
    creation_time_100ns: int
    rss_bytes: int
    cpu_seconds: float
    io_read_bytes: int
    io_write_bytes: int
    io_other_bytes: int
    thread_count: int

    @property
    def identity(self) -> tuple[int, int]:
        return self.pid, self.creation_time_100ns


@dataclass(frozen=True)
class ExactStorageContract:
    """Auditable R01 promise that closes storage high-water by monotonicity.

    The caller must statically ensure the dedicated scratch root is never
    passed to a child or loader and that durable effects occur only through the
    recorder methods on :class:`ProcessTreeTelemetrySink`.
    """

    frozen_native_artifacts: Mapping[str, str]
    scratch_not_shared_with_children_or_loaders: bool
    durable_root_is_new_namespace: bool
    durable_writes_use_create_once_recorder_only: bool
    serial_no_child_processes: bool
    source_stage_loads_frozen_native_without_build: bool


@dataclass(frozen=True)
class _DurableFileRecord:
    relative_path: str
    size_bytes: int
    sha256: str
    identity: tuple[int, int]
    mtime_ns: int
    ctime_ns: int

    def public(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


def _filetime_value(value: object) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)  # type: ignore[attr-defined]


def sample_windows_process_tree(
    root_pid: int | None = None,
    tracked_identities: Sequence[tuple[int, int]] = (),
) -> tuple[ProcessSample, ...]:
    """Observe root, current descendants, and still-live discovered descendants.

    ``tracked_identities`` lets a long-lived descendant remain observable after
    an intermediate parent exits.  Creation identity is checked before a
    tracked PID becomes an ancestry seed, preventing PID reuse from attaching
    an unrelated process tree.
    """

    if os.name != "nt":
        raise ProcessTelemetryError("Windows process-tree telemetry is required")
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
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    root_pid = os.getpid() if root_pid is None else int(root_pid)
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ProcessTelemetryError("CreateToolhelp32Snapshot failed")
    entries: list[tuple[int, int, int]] = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        if not present:
            raise ProcessTelemetryError("Process32FirstW failed")
        while present:
            entries.append(
                (int(entry.th32ProcessID), int(entry.th32ParentProcessID), int(entry.cntThreads))
            )
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)

    present_pids = {pid for pid, _, _ in entries}
    verified_tracked_pids: set[int] = set()
    for tracked_pid, tracked_creation in tracked_identities:
        if tracked_pid == root_pid or tracked_pid not in present_pids:
            continue
        handle = kernel32.OpenProcess(0x1000, False, tracked_pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                continue
            raise ProcessTelemetryError(f"OpenProcess failed for tracked pid {tracked_pid}")
        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                raise ProcessTelemetryError(f"GetProcessTimes failed for tracked pid {tracked_pid}")
            if _filetime_value(creation) == tracked_creation:
                verified_tracked_pids.add(tracked_pid)
        finally:
            kernel32.CloseHandle(handle)

    descendants = {root_pid, *verified_tracked_pids}
    changed = True
    while changed:
        changed = False
        for pid, parent, _ in entries:
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    threads = {pid: count for pid, _, count in entries}
    samples: list[ProcessSample] = []
    for pid in sorted(descendants):
        handle = kernel32.GetCurrentProcess() if pid == os.getpid() else kernel32.OpenProcess(
            0x1000 | 0x0010, False, pid
        )
        if not handle:
            # ERROR_INVALID_PARAMETER means the enumerated process exited.
            if ctypes.get_last_error() == 87 and pid != root_pid:
                continue
            raise ProcessTelemetryError(f"OpenProcess failed for pid {pid}")
        close_handle = pid != os.getpid()
        try:
            memory = PROCESS_MEMORY_COUNTERS_EX()
            memory.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            io = IO_COUNTERS()
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise ProcessTelemetryError(f"GetProcessMemoryInfo failed for pid {pid}")
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
                raise ProcessTelemetryError(f"GetProcessIoCounters failed for pid {pid}")
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                raise ProcessTelemetryError(f"GetProcessTimes failed for pid {pid}")
            samples.append(
                ProcessSample(
                    pid=pid,
                    creation_time_100ns=_filetime_value(creation),
                    rss_bytes=int(memory.WorkingSetSize),
                    cpu_seconds=(_filetime_value(kernel) + _filetime_value(user)) / 10_000_000.0,
                    io_read_bytes=int(io.ReadTransferCount),
                    io_write_bytes=int(io.WriteTransferCount),
                    io_other_bytes=int(io.OtherTransferCount),
                    thread_count=int(threads.get(pid, 0)),
                )
            )
        finally:
            if close_handle:
                kernel32.CloseHandle(handle)
    if not any(row.pid == root_pid for row in samples):
        raise ProcessTelemetryError("root process was absent from process-tree observation")
    return tuple(samples)


def _plain_directory_size(root: Path) -> int:
    if not root.exists():
        return 0
    root_attributes = int(getattr(root.lstat(), "st_file_attributes", 0))
    if root.is_symlink() or root_attributes & 0x400 or not root.is_dir():
        raise ProcessTelemetryError(f"telemetry root is not a plain directory: {root}")
    total = 0
    for path in root.rglob("*"):
        attributes = int(getattr(path.lstat(), "st_file_attributes", 0))
        if path.is_symlink() or attributes & 0x400:
            raise ProcessTelemetryError(f"telemetry root contains a reparse point: {path}")
        if path.is_file():
            total += path.stat().st_size
    return total


def _plain_root_identity(root: Path) -> tuple[int, int]:
    if not root.exists() or root.is_symlink() or not root.is_dir():
        raise ProcessTelemetryError(f"exact storage root is not a plain directory: {root}")
    stat = root.lstat()
    if int(getattr(stat, "st_file_attributes", 0)) & 0x400:
        raise ProcessTelemetryError(f"exact storage root is a reparse point: {root}")
    return int(stat.st_dev), int(stat.st_ino)


def _durable_inventory(
    root: Path,
) -> tuple[tuple[str, ...], dict[str, _DurableFileRecord]]:
    _plain_root_identity(root)
    directories: list[str] = []
    files: dict[str, _DurableFileRecord] = {}
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        stat = path.lstat()
        if path.is_symlink() or int(getattr(stat, "st_file_attributes", 0)) & 0x400:
            raise ProcessTelemetryError(f"exact storage root contains a reparse point: {path}")
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.append(relative)
            continue
        if not path.is_file():
            raise ProcessTelemetryError(f"exact storage root contains a non-file: {path}")
        raw = path.read_bytes()
        after = path.stat()
        if (
            int(after.st_dev) != int(stat.st_dev)
            or int(after.st_ino) != int(stat.st_ino)
            or int(after.st_size) != len(raw)
            or int(after.st_mtime_ns) != int(stat.st_mtime_ns)
        ):
            raise ProcessTelemetryError(f"durable artifact changed during inventory: {relative}")
        files[relative] = _DurableFileRecord(
            relative_path=relative,
            size_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            identity=(int(stat.st_dev), int(stat.st_ino)),
            mtime_ns=int(stat.st_mtime_ns),
            ctime_ns=int(stat.st_ctime_ns),
        )
    return tuple(directories), files


def _required_parent_directories(relative_paths: Sequence[str]) -> set[str]:
    required: set[str] = set()
    for relative in relative_paths:
        parent = Path(relative).parent
        while parent != Path("."):
            required.add(parent.as_posix())
            parent = parent.parent
    return required


def _safe_relative_artifact_path(value: str | Path) -> str:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ProcessTelemetryError("durable artifact path must be a safe relative path")
    return path.as_posix()


def _canonical_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _bind_preflight(
    receipt: Mapping[str, object], now: datetime
) -> tuple[int, int, dict[str, object]]:
    required = {
        "schema_version",
        "captured_at",
        "assessed_at",
        "minimum_available_bytes",
        "available_physical_bytes",
        "effective_available_bytes",
        "physical_floor_pass",
        "effective_floor_pass",
        "passed",
    }
    if not required <= set(receipt) or receipt.get("schema_version") != 1:
        raise ProcessTelemetryError("4 GiB preflight receipt fields/schema are incomplete")
    if now.tzinfo is None:
        raise ProcessTelemetryError("preflight binding time must be timezone-aware")
    try:
        captured = datetime.fromisoformat(str(receipt["captured_at"]).replace("Z", "+00:00"))
        assessed = datetime.fromisoformat(str(receipt["assessed_at"]).replace("Z", "+00:00"))
        physical = int(receipt["available_physical_bytes"])
        effective = int(receipt["effective_available_bytes"])
    except (TypeError, ValueError, OverflowError) as error:
        raise ProcessTelemetryError("preflight receipt values are invalid") from error
    if captured.tzinfo is None or assessed.tzinfo is None:
        raise ProcessTelemetryError("preflight timestamps must be timezone-aware")
    age = (now.astimezone(timezone.utc) - captured.astimezone(timezone.utc)).total_seconds()
    if age < -5.0 or age > PREFLIGHT_FRESH_SECONDS or assessed < captured:
        raise ProcessTelemetryError("4 GiB preflight receipt is not fresh")
    if (
        receipt.get("minimum_available_bytes") != MINIMUM_AVAILABLE_BYTES
        or physical < MINIMUM_AVAILABLE_BYTES
        or effective < MINIMUM_AVAILABLE_BYTES
        or receipt.get("physical_floor_pass") is not True
        or receipt.get("effective_floor_pass") is not True
        or receipt.get("passed") is not True
    ):
        raise ProcessTelemetryError("4 GiB physical/effective memory admission did not pass")
    binding_source = {name: receipt[name] for name in sorted(required)}
    binding = {
        "schema_version": 1,
        "receipt_sha256": _canonical_digest(binding_source),
        "captured_at": str(receipt["captured_at"]),
        "assessed_at": str(receipt["assessed_at"]),
        "age_seconds_at_monitor_start": age,
        "available_physical_bytes": physical,
        "effective_available_bytes": effective,
    }
    return physical, effective, binding


class ProcessTreeTelemetrySink:
    """Bounded sampler; terminal emission stays fenced until peaks are exact."""

    schema = TELEMETRY_SCHEMA
    fields = tuple(sorted(TELEMETRY_FIELDS))

    def __init__(
        self,
        *,
        preflight_receipt: Mapping[str, object],
        scratch_root: Path,
        durable_root: Path,
        now: datetime | None = None,
        sample_interval_seconds: float | None = None,
        sampler: Callable[[Sequence[tuple[int, int]]], Sequence[ProcessSample]] | None = None,
        clock: Callable[[], float] = time.perf_counter,
        logical_processor_count: int | None = None,
        test_mode: bool = False,
        exact_storage_contract: ExactStorageContract | None = None,
    ) -> None:
        interval = (
            FROZEN_SAMPLE_INTERVAL_SECONDS
            if sample_interval_seconds is None
            else sample_interval_seconds
        )
        if (
            isinstance(interval, bool)
            or not isinstance(interval, (int, float))
            or not math.isfinite(float(interval))
            or interval <= 0
        ):
            raise ProcessTelemetryError("sample interval must be positive")
        binding_now = datetime.now(timezone.utc) if now is None else now
        physical, effective, binding = _bind_preflight(preflight_receipt, binding_now)
        if sampler is None and os.name != "nt":
            raise ProcessTelemetryError("Windows process-tree telemetry is required")
        injected_measurement = (
            now is not None
            or sample_interval_seconds is not None
            or sampler is not None
            or clock is not time.perf_counter
            or logical_processor_count is not None
        )
        logical = int(os.cpu_count() or 1) if logical_processor_count is None else logical_processor_count
        if isinstance(logical, bool) or not isinstance(logical, int) or logical <= 0:
            raise ProcessTelemetryError("logical processor count must be positive")
        self.scratch_root = Path(scratch_root)
        self.durable_root = Path(durable_root)
        self.sample_interval_seconds = float(interval)
        self._sampler = (
            (lambda tracked: sample_windows_process_tree(tracked_identities=tracked))
            if sampler is None
            else sampler
        )
        self._clock = clock
        self._logical_processors = logical
        self._preflight_receipt = dict(preflight_receipt)
        self._binding_now_override = now
        self._test_mode = bool(test_mode or injected_measurement)
        self._exact_storage_contract = exact_storage_contract
        self._physical_available = physical
        self._effective_available = effective
        self.preflight_binding = binding
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._started_at: float | None = None
        self._first: dict[tuple[int, int], ProcessSample] = {}
        self._last: dict[tuple[int, int], ProcessSample] = {}
        self._discovered_identities: set[tuple[int, int]] = set()
        self._peak_rss = 0
        self._peak_processes = 0
        self._peak_threads = 0
        self._scratch_peak = 0
        self._durable_peak = 0
        self._scratch_root_identity: tuple[int, int] | None = None
        self._durable_root_identity: tuple[int, int] | None = None
        self._durable_records: dict[str, _DurableFileRecord] = {}
        self._durable_directories: set[str] = set()
        self._frozen_native_records: tuple[dict[str, object], ...] = ()
        self._storage_write_active: str | None = None
        self._storage_error: str | None = None
        self._exact_storage_started = False
        self._storage_sealed = False
        self._attempt_disposition = "VALID_CAPABLE"
        self._incomplete_reasons: list[str] = []
        self._serial_root_identity: tuple[int, int] | None = None
        self._observer_publication_root: Path | None = None
        self._observer_publication_root_identity: tuple[int, int] | None = None
        self._observer_publication_records: dict[str, _DurableFileRecord] = {}
        self._observer_publication_sealed = False
        self._observer_namespace: str | None = None
        self._observer_body_relative: str | None = None
        self._observer_claim_name: str | None = None
        self._sample_count = 0
        self._active_stage: tuple[str, float, float] | None = None
        self._stage_wall = {name: 0.0 for name in STAGES}
        self._stage_cpu = {name: 0.0 for name in STAGES}
        self._stage_counts = {name: 0 for name in STAGES}
        self._next_stage_index = 0
        self._stage_error: str | None = None
        self._stage_error_kind: str | None = None
        self._finished = False
        self._finish_attempted = False
        self._emitted: dict[str, object] | None = None

    def _raise_background_error_locked(self) -> None:
        if self._error is not None:
            raise ProcessTelemetryError(f"process telemetry sampler failed: {self._error}") from self._error

    def _counters_locked(self) -> tuple[float, int, int, int]:
        cpu = 0.0
        read_bytes = write_bytes = other_bytes = 0
        for identity, last in self._last.items():
            first = self._first[identity]
            cpu += max(0.0, last.cpu_seconds - first.cpu_seconds)
            read_bytes += max(0, last.io_read_bytes - first.io_read_bytes)
            write_bytes += max(0, last.io_write_bytes - first.io_write_bytes)
            other_bytes += max(0, last.io_other_bytes - first.io_other_bytes)
        return cpu, read_bytes, write_bytes, other_bytes

    def _observe_locked(self) -> None:
        if self._finished:
            raise ProcessTelemetryError("process telemetry is already finished")
        try:
            rows = tuple(self._sampler(tuple(sorted(self._discovered_identities))))
        except ProcessTelemetryError:
            raise
        except BaseException as error:
            raise ProcessTelemetryError(f"process sampler failed: {error}") from error
        if not rows:
            raise ProcessTelemetryError("process sampler returned no rows")
        identities = [row.identity for row in rows]
        if len(identities) != len(set(identities)):
            raise ProcessTelemetryError("process sampler returned duplicate identities")
        for row in rows:
            if (
                isinstance(row.pid, bool)
                or not isinstance(row.pid, int)
                or row.pid <= 0
                or isinstance(row.creation_time_100ns, bool)
                or not isinstance(row.creation_time_100ns, int)
                or row.creation_time_100ns <= 0
            ):
                raise ProcessTelemetryError("process sampler returned an invalid PID/creation identity")
            values = (
                row.rss_bytes,
                row.cpu_seconds,
                row.io_read_bytes,
                row.io_write_bytes,
                row.io_other_bytes,
                row.thread_count,
            )
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
                raise ProcessTelemetryError("process sampler returned non-numeric counters")
            if any(not math.isfinite(float(value)) or value < 0 for value in values):
                raise ProcessTelemetryError("process sampler returned invalid counters")
            prior = self._last.get(row.identity)
            if prior is not None and (
                row.cpu_seconds < prior.cpu_seconds
                or row.io_read_bytes < prior.io_read_bytes
                or row.io_write_bytes < prior.io_write_bytes
                or row.io_other_bytes < prior.io_other_bytes
            ):
                raise ProcessTelemetryError("process cumulative counters regressed")
        if self._exact_storage_started:
            if len(rows) != 1:
                self._storage_incomplete_locked(
                    "SERIAL_NO_CHILD_PROCESSES observed a descendant process"
                )
            only = rows[0]
            if not self._test_mode and only.pid != os.getpid():
                self._storage_incomplete_locked(
                    "SERIAL_NO_CHILD_PROCESSES root PID differs from current process"
                )
            if self._serial_root_identity is None:
                self._serial_root_identity = only.identity
            elif only.identity != self._serial_root_identity:
                self._storage_incomplete_locked(
                    "SERIAL_NO_CHILD_PROCESSES root creation identity changed"
                )
        initial_sample = self._sample_count == 0
        self._sample_count += 1
        self._peak_rss = max(self._peak_rss, sum(int(row.rss_bytes) for row in rows))
        self._peak_processes = max(self._peak_processes, len(rows))
        self._peak_threads = max(self._peak_threads, sum(int(row.thread_count) for row in rows))
        self._scratch_peak = max(self._scratch_peak, _plain_directory_size(self.scratch_root))
        self._durable_peak = max(self._durable_peak, _plain_directory_size(self.durable_root))
        for row in rows:
            if row.identity not in self._first:
                # Processes already present at monitor start use their observed
                # cumulative counters as baseline.  A descendant first seen
                # later was created inside the monitored interval, so its CPU
                # and I/O counters start at zero for invocation accounting.
                self._first[row.identity] = row if initial_sample else ProcessSample(
                    pid=row.pid,
                    creation_time_100ns=row.creation_time_100ns,
                    rss_bytes=row.rss_bytes,
                    cpu_seconds=0.0,
                    io_read_bytes=0,
                    io_write_bytes=0,
                    io_other_bytes=0,
                    thread_count=row.thread_count,
                )
            self._last[row.identity] = row
            self._discovered_identities.add(row.identity)

    def _loop(self) -> None:
        try:
            while not self._stop.wait(self.sample_interval_seconds):
                with self._lock:
                    self._observe_locked()
        except BaseException as error:
            with self._lock:
                self._error = error
            self._stop.set()

    def _storage_incomplete_locked(self, reason: str) -> None:
        self._storage_error = reason
        self._stop.set()
        raise ProcessTelemetryError(f"INCOMPLETE: exact R01 storage contract violated: {reason}")

    def _verify_frozen_native_locked(self) -> None:
        for record in self._frozen_native_records:
            path = Path(str(record["path"]))
            if not path.is_file() or path.is_symlink():
                self._storage_incomplete_locked(f"frozen native artifact disappeared: {path}")
            stat = path.stat()
            raw = path.read_bytes()
            if (
                len(raw) != record["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != record["sha256"]
                or (int(stat.st_dev), int(stat.st_ino)) != record["identity"]
                or int(stat.st_mtime_ns) != record["mtime_ns"]
            ):
                self._storage_incomplete_locked(f"frozen native artifact drifted: {path}")

    def _scan_exact_storage_locked(
        self, *, allowed_new_file: str | None = None
    ) -> tuple[set[str], dict[str, _DurableFileRecord]]:
        if self._storage_error is not None:
            raise ProcessTelemetryError(f"INCOMPLETE: {self._storage_error}")
        if _plain_root_identity(self.scratch_root) != self._scratch_root_identity:
            self._storage_incomplete_locked("scratch root identity changed")
        try:
            scratch_dirs, scratch_files = _durable_inventory(self.scratch_root)
        except ProcessTelemetryError as error:
            self._storage_incomplete_locked(str(error))
        if scratch_dirs or scratch_files:
            self._storage_incomplete_locked("dedicated scratch root mutated from exact-empty state")
        if _plain_root_identity(self.durable_root) != self._durable_root_identity:
            self._storage_incomplete_locked("durable root identity changed")
        try:
            directories, files = _durable_inventory(self.durable_root)
        except ProcessTelemetryError as error:
            self._storage_incomplete_locked(str(error))
        known = set(self._durable_records)
        current = set(files)
        missing = known - current
        unknown = current - known
        if missing:
            self._storage_incomplete_locked(f"durable artifact was deleted: {sorted(missing)}")
        if unknown != ({allowed_new_file} if allowed_new_file is not None else set()):
            self._storage_incomplete_locked(f"unknown durable artifact mutation: {sorted(unknown)}")
        for relative, prior in self._durable_records.items():
            if files[relative] != prior:
                self._storage_incomplete_locked(f"durable artifact was overwritten: {relative}")
        expected_dirs = set(self._durable_directories)
        if allowed_new_file is not None:
            expected_dirs.update(_required_parent_directories((allowed_new_file,)))
        if set(directories) != expected_dirs:
            self._storage_incomplete_locked(
                f"unknown durable directory mutation: {sorted(set(directories) ^ expected_dirs)}"
            )
        self._verify_frozen_native_locked()
        return set(directories), files

    def _freeze_exact_storage_locked(self) -> None:
        contract = self._exact_storage_contract
        if contract is None:
            return
        if (
            contract.scratch_not_shared_with_children_or_loaders is not True
            or contract.durable_root_is_new_namespace is not True
            or contract.durable_writes_use_create_once_recorder_only is not True
            or contract.serial_no_child_processes is not True
            or contract.source_stage_loads_frozen_native_without_build is not True
            or not isinstance(contract.frozen_native_artifacts, Mapping)
            or not contract.frozen_native_artifacts
        ):
            self._storage_incomplete_locked("R01 storage contract assertions are incomplete")
        scratch = self.scratch_root.resolve()
        durable = self.durable_root.resolve()
        if scratch == durable or scratch in durable.parents or durable in scratch.parents:
            self._storage_incomplete_locked("scratch and durable roots are not disjoint")
        self._scratch_root_identity = _plain_root_identity(self.scratch_root)
        self._durable_root_identity = _plain_root_identity(self.durable_root)
        scratch_dirs, scratch_files = _durable_inventory(self.scratch_root)
        durable_dirs, durable_files = _durable_inventory(self.durable_root)
        if scratch_dirs or scratch_files or durable_dirs or durable_files:
            self._storage_incomplete_locked("exact R01 storage roots were not empty at start")
        frozen: list[dict[str, object]] = []
        for raw_path, expected_sha in sorted(contract.frozen_native_artifacts.items()):
            path = Path(raw_path)
            if not path.is_absolute():
                self._storage_incomplete_locked("frozen native artifact path is not absolute")
            resolved = path.resolve()
            if resolved == scratch or resolved == durable or scratch in resolved.parents or durable in resolved.parents:
                self._storage_incomplete_locked("frozen native artifact is inside an invocation storage root")
            if (
                not isinstance(expected_sha, str)
                or len(expected_sha) != 64
                or any(character not in "0123456789abcdef" for character in expected_sha)
            ):
                self._storage_incomplete_locked("frozen native artifact digest is invalid")
            if not resolved.is_file() or resolved.is_symlink():
                self._storage_incomplete_locked(f"frozen native artifact is not a plain file: {resolved}")
            stat = resolved.stat()
            if int(getattr(stat, "st_file_attributes", 0)) & 0x400:
                self._storage_incomplete_locked(f"frozen native artifact is a reparse point: {resolved}")
            raw = resolved.read_bytes()
            actual_sha = hashlib.sha256(raw).hexdigest()
            if actual_sha != expected_sha:
                self._storage_incomplete_locked(f"frozen native artifact digest differs: {resolved}")
            frozen.append(
                {
                    "path": str(resolved),
                    "size_bytes": len(raw),
                    "sha256": actual_sha,
                    "identity": (int(stat.st_dev), int(stat.st_ino)),
                    "mtime_ns": int(stat.st_mtime_ns),
                }
            )
        self._frozen_native_records = tuple(frozen)
        self._exact_storage_started = True
        self._scan_exact_storage_locked()

    def start(self) -> "ProcessTreeTelemetrySink":
        with self._lock:
            if self._thread is not None or self._started_at is not None or self._finished:
                raise ProcessTelemetryError("process telemetry may be started only once")
            binding_now = (
                datetime.now(timezone.utc)
                if self._binding_now_override is None
                else self._binding_now_override
            )
            physical, effective, binding = _bind_preflight(self._preflight_receipt, binding_now)
            self._physical_available = physical
            self._effective_available = effective
            self.preflight_binding = binding
            self._started_at = float(self._clock())
            self._freeze_exact_storage_locked()
            self._observe_locked()
            self._thread = threading.Thread(
                target=self._loop, name="vnfc-b-explore-process-telemetry", daemon=True
            )
            self._thread.start()
        return self

    def _require_active_locked(self) -> None:
        if self._started_at is None or self._thread is None or self._finished:
            raise ProcessTelemetryError("process telemetry is not active")
        self._raise_background_error_locked()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            self._require_active_locked()
            self._observe_locked()
            cpu, read_bytes, write_bytes, other_bytes = self._counters_locked()
            return {
                "sample_count": self._sample_count,
                "wall_seconds": float(self._clock()) - self._started_at,  # type: ignore[operator]
                "cpu_seconds": cpu,
                "process_tree_peak_rss_bytes": self._peak_rss,
                "peak_process_count": self._peak_processes,
                "peak_thread_count": self._peak_threads,
                "scratch_peak_bytes": self._scratch_peak,
                "durable_peak_bytes": self._durable_peak,
                "io_read_bytes": read_bytes,
                "io_write_bytes": write_bytes,
                "io_other_bytes": other_bytes,
            }

    @contextlib.contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if name not in STAGES:
            raise ProcessTelemetryError(f"unknown telemetry stage: {name}")
        with self._lock:
            self._require_active_locked()
            if self._attempt_disposition != "VALID_CAPABLE":
                raise ProcessTelemetryError(
                    "INCOMPLETE_ONLY: scientific stages cannot continue after an INCOMPLETE transition"
                )
            if self._active_stage is not None:
                raise ProcessTelemetryError("telemetry stages may not overlap")
            expected = STAGES[self._next_stage_index] if self._next_stage_index < len(STAGES) else None
            if name != expected:
                self._stage_error = f"expected {expected!r}, received {name!r}"
                self._stage_error_kind = "ORDER"
                self._stop.set()
                raise ProcessTelemetryError(
                    f"INCOMPLETE: telemetry stage order/exact-once contract violated: {self._stage_error}"
                )
            self._observe_locked()
            cpu, _, _, _ = self._counters_locked()
            self._active_stage = (name, float(self._clock()), cpu)
        body_error: BaseException | None = None
        try:
            yield
        except BaseException as error:
            body_error = error
            raise
        finally:
            with self._lock:
                active = self._active_stage
                if active is None or active[0] != name:
                    raise ProcessTelemetryError("telemetry stage state was corrupted")
                try:
                    self._raise_background_error_locked()
                    self._observe_locked()
                    end_cpu, _, _, _ = self._counters_locked()
                    end_wall = float(self._clock())
                    wall_delta = end_wall - active[1]
                    cpu_delta = end_cpu - active[2]
                    if (
                        not math.isfinite(wall_delta)
                        or not math.isfinite(cpu_delta)
                        or wall_delta < 0
                        or cpu_delta < -1e-12
                    ):
                        raise ProcessTelemetryError("telemetry stage counters regressed")
                    self._stage_wall[name] += wall_delta
                    self._stage_cpu[name] += max(0.0, cpu_delta)
                    if body_error is None:
                        self._stage_counts[name] += 1
                        self._next_stage_index += 1
                    else:
                        self._stage_error = f"stage {name!r} body raised {type(body_error).__name__}"
                        self._stage_error_kind = "BODY"
                        self._stop.set()
                finally:
                    self._active_stage = None

    def retarget_durable_root(self, durable_root: Path) -> None:
        with self._lock:
            self._require_active_locked()
            if self._exact_storage_started:
                self._storage_incomplete_locked(
                    "durable root retarget is forbidden by monotonic create-only identity"
                )
            self._observe_locked()
            self.durable_root = Path(durable_root)
            self._observe_locked()

    def _transition_incomplete_locked(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ProcessTelemetryError("INCOMPLETE transition requires a non-empty reason")
        if self._attempt_disposition == "VALID_CAPABLE":
            self._attempt_disposition = "INCOMPLETE_ONLY"
        if reason not in self._incomplete_reasons:
            self._incomplete_reasons.append(reason)

    def mark_incomplete(self, reason: str) -> None:
        """Irreversibly lower this attempt to INCOMPLETE while keeping the recorder active."""

        with self._lock:
            if self._storage_sealed:
                raise ProcessTelemetryError("INCOMPLETE: durable storage is already sealed")
            self._require_active_locked()
            if not self._exact_storage_started:
                raise ProcessTelemetryError("REPAIR_REQUIRED: exact storage contract is not active")
            self._scan_exact_storage_locked()
            self._transition_incomplete_locked(reason)

    def _capture_failed_expected_create_locked(self, relative: str, reason: str) -> None:
        if _plain_root_identity(self.scratch_root) != self._scratch_root_identity:
            self._storage_incomplete_locked("scratch root identity changed after create failure")
        try:
            scratch_dirs, scratch_files = _durable_inventory(self.scratch_root)
        except ProcessTelemetryError as error:
            self._storage_incomplete_locked(str(error))
        if scratch_dirs or scratch_files:
            self._storage_incomplete_locked("scratch mutated during failed create-once operation")
        if _plain_root_identity(self.durable_root) != self._durable_root_identity:
            self._storage_incomplete_locked("durable root identity changed after create failure")
        try:
            directories, files = _durable_inventory(self.durable_root)
        except ProcessTelemetryError as error:
            self._storage_incomplete_locked(str(error))
        known = set(self._durable_records)
        current = set(files)
        if known - current:
            self._storage_incomplete_locked("registered durable artifact was deleted during create failure")
        unknown = current - known
        if unknown not in (set(), {relative}):
            self._storage_incomplete_locked(
                f"unknown durable artifact appeared during create failure: {sorted(unknown)}"
            )
        for name, prior in self._durable_records.items():
            if files[name] != prior:
                self._storage_incomplete_locked(
                    f"registered durable artifact changed during create failure: {name}"
                )
        allowed_dirs = set(self._durable_directories) | _required_parent_directories((relative,))
        if not set(directories).issubset(allowed_dirs) or not set(self._durable_directories).issubset(
            set(directories)
        ):
            self._storage_incomplete_locked("unknown durable directory mutation during create failure")
        if relative in files:
            self._durable_records[relative] = files[relative]
        self._durable_directories = set(directories)
        self._verify_frozen_native_locked()
        self._transition_incomplete_locked(reason)

    @contextlib.contextmanager
    def _observe_create_once(
        self, relative_path: str | Path, *, incomplete_reason: str | None
    ) -> Iterator[Path]:
        """Bracket exactly one runner-owned durable file creation."""

        relative = _safe_relative_artifact_path(relative_path)
        with self._lock:
            if self._storage_sealed:
                raise ProcessTelemetryError("INCOMPLETE: durable storage is already sealed")
            self._require_active_locked()
            if not self._exact_storage_started:
                raise ProcessTelemetryError("REPAIR_REQUIRED: exact storage contract is not active")
            if incomplete_reason is None and self._attempt_disposition != "VALID_CAPABLE":
                raise ProcessTelemetryError(
                    "INCOMPLETE_ONLY: use observe_incomplete_create_once for quarantine artifacts"
                )
            if incomplete_reason is not None:
                if self._attempt_disposition != "INCOMPLETE_ONLY":
                    raise ProcessTelemetryError(
                        "observe_incomplete_create_once requires a prior INCOMPLETE transition"
                    )
                self._transition_incomplete_locked(incomplete_reason)
            if self._storage_write_active is not None:
                self._storage_incomplete_locked("durable create-once operations overlapped")
            self._scan_exact_storage_locked()
            if relative in self._durable_records or (self.durable_root / relative).exists():
                self._storage_incomplete_locked(f"durable create-once target already exists: {relative}")
            self._storage_write_active = relative
        try:
            yield self.durable_root / relative
        except BaseException as error:
            with self._lock:
                self._storage_write_active = None
                self._capture_failed_expected_create_locked(
                    relative,
                    f"create_once_operation_failed:{relative}:{type(error).__name__}",
                )
            raise
        else:
            with self._lock:
                try:
                    if not (self.durable_root / relative).is_file():
                        reason = f"create_once_target_absent:{relative}"
                        self._capture_failed_expected_create_locked(relative, reason)
                        raise ProcessTelemetryError(f"INCOMPLETE: {reason}")
                    directories, files = self._scan_exact_storage_locked(
                        allowed_new_file=relative
                    )
                    record = files.get(relative)
                    if record is None:
                        self._storage_incomplete_locked(
                            f"durable create-once target was not created: {relative}"
                        )
                    self._durable_records[relative] = record
                    self._durable_directories = directories
                finally:
                    self._storage_write_active = None

    def observe_create_once(self, relative_path: str | Path) -> contextlib.AbstractContextManager[Path]:
        """Create one VALID-path artifact; operation failure lowers to INCOMPLETE_ONLY."""

        return self._observe_create_once(relative_path, incomplete_reason=None)

    def observe_incomplete_create_once(
        self, relative_path: str | Path, *, reason: str
    ) -> contextlib.AbstractContextManager[Path]:
        """Append one immutable quarantine artifact after an INCOMPLETE transition."""

        return self._observe_create_once(relative_path, incomplete_reason=reason)

    def verify_storage_seal(self) -> dict[str, object]:
        """Recheck the immutable post-publication tree before consumption."""

        with self._lock:
            if not self._storage_sealed or not self._exact_storage_started:
                raise ProcessTelemetryError("exact durable storage seal is absent")
            directories, files = self._scan_exact_storage_locked()
            total = sum(record.size_bytes for record in files.values())
            return {
                "storage_high_water_disposition": "EXACT_R01_MONOTONIC_CREATE_ONLY",
                "durable_directory_total_bytes": total,
                "durable_artifact_inventory": tuple(
                    files[name].public() for name in sorted(files)
                ),
                "directory_inventory": tuple(sorted(directories)),
                "valid": True,
            }

    def abort(self) -> None:
        """Stop sampling without creating a telemetry terminal."""

        with self._lock:
            if self._finished:
                return
            self._finished = True
            self._stop.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=max(5.0, self.sample_interval_seconds * 4.0))
            if thread.is_alive():
                raise ProcessTelemetryError("process sampler did not terminate during abort")

    @staticmethod
    def _positive_int(name: str, value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ProcessTelemetryError(f"{name} must be a positive integer")
        return value

    @staticmethod
    def _positive_arm_mapping(name: str, value: object) -> dict[str, int | float]:
        if not isinstance(value, Mapping) or not value:
            raise ProcessTelemetryError(f"{name} must be a non-empty arm mapping")
        result: dict[str, int | float] = {}
        for arm, count in value.items():
            if not isinstance(arm, str) or not arm:
                raise ProcessTelemetryError(f"{name} contains an invalid arm")
            if (
                isinstance(count, bool)
                or not isinstance(count, (int, float))
                or not math.isfinite(float(count))
                or count <= 0
            ):
                raise ProcessTelemetryError(f"{name} contains a nonpositive count")
            result[arm] = count
        if set(result) != set(ARMS):
            raise ProcessTelemetryError(f"{name} arm inventory differs")
        return result

    def _finish(
        self,
        *,
        scientific_counters: Mapping[str, object],
        host_call_ledger: Mapping[str, object],
        allow_incomplete: bool = False,
    ) -> dict[str, object]:
        """Stop once and bind outcome-free external scientific counters."""

        with self._lock:
            self._require_active_locked()
            if self._finish_attempted:
                raise ProcessTelemetryError("process telemetry finish may be attempted only once")
            if self._active_stage is not None:
                raise ProcessTelemetryError("cannot finish inside a telemetry stage")
            if allow_incomplete:
                if self._attempt_disposition != "INCOMPLETE_ONLY" or not self._incomplete_reasons:
                    raise ProcessTelemetryError("finish_incomplete requires a recorded INCOMPLETE transition")
                if self._stage_error_kind == "ORDER":
                    raise ProcessTelemetryError(
                        f"INCOMPLETE: invalid stage order cannot be sealed: {self._stage_error}"
                    )
                expected_counts = {
                    name: 1 if index < self._next_stage_index else 0
                    for index, name in enumerate(STAGES)
                }
                if self._stage_counts != expected_counts:
                    raise ProcessTelemetryError("INCOMPLETE stage prefix inventory differs")
            else:
                if self._attempt_disposition != "VALID_CAPABLE":
                    raise ProcessTelemetryError(
                        "attempt is INCOMPLETE_ONLY; finish_incomplete is required"
                    )
                if self._stage_error is not None:
                    raise ProcessTelemetryError(
                        f"INCOMPLETE: telemetry stage sequence failed: {self._stage_error}"
                    )
                if self._next_stage_index != len(STAGES) or any(
                    self._stage_counts[name] != 1 for name in STAGES
                ):
                    raise ProcessTelemetryError(
                        "all four telemetry stages must be observed exactly once in frozen order"
                    )
            if self._storage_write_active is not None:
                self._storage_incomplete_locked("finish overlapped a durable create-once operation")
            if self._exact_storage_started:
                self._scan_exact_storage_locked()
                if not self._durable_records:
                    self._storage_incomplete_locked("attempt produced no durable artifacts")
            self._finish_attempted = True
        self._stop.set()
        assert self._thread is not None
        self._thread.join(timeout=max(5.0, self.sample_interval_seconds * 4.0))
        if self._thread.is_alive():
            raise ProcessTelemetryError("process sampler did not terminate")
        with self._lock:
            self._raise_background_error_locked()
            self._observe_locked()
            end = float(self._clock())
            assert self._started_at is not None
            wall = end - self._started_at
            if not math.isfinite(wall) or wall <= 0:
                raise ProcessTelemetryError("end-to-end wall measurement is nonpositive")
            cpu, read_bytes, write_bytes, other_bytes = self._counters_locked()
            storage_exact = self._exact_storage_started and self._storage_error is None
            if storage_exact:
                directories, final_files = self._scan_exact_storage_locked()
                self._durable_directories = directories
                exact_scratch_peak = 0
                exact_durable_peak = sum(record.size_bytes for record in final_files.values())
            else:
                final_files = dict(self._durable_records)
                exact_scratch_peak = self._scratch_peak
                exact_durable_peak = self._durable_peak

            required_scientific = {
                "native_integrated_ticks",
                "scientific_work_transitions",
                "worker_count",
                "threads_per_worker",
                "parameter_count_by_arm",
                "forward_calls_by_arm",
                "backward_calls_by_arm",
                "flop_exposure_by_arm",
            }
            if set(scientific_counters) != required_scientific:
                raise ProcessTelemetryError("scientific counter inventory differs")
            native_ticks = self._positive_int(
                "native_integrated_ticks", scientific_counters["native_integrated_ticks"]
            )
            transitions = self._positive_int(
                "scientific_work_transitions", scientific_counters["scientific_work_transitions"]
            )
            workers = self._positive_int("worker_count", scientific_counters["worker_count"])
            threads_per_worker = self._positive_int(
                "threads_per_worker", scientific_counters["threads_per_worker"]
            )
            if self._exact_storage_started and (workers != 1 or threads_per_worker != 1):
                self._storage_incomplete_locked(
                    "SERIAL_NO_CHILD_PROCESSES requires worker_count=1 and threads_per_worker=1"
                )
            arm_fields = {
                name: self._positive_arm_mapping(name, scientific_counters[name])
                for name in (
                    "parameter_count_by_arm",
                    "forward_calls_by_arm",
                    "backward_calls_by_arm",
                    "flop_exposure_by_arm",
                )
            }
            arm_inventory = set(arm_fields["parameter_count_by_arm"])
            if any(set(value) != arm_inventory for value in arm_fields.values()):
                raise ProcessTelemetryError("scientific per-arm inventories differ")

            required_ledger = {
                "primary_host_calls",
                "shadow_host_calls",
            }
            if set(host_call_ledger) != required_ledger:
                raise ProcessTelemetryError("host-call ledger inventory differs")
            primary_calls = self._positive_int(
                "primary_host_calls", host_call_ledger["primary_host_calls"]
            )
            shadow_calls = self._positive_int(
                "shadow_host_calls", host_call_ledger["shadow_host_calls"]
            )
            payload_ready = IMPLEMENTATION_READY and storage_exact
            payload: dict[str, object] = {
                "telemetry_schema": TELEMETRY_SCHEMA,
                "telemetry_terminal": payload_ready and not self._test_mode,
                "performance_evidence": payload_ready and not self._test_mode,
                "implementation_ready": payload_ready,
                "performance_readiness": "READY" if payload_ready else "REPAIR_REQUIRED",
                "implementation_blocker": None if payload_ready else IMPLEMENTATION_BLOCKER,
                "attempt_disposition": "INCOMPLETE" if allow_incomplete else "VALID_CAPABLE",
                "scientific_result_valid": not allow_incomplete,
                "incomplete_reasons": tuple(self._incomplete_reasons),
                "telemetry_phase": "FINAL_STORAGE_SEAL" if storage_exact else "UNSEALED_MEASUREMENT",
                "storage_sealed": storage_exact,
                "post_seal_writes_forbidden": storage_exact,
                "observer_publication_required": storage_exact,
                "valid_artifact_bundle": (
                    (
                        "INCOMPLETE_BODY_PLUS_TELEMETRY_TERMINAL_PLUS_INCOMPLETE_CLAIM"
                        if allow_incomplete
                        else "RESULT_BODY_PLUS_TELEMETRY_TERMINAL_PLUS_VALID_CLAIM"
                    )
                    if storage_exact
                    else None
                ),
                "storage_high_water_disposition": (
                    "EXACT_R01_MONOTONIC_CREATE_ONLY"
                    if storage_exact
                    else "SAMPLED_LOWER_BOUND_NOT_EXACT"
                ),
                "measurement_source": (
                    "INJECTED_TEST_ONLY_NOT_PERFORMANCE_EVIDENCE"
                    if self._test_mode
                    else "Windows Toolhelp/Process/PSAPI process-tree sampling"
                ),
                "measurement_limitations": (
                    "Windows only; descendants that start and exit wholly between samples may be missed",
                    "stage CPU inherits the same finite-interval sampling limitation",
                ) + (() if storage_exact else (
                    "scratch/durable values are sampled lower bounds and may miss transient external writes",
                )),
                "sample_interval_seconds": self.sample_interval_seconds,
                "sample_count": self._sample_count,
                "preflight_binding": dict(self.preflight_binding),
                "stage_wall_seconds": dict(self._stage_wall),
                "stage_cpu_seconds": dict(self._stage_cpu),
                "stage_observation_count": dict(self._stage_counts),
                "end_to_end_wall_seconds": wall,
                "end_to_end_cpu_seconds": cpu,
                "cpu_core_equivalents": cpu / wall,
                "host_cpu_occupancy": cpu / (wall * self._logical_processors),
                "logical_processor_count": self._logical_processors,
                "process_tree_peak_rss_bytes": self._peak_rss,
                "peak_process_count": self._peak_processes,
                "peak_thread_count": self._peak_threads,
                "available_physical_bytes": self._physical_available,
                "effective_available_bytes": self._effective_available,
                "native_integrated_ticks": native_ticks,
                "scientific_work_transitions_per_second": transitions / wall,
                "scientific_work_transitions": transitions,
                "worker_count": workers,
                "threads_per_worker": threads_per_worker,
                "execution_topology": (
                    "SERIAL_NO_CHILD_PROCESSES" if storage_exact else "UNFROZEN"
                ),
                "serial_topology_reason": (
                    "old native DLL is loaded in-process via ctypes; torch threads are frozen to one"
                    if storage_exact
                    else None
                ),
                "source_native_admission": (
                    "PREBUILT_FROZEN_LOAD_ONLY_NO_COMPILE" if storage_exact else "UNFROZEN"
                ),
                "scratch_peak_bytes": exact_scratch_peak,
                "durable_peak_bytes": exact_durable_peak,
                "durable_directory_total_bytes": exact_durable_peak,
                "durable_artifact_inventory": tuple(
                    final_files[name].public() for name in sorted(final_files)
                ),
                "frozen_native_artifact_inventory": tuple(
                    {
                        "path": record["path"],
                        "size_bytes": record["size_bytes"],
                        "sha256": record["sha256"],
                    }
                    for record in self._frozen_native_records
                ),
                "exact_storage_contract": (
                    {
                        "scratch_root": str(self.scratch_root.resolve()),
                        "durable_root": str(self.durable_root.resolve()),
                        "scratch_start_empty_and_unshared": True,
                        "durable_new_namespace_start_empty": True,
                        "durable_effects_monotonic_create_once": True,
                    }
                    if storage_exact
                    else None
                ),
                "io_read_bytes": int(read_bytes),
                "io_write_bytes": int(write_bytes),
                "io_other_bytes": int(other_bytes),
                "aggregate_io_bytes": int(read_bytes + write_bytes + other_bytes),
                **arm_fields,
                "primary_host_calls": primary_calls,
                "shadow_host_calls": shadow_calls,
            }
            if not TELEMETRY_FIELDS <= set(payload):
                raise ProcessTelemetryError("terminal telemetry schema is incomplete")
            if storage_exact:
                self._storage_sealed = True
            self._finished = True
            self._emitted = dict(payload)
            return payload

    def finish(
        self,
        *,
        scientific_counters: Mapping[str, object],
        host_call_ledger: Mapping[str, object],
    ) -> dict[str, object]:
        """Finish a run whose durable artifacts were created under recorder contexts."""

        return self._finish(
            scientific_counters=scientific_counters,
            host_call_ledger=host_call_ledger,
        )

    def finish_incomplete(
        self,
        *,
        scientific_counters: Mapping[str, object],
        host_call_ledger: Mapping[str, object],
    ) -> dict[str, object]:
        """Seal immutable partials plus an INCOMPLETE quarantine without reinterpretation."""

        return self._finish(
            scientific_counters=scientific_counters,
            host_call_ledger=host_call_ledger,
            allow_incomplete=True,
        )

    @staticmethod
    def _write_publication_file(root: Path, relative: str, encoded: bytes) -> None:
        target = root / relative
        if target.exists():
            raise ProcessTelemetryError(f"INCOMPLETE: observer publication target exists: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            written = stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if written != len(encoded):
            raise ProcessTelemetryError(f"INCOMPLETE: observer publication write was short: {relative}")

    def publish_observer_bundle(
        self,
        publication_root: Path,
        *,
        namespace: str,
        scientific_body_relative_path: str | Path,
        publication_root_is_new_namespace: bool,
    ) -> dict[str, object]:
        """Publish telemetry and VALID claim outside the scientific boundary.

        Scientific process/storage measurement is already sealed.  Telemetry
        binds the RESULT_BODY/checkpoint inventory in the emitted payload; the
        module-owned VALID claim binds namespace, body, telemetry and storage.
        Observer publication time and bytes are recorded separately and are
        expressly excluded from scientific wall/CPU/durable measurements.
        """

        if (
            not isinstance(namespace, str)
            or not namespace
            or namespace.strip() != namespace
            or len(namespace) > 256
            or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/.:" for character in namespace)
        ):
            raise ProcessTelemetryError("observer namespace is invalid")
        body_relative = _safe_relative_artifact_path(scientific_body_relative_path)
        telemetry_relative = TELEMETRY_TERMINAL_NAME
        with self._lock:
            if not self._finished or self._emitted is None:
                raise ProcessTelemetryError("scientific telemetry/storage boundary is not sealed")
            if self._observer_publication_root is not None:
                raise ProcessTelemetryError("observer publication may occur only once")
            if publication_root_is_new_namespace is not True:
                raise ProcessTelemetryError("observer publication root must be a new namespace")
            scientific_storage = self.verify_storage_seal()
            body_record = self._durable_records.get(body_relative)
            if body_record is None:
                raise ProcessTelemetryError("bound scientific body is absent from exact storage seal")
            incomplete = self._emitted.get("attempt_disposition") == "INCOMPLETE"
            claim_relative = INCOMPLETE_CLAIM_NAME if incomplete else VALID_CLAIM_NAME
            root = Path(publication_root)
            root_identity = _plain_root_identity(root)
            root_resolved = root.resolve()
            scratch = self.scratch_root.resolve()
            durable = self.durable_root.resolve()
            if (
                root_resolved in {scratch, durable}
                or root_resolved in scratch.parents
                or root_resolved in durable.parents
                or scratch in root_resolved.parents
                or durable in root_resolved.parents
            ):
                raise ProcessTelemetryError("observer publication root overlaps invocation storage")
            directories, files = _durable_inventory(root)
            if directories or files:
                raise ProcessTelemetryError("observer publication root was not empty")
            self._observer_publication_root = root
            self._observer_publication_root_identity = root_identity
            self._observer_namespace = namespace
            self._observer_body_relative = body_relative
            self._observer_claim_name = claim_relative
            started_wall = time.perf_counter()
            started_cpu = time.process_time()
            telemetry_document = {
                "schema": "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1",
                "namespace": namespace,
                "scientific_body": body_record.public(),
                "scientific_storage_seal": scientific_storage,
                "telemetry": self._emitted,
            }
            telemetry_bytes = _canonical_json_bytes(telemetry_document)
            self._write_publication_file(root, telemetry_relative, telemetry_bytes)
            telemetry_record = _durable_inventory(root)[1].get(telemetry_relative)
            if telemetry_record is None:
                raise ProcessTelemetryError("INCOMPLETE: telemetry publication artifact is absent")
            claim_document = {
                "schema": (
                    "VNFC_BPCR_BEXP_R01_INCOMPLETE_CLAIM_V1"
                    if incomplete
                    else "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1"
                ),
                "namespace": namespace,
                "scientific_body_relative_path": body_record.relative_path,
                "scientific_body_size_bytes": body_record.size_bytes,
                "scientific_body_sha256": body_record.sha256,
                "scientific_storage_seal_sha256": hashlib.sha256(
                    _canonical_json_bytes(scientific_storage)
                ).hexdigest(),
                "telemetry_relative_path": telemetry_record.relative_path,
                "telemetry_size_bytes": telemetry_record.size_bytes,
                "telemetry_sha256": telemetry_record.sha256,
            }
            if incomplete:
                claim_document.update(
                    {
                        "attempt_disposition": "INCOMPLETE",
                        "incomplete_reasons_sha256": hashlib.sha256(
                            _canonical_json_bytes(
                                {"incomplete_reasons": self._emitted["incomplete_reasons"]}
                            )
                        ).hexdigest(),
                    }
                )
            claim_bytes = _canonical_json_bytes(claim_document)
            self._write_publication_file(root, claim_relative, claim_bytes)
            directories, files = _durable_inventory(root)
            expected_files = {telemetry_relative, claim_relative}
            if set(files) != expected_files or set(directories) != _required_parent_directories(
                tuple(expected_files)
            ):
                raise ProcessTelemetryError("INCOMPLETE: observer publication inventory differs")
            self._observer_publication_records = files
            self._observer_publication_sealed = True
            elapsed_wall = time.perf_counter() - started_wall
            elapsed_cpu = time.process_time() - started_cpu
            return {
                "schema": "VNFC_BPCR_BEXP_R01_OBSERVER_PUBLICATION_RECEIPT_V1",
                "measurement_boundary": (
                    "scientific process and durable storage sealed before observer publication"
                ),
                "observer_publication_overhead_excluded_from_scientific_measurement": True,
                "observer_publication_wall_seconds": elapsed_wall,
                "observer_publication_cpu_seconds": elapsed_cpu,
                "telemetry_publication_bytes": sum(record.size_bytes for record in files.values()),
                "telemetry_terminal_bytes": telemetry_record.size_bytes,
                "observer_claim_bytes": files[claim_relative].size_bytes,
                "claim_disposition": "INCOMPLETE" if incomplete else "VALID",
                "telemetry_publication_sha256": telemetry_record.sha256,
                "publication_artifact_inventory": tuple(
                    files[name].public() for name in sorted(files)
                ),
                "scientific_storage_binding": scientific_storage,
                "valid": True,
            }

    def verify_observer_publication(self) -> dict[str, object]:
        with self._lock:
            if (
                not self._observer_publication_sealed
                or self._observer_publication_root is None
                or self._observer_publication_root_identity is None
            ):
                raise ProcessTelemetryError("observer publication seal is absent")
            if _plain_root_identity(self._observer_publication_root) != self._observer_publication_root_identity:
                raise ProcessTelemetryError("INCOMPLETE: observer publication root identity changed")
            directories, files = _durable_inventory(self._observer_publication_root)
            if files != self._observer_publication_records or set(directories) != _required_parent_directories(
                tuple(files)
            ):
                raise ProcessTelemetryError("INCOMPLETE: observer publication changed after seal")
            if (
                self._observer_namespace is None
                or self._observer_body_relative is None
                or self._observer_claim_name is None
                or self._emitted is None
            ):
                raise ProcessTelemetryError("INCOMPLETE: observer publication binding state is absent")
            body_record = self._durable_records.get(self._observer_body_relative)
            telemetry_record = files.get(TELEMETRY_TERMINAL_NAME)
            claim_record = files.get(self._observer_claim_name)
            if body_record is None or telemetry_record is None or claim_record is None:
                raise ProcessTelemetryError("INCOMPLETE: observer publication binding inventory differs")
            scientific_storage = self.verify_storage_seal()
            telemetry_document = {
                "schema": "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1",
                "namespace": self._observer_namespace,
                "scientific_body": body_record.public(),
                "scientific_storage_seal": scientific_storage,
                "telemetry": self._emitted,
            }
            expected_telemetry = _canonical_json_bytes(telemetry_document)
            actual_telemetry = (self._observer_publication_root / TELEMETRY_TERMINAL_NAME).read_bytes()
            if actual_telemetry != expected_telemetry:
                raise ProcessTelemetryError("INCOMPLETE: TELEMETRY_TERMINAL schema/binding differs")
            incomplete = self._emitted.get("attempt_disposition") == "INCOMPLETE"
            claim_document = {
                "schema": (
                    "VNFC_BPCR_BEXP_R01_INCOMPLETE_CLAIM_V1"
                    if incomplete
                    else "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1"
                ),
                "namespace": self._observer_namespace,
                "scientific_body_relative_path": body_record.relative_path,
                "scientific_body_size_bytes": body_record.size_bytes,
                "scientific_body_sha256": body_record.sha256,
                "scientific_storage_seal_sha256": hashlib.sha256(
                    _canonical_json_bytes(scientific_storage)
                ).hexdigest(),
                "telemetry_relative_path": telemetry_record.relative_path,
                "telemetry_size_bytes": telemetry_record.size_bytes,
                "telemetry_sha256": telemetry_record.sha256,
            }
            if incomplete:
                claim_document.update(
                    {
                        "attempt_disposition": "INCOMPLETE",
                        "incomplete_reasons_sha256": hashlib.sha256(
                            _canonical_json_bytes(
                                {"incomplete_reasons": self._emitted["incomplete_reasons"]}
                            )
                        ).hexdigest(),
                    }
                )
            actual_claim = (self._observer_publication_root / self._observer_claim_name).read_bytes()
            if actual_claim != _canonical_json_bytes(claim_document):
                raise ProcessTelemetryError("INCOMPLETE: observer claim schema/binding differs")
            return {
                "publication_artifact_inventory": tuple(
                    files[name].public() for name in sorted(files)
                ),
                "valid": True,
            }

    def emit(self, payload: Mapping[str, object]) -> None:
        """Runner-compatible terminal consumer; accepts only this monitor's terminal."""

        with self._lock:
            if not self._finished or self._emitted is None:
                raise ProcessTelemetryError("telemetry terminal has not been formed")
            if self._test_mode:
                raise ProcessTelemetryError("test-mode telemetry cannot be emitted as performance evidence")
            if self._emitted.get("implementation_ready") is not True:
                raise ProcessTelemetryError(
                    f"REPAIR_REQUIRED: production telemetry evidence is fenced: {IMPLEMENTATION_BLOCKER}"
                )
            self.verify_storage_seal()
            self.verify_observer_publication()
            if dict(payload) != self._emitted:
                raise ProcessTelemetryError("emitted telemetry differs from measured terminal")


__all__ = [
    "ARMS",
    "ExactStorageContract",
    "FROZEN_SAMPLE_INTERVAL_SECONDS",
    "IMPLEMENTATION_BLOCKER",
    "IMPLEMENTATION_READY",
    "MINIMUM_AVAILABLE_BYTES",
    "PREFLIGHT_FRESH_SECONDS",
    "ProcessSample",
    "ProcessTelemetryError",
    "ProcessTreeTelemetrySink",
    "STAGES",
    "TELEMETRY_FIELDS",
    "TELEMETRY_SCHEMA",
    "sample_windows_process_tree",
]
