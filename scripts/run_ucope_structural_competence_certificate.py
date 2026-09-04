"""Create, run, and validate the fixed UCOPE structural certificate."""

from __future__ import annotations

import argparse
import ast
import ctypes
from ctypes import wintypes
from io import BytesIO
import gzip
import json
import math
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import uuid
import zlib
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PROJECT_ROOT = PROJECT_ROOT
FROZEN_PYTHON_EXECUTABLE = Path(
    "C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe"
)
FROZEN_PYTHON_VERSION = (3, 11, 9)
FROZEN_PYTHON_IMPLEMENTATION = "CPython"
FROZEN_RESULT_ROOT_ARG = (
    "temp/directions/ucope/exp/ucope-structural-competence-r01"
)
FROZEN_RESULT_ROOT = (
    FROZEN_PROJECT_ROOT
    / "temp/directions/ucope/exp/ucope-structural-competence-r01"
)
STRUCTURAL_PATH = PROJECT_ROOT / "experiments/candidates/ucope/contextual_paid_acquisition_r01/structural_competence.py"
RUNNER_PATH = Path(__file__).resolve()
RUNNER_START_BYTES = RUNNER_PATH.read_bytes()
FIXED_BUNDLE_ROOT = FROZEN_PROJECT_ROOT / "temp/directions/ucope/exp/ucope-structural-competence-reference-bundle-v2"
CONTROL_ROOT = FROZEN_PROJECT_ROOT / "temp/directions/ucope/exp/ucope-structural-competence-controls-v2"
RESOURCE_SCRIPT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
REFERENCE_BUNDLE_FORMAT = "UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V2"
CONTROL_RECEIPT_FORMAT = "UCOPE_STRUCTURAL_CONTROL_STOP_V2"
FIT_FILENAME = "structural-fit.json"
FIT_REFERENCE_FILENAME = "structural-fit-reference.bin"
CERTIFICATE_FILENAME = "structural-competence-certificate.json"
RESOURCE_RECEIPT_FILENAME = "resource-admission.json"
RESOURCE_LEDGER_FILENAME = "resource-ledger.json"
PREFIT_BINDING_RECEIPT_FILENAME = "prefit-binding-receipt.json"
ASSESSMENT_ROOT = CONTROL_ROOT / "assessments"
ASSESSMENT_RECEIPT_FILENAME = "assessment-receipt.json"
ASSESSMENT_FORMAT = "UCOPE_STRUCTURAL_OUTCOME_BLIND_ASSESSMENT_V2"
CONTROL_STAGES_BY_ENTRY = {
    "freeze-reference-bundle": frozenset({
        "EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP",
        "BUNDLE_SOURCE_CAPTURE", "PREFIT_BINDING", "BUNDLE_PUBLICATION",
        "PREPUBLICATION_RESOURCE",
    }),
    "check-binding": frozenset({
        "EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP",
        "PREFIT_BINDING",
    }),
    "run": frozenset({
        "EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP",
        "PERFORMANCE_QUALIFICATION", "PREFIT_BINDING", "FIT",
        "POSTFIT_BINDING", "EVALUATION", "FINAL_BINDING",
        "PREPUBLICATION_RESOURCE",
    }),
    "validate": frozenset({
        "EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP",
        "STORED_RESOURCE_VALIDATION", "PREFIT_BINDING", "REFIT",
        "POSTFIT_BINDING", "EVALUATION", "FINAL_BINDING",
        "PREPUBLICATION_RESOURCE",
    }),
}
CONTROL_STAGES = frozenset().union(*CONTROL_STAGES_BY_ENTRY.values())
MINIMUM_MEMORY_BYTES = 4 * 1024**3
RESOURCE_BASELINE_PROCESS_THREAD_CEILING = 4
RESOURCE_SAMPLER_THREAD_ALLOWANCE = 1
RESOURCE_CEILINGS = {
    "workers": 1,
    "scientific_child_processes": 0,
    "wall_seconds": 3_600,
    "cpu_seconds": 3_600,
    "peak_process_threads": (
        RESOURCE_BASELINE_PROCESS_THREAD_CEILING
        + RESOURCE_SAMPLER_THREAD_ALLOWANCE
    ),
    "peak_rss_bytes": 2 * 1024**3,
    "scratch_high_water_bytes": 256 * 1024**2,
    "durable_high_water_bytes": 256 * 1024**2,
    "aggregate_io_bytes": 8 * 1024**3,
}
PUBLICATION_HEADROOM = {
    "wall_seconds": 10,
    "cpu_seconds": 10,
    "peak_rss_bytes": 16 * 1024**2,
    "scratch_high_water_bytes": 1024**2,
    "durable_high_water_bytes": 1024**2,
    "aggregate_io_bytes": 4 * 1024**2,
}
RESOURCE_MEASUREMENT_SCOPE = (
    "ENTRY_WORK_THROUGH_FINAL_BINDING_BEFORE_FIXED_HEADROOM_TELEMETRY_WRITE_AND_RENAME"
)
RESOURCE_SAMPLE_SECONDS = 0.25


class DataBindingMismatch(ValueError):
    """The fixed source-byte binding could not be established."""


class ResourceAdmissionRefusal(RuntimeError):
    """Fresh physical/effective memory admission did not pass."""


class ExecutionEnvironmentMismatch(RuntimeError):
    """The frozen command environment is not the prospective environment."""


class AssessmentQualificationError(RuntimeError):
    """The unique outcome-blind performance qualification is not usable."""


def require_frozen_execution_environment() -> None:
    """Fail before any UCOPE data state when cwd or interpreter drifts."""
    if Path.cwd().resolve() != FROZEN_PROJECT_ROOT.resolve():
        raise ExecutionEnvironmentMismatch("frozen working directory mismatch")
    if PROJECT_ROOT.resolve() != FROZEN_PROJECT_ROOT.resolve():
        raise ExecutionEnvironmentMismatch("runner project root mismatch")
    if Path(sys.executable).resolve() != FROZEN_PYTHON_EXECUTABLE.resolve():
        raise ExecutionEnvironmentMismatch("frozen interpreter executable mismatch")
    if tuple(sys.version_info[:3]) != FROZEN_PYTHON_VERSION:
        raise ExecutionEnvironmentMismatch("frozen interpreter version mismatch")
    if platform.python_implementation() != FROZEN_PYTHON_IMPLEMENTATION:
        raise ExecutionEnvironmentMismatch("frozen interpreter implementation mismatch")


def require_frozen_result_argument(value: Any) -> None:
    if type(value) is not str or value != FROZEN_RESULT_ROOT_ARG:
        raise ExecutionEnvironmentMismatch("frozen result root argument mismatch")
    if FROZEN_PROJECT_ROOT / Path(value) != FROZEN_RESULT_ROOT:
        raise ExecutionEnvironmentMismatch("frozen absolute result root mismatch")


def require_frozen_result_argv(raw_argv: list[str], command: str) -> None:
    expected = [command, "--output-root", FROZEN_RESULT_ROOT_ARG]
    if raw_argv != expected:
        raise ExecutionEnvironmentMismatch("result command requires exact frozen argv")


def _directory_size(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _unsafe_source_path(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return True
    if os.name == "nt":
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & 0x400)
    return False


def _resource_observation_passes(observed: Mapping[str, Any]) -> bool:
    return bool(
        observed["workers"] == RESOURCE_CEILINGS["workers"]
        and observed["wall_seconds"] + PUBLICATION_HEADROOM["wall_seconds"] <= RESOURCE_CEILINGS["wall_seconds"]
        and observed["cpu_seconds"] + PUBLICATION_HEADROOM["cpu_seconds"] <= RESOURCE_CEILINGS["cpu_seconds"]
        and observed["peak_process_threads"] <= RESOURCE_CEILINGS["peak_process_threads"]
        and observed["peak_rss_bytes"] + PUBLICATION_HEADROOM["peak_rss_bytes"] <= RESOURCE_CEILINGS["peak_rss_bytes"]
        and observed["scientific_child_processes"] <= RESOURCE_CEILINGS["scientific_child_processes"]
        and observed["scratch_high_water_bytes"] + PUBLICATION_HEADROOM["scratch_high_water_bytes"] <= RESOURCE_CEILINGS["scratch_high_water_bytes"]
        and observed["durable_high_water_bytes"] + PUBLICATION_HEADROOM["durable_high_water_bytes"] <= RESOURCE_CEILINGS["durable_high_water_bytes"]
        and observed["aggregate_io_bytes"] + PUBLICATION_HEADROOM["aggregate_io_bytes"] <= RESOURCE_CEILINGS["aggregate_io_bytes"]
    )


class ResourceMonitor:
    """Fixed-cadence process-tree and filesystem high-water sampler.

    Windows observations use GetProcessMemoryInfo, GetProcessIoCounters,
    GetProcessTimes, and CreateToolhelp32Snapshot through the host process
    library; other hosts use dependency-free process counters where available.
    """

    def __init__(self, entry: str, *, scratch: Path | None = None, durable: Path | None = None) -> None:
        self.entry = entry
        self.scratch = scratch
        self.durable = durable
        self.started = time.perf_counter()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._peak_rss_bytes = 0
        self._peak_process_threads = 0
        self._scientific_child_processes = 0
        self._cpu_seconds = 0.0
        self._read_bytes = 0
        self._write_bytes = 0
        self._scratch_high_water_bytes = 0
        self._durable_high_water_bytes = 0
        self._sampler_error: BaseException | None = None
        self._thread = threading.Thread(target=self._sample_loop, name="ucope-resource-sampler", daemon=True)
        self._started = False
        self._finished_ledger: dict[str, Any] | None = None

    def set_paths(self, *, scratch: Path | None = None, durable: Path | None = None) -> None:
        self.scratch = scratch
        self.durable = durable

    def start(self) -> "ResourceMonitor":
        try:
            self._sample_once()
            self._baseline_cpu_seconds = self._cpu_seconds
            self._baseline_read_bytes = self._read_bytes
            self._baseline_write_bytes = self._write_bytes
            self._thread.start()
            self._started = True
        except BaseException:
            self._stop.set()
            if self._thread.is_alive():
                self._thread.join(timeout=2.0)
            raise
        return self

    def _process_observation(self) -> tuple[float, int, int, int, int, int]:
        if os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi

            class PROCESSENTRY32W(ctypes.Structure):
                _fields_ = [
                    ("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                    ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                    ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260),
                ]

            class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t),
                ]

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("ReadOperationCount", ctypes.c_ulonglong), ("WriteOperationCount", ctypes.c_ulonglong),
                    ("OtherOperationCount", ctypes.c_ulonglong), ("ReadTransferCount", ctypes.c_ulonglong),
                    ("WriteTransferCount", ctypes.c_ulonglong), ("OtherTransferCount", ctypes.c_ulonglong),
                ]

            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong)]

            kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
            kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
            kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
            kernel32.Process32FirstW.restype = wintypes.BOOL
            kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
            kernel32.Process32NextW.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel32.GetProcessIoCounters.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(IO_COUNTERS),
            ]
            kernel32.GetProcessIoCounters.restype = wintypes.BOOL
            kernel32.GetProcessTimes.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME),
            ]
            kernel32.GetProcessTimes.restype = wintypes.BOOL

            snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
            if snapshot in (0, ctypes.c_void_p(-1).value):
                raise RuntimeError("CreateToolhelp32Snapshot failed")
            entries: list[tuple[int, int, int]] = []
            try:
                entry = PROCESSENTRY32W()
                entry.dwSize = ctypes.sizeof(entry)
                present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
                if not present:
                    raise RuntimeError("Process32FirstW failed")
                while present:
                    entries.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID), int(entry.cntThreads)))
                    present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
            finally:
                kernel32.CloseHandle(snapshot)
            descendants = {os.getpid()}
            changed = True
            while changed:
                changed = False
                for pid, parent, _ in entries:
                    if parent in descendants and pid not in descendants:
                        descendants.add(pid)
                        changed = True
            thread_map = {pid: count for pid, _, count in entries}
            if os.getpid() not in thread_map:
                raise RuntimeError("current process is absent from the process snapshot")
            cpu_seconds = 0.0
            rss_bytes = read_bytes = write_bytes = 0
            for pid in sorted(descendants):
                handle = kernel32.GetCurrentProcess() if pid == os.getpid() else kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
                if not handle:
                    continue
                close = pid != os.getpid()
                try:
                    memory = PROCESS_MEMORY_COUNTERS_EX()
                    memory.cb = ctypes.sizeof(memory)
                    memory_ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb)
                    if memory_ok:
                        rss_bytes += int(memory.WorkingSetSize)
                    io = IO_COUNTERS()
                    io_ok = kernel32.GetProcessIoCounters(handle, ctypes.byref(io))
                    if io_ok:
                        read_bytes += int(io.ReadTransferCount)
                        write_bytes += int(io.WriteTransferCount)
                    creation = FILETIME(); exit_time = FILETIME(); kernel = FILETIME(); user = FILETIME()
                    times_ok = kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user))
                    if times_ok:
                        ticks = (kernel.dwHighDateTime << 32) + kernel.dwLowDateTime
                        ticks += (user.dwHighDateTime << 32) + user.dwLowDateTime
                        cpu_seconds += ticks / 10_000_000.0
                    if pid == os.getpid() and not (memory_ok and io_ok and times_ok):
                        raise RuntimeError("current process resource counters are unavailable")
                finally:
                    if close:
                        kernel32.CloseHandle(handle)
            threads = sum(thread_map.get(pid, 0) for pid in descendants)
            return cpu_seconds, rss_bytes, threads, max(0, len(descendants) - 1), read_bytes, write_bytes

        cpu = os.times()
        rss_bytes = 0
        try:
            import resource
            rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
        except (ImportError, OSError):
            pass
        return float(cpu.user + cpu.system), rss_bytes, threading.active_count(), 0, 0, 0

    def _sample_once(self) -> None:
        cpu_seconds, rss_bytes, threads, children, read_bytes, write_bytes = self._process_observation()
        scratch = _directory_size(self.scratch)
        durable = _directory_size(self.durable)
        with self._lock:
            self._cpu_seconds = max(self._cpu_seconds, cpu_seconds)
            self._peak_rss_bytes = max(self._peak_rss_bytes, rss_bytes)
            self._peak_process_threads = max(self._peak_process_threads, threads)
            self._scientific_child_processes = max(self._scientific_child_processes, children)
            self._read_bytes = max(self._read_bytes, read_bytes)
            self._write_bytes = max(self._write_bytes, write_bytes)
            self._scratch_high_water_bytes = max(self._scratch_high_water_bytes, scratch)
            self._durable_high_water_bytes = max(self._durable_high_water_bytes, durable)

    def _sample_loop(self) -> None:
        try:
            while not self._stop.wait(RESOURCE_SAMPLE_SECONDS):
                self._sample_once()
        except BaseException as exc:
            self._sampler_error = exc
            self._stop.set()

    def finish(self) -> dict[str, Any]:
        if self._finished_ledger is not None:
            return self._finished_ledger
        if not self._started:
            raise RuntimeError("resource sampler was not started")
        self._stop.set()
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            raise RuntimeError("resource sampler did not terminate")
        if self._sampler_error is not None:
            raise RuntimeError("resource sampler failed") from self._sampler_error
        self._sample_once()
        with self._lock:
            wall_seconds = time.perf_counter() - self.started
            cpu_seconds = max(0.0, self._cpu_seconds - self._baseline_cpu_seconds)
            read_bytes = max(0, self._read_bytes - self._baseline_read_bytes)
            write_bytes = max(0, self._write_bytes - self._baseline_write_bytes)
            aggregate_io_bytes = read_bytes + write_bytes
            observed = {
                "workers": 1,
                "wall_seconds": wall_seconds,
                "cpu_seconds": cpu_seconds,
                "peak_process_threads": self._peak_process_threads,
                "peak_rss_bytes": self._peak_rss_bytes,
                "scientific_child_processes": self._scientific_child_processes,
                "scratch_high_water_bytes": self._scratch_high_water_bytes,
                "durable_high_water_bytes": self._durable_high_water_bytes,
                "read_bytes": read_bytes,
                "write_bytes": write_bytes,
                "aggregate_io_bytes": aggregate_io_bytes,
            }
        passed = _resource_observation_passes(observed)
        self._finished_ledger = {
            "format": "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1",
            "entry": self.entry,
            "ceilings": dict(RESOURCE_CEILINGS),
            "measurement_scope": RESOURCE_MEASUREMENT_SCOPE,
            "sample_interval_seconds": RESOURCE_SAMPLE_SECONDS,
            "publication_headroom": dict(PUBLICATION_HEADROOM),
            "observed": observed,
            "passed": passed,
        }
        return self._finished_ledger


