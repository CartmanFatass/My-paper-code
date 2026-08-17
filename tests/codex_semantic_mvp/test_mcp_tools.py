"""In-memory MCP v2 coverage for the basic semantic workflow tools."""

import asyncio
import json
from contextlib import asynccontextmanager

import anyio
import pytest

from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tools.codex_semantic_mvp import mcp_server


def run(coro):
    return anyio.run(coro)


@asynccontextmanager
async def connected_server(state_dir):
    server = mcp_server.build_server(state_dir)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as tg:
            tg.start_soon(
                server._lowlevel_server.run,
                server_streams[0],
                server_streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client_streams) as client:
                await client.initialize()
                yield client
                tg.cancel_scope.cancel()


async def call(client, name, arguments=None):
    result = await client.call_tool(name, arguments or {})
    if result.is_error:
        text = result.content[0].text if result.content else ""
        raise RuntimeError(text)
    if result.structured_content:
        return result.structured_content
    return json.loads(result.content[0].text)


def test_runtime_health_and_workflow_open(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            health = await call(client, "runtime_health")
            assert health["status"] == "OK"
            assert health["ledger_role"] == "control_plane_delivery_and_obligation_ledger"
            opened = await call(client, "workflow_open", {
                "session_id": "session-1",
                "opened_turn_id": "turn-1",
                "scope": "test",
                "objective": "exercise basic tools",
            })
            assert opened["workflow_id"].startswith("wf_")
            current = await call(client, "workflow_current", {"session_id": "session-1"})
            assert current["workflow_id"] == opened["workflow_id"]
            assert current["state"] == "ACTIVE"
            assert current["state_version"] >= 1
    run(scenario)


def test_duplicate_active_workflow_is_rejected(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            args = {"session_id": "session-1", "opened_turn_id": "turn-1", "scope": "test", "objective": "one"}
            await call(client, "workflow_open", args)
            result = await client.call_tool("workflow_open", {**args, "opened_turn_id": "turn-2"})
            assert result.is_error
    run(scenario)


def test_task_register_footer_and_bind_running_state(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            opened = await call(client, "workflow_open", {
                "session_id": "s", "opened_turn_id": "t", "scope": "x", "objective": "y"
            })
            wf = opened["workflow_id"]
            registered = await call(client, "task_register", {
                "workflow_id": wf, "task_id": "child", "expected_agent_type": "worker",
                "objective": "inspect", "required": True,
            })
            assert f"workflow_id={wf}" in registered["footer"]
            assert "task_id=child" in registered["footer"]
            assert "return_schema=HMASD_SUBAGENT_RETURN_V1" in registered["footer"]
            assert "global_disposition_authority=none" in registered["footer"]
            await call(client, "task_bind", {
                "workflow_id": wf, "task_id": "child", "agent_id": "agent-1", "agent_type": "worker"
            })
            state = await call(client, "workflow_state", {"workflow_id": wf})
            assert state["tasks"][0]["lifecycle"] == "RUNNING"
    run(scenario)


def test_root_record_intake_and_explicit_portfolio_obligation(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            wf = (await call(client, "workflow_open", {
                "session_id": "s", "opened_turn_id": "t", "scope": "x", "objective": "y"
            })) ["workflow_id"]
            await call(client, "task_register", {
                "workflow_id": wf, "task_id": "child", "expected_agent_type": "worker",
                "objective": "inspect", "required": True,
            })
            packet = {
                "schema_version": "1.0", "packet_kind": "SUBAGENT_RETURN", "workflow_id": wf,
                "task_id": "child", "return_kind": "COMPLETED_ASSIGNMENT", "observed_facts": [],
                "interpretive_claims": [], "remaining_unknowns": [], "suggested_next_actions": [],
                "research_frontier": None, "global_disposition": "NOT_ASSERTED",
            }
            report_id = mcp_server._get_store().record_report(
                wf, "child", "agent-1", "worker", "child report", packet
            )
            intake = await call(client, "root_record_intake", {
                "workflow_id": wf, "report_id": report_id, "intake_kind": "INTEGRATE",
                "translation": {"exact_observed_fact": "fact", "exact_object": "object", "remaining_unknown": "none", "global_effect": "NONE"},
                "next_action": {"owner": "/root", "action": "close"}, "note": "intaked",
            })
            assert intake["intake_id"].startswith("intake_")
            opened = await call(client, "obligation_open", {
                "workflow_id": wf, "kind": "PORTFOLIO_REVIEW_REQUIRED", "owner": "portfolio",
                "subject": "direction:test", "reason": "review", "source_ref": "stage:test",
            })
            assert opened["kind"] == "PORTFOLIO_REVIEW_REQUIRED"
    run(scenario)


def test_invalid_obligation_and_close_with_open_obligation_rejected(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            wf = (await call(client, "workflow_open", {
                "session_id": "s", "opened_turn_id": "t", "scope": "x", "objective": "y"
            })) ["workflow_id"]
            invalid = await client.call_tool("obligation_open", {
                "workflow_id": wf, "kind": "NOT_A_KIND", "owner": "x", "subject": "x",
                "reason": "x", "source_ref": "x",
            })
            assert invalid.is_error
            await call(client, "obligation_open", {
                "workflow_id": wf, "kind": "PORTFOLIO_REVIEW_REQUIRED", "owner": "portfolio",
                "subject": "direction:test", "reason": "review", "source_ref": "stage:test",
            })
            close = await client.call_tool("workflow_close", {
                "workflow_id": wf, "closure_kind": "COMPLETED", "summary": "done",
            })
            assert close.is_error
    run(scenario)
