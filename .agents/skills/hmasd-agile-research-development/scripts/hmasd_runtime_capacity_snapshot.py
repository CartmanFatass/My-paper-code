#!/usr/bin/env python3
"""Write one stateless, factual Windows capacity observation.

The input is a small JSON record owned by CPM.  This module only validates
that record, observes one set of host facts, performs fixed three-unit
arithmetic and atomically writes the resulting snapshot.  It never retains
state between invocations.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 2
SNAPSHOT_KIND = "stateless_capacity_observation"
TOTAL_CAPACITY_UNITS = 3


class SnapshotError(ValueError):
    """A direct factual or input error."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError("INVALID_INPUT", f"{field} must be a non-empty string", field)
    return value.strip()


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SnapshotError("INVALID_INPUT", f"{field} must be a positive integer", field)
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], field: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing:
        raise SnapshotError("INVALID_INPUT", f"{field} is missing keys: {', '.join(missing)}", field)
    if extra:
        raise SnapshotError("INVALID_INPUT", f"{field} has unknown keys: {', '.join(extra)}", field)


def _paths(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise SnapshotError("INVALID_INPUT", f"{field} must be a list of non-empty strings", field)
    return [item.strip() for item in value]


def _claims(value: Any, field: str) -> list[str]:
    """Validate exact resource claims without contacting the claimed service."""

    return _paths(value, field)


def _process_ids(value: Any, field: str) -> list[int]:
    if not isinstance(value, list) or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value):
        raise SnapshotError("INVALID_INPUT", f"{field} must be a list of positive integers", field)
    if len(set(value)) != len(value):
        raise SnapshotError("INVALID_INPUT", f"{field} contains duplicate process ids", field)
    return list(value)


def _canonical_path(value: str) -> str:
    # ``strict=False`` is intentional: prospective output paths need not exist.
    return os.path.normcase(str(Path(value).expanduser().resolve(strict=False)))


def _parse_input(payload: Any) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(payload, Mapping):
        raise SnapshotError("INVALID_INPUT", "input JSON must be an object", "input")
    _exact_keys(payload, {"assignment_id", "active_treatments", "prospective"}, "input")
    assignment_id = _nonempty_text(payload["assignment_id"], "assignment_id")
    raw_active = payload["active_treatments"]
    if not isinstance(raw_active, list):
        raise SnapshotError("INVALID_INPUT", "active_treatments must be a list", "active_treatments")

    active: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_active):
        field = f"active_treatments[{index}]"
        if not isinstance(raw, Mapping):
            raise SnapshotError("INVALID_INPUT", f"{field} must be an object", field)
        _exact_keys(
            raw,
            {
                "treatment_id",
                "process_ids",
                "units",
                "cpu_units",
                "memory_bytes",
                "gpu_claims",
                "paid_service_claims",
                "output_paths",
                "writable_paths",
            },
            field,
        )
        active.append(
            {
                "treatment_id": _nonempty_text(raw["treatment_id"], f"{field}.treatment_id"),
                "process_ids": _process_ids(raw["process_ids"], f"{field}.process_ids"),
                "units": _positive_int(raw["units"], f"{field}.units"),
                "cpu_units": _positive_int(raw["cpu_units"], f"{field}.cpu_units"),
                "memory_bytes": _positive_int(raw["memory_bytes"], f"{field}.memory_bytes"),
                "gpu_claims": _claims(raw["gpu_claims"], f"{field}.gpu_claims"),
                "paid_service_claims": _claims(
                    raw["paid_service_claims"], f"{field}.paid_service_claims"
                ),
                "output_paths": _paths(raw["output_paths"], f"{field}.output_paths"),
                "writable_paths": _paths(raw["writable_paths"], f"{field}.writable_paths"),
            }
        )

    raw_prospective = payload["prospective"]
    if not isinstance(raw_prospective, Mapping):
        raise SnapshotError("INVALID_INPUT", "prospective must be an object", "prospective")
    _exact_keys(
        raw_prospective,
        {
            "class",
            "units",
            "process_ids",
            "cpu_units",
            "memory_bytes",
            "gpu_claims",
            "paid_service_claims",
            "output_paths",
            "writable_paths",
        },
        "prospective",
    )
    prospective = {
        "class": _nonempty_text(raw_prospective["class"], "prospective.class"),
        "units": _positive_int(raw_prospective["units"], "prospective.units"),
        "process_ids": _process_ids(raw_prospective["process_ids"], "prospective.process_ids"),
        "cpu_units": _positive_int(raw_prospective["cpu_units"], "prospective.cpu_units"),
        "memory_bytes": _positive_int(raw_prospective["memory_bytes"], "prospective.memory_bytes"),
        "gpu_claims": _claims(raw_prospective["gpu_claims"], "prospective.gpu_claims"),
        "paid_service_claims": _claims(
            raw_prospective["paid_service_claims"], "prospective.paid_service_claims"
        ),
        "output_paths": _paths(raw_prospective["output_paths"], "prospective.output_paths"),
        "writable_paths": _paths(raw_prospective["writable_paths"], "prospective.writable_paths"),
    }
    return assignment_id, active, prospective


