"""Root↔Portfolio automatic-delivery ACL. No peer mesh."""

from __future__ import annotations

from .mailbox_models import MailboxMessageKind, MailboxSourceSystem
from .managed_models import BindingState, ManagedActorKind


class MailboxAclError(ValueError):
    """Raised when a mailbox send is not automatically deliverable."""


AUTOMATIC_ACTOR_PAIRS: frozenset[tuple[str, str, str]] = frozenset(
    {
        (
            ManagedActorKind.OPERATIONAL_ROOT.value,
            ManagedActorKind.PORTFOLIO.value,
            MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW.value,
        ),
        (
            ManagedActorKind.PORTFOLIO.value,
            ManagedActorKind.OPERATIONAL_ROOT.value,
            MailboxMessageKind.PORTFOLIO_TO_ROOT_DECISION.value,
        ),
        (
            ManagedActorKind.OPERATIONAL_ROOT.value,
            ManagedActorKind.PORTFOLIO.value,
            MailboxMessageKind.ROOT_TO_PORTFOLIO_APPLIED_ACK.value,
        ),
    }
)

LEDGER_KINDS = frozenset(
    {
        MailboxMessageKind.OBLIGATION_AVAILABLE,
        MailboxMessageKind.PACKET_AVAILABLE,
        MailboxMessageKind.REPORT_AVAILABLE,
        MailboxMessageKind.REANCHOR_REQUIRED,
    }
)

EMBEDDED_KINDS = frozenset({"EM", "CM", "LEAF"})


def allow_self_send(message_kind: MailboxMessageKind) -> bool:
    return False


def evaluate_automatic_delivery(
    *,
    source_system: str,
    sender_kind: str | None,
    sender_actor_context_id: str | None,
    target_kind: str | None,
    target_actor_context_id: str,
    target_binding_state: str | None,
    message_kind: MailboxMessageKind,
) -> None:
    if message_kind.value in {"BLOCKED", "FAILED", "SUCCESS", "RETIRED", "PAUSED", "PARKED", "RELEASED"}:
        raise MailboxAclError("forbidden mailbox kind")
    if sender_kind in EMBEDDED_KINDS or target_kind in EMBEDDED_KINDS:
        raise MailboxAclError("embedded actors are not automatically delivered")
    if target_kind is None:
        raise MailboxAclError("unknown target")
    if target_kind not in {ManagedActorKind.OPERATIONAL_ROOT.value, ManagedActorKind.PORTFOLIO.value}:
        raise MailboxAclError("target is not a managed actor kind")
    if target_binding_state != BindingState.ACTIVE.value:
        raise MailboxAclError("target binding is not ACTIVE")
    if (
        sender_actor_context_id
        and sender_actor_context_id == target_actor_context_id
        and not allow_self_send(message_kind)
    ):
        raise MailboxAclError("self-send is not allowed")
    if source_system == MailboxSourceSystem.SEMANTIC_LEDGER.value:
        if message_kind in LEDGER_KINDS:
            return
        raise MailboxAclError("semantic ledger kind is not automatically deliverable")
    if source_system == MailboxSourceSystem.OPERATOR.value:
        if message_kind is MailboxMessageKind.OPERATOR_ATTENTION_REQUEST:
            return
        raise MailboxAclError("operator may only send OPERATOR_ATTENTION_REQUEST")
    if source_system == MailboxSourceSystem.MANAGED_ACTOR.value:
        if sender_kind is None:
            raise MailboxAclError("unknown sender")
        pair = (sender_kind, target_kind, message_kind.value)
        if pair not in AUTOMATIC_ACTOR_PAIRS:
            raise MailboxAclError("actor pair is outside the Root↔Portfolio ACL")
        return
    raise MailboxAclError(f"unknown source system: {source_system}")
