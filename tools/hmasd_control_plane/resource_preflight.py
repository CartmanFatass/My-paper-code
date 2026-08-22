"""Host-specific CPU/memory preflight records with no project worker default."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass(frozen=True)
class ResourceSnapshot:
    preflight_id: str
    assignment_id: str
    captured_at: str
    host_identity: str
    route_id: str
    backend: str
    physical_cores: int
    logical_processors: int
    cpu_load_percent: float
    total_memory_gib: float
    available_memory_gib: float
    selected_worker_count: int
    threads_per_worker: int
    parallel: bool
    selection_rationale: str
    cm_owner: str


def _read(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError("resource preflight must be an object")
    return data


def _section(data: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = data.get(name, {})
    return value if isinstance(value, dict) else {}


def _value(data: Mapping[str, object], section: str, key: str, default: object = None) -> object:
    nested = _section(data, section)
    return nested.get(key, data.get(key, default))


def load_resource_preflight(path: Path) -> ResourceSnapshot:
    data = _read(path)
    return ResourceSnapshot(
        preflight_id=str(data.get("preflight_id") or ""),
        assignment_id=str(data.get("assignment_id") or ""),
        captured_at=str(data.get("captured_at") or ""),
        host_identity=str(data.get("host_identity") or ""),
        route_id=str(data.get("route_id") or ""),
        backend=str(data.get("backend") or ""),
        physical_cores=int(_value(data, "cpu", "physical_cores", 0) or 0),
        logical_processors=int(_value(data, "cpu", "logical_processors", 0) or 0),
        cpu_load_percent=float(_value(data, "cpu", "load_percent", 0.0) or 0.0),
        total_memory_gib=float(_value(data, "memory", "total_gib", 0.0) or 0.0),
        available_memory_gib=float(_value(data, "memory", "available_gib", 0.0) or 0.0),
        selected_worker_count=int(_value(data, "selection", "selected_worker_count", 0) or 0),
        threads_per_worker=int(_value(data, "selection", "threads_per_worker", 0) or 0),
        parallel=bool(_value(data, "selection", "parallel", False)),
        selection_rationale=str(_value(data, "selection", "selection_rationale", "") or ""),
        cm_owner=str(_value(data, "selection", "cm_owner", "") or ""),
    )


def validate_resource_preflight(snapshot: ResourceSnapshot) -> list[str]:
    errors: list[str] = []
    for name in ("preflight_id", "assignment_id", "captured_at", "host_identity", "route_id", "backend", "selection_rationale", "cm_owner"):
        if not str(getattr(snapshot, name)).strip():
            errors.append(f"{name} is required")
    try:
        normalized = snapshot.captured_at.replace("Z", "+00:00")
        normalized = re.sub(r"(\.\d{6})\d+(?=\+00:00$)", r"\1", normalized)
        captured = datetime.fromisoformat(normalized)
        if captured.tzinfo is None:
            errors.append("captured_at must include timezone")
        elif captured > datetime.now(timezone.utc):
            errors.append("captured_at cannot be in the future")
        elif datetime.now(timezone.utc) - captured > timedelta(hours=24):
            errors.append("captured_at is stale; capture a current host preflight")
    except ValueError:
        errors.append("captured_at must be ISO-8601")
    if snapshot.physical_cores <= 0 or snapshot.logical_processors <= 0:
        errors.append("CPU core counts must be positive")
    if snapshot.physical_cores > snapshot.logical_processors > 0:
        errors.append("physical_cores cannot exceed logical_processors")
    if not 0 <= snapshot.cpu_load_percent <= 100:
        errors.append("cpu_load_percent must be between 0 and 100")
    if snapshot.total_memory_gib <= 0 or snapshot.available_memory_gib <= 0:
        errors.append("measured memory fields must be positive")
    if snapshot.available_memory_gib > snapshot.total_memory_gib > 0:
        errors.append("available_memory_gib cannot exceed total_memory_gib")
    if snapshot.selected_worker_count <= 0:
        errors.append("selected_worker_count must be positive and run-specific")
    if snapshot.threads_per_worker <= 0:
        errors.append("threads_per_worker must be positive")
    if snapshot.selected_worker_count > snapshot.logical_processors and "oversubscription" not in snapshot.selection_rationale.lower() and "io" not in snapshot.selection_rationale.lower():
        errors.append("WARNING: selected workers exceed logical processors without oversubscription/IO rationale")
    return errors