def _path_conflicts(active: list[dict[str, Any]], prospective: Mapping[str, Any]) -> list[dict[str, str]]:
    claims: list[tuple[str, str, str, str]] = []
    for treatment in active:
        treatment_id = treatment["treatment_id"]
        for kind in ("output_paths", "writable_paths"):
            for raw_path in treatment[kind]:
                claims.append(("active", treatment_id, kind.removesuffix("_paths"), raw_path))
    for kind in ("output_paths", "writable_paths"):
        for raw_path in prospective[kind]:
            claims.append(("prospective", "requested", kind.removesuffix("_paths"), raw_path))

    conflicts: list[dict[str, str]] = []
    for left_index, left in enumerate(claims):
        for right in claims[left_index + 1 :]:
            if _canonical_path(left[3]) != _canonical_path(right[3]):
                continue
            conflicts.append(
                {
                    "path": _canonical_path(left[3]),
                    "left_scope": left[0],
                    "left_owner": left[1],
                    "left_kind": left[2],
                    "right_scope": right[0],
                    "right_owner": right[1],
                    "right_kind": right[2],
                }
            )
    conflicts.sort(key=lambda item: (item["path"], item["left_scope"], item["left_owner"], item["right_scope"], item["right_owner"]))
    return conflicts


def _claim_conflicts(
    active: list[dict[str, Any]], prospective: Mapping[str, Any], field: str
) -> list[dict[str, Any]]:
    """Return deterministic exact conflicts for process, GPU or paid claims."""

    claims: list[tuple[str, str, str]] = []
    for treatment in active:
        for claim in treatment[field]:
            claims.append(("active", treatment["treatment_id"], str(claim)))
    for claim in prospective[field]:
        claims.append(("prospective", "requested", str(claim)))

    conflicts: list[dict[str, Any]] = []
    for left_index, left in enumerate(claims):
        for right in claims[left_index + 1 :]:
            if left[2].casefold() != right[2].casefold():
                continue
            conflicts.append(
                {
                    "claim": left[2],
                    "left_scope": left[0],
                    "left_owner": left[1],
                    "right_scope": right[0],
                    "right_owner": right[1],
                }
            )
    conflicts.sort(
        key=lambda item: (
            str(item["claim"]).casefold(),
            item["left_scope"],
            item["left_owner"],
            item["right_scope"],
            item["right_owner"],
        )
    )
    return conflicts


class _MemoryStatusEx(ctypes.Structure):
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


def _windows_memory() -> dict[str, int]:
    if os.name != "nt":
        raise SnapshotError("LIVE_FACTS_INCOMPLETE", "Windows memory facts are unavailable", "live.memory")
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        error = ctypes.get_last_error()
        raise SnapshotError("LIVE_FACTS_INCOMPLETE", f"GlobalMemoryStatusEx failed with error {error}", "live.memory")
    return {
        "memory_load_percent": int(status.dwMemoryLoad),
        "total_physical_bytes": int(status.ullTotalPhys),
        "available_physical_bytes": int(status.ullAvailPhys),
    }


