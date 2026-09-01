#!/usr/bin/env python3
"""Capture host resources and assess one result-bearing run.

The capture mode is deliberately observational: it never accepts a run estimate
and never makes an admission decision. ``admit-memory`` applies the fixed 4 GiB
physical/effective available-memory floor. ``assess-run`` additionally applies
the frozen HMASD reserve and peak formula to a fresh capture.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import math
import os
import platform
import re
import tempfile
import sys
import uuid
import ctypes
from pathlib import Path
from typing import Any, Mapping

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform

SCHEMA_VERSION = 1
GIB = 1024**3
KIB = 1024
MINIMUM_AVAILABLE_MEMORY_BYTES = 4 * GIB
_DIRECTION_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")

PROC_CPUINFO = Path("/proc/cpuinfo")
PROC_MEMINFO = Path("/proc/meminfo")
CGROUP_ROOT = Path("/sys/fs/cgroup")


def _utc_now() -> str:
    return (
        _datetime.datetime.now(_datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".hmasd-rsrc-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        hmasd_platform.fsync_directory(path.parent)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _parse_memory_bytes(value: Any, *, default_unit: str = "bytes") -> int | None:
    """Normalize a byte, KiB, or GiB value to integer bytes.

    ``memory.max`` uses the literal string ``max`` for an unbounded limit.  The
    parser intentionally accepts both Linux spellings (``kB`` and ``KiB``) so
    fixtures can exercise unit boundaries without depending on a live host.
    """

    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("boolean is not a memory value")
    if isinstance(value, (int, float)):
        number = float(value)
        unit = default_unit
    else:
        raw = str(value).strip()
        if raw.lower() == "max":
            return None
        match = re.fullmatch(r"([+]?(?:\d+(?:\.\d*)?|\.\d+))\s*([A-Za-z]*)", raw)
        if match is None:
            raise ValueError(f"invalid memory value: {value!r}")
        number = float(match.group(1))
        unit = match.group(2) or default_unit
    if not math.isfinite(number) or number < 0:
        raise ValueError("memory values must be finite and non-negative")
    normalized = unit.lower()
    factors = {
        "b": 1,
        "byte": 1,
        "bytes": 1,
        "k": KIB,
        "kb": KIB,
        "kib": KIB,
        "m": KIB**2,
        "mb": KIB**2,
        "mib": KIB**2,
        "g": GIB,
        "gb": GIB,
        "gib": GIB,
        "t": KIB**3,
        "tb": KIB**3,
        "tib": KIB**3,
    }
    if normalized not in factors:
        raise ValueError(f"unsupported memory unit: {unit!r}")
    return int(number * factors[normalized])


def _read_cpu() -> dict[str, Any]:
    logical = os.cpu_count() or 1
    physical_ids: set[tuple[str, str]] = set()
    physical_id: str | None = None
    core_id: str | None = None
    try:
        lines = PROC_CPUINFO.read_text(encoding="utf-8").splitlines() + [""]
    except OSError:
        lines = []
    for line in lines:
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "physical id":
            physical_id = value
        elif key == "core id":
            core_id = value
        elif not key:
            if physical_id is not None and core_id is not None:
                physical_ids.add((physical_id, core_id))
            physical_id = None
            core_id = None
    physical = len(physical_ids) or logical
    try:
        load_one = os.getloadavg()[0]
    except (AttributeError, OSError):
        load_one = 0.0
    return {
        "physical_cores": physical,
        "logical_processors": logical,
        "load_average_1m": round(max(0.0, float(load_one)), 6),
        "load_percent": round(max(0.0, float(load_one)) * 100.0 / logical, 6),
    }


def _read_meminfo() -> dict[str, Any]:
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
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

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return {}
        return {
            "MemTotal": int(status.ullTotalPhys),
            "MemAvailable": int(status.ullAvailPhys),
        }

    values: dict[str, int] = {}
    try:
        lines = PROC_MEMINFO.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        key, _, raw = line.partition(":")
        if key not in {"MemTotal", "MemAvailable"}:
            continue
        try:
            values[key] = _parse_memory_bytes(raw.strip(), default_unit="KiB") or 0
        except ValueError:
            continue
    return values


def _read_cgroup_value(name: str) -> tuple[str | None, int | None]:
    path = CGROUP_ROOT / name
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None, None
    if raw.lower() == "max":
        return raw, None
    try:
        return raw, _parse_memory_bytes(raw, default_unit="bytes")
    except ValueError:
        return raw, None


def capture_snapshot() -> dict[str, Any]:
    """Capture directly observable host and cgroup resource facts."""

    memory_values = _read_meminfo()
    max_raw, max_bytes = _read_cgroup_value("memory.max")
    current_raw, current_bytes = _read_cgroup_value("memory.current")
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_id": f"resource_{uuid.uuid4().hex}",
        "captured_at": _utc_now(),
        "host_identity": platform.node(),
        "cpu": _read_cpu(),
        "memory": {
            "measurement_source": (
                "GlobalMemoryStatusEx" if os.name == "nt" else "/proc/meminfo"
            ),
            "total_bytes": memory_values.get("MemTotal", 0),
            "available_bytes": memory_values.get("MemAvailable", 0),
            "total_gib": round(memory_values.get("MemTotal", 0) / GIB, 6),
            "available_gib": round(memory_values.get("MemAvailable", 0) / GIB, 6),
            "cgroup_memory_max_raw": max_raw,
            "cgroup_memory_max_bytes": max_bytes,
            "cgroup_memory_max_gib": None if max_bytes is None else round(max_bytes / GIB, 6),
            "cgroup_memory_current_raw": current_raw,
            "cgroup_memory_current_bytes": current_bytes,
            "cgroup_memory_current_gib": (
                None if current_bytes is None else round(current_bytes / GIB, 6)
            ),
        },
    }


def assess_memory_floor(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Assess the fixed pre-run available-memory floor without a run estimate."""

    memory = snapshot.get("memory")
    reasons: list[str] = []
    if not isinstance(memory, Mapping):
        memory = {}
        reasons.append("snapshot memory is missing")

    try:
        available_bytes = _parse_memory_bytes(
            _memory_field(memory, "available_bytes", "available_gib", "MemAvailable"),
            default_unit="bytes",
        )
        if "available_gib" in memory and "available_bytes" not in memory:
            available_bytes = _parse_memory_bytes(memory["available_gib"], default_unit="GiB")
    except ValueError as exc:
        available_bytes = None
        reasons.append(f"available physical memory is invalid: {exc}")
    if available_bytes is None or available_bytes < 0:
        available_bytes = None
        if not any(reason.startswith("available physical memory") for reason in reasons):
            reasons.append("available physical memory is unavailable")

    cgroup_max_raw = _memory_field(memory, "cgroup_memory_max_raw", "memory_max")
    cgroup_max_value = _memory_field(memory, "cgroup_memory_max_bytes", "cgroup_max_bytes")
    try:
        if cgroup_max_raw is not None and str(cgroup_max_raw).strip().lower() == "max":
            cgroup_max_bytes = None
        elif cgroup_max_value is not None:
            cgroup_max_bytes = _parse_memory_bytes(cgroup_max_value, default_unit="bytes")
        elif cgroup_max_raw is not None:
            cgroup_max_bytes = _parse_memory_bytes(cgroup_max_raw, default_unit="bytes")
        else:
            cgroup_max_bytes = None
    except ValueError as exc:
        cgroup_max_bytes = None
        reasons.append(f"cgroup memory limit is invalid: {exc}")

    cgroup_current_value = _memory_field(
        memory,
        "cgroup_memory_current_bytes",
        "cgroup_current_bytes",
        "memory_current",
        "cgroup_memory_current_raw",
    )
    try:
        cgroup_current_bytes = (
            None
            if cgroup_current_value is None
            else _parse_memory_bytes(cgroup_current_value, default_unit="bytes")
        )
    except ValueError as exc:
        cgroup_current_bytes = None
        reasons.append(f"cgroup memory.current is invalid: {exc}")

    if cgroup_max_bytes is not None and cgroup_current_bytes is None:
        reasons.append("bounded cgroup memory.current is unavailable")
        cgroup_headroom_bytes = None
        effective_available_bytes = None
    elif cgroup_max_bytes is None:
        cgroup_headroom_bytes = None
        effective_available_bytes = available_bytes
    else:
        cgroup_headroom_bytes = max(0, cgroup_max_bytes - (cgroup_current_bytes or 0))
        effective_available_bytes = (
            None
            if available_bytes is None
            else min(available_bytes, cgroup_headroom_bytes)
        )

    physical_floor_pass = (
        available_bytes is not None
        and available_bytes >= MINIMUM_AVAILABLE_MEMORY_BYTES
    )
    effective_floor_pass = (
        effective_available_bytes is not None
        and effective_available_bytes >= MINIMUM_AVAILABLE_MEMORY_BYTES
    )
    if not physical_floor_pass:
        reasons.append("available physical memory is below 4 GiB")
    if physical_floor_pass and not effective_floor_pass:
        reasons.append("effective available memory is below 4 GiB")

    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at": snapshot.get("captured_at"),
        "assessed_at": _utc_now(),
        "measurement_source": memory.get("measurement_source"),
        "minimum_available_bytes": MINIMUM_AVAILABLE_MEMORY_BYTES,
        "available_physical_bytes": available_bytes,
        "cgroup_memory_max_bytes": cgroup_max_bytes,
        "cgroup_memory_current_bytes": cgroup_current_bytes,
        "cgroup_headroom_bytes": cgroup_headroom_bytes,
        "effective_available_bytes": effective_available_bytes,
        "physical_floor_pass": physical_floor_pass,
        "effective_floor_pass": effective_floor_pass,
        "passed": physical_floor_pass and effective_floor_pass and not reasons,
        "failure_reasons": reasons,
    }


