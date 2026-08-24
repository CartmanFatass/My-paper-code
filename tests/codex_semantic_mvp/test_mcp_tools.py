"""In-memory MCP v2 coverage for the basic semantic workflow tools."""

import asyncio
import json
from contextlib import asynccontextmanager

import anyio
import pytest

from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tools.codex_semantic_mvp import mcp_server
from tools.codex_context_lifecycle.authority import bind_requester, grant_user_authority
from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import _insert_actor, register_session_root


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
    arguments = dict(arguments or {})
    if name in mcp_server.MUTATING_TOOL_NAMES and "requester_actor_context_id" not in arguments:
        store = mcp_server._get_store()
        if name == "workflow_open":
            actor = register_session_root(store, session_id=arguments["session_id"])
            requester = actor.actor_context_id
        elif "workflow_id" in arguments:
            requester = mcp_server._workflow_owner(store, arguments["workflow_id"])
        else:  # pragma: no cover - this helper only exercises Root workflow tools
            raise AssertionError(f"test helper cannot infer owner for {name}")
        bind_requester(requester)
        arguments.update(
            source_kind="ROLE_CONTRACT",
            requester_actor_context_id=requester,
        )
    result = await client.call_tool(name, arguments)
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
            actor = await call(client, "actor_context_current", {"session_id": "session-1"})
            assert actor["actor_context"]["actor_kind"] == "OPERATIONAL_ROOT"
            assert actor["workflow"]["workflow_id"] == opened["workflow_id"]
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


def test_session_root_cutover_is_explicit_and_preserves_actor_identity(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._get_store()
            session_id = "01a03351-e8ef-7620-b2ab-b77b9512f499"
            actor = _insert_actor(
                store,
                session_id=session_id,
                actor_kind=ActorKind.OPERATIONAL_ROOT,
                scope_key=f"session:{session_id}",
                identity_source="TEST_PRECUTOVER",
                actor_context_id="actor-cutover-mcp",
            )
            bind_requester(actor.actor_context_id)
            grant = grant_user_authority(
                store,
                actor_context_id=actor.actor_context_id,
                operation="change_actor_state",
            )
            result = await call(client, "actor_context_reconcile_session_root", {
                "actor_context_id": actor.actor_context_id,
                "session_id": session_id,
                "cutover_evidence_ref": "docs/session/PORTFOLIO_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260824.md",
                "source_kind": "USER_AUTHORITY",
                "requester_actor_context_id": actor.actor_context_id,
                "user_authority_id": grant["grant_id"],
            })
            assert result["actor_context"] == {
                "actor_context_id": actor.actor_context_id,
                "actor_kind": "PORTFOLIO",
                "session_id": session_id,
                "scope_key": f"session:{session_id}",
                "state": "ACTIVE",
                "identity_source": (
                    "SESSION_ROOT_CUTOVER_MAPPING:"
                    "docs/session/PORTFOLIO_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260824.md"
                ),
            }
            current = await call(client, "actor_context_current", {"session_id": session_id})
            assert current["actor_context"]["actor_context_id"] == actor.actor_context_id
            assert current["actor_context"]["actor_kind"] == "PORTFOLIO"
            assert current["actor_context"]["state"] == "ACTIVE"
    run(scenario)


def test_native_child_register_binds_and_returns_one_terminal_signal_contract(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            wf = (
                await call(client, "workflow_open", {
                    "session_id": "native", "opened_turn_id": "turn", "scope": "test", "objective": "wait"
                })
            )["workflow_id"]
            registered = await call(client, "native_child_register", {
                "workflow_id": wf,
                "task_id": "cm-native",
                "agent_id": "agent-native",
                "agent_type": "cm",
                "objective": "frozen technical milestone",
            })
            assert registered["lifecycle"] == "RUNNING"
            assert registered["signal_id"] == f"native:{wf}:cm-native:agent-native"
            assert "native-child-signal" in registered["signal_command"]
            assert "--outcome COMPLETED|ANOMALY" in registered["signal_command"]
            state = await call(client, "workflow_state", {"workflow_id": wf})
            assert state["tasks"][0]["agent_id"] == "agent-native"
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