def _windows_process_ids() -> list[int]:
    if os.name != "nt":
        raise SnapshotError("LIVE_FACTS_INCOMPLETE", "Windows process facts are unavailable", "live.processes")
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
    except OSError as exc:
        raise SnapshotError("LIVE_FACTS_INCOMPLETE", f"tasklist could not be read: {exc}", "live.processes") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"tasklist exited {completed.returncode}"
        raise SnapshotError("LIVE_FACTS_INCOMPLETE", detail, "live.processes")
    process_ids: list[int] = []
    for row in csv.reader(completed.stdout.splitlines()):
        if len(row) < 2:
            continue
        try:
            process_ids.append(int(row[1].replace(",", "")))
        except ValueError:
            continue
    return sorted(set(process_ids))


def observe_windows_facts(process_ids: list[int]) -> dict[str, Any]:
    """Read one set of host facts; no state is retained between calls."""

    failures: list[dict[str, str]] = []
    cpu_count = os.cpu_count()
    if cpu_count is None or cpu_count <= 0:
        failures.append({"field": "live.cpu", "message": "logical processor count is unavailable"})
        cpu_count = None
    try:
        memory = _windows_memory()
    except SnapshotError as exc:
        memory = {}
        failures.append({"field": exc.field or "live.memory", "message": exc.message})
    try:
        running_ids = _windows_process_ids()
    except SnapshotError as exc:
        running_ids = []
        failures.append({"field": exc.field or "live.processes", "message": exc.message})

    missing = sorted(set(process_ids) - set(running_ids))
    processes: dict[str, Any] = {
        "observed_process_count": len(running_ids),
        "known_process_ids": list(process_ids),
        "running_known_process_ids": sorted(set(process_ids) - set(missing)),
        "missing_known_process_ids": missing,
    }
    if missing:
        failures.append(
            {
                "field": "live.processes",
                "message": "active process ids were not present in the one-shot process listing",
            }
        )
    return {
        "complete": not failures,
        "cpu": {"logical_processors": cpu_count},
        "memory": memory,
        "processes": processes,
        "errors": failures,
    }


def _error_snapshot(assignment_id: str | None, error: SnapshotError, facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "snapshot": SNAPSHOT_KIND,
        "status": "ERROR",
        "assignment_id": assignment_id,
        "error": {"code": error.code, "message": error.message},
    }
    if error.field:
        value["error"]["field"] = error.field
    if facts is not None:
        value["facts"] = dict(facts)
    return value


