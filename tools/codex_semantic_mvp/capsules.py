"""Role-projected context capsules. Raw prose is never included."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .actor_models import ActorKind, actor_context_from_row
from .constants import MAX_CAPSULE_BYTES
from .epochs import plan_epoch_current
from .models import normalize_obligation_kind
from .semantic_commits import semantic_commit_current
from .store import SemanticStore

try:
    from tools.codex_context_lifecycle.precedence import PRECEDENCE_HEADER
    from tools.codex_context_lifecycle.working_set import build_working_set
except ImportError:  # pragma: no cover - overlay-only environments
    PRECEDENCE_HEADER = ""
    build_working_set = None


CAPSULE_SCHEMA_VERSION = 1
FORBIDDEN_INFERENCES = (
    "Do not infer scientific, technical, direction, or portfolio dispositions from raw prose.",
    "Compaction does not close tasks, resolve obligations, or revise a plan epoch.",
    "SQLite is a control-plane ledger, not canonical project memory.",
)

FORBIDDEN_ROOT_LEAKS = ("implementer", "reviewer", "operator", "CPU", "RSS", "PID")
FORBIDDEN_PORTFOLIO_LEAKS = ("CPU", "RSS", "PID", "worktree", "tab state")
FORBIDDEN_CM_LEAKS = ("portfolio priority", "scientific successor", "claim interpretation")
FORBIDDEN_LEAF_LEAKS = ("sibling_direction", "portfolio graph", "root user state")


def _workflow(store: SemanticStore, actor_context_id: str) -> dict[str, Any] | None:
    return store.current_actor_workflow(actor_context_id)


def _obligations(store: SemanticStore, workflow_id: str | None) -> list[dict[str, Any]]:
    if not workflow_id:
        return []
    state = store.workflow_state(workflow_id)
    return list(state.get("open_obligations") or [])


def _packet_rows(store: SemanticStore, actor_context_id: str) -> list[dict[str, Any]]:
    rows = store.connection.execute(
        """SELECT packet_id, packet_kind, marker, payload_ref, delivery_state, intake_state
        FROM packet_refs
        WHERE source_actor_context_id = ? OR target_actor_context_id = ?
        ORDER BY created_at, packet_id""",
        (actor_context_id, actor_context_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _canonical_refs(actor_kind: ActorKind, commit: Mapping[str, Any] | None, epoch: Mapping[str, Any] | None) -> list[str]:
    refs = ["AGENTS.md"]
    if actor_kind == ActorKind.OPERATIONAL_ROOT:
        refs.append(".agents/roles/ROOT.md")
    elif actor_kind == ActorKind.PORTFOLIO:
        refs.append("docs/research/workflow-runs/2026-08-11_five-round-research-team/CROSS_DIRECTION_PORTFOLIO_HANDOFF_SOL_ULTRA.md")
    elif actor_kind == ActorKind.EM:
        refs.append(".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md")
    elif actor_kind == ActorKind.CM:
        refs.append(".agents/roles/CODE_PROJECT_MANAGER.md")
    if epoch:
        refs.extend(str(item) for item in epoch.get("authority_refs") or [] if item)
    if commit:
        payload = commit.get("payload") or {}
        for key, value in payload.items():
            if key.endswith("_ref") and isinstance(value, str) and value:
                refs.append(value)
        refs.extend(str(item) for item in commit.get("source_refs") or [] if item)
    return list(dict.fromkeys(refs))


def build_capsule(store: SemanticStore, actor_context_id: str) -> dict[str, object]:
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    actor = actor_context_from_row(row)
    workflow = _workflow(store, actor_context_id)
    epoch = plan_epoch_current(store, actor_context_id)
    commit = semantic_commit_current(store, actor_context_id)
    working = build_working_set(store, actor_context_id) if build_working_set else None
    obligations = _obligations(store, workflow["workflow_id"] if workflow else None)
    report_ids = [
        str(item.get("subject") or "")
        for item in obligations
        if normalize_obligation_kind(str(item.get("kind") or "")) == "REPORT_INTAKE_REQUIRED"
        and item.get("subject")
    ]
    packets = _packet_rows(store, actor_context_id)
    if working is not None:
        allowed_packets = set(working.active_packet_ids)
        packets = [item for item in packets if item.get("packet_id") in allowed_packets]
        report_ids = list(working.unintaken_report_ids)
        obligations = [
            item
            for item in obligations
            if item.get("obligation_id") in set(working.open_obligation_ids)
        ]
    payload = commit.get("payload") if commit else {}
    body = _project_body(actor.actor_kind, payload or {}, workflow, packets, obligations)
    capsule: dict[str, object] = {
        "schema_version": CAPSULE_SCHEMA_VERSION,
        "capsule_kind": f"{actor.actor_kind.value}_CAPSULE",
        "actor_context_id": actor.actor_context_id,
        "actor_kind": actor.actor_kind.value,
        "scope_key": actor.scope_key,
        "direction_id": actor.direction_id,
        "checkpoint_id": working.checkpoint_id if working else None,
        "state_version": workflow.get("state_version") if workflow else 0,
        "epoch_id": epoch.get("epoch_id") if epoch else None,
        "epoch_revision": epoch.get("revision") if epoch else None,
        "canonical_refs": list((working.canonical_refs if working else _canonical_refs(actor.actor_kind, commit, epoch))),
        "open_obligation_ids": [item.get("obligation_id") for item in obligations],
        "unintaken_report_ids": report_ids,
        "forbidden_inferences": list(FORBIDDEN_INFERENCES),
        "current_objective": (epoch or {}).get("objective") or (workflow or {}).get("objective") or "",
        "frozen_invariants": list((epoch or {}).get("frozen_invariants") or []),
        "next_safe_action": "Call context_checkpoint_current and context_reanchor_ack before mutating actor state.",
        "memory_authority": "none",
        "compaction_summary_authority": "none",
        "body": body,
    }
    return capsule


def _project_body(
    actor_kind: ActorKind,
    payload: Mapping[str, Any],
    workflow: Mapping[str, Any] | None,
    packets: list[dict[str, Any]],
    obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    packet_meta = [
        {
            "packet_id": item.get("packet_id"),
            "packet_kind": item.get("packet_kind"),
            "marker": item.get("marker"),
            "payload_ref": item.get("payload_ref"),
            "delivery_state": item.get("delivery_state"),
            "intake_state": item.get("intake_state"),
        }
        for item in packets
    ]
    if actor_kind == ActorKind.PORTFOLIO:
        return {
            "current_cut_ref": payload.get("current_cut_ref"),
            "bounded_objective": payload.get("bounded_objective"),
            "direction_allocation_summaries": payload.get("direction_rows") or [],
            "cross_direction_relations": payload.get("cross_direction_relations") or [],
            "pending_root_packet_refs": packet_meta,
            "portfolio_local_obligations": [item.get("obligation_id") for item in obligations],
        }
    if actor_kind == ActorKind.OPERATIONAL_ROOT:
        return {
            "current_user_goal": payload.get("current_user_goal"),
            "direction_pairs": payload.get("direction_pairs") or [],
            "pending_l1_milestones": payload.get("pending_l1_milestone_ids") or [],
            "pending_portfolio_refs": payload.get("pending_portfolio_packet_ids") or [],
            "lease_user_git_obligations": [item.get("obligation_id") for item in obligations],
        }
    if actor_kind == ActorKind.EM:
        return {
            "direction_id": payload.get("direction_id"),
            "stage_envelope_ref": payload.get("stage_envelope_ref"),
            "cm_counterpart": payload.get("cm_counterpart_actor_context_id"),
            "current_science_object_ref": payload.get("current_science_object_ref"),
            "current_question": payload.get("current_question"),
            "strongest_live_alternative": payload.get("strongest_live_alternative"),
            "claim_ceiling": payload.get("claim_ceiling"),
            "next_discriminator": payload.get("next_discriminator"),
            "exploration_debt": payload.get("exploration_debt") or [],
            "pending_cm_packet_refs": packet_meta,
            "root_return_trigger": payload.get("root_return_trigger"),
        }
    if actor_kind == ActorKind.CM:
        return {
            "direction_id": payload.get("direction_id"),
            "stage_envelope_ref": payload.get("stage_envelope_ref"),
            "science_card_ref": payload.get("science_card_ref"),
            "protected_semantics": payload.get("protected_semantics") or [],
            "owned_paths": payload.get("owned_paths") or [],
            "worktree_ref": payload.get("worktree_ref") or "",
            "technical_objective": payload.get("technical_objective"),
            "pending_em_handoff_ref": payload.get("pending_em_handoff_ref"),
            "packet_refs": packet_meta,
        }
    return {
        "task_id": payload.get("task_id"),
        "exact_assignment": payload.get("exact_assignment"),
        "named_sources_or_interfaces": payload.get("named_sources_or_interfaces") or [],
        "protected_assumptions": payload.get("protected_assumptions") or [],
        "completion_evidence": payload.get("completion_evidence"),
        "return_contract": payload.get("return_contract") or "HMASD_SUBAGENT_RETURN_V1",
        "invoker_actor_id": workflow.get("actor_context_id") if workflow else None,
    }


def _trim(capsule: dict[str, object]) -> dict[str, object]:
    protected = {
        "schema_version",
        "capsule_kind",
        "actor_context_id",
        "actor_kind",
        "scope_key",
        "direction_id",
        "checkpoint_id",
        "state_version",
        "epoch_id",
        "epoch_revision",
        "canonical_refs",
        "open_obligation_ids",
        "unintaken_report_ids",
        "forbidden_inferences",
        "current_objective",
        "frozen_invariants",
        "next_safe_action",
        "memory_authority",
        "compaction_summary_authority",
    }
    rendered = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(rendered.encode("utf-8")) <= MAX_CAPSULE_BYTES:
        return capsule
    body = dict(capsule.get("body") or {})
    for key in ("closed_historical_references", "older_packet_refs", "advisory_notes"):
        body.pop(key, None)
    if "pending_cm_packet_refs" in body and isinstance(body["pending_cm_packet_refs"], list):
        body["pending_cm_packet_refs"] = body["pending_cm_packet_refs"][-3:]
    if "packet_refs" in body and isinstance(body["packet_refs"], list):
        body["packet_refs"] = body["packet_refs"][-3:]
    trimmed = {key: value for key, value in capsule.items() if key in protected or key == "body"}
    trimmed["body"] = body
    return trimmed


def render_capsule(capsule: Mapping[str, object]) -> str:
    trimmed = _trim(dict(capsule))
    lines = [
        "[HMASD_ACTOR_CAPSULE_V1]",
        f"actor={trimmed.get('actor_kind')} {trimmed.get('actor_context_id')}",
        f"epoch={trimmed.get('epoch_id')} rev={trimmed.get('epoch_revision')}",
        f"state_version={trimmed.get('state_version')}",
        f"objective={trimmed.get('current_objective')}",
        PRECEDENCE_HEADER or "CONTEXT PRECEDENCE",
        "AUTOMATIC_MEMORY_AUTHORITY=NONE",
        "COMPACTION_SUMMARY_AUTHORITY=NONE",
        "AUTHORITY REFERENCES",
    ]
    for ref in trimmed.get("canonical_refs") or []:
        lines.append(f"- {ref}")
    lines.append(f"open_obligation_ids={','.join(str(item) for item in (trimmed.get('open_obligation_ids') or []))}")
    lines.append(f"unintaken_report_ids={','.join(str(item) for item in (trimmed.get('unintaken_report_ids') or []))}")
    lines.append("FORBIDDEN INFERENCES")
    for item in trimmed.get("forbidden_inferences") or []:
        lines.append(f"- {item}")
    body = trimmed.get("body") or {}
    if isinstance(body, Mapping):
        for key, value in body.items():
            if value not in (None, "", [], {}):
                lines.append(f"{key}={value if not isinstance(value, (list, dict)) else json.dumps(value, ensure_ascii=False)}")
    lines.append(f"next_safe_action={trimmed.get('next_safe_action')}")
    lines.append("[/HMASD_ACTOR_CAPSULE_V1]")
    text = "\n".join(lines)
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_CAPSULE_BYTES:
        text = encoded[:MAX_CAPSULE_BYTES].decode("utf-8", errors="ignore")
    return text
