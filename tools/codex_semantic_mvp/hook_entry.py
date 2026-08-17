"""Fail-open SHADOW/ACTIVE hook entrypoint for the semantic MVP.

SHADOW mode is deliberately observational: it records bounded diagnostics and
always returns a neutral continuation response.  ACTIVE mode adds managed
session SubagentStart context and validates/persists managed SubagentStop
returns, while unmanaged sessions remain behavior-neutral.  The entrypoint
uses only the repository-local SQLite overlay and has no SDK/App Server
dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Keep imports explicit so this module remains usable with the repository's
# package layout and does not introduce an SDK/App Server dependency.
from datetime import datetime, timezone

from .constants import ALWAYS_ON_OBJECTIVE, ALWAYS_ON_SCOPE, SHADOW_MODE, STATE_DIR_ENV
from .db import DEFAULT_STATE_PATH
from .hook_identity import normalize_hook_identity
from .models import ObligationKind
from .protocol import ProtocolError, extract_return_envelope, validate_subagent_return
from .store import OPEN_TASK_LIFECYCLES, SemanticStore
from .topology_probe import append_probe_record


SUPPORTED_EVENTS = frozenset(
    {
        "SessionStart",
        "SubagentStart",
        "SubagentStop",
        "Stop",
        "PreToolUse",
        "PreCompact",
        "PostCompact",
    }
)
EVENT_KINDS = {
    "SessionStart": "SESSION_STARTED",
    "SubagentStart": "SUBAGENT_STARTED",
    "SubagentStop": "SUBAGENT_STOPPED",
    "Stop": "STOP_OBSERVED",
    "PreToolUse": "PRE_TOOL_USE_OBSERVED",
    "PreCompact": "COMPACTION_STARTED",
    "PostCompact": "COMPACTION_COMPLETED",
}
MAX_PREVIEW_BYTES = 2048

GENERIC_SUBAGENT_CONTEXT = """This parent session is using the HMASD managed semantic protocol.

Your natural-language analysis remains unrestricted.
For the control plane:
- treat blocked/error/failed/stop/park/pause/retire/released as non-authoritative words;
- do not assert a parent, workflow, direction, or portfolio disposition;
- end with exactly one HMASD_SUBAGENT_RETURN_V1 envelope;
- use LOCAL_AUTHORITY_BOUNDARY when only your own authorized action set is exhausted."""


def _managed_task_context(workflow_id: str, task_id: str, expected_agent_type: str) -> str:
    return "\n".join(
        [
            GENERIC_SUBAGENT_CONTEXT,
            "",
            "[HMASD_MANAGED_TASK_V1]",
            f"workflow_id={workflow_id}",
            f"task_id={task_id}",
            f"expected_agent_type={expected_agent_type}",
            "return_schema=HMASD_SUBAGENT_RETURN_V1",
            "global_disposition_authority=none",
            "[/HMASD_MANAGED_TASK_V1]",
        ]
    )


def _workflow_current_context(workflow: Mapping[str, object], state: Mapping[str, object] | None = None) -> str:
    obligation_ids = ""
    report_ids = ""
    if state is not None:
        obligation_ids = ",".join(
            str(item.get("obligation_id") or "")
            for item in state.get("open_obligations", [])
            if item.get("obligation_id")
        )
        report_ids = ",".join(
            str(item.get("subject") or "")
            for item in state.get("open_obligations", [])
            if str(item.get("kind") or "") == "REPORT_INTAKE_REQUIRED" and item.get("subject")
        )
    return "\n".join(
        [
            "[HMASD_WORKFLOW_CURRENT_V1]",
            f"workflow_id={workflow.get('workflow_id') or ''}",
            f"state_version={workflow.get('state_version') or (state or {}).get('state_version') or ''}",
            f"open_obligation_ids={obligation_ids}",
            f"unconsumed_report_ids={report_ids}",
            "[/HMASD_WORKFLOW_CURRENT_V1]",
        ]
    )

REPORT_FORMAT_REPAIR = """Do not redo the investigation.
Return exactly one HMASD_SUBAGENT_RETURN_V1 envelope as the final output.
The envelope must contain these fields: schema_version, packet_kind, workflow_id,
task_id, return_kind, observed_facts, interpretive_claims, remaining_unknowns,
suggested_next_actions, research_frontier, and global_disposition.
Use schema_version=1.0, packet_kind=SUBAGENT_RETURN, and
global_disposition=NOT_ASSERTED. Use LOCAL_AUTHORITY_BOUNDARY only for the
child's own authorized action boundary. Do not assert blocked, failed, paused,
parked, released, retired, or any parent, workflow, direction, or portfolio
disposition."""

OBLIGATION_CONTINUATION = """[HMASD_OBLIGATION_CONTINUATION_V1]

