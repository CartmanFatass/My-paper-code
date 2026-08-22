"""MCP v2 server for the repository-local semantic workflow overlay."""

from __future__ import annotations

import asyncio
import json
import math
import os
import sqlite3
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, Mapping

from mcp.server import MCPServer
from pydantic import Field

from tools.codex_context_lifecycle.authority import (
    AuthorityError,
    assert_mutation_source,
    bind_requester,
    default_repo_root,
    require_requester,
    resolve_mcp_requester,
)
from tools.hmasd_control_plane.mcp_runtime import begin_mcp_instance

from .actor_models import ActorContext, ActorKind
from .db import DEFAULT_STATE_PATH
from .constants import MAX_WAIT_SECONDS, WAIT_POLL_SECONDS
from .models import ObligationKind
from .store import CLOSURE_KINDS, SemanticStore


SERVER_NAME = "hmasd_orchestrator"
SERVER_VERSION = "1.1"
STATE_ENV = "HMASD_CODEX_MVP_STATE_DIR"
_active_store: SemanticStore | None = None
_active_instance_id: str | None = None

ORCHESTRATOR_INSTRUCTIONS = (
    "For an explicitly native_child_register-bound EM/CM child, include its "
    "native-child-signal command in the child assignment, then call workflow_wait_plan first; "
    "call workflow_await_event "
    "only when it returns WAIT_SEMANTIC_EVENT. Pass await_cursor as after_seq, "
    "never state_version, and use only the four declared condition enum values. "
    "For an unbridged native child use collaboration.wait_agent. After a native "
    "bridge event, collect the ordinary native return through collaboration; the "
    "bridge signal contains no scientific conclusion. "
    "For a cross-workflow wait that must not bind to a session, workflow, or task, "
    "call workflow_await_global_event directly with the global cursor returned by "
    "the previous call; it does not require workflow_wait_plan. "
    "Known stale workflow ids may be passed as ignore_workflow_ids without "
    "binding the wait to a workflow. "
    "Control-plane errors never imply scientific failure, direction pause, or "
    "portfolio disposition. Mutations require a bound ACTIVE actor and explicit "
    "role-compatible authority. This server does not schedule, retry, or wake an "
    "ended Codex task. Observe file-backed runs through hmasd_observability."
)

ORCHESTRATOR_TOOL_ALLOWLIST = (
    "runtime_health",
    "workflow_current",
    "workflow_wait_plan",
    "workflow_open",
    "task_register",
    "task_bind",
    "native_child_register",
    "workflow_state",
    "report_get",
    "root_record_intake",
    "obligation_open",
    "obligation_resolve",
    "workflow_await_event",
    "workflow_await_global_event",
    "workflow_close",
    "actor_context_current",
    "plan_epoch_open",
    "plan_epoch_current",
    "plan_epoch_revise",
    "plan_epoch_close",
    "semantic_commit_write",
    "semantic_commit_current",
    "context_checkpoint_materialize",
    "context_checkpoint_current",
    "context_reanchor_ack",
    "packet_register",
    "packet_ack",
    "context_promotion_propose",
    "context_promotion_resolve",
    "context_promotion_mark_applied",
    "context_promotion_list",
    "plan_epoch_rollover_prepare",
    "plan_epoch_rollover_confirm",
    "plan_epoch_rollover_apply",
    "plan_epoch_rollover_current",
    "working_set_refs",
)
READ_ONLY_TOOL_NAMES = frozenset(
    {
        "runtime_health",
        "workflow_current",
        "workflow_wait_plan",
        "workflow_state",
        "report_get",
        "workflow_await_event",
        "workflow_await_global_event",
        "actor_context_current",
        "plan_epoch_current",
        "semantic_commit_current",
        "context_checkpoint_current",
        "context_promotion_list",
        "plan_epoch_rollover_current",
        "working_set_refs",
    }
)
MUTATING_TOOL_NAMES = frozenset(ORCHESTRATOR_TOOL_ALLOWLIST) - READ_ONLY_TOOL_NAMES
MUTATION_OPERATION_BY_TOOL = {
    "workflow_open": "open_workflow",
    "task_register": "register_task",
    "task_bind": "bind_task",
    "native_child_register": "register_task",
    "root_record_intake": "record_intake",
    "obligation_open": "open_obligation",
    "obligation_resolve": "resolve_obligation",
    "workflow_close": "close_workflow",
    "plan_epoch_open": "open_epoch",
    "plan_epoch_revise": "revise_epoch",
    "plan_epoch_close": "close_epoch",
    "semantic_commit_write": "write_semantic_commit",
    "context_checkpoint_materialize": "materialize_checkpoint",
    "context_reanchor_ack": "ack_checkpoint",
    "packet_register": "register_packet",
    "packet_ack": "ack_packet",
    "context_promotion_propose": "create_promotion_proposal",
    "context_promotion_resolve": "create_owner_decision",
    "context_promotion_mark_applied": "promote_canonical",
    "plan_epoch_rollover_prepare": "prepare_rollover",
    "plan_epoch_rollover_confirm": "confirm_rollover",
    "plan_epoch_rollover_apply": "apply_rollover",
}
if READ_ONLY_TOOL_NAMES | MUTATING_TOOL_NAMES != frozenset(
    ORCHESTRATOR_TOOL_ALLOWLIST
):  # pragma: no cover - import-time inventory invariant
    raise RuntimeError("orchestrator tool inventory is inconsistent")
