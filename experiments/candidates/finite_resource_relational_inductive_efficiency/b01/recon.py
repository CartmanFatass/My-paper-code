"""Dedicated-process TEST-only native scalar/batch/worker reconstruction."""

from __future__ import annotations

import argparse
import base64
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

from ..explore_infrastructure import (
    ResourceObservationUnavailable, recursive_byte_census,
)
from ..native.native_abi import STATE_SIZE, NativeStateV1
from ..native_adapter import (
    _validate_vcvars_compiler, _windows_build_environment, _windows_vcvars64,
    build_package_native_artifact, expected_native_contract,
    load_package_native_adapter, package_native_artifact_path,
)
from ..orchestration import PackageExternalActionEnvironment
from ..tapes import complete_test_only_witness
from .contract import canonical_json_bytes, named_compute_profile, validate_resource_receipt
from .native_batch import (
    B01NativeBatchEnvironment, NativePrimitives, bounded_worker_map,
)


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _filetime_value(value: object) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)  # type: ignore[attr-defined]


@dataclass(frozen=True)
class _ProcessObservation:
    pid: int
    creation_time_100ns: int
    rss_bytes: int
    cpu_seconds: float
    read_bytes: int
    write_bytes: int
    thread_count: int

    @property
    def identity(self) -> tuple[int, int]:
        return self.pid, self.creation_time_100ns


def _sample_windows_process_tree(
    retained_handles: dict[
        tuple[int, int], tuple[Callable[[], _ProcessObservation], Callable[[], None]]
    ] | None = None,
) -> tuple[_ProcessObservation, ...]:
    """Direct Windows process-tree sample; never substitutes the root process alone."""

    if os.name != "nt":  # pragma: no cover - A/RECON is a Windows-native artifact
        raise ResourceObservationUnavailable("A/RECON requires Windows process-tree telemetry")
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
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
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(IO_COUNTERS)]
    kernel32.GetProcessIoCounters.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    def process_entries() -> list[tuple[int, int, int]]:
        snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        if snapshot == wintypes.HANDLE(-1).value:
            raise ResourceObservationUnavailable("CreateToolhelp32Snapshot failed")
        rows: list[tuple[int, int, int]] = []
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            present = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            if not present:
                raise ResourceObservationUnavailable("Process32FirstW failed")
            while present:
                rows.append((
                    int(entry.th32ProcessID), int(entry.th32ParentProcessID), int(entry.cntThreads),
                ))
                entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                present = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snapshot)
        return rows

    entries = process_entries()

    root_pid = os.getpid()
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent, _ in entries:
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True

    observations: list[_ProcessObservation] = []
    threads_by_pid = {pid: threads for pid, _, threads in entries}
    for pid in sorted(descendants):
        handle = kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not handle:
            live_pids = {live_pid for live_pid, _, _ in process_entries()}
            if pid != root_pid and pid not in live_pids:
                continue
            raise ResourceObservationUnavailable(
                f"OpenProcess failed for live pid {pid} (winerror={ctypes.get_last_error()})"
            )
        keep_handle = False
        try:
            memory = PROCESS_MEMORY_COUNTERS_EX()
            memory.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            io = IO_COUNTERS()
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            succeeded = psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb)
            succeeded = succeeded and kernel32.GetProcessIoCounters(handle, ctypes.byref(io))
            succeeded = succeeded and kernel32.GetProcessTimes(
                handle, ctypes.byref(creation), ctypes.byref(exit_time),
                ctypes.byref(kernel), ctypes.byref(user),
            )
            if not succeeded:
                live_pids = {live_pid for live_pid, _, _ in process_entries()}
                if pid != root_pid and pid not in live_pids:
                    continue
                raise ResourceObservationUnavailable(f"process counters failed for live pid {pid}")
            observed = _ProcessObservation(
                pid=pid, creation_time_100ns=_filetime_value(creation),
                rss_bytes=int(memory.WorkingSetSize),
                cpu_seconds=(_filetime_value(kernel) + _filetime_value(user)) / 10_000_000.0,
                read_bytes=int(io.ReadTransferCount), write_bytes=int(io.WriteTransferCount),
                thread_count=int(threads_by_pid.get(pid, 0)),
            )
            observations.append(observed)
            if retained_handles is not None and observed.identity not in retained_handles:
                def final_observation(
                    *, retained_handle=handle, identity=observed.identity,
                    last_thread_count=observed.thread_count,
                ) -> _ProcessObservation:
                    final_io = IO_COUNTERS()
                    final_creation = wintypes.FILETIME()
                    final_exit = wintypes.FILETIME()
                    final_kernel = wintypes.FILETIME()
                    final_user = wintypes.FILETIME()
                    if not kernel32.GetProcessIoCounters(retained_handle, ctypes.byref(final_io)):
                        raise ResourceObservationUnavailable(
                            f"final GetProcessIoCounters failed for pid {identity[0]}"
                        )
                    if not kernel32.GetProcessTimes(
                        retained_handle, ctypes.byref(final_creation), ctypes.byref(final_exit),
                        ctypes.byref(final_kernel), ctypes.byref(final_user),
                    ):
                        raise ResourceObservationUnavailable(
                            f"final GetProcessTimes failed for pid {identity[0]}"
                        )
                    return _ProcessObservation(
                        pid=identity[0], creation_time_100ns=identity[1], rss_bytes=0,
                        cpu_seconds=(
                            _filetime_value(final_kernel) + _filetime_value(final_user)
                        ) / 10_000_000.0,
                        read_bytes=int(final_io.ReadTransferCount),
                        write_bytes=int(final_io.WriteTransferCount),
                        thread_count=last_thread_count,
                    )

                def close_retained(*, retained_handle=handle) -> None:
                    kernel32.CloseHandle(retained_handle)

                retained_handles[observed.identity] = (final_observation, close_retained)
                keep_handle = True
        finally:
            if not keep_handle:
                kernel32.CloseHandle(handle)
    if not any(row.pid == root_pid for row in observations):
        raise ResourceObservationUnavailable("A/RECON process tree had no observable members")
    return tuple(observations)