A managed workflow has unresolved control obligations.

Child wording is evidence only and does not create a global disposition.
Call workflow_state, then do exactly one of:
1. intake an available report;
2. route or resolve an open obligation;
3. authorize/cancel a task within existing authority;
4. escalate a genuine user decision;
5. call workflow_await_event when required work is still running.

Do not infer blocked, failed, paused, parked, released, retired, or completed
from the absence of an active child or from a child status word.
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def state_dir_from_environment() -> Path:
    """Resolve state relative to this repository unless an absolute path is given."""
    configured = os.environ.get(STATE_DIR_ENV)
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else _repo_root() / path
    return _repo_root() / DEFAULT_STATE_PATH.parent


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _canonical_json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _diagnostic_payload(payload: Mapping[str, object], event: str) -> dict[str, object]:
    """Return bounded metadata; never copy arbitrary hook input to diagnostics."""
    tool_input = payload.get("tool_input")
    tool_input_json = _canonical_json(tool_input) if tool_input is not None else ""
    selected = {
        "hook_event_name": event,
        "session_id": str(payload.get("session_id") or ""),
        "turn_id": str(payload.get("turn_id") or ""),
        "tool_name": str(payload.get("tool_name") or ""),
        "tool_use_id": str(payload.get("tool_use_id") or ""),
        "tool_input_sha256": hashlib.sha256(tool_input_json.encode("utf-8")).hexdigest()
        if tool_input is not None
        else None,
    }
    preview = _canonical_json(selected)
    # The preview consists only of selected metadata and is bounded by bytes.
    selected["payload_preview"] = preview.encode("utf-8")[:MAX_PREVIEW_BYTES].decode(
        "utf-8", errors="ignore"
    )
    return selected


