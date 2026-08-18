from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.mailbox_acl import MailboxAclError, evaluate_automatic_delivery
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.scheduler_leases import LeaseError, SchedulerLeases


def test_one_thousand_message_dedupe(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    ids = []
    for index in range(1000):
        message = mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key=f"op:load:{index % 50}",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref=f"s{index}",
            payload_ref="FAILED.md" if index == 0 else f"ref{index}",
        )
        ids.append(message.message_id)
    assert len(set(ids)) == 50
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_two_scheduler_instances_and_acl_matrix(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    leases = SchedulerLeases(seeded["supervisor"])
    leases.acquire(seeded["root_binding_id"], "a")
    with pytest.raises(LeaseError):
        leases.acquire(seeded["root_binding_id"], "b")
    forbidden = [
        ("EM", "CM", MailboxMessageKind.PACKET_AVAILABLE),
        ("PORTFOLIO", "PORTFOLIO", MailboxMessageKind.PORTFOLIO_TO_ROOT_DECISION),
        ("OPERATIONAL_ROOT", "OPERATIONAL_ROOT", MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW),
        ("PORTFOLIO", "OPERATIONAL_ROOT", MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW),
    ]
    for sender, target, kind in forbidden:
        with pytest.raises(MailboxAclError):
            evaluate_automatic_delivery(
                source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
                sender_kind=sender,
                sender_actor_context_id="s",
                target_kind=target,
                target_actor_context_id="t" if sender != target else "s",
                target_binding_state="ACTIVE",
                message_kind=kind,
            )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
