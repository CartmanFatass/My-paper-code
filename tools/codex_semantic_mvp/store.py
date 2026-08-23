"""Transactional SQLite event and obligation store for the semantic MVP.

Persisted rows are a control-plane delivery and obligation ledger. They are
not scientific truth, not canonical project memory, and not a source that
compaction may rehydrate as research conclusions or ``research_frontier``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .db import (
    DEFAULT_STATE_PATH,
    connect,
    connect_existing,
    initialize_database,
    validate_existing_database,
)
from .models import (
    IntakeKind,
    ObligationKind,
    RootIntakePacket,
    SubagentReturnPacket,
    normalize_obligation_kind,
)
from .protocol import ProtocolError, validate_subagent_return


TASK_LIFECYCLES = frozenset(
    {"DECLARED", "RUNNING", "RETURNED_TYPED", "RETURNED_UNTYPED", "INTAKEN", "CANCELLED"}
)
OBLIGATION_STATES = frozenset({"OPEN", "RESOLVED", "CANCELLED"})
WORKFLOW_STATES = frozenset({"ACTIVE", "QUIESCENT", "CLOSED", "CANCELLED"})
DISALLOWED_SEMANTIC_STATES = frozenset({"SUCCESS", "FAILURE", "BLOCKED", "RETIRED"})
RETURNED_TASK_LIFECYCLES = frozenset(
    {"RETURNED_TYPED", "RETURNED_UNTYPED", "INTAKEN", "CANCELLED"}
)
QUIESCENT_TASK_LIFECYCLES = frozenset({"INTAKEN", "CANCELLED"})
OPEN_TASK_LIFECYCLES = frozenset(
    {"DECLARED", "RUNNING", "RETURNED_TYPED", "RETURNED_UNTYPED"}
)
ROOT_EXPLICIT_CLOSURE_KINDS = frozenset(
    {"COMPLETED", "USER_CANCELLED", "SCOPE_TRANSFERRED", "DEFERRED_BY_USER", "GOAL_BLOCKED_AFTER_AUDIT"}
)
MECHANICAL_CLOSURE_KINDS = frozenset({"EMPTY_SESSION_ENDED"})
CONTROL_PLANE_CLOSURE_KINDS = frozenset({"CONTROL_PLANE_ROLLOVER"})
CLOSURE_KINDS = (
    ROOT_EXPLICIT_CLOSURE_KINDS
    | MECHANICAL_CLOSURE_KINDS
    | CONTROL_PLANE_CLOSURE_KINDS
)
CLOSED_WORKFLOW_STATES = frozenset({"CLOSED", "CANCELLED"})

ROLLOVER_RECEIPT_SCHEMA = "HMASD_CONTROL_PLANE_ROLLOVER_RECEIPT_V1"
ROLLOVER_RESOLUTION_KIND = "CONTROL_PLANE_EPOCH_ROLLOVER"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def _json(value: Any) -> str:
    return json.dumps(value, default=_json_default, ensure_ascii=False, separators=(",", ":"))


class SemanticStore:
    """Small, explicit state store; prose never determines a lifecycle."""

    def __init__(self, path: str | Path = DEFAULT_STATE_PATH):
        self.path = Path(path)
        self.connection = connect(self.path)
        self._lock = threading.RLock()

    def initialize(self) -> "SemanticStore":
        with self._lock:
            initialize_database(self.connection)
        return self

    @classmethod
    def open_existing(cls, path: str | Path) -> "SemanticStore":
        """Open one already initialized compatible database without migrating it."""

        resolved = validate_existing_database(path)
        connection = connect_existing(resolved)
        try:
            # Bind the compatibility check to the connection that will be used
            # for host mutations as well as to the prior zero-write probe.
            from .db import _validate_schema_v3_connection

            _validate_schema_v3_connection(connection)
        except Exception:
            connection.close()
            raise
        instance = cls.__new__(cls)
        instance.path = resolved
        instance.connection = connection
        instance._lock = threading.RLock()
        return instance

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def create_promotion_proposal(self, **kwargs):
        from tools.codex_context_lifecycle.promotion import create_promotion_proposal

        return create_promotion_proposal(self, **kwargs)

    def resolve_promotion_proposal(self, **kwargs):
        from tools.codex_context_lifecycle.promotion import resolve_promotion_proposal

        return resolve_promotion_proposal(self, **kwargs)

    def mark_promotion_applied(self, **kwargs):
        from tools.codex_context_lifecycle.promotion import mark_promotion_applied

        return mark_promotion_applied(self, **kwargs)

    def promotion_proposals_for_epoch(self, epoch_id: str):
        from tools.codex_context_lifecycle.promotion import promotion_proposals_for_epoch

        return promotion_proposals_for_epoch(self, epoch_id)

    def _ensure_session_root_actor(self, session_id: str, now: str) -> str:
        """Attach or create the unclassified session-root actor for a workflow."""
        existing = self.connection.execute(
            """SELECT actor_context_id FROM actor_contexts
            WHERE session_id = ? AND actor_kind = 'SESSION_ROOT_UNCLASSIFIED'
            ORDER BY created_at, actor_context_id LIMIT 1""",
            (session_id,),
        ).fetchone()
        if existing is not None:
            return str(existing[0])
        actor_context_id = _new_id("actor")
        self.connection.execute(
            """INSERT INTO actor_contexts (
                actor_context_id, session_id, agent_id, canonical_path, actor_kind,
                scope_key, direction_id, parent_actor_context_id,
                counterpart_actor_context_id, identity_source, state,
                created_at, updated_at
            ) VALUES (?, ?, NULL, NULL, 'SESSION_ROOT_UNCLASSIFIED', ?, NULL, NULL, NULL,
                      'OPEN_WORKFLOW', 'ACTIVE', ?, ?)""",
            (actor_context_id, session_id, f"session:{session_id}", now, now),
        )
        return actor_context_id

    def _touch_workflow(self, workflow_id: str, state: str | None = None) -> None:
        if state is not None and state not in WORKFLOW_STATES:
            raise ValueError(f"unknown workflow state: {state}")
        now = _now()
        if state is None:
            self.connection.execute(
                "UPDATE workflows SET state_version = state_version + 1, updated_at = ? WHERE workflow_id = ?",
                (now, workflow_id),
            )
        else:
            self.connection.execute(
                "UPDATE workflows SET state = ?, state_version = state_version + 1, updated_at = ? WHERE workflow_id = ?",
                (state, now, workflow_id),
            )

    def open_workflow(
        self,
        workflow_id: str | None = None,
        session_id: str | None = None,
        opened_turn_id: str | None = None,
        scope: str | None = None,
        objective: str | None = None,
    ) -> str:
        # The persisted schema has an explicit workflow id.  For callers that
        # only have the public workflow-open inputs, generate one while still
        # accepting the explicit schema-oriented form used by the store tests.
        if objective is None and workflow_id is not None and session_id is not None:
            workflow_id, session_id, opened_turn_id, scope, objective = (
                None, workflow_id, session_id, opened_turn_id, scope
            )
        workflow_id = workflow_id or _new_id("wf")
        if session_id is None or opened_turn_id is None or scope is None or objective is None:
            raise TypeError("session_id, opened_turn_id, scope, and objective are required")
        now = _now()
        with self._lock, self.connection:
            actor_context_id = self._ensure_session_root_actor(session_id, now)
            self.connection.execute(
                """INSERT INTO workflows
                (workflow_id, session_id, opened_turn_id, scope, objective, state,
                 state_version, actor_context_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', 1, ?, ?, ?)""",
                (workflow_id, session_id, opened_turn_id, scope, objective, actor_context_id, now, now),
            )
            self._append_event(
                workflow_id,
                "WORKFLOW_OPENED",
                workflow_id,
                {"session_id": session_id, "scope": scope, "actor_context_id": actor_context_id},
                f"WORKFLOW_OPENED:{workflow_id}",
            )
        return workflow_id

    def open_actor_workflow(
        self,
        actor_context_id: str,
        opened_turn_id: str,
        scope: str,
        objective: str,
        workflow_id: str | None = None,
    ) -> str:
        """Open one ACTIVE workflow owned by an explicit actor context."""
        if not actor_context_id:
            raise ValueError("actor_context_id is required")
        workflow_id = workflow_id or _new_id("wf")
        now = _now()
        with self._lock, self.connection:
            actor = self.connection.execute(
                "SELECT session_id FROM actor_contexts WHERE actor_context_id = ?",
                (actor_context_id,),
            ).fetchone()
            if actor is None:
                raise KeyError(f"unknown actor: {actor_context_id}")
            session_id = str(actor["session_id"])
            self.connection.execute(
                """INSERT INTO workflows
                (workflow_id, session_id, opened_turn_id, scope, objective, state,
                 state_version, actor_context_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', 1, ?, ?, ?)""",
                (
                    workflow_id,
                    session_id,
                    opened_turn_id,
                    scope,
                    objective,
                    actor_context_id,
                    now,
                    now,
                ),
            )
            self._append_event(
                workflow_id,
                "WORKFLOW_OPENED",
                workflow_id,
                {"session_id": session_id, "scope": scope, "actor_context_id": actor_context_id},
                f"WORKFLOW_OPENED:{workflow_id}",
            )
        return workflow_id

    def current_actor_workflow(self, actor_context_id: str) -> dict[str, Any] | None:
        if not actor_context_id:
            return None
        with self._lock:
            active = self.connection.execute(
                "SELECT * FROM workflows WHERE actor_context_id = ? AND state = 'ACTIVE'",
                (actor_context_id,),
            ).fetchone()
            if active is not None:
                return dict(active)
            latest = self.connection.execute(
                """SELECT * FROM workflows WHERE actor_context_id = ?
                ORDER BY updated_at DESC, created_at DESC, workflow_id DESC LIMIT 1""",
                (actor_context_id,),
            ).fetchone()
            return dict(latest) if latest is not None else None

    def current_workflow(self, session_id: str) -> dict[str, Any] | None:
        """Return the ACTIVE workflow, else the most recently updated session row."""
        if not session_id:
            return None
        with self._lock:
            active = self.connection.execute(
                "SELECT * FROM workflows WHERE session_id = ? AND state = 'ACTIVE'",
                (session_id,),
            ).fetchone()
            if active is not None:
                return dict(active)
            latest = self.connection.execute(
                """SELECT * FROM workflows WHERE session_id = ?
                ORDER BY updated_at DESC, created_at DESC, workflow_id DESC LIMIT 1""",
                (session_id,),
            ).fetchone()
            return dict(latest) if latest is not None else None

    def find_session_task(
        self,
        session_id: str,
        task_id: str | None = None,
        agent_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Find a task in any workflow of this session, including closed ones."""
        if not session_id or (not task_id and not agent_id):
            return None
        with self._lock:
            if task_id:
                row = self.connection.execute(
                    """SELECT workflows.*, tasks.task_id AS matched_task_id
                    FROM tasks JOIN workflows ON workflows.workflow_id = tasks.workflow_id
                    WHERE workflows.session_id = ? AND tasks.task_id = ?
                    ORDER BY workflows.updated_at DESC LIMIT 1""",
                    (session_id, task_id),
                ).fetchone()
                if row is not None:
                    workflow = dict(row)
                    task = self.connection.execute(
                        "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
                        (workflow["workflow_id"], task_id),
                    ).fetchone()
                    if task is not None:
                        return dict(row), dict(task)
            if agent_id:
                row = self.connection.execute(
                    """SELECT * FROM tasks JOIN workflows
                    ON workflows.workflow_id = tasks.workflow_id
                    WHERE workflows.session_id = ? AND tasks.agent_id = ?
                    ORDER BY workflows.updated_at DESC, tasks.created_at DESC LIMIT 1""",
                    (session_id, agent_id),
                ).fetchone()
                if row is not None:
                    task = self.connection.execute(
                        "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
                        (row["workflow_id"], row["task_id"]),
                    ).fetchone()
                    workflow = self.connection.execute(
                        "SELECT * FROM workflows WHERE workflow_id = ?",
                        (row["workflow_id"],),
                    ).fetchone()
                    if task is not None and workflow is not None:
                        return dict(workflow), dict(task)
        return None

    def workflow_for_session_return(
        self,
        session_id: str,
        task_id: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Resolve the workflow that should receive a child return.

        A late SubagentStop after mechanical close must stay on that closed
        workflow and must not bind to a newer ACTIVE successor.
        """
        matched = self.find_session_task(session_id, task_id=task_id, agent_id=agent_id)
        if matched is not None:
            return matched[0]
        with self._lock:
            active = self.connection.execute(
                "SELECT * FROM workflows WHERE session_id = ? AND state = 'ACTIVE'",
                (session_id,),
            ).fetchone()
            closed = self.connection.execute(
                """SELECT * FROM workflows WHERE session_id = ? AND state IN ('CLOSED', 'CANCELLED')
                ORDER BY updated_at DESC, created_at DESC, workflow_id DESC LIMIT 1""",
                (session_id,),
            ).fetchone()
        if closed is not None:
            if active is None:
                return dict(closed)
            started_on_active = False
            if agent_id:
                started_on_active = self.connection.execute(
                    "SELECT 1 FROM tasks WHERE workflow_id = ? AND agent_id = ?",
                    (active["workflow_id"], agent_id),
                ).fetchone() is not None
            if not started_on_active:
                return dict(closed)
            return dict(active)
        return dict(active) if active is not None else None

    def ensure_delivery_task(
        self,
        workflow_id: str,
        agent_id: str,
        agent_type: str,
    ) -> dict[str, Any]:
        """Return the bound or unique declared task, else create a delivery-only task."""
        if not agent_id:
            raise ValueError("agent_id is required to create a delivery task")
        expected_type = agent_type or "unspecified"
        with self._lock:
            bound = self.connection.execute(
                "SELECT * FROM tasks WHERE workflow_id = ? AND agent_id = ?",
                (workflow_id, agent_id),
            ).fetchone()
            if bound is not None:
                return dict(bound)
            unbound = self.connection.execute(
                """SELECT * FROM tasks
                WHERE workflow_id = ? AND expected_agent_type = ?
                  AND (agent_id IS NULL OR agent_id = '')
                  AND lifecycle IN ('DECLARED', 'RUNNING')
                ORDER BY created_at, task_id""",
                (workflow_id, expected_type),
            ).fetchall()
            if len(unbound) == 1:
                return dict(unbound[0])
            task_id = f"delivery_{hashlib.sha256(agent_id.encode('utf-8')).hexdigest()[:16]}"
            existing = self.connection.execute(
                "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
                (workflow_id, task_id),
            ).fetchone()
            if existing is not None:
                return dict(existing)
        self.register_task(
            workflow_id,
            task_id,
            expected_type,
            f"delivery-only return for {agent_id}",
            required=False,
        )
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
            (workflow_id, task_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"failed to create delivery task: {workflow_id}/{task_id}")
        return dict(row)

    def ensure_open_obligation(
        self,
        workflow_id: str,
        kind: str | ObligationKind,
        owner: str,
        subject: str,
        reason: str,
        source_ref: str,
        touch: bool = True,
    ) -> str:
        """Open an obligation unless the same source_ref is already open."""
        kind_value = kind.value if isinstance(kind, Enum) else str(kind)
        with self._lock:
            existing = self.connection.execute(
                """SELECT obligation_id FROM obligations
                WHERE workflow_id = ? AND kind = ? AND source_ref = ? AND state = 'OPEN'""",
                (workflow_id, kind_value, source_ref),
            ).fetchone()
            if existing is not None:
                return existing[0]
        return self.open_obligation(
            workflow_id, kind, owner, subject, reason, source_ref, touch=touch
        )

    def register_task(
        self,
        workflow_id: str,
        task_id: str,
        expected_agent_type: str,
        objective: str,
        required: bool = True,
    ) -> str:
        now = _now()
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO tasks
                (workflow_id, task_id, expected_agent_type, objective, required, lifecycle, created_at)
                VALUES (?, ?, ?, ?, ?, 'DECLARED', ?)""",
                (workflow_id, task_id, expected_agent_type, objective, int(required), now),
            )
            self._touch_workflow(workflow_id)
            self._append_event(
                workflow_id, "TASK_DECLARED", task_id,
                {"required": bool(required)}, f"TASK_DECLARED:{workflow_id}:{task_id}"
            )
        return task_id

    def _set_task_lifecycle(self, workflow_id: str, task_id: str, lifecycle: str) -> None:
        if lifecycle in DISALLOWED_SEMANTIC_STATES or lifecycle not in TASK_LIFECYCLES:
            raise ValueError(f"invalid task lifecycle: {lifecycle}")
        returned_at = _now() if lifecycle in {"RETURNED_TYPED", "RETURNED_UNTYPED", "INTAKEN"} else None
        self.connection.execute(
            "UPDATE tasks SET lifecycle = ?, returned_at = COALESCE(?, returned_at) WHERE workflow_id = ? AND task_id = ?",
            (lifecycle, returned_at, workflow_id, task_id),
        )
        if self.connection.execute("SELECT changes()").fetchone()[0] != 1:
            raise KeyError(f"unknown task: {workflow_id}/{task_id}")

    def record_agent_started(
        self, workflow_id: str, task_id: str, agent_id: str, agent_type: str = ""
    ) -> str | None:
        dedupe = f"SUBAGENT_START:{workflow_id}:{task_id}:{agent_id}"
        with self._lock, self.connection:
            if self._event_exists(dedupe):
                return None
            self.connection.execute(
                "UPDATE tasks SET agent_id = ?, lifecycle = 'RUNNING' WHERE workflow_id = ? AND task_id = ?",
                (agent_id, workflow_id, task_id),
            )
            if self.connection.execute("SELECT changes()").fetchone()[0] != 1:
                raise KeyError(f"unknown task: {workflow_id}/{task_id}")
            event_id = _new_id("evt")
            self._append_event(
                workflow_id, "SUBAGENT_START", task_id,
                {"agent_id": agent_id, "agent_type": agent_type}, dedupe, event_id
            )
            self._touch_workflow(workflow_id)
            return event_id

    def _event_exists(self, dedupe_key: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM events WHERE dedupe_key = ?", (dedupe_key,)
        ).fetchone() is not None

    def _append_event(
        self,
        workflow_id: str | None,
        kind: str,
        subject_id: str | None,
        payload: Mapping[str, Any] | None,
        dedupe_key: str,
        event_id: str | None = None,
    ) -> str | None:
        event_id = event_id or _new_id("evt")
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO events
            (event_id, workflow_id, kind, subject_id, payload_json, dedupe_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, workflow_id, kind, subject_id, _json(payload or {}), dedupe_key, _now()),
        )
        return event_id if cursor.rowcount else None

    def append_event(
        self,
        workflow_id: str | None,
        kind: str,
        subject_id: str | None,
        payload: Mapping[str, Any] | None,
        dedupe_key: str,
    ) -> str | None:
        with self._lock, self.connection:
            return self._append_event(workflow_id, kind, subject_id, payload, dedupe_key)

    def _insert_obligation(
        self,
        connection: sqlite3.Connection,
        workflow_id: str,
        kind: str | ObligationKind,
        owner: str,
        subject: str,
        reason: str,
        source_ref: str,
        obligation_id: str | None = None,
        owner_actor_context_id: str | None = None,
        source_actor_context_id: str | None = None,
    ) -> str:
        kind_value = normalize_obligation_kind(kind)
        allowed = {normalize_obligation_kind(member) for member in ObligationKind}
        if kind_value not in allowed:
            raise ValueError(f"unknown obligation kind: {kind_value}")
        if owner_actor_context_id is None:
            workflow = connection.execute(
                "SELECT actor_context_id FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()
            if workflow is not None and workflow["actor_context_id"]:
                owner_actor_context_id = str(workflow["actor_context_id"])
        obligation_id = obligation_id or _new_id("obl")
        connection.execute(
            """INSERT INTO obligations
            (obligation_id, workflow_id, kind, owner, subject, reason, source_ref, state,
             owner_actor_context_id, source_actor_context_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)""",
            (
                obligation_id,
                workflow_id,
                kind_value,
                owner,
                subject,
                reason,
                source_ref,
                owner_actor_context_id,
                source_actor_context_id,
                _now(),
            ),
        )
        return obligation_id

    def open_obligation(
        self,
        workflow_id: str,
        kind: str | ObligationKind,
        owner: str,
        subject: str,
        reason: str,
        source_ref: str,
        obligation_id: str | None = None,
        touch: bool = True,
    ) -> str:
        with self._lock, self.connection:
            result = self._insert_obligation(
                self.connection, workflow_id, kind, owner, subject, reason, source_ref, obligation_id
            )
            if touch:
                self._touch_workflow(workflow_id)
            kind_value = kind.value if isinstance(kind, Enum) else str(kind)
            self._append_event(
                workflow_id, "OBLIGATION_OPENED", result, {"kind": kind_value},
                f"OBLIGATION_OPENED:{result}"
            )
            return result

    def _report_values(
        self, raw_message: str, packet: SubagentReturnPacket | Mapping[str, Any] | None
    ) -> tuple[str | None, int, str]:
        if packet is None:
            return None, 0, ""
        if isinstance(packet, Mapping):
            typed = dict(packet)
        else:
            typed = dataclasses.asdict(packet)
        typed_json = _json(typed)
        return typed_json, 1, typed_json

    def _record_report(
        self,
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str,
        raw_message: str,
        packet: SubagentReturnPacket | Mapping[str, Any] | None,
        lifecycle: str,
        event_kind: str,
    ) -> str:
        if not isinstance(raw_message, str):
            raise TypeError("raw_message must be text")
        if lifecycle == "RETURNED_TYPED":
            if packet is None:
                raise ProtocolError("typed report packet is required")
            if isinstance(packet, SubagentReturnPacket):
                # Round-trip through JSON so tuple fields in the frozen Python
                # model have the same list shape as the wire envelope.
                packet_data: Mapping[str, Any] = json.loads(
                    _json(dataclasses.asdict(packet))
                )
            elif isinstance(packet, Mapping):
                packet_data = packet
            else:
                raise ProtocolError("typed report packet must be a validated packet or mapping")
            packet = validate_subagent_return(packet_data)
            if packet.workflow_id != workflow_id or packet.task_id != task_id:
                raise ValueError("typed report identity does not match its task")
        elif lifecycle == "RETURNED_UNTYPED":
            packet = None
        else:
            raise ValueError(f"invalid report lifecycle: {lifecycle}")
        typed_json, schema_valid, _ = self._report_values(raw_message, packet)
        digest = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()
        with self._lock, self.connection:
            existing = self.connection.execute(
                "SELECT report_id FROM reports WHERE workflow_id = ? AND task_id = ? AND raw_sha256 = ?",
                (workflow_id, task_id, digest),
            ).fetchone()
            if existing:
                return existing[0]
            report_id = _new_id("rep")
            self.connection.execute(
                """INSERT INTO reports
                (report_id, workflow_id, task_id, agent_id, agent_type, raw_message, typed_json,
                 schema_valid, raw_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (report_id, workflow_id, task_id, agent_id, agent_type, raw_message,
                 typed_json, schema_valid, digest, _now()),
            )
            self._set_task_lifecycle(workflow_id, task_id, lifecycle)
            workflow_row = self.connection.execute(
                "SELECT actor_context_id FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()
            owner_actor = (
                str(workflow_row["actor_context_id"])
                if workflow_row is not None and workflow_row["actor_context_id"]
                else None
            )
            task_row = self.connection.execute(
                "SELECT child_actor_context_id FROM tasks WHERE workflow_id = ? AND task_id = ?",
                (workflow_id, task_id),
            ).fetchone()
            source_actor = (
                str(task_row["child_actor_context_id"])
                if task_row is not None and task_row["child_actor_context_id"]
                else None
            )
            self.connection.execute(
                """UPDATE reports SET reporter_actor_context_id = ?
                WHERE report_id = ?""",
                (source_actor, report_id),
            )
            obligation_id = self._insert_obligation(
                self.connection,
                workflow_id,
                ObligationKind.REPORT_INTAKE_REQUIRED,
                owner_actor or "/root",
                report_id,
                "A child report requires explicit owner intake.",
                report_id,
                owner_actor_context_id=owner_actor,
                source_actor_context_id=source_actor,
            )
            self._touch_workflow(workflow_id)
            self._append_event(
                workflow_id, "OBLIGATION_OPENED", obligation_id,
                {"kind": ObligationKind.REPORT_INTAKE_REQUIRED.value},
                f"OBLIGATION_OPENED:{obligation_id}",
            )
            self._append_event(
                workflow_id, event_kind, report_id,
                {"report_id": report_id, "schema_valid": bool(schema_valid)},
                f"{event_kind}:{report_id}",
            )
            return report_id

    def record_report(
        self,
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str,
        raw_message: str,
        packet: SubagentReturnPacket | Mapping[str, Any],
    ) -> str:
        return self._record_report(
            workflow_id, task_id, agent_id, agent_type, raw_message, packet,
            "RETURNED_TYPED", "REPORT_AVAILABLE"
        )

    def record_untyped_return(
        self, workflow_id: str, task_id: str, agent_id: str, agent_type: str, raw_message: str
    ) -> str:
        return self._record_report(
            workflow_id, task_id, agent_id, agent_type, raw_message, None,
            "RETURNED_UNTYPED", "UNTYPED_REPORT_AVAILABLE"
        )

    def register_native_child_bridge(
        self,
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str,
        objective: str,
        required: bool = True,
    ) -> str | None:
        """Register and bind one native child for the explicit wait bridge.

        This is deliberately only task delivery metadata.  It does not infer a
        child result, scientific state, or any disposition.  Repeating the
        same registration is idempotent; a conflicting identity or terminal
        task is rejected before a new event can be written.
        """
        for label, value in {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "objective": objective,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be non-empty")
        with self._lock:
            workflow = self.connection.execute(
                "SELECT state FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
            if workflow is None:
                raise KeyError(f"unknown workflow: {workflow_id}")
            if str(workflow["state"]) != "ACTIVE":
                raise ValueError("native child bridge requires an ACTIVE workflow")
            task = self.connection.execute(
                "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
                (workflow_id, task_id),
            ).fetchone()
            if task is None:
                self.register_task(
                    workflow_id, task_id, agent_type, objective, required=required
                )
            else:
                if str(task["expected_agent_type"]) != agent_type:
                    raise ValueError("native child agent_type conflicts with declared task")
                if str(task["objective"]) != objective or bool(task["required"]) != bool(required):
                    raise ValueError("native child registration conflicts with declared task")
                bound_agent_id = str(task["agent_id"] or "")
                if bound_agent_id and bound_agent_id != agent_id:
                    raise ValueError("native child agent_id conflicts with declared task")
                if str(task["lifecycle"]) in {"RETURNED_TYPED", "RETURNED_UNTYPED", "INTAKEN", "CANCELLED"}:
                    raise ValueError("native child task is already terminal")
            return self.record_agent_started(workflow_id, task_id, agent_id, agent_type)

    def record_native_child_signal(
        self,
        workflow_id: str,
        task_id: str,
        agent_id: str,
        agent_type: str,
        signal_id: str,
        outcome: str,
    ) -> dict[str, Any]:
        """Append one idempotent, content-free native-child report event.

        The child calls this immediately before its ordinary final return.  It
        gives a waiting Root a durable cursor wake-up, but the actual child
        conclusion remains on the native collaboration channel.  ``ANOMALY``
        is therefore a report event, never a direction disposition.
        """
        allowed_outcomes = {"COMPLETED", "ANOMALY"}
        if outcome not in allowed_outcomes:
            raise ValueError("outcome must be COMPLETED or ANOMALY")
        for label, value in {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "signal_id": signal_id,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be non-empty")
        if len(signal_id) > 256:
            raise ValueError("signal_id must be at most 256 characters")

        raw_message = _json(
            {
                "schema": "HMASD_NATIVE_CHILD_SIGNAL_V1",
                "signal_id": signal_id,
                "outcome": outcome,
            }
        )
        digest = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()
        with self._lock:
            workflow = self.connection.execute(
                "SELECT state FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
            if workflow is None:
                raise KeyError(f"unknown workflow: {workflow_id}")
            if str(workflow["state"]) != "ACTIVE":
                raise ValueError("native child signal requires an ACTIVE workflow")
            task = self.connection.execute(
                "SELECT * FROM tasks WHERE workflow_id = ? AND task_id = ?",
                (workflow_id, task_id),
            ).fetchone()
            if task is None:
                raise KeyError(f"unknown task: {workflow_id}/{task_id}")
            if str(task["agent_id"] or "") != agent_id:
                raise ValueError("native child signal agent_id is not bound to task")
            existing = self.connection.execute(
                """SELECT report_id FROM reports
                WHERE workflow_id = ? AND task_id = ? AND raw_sha256 = ?""",
                (workflow_id, task_id, digest),
            ).fetchone()
            if existing is not None:
                return {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "report_id": str(existing["report_id"]),
                    "outcome": outcome,
                    "idempotent": True,
                }
            if str(task["lifecycle"]) != "RUNNING":
                raise ValueError("native child task is not running and cannot signal")
            report_id = self._record_report(
                workflow_id,
                task_id,
                agent_id,
                agent_type,
                raw_message,
                None,
                "RETURNED_UNTYPED",
                "NATIVE_CHILD_REPORT_AVAILABLE",
            )
            return {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "report_id": report_id,
                "outcome": outcome,
                "idempotent": False,
            }

    def record_intake(
        self,
        workflow_id: str,
        report_id: str,
        intake_kind: IntakeKind | str,
        translation: Mapping[str, str],
        next_action: Mapping[str, str] | None = None,
        note: str = "",
    ) -> str:
        if isinstance(intake_kind, RootIntakePacket):
            packet = intake_kind
            intake_kind, translation, next_action, note = (
                packet.intake_kind, packet.translation, dataclasses.asdict(packet.next_action), packet.note
            )
        kind_value = intake_kind.value if isinstance(intake_kind, Enum) else str(intake_kind)
        if kind_value not in {member.value for member in IntakeKind}:
            raise ValueError(f"unknown intake kind: {kind_value}")
        with self._lock, self.connection:
            report = self.connection.execute(
                "SELECT task_id FROM reports WHERE report_id = ? AND workflow_id = ?",
                (report_id, workflow_id),
            ).fetchone()
            if report is None:
                raise KeyError(f"unknown report: {report_id}")
            obligation = self.connection.execute(
                """SELECT obligation_id FROM obligations
                WHERE workflow_id = ? AND kind IN (?, ?) AND subject = ? AND state = 'OPEN'""",
                (
                    workflow_id,
                    ObligationKind.REPORT_INTAKE_REQUIRED.value,
                    ObligationKind.ROOT_INTAKE_REQUIRED.value,
                    report_id,
                ),
            ).fetchone()
            if obligation is None:
                raise ValueError(f"report obligation is not open: {report_id}")
            intake_id = _new_id("intake")
            self.connection.execute(
                """INSERT INTO intakes
                (intake_id, workflow_id, report_id, intake_kind, translation_json, next_action_json, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (intake_id, workflow_id, report_id, kind_value, _json(dict(translation)),
                 _json(dict(next_action)) if next_action is not None else None, note, _now()),
            )
            resolution = {"intake_id": intake_id}
            self.connection.execute(
                "UPDATE obligations SET state = 'RESOLVED', resolution_json = ?, resolved_at = ? WHERE obligation_id = ?",
                (_json(resolution), _now(), obligation[0]),
            )
            self._set_task_lifecycle(workflow_id, report[0], "INTAKEN")
            self._touch_workflow(workflow_id)
            self._append_event(
                workflow_id, "OBLIGATION_RESOLVED", obligation[0],
                {"resolution": resolution}, f"OBLIGATION_RESOLVED:{obligation[0]}",
            )
            self._append_event(
                workflow_id, "ROOT_INTAKE_RECORDED", report_id,
                {"intake_id": intake_id, "intake_kind": kind_value},
                f"ROOT_INTAKE_RECORDED:{report_id}",
            )
            return intake_id

    def resolve_obligation(
        self, workflow_id: str, obligation_id: str, resolution: Mapping[str, Any] | None = None
    ) -> str:
        with self._lock, self.connection:
            cursor = self.connection.execute(
                """UPDATE obligations SET state = 'RESOLVED', resolution_json = ?, resolved_at = ?
                WHERE workflow_id = ? AND obligation_id = ? AND state = 'OPEN'""",
                (_json(resolution or {}), _now(), workflow_id, obligation_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"open obligation not found: {obligation_id}")
            self._touch_workflow(workflow_id)
            self._append_event(
                workflow_id, "OBLIGATION_RESOLVED", obligation_id,
                {"resolution": resolution or {}}, f"OBLIGATION_RESOLVED:{obligation_id}"
            )
            return obligation_id

    def events_after(self, workflow_id: str | None, after_seq: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                """SELECT seq, event_id, workflow_id, kind, subject_id, payload_json, dedupe_key, created_at
                FROM events WHERE (? IS NULL OR workflow_id = ?) AND seq > ? ORDER BY seq""",
                (workflow_id, workflow_id, after_seq),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            item["disposition_implied"] = False
            result.append(item)
        return result

    def await_events(self, workflow_id: str, after_seq: int = 0) -> list[dict[str, Any]]:
        """Return the durable event stream after a caller-owned cursor.

        The wait loop deliberately re-reads this cursor from SQLite before each
        sleep.  Keeping this small primitive on the store gives the MCP layer a
        single, explicit read path and avoids coupling event polling to report
        payloads or model-visible state.
        """
        self.workflow_state(workflow_id)
        return self.events_after(workflow_id, after_seq)

    def await_global_events(self, after_seq: int = 0) -> list[dict[str, Any]]:
        """Return the global durable event stream after a caller-owned cursor.

        ``events.seq`` is a database-wide AUTOINCREMENT cursor, so this path
        intentionally has no workflow, session, or task binding. It is used by
        the cross-workflow wait primitive; callers still own the cursor and
        must pass the returned value back to avoid replaying observed events.
        """
        return self.events_after(None, after_seq)

    def validate_task_ids(self, workflow_id: str, task_ids: list[str] | tuple[str, ...]) -> None:
        """Reject task filters that name tasks outside the selected workflow."""
        state = self.workflow_state(workflow_id)
        known = {str(task["task_id"]) for task in state["tasks"]}
        requested = {str(task_id) for task_id in task_ids}
        unknown = sorted(requested - known)
        if unknown:
            raise ValueError(
                f"task_ids must belong to workflow {workflow_id}: {', '.join(unknown)}"
            )

    def workflow_state(self, workflow_id: str) -> dict[str, Any]:
        with self._lock:
            workflow = self.connection.execute(
                "SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
            if workflow is None:
                raise KeyError(f"unknown workflow: {workflow_id}")
            tasks = [dict(row) for row in self.connection.execute(
                "SELECT * FROM tasks WHERE workflow_id = ? ORDER BY created_at, task_id", (workflow_id,)
            ).fetchall()]
            obligations = [dict(row) for row in self.connection.execute(
                "SELECT * FROM obligations WHERE workflow_id = ? AND state = 'OPEN' ORDER BY created_at, obligation_id",
                (workflow_id,),
            ).fetchall()]
            latest_event_seq = self.connection.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM events WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()[0]
            for item in obligations:
                item["kind"] = normalize_obligation_kind(str(item.get("kind") or ""))
            result = dict(workflow)
            result["tasks"] = tasks
            result["open_obligations"] = obligations
            result["obligation_count"] = len(obligations)
            # This is the only cursor callers may feed back to after_seq.
            # state_version tracks workflow mutations and deliberately has
            # independent semantics from the durable event stream.
            result["await_cursor"] = int(latest_event_seq)
            result["open_task_ids"] = [
                task["task_id"] for task in tasks if task["lifecycle"] not in {"INTAKEN", "CANCELLED"}
            ]
            return result

    def all_required_tasks_returned(self, workflow_id: str) -> bool:
        """Return whether every required task has reached a returned lifecycle."""
        state = self.workflow_state(workflow_id)
        return all(
            not task["required"] or task["lifecycle"] in RETURNED_TASK_LIFECYCLES
            for task in state["tasks"]
        )

    def is_workflow_quiescent(self, workflow_id: str) -> bool:
        """Return the typed-state quiescence predicate without mutating the workflow."""
        state = self.workflow_state(workflow_id)
        return (
            not state["open_obligations"]
            and all(task["lifecycle"] in QUIESCENT_TASK_LIFECYCLES for task in state["tasks"])
        )

    def create_closure_receipt(
        self, workflow_id: str, closure_kind: str, summary: str
    ) -> str:
        if closure_kind not in CLOSURE_KINDS:
            raise ValueError(f"unknown closure kind: {closure_kind}")
        if closure_kind in CONTROL_PLANE_CLOSURE_KINDS:
            raise ValueError("CONTROL_PLANE_ROLLOVER requires workflow-reconcile")
        with self._lock, self.connection:
            state = self.workflow_state(workflow_id)
            if state["open_obligations"]:
                raise ValueError("workflow has open obligations")
            open_tasks = [
                task for task in state["tasks"]
                if task["lifecycle"] in OPEN_TASK_LIFECYCLES
            ]
            if open_tasks:
                raise ValueError("workflow has tasks that are not complete")
            if closure_kind == "EMPTY_SESSION_ENDED" and state["tasks"]:
                raise ValueError("empty-session close requires no managed tasks")
            receipt_id = _new_id("receipt")
            self.connection.execute(
                "INSERT INTO closure_receipts(receipt_id, workflow_id, closure_kind, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                (receipt_id, workflow_id, closure_kind, summary, _now()),
            )
            next_state = "CLOSED" if closure_kind in {"COMPLETED", "EMPTY_SESSION_ENDED"} else "CANCELLED"
            self._touch_workflow(workflow_id, next_state)
            self._append_event(
                workflow_id, "WORKFLOW_CLOSED", receipt_id,
                {"closure_kind": closure_kind}, f"WORKFLOW_CLOSED:{workflow_id}"
            )
            return receipt_id

    @staticmethod
    def _rollover_receipt_payload(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any] | None:
        """Decode only receipts produced by the explicit rollover operation."""
        if str(row["closure_kind"]) != "CONTROL_PLANE_ROLLOVER":
            return None
        try:
            payload = json.loads(str(row["summary"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or payload.get("schema") != ROLLOVER_RECEIPT_SCHEMA:
            return None
        return payload

    def reconcile_workflow(
        self,
        workflow_id: str,
        *,
        expected_state_version: int,
        expected_await_cursor: int,
        reconciliation_id: str,
        reason: str,
        apply: bool,
        operator_id: str | None = None,
    ) -> dict[str, Any]:
        """Plan or atomically apply one explicit control-plane epoch rollover.

        This operation deliberately bypasses ordinary scientific intake.  It
        retains every report and existing event while retiring only the stale
        delivery-control objects named by the selected workflow.
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")
        if expected_state_version < 0 or expected_await_cursor < 0:
            raise ValueError("expected state version and await cursor must be non-negative")
        if not reconciliation_id.strip():
            raise ValueError("reconciliation_id is required")
        if not reason.strip():
            raise ValueError("reason is required")
        if apply and operator_id != "/root":
            raise ValueError("workflow-reconcile --apply requires operator_id=/root")

        with self._lock:
            # Planning uses a consistent read snapshot without acquiring a
            # reserved writer lock.  Only the mutating path uses IMMEDIATE so
            # the expected-version/cursor comparison and all changes are one
            # indivisible writer transaction.
            self.connection.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
            try:
                prior = self.connection.execute(
                    "SELECT * FROM closure_receipts WHERE workflow_id = ?",
                    (workflow_id,),
                ).fetchone()
                if prior is not None:
                    payload = self._rollover_receipt_payload(prior)
                    if payload is None:
                        raise ValueError("workflow already has a non-rollover closure receipt")
                    if payload.get("reconciliation_id") != reconciliation_id:
                        raise ValueError("workflow was rolled over by a different reconciliation_id")
                    result = dict(payload)
                    result.update(
                        {
                            "workflow_id": workflow_id,
                            "receipt_id": str(prior["receipt_id"]),
                            "eligible": True,
                            "applied": True,
                            "replayed": True,
                        }
                    )
                    self.connection.rollback()
                    return result

                workflow = self.connection.execute(
                    "SELECT * FROM workflows WHERE workflow_id = ?",
                    (workflow_id,),
                ).fetchone()
                if workflow is None:
                    raise KeyError(f"unknown workflow: {workflow_id}")

                actual_state_version = int(workflow["state_version"])
                actual_await_cursor = int(
                    self.connection.execute(
                        "SELECT COALESCE(MAX(seq), 0) FROM events WHERE workflow_id = ?",
                        (workflow_id,),
                    ).fetchone()[0]
                )
                if actual_state_version != expected_state_version:
                    raise ValueError(
                        "expected_state_version mismatch: "
                        f"expected {expected_state_version}, observed {actual_state_version}"
                    )
                if actual_await_cursor != expected_await_cursor:
                    raise ValueError(
                        "expected_await_cursor mismatch: "
                        f"expected {expected_await_cursor}, observed {actual_await_cursor}"
                    )

                exclusions: list[dict[str, str]] = []
                if str(workflow["state"]) != "ACTIVE":
                    exclusions.append(
                        {
                            "kind": "WORKFLOW_NOT_ACTIVE",
                            "exact_object": workflow_id,
                            "observed_fact": f"state={workflow['state']}",
                        }
                    )
                if str(workflow["scope"]) != "session":
                    exclusions.append(
                        {
                            "kind": "NON_SESSION_SCOPE",
                            "exact_object": workflow_id,
                            "observed_fact": f"scope={workflow['scope']}",
                        }
                    )

                user_decisions = self.connection.execute(
                    """SELECT obligation_id FROM obligations
                    WHERE workflow_id = ? AND state = 'OPEN' AND kind = ?
                    ORDER BY created_at, obligation_id""",
                    (workflow_id, ObligationKind.USER_DECISION_REQUIRED.value),
                ).fetchall()
                for obligation in user_decisions:
                    exclusions.append(
                        {
                            "kind": "USER_DECISION_OBLIGATION",
                            "exact_object": str(obligation["obligation_id"]),
                            "observed_fact": "open USER_DECISION_REQUIRED obligation",
                        }
                    )

                open_obligation_count = int(
                    self.connection.execute(
                        "SELECT COUNT(*) FROM obligations WHERE workflow_id = ? AND state = 'OPEN'",
                        (workflow_id,),
                    ).fetchone()[0]
                )
                cancellable_task_count = int(
                    self.connection.execute(
                        """SELECT COUNT(*) FROM tasks
                        WHERE workflow_id = ? AND lifecycle NOT IN ('INTAKEN', 'CANCELLED')""",
                        (workflow_id,),
                    ).fetchone()[0]
                )
                intaken_task_count = int(
                    self.connection.execute(
                        "SELECT COUNT(*) FROM tasks WHERE workflow_id = ? AND lifecycle = 'INTAKEN'",
                        (workflow_id,),
                    ).fetchone()[0]
                )
                report_count = int(
                    self.connection.execute(
                        "SELECT COUNT(*) FROM reports WHERE workflow_id = ?", (workflow_id,)
                    ).fetchone()[0]
                )
                event_count = int(
                    self.connection.execute(
                        "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (workflow_id,)
                    ).fetchone()[0]
                )

                plan = {
                    "schema": ROLLOVER_RECEIPT_SCHEMA,
                    "workflow_id": workflow_id,
                    "reconciliation_id": reconciliation_id,
                    "reason": reason,
                    "operator_id": operator_id if apply else None,
                    "old_state_version": actual_state_version,
                    "old_await_cursor": actual_await_cursor,
                    "cancelled_obligation_count": open_obligation_count,
                    "cancelled_task_count": cancellable_task_count,
                    "preserved_intaken_task_count": intaken_task_count,
                    "preserved_report_count": report_count,
                    "preserved_event_count": event_count,
                }
                if exclusions:
                    self.connection.rollback()
                    return {
                        **plan,
                        "eligible": False,
                        "applied": False,
                        "replayed": False,
                        "exclusions": exclusions,
                    }
                if not apply:
                    self.connection.rollback()
                    return {
                        **plan,
                        "eligible": True,
                        "applied": False,
                        "replayed": False,
                        "exclusions": [],
                    }

                now = _now()
                resolution = _json(
                    {
                        "resolution_kind": ROLLOVER_RESOLUTION_KIND,
                        "reconciliation_id": reconciliation_id,
                        "reason": reason,
                    }
                )
                self.connection.execute(
                    """UPDATE obligations
                    SET state = 'CANCELLED', resolution_json = ?, resolved_at = ?
                    WHERE workflow_id = ? AND state = 'OPEN'""",
                    (resolution, now, workflow_id),
                )
                if self.connection.execute("SELECT changes()").fetchone()[0] != open_obligation_count:
                    raise RuntimeError("open obligation set changed during rollover")
                self.connection.execute(
                    """UPDATE tasks SET lifecycle = 'CANCELLED'
                    WHERE workflow_id = ? AND lifecycle NOT IN ('INTAKEN', 'CANCELLED')""",
                    (workflow_id,),
                )
                if self.connection.execute("SELECT changes()").fetchone()[0] != cancellable_task_count:
                    raise RuntimeError("open task set changed during rollover")

                receipt_id = _new_id("receipt")
                receipt_summary = _json({**plan, "operator_id": operator_id})
                self.connection.execute(
                    """INSERT INTO closure_receipts
                    (receipt_id, workflow_id, closure_kind, summary, created_at)
                    VALUES (?, ?, 'CONTROL_PLANE_ROLLOVER', ?, ?)""",
                    (receipt_id, workflow_id, receipt_summary, now),
                )
                self._touch_workflow(workflow_id, "CANCELLED")
                self._append_event(
                    workflow_id,
                    "WORKFLOW_ROLLED_OVER",
                    receipt_id,
                    {**plan, "operator_id": operator_id, "receipt_id": receipt_id},
                    f"WORKFLOW_ROLLED_OVER:{workflow_id}:{reconciliation_id}",
                )
                self.connection.commit()
                return {
                    **plan,
                    "operator_id": operator_id,
                    "receipt_id": receipt_id,
                    "eligible": True,
                    "applied": True,
                    "replayed": False,
                    "exclusions": [],
                }
            except Exception:
                self.connection.rollback()
                raise

    def acquire_guard_once(self, guard_key: str, event_name: str) -> bool:
        with self._lock, self.connection:
            now = _now()
            cursor = self.connection.execute(
                """INSERT OR IGNORE INTO hook_guards
                (guard_key, event_name, count, created_at, updated_at) VALUES (?, ?, 1, ?, ?)""",
                (guard_key, event_name, now, now),
            )
            if cursor.rowcount:
                return True
            self.connection.execute(
                "UPDATE hook_guards SET count = count + 1, updated_at = ? WHERE guard_key = ?",
                (now, guard_key),
            )
            return False
