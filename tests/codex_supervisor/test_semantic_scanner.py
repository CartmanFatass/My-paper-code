from pathlib import Path

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_reanchor
from tools.codex_semantic_mvp.models import ObligationKind
from tools.codex_semantic_mvp.packet_refs import packet_register
from tools.codex_supervisor.mailbox_models import MailboxMessageKind
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.wake_batches import build_wake_text


def test_scanner_maps_obligations_and_packets_without_mutating_semantic(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    checkpoint = seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    packet_register(
        seeded["semantic"],
        packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
        source_actor_context_id=seeded["root"].actor_context_id,
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        payload_ref="docs/canary.md",
        marker="marker-scan-1",
        direction_id="demo",
    )
    before = seeded["semantic"].connection.execute("SELECT COUNT(*) FROM obligations").fetchone()[0]
    scanner = SemanticScanner(seeded["mailbox"], seeded["bridge"])
    created = scanner.scan()
    again = scanner.scan()
    assert created
    assert set(again) <= set(created)
    messages = seeded["mailbox"].list_messages()
    kinds = {item.message_kind for item in messages}
    assert MailboxMessageKind.REANCHOR_REQUIRED in kinds
    assert MailboxMessageKind.PACKET_AVAILABLE in kinds
    assert seeded["semantic"].connection.execute("SELECT COUNT(*) FROM obligations").fetchone()[0] == before
    assert checkpoint["checkpoint_id"]
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_unbound_targets_remain_enqueued(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    packet_register(
        seeded["semantic"],
        packet_kind="EM_TO_CM_SCIENCE_CARD",
        source_actor_context_id=seeded["em"].actor_context_id,
        target_actor_context_id=seeded["cm"].actor_context_id,
        payload_ref="docs/em.md",
        marker="marker-scan-em",
        direction_id="demo",
    )
    SemanticScanner(seeded["mailbox"], seeded["bridge"]).scan()
    stored = [item for item in seeded["mailbox"].list_messages() if item.target_actor_context_id == seeded["cm"].actor_context_id]
    assert stored
    assert stored[0].delivery_state.value == "ENQUEUED"
    eligible = seeded["mailbox"].select_eligible(
        target_actor_context_id=seeded["cm"].actor_context_id,
        target_kind="CM",
        target_binding_state="ACTIVE",
        sender_kind_for={seeded["em"].actor_context_id: "EM"},
    )
    assert eligible == []
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_obligation_human_subject_is_not_copied_into_mailbox_or_wake_refs(
    tmp_path: Path,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    workflow = seeded["semantic"].current_actor_workflow(
        seeded["portfolio"].actor_context_id
    )
    assert workflow is not None
    human_subject = "Review the external report\nbefore applying it"
    obligation_id = seeded["semantic"].open_obligation(
        str(workflow["workflow_id"]),
        ObligationKind.REPORT_INTAKE_REQUIRED,
        seeded["portfolio"].actor_context_id,
        human_subject,
        "A human-readable explanation remains in the semantic ledger.",
        "semantic-report-source",
    )

    SemanticScanner(seeded["mailbox"], seeded["bridge"]).scan()
    message = next(
        item
        for item in seeded["mailbox"].list_messages()
        if item.source_event_key == f"semantic:obligation:{obligation_id}:OPEN"
    )
    assert message.subject_ref == obligation_id
    assert message.payload_ref == obligation_id
    assert human_subject not in message.subject_ref
    assert "\n" not in message.subject_ref

    snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    wake = build_wake_text(snapshot, wake_batch_id="wake_obligation_ref", messages=[message])
    assert f"  subject_ref={obligation_id}" in wake.text.splitlines()
    assert f"  payload_ref={obligation_id}" in wake.text.splitlines()
    assert human_subject not in wake.text

    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
