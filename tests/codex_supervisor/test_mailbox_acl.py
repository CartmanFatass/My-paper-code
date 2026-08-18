import pytest

from tools.codex_supervisor.mailbox_acl import MailboxAclError, evaluate_automatic_delivery
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem


def test_root_portfolio_matrix_and_rejections() -> None:
    evaluate_automatic_delivery(
        source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
        sender_kind="OPERATIONAL_ROOT",
        sender_actor_context_id="root",
        target_kind="PORTFOLIO",
        target_actor_context_id="port",
        target_binding_state="ACTIVE",
        message_kind=MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW,
    )
    evaluate_automatic_delivery(
        source_system=MailboxSourceSystem.SEMANTIC_LEDGER.value,
        sender_kind=None,
        sender_actor_context_id=None,
        target_kind="OPERATIONAL_ROOT",
        target_actor_context_id="root",
        target_binding_state="ACTIVE",
        message_kind=MailboxMessageKind.REANCHOR_REQUIRED,
    )
    evaluate_automatic_delivery(
        source_system=MailboxSourceSystem.OPERATOR.value,
        sender_kind=None,
        sender_actor_context_id=None,
        target_kind="PORTFOLIO",
        target_actor_context_id="port",
        target_binding_state="ACTIVE",
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
    )
    with pytest.raises(MailboxAclError, match="self-send"):
        evaluate_automatic_delivery(
            source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
            sender_kind="OPERATIONAL_ROOT",
            sender_actor_context_id="root",
            target_kind="OPERATIONAL_ROOT",
            target_actor_context_id="root",
            target_binding_state="ACTIVE",
            message_kind=MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW,
        )
    with pytest.raises(MailboxAclError, match="embedded"):
        evaluate_automatic_delivery(
            source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
            sender_kind="EM",
            sender_actor_context_id="em",
            target_kind="CM",
            target_actor_context_id="cm",
            target_binding_state="ACTIVE",
            message_kind=MailboxMessageKind.PACKET_AVAILABLE,
        )
    with pytest.raises(MailboxAclError, match="unknown sender"):
        evaluate_automatic_delivery(
            source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
            sender_kind=None,
            sender_actor_context_id=None,
            target_kind="PORTFOLIO",
            target_actor_context_id="port",
            target_binding_state="ACTIVE",
            message_kind=MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW,
        )
    with pytest.raises(MailboxAclError, match="outside"):
        evaluate_automatic_delivery(
            source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
            sender_kind="PORTFOLIO",
            sender_actor_context_id="port",
            target_kind="OPERATIONAL_ROOT",
            target_actor_context_id="root",
            target_binding_state="ACTIVE",
            message_kind=MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW,
        )
    with pytest.raises(MailboxAclError, match="not ACTIVE"):
        evaluate_automatic_delivery(
            source_system=MailboxSourceSystem.OPERATOR.value,
            sender_kind=None,
            sender_actor_context_id=None,
            target_kind="PORTFOLIO",
            target_actor_context_id="port",
            target_binding_state="SUSPENDED",
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        )
