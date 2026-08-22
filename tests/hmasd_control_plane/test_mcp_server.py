from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import anyio
from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tools.hmasd_control_plane import mcp_server
from tools.hmasd_control_plane.diagnostics import collect_doctor
from tools.hmasd_control_plane.mcp_runtime import begin_mcp_instance


def run(coro):
    return anyio.run(coro)


@asynccontextmanager
async def connected_server(repo_root: Path):
    server = mcp_server.build_server(repo_root)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(
                server._lowlevel_server.run,
                server_streams[0],
                server_streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client_streams) as client:
                initialization = await client.initialize()
                yield client, initialization
                task_group.cancel_scope.cancel()


async def call(client: ClientSession, name: str, arguments=None):
    result = await client.call_tool(name, arguments or {})
    if result.is_error:
        text = result.content[0].text if result.content else ""
        raise RuntimeError(text)
    if result.structured_content:
        return result.structured_content
    return json.loads(result.content[0].text)


def _hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _file_state(root: Path) -> dict[str, tuple[str, int, int]]:
    return {
        str(path.relative_to(root)): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


CONTEXT_QUERY_TOOL_NAMES = (
    "context_foundation_health",
    "context_sources_for_actor",
    "decision_list",
    "decision_get",
    "project_map_validate",
    "project_map_resolve_anchor",
    "current_work_index",
)


def test_server_exposes_readonly_tools_and_instructions(tmp_path: Path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as (client, initialization):
            tools = await client.list_tools()
            assert tuple(tool.name for tool in tools.tools) == mcp_server.OBSERVABILITY_TOOL_ALLOWLIST
            assert initialization.instructions == mcp_server.OBSERVABILITY_INSTRUCTIONS
            health = await call(client, "control_plane_health")
            assert health["read_only_domain_surface"] is True
            assert health["server"] == "hmasd_observability"

    run(scenario)


def test_context_query_mcp_has_no_mutating_tool(tmp_path: Path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as (client, _initialization):
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert set(CONTEXT_QUERY_TOOL_NAMES) <= names
            assert "decision_write" not in names
            assert "project_map_write" not in names
            assert "current_work_write" not in names

    run(scenario)


def test_context_query_tools_are_enabled_only_for_observability() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((repo_root / ".codex/config.toml").read_text(encoding="utf-8"))
    servers = config["mcp_servers"]
    observability = tuple(servers["hmasd_observability"]["enabled_tools"])
    orchestrator = set(servers["hmasd_orchestrator"]["enabled_tools"])
    assert observability == mcp_server.OBSERVABILITY_TOOL_ALLOWLIST
    assert set(CONTEXT_QUERY_TOOL_NAMES).isdisjoint(orchestrator)


def _copy_context_fixture(source: Path, target: Path) -> None:
    paths = [
        Path("docs/project/PROJECT_MAP.md"),
        Path("docs/project/CURRENT_WORK.md"),
        Path("docs/project/CONTEXT_SOURCE_REGISTRY.toml"),
        Path("docs/project/DECISIONS_INDEX.md"),
        Path("docs/project/CONTEXT_PRECEDENCE.md"),
        Path("docs/project/CONTEXT_RETENTION_POLICY.md"),
        Path("docs/project/LOW_INTRUSION_CONTROL_PLANE.md"),
        Path("docs/project/PROJECT_REQUIREMENTS.toml"),
        Path("docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md"),
        Path("docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md"),
        Path("docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md"),
        Path("docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md"),
        Path(
            "docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/"
            "ACTOR_CONTEXT_AND_COMPACTION_CONTRACT.md"
        ),
    ]
    paths.extend(
        path.relative_to(source)
        for path in sorted((source / "docs/project/decisions").glob("ADR-*.md"))
    )
    for relative in paths:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)


def test_seven_context_query_tools_mutate_no_repository_sqlite_or_runtime_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    isolated = tmp_path / "repo"
    _copy_context_fixture(repo_root, isolated)
    sqlite = isolated / "runtime/context.sqlite3"
    sqlite.parent.mkdir(parents=True, exist_ok=True)
    sqlite.write_bytes(b"not-a-database-readonly-sentinel")
    runtime_state = isolated / "runtime/observer/state.json"
    runtime_state.parent.mkdir(parents=True, exist_ok=True)
    runtime_state.write_text('{"sentinel": true}\n', encoding="utf-8")
    before = _file_state(isolated)

    def forbid_sqlite_open(*_args, **_kwargs):
        raise AssertionError("context query tools must not open SQLite")

    monkeypatch.setattr(sqlite3, "connect", forbid_sqlite_open)

    async def scenario():
        async with connected_server(isolated) as (client, _initialization):
            await call(client, "context_foundation_health")
            await call(
                client,
                "context_sources_for_actor",
                {"actor": "CM", "requested_ids": []},
            )
            await call(client, "decision_list")
            await call(client, "decision_get", {"decision_id": "ADR-0001"})
            await call(client, "project_map_validate")
            await call(
                client,
                "project_map_resolve_anchor",
                {"anchor": "Codex App Server runtime plane"},
            )
            await call(client, "current_work_index")

    run(scenario)
    assert _file_state(isolated) == before


def test_doctor_wrapper_matches_collector_and_mutates_no_source(tmp_path: Path) -> None:
    registration = begin_mcp_instance(
        tmp_path, server_name="fixture", profile="test"
    )
    start_path = registration.instance_root / "start.json"
    before = start_path.read_bytes()
    direct, direct_code = collect_doctor(tmp_path, component="mcp-runtime")

    async def scenario():
        async with connected_server(tmp_path) as (client, _initialization):
            wrapped = await call(
                client,
                "control_plane_doctor",
                {"component": "mcp-runtime", "limit": 100},
            )
            assert wrapped["schema"] == direct["schema"]
            assert wrapped["status"] == direct["status"]
            assert wrapped["sources"] == direct["sources"]
            assert wrapped["counters"] == direct["counters"]
            assert wrapped["findings"] == direct["findings"]
            assert wrapped["diagnostic_exit_code"] == direct_code

    run(scenario)
    assert start_path.read_bytes() == before
    registration.close()


def test_paths_are_repo_scoped_and_limit_is_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    first = begin_mcp_instance(repo, server_name="one", profile="test")
    second = begin_mcp_instance(repo, server_name="two", profile="test")
    outside = tmp_path / "outside"
    outside.mkdir()

    async def scenario():
        async with connected_server(repo) as (client, _initialization):
            escaped = await client.call_tool(
                "long_effect_observe", {"run_root": str(outside)}
            )
            assert escaped.is_error
            invalid_limit = await client.call_tool(
                "mcp_instance_list", {"limit": 0}
            )
            assert invalid_limit.is_error
            bounded = await call(client, "mcp_instance_list", {"limit": 1})
            assert bounded["truncated"] is True
            assert bounded["total_items"] == 2
            assert len(bounded["instances"]) == 1

    run(scenario)
    first.close()
    second.close()


def test_missing_source_is_unavailable_and_long_effect_logs_are_not_read(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "runtime/long/run-1"
    run_root.mkdir(parents=True)
    (run_root / "experiment.json").write_text(
        json.dumps(
            {
                "schema": "HMASD_LONG_EFFECT_V1",
                "experiment_id": "00000000-0000-4000-8000-000000000001",
                "component": "canary",
                "metadata": {"direction_id": None, "stage": None, "effect_id": None},
                "output_refs": [{"name": "secret", "path": str(tmp_path / "result.json")}],
            }
        ),
        encoding="utf-8",
    )
    (run_root / "owner.json").write_text(
        json.dumps({"owner_pid": 1, "acquired_at": "2026-08-20T00:00:00Z"}),
        encoding="utf-8",
    )
    (run_root / "stdout.log").write_text("SECRET SCIENCE 99.1", encoding="utf-8")
    (run_root / "stderr.log").write_text("SECRET ERROR BODY", encoding="utf-8")
    before = _hashes(tmp_path)

    async def scenario():
        async with connected_server(tmp_path) as (client, _initialization):
            missing = await call(
                client, "control_plane_doctor", {"component": "semantic"}
            )
            assert missing["status"] == "UNAVAILABLE"
            observed = await call(
                client, "long_effect_observe", {"run_root": str(run_root)}
            )
            encoded = json.dumps(observed)
            assert observed["owner_without_terminal"] is True
            assert "output_refs" not in encoded
            assert "SECRET SCIENCE" not in encoded
            assert "SECRET ERROR BODY" not in encoded
            assert "99.1" not in encoded

    run(scenario)
    assert _hashes(tmp_path) == before
