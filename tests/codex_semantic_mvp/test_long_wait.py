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
