"""Typed responsibility projections carried by the existing obligation ledger.

The projection is deliberately data-only: it gives a fresh workflow-state read
the queue, receiver, next event, boundary, continuity and evidence that prose
or chat history previously supplied.  It neither observes processes nor
interprets scientific payloads.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Mapping


RESPONSIBILITY_SCHEMA = "HMASD_RESPONSIBILITY_PROJECTION_V1"


class ResponsibilityStage(str, Enum):
    CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE = "CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE"
    SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION = "SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION"
    OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE = "OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE"
    CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION = "CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION"
    PRESTART_TIME_GATE_TO_SCHEDULED_CONTINUATION = "PRESTART_TIME_GATE_TO_SCHEDULED_CONTINUATION"
    RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT = "RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT"
    TECHNICAL_FAILURE_TO_ENGINEERING_REPAIR = "TECHNICAL_FAILURE_TO_ENGINEERING_REPAIR"
    SCIENCE_NEGATIVE_TO_SCIENTIFIC_NO_CURRENT = "SCIENCE_NEGATIVE_TO_SCIENTIFIC_NO_CURRENT"
    MATERIAL_RESULT_WITHOUT_OWNER_TO_ORPHAN_RECOVERY = "MATERIAL_RESULT_WITHOUT_OWNER_TO_ORPHAN_RECOVERY"
    LOCAL_BOUNDARY_RETURN_TO_CONTINUATION = "LOCAL_BOUNDARY_RETURN_TO_CONTINUATION"


class PrimaryQueue(str, Enum):
    ACTIVE_SCIENCE = "ACTIVE_SCIENCE"
    SCIENCE_INTAKE = "SCIENCE_INTAKE"
    PORTFOLIO_DECISION = "PORTFOLIO_DECISION"
    EXPERIMENT_TERMINAL = "EXPERIMENT_TERMINAL"
    SCHEDULED_CONTINUATION = "SCHEDULED_CONTINUATION"
    RESOURCE_OR_SUBSTRATE_WAIT = "RESOURCE_OR_SUBSTRATE_WAIT"
    ENGINEERING_REPAIR = "ENGINEERING_REPAIR"
    SCIENTIFIC_NO_CURRENT = "SCIENTIFIC_NO_CURRENT"
    ORPHAN_RECOVERY = "ORPHAN_RECOVERY"


class BoundaryDomain(str, Enum):
    SCIENCE_DISPOSITION = "SCIENCE_DISPOSITION"
    EXPERIMENT_TRANSACTION = "EXPERIMENT_TRANSACTION"
    ENGINEERING_BOUNDARY = "ENGINEERING_BOUNDARY"
    RESOURCE_OR_LEASE_BOUNDARY = "RESOURCE_OR_LEASE_BOUNDARY"
    CONTROL_PLANE_ANOMALY = "CONTROL_PLANE_ANOMALY"
    EXTERNAL_REVIEW_BOUNDARY = "EXTERNAL_REVIEW_BOUNDARY"


class ContinuityState(str, Enum):
    CURRENT_WORK = "CURRENT_WORK"
    DORMANT_SCHEDULED_CONTINUATION = "DORMANT_SCHEDULED_CONTINUATION"
    IDLE_COMPLETE = "IDLE_COMPLETE"
    UNOWNED_STALL = "UNOWNED_STALL"


class ProviderTransactionLifecycle(str, Enum):
    SEND_NOT_COMMITTED = "SEND_NOT_COMMITTED"
    COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN = "COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN"
    COMMITTED_TERMINAL_NO_RESPONSE_PROVED = "COMMITTED_TERMINAL_NO_RESPONSE_PROVED"
    COMPLETE_RESPONSE_PRESENT = "COMPLETE_RESPONSE_PRESENT"


class DirectionQueueAuthority(str, Enum):
    SAME_DIRECTION_EM = "SAME_DIRECTION_EM"
    PORTFOLIO = "PORTFOLIO"


CUSTODY_HANDOFF_STAGES = frozenset(
    {
        ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE,
        ResponsibilityStage.OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE,
        ResponsibilityStage.CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION,
        ResponsibilityStage.SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION,
    }
)

_PROVIDER_LIFECYCLE_TRANSITIONS = {
    ProviderTransactionLifecycle.SEND_NOT_COMMITTED: frozenset(
        {
            ProviderTransactionLifecycle.SEND_NOT_COMMITTED,
            ProviderTransactionLifecycle.COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN,
        }
    ),
    ProviderTransactionLifecycle.COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN: frozenset(
        {
            ProviderTransactionLifecycle.COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN,
            ProviderTransactionLifecycle.COMMITTED_TERMINAL_NO_RESPONSE_PROVED,
            ProviderTransactionLifecycle.COMPLETE_RESPONSE_PRESENT,
        }
    ),
    ProviderTransactionLifecycle.COMMITTED_TERMINAL_NO_RESPONSE_PROVED: frozenset(
        {ProviderTransactionLifecycle.COMMITTED_TERMINAL_NO_RESPONSE_PROVED}
    ),
    ProviderTransactionLifecycle.COMPLETE_RESPONSE_PRESENT: frozenset(
        {ProviderTransactionLifecycle.COMPLETE_RESPONSE_PRESENT}
    ),
}


_STAGE_CONTRACTS: dict[ResponsibilityStage, tuple[PrimaryQueue, BoundaryDomain, ContinuityState]] = {
    ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE: (PrimaryQueue.SCIENCE_INTAKE, BoundaryDomain.ENGINEERING_BOUNDARY, ContinuityState.CURRENT_WORK),
    ResponsibilityStage.SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION: (PrimaryQueue.PORTFOLIO_DECISION, BoundaryDomain.SCIENCE_DISPOSITION, ContinuityState.CURRENT_WORK),
    ResponsibilityStage.OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE: (PrimaryQueue.EXPERIMENT_TERMINAL, BoundaryDomain.EXPERIMENT_TRANSACTION, ContinuityState.CURRENT_WORK),
    ResponsibilityStage.CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION: (PrimaryQueue.SCIENCE_INTAKE, BoundaryDomain.ENGINEERING_BOUNDARY, ContinuityState.CURRENT_WORK),
    ResponsibilityStage.PRESTART_TIME_GATE_TO_SCHEDULED_CONTINUATION: (PrimaryQueue.SCHEDULED_CONTINUATION, BoundaryDomain.RESOURCE_OR_LEASE_BOUNDARY, ContinuityState.DORMANT_SCHEDULED_CONTINUATION),
    ResponsibilityStage.RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT: (PrimaryQueue.RESOURCE_OR_SUBSTRATE_WAIT, BoundaryDomain.RESOURCE_OR_LEASE_BOUNDARY, ContinuityState.IDLE_COMPLETE),
    ResponsibilityStage.TECHNICAL_FAILURE_TO_ENGINEERING_REPAIR: (PrimaryQueue.ENGINEERING_REPAIR, BoundaryDomain.ENGINEERING_BOUNDARY, ContinuityState.CURRENT_WORK),
    ResponsibilityStage.SCIENCE_NEGATIVE_TO_SCIENTIFIC_NO_CURRENT: (PrimaryQueue.SCIENTIFIC_NO_CURRENT, BoundaryDomain.SCIENCE_DISPOSITION, ContinuityState.IDLE_COMPLETE),
    ResponsibilityStage.MATERIAL_RESULT_WITHOUT_OWNER_TO_ORPHAN_RECOVERY: (PrimaryQueue.ORPHAN_RECOVERY, BoundaryDomain.CONTROL_PLANE_ANOMALY, ContinuityState.UNOWNED_STALL),
    ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION: (PrimaryQueue.ACTIVE_SCIENCE, BoundaryDomain.CONTROL_PLANE_ANOMALY, ContinuityState.CURRENT_WORK),
}
_INVALID_STANDALONE_STATUS = {"blocked", "failed", "pending", "no-current"}
_MANDATORY_SUCCESSORS: dict[ResponsibilityStage, ResponsibilityStage] = {
    ResponsibilityStage.OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE:
        ResponsibilityStage.CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION,
    ResponsibilityStage.CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION:
        ResponsibilityStage.SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION,
    ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE:
        ResponsibilityStage.SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION,
}


def _text(name: str, value: Any, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _stage(value: ResponsibilityStage | str) -> ResponsibilityStage:
    try:
        return ResponsibilityStage(value)
    except ValueError as exc:
        raise ValueError(f"unknown responsibility stage: {value}") from exc


def _boundary(value: BoundaryDomain | str) -> BoundaryDomain:
    try:
        return BoundaryDomain(value)
    except ValueError as exc:
        raise ValueError(f"unknown boundary domain: {value}") from exc


def classify_provider_transaction(
    *,
    send_commit_proved: bool | None,
    remote_active_or_response_unknown: bool = False,
    terminal_no_response_proved: bool = False,
    complete_response_present: bool = False,
    local_archive_present: bool | None = None,
) -> dict[str, object]:
    """Classify provider delivery from positive evidence, never archive absence.

    ``local_archive_present`` is intentionally not evidence of remote delivery,
    absence, or success.  Unknown commit state is conservative and forbids a
    duplicate send until reconnect/observation resolves it.
    """
    if send_commit_proved is False and (
        remote_active_or_response_unknown or terminal_no_response_proved or complete_response_present
    ):
        raise ValueError("contradictory provider lifecycle evidence")
    if terminal_no_response_proved and (
        send_commit_proved is not True or remote_active_or_response_unknown or complete_response_present
    ):
        raise ValueError("contradictory provider lifecycle evidence")
    if complete_response_present and remote_active_or_response_unknown:
        raise ValueError("contradictory provider lifecycle evidence")
    if complete_response_present:
        lifecycle = ProviderTransactionLifecycle.COMPLETE_RESPONSE_PRESENT
        return {"lifecycle": lifecycle.value, "action": "ARCHIVE_NO_RESEND", "duplicate_send_forbidden": True}
    if terminal_no_response_proved:
        lifecycle = ProviderTransactionLifecycle.COMMITTED_TERMINAL_NO_RESPONSE_PROVED
        return {"lifecycle": lifecycle.value, "action": "ONE_IDENTICAL_PROVENANCE_LINKED_RECOVERY_RESEND_ALLOWED", "duplicate_send_forbidden": True}
    if remote_active_or_response_unknown or send_commit_proved is True:
        lifecycle = ProviderTransactionLifecycle.COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN
        return {"lifecycle": lifecycle.value, "action": "RECONNECT_OR_OBSERVE_NO_DUPLICATE_SEND", "duplicate_send_forbidden": True}
    if send_commit_proved is False:
        lifecycle = ProviderTransactionLifecycle.SEND_NOT_COMMITTED
        return {"lifecycle": lifecycle.value, "action": "EXACT_RETRY_ALLOWED", "duplicate_send_forbidden": False}
    # A missing local archive is deliberately ignored here; it cannot prove a
    # remote absence or successful send, so unknown remains conservative.
    return {
        "lifecycle": ProviderTransactionLifecycle.COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN.value,
        "action": "RECONNECT_OR_OBSERVE_NO_DUPLICATE_SEND",
        "duplicate_send_forbidden": True,
        "local_archive_evidence": "PRESENT" if local_archive_present else "ABSENT_OR_UNKNOWN_NONPROBATIVE",
    }


def validate_provider_lifecycle_transition(
    previous: ProviderTransactionLifecycle | str,
    next_lifecycle: ProviderTransactionLifecycle | str,
) -> None:
    """Reject provider lifecycle regression or reopening for one transaction."""

    try:
        prior = ProviderTransactionLifecycle(previous)
        following = ProviderTransactionLifecycle(next_lifecycle)
    except ValueError as exc:
        raise ValueError("unknown provider transaction lifecycle") from exc
    if following not in _PROVIDER_LIFECYCLE_TRANSITIONS[prior]:
        raise ValueError(
            f"provider lifecycle cannot transition from {prior.value} to {following.value}"
        )


def build_responsibility(*, stage: ResponsibilityStage | str, receiving_owner: str | None,
                         next_event: str, evidence_ref: str, disposition_reason: str,
                         active_worker: str | None = None, continuity_owner: str | None = None,
                         continuation_owner: str | None = None, affected_scope: str | None = None,
                         affected_actions: tuple[str, ...] | list[str] = (),
                         unaffected_scopes: tuple[str, ...] | list[str] = (),
                         direction_primary_queue: str | None = None,
                         prior_direction_primary_queue: str | None = None,
                         queue_authority_artifact: str | None = None,
                         queue_authority_owner: DirectionQueueAuthority | str | None = None,
                         boundary_domain: BoundaryDomain | str | None = None,
                         revisit_condition: str | None = None, current_work: bool = False) -> dict[str, Any]:
    """Build and validate one typed obligation/disposition projection."""
    stage_value = _stage(stage)
    queue, default_boundary, continuity = _STAGE_CONTRACTS[stage_value]
    boundary = _boundary(boundary_domain) if boundary_domain is not None else default_boundary
    is_orphan = stage_value == ResponsibilityStage.MATERIAL_RESULT_WITHOUT_OWNER_TO_ORPHAN_RECOVERY
    owner = _text("receiving_owner", receiving_owner, allow_none=is_orphan)
    next_event_value = _text("next_event", next_event)
    evidence = _text("evidence_ref", evidence_ref)
    reason = _text("disposition_reason", disposition_reason)
    if reason.lower() in _INVALID_STANDALONE_STATUS or re.fullmatch(r"[A-Z0-9_]+(?:\|[A-Z0-9_]+)+", reason):
        raise ValueError("disposition_reason cannot be a standalone status or cut tuple")
    worker = _text("active_worker", active_worker, allow_none=True)
    legacy_continuity_owner = _text("continuity_owner", continuity_owner, allow_none=True)
    named_continuation_owner = _text("continuation_owner", continuation_owner, allow_none=True)
    if legacy_continuity_owner and named_continuation_owner and legacy_continuity_owner != named_continuation_owner:
        raise ValueError("continuity_owner and continuation_owner conflict")
    continuation = named_continuation_owner or legacy_continuity_owner
    scope = _text("affected_scope", affected_scope, allow_none=True)
    if stage_value == ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION and scope is None:
        raise ValueError("local boundary return requires an affected_scope")
    scope = scope or "WORKFLOW_SCOPE"
    if not isinstance(affected_actions, (tuple, list)) or any(
        not isinstance(item, str) or not item.strip() for item in affected_actions
    ):
        raise ValueError("affected_actions must be exact non-empty action strings")
    actions = tuple(item.strip() for item in affected_actions)
    if not isinstance(unaffected_scopes, (tuple, list)) or any(not isinstance(item, str) or not item.strip() for item in unaffected_scopes):
        raise ValueError("unaffected_scopes must be exact non-empty scope strings")
    unaffected = tuple(item.strip() for item in unaffected_scopes)
    if scope in unaffected or len(set(unaffected)) != len(unaffected):
        raise ValueError("unaffected_scopes must be distinct and exclude affected_scope")
    if stage_value == ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION:
        if not actions or not unaffected:
            raise ValueError("local boundary return requires affected_actions and unaffected_scopes")
    prior_queue = _text("prior_direction_primary_queue", prior_direction_primary_queue, allow_none=True)
    direction_queue = _text("direction_primary_queue", direction_primary_queue, allow_none=True) or (prior_queue or queue.value)
    authority = _text("queue_authority_artifact", queue_authority_artifact, allow_none=True)
    authority_owner_value = _text("queue_authority_owner", queue_authority_owner, allow_none=True)
    if stage_value == ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION and prior_queue is None:
        raise ValueError("local boundary return requires the prior direction primary queue")
    queue_changed = prior_queue is not None and direction_queue != prior_queue
    if queue_changed:
        if authority is None:
            raise ValueError("direction primary queue change requires an exact EM/Portfolio authority artifact")
        try:
            authority_owner_value = DirectionQueueAuthority(str(authority_owner_value)).value
        except ValueError as exc:
            raise ValueError("direction primary queue change requires an exact EM/Portfolio authority owner") from exc
    elif authority is not None or authority_owner_value is not None:
        raise ValueError("queue authority fields are valid only for a direction primary queue change")
    revisit = _text("revisit_condition", revisit_condition, allow_none=True)
    if (is_orphan and owner is not None) or (stage_value == ResponsibilityStage.RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT and current_work):
        continuity = ContinuityState.CURRENT_WORK
    if continuity == ContinuityState.DORMANT_SCHEDULED_CONTINUATION:
        if worker is not None or continuation is None:
            raise ValueError("scheduled continuation requires zero active workers and one continuity owner")
    elif continuity == ContinuityState.CURRENT_WORK:
        if owner is None or worker is None:
            raise ValueError("current work requires an exact receiving owner and active worker")
        continuation = continuation or owner
    elif continuity == ContinuityState.IDLE_COMPLETE:
        if worker is not None or revisit is None:
            raise ValueError("idle complete responsibility requires zero workers and a revisit condition")
        continuation = None
    elif continuity == ContinuityState.UNOWNED_STALL:
        if owner is not None or worker is not None or continuation is not None:
            raise ValueError("unowned stall must not pretend to have an owner or worker")
    return {"schema": RESPONSIBILITY_SCHEMA, "stage": stage_value.value,
            "primary_queue": queue.value, "receiving_owner": owner,
            "next_event": next_event_value, "boundary_domain": boundary.value,
            "continuity_state": continuity.value, "active_worker": worker,
            "continuity_owner": continuation, "continuation_owner": continuation,
            "affected_scope": scope, "affected_actions": actions,
            "unaffected_scopes": unaffected,
            "direction_primary_queue": direction_queue,
            "prior_direction_primary_queue": prior_queue,
            "queue_authority_artifact": authority,
            "queue_authority_owner": authority_owner_value, "evidence_ref": evidence,
            "disposition_reason": reason, "revisit_condition": revisit,
            "requires_recovery_owner": continuity == ContinuityState.UNOWNED_STALL}


def responsibility_from_reason(reason: str) -> dict[str, Any] | None:
    """Return a validated projection only when this obligation stores one."""
    import json
    try:
        value = json.loads(reason)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(value, Mapping) or value.get("schema") != RESPONSIBILITY_SCHEMA:
        return None
    return build_responsibility(stage=value.get("stage"), receiving_owner=value.get("receiving_owner"),
        next_event=value.get("next_event"), evidence_ref=value.get("evidence_ref"),
        disposition_reason=value.get("disposition_reason"), active_worker=value.get("active_worker"),
        continuation_owner=value.get("continuation_owner") or value.get("continuity_owner"),
        affected_scope=value.get("affected_scope"), affected_actions=value.get("affected_actions") or (),
        unaffected_scopes=value.get("unaffected_scopes") or (),
        direction_primary_queue=value.get("direction_primary_queue"),
        prior_direction_primary_queue=value.get("prior_direction_primary_queue"),
        queue_authority_artifact=value.get("queue_authority_artifact"),
        queue_authority_owner=value.get("queue_authority_owner"),
        boundary_domain=value.get("boundary_domain"), revisit_condition=value.get("revisit_condition"),
        current_work=value.get("continuity_state") == ContinuityState.CURRENT_WORK.value)


def validate_handoff_successor(
    current_stage: ResponsibilityStage | str,
    successor_stage: ResponsibilityStage | str | None,
    *,
    portfolio_accepted: bool,
) -> None:
    """Reject a stage acceptance that would drop a mandatory receiver handoff."""
    current = _stage(current_stage)
    required = _MANDATORY_SUCCESSORS.get(current)
    if required is not None:
        if successor_stage is None:
            raise ValueError(f"{current.value} requires successor {required.value}")
        if _stage(successor_stage) != required:
            raise ValueError(f"{current.value} requires successor {required.value}")
        if portfolio_accepted:
            raise ValueError("portfolio acceptance applies only to the final Portfolio decision")
        return
    if current == ResponsibilityStage.SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION:
        if successor_stage is None and not portfolio_accepted:
            raise ValueError("final Portfolio decision requires explicit portfolio_accepted=true")
        if successor_stage is not None and portfolio_accepted:
            raise ValueError("Portfolio acceptance cannot also open a successor handoff")
        return
    if portfolio_accepted:
        raise ValueError("portfolio acceptance applies only to the final Portfolio decision")


def responsibility_blocks_stop(projection: Mapping[str, Any]) -> bool:
    return projection.get("continuity_state") == ContinuityState.CURRENT_WORK.value
