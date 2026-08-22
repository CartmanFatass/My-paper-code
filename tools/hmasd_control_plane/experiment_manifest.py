"""Validation for exact, resource-grounded experiment manifests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from .requirements_registry import Requirement, require_active
from .resource_preflight import ResourceSnapshot


@dataclass(frozen=True)
class ExperimentManifest:
    manifest_id: str
    assignment_id: str
    evidence_class: str
    strictness_profile: str
    runtime_profile: str
    result_bearing: bool
    requirement_ids: tuple[str, ...]
    nonrequirement_ids: tuple[str, ...]
    resource_preflight_ref: str
    project_map_anchor: str
    entrypoint: str
    runner: str
    environment_factory: str
    native_boundary: str
    direct_consumer: str
    route_id: str
    backend: str
    parallel: bool
    worker_count: int
    worker_count_source: str
    threads_per_worker: int
    silent_fallback_allowed: bool
    deviation_ref: str | None


def _read(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError("manifest must be an object")
    return data


def _section(data: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = data.get(name, {})
    return value if isinstance(value, dict) else {}


def _v(data: Mapping[str, object], section: str, key: str, default: object = "") -> object:
    nested = _section(data, section)
    return nested.get(key, data.get(key, default))


def _tuple(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value) if isinstance(value, list) else ()


def load_manifest(path: Path) -> ExperimentManifest:
    data = _read(path)
    return ExperimentManifest(
        manifest_id=str(data.get("manifest_id") or ""), assignment_id=str(data.get("assignment_id") or ""),
        evidence_class=str(data.get("evidence_class") or ""), strictness_profile=str(data.get("strictness_profile") or ""),
        runtime_profile=str(data.get("runtime_profile") or ""), result_bearing=bool(data.get("result_bearing", False)),
        requirement_ids=_tuple(data.get("requirement_ids")), nonrequirement_ids=_tuple(data.get("nonrequirement_ids")),
        resource_preflight_ref=str(data.get("resource_preflight_ref") or ""), project_map_anchor=str(_v(data, "code_surface", "project_map_anchor") or data.get("project_map_anchor") or ""),
        entrypoint=str(_v(data, "code_surface", "entrypoint") or data.get("entrypoint") or ""), runner=str(_v(data, "code_surface", "runner") or data.get("runner") or ""),
        environment_factory=str(_v(data, "code_surface", "environment_factory") or data.get("environment_factory") or ""), native_boundary=str(_v(data, "code_surface", "native_boundary") or data.get("native_boundary") or ""),
        direct_consumer=str(_v(data, "code_surface", "direct_consumer") or data.get("direct_consumer") or ""), route_id=str(_v(data, "execution", "route_id") or data.get("route_id") or ""), backend=str(_v(data, "execution", "backend") or data.get("backend") or ""),
        parallel=bool(_v(data, "execution", "parallel", data.get("parallel", False))), worker_count=int(_v(data, "execution", "worker_count", data.get("worker_count", 0)) or 0),
        worker_count_source=str(_v(data, "execution", "worker_count_source") or data.get("worker_count_source") or ""), threads_per_worker=int(_v(data, "execution", "threads_per_worker", data.get("threads_per_worker", 0)) or 0),
        silent_fallback_allowed=bool(_v(data, "execution", "silent_fallback_allowed", data.get("silent_fallback_allowed", False))), deviation_ref=str(_v(data, "execution", "deviation_ref") or data.get("deviation_ref") or "") or None,
    )


def load_backend_registry(path: Path) -> dict[str, dict[str, object]]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    routes = data.get("routes", [])
    if not isinstance(routes, list):
        raise ValueError("routes must be an array of tables")
    return {str(row["route_id"]): dict(row) for row in routes if isinstance(row, dict) and row.get("route_id")}


def _headings(project_map: Path) -> set[str]:
    return {match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", project_map.read_text(encoding="utf-8"), re.MULTILINE)} if project_map.exists() else set()


def validate_manifest(manifest: ExperimentManifest, preflight: ResourceSnapshot, requirements: Mapping[str, Requirement], backend_registry: Mapping[str, object], project_map: Path) -> list[str]:
    errors: list[str] = []
    for name in ("manifest_id", "assignment_id", "strictness_profile", "runtime_profile", "resource_preflight_ref", "project_map_anchor", "entrypoint", "runner", "environment_factory", "native_boundary", "direct_consumer", "route_id", "backend"):
        if not str(getattr(manifest, name)).strip():
            errors.append(f"{name} is required")
    if manifest.result_bearing and manifest.strictness_profile != "R2_EXPERIMENT_EXECUTION":
        errors.append("result-bearing manifest requires R2_EXPERIMENT_EXECUTION")
    if manifest.result_bearing:
        required = {"UR-EXEC-001", "UR-EXEC-002", "UR-RESOURCE-001", "UR-PERF-001"}
        missing = sorted(required.difference(manifest.requirement_ids))
        if missing:
            errors.append("result-bearing manifest missing requirements: " + ", ".join(missing))
        if "NR-WORKER-LIMIT-001" not in manifest.nonrequirement_ids:
            errors.append("result-bearing manifest must cite NR-WORKER-LIMIT-001")
        if manifest.runtime_profile.upper() in {"DEBUG_REFERENCE", "REFERENCE_ORACLE"}:
            errors.append("debug/reference profile cannot be result-bearing")
    try:
        require_active(requirements, manifest.requirement_ids + manifest.nonrequirement_ids)
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))
    if manifest.project_map_anchor not in _headings(project_map):
        errors.append("project_map_anchor does not match PROJECT_MAP")
    for name in ("entrypoint", "runner", "environment_factory", "native_boundary", "direct_consumer"):
        value = Path(str(getattr(manifest, name)).replace("\\", "/"))
        if value.is_absolute() or ".." in value.parts:
            errors.append(f"{name} must be repository-relative")
        elif name == "native_boundary" and str(value).lower() in {"none", "n/a"} and not manifest.result_bearing:
            pass
        elif not value.exists():
            errors.append(f"{name} path does not exist: {value}")
    preflight_path = Path(manifest.resource_preflight_ref.replace("\\", "/"))
    if preflight_path.is_absolute() or ".." in preflight_path.parts:
        errors.append("resource_preflight_ref must be repository-relative")
    elif manifest.resource_preflight_ref and not preflight_path.exists():
        errors.append("resource_preflight_ref does not exist")
    if manifest.assignment_id != preflight.assignment_id:
        errors.append("manifest/preflight assignment_id mismatch")
    if manifest.route_id != preflight.route_id or manifest.backend != preflight.backend:
        errors.append("manifest route/backend does not match preflight")
    if manifest.worker_count != preflight.selected_worker_count:
        errors.append("manifest worker_count must equal preflight selected_worker_count")
    if manifest.worker_count_source != "RESOURCE_PREFLIGHT":
        errors.append("worker_count_source must be RESOURCE_PREFLIGHT")
    if manifest.parallel != preflight.parallel:
        errors.append("manifest parallel must equal preflight")
    if manifest.threads_per_worker != preflight.threads_per_worker:
        errors.append("manifest threads_per_worker must equal preflight")
    if manifest.silent_fallback_allowed:
        errors.append("silent backend/serial fallback is forbidden")
    route = backend_registry.get(manifest.route_id, {})
    if not isinstance(route, Mapping):
        route = {}
    cpp_available = str(route.get("cpp_backend", "")).upper() in {"AVAILABLE", "REGISTERED"} and str(route.get("semantic_equivalence", "")).upper() in {"REGISTERED", "EQUIVALENT"}
    parallel_available = str(route.get("parallel_execution", "")).upper() in {"AVAILABLE", "REGISTERED"}
    if manifest.result_bearing:
        if not manifest.parallel:
            errors.append("result-bearing execution must be parallel")
        if parallel_available and not cpp_available:
            errors.append("registered parallel route lacks a semantics-preserving C++ backend: E2_ASSIGNMENT_RECOVERY")
        if cpp_available and manifest.backend.lower() != "cpp":
            errors.append("available equivalent route requires backend=cpp")
        if not parallel_available:
            errors.append("result-bearing route is not registered parallel: E2_ASSIGNMENT_RECOVERY")
    elif manifest.parallel is False and manifest.backend.lower() in {"python", "reference"}:
        pass
    return errors