if frozenset(MUTATION_OPERATION_BY_TOOL) != MUTATING_TOOL_NAMES:  # pragma: no cover
    raise RuntimeError("orchestrator mutation operation map is incomplete")


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


def _resolve_requester(
    claimed_requester: str | None,
) -> tuple[SemanticStore, ActorContext]:
    """Resolve one bound ACTIVE requester without consuming any authority grant."""

    store = _get_store()
    requester_id = resolve_mcp_requester(store, claimed_requester)
    return store, require_requester(store, requester_id)


def _admit_mutation(
    claimed_requester: str | None,
    source_kind: str | None,
    operation: str,
    user_authority_id: str | None = None,
    *,
    owner_actor_context_id: str | None = None,
    root_only: bool = False,
) -> tuple[SemanticStore, ActorContext]:
    """Apply the uniform MCP mutation admission after role/owner checks.

    Owner checks deliberately precede ``assert_mutation_source`` so a rejected
    USER_AUTHORITY call cannot consume a grant or leave any other ledger change.
    """

    store, requester = _resolve_requester(claimed_requester)
    if root_only and requester.actor_kind is not ActorKind.OPERATIONAL_ROOT:
        raise AuthorityError("operation requires the operational Root actor")
    if (
        owner_actor_context_id is not None
        and requester.actor_context_id != owner_actor_context_id
    ):
        raise AuthorityError("requester does not own the target object")
    assert_mutation_source(
        store,
        source_kind,
        operation,
        requester_actor_context_id=requester.actor_context_id,
        user_authority_id=user_authority_id,
    )
    return store, requester


