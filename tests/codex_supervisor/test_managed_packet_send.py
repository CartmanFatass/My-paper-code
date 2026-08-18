from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.managed_packet_send import ManagedPacketSendError, ManagedPacketSender


def test_packet_send_acl_and_idempotent_marker(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    payload = tmp_path / "typed-packet.md"
    payload.write_text("typed canary", encoding="utf-8")
    sender = ManagedPacketSender(seeded["bindings"], seeded["bridge"], tmp_path)
    first = sender.send(
        source_binding_id=seeded["root_binding_id"],
        packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
        target_alias="PORTFOLIO",
        payload_ref="typed-packet.md",
        marker="ROOT_TO_PORTFOLIO_REVIEW:canary",
        direction_id="demo",
    )
    again = sender.send(
        source_binding_id=seeded["root_binding_id"],
        packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
        target_alias="PORTFOLIO",
        payload_ref="typed-packet.md",
        marker="ROOT_TO_PORTFOLIO_REVIEW:canary",
        direction_id="demo",
    )
    assert first["packet_id"] == again["packet_id"]
    with pytest.raises(ManagedPacketSendError, match="repository-relative"):
        sender.send(
            source_binding_id=seeded["root_binding_id"],
            packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
            target_alias="PORTFOLIO",
            payload_ref="../secret.md",
            marker="ROOT_TO_PORTFOLIO_REVIEW:escape",
        )
    with pytest.raises(ManagedPacketSendError):
        sender.send(
            source_binding_id=seeded["portfolio_binding_id"],
            packet_kind="ROOT_TO_PORTFOLIO_REVIEW",
            target_alias="OPERATIONAL_ROOT",
            payload_ref="typed-packet.md",
            marker="ROOT_TO_PORTFOLIO_REVIEW:wrong-way",
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
