"""Result-blind process-tree and filesystem telemetry for OMRC B0.

The monitor is deliberately independent of the host and learner.  It records
engineering facts only; the B0 orchestrator combines those facts with the
engine's explicit work counters and refuses zero-work or incomplete records.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
import math
import os
from pathlib import Path
import threading
import time
from typing import Any, Mapping


GIB = 1024**3
MIB = 1024**2
B0_WALL_CAP_SECONDS = 1_800.0
PEAK_RSS_CAP_BYTES = 4 * GIB
SCRATCH_CAP_BYTES = 2 * GIB
DURABLE_CAP_BYTES = 512 * MIB


class TelemetryError(ValueError):
    """Required runtime telemetry is absent, nonfinite, or over a cap."""


@dataclass(frozen=True)
class ResourceCaps:
    wall_seconds: float = B0_WALL_CAP_SECONDS
    process_tree_peak_rss_bytes: int = PEAK_RSS_CAP_BYTES
    scratch_high_water_bytes: int = SCRATCH_CAP_BYTES
    durable_high_water_bytes: int = DURABLE_CAP_BYTES

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


REQUIRED_TELEMETRY_FIELDS = frozenset(
    {
        "measurement_complete",
        "measurement_source",
        "sample_interval_seconds",
        "sample_count",
        "end_to_end_wall_seconds",
        "end_to_end_cpu_seconds",
        "cpu_core_equivalents",
        "cpu_occupancy_fraction",
        "process_tree_peak_rss_bytes",
        "peak_process_count",
        "peak_thread_count",
        "worker_count",
        "threads_per_worker",
        "io_read_bytes",
        "io_write_bytes",
        "scratch_high_water_bytes",
        "durable_high_water_bytes",
        "scientific_work_transitions",
        "scientific_work_transitions_per_second",
        "stage_measurements",
    }
)


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TelemetryError(f"{name} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TelemetryError(f"{name} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise TelemetryError(f"{name} must be a positive finite number")
    return number


def _finite_nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TelemetryError(f"{name} must be a nonnegative finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TelemetryError(f"{name} must be a nonnegative finite number") from exc
    if not math.isfinite(number) or number < 0:
        raise TelemetryError(f"{name} must be a nonnegative finite number")
    return number


def _nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise TelemetryError(f"{name} must be a nonnegative integer")
    return value


def validate_telemetry(
    value: Mapping[str, Any], *, caps: ResourceCaps = ResourceCaps()
) -> dict[str, Any]:
    """Validate measured, nonzero B0 work without interpreting outcomes."""

    missing = REQUIRED_TELEMETRY_FIELDS - set(value)
    if missing:
        raise TelemetryError(f"telemetry fields are missing: {sorted(missing)}")
    record = dict(value)
    if record["measurement_complete"] is not True:
        raise TelemetryError("telemetry measurement is incomplete")
    if not isinstance(record["measurement_source"], str) or not record[
        "measurement_source"
    ].strip():
        raise TelemetryError("telemetry measurement_source is absent")

    sample_interval = _finite_positive(
        record["sample_interval_seconds"], "sample_interval_seconds"
    )
    sample_count = _nonnegative_int(record["sample_count"], "sample_count")
    if sample_count < 2:
        raise TelemetryError("telemetry requires at least two process-tree samples")
    wall = _finite_positive(record["end_to_end_wall_seconds"], "end_to_end_wall_seconds")
    cpu = _finite_nonnegative(
        record["end_to_end_cpu_seconds"], "end_to_end_cpu_seconds"
    )
    core_equivalents = _finite_nonnegative(
        record["cpu_core_equivalents"], "cpu_core_equivalents"
    )
    occupancy = _finite_nonnegative(
        record["cpu_occupancy_fraction"], "cpu_occupancy_fraction"
    )
    rss = _nonnegative_int(
        record["process_tree_peak_rss_bytes"], "process_tree_peak_rss_bytes"
    )
    if rss == 0:
        raise TelemetryError("process_tree_peak_rss_bytes must be measured and nonzero")
    for name in ("peak_process_count", "peak_thread_count", "worker_count", "threads_per_worker"):
        if _nonnegative_int(record[name], name) < 1:
            raise TelemetryError(f"{name} must be at least one")
    for name in (
        "io_read_bytes",
        "io_write_bytes",
        "scratch_high_water_bytes",
        "durable_high_water_bytes",
    ):
        _nonnegative_int(record[name], name)
    transitions = _nonnegative_int(
        record["scientific_work_transitions"], "scientific_work_transitions"
    )
    if transitions == 0:
        raise TelemetryError("zero scientific work is not performance evidence")
    throughput = _finite_positive(
        record["scientific_work_transitions_per_second"],
        "scientific_work_transitions_per_second",
    )
    expected_throughput = transitions / wall
    if not math.isclose(throughput, expected_throughput, rel_tol=1e-9, abs_tol=1e-12):
        raise TelemetryError("scientific-work throughput differs from transitions / wall")
    if not math.isclose(core_equivalents, cpu / wall, rel_tol=1e-9, abs_tol=1e-12):
        raise TelemetryError("cpu_core_equivalents differs from cpu / wall")
    expected_occupancy = core_equivalents / record["worker_count"]
    if not math.isclose(occupancy, expected_occupancy, rel_tol=1e-9, abs_tol=1e-12):
        raise TelemetryError("cpu occupancy differs from measured CPU, wall, and workers")

    stages = record["stage_measurements"]
    if not isinstance(stages, list) or not stages:
        raise TelemetryError("stage_measurements must contain measured stages")
    for index, stage in enumerate(stages):
        if not isinstance(stage, Mapping):
            raise TelemetryError(f"stage_measurements[{index}] must be an object")
        if not isinstance(stage.get("stage"), str) or not stage["stage"].strip():
            raise TelemetryError(f"stage_measurements[{index}].stage is absent")
        _finite_positive(stage.get("wall_seconds"), f"stage[{index}].wall_seconds")
        _finite_nonnegative(stage.get("cpu_seconds"), f"stage[{index}].cpu_seconds")
        stage_wall = float(stage["wall_seconds"])
        stage_transitions = _nonnegative_int(
            stage.get("transitions"), f"stage[{index}].transitions"
        )
        if stage_transitions == 0:
            raise TelemetryError(f"stage_measurements[{index}] reports zero work")
        stage_throughput = _finite_positive(
            stage.get("transitions_per_second"),
            f"stage[{index}].transitions_per_second",
        )
        if not math.isclose(
            stage_throughput,
            stage_transitions / stage_wall,
            rel_tol=1e-9,
            abs_tol=1e-12,
        ):
            raise TelemetryError(f"stage_measurements[{index}] throughput differs")

    cap_failures = []
    if wall > caps.wall_seconds:
        cap_failures.append("wall_seconds")
    if rss > caps.process_tree_peak_rss_bytes:
        cap_failures.append("process_tree_peak_rss_bytes")
    if record["scratch_high_water_bytes"] > caps.scratch_high_water_bytes:
        cap_failures.append("scratch_high_water_bytes")
    if record["durable_high_water_bytes"] > caps.durable_high_water_bytes:
        cap_failures.append("durable_high_water_bytes")
    if cap_failures:
        raise TelemetryError(f"resource cap exceeded: {','.join(cap_failures)}")

    record["sample_interval_seconds"] = sample_interval
    return record


#: Only the wall cap stops a B1 run.  Section-11 recast, owner decisions 3 and 7
#: of 2026-09-02: the peak-RSS, scratch and durable caps are recorded budgets, a
#: measured exceedance is recorded, and missing or failed resource measurement
#: downgrades to ``resources_unmeasured`` rather than annulling or quarantining.
STOPPING_CAPS = ("wall_seconds",)
RESOURCE_ASSESSMENT_SCHEMA = "cbsc_omrc_b01_resource_assessment_v1"


def assess_resource_telemetry(
    value: object, *, caps: ResourceCaps = ResourceCaps()
) -> dict[str, Any]:
    """Assess one invocation's resource telemetry without refusing on it.

    Returns a record that is always publishable.  ``resources_unmeasured`` is
    true when the measurement is absent, unreadable, or fails validation, and
    ``unmeasured_reasons`` says why.  ``cap_exceedances`` lists every measured
    cap that was exceeded; ``stop_run`` is true only for the wall cap.

    Learner-side instrumentation failure is out of scope here and still
    quarantines under evidence spec §6.2; this function judges resource
    telemetry only.
    """

    record: dict[str, Any] = {
        "schema": RESOURCE_ASSESSMENT_SCHEMA,
        "resources_unmeasured": False,
        "unmeasured_reasons": [],
        "cap_exceedances": [],
        "stopping_cap_exceedances": [],
        "stop_run": False,
        "caps": caps.as_dict(),
        "measurement": None,
    }
    measured = dict(value) if isinstance(value, Mapping) else {}
    try:
        measured = validate_telemetry(measured, caps=RECORDED_BUDGET_CAPS)
    except (TypeError, ValueError) as exc:
        record["resources_unmeasured"] = True
        record["unmeasured_reasons"] = [
            "telemetry_missing" if value is None else f"telemetry_measurement_failed: {exc}"
        ]
        measured["measurement_complete"] = False
    # Keep actual partial observations; missing or malformed quantities are null.
    for name in REQUIRED_TELEMETRY_FIELDS - {
        "measurement_complete", "measurement_source", "stage_measurements",
        "scientific_work_transitions",
    }:
        number = measured.get(name)
        if type(number) not in (int, float) or not math.isfinite(number) or number < 0:
            measured[name] = None
    measured["resources_unmeasured"] = record["resources_unmeasured"]
    record["measurement"] = measured
    exceeded: list[str] = []
    for field, cap_name in (
        ("end_to_end_wall_seconds", "wall_seconds"),
        ("process_tree_peak_rss_bytes", "process_tree_peak_rss_bytes"),
        ("scratch_high_water_bytes", "scratch_high_water_bytes"),
        ("durable_high_water_bytes", "durable_high_water_bytes"),
    ):
        if measured[field] is not None and measured[field] > getattr(caps, cap_name):
            exceeded.append(cap_name)
    record["cap_exceedances"] = exceeded
    stopping = [name for name in exceeded if name in STOPPING_CAPS]
    record["stopping_cap_exceedances"] = stopping
    record["stop_run"] = bool(stopping)
    return record


#: The RSS, scratch and durable caps are recorded budgets under the section-11
#: recast, so completeness validation inside the B1 chain runs against these.
RECORDED_BUDGET_CAPS = ResourceCaps(
    wall_seconds=float("inf"),
    process_tree_peak_rss_bytes=1 << 62,
    scratch_high_water_bytes=1 << 62,
    durable_high_water_bytes=1 << 62,
)


def _tree_size(root: Path, *, exclude: Path | None = None) -> int:
    total = 0
    if not root.exists():
        return 0
    excluded = None if exclude is None else exclude.resolve(strict=False)
    for path in root.rglob("*"):
        try:
            if not path.is_file():
                continue
            if excluded is not None:
                try:
                    path.resolve(strict=False).relative_to(excluded)
                    continue
                except ValueError:
                    pass
            total += path.stat().st_size
        except OSError:
            continue
    return total


def _windows_process_tree_samples(
    root_pid: int,
) -> list[tuple[int, int, float, int, int, int]]:
    """Dependency-free Windows process-tree snapshot using documented Win32 APIs."""

    from ctypes import wintypes

    ULONG_PTR = ctypes.c_size_t

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ULONG_PTR),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
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
    kernel32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
    )
    kernel32.GetProcessIoCounters.argtypes = (wintypes.HANDLE, ctypes.POINTER(IO_COUNTERS))
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD,
    )
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise TelemetryError("CreateToolhelp32Snapshot failed")
    entries: dict[int, tuple[int, int]] = {}
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        more = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while more:
            entries[int(entry.th32ProcessID)] = (
                int(entry.th32ParentProcessID), int(entry.cntThreads)
            )
            more = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    selected = {int(root_pid)}
    changed = True
    while changed:
        changed = False
        for pid, (parent, _) in entries.items():
            if parent in selected and pid not in selected:
                selected.add(pid)
                changed = True
    rows: list[tuple[int, int, float, int, int, int]] = []
    for pid in selected:
        handle = kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not handle:
            continue
        try:
            memory = PROCESS_MEMORY_COUNTERS()
            memory.cb = ctypes.sizeof(memory)
            created = wintypes.FILETIME(); exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME(); user = wintypes.FILETIME()
            io = IO_COUNTERS()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                continue
            if not kernel32.GetProcessTimes(
                handle, ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(kernel), ctypes.byref(user)
            ):
                continue
            if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
                continue
            kernel_ticks = (int(kernel.dwHighDateTime) << 32) | int(kernel.dwLowDateTime)
            user_ticks = (int(user.dwHighDateTime) << 32) | int(user.dwLowDateTime)
            rows.append(
                (
                    pid, int(memory.WorkingSetSize), (kernel_ticks + user_ticks) / 10_000_000.0,
                    int(io.ReadTransferCount), int(io.WriteTransferCount),
                    entries.get(pid, (0, 0))[1],
                )
            )
        finally:
            kernel32.CloseHandle(handle)
    return rows


class ProcessTreeMonitor:
    """Fixed-cadence observation of the current process and descendants."""

    def __init__(
        self,
        scratch_root: Path,
        durable_root: Path,
        *,
        worker_count: int,
        threads_per_worker: int,
        interval_seconds: float = 0.05,
        root_pid: int | None = None,
    ) -> None:
        if worker_count < 1 or threads_per_worker < 1:
            raise TelemetryError("worker topology must be positive")
        self.scratch_root = Path(scratch_root)
        self.durable_root = Path(durable_root)
        self.worker_count = worker_count
        self.threads_per_worker = threads_per_worker
        self.interval_seconds = interval_seconds
        self._subtract_initial_counters = root_pid is None
        self.root_pid = os.getpid() if root_pid is None else int(root_pid)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = 0.0
        self._start_cpu = 0.0
        self._last_cpu = 0.0
        self._start_read = 0
        self._start_write = 0
        self._last_read = 0
        self._last_write = 0
        self._samples = 0
        self._peak_rss = 0
        self._peak_processes = 0
        self._peak_threads = 0
        self._scratch_high = 0
        self._durable_high = 0
        self._error: BaseException | None = None
        self._measurement_source = "uninitialized_process_tree_sampler"

    def _process_samples(self) -> list[tuple[int, int, float, int, int, int]]:
        try:
            import psutil
        except ImportError:
            if os.name != "nt":  # pragma: no cover - Windows is the declared host
                raise TelemetryError("process-tree telemetry backend is unavailable")
            self._measurement_source = "windows_toolhelp_process_tree_fixed_cadence"
            return _windows_process_tree_samples(self.root_pid)
        self._measurement_source = "psutil_process_tree_fixed_cadence"
        root = psutil.Process(self.root_pid)
        rows = []
        for process in [root, *root.children(recursive=True)]:
            try:
                times = process.cpu_times()
                io = process.io_counters()
                rows.append(
                    (
                        int(process.pid), int(process.memory_info().rss),
                        float(times.user + times.system), int(io.read_bytes),
                        int(io.write_bytes), int(process.num_threads()),
                    )
                )
            except Exception:
                continue
        return rows

    def _observe(self) -> None:
        processes = self._process_samples()
        rss = cpu = read = write = threads = 0
        observed = 0
        for _, process_rss, process_cpu, process_read, process_write, process_threads in processes:
            rss += process_rss
            cpu += process_cpu
            read += process_read
            write += process_write
            threads += process_threads
            observed += 1
        if observed == 0:
            raise TelemetryError("no process-tree member could be observed")
        if self._samples == 0:
            # Counters for an explicitly supplied child PID cover that child's
            # whole lifetime, including work before the monitor's first poll.
            # Counters for this already-running process need a local baseline.
            if self._subtract_initial_counters:
                self._start_cpu = cpu
                self._start_read = read
                self._start_write = write
        self._last_cpu = cpu
        self._last_read = read
        self._last_write = write
        self._samples += 1
        self._peak_rss = max(self._peak_rss, rss)
        self._peak_processes = max(self._peak_processes, observed)
        self._peak_threads = max(self._peak_threads, threads)
        self._scratch_high = max(self._scratch_high, _tree_size(self.scratch_root))
        self._durable_high = max(
            self._durable_high,
            _tree_size(self.durable_root, exclude=self.scratch_root),
        )

    def _sample_loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            try:
                self._observe()
            except BaseException as exc:  # surfaced synchronously by finish
                self._error = exc
                self._stop.set()

    def __enter__(self) -> "ProcessTreeMonitor":
        return self.begin()

    def begin(self) -> "ProcessTreeMonitor":
        self._started = time.perf_counter()
        self._observe()
        return self

    def poll_caps(self, *, caps: ResourceCaps = ResourceCaps()) -> tuple[str, ...]:
        """Observe once and return live hard-cap violations to a supervisor."""

        self._observe()
        failures: list[str] = []
        if time.perf_counter() - self._started > caps.wall_seconds:
            failures.append("wall_seconds")
        if self._peak_rss > caps.process_tree_peak_rss_bytes:
            failures.append("process_tree_peak_rss_bytes")
        if self._scratch_high > caps.scratch_high_water_bytes:
            failures.append("scratch_high_water_bytes")
        if self._durable_high > caps.durable_high_water_bytes:
            failures.append("durable_high_water_bytes")
        return tuple(failures)

    def finish(
        self, *, scientific_work_transitions: int, stage_measurements: list[dict[str, Any]]
    ) -> dict[str, Any]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.interval_seconds * 4))
        # The supervised child normally no longer exists here.  Its last live
        # sample is retained rather than substituting the parent's resources.
        if self._error is not None:
            raise TelemetryError("process-tree telemetry failed") from self._error
        wall = time.perf_counter() - self._started
        cpu = self._last_cpu - self._start_cpu
        read = max(0, self._last_read - self._start_read)
        write = max(0, self._last_write - self._start_write)
        return {
            "measurement_complete": True,
            "measurement_source": self._measurement_source,
            "sample_interval_seconds": self.interval_seconds,
            "sample_count": self._samples,
            "end_to_end_wall_seconds": wall,
            "end_to_end_cpu_seconds": cpu,
            "cpu_core_equivalents": cpu / wall if wall else 0.0,
            "cpu_occupancy_fraction": cpu / wall / self.worker_count if wall else 0.0,
            "process_tree_peak_rss_bytes": self._peak_rss,
            "peak_process_count": self._peak_processes,
            "peak_thread_count": self._peak_threads,
            "worker_count": self.worker_count,
            "threads_per_worker": self.threads_per_worker,
            "io_read_bytes": read,
            "io_write_bytes": write,
            "scratch_high_water_bytes": self._scratch_high,
            "durable_high_water_bytes": self._durable_high,
            "scientific_work_transitions": scientific_work_transitions,
            "scientific_work_transitions_per_second": (
                scientific_work_transitions / wall if wall else 0.0
            ),
            "stage_measurements": stage_measurements,
        }

    def incident_snapshot(
        self, *, reason: str, cap_failures: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        """Return outcome-free partial facts for a killed or failed child."""

        wall = max(0.0, time.perf_counter() - self._started)
        return {
            "schema": "cbsc_omrc_b01_supervisor_incident_v1",
            "measurement_complete": False,
            "measurement_source": self._measurement_source,
            "reason": reason,
            "cap_failures": list(cap_failures),
            "sample_interval_seconds": self.interval_seconds,
            "sample_count": self._samples,
            "observed_wall_seconds": wall,
            "observed_cpu_seconds": max(0.0, self._last_cpu - self._start_cpu),
            "process_tree_peak_rss_bytes": self._peak_rss,
            "peak_process_count": self._peak_processes,
            "peak_thread_count": self._peak_threads,
            "io_read_bytes": max(0, self._last_read - self._start_read),
            "io_write_bytes": max(0, self._last_write - self._start_write),
            "scratch_high_water_bytes": self._scratch_high,
            "durable_high_water_bytes": self._durable_high,
            "scientific_branch": None,
        }

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.interval_seconds * 4))


__all__ = [
    "B0_WALL_CAP_SECONDS",
    "DURABLE_CAP_BYTES",
    "PEAK_RSS_CAP_BYTES",
    "ProcessTreeMonitor",
    "ResourceCaps",
    "SCRATCH_CAP_BYTES",
    "TelemetryError",
    "validate_telemetry",
]
