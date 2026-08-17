"""Actor identity models for the repository-local semantic overlay.

Actor kind is explicit or comes from the reviewed session-root mapping.
A session ID alone never identifies EM or CM.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActorKind(str, Enum):
    PORTFOLIO = "PORTFOLIO"
    OPERATIONAL_ROOT = "OPERATIONAL_ROOT"
    EM = "EM"
    CM = "CM"
    LEAF = "LEAF"
    SESSION_ROOT_UNCLASSIFIED = "SESSION_ROOT_UNCLASSIFIED"


class ActorState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CLOSED = "CLOSED"


class SemanticCommitKind(str, Enum):
    PORTFOLIO_FRONTIER = "PORTFOLIO_FRONTIER"
    ROOT_COORDINATION_FRONTIER = "ROOT_COORDINATION_FRONTIER"
    EM_DIRECTION_FRONTIER = "EM_DIRECTION_FRONTIER"
    CM_TECHNICAL_FRONTIER = "CM_TECHNICAL_FRONTIER"
    LEAF_ASSIGNMENT_FRONTIER = "LEAF_ASSIGNMENT_FRONTIER"


class EpochKind(str, Enum):
    PORTFOLIO_INQUIRY = "PORTFOLIO_INQUIRY"
    OPERATIONAL_COORDINATION = "OPERATIONAL_COORDINATION"
    DIRECTION_STAGE = "DIRECTION_STAGE"
    TECHNICAL_CLOSURE = "TECHNICAL_CLOSURE"
    ASSIGNMENT = "ASSIGNMENT"


ACTOR_EPOCH_KINDS: dict[ActorKind, EpochKind] = {
    ActorKind.PORTFOLIO: EpochKind.PORTFOLIO_INQUIRY,
    ActorKind.OPERATIONAL_ROOT: EpochKind.OPERATIONAL_COORDINATION,
    ActorKind.EM: EpochKind.DIRECTION_STAGE,
    ActorKind.CM: EpochKind.TECHNICAL_CLOSURE,
    ActorKind.LEAF: EpochKind.ASSIGNMENT,
}

ACTOR_COMMIT_KINDS: dict[ActorKind, SemanticCommitKind] = {
    ActorKind.PORTFOLIO: SemanticCommitKind.PORTFOLIO_FRONTIER,
    ActorKind.OPERATIONAL_ROOT: SemanticCommitKind.ROOT_COORDINATION_FRONTIER,
    ActorKind.EM: SemanticCommitKind.EM_DIRECTION_FRONTIER,
    ActorKind.CM: SemanticCommitKind.CM_TECHNICAL_FRONTIER,
    ActorKind.LEAF: SemanticCommitKind.LEAF_ASSIGNMENT_FRONTIER,
}


@dataclass(frozen=True)
class ActorContext:
    actor_context_id: str
    session_id: str
    actor_kind: ActorKind
    scope_key: str
    identity_source: str
    state: ActorState
    agent_id: str | None = None
    canonical_path: str | None = None
    direction_id: str | None = None
    parent_actor_context_id: str | None = None
    counterpart_actor_context_id: str | None = None
    created_at: str = ""
    updated_at: str = ""


def actor_context_from_row(row: object) -> ActorContext:
    mapping = dict(row) if not isinstance(row, dict) else row
    return ActorContext(
        actor_context_id=str(mapping["actor_context_id"]),
        session_id=str(mapping["session_id"]),
        actor_kind=ActorKind(str(mapping["actor_kind"])),
        scope_key=str(mapping["scope_key"]),
        identity_source=str(mapping["identity_source"]),
        state=ActorState(str(mapping["state"])),
        agent_id=str(mapping["agent_id"]) if mapping.get("agent_id") else None,
        canonical_path=str(mapping["canonical_path"]) if mapping.get("canonical_path") else None,
        direction_id=str(mapping["direction_id"]) if mapping.get("direction_id") else None,
        parent_actor_context_id=(
            str(mapping["parent_actor_context_id"])
            if mapping.get("parent_actor_context_id")
            else None
        ),
        counterpart_actor_context_id=(
            str(mapping["counterpart_actor_context_id"])
            if mapping.get("counterpart_actor_context_id")
            else None
        ),
        created_at=str(mapping.get("created_at") or ""),
        updated_at=str(mapping.get("updated_at") or ""),
    )