@dataclass(frozen=True)
class _TreeSample:
    monotonic_seconds: float
    members: tuple[_ProcessObservation, ...]
    scratch_bytes: int
    durable_bytes: int


class _AReconProcessTreeMonitor:
    """Retain per-process cumulative counters, including sampled children after exit."""

    def __init__(self, *, scratch_root: Path, durable_root: Path, interval_seconds: float) -> None:
        self.scratch_root = scratch_root
        self.durable_root = durable_root
        self.interval_seconds = interval_seconds
        self._stage = "UNASSIGNED"
        self._samples: list[tuple[str, _TreeSample]] = []
        self._lock = threading.Lock()
        self._capture_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._failure: BaseException | None = None
        self._retained_handles: dict[
            tuple[int, int], tuple[Callable[[], _ProcessObservation], Callable[[], None]]
        ] = {}

    def _capture(self) -> None:
        with self._capture_lock:
            sample = _TreeSample(
                monotonic_seconds=time.monotonic(),
                members=_sample_windows_process_tree(self._retained_handles),
                scratch_bytes=recursive_byte_census(self.scratch_root),
                durable_bytes=recursive_byte_census(self.durable_root),
            )
            with self._lock:
                self._samples.append((self._stage, sample))

    def set_stage(self, stage: str) -> None:
        running = self._thread is not None and self._thread.is_alive()
        if running:
            self._capture()
        with self._lock:
            self._stage = stage
        if running:
            self._capture()

    def _run(self) -> None:
        try:
            self._capture()
            while not self._stop.wait(self.interval_seconds):
                self._capture()
        except BaseException as error:
            self._failure = error
            self._stop.set()

    def start(self) -> "_AReconProcessTreeMonitor":
        if self._thread is not None:
            raise RuntimeError("A/RECON monitor can start only once")
        self._thread = threading.Thread(target=self._run, name="frrie-b01-recon-monitor", daemon=True)
        self._thread.start()
        return self

    @staticmethod
    def _telemetry(
        samples: Sequence[_TreeSample],
        final_observations: dict[tuple[int, int], _ProcessObservation],
    ) -> dict[str, Any]:
        if not samples:
            raise ResourceObservationUnavailable("A/RECON telemetry stage has no samples")
        first_identities = {row.identity for row in samples[0].members}
        first: dict[tuple[int, int], _ProcessObservation] = {}
        last: dict[tuple[int, int], _ProcessObservation] = {}
        for sample in samples:
            for row in sample.members:
                first.setdefault(row.identity, row)
                last[row.identity] = row
        for identity, row in final_observations.items():
            if identity in last:
                last[identity] = row
        cpu = read_bytes = write_bytes = 0.0
        for identity, end in last.items():
            start = first[identity]
            if identity not in first_identities:
                cpu += end.cpu_seconds
                read_bytes += end.read_bytes
                write_bytes += end.write_bytes
            else:
                cpu += max(0.0, end.cpu_seconds - start.cpu_seconds)
                read_bytes += max(0, end.read_bytes - start.read_bytes)
                write_bytes += max(0, end.write_bytes - start.write_bytes)
        wall = max(0.0, samples[-1].monotonic_seconds - samples[0].monotonic_seconds)
        peak_process_count = max(len(sample.members) for sample in samples)
        peak_thread_count = max(sum(row.thread_count for row in sample.members) for sample in samples)
        logical_cpu_count = int(os.cpu_count() or 1)
        core_equivalents = 0.0 if wall == 0.0 else float(cpu) / wall
        return {
            "wall_seconds": wall,
            "cpu_seconds": float(cpu),
            "cpu_core_equivalents": core_equivalents,
            "host_cpu_occupancy_fraction": core_equivalents / logical_cpu_count,
            "logical_cpu_count": logical_cpu_count,
            "peak_rss_bytes": max(sum(row.rss_bytes for row in sample.members) for sample in samples),
            "scratch_peak_bytes": max(sample.scratch_bytes for sample in samples),
            "durable_peak_bytes": max(sample.durable_bytes for sample in samples),
            "io_read_transfer_bytes": int(read_bytes),
            "io_write_transfer_bytes": int(write_bytes),
            "peak_process_count": peak_process_count,
            "peak_thread_count": peak_thread_count,
            "sample_count": len(samples),
        }

    def stop(self) -> dict[str, Any]:
        if self._thread is None:
            raise RuntimeError("A/RECON monitor was not started")
        self._stop.set()
        self._thread.join(timeout=max(1.0, self.interval_seconds * 4.0))
        if self._thread.is_alive():
            raise ResourceObservationUnavailable("A/RECON process monitor did not stop")
        if self._failure is not None:
            raise ResourceObservationUnavailable("A/RECON process monitor failed") from self._failure
        self._capture()
        with self._lock:
            labelled = list(self._samples)
        if len(labelled) < 2:
            raise ResourceObservationUnavailable("A/RECON monitor requires start/terminal samples")
        stage_order: list[str] = []
        grouped: dict[str, list[_TreeSample]] = {}
        for stage, sample in labelled:
            if stage not in grouped:
                stage_order.append(stage)
                grouped[stage] = []
            grouped[stage].append(sample)
        last_stage_by_identity: dict[tuple[int, int], str] = {}
        for stage, sample in labelled:
            for row in sample.members:
                last_stage_by_identity[row.identity] = stage
        try:
            finals = {
                identity: query() for identity, (query, _) in self._retained_handles.items()
            }
            return {
                "schema": "FRRIE_B01_A_RECON_PROCESS_TREE_TELEMETRY_V2",
                "stages": [
                    {
                        "stage_id": stage,
                        "telemetry": self._telemetry(
                            grouped[stage],
                            {
                                identity: row for identity, row in finals.items()
                                if last_stage_by_identity.get(identity) == stage
                            },
                        ),
                    }
                    for stage in stage_order
                ],
                "end_to_end": self._telemetry(
                    [sample for _, sample in labelled], finals,
                ),
            }
        finally:
            for _, close in self._retained_handles.values():
                close()
            self._retained_handles.clear()


