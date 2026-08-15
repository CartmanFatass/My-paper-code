"""MCP v2 server for the repository-local semantic workflow overlay."""

from __future__ import annotations

import asyncio
import json
import math
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping

from mcp.server import MCPServer

from .db import DEFAULT_STATE_PATH
from .constants import MAX_WAIT_SECONDS, WAIT_POLL_SECONDS
from .models import ObligationKind
from .store import CLOSURE_KINDS, SemanticStore


SERVER_NAME = "hmasd_orchestrator"
STATE_ENV = "HMASD_CODEX_MVP_STATE_DIR"
_active_store: SemanticStore | None = None


def _state_path(state_dir: str | Path | None) -> Path:
    if state_dir is None:
        state_dir = os.environ.get(STATE_ENV)
    if state_dir is None and "--state-dir" in sys.argv:
        index = sys.argv.index("--state-dir")
        if index + 1 < len(sys.argv):
            state_dir = sys.argv[index + 1]
    if state_dir is None:
        return DEFAULT_STATE_PATH
    value = Path(state_dir)
    return value / "state.sqlite3" if value.suffix != ".sqlite3" else value


def _get_store() -> SemanticStore:
    if _active_store is None:
        raise RuntimeError("MCP semantic store is not initialized")
    return _active_store


def _jsonable(value: Any) -> Any:
    if isinstance(value, sqlite3.Row):
        return {key: _jsonable(value[key]) for key in value.keys()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _report_dict(store: SemanticStore, report_id: str, workflow_id: str, include_raw: bool) -> dict[str, Any]:
    row = store.connection.execute(
        "SELECT * FROM reports WHERE report_id = ? AND workflow_id = ?",
        (report_id, workflow_id),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown report: {report_id}")
    result = _jsonable(row)
    if result.get("typed_json"):
        result["typed"] = json.loads(result.pop("typed_json"))
    else:
        result.pop("typed_json", None)
    if not include_raw:
        result.pop("raw_message", None)
    return result


def _event_matches(store: SemanticStore, event: Mapping[str, Any], condition: str, task_ids: list[str]) -> bool:
    kind = str(event["kind"])
    if condition == "ANY_REPORT":
        if kind not in {"REPORT_AVAILABLE", "UNTYPED_REPORT_AVAILABLE"}:
            return False
        if not task_ids:
            return True
        report_id = event.get("subject_id")
        row = store.connection.execute("SELECT task_id FROM reports WHERE report_id = ?", (report_id,)).fetchone()
        return row is not None and row[0] in task_ids
    if condition == "OPEN_OBLIGATION_CHANGED":
        return kind.startswith("OBLIGATION_")
    if condition in {"WORKFLOW_QUIESCENT", "ALL_REQUIRED_RETURNED"}:
        return False
    raise ValueError(f"unknown await condition: {condition}")


def _event_summary(store: SemanticStore, event: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "seq": event["seq"],
        "kind": event["kind"],
        "disposition_implied": False,
    }
    subject_id = event.get("subject_id")
    if event["kind"] in {"REPORT_AVAILABLE", "UNTYPED_REPORT_AVAILABLE"}:
        row = store.connection.execute("SELECT task_id FROM reports WHERE report_id = ?", (subject_id,)).fetchone()
        if row is not None:
            result["task_id"] = row[0]
    return result


_AWAIT_CONDITIONS = frozenset(
    {"ANY_REPORT", "ALL_REQUIRED_RETURNED", "OPEN_OBLIGATION_CHANGED", "WORKFLOW_QUIESCENT"}
)


def _state_condition_met(store: SemanticStore, workflow_id: str, condition: str) -> bool:
    if condition == "ALL_REQUIRED_RETURNED":
        return store.all_required_tasks_returned(workflow_id)
    if condition == "WORKFLOW_QUIESCENT":
        return store.is_workflow_quiescent(workflow_id)
    return False


def _validate_await_inputs(
    store: SemanticStore,
    workflow_id: str,
    after_seq: int,
    condition: str,
    task_ids: list[str] | None,
    timeout_s: float,
) -> list[str]:
    if condition not in _AWAIT_CONDITIONS:
        raise ValueError(f"unknown await condition: {condition}")
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise ValueError("timeout_s must be a finite number between 1 and 1500 seconds")
    if not math.isfinite(float(timeout_s)) or not 1 <= float(timeout_s) <= MAX_WAIT_SECONDS:
        raise ValueError(f"timeout_s must be between 1 and {MAX_WAIT_SECONDS} seconds")
    if isinstance(after_seq, bool) or not isinstance(after_seq, int) or after_seq < 0:
        raise ValueError("after_seq must be a non-negative integer")
    selected = list(task_ids or [])
    store.validate_task_ids(workflow_id, selected)
    return selected


async def await_events(
    store: SemanticStore,
    workflow_id: str,
    after_seq: int = 0,
    condition: str = "ANY_REPORT",
    task_ids: list[str] | None = None,
    timeout_s: float = 900,
) -> dict[str, Any]:
    """Wait in the runtime for one matching event, advancing a durable cursor."""
    task_ids = _validate_await_inputs(
        store, workflow_id, after_seq, condition, task_ids, timeout_s
    )
    deadline = asyncio.get_running_loop().time() + float(timeout_s)
    cursor = after_seq
    while True:
        events = store.await_events(workflow_id, cursor)
        for event in events:
            cursor = max(cursor, int(event["seq"]))
            if _event_matches(store, event, condition, task_ids):
                return {"status": "EVENT", "cursor": cursor, "events": [_event_summary(store, event)]}
        if _state_condition_met(store, workflow_id, condition):
            return {"status": "EVENT", "cursor": cursor, "events": []}
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            state = store.workflow_state(workflow_id)
            return {
                "status": "TIMEOUT_NO_DISPOSITION",
                "cursor": cursor,
                "open_tasks": state["open_task_ids"],
                "open_obligations": [item["obligation_id"] for item in state["open_obligations"]],
            }
        await asyncio.sleep(min(WAIT_POLL_SECONDS, remaining))


def _register_tools(server: MCPServer) -> MCPServer:
    @server.tool(description="Check MCP semantic runtime availability.")
    def runtime_health() -> dict[str, Any]:
        store = _get_store()
        store.initialize()
        return {"status": "OK", "server": SERVER_NAME, "schema_version": 1}

    @server.tool(description="Open one active managed workflow for a session.")
    def workflow_open(session_id: str, opened_turn_id: str, scope: str, objective: str) -> dict[str, Any]:
        store = _get_store()
        try:
            workflow_id = store.open_workflow(
                session_id=session_id,
                opened_turn_id=opened_turn_id,
                scope=scope,
                objective=objective,
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("an active workflow already exists for this session") from exc
        return {"workflow_id": workflow_id, "state": "ACTIVE"}

    @server.tool(description="Declare a child task and return its managed dispatch footer.")
    def task_register(
        workflow_id: str,
        task_id: str,
        expected_agent_type: str,
        objective: str,
        required: bool = True,
    ) -> dict[str, Any]:
        store = _get_store()
        store.register_task(workflow_id, task_id, expected_agent_type, objective, required)
        footer = "\n".join(
            [
                "[HMASD_MANAGED_TASK_V1]",
                f"workflow_id={workflow_id}",
                f"task_id={task_id}",
                "return_schema=HMASD_SUBAGENT_RETURN_V1",
                "global_disposition_authority=none",
                "[/HMASD_MANAGED_TASK_V1]",
            ]
        )
        return {"workflow_id": workflow_id, "task_id": task_id, "footer": footer}

    @server.tool(description="Bind the provider agent id to a declared task.")
    def task_bind(workflow_id: str, task_id: str, agent_id: str, agent_type: str = "") -> dict[str, Any]:
        store = _get_store()
        event_id = store.record_agent_started(workflow_id, task_id, agent_id, agent_type)
        return {"workflow_id": workflow_id, "task_id": task_id, "agent_id": agent_id, "event_id": event_id, "lifecycle": "RUNNING"}

    @server.tool(description="Return the persisted workflow state and open obligations.")
    def workflow_state(workflow_id: str) -> dict[str, Any]:
        return _jsonable(_get_store().workflow_state(workflow_id))

    @server.tool(description="Read one persisted child report without raw text by default.")
    def report_get(workflow_id: str, report_id: str, include_raw: bool = False) -> dict[str, Any]:
        return _report_dict(_get_store(), report_id, workflow_id, include_raw)

    @server.tool(description="Record an explicit Root intake for a report.")
    def root_record_intake(
        workflow_id: str,
        report_id: str,
        intake_kind: str,
        translation: dict[str, str],
        next_action: dict[str, str] | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        intake_id = _get_store().record_intake(
            workflow_id, report_id, intake_kind, translation, next_action, note
        )
        return {"workflow_id": workflow_id, "report_id": report_id, "intake_id": intake_id, "intake_kind": intake_kind}

    @server.tool(description="Open a typed control-plane obligation.")
    def obligation_open(
        workflow_id: str,
        kind: str,
        owner: str,
        subject: str,
        reason: str,
        source_ref: str,
    ) -> dict[str, Any]:
        if kind not in {member.value for member in ObligationKind}:
            raise ValueError(f"unknown obligation kind: {kind}")
        obligation_id = _get_store().open_obligation(workflow_id, kind, owner, subject, reason, source_ref)
        return {"workflow_id": workflow_id, "obligation_id": obligation_id, "kind": kind, "state": "OPEN"}

    @server.tool(description="Resolve one open control-plane obligation.")
    def obligation_resolve(
        workflow_id: str, obligation_id: str, resolution: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        resolved = _get_store().resolve_obligation(workflow_id, obligation_id, resolution)
        return {"workflow_id": workflow_id, "obligation_id": resolved, "state": "RESOLVED"}

    @server.tool(description="Wait for an event matching a bounded workflow condition.")
    async def workflow_await_event(
        workflow_id: str,
        after_seq: int = 0,
        condition: str = "ANY_REPORT",
        task_ids: list[str] | None = None,
        timeout_s: float = 900,
    ) -> dict[str, Any]:
        return await await_events(
            _get_store(), workflow_id, after_seq, condition, task_ids, timeout_s
        )

    @server.tool(description="Close a workflow after validating task and obligation obligations.")
    def workflow_close(workflow_id: str, closure_kind: str, summary: str = "") -> dict[str, Any]:
        if closure_kind not in CLOSURE_KINDS:
            raise ValueError(f"unknown closure kind: {closure_kind}")
        receipt_id = _get_store().create_closure_receipt(workflow_id, closure_kind, summary)
        return {"workflow_id": workflow_id, "receipt_id": receipt_id, "closure_kind": closure_kind}

    return server


def build_server(state_dir: str | Path | None = None) -> MCPServer:
    """Create a server backed by an initialized SQLite store.

    Tests use this factory to keep state isolated.  The module-level ``mcp``
    remains the stdio entrypoint used by the configured Codex server.
    """
    global _active_store
    if _active_store is not None:
        try:
            _active_store.close()
        except Exception:
            pass
    _active_store = SemanticStore(_state_path(state_dir)).initialize()
    return _register_tools(MCPServer(SERVER_NAME, version="1.0"))


mcp = build_server()


if __name__ == "__main__":
    mcp.run()
