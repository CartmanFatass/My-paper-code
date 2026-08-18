from pathlib import Path

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_reanchor
from tools.codex_semantic_mvp.packet_refs import packet_register
from tools.codex_supervisor.mailbox_models import MailboxMessageKind
from tools.codex_supervisor.semantic_scanner import SemanticScanner


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
