"""Read-only MCP surface for HMASD control-plane observability."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from pydantic import Field

from tools.codex_context_lifecycle.authority import default_repo_root
from tools.codex_context_lifecycle import context_query

from .diagnostics import COMPONENTS, collect_doctor, collect_incidents
from .long_effect import observe_long_effect
from .mcp_runtime import begin_mcp_instance, inspect_mcp_instances


SERVER_NAME = "hmasd_observability"
SERVER_VERSION = "1.1"
REPO_ENV = "HMASD_REPO_ROOT"
ALLOWED_ROOTS_ENV = "HMASD_CONTROL_PLANE_ALLOWED_ROOTS"
INSTANCE_STATUSES = frozenset({"ACTIVE", "CLOSED", "STALE", "UNKNOWN"})
OBSERVABILITY_INSTRUCTIONS = (
    "This server is read-only for domain and canonical state. Use it to inspect "
    "doctor findings, incidents, MCP process evidence, and long-effect metadata. "
    "Never infer scientific failure, direction pause, portfolio disposition, or "
    "retry authority from ERROR, missing terminal, stale process, or unavailable "
    "sources. Never read provider text, process logs, or scientific outputs. "
    "These tools do not repair, restart, clean, schedule, or wake work."
)
OBSERVABILITY_TOOL_ALLOWLIST = (
    "control_plane_health",
    "control_plane_doctor",
    "control_plane_incidents",
    "long_effect_observe",
    "mcp_instance_list",
    "context_foundation_health",
    "context_sources_for_actor",
    "decision_list",
    "decision_get",
    "project_map_validate",
    "project_map_resolve_anchor",
    "current_work_index",
)

_active_repo_root: Path | None = None
_active_instance_id: str | None = None


def _repo_root(repo_root: str | os.PathLike[str] | None = None) -> Path:
    if repo_root is None:
        repo_root = os.environ.get(REPO_ENV)
    if repo_root is None and "--repo-root" in sys.argv:
        index = sys.argv.index("--repo-root")
        if index + 1 < len(sys.argv):
            repo_root = sys.argv[index + 1]
    return Path(repo_root).resolve() if repo_root else default_repo_root().resolve()


def _get_repo_root() -> Path:
    if _active_repo_root is None:
        raise RuntimeError("observability MCP repo root is not initialized")
    return _active_repo_root


def _allowed_roots() -> tuple[Path, ...]:
    roots = [_get_repo_root()]
    raw = os.environ.get(ALLOWED_ROOTS_ENV, "")
    for value in raw.split(os.pathsep):
        if value.strip():
            roots.append(Path(value.strip()).resolve())
    return tuple(dict.fromkeys(roots))


def _require_allowed_path(value: str, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty path")
    path = Path(value).resolve()
    for root in _allowed_roots():
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return path
    raise ValueError(f"{label} must be inside the repository or an explicitly allowed root")


def _validate_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit must be an integer between 1 and 500")
    return limit


def _bounded_items(payload: dict[str, Any], key: str, limit: int) -> dict[str, Any]:
    values = payload.get(key, [])
    if not isinstance(values, list):
        return payload
    result = dict(payload)
    result[key] = values[:limit]
    result["truncated"] = len(values) > limit
    result["total_items"] = len(values)
    return result


def _register_tools(server: MCPServer) -> MCPServer:
    @server.tool(description="Return read-only HMASD observability MCP health.")
    def control_plane_health() -> dict[str, Any]:
        return {
            "status": "OK",
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "read_only_domain_surface": True,
            "repo_root": str(_get_repo_root()),
            "instance_id": _active_instance_id,
        }

    @server.tool(description="Collect a bounded, read-only HMASD control-plane doctor snapshot.")
    def control_plane_doctor(
        component: str | None = None,
        since: str | None = None,
        experiment_roots: list[str] | None = None,
        limit: Annotated[int, Field(strict=True, ge=1, le=500)] = 100,
    ) -> dict[str, Any]:
        selected_limit = _validate_limit(limit)
        if component is not None and component not in COMPONENTS:
            raise ValueError(f"unknown component: {component}")
        roots = [
            _require_allowed_path(value, "experiment_roots")
            for value in (experiment_roots or [])
        ]
        doctor, exit_code = collect_doctor(
            _get_repo_root(), component=component, since=since, experiment_roots=roots
        )
        result = _bounded_items(dict(doctor), "findings", selected_limit)
        result["diagnostic_exit_code"] = exit_code
        return result

    @server.tool(description="Collect a bounded, read-only HMASD incident index.")
    def control_plane_incidents(
        component: str | None = None,
        since: str | None = None,
        experiment_roots: list[str] | None = None,
        limit: Annotated[int, Field(strict=True, ge=1, le=500)] = 100,
    ) -> dict[str, Any]:
        selected_limit = _validate_limit(limit)
        if component is not None and component not in COMPONENTS:
            raise ValueError(f"unknown component: {component}")
        roots = [
            _require_allowed_path(value, "experiment_roots")
            for value in (experiment_roots or [])
        ]
        incidents, exit_code = collect_incidents(
            _get_repo_root(), component=component, since=since, experiment_roots=roots
        )
        return {
            "schema": "HMASD_CONTROL_PLANE_INCIDENT_INDEX_V1",
            "incidents": incidents[:selected_limit],
            "truncated": len(incidents) > selected_limit,
            "total_items": len(incidents),
            "diagnostic_exit_code": exit_code,
        }

    @server.tool(description="Observe one file-backed long effect without reading logs or outputs.")
    def long_effect_observe(run_root: str) -> dict[str, Any]:
        return observe_long_effect(_require_allowed_path(run_root, "run_root"))

    @server.tool(description="List bounded runtime-only MCP process lifecycle evidence.")
    def mcp_instance_list(
        server_name: str | None = None,
        status: Literal["ACTIVE", "CLOSED", "STALE", "UNKNOWN"] | None = None,
        limit: Annotated[int, Field(strict=True, ge=1, le=500)] = 100,
    ) -> dict[str, Any]:
        selected_limit = _validate_limit(limit)
        if status is not None and status not in INSTANCE_STATUSES:
            raise ValueError(f"unknown MCP instance status: {status}")
        index = inspect_mcp_instances(_get_repo_root())
        selected = [
            item
            for item in index["instances"]
            if (server_name is None or item.get("server_name") == server_name)
            and (status is None or item.get("status") == status)
        ]
        return {
            **index,
            "instances": selected[:selected_limit],
            "truncated": len(selected) > selected_limit,
            "total_items": len(selected),
        }

    @server.tool(description="Return read-only repository context-foundation health.")
    def context_foundation_health() -> dict[str, Any]:
        return context_query.context_foundation_health(_get_repo_root())

    @server.tool(description="List bounded context sources selected for one actor.")
    def context_sources_for_actor(
        actor: str,
        requested_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return context_query.context_sources_for_actor(
            _get_repo_root(), actor, tuple(requested_ids or ())
        )

    @server.tool(description="List bounded repository decision metadata.")
    def decision_list(status: str | None = None) -> list[dict[str, Any]]:
        return context_query.decision_list(_get_repo_root(), status)

    @server.tool(description="Get one exact repository decision record.")
    def decision_get(decision_id: str) -> dict[str, Any]:
        return context_query.decision_get(_get_repo_root(), decision_id)

    @server.tool(description="Validate the repository PROJECT_MAP without writing it.")
    def project_map_validate() -> dict[str, Any]:
        return context_query.project_map_validate(_get_repo_root())

    @server.tool(description="Resolve one exact PROJECT_MAP H2 anchor.")
    def project_map_resolve_anchor(anchor: str) -> dict[str, Any]:
        return context_query.project_map_resolve_anchor(_get_repo_root(), anchor)

    @server.tool(description="List bounded repository CURRENT_WORK pointers.")
    def current_work_index() -> list[dict[str, Any]]:
        return context_query.current_work_index(_get_repo_root())

    return server


def build_server(repo_root: str | os.PathLike[str] | None = None) -> MCPServer:
    global _active_repo_root
    _active_repo_root = _repo_root(repo_root)
    return _register_tools(
        MCPServer(
            SERVER_NAME,
            version=SERVER_VERSION,
            instructions=OBSERVABILITY_INSTRUCTIONS,
        )
    )


mcp = build_server()


def main() -> None:
    global _active_instance_id
    registration = begin_mcp_instance(
        _get_repo_root(), server_name=SERVER_NAME, profile="observability"
    )
    _active_instance_id = registration.instance_id
    mcp.run()
    registration.close()


if __name__ == "__main__":
    main()