class BindingCapture(dict):
    def __init__(
        self,
        receipt: Mapping[str, Any],
        *,
        manifest_bytes: bytes,
        frozen_binding_bytes: bytes,
        bundle_admission_bytes: bytes,
        bundle_ledger_bytes: bytes,
        prefit_bytes: tuple[bytes, ...],
    ) -> None:
        super().__init__(receipt)
        self.manifest_bytes = manifest_bytes
        self.frozen_binding_bytes = frozen_binding_bytes
        self.bundle_admission_bytes = bundle_admission_bytes
        self.bundle_ledger_bytes = bundle_ledger_bytes
        self.prefit_bytes = prefit_bytes
        self.tape_bytes = prefit_bytes[:80]


class PostfitCapture(dict):
    def __init__(self, receipt: Mapping[str, Any], runtime: Mapping[str, Any], postfit_bytes: tuple[bytes, ...]) -> None:
        super().__init__(receipt)
        self.runtime = runtime
        self.postfit_bytes = postfit_bytes


def _source_lists() -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    data_prefix = (
        "temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/"
        "preflight/support/materialized"
    )
    retained = "temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production"
    package = "experiments/candidates/ucope/contextual_paid_acquisition_r01"
    prefit: list[tuple[str, str]] = [
        (f"{data_prefix}/cell-{seed:02d}-{cell:02d}.jsonl.gz", "retained_gzip_tape")
        for seed in range(10)
        for cell in range(8)
    ]
    prefit.extend(
        (
            (f"{retained}/manifest.json", "retained_manifest"),
            (f"{retained}/preflight/production-preflight.json", "retained_preflight"),
            (f"{retained}/preflight/support/support-preflight.json", "retained_support"),
            (f"{package}/contract.py", "frozen_contract_source"),
            (f"{package}/schema.py", "frozen_schema_source"),
            (f"{package}/training.py", "frozen_training_source"),
            (f"{package}/rng.py", "frozen_rng_source"),
            (f"{package}/structural_replay.py", "frozen_structural_replay_source"),
            (f"{package}/structural_competence.py", "structural_source"),
            ("scripts/run_ucope_structural_competence_certificate.py", "runner_source"),
        )
    )
    postfit = ((f"{package}/oracle.py", "frozen_oracle_source"),)
    return tuple(prefit), postfit


PREFIT_MEMBERS, POSTFIT_MEMBERS = _source_lists()
ALL_MEMBERS = PREFIT_MEMBERS + POSTFIT_MEMBERS
STRUCTURAL_ORDINAL = next(index for index, (_, role) in enumerate(ALL_MEMBERS) if role == "structural_source")
RUNNER_ORDINAL = next(index for index, (_, role) in enumerate(ALL_MEMBERS) if role == "runner_source")
RNG_ORDINAL = next(index for index, (_, role) in enumerate(ALL_MEMBERS) if role == "frozen_rng_source")
STRUCTURAL_REPLAY_ORDINAL = next(
    index
    for index, (_, role) in enumerate(ALL_MEMBERS)
    if role == "frozen_structural_replay_source"
)
CONTRACT_ORDINAL = next(index for index, (_, role) in enumerate(ALL_MEMBERS) if role == "frozen_contract_source")


def _plain_jsonable(value: Any) -> Any:
    from fractions import Fraction

    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, Mapping):
        return {str(key): _plain_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_jsonable(item) for item in value]
    return value


def _plain_canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _reject_nonfinite_json(value: str) -> None:
    raise DataBindingMismatch(f"nonfinite JSON constant is forbidden: {value}")


def _compile_structural(raw: bytes):
    module = types.ModuleType(f"_ucope_bound_structural_{uuid.uuid4().hex}")
    module.__file__ = str(STRUCTURAL_PATH)
    exec(compile(raw, str(STRUCTURAL_PATH), "exec"), module.__dict__)
    return module


def _load_live_structural_for_nonproduction_tests():
    return _compile_structural(STRUCTURAL_PATH.read_bytes())


class _StructuralFacade:
    def __init__(self) -> None:
        object.__setattr__(self, "_module", None)

    def use(self, module: Any) -> None:
        object.__setattr__(self, "_module", module)

    def get(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = _load_live_structural_for_nonproduction_tests()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self.get(), name, value)


STRUCTURAL = _StructuralFacade()


def atomic_create_bytes(path: str | Path, payload: bytes) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return destination


def atomic_create_json(path: str | Path, value: Any) -> Path:
    return atomic_create_bytes(path, _plain_canonical_bytes(value))