def build_snapshot(payload: Any, live_facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build one snapshot, optionally using deterministic test-supplied live facts."""

    assignment_id: str | None = payload.get("assignment_id") if isinstance(payload, Mapping) else None
    try:
        assignment_id, active, prospective = _parse_input(payload)
    except SnapshotError as exc:
        return _error_snapshot(assignment_id if isinstance(assignment_id, str) else None, exc)

    process_ids = sorted({pid for treatment in active for pid in treatment["process_ids"]})
    live = dict(live_facts) if live_facts is not None else observe_windows_facts(process_ids)
    process_conflicts = _claim_conflicts(
        active,
        {**prospective, "process_ids": [str(pid) for pid in prospective["process_ids"]]},
        "process_ids",
    )
    gpu_conflicts = _claim_conflicts(active, prospective, "gpu_claims")
    paid_service_conflicts = _claim_conflicts(active, prospective, "paid_service_claims")
    path_conflicts = _path_conflicts(active, prospective)
    output_path_conflicts = [
        conflict
        for conflict in path_conflicts
        if conflict["left_kind"] == "output" or conflict["right_kind"] == "output"
    ]
    writable_path_conflicts = [
        conflict
        for conflict in path_conflicts
        if conflict["left_kind"] == "writable" or conflict["right_kind"] == "writable"
    ]
    active_units = sum(treatment["units"] for treatment in active)
    requested_units = prospective["units"]
    projected_units = active_units + requested_units
    reserved_cpu_units = sum(treatment["cpu_units"] for treatment in active)
    requested_cpu_units = prospective["cpu_units"]
    reserved_memory_bytes = sum(treatment["memory_bytes"] for treatment in active)
    requested_memory_bytes = prospective["memory_bytes"]
    live_cpu = live.get("cpu") if isinstance(live.get("cpu"), Mapping) else {}
    live_memory = live.get("memory") if isinstance(live.get("memory"), Mapping) else {}
    cpu_total = live_cpu.get("logical_processors")
    memory_available = live_memory.get("available_physical_bytes")
    incomplete_resources: list[str] = []
    cpu_conflicts: list[dict[str, Any]] = []
    memory_conflicts: list[dict[str, Any]] = []
    cpu_valid = isinstance(cpu_total, int) and not isinstance(cpu_total, bool) and cpu_total > 0
    memory_valid = isinstance(memory_available, int) and not isinstance(memory_available, bool) and memory_available >= 0
    if not cpu_valid:
        incomplete_resources.append("cpu")
    else:
        free_cpu_units = cpu_total - reserved_cpu_units
        if free_cpu_units < 0:
            cpu_conflicts.append(
                {
                    "kind": "reserved_claim_exceeds_capacity",
                    "reserved_cpu_units": reserved_cpu_units,
                    "cpu_units_total": cpu_total,
                }
            )
        if requested_cpu_units > free_cpu_units:
            cpu_conflicts.append(
                {
                    "kind": "prospective_claim_exceeds_free",
                    "requested_cpu_units": requested_cpu_units,
                    "free_cpu_units_before_request": free_cpu_units,
                }
            )
    if not memory_valid:
        incomplete_resources.append("memory")
    else:
        free_memory_bytes = memory_available - reserved_memory_bytes
        if free_memory_bytes < 0:
            memory_conflicts.append(
                {
                    "kind": "reserved_claim_exceeds_available",
                    "reserved_memory_bytes": reserved_memory_bytes,
                    "available_physical_bytes": memory_available,
                }
            )
        if requested_memory_bytes > free_memory_bytes:
            memory_conflicts.append(
                {
                    "kind": "prospective_claim_exceeds_free",
                    "requested_memory_bytes": requested_memory_bytes,
                    "free_memory_bytes_before_request": free_memory_bytes,
                }
            )
    facts: dict[str, Any] = {
        "capacity_units_total": TOTAL_CAPACITY_UNITS,
        "active_units": active_units,
        "reserved_units": active_units,
        "requested_units": requested_units,
        "free_units": TOTAL_CAPACITY_UNITS - active_units,
        "available_units_before_request": TOTAL_CAPACITY_UNITS - active_units,
        "projected_units": projected_units,
        "free_units_after_request": TOTAL_CAPACITY_UNITS - projected_units,
        "remaining_units_after_request": TOTAL_CAPACITY_UNITS - projected_units,
        "capacity_overage_units": max(0, projected_units - TOTAL_CAPACITY_UNITS),
        "prospective_class": prospective["class"],
        "reserved_cpu_units": reserved_cpu_units,
        "requested_cpu_units": requested_cpu_units,
        "free_cpu_units_before_request": None if not cpu_valid else cpu_total - reserved_cpu_units,
        "reserved_memory_bytes": reserved_memory_bytes,
        "requested_memory_bytes": requested_memory_bytes,
        "free_memory_bytes_before_request": None
        if not memory_valid
        else memory_available - reserved_memory_bytes,
        "active_treatments": [
            {
                "treatment_id": treatment["treatment_id"],
                "process_ids": list(treatment["process_ids"]),
                "units": treatment["units"],
                "cpu_units": treatment["cpu_units"],
                "memory_bytes": treatment["memory_bytes"],
                "gpu_claims": list(treatment["gpu_claims"]),
                "paid_service_claims": list(treatment["paid_service_claims"]),
                "output_paths": list(treatment["output_paths"]),
                "writable_paths": list(treatment["writable_paths"]),
            }
            for treatment in active
        ],
        "active_process_ids": process_ids,
        "prospective_process_ids": list(prospective["process_ids"]),
        "gpu_claims": {
            "active": [
                {"treatment_id": treatment["treatment_id"], "claims": list(treatment["gpu_claims"])}
                for treatment in active
            ],
            "prospective": list(prospective["gpu_claims"]),
        },
        "paid_service_claims": {
            "active": [
                {
                    "treatment_id": treatment["treatment_id"],
                    "claims": list(treatment["paid_service_claims"]),
                }
                for treatment in active
            ],
            "prospective": list(prospective["paid_service_claims"]),
        },
        "cpu_conflicts": cpu_conflicts,
        "memory_conflicts": memory_conflicts,
        "process_conflicts": process_conflicts,
        "gpu_conflicts": gpu_conflicts,
        "paid_service_conflicts": paid_service_conflicts,
        "output_path_conflicts": output_path_conflicts,
        "writable_path_conflicts": writable_path_conflicts,
        "path_conflicts": path_conflicts,
        "live": live,
    }
    conflict_types: list[str] = []
    if cpu_conflicts:
        conflict_types.append("cpu")
    if memory_conflicts:
        conflict_types.append("memory")
    if process_conflicts:
        conflict_types.append("process")
    if gpu_conflicts:
        conflict_types.append("gpu")
    if paid_service_conflicts:
        conflict_types.append("paid_service")
    if path_conflicts:
        conflict_types.append("path")
    if conflict_types:
        first = conflict_types[0]
        error_code = {
            "cpu": "CPU_CONFLICT",
            "memory": "MEMORY_CONFLICT",
            "process": "PROCESS_CONFLICT",
            "gpu": "GPU_CONFLICT",
            "paid_service": "PAID_SERVICE_CONFLICT",
            "path": "PATH_CONFLICT",
        }[first]
        return _error_snapshot(
            assignment_id,
            SnapshotError(
                error_code,
                "one or more exact resource claims overlap",
                f"facts.{first}_conflicts",
            ),
            facts,
        )
    if live.get("complete") is not True or incomplete_resources:
        if incomplete_resources:
            facts["live_resource_facts_incomplete"] = list(incomplete_resources)
        return _error_snapshot(
            assignment_id,
            SnapshotError("LIVE_FACTS_INCOMPLETE", "one-shot Windows facts are incomplete", "facts.live"),
            facts,
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot": SNAPSHOT_KIND,
        "status": "SUCCESS",
        "assignment_id": assignment_id,
        "facts": facts,
    }


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = path.expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def run(input_path: Path, output_path: Path) -> int:
    output_resolved = output_path.expanduser().resolve(strict=False)
    try:
        input_resolved = input_path.expanduser().resolve(strict=True)
        if input_resolved == output_resolved:
            raise SnapshotError("INVALID_INPUT", "input and output paths must differ", "output")
        payload = json.loads(input_resolved.read_text(encoding="utf-8"))
        snapshot = build_snapshot(payload)
    except SnapshotError as exc:
        assignment_id = payload.get("assignment_id") if "payload" in locals() and isinstance(payload, Mapping) else None
        snapshot = _error_snapshot(assignment_id if isinstance(assignment_id, str) else None, exc)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        snapshot = _error_snapshot(None, SnapshotError("INPUT_READ_ERROR", str(exc), "input"))

    try:
        _atomic_write(output_resolved, snapshot)
    except OSError as exc:
        print(f"HMASD_RUNTIME_CAPACITY_SNAPSHOT_ERROR {exc}", file=sys.stderr)
        return 1
    if snapshot["status"] == "SUCCESS":
        print("HMASD_RUNTIME_CAPACITY_SNAPSHOT_OK")
        return 0
    print(f"HMASD_RUNTIME_CAPACITY_SNAPSHOT_ERROR {snapshot['error']['code']}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one stateless Windows capacity observation")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args.input, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
