"""Focused long-wait cursor tests for the semantic MVP."""

import asyncio
import json
import time
from contextlib import asynccontextmanager

import anyio
import pytest
from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tools.codex_semantic_mvp import mcp_server
from tools.codex_context_lifecycle.authority import bind_requester
from tools.codex_semantic_mvp.actor_registry import register_session_root


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


async def open_workflow(client):
    return (
        await call(
            client,
            "workflow_open",
            {
                "session_id": "long-wait-session",
                "opened_turn_id": "turn-1",
                "scope": "test",
                "objective": "exercise long wait",
            },
        )
    )["workflow_id"]


def test_immediate_event_returns_neutral_summary_and_advances_cursor(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "emit report",
                },
            )
            store = mcp_server._get_store()
            store.record_untyped_return(workflow_id, "child", "agent", "worker", "secret raw text")
            result = await call(
                client,
                "workflow_await_event",
                {"workflow_id": workflow_id, "after_seq": 0, "condition": "ANY_REPORT", "timeout_s": 1},
            )
            assert result["status"] == "EVENT"
            assert result["cursor"] > 0
            assert len(result["events"]) == 1
            assert "raw_message" not in json.dumps(result)
            assert "secret raw text" not in json.dumps(result)

    run(scenario)


def test_delayed_event_is_observed_by_one_runtime_wait(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "emit report",
                },
            )
            store = mcp_server._get_store()

            async def delayed_insert():
                await asyncio.sleep(1)
                store.record_untyped_return(workflow_id, "child", "agent", "worker", "delayed")

            started = time.monotonic()
            result, _ = await asyncio.gather(
                call(
                    client,
                    "workflow_await_event",
                    {"workflow_id": workflow_id, "after_seq": 0, "condition": "ANY_REPORT", "timeout_s": 5},
                ),
                delayed_insert(),
            )
            elapsed = time.monotonic() - started
            assert 0.8 <= elapsed <= 2.5
            assert result["status"] == "EVENT"
            assert len(result["events"]) == 1

    run(scenario)


def test_timeout_is_neutral_and_cancellation_does_not_mutate_state(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            before = await call(client, "workflow_state", {"workflow_id": workflow_id})
            timeout = await call(
                client,
                "workflow_await_event",
                {"workflow_id": workflow_id, "after_seq": 0, "condition": "ANY_REPORT", "timeout_s": 1},
            )
            assert timeout["status"] == "TIMEOUT_NO_DISPOSITION"
            assert set(timeout) >= {"status", "cursor", "open_tasks", "open_obligations"}

            task = asyncio.create_task(
                call(
                    client,
                    "workflow_await_event",
                    {"workflow_id": workflow_id, "after_seq": 0, "condition": "ANY_REPORT", "timeout_s": 5},
                )
            )
            await asyncio.sleep(0.05)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            after = await call(client, "workflow_state", {"workflow_id": workflow_id})
            assert after == before

    run(scenario)


@pytest.mark.parametrize(
    "arguments",
    [
        {"timeout_s": 0},
        {"timeout_s": 1501},
        {"condition": "UNKNOWN"},
    ],
)
def test_invalid_wait_bounds_and_condition_are_rejected(tmp_path, arguments):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            result = await client.call_tool(
                "workflow_await_event",
                {"workflow_id": workflow_id, **arguments},
            )
            assert result.is_error

    run(scenario)


def test_wait_holds_no_sqlite_transaction_across_sleep(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "emit report",
                },
            )
            store = mcp_server._get_store()
            cursor = store.workflow_state(workflow_id)["await_cursor"]
            waiter = asyncio.create_task(
                call(
                    client,
                    "workflow_await_event",
                    {
                        "workflow_id": workflow_id,
                        "after_seq": cursor,
                        "condition": "ANY_REPORT",
                        "timeout_s": 5,
                    },
                )
            )
            await asyncio.sleep(0.1)
            assert store.connection.in_transaction is False

            from tools.codex_semantic_mvp.store import SemanticStore

            writer = SemanticStore(store.path).initialize()
            try:
                writer.record_untyped_return(
                    workflow_id, "child", "agent", "worker", "cross-connection"
                )
            finally:
                writer.close()
            result = await waiter
            assert result["status"] == "EVENT"
            assert result["events"][0]["task_id"] == "child"

    run(scenario)