def _admit_memory(entry: str) -> dict[str, Any]:
    resource_program = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
    receipt_path = CONTROL_ROOT / "resource-receipts" / f"{entry}-{uuid.uuid4().hex}.json"
    try:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [str(FROZEN_PYTHON_EXECUTABLE), str(resource_program), "admit-memory", "--out", str(receipt_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ResourceAdmissionRefusal("fresh memory admission could not execute") from exc
    if completed.returncode != 0 or not receipt_path.is_file():
        raise ResourceAdmissionRefusal("fresh memory admission command refused")
    try:
        receipt = json.loads(receipt_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResourceAdmissionRefusal("fresh memory receipt is unreadable") from exc
    required = {
        "passed", "available_physical_bytes", "effective_available_bytes",
        "physical_floor_pass", "effective_floor_pass",
    }
    if (
        not isinstance(receipt, dict)
        or not required <= set(receipt)
        or receipt["passed"] is not True
        or receipt["physical_floor_pass"] is not True
        or receipt["effective_floor_pass"] is not True
        or type(receipt["available_physical_bytes"]) is not int
        or type(receipt["effective_available_bytes"]) is not int
        or receipt["available_physical_bytes"] < MINIMUM_MEMORY_BYTES
        or receipt["effective_available_bytes"] < MINIMUM_MEMORY_BYTES
    ):
        raise ResourceAdmissionRefusal("fresh physical/effective memory floor failed")
    return {
        "entry": entry,
        "preflight_receipt_relative_path": receipt_path.relative_to(PROJECT_ROOT).as_posix(),
        **receipt,
    }


def _persist_entry_admission(entry: str, receipt: Mapping[str, Any]) -> Path | None:
    retained = receipt.get("preflight_receipt_relative_path")
    if isinstance(retained, str):
        path = PROJECT_ROOT / retained
        if path.is_file():
            return path
    required = {"available_physical_bytes", "effective_available_bytes", "physical_floor_pass", "effective_floor_pass"}
    if not required <= set(receipt):
        return None
    destination = CONTROL_ROOT / "resource-receipts" / f"{entry}-{uuid.uuid4().hex}.json"
    return atomic_create_json(destination, dict(receipt))


def _admission_relative_path(receipt: Mapping[str, Any] | None) -> str | None:
    if receipt is None:
        return None
    value = receipt.get("preflight_receipt_relative_path")
    if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
        return None
    return value


def _member_record(ordinal: int, source: str, role: str, phase: str) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "source_relative_path": source,
        "bundle_relative_path": f"members/{ordinal:03d}.bin",
        "length": (PROJECT_ROOT / source).stat().st_size,
        "schema_role": role,
        "phase_role": phase,
    }


def _bundle_manifest() -> dict[str, Any]:
    boundary = len(PREFIT_MEMBERS)
    return {
        "format": REFERENCE_BUNDLE_FORMAT,
        "complete": True,
        "prefit_members": [
            _member_record(i, source, role, "PREFIT")
            for i, (source, role) in enumerate(PREFIT_MEMBERS)
        ],
        "postfit_members": [
            _member_record(i, source, role, "POSTFIT")
            for i, (source, role) in enumerate(POSTFIT_MEMBERS, start=boundary)
        ],
    }


def _prefit_binding_receipt(
    *, gzip_members_opened: int, json_rows_parsed: int, canonical_rows_compared: int,
) -> dict[str, Any]:
    return {
        "status": "MATCH",
        "bundle_format": REFERENCE_BUNDLE_FORMAT,
        "member_count": len(ALL_MEMBERS),
        "prefit_member_count": len(PREFIT_MEMBERS),
        "postfit_member_count": len(POSTFIT_MEMBERS),
        "raw_members_compared": len(PREFIT_MEMBERS),
        "gzip_members_opened": gzip_members_opened,
        "json_rows_parsed": json_rows_parsed,
        "canonical_rows_compared": canonical_rows_compared,
        "decoder_rows_replayed": json_rows_parsed,
    }


def freeze_reference_bundle(destination: str | Path) -> Path:
    try:
        require_frozen_execution_environment()
    except ExecutionEnvironmentMismatch:
        return publish_technical_stop(
            "freeze-reference-bundle", actual_stage="EXECUTION_ENVIRONMENT"
        )
    try:
        admission = _admit_memory("freeze-reference-bundle")
    except ResourceAdmissionRefusal:
        return publish_resource_stop("freeze-reference-bundle")
    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"reference bundle already exists: {target}")
    staging: Path | None = None
    monitor: Any | None = None
    ledger: dict[str, Any] | None = None
    actual_stage = "ENTRY_SETUP"
    try:
        _persist_entry_admission("freeze-reference-bundle", admission)
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target.parent))
        monitor = ResourceMonitor(
            "freeze-reference-bundle", scratch=staging, durable=staging
        ).start()
        actual_stage = "BUNDLE_SOURCE_CAPTURE"
        try:
            if RUNNER_PATH.read_bytes() != RUNNER_START_BYTES:
                raise DataBindingMismatch("runner source changed after entry")
            manifest = _bundle_manifest()
            records = manifest["prefit_members"] + manifest["postfit_members"]
            captured: list[bytes] = []
            for record in records:
                source = PROJECT_ROOT / record["source_relative_path"]
                if _unsafe_source_path(source):
                    raise DataBindingMismatch("bundle source is absent, unsafe, or not a file")
                raw = source.read_bytes()
                if len(raw) != record["length"]:
                    raise DataBindingMismatch("bundle source length changed during capture")
                captured.append(raw)
        except DataBindingMismatch:
            raise
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise DataBindingMismatch("bundle source capture could not be established") from exc

        (staging / "members").mkdir()
        for record, raw in zip(records, captured):
            atomic_create_bytes(staging / record["bundle_relative_path"], raw)
        for record, captured_raw in zip(records, captured):
            source = PROJECT_ROOT / record["source_relative_path"]
            try:
                source_bytes = source.read_bytes()
            except OSError as exc:
                raise DataBindingMismatch("bundle source became unreadable during freeze") from exc
            bundled_bytes = (staging / record["bundle_relative_path"]).read_bytes()
            if source_bytes != captured_raw or bundled_bytes != captured_raw:
                raise DataBindingMismatch("source-byte mismatch during bundle freeze")
        if RUNNER_PATH.read_bytes() != RUNNER_START_BYTES:
            raise DataBindingMismatch("runner source changed after entry")
        actual_stage = "PREFIT_BINDING"
        gzip_opened, parsed, canonical = _validate_prefit_row_structure(
            tuple(captured[: len(PREFIT_MEMBERS)])
        )
        binding_receipt = _prefit_binding_receipt(
            gzip_members_opened=gzip_opened,
            json_rows_parsed=parsed,
            canonical_rows_compared=canonical,
        )
        actual_stage = "BUNDLE_PUBLICATION"
        manifest_payload = _plain_canonical_bytes(manifest)
        binding_payload = _plain_canonical_bytes(binding_receipt)
        admission_payload = _plain_canonical_bytes(admission)
        atomic_create_bytes(staging / "manifest.json", manifest_payload)
        atomic_create_bytes(
            staging / PREFIT_BINDING_RECEIPT_FILENAME, binding_payload
        )
        atomic_create_bytes(staging / RESOURCE_RECEIPT_FILENAME, admission_payload)
        for record, captured_raw in zip(records, captured):
            source = PROJECT_ROOT / record["source_relative_path"]
            frozen = staging / record["bundle_relative_path"]
            try:
                source_unsafe = _unsafe_source_path(source)
                source_bytes = source.read_bytes()
            except OSError as exc:
                raise DataBindingMismatch(
                    "bundle source became unreadable after training replay"
                ) from exc
            if source_unsafe or source_bytes != captured_raw:
                raise DataBindingMismatch("bundle member changed after training replay")
            if _unsafe_source_path(frozen) or frozen.read_bytes() != captured_raw:
                raise OSError("staged bundle member changed after training replay")
        try:
            runner_after_replay = RUNNER_PATH.read_bytes()
        except OSError as exc:
            raise DataBindingMismatch(
                "runner source became unreadable after training replay"
            ) from exc
        if runner_after_replay != RUNNER_START_BYTES:
            raise DataBindingMismatch("runner source changed after training replay")
        if (
            (staging / "manifest.json").read_bytes() != manifest_payload
            or (staging / PREFIT_BINDING_RECEIPT_FILENAME).read_bytes() != binding_payload
            or (staging / RESOURCE_RECEIPT_FILENAME).read_bytes() != admission_payload
        ):
            raise OSError("staged bundle control bytes changed before publication")
        actual_stage = "PREPUBLICATION_RESOURCE"
        ledger = monitor.finish()
        if ledger["passed"] is not True:
            raise ResourceAdmissionRefusal("freeze-reference-bundle resource ceiling exceeded")
        atomic_create_json(staging / RESOURCE_LEDGER_FILENAME, ledger)
        os.replace(staging, target)
        return target / "manifest.json"
    except ResourceAdmissionRefusal:
        return _publish_failed_entry(
            "freeze-reference-bundle", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=False,
            evaluation_entered=False, monitor=monitor, admission=admission,
            existing_ledger=ledger, private_path=staging,
        )
    except DataBindingMismatch as exc:
        return _publish_failed_entry(
            "freeze-reference-bundle", kind="binding", output_root=None,
            actual_stage=actual_stage, fit_entered=False,
            evaluation_entered=False, monitor=monitor, admission=admission,
            private_path=staging,
        )
    except (
        OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError,
        TypeError, KeyError, RuntimeError,
    ) as exc:
        return _publish_failed_entry(
            "freeze-reference-bundle", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=False,
            evaluation_entered=False, monitor=monitor, admission=admission,
            private_path=staging,
        )
    except BaseException:
        _settle_failure("freeze-reference-bundle", monitor, ledger)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        raise


def _validate_manifest_shape(value: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(value, dict) or set(value) != {"format", "complete", "prefit_members", "postfit_members"}:
        raise DataBindingMismatch("bundle manifest field inventory mismatch")
    if value["format"] != REFERENCE_BUNDLE_FORMAT or value["complete"] is not True:
        raise DataBindingMismatch("bundle manifest envelope mismatch")
    prefit, postfit = value["prefit_members"], value["postfit_members"]
    if not isinstance(prefit, list) or not isinstance(postfit, list):
        raise DataBindingMismatch("bundle phase member lists are malformed")
    expected = PREFIT_MEMBERS + POSTFIT_MEMBERS
    records = prefit + postfit
    if len(prefit) != len(PREFIT_MEMBERS) or len(postfit) != len(POSTFIT_MEMBERS) or len(records) != len(expected):
        raise DataBindingMismatch("bundle phase member count mismatch")
    keys = {
        "ordinal", "source_relative_path", "bundle_relative_path", "length",
        "schema_role", "phase_role",
    }
    for ordinal, (record, (source, role)) in enumerate(zip(records, expected)):
        if (
            not isinstance(record, dict) or set(record) != keys or record["ordinal"] != ordinal
            or record["source_relative_path"] != source
            or record["bundle_relative_path"] != f"members/{ordinal:03d}.bin"
            or type(record["length"]) is not int or record["length"] < 0
            or record["schema_role"] != role
            or record["phase_role"] != ("PREFIT" if ordinal < len(PREFIT_MEMBERS) else "POSTFIT")
        ):
            raise DataBindingMismatch("bundle ordered member schema mismatch")
    return prefit, postfit


def _validate_runtime_ledger(
    ledger: Any, *, entry: str, require_pass: bool | None,
) -> None:
    if (
        not isinstance(ledger, dict)
        or set(ledger) != {
            "format", "entry", "ceilings", "measurement_scope",
            "sample_interval_seconds", "publication_headroom", "observed", "passed",
        }
        or ledger.get("format") != "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1"
        or ledger.get("entry") != entry
        or ledger.get("ceilings") != RESOURCE_CEILINGS
        or ledger.get("measurement_scope") != RESOURCE_MEASUREMENT_SCOPE
        or ledger.get("sample_interval_seconds") != RESOURCE_SAMPLE_SECONDS
        or ledger.get("publication_headroom") != PUBLICATION_HEADROOM
        or type(ledger.get("passed")) is not bool
        or not isinstance(ledger.get("observed"), dict)
    ):
        raise ResourceAdmissionRefusal("stored resource ledger mismatch")
    observed = ledger["observed"]
    expected_observed = {
        "workers", "wall_seconds", "cpu_seconds", "peak_process_threads",
        "peak_rss_bytes", "scientific_child_processes", "scratch_high_water_bytes",
        "durable_high_water_bytes", "read_bytes", "write_bytes", "aggregate_io_bytes",
    }
    if set(observed) != expected_observed:
        raise ResourceAdmissionRefusal("stored resource observation field inventory mismatch")
    for name in ("wall_seconds", "cpu_seconds"):
        value = observed.get(name)
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0
        ):
            raise ResourceAdmissionRefusal("stored resource duration is malformed")
    for name in (
        "workers", "peak_process_threads", "peak_rss_bytes",
        "scientific_child_processes", "scratch_high_water_bytes", "durable_high_water_bytes",
        "read_bytes", "write_bytes", "aggregate_io_bytes",
    ):
        value = observed.get(name)
        if type(value) is not int or value < 0:
            raise ResourceAdmissionRefusal("stored resource observation is malformed")
    if observed["read_bytes"] + observed["write_bytes"] != observed["aggregate_io_bytes"]:
        raise ResourceAdmissionRefusal("stored aggregate I/O observation mismatch")
    if observed["workers"] != RESOURCE_CEILINGS["workers"]:
        raise ResourceAdmissionRefusal("stored worker count mismatch")
    recomputed = _resource_observation_passes(observed)
    if require_pass is True and not recomputed:
        raise ResourceAdmissionRefusal("stored resource observation exceeds its ceiling")
    if require_pass is False and recomputed:
        raise ResourceAdmissionRefusal("stored resource observation does not exceed a ceiling")
    if ledger["passed"] is not recomputed:
        raise ResourceAdmissionRefusal("stored resource disposition differs from frozen predicate")


def _validate_resource_values(admission: Any, ledger: Any, *, entry: str) -> None:
    if (
        not isinstance(admission, dict)
        or admission.get("entry") != entry
        or admission.get("passed") is not True
        or admission.get("physical_floor_pass") is not True
        or admission.get("effective_floor_pass") is not True
        or type(admission.get("available_physical_bytes")) is not int
        or type(admission.get("effective_available_bytes")) is not int
        or admission["available_physical_bytes"] < MINIMUM_MEMORY_BYTES
        or admission["effective_available_bytes"] < MINIMUM_MEMORY_BYTES
    ):
        raise ResourceAdmissionRefusal("stored memory admission mismatch")
    _validate_runtime_ledger(ledger, entry=entry, require_pass=True)


def _persist_failure_ledger(
    entry: str, monitor: Any, existing: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    ledger = dict(existing) if existing is not None else monitor.finish()
    _validate_runtime_ledger(ledger, entry=entry, require_pass=None)
    destination = (
        CONTROL_ROOT / "resource-receipts"
        / f"{entry}-stop-ledger-{uuid.uuid4().hex}.json"
    )
    atomic_create_json(destination, ledger)
    return ledger, destination.relative_to(PROJECT_ROOT).as_posix()


def _settle_failure(
    entry: str, monitor: Any | None, existing: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    if monitor is None:
        return None, None, False
    try:
        ledger, relative_path = _persist_failure_ledger(entry, monitor, existing)
    except (OSError, RuntimeError, ResourceAdmissionRefusal, TypeError, ValueError):
        return None, None, True
    return ledger, relative_path, False


_ROW_KEYS = {
    "index", "seed_slot", "context_id", "link", "reliability", "total_cost",
    "regime", "actual_marks", "displayed_regime", "displayed_marks",
    "displayed_short_count", "root_action", "period", "primitive_ledger",
    "tail_return", "immediate_return", "unshaped_return",
}
_LEDGER_KEYS = {
    "tail_service", "tail_time", "tail_energy", "probe_service", "probe_time",
    "probe_energy", "executed_probe_count", "executed_probe_mark_count",
    "executed_probe_time_units", "executed_tail_commit_count",
    "executed_tail_period_units",
}
_K_TRAIN = (1, 3, 5, 7, 9)
_PREFIT_CONTEXTS = {
    f"{link}-p{p.replace('/', '_')}-c{cost.replace('/', '_')}": {
        "link": link,
        "reliability": p,
        "total_cost": cost,
    }
    for link in ("LINKED", "SEVERED")
    for p in ("13/20", "17/20")
    for cost in ("9/100", "7/50")
}


def _training_rng_constants(contract_source: bytes) -> tuple[str, str]:
    try:
        tree = ast.parse(contract_source, filename="bound-contract.py")
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise DataBindingMismatch("bound contract source cannot be parsed") from exc
    found: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id in {"CONTRACT_ID", "RNG_VERSION_SPEC"}
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) is str
        ):
            found[target.id] = node.value.value
    if set(found) != {"CONTRACT_ID", "RNG_VERSION_SPEC"}:
        raise DataBindingMismatch("training RNG constants are absent from the bound contract")
    return found["CONTRACT_ID"], found["RNG_VERSION_SPEC"]


