"""Focused contracts for the explicit native-child semantic wait bridge."""

from __future__ import annotations

import asyncio

import anyio
import pytest

from tools.codex_semantic_mvp import mcp_server
from tools.codex_semantic_mvp import cli
from tools.codex_semantic_mvp.store import SemanticStore


def run(coro):
    return anyio.run(coro)


def _opened_store(tmp_path):
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    workflow_id = store.open_workflow(
        session_id="native-bridge-session",
        opened_turn_id="turn-1",
        scope="test",
        objective="native bridge test",
    )
    return store, workflow_id


def _register(store: SemanticStore, workflow_id: str) -> None:
    store.register_native_child_bridge(
        workflow_id,
        "cm-direction",
        "agent-cm-direction",
        "cm",
        "complete the frozen technical milestone",
    )


def test_registered_native_task_projects_to_semantic_wait_plan(tmp_path):
    store, workflow_id = _opened_store(tmp_path)
    try:
        _register(store, workflow_id)
        plan = mcp_server.workflow_wait_plan_for_session(
            store, "native-bridge-session", timeout_s=321
        )
        state = store.workflow_state(workflow_id)
        assert plan == {
            "schema": "HMASD_WORKFLOW_WAIT_PLAN_V1",
            "action": "WAIT_SEMANTIC_EVENT",
            "workflow_id": workflow_id,
            "condition": "ANY_REPORT",
            "after_seq": state["await_cursor"],
            "task_ids": ["cm-direction"],
            "timeout_s": 321,
            "reason_code": "OPEN_TASKS_AWAITING_REPORT",
        }
    finally:
        store.close()


def test_native_completion_wakes_at_the_exact_await_cursor(tmp_path):
    async def scenario():
        store, workflow_id = _opened_store(tmp_path)
        try:
            _register(store, workflow_id)
            cursor = store.workflow_state(workflow_id)["await_cursor"]

            async def signal():
                await asyncio.sleep(0.05)
                return store.record_native_child_signal(
                    workflow_id,
                    "cm-direction",
                    "agent-cm-direction",
                    "cm",
                    "signal-1",
                    "COMPLETED",
                )

            waited, recorded = await asyncio.gather(
                mcp_server.await_events(
                    store,
                    workflow_id,
                    after_seq=cursor,
                    condition="ANY_REPORT",
                    task_ids=["cm-direction"],
                    timeout_s=2,
                ),
                signal(),
            )
            assert waited["status"] == "EVENT"
            assert waited["events"] == [
                {
                    "seq": waited["cursor"],
                    "kind": "NATIVE_CHILD_REPORT_AVAILABLE",
                    "disposition_implied": False,
                    "task_id": "cm-direction",
                }
            ]
            assert recorded["idempotent"] is False
            assert waited["cursor"] > cursor
        finally:
            store.close()

    run(scenario)


def test_native_anomaly_is_a_report_event_without_a_disposition(tmp_path):
    store, workflow_id = _opened_store(tmp_path)
    try:
        _register(store, workflow_id)
        recorded = store.record_native_child_signal(
            workflow_id,
            "cm-direction",
            "agent-cm-direction",
            "cm",
            "signal-anomaly",
            "ANOMALY",
        )
        report = store.connection.execute(
            "SELECT raw_message FROM reports WHERE report_id = ?", (recorded["report_id"],)
        ).fetchone()
        event = store.events_after(workflow_id, 0)[-1]
        assert '"outcome":"ANOMALY"' in str(report["raw_message"])
        assert event["kind"] == "NATIVE_CHILD_REPORT_AVAILABLE"
        assert event["disposition_implied"] is False
        assert mcp_server.workflow_wait_plan_for_session(
            store, "native-bridge-session"
        )["action"] == "REPORT_INTAKE_REQUIRED"
    finally:
        store.close()


def test_cancelled_workflow_is_neither_bridged_nor_waited(tmp_path):
    store, workflow_id = _opened_store(tmp_path)
    try:
        _register(store, workflow_id)
        with store._lock, store.connection:
            store._touch_workflow(workflow_id, "CANCELLED")
        assert mcp_server.workflow_wait_plan_for_session(
            store, "native-bridge-session"
        )["action"] == "NO_ACTIVE_WORKFLOW"
        with pytest.raises(ValueError, match="ACTIVE workflow"):
            store.record_native_child_signal(
                workflow_id,
                "cm-direction",
                "agent-cm-direction",
                "cm",
                "signal-cancelled",
                "COMPLETED",
            )
    finally:
        store.close()


def test_native_signal_is_idempotent_and_does_not_append_a_second_event(tmp_path):
    store, workflow_id = _opened_store(tmp_path)
    try:
        _register(store, workflow_id)
        first = store.record_native_child_signal(
            workflow_id,
            "cm-direction",
            "agent-cm-direction",
            "cm",
            "stable-signal",
            "COMPLETED",
        )
        before = store.workflow_state(workflow_id)["await_cursor"]
        second = store.record_native_child_signal(
            workflow_id,
            "cm-direction",
            "agent-cm-direction",
            "cm",
            "stable-signal",
            "COMPLETED",
        )
        assert second == {**first, "idempotent": True}
        assert store.workflow_state(workflow_id)["await_cursor"] == before
        with pytest.raises(ValueError, match="not running"):
            store.record_native_child_signal(
                workflow_id,
                "cm-direction",
                "agent-cm-direction",
                "cm",
                "different-signal",
                "ANOMALY",
            )
    finally:
        store.close()


def test_native_bridge_routing_instructions_are_explicit():
    instructions = mcp_server.ORCHESTRATOR_INSTRUCTIONS
    assert "native_child_register" in instructions
    assert "native-child-signal" in instructions
    assert "collaboration.wait_agent" in instructions
    assert "await_cursor" in instructions


def test_native_child_signal_cli_has_no_result_payload(tmp_path, capsys):
    store, workflow_id = _opened_store(tmp_path)
    try:
        _register(store, workflow_id)
    finally:
        store.close()
    status = cli.main(
        [
            "--state-dir",
            str(tmp_path),
            "native-child-signal",
            "--workflow-id",
            workflow_id,
            "--task-id",
            "cm-direction",
            "--agent-id",
            "agent-cm-direction",
            "--agent-type",
            "cm",
            "--signal-id",
            "cli-signal",
            "--outcome",
            "COMPLETED",
        ]
    )
    output = capsys.readouterr().out
    assert status == 0
    assert "report_id" in output
    assert "result" not in output
