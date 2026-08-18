from pathlib import Path

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.timeline import binding_timeline, mailbox_timeline, wake_timeline
from tools.codex_supervisor.wake_batches import WakeBatchStore


def test_mailbox_and_wake_timelines(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    message = seeded["mailbox"].enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="op:tl",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="s",
        payload_ref="p",
    )
    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    batch = WakeBatchStore(seeded["supervisor"], seeded["mailbox"]).prepare(
        binding_id=seeded["portfolio_binding_id"],
        thread_id="thr_port",
        snapshot=snapshot,
        messages=[message],
    )
    mail = mailbox_timeline(seeded["supervisor"])
    assert mail[0]["message_id"] == message.message_id
    wakes = wake_timeline(seeded["supervisor"], str(batch["wake_batch_id"]))
    assert wakes[0]["client_user_message_id"].startswith("hmasd-wake:")
    events = binding_timeline(seeded["supervisor"], seeded["portfolio_binding_id"])
    assert events
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