def _compile_prefit_runtime(prefit_bytes: tuple[bytes, ...]) -> Mapping[str, Any]:
    if len(prefit_bytes) != len(PREFIT_MEMBERS):
        raise DataBindingMismatch("pre-fit byte capture count mismatch")
    package_name = f"_ucope_bound_prefit_{uuid.uuid4().hex}"
    package = types.ModuleType(package_name)
    package.__path__ = []
    contract = types.ModuleType(f"{package_name}.contract")
    contract.CONTRACT_ID, contract.RNG_VERSION_SPEC = _training_rng_constants(
        prefit_bytes[CONTRACT_ORDINAL]
    )
    rng = types.ModuleType(f"{package_name}.rng")
    rng.__file__ = f"{package_name}/rng.py"
    rng.__package__ = package_name
    replay = types.ModuleType(f"{package_name}.structural_replay")
    replay.__file__ = f"{package_name}/structural_replay.py"
    replay.__package__ = package_name
    sys.modules[package_name] = package
    sys.modules[contract.__name__] = contract
    sys.modules[rng.__name__] = rng
    sys.modules[replay.__name__] = replay
    try:
        exec(compile(prefit_bytes[RNG_ORDINAL], rng.__file__, "exec"), rng.__dict__)
        exec(
            compile(
                prefit_bytes[STRUCTURAL_REPLAY_ORDINAL], replay.__file__, "exec"
            ),
            replay.__dict__,
        )
        if not callable(getattr(replay, "expected_episode_row", None)):
            raise DataBindingMismatch("training replay surface is absent")
        return {"rng": rng, "replay": replay}
    except DataBindingMismatch:
        raise
    except (ImportError, SyntaxError, UnicodeDecodeError, ValueError, TypeError) as exc:
        raise DataBindingMismatch("training replay runtime could not be loaded") from exc
    finally:
        for name in (replay.__name__, rng.__name__, contract.__name__, package_name):
            sys.modules.pop(name, None)


def _validate_prefit_row_structure(prefit_bytes: tuple[bytes, ...]) -> tuple[int, int, int]:
    if len(prefit_bytes) != len(PREFIT_MEMBERS):
        raise DataBindingMismatch("pre-fit byte capture count mismatch")
    try:
        runtime = _compile_prefit_runtime(prefit_bytes)
        rng = runtime["rng"]
        replay = runtime["replay"]
        support = json.loads(prefit_bytes[82], parse_constant=_reject_nonfinite_json)
        materialized = support["materialized_files"]
        if not isinstance(materialized, dict) or len(materialized) != 80:
            raise DataBindingMismatch("retained support member map mismatch")
        by_filename: dict[str, tuple[str, Mapping[str, Any]]] = {}
        for logical_key, record in materialized.items():
            if (
                not isinstance(logical_key, str)
                or not isinstance(record, Mapping)
                or type(record.get("filename")) is not str
                or type(record.get("rows")) is not int
                or record["rows"] != 20_480
                or record["filename"] in by_filename
            ):
                raise DataBindingMismatch("retained support member record mismatch")
            by_filename[record["filename"]] = (logical_key, record)

        parsed = canonical = 0
        assignment_cache: dict[str, tuple[list[str | None], list[str | None]]] = {}
        for ordinal, raw in enumerate(prefit_bytes[:80]):
            filename = f"cell-{ordinal // 8:02d}-{ordinal % 8:02d}.jsonl.gz"
            mapped = by_filename.get(filename)
            if mapped is None or "|" not in mapped[0]:
                raise DataBindingMismatch("retained support/tape mapping mismatch")
            seed_slot, context_id = mapped[0].split("|", 1)
            if seed_slot != f"cpa-r01-fresh-slot-{ordinal // 8:02d}":
                raise DataBindingMismatch("retained tape seed order mismatch")
            context = _PREFIT_CONTEXTS.get(context_id)
            if context is None:
                raise DataBindingMismatch("retained tape context is outside the fixed population")
            if seed_slot not in assignment_cache:
                regime_values: list[str | None] = [None] * 20_480
                display_values: list[str | None] = [None] * 20_480
                for slot in range(10):
                    selected = list(range(slot, 20_480, 10))
                    assignments = rng.balanced_binary_assignments(
                        len(selected), "regime-rank", seed_slot, slot
                    )
                    for index, is_short in zip(selected, assignments):
                        regime_values[index] = "SHORT" if is_short else "LONG"
                    for actual in ("SHORT", "LONG"):
                        subgroup = [
                            index for index in selected
                            if regime_values[index] == actual
                        ]
                        displays = rng.balanced_binary_assignments(
                            len(subgroup), "display-regime-rank", seed_slot, slot, actual
                        )
                        for index, is_short in zip(subgroup, displays):
                            display_values[index] = "SHORT" if is_short else "LONG"
                assignment_cache[seed_slot] = (regime_values, display_values)
            regime_by_index, severed_display_by_index = assignment_cache[seed_slot]
            display_by_index = (
                [None] * 20_480
                if context["link"] == "LINKED"
                else severed_display_by_index
            )
            row_count = 0
            with gzip.GzipFile(fileobj=BytesIO(raw), mode="rb") as stream:
                for raw_line in stream:
                    try:
                        row = json.loads(raw_line, parse_constant=_reject_nonfinite_json)
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise DataBindingMismatch("retained training row is not JSON") from exc
                    if _plain_canonical_bytes(row) + b"\n" != raw_line:
                        raise DataBindingMismatch("retained training row is not canonical")
                    if not isinstance(row, dict) or set(row) != _ROW_KEYS:
                        raise DataBindingMismatch("retained training row field inventory mismatch")
                    if (
                        type(row["index"]) is not int
                        or row["index"] != row_count
                        or row["seed_slot"] != seed_slot
                        or row["context_id"] != context_id
                        or row["link"] not in ("LINKED", "SEVERED")
                        or row["reliability"] not in ("13/20", "17/20")
                        or row["total_cost"] not in ("9/100", "7/50")
                        or type(row["displayed_short_count"]) is not int
                        or not 0 <= row["displayed_short_count"] <= 6
                    ):
                        raise DataBindingMismatch("retained training row navigation mismatch")
                    expected_context = (
                        f"{row['link']}-p{row['reliability'].replace('/', '_')}"
                        f"-c{row['total_cost'].replace('/', '_')}"
                    )
                    if expected_context != context_id:
                        raise DataBindingMismatch("retained training context field mismatch")
                    slot = row_count % 10
                    expected_action = "PROBE" if slot < 5 else "IMMEDIATE"
                    expected_period = _K_TRAIN[slot if slot < 5 else slot - 5]
                    if row["root_action"] != expected_action or row["period"] != expected_period:
                        raise DataBindingMismatch("retained training behavior stratum mismatch")
                    if (
                        row["regime"] not in ("SHORT", "LONG")
                        or row["displayed_regime"] not in ("SHORT", "LONG")
                        or type(row["actual_marks"]) is not list
                        or type(row["displayed_marks"]) is not list
                        or len(row["actual_marks"]) != 6
                        or len(row["displayed_marks"]) != 6
                        or any(mark not in ("SHORT", "LONG") for mark in row["actual_marks"])
                        or any(mark not in ("SHORT", "LONG") for mark in row["displayed_marks"])
                        or row["displayed_short_count"] != row["displayed_marks"].count("SHORT")
                    ):
                        raise DataBindingMismatch("retained training mark structure mismatch")
                    ledger = row["primitive_ledger"]
                    if not isinstance(ledger, dict) or set(ledger) != _LEDGER_KEYS:
                        raise DataBindingMismatch("retained primitive ledger structure mismatch")
                    scalar_names = (
                        "tail_service", "tail_time", "tail_energy", "probe_service",
                        "probe_time", "probe_energy",
                    )
                    count_names = tuple(_LEDGER_KEYS - set(scalar_names))
                    if (
                        any(
                            isinstance(ledger[name], bool)
                            or not isinstance(ledger[name], (int, float))
                            for name in scalar_names
                        )
                        or any(type(ledger[name]) is not int for name in count_names)
                        or any(
                            isinstance(row[name], bool)
                            or not isinstance(row[name], (int, float))
                            for name in ("tail_return", "immediate_return", "unshaped_return")
                        )
                    ):
                        raise DataBindingMismatch("retained training numeric field mismatch")
                    expected = replay.expected_episode_row(
                        seed_slot=seed_slot,
                        context=context,
                        index=row_count,
                        root_action=expected_action,
                        period=expected_period,
                        regime=regime_by_index[row_count],
                        display_regime=display_by_index[row_count],
                        rng=rng,
                    )
                    if _plain_canonical_bytes(expected) + b"\n" != raw_line:
                        raise DataBindingMismatch(
                            "retained training row differs from deterministic replay"
                        )
                    row_count += 1
                    parsed += 1
                    canonical += 1
            if row_count != 20_480:
                raise DataBindingMismatch("retained training row population mismatch")
        return 80, parsed, canonical
    except DataBindingMismatch:
        raise
    except (OSError, EOFError, gzip.BadGzipFile, zlib.error, ValueError, TypeError, KeyError) as exc:
        raise DataBindingMismatch("retained training row structure could not be established") from exc


def _final_prefit_sweep(
    *,
    bundle_path: Path,
    manifest_bytes: bytes,
    frozen_binding_bytes: bytes,
    admission_bytes: bytes,
    ledger_bytes: bytes,
    records: list[dict[str, Any]],
    snapshots: tuple[bytes, ...],
) -> None:
    try:
        if (bundle_path / "manifest.json").read_bytes() != manifest_bytes:
            raise DataBindingMismatch("bundle manifest changed during training replay")
        if (
            bundle_path / PREFIT_BINDING_RECEIPT_FILENAME
        ).read_bytes() != frozen_binding_bytes:
            raise DataBindingMismatch("pre-fit binding receipt changed during training replay")
        if (bundle_path / RESOURCE_RECEIPT_FILENAME).read_bytes() != admission_bytes:
            raise DataBindingMismatch("bundle admission receipt changed during training replay")
        if (bundle_path / RESOURCE_LEDGER_FILENAME).read_bytes() != ledger_bytes:
            raise DataBindingMismatch("bundle resource ledger changed during training replay")
        for record, captured in zip(records, snapshots):
            source = PROJECT_ROOT / record["source_relative_path"]
            frozen = bundle_path / record["bundle_relative_path"]
            if (
                _unsafe_source_path(source)
                or _unsafe_source_path(frozen)
                or source.read_bytes() != captured
                or frozen.read_bytes() != captured
            ):
                raise DataBindingMismatch("pre-fit member changed during training replay")
        if RUNNER_PATH.read_bytes() != RUNNER_START_BYTES:
            raise DataBindingMismatch("runner source changed during training replay")
    except DataBindingMismatch:
        raise
    except OSError as exc:
        raise DataBindingMismatch("final pre-fit direct sweep could not be established") from exc


