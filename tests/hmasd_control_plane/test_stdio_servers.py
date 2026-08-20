from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tools.codex_semantic_mvp.mcp_server import ORCHESTRATOR_TOOL_ALLOWLIST
from tools.codex_semantic_mvp.store import SemanticStore
from tools.hmasd_control_plane.mcp_runtime import inspect_mcp_instances
from tools.hmasd_control_plane.mcp_server import OBSERVABILITY_TOOL_ALLOWLIST


PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
REPO_ROOT = Path(__file__).resolve().parents[2]


def run(coro):
    return anyio.run(coro)


def _environment(repo_root: Path, state_dir: Path | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment["HMASD_REPO_ROOT"] = str(repo_root)
    if state_dir is not None:
        environment["HMASD_CODEX_MVP_STATE_DIR"] = str(state_dir)
    return environment


async def _call(client: ClientSession, name: str, arguments=None) -> dict:
    result = await client.call_tool(name, arguments or {})
    assert not result.is_error, result.content
    if result.structured_content:
        return dict(result.structured_content)
    return json.loads(result.content[0].text)


def test_two_real_observability_stdio_instances_are_distinct_and_close(
    tmp_path: Path,
) -> None:
    parameters = StdioServerParameters(
        command=PYTHON,
        args=[
            "-m",
            "tools.hmasd_control_plane.mcp_server",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=_environment(tmp_path),
    )

    async def scenario() -> tuple[str, str]:
        async with stdio_client(parameters) as first_streams:
            async with ClientSession(*first_streams) as first:
                first_init = await first.initialize()
                assert "read-only" in (first_init.instructions or "")
                assert tuple(
                    tool.name for tool in (await first.list_tools()).tools
                ) == OBSERVABILITY_TOOL_ALLOWLIST
                first_health = await _call(first, "control_plane_health")
                async with stdio_client(parameters) as second_streams:
                    async with ClientSession(*second_streams) as second:
                        await second.initialize()
                        second_health = await _call(second, "control_plane_health")
                        index = await _call(first, "mcp_instance_list")
                        active = [
                            item
                            for item in index["instances"]
                            if item["server_name"] == "hmasd_observability"
                            and item["status"] == "ACTIVE"
                        ]
                        assert len(active) == 2
                        assert first_health["instance_id"] != second_health["instance_id"]
                        return first_health["instance_id"], second_health["instance_id"]

    first_id, second_id = run(scenario)
    index = inspect_mcp_instances(tmp_path)
    selected = {
        item["instance_id"]: item
        for item in index["instances"]
        if item["instance_id"] in {first_id, second_id}
    }
    assert set(selected) == {first_id, second_id}
    assert {item["status"] for item in selected.values()} == {"CLOSED"}


def test_real_orchestrator_stdio_wait_plan_is_read_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "semantic-state"
    state_path = state_dir / "state.sqlite3"
    SemanticStore(state_path).initialize().close()
    before = hashlib.sha256(state_path.read_bytes()).hexdigest()
    parameters = StdioServerParameters(
        command=PYTHON,
        args=["-m", "tools.codex_semantic_mvp.mcp_server"],
        cwd=REPO_ROOT,
        env=_environment(tmp_path, state_dir),
    )

    async def scenario() -> str:
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as client:
                initialization = await client.initialize()
                assert "workflow_wait_plan first" in (initialization.instructions or "")
                assert tuple(
                    tool.name for tool in (await client.list_tools()).tools
                ) == ORCHESTRATOR_TOOL_ALLOWLIST
                plan = await _call(
                    client,
                    "workflow_wait_plan",
                    {"session_id": "stdio-no-active-workflow"},
                )
                assert plan == {
                    "schema": "HMASD_WORKFLOW_WAIT_PLAN_V1",
                    "action": "NO_ACTIVE_WORKFLOW",
                    "workflow_id": None,
                    "condition": None,
                    "after_seq": None,
                    "task_ids": [],
                    "timeout_s": None,
                    "reason_code": "NO_ACTIVE_WORKFLOW",
                }
                health = await _call(client, "runtime_health")
                return health["instance_id"]

    instance_id = run(scenario)
    after = hashlib.sha256(state_path.read_bytes()).hexdigest()
    assert after == before
    instance = next(
        item
        for item in inspect_mcp_instances(tmp_path)["instances"]
        if item["instance_id"] == instance_id
    )
    assert instance["status"] == "CLOSED"