def _workflow_owner(store: SemanticStore, workflow_id: str) -> str:
    row = store.connection.execute(
        "SELECT actor_context_id FROM workflows WHERE workflow_id = ?",
        (workflow_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown workflow: {workflow_id}")
    owner = str(row["actor_context_id"] or "")
    if not owner:
        raise AuthorityError("workflow has no explicit actor owner")
    return owner


def _rollover_owner(store: SemanticStore, rollover_id: str) -> str:
    row = store.connection.execute(
        "SELECT actor_context_id FROM epoch_rollovers WHERE rollover_id = ?",
        (rollover_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown rollover: {rollover_id}")
    return str(row["actor_context_id"])


def _promotion_owner(store: SemanticStore, promotion_id: str) -> str:
    row = store.connection.execute(
        "SELECT owner_actor_context_id FROM promotion_proposals WHERE promotion_id = ?",
        (promotion_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown promotion: {promotion_id}")
    return str(row["owner_actor_context_id"])


def _load_registry():
    from tools.codex_context_lifecycle.source_registry import load_registry

    path = default_repo_root() / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    return load_registry(path) if path.is_file() else None


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
        if kind not in {"REPORT_AVAILABLE", "UNTYPED_REPORT_AVAILABLE", "NATIVE_CHILD_REPORT_AVAILABLE"}:
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
    if event["kind"] in {"REPORT_AVAILABLE", "UNTYPED_REPORT_AVAILABLE", "NATIVE_CHILD_REPORT_AVAILABLE"}:
        row = store.connection.execute("SELECT task_id FROM reports WHERE report_id = ?", (subject_id,)).fetchone()
        if row is not None:
            result["task_id"] = row[0]
    return result


AwaitCondition = Literal[
    "ANY_REPORT",
    "ALL_REQUIRED_RETURNED",
    "OPEN_OBLIGATION_CHANGED",
    "WORKFLOW_QUIESCENT",
]

_AWAIT_CONDITIONS = frozenset(
    {"ANY_REPORT", "ALL_REQUIRED_RETURNED", "OPEN_OBLIGATION_CHANGED", "WORKFLOW_QUIESCENT"}
)

GlobalAwaitCondition = Literal["ANY_EVENT", "ANY_REPORT", "OPEN_OBLIGATION_CHANGED"]
_GLOBAL_AWAIT_CONDITIONS = frozenset(
    {"ANY_EVENT", "ANY_REPORT", "OPEN_OBLIGATION_CHANGED"}
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


def _validate_global_await_inputs(
    after_seq: int,
    condition: str,
    timeout_s: float,
    ignore_workflow_ids: list[str] | None,
) -> list[str]:
    if condition not in _GLOBAL_AWAIT_CONDITIONS:
        raise ValueError(f"unknown global await condition: {condition}")
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise ValueError("timeout_s must be a finite number between 1 and 1500 seconds")
    if not math.isfinite(float(timeout_s)) or not 1 <= float(timeout_s) <= MAX_WAIT_SECONDS:
        raise ValueError(f"timeout_s must be between 1 and {MAX_WAIT_SECONDS} seconds")
    if isinstance(after_seq, bool) or not isinstance(after_seq, int) or after_seq < 0:
        raise ValueError("after_seq must be a non-negative integer")
    selected = list(ignore_workflow_ids or [])
    if any(not isinstance(item, str) or not item.strip() for item in selected):
        raise ValueError("ignore_workflow_ids must contain non-empty strings")
    if len(set(selected)) != len(selected):
        raise ValueError("ignore_workflow_ids must be unique")
    return selected


def _global_event_matches(
    event: Mapping[str, Any], condition: str, ignored_workflows: set[str]
) -> bool:
    if str(event.get("workflow_id") or "") in ignored_workflows:
        return False
    if condition == "ANY_EVENT":
        return True
    kind = str(event["kind"])
    if condition == "ANY_REPORT":
        return kind in {
            "REPORT_AVAILABLE",
            "UNTYPED_REPORT_AVAILABLE",
            "NATIVE_CHILD_REPORT_AVAILABLE",
        }
    if condition == "OPEN_OBLIGATION_CHANGED":
        return kind.startswith("OBLIGATION_")
    raise ValueError(f"unknown global await condition: {condition}")


def _global_event_summary(store: SemanticStore, event: Mapping[str, Any]) -> dict[str, Any]:
    """Return a neutral event summary with source workflow metadata only."""
    result = _event_summary(store, event)
    result["workflow_id"] = event.get("workflow_id")
    return result


async def await_global_events(
    store: SemanticStore,
    after_seq: int = 0,
    condition: str = "ANY_REPORT",
    timeout_s: float = 900,
    ignore_workflow_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Wait for one event from any workflow without task/session binding.

    This is deliberately an event-stream primitive rather than a workflow
    state predicate. A global SQLite ``seq`` cursor makes the operation
    resumable across all managed workflows while preserving the existing
    task-bound ``workflow_await_event`` contract.
    """
    selected_ignored = _validate_global_await_inputs(
        after_seq, condition, timeout_s, ignore_workflow_ids
    )
    ignored_workflows = set(selected_ignored)
    deadline = asyncio.get_running_loop().time() + float(timeout_s)
    cursor = after_seq
    while True:
        events = store.await_global_events(cursor)
        for event in events:
            cursor = max(cursor, int(event["seq"]))
            if _global_event_matches(event, condition, ignored_workflows):
                return {
                    "status": "EVENT",
                    "scope": "GLOBAL_EVENT_STREAM",
                    "cursor": cursor,
                    "events": [_global_event_summary(store, event)],
                }
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            return {
                "status": "TIMEOUT_NO_DISPOSITION",
                "scope": "GLOBAL_EVENT_STREAM",
                "cursor": cursor,
            }
        await asyncio.sleep(min(WAIT_POLL_SECONDS, remaining))


def workflow_wait_plan_for_session(
    store: SemanticStore,
    session_id: str,
    timeout_s: int = 900,
) -> dict[str, Any]:
    """Project persisted semantic state into one deterministic Root action.

    This is intentionally read-only.  It creates neither a cursor nor a task
    disposition and therefore is not a second workflow state machine.
    """

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be non-empty")
    if (
        isinstance(timeout_s, bool)
        or not isinstance(timeout_s, int)
        or not 1 <= timeout_s <= MAX_WAIT_SECONDS
    ):
        raise ValueError(f"timeout_s must be an integer between 1 and {MAX_WAIT_SECONDS}")

    base: dict[str, Any] = {
        "schema": "HMASD_WORKFLOW_WAIT_PLAN_V1",
        "action": "NO_ACTIVE_WORKFLOW",
        "workflow_id": None,
        "condition": None,
        "after_seq": None,
        "task_ids": [],
        "timeout_s": None,
        "reason_code": "NO_ACTIVE_WORKFLOW",
    }
    workflow = store.current_workflow(session_id)
    if workflow is None or str(workflow.get("state")) != "ACTIVE":
        return base

    workflow_id = str(workflow["workflow_id"])
    state = store.workflow_state(workflow_id)
    base["workflow_id"] = workflow_id

    unconsumed_reports = store.connection.execute(
        """SELECT r.report_id, r.task_id
        FROM reports AS r
        LEFT JOIN intakes AS i ON i.report_id = r.report_id
        WHERE r.workflow_id = ? AND i.report_id IS NULL
        ORDER BY r.created_at, r.report_id""",
        (workflow_id,),
    ).fetchall()
    if unconsumed_reports:
        return {
            **base,
            "action": "REPORT_INTAKE_REQUIRED",
            "task_ids": sorted({str(row["task_id"]) for row in unconsumed_reports}),
            "reason_code": "UNINTAKEN_REPORT_PRESENT",
        }

    obligations = list(state.get("open_obligations", []))
    if obligations:
        return {
            **base,
            "action": "OBLIGATION_ACTION_REQUIRED",
            "task_ids": [],
            "reason_code": "OPEN_OBLIGATION_PRESENT",
        }

    pending_tasks = [
        str(task["task_id"])
        for task in state.get("tasks", [])
        if str(task.get("lifecycle")) in {"DECLARED", "RUNNING"}
    ]
    if pending_tasks:
        return {
            **base,
            "action": "WAIT_SEMANTIC_EVENT",
            "condition": "ANY_REPORT",
            "after_seq": int(state["await_cursor"]),
            "task_ids": pending_tasks,
            "timeout_s": timeout_s,
            "reason_code": "OPEN_TASKS_AWAITING_REPORT",
        }

    return {
        **base,
        "action": "WORKFLOW_CLOSE_ELIGIBLE",
        "reason_code": "WORKFLOW_QUIESCENT",
    }


def _register_tools(server: MCPServer) -> MCPServer:
    @server.tool(description="Check MCP semantic runtime availability.")
    def runtime_health() -> dict[str, Any]:
        store = _get_store()
        store.initialize()
        health_path = store.path.parent / "health.json"
        fail_open = None
        if health_path.is_file():
            try:
                loaded = json.loads(health_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    fail_open = loaded
            except (OSError, UnicodeError, json.JSONDecodeError):
                fail_open = {"status": "unreadable"}
        return {
            "status": "OK",
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "instance_id": _active_instance_id,
            "schema_version": 3,
            "fail_open": fail_open,
            "ledger_role": "control_plane_delivery_and_obligation_ledger",
        }

    @server.tool(description="Return the current session workflow id, await cursor, and thin obligation summary.")
    def workflow_current(session_id: str) -> dict[str, Any]:
        store = _get_store()
        workflow = store.current_workflow(session_id)
        if workflow is None:
            return {
                "workflow_id": None,
                "state": None,
                "state_version": None,
                "await_cursor": None,
                "open_obligation_ids": [],
                "unconsumed_report_ids": [],
            }
        state = store.workflow_state(str(workflow["workflow_id"]))
        obligations = list(state.get("open_obligations", []))
        return {
            "workflow_id": workflow["workflow_id"],
            "state": workflow["state"],
            "state_version": state.get("state_version"),
            "await_cursor": state.get("await_cursor"),
            "open_obligation_ids": [item["obligation_id"] for item in obligations],
            "unconsumed_report_ids": [
                item["subject"]
                for item in obligations
                if item.get("kind") == "REPORT_INTAKE_REQUIRED" and item.get("subject")
            ],
        }

    @server.tool(description=(
        "Return the deterministic next semantic action for one session. Call this "
        "before workflow_await_event; only WAIT_SEMANTIC_EVENT authorizes waiting."
    ))
    def workflow_wait_plan(
        session_id: str,
        timeout_s: Annotated[
            int, Field(strict=True, ge=1, le=MAX_WAIT_SECONDS)
        ] = 900,
    ) -> dict[str, Any]:
        return workflow_wait_plan_for_session(_get_store(), session_id, timeout_s)

    @server.tool(description="Open one active managed workflow for a session.")
    def workflow_open(
        session_id: str,
        opened_turn_id: str,
        scope: str,
        objective: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "open_workflow",
            user_authority_id,
            root_only=True,
        )
        if requester.session_id != session_id:
            raise AuthorityError("session_id does not belong to the bound Root actor")
        try:
            workflow_id = store.open_actor_workflow(
                actor_context_id=requester.actor_context_id,
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
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "register_task",
            user_authority_id,
            owner_actor_context_id=owner,
            root_only=True,
        )
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
    def task_bind(
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "bind_task",
            user_authority_id,
            owner_actor_context_id=owner,
            root_only=True,
        )
        event_id = store.record_agent_started(workflow_id, task_id, agent_id, agent_type)
        return {"workflow_id": workflow_id, "task_id": task_id, "agent_id": agent_id, "event_id": event_id, "lifecycle": "RUNNING"}

    @server.tool(description=(
        "Register and bind one native EM/CM child for file-backed semantic waiting. "
        "Return a content-free terminal signal command for the child to invoke once "
        "immediately before its ordinary native final return."
    ))
    def native_child_register(
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str,
        objective: str,
        required: bool = True,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "register_task",
            user_authority_id,
            owner_actor_context_id=owner,
            root_only=True,
        )
        event_id = store.register_native_child_bridge(
            workflow_id, task_id, agent_id, agent_type, objective, required
        )
        signal_id = f"native:{workflow_id}:{task_id}:{agent_id}"
        command = " ".join(
            [
                '"C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe"',
                "-m tools.codex_semantic_mvp.cli",
                f'--state-dir "{store.path.parent}"',
                "native-child-signal",
                f'--workflow-id "{workflow_id}"',
                f'--task-id "{task_id}"',
                f'--agent-id "{agent_id}"',
                f'--agent-type "{agent_type}"',
                f'--signal-id "{signal_id}"',
                "--outcome COMPLETED|ANOMALY",
            ]
        )
        return {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "event_id": event_id,
            "lifecycle": "RUNNING",
            "signal_id": signal_id,
            "signal_command": command,
            "signal_contract": (
                "Invoke exactly once immediately before the native final return. "
                "Use ANOMALY only for a WORKFLOW_ANOMALY_REPORT; do not include result text."
            ),
        }

    @server.tool(description="Return persisted workflow state, open obligations, and await_cursor. state_version is not an event cursor.")
    def workflow_state(workflow_id: str) -> dict[str, Any]:
        return _jsonable(_get_store().workflow_state(workflow_id))

    @server.tool(description="Read one persisted child report without raw text by default.")
    def report_get(
        workflow_id: str,
        report_id: str,
        include_raw: bool = False,
        requester_actor_context_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        if include_raw:
            owner = _workflow_owner(store, workflow_id)
            _store, requester = _resolve_requester(requester_actor_context_id)
            if requester.actor_context_id != owner:
                raise AuthorityError("raw report access requires the workflow owner")
        return _report_dict(store, report_id, workflow_id, include_raw)

    @server.tool(description="Record an explicit Root intake for a report.")
    def root_record_intake(
        workflow_id: str,
        report_id: str,
        intake_kind: str,
        translation: dict[str, str],
        next_action: dict[str, str] | None = None,
        note: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "record_intake",
            user_authority_id,
            owner_actor_context_id=owner,
            root_only=True,
        )
        intake_id = store.record_intake(
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
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        if kind not in {member.value for member in ObligationKind}:
            raise ValueError(f"unknown obligation kind: {kind}")
        store = _get_store()
        workflow_owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "open_obligation",
            user_authority_id,
            owner_actor_context_id=workflow_owner,
            root_only=True,
        )
        obligation_id = store.open_obligation(
            workflow_id, kind, owner, subject, reason, source_ref
        )
        return {"workflow_id": workflow_id, "obligation_id": obligation_id, "kind": kind, "state": "OPEN"}

    @server.tool(description="Resolve one open control-plane obligation.")
    def obligation_resolve(
        workflow_id: str,
        obligation_id: str,
        resolution: dict[str, Any] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        row = store.connection.execute(
            """SELECT obligation_id, owner_actor_context_id, owner FROM obligations
            WHERE obligation_id = ? AND workflow_id = ?""",
            (obligation_id, workflow_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown obligation: {obligation_id}")
        owner = str(row["owner_actor_context_id"] or row["owner"] or "")
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "resolve_obligation",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        resolved = store.resolve_obligation(workflow_id, obligation_id, resolution)
        return {"workflow_id": workflow_id, "obligation_id": resolved, "state": "RESOLVED"}

    @server.tool(description=(
        "Wait for one workflow event. condition is one of ANY_REPORT, "
        "ALL_REQUIRED_RETURNED, OPEN_OBLIGATION_CHANGED, or WORKFLOW_QUIESCENT. "
        "Use await_cursor returned by workflow_state or workflow_current as after_seq; "
        "state_version is not an event cursor."
    ))
    async def workflow_await_event(
        workflow_id: str,
        after_seq: int = 0,
        condition: AwaitCondition = "ANY_REPORT",
        task_ids: list[str] | None = None,
        timeout_s: float = 900,
    ) -> dict[str, Any]:
        return await await_events(
            _get_store(), workflow_id, after_seq, condition, task_ids, timeout_s
        )

    @server.tool(description=(
        "Wait for one event from any managed workflow without binding to a "
        "session, workflow, or task. condition is ANY_EVENT, ANY_REPORT, or "
        "OPEN_OBLIGATION_CHANGED. Pass the returned global cursor as after_seq. "
        "Optional ignore_workflow_ids skips explicitly stale workflow ids while "
        "remaining globally unbound."
    ))
    async def workflow_await_global_event(
        after_seq: int = 0,
        condition: GlobalAwaitCondition = "ANY_REPORT",
        timeout_s: float = 900,
        ignore_workflow_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return await await_global_events(
            _get_store(), after_seq, condition, timeout_s, ignore_workflow_ids
        )

    @server.tool(description="Close a workflow after validating task and obligation obligations.")
    def workflow_close(
        workflow_id: str,
        closure_kind: str,
        summary: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store = _get_store()
        owner = _workflow_owner(store, workflow_id)
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "close_workflow",
            user_authority_id,
            owner_actor_context_id=owner,
            root_only=True,
        )
        if closure_kind not in CLOSURE_KINDS:
            raise ValueError(f"unknown closure kind: {closure_kind}")
        receipt_id = store.create_closure_receipt(workflow_id, closure_kind, summary)
        return {"workflow_id": workflow_id, "receipt_id": receipt_id, "closure_kind": closure_kind}

    @server.tool(description="Return the actor context and its current workflow.")
    def actor_context_current(
        session_id: str,
        agent_id: str = "",
        canonical_path: str = "",
    ) -> dict[str, Any]:
        from .actor_registry import resolve_actor_context

        store = _get_store()
        actor = resolve_actor_context(
            store,
            session_id=session_id,
            agent_id=agent_id,
            canonical_path=canonical_path,
        )
        if actor is None:
            return {"actor_context": None, "workflow": None}
        workflow = store.current_actor_workflow(actor.actor_context_id)
        return {
            "actor_context": {
                "actor_context_id": actor.actor_context_id,
                "actor_kind": actor.actor_kind.value,
                "session_id": actor.session_id,
                "scope_key": actor.scope_key,
                "direction_id": actor.direction_id,
                "state": actor.state.value,
            },
            "workflow": _jsonable(workflow) if workflow is not None else None,
        }

    @server.tool(description="Open one role-compatible plan epoch for an actor.")
    def plan_epoch_open(
        actor_context_id: str,
        epoch_kind: str,
        objective: str,
        authority_refs: list[str],
        frozen_invariants: list[str],
        exit_boundary: str,
        navigation_refs: list[str] | None = None,
        procedure_refs: list[str] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .epochs import plan_epoch_open as _open

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "open_epoch",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        return _open(
            store,
            actor_context_id=actor_context_id,
            epoch_kind=epoch_kind,
            objective=objective,
            authority_refs=authority_refs,
            frozen_invariants=frozen_invariants,
            exit_boundary=exit_boundary,
            navigation_refs=navigation_refs or (),
            procedure_refs=procedure_refs or (),
            registry=_load_registry(),
        )

    @server.tool(description="Return the actor's current open plan epoch.")
    def plan_epoch_current(actor_context_id: str) -> dict[str, Any]:
        from .epochs import plan_epoch_current as _current

        epoch = _current(_get_store(), actor_context_id)
        return {"epoch": epoch}

    @server.tool(description="Revise an open plan epoch with an expected revision.")
    def plan_epoch_revise(
        actor_context_id: str,
        epoch_id: str,
        expected_revision: int,
        objective: str,
        authority_refs: list[str],
        frozen_invariants: list[str],
        exit_boundary: str,
        reason: str,
        navigation_refs: list[str] | None = None,
        procedure_refs: list[str] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .epochs import plan_epoch_current as _current
        from .epochs import revise_epoch

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "revise_epoch",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        current = _current(store, actor_context_id)
        if current is None or current["epoch_id"] != epoch_id:
            raise ValueError("epoch does not belong to this actor")
        return revise_epoch(
            store,
            epoch_id=epoch_id,
            expected_revision=expected_revision,
            objective=objective,
            authority_refs=authority_refs,
            frozen_invariants=frozen_invariants,
            exit_boundary=exit_boundary,
            reason=reason,
            navigation_refs=navigation_refs,
            procedure_refs=procedure_refs,
            registry=_load_registry(),
        )

    @server.tool(description="Close the actor's open plan epoch.")
    def plan_epoch_close(
        actor_context_id: str,
        epoch_id: str,
        reason: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .epochs import plan_epoch_close as _close
        from .epochs import plan_epoch_current as _current

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "close_epoch",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        current = _current(store, actor_context_id)
        if current is None or current["epoch_id"] != epoch_id:
            raise ValueError("epoch does not belong to this actor")
        return _close(store, epoch_id=epoch_id, reason=reason)

    @server.tool(description="Write an owner-authored semantic reanchor snapshot.")
    def semantic_commit_write(
        actor_context_id: str,
        epoch_id: str,
        commit_kind: str,
        payload: dict[str, Any],
        source_refs: list[str],
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .semantic_commits import semantic_commit_write as _write

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "write_semantic_commit",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        return _write(
            store,
            actor_context_id=actor_context_id,
            epoch_id=epoch_id,
            commit_kind=commit_kind,
            payload=payload,
            source_refs=source_refs,
        )

    @server.tool(description="Return the actor's latest compatible semantic commit.")
    def semantic_commit_current(actor_context_id: str) -> dict[str, Any]:
        from .semantic_commits import semantic_commit_current as _current

        return {"commit": _current(_get_store(), actor_context_id)}

    @server.tool(description="Materialize a deterministic actor context checkpoint.")
    def context_checkpoint_materialize(
        actor_context_id: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .checkpoints import materialize_checkpoint

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "materialize_checkpoint",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        return materialize_checkpoint(store, actor_context_id)

    @server.tool(description="Return the actor's latest context checkpoint.")
    def context_checkpoint_current(actor_context_id: str) -> dict[str, Any]:
        from .checkpoints import current_checkpoint

        return {"checkpoint": current_checkpoint(_get_store(), actor_context_id)}

    @server.tool(description="Acknowledge a compact/resume actor checkpoint.")
    def context_reanchor_ack(
        actor_context_id: str,
        checkpoint_id: str,
        state_version: int,
        actor_turn_id: str,
        epoch_id: str = "",
        epoch_revision: int | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .checkpoints import context_reanchor_ack as _ack

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "ack_checkpoint",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        return _ack(
            store,
            actor_context_id=actor_context_id,
            checkpoint_id=checkpoint_id,
            state_version=state_version,
            epoch_id=epoch_id or None,
            epoch_revision=epoch_revision,
            actor_turn_id=actor_turn_id,
        )

    @server.tool(description="Register a typed cross-owner packet reference.")
    def packet_register(
        packet_kind: str,
        source_actor_context_id: str,
        target_actor_context_id: str,
        payload_ref: str,
        marker: str = "",
        direction_id: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .checkpoints import require_actor_reanchored
        from .packet_refs import packet_register as _register

        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "register_packet",
            user_authority_id,
            owner_actor_context_id=source_actor_context_id,
        )
        require_actor_reanchored(store, source_actor_context_id)
        return _register(
            store,
            packet_kind=packet_kind,
            source_actor_context_id=source_actor_context_id,
            target_actor_context_id=target_actor_context_id,
            payload_ref=payload_ref,
            marker=marker or None,
            direction_id=direction_id or None,
        )

    @server.tool(description="Acknowledge delivery of a typed packet reference.")
    def packet_ack(
        packet_id: str,
        actor_context_id: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from .checkpoints import require_actor_reanchored
        from .packet_refs import packet_acknowledge

        store = _get_store()
        packet = store.connection.execute(
            "SELECT target_actor_context_id FROM packet_refs WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
        if packet is None:
            raise KeyError(f"unknown packet: {packet_id}")
        owner = str(packet["target_actor_context_id"])
        if actor_context_id and actor_context_id != owner:
            raise AuthorityError("actor_context_id is not the packet target")
        store, _requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "ack_packet",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        require_actor_reanchored(store, owner)
        return packet_acknowledge(store, packet_id)

    @server.tool(description="Propose an owner-reviewed context promotion. Never edits files.")
    def context_promotion_propose(
        actor_context_id: str,
        epoch_id: str,
        promotion_kind: str,
        summary: str,
        rationale: str,
        source_refs: list[str],
        owner_actor_context_id: str,
        target_ref: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.promotion import create_promotion_proposal

        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "create_promotion_proposal",
            user_authority_id,
            owner_actor_context_id=owner_actor_context_id,
        )
        return create_promotion_proposal(
            store,
            actor_context_id=actor_context_id,
            epoch_id=epoch_id,
            promotion_kind=promotion_kind,
            summary=summary,
            rationale=rationale,
            source_refs=source_refs,
            owner_actor_context_id=owner_actor_context_id,
            target_ref=target_ref or None,
            source_kind=source_kind,
            requester_actor_context_id=requester.actor_context_id,
            repo_root=default_repo_root(),
        )

    @server.tool(description="Resolve a promotion proposal with an explicit owner disposition.")
    def context_promotion_resolve(
        promotion_id: str,
        next_state: str,
        disposition: dict[str, Any] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.promotion import resolve_promotion_proposal

        store = _get_store()
        owner = _promotion_owner(store, promotion_id)
        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "create_owner_decision",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        return resolve_promotion_proposal(
            store,
            promotion_id=promotion_id,
            next_state=next_state,
            disposition=disposition,
            requester_actor_context_id=requester.actor_context_id,
            source_kind=source_kind or "ROLE_CONTRACT",
        )

    @server.tool(description="Record that an authorized writer applied a promotion to a file.")
    def context_promotion_mark_applied(
        promotion_id: str,
        canonical_ref: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.promotion import mark_promotion_applied

        store = _get_store()
        owner = _promotion_owner(store, promotion_id)
        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "promote_canonical",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        return mark_promotion_applied(
            store,
            promotion_id=promotion_id,
            canonical_ref=canonical_ref,
            repo_root=default_repo_root(),
            requester_actor_context_id=requester.actor_context_id,
            writer_actor_context_id=requester.actor_context_id,
        )

    @server.tool(description="List promotion proposals for one epoch.")
    def context_promotion_list(epoch_id: str) -> dict[str, Any]:
        from tools.codex_context_lifecycle.promotion import promotion_proposals_for_epoch

        return {"promotions": promotion_proposals_for_epoch(_get_store(), epoch_id)}

    @server.tool(description="Prepare an owner-local epoch rollover without changing epoch state.")
    def plan_epoch_rollover_prepare(
        actor_context_id: str,
        from_epoch_id: str,
        from_epoch_revision: int,
        next_epoch_kind: str,
        next_objective: str,
        carry_obligation_ids: list[str] | None = None,
        carry_packet_ids: list[str] | None = None,
        carry_frontier: dict[str, Any] | None = None,
        promotion_ids: list[str] | None = None,
        forgotten_refs: list[str] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.rollover import prepare_rollover

        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "prepare_rollover",
            user_authority_id,
            owner_actor_context_id=actor_context_id,
        )
        return prepare_rollover(
            store,
            actor_context_id=actor_context_id,
            from_epoch_id=from_epoch_id,
            from_epoch_revision=from_epoch_revision,
            next_epoch_kind=next_epoch_kind,
            next_objective=next_objective,
            carry_obligation_ids=carry_obligation_ids or (),
            carry_packet_ids=carry_packet_ids or (),
            carry_frontier=carry_frontier or {},
            promotion_ids=promotion_ids or (),
            forgotten_refs=forgotten_refs or (),
            source_kind=source_kind or "PLAN_EPOCH",
            requester_actor_context_id=requester.actor_context_id,
        )

    @server.tool(description="Confirm owner review of a prepared epoch rollover.")
    def plan_epoch_rollover_confirm(
        rollover_id: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.rollover import confirm_rollover

        store = _get_store()
        owner = _rollover_owner(store, rollover_id)
        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "confirm_rollover",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        return confirm_rollover(
            store,
            rollover_id,
            requester_actor_context_id=requester.actor_context_id,
            source_kind=source_kind or "ROLE_CONTRACT",
        )

    @server.tool(description="Apply a confirmed owner-local epoch rollover.")
    def plan_epoch_rollover_apply(
        rollover_id: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.rollover import apply_rollover

        store = _get_store()
        owner = _rollover_owner(store, rollover_id)
        store, requester = _admit_mutation(
            requester_actor_context_id,
            source_kind,
            "apply_rollover",
            user_authority_id,
            owner_actor_context_id=owner,
        )
        return apply_rollover(
            store,
            rollover_id=rollover_id,
            source_kind=source_kind or "PLAN_EPOCH",
            requester_actor_context_id=requester.actor_context_id,
        )

    @server.tool(description="Return the current prepared or confirmed rollover for an actor.")
    def plan_epoch_rollover_current(actor_context_id: str) -> dict[str, Any]:
        from tools.codex_context_lifecycle.rollover import current_rollover

        return {"rollover": current_rollover(_get_store(), actor_context_id)}

    @server.tool(description="Return the actor's active working-set references.")
    def working_set_refs(actor_context_id: str) -> dict[str, Any]:
        from tools.codex_context_lifecycle.working_set import working_set_refs as _refs

        return _refs(_get_store(), actor_context_id)

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
    bind_requester(None)
    _active_store = SemanticStore(_state_path(state_dir)).initialize()
    return _register_tools(
        MCPServer(
            SERVER_NAME,
            version=SERVER_VERSION,
            instructions=ORCHESTRATOR_INSTRUCTIONS,
        )
    )


mcp = build_server()


def main() -> None:
    global _active_instance_id
    store = _get_store()
    registration = begin_mcp_instance(
        default_repo_root(),
        server_name=SERVER_NAME,
        profile="orchestrator",
        state_path=store.path,
    )
    _active_instance_id = registration.instance_id
    mcp.run()
    registration.close()


if __name__ == "__main__":
    main()
