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

from tools.codex_context_lifecycle.authority import (
    assert_mutation_source,
    bind_requester,
    default_repo_root,
    resolve_mcp_requester,
)

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


def _require_mutation(
    claimed_requester: str | None,
    source_kind: str | None,
    operation: str,
    user_authority_id: str | None = None,
) -> tuple[SemanticStore, str]:
    store = _get_store()
    requester = resolve_mcp_requester(store, claimed_requester)
    assert_mutation_source(
        store,
        source_kind,
        operation,
        requester_actor_context_id=requester,
        user_authority_id=user_authority_id,
    )
    return store, requester


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
            "schema_version": 3,
            "fail_open": fail_open,
            "ledger_role": "control_plane_delivery_and_obligation_ledger",
        }

    @server.tool(description="Return the current session workflow id and thin obligation summary.")
    def workflow_current(session_id: str) -> dict[str, Any]:
        store = _get_store()
        workflow = store.current_workflow(session_id)
        if workflow is None:
            return {
                "workflow_id": None,
                "state": None,
                "state_version": None,
                "open_obligation_ids": [],
                "unconsumed_report_ids": [],
            }
        state = store.workflow_state(str(workflow["workflow_id"]))
        obligations = list(state.get("open_obligations", []))
        return {
            "workflow_id": workflow["workflow_id"],
            "state": workflow["state"],
            "state_version": state.get("state_version"),
            "open_obligation_ids": [item["obligation_id"] for item in obligations],
            "unconsumed_report_ids": [
                item["subject"]
                for item in obligations
                if item.get("kind") == "REPORT_INTAKE_REQUIRED" and item.get("subject")
            ],
        }

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
        workflow_id: str,
        obligation_id: str,
        resolution: dict[str, Any] | None = None,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "resolve_obligation", user_authority_id
        )
        row = store.connection.execute(
            """SELECT obligation_id, owner_actor_context_id, owner FROM obligations
            WHERE obligation_id = ? AND workflow_id = ?""",
            (obligation_id, workflow_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown obligation: {obligation_id}")
        owner = str(row["owner_actor_context_id"] or row["owner"] or "")
        if owner != requester:
            raise PermissionError("requester is not the obligation owner")
        resolved = store.resolve_obligation(workflow_id, obligation_id, resolution)
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
    def workflow_close(
        workflow_id: str,
        closure_kind: str,
        summary: str = "",
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "close_workflow", user_authority_id
        )
        workflow = store.connection.execute(
            "SELECT actor_context_id FROM workflows WHERE workflow_id = ?",
            (workflow_id,),
        ).fetchone()
        if workflow is None:
            raise KeyError(f"unknown workflow: {workflow_id}")
        owner = str(workflow["actor_context_id"] or "")
        if owner and owner != requester:
            raise PermissionError("requester does not own this workflow")
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "open_epoch", user_authority_id
        )
        if requester != actor_context_id:
            raise PermissionError("requester does not own the epoch")
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "revise_epoch", user_authority_id
        )
        if requester != actor_context_id:
            raise PermissionError("requester does not own the epoch")
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "close_epoch", user_authority_id
        )
        if requester != actor_context_id:
            raise PermissionError("requester does not own the epoch")
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
    ) -> dict[str, Any]:
        from .semantic_commits import semantic_commit_write as _write

        return _write(
            _get_store(),
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
    def context_checkpoint_materialize(actor_context_id: str) -> dict[str, Any]:
        from .checkpoints import materialize_checkpoint

        return materialize_checkpoint(_get_store(), actor_context_id)

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
    ) -> dict[str, Any]:
        from .checkpoints import context_reanchor_ack as _ack

        return _ack(
            _get_store(),
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
    ) -> dict[str, Any]:
        from .checkpoints import require_actor_reanchored
        from .packet_refs import packet_register as _register

        require_actor_reanchored(_get_store(), source_actor_context_id)
        return _register(
            _get_store(),
            packet_kind=packet_kind,
            source_actor_context_id=source_actor_context_id,
            target_actor_context_id=target_actor_context_id,
            payload_ref=payload_ref,
            marker=marker or None,
            direction_id=direction_id or None,
        )

    @server.tool(description="Acknowledge delivery of a typed packet reference.")
    def packet_ack(packet_id: str, actor_context_id: str = "") -> dict[str, Any]:
        from .checkpoints import require_actor_reanchored
        from .packet_refs import packet_acknowledge

        if actor_context_id:
            require_actor_reanchored(_get_store(), actor_context_id)
        return packet_acknowledge(_get_store(), packet_id)

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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "create_promotion_proposal", user_authority_id
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
            requester_actor_context_id=requester,
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "create_owner_decision", user_authority_id
        )
        return resolve_promotion_proposal(
            store,
            promotion_id=promotion_id,
            next_state=next_state,
            disposition=disposition,
            requester_actor_context_id=requester,
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "promote_canonical", user_authority_id
        )
        return mark_promotion_applied(
            store,
            promotion_id=promotion_id,
            canonical_ref=canonical_ref,
            repo_root=default_repo_root(),
            requester_actor_context_id=requester,
            writer_actor_context_id=requester,
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "apply_rollover", user_authority_id
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
            requester_actor_context_id=requester,
        )

    @server.tool(description="Confirm owner review of a prepared epoch rollover.")
    def plan_epoch_rollover_confirm(
        rollover_id: str,
        source_kind: str | None = None,
        requester_actor_context_id: str | None = None,
        user_authority_id: str | None = None,
    ) -> dict[str, Any]:
        from tools.codex_context_lifecycle.rollover import confirm_rollover

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "create_owner_decision", user_authority_id
        )
        return confirm_rollover(
            store,
            rollover_id,
            requester_actor_context_id=requester,
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

        store, requester = _require_mutation(
            requester_actor_context_id, source_kind, "apply_rollover", user_authority_id
        )
        return apply_rollover(
            store,
            rollover_id=rollover_id,
            source_kind=source_kind or "PLAN_EPOCH",
            requester_actor_context_id=requester,
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
    return _register_tools(MCPServer(SERVER_NAME, version="1.0"))


mcp = build_server()


if __name__ == "__main__":
    mcp.run()
