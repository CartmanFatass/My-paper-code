"""Actor-local Stop decisions. One actor's routine work cannot hold another open."""

from __future__ import annotations

from typing import Any

from .actor_models import ActorKind, actor_context_from_row
from .models import normalize_obligation_kind
from .responsibility import responsibility_blocks_stop
from .store import OPEN_TASK_LIFECYCLES, SemanticStore


ROOT_BLOCKING = frozenset(
    {
        "PACKET_INTAKE_REQUIRED",
        "PORTFOLIO_REVIEW_REQUIRED",
        "USER_DECISION_REQUIRED",
        "CONTEXT_REANCHOR_REQUIRED",
        "REPORT_INTAKE_REQUIRED",
    }
)
PORTFOLIO_BLOCKING = frozenset(
    {
        "PACKET_INTAKE_REQUIRED",
        "PORTFOLIO_REVIEW_REQUIRED",
        "CONTEXT_REANCHOR_REQUIRED",
        "REPORT_INTAKE_REQUIRED",
    }
)
EM_BLOCKING = frozenset(
    {
        "REPORT_INTAKE_REQUIRED",
        "PACKET_INTAKE_REQUIRED",
        "CONTEXT_REANCHOR_REQUIRED",
        "FOLLOWUP_DECISION_REQUIRED",
    }
)
CM_BLOCKING = frozenset(
    {
        "REPORT_INTAKE_REQUIRED",
        "PACKET_INTAKE_REQUIRED",
        "CONTEXT_REANCHOR_REQUIRED",
        "FOLLOWUP_DECISION_REQUIRED",
    }
)


def _blocking_kinds(kind: ActorKind) -> frozenset[str]:
    if kind == ActorKind.PORTFOLIO:
        return PORTFOLIO_BLOCKING
    if kind == ActorKind.OPERATIONAL_ROOT:
        return ROOT_BLOCKING
    if kind == ActorKind.EM:
        return EM_BLOCKING
    if kind == ActorKind.CM:
        return CM_BLOCKING
    return frozenset()


def stop_decision_for_actor(
    store: SemanticStore,
    actor_context_id: str,
    turn_id: str,
    stop_hook_active: bool,
) -> dict[str, Any]:
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        return {"continue": True, "empty_session_ended": False}
    actor = actor_context_from_row(row)
    if actor.actor_kind == ActorKind.LEAF:
        return {"continue": True, "empty_session_ended": False, "leaf": True}
    workflow = store.current_actor_workflow(actor_context_id)
    if workflow is None:
        return {"continue": True, "empty_session_ended": False}
    state = store.workflow_state(str(workflow["workflow_id"]))
    obligations = list(state.get("open_obligations") or [])
    blocking = [
        item
        for item in obligations
        if (
            normalize_obligation_kind(str(item.get("kind") or "")) in _blocking_kinds(actor.actor_kind)
            or responsibility_blocks_stop(dict(item.get("responsibility") or {}))
        )
    ]
    local_tasks = [
        task
        for task in state.get("tasks", [])
        if str(task.get("lifecycle") or "") in OPEN_TASK_LIFECYCLES
        and (
            str(task.get("invoker_actor_context_id") or "") == actor_context_id
            or not task.get("invoker_actor_context_id")
        )
    ]
    if not blocking and not local_tasks:
        from .epochs import plan_epoch_current

        epoch = plan_epoch_current(store, actor_context_id)
        if epoch is None and actor.actor_kind in {ActorKind.OPERATIONAL_ROOT, ActorKind.PORTFOLIO, ActorKind.SESSION_ROOT_UNCLASSIFIED}:
            return {
                "continue": True,
                "empty_session_ended": True,
                "workflow_id": workflow["workflow_id"],
            }
        return {"continue": True, "empty_session_ended": False}
    if stop_hook_active:
        return {"continue": True, "loop_prevented": True, "empty_session_ended": False}
    state_version = str(state.get("state_version") or "")
    guard_key = f"STOP:{actor_context_id}:{turn_id}:{state_version}"
    if not store.acquire_guard_once(guard_key, "Stop"):
        return {"continue": True, "loop_prevented": True, "empty_session_ended": False}
    return {
        "decision": "block",
        "reason": "HMASD_ACTOR_LOCAL_STOP",
        "open_obligation_ids": [item.get("obligation_id") for item in blocking],
        "empty_session_ended": False,
    }
