"""Context precedence and non-authority rules.

Lower numeric rank is stronger. Compaction summaries and automatic memory
cannot create authority, epochs, promotions, or owner decisions.
"""

from __future__ import annotations

from .models import ContextSourceKind, PrecedenceLayer


AUTHORITY_LAYERS = frozenset(
    {
        PrecedenceLayer.P0_USER_AUTHORITY,
        PrecedenceLayer.P1_ROUTER_AND_ROLE,
        PrecedenceLayer.P2_STAGE_OR_PORTFOLIO_CONTRACT,
        PrecedenceLayer.P3_CANONICAL_OWNER_ARTIFACT,
    }
)
STATE_TRANSITION_LAYERS = AUTHORITY_LAYERS | {PrecedenceLayer.P4_PLAN_EPOCH}

_KIND_TO_LAYER = {
    ContextSourceKind.USER_AUTHORITY: PrecedenceLayer.P0_USER_AUTHORITY,
    ContextSourceKind.ROUTER: PrecedenceLayer.P1_ROUTER_AND_ROLE,
    ContextSourceKind.ROLE_CONTRACT: PrecedenceLayer.P1_ROUTER_AND_ROLE,
    ContextSourceKind.STAGE_OR_PORTFOLIO_CONTRACT: (
        PrecedenceLayer.P2_STAGE_OR_PORTFOLIO_CONTRACT
    ),
    ContextSourceKind.CANONICAL_OWNER_ARTIFACT: (
        PrecedenceLayer.P3_CANONICAL_OWNER_ARTIFACT
    ),
    ContextSourceKind.PLAN_EPOCH: PrecedenceLayer.P4_PLAN_EPOCH,
    ContextSourceKind.SEMANTIC_COMMIT: PrecedenceLayer.P5_SEMANTIC_COMMIT,
    ContextSourceKind.TYPED_PACKET: PrecedenceLayer.P6_TYPED_PACKET,
    ContextSourceKind.TYPED_REPORT: PrecedenceLayer.P6_TYPED_PACKET,
    ContextSourceKind.RAW_CONVERSATION: PrecedenceLayer.P7_RAW_CONTEXT,
    ContextSourceKind.TOOL_OUTPUT: PrecedenceLayer.P7_RAW_CONTEXT,
    ContextSourceKind.COMPACTION_SUMMARY: PrecedenceLayer.P8_COMPACTION_SUMMARY,
    ContextSourceKind.AUTOMATIC_MEMORY: PrecedenceLayer.P9_AUTOMATIC_MEMORY,
    ContextSourceKind.NAVIGATION: PrecedenceLayer.NAVIGATION,
    ContextSourceKind.PROCEDURE: PrecedenceLayer.PROCEDURE,
    ContextSourceKind.HISTORY: PrecedenceLayer.HISTORY,
}

AUTHORITY_OPERATIONS = frozenset(
    {
        "create_owner_decision",
        "create_portfolio_decision",
        "change_actor_state",
        "promote_canonical",
    }
)
MUTATION_OPERATIONS = frozenset(
    {
        "open_workflow",
        "register_task",
        "bind_task",
        "record_intake",
        "open_obligation",
        "open_epoch",
        "revise_epoch",
        "close_epoch",
        "resolve_obligation",
        "write_semantic_commit",
        "materialize_checkpoint",
        "ack_checkpoint",
        "register_packet",
        "ack_packet",
        "create_promotion_proposal",
        "create_owner_decision",
        "promote_canonical",
        "prepare_rollover",
        "confirm_rollover",
        "apply_rollover",
        "close_workflow",
        "change_actor_state",
        "create_portfolio_decision",
    }
)

PRECEDENCE_HEADER = (
    "CONTEXT PRECEDENCE\n"
    "user > router/role > stage/portfolio contract > owner canonical artifact\n"
    "> epoch > semantic commit > typed packet/report > raw context\n"
    "> compaction summary > automatic memory"
)


def precedence_for_kind(kind: ContextSourceKind | str) -> PrecedenceLayer:
    value = kind if isinstance(kind, ContextSourceKind) else ContextSourceKind(str(kind))
    return _KIND_TO_LAYER[value]


def can_create_authority(layer: PrecedenceLayer) -> bool:
    return layer in AUTHORITY_LAYERS


def can_create_state_transition(layer: PrecedenceLayer) -> bool:
    return layer in STATE_TRANSITION_LAYERS


def source_effects(source_kind: ContextSourceKind | str) -> dict[str, bool]:
    layer = precedence_for_kind(source_kind)
    return {
        "may_define_authority": can_create_authority(layer),
        "may_revise_epoch": layer is PrecedenceLayer.P4_PLAN_EPOCH
        or layer is PrecedenceLayer.P0_USER_AUTHORITY
        or layer is PrecedenceLayer.P3_CANONICAL_OWNER_ARTIFACT,
        "may_create_owner_decision": can_create_authority(layer),
        "may_serve_as_retrieval_hint": True,
        "layer": layer.name,
        "rank": layer.rank,
    }


def assert_authoritative_source(
    layer: PrecedenceLayer | ContextSourceKind | str,
    operation: str,
) -> None:
    """Reject memory/summary/raw sources before any state mutation."""
    if isinstance(layer, ContextSourceKind) or isinstance(layer, str):
        resolved = precedence_for_kind(layer)
    else:
        resolved = layer
    if operation in AUTHORITY_OPERATIONS and not can_create_authority(resolved):
        raise PermissionError(
            f"{resolved.name} cannot create authority for {operation}"
        )
    if operation in MUTATION_OPERATIONS and not can_create_state_transition(resolved):
        raise PermissionError(
            f"{resolved.name} cannot create a state transition for {operation}"
        )