def test_await_tool_schema_exposes_closed_condition_enum(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            tools = await client.list_tools()
            await_tool = next(tool for tool in tools.tools if tool.name == "workflow_await_event")
            condition_schema = await_tool.input_schema["properties"]["condition"]
            assert condition_schema["enum"] == [
                "ANY_REPORT",
                "ALL_REQUIRED_RETURNED",
                "OPEN_OBLIGATION_CHANGED",
                "WORKFLOW_QUIESCENT",
            ]
            assert condition_schema["default"] == "ANY_REPORT"

    run(scenario)


def test_await_runtime_keeps_server_side_condition_validation(tmp_path):
    async def scenario():
        mcp_server.build_server(tmp_path)
        store = mcp_server._get_store()
        with pytest.raises(
            ValueError,
            match="unknown await condition: decision-level report from recovery owner",
        ):
            await mcp_server.await_events(
                store,
                "uncreated-workflow",
                condition="decision-level report from recovery owner",
                timeout_s=1,
            )
        assert store.events_after(None) == []

    run(scenario)


def test_state_and_current_expose_await_cursor_not_state_version(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            before = await call(client, "workflow_state", {"workflow_id": workflow_id})
            mcp_server._get_store().append_event(
                workflow_id, "CURSOR_CANARY", "subject", {}, "cursor-canary"
            )
            state = await call(client, "workflow_state", {"workflow_id": workflow_id})
            current = await call(client, "workflow_current", {"session_id": "long-wait-session"})

            assert state["state_version"] == before["state_version"]
            assert state["await_cursor"] > before["await_cursor"]
            assert state["await_cursor"] != state["state_version"]
            assert current["await_cursor"] == state["await_cursor"]

    run(scenario)


def test_task_ids_must_belong_to_workflow(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            result = await client.call_tool(
                "workflow_await_event",
                {
                    "workflow_id": workflow_id,
                    "condition": "ANY_REPORT",
                    "task_ids": ["not-registered"],
                    "timeout_s": 1,
                },
            )
            assert result.is_error

    run(scenario)


def test_store_exposes_cursor_first_await_events(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            store = mcp_server._get_store()
            store.append_event(workflow_id, "CANARY", "subject", {}, "canary-await-events")
            events = store.await_events(workflow_id, after_seq=0)
            assert [event["kind"] for event in events] == ["WORKFLOW_OPENED", "CANARY"]

    run(scenario)


def test_wait_plan_covers_all_actions_with_fixed_priority(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            none = await call(
                client, "workflow_wait_plan", {"session_id": "no-workflow"}
            )
            assert none == {
                "schema": "HMASD_WORKFLOW_WAIT_PLAN_V1",
                "action": "NO_ACTIVE_WORKFLOW",
                "workflow_id": None,
                "condition": None,
                "after_seq": None,
                "task_ids": [],
                "timeout_s": None,
                "reason_code": "NO_ACTIVE_WORKFLOW",
            }

            close_workflow = (
                await call(
                    client,
                    "workflow_open",
                    {
                        "session_id": "close-session",
                        "opened_turn_id": "turn",
                        "scope": "test",
                        "objective": "close",
                    },
                )
            )["workflow_id"]
            close_plan = await call(
                client, "workflow_wait_plan", {"session_id": "close-session"}
            )
            assert close_plan["action"] == "WORKFLOW_CLOSE_ELIGIBLE"
            assert close_plan["workflow_id"] == close_workflow

            wait_workflow = (
                await call(
                    client,
                    "workflow_open",
                    {
                        "session_id": "wait-session",
                        "opened_turn_id": "turn",
                        "scope": "test",
                        "objective": "wait",
                    },
                )
            )["workflow_id"]
            await call(
                client,
                "task_register",
                {
                    "workflow_id": wait_workflow,
                    "task_id": "child-wait",
                    "expected_agent_type": "worker",
                    "objective": "return",
                },
            )
            mcp_server._get_store().append_event(
                wait_workflow, "CURSOR_ONLY", "fixture", {}, "wait-plan-cursor-only"
            )
            state_before = await call(
                client, "workflow_state", {"workflow_id": wait_workflow}
            )
            wait_plan = await call(
                client,
                "workflow_wait_plan",
                {"session_id": "wait-session", "timeout_s": 321},
            )
            assert wait_plan["action"] == "WAIT_SEMANTIC_EVENT"
            assert wait_plan["condition"] == "ANY_REPORT"
            assert wait_plan["after_seq"] == state_before["await_cursor"]
            assert wait_plan["after_seq"] != state_before["state_version"]
            assert wait_plan["task_ids"] == ["child-wait"]
            assert wait_plan["timeout_s"] == 321
            assert await call(
                client, "workflow_state", {"workflow_id": wait_workflow}
            ) == state_before

            obligation_workflow = (
                await call(
                    client,
                    "workflow_open",
                    {
                        "session_id": "obligation-session",
                        "opened_turn_id": "turn",
                        "scope": "test",
                        "objective": "obligation",
                    },
                )
            )["workflow_id"]
            await call(
                client,
                "obligation_open",
                {
                    "workflow_id": obligation_workflow,
                    "kind": "USER_DECISION_REQUIRED",
                    "owner": "/root",
                    "subject": "choice",
                    "reason": "choose",
                    "source_ref": "user",
                },
            )
            obligation_plan = await call(
                client,
                "workflow_wait_plan",
                {"session_id": "obligation-session"},
            )
            assert obligation_plan["action"] == "OBLIGATION_ACTION_REQUIRED"

            report_workflow = (
                await call(
                    client,
                    "workflow_open",
                    {
                        "session_id": "report-session",
                        "opened_turn_id": "turn",
                        "scope": "test",
                        "objective": "report",
                    },
                )
            )["workflow_id"]
            await call(
                client,
                "task_register",
                {
                    "workflow_id": report_workflow,
                    "task_id": "child-report",
                    "expected_agent_type": "worker",
                    "objective": "return",
                },
            )
            mcp_server._get_store().record_untyped_return(
                report_workflow, "child-report", "agent", "worker", "private"
            )
            report_plan = await call(
                client,
                "workflow_wait_plan",
                {"session_id": "report-session"},
            )
            assert report_plan["action"] == "REPORT_INTAKE_REQUIRED"
            assert report_plan["task_ids"] == ["child-report"]
            assert report_plan["condition"] is None
            assert report_plan["after_seq"] is None

    run(scenario)


def test_wait_plan_schema_and_server_instructions_lock_native_routing(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            tools = await client.list_tools()
            assert tuple(tool.name for tool in tools.tools) == mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST
            wait_plan = next(tool for tool in tools.tools if tool.name == "workflow_wait_plan")
            timeout_schema = wait_plan.input_schema["properties"]["timeout_s"]
            assert timeout_schema["default"] == 900
            assert "collaboration.wait_agent" in mcp_server.ORCHESTRATOR_INSTRUCTIONS
            assert "workflow_wait_plan" in mcp_server.ORCHESTRATOR_INSTRUCTIONS
            assert "await_cursor" in mcp_server.ORCHESTRATOR_INSTRUCTIONS
            assert "state_version" in mcp_server.ORCHESTRATOR_INSTRUCTIONS

    run(scenario)


@pytest.mark.parametrize("timeout_s", [0, 1501, 1.5, True])
def test_wait_plan_timeout_is_strict(tmp_path, timeout_s):
    async def scenario():
        async with connected_server(tmp_path) as client:
            result = await client.call_tool(
                "workflow_wait_plan",
                {"session_id": "session", "timeout_s": timeout_s},
            )
            assert result.is_error

    run(scenario)


def test_all_required_returned_is_immediate_when_state_is_already_satisfied(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "return",
                },
            )
            store = mcp_server._get_store()
            store.record_untyped_return(workflow_id, "child", "agent", "worker", "returned")
            after_seq = store.events_after(workflow_id, 0)[-1]["seq"]

            result = await call(
                client,
                "workflow_await_event",
                {
                    "workflow_id": workflow_id,
                    "after_seq": after_seq,
                    "condition": "ALL_REQUIRED_RETURNED",
                    "timeout_s": 1,
                },
            )
            assert result == {"status": "EVENT", "cursor": after_seq, "events": []}

    run(scenario)


def test_all_required_returned_is_observed_when_state_changes_during_wait(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "return",
                },
            )
            store = mcp_server._get_store()
            after_seq = store.events_after(workflow_id, 0)[-1]["seq"]

            async def delayed_return():
                await asyncio.sleep(1)
                store.record_untyped_return(workflow_id, "child", "agent", "worker", "returned")

            started = time.monotonic()
            result, _ = await asyncio.gather(
                call(
                    client,
                    "workflow_await_event",
                    {
                        "workflow_id": workflow_id,
                        "after_seq": after_seq,
                        "condition": "ALL_REQUIRED_RETURNED",
                        "timeout_s": 5,
                    },
                ),
                delayed_return(),
            )
            assert 0.8 <= time.monotonic() - started <= 2.5
            assert result["status"] == "EVENT"
            assert result["cursor"] > after_seq
            assert result["events"] == []

    run(scenario)


def test_workflow_quiescent_state_predicate_is_immediate_and_delayed(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            store = mcp_server._get_store()
            initial_cursor = store.events_after(workflow_id, 0)[-1]["seq"]
            immediate = await call(
                client,
                "workflow_await_event",
                {
                    "workflow_id": workflow_id,
                    "after_seq": initial_cursor,
                    "condition": "WORKFLOW_QUIESCENT",
                    "timeout_s": 1,
                },
            )
            assert immediate == {"status": "EVENT", "cursor": initial_cursor, "events": []}

            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "return then intake",
                },
            )
            report_id = store.record_untyped_return(
                workflow_id, "child", "agent", "worker", "returned"
            )
            after_seq = store.events_after(workflow_id, 0)[-1]["seq"]

            async def delayed_intake():
                await asyncio.sleep(1)
                await call(
                    client,
                    "root_record_intake",
                    {
                        "workflow_id": workflow_id,
                        "report_id": report_id,
                        "intake_kind": "INTEGRATE",
                        "translation": {
                            "exact_observed_fact": "returned",
                            "exact_object": "child",
                            "remaining_unknown": "none",
                            "global_effect": "NONE",
                        },
                    },
                )

            started = time.monotonic()
            delayed, _ = await asyncio.gather(
                call(
                    client,
                    "workflow_await_event",
                    {
                        "workflow_id": workflow_id,
                        "after_seq": after_seq,
                        "condition": "WORKFLOW_QUIESCENT",
                        "timeout_s": 5,
                    },
                ),
                delayed_intake(),
            )
            assert 0.8 <= time.monotonic() - started <= 2.5
            assert delayed["status"] == "EVENT"
            assert delayed["cursor"] > after_seq
            assert delayed["events"] == []
            assert store.is_workflow_quiescent(workflow_id) is True

    run(scenario)


def test_open_obligation_changed_emits_automatic_open_and_resolution_events(tmp_path):
    async def scenario():
        async with connected_server(tmp_path) as client:
            workflow_id = await open_workflow(client)
            await call(
                client,
                "task_register",
                {
                    "workflow_id": workflow_id,
                    "task_id": "child",
                    "expected_agent_type": "worker",
                    "objective": "return then intake",
                },
            )
            store = mcp_server._get_store()
            registered_cursor = store.events_after(workflow_id, 0)[-1]["seq"]

            async def delayed_report():
                await asyncio.sleep(1)
                return store.record_untyped_return(
                    workflow_id, "child", "agent", "worker", "returned"
                )

            opened, report_id = await asyncio.gather(
                call(
                    client,
                    "workflow_await_event",
                    {
                        "workflow_id": workflow_id,
                        "after_seq": registered_cursor,
                        "condition": "OPEN_OBLIGATION_CHANGED",
                        "timeout_s": 5,
                    },
                ),
                delayed_report(),
            )
            assert opened["status"] == "EVENT"
            assert opened["events"][0]["kind"] == "OBLIGATION_OPENED"

            after_open = store.events_after(workflow_id, 0)[-1]["seq"]

            async def delayed_intake():
                await asyncio.sleep(1)
                await call(
                    client,
                    "root_record_intake",
                    {
                        "workflow_id": workflow_id,
                        "report_id": report_id,
                        "intake_kind": "INTEGRATE",
                        "translation": {
                            "exact_observed_fact": "returned",
                            "exact_object": "child",
                            "remaining_unknown": "none",
                            "global_effect": "NONE",
                        },
                    },
                )

            resolved, _ = await asyncio.gather(
                call(
                    client,
                    "workflow_await_event",
                    {
                        "workflow_id": workflow_id,
                        "after_seq": after_open,
                        "condition": "OPEN_OBLIGATION_CHANGED",
                        "timeout_s": 5,
                    },
                ),
                delayed_intake(),
            )
            assert resolved["status"] == "EVENT"
            assert resolved["events"][0]["kind"] == "OBLIGATION_RESOLVED"

    run(scenario)