def _memory_field(memory: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in memory:
            return memory[name]
    return None


def _as_positive_number(value: Any, name: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{name} is required")
    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(converted) or converted <= 0:
        raise ValueError(f"{name} must be positive")
    return converted


def _as_positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be positive")
    try:
        converted = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be positive") from exc
    if converted <= 0:
        raise ValueError(f"{name} must be positive")
    return converted


def assess_snapshot(
    snapshot: Mapping[str, Any],
    *,
    direction_id: str,
    run_id: str,
    workers: int,
    threads_per_worker: int,
    estimated_wall_seconds: Any,
    estimated_peak_gib: Any,
    basis: str,
) -> dict[str, Any]:
    """Apply the exact HMASD run-memory formula to a captured snapshot."""

    if not _DIRECTION_RE.fullmatch(direction_id):
        raise ValueError("direction_id is invalid")
    if not _DIRECTION_RE.fullmatch(run_id):
        raise ValueError("run_id is invalid")
    worker_count = _as_positive_int(workers, "workers")
    thread_count = _as_positive_int(threads_per_worker, "threads_per_worker")
    wall_seconds = _as_positive_number(estimated_wall_seconds, "estimated_wall_seconds")
    peak_gib = _as_positive_number(estimated_peak_gib, "estimated_peak_gib")
    if not isinstance(basis, str) or not basis.strip():
        raise ValueError("basis is required")

    memory = snapshot.get("memory")
    if not isinstance(memory, Mapping):
        raise ValueError("snapshot memory is missing")
    total_bytes = _parse_memory_bytes(
        _memory_field(memory, "total_bytes", "total_gib", "MemTotal"),
        default_unit="bytes",
    )
    if "total_gib" in memory and "total_bytes" not in memory:
        total_bytes = _parse_memory_bytes(memory["total_gib"], default_unit="GiB")
    available_bytes = _parse_memory_bytes(
        _memory_field(memory, "available_bytes", "available_gib", "MemAvailable"),
        default_unit="bytes",
    )
    if "available_gib" in memory and "available_bytes" not in memory:
        available_bytes = _parse_memory_bytes(memory["available_gib"], default_unit="GiB")
    if total_bytes is None or total_bytes <= 0 or available_bytes is None:
        raise ValueError("snapshot memory totals are invalid")
    available_bytes = max(0, available_bytes)

    cgroup_max_raw = _memory_field(memory, "cgroup_memory_max_raw", "memory_max")
    cgroup_max_value = _memory_field(memory, "cgroup_memory_max_bytes", "cgroup_max_bytes")
    if cgroup_max_raw is not None and str(cgroup_max_raw).strip().lower() == "max":
        cgroup_max_bytes = None
    elif cgroup_max_value is not None:
        cgroup_max_bytes = _parse_memory_bytes(cgroup_max_value, default_unit="bytes")
    elif cgroup_max_raw is not None:
        cgroup_max_bytes = _parse_memory_bytes(cgroup_max_raw, default_unit="bytes")
    else:
        cgroup_max_bytes = None
    cgroup_current_value = _memory_field(
        memory,
        "cgroup_memory_current_bytes",
        "cgroup_current_bytes",
        "memory_current",
        "cgroup_memory_current_raw",
    )
    cgroup_current_bytes = (
        None
        if cgroup_current_value is None
        else _parse_memory_bytes(cgroup_current_value, default_unit="bytes")
    )
    if cgroup_max_bytes is not None and cgroup_current_bytes is None:
        raise ValueError("bounded cgroup memory.current is unavailable")

    effective_limit_bytes = (
        min(total_bytes, cgroup_max_bytes) if cgroup_max_bytes is not None else total_bytes
    )
    if cgroup_max_bytes is None:
        cgroup_headroom_bytes: int | None = None
        effective_available_bytes = available_bytes
    else:
        cgroup_headroom_bytes = max(0, cgroup_max_bytes - (cgroup_current_bytes or 0))
        effective_available_bytes = min(available_bytes, cgroup_headroom_bytes)
    effective_limit_gib = effective_limit_bytes / GIB
    cgroup_headroom_gib = (
        None if cgroup_headroom_bytes is None else cgroup_headroom_bytes / GIB
    )
    effective_available_gib = effective_available_bytes / GIB
    reserve_gib = max(4.0, 0.20 * effective_limit_gib)
    usable_gib = max(0.0, effective_available_gib - reserve_gib)
    adjusted_peak_gib = 1.25 * peak_gib
    physical_floor_pass = available_bytes >= MINIMUM_AVAILABLE_MEMORY_BYTES
    effective_floor_pass = effective_available_bytes >= MINIMUM_AVAILABLE_MEMORY_BYTES
    memory_floor_pass = physical_floor_pass and effective_floor_pass
    memory_safe = memory_floor_pass and adjusted_peak_gib <= usable_gib
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_id": snapshot.get("preflight_id"),
        "captured_at": snapshot.get("captured_at"),
        "assessed_at": _utc_now(),
        "direction_id": direction_id,
        "run_id": run_id,
        "workers": worker_count,
        "threads_per_worker": thread_count,
        "estimate": {
            "wall_seconds": wall_seconds,
            "peak_memory_gib": peak_gib,
            "basis": str(basis),
        },
        "effective_limit_gib": round(effective_limit_gib, 6),
        "cgroup_headroom_gib": (
            None if cgroup_headroom_gib is None else round(cgroup_headroom_gib, 6)
        ),
        "effective_available_gib": round(effective_available_gib, 6),
        "reserve_gib": round(reserve_gib, 6),
        "usable_gib": round(usable_gib, 6),
        "adjusted_peak_gib": round(adjusted_peak_gib, 6),
        "minimum_available_bytes": MINIMUM_AVAILABLE_MEMORY_BYTES,
        "physical_floor_pass": physical_floor_pass,
        "effective_floor_pass": effective_floor_pass,
        "memory_floor_pass": memory_floor_pass,
        "memory_safe": memory_safe,
        "memory": {
            "total_bytes": total_bytes,
            "available_bytes": available_bytes,
            "cgroup_memory_max_bytes": cgroup_max_bytes,
            "cgroup_memory_current_bytes": cgroup_current_bytes,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    capture = modes.add_parser("capture", help="capture observed host resources")
    capture.add_argument("--out", required=True)
    memory_floor = modes.add_parser(
        "admit-memory",
        help="require at least 4 GiB of physical and effective available memory",
    )
    memory_floor.add_argument("--out", required=True)
    assess = modes.add_parser("assess-run", help="assess one result-bearing run")
    assess.add_argument("--direction", required=True)
    assess.add_argument("--run-id", required=True)
    assess.add_argument("--workers", required=True, type=int)
    assess.add_argument("--threads-per-worker", required=True, type=int)
    assess.add_argument("--estimated-wall-seconds", type=float)
    assess.add_argument("--estimated-peak-gib", type=float)
    assess.add_argument("--basis")
    assess.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "capture":
            payload = capture_snapshot()
            _atomic_write_json(Path(args.out), payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.mode == "admit-memory":
            payload = assess_memory_floor(capture_snapshot())
            _atomic_write_json(Path(args.out), payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if payload["passed"] else 6

        snapshot = capture_snapshot()
        assessed = assess_snapshot(
            snapshot,
            direction_id=args.direction,
            run_id=args.run_id,
            workers=args.workers,
            threads_per_worker=args.threads_per_worker,
            estimated_wall_seconds=args.estimated_wall_seconds,
            estimated_peak_gib=args.estimated_peak_gib,
            basis=args.basis,
        )
        _atomic_write_json(Path(args.out), assessed)
        print(json.dumps(assessed, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if assessed["memory_safe"] else 6
    except ValueError as exc:
        print(f"resource preflight refused: {exc}", file=sys.stderr)
        return 6
    except OSError as exc:
        print(f"resource preflight failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
