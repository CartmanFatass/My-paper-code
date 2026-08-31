"""Guarded V3 FCEOV production with fixed-frontier technical resume."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
_MODULE_ENTRY_AT = time.perf_counter()
from typing import Sequence

import torch

from .artifacts import (
    FINAL_BUNDLE_SCHEMA, RESUME_WITNESS_SCHEMA, TERMINAL_FACT_SCHEMA, ArtifactContractError,
    SourceNativeSnapshot, build_panel_frontier, build_run_record, capture_source_native_snapshot,
    compare_source_native_snapshot, load_checkpoint, load_contiguous_panel_slices,
    load_final_bundle, load_foundation_gate, load_foundation_nonpass_terminal,
    load_panel_frontier, load_resume_witness, load_rng_master, load_run_record,
    load_source_native_snapshot, observe_resume_equality, prepare_final_bundle,
    restore_checkpoint, write_checkpoint, write_foundation_gate,
    write_panel_frontier, write_panel_slice, write_resume_witness, write_rng_master,
    write_run_record, write_source_native_snapshot, write_terminal_fact,
    write_prepared_final_bundle, validate_live_run_record_runtime,
    observe_atomic_scratch, set_atomic_scratch_observer,
)
from .analysis import analyze_complete_panel
from .contracts import (
    CHECKPOINT_UPDATE, PANEL_FINAL_NATIVE_WIDTH, PANEL_MAX_NATIVE_WIDTH, PANEL_SLICE_COUNT,
    PANEL_WIDTH, RESOURCE_ENVELOPE, RESOURCE_MAXIMA, Disposition, LIFECYCLE_STATUS,
    RESULT_COMMAND_STATUS, TERMINAL_TOMBSTONE_MESSAGE, TerminalFact,
)
from .foundation import (
    analyze_competence, execute_native_competence, freeze_foundation, materialize_foundation,
    validate_competence_rng_contract,
)
from .host_bridge import headroom_conformance, verify_public_alias
from .panel import (
    aggregate_panel_slices, build_native_resets, build_panel_inventory, build_panel_slices,
    execute_native_panel_slice, materialize_disturbance_tapes, preflight_native_panel_widths,
    validate_complete_panel_cells, validate_panel_slices, validate_tape_pairing,
)
from .rng import AddressRNG, fresh_master
from .source_manifest import load_consumed_source_manifest, load_source_manifest, write_source_manifest
from .training import (
    ExactAdamW, build_training_plan, summarize_resource_usage, train_one_update,
    validate_training_rng_contract,
)


PHASE = "FOUNDATION_AND_2X3"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
QUARANTINED_RESULT_ROOT = _REPOSITORY_ROOT / "temp" / "directions" / (
    "semigroup_consistent_duration_model_policy"
) / "exp" / "2026-08-31.1-wave3-fceov-v3"
QUARANTINED_REPLACEMENT_RESULT_ROOT = _REPOSITORY_ROOT / "temp" / "directions" / (
    "semigroup_consistent_duration_model_policy"
) / "exp" / "2026-08-31.2-wave3-fceov-v3-replacement"
CANONICAL_RESULT_ROOT = _REPOSITORY_ROOT / "temp" / "directions" / (
    "semigroup_consistent_duration_model_policy"
) / "exp" / "2026-08-31.3-wave3-fceov-v3-replacement"
_RESOURCE_SCRIPT = _REPOSITORY_ROOT / "scripts" / "hmasd_resource_preflight.py"
_FORBIDDEN_RECEIPT_KEYS = ("identity", "hash", "approval", "authorization")
_WALL_SECONDS_CEILING = 300.0
_PEAK_RSS_BYTES_CEILING = 1 * 1024**3
_SCRATCH_BYTES_CEILING = 64 * 1024**2
_DURABLE_BYTES_CEILING = 64 * 1024**2
_DIRECTION_RESOURCE_SCHEMA = "SCDMP_FCEOV_DIRECTION_RESOURCE_V1"
_ASSESS_DIRECTION = "semigroup_consistent_duration_model_policy"
_ASSESS_RUN_ID = "2026-08-31-3-wave3-fceov-v3-replacement"


class _InvocationScratchTracker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.invocation_peak_bytes = 0
        self.attempt_cumulative_peak_bytes = _prior_attempt_scratch_peak(root)
        self.scientific_state_started = False
        self.failed = False

    def observe(self, path: Path) -> None:
        try:
            temporary_size = path.stat().st_size
            staging = _staging_root(self.root)
            size = (
                _recursive_file_bytes(staging)
                if path.is_relative_to(staging)
                else temporary_size
            )
        except (OSError, ValueError) as error:
            self.failed = True
            set_atomic_scratch_observer(None)
            assessment = {
                "schema": _DIRECTION_RESOURCE_SCHEMA,
                "passed": False,
                "failure_reasons": ["scratch_observation_failed"],
                "measurement_error_type": type(error).__name__,
                "invocation_scratch_peak_bytes": self.invocation_peak_bytes,
                "attempt_cumulative_scratch_peak_bytes": self.attempt_cumulative_peak_bytes,
            }
            if self.scientific_state_started:
                _record_invalid_evidence(
                    root=self.root, stage="atomic-scratch-observer", assessment=assessment,
                )
            raise ResourceAdmissionError("atomic scratch observation failed") from error
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            self.failed = True
            set_atomic_scratch_observer(None)
            assessment = {
                "schema": _DIRECTION_RESOURCE_SCHEMA,
                "passed": False,
                "failure_reasons": ["scratch_observation_failed"],
                "measurement_error_type": "invalid_size",
                "invocation_scratch_peak_bytes": self.invocation_peak_bytes,
                "attempt_cumulative_scratch_peak_bytes": self.attempt_cumulative_peak_bytes,
            }
            if self.scientific_state_started:
                _record_invalid_evidence(
                    root=self.root, stage="atomic-scratch-observer", assessment=assessment,
                )
            raise ResourceAdmissionError("atomic scratch observation returned an invalid size")
        self.invocation_peak_bytes = max(self.invocation_peak_bytes, size)
        self.attempt_cumulative_peak_bytes = max(
            self.attempt_cumulative_peak_bytes, self.invocation_peak_bytes,
        )


_ACTIVE_SCRATCH_TRACKER: _InvocationScratchTracker | None = None


def _process_creation_perf_counter() -> float:
    """Map OS process creation time onto the monotonic perf-counter clock."""

    now_perf = time.perf_counter()
    try:
        if sys.platform == "win32":
            from ctypes import wintypes

            created = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not ctypes.windll.kernel32.GetProcessTimes(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(kernel), ctypes.byref(user),
            ):
                raise OSError("GetProcessTimes failed")
            ticks = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            created_epoch = ticks / 10_000_000.0 - 11_644_473_600.0
            return now_perf - max(0.0, time.time() - created_epoch)
        if sys.platform.startswith("linux"):
            stat = Path("/proc/self/stat").read_text(encoding="ascii")
            fields = stat[stat.rfind(")") + 2:].split()
            start_ticks = int(fields[19])
            ticks_per_second = int(os.sysconf("SC_CLK_TCK"))
            uptime = float(Path("/proc/uptime").read_text(encoding="ascii").split()[0])
            return now_perf - max(0.0, uptime - start_ticks / ticks_per_second)
    except (OSError, ValueError, IndexError):
        pass
    return _MODULE_ENTRY_AT


_PROCESS_STARTED_AT = _process_creation_perf_counter()


class PreflightError(RuntimeError):
    pass


class ResourceAdmissionError(RuntimeError):
    pass


def _require_canonical_result_root(result_root: str | Path) -> Path:
    root = Path(result_root).resolve(strict=False)
    quarantined = tuple(
        Path(path).resolve(strict=False)
        for path in (QUARANTINED_RESULT_ROOT, QUARANTINED_REPLACEMENT_RESULT_ROOT)
    )
    if any(
        os.path.normcase(str(root)) == os.path.normcase(str(path))
        for path in quarantined
    ):
        raise PreflightError("the .1 and .2 FCEOV attempts are quarantined and cannot be resumed")
    expected = Path(CANONICAL_RESULT_ROOT).resolve(strict=False)
    if os.path.normcase(str(root)) != os.path.normcase(str(expected)):
        raise PreflightError(
            "result-root is not the sole canonical FCEOV V3 result coordinate"
        )
    return root


def _prior_attempt_scratch_peak(root: Path) -> int:
    """Load the maximum scratch peak from direct receipts of this .3 attempt only."""

    candidates = [root]
    staging = _staging_root(root)
    if staging != root:
        candidates.append(staging)
    peak = 0
    for parent in candidates:
        if not parent.is_dir():
            continue
        for path in parent.glob("direction-resource-*.json"):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if (
                not isinstance(value, dict)
                or value.get("schema") != _DIRECTION_RESOURCE_SCHEMA
                or not isinstance(value.get("stage"), str)
                or value.get("passed") not in (True, False)
                or _contains_forbidden_receipt_key(value)
            ):
                continue
            for key in (
                "attempt_cumulative_scratch_peak_bytes",
                "invocation_scratch_peak_bytes",
                "observed_scratch_peak_bytes",
            ):
                observed = value.get(key)
                if isinstance(observed, int) and not isinstance(observed, bool) and observed >= 0:
                    peak = max(peak, observed)
    return peak


def _staging_root(root: Path) -> Path:
    return root.with_name(f".{root.name}.staging")


def _recursive_file_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if not path.is_dir():
        return path.stat().st_size
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def _largest_file_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return max((entry.stat().st_size for entry in path.rglob("*") if entry.is_file()), default=0)


def _physical_total_memory_bytes() -> int:
    if sys.platform == "win32":
        class _MemoryStatusEx(ctypes.Structure):
            _fields_ = (
                ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            )

        status = _MemoryStatusEx()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise ResourceAdmissionError("direct physical-memory limit measurement failed")
        return int(status.total_physical)
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        pages = int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise ResourceAdmissionError("direct physical-memory limit measurement failed") from error
    total = page_size * pages
    if total <= 0:
        raise ResourceAdmissionError("direct physical-memory limit measurement failed")
    return total


def _peak_working_set_bytes() -> int:
    if sys.platform == "win32":
        from ctypes import wintypes

        class _ProcessMemoryCounters(ctypes.Structure):
            _fields_ = (
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
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        ):
            raise ResourceAdmissionError(
                f"direct process peak working-set measurement failed: {ctypes.get_last_error()}"
            )
        return int(counters.PeakWorkingSetSize)
    try:
        import resource

        observed = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (ImportError, OSError, ValueError) as error:
        raise ResourceAdmissionError("direct process peak RSS measurement failed") from error
    return observed if sys.platform == "darwin" else observed * 1024


def _atomic_create_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=False, exist_ok=True)
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        observe_atomic_scratch(temporary)
        os.link(temporary, path)
    except FileExistsError as error:
        raise ResourceAdmissionError("resource receipt already exists") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _direction_resource_assessment(
    *, root: Path, scratch_root: Path | None, started_at: float,
    projected_durable_bytes: int = 0, projected_scratch_bytes: int = 0,
    memory_receipt: dict[str, object] | None = None,
) -> dict[str, object]:
    elapsed = time.perf_counter() - started_at
    peak_rss = _peak_working_set_bytes()
    scratch_bytes = 0 if scratch_root is None else _recursive_file_bytes(scratch_root)
    durable_bytes = _recursive_file_bytes(root)
    largest_artifact_bytes = max(
        _largest_file_bytes(root),
        0 if scratch_root is None else _largest_file_bytes(scratch_root),
    )
    tracker = _ACTIVE_SCRATCH_TRACKER
    invocation_peak = 0 if tracker is None else tracker.invocation_peak_bytes
    prior_cumulative_peak = (
        _prior_attempt_scratch_peak(root)
        if tracker is None else tracker.attempt_cumulative_peak_bytes
    )
    observed_scratch_peak_bytes = max(scratch_bytes, invocation_peak)
    attempt_cumulative_peak = max(prior_cumulative_peak, observed_scratch_peak_bytes)
    scratch_envelope_bytes = max(attempt_cumulative_peak, projected_scratch_bytes)
    if tracker is not None:
        tracker.attempt_cumulative_peak_bytes = attempt_cumulative_peak
    disk_parent = root.parent
    disk_free = shutil.disk_usage(disk_parent).free
    reasons: list[str] = []
    if elapsed > _WALL_SECONDS_CEILING:
        reasons.append("wall_seconds_exceeded")
    if peak_rss > _PEAK_RSS_BYTES_CEILING:
        reasons.append("peak_rss_bytes_exceeded")
    if scratch_envelope_bytes > _SCRATCH_BYTES_CEILING:
        reasons.append("scratch_bytes_exceeded")
    if durable_bytes + projected_durable_bytes > _DURABLE_BYTES_CEILING:
        reasons.append("durable_bytes_exceeded")
    if disk_free < _SCRATCH_BYTES_CEILING + _DURABLE_BYTES_CEILING:
        reasons.append("disk_free_below_projection")
    capacity: dict[str, object] = {
        "workers": 1,
        "threads_per_worker": 1,
        "estimated_wall_seconds": 300,
        "estimated_peak_bytes": _PEAK_RSS_BYTES_CEILING,
    }
    if memory_receipt is not None:
        effective_available = memory_receipt.get("effective_available_bytes")
        cgroup_limit = memory_receipt.get("cgroup_memory_max_bytes")
        if isinstance(effective_available, bool) or not isinstance(effective_available, int):
            reasons.append("effective_available_memory_missing")
        else:
            total_memory = _physical_total_memory_bytes()
            effective_limit = (
                min(total_memory, cgroup_limit)
                if isinstance(cgroup_limit, int) and not isinstance(cgroup_limit, bool)
                else total_memory
            )
            reserve = max(4 * 1024**3, (effective_limit + 4) // 5)
            adjusted_peak = (_PEAK_RSS_BYTES_CEILING * 5) // 4
            capacity.update({
                "effective_limit_bytes": effective_limit,
                "effective_available_bytes": effective_available,
                "reserve_bytes": reserve,
                "adjusted_peak_bytes": adjusted_peak,
                "memory_safe": effective_available >= reserve + adjusted_peak,
            })
            if effective_available < reserve + adjusted_peak:
                reasons.append("shared_reserve_and_peak_formula_failed")
    value = {
        "schema": _DIRECTION_RESOURCE_SCHEMA,
        "wall_seconds_ceiling": _WALL_SECONDS_CEILING,
        "peak_rss_bytes_ceiling": _PEAK_RSS_BYTES_CEILING,
        "scratch_bytes_ceiling": _SCRATCH_BYTES_CEILING,
        "durable_bytes_ceiling": _DURABLE_BYTES_CEILING,
        "wall_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "scratch_bytes": scratch_bytes,
        "largest_artifact_bytes": largest_artifact_bytes,
        "observed_scratch_peak_bytes": observed_scratch_peak_bytes,
        "invocation_scratch_peak_bytes": invocation_peak,
        "attempt_cumulative_scratch_peak_bytes": attempt_cumulative_peak,
        "scratch_envelope_bytes": scratch_envelope_bytes,
        "projected_scratch_bytes": projected_scratch_bytes,
        "durable_bytes": durable_bytes,
        "projected_durable_bytes": projected_durable_bytes,
        "disk_free_bytes": disk_free,
        "passed": not reasons,
        "failure_reasons": reasons,
        "capacity": capacity,
    }
    return value


def _invalid_evidence_path(root: Path) -> Path:
    if root.exists():
        return root / "invalid-evidence.json"
    return root.parent / f".{root.name}.invalid-evidence.json"


def _record_invalid_evidence(
    *, root: Path, stage: str, assessment: dict[str, object],
) -> None:
    path = _invalid_evidence_path(root)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ResourceAdmissionError("existing invalid-evidence fact is unreadable") from error
        if not isinstance(existing, dict) or existing.get("schema") != (
            "SCDMP_FCEOV_INVALID_EVIDENCE_V1"
        ):
            raise ResourceAdmissionError("existing invalid-evidence fact differs")
        return
    payload = {
        "schema": "SCDMP_FCEOV_INVALID_EVIDENCE_V1",
        "stage": stage,
        "disposition": "INVALID_EVIDENCE",
        "scientific_polarity": False,
        "failure_reasons": assessment.get("failure_reasons"),
        "resource_assessment": assessment,
    }
    if _contains_forbidden_receipt_key(payload):
        raise ResourceAdmissionError("invalid-evidence fact contains forbidden fields")
    _atomic_create_json(path, payload)


def _load_invalid_evidence(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError("terminal invalid-evidence fact is unreadable") from error
    required = {
        "schema", "stage", "disposition", "scientific_polarity",
        "failure_reasons", "resource_assessment",
    }
    if (
        not isinstance(value, dict)
        or set(value) != required
        or value.get("schema") != "SCDMP_FCEOV_INVALID_EVIDENCE_V1"
        or value.get("disposition") != "INVALID_EVIDENCE"
        or value.get("scientific_polarity") is not False
        or not isinstance(value.get("stage"), str)
        or not isinstance(value.get("failure_reasons"), list)
        or not value.get("failure_reasons")
        or not isinstance(value.get("resource_assessment"), dict)
        or value["resource_assessment"].get("passed") is not False
        or _contains_forbidden_receipt_key(value)
    ):
        raise PreflightError("terminal invalid-evidence fact differs")
    return value


def _enforce_direction_resources(
    *, stage: str, root: Path, scratch_root: Path | None, started_at: float,
    receipt: Path | None = None, projected_durable_bytes: int = 0,
    projected_scratch_bytes: int = 0,
    memory_receipt: dict[str, object] | None = None,
    terminal_on_failure: bool = False,
) -> dict[str, object]:
    try:
        assessment = _direction_resource_assessment(
            root=root, scratch_root=scratch_root, started_at=started_at,
            projected_durable_bytes=projected_durable_bytes,
            projected_scratch_bytes=projected_scratch_bytes,
            memory_receipt=memory_receipt,
        )
    except Exception as error:
        assessment = {
            "schema": _DIRECTION_RESOURCE_SCHEMA,
            "passed": False,
            "failure_reasons": ["resource_measurement_failed"],
            "measurement_error_type": type(error).__name__,
        }
        if terminal_on_failure:
            _record_invalid_evidence(root=root, stage=stage, assessment=assessment)
        raise ResourceAdmissionError(
            f"direction resource measurement failed at stage {stage}"
        ) from error
    value = {"stage": stage, **assessment}
    if _contains_forbidden_receipt_key(value):
        raise ResourceAdmissionError("direction resource receipt contains forbidden fields")
    if receipt is not None:
        _atomic_create_json(receipt, value)
    if value["passed"] is not True:
        # A refusal before result-bearing work is a recoverable no-work
        # condition at the same master/frontier.  Only telemetry observed
        # after a stage has executed can terminally invalidate the attempt.
        if terminal_on_failure:
            _record_invalid_evidence(root=root, stage=stage, assessment=value)
        raise ResourceAdmissionError(
            f"direction resource ceiling refused stage {stage}: "
            f"{','.join(value['failure_reasons'])}"
        )
    return value


def _configure_numerical_runtime() -> None:
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError as error:
        if torch.get_num_interop_threads() != 1:
            raise PreflightError("single-thread Torch inter-op control could not engage") from error
    torch.use_deterministic_algorithms(True)
    if (
        torch.get_num_threads() != 1
        or torch.get_num_interop_threads() != 1
        or not torch.are_deterministic_algorithms_enabled()
    ):
        raise PreflightError("deterministic single-thread Torch runtime controls did not engage")


def _contains_forbidden_receipt_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            any(token in str(key).lower() for token in _FORBIDDEN_RECEIPT_KEYS)
            or _contains_forbidden_receipt_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_receipt_key(item) for item in value)
    return False


def admit_memory(receipt: str | Path) -> dict[str, object]:
    """Run the repository-wide 4 GiB admission and validate its direct receipt."""

    path = Path(receipt)
    completed = subprocess.run(
        [sys.executable, str(_RESOURCE_SCRIPT), "admit-memory", "--out", str(path)],
        capture_output=True, text=True, check=False,
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResourceAdmissionError("4 GiB admission did not produce a readable receipt") from error
    if not isinstance(value, dict) or _contains_forbidden_receipt_key(value):
        raise ResourceAdmissionError("4 GiB admission receipt fields differ")
    required = {
        "minimum_available_bytes", "available_physical_bytes", "effective_available_bytes",
        "physical_floor_pass", "effective_floor_pass", "passed",
    }
    if not required <= set(value) or value["minimum_available_bytes"] != 4 * 1024**3:
        raise ResourceAdmissionError("4 GiB admission receipt contract differs")
    if completed.returncode != 0 or value["passed"] is not True:
        raise ResourceAdmissionError("4 GiB memory admission refused before result work")
    if (
        value["physical_floor_pass"] is not True
        or value["effective_floor_pass"] is not True
        or not isinstance(value["available_physical_bytes"], int)
        or not isinstance(value["effective_available_bytes"], int)
        or value["available_physical_bytes"] < 4 * 1024**3
        or value["effective_available_bytes"] < 4 * 1024**3
    ):
        raise ResourceAdmissionError("4 GiB memory admission receipt is internally inconsistent")
    return value


def assess_run(receipt: str | Path) -> dict[str, object]:
    """Run and validate the shared prospective one-worker FCEOV assessment."""

    path = Path(receipt)
    completed = subprocess.run(
        [
            sys.executable, str(_RESOURCE_SCRIPT), "assess-run",
            "--direction", _ASSESS_DIRECTION,
            "--run-id", _ASSESS_RUN_ID,
            "--workers", "1",
            "--threads-per-worker", "1",
            "--estimated-wall-seconds", "300",
            "--estimated-peak-gib", "1",
            "--basis", "frozen SCDMP FCEOV replacement resource envelope",
            "--out", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResourceAdmissionError("shared assess-run did not produce a readable receipt") from error
    if (
        completed.returncode != 0
        or not isinstance(value, dict)
        or value.get("memory_safe") is not True
        or value.get("memory_floor_pass") is not True
        or value.get("physical_floor_pass") is not True
        or value.get("effective_floor_pass") is not True
        or value.get("minimum_available_bytes") != 4 * 1024**3
        or _contains_forbidden_receipt_key(value)
    ):
        raise ResourceAdmissionError("shared assess-run refused before result work")
    expected = {
        "direction_id": _ASSESS_DIRECTION,
        "run_id": _ASSESS_RUN_ID,
        "workers": 1,
        "threads_per_worker": 1,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ResourceAdmissionError("shared assess-run receipt contract differs")
    estimate = value.get("estimate")
    if (
        not isinstance(estimate, dict)
        or estimate.get("wall_seconds") != 300
        or estimate.get("peak_memory_gib") != 1.0
        or estimate.get("basis") != "frozen SCDMP FCEOV replacement resource envelope"
    ):
        raise ResourceAdmissionError("shared assess-run peak estimate differs")
    return value


def _admit_memory_or_record(
    *, root: Path, receipt: Path, stage: str,
) -> dict[str, object]:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    try:
        return admit_memory(receipt)
    except ResourceAdmissionError:
        # The shared admission runs before the corresponding native work.  Its
        # refusal preserves the same fixed master/frontier and never creates a
        # scientific INVALID disposition.
        raise


def run_preflight(*, manifest: str | Path, result_root: str | Path) -> dict[str, object]:
    """Report the consumed-object tombstone without inspecting either argument."""

    # Deliberately do not coerce, resolve, read, or validate either supplied
    # path.  Preflight is now an effect-free lifecycle query, not an execution
    # admission seam.
    return {
        "lifecycle_status": LIFECYCLE_STATUS,
        "result_command_status": RESULT_COMMAND_STATUS,
        "message": TERMINAL_TOMBSTONE_MESSAGE,
    }


def run_result(*, manifest: str | Path, result_root: str | Path) -> TerminalFact:
    """Reject every result invocation before inspecting its arguments."""

    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)


def _load_consumed_run_record_bytes(path: Path) -> bytes:
    """Validate historical static controls without consulting the live runtime."""

    try:
        encoded = path.read_bytes()
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("consumed run record cannot be loaded") from error
    expected_top = {
        "schema": "SCDMP_FCEOV_RUN_RECORD_V4",
        "phase": PHASE,
        "checkpoint_update": CHECKPOINT_UPDATE,
        "foundation_updates": 160,
        "episodes_per_update": 12,
        "competence_missions": 120,
        "panel_width": PANEL_WIDTH,
        "actions": [0, 10, 12],
        "resources": dict(RESOURCE_MAXIMA),
    }
    if not isinstance(value, dict) or set(value) != {*expected_top, "runtime"}:
        raise ArtifactContractError("consumed run record fields differ")
    if any(value.get(key) != expected for key, expected in expected_top.items()):
        raise ArtifactContractError("consumed run record static contract differs")
    runtime = value.get("runtime")
    if not isinstance(runtime, dict) or set(runtime) != {
        "python", "torch", "device", "torch_threads", "torch_interop_threads",
        "deterministic_algorithms", "native_batch_widths",
    }:
        raise ArtifactContractError("consumed run record runtime fields differ")
    if any(
        not isinstance(runtime.get(name), str)
        or not runtime[name].strip()
        or any(ord(character) < 32 for character in runtime[name])
        for name in ("python", "torch")
    ) or {
        "device": runtime.get("device"),
        "torch_threads": runtime.get("torch_threads"),
        "torch_interop_threads": runtime.get("torch_interop_threads"),
        "deterministic_algorithms": runtime.get("deterministic_algorithms"),
        "native_batch_widths": runtime.get("native_batch_widths"),
    } != {
        "device": "cpu",
        "torch_threads": 1,
        "torch_interop_threads": 1,
        "deterministic_algorithms": True,
        "native_batch_widths": {
            "training": 12, "competence": 120, "panel_full": 144, "panel_final": 60,
        },
    }:
        raise ArtifactContractError("consumed run record runtime controls differ")
    return encoded


def validate_consumed_artifact(
    *, artifact: str | Path, result_root: str | Path,
) -> dict[str, object]:
    """Read-only validation of the already consumed canonical .3 final bundle."""

    root = _require_canonical_result_root(result_root)
    artifact_path = Path(artifact).resolve(strict=False)
    expected_artifact = (root / "final-bundle.json").resolve(strict=False)
    if os.path.normcase(str(artifact_path)) != os.path.normcase(str(expected_artifact)):
        raise PreflightError("consumed artifact is not the canonical .3 final bundle")
    if not root.is_dir() or not artifact_path.is_file():
        raise PreflightError("consumed .3 final bundle is missing")

    _validate_existing_root_shape(root)
    # The manifest and snapshot are historical evidence.  Validate their
    # persisted schemas/direct bytes, but do not compare the old snapshot with
    # the now-tombstoned live runner source.
    load_consumed_source_manifest(root / "source-manifest.json")
    run_record_bytes = _load_consumed_run_record_bytes(root / "run-record.json")
    source_snapshot = load_source_native_snapshot(root / "source-native-snapshot.json")
    master = load_rng_master(root / "rng-master.bin")
    _validate_final_publication_receipt(root)
    _validate_end_receipt(root, "final-publication")
    fact = load_final_bundle(
        artifact_path,
        expected_result_root=str(root),
        expected_rng_master=master,
        expected_run_record_bytes=run_record_bytes,
        expected_source_native_snapshot=source_snapshot,
    )
    return {
        "validated": True,
        "lifecycle_status": LIFECYCLE_STATUS,
        "result_command_status": RESULT_COMMAND_STATUS,
        "artifact": str(artifact_path),
        "disposition": fact.disposition,
        "panel_complete": fact.panel_complete,
    }


def _next_admission_path(root: Path, stage: str) -> Path:
    existing = tuple(root.glob(f"resource-admission-{stage}-*.json"))
    indices = []
    for path in existing:
        try:
            indices.append(int(path.stem.rsplit("-", 1)[1]))
        except (IndexError, ValueError) as error:
            raise PreflightError("resource admission receipt inventory differs") from error
    return root / f"resource-admission-{stage}-{max(indices, default=-1) + 1:04d}.json"


def _next_direction_resource_path(root: Path, stage: str) -> Path:
    existing = tuple(root.glob(f"direction-resource-{stage}-*.json"))
    indices = []
    for path in existing:
        try:
            indices.append(int(path.stem.rsplit("-", 1)[1]))
        except (IndexError, ValueError) as error:
            raise PreflightError("direction resource receipt inventory differs") from error
    return root / f"direction-resource-{stage}-{max(indices, default=-1) + 1:04d}.json"


def _next_sibling_receipt(root: Path, family: str) -> Path:
    prefix = f".{root.name}.{family}-"
    existing = tuple(root.parent.glob(f"{prefix}*.json"))
    indices = []
    for path in existing:
        try:
            indices.append(int(path.stem.rsplit("-", 1)[1]))
        except (IndexError, ValueError) as error:
            raise PreflightError("sibling resource receipt inventory differs") from error
    return root.parent / f"{prefix}{max(indices, default=-1) + 1:04d}.json"


def _validate_existing_root_shape(root: Path) -> None:
    if not root.is_dir():
        raise PreflightError("existing result-root is not a directory")
    fixed = {
        "source-manifest.json", "source-native-snapshot.json", "rng-master.bin", "run-record.json",
        "foundation.checkpoint.pt", "resume-witness.json", "foundation-gate.json",
        "panel-frontier.json", "terminal-fact.json", "final-bundle.json",
        "final-bundle.pending.json", "invalid-evidence.json",
    }
    for path in root.iterdir():
        if path.name in fixed or path.match("panel-slice-[0-9][0-9][0-9].json") or path.match(
            "resource-admission-*.json"
        ) or path.match(
            "direction-resource-*.json"
        ):
            continue
        raise PreflightError(f"existing result-root contains an unrecognized entry: {path.name}")
    names = {path.name for path in root.iterdir()}
    required = {
        "source-manifest.json", "source-native-snapshot.json", "rng-master.bin", "run-record.json",
    }
    if not required <= names:
        raise PreflightError(
            "existing result-root lacks the direct V3 shape before the fixed resume seam"
        )
    terminal_markers = names & {
        "terminal-fact.json", "final-bundle.json", "invalid-evidence.json",
    }
    if len(terminal_markers) > 1:
        raise PreflightError("terminal nonpass, invalid evidence, and final bundle cannot coexist")


def _validate_staging_shape(staging: Path) -> None:
    if not staging.is_dir():
        raise PreflightError("deterministic staging path is not a directory")
    allowed = {
        "source-manifest.json", "source-native-snapshot.json", "rng-master.bin", "run-record.json",
    }
    for path in staging.iterdir():
        if path.name in allowed or path.match("direction-resource-init-*.json"):
            continue
        raise PreflightError(f"staging root contains an unrecognized entry: {path.name}")


def _manifest_bytes_and_value(manifest: str | Path) -> tuple[bytes, object]:
    requested = load_source_manifest(manifest)
    try:
        direct_bytes = Path(manifest).read_bytes()
    except OSError as error:
        raise PreflightError("direct source manifest bytes cannot be loaded") from error
    return direct_bytes, requested


def _validate_source_manifest_file(
    manifest: str | Path, persisted_path: Path,
) -> bytes:
    requested_bytes, requested = _manifest_bytes_and_value(manifest)
    persisted = load_source_manifest(persisted_path)
    try:
        persisted_bytes = persisted_path.read_bytes()
    except OSError as error:
        raise PreflightError("persisted source manifest bytes cannot be loaded") from error
    if requested != persisted or requested_bytes != persisted_bytes:
        raise PreflightError("persisted source manifest differs by type or direct bytes")
    return persisted_bytes


def _init_seam(name: str) -> None:
    """TEST seam after each durable initialization atom; production is a no-op."""


def _publish_staging_root(staging: Path, root: Path) -> None:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    if root.exists():
        raise PreflightError("canonical result-root appeared during staging initialization")
    staging.rename(root)


def _initialize_fresh_root(
    *, manifest: str | Path, root: Path, started_at: float,
) -> tuple[bytes, SourceNativeSnapshot, bytes]:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    staging = _staging_root(root)
    if staging.exists():
        _validate_staging_shape(staging)
    else:
        staging.mkdir(parents=False, exist_ok=False)

    master_path = staging / "rng-master.bin"
    if master_path.exists():
        master = load_rng_master(master_path)
    else:
        generated = fresh_master()
        write_rng_master(master_path, generated)
        master = load_rng_master(master_path)
        if master != generated:
            raise PreflightError("persisted RNG master differs immediately after creation")
        del generated
    _init_seam("rng-master")

    source_manifest_path = staging / "source-manifest.json"
    if not source_manifest_path.exists():
        write_source_manifest(source_manifest_path)
    _validate_source_manifest_file(manifest, source_manifest_path)
    _init_seam("source-manifest")

    snapshot_path = staging / "source-native-snapshot.json"
    if snapshot_path.exists():
        snapshot = load_source_native_snapshot(snapshot_path)
        compare_source_native_snapshot(snapshot)
    else:
        snapshot = capture_source_native_snapshot()
        write_source_native_snapshot(snapshot_path, snapshot)
        snapshot = load_source_native_snapshot(snapshot_path)
        compare_source_native_snapshot(snapshot)
    _init_seam("source-native-snapshot")

    run_record_path = staging / "run-record.json"
    if not run_record_path.exists():
        write_run_record(run_record_path, build_run_record())
    load_run_record(run_record_path)
    run_record_bytes = run_record_path.read_bytes()
    _init_seam("run-record")

    _enforce_direction_resources(
        stage="init", root=root, scratch_root=staging, started_at=started_at,
        receipt=_next_direction_resource_path(staging, "init"),
    )
    _init_seam("resource-assessment")
    _publish_staging_root(staging, root)
    return master, snapshot, run_record_bytes


def _validate_persisted_contract(
    manifest: str | Path, root: Path,
) -> tuple[SourceNativeSnapshot, bytes]:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    _validate_source_manifest_file(manifest, root / "source-manifest.json")
    load_run_record(root / "run-record.json")
    run_record_bytes = (root / "run-record.json").read_bytes()
    snapshot = load_source_native_snapshot(root / "source-native-snapshot.json")
    compare_source_native_snapshot(snapshot)
    return snapshot, run_record_bytes


def _train_and_restore_foundation(
    root: Path, master: bytes,
) -> tuple[object, AddressRNG]:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    source = AddressRNG(master)
    checkpoint_path = root / "foundation.checkpoint.pt"
    witness_path = root / "resume-witness.json"

    if checkpoint_path.exists() and witness_path.exists():
        model = materialize_foundation(source)
        optimizer = ExactAdamW(tuple(model.named_parameters()))
        checkpoint = load_checkpoint(checkpoint_path, model, optimizer)
        if checkpoint.get("rng_master") != master:
            raise PreflightError("resume checkpoint binds a different RNG master")
        restore_checkpoint(checkpoint, model, optimizer)
        load_resume_witness(witness_path)
        return freeze_foundation(model), source

    if witness_path.exists() and not checkpoint_path.exists():
        raise PreflightError("resume witness exists without the final checkpoint")

    uninterrupted_model = materialize_foundation(source)
    uninterrupted_optimizer = ExactAdamW(tuple(uninterrupted_model.named_parameters()))
    for update in range(1, 161):
        observed = train_one_update(uninterrupted_model, uninterrupted_optimizer, source, update=update)
        if observed.update != update or observed.episodes_complete != 12:
            raise PreflightError("foundation training update did not complete exactly")
    if not checkpoint_path.exists():
        write_checkpoint(
            checkpoint_path, uninterrupted_model, uninterrupted_optimizer,
            completed_updates=CHECKPOINT_UPDATE, rng_master=master,
        )

    restored_source = AddressRNG(master)
    restored_model = materialize_foundation(restored_source)
    restored_optimizer = ExactAdamW(tuple(restored_model.named_parameters()))
    checkpoint = load_checkpoint(checkpoint_path, restored_model, restored_optimizer)
    restore_checkpoint(checkpoint, restored_model, restored_optimizer)
    witness = observe_resume_equality(
        checkpoint, uninterrupted_model, uninterrupted_optimizer, restored_model,
        restored_optimizer, persisted_master=master,
    )
    if witness.schema != RESUME_WITNESS_SCHEMA:
        raise PreflightError("resume witness schema differs")
    if not witness_path.exists():
        write_resume_witness(witness_path, witness)
    else:
        load_resume_witness(witness_path)
    return freeze_foundation(restored_model), restored_source


def _load_or_execute_foundation_gate(root: Path, frozen: object, source: AddressRNG):
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    gate_path = root / "foundation-gate.json"
    if gate_path.exists():
        return load_foundation_gate(gate_path)
    records = execute_native_competence(frozen, source)  # type: ignore[arg-type]
    gate = analyze_competence(records)
    write_foundation_gate(gate_path, gate, records)
    return gate, tuple(records)


def _reconcile_frontier(root: Path, completed: int) -> None:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    path = root / "panel-frontier.json"
    expected = build_panel_frontier(completed)
    if path.exists():
        observed = load_panel_frontier(path)
        if observed.completed_slices > completed:
            raise PreflightError("typed frontier advances beyond durable complete slices")
        if observed == expected:
            return
    write_panel_frontier(path, expected)


def _prepare_and_publish_final(
    *, root: Path, master: bytes, run_record_bytes: bytes,
    source_snapshot: SourceNativeSnapshot, records: Sequence[object], cells: Sequence[object],
    panel_analysis: object, started_at: float,
) -> TerminalFact:
    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    _enforce_direction_resources(
        stage="pre-final-prepare", root=root, scratch_root=None, started_at=started_at,
        terminal_on_failure=True,
    )
    prepared = prepare_final_bundle(
        competence_records=records, panel_cells=cells, panel_analysis=panel_analysis,
        resolved_result_root=str(root), rng_master=master,
        run_record_bytes=run_record_bytes, source_native_snapshot=source_snapshot,
    )
    pending_path = root / "final-bundle.pending.json"
    if pending_path.exists():
        try:
            pending_bytes = pending_path.read_bytes()
        except OSError as error:
            raise PreflightError("pending final bundle cannot be loaded") from error
        if pending_bytes != prepared.encoded:
            raise PreflightError("pending final bundle differs from the prepared direct bytes")
    else:
        write_prepared_final_bundle(pending_path, prepared)
    _enforce_direction_resources(
        stage="pre-final-publication", root=root, scratch_root=pending_path,
        started_at=started_at,
        receipt=_next_direction_resource_path(root, "pre-final-publication"),
        terminal_on_failure=True,
    )
    final_path = root / "final-bundle.json"
    if final_path.exists():
        raise PreflightError("atomic final bundle already exists before publication")
    try:
        os.link(pending_path, final_path)
    except FileExistsError as error:
        raise PreflightError("atomic final bundle appeared during publication") from error
    except OSError as error:
        raise PreflightError("atomic final bundle publication failed") from error
    try:
        pending_path.unlink()
    except OSError:
        # The canonical hard link is already durable and the passing resource
        # receipt precedes it; a redundant pending link is safe to validate on reload.
        pass
    if final_path.exists() is not True:
        raise PreflightError("atomic final bundle was not published")
    _enforce_direction_resources(
        stage="final-publication", root=root,
        scratch_root=pending_path if pending_path.exists() else None, started_at=started_at,
        receipt=_next_direction_resource_path(root, "final-publication"),
        terminal_on_failure=True,
    )
    return prepared.fact


def _validate_end_receipt(root: Path, stage: str) -> dict[str, object]:
    receipts = tuple(root.glob(f"direction-resource-{stage}-*.json"))
    indexed: list[tuple[int, Path]] = []
    for path in receipts:
        try:
            indexed.append((int(path.stem.rsplit("-", 1)[1]), path))
        except (IndexError, ValueError) as error:
            raise PreflightError(f"{stage} resource receipt inventory differs") from error
    if not indexed:
        raise PreflightError(f"{stage} lacks a passing end-of-invocation resource receipt")
    try:
        value = json.loads(max(indexed)[1].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"{stage} resource receipt cannot be loaded") from error
    if (
        not isinstance(value, dict)
        or value.get("schema") != _DIRECTION_RESOURCE_SCHEMA
        or value.get("stage") != stage
        or value.get("passed") is not True
        or value.get("failure_reasons") != []
        or isinstance(value.get("attempt_cumulative_scratch_peak_bytes"), bool)
        or not isinstance(value.get("attempt_cumulative_scratch_peak_bytes"), int)
        or value["attempt_cumulative_scratch_peak_bytes"] < 0
        or value["attempt_cumulative_scratch_peak_bytes"] > _SCRATCH_BYTES_CEILING
        or not isinstance(value.get("peak_rss_bytes"), int)
        or value["peak_rss_bytes"] < 0
        or value["peak_rss_bytes"] > _PEAK_RSS_BYTES_CEILING
        or not isinstance(value.get("wall_seconds"), (int, float))
        or value["wall_seconds"] < 0
        or value["wall_seconds"] > _WALL_SECONDS_CEILING
        or not isinstance(value.get("durable_bytes"), int)
        or value["durable_bytes"] < 0
        or value["durable_bytes"] > _DURABLE_BYTES_CEILING
        or _contains_forbidden_receipt_key(value)
    ):
        raise PreflightError(f"{stage} resource receipt differs")
    return value


def _validate_final_publication_receipt(root: Path) -> dict[str, object]:
    receipts = tuple(root.glob("direction-resource-pre-final-publication-*.json"))
    indexed: list[tuple[int, Path]] = []
    for path in receipts:
        try:
            indexed.append((int(path.stem.rsplit("-", 1)[1]), path))
        except (IndexError, ValueError) as error:
            raise PreflightError("final publication resource receipt inventory differs") from error
    if not indexed:
        raise PreflightError("final bundle lacks a passing pre-publication resource receipt")
    path = max(indexed)[1]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError("final publication resource receipt cannot be loaded") from error
    final_path = root / "final-bundle.json"
    try:
        final_size = final_path.stat().st_size
    except OSError as error:
        raise PreflightError("final bundle size cannot be measured") from error
    if (
        not isinstance(value, dict)
        or value.get("schema") != _DIRECTION_RESOURCE_SCHEMA
        or value.get("stage") != "pre-final-publication"
        or value.get("passed") is not True
        or value.get("failure_reasons") != []
        or value.get("scratch_bytes") != final_size
        or _contains_forbidden_receipt_key(value)
    ):
        raise PreflightError("final publication resource receipt differs")
    pending_path = root / "final-bundle.pending.json"
    if pending_path.exists():
        try:
            if pending_path.read_bytes() != final_path.read_bytes():
                raise PreflightError("pending and canonical final bundle direct bytes differ")
        except OSError as error:
            raise PreflightError("redundant pending final bundle cannot be loaded") from error
    return value


def _execute_result_pipeline_body(
    *, manifest: str | Path, result_root: str | Path
) -> TerminalFact:
    """Disabled historical implementation; the scientific object is consumed."""

    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    root = _require_canonical_result_root(result_root)
    # The frozen wall ceiling includes cold interpreter/import time, so use the
    # OS process creation origin rather than the moment this function is called.
    started_at = _PROCESS_STARTED_AT
    fresh = not root.exists()
    if fresh:
        sibling_invalid = _invalid_evidence_path(root)
        if sibling_invalid.exists():
            _load_invalid_evidence(sibling_invalid)
            raise PreflightError("terminal sibling invalid evidence forbids replacement reentry")
        report = run_preflight(manifest=manifest, result_root=root)
        if (
            report.get("resources") != dict(RESOURCE_MAXIMA)
            or report.get("resource_envelope") != dict(RESOURCE_ENVELOPE)
        ):
            raise PreflightError("internal execution resource report differs after direct preflight")
        assess_run(_next_sibling_receipt(root, "shared-assess-run-launch"))
        memory_receipt = _admit_memory_or_record(
            root=root, receipt=_next_sibling_receipt(root, "resource-admission-launch"),
            stage="launch-memory",
        )
        _enforce_direction_resources(
            stage="launch", root=root, scratch_root=None, started_at=started_at,
            receipt=_next_sibling_receipt(root, "direction-resource-launch"),
            memory_receipt=memory_receipt,
        )
        _configure_numerical_runtime()
        if _ACTIVE_SCRATCH_TRACKER is not None:
            _ACTIVE_SCRATCH_TRACKER.scientific_state_started = True
        master, source_snapshot, run_record_bytes = _initialize_fresh_root(
            manifest=manifest, root=root, started_at=started_at,
        )
    else:
        _validate_existing_root_shape(root)
        invalid_path = root / "invalid-evidence.json"
        if invalid_path.exists():
            _load_invalid_evidence(invalid_path)
            raise PreflightError("terminal invalid evidence forbids resume or final publication")
        source_snapshot, run_record_bytes = _validate_persisted_contract(manifest, root)
        terminal_path = root / "terminal-fact.json"
        if terminal_path.exists():
            load_rng_master(root / "rng-master.bin")
            fact, _ = load_foundation_nonpass_terminal(terminal_path)
            _validate_end_receipt(root, "foundation-nonpass-complete")
            return fact
        master = load_rng_master(root / "rng-master.bin")
        if (root / "final-bundle.json").exists():
            _validate_final_publication_receipt(root)
            _validate_end_receipt(root, "final-publication")
            return load_final_bundle(
                root / "final-bundle.json",
                expected_result_root=str(root), expected_rng_master=master,
                expected_run_record_bytes=run_record_bytes,
                expected_source_native_snapshot=source_snapshot,
            )
        if _ACTIVE_SCRATCH_TRACKER is not None:
            _ACTIVE_SCRATCH_TRACKER.scientific_state_started = True
        memory_receipt = _admit_memory_or_record(
            root=root, receipt=_next_admission_path(root, "resume"), stage="resume-memory",
        )
        _enforce_direction_resources(
            stage="resume", root=root, scratch_root=None, started_at=started_at,
            receipt=_next_direction_resource_path(root, "resume"),
            memory_receipt=memory_receipt,
        )
        _configure_numerical_runtime()
        validate_live_run_record_runtime(root / "run-record.json")

    frozen, source = _train_and_restore_foundation(root, master)
    _enforce_direction_resources(
        stage="foundation", root=root, scratch_root=None, started_at=started_at,
        receipt=_next_direction_resource_path(root, "foundation"),
        terminal_on_failure=True,
    )
    gate, records = _load_or_execute_foundation_gate(root, frozen, source)
    _enforce_direction_resources(
        stage="competence", root=root, scratch_root=None, started_at=started_at,
        receipt=_next_direction_resource_path(root, "competence"),
        terminal_on_failure=True,
    )
    if not gate.passed:
        fact = TerminalFact(
            TERMINAL_FACT_SCHEMA, Disposition.FOUNDATION_NONPASS.value, gate, False,
        )
        terminal_path = root / "terminal-fact.json"
        if terminal_path.exists():
            raise PreflightError("foundation nonpass terminal fact already exists")
        write_terminal_fact(terminal_path, fact, competence_records=records)
        _enforce_direction_resources(
            stage="foundation-nonpass-complete", root=root, scratch_root=None,
            started_at=started_at,
            receipt=_next_direction_resource_path(root, "foundation-nonpass-complete"),
            terminal_on_failure=True,
        )
        return fact

    if (root / "terminal-fact.json").exists():
        raise PreflightError("passing foundation cannot coexist with a terminal nonpass fact")
    slices = build_panel_slices()
    durable_slices = load_contiguous_panel_slices(root)
    _reconcile_frontier(root, len(durable_slices))
    for panel_slice in slices[len(durable_slices):]:
        # This receipt is immediately adjacent to the only native result-bearing slice work.
        slice_memory_receipt = _admit_memory_or_record(
            root=root,
            receipt=_next_admission_path(root, f"slice-{panel_slice.index:03d}"),
            stage=f"slice-{panel_slice.index:03d}-memory",
        )
        _enforce_direction_resources(
            stage=f"slice-{panel_slice.index:03d}-before", root=root, scratch_root=None,
            started_at=started_at,
            receipt=_next_direction_resource_path(root, f"slice-{panel_slice.index:03d}-before"),
            memory_receipt=slice_memory_receipt,
        )
        tapes = materialize_disturbance_tapes(
            source, start_tape=panel_slice.start_tape, tape_count=panel_slice.tape_count,
        )
        cells = execute_native_panel_slice(frozen, tapes, panel_slice)  # type: ignore[arg-type]
        _enforce_direction_resources(
            stage=f"slice-{panel_slice.index:03d}-native", root=root, scratch_root=None,
            started_at=started_at,
            terminal_on_failure=True,
        )
        slice_path = root / f"panel-slice-{panel_slice.index:03d}.json"
        write_panel_slice(slice_path, slice_index=panel_slice.index, cells=cells)
        durable_slices = (*durable_slices, tuple(cells))
        _reconcile_frontier(root, len(durable_slices))
        _enforce_direction_resources(
            stage=f"slice-{panel_slice.index:03d}-durable", root=root, scratch_root=None,
            started_at=started_at,
            receipt=_next_direction_resource_path(root, f"slice-{panel_slice.index:03d}-durable"),
            terminal_on_failure=True,
        )

    if len(durable_slices) != PANEL_SLICE_COUNT:
        raise PreflightError("all fixed assay slices did not complete")
    cells = aggregate_panel_slices(durable_slices)
    if len(cells) != PANEL_WIDTH or not validate_complete_panel_cells(cells):
        raise PreflightError("complete fixed assay cell inventory differs")
    panel_analysis = analyze_complete_panel(cells)
    return _prepare_and_publish_final(
        root=root, master=master, run_record_bytes=run_record_bytes,
        source_snapshot=source_snapshot, records=records, cells=cells,
        panel_analysis=panel_analysis, started_at=started_at,
    )


def _execute_result_pipeline(
    *, manifest: str | Path, result_root: str | Path
) -> TerminalFact:
    """Reject internal execution bypasses before installing observers."""

    raise PreflightError(TERMINAL_TOMBSTONE_MESSAGE)

    global _ACTIVE_SCRATCH_TRACKER
    root = _require_canonical_result_root(result_root)
    if _ACTIVE_SCRATCH_TRACKER is not None:
        raise PreflightError("nested FCEOV result invocations are forbidden")
    tracker = _InvocationScratchTracker(root)
    _ACTIVE_SCRATCH_TRACKER = tracker
    set_atomic_scratch_observer(tracker.observe)
    try:
        return _execute_result_pipeline_body(manifest=manifest, result_root=root)
    finally:
        set_atomic_scratch_observer(None)
        _ACTIVE_SCRATCH_TRACKER = None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scdmp-fceov")
    parser.add_argument("--manifest")
    parser.add_argument("--result-root", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--phase", choices=(PHASE,))
    mode.add_argument("--validate-consumed-artifact")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.preflight_only:
            report = run_preflight(manifest=args.manifest, result_root=args.result_root)
            print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        elif args.validate_consumed_artifact:
            report = validate_consumed_artifact(
                artifact=args.validate_consumed_artifact, result_root=args.result_root,
            )
            print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        else:
            fact = run_result(manifest=args.manifest, result_root=args.result_root)
            print(f"FCEOV terminal disposition: {fact.disposition}")
    except (ValueError, RuntimeError, OSError) as error:
        print(f"FCEOV stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CANONICAL_RESULT_ROOT", "QUARANTINED_RESULT_ROOT",
    "QUARANTINED_REPLACEMENT_RESULT_ROOT", "PHASE", "PreflightError",
    "ResourceAdmissionError", "main",
    "run_preflight", "run_result", "validate_consumed_artifact",
]
