from pathlib import Path

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem, WAKE_ENVELOPE_HEADER
from tools.codex_supervisor.wake_batches import WakeBatchStore, build_wake_text


def test_wake_envelope_is_neutral_and_ordered(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    mailbox = seeded["mailbox"]
    late = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:2",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="late",
        payload_ref="ref-late",
        priority=1,
    )
    early = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:1",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="early",
        payload_ref="ref-early",
        priority=9,
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    batch = batches.prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[late, early],
    )
    text = str(batch["input_text"])
    assert WAKE_ENVELOPE_HEADER in text
    assert "new_user_authority=false" in text
    assert text.index(early.message_id) < text.index(late.message_id)
    assert "BLOCKED" not in text
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
    assert "wake_batch_id=" in build_wake_text(snapshot, wake_batch_id="wake_x", messages=[early])