def _fresh_admit(receipt_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
            "admit-memory", "--out", str(receipt_path),
        ],
        check=False, capture_output=True, text=True, timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return validate_resource_receipt(json.loads(receipt_path.read_text(encoding="utf-8")))


def _state_primitives(snapshot: bytes) -> tuple[NativePrimitives, bytes]:
    state = NativeStateV1.from_buffer_copy(snapshot)
    metrics = state.metrics
    return NativePrimitives(
        dw=int(metrics.dw), de=int(metrics.de), waste=float(metrics.waste),
        duplicate=int(metrics.duplicate_arrivals), expired=int(metrics.expired_arrivals),
        collision=int(metrics.collision_loss), empty_radio=int(metrics.empty_actions),
        radio_actions=int(metrics.radio_actions), waste_actions=int(metrics.waste_actions),
        successful_deliveries=int(metrics.new_timely_deliveries),
    ), bytes(state.previous_success[:state.roster])


def validate_recon_evidence(value: Any) -> dict[str, Any]:
    fields = {
        "schema", "test_only", "result_bearing", "scientific_values",
        "model_created", "optimizer_created", "result_roots_created",
        "native_artifact_path", "native_artifact_bytes_b64", "native_artifact_byte_count",
        "vcvars_path", "compiler_path", "vc_tools_root", "compiler_in_vc_tools",
        "resource_receipt_path", "resource_receipt", "native_contract", "compute",
        "scalar_batch_rows", "scalar_work_ledger", "batch_work_ledger",
        "worker_rows", "executor_worker_counts", "telemetry",
        "performance_disposition", "performance_blocker",
        "scalar_batch_direct_equal", "worker_1_2_4_direct_equal", "complete",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise RuntimeError("A/RECON evidence fields differ")
    if (
        value["schema"] != "FRRIE_B01_A_RECON_DIRECT_EQUIVALENCE_V1"
        or value["test_only"] is not True or value["result_bearing"] is not False
        or value["scientific_values"] is not None or value["model_created"] is not False
        or value["optimizer_created"] is not False or value["result_roots_created"] is not False
        or value["complete"] is not True
    ):
        raise RuntimeError("A/RECON TEST/non-result identity differs")
    validate_resource_receipt(value["resource_receipt"])
    artifact_bytes = base64.b64decode(value["native_artifact_bytes_b64"], validate=True)
    if len(artifact_bytes) != value["native_artifact_byte_count"] or not artifact_bytes:
        raise RuntimeError("A/RECON native artifact bytes/count differ")
    if sys.platform == "win32":
        compiler = _validate_vcvars_compiler(Path(value["vcvars_path"]), value["compiler_path"])
        if (
            value["compiler_in_vc_tools"] is not True
            or str(compiler) != str(Path(value["compiler_path"]).resolve(strict=True))
            or str(Path(value["vc_tools_root"]).resolve(strict=True))
            != str(Path(value["vcvars_path"]).resolve(strict=True).parents[2] / "Tools")
        ):
            raise RuntimeError("A/RECON compiler/vcvars containment differs")
    if value["native_contract"] != asdict(expected_native_contract(value["compute"])):
        raise RuntimeError("A/RECON native contract differs from compute")
    rows = value["scalar_batch_rows"]
    if not isinstance(rows, list) or len(rows) != 48:
        raise RuntimeError("A/RECON scalar/batch row count differs")
    coordinates = set()
    for row in rows:
        coordinates.add((row["lane"], row["slot"]))
        for left, right in (
            ("scalar_state_b64", "batch_state_b64"),
            ("scalar_observation_b64", "batch_observation_b64"),
            ("scalar_roles_b64", "batch_roles_b64"),
            ("scalar_masks_b64", "batch_masks_b64"),
            ("scalar_previous_success_b64", "batch_previous_success_b64"),
        ):
            if base64.b64decode(row[left], validate=True) != base64.b64decode(row[right], validate=True):
                raise RuntimeError(f"A/RECON scalar/batch direct field differs: {left}")
        if (
            row["scalar_slot"] != row["batch_slot"]
            or row["scalar_observation_terminal"] != row["batch_observation_terminal"]
            or row["scalar_step_terminal"] != row["batch_step_terminal"]
            or row["scalar_return_hex"] != row["batch_return_hex"]
            or row["scalar_primitives"] != row["batch_primitives"]
        ):
            raise RuntimeError("A/RECON scalar/batch step facts differ")
    if coordinates != {(lane, slot) for lane in range(4) for slot in range(12)}:
        raise RuntimeError("A/RECON scalar/batch coordinate inventory differs")
    if value["scalar_work_ledger"] != {
        "lanes": 4, "native_reset_calls": 4, "native_observe_calls": 48,
        "native_step_calls": 48, "environment_slots": 48,
    } or value["batch_work_ledger"] != {
        "lanes": 4, "native_reset_calls": 1, "native_observe_calls": 12,
        "native_step_calls": 12, "environment_slots": 48,
    }:
        raise RuntimeError("A/RECON scalar/batch work ledgers differ from direct calls")
    worker_rows = value["worker_rows"]
    if value["executor_worker_counts"] != [1, 2, 4]:
        raise RuntimeError("A/RECON executor worker configuration differs")
    if not isinstance(worker_rows, list) or len(worker_rows) != 24:
        raise RuntimeError("A/RECON worker row count differs")
    by_coordinate = {(row["worker_count"], row["task"]): row for row in worker_rows}
    if set(by_coordinate) != {(workers, task) for workers in (1, 2, 4) for task in range(8)}:
        raise RuntimeError("A/RECON worker coordinate inventory differs")
    for task in range(8):
        baseline = dict(by_coordinate[(1, task)])
        baseline.pop("worker_count")
        for workers in (2, 4):
            observed = dict(by_coordinate[(workers, task)])
            observed.pop("worker_count")
            if observed != baseline:
                raise RuntimeError("A/RECON 1/2/4 direct task rows differ")
        if (
            len(baseline["trace"]) != 12
            or baseline["work_ledger"] != {
                "lanes": 1, "native_reset_calls": 1, "native_observe_calls": 12,
                "native_step_calls": 12, "environment_slots": 12,
            }
        ):
            raise RuntimeError("A/RECON worker trace/work differs")
    telemetry = value["telemetry"]
    if not isinstance(telemetry, dict) or telemetry.get("schema") != (
        "FRRIE_B01_A_RECON_PROCESS_TREE_TELEMETRY_V2"
    ) or set(telemetry) != {
        "schema", "stages", "end_to_end", "known_created_files",
    } or not telemetry.get("stages") or not isinstance(telemetry.get("end_to_end"), dict):
        raise RuntimeError("A/RECON process-tree telemetry is absent")
    telemetry_fields = {
        "wall_seconds", "cpu_seconds", "cpu_core_equivalents",
        "host_cpu_occupancy_fraction", "logical_cpu_count", "peak_rss_bytes",
        "scratch_peak_bytes", "durable_peak_bytes", "io_read_transfer_bytes",
        "io_write_transfer_bytes",
        "peak_process_count", "peak_thread_count", "sample_count",
    }
    telemetry_rows = [row.get("telemetry") for row in telemetry["stages"]]
    telemetry_rows.append(telemetry["end_to_end"])
    for row in telemetry_rows:
        if not isinstance(row, dict) or set(row) != telemetry_fields:
            raise RuntimeError("A/RECON process-tree telemetry fields differ")
        if isinstance(row["peak_process_count"], bool) or not isinstance(
            row["peak_process_count"], int,
        ):
            raise RuntimeError("A/RECON process peak is invalid")
        if (
            row["peak_process_count"] < 1 or row["peak_thread_count"] < 1
            or row["sample_count"] < 1 or row["logical_cpu_count"] < 1
        ):
            raise RuntimeError("A/RECON process-tree telemetry has no direct samples")
        expected_core = 0.0 if row["wall_seconds"] == 0.0 else (
            row["cpu_seconds"] / row["wall_seconds"]
        )
        if row["cpu_core_equivalents"] != expected_core or (
            row["host_cpu_occupancy_fraction"]
            != expected_core / row["logical_cpu_count"]
        ):
            raise RuntimeError("A/RECON CPU denominator semantics differ")
    if telemetry["end_to_end"]["cpu_seconds"] <= 0.0:
        raise RuntimeError("A/RECON process-tree CPU evidence is absent")
    stage_by_id = {row["stage_id"]: row["telemetry"] for row in telemetry["stages"]}
    native_build = stage_by_id.get("NATIVE_BUILD")
    if not isinstance(native_build, dict) or (
        native_build["io_write_transfer_bytes"] <= 0 or native_build["cpu_seconds"] <= 0.0
    ):
        raise RuntimeError("A/RECON native-build child CPU/I/O evidence is absent")
    if telemetry["known_created_files"] != [{
        "stage_id": "NATIVE_BUILD",
        "path": value["native_artifact_path"],
        "direct_created_file_bytes": value["native_artifact_byte_count"],
        "census_semantics": "DIRECT_FINAL_FILE_LENGTH_NOT_OS_IO_TRANSFER_TOTAL",
    }]:
        raise RuntimeError("A/RECON direct build-output census differs")
    if (
        value["performance_disposition"] != "REPAIR_REQUIRED"
        or value["performance_blocker"] != "FULL_B01_END_TO_END_TRAIN_EVAL_TELEMETRY_ABSENT"
    ):
        raise RuntimeError("A/RECON must remain performance REPAIR_REQUIRED")
    if value["scalar_batch_direct_equal"] is not True or value["worker_1_2_4_direct_equal"] is not True:
        raise RuntimeError("A/RECON redundant equality summaries differ")
    return value


def run_test_recon(*, root: Path) -> dict[str, Any]:
    root = root.resolve(strict=False)
    staging = root.with_name(root.name + ".creating")
    if root.exists() or staging.exists():
        raise RuntimeError("A/RECON TEST root is not fresh")
    staging.mkdir(parents=True, exist_ok=False)
    scratch = staging / "scratch"
    scratch.mkdir()
    receipt_path = staging / "admit-memory.json"
    monitor = _AReconProcessTreeMonitor(
        scratch_root=scratch, durable_root=staging, interval_seconds=0.005,
    )
    monitor.set_stage("NATIVE_BUILD")
    monitor.start()
    if sys.platform == "win32":
        vcvars = _windows_vcvars64()
        compiler, _ = _windows_build_environment(vcvars)
        compiler_path = _validate_vcvars_compiler(vcvars, compiler)
        vc_tools_root = (vcvars.resolve(strict=True).parents[2] / "Tools").resolve(strict=True)
    else:  # pragma: no cover - this retained artifact contract is exercised on Windows
        vcvars = Path("")
        compiler_path = Path("")
        vc_tools_root = Path("")
    artifact = build_package_native_artifact()
    artifact_bytes = artifact.read_bytes()
    compute = named_compute_profile()
    adapter = load_package_native_adapter(compute)
    monitor.set_stage("MEMORY_ADMISSION")
    receipt = _fresh_admit(receipt_path)
    monitor.set_stage("SCALAR_BATCH_4X12")
    tapes = [complete_test_only_witness(roster=6, episode=index) for index in range(4)]
    scalars = [PackageExternalActionEnvironment(adapter, 6) for _ in range(4)]
    batch = B01NativeBatchEnvironment(adapter, roster=6, lanes=4)
    for scalar, tape in zip(scalars, tapes):
        scalar.reset(tape)
    batch.reset(tapes)
    scalar_batch_rows = []
    for slot in range(12):
        scalar_observations = [scalar.observe() for scalar in scalars]
        batch_observation = batch.observe()
        scalar_steps = [scalar.step([5] * 6) for scalar in scalars]
        batch_step = batch.step(np.full((4, 6), 5, dtype=np.int64))
        batch_snapshot = batch.snapshot()
        for lane in range(4):
            scalar_observation = scalar_observations[lane]
            scalar_step = scalar_steps[lane]
            scalar_state = scalars[lane].snapshot()
            batch_state = batch_snapshot[lane * STATE_SIZE:(lane + 1) * STATE_SIZE]
            scalar_primitives, scalar_success = _state_primitives(scalar_state)
            scalar_batch_rows.append({
                "lane": lane, "slot": slot,
                "scalar_state_b64": _b64(scalar_state), "batch_state_b64": _b64(batch_state),
                "scalar_observation_b64": _b64(scalar_observation.observations.tobytes()),
                "batch_observation_b64": _b64(batch_observation.observations[lane].tobytes()),
                "scalar_roles_b64": _b64(scalar_observation.roles.tobytes()),
                "batch_roles_b64": _b64(batch_observation.roles[lane].tobytes()),
                "scalar_masks_b64": _b64(scalar_observation.legal_masks.tobytes()),
                "batch_masks_b64": _b64(batch_observation.legal_masks[lane].tobytes()),
                "scalar_slot": scalar_observation.slot, "batch_slot": batch_observation.slots[lane],
                "scalar_observation_terminal": scalar_observation.terminal,
                "batch_observation_terminal": batch_observation.terminals[lane],
                "scalar_step_terminal": scalar_step.terminal,
                "batch_step_terminal": batch_step.terminals[lane],
                "scalar_return_hex": float(scalar_step.terminal_return).hex(),
                "batch_return_hex": float(batch_step.returns[lane]).hex(),
                "scalar_primitives": asdict(scalar_primitives),
                "batch_primitives": asdict(batch_step.primitives[lane]),
                "scalar_previous_success_b64": _b64(scalar_success),
                "batch_previous_success_b64": _b64(batch_step.previous_success[lane].tobytes()),
            })
    scalar_ledger = {
        "lanes": 4, "native_reset_calls": 4, "native_observe_calls": 48,
        "native_step_calls": 48, "environment_slots": 48,
    }
    batch_ledger = asdict(batch.work_ledger())

    def rollout(episode: int):
        environment = B01NativeBatchEnvironment(adapter, roster=6, lanes=1)
        environment.reset([complete_test_only_witness(roster=6, episode=episode)])
        trace = []
        for slot in range(12):
            observation = environment.observe()
            step = environment.step([[5] * 6])
            trace.append({
                "slot": slot, "state_b64": _b64(environment.snapshot()),
                "observation_b64": _b64(observation.observations.tobytes()),
                "roles_b64": _b64(observation.roles.tobytes()),
                "masks_b64": _b64(observation.legal_masks.tobytes()),
                "observation_slots": list(observation.slots),
                "observation_terminals": list(observation.terminals),
                "step_terminals": list(step.terminals),
                "returns_hex": [float(value).hex() for value in step.returns],
                "previous_success_b64": _b64(step.previous_success.tobytes()),
                "primitives": [asdict(item) for item in step.primitives],
            })
        return {
            "trace": trace, "final_state_b64": _b64(environment.snapshot()),
            "work_ledger": asdict(environment.work_ledger()),
        }

    results = {}
    for workers in (1, 2, 4):
        monitor.set_stage(f"WORKERS_{workers}")
        results[workers] = bounded_worker_map(rollout, tuple(range(8)), workers=workers)
    worker_rows = [
        {"worker_count": workers, "task": task, **dict(row)}
        for workers in (1, 2, 4)
        for task, row in enumerate(results[workers])
    ]
    telemetry = monitor.stop()
    telemetry["known_created_files"] = [{
        "stage_id": "NATIVE_BUILD", "path": str(artifact.resolve(strict=True)),
        "direct_created_file_bytes": len(artifact_bytes),
        "census_semantics": "DIRECT_FINAL_FILE_LENGTH_NOT_OS_IO_TRANSFER_TOTAL",
    }]
    final_receipt_path = root / "admit-memory.json"
    evidence = {
        "schema": "FRRIE_B01_A_RECON_DIRECT_EQUIVALENCE_V1",
        "test_only": True, "result_bearing": False, "scientific_values": None,
        "model_created": False, "optimizer_created": False, "result_roots_created": False,
        "native_artifact_path": str(artifact.resolve(strict=True)),
        "native_artifact_bytes_b64": _b64(artifact_bytes),
        "native_artifact_byte_count": len(artifact_bytes),
        "vcvars_path": str(vcvars.resolve(strict=True)),
        "compiler_path": str(compiler_path), "vc_tools_root": str(vc_tools_root),
        "compiler_in_vc_tools": True,
        "resource_receipt_path": str(final_receipt_path), "resource_receipt": receipt,
        "native_contract": asdict(adapter.contract), "compute": compute,
        "scalar_batch_rows": scalar_batch_rows,
        "scalar_work_ledger": scalar_ledger, "batch_work_ledger": batch_ledger,
        "worker_rows": worker_rows, "executor_worker_counts": [1, 2, 4],
        "telemetry": telemetry,
        "performance_disposition": "REPAIR_REQUIRED",
        "performance_blocker": "FULL_B01_END_TO_END_TRAIN_EVAL_TELEMETRY_ABSENT",
        "scalar_batch_direct_equal": True, "worker_1_2_4_direct_equal": True,
        "complete": True,
    }
    validate_recon_evidence(evidence)
    (staging / "evidence.json").write_bytes(canonical_json_bytes(evidence))
    os.rename(staging, root)
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="frrie-b01-recon")
    parser.add_argument("--root", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    staging = root.with_name(root.name + ".creating")
    try:
        run_test_recon(root=root)
    except BaseException as error:
        if staging.is_dir():
            incomplete = root.with_name(root.name + ".incomplete")
            if incomplete.exists():
                raise RuntimeError(
                    "A/RECON incomplete quarantine already exists; staging was preserved"
                ) from error
            marker = {
                "schema": "FRRIE_B01_A_RECON_INCOMPLETE_V1",
                "status": "INCOMPLETE_SUPERSEDED_TECHNICAL_ARTIFACT",
                "test_only": True, "result_bearing": False, "scientific_values": None,
                "intended_root": str(root), "exception_type": type(error).__name__,
                "exception_message": str(error),
            }
            (staging / "incomplete.json").write_bytes(canonical_json_bytes(marker))
            os.rename(staging, incomplete)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