def _append_audit(state_dir: Path, kind: str, payload: Mapping[str, object]) -> None:
    """Append one JSON diagnostic, swallowing all I/O failures (fail open)."""
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        record = {"event": kind, **_json_safe(payload)}
        with (state_dir / "audit.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        return


def _record_fail_open(state_dir: Path, kind: str, exception_class: str) -> None:
    """Keep fail-open behavior but leave a visible health signal."""
    payload = {
        "last_fail_open_at": datetime.now(timezone.utc).isoformat(),
        "last_fail_open_kind": kind,
        "last_fail_open_exception": exception_class,
    }
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "health.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    except Exception:
        pass
    try:
        print(
            f"HMASD_SEMANTIC_FAIL_OPEN kind={kind} exception={exception_class}",
            file=sys.stderr,
        )
    except Exception:
        pass
    _append_audit(state_dir, kind, {"exception_class": exception_class})


def _neutral_response() -> dict[str, object]:
    return {"continue": True}


def _active_workflow(store: SemanticStore, session_id: str) -> dict[str, object] | None:
    """Return the one ACTIVE workflow for a session, without changing state."""
    if not session_id:
        return None
    row = store.connection.execute(
        "SELECT * FROM workflows WHERE session_id = ? AND state = 'ACTIVE'",
        (session_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def _ensure_active_workflow(
    payload: Mapping[str, object], store: SemanticStore
) -> dict[str, object] | None:
    """Open the session workflow on first ACTIVE hook if none exists."""
    session_id = str(payload.get("session_id") or "")
    existing = _active_workflow(store, session_id)
    if existing is not None:
        return existing
    if not session_id:
        return None
    turn_id = str(payload.get("turn_id") or "session-start")
    try:
        store.open_workflow(
            session_id=session_id,
            opened_turn_id=turn_id,
            scope=ALWAYS_ON_SCOPE,
            objective=ALWAYS_ON_OBJECTIVE,
        )
    except Exception as exc:
        _hook_audit(
            store,
            "HOOK_FAIL_OPEN",
            session_id,
            None,
            {"exception_class": type(exc).__name__, "phase": "always_on_open"},
        )
        return _active_workflow(store, session_id)
    return _active_workflow(store, session_id)


def _task(store: SemanticStore, workflow_id: str, task_id: str) -> dict[str, object] | None:
    if not workflow_id or not task_id:
        return None
    row = store.connection.execute(
        "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
        (workflow_id, task_id),
    ).fetchone()
    return dict(row) if row is not None else None


def _untyped_task(
    store: SemanticStore,
    workflow_id: str,
    payload: Mapping[str, object],
) -> dict[str, object] | None:
    """Resolve a task for an untyped return using only hook identity fields."""
    task_id = str(payload.get("task_id") or "")
    if task_id:
        return _task(store, workflow_id, task_id)
    agent_id = str(payload.get("agent_id") or "")
    if agent_id:
        row = store.connection.execute(
            "SELECT * FROM tasks WHERE workflow_id = ? AND agent_id = ?",
            (workflow_id, agent_id),
        ).fetchone()
        if row is not None:
            return dict(row)
    agent_type = str(payload.get("agent_type") or "")
    rows = store.connection.execute(
        "SELECT * FROM tasks WHERE workflow_id = ? AND expected_agent_type = ? ORDER BY created_at, task_id",
        (workflow_id, agent_type),
    ).fetchall()
    return dict(rows[0]) if len(rows) == 1 else None


def _hook_audit(
    store: SemanticStore,
    kind: str,
    workflow_id: str | None,
    subject_id: str | None,
    payload: Mapping[str, object],
) -> None:
    """Write a bounded event and audit record; never include raw child prose."""
    try:
        store.append_event(
            workflow_id,
            kind,
            subject_id,
            payload,
            f"{kind}:{uuid.uuid4().hex}",
        )
    except Exception:
        pass
    try:
        _append_audit(store.path.parent, kind, payload)
    except Exception:
        pass
    if kind in {"HOOK_FAIL_OPEN", "STOP_GUARD_FAIL_OPEN"}:
        _record_fail_open(
            store.path.parent,
            kind,
            str(payload.get("exception_class") or "Exception"),
        )


def _open_unbound_intake(
    store: SemanticStore,
    workflow_id: str,
    subject: str,
    reason: str,
    source_ref: str,
) -> None:
    try:
        store.ensure_open_obligation(
            workflow_id,
            ObligationKind.UNBOUND_SUBAGENT_INTAKE_REQUIRED,
            "/root",
            subject,
            reason,
            source_ref,
        )
    except Exception as exc:
        _hook_audit(
            store,
            "HOOK_FAIL_OPEN",
            workflow_id,
            subject,
            {"exception_class": type(exc).__name__, "phase": "unbound_intake"},
        )


def _binding_mismatch(
    store: SemanticStore,
    workflow_id: str,
    task_id: str | None,
    reason: str,
) -> dict[str, object]:
    _hook_audit(
        store,
        "HOOK_BINDING_MISMATCH",
        workflow_id,
        task_id,
        {"reason": reason},
    )
    _open_unbound_intake(
        store,
        workflow_id,
        task_id or "unbound",
        f"child return binding mismatch: {reason}",
        f"binding:{task_id or 'none'}:{reason}",
    )
    return _neutral_response()


def _record_untyped_binding_mismatch(
    store: SemanticStore,
    workflow_id: str,
    task: Mapping[str, object],
    agent_id: str,
    agent_type: str,
    raw_message: str,
    reason: str,
) -> dict[str, object]:
    """Preserve a report whose typed identity cannot be trusted."""
    task_id = str(task.get("task_id") or "")
    try:
        store.record_untyped_return(workflow_id, task_id, agent_id, agent_type, raw_message)
    except Exception as exc:
        _hook_audit(
            store,
            "HOOK_FAIL_OPEN",
            workflow_id,
            task_id,
            {"exception_class": type(exc).__name__},
        )
    return _binding_mismatch(store, workflow_id, task_id, reason)


def _active_session_start(
    payload: Mapping[str, object], store: SemanticStore
) -> dict[str, object]:
    workflow = _ensure_active_workflow(payload, store)
    if workflow is None:
        return _neutral_response()
    try:
        state = store.workflow_state(str(workflow["workflow_id"]))
    except Exception:
        state = None
    return {"continue": True, "additionalContext": _workflow_current_context(workflow, state)}


def _active_subagent_start(
    payload: Mapping[str, object], store: SemanticStore
) -> dict[str, object] | None:
    workflow = _ensure_active_workflow(payload, store)
    if workflow is None:
        return None
    workflow_id = str(workflow["workflow_id"])
    agent_id = str(payload.get("agent_id") or "")
    agent_type = str(payload.get("agent_type") or "")
    if not agent_id:
        _open_unbound_intake(
            store,
            workflow_id,
            "missing_agent_id",
            "SubagentStart without agent_id cannot bind a delivery task",
            "unbound:missing_agent_id:start",
        )
        return {
            "continue": True,
            "additionalContext": _workflow_current_context(workflow),
        }
    try:
        task = store.ensure_delivery_task(workflow_id, agent_id, agent_type)
        task_id = str(task["task_id"])
        if not str(task.get("agent_id") or ""):
            store.record_agent_started(workflow_id, task_id, agent_id, agent_type)
            task = _task(store, workflow_id, task_id) or task
    except Exception as exc:
        _hook_audit(
            store,
            "HOOK_FAIL_OPEN",
            workflow_id,
            None,
            {"exception_class": type(exc).__name__, "phase": "delivery_bind"},
        )
        _open_unbound_intake(
            store,
            workflow_id,
            agent_id,
            "SubagentStart failed to bind a delivery task",
            f"unbound:{agent_id}:start_bind",
        )
        return {
            "continue": True,
            "additionalContext": _workflow_current_context(workflow),
        }
    return {
        "continue": True,
        "additionalContext": _managed_task_context(
            workflow_id,
            str(task["task_id"]),
            str(task.get("expected_agent_type") or agent_type or "unspecified"),
        ),
    }


def _active_subagent_stop(
    payload: Mapping[str, object], store: SemanticStore
) -> dict[str, object]:
    session_id = str(payload.get("session_id") or "")
    envelope_task_id = str(payload.get("task_id") or "")
    agent_id = str(payload.get("agent_id") or "")
    workflow = store.workflow_for_session_return(
        session_id,
        task_id=envelope_task_id or None,
        agent_id=agent_id or None,
    )
    if workflow is None:
        return _neutral_response()
    workflow_id = str(workflow["workflow_id"])
    raw_message = payload.get("last_assistant_message")
    raw_message = raw_message if isinstance(raw_message, str) else ""
    report_hash = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()
    agent_type = str(payload.get("agent_type") or "")

    packet_data: dict[str, object] | None = None
    packet_task_id = ""
    try:
        packet_data = extract_return_envelope(raw_message)
        packet = validate_subagent_return(packet_data)
        packet_task_id = packet.task_id
    except (ProtocolError, TypeError, ValueError, json.JSONDecodeError):
        packet_data = None

    if packet_data is not None:
        packet_workflow_id = str(packet_data.get("workflow_id") or "")
        if packet_workflow_id != workflow_id:
            return _binding_mismatch(store, workflow_id, packet_task_id, "workflow_id")
        task = _task(store, workflow_id, packet_task_id)
        if task is None:
            return _binding_mismatch(store, workflow_id, packet_task_id, "task_id")
        if str(task.get("expected_agent_type") or "") != agent_type:
            return _binding_mismatch(store, workflow_id, packet_task_id, "agent_type")
        bound_agent_id = str(task.get("agent_id") or "")
        if bound_agent_id and bound_agent_id != agent_id:
            return _record_untyped_binding_mismatch(
                store,
                workflow_id,
                task,
                agent_id,
                agent_type,
                raw_message,
                "agent_id",
            )
        if not agent_id:
            return _binding_mismatch(store, workflow_id, packet_task_id, "missing_agent_id")
        try:
            if not bound_agent_id:
                store.record_agent_started(workflow_id, packet_task_id, agent_id, agent_type)
            store.record_report(
                workflow_id,
                packet_task_id,
                agent_id,
                agent_type,
                raw_message,
                packet_data,
            )
        except Exception as exc:
            _hook_audit(
                store,
                "HOOK_FAIL_OPEN",
                workflow_id,
                packet_task_id,
                {"exception_class": type(exc).__name__},
            )
        return _neutral_response()

    # The durable guard identifies the logical stop invocation, not the prose
    # body.  A child changing invalid wording on a repair pass must not obtain
    # another automatic block.  Keep report_hash only as audit metadata.
    guard_key = f"SUBAGENT_STOP:{session_id}:{payload.get('turn_id') or ''}:{agent_id}"
    try:
        first_repair = store.acquire_guard_once(guard_key, "SubagentStop")
    except Exception as exc:
        _hook_audit(
            store,
            "HOOK_FAIL_OPEN",
            workflow_id,
            None,
            {"exception_class": type(exc).__name__},
        )
        return _neutral_response()

    task = _untyped_task(store, workflow_id, payload)
    if task is not None and not bool(payload.get("stop_hook_active")) and first_repair:
        _hook_audit(
            store,
            "REPORT_FORMAT_REPAIR_REQUESTED",
            workflow_id,
            str(task.get("task_id")),
            {"report_sha256": report_hash},
        )
        return {"decision": "block", "reason": REPORT_FORMAT_REPAIR}

    if task is not None and agent_id:
        bound_agent_id = str(task.get("agent_id") or "")
        if bound_agent_id and bound_agent_id != agent_id:
            return _binding_mismatch(store, workflow_id, str(task["task_id"]), "agent_id")
        if str(task.get("expected_agent_type") or "") != agent_type:
            return _binding_mismatch(store, workflow_id, str(task["task_id"]), "agent_type")
        try:
            if not bound_agent_id:
                store.record_agent_started(workflow_id, str(task["task_id"]), agent_id, agent_type)
            store.record_untyped_return(
                workflow_id,
                str(task["task_id"]),
                agent_id,
                agent_type,
                raw_message,
            )
        except Exception as exc:
            _hook_audit(
                store,
                "HOOK_FAIL_OPEN",
                workflow_id,
                str(task["task_id"]),
                {"exception_class": type(exc).__name__},
            )
    else:
        _hook_audit(
            store,
            "HOOK_BINDING_MISMATCH",
            workflow_id,
            None,
            {"reason": "untyped_task_identity"},
        )
        _open_unbound_intake(
            store,
            workflow_id,
            agent_id or "unbound",
            "untyped child return could not bind to a task",
            f"unbound:{agent_id or 'none'}:untyped_task_identity",
        )
    return _neutral_response()


def _active_stop(
    payload: Mapping[str, object], store: SemanticStore
) -> dict[str, object]:
    """Guard Root Stop using only the active workflow's typed SQLite state."""
    session_id = str(payload.get("session_id") or "")
    workflow_id: str | None = None
    try:
        workflow = _active_workflow(store, session_id)
        if workflow is None:
            return _neutral_response()
        workflow_id = str(workflow["workflow_id"])
        state = store.workflow_state(workflow_id)
        receipt = store.connection.execute(
            "SELECT 1 FROM closure_receipts WHERE workflow_id = ? LIMIT 1",
            (workflow_id,),
        ).fetchone()
        pending_required = [
            task
            for task in state.get("tasks", [])
            if bool(task.get("required"))
            and str(task.get("lifecycle") or "") not in {"INTAKEN", "CANCELLED"}
        ]
        open_tasks = [
            task
            for task in state.get("tasks", [])
            if str(task.get("lifecycle") or "") in OPEN_TASK_LIFECYCLES
        ]
        open_obligations = list(state.get("open_obligations", []))
        if not open_tasks and not open_obligations:
            if receipt is None:
                store.create_closure_receipt(
                    workflow_id,
                    "EMPTY_SESSION_ENDED",
                    "session stop with no managed activity",
                )
            return _neutral_response()
        if not pending_required and not open_obligations:
            # Optional in-flight work must not be rewritten as COMPLETED, but
            # it also must not brick an ordinary session stop.
            return _neutral_response()

        if bool(payload.get("stop_hook_active")):
            _hook_audit(
                store,
                "LOOP_PREVENTED",
                workflow_id,
                None,
                {"state_version": state.get("state_version")},
            )
            return _neutral_response()

        state_version = str(state.get("state_version") or "")
        guard_key = f"STOP:{session_id}:{payload.get('turn_id') or ''}:{state_version}"
        if not store.acquire_guard_once(guard_key, "Stop"):
            _hook_audit(
                store,
                "LOOP_PREVENTED",
                workflow_id,
                None,
                {"state_version": state.get("state_version")},
            )
            return _neutral_response()

        _hook_audit(
            store,
            "STOP_GUARD_CONTINUATION",
            workflow_id,
            None,
            {"state_version": state.get("state_version")},
        )
        return {"decision": "block", "reason": OBLIGATION_CONTINUATION}
    except Exception as exc:
        _hook_audit(
            store,
            "STOP_GUARD_FAIL_OPEN",
            workflow_id,
            None,
            {"exception_class": type(exc).__name__},
        )
        return _neutral_response()


def handle_hook(
    payload: Mapping[str, object], mode: str, store: SemanticStore | None
) -> dict[str, object] | None:
    """Observe one hook invocation and return a behavior-neutral response."""
    if os.environ.get("HMASD_CODEX_MVP_DISABLE") == "1":
        return None
    event = str(payload.get("hook_event_name") or payload.get("event") or "") if isinstance(payload, Mapping) else ""
    kind = EVENT_KINDS.get(event, "UNKNOWN_HOOK_EVENT")
    diagnostic = _diagnostic_payload(payload if isinstance(payload, Mapping) else {}, event)
    diagnostic["mode"] = mode
    if store is not None:
        try:
            store.append_event(
                None,
                kind,
                diagnostic.get("session_id") or None,
                diagnostic,
                f"HOOK:{uuid.uuid4().hex}",
            )
        except Exception:
            # A broken local store must never turn an observational hook into
            # a behavioral gate.
            pass
        try:
            _append_audit(store.path.parent, kind, diagnostic)
        except Exception:
            pass
        if mode == SHADOW_MODE and event in {"PreCompact", "PostCompact"}:
            try:
                append_probe_record(
                    store.path.parent / "topology-probe.jsonl",
                    normalize_hook_identity(payload),
                    payload,
                )
            except Exception:
                pass
        if mode == "active" and event == "SessionStart":
            try:
                return _active_session_start(payload, store)
            except Exception as exc:
                _hook_audit(store, "HOOK_FAIL_OPEN", diagnostic.get("session_id") or None, None, {"exception_class": type(exc).__name__})
                return _neutral_response()
        if mode == "active" and event == "SubagentStart":
            try:
                return _active_subagent_start(payload, store)
            except Exception as exc:
                _hook_audit(store, "HOOK_FAIL_OPEN", diagnostic.get("session_id") or None, None, {"exception_class": type(exc).__name__})
                return _neutral_response()
        if mode == "active" and event == "SubagentStop":
            try:
                return _active_subagent_stop(payload, store)
            except Exception as exc:
                _hook_audit(store, "HOOK_FAIL_OPEN", diagnostic.get("session_id") or None, None, {"exception_class": type(exc).__name__})
                return _neutral_response()
        if mode == "active" and event == "Stop":
            try:
                return _active_stop(payload, store)
            except Exception as exc:
                _hook_audit(
                    store,
                    "STOP_GUARD_FAIL_OPEN",
                    diagnostic.get("session_id") or None,
                    None,
                    {"exception_class": type(exc).__name__},
                )
                return _neutral_response()
    return _neutral_response()


def _parse_stdin() -> Mapping[str, object] | None:
    try:
        text = sys.stdin.read()
        value = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, Mapping) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SHADOW/ACTIVE semantic MVP hook (use --mode active for managed SubagentStart/SubagentStop semantics)"
    )
    parser.add_argument("--mode", default=SHADOW_MODE)
    args = parser.parse_args(argv)
    if os.environ.get("HMASD_CODEX_MVP_DISABLE") == "1":
        return 0
    payload = _parse_stdin()
    if payload is None:
        _append_audit(state_dir_from_environment(), "MALFORMED_HOOK_INPUT", {})
        return 0

    state_dir = state_dir_from_environment()
    store: SemanticStore | None = None
    try:
        store = SemanticStore(state_dir / "state.sqlite3").initialize()
        response = handle_hook(payload, args.mode, store)
    except Exception as exc:
        _record_fail_open(state_dir, "HOOK_FAIL_OPEN", type(exc).__name__)
        response = _neutral_response()
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:
                pass
    if response is not None:
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