def capture_prefit_binding(bundle: str | Path, *, validate_rows: bool = True) -> BindingCapture:
    try:
        bundle_path = Path(bundle)
        manifest_bytes = (bundle_path / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest_bytes != _plain_canonical_bytes(manifest):
            raise DataBindingMismatch("bundle manifest is not canonical")
        prefit_records, _ = _validate_manifest_shape(manifest)
        frozen_binding_bytes = (bundle_path / PREFIT_BINDING_RECEIPT_FILENAME).read_bytes()
        frozen_binding = json.loads(frozen_binding_bytes)
        if frozen_binding_bytes != _plain_canonical_bytes(frozen_binding):
            raise DataBindingMismatch("frozen pre-fit binding receipt is not canonical")
        admission_bytes = (bundle_path / RESOURCE_RECEIPT_FILENAME).read_bytes()
        ledger_bytes = (bundle_path / RESOURCE_LEDGER_FILENAME).read_bytes()
        admission = json.loads(admission_bytes)
        ledger = json.loads(ledger_bytes)
        if admission_bytes != _plain_canonical_bytes(admission) or ledger_bytes != _plain_canonical_bytes(ledger):
            raise DataBindingMismatch("bundle resource records are not canonical")
        _validate_resource_values(admission, ledger, entry="freeze-reference-bundle")
        snapshots: list[bytes] = []
        comparisons: list[tuple[int, bytes, bytes]] = []
        for record in prefit_records:
            source = PROJECT_ROOT / record["source_relative_path"]
            frozen = bundle_path / record["bundle_relative_path"]
            if _unsafe_source_path(source) or _unsafe_source_path(frozen):
                raise DataBindingMismatch("pre-fit member absent, unsafe, or not a file")
            source_bytes, frozen_bytes = source.read_bytes(), frozen.read_bytes()
            comparisons.append((record["ordinal"], source_bytes, frozen_bytes))
            snapshots.append(frozen_bytes)
        drift = [ordinal for ordinal, source_bytes, frozen_bytes in comparisons if source_bytes != frozen_bytes]
        if drift:
            raise DataBindingMismatch(f"pre-fit source-byte mismatch at member ordinals {drift}")
        for record, raw in zip(prefit_records, snapshots):
            if record["length"] != len(raw):
                raise DataBindingMismatch("pre-fit member length mismatch")
        if snapshots[RUNNER_ORDINAL] != RUNNER_START_BYTES or RUNNER_PATH.read_bytes() != RUNNER_START_BYTES:
            raise DataBindingMismatch("runner start/source/bundle byte mismatch")
        gzip_opened = parsed = canonical = 0
        if validate_rows:
            gzip_opened, parsed, canonical = _validate_prefit_row_structure(tuple(snapshots))
            receipt = _prefit_binding_receipt(
                gzip_members_opened=gzip_opened,
                json_rows_parsed=parsed,
                canonical_rows_compared=canonical,
            )
            if frozen_binding != receipt:
                raise DataBindingMismatch("frozen pre-fit binding receipt mismatch")
            _final_prefit_sweep(
                bundle_path=bundle_path,
                manifest_bytes=manifest_bytes,
                frozen_binding_bytes=frozen_binding_bytes,
                admission_bytes=admission_bytes,
                ledger_bytes=ledger_bytes,
                records=prefit_records,
                snapshots=tuple(snapshots),
            )
        else:
            receipt = _prefit_binding_receipt(
                gzip_members_opened=0,
                json_rows_parsed=0,
                canonical_rows_compared=0,
            )
            receipt["decoder_rows_replayed"] = 0
        return BindingCapture(
            receipt,
            manifest_bytes=manifest_bytes,
            frozen_binding_bytes=frozen_binding_bytes,
            bundle_admission_bytes=admission_bytes,
            bundle_ledger_bytes=ledger_bytes,
            prefit_bytes=tuple(snapshots),
        )
    except DataBindingMismatch:
        raise
    except (
        OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError,
        ResourceAdmissionRefusal,
    ) as exc:
        raise DataBindingMismatch("pre-fit data binding could not be established") from exc


def verify_reference_binding(bundle: str | Path, replay_rows: bool = False) -> dict[str, Any]:
    if replay_rows:
        raise DataBindingMismatch("row replay is post-seal only")
    return dict(capture_prefit_binding(bundle, validate_rows=False))


def verify_data_binding() -> BindingCapture:
    return capture_prefit_binding(FIXED_BUNDLE_ROOT)


def check_binding() -> BindingCapture | Path:
    try:
        require_frozen_execution_environment()
    except ExecutionEnvironmentMismatch:
        return publish_technical_stop(
            "check-binding", actual_stage="EXECUTION_ENVIRONMENT"
        )
    try:
        admission = _admit_memory("check-binding")
    except ResourceAdmissionRefusal:
        return publish_resource_stop("check-binding")
    monitor: Any | None = None
    ledger: dict[str, Any] | None = None
    actual_stage = "ENTRY_SETUP"
    try:
        _persist_entry_admission("check-binding", admission)
        monitor = ResourceMonitor("check-binding").start()
        actual_stage = "PREFIT_BINDING"
        capture = verify_data_binding()
        ledger = monitor.finish()
        if ledger["passed"] is not True:
            return _publish_failed_entry(
                "check-binding", kind="technical", output_root=None,
                actual_stage=actual_stage, fit_entered=False,
                evaluation_entered=False, monitor=monitor, admission=admission,
                existing_ledger=ledger,
            )
        atomic_create_json(
            CONTROL_ROOT / "resource-receipts" / f"check-binding-ledger-{uuid.uuid4().hex}.json",
            ledger,
        )
        return capture
    except DataBindingMismatch as exc:
        return _publish_failed_entry(
            "check-binding", kind="binding", output_root=None,
            actual_stage=actual_stage, fit_entered=False,
            evaluation_entered=False, monitor=monitor, admission=admission,
        )
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        return _publish_failed_entry(
            "check-binding", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=False,
            evaluation_entered=False, monitor=monitor, admission=admission,
            existing_ledger=ledger,
        )
    except BaseException:
        _settle_failure("check-binding", monitor, ledger)
        raise


def _new_assessment_destination() -> Path:
    while True:
        destination = ASSESSMENT_ROOT / f"assess-run-{uuid.uuid4().hex}"
        if not destination.exists():
            return destination


def _publish_assessment_receipt(destination: Path, body: Mapping[str, Any]) -> Path:
    if destination.exists():
        raise FileExistsError(f"assessment root already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging: Path | None = None
    try:
        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.staging-", dir=destination.parent
            )
        )
        receipt = atomic_create_json(staging / ASSESSMENT_RECEIPT_FILENAME, body)
        if set(staging.iterdir()) != {receipt}:
            raise RuntimeError("assessment publication inventory mismatch")
        os.rename(staging, destination)
        staging = None
        return destination / ASSESSMENT_RECEIPT_FILENAME
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)


def _persist_assessment_ledger(ledger: Mapping[str, Any]) -> str:
    _validate_runtime_ledger(ledger, entry="assess-run", require_pass=True)
    destination = (
        CONTROL_ROOT / "resource-receipts"
        / f"assess-run-ledger-{uuid.uuid4().hex}.json"
    )
    atomic_create_json(destination, dict(ledger))
    return destination.relative_to(PROJECT_ROOT).as_posix()


def _assessment_final_prefit_sweep(capture: BindingCapture) -> None:
    try:
        manifest = json.loads(
            capture.manifest_bytes, parse_constant=_reject_nonfinite_json
        )
        prefit_records, _postfit_records = _validate_manifest_shape(manifest)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DataBindingMismatch("assessment manifest became invalid") from exc
    _final_prefit_sweep(
        bundle_path=FIXED_BUNDLE_ROOT,
        manifest_bytes=capture.manifest_bytes,
        frozen_binding_bytes=capture.frozen_binding_bytes,
        admission_bytes=capture.bundle_admission_bytes,
        ledger_bytes=capture.bundle_ledger_bytes,
        records=prefit_records,
        snapshots=capture.prefit_bytes,
    )


def _compare_independent_in_memory_fits(capture: BindingCapture) -> bool:
    """Compute both complete exact documents in isolated prefit-only modules."""
    first_document: Any | None = None
    second_document: Any | None = None
    first_module: Any | None = None
    second_module: Any | None = None
    try:
        source = capture.prefit_bytes[STRUCTURAL_ORDINAL]
        first_module = _compile_structural(source)
        first_document = first_module._assessment_fit_document(
            capture, capture.tape_bytes
        )
        second_module = _compile_structural(source)
        second_document = second_module._assessment_fit_document(
            capture, capture.tape_bytes
        )
        return bool(first_document == second_document)
    finally:
        first_document = None
        second_document = None
        first_module = None
        second_module = None


def _assessment_work(capture: BindingCapture) -> dict[str, int]:
    if (
        not isinstance(capture, BindingCapture)
        or capture.get("prefit_member_count") != 90
        or capture.get("raw_members_compared") != 90
        or capture.get("decoder_rows_replayed") != 1_638_400
        or capture.get("canonical_rows_compared") != 1_638_400
    ):
        raise DataBindingMismatch("assessment did not complete the fixed prefit work")
    return _prefit_assessment_work()


def _prefit_assessment_work() -> dict[str, int]:
    return {
        "prefit_members_compared": 90,
        "canonical_rows_replayed": 1_638_400,
        "exact_in_memory_solve_passes": 0,
        "independent_prefit_modules": 0,
        "exact_row_decodes": 0,
        "exact_root_normal_accumulations": 0,
        "postfit_members_opened": 0,
        "serialized_solve_documents": 0,
        "scientific_outputs_created": 0,
    }


def _empty_assessment_work() -> dict[str, int]:
    return {
        "prefit_members_compared": 0,
        "canonical_rows_replayed": 0,
        "exact_in_memory_solve_passes": 0,
        "independent_prefit_modules": 0,
        "exact_row_decodes": 0,
        "exact_root_normal_accumulations": 0,
        "postfit_members_opened": 0,
        "serialized_solve_documents": 0,
        "scientific_outputs_created": 0,
    }


def _publish_assessment_terminal(
    destination: Path,
    *,
    disposition: str,
    actual_stage: str,
    admission: Mapping[str, Any] | None = None,
    ledger_relative_path: str | None = None,
    work: Mapping[str, int] | None = None,
    exact_refit_equal: bool | None = None,
) -> Path:
    if disposition not in {
        "RESOURCE_REFUSAL_NO_SCIENCE_STATE",
        "INCOMPLETE_RESOURCE_CEILING",
        "INCOMPLETE_TECHNICAL_ASSESSMENT",
    }:
        raise ValueError("unknown assessment terminal disposition")
    return _publish_assessment_receipt(
        destination,
        {
            "format": ASSESSMENT_FORMAT,
            "entry": "assess-run",
            "complete": False,
            "performance_disposition": "REPAIR_REQUIRED",
            "disposition": disposition,
            "actual_stage": actual_stage,
            "scope": "RESOURCE_AND_TECHNICAL_ONLY",
            "exact_refit_equal": exact_refit_equal,
            "work": dict(work or _empty_assessment_work()),
            "resource_admission_relative_path": _admission_relative_path(admission),
            "resource_ledger_relative_path": ledger_relative_path,
        },
    )


def assess_run() -> Path:
    """Run the fixed outcome-blind resource and exact-refit assessment."""
    destination = _new_assessment_destination()
    try:
        require_frozen_execution_environment()
    except ExecutionEnvironmentMismatch:
        return _publish_assessment_terminal(
            destination,
            disposition="INCOMPLETE_TECHNICAL_ASSESSMENT",
            actual_stage="EXECUTION_ENVIRONMENT",
        )
    try:
        admission = _admit_memory("assess-run")
    except ResourceAdmissionRefusal:
        return _publish_assessment_terminal(
            destination,
            disposition="RESOURCE_REFUSAL_NO_SCIENCE_STATE",
            actual_stage="MEMORY_ADMISSION",
        )
    monitor: Any | None = None
    ledger: dict[str, Any] | None = None
    capture: BindingCapture | None = None
    work: dict[str, int] = _empty_assessment_work()
    exact_refit_equal: bool | None = None
    actual_stage = "ENTRY_SETUP"
    try:
        _persist_entry_admission("assess-run", admission)
        monitor = ResourceMonitor("assess-run")
        monitor.start()
        actual_stage = "PREFIT_BINDING"
        capture = verify_data_binding()
        work = _assessment_work(capture)
        actual_stage = "EXACT_REFIT"
        exact_refit_equal = _compare_independent_in_memory_fits(capture)
        work["exact_in_memory_solve_passes"] = 2
        work["independent_prefit_modules"] = 2
        work["exact_row_decodes"] = 9_830_400
        work["exact_root_normal_accumulations"] = 3_276_800
        if not exact_refit_equal:
            raise RuntimeError("independent exact in-memory refit mismatch")
        actual_stage = "FINAL_BINDING"
        _assessment_final_prefit_sweep(capture)
        actual_stage = "PREPUBLICATION_RESOURCE"
        ledger = monitor.finish()
        _validate_resource_values(admission, ledger, entry="assess-run")
        ledger_relative_path = _persist_assessment_ledger(ledger)
        return _publish_assessment_receipt(
            destination,
            {
                "format": ASSESSMENT_FORMAT,
                "entry": "assess-run",
                "complete": True,
                "performance_disposition": "PERFORMANCE_READY",
                "scope": "RESOURCE_AND_TECHNICAL_ONLY",
                "exact_refit_equal": True,
                "work": work,
                "resource_admission_relative_path": _admission_relative_path(admission),
                "resource_ledger_relative_path": ledger_relative_path,
            },
        )
    except Exception:
        settled, ledger_relative_path, settlement_failed = _settle_failure(
            "assess-run", monitor, ledger
        )
        if settled is not None and settled.get("passed") is False:
            disposition = "INCOMPLETE_RESOURCE_CEILING"
        else:
            disposition = "INCOMPLETE_TECHNICAL_ASSESSMENT"
        if settlement_failed:
            ledger_relative_path = None
            disposition = "INCOMPLETE_TECHNICAL_ASSESSMENT"
        return _publish_assessment_terminal(
            destination,
            disposition=disposition,
            actual_stage=actual_stage,
            admission=admission,
            ledger_relative_path=ledger_relative_path,
            work=work,
            exact_refit_equal=exact_refit_equal,
        )
    except BaseException:
        _settle_failure("assess-run", monitor, ledger)
        raise
    finally:
        capture = None


def _is_lower_hex(value: str, length: int = 32) -> bool:
    return len(value) == length and all(character in "0123456789abcdef" for character in value)


def _safe_directory(path: Path) -> bool:
    if path.is_symlink() or not path.is_dir():
        return False
    if os.name == "nt":
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        if attributes & 0x400:
            return False
    return True


