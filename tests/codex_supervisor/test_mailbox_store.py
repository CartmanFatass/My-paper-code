from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.mailbox_models import (
    MAX_MAILBOX_REF_BYTES,
    DeliveryState,
    IntakeState,
    MailboxMessageKind,
    MailboxSourceSystem,
)
from tools.codex_supervisor.mailbox_store import MailboxStoreError


def test_enqueue_idempotent_and_transitions(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    first = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:1",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subj",
        payload_ref="ref",
        priority=3,
    )
    second = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:1",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subj",
        payload_ref="ref",
    )
    assert first.message_id == second.message_id
    with pytest.raises(MailboxStoreError, match="conflicts"):
        mailbox.enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key="op:attn:1",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref="other",
            payload_ref="other",
        )
    eligible = mailbox.mark_eligible(first.message_id)
    assert eligible.delivery_state is DeliveryState.ELIGIBLE
    batched = mailbox.mark_batched(first.message_id)
    assert batched.delivery_state is DeliveryState.BATCHED
    with pytest.raises(MailboxStoreError, match="delivered"):
        mailbox.acknowledge(first.message_id)
    delivered = mailbox.mark_delivered(first.message_id)
    assert delivered.delivery_state is DeliveryState.DELIVERED_TO_TURN
    acked = mailbox.acknowledge(first.message_id)
    assert acked.intake_state is IntakeState.ACKNOWLEDGED
    intaken = mailbox.intake(first.message_id)
    assert intaken.intake_state is IntakeState.INTAKEN
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_dead_letter_and_select_eligible(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:attn:2",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subj",
        payload_ref="ref",
        priority=9,
    )
    selected = mailbox.select_eligible(
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        target_kind="PORTFOLIO",
        target_binding_state="ACTIVE",
        sender_kind_for={},
    )
    assert selected[0].message_id == message.message_id
    assert selected[0].delivery_state is DeliveryState.ELIGIBLE
    mailbox.dead_letter(message.message_id, "revoked target")
    assert mailbox.get(message.message_id).delivery_state is DeliveryState.DEAD_LETTER
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize(
    ("subject_ref", "payload_ref"),
    [
        (
            "operator_attention-20260823",
            "docs/research/workflow-runs/2026-08-22_app-server-live-runtime/STAGE2_BASELINE.md",
        ),
        ("pkt_0123456789abcdef", "obl_abcdef0123456789"),
        ("checkpoint_0123456789abcdef", r"docs\project\CODEX_SUPERVISOR_LIVE_PROFILES.md"),
    ],
)
def test_enqueue_accepts_closed_reference_families(
    tmp_path: Path,
    subject_ref: str,
    payload_ref: str,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    message = seeded["mailbox"].enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=f"op:valid:{subject_ref}",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref=subject_ref,
        payload_ref=payload_ref,
    )
    assert message.subject_ref == subject_ref
    assert message.payload_ref == payload_ref
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize(
    "invalid_ref",
    [
        "",
        " outer",
        "outer ",
        "two words",
        "line\nbreak",
        "tab\tbreak",
        "nul\0break",
        "control\x1fbreak",
        "delete\x7fbreak",
        "https://example.invalid/artifact",
        "urn:packet:123",
        "/absolute/path.md",
        r"C:\absolute\path.md",
        r"C:drive-relative.md",
        r"\rooted-current-drive.md",
        r"\\server\share\packet.md",
        "../secret.md",
        "docs/../secret.md",
        "docs//artifact.md",
        "a" * (MAX_MAILBOX_REF_BYTES + 1),
    ],
)
@pytest.mark.parametrize("field_name", ["subject_ref", "payload_ref"])
def test_invalid_reference_never_persists(
    tmp_path: Path,
    field_name: str,
    invalid_ref: str,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    refs = {"subject_ref": "safe-subject", "payload_ref": "docs/safe.md"}
    refs[field_name] = invalid_ref
    with pytest.raises(MailboxStoreError, match=field_name):
        seeded["mailbox"].enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key=f"op:invalid:{field_name}",
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref=refs["subject_ref"],
            payload_ref=refs["payload_ref"],
        )
    assert seeded["mailbox"].list_messages() == []
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