def _assessment_resource_path(relative: Any, *, prefix: str) -> Path:
    if not isinstance(relative, str):
        raise AssessmentQualificationError("assessment resource path is malformed")
    candidate_relative = Path(relative)
    if (
        candidate_relative.is_absolute()
        or ".." in candidate_relative.parts
        or candidate_relative.as_posix() != relative
    ):
        raise AssessmentQualificationError("assessment resource path is malformed")
    resource_root = CONTROL_ROOT / "resource-receipts"
    try:
        expected_parent = resource_root.relative_to(PROJECT_ROOT).as_posix()
    except ValueError as exc:
        raise AssessmentQualificationError("assessment resource root escaped project") from exc
    if candidate_relative.parent.as_posix() != expected_parent:
        raise AssessmentQualificationError("assessment resource path escaped its root")
    name = candidate_relative.name
    if not name.startswith(prefix) or not name.endswith(".json"):
        raise AssessmentQualificationError("assessment resource filename is malformed")
    identifier = name[len(prefix):-5]
    if not _is_lower_hex(identifier):
        raise AssessmentQualificationError("assessment resource filename is malformed")
    path = PROJECT_ROOT / candidate_relative
    if _unsafe_source_path(path):
        raise AssessmentQualificationError(
            "assessment admission or ledger is absent, unsafe, or orphaned"
        )
    return path


def _load_json_object(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, parse_constant=_reject_nonfinite_json)
    except (UnicodeDecodeError, json.JSONDecodeError, DataBindingMismatch) as exc:
        raise AssessmentQualificationError(f"assessment {label} JSON is malformed") from exc
    if not isinstance(value, dict):
        raise AssessmentQualificationError(f"assessment {label} must be one object")
    return value


def _resource_admission_canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _validate_assessment_admission(raw: bytes) -> dict[str, Any]:
    value = _load_json_object(raw, label="admission")
    expected_keys = {
        "schema_version", "captured_at", "assessed_at", "measurement_source",
        "minimum_available_bytes", "available_physical_bytes",
        "cgroup_memory_max_bytes", "cgroup_memory_current_bytes",
        "cgroup_headroom_bytes", "effective_available_bytes",
        "physical_floor_pass", "effective_floor_pass", "passed",
        "failure_reasons",
    }
    if set(value) != expected_keys:
        raise AssessmentQualificationError("assessment admission field inventory mismatch")
    if raw != _resource_admission_canonical_bytes(value):
        raise AssessmentQualificationError("assessment admission bytes are not canonical")
    available = value["available_physical_bytes"]
    effective = value["effective_available_bytes"]
    if (
        value["schema_version"] != 1
        or not isinstance(value["captured_at"], str)
        or not value["captured_at"]
        or not isinstance(value["assessed_at"], str)
        or not value["assessed_at"]
        or not isinstance(value["measurement_source"], str)
        or not value["measurement_source"]
        or value["minimum_available_bytes"] != MINIMUM_MEMORY_BYTES
        or type(available) is not int
        or type(effective) is not int
        or available < MINIMUM_MEMORY_BYTES
        or effective < MINIMUM_MEMORY_BYTES
        or value["physical_floor_pass"] is not True
        or value["effective_floor_pass"] is not True
        or value["passed"] is not True
        or value["failure_reasons"] != []
    ):
        raise AssessmentQualificationError("assessment admission did not pass exactly")
    maximum = value["cgroup_memory_max_bytes"]
    current = value["cgroup_memory_current_bytes"]
    headroom = value["cgroup_headroom_bytes"]
    if maximum is None:
        if current is not None or headroom is not None or effective != available:
            raise AssessmentQualificationError("assessment admission cgroup relation mismatch")
    elif (
        type(maximum) is not int
        or type(current) is not int
        or type(headroom) is not int
        or min(maximum, current, headroom) < 0
        or headroom != max(0, maximum - current)
        or effective != min(available, headroom)
    ):
        raise AssessmentQualificationError("assessment admission cgroup relation mismatch")
    return value


def _complete_assessment_work() -> dict[str, int]:
    return {
        "prefit_members_compared": 90,
        "canonical_rows_replayed": 1_638_400,
        "exact_in_memory_solve_passes": 2,
        "independent_prefit_modules": 2,
        "exact_row_decodes": 9_830_400,
        "exact_root_normal_accumulations": 3_276_800,
        "postfit_members_opened": 0,
        "serialized_solve_documents": 0,
        "scientific_outputs_created": 0,
    }


def _assessment_receipt_at(root: Path) -> tuple[Path, dict[str, Any]]:
    prefix = "assess-run-"
    if (
        not _safe_directory(root)
        or not root.name.startswith(prefix)
        or not _is_lower_hex(root.name[len(prefix):])
    ):
        raise AssessmentQualificationError("performance assessment inventory is malformed")
    receipt_path = root / ASSESSMENT_RECEIPT_FILENAME
    if set(root.iterdir()) != {receipt_path} or _unsafe_source_path(receipt_path):
        raise AssessmentQualificationError("performance assessment receipt is orphaned")
    raw = receipt_path.read_bytes()
    receipt = _load_json_object(raw, label="receipt")
    if raw != _plain_canonical_bytes(receipt):
        raise AssessmentQualificationError("assessment receipt bytes are not canonical")
    return receipt_path, receipt


def _validate_failed_assessment(receipt: Mapping[str, Any]) -> None:
    expected_keys = {
        "format", "entry", "complete", "performance_disposition", "disposition",
        "actual_stage", "scope", "exact_refit_equal", "work",
        "resource_admission_relative_path", "resource_ledger_relative_path",
    }
    if set(receipt) != expected_keys:
        raise AssessmentQualificationError("failed assessment field inventory mismatch")
    disposition = receipt["disposition"]
    stage = receipt["actual_stage"]
    if (
        receipt["format"] != ASSESSMENT_FORMAT
        or receipt["entry"] != "assess-run"
        or receipt["complete"] is not False
        or receipt["performance_disposition"] != "REPAIR_REQUIRED"
        or disposition not in {
            "RESOURCE_REFUSAL_NO_SCIENCE_STATE",
            "INCOMPLETE_RESOURCE_CEILING",
            "INCOMPLETE_TECHNICAL_ASSESSMENT",
        }
        or stage not in {
            "EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP",
            "PREFIT_BINDING", "EXACT_REFIT", "FINAL_BINDING",
            "PREPUBLICATION_RESOURCE",
        }
        or receipt["scope"] != "RESOURCE_AND_TECHNICAL_ONLY"
        or (
            receipt["exact_refit_equal"] is not None
            and type(receipt["exact_refit_equal"]) is not bool
        )
    ):
        raise AssessmentQualificationError("failed assessment state mismatch")
    work = receipt["work"]
    complete_work = _complete_assessment_work()
    if not isinstance(work, dict) or set(work) != set(complete_work):
        raise AssessmentQualificationError("failed assessment work inventory mismatch")
    if work not in (
        _empty_assessment_work(), _prefit_assessment_work(), complete_work
    ):
        raise AssessmentQualificationError("failed assessment work value mismatch")
    if (
        (stage in {"EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION", "ENTRY_SETUP"}
         and work != _empty_assessment_work())
        or (
            stage == "PREFIT_BINDING"
            and work not in (_empty_assessment_work(), _prefit_assessment_work())
        )
        or (
            stage == "EXACT_REFIT"
            and work not in (_prefit_assessment_work(), complete_work)
        )
        or (
            stage in {"FINAL_BINDING", "PREPUBLICATION_RESOURCE"}
            and work != complete_work
        )
    ):
        raise AssessmentQualificationError("failed assessment stage/work mismatch")
    if (
        (work != complete_work and receipt["exact_refit_equal"] is not None)
        or (
            stage in {"FINAL_BINDING", "PREPUBLICATION_RESOURCE"}
            and receipt["exact_refit_equal"] is not True
        )
    ):
        raise AssessmentQualificationError("failed assessment refit state mismatch")
    admission_relative = receipt["resource_admission_relative_path"]
    ledger_relative = receipt["resource_ledger_relative_path"]
    admission: dict[str, Any] | None = None
    ledger: dict[str, Any] | None = None
    if admission_relative is not None:
        admission_path = _assessment_resource_path(
            admission_relative, prefix="assess-run-"
        )
        admission = _validate_assessment_admission(admission_path.read_bytes())
    if ledger_relative is not None:
        ledger_path = _assessment_resource_path(
            ledger_relative, prefix="assess-run-stop-ledger-"
        )
        raw_ledger = ledger_path.read_bytes()
        ledger = _load_json_object(raw_ledger, label="ledger")
        if raw_ledger != _plain_canonical_bytes(ledger):
            raise AssessmentQualificationError("failed assessment ledger is not canonical")
        try:
            _validate_runtime_ledger(ledger, entry="assess-run", require_pass=None)
        except ResourceAdmissionRefusal as exc:
            raise AssessmentQualificationError("failed assessment resource mismatch") from exc
    if (
        (admission is None and ledger is not None)
        or (
            stage not in {"EXECUTION_ENVIRONMENT", "MEMORY_ADMISSION"}
            and admission is None
        )
        or (
            disposition == "RESOURCE_REFUSAL_NO_SCIENCE_STATE"
            and (
                stage != "MEMORY_ADMISSION" or admission is not None or ledger is not None
            )
        )
        or (
            disposition == "INCOMPLETE_RESOURCE_CEILING"
            and (admission is None or ledger is None or ledger["passed"] is not False)
        )
        or (
            disposition == "INCOMPLETE_TECHNICAL_ASSESSMENT"
            and ledger is not None and ledger["passed"] is not True
        )
        or (stage == "EXECUTION_ENVIRONMENT" and (admission is not None or ledger is not None))
    ):
        raise AssessmentQualificationError("failed assessment resource disposition mismatch")


def _validate_ready_assessment(
    receipt_path: Path, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    expected_receipt_keys = {
        "format", "entry", "complete", "performance_disposition", "scope",
        "exact_refit_equal", "work", "resource_admission_relative_path",
        "resource_ledger_relative_path",
    }
    if set(receipt) != expected_receipt_keys:
        raise AssessmentQualificationError("assessment receipt field inventory mismatch")
    if (
        receipt["format"] != ASSESSMENT_FORMAT
        or receipt["entry"] != "assess-run"
        or receipt["complete"] is not True
        or receipt["performance_disposition"] != "PERFORMANCE_READY"
        or receipt["scope"] != "RESOURCE_AND_TECHNICAL_ONLY"
        or receipt["exact_refit_equal"] is not True
    ):
        raise AssessmentQualificationError(
            "assessment receipt is not complete PERFORMANCE_READY"
        )
    if receipt["work"] != _complete_assessment_work():
        raise AssessmentQualificationError("assessment fixed work mismatch")
    admission_path = _assessment_resource_path(
        receipt["resource_admission_relative_path"], prefix="assess-run-"
    )
    ledger_path = _assessment_resource_path(
        receipt["resource_ledger_relative_path"], prefix="assess-run-ledger-"
    )
    if admission_path == ledger_path:
        raise AssessmentQualificationError("assessment resource references alias")
    admission = _validate_assessment_admission(admission_path.read_bytes())
    raw_ledger = ledger_path.read_bytes()
    ledger = _load_json_object(raw_ledger, label="ledger")
    if raw_ledger != _plain_canonical_bytes(ledger):
        raise AssessmentQualificationError("assessment ledger bytes are not canonical")
    try:
        _validate_resource_values(
            {"entry": "assess-run", **admission}, ledger, entry="assess-run"
        )
    except ResourceAdmissionRefusal as exc:
        raise AssessmentQualificationError("assessment resource qualification mismatch") from exc
    return {
        "receipt_path": receipt_path,
        "receipt": dict(receipt),
        "admission": admission,
        "ledger": ledger,
    }


def _validate_performance_assessment() -> dict[str, Any]:
    """Validate the one complete technical qualification without opening data."""
    if not ASSESSMENT_ROOT.exists():
        raise AssessmentQualificationError("performance assessment is absent")
    if not _safe_directory(ASSESSMENT_ROOT):
        raise AssessmentQualificationError("performance assessment inventory is unsafe")
    entries = tuple(ASSESSMENT_ROOT.iterdir())
    if not entries:
        raise AssessmentQualificationError("performance assessment is absent")
    ready: list[dict[str, Any]] = []
    for root in entries:
        receipt_path, receipt = _assessment_receipt_at(root)
        if receipt.get("performance_disposition") == "PERFORMANCE_READY":
            ready.append(_validate_ready_assessment(receipt_path, receipt))
        else:
            _validate_failed_assessment(receipt)
    if len(ready) != 1:
        raise AssessmentQualificationError(
            "performance assessment requires exactly one PERFORMANCE_READY receipt"
        )
    return ready[0]


def validate_performance_assessment() -> dict[str, Any]:
    try:
        return _validate_performance_assessment()
    except AssessmentQualificationError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AssessmentQualificationError(
            "performance assessment could not be validated read-only"
        ) from exc


def _compile_runtime(capture: BindingCapture, postfit_bytes: tuple[bytes, ...]) -> Mapping[str, Any]:
    if len(postfit_bytes) != 1:
        raise DataBindingMismatch("post-fit oracle byte capture count mismatch")
    sources = {"contract": capture.prefit_bytes[CONTRACT_ORDINAL], "oracle": postfit_bytes[0]}
    package_name = f"_ucope_bound_runtime_{uuid.uuid4().hex}"
    package = types.ModuleType(package_name)
    package.__path__ = []
    sys.modules[package_name] = package
    loaded: dict[str, Any] = {}
    try:
        for name in ("contract", "oracle"):
            module_name = f"{package_name}.{name}"
            module = types.ModuleType(module_name)
            module.__file__ = f"{package_name}/{name}.py"
            module.__package__ = package_name
            sys.modules[module_name] = module
            exec(compile(sources[name], module.__file__, "exec"), module.__dict__)
            loaded[name] = module
    except BaseException:
        for key in tuple(sys.modules):
            if key == package_name or key.startswith(package_name + "."):
                sys.modules.pop(key, None)
        raise
    contract, oracle = loaded["contract"], loaded["oracle"]
    return {
        "surface": {
            "K_TEST": contract.K_TEST, "as_fraction": contract.as_fraction,
            "context_id": contract.context_id, "contexts": contract.contexts,
            "direct_probe_value": oracle.direct_probe_value,
            "expected_tail_value": oracle.expected_tail_value,
            "informed_value": oracle.informed_value,
            "joint_count_probability": oracle.joint_count_probability,
            "optimal_tail": oracle.optimal_tail, "posterior_short": oracle.posterior_short,
        },
    }


def _verify_postfit_binding(prefit: Mapping[str, Any]) -> PostfitCapture:
    try:
        if not isinstance(prefit, BindingCapture):
            raise DataBindingMismatch("post-fit verification requires the pre-fit byte capture")
        manifest_path = FIXED_BUNDLE_ROOT / "manifest.json"
        if manifest_path.read_bytes() != prefit.manifest_bytes:
            raise DataBindingMismatch("bundle manifest changed after fitting")
        if (
            FIXED_BUNDLE_ROOT / PREFIT_BINDING_RECEIPT_FILENAME
        ).read_bytes() != prefit.frozen_binding_bytes:
            raise DataBindingMismatch("pre-fit binding receipt changed after fitting")
        if (
            (FIXED_BUNDLE_ROOT / RESOURCE_RECEIPT_FILENAME).read_bytes()
            != prefit.bundle_admission_bytes
            or (FIXED_BUNDLE_ROOT / RESOURCE_LEDGER_FILENAME).read_bytes()
            != prefit.bundle_ledger_bytes
        ):
            raise DataBindingMismatch("bundle resource records changed after fitting")
        manifest = json.loads(prefit.manifest_bytes)
        prefit_records, postfit_records = _validate_manifest_shape(manifest)
        for record, captured in zip(prefit_records, prefit.prefit_bytes):
            source_path = PROJECT_ROOT / record["source_relative_path"]
            frozen_path = FIXED_BUNDLE_ROOT / record["bundle_relative_path"]
            if _unsafe_source_path(source_path) or _unsafe_source_path(frozen_path):
                raise DataBindingMismatch("pre-fit member became unsafe after fitting")
            source = source_path.read_bytes()
            frozen = frozen_path.read_bytes()
            if source != captured or frozen != captured:
                raise DataBindingMismatch("pre-fit member changed after fitting")
        postfit_bytes: list[bytes] = []
        for record in postfit_records:
            source_path = PROJECT_ROOT / record["source_relative_path"]
            frozen_path = FIXED_BUNDLE_ROOT / record["bundle_relative_path"]
            if _unsafe_source_path(source_path) or _unsafe_source_path(frozen_path):
                raise DataBindingMismatch("post-fit member is absent or unsafe")
            source = source_path.read_bytes()
            frozen = frozen_path.read_bytes()
            if source != frozen or len(frozen) != record["length"]:
                raise DataBindingMismatch("post-fit source-byte mismatch")
            postfit_bytes.append(frozen)
        runtime = _compile_runtime(prefit, tuple(postfit_bytes))
        receipt = {
            "status": "MATCH", "bundle_format": REFERENCE_BUNDLE_FORMAT,
            "member_count": len(ALL_MEMBERS), "prefit_members_rechecked": len(PREFIT_MEMBERS),
            "postfit_members_compared": len(POSTFIT_MEMBERS),
            "prefit_decoder_rows_replayed": prefit["decoder_rows_replayed"],
        }
        return PostfitCapture(receipt, runtime, tuple(postfit_bytes))
    except DataBindingMismatch:
        raise
    except (
        OSError, EOFError, gzip.BadGzipFile, zlib.error, UnicodeDecodeError, json.JSONDecodeError,
        ValueError, TypeError, KeyError, ImportError, RuntimeError, SyntaxError,
    ) as exc:
        raise DataBindingMismatch("post-fit data binding could not be established") from exc


def _verify_final_binding(prefit: BindingCapture, postfit: PostfitCapture) -> None:
    try:
        manifest = json.loads(prefit.manifest_bytes)
        prefit_records, postfit_records = _validate_manifest_shape(manifest)
        if (FIXED_BUNDLE_ROOT / "manifest.json").read_bytes() != prefit.manifest_bytes:
            raise DataBindingMismatch("bundle manifest changed before publication")
        if (
            FIXED_BUNDLE_ROOT / PREFIT_BINDING_RECEIPT_FILENAME
        ).read_bytes() != prefit.frozen_binding_bytes:
            raise DataBindingMismatch("pre-fit binding receipt changed before publication")
        if (
            (FIXED_BUNDLE_ROOT / RESOURCE_RECEIPT_FILENAME).read_bytes()
            != prefit.bundle_admission_bytes
            or (FIXED_BUNDLE_ROOT / RESOURCE_LEDGER_FILENAME).read_bytes()
            != prefit.bundle_ledger_bytes
        ):
            raise DataBindingMismatch("bundle resource records changed before publication")
        for record, captured in zip(prefit_records, prefit.prefit_bytes):
            source_path = PROJECT_ROOT / record["source_relative_path"]
            frozen_path = FIXED_BUNDLE_ROOT / record["bundle_relative_path"]
            if (
                _unsafe_source_path(source_path)
                or _unsafe_source_path(frozen_path)
                or source_path.read_bytes() != captured
                or frozen_path.read_bytes() != captured
            ):
                raise DataBindingMismatch("pre-fit member changed before publication")
        for record, captured in zip(postfit_records, postfit.postfit_bytes):
            source_path = PROJECT_ROOT / record["source_relative_path"]
            frozen_path = FIXED_BUNDLE_ROOT / record["bundle_relative_path"]
            if (
                _unsafe_source_path(source_path)
                or _unsafe_source_path(frozen_path)
                or source_path.read_bytes() != captured
                or frozen_path.read_bytes() != captured
            ):
                raise DataBindingMismatch("post-fit member changed before publication")
    except DataBindingMismatch:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        raise DataBindingMismatch("final data binding could not be established") from exc


def _control_path(
    entry: str, output_root: str | Path | None, *, kind: str,
) -> Path:
    # Failure evidence is deliberately outside the sole scientific result
    # namespace.  A supplied result path must never influence its location.
    del output_root
    return CONTROL_ROOT / f"{entry}-{kind}-{uuid.uuid4().hex}.json"


def _require_control_publication(
    entry: str,
    *,
    actual_stage: str,
    fit_entered: bool,
    evaluation_entered: bool,
    resource_admission_relative_path: str | None,
    resource_ledger_relative_path: str | None,
) -> None:
    allowed_stages = CONTROL_STAGES_BY_ENTRY.get(entry)
    if allowed_stages is None or actual_stage not in allowed_stages:
        raise ValueError("control entry/stage mismatch")
    if type(fit_entered) is not bool or type(evaluation_entered) is not bool:
        raise TypeError("control activity flags must be exact booleans")
    if evaluation_entered and not fit_entered:
        raise ValueError("control evaluation cannot precede fit")
    for value in (
        resource_admission_relative_path, resource_ledger_relative_path,
    ):
        if value is not None and (
            not isinstance(value, str)
            or Path(value).is_absolute()
            or ".." in Path(value).parts
        ):
            raise ValueError("control resource path is unsafe")
    if actual_stage == "EXECUTION_ENVIRONMENT" and (
        fit_entered
        or evaluation_entered
        or resource_admission_relative_path is not None
        or resource_ledger_relative_path is not None
    ):
        raise ValueError("environment control cannot reference later activity")


def publish_binding_stop(
    entry: str,
    reason: str,
    output_root: str | Path | None = None,
    *,
    actual_stage: str = "PREFIT_BINDING",
    fit_entered: bool = False,
    evaluation_entered: bool = False,
    resource_admission_relative_path: str | None = None,
    resource_ledger_relative_path: str | None = None,
) -> Path:
    _require_control_publication(
        entry, actual_stage=actual_stage, fit_entered=fit_entered,
        evaluation_entered=evaluation_entered,
        resource_admission_relative_path=resource_admission_relative_path,
        resource_ledger_relative_path=resource_ledger_relative_path,
    )
    path = _control_path(entry, output_root, kind="binding-control")
    body = {
        "format": CONTROL_RECEIPT_FORMAT,
        "complete": True,
        "disposition": "STOP_DATA_BINDING",
        "actual_stage": actual_stage,
        "fit_entered": fit_entered,
        "evaluation_entered": evaluation_entered,
        "fit_published": False,
        "evaluation_published": False,
        "scientific_certificate_published": False,
        "resource_admission_relative_path": resource_admission_relative_path,
        "resource_ledger_relative_path": resource_ledger_relative_path,
    }
    return atomic_create_json(path, body)


def publish_resource_stop(
    entry: str,
    output_root: str | Path | None = None,
    *,
    runtime_ceiling: bool = False,
    actual_stage: str = "MEMORY_ADMISSION",
    fit_entered: bool = False,
    evaluation_entered: bool = False,
    resource_admission_relative_path: str | None = None,
    resource_ledger_relative_path: str | None = None,
) -> Path:
    _require_control_publication(
        entry, actual_stage=actual_stage, fit_entered=fit_entered,
        evaluation_entered=evaluation_entered,
        resource_admission_relative_path=resource_admission_relative_path,
        resource_ledger_relative_path=resource_ledger_relative_path,
    )
    path = _control_path(entry, output_root, kind="resource-control")
    return atomic_create_json(
        path,
        {
            "format": CONTROL_RECEIPT_FORMAT,
            "complete": not runtime_ceiling,
            "disposition": (
                "INCOMPLETE_RESOURCE_CEILING"
                if runtime_ceiling
                else "RESOURCE_REFUSAL_NO_SCIENCE_STATE"
            ),
            "actual_stage": actual_stage,
            "fit_entered": fit_entered,
            "evaluation_entered": evaluation_entered,
            "fit_published": False,
            "evaluation_published": False,
            "scientific_certificate_published": False,
            "resource_admission_relative_path": resource_admission_relative_path,
            "resource_ledger_relative_path": resource_ledger_relative_path,
        },
    )


def publish_technical_stop(
    entry: str,
    output_root: str | Path | None = None,
    *,
    actual_stage: str,
    fit_entered: bool = False,
    evaluation_entered: bool = False,
    resource_admission_relative_path: str | None = None,
    resource_ledger_relative_path: str | None = None,
) -> Path:
    _require_control_publication(
        entry, actual_stage=actual_stage, fit_entered=fit_entered,
        evaluation_entered=evaluation_entered,
        resource_admission_relative_path=resource_admission_relative_path,
        resource_ledger_relative_path=resource_ledger_relative_path,
    )
    path = _control_path(entry, output_root, kind="technical-control")
    return atomic_create_json(
        path,
        {
            "format": CONTROL_RECEIPT_FORMAT,
            "complete": False,
            "disposition": "INCOMPLETE_TECHNICAL_PUBLICATION",
            "actual_stage": actual_stage,
            "fit_entered": fit_entered,
            "evaluation_entered": evaluation_entered,
            "fit_published": False,
            "evaluation_published": False,
            "scientific_certificate_published": False,
            "resource_admission_relative_path": resource_admission_relative_path,
            "resource_ledger_relative_path": resource_ledger_relative_path,
        },
    )


def _publish_failed_entry(
    entry: str,
    *,
    kind: str,
    output_root: str | Path | None,
    actual_stage: str,
    fit_entered: bool,
    evaluation_entered: bool,
    monitor: Any | None,
    admission: Mapping[str, Any] | None,
    existing_ledger: Mapping[str, Any] | None = None,
    private_path: Path | None = None,
) -> Path:
    ledger, relative_path, settlement_failed = _settle_failure(
        entry, monitor, existing_ledger
    )
    cleanup_failed = False
    if private_path is not None and private_path.exists():
        try:
            shutil.rmtree(private_path)
            if private_path.exists():
                raise OSError("private staging removal was incomplete")
        except OSError:
            cleanup_failed = True
    if ledger is not None and ledger["passed"] is not True:
        return publish_resource_stop(
            entry, output_root, runtime_ceiling=True, actual_stage=actual_stage,
            fit_entered=fit_entered, evaluation_entered=evaluation_entered,
            resource_admission_relative_path=_admission_relative_path(admission),
            resource_ledger_relative_path=relative_path,
        )
    if settlement_failed or cleanup_failed:
        return publish_technical_stop(
            entry, output_root, actual_stage=actual_stage,
            fit_entered=fit_entered, evaluation_entered=evaluation_entered,
            resource_admission_relative_path=_admission_relative_path(admission),
            resource_ledger_relative_path=relative_path,
        )
    if kind == "binding":
        return publish_binding_stop(
            entry, "data binding drift", output_root, actual_stage=actual_stage,
            fit_entered=fit_entered, evaluation_entered=evaluation_entered,
            resource_admission_relative_path=_admission_relative_path(admission),
            resource_ledger_relative_path=relative_path,
        )
    if kind != "technical":
        raise ValueError("unknown failure publication kind")
    return publish_technical_stop(
        entry, output_root, actual_stage=actual_stage,
        fit_entered=fit_entered, evaluation_entered=evaluation_entered,
        resource_admission_relative_path=_admission_relative_path(admission),
        resource_ledger_relative_path=relative_path,
    )


def _bound_structural(capture: BindingCapture):
    module = _compile_structural(capture.prefit_bytes[STRUCTURAL_ORDINAL])
    STRUCTURAL.use(module)
    return module


def _run_certificate_admitted(output_root: str | Path, admission: Mapping[str, Any]) -> Path:
    destination = Path(output_root)
    if destination.exists():
        raise FileExistsError(f"output root already exists: {destination}")
    monitor: Any | None = None
    staging: Path | None = None
    ledger: dict[str, Any] | None = None
    actual_stage = "ENTRY_SETUP"
    fit_entered = False
    evaluation_entered = False
    try:
        monitor = ResourceMonitor("run").start()
        actual_stage = "PERFORMANCE_QUALIFICATION"
        validate_performance_assessment()
        actual_stage = "PREFIT_BINDING"
        prefit = verify_data_binding()
        structural = _bound_structural(prefit) if isinstance(prefit, BindingCapture) else STRUCTURAL.get()
        actual_stage = "ENTRY_SETUP"
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent))
        monitor.set_paths(scratch=staging, durable=staging)
        fit_path = staging / FIT_FILENAME
        fit_reference_path = staging / FIT_REFERENCE_FILENAME
        certificate_path = staging / CERTIFICATE_FILENAME
        arguments: dict[str, Any] = {"binding_receipt": prefit, "output_path": fit_path}
        if isinstance(prefit, BindingCapture):
            arguments["tape_bytes"] = prefit.tape_bytes
        try:
            actual_stage = "FIT"
            fit_entered = True
            structural.fit_structural_artifact(**arguments)
        except (
            EOFError, gzip.BadGzipFile, zlib.error, UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise DataBindingMismatch("captured fit tapes could not be decoded") from exc
        actual_stage = "POSTFIT_BINDING"
        postfit = _verify_postfit_binding(prefit)
        if isinstance(postfit, PostfitCapture):
            structural.configure_postseal_runtime(postfit.runtime["surface"])
        atomic_create_bytes(fit_reference_path, fit_path.read_bytes())
        if fit_path.read_bytes() != fit_reference_path.read_bytes():
            raise RuntimeError("sealed fit/reference byte mismatch")
        actual_stage = "EVALUATION"
        evaluation_entered = True
        structural.evaluate_sealed_fit(
            fit_path=fit_path, fit_reference_path=fit_reference_path,
            binding_receipt=prefit, postfit_binding_receipt=postfit,
            output_path=certificate_path,
        )
        actual_stage = "FINAL_BINDING"
        if isinstance(prefit, BindingCapture) and isinstance(postfit, PostfitCapture):
            _verify_final_binding(prefit, postfit)
        actual_stage = "PREPUBLICATION_RESOURCE"
        atomic_create_json(staging / RESOURCE_RECEIPT_FILENAME, dict(admission))
        ledger = monitor.finish()
        if ledger["passed"] is not True:
            raise ResourceAdmissionRefusal("run resource ceiling exceeded")
        atomic_create_json(staging / RESOURCE_LEDGER_FILENAME, ledger)
        os.replace(staging, destination)
        return destination / CERTIFICATE_FILENAME
    except AssessmentQualificationError:
        return _publish_failed_entry(
            "run", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission, private_path=staging,
        )
    except DataBindingMismatch as exc:
        return _publish_failed_entry(
            "run", kind="binding", output_root=None,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission, private_path=staging,
        )
    except ResourceAdmissionRefusal:
        return _publish_failed_entry(
            "run", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission, existing_ledger=ledger,
            private_path=staging,
        )
    except (OSError, RuntimeError, ValueError, TypeError, KeyError):
        return _publish_failed_entry(
            "run", kind="technical", output_root=None,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission, existing_ledger=ledger,
            private_path=staging,
        )
    except BaseException:
        _settle_failure("run", monitor, ledger)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        raise


def run_certificate(output_root: str | Path) -> Path:
    try:
        require_frozen_execution_environment()
    except ExecutionEnvironmentMismatch:
        return publish_technical_stop(
            "run", actual_stage="EXECUTION_ENVIRONMENT"
        )
    require_frozen_result_argument(output_root)
    try:
        admission = _admit_memory("run")
    except ResourceAdmissionRefusal:
        return publish_resource_stop("run")
    try:
        _persist_entry_admission("run", admission)
    except (OSError, RuntimeError, TypeError, ValueError):
        return publish_technical_stop(
            "run", actual_stage="ENTRY_SETUP",
            resource_admission_relative_path=_admission_relative_path(admission),
        )
    return _run_certificate_admitted(FROZEN_RESULT_ROOT, admission)


def _validate_stored_resources(root: Path) -> None:
    admission_raw = (root / RESOURCE_RECEIPT_FILENAME).read_bytes()
    ledger_raw = (root / RESOURCE_LEDGER_FILENAME).read_bytes()
    admission = json.loads(admission_raw)
    ledger = json.loads(ledger_raw)
    if admission_raw != _plain_canonical_bytes(admission) or ledger_raw != _plain_canonical_bytes(ledger):
        raise ResourceAdmissionRefusal("stored resource records are not canonical")
    _validate_resource_values(admission, ledger, entry="run")


def _validate_result_inventory(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise DataBindingMismatch("result root is absent, unsafe, or not a directory")
    if os.name == "nt" and getattr(root.lstat(), "st_file_attributes", 0) & 0x400:
        raise DataBindingMismatch("result root is a reparse point")
    expected = {
        FIT_FILENAME, FIT_REFERENCE_FILENAME, CERTIFICATE_FILENAME,
        RESOURCE_RECEIPT_FILENAME, RESOURCE_LEDGER_FILENAME,
    }
    children = {item.name: item for item in root.iterdir()}
    if set(children) != expected or any(_unsafe_source_path(item) for item in children.values()):
        raise DataBindingMismatch("result artifact inventory mismatch")


def _publish_validation_resources(
    root: Path, admission: Mapping[str, Any], ledger: Mapping[str, Any],
) -> tuple[Path, Path]:
    token = uuid.uuid4().hex
    admission_path = root.parent / f".{root.name}.validate-{token}-resource-admission.json"
    ledger_path = root.parent / f".{root.name}.validate-{token}-resource-ledger.json"
    atomic_create_json(admission_path, dict(admission))
    atomic_create_json(ledger_path, dict(ledger))
    return admission_path, ledger_path


def _validate_run_admitted(output_root: str | Path, admission: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(output_root)
    monitor: Any | None = None
    private_root: Path | None = None
    ledger: dict[str, Any] | None = None
    actual_stage = "ENTRY_SETUP"
    fit_entered = False
    evaluation_entered = False
    try:
        monitor = ResourceMonitor("validate", durable=root).start()
        root.parent.mkdir(parents=True, exist_ok=True)
        private_root = Path(tempfile.mkdtemp(prefix=f".{root.name}.validation-", dir=root.parent))
        monitor.set_paths(scratch=private_root, durable=root)
        actual_stage = "STORED_RESOURCE_VALIDATION"
        _validate_result_inventory(root)
        _validate_stored_resources(root)
        actual_stage = "PREFIT_BINDING"
        prefit = verify_data_binding()
        structural = _bound_structural(prefit)
        actual_stage = "REFIT"
        fit_entered = True
        expected_fit = structural._fit_document(prefit, prefit.tape_bytes)
        recomputed_raw = structural.canonical_bytes(expected_fit)
        recomputed_path = atomic_create_bytes(
            private_root / "recomputed-structural-fit.json", recomputed_raw
        )
        if (
            recomputed_path.read_bytes() != (root / FIT_FILENAME).read_bytes()
            or recomputed_path.read_bytes() != (root / FIT_REFERENCE_FILENAME).read_bytes()
        ):
            raise structural.StructuralCertificateError(
                "stored fit differs from full exact recomputation"
            )
        actual_stage = "POSTFIT_BINDING"
        postfit = _verify_postfit_binding(prefit)
        structural.configure_postseal_runtime(postfit.runtime["surface"])
        actual_stage = "EVALUATION"
        evaluation_entered = True
        result = structural.validate_certificate(
            fit_path=root / FIT_FILENAME, fit_reference_path=root / FIT_REFERENCE_FILENAME,
            certificate_path=root / CERTIFICATE_FILENAME, binding_receipt=prefit,
            postfit_binding_receipt=postfit, tape_bytes=prefit.tape_bytes,
            recomputed_fit=expected_fit,
        )
        actual_stage = "FINAL_BINDING"
        _verify_final_binding(prefit, postfit)
        actual_stage = "PREPUBLICATION_RESOURCE"
        ledger = monitor.finish()
        if ledger["passed"] is not True:
            raise ResourceAdmissionRefusal("validate resource ceiling exceeded")
        _publish_validation_resources(root, admission, ledger)
        shutil.rmtree(private_root)
        return result
    except DataBindingMismatch as exc:
        _publish_failed_entry(
            "validate", kind="binding", output_root=root,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission, private_path=private_root,
        )
        raise
    except ResourceAdmissionRefusal:
        _publish_failed_entry(
            "validate", kind="technical", output_root=root,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission,
            existing_ledger=ledger, private_path=private_root,
        )
        raise
    except (OSError, RuntimeError, ValueError, TypeError, KeyError):
        _publish_failed_entry(
            "validate", kind="technical", output_root=root,
            actual_stage=actual_stage, fit_entered=fit_entered,
            evaluation_entered=evaluation_entered, monitor=monitor,
            admission=admission,
            existing_ledger=ledger, private_path=private_root,
        )
        raise
    except BaseException:
        _settle_failure("validate", monitor, ledger)
        if private_root is not None:
            shutil.rmtree(private_root, ignore_errors=True)
        raise


def validate_run(output_root: str | Path) -> dict[str, Any]:
    try:
        require_frozen_execution_environment()
    except ExecutionEnvironmentMismatch:
        publish_technical_stop(
            "validate", actual_stage="EXECUTION_ENVIRONMENT"
        )
        raise
    require_frozen_result_argument(output_root)
    try:
        admission = _admit_memory("validate")
    except ResourceAdmissionRefusal:
        publish_resource_stop("validate", FROZEN_RESULT_ROOT)
        raise
    try:
        _persist_entry_admission("validate", admission)
    except (OSError, RuntimeError, TypeError, ValueError):
        publish_technical_stop(
            "validate", FROZEN_RESULT_ROOT, actual_stage="ENTRY_SETUP",
            resource_admission_relative_path=_admission_relative_path(admission),
        )
        raise
    return _validate_run_admitted(FROZEN_RESULT_ROOT, admission)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run-ucope-structural-competence-certificate", allow_abbrev=False
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("freeze-reference-bundle", allow_abbrev=False)
    commands.add_parser("check-binding", allow_abbrev=False)
    commands.add_parser("assess-run", allow_abbrev=False)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    validate = commands.add_parser("validate", allow_abbrev=False)
    validate.add_argument("--output-root", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(raw_argv)
    if args.command in {"run", "validate"}:
        require_frozen_result_argv(raw_argv, args.command)
    if args.command == "freeze-reference-bundle":
        print(freeze_reference_bundle(FIXED_BUNDLE_ROOT))
    elif args.command == "check-binding":
        checked = check_binding()
        print(
            json.dumps(dict(checked), sort_keys=True, separators=(",", ":"))
            if isinstance(checked, BindingCapture)
            else checked
        )
    elif args.command == "assess-run":
        print(assess_run())
    elif args.command == "run":
        print(run_certificate(args.output_root))
    elif args.command == "validate":
        print(json.dumps(validate_run(args.output_root), sort_keys=True, separators=(",", ":")))
    else:
        raise AssertionError("unreachable command")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
